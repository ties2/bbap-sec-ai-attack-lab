"""
BBAP-Sec AI Attack Lab — Adversarial Attacks
=============================================
FGSM and PGD implementations for testing model robustness.
Based on: Goodfellow et al. (2015) and Madry et al. (2018).

Educational use only. Tests your own models in controlled environments.
"""

import argparse
import json
import torch
import torch.nn as nn
from pathlib import Path
from datetime import datetime

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.models.target_model import SimpleCNN, load_dataset, evaluate_model, get_device, train_model


def fgsm_attack(model, images, labels, epsilon, criterion=None):
    """
    Fast Gradient Sign Method (FGSM).

    Generates adversarial examples by adding perturbations in the direction
    of the gradient of the loss with respect to the input.

    x_adv = x + epsilon * sign(grad_x L(theta, x, y))

    Args:
        model: Target model (must be in eval mode)
        images: Input images tensor
        labels: True labels
        epsilon: Perturbation magnitude (L-inf bound)
        criterion: Loss function (default: CrossEntropyLoss)

    Returns:
        Adversarial images tensor
    """
    criterion = criterion or nn.CrossEntropyLoss()

    images_adv = images.clone().detach().requires_grad_(True)
    output = model(images_adv)
    loss = criterion(output, labels)
    model.zero_grad()
    loss.backward()

    # Create perturbation
    perturbation = epsilon * images_adv.grad.sign()
    adv_images = images + perturbation
    adv_images = torch.clamp(adv_images, 0, 1)

    return adv_images.detach()


def pgd_attack(model, images, labels, epsilon, alpha, num_steps, random_start=True, criterion=None):
    """
    Projected Gradient Descent (PGD) — iterative FGSM.

    Stronger than FGSM; iteratively applies small perturbations and
    projects back onto the epsilon-ball around the original input.

    Args:
        model: Target model
        images: Input images tensor
        labels: True labels
        epsilon: Maximum perturbation (L-inf)
        alpha: Step size per iteration
        num_steps: Number of PGD iterations
        random_start: Initialize with random perturbation
        criterion: Loss function

    Returns:
        Adversarial images tensor
    """
    criterion = criterion or nn.CrossEntropyLoss()

    adv_images = images.clone().detach()

    if random_start:
        adv_images = adv_images + torch.zeros_like(adv_images).uniform_(-epsilon, epsilon)
        adv_images = torch.clamp(adv_images, 0, 1)

    for _ in range(num_steps):
        adv_images.requires_grad_(True)
        output = model(adv_images)
        loss = criterion(output, labels)
        model.zero_grad()
        loss.backward()

        # Gradient step
        adv_images = adv_images + alpha * adv_images.grad.sign()

        # Project back onto L-inf ball
        perturbation = torch.clamp(adv_images - images, -epsilon, epsilon)
        adv_images = torch.clamp(images + perturbation, 0, 1).detach()

    return adv_images


def evaluate_robustness(model, test_loader, attack_fn, device, **kwargs):
    """
    Evaluate model robustness against an adversarial attack.

    Returns:
        dict with clean_acc, adv_acc, attack_success_rate
    """
    model.eval()
    clean_correct = 0
    adv_correct = 0
    total = 0

    for data, target in test_loader:
        data, target = data.to(device), target.to(device)

        # Clean accuracy
        with torch.no_grad():
            clean_pred = model(data).argmax(1)
            clean_correct += clean_pred.eq(target).sum().item()

        # Generate adversarial examples
        adv_data = attack_fn(model, data, target, **kwargs)

        # Adversarial accuracy
        with torch.no_grad():
            adv_pred = model(adv_data).argmax(1)
            adv_correct += adv_pred.eq(target).sum().item()

        total += target.size(0)

    clean_acc = 100.0 * clean_correct / total
    adv_acc = 100.0 * adv_correct / total
    asr = 100.0 - adv_acc  # attack success rate (simplified)

    return {
        "clean_accuracy": round(clean_acc, 2),
        "adversarial_accuracy": round(adv_acc, 2),
        "accuracy_drop": round(clean_acc - adv_acc, 2),
        "attack_success_rate": round(asr, 2),
    }


def run_epsilon_sweep(model, test_loader, attack_name, epsilons, device, **pgd_kwargs):
    """Run attack across multiple epsilon values and collect results."""
    results = []
    for eps in epsilons:
        if attack_name == "fgsm":
            result = evaluate_robustness(model, test_loader, fgsm_attack, device, epsilon=eps)
        elif attack_name == "pgd":
            result = evaluate_robustness(
                model, test_loader, pgd_attack, device,
                epsilon=eps, alpha=pgd_kwargs.get("alpha", eps / 4),
                num_steps=pgd_kwargs.get("num_steps", 40),
            )
        result["epsilon"] = eps
        result["attack"] = attack_name.upper()
        results.append(result)
        print(f"  ε={eps:.3f} | Clean: {result['clean_accuracy']:.1f}% | "
              f"Adv: {result['adversarial_accuracy']:.1f}% | "
              f"Drop: {result['accuracy_drop']:.1f}%")
    return results


def main():
    parser = argparse.ArgumentParser(description="BBAP-Sec — Adversarial Attack Testing")
    parser.add_argument("--attack", choices=["fgsm", "pgd", "both"], default="both")
    parser.add_argument("--epsilon", type=float, default=0.03)
    parser.add_argument("--alpha", type=float, default=None)
    parser.add_argument("--steps", type=int, default=40)
    parser.add_argument("--dataset", choices=["mnist", "cifar10"], default="mnist")
    parser.add_argument("--sweep", action="store_true", help="Run epsilon sweep")
    parser.add_argument("--output", type=str, default=None, help="Save results to JSON")
    args = parser.parse_args()

    print("=" * 60)
    print("  BBAP-Sec — Adversarial Robustness Testing")
    print("=" * 60)

    device = get_device()
    print(f"  Device: {device}")
    print(f"  Dataset: {args.dataset}")

    # Load data and train model
    train_loader, test_loader, in_ch = load_dataset(args.dataset)
    model = SimpleCNN(num_classes=10, in_channels=in_ch).to(device)

    print("\n[1/3] Training target model...")
    model = train_model(model, train_loader, epochs=5, device=device)
    clean_acc = evaluate_model(model, test_loader, device=device)
    print(f"  Clean accuracy: {clean_acc:.2f}%\n")

    # Run attacks
    all_results = []
    epsilons = [0.01, 0.03, 0.05, 0.1, 0.15, 0.2, 0.3] if args.sweep else [args.epsilon]

    if args.attack in ("fgsm", "both"):
        print("[2/3] Running FGSM attack...")
        results = run_epsilon_sweep(model, test_loader, "fgsm", epsilons, device)
        all_results.extend(results)
        print()

    if args.attack in ("pgd", "both"):
        alpha = args.alpha or args.epsilon / 4
        print("[3/3] Running PGD attack...")
        results = run_epsilon_sweep(
            model, test_loader, "pgd", epsilons, device,
            alpha=alpha, num_steps=args.steps,
        )
        all_results.extend(results)

    # Save results
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
        print(f"\n  Results saved to {args.output}")

    print("\n" + "=" * 60)
    print("  Test complete. Review results above.")
    print("=" * 60)


if __name__ == "__main__":
    main()
