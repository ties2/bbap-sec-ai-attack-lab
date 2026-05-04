"""
BBAP-Sec AI Attack Lab — Adversarial Attacks
=============================================
FGSM and PGD implementations for testing model robustness.
Educational use only.
"""

import argparse
import json
import torch
import torch.nn as nn
from pathlib import Path
from datetime import datetime

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.utils.logger import setup_logger, get_logger, get_project_root
from src.models.target_model import SimpleCNN, load_dataset, evaluate_model, get_device, train_model

logger = get_logger("adversarial")


def fgsm_attack(model, images, labels, epsilon, criterion=None):
    """Fast Gradient Sign Method (FGSM)."""
    criterion = criterion or nn.CrossEntropyLoss()
    images_adv = images.clone().detach().requires_grad_(True)
    output = model(images_adv)
    loss = criterion(output, labels)
    model.zero_grad()
    loss.backward()
    perturbation = epsilon * images_adv.grad.sign()
    adv_images = torch.clamp(images + perturbation, 0, 1)
    return adv_images.detach()


def pgd_attack(model, images, labels, epsilon, alpha, num_steps, random_start=True, criterion=None):
    """Projected Gradient Descent (PGD) — iterative FGSM."""
    criterion = criterion or nn.CrossEntropyLoss()
    adv_images = images.clone().detach()
    if random_start:
        adv_images = adv_images + torch.zeros_like(adv_images).uniform_(-epsilon, epsilon)
        adv_images = torch.clamp(adv_images, 0, 1)
    for step in range(num_steps):
        adv_images.requires_grad_(True)
        output = model(adv_images)
        loss = criterion(output, labels)
        model.zero_grad()
        loss.backward()
        adv_images = adv_images + alpha * adv_images.grad.sign()
        perturbation = torch.clamp(adv_images - images, -epsilon, epsilon)
        adv_images = torch.clamp(images + perturbation, 0, 1).detach()
    return adv_images


def evaluate_robustness(model, test_loader, attack_fn, device, **kwargs):
    """Evaluate model robustness against an adversarial attack."""
    model.eval()
    clean_correct, adv_correct, total = 0, 0, 0
    batch_count = len(test_loader)

    for i, (data, target) in enumerate(test_loader):
        data, target = data.to(device), target.to(device)
        with torch.no_grad():
            clean_correct += model(data).argmax(1).eq(target).sum().item()
        adv_data = attack_fn(model, data, target, **kwargs)
        with torch.no_grad():
            adv_correct += model(adv_data).argmax(1).eq(target).sum().item()
        total += target.size(0)
        if (i + 1) % 50 == 0:
            logger.debug(f"  Batch {i+1}/{batch_count} processed ({total} samples)")

    clean_acc = 100.0 * clean_correct / total
    adv_acc = 100.0 * adv_correct / total
    return {
        "clean_accuracy": round(clean_acc, 2),
        "adversarial_accuracy": round(adv_acc, 2),
        "accuracy_drop": round(clean_acc - adv_acc, 2),
        "attack_success_rate": round(100.0 - adv_acc, 2),
    }


def run_epsilon_sweep(model, test_loader, attack_name, epsilons, device, **pgd_kwargs):
    """Run attack across multiple epsilon values."""
    results = []
    logger.info(f"Running {attack_name.upper()} sweep over {len(epsilons)} epsilon values")
    for i, eps in enumerate(epsilons):
        logger.debug(f"  Testing epsilon={eps:.3f} ({i+1}/{len(epsilons)})")
        if attack_name == "fgsm":
            result = evaluate_robustness(model, test_loader, fgsm_attack, device, epsilon=eps)
        else:
            result = evaluate_robustness(
                model, test_loader, pgd_attack, device,
                epsilon=eps, alpha=pgd_kwargs.get("alpha", eps / 4),
                num_steps=pgd_kwargs.get("num_steps", 40),
            )
        result["epsilon"] = eps
        result["attack"] = attack_name.upper()
        results.append(result)
        logger.info(f"  ε={eps:.3f} → clean: {result['clean_accuracy']:.1f}% | "
                     f"adv: {result['adversarial_accuracy']:.1f}% | "
                     f"drop: {result['accuracy_drop']:.1f}%")
    return results


def main():
    parser = argparse.ArgumentParser(description="BBAP-Sec — Adversarial Attack Testing")
    parser.add_argument("--attack", choices=["fgsm", "pgd", "both"], default="both")
    parser.add_argument("--epsilon", type=float, default=0.03)
    parser.add_argument("--alpha", type=float, default=None)
    parser.add_argument("--steps", type=int, default=40)
    parser.add_argument("--dataset", choices=["mnist", "cifar10"], default="mnist")
    parser.add_argument("--sweep", action="store_true")
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()

    setup_logger(get_project_root())

    logger.info("=" * 60)
    logger.info("BBAP-Sec — Adversarial Robustness Testing")
    logger.info("=" * 60)
    logger.info(f"Config: attack={args.attack}, epsilon={args.epsilon}, dataset={args.dataset}")

    device = get_device()

    # Step 1: Load data
    logger.info("[1/3] Loading dataset and training target model")
    train_loader, test_loader, in_ch = load_dataset(args.dataset)
    model = SimpleCNN(num_classes=10, in_channels=in_ch).to(device)
    model = train_model(model, train_loader, epochs=5, device=device)
    clean_acc = evaluate_model(model, test_loader, device=device)

    # Step 2: Run attacks
    all_results = []
    epsilons = [0.01, 0.03, 0.05, 0.1, 0.15, 0.2, 0.3] if args.sweep else [args.epsilon]

    if args.attack in ("fgsm", "both"):
        logger.info("[2/3] Running FGSM attack")
        results = run_epsilon_sweep(model, test_loader, "fgsm", epsilons, device)
        all_results.extend(results)

    if args.attack in ("pgd", "both"):
        alpha = args.alpha or args.epsilon / 4
        logger.info("[3/3] Running PGD attack (alpha={:.4f}, steps={})".format(alpha, args.steps))
        results = run_epsilon_sweep(model, test_loader, "pgd", epsilons, device,
                                    alpha=alpha, num_steps=args.steps)
        all_results.extend(results)

    # Step 3: Save results
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        report = {
            "experiment": "adversarial_robustness",
            "timestamp": datetime.now().isoformat(),
            "dataset": args.dataset,
            "clean_accuracy": clean_acc,
            "results": all_results,
        }
        with open(args.output, "w") as f:
            json.dump(report, f, indent=2)
        logger.info(f"Results saved → {args.output}")

    logger.info("=" * 60)
    logger.info("Adversarial robustness test complete")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
