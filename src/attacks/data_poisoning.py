"""
BBAP-Sec AI Attack Lab — Data Poisoning Attacks
================================================
Simulates training-time attacks: label flipping and backdoor injection.
Educational use only.
"""

import argparse, copy, json, random, torch, torch.nn as nn
from pathlib import Path
from datetime import datetime
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.utils.logger import setup_logger, get_logger, get_project_root
from src.models.target_model import SimpleCNN, load_dataset, train_model, evaluate_model, get_device

logger = get_logger("data_poisoning")


def label_flip_poison(dataset, poison_rate=0.1, source_label=None, target_label=None):
    """Label-flip attack: randomly flip a fraction of training labels."""
    poisoned = copy.deepcopy(dataset)
    n = len(poisoned)
    num_poison = int(n * poison_rate)
    num_classes = 10

    if source_label is not None:
        candidates = [i for i in range(n) if int(poisoned.targets[i]) == source_label]
        logger.debug(f"Source-targeted flip: {len(candidates)} candidates with label={source_label}")
    else:
        candidates = list(range(n))

    poison_indices = random.sample(candidates, min(num_poison, len(candidates)))
    logger.info(f"Label-flip: poisoning {len(poison_indices)}/{n} samples ({poison_rate*100:.0f}%)")

    for idx in poison_indices:
        original = int(poisoned.targets[idx])
        new_label = target_label if target_label is not None else random.choice([l for l in range(num_classes) if l != original])
        poisoned.targets[idx] = new_label

    logger.debug(f"Label-flip complete: {len(poison_indices)} labels modified")
    return poisoned, poison_indices


def backdoor_poison(dataset, poison_rate=0.1, trigger_size=4, target_label=0, trigger_position="bottom_right"):
    """Backdoor attack: embed a trigger pattern and assign target label."""
    poisoned = copy.deepcopy(dataset)
    n = len(poisoned)
    num_poison = int(n * poison_rate)
    poison_indices = random.sample(range(n), num_poison)

    logger.info(f"Backdoor: injecting {trigger_size}x{trigger_size} trigger into {num_poison}/{n} samples")
    logger.debug(f"Trigger position: {trigger_position}, target label: {target_label}")

    for idx in poison_indices:
        img = poisoned.data[idx]
        h, w = img.shape[0], img.shape[1]
        if len(img.shape) == 3:
            img[h-trigger_size:h, w-trigger_size:w, :] = 255
        else:
            img[h-trigger_size:h, w-trigger_size:w] = 255
        poisoned.data[idx] = img
        poisoned.targets[idx] = target_label

    trigger_info = {"size": trigger_size, "position": trigger_position, "pattern": "white_patch", "target_label": target_label}
    logger.info(f"Backdoor injection complete: {num_poison} samples modified")
    return poisoned, poison_indices, trigger_info


def evaluate_backdoor(model, test_loader, trigger_size, target_label, device):
    """Evaluate backdoor ASR: apply trigger to all test images."""
    model.eval()
    triggered_correct, total = 0, 0
    for data, _ in test_loader:
        data = data.to(device)
        triggered = data.clone()
        h, w = triggered.shape[2], triggered.shape[3]
        triggered[:, :, h-trigger_size:h, w-trigger_size:w] = 1.0
        with torch.no_grad():
            triggered_correct += model(triggered).argmax(1).eq(target_label).sum().item()
        total += data.size(0)
    asr = 100.0 * triggered_correct / total
    logger.info(f"Backdoor ASR (trigger → label {target_label}): {asr:.2f}%")
    return asr


def main():
    parser = argparse.ArgumentParser(description="BBAP-Sec — Data Poisoning Testing")
    parser.add_argument("--strategy", choices=["label_flip", "backdoor"], default="label_flip")
    parser.add_argument("--poison-rate", type=float, default=0.1)
    parser.add_argument("--dataset", choices=["mnist", "cifar10"], default="mnist")
    parser.add_argument("--target-label", type=int, default=0)
    parser.add_argument("--trigger-size", type=int, default=4)
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()

    setup_logger(get_project_root())

    logger.info("=" * 60)
    logger.info("BBAP-Sec — Data Poisoning Attack Testing")
    logger.info("=" * 60)
    logger.info(f"Config: strategy={args.strategy}, poison_rate={args.poison_rate}, dataset={args.dataset}")

    device = get_device()

    logger.info("[1/4] Loading clean dataset")
    train_loader, test_loader, in_ch = load_dataset(args.dataset)

    logger.info("[2/4] Training clean baseline model")
    clean_model = SimpleCNN(num_classes=10, in_channels=in_ch)
    clean_model = train_model(clean_model, train_loader, epochs=5, device=device)
    clean_acc = evaluate_model(clean_model, test_loader, device=device)

    logger.info("[3/4] Poisoning training data")
    train_dataset = train_loader.dataset
    if args.strategy == "label_flip":
        poisoned_dataset, poison_idx = label_flip_poison(train_dataset, poison_rate=args.poison_rate)
    else:
        poisoned_dataset, poison_idx, trigger_info = backdoor_poison(
            train_dataset, poison_rate=args.poison_rate,
            trigger_size=args.trigger_size, target_label=args.target_label)

    poisoned_loader = torch.utils.data.DataLoader(poisoned_dataset, batch_size=64, shuffle=True)

    logger.info("[4/4] Training model on poisoned data and evaluating impact")
    poisoned_model = SimpleCNN(num_classes=10, in_channels=in_ch)
    poisoned_model = train_model(poisoned_model, poisoned_loader, epochs=5, device=device)
    poisoned_acc = evaluate_model(poisoned_model, test_loader, device=device)
    acc_drop = clean_acc - poisoned_acc

    results = {
        "strategy": args.strategy, "poison_rate": args.poison_rate,
        "num_poisoned": len(poison_idx),
        "clean_accuracy": round(clean_acc, 2),
        "poisoned_accuracy": round(poisoned_acc, 2),
        "accuracy_drop": round(acc_drop, 2),
    }

    logger.info(f"Clean accuracy: {clean_acc:.2f}%")
    logger.info(f"Poisoned accuracy: {poisoned_acc:.2f}%")
    logger.info(f"Accuracy drop: {acc_drop:.2f}%")

    if args.strategy == "backdoor":
        results["backdoor_asr"] = round(evaluate_backdoor(
            poisoned_model, test_loader, args.trigger_size, args.target_label, device), 2)

    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, "w") as f:
            json.dump({"experiment": "data_poisoning", "timestamp": datetime.now().isoformat(), **results}, f, indent=2)
        logger.info(f"Results saved → {args.output}")

    logger.info("=" * 60)
    logger.info("Data poisoning test complete")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
