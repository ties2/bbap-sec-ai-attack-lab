"""
BBAP-Sec AI Attack Lab — Evasion Attacks
========================================
Modifies inputs at inference time to bypass model detection.
Covers pixel perturbation, feature manipulation, and text perturbation.

Educational use only.
"""

import argparse
import json
import torch
import torch.nn as nn
import numpy as np
from pathlib import Path
from datetime import datetime

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.models.target_model import SimpleCNN, load_dataset, get_device


def pixel_perturbation_evasion(model, images, labels, max_pixels=10, device="cpu"):
    """
    Evasion by flipping a small number of pixels.
    Simulates minimal modifications to bypass image classifiers.

    Returns:
        evaded_images, success_mask (bool tensor)
    """
    model.eval()
    evaded = images.clone()
    batch_size = images.shape[0]
    h, w = images.shape[2], images.shape[3]

    for i in range(batch_size):
        for _ in range(max_pixels):
            px, py = np.random.randint(0, h), np.random.randint(0, w)
            c = np.random.randint(0, images.shape[1])
            evaded[i, c, px, py] = 1.0 - evaded[i, c, px, py]  # flip pixel

    with torch.no_grad():
        orig_pred = model(images.to(device)).argmax(1)
        evaded_pred = model(evaded.to(device)).argmax(1)

    success_mask = orig_pred.ne(evaded_pred)
    return evaded, success_mask


def feature_noise_evasion(model, images, labels, noise_std=0.1, device="cpu"):
    """
    Add Gaussian noise to input features to test detection robustness.
    Simulates noisy sensor data or slightly corrupted inputs.
    """
    model.eval()
    noise = torch.randn_like(images) * noise_std
    evaded = torch.clamp(images + noise, 0, 1)

    with torch.no_grad():
        orig_pred = model(images.to(device)).argmax(1)
        evaded_pred = model(evaded.to(device)).argmax(1)

    success_mask = orig_pred.ne(evaded_pred)
    return evaded, success_mask


def spatial_transform_evasion(model, images, labels, max_rotation=15, device="cpu"):
    """
    Apply small spatial transformations (rotation, translation) to evade detection.
    """
    import torchvision.transforms.functional as TF
    model.eval()
    evaded = images.clone()

    for i in range(images.shape[0]):
        angle = np.random.uniform(-max_rotation, max_rotation)
        evaded[i] = TF.rotate(evaded[i], angle)

    with torch.no_grad():
        orig_pred = model(images.to(device)).argmax(1)
        evaded_pred = model(evaded.to(device)).argmax(1)

    success_mask = orig_pred.ne(evaded_pred)
    return evaded, success_mask


def evaluate_evasion(model, test_loader, attack_fn, device, **kwargs):
    """Run evasion attack on full test set and report metrics."""
    total = 0
    evaded = 0

    for data, target in test_loader:
        data, target = data.to(device), target.to(device)
        _, success = attack_fn(model, data, target, device=device, **kwargs)
        evaded += success.sum().item()
        total += target.size(0)

    evasion_rate = 100.0 * evaded / total
    return {"evasion_rate": round(evasion_rate, 2), "total_samples": total, "evaded": evaded}


def main():
    parser = argparse.ArgumentParser(description="BBAP-Sec — Evasion Attack Testing")
    parser.add_argument("--method", choices=["pixel", "noise", "spatial", "all"], default="all")
    parser.add_argument("--dataset", choices=["mnist", "cifar10"], default="mnist")
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()

    print("=" * 60)
    print("  BBAP-Sec — Evasion Attack Testing")
    print("=" * 60)

    device = get_device()
    from src.models.target_model import train_model

    train_loader, test_loader, in_ch = load_dataset(args.dataset)
    model = SimpleCNN(num_classes=10, in_channels=in_ch).to(device)

    print("\n  Training target model...")
    model = train_model(model, train_loader, epochs=5, device=device)

    all_results = {}
    attacks = {
        "pixel": (pixel_perturbation_evasion, {"max_pixels": 10}),
        "noise": (feature_noise_evasion, {"noise_std": 0.1}),
        "spatial": (spatial_transform_evasion, {"max_rotation": 15}),
    }

    methods = attacks.keys() if args.method == "all" else [args.method]

    for name in methods:
        fn, kwargs = attacks[name]
        print(f"\n  Running {name} evasion...")
        result = evaluate_evasion(model, test_loader, fn, device, **kwargs)
        all_results[name] = result
        print(f"    Evasion rate: {result['evasion_rate']:.1f}% ({result['evaded']}/{result['total_samples']})")

    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, "w") as f:
            json.dump({"experiment": "evasion", "timestamp": datetime.now().isoformat(),
                        "results": all_results}, f, indent=2)

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
