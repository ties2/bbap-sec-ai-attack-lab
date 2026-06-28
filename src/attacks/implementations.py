"""
BBAP-Sec — Attack Implementations
====================================
Each attack function receives a target (SandboxTarget or APITarget),
a progress tracker, and attack-specific params.
Returns a dict with {title, metrics, atlas}.

All attacks work through the target abstraction:
  - target.predict(inputs)        → class labels (black-box)
  - target.predict_proba(inputs)  → probabilities (black-box)
  - target.gradient(inputs)       → input gradients (white-box, sandbox only)
"""

import numpy as np
import logging

from .runner import register_attack, ATTACK_REGISTRY

logger = logging.getLogger("attacks.impl")


# ═══════════════════════════════════
#  INFERENCE PHASE — Adversarial
# ═══════════════════════════════════

def attack_fgsm(target, progress, epsilon=0.03, num_samples=200, input_shape=None):
    """Fast Gradient Sign Method — white-box adversarial attack."""
    shape = input_shape or [1, 28, 28]
    batch_size = min(50, num_samples)
    total_batches = (num_samples + batch_size - 1) // batch_size

    progress.update(0, f"FGSM ε={epsilon} — generating {num_samples} samples")

    clean_correct = 0
    adv_correct = 0
    total = 0

    for batch_idx in range(total_batches):
        n = min(batch_size, num_samples - total)
        images = np.random.rand(n, *shape).astype(np.float32)

        # Get clean predictions
        clean_preds = target.predict(images)
        labels = clean_preds  # Use clean predictions as ground truth

        # Compute gradients w.r.t. each sample's predicted class
        adv_images = images.copy()
        for i in range(n):
            grad = target.gradient(images[i:i+1], target_class=int(labels[i]))
            perturbation = epsilon * np.sign(grad)
            adv_images[i] = np.clip(images[i] + perturbation, 0, 1)

        # Get adversarial predictions
        adv_preds = target.predict(adv_images)

        # Count
        for i in range(n):
            clean_correct += 1  # By definition (we used clean preds as labels)
            if adv_preds[i] == labels[i]:
                adv_correct += 1
        total += n

        progress.update(
            int((batch_idx + 1) / total_batches * 90),
            f"Batch {batch_idx+1}/{total_batches} — ASR: {100*(1 - adv_correct/total):.1f}%"
        )

    clean_acc = 100.0 * clean_correct / total
    adv_acc = 100.0 * adv_correct / total
    drop = clean_acc - adv_acc
    asr = 100.0 - adv_acc

    progress.update(95, "Computing final metrics")

    return {
        "title": f"FGSM at ε={epsilon}: accuracy drops {drop:.1f}%",
        "atlas": "AML.T0043.001",
        "metrics": {
            "epsilon": epsilon,
            "clean_accuracy": round(clean_acc, 2),
            "adversarial_accuracy": round(adv_acc, 2),
            "accuracy_drop": round(drop, 2),
            "attack_success_rate": round(asr, 2),
            "total_samples": total,
            "queries": target.query_count,
        }
    }


