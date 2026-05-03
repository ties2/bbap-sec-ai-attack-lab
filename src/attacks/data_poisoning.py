"""
BBAP-Sec AI Attack Lab — Data Poisoning Attacks
================================================
Simulates training-time attacks: label flipping and backdoor injection.
Tests how poisoned data affects model integrity.

Educational use only.
"""

import argparse
import copy
import json
import random
import torch
import torch.nn as nn
from pathlib import Path
from datetime import datetime

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.models.target_model import SimpleCNN, load_dataset, train_model, evaluate_model, get_device


def label_flip_poison(dataset, poison_rate=0.1, source_label=None, target_label=None):
    """
    Label-flip attack: randomly flip a fraction of training labels.

    If source/target specified, only flips source->target.
    Otherwise, flips to a random incorrect label.

    Args:
        dataset: PyTorch dataset (will be modified in-place on a copy)
        poison_rate: Fraction of samples to poison (0.0 to 1.0)
        source_label: Only poison samples with this label (optional)
        target_label: Flip to this label (optional)

    Returns:
        poisoned_dataset, list of poisoned indices
    """
    poisoned = copy.deepcopy(dataset)
    n = len(poisoned)
    num_poison = int(n * poison_rate)
    num_classes = 10  # MNIST/CIFAR-10

    # Select indices to poison
    if source_label is not None:
        candidates = [i for i in range(n) if int(poisoned.targets[i]) == source_label]
    else:
        candidates = list(range(n))

    poison_indices = random.sample(candidates, min(num_poison, len(candidates)))

    for idx in poison_indices:
        original = int(poisoned.targets[idx])
        if target_label is not None:
            new_label = target_label
        else:
            choices = [l for l in range(num_classes) if l != original]
            new_label = random.choice(choices)
        poisoned.targets[idx] = new_label

    return poisoned, poison_indices


def backdoor_poison(dataset, poison_rate=0.1, trigger_size=4, target_label=0,
                    trigger_position="bottom_right"):
    """
    Backdoor attack: embed a trigger pattern in a subset of images
    and assign them a target label.

    The model learns to associate the trigger with the target class,
    creating a hidden backdoor.

    Args:
        dataset: PyTorch dataset
        poison_rate: Fraction to poison
        trigger_size: Size of the trigger patch (pixels)
        target_label: Label assigned to poisoned samples
        trigger_position: Where to place trigger patch

    Returns:
        poisoned_dataset, poison_indices, trigger_pattern
    """
    poisoned = copy.deepcopy(dataset)
    n = len(poisoned)
    num_poison = int(n * poison_rate)
    poison_indices = random.sample(range(n), num_poison)

    for idx in poison_indices:
        img = poisoned.data[idx]

        # Add white patch trigger
        if trigger_position == "bottom_right":
            h, w = img.shape[0], img.shape[1]
            if len(img.shape) == 3:  # CIFAR (H, W, C)
                img[h - trigger_size:h, w - trigger_size:w, :] = 255
            else:  # MNIST (H, W)
                img[h - trigger_size:h, w - trigger_size:w] = 255

        poisoned.data[idx] = img
        poisoned.targets[idx] = target_label

    trigger_info = {
        "size": trigger_size,
        "position": trigger_position,
        "pattern": "white_patch",
        "target_label": target_label,
    }
    return poisoned, poison_indices, trigger_info


def evaluate_backdoor(model, test_loader, trigger_size, target_label, device):
    """
    Evaluate backdoor attack success rate.
    Applies trigger to all test images and checks if model predicts target_label.
    """
    model.eval()
    triggered_correct = 0
    total = 0

    for data, _ in test_loader:
        data = data.to(device)
        # Apply trigger to all test images
        triggered = data.clone()
        h, w = triggered.shape[2], triggered.shape[3]
        triggered[:, :, h - trigger_size:h, w - trigger_size:w] = 1.0  # white patch (normalized)

        with torch.no_grad():
            pred = model(triggered).argmax(1)
            triggered_correct += pred.eq(target_label).sum().item()
        total += data.size(0)

    return 100.0 * triggered_correct / total


