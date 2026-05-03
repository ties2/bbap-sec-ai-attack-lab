"""
BBAP-Sec AI Attack Lab — Dataset Downloader
============================================
Downloads public datasets used in the attack lab.
All datasets are freely available for research/educational use.
"""

import os
from pathlib import Path


def download_all(data_dir="datasets/data"):
    Path(data_dir).mkdir(parents=True, exist_ok=True)
    print("=" * 50)
    print("  BBAP-Sec — Downloading Public Datasets")
    print("=" * 50)

    # MNIST and CIFAR-10 are handled by torchvision on first use
    try:
        from torchvision import datasets
        print("\n  [1/2] Downloading MNIST...")
        datasets.MNIST(data_dir, train=True, download=True)
        print("    Done.")

        print("  [2/2] Downloading CIFAR-10...")
        datasets.CIFAR10(data_dir, train=True, download=True)
        print("    Done.")
    except ImportError:
        print("  torchvision not installed. Install requirements first:")
        print("    pip install -r requirements.txt")
        return

    print(f"\n  All datasets saved to: {data_dir}/")
    print("=" * 50)


if __name__ == "__main__":
    download_all()
