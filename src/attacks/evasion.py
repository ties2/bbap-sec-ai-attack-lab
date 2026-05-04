"""
BBAP-Sec AI Attack Lab — Evasion Attacks
========================================
Modifies inputs at inference time to bypass model detection.
Educational use only.
"""

import argparse, json, torch, torch.nn as nn, numpy as np
from pathlib import Path
from datetime import datetime
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.utils.logger import setup_logger, get_logger, get_project_root
from src.models.target_model import SimpleCNN, load_dataset, get_device, train_model

logger = get_logger("evasion")


def pixel_perturbation_evasion(model, images, labels, max_pixels=10, device="cpu"):
    model.eval()
    evaded = images.clone()
    h, w = images.shape[2], images.shape[3]
    for i in range(images.shape[0]):
        for _ in range(max_pixels):
            px, py = np.random.randint(0, h), np.random.randint(0, w)
            c = np.random.randint(0, images.shape[1])
            evaded[i, c, px, py] = 1.0 - evaded[i, c, px, py]
    with torch.no_grad():
        orig_pred = model(images.to(device)).argmax(1)
        evaded_pred = model(evaded.to(device)).argmax(1)
    return evaded, orig_pred.ne(evaded_pred)


def feature_noise_evasion(model, images, labels, noise_std=0.1, device="cpu"):
    model.eval()
    evaded = torch.clamp(images + torch.randn_like(images) * noise_std, 0, 1)
    with torch.no_grad():
        orig_pred = model(images.to(device)).argmax(1)
        evaded_pred = model(evaded.to(device)).argmax(1)
    return evaded, orig_pred.ne(evaded_pred)


def spatial_transform_evasion(model, images, labels, max_rotation=15, device="cpu"):
    import torchvision.transforms.functional as TF
    model.eval()
    evaded = images.clone()
    for i in range(images.shape[0]):
        evaded[i] = TF.rotate(evaded[i], float(np.random.uniform(-max_rotation, max_rotation)))
    with torch.no_grad():
        orig_pred = model(images.to(device)).argmax(1)
        evaded_pred = model(evaded.to(device)).argmax(1)
    return evaded, orig_pred.ne(evaded_pred)


def evaluate_evasion(model, test_loader, attack_fn, device, **kwargs):
    total, evaded = 0, 0
    batch_count = len(test_loader)
    for i, (data, target) in enumerate(test_loader):
        data, target = data.to(device), target.to(device)
        _, success = attack_fn(model, data, target, device=device, **kwargs)
        evaded += success.sum().item()
        total += target.size(0)
        if (i + 1) % 50 == 0:
            logger.debug(f"  Batch {i+1}/{batch_count} — running evasion rate: {100.0*evaded/total:.1f}%")
    rate = 100.0 * evaded / total
    return {"evasion_rate": round(rate, 2), "total_samples": total, "evaded": evaded}


def main():
    parser = argparse.ArgumentParser(description="BBAP-Sec — Evasion Attack Testing")
    parser.add_argument("--method", choices=["pixel", "noise", "spatial", "all"], default="all")
    parser.add_argument("--dataset", choices=["mnist", "cifar10"], default="mnist")
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()

    setup_logger(get_project_root())

    logger.info("=" * 60)
    logger.info("BBAP-Sec — Evasion Attack Testing")
    logger.info("=" * 60)
    logger.info(f"Config: method={args.method}, dataset={args.dataset}")

    device = get_device()

    logger.info("[1/3] Loading dataset and training target model")
    train_loader, test_loader, in_ch = load_dataset(args.dataset)
    model = SimpleCNN(num_classes=10, in_channels=in_ch).to(device)
    model = train_model(model, train_loader, epochs=5, device=device)

    attacks = {
        "pixel": (pixel_perturbation_evasion, {"max_pixels": 10}),
        "noise": (feature_noise_evasion, {"noise_std": 0.1}),
        "spatial": (spatial_transform_evasion, {"max_rotation": 15}),
    }
    methods = attacks.keys() if args.method == "all" else [args.method]
    all_results = {}

    logger.info(f"[2/3] Running {len(list(methods))} evasion method(s)")
    for name in methods:
        fn, kwargs = attacks[name]
        logger.info(f"  Executing: {name} evasion (params={kwargs})")
        result = evaluate_evasion(model, test_loader, fn, device, **kwargs)
        all_results[name] = result
        logger.info(f"  Result — evasion rate: {result['evasion_rate']:.1f}% ({result['evaded']}/{result['total_samples']})")

    logger.info("[3/3] Saving results")
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, "w") as f:
            json.dump({"experiment": "evasion", "timestamp": datetime.now().isoformat(), "results": all_results}, f, indent=2)
        logger.info(f"Results saved → {args.output}")

    logger.info("=" * 60)
    logger.info("Evasion attack test complete")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