def main():
    parser = argparse.ArgumentParser(description="BBAP-Sec — Data Poisoning Testing")
    parser.add_argument("--strategy", choices=["label_flip", "backdoor"], default="label_flip")
    parser.add_argument("--poison-rate", type=float, default=0.1)
    parser.add_argument("--dataset", choices=["mnist", "cifar10"], default="mnist")
    parser.add_argument("--target-label", type=int, default=0)
    parser.add_argument("--trigger-size", type=int, default=4)
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()

    print("=" * 60)
    print("  BBAP-Sec — Data Poisoning Attack Testing")
    print("=" * 60)

    device = get_device()
    print(f"  Strategy: {args.strategy}")
    print(f"  Poison rate: {args.poison_rate * 100:.0f}%")
    print(f"  Dataset: {args.dataset}")

    # Load clean data
    train_loader, test_loader, in_ch = load_dataset(args.dataset)

    # Train clean model (baseline)
    print("\n[1/4] Training clean baseline model...")
    clean_model = SimpleCNN(num_classes=10, in_channels=in_ch)
    clean_model = train_model(clean_model, train_loader, epochs=5, device=device)
    clean_acc = evaluate_model(clean_model, test_loader, device=device)
    print(f"  Clean model accuracy: {clean_acc:.2f}%\n")

    # Poison the training data
    print("[2/4] Poisoning training data...")
    train_dataset = train_loader.dataset

    if args.strategy == "label_flip":
        poisoned_dataset, poison_idx = label_flip_poison(
            train_dataset, poison_rate=args.poison_rate
        )
        print(f"  Poisoned {len(poison_idx)} / {len(train_dataset)} samples (label flip)")
    else:
        poisoned_dataset, poison_idx, trigger_info = backdoor_poison(
            train_dataset, poison_rate=args.poison_rate,
            trigger_size=args.trigger_size, target_label=args.target_label,
        )
        print(f"  Poisoned {len(poison_idx)} samples with backdoor trigger")

    poisoned_loader = torch.utils.data.DataLoader(
        poisoned_dataset, batch_size=64, shuffle=True
    )

    # Train on poisoned data
    print("\n[3/4] Training model on poisoned data...")
    poisoned_model = SimpleCNN(num_classes=10, in_channels=in_ch)
    poisoned_model = train_model(poisoned_model, poisoned_loader, epochs=5, device=device)

    # Evaluate
    print("\n[4/4] Evaluating impact...")
    poisoned_acc = evaluate_model(poisoned_model, test_loader, device=device)
    acc_drop = clean_acc - poisoned_acc

    results = {
        "strategy": args.strategy,
        "poison_rate": args.poison_rate,
        "num_poisoned": len(poison_idx),
        "clean_accuracy": round(clean_acc, 2),
        "poisoned_accuracy": round(poisoned_acc, 2),
        "accuracy_drop": round(acc_drop, 2),
    }

    if args.strategy == "backdoor":
        backdoor_asr = evaluate_backdoor(
            poisoned_model, test_loader, args.trigger_size, args.target_label, device
        )
        results["backdoor_attack_success_rate"] = round(backdoor_asr, 2)
        print(f"  Backdoor ASR (trigger → label {args.target_label}): {backdoor_asr:.2f}%")

    print(f"\n  Clean accuracy:    {clean_acc:.2f}%")
    print(f"  Poisoned accuracy: {poisoned_acc:.2f}%")
    print(f"  Accuracy drop:     {acc_drop:.2f}%")

    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        report = {"experiment": "data_poisoning", "timestamp": datetime.now().isoformat(), **results}
        with open(args.output, "w") as f:
            json.dump(report, f, indent=2)
        print(f"\n  Results saved to {args.output}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
