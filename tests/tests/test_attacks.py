"""
BBAP-Sec AI Attack Lab — Unit Tests
====================================
"""

import pytest
import torch
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.models.target_model import SimpleCNN
from src.attacks.adversarial import fgsm_attack, pgd_attack
from src.utils.metrics import attack_success_rate, perturbation_magnitude


@pytest.fixture
def simple_model():
    model = SimpleCNN(num_classes=10, in_channels=1)
    model.eval()
    return model


@pytest.fixture
def sample_batch():
    images = torch.rand(8, 1, 28, 28)
    labels = torch.randint(0, 10, (8,))
    return images, labels


class TestFGSM:
    def test_output_shape(self, simple_model, sample_batch):
        images, labels = sample_batch
        adv = fgsm_attack(simple_model, images, labels, epsilon=0.1)
        assert adv.shape == images.shape

    def test_perturbation_bound(self, simple_model, sample_batch):
        images, labels = sample_batch
        eps = 0.1
        adv = fgsm_attack(simple_model, images, labels, epsilon=eps)
        diff = (adv - images).abs().max().item()
        assert diff <= eps + 1e-6

    def test_clipped_to_valid_range(self, simple_model, sample_batch):
        images, labels = sample_batch
        adv = fgsm_attack(simple_model, images, labels, epsilon=0.5)
        assert adv.min() >= 0.0
        assert adv.max() <= 1.0


class TestPGD:
    def test_output_shape(self, simple_model, sample_batch):
        images, labels = sample_batch
        adv = pgd_attack(simple_model, images, labels, epsilon=0.1, alpha=0.025, num_steps=5)
        assert adv.shape == images.shape

    def test_perturbation_bound(self, simple_model, sample_batch):
        images, labels = sample_batch
        eps = 0.1
        adv = pgd_attack(simple_model, images, labels, epsilon=eps, alpha=0.025, num_steps=10)
        diff = (adv - images).abs().max().item()
        assert diff <= eps + 1e-6


class TestMetrics:
    def test_asr_calculation(self):
        orig = torch.tensor([0, 1, 2, 3, 4])
        adv = torch.tensor([0, 5, 2, 6, 4])
        true = torch.tensor([0, 1, 2, 3, 4])
        asr = attack_success_rate(orig, adv, true)
        assert asr == 2.0 / 5.0  # 2 out of 5 misclassified

    def test_perturbation_linf(self):
        a = torch.zeros(2, 1, 4, 4)
        b = torch.ones(2, 1, 4, 4) * 0.5
        mag = perturbation_magnitude(a, b, norm="linf")
        assert abs(mag - 0.5) < 1e-6


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