def attack_pgd(target, progress, epsilon=0.03, alpha=None, num_steps=20,
               num_samples=100, input_shape=None):
    """Projected Gradient Descent — iterative white-box attack."""
    shape = input_shape or [1, 28, 28]
    alpha = alpha or epsilon / 4
    batch_size = min(20, num_samples)
    total_batches = (num_samples + batch_size - 1) // batch_size

    progress.update(0, f"PGD ε={epsilon}, α={alpha:.4f}, steps={num_steps}")

    clean_correct = 0
    adv_correct = 0
    total = 0

    for batch_idx in range(total_batches):
        n = min(batch_size, num_samples - total)
        images = np.random.rand(n, *shape).astype(np.float32)
        clean_preds = target.predict(images)
        labels = clean_preds

        # PGD for each sample
        adv_images = images.copy()
        # Random start
        adv_images = adv_images + np.random.uniform(-epsilon, epsilon, adv_images.shape).astype(np.float32)
        adv_images = np.clip(adv_images, 0, 1)

        for step in range(num_steps):
            for i in range(n):
                grad = target.gradient(adv_images[i:i+1], target_class=int(labels[i]))
                adv_images[i] = adv_images[i] + alpha * np.sign(grad[0])
                # Project back to epsilon ball
                perturbation = np.clip(adv_images[i] - images[i], -epsilon, epsilon)
                adv_images[i] = np.clip(images[i] + perturbation, 0, 1)

            step_pct = (batch_idx * num_steps + step + 1) / (total_batches * num_steps)
            if (step + 1) % 5 == 0:
                progress.update(int(step_pct * 90), f"PGD step {step+1}/{num_steps}, batch {batch_idx+1}")

        adv_preds = target.predict(adv_images)
        for i in range(n):
            clean_correct += 1
            if adv_preds[i] == labels[i]:
                adv_correct += 1
        total += n

    clean_acc = 100.0 * clean_correct / total
    adv_acc = 100.0 * adv_correct / total

    return {
        "title": f"PGD at ε={epsilon}: accuracy drops {clean_acc - adv_acc:.1f}%",
        "atlas": "AML.T0043.001",
        "metrics": {
            "epsilon": epsilon,
            "alpha": round(alpha, 4),
            "num_steps": num_steps,
            "clean_accuracy": round(clean_acc, 2),
            "adversarial_accuracy": round(adv_acc, 2),
            "accuracy_drop": round(clean_acc - adv_acc, 2),
            "attack_success_rate": round(100.0 - adv_acc, 2),
            "total_samples": total,
            "queries": target.query_count,
        }
    }


# ═══════════════════════════════════
#  INFERENCE PHASE — Evasion
# ═══════════════════════════════════

def attack_evasion_pixel(target, progress, max_pixels=10, num_samples=200, input_shape=None):
    """Pixel perturbation evasion — flips random pixels to change prediction."""
    shape = input_shape or [1, 28, 28]
    batch_size = min(50, num_samples)
    total_batches = (num_samples + batch_size - 1) // batch_size

    progress.update(0, f"Pixel evasion — max_pixels={max_pixels}")

    evaded = 0
    total = 0

    for batch_idx in range(total_batches):
        n = min(batch_size, num_samples - total)
        images = np.random.rand(n, *shape).astype(np.float32)
        orig_preds = target.predict(images)

        modified = images.copy()
        for i in range(n):
            for _ in range(max_pixels):
                c = np.random.randint(0, shape[0])
                px = np.random.randint(0, shape[1])
                py = np.random.randint(0, shape[2])
                modified[i, c, px, py] = 1.0 - modified[i, c, px, py]

        mod_preds = target.predict(modified)
        for i in range(n):
            if mod_preds[i] != orig_preds[i]:
                evaded += 1
        total += n

        progress.update(
            int((batch_idx + 1) / total_batches * 90),
            f"Batch {batch_idx+1}/{total_batches} — evasion rate: {100*evaded/total:.1f}%"
        )

    rate = 100.0 * evaded / total

    return {
        "title": f"Pixel evasion: {rate:.1f}% evasion rate ({max_pixels} pixels)",
        "atlas": "AML.T0047",
        "metrics": {
            "evasion_rate": round(rate, 2),
            "max_pixels": max_pixels,
            "total_samples": total,
            "evaded": evaded,
            "queries": target.query_count,
        }
    }


def attack_evasion_noise(target, progress, noise_std=0.1, num_samples=200, input_shape=None):
    """Gaussian noise evasion — adds random noise to change prediction."""
    shape = input_shape or [1, 28, 28]
    batch_size = min(50, num_samples)
    total_batches = (num_samples + batch_size - 1) // batch_size

    progress.update(0, f"Noise evasion — std={noise_std}")

    evaded = 0
    total = 0

    for batch_idx in range(total_batches):
        n = min(batch_size, num_samples - total)
        images = np.random.rand(n, *shape).astype(np.float32)
        orig_preds = target.predict(images)

        noisy = np.clip(images + np.random.randn(*images.shape).astype(np.float32) * noise_std, 0, 1)
        noisy_preds = target.predict(noisy)

        for i in range(n):
            if noisy_preds[i] != orig_preds[i]:
                evaded += 1
        total += n

        progress.update(int((batch_idx + 1) / total_batches * 90))

    rate = 100.0 * evaded / total

    return {
        "title": f"Noise evasion: {rate:.1f}% evasion rate (σ={noise_std})",
        "atlas": "AML.T0047",
        "metrics": {
            "evasion_rate": round(rate, 2),
            "noise_std": noise_std,
            "total_samples": total,
            "evaded": evaded,
            "queries": target.query_count,
        }
    }


