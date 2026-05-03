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


class SimpleCNN(nn.Module):
    """Lightweight CNN for MNIST / CIFAR-10 classification."""

    def __init__(self, num_classes=10, in_channels=1):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(in_channels, 32, 3, padding=1),
            nn.ReLU(),
            nn.Conv2d(32, 64, 3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Dropout(0.25),
        )
        feat_size = 64 * 14 * 14 if in_channels == 1 else 64 * 16 * 16
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(feat_size, 128),
            nn.ReLU(),
            nn.Dropout(0.5),
            nn.Linear(128, num_classes),
        )

    def forward(self, x):
        x = self.features(x)
        return self.classifier(x)


def get_device():
    if torch.cuda.is_available():
        return torch.device("cuda")
    elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def load_dataset(name="mnist", batch_size=64, data_dir="datasets/data"):
    """Load a public dataset for training/testing."""
    Path(data_dir).mkdir(parents=True, exist_ok=True)

    if name == "mnist":
        transform = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize((0.1307,), (0.3081,)),
        ])
        train = datasets.MNIST(data_dir, train=True, download=True, transform=transform)
        test = datasets.MNIST(data_dir, train=False, download=True, transform=transform)
        in_channels = 1
    elif name == "cifar10":
        transform = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize((0.4914, 0.4822, 0.4465), (0.2470, 0.2435, 0.2616)),
        ])
        train = datasets.CIFAR10(data_dir, train=True, download=True, transform=transform)
        test = datasets.CIFAR10(data_dir, train=False, download=True, transform=transform)
        in_channels = 3
    else:
        raise ValueError(f"Unknown dataset: {name}")

    train_loader = DataLoader(train, batch_size=batch_size, shuffle=True)
    test_loader = DataLoader(test, batch_size=batch_size, shuffle=False)
    return train_loader, test_loader, in_channels


def train_model(model, train_loader, epochs=10, lr=0.001, device=None):
    """Train the target model."""
    device = device or get_device()
    model = model.to(device)
    optimizer = optim.Adam(model.parameters(), lr=lr)
    criterion = nn.CrossEntropyLoss()

    model.train()
    for epoch in range(epochs):
        total_loss = 0
        correct = 0
        total = 0
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
        print(f"  Epoch {epoch+1}/{epochs} — Loss: {total_loss/len(train_loader):.4f} | Acc: {acc:.1f}%")

    return model


def evaluate_model(model, test_loader, device=None):
    """Evaluate model accuracy on test set."""
    device = device or get_device()
    model = model.to(device)
    model.eval()
    correct = 0
    total = 0
    with torch.no_grad():
        for data, target in test_loader:
            data, target = data.to(device), target.to(device)
            output = model(data)
            correct += output.argmax(1).eq(target).sum().item()
            total += target.size(0)
    return 100.0 * correct / total


if __name__ == "__main__":
    print("=" * 60)
    print("  BBAP-Sec — Training Target Model")
    print("=" * 60)
    device = get_device()
    print(f"  Device: {device}")

    train_loader, test_loader, in_ch = load_dataset("mnist")
    model = SimpleCNN(num_classes=10, in_channels=in_ch)
    model = train_model(model, train_loader, epochs=5, device=device)

    acc = evaluate_model(model, test_loader, device=device)
    print(f"\n  Clean Test Accuracy: {acc:.2f}%")

    Path("saved_models").mkdir(exist_ok=True)
    torch.save(model.state_dict(), "saved_models/target_mnist_cnn.pt")
    print("  Model saved to saved_models/target_mnist_cnn.pt")
