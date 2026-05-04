"""
BBAP-Sec AI Attack Lab — Target Model
=====================================
Defines target ML models for adversarial testing.
Uses public datasets (MNIST, CIFAR-10) for educational purposes.
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import datasets, transforms
from torch.utils.data import DataLoader
from pathlib import Path

from src.utils.logger import get_logger, get_dataset_dir

logger = get_logger("target_model")


class SimpleCNN(nn.Module):
    """Lightweight CNN for MNIST / CIFAR-10 classification."""

    def __init__(self, num_classes=10, in_channels=1):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(in_channels, 32, 3, padding=1), nn.ReLU(),
            nn.Conv2d(32, 64, 3, padding=1), nn.ReLU(),
            nn.MaxPool2d(2), nn.Dropout(0.25),
        )
        feat_size = 64 * 14 * 14 if in_channels == 1 else 64 * 16 * 16
        self.classifier = nn.Sequential(
            nn.Flatten(), nn.Linear(feat_size, 128), nn.ReLU(),
            nn.Dropout(0.5), nn.Linear(128, num_classes),
        )

    def forward(self, x):
        return self.classifier(self.features(x))


def get_device():
    if torch.cuda.is_available():
        d = torch.device("cuda")
    elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        d = torch.device("mps")
    else:
        d = torch.device("cpu")
    logger.debug(f"Device selected: {d}")
    return d


def load_dataset(name="mnist", batch_size=64, data_dir=None):
    data_dir = data_dir or get_dataset_dir()
    Path(data_dir).mkdir(parents=True, exist_ok=True)
    logger.info(f"Loading dataset: {name} (batch_size={batch_size})")
    logger.debug(f"Data directory: {data_dir}")

    if name == "mnist":
        tx = transforms.Compose([transforms.ToTensor(), transforms.Normalize((0.1307,), (0.3081,))])
        train = datasets.MNIST(data_dir, train=True, download=True, transform=tx)
        test = datasets.MNIST(data_dir, train=False, download=True, transform=tx)
        in_ch = 1
    elif name == "cifar10":
        tx = transforms.Compose([transforms.ToTensor(), transforms.Normalize((0.4914,0.4822,0.4465),(0.2470,0.2435,0.2616))])
        train = datasets.CIFAR10(data_dir, train=True, download=True, transform=tx)
        test = datasets.CIFAR10(data_dir, train=False, download=True, transform=tx)
        in_ch = 3
    else:
        logger.error(f"Unknown dataset: {name}")
        raise ValueError(f"Unknown dataset: {name}")

    train_loader = DataLoader(train, batch_size=batch_size, shuffle=True)
    test_loader = DataLoader(test, batch_size=batch_size, shuffle=False)
    logger.info(f"Dataset ready: {len(train)} train / {len(test)} test samples, {in_ch} channels")
    return train_loader, test_loader, in_ch


def train_model(model, train_loader, epochs=10, lr=0.001, device=None):
    device = device or get_device()
    model = model.to(device)
    optimizer = optim.Adam(model.parameters(), lr=lr)
    criterion = nn.CrossEntropyLoss()
    params = sum(p.numel() for p in model.parameters())
    logger.info(f"Training {model.__class__.__name__} ({params:,} params), epochs={epochs}, lr={lr}")

    model.train()
    for epoch in range(epochs):
        total_loss, correct, total = 0, 0, 0
        for data, target in train_loader:
            data, target = data.to(device), target.to(device)
            optimizer.zero_grad()
            output = model(data)
            loss = criterion(output, target)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
            correct += output.argmax(1).eq(target).sum().item()
            total += target.size(0)
        acc = 100.0 * correct / total
        logger.info(f"  epoch {epoch+1}/{epochs} — loss: {total_loss/len(train_loader):.4f} | accuracy: {acc:.1f}%")

    logger.info("Training complete")
    return model


def evaluate_model(model, test_loader, device=None):
    device = device or get_device()
    model.to(device).eval()
    correct, total = 0, 0
    with torch.no_grad():
        for data, target in test_loader:
            data, target = data.to(device), target.to(device)
            correct += model(data).argmax(1).eq(target).sum().item()
            total += target.size(0)
    acc = 100.0 * correct / total
    logger.info(f"Evaluation accuracy: {acc:.2f}% ({correct}/{total})")
    return acc


if __name__ == "__main__":
    from src.utils.logger import setup_logger, get_project_root
    setup_logger(get_project_root())
    logger.info("=" * 60)
    logger.info("BBAP-Sec — Training Target Model (standalone)")
    logger.info("=" * 60)
    device = get_device()
    train_loader, test_loader, in_ch = load_dataset("mnist")
    model = SimpleCNN(num_classes=10, in_channels=in_ch)
    model = train_model(model, train_loader, epochs=5, device=device)
    evaluate_model(model, test_loader, device=device)
    Path("saved_models").mkdir(exist_ok=True)
    torch.save(model.state_dict(), "saved_models/target_mnist_cnn.pt")
    logger.info("Model saved → saved_models/target_mnist_cnn.pt")
