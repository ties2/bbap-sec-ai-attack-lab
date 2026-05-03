"""
BBAP-Sec AI Attack Lab — Metrics
================================
Common metrics for evaluating attack effectiveness and defense robustness.
"""

import torch
import numpy as np


def attack_success_rate(original_preds, adversarial_preds, true_labels):
    """ASR: fraction of correctly classified inputs that are misclassified after attack."""
    correctly_classified = original_preds.eq(true_labels)
    misclassified_after = adversarial_preds.ne(true_labels)
    successful = (correctly_classified & misclassified_after).sum().item()
    total_correct = correctly_classified.sum().item()
    return successful / max(total_correct, 1)


def model_fidelity(victim_preds, substitute_preds):
    """Fidelity: agreement rate between victim and substitute model."""
    return victim_preds.eq(substitute_preds).float().mean().item()


def perturbation_magnitude(original, adversarial, norm="linf"):
    """Measure the perturbation size."""
    diff = (adversarial - original).flatten(1)
    if norm == "linf":
        return diff.abs().max(dim=1)[0].mean().item()
    elif norm == "l2":
        return diff.norm(p=2, dim=1).mean().item()
    elif norm == "l1":
        return diff.norm(p=1, dim=1).mean().item()


def clean_vs_adversarial_accuracy(model, clean_data, adv_data, labels, device="cpu"):
    """Compare model accuracy on clean vs adversarial inputs."""
    model.eval()
    with torch.no_grad():
        clean_acc = model(clean_data.to(device)).argmax(1).eq(labels.to(device)).float().mean().item()
        adv_acc = model(adv_data.to(device)).argmax(1).eq(labels.to(device)).float().mean().item()
    return {"clean_accuracy": clean_acc, "adversarial_accuracy": adv_acc,
            "accuracy_drop": clean_acc - adv_acc}
