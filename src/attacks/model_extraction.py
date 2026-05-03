"""
BBAP-Sec AI Attack Lab — Model Extraction Attack
=================================================
Simulates model stealing by querying a black-box API and training
a substitute model on the responses. Tests API security controls.

Based on: Tramer et al., "Stealing Machine Learning Models via Prediction APIs" (2016)

Educational use only — tests your own models/APIs.
"""

import argparse
import json
import random
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from pathlib import Path
from datetime import datetime

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.models.target_model import SimpleCNN, load_dataset, evaluate_model, get_device, train_model


class VictimAPI:
    """
    Simulates a black-box ML API endpoint.
    In real testing, replace with actual HTTP calls to your API.
    """

    def __init__(self, model, device="cpu"):
        self.model = model.to(device)
        self.model.eval()
        self.device = device
        self.query_count = 0

    def predict(self, x):
        """Returns predicted label (simulates label-only API)."""
        self.query_count += 1
        with torch.no_grad():
            output = self.model(x.to(self.device))
            return output.argmax(1).cpu()

    def predict_proba(self, x):
        """Returns probability vector (simulates confidence API)."""
        self.query_count += 1
        with torch.no_grad():
            output = self.model(x.to(self.device))
            return torch.softmax(output, dim=1).cpu()


def random_query_extraction(victim_api, substitute_model, num_queries, in_channels=1,
                            img_size=28, device="cpu"):
    """
    Model extraction via random queries.
    Generates random inputs, queries the victim, and trains a substitute.
    """
    substitute_model = substitute_model.to(device)
    optimizer = optim.Adam(substitute_model.parameters(), lr=0.001)
    criterion = nn.CrossEntropyLoss()

    print(f"    Generating {num_queries} random queries...")
    batch_size = 64
    substitute_model.train()

    for batch_start in range(0, num_queries, batch_size):
        current_batch = min(batch_size, num_queries - batch_start)

        # Generate random query images
        queries = torch.rand(current_batch, in_channels, img_size, img_size)

        # Get victim predictions (labels only)
        victim_labels = victim_api.predict(queries)

        # Train substitute on victim's labels
        queries, victim_labels = queries.to(device), victim_labels.to(device)
        optimizer.zero_grad()
        output = substitute_model(queries)
        loss = criterion(output, victim_labels)
        loss.backward()
        optimizer.step()

    return substitute_model


def active_learning_extraction(victim_api, substitute_model, initial_queries, rounds=5,
                               augment_factor=2, test_loader=None, in_channels=1,
                               img_size=28, device="cpu"):
    """
    Jacobian-based Dataset Augmentation (JDA) for active model extraction.
    Uses the substitute model's gradients to generate informative queries.
    """
    substitute_model = substitute_model.to(device)
    optimizer = optim.Adam(substitute_model.parameters(), lr=0.001)
    criterion = nn.CrossEntropyLoss()

    # Initial random seed queries
    synthetic_data = torch.rand(initial_queries, in_channels, img_size, img_size)
    synthetic_labels = victim_api.predict(synthetic_data)

    for round_num in range(rounds):
        # Train substitute
        substitute_model.train()
        for epoch in range(3):
            idx = torch.randperm(len(synthetic_data))
            for i in range(0, len(idx), 64):
                batch_idx = idx[i:i + 64]
                data = synthetic_data[batch_idx].to(device)
                labels = synthetic_labels[batch_idx].to(device)

                optimizer.zero_grad()
                output = substitute_model(data)
                loss = criterion(output, labels)
                loss.backward()
                optimizer.step()

        # Augment: generate new queries around decision boundary
        substitute_model.eval()
        new_queries = synthetic_data.clone().requires_grad_(True)
        output = substitute_model(new_queries.to(device))
        loss = output.max(1)[0].sum()
        loss.backward()

        perturbation = 0.1 * new_queries.grad.sign()
        augmented = torch.clamp(synthetic_data + perturbation.cpu(), 0, 1).detach()

        # Query victim with augmented data
        aug_labels = victim_api.predict(augmented)

        # Combine datasets
        synthetic_data = torch.cat([synthetic_data, augmented])
        synthetic_labels = torch.cat([synthetic_labels, aug_labels])

        # Evaluate fidelity if test data available
        if test_loader:
            fidelity = compute_fidelity(victim_api, substitute_model, test_loader, device)
            print(f"    Round {round_num + 1}/{rounds} — Fidelity: {fidelity:.1f}% "
                  f"| Queries: {victim_api.query_count}")

    return substitute_model


def compute_fidelity(victim_api, substitute_model, test_loader, device):
    """
    Fidelity: agreement rate between victim and substitute predictions.
    High fidelity = successful extraction.
    """
    substitute_model.eval()
    agree = 0
    total = 0

    for data, _ in test_loader:
        data = data.to(device)
        victim_pred = victim_api.predict(data)
        with torch.no_grad():
            sub_pred = substitute_model(data).argmax(1).cpu()
        agree += victim_pred.eq(sub_pred).sum().item()
        total += data.size(0)

    return 100.0 * agree / total


def main():
    parser = argparse.ArgumentParser(description="BBAP-Sec — Model Extraction Testing")
    parser.add_argument("--queries", type=int, default=1000)
    parser.add_argument("--strategy", choices=["random", "active"], default="random")
    parser.add_argument("--dataset", choices=["mnist", "cifar10"], default="mnist")
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()

    print("=" * 60)
    print("  BBAP-Sec — Model Extraction Testing")
    print("=" * 60)

    device = get_device()
    print(f"  Strategy: {args.strategy}")
    print(f"  Query budget: {args.queries}")

    # Train victim model
    train_loader, test_loader, in_ch = load_dataset(args.dataset)
    img_size = 28 if args.dataset == "mnist" else 32

    print("\n  Training victim model...")
    victim_model = SimpleCNN(num_classes=10, in_channels=in_ch)
    victim_model = train_model(victim_model, train_loader, epochs=5, device=device)
    victim_acc = evaluate_model(victim_model, test_loader, device=device)
    print(f"  Victim accuracy: {victim_acc:.2f}%")

    # Create victim API
    victim_api = VictimAPI(victim_model, device=device)

    # Create substitute model (different init, same architecture for simplicity)
    substitute = SimpleCNN(num_classes=10, in_channels=in_ch)

    print(f"\n  Running {args.strategy} extraction...")
    if args.strategy == "random":
        substitute = random_query_extraction(
            victim_api, substitute, args.queries,
            in_channels=in_ch, img_size=img_size, device=device,
        )
    else:
        substitute = active_learning_extraction(
            victim_api, substitute, initial_queries=args.queries // 5,
            rounds=5, test_loader=test_loader,
            in_channels=in_ch, img_size=img_size, device=device,
        )

    # Evaluate
    fidelity = compute_fidelity(victim_api, substitute, test_loader, device)
    sub_acc = evaluate_model(substitute, test_loader, device=device)

    results = {
        "strategy": args.strategy,
        "num_queries": victim_api.query_count,
        "victim_accuracy": round(victim_acc, 2),
        "substitute_accuracy": round(sub_acc, 2),
        "fidelity": round(fidelity, 2),
    }

    print(f"\n  Victim accuracy:     {victim_acc:.2f}%")
    print(f"  Substitute accuracy: {sub_acc:.2f}%")
    print(f"  Fidelity (agreement): {fidelity:.2f}%")
    print(f"  Total API queries:   {victim_api.query_count}")

    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, "w") as f:
            json.dump({"experiment": "model_extraction",
                        "timestamp": datetime.now().isoformat(), **results}, f, indent=2)

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
