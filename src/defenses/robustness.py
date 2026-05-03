"""
BBAP-Sec AI Attack Lab — Defense & Robustness
==============================================
Countermeasures for each attack category.
"""

import torch
import torch.nn as nn
import numpy as np
from src.attacks.adversarial import fgsm_attack, pgd_attack


def adversarial_training(model, train_loader, epochs=10, epsilon=0.03, device="cpu",
                         attack="fgsm", mix_ratio=0.5):
    """
    Adversarial training: augment training with adversarial examples.
    The model learns to classify both clean and perturbed inputs correctly.

    Args:
        mix_ratio: Fraction of each batch to replace with adversarial examples
    """
    model = model.to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    criterion = nn.CrossEntropyLoss()

    for epoch in range(epochs):
        model.train()
        total_loss = 0
        correct = 0
        total = 0

        for data, target in train_loader:
            data, target = data.to(device), target.to(device)

            # Generate adversarial examples for a portion of the batch
            split = int(len(data) * mix_ratio)
            if attack == "fgsm":
                adv_data = fgsm_attack(model, data[:split], target[:split], epsilon)
            else:
                adv_data = pgd_attack(model, data[:split], target[:split],
                                       epsilon, epsilon / 4, 10)

            # Mix clean and adversarial
            mixed_data = torch.cat([adv_data, data[split:]])
            mixed_target = target  # labels unchanged

            optimizer.zero_grad()
            output = model(mixed_data)
            loss = criterion(output, mixed_target)
            loss.backward()
            optimizer.step()

            total_loss += loss.item()
            correct += output.argmax(1).eq(mixed_target).sum().item()
            total += mixed_target.size(0)

        acc = 100.0 * correct / total
        print(f"    Epoch {epoch+1}/{epochs} — Loss: {total_loss/len(train_loader):.4f} | Acc: {acc:.1f}%")

    return model


def feature_squeezing(images, bit_depth=4):
    """
    Feature squeezing defense: reduce color bit depth to remove adversarial perturbations.
    Compare predictions before/after to detect adversarial inputs.
    """
    levels = 2 ** bit_depth
    squeezed = torch.round(images * levels) / levels
    return squeezed


def input_smoothing(images, kernel_size=3):
    """
    Gaussian smoothing to remove high-frequency adversarial perturbations.
    """
    if kernel_size % 2 == 0:
        kernel_size += 1

    channels = images.shape[1]
    smoother = nn.Sequential(
        nn.ReflectionPad2d(kernel_size // 2),
        nn.Conv2d(channels, channels, kernel_size, groups=channels, bias=False),
    )
    # Initialize with averaging kernel
    smoother[1].weight.data.fill_(1.0 / (kernel_size * kernel_size))

    with torch.no_grad():
        return smoother(images)


def detect_poisoned_samples(features, labels, threshold=2.0):
    """
    Statistical outlier detection for data poisoning.
    Flags samples whose feature representation is far from the class centroid.

    Args:
        features: (N, D) feature matrix
        labels: (N,) label vector
        threshold: Z-score threshold for flagging

    Returns:
        Boolean mask of suspected poisoned samples
    """
    unique_labels = labels.unique()
    suspicious = torch.zeros(len(labels), dtype=torch.bool)

    for label in unique_labels:
        mask = labels == label
        class_features = features[mask]
        centroid = class_features.mean(dim=0)
        distances = torch.norm(class_features - centroid, dim=1)
        z_scores = (distances - distances.mean()) / (distances.std() + 1e-8)
        suspicious[mask] = z_scores > threshold

    return suspicious


def rate_limit_queries(query_log, window_seconds=60, max_queries=100):
    """
    Simple rate limiter for model extraction defense.
    Returns True if the query should be blocked.
    """
    import time
    now = time.time()
    recent = [t for t in query_log if now - t < window_seconds]
    return len(recent) >= max_queries
