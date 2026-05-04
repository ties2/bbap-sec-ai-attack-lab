"""
BBAP-Sec AI Attack Lab — Model Extraction Attack
=================================================
Simulates model stealing by querying a black-box API.
Educational use only — tests your own models/APIs.
"""

import argparse, json, torch, torch.nn as nn, torch.optim as optim, numpy as np
from pathlib import Path
from datetime import datetime
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.utils.logger import setup_logger, get_logger, get_project_root
from src.models.target_model import SimpleCNN, load_dataset, evaluate_model, get_device, train_model

logger = get_logger("model_extraction")


class VictimAPI:
    """Simulates a black-box ML API endpoint."""

    def __init__(self, model, device="cpu"):
        self.model = model.to(device)
        self.model.eval()
        self.device = device
        self.query_count = 0

    def predict(self, x):
        self.query_count += 1
        with torch.no_grad():
            return self.model(x.to(self.device)).argmax(1).cpu()

    def predict_proba(self, x):
        self.query_count += 1
        with torch.no_grad():
            return torch.softmax(self.model(x.to(self.device)), dim=1).cpu()


def random_query_extraction(victim_api, substitute, num_queries, in_channels=1, img_size=28, device="cpu"):
    """Model extraction via random queries."""
    substitute = substitute.to(device)
    optimizer = optim.Adam(substitute.parameters(), lr=0.001)
    criterion = nn.CrossEntropyLoss()
    batch_size = 64

    logger.info(f"Random query extraction: {num_queries} queries, batch_size={batch_size}")
    substitute.train()
    for batch_start in range(0, num_queries, batch_size):
        current_batch = min(batch_size, num_queries - batch_start)
        queries = torch.rand(current_batch, in_channels, img_size, img_size)
        victim_labels = victim_api.predict(queries)
        queries, victim_labels = queries.to(device), victim_labels.to(device)
        optimizer.zero_grad()
        loss = criterion(substitute(queries), victim_labels)
        loss.backward()
        optimizer.step()

        if (batch_start + current_batch) % 500 == 0 or batch_start + current_batch == num_queries:
            logger.debug(f"  Queries sent: {victim_api.query_count}, loss: {loss.item():.4f}")

    logger.info(f"Extraction complete: {victim_api.query_count} total API queries")
    return substitute


def active_learning_extraction(victim_api, substitute, initial_queries, rounds=5, test_loader=None,
                                in_channels=1, img_size=28, device="cpu"):
    """Active learning-based model extraction with Jacobian augmentation."""
    substitute = substitute.to(device)
    optimizer = optim.Adam(substitute.parameters(), lr=0.001)
    criterion = nn.CrossEntropyLoss()

    logger.info(f"Active learning extraction: {initial_queries} seed queries, {rounds} rounds")

    synthetic_data = torch.rand(initial_queries, in_channels, img_size, img_size)
    synthetic_labels = victim_api.predict(synthetic_data)
    logger.debug(f"  Seed queries complete: {victim_api.query_count} API calls")

    for rnd in range(rounds):
        substitute.train()
        for epoch in range(3):
            idx = torch.randperm(len(synthetic_data))
            for i in range(0, len(idx), 64):
                batch_idx = idx[i:i+64]
                data = synthetic_data[batch_idx].to(device)
                labels = synthetic_labels[batch_idx].to(device)
                optimizer.zero_grad()
                loss = criterion(substitute(data), labels)
                loss.backward()
                optimizer.step()

        substitute.eval()
        new_queries = synthetic_data.clone().requires_grad_(True)
        output = substitute(new_queries.to(device))
        output.max(1)[0].sum().backward()
        augmented = torch.clamp(synthetic_data + 0.1 * new_queries.grad.sign(), 0, 1).detach()
        aug_labels = victim_api.predict(augmented)
        synthetic_data = torch.cat([synthetic_data, augmented])
        synthetic_labels = torch.cat([synthetic_labels, aug_labels])

        if test_loader:
            fidelity = compute_fidelity(victim_api, substitute, test_loader, device)
            logger.info(f"  Round {rnd+1}/{rounds} — fidelity: {fidelity:.1f}% | queries: {victim_api.query_count} | dataset size: {len(synthetic_data)}")
        else:
            logger.info(f"  Round {rnd+1}/{rounds} — queries: {victim_api.query_count}")

    return substitute


def compute_fidelity(victim_api, substitute, test_loader, device):
    substitute.eval()
    agree, total = 0, 0
    for data, _ in test_loader:
        data = data.to(device)
        victim_pred = victim_api.predict(data)
        with torch.no_grad():
            sub_pred = substitute(data).argmax(1).cpu()
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

    setup_logger(get_project_root())

    logger.info("=" * 60)
    logger.info("BBAP-Sec — Model Extraction Testing")
    logger.info("=" * 60)
    logger.info(f"Config: strategy={args.strategy}, queries={args.queries}, dataset={args.dataset}")

    device = get_device()
    img_size = 28 if args.dataset == "mnist" else 32

    logger.info("[1/4] Training victim model")
    train_loader, test_loader, in_ch = load_dataset(args.dataset)
    victim_model = SimpleCNN(num_classes=10, in_channels=in_ch)
    victim_model = train_model(victim_model, train_loader, epochs=5, device=device)
    victim_acc = evaluate_model(victim_model, test_loader, device=device)

    logger.info("[2/4] Creating victim API and substitute model")
    victim_api = VictimAPI(victim_model, device=device)
    substitute = SimpleCNN(num_classes=10, in_channels=in_ch)
    logger.debug(f"Victim API initialized, substitute model created (random weights)")

    logger.info(f"[3/4] Running {args.strategy} extraction attack")
    if args.strategy == "random":
        substitute = random_query_extraction(victim_api, substitute, args.queries,
                                              in_channels=in_ch, img_size=img_size, device=device)
    else:
        substitute = active_learning_extraction(victim_api, substitute, initial_queries=args.queries // 5,
                                                 rounds=5, test_loader=test_loader,
                                                 in_channels=in_ch, img_size=img_size, device=device)

    logger.info("[4/4] Evaluating extraction success")
    fidelity = compute_fidelity(victim_api, substitute, test_loader, device)
    sub_acc = evaluate_model(substitute, test_loader, device=device)

    logger.info(f"Victim accuracy: {victim_acc:.2f}%")
    logger.info(f"Substitute accuracy: {sub_acc:.2f}%")
    logger.info(f"Fidelity (agreement): {fidelity:.2f}%")
    logger.info(f"Total API queries: {victim_api.query_count}")

    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        results = {"experiment": "model_extraction", "timestamp": datetime.now().isoformat(),
                    "strategy": args.strategy, "num_queries": victim_api.query_count,
                    "victim_accuracy": round(victim_acc, 2), "substitute_accuracy": round(sub_acc, 2),
                    "fidelity": round(fidelity, 2)}
        with open(args.output, "w") as f:
            json.dump(results, f, indent=2)
        logger.info(f"Results saved → {args.output}")

    logger.info("=" * 60)
    logger.info("Model extraction test complete")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