def attack_evasion_spatial(target, progress, max_rotation=15, num_samples=200, input_shape=None):
    """Spatial transform evasion — rotates images to change prediction."""
    shape = input_shape or [1, 28, 28]

    progress.update(0, f"Spatial evasion — max_rotation={max_rotation}°")

    evaded = 0
    total = 0
    batch_size = min(50, num_samples)

    for batch_start in range(0, num_samples, batch_size):
        n = min(batch_size, num_samples - batch_start)
        images = np.random.rand(n, *shape).astype(np.float32)
        orig_preds = target.predict(images)

        # Simple rotation via numpy (shift rows/cols)
        rotated = images.copy()
        for i in range(n):
            shift = np.random.randint(-3, 4)
            for c in range(shape[0]):
                rotated[i, c] = np.roll(rotated[i, c], shift, axis=0)
                rotated[i, c] = np.roll(rotated[i, c], np.random.randint(-3, 4), axis=1)

        rot_preds = target.predict(rotated)
        for i in range(n):
            if rot_preds[i] != orig_preds[i]:
                evaded += 1
        total += n

        progress.update(int((batch_start + n) / num_samples * 90))

    rate = 100.0 * evaded / total

    return {
        "title": f"Spatial evasion: {rate:.1f}% evasion rate (±{max_rotation}°)",
        "atlas": "AML.T0047.003",
        "metrics": {
            "evasion_rate": round(rate, 2),
            "max_rotation": max_rotation,
            "total_samples": total,
            "evaded": evaded,
            "queries": target.query_count,
        }
    }


# ═══════════════════════════════════
#  MODEL ARTIFACTS — Extraction
# ═══════════════════════════════════

def attack_extract_random(target, progress, num_queries=1000, num_classes=10, input_shape=None):
    """Model extraction via random queries — trains a substitute model."""
    shape = input_shape or [1, 28, 28]
    batch_size = 64

    progress.update(0, f"Random extraction — {num_queries} queries")

    # Collect query-response pairs
    all_inputs = []
    all_labels = []
    queries_sent = 0

    for batch_start in range(0, num_queries, batch_size):
        n = min(batch_size, num_queries - batch_start)
        queries = np.random.rand(n, *shape).astype(np.float32)
        labels = target.predict(queries)

        all_inputs.append(queries)
        all_labels.extend(labels)
        queries_sent += n

        progress.update(
            int(queries_sent / num_queries * 60),
            f"Querying: {queries_sent}/{num_queries}"
        )

    progress.update(65, "Training substitute model...")

    # Train a simple substitute (using numpy — no torch dependency in runner)
    # We measure fidelity by testing agreement on held-out queries
    test_queries = np.random.rand(200, *shape).astype(np.float32)
    victim_preds = target.predict(test_queries)

    # Simple nearest-neighbor substitute for fidelity measurement
    all_inputs_flat = np.concatenate(all_inputs).reshape(queries_sent, -1)
    test_flat = test_queries.reshape(200, -1)

    progress.update(80, "Computing fidelity...")

    agree = 0
    for i in range(200):
        # Find nearest training query
        dists = np.sum((all_inputs_flat - test_flat[i]) ** 2, axis=1)
        nearest_idx = np.argmin(dists)
        sub_pred = all_labels[nearest_idx]
        if sub_pred == victim_preds[i]:
            agree += 1

    fidelity = 100.0 * agree / 200

    # Random baseline accuracy
    victim_test_preds = target.predict(test_queries)
    sub_correct = sum(1 for i in range(200) if all_labels[np.argmin(
        np.sum((all_inputs_flat - test_flat[i]) ** 2, axis=1)
    )] == victim_test_preds[i])
    substitute_acc = 100.0 * sub_correct / 200

    return {
        "title": f"Model extracted with {fidelity:.1f}% fidelity ({queries_sent} queries)",
        "atlas": "AML.T0044",
        "metrics": {
            "fidelity": round(fidelity, 2),
            "num_queries": queries_sent,
            "substitute_accuracy": round(substitute_acc, 2),
            "test_samples": 200,
            "queries": target.query_count,
        }
    }


def attack_extract_active(target, progress, initial_queries=200, rounds=5,
                          num_classes=10, input_shape=None):
    """Model extraction via active learning — iteratively refines substitute."""
    shape = input_shape or [1, 28, 28]

    progress.update(0, f"Active extraction — {initial_queries} seed, {rounds} rounds")

    # Seed queries
    synthetic = np.random.rand(initial_queries, *shape).astype(np.float32)
    labels = list(target.predict(synthetic))
    queries_used = initial_queries

    progress.update(10, f"Seed complete: {queries_used} queries")

    for rnd in range(rounds):
        # Augment: add noise to existing queries
        augmented = np.clip(
            synthetic + 0.1 * np.sign(np.random.randn(*synthetic.shape)).astype(np.float32),
            0, 1
        )
        aug_labels = target.predict(augmented)
        synthetic = np.concatenate([synthetic, augmented])
        labels.extend(aug_labels)
        queries_used += len(augmented)

        progress.update(
            10 + int((rnd + 1) / rounds * 60),
            f"Round {rnd+1}/{rounds} — {queries_used} queries"
        )

    # Compute fidelity
    progress.update(80, "Computing fidelity...")
    test = np.random.rand(200, *shape).astype(np.float32)
    victim_preds = target.predict(test)

    syn_flat = synthetic.reshape(len(synthetic), -1)
    test_flat = test.reshape(200, -1)

    agree = 0
    for i in range(200):
        dists = np.sum((syn_flat - test_flat[i]) ** 2, axis=1)
        nearest = np.argmin(dists)
        if labels[nearest] == victim_preds[i]:
            agree += 1

    fidelity = 100.0 * agree / 200

    return {
        "title": f"Active extraction: {fidelity:.1f}% fidelity ({queries_used} queries, {rounds} rounds)",
        "atlas": "AML.T0044",
        "metrics": {
            "fidelity": round(fidelity, 2),
            "num_queries": queries_used,
            "rounds": rounds,
            "dataset_size": len(synthetic),
            "queries": target.query_count,
        }
    }


# ═══════════════════════════════════
#  INFRASTRUCTURE — API Security
# ═══════════════════════════════════

def attack_rate_limit(target, progress, burst_size=100, delay_ms=0):
    """Rate limit bypass — rapid-fire queries to test throttling."""
    import time as _time

    progress.update(0, f"Rate limit test — {burst_size} rapid queries")

    successful = 0
    blocked = 0
    latencies = []

    for i in range(burst_size):
        try:
            start = _time.time()
            dummy = np.random.rand(1, 1, 28, 28).astype(np.float32)
            target.predict(dummy)
            latencies.append((_time.time() - start) * 1000)
            successful += 1
        except Exception:
            blocked += 1

        if delay_ms > 0:
            _time.sleep(delay_ms / 1000)

        progress.update(int((i + 1) / burst_size * 90))

    avg_latency = round(np.mean(latencies), 1) if latencies else 0
    p95_latency = round(np.percentile(latencies, 95), 1) if len(latencies) > 5 else avg_latency

    return {
        "title": f"Rate limit: {successful}/{burst_size} queries succeeded ({blocked} blocked)",
        "atlas": "AML.T0005",
        "metrics": {
            "burst_size": burst_size,
            "successful": successful,
            "blocked": blocked,
            "block_rate": round(100.0 * blocked / burst_size, 1),
            "avg_latency_ms": avg_latency,
            "p95_latency_ms": p95_latency,
            "queries": target.query_count,
        }
    }


# ═══════════════════════════════════
#  REGISTER ALL ATTACKS
# ═══════════════════════════════════

def register_all():
    """Register all attack implementations."""
    # Inference phase
    register_attack("fgsm",            "inference",  attack_fgsm)
    register_attack("pgd",             "inference",  attack_pgd)
    register_attack("evasion_pixel",   "inference",  attack_evasion_pixel)
    register_attack("evasion_noise",   "inference",  attack_evasion_noise)
    register_attack("evasion_spatial", "inference",  attack_evasion_spatial)

    # Model artifacts
    register_attack("extract_random",  "artifacts",  attack_extract_random)
    register_attack("extract_active",  "artifacts",  attack_extract_active)

    # Infrastructure
    register_attack("rate_limit",      "infra",      attack_rate_limit)

    logger.info(f"Registered {len(ATTACK_REGISTRY)} attacks")


# Auto-register on import
register_all()
