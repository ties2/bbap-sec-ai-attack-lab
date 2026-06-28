"""
BBAP-Sec — Attack Runner
==========================
Core execution engine that bridges attack modules with target models.
Runs attacks against sandbox containers or external API endpoints,
computes metrics, and returns structured Findings.

Usage:
    runner = AttackRunner(sandbox_manager)
    result = runner.run(
        project_id=1,
        attack_id="fgsm",
        layer="inference",
        target={"type": "sandbox", "sandbox_id": 1},
        params={"epsilon": 0.03, "num_samples": 200}
    )
"""

import time
import uuid
import logging
import numpy as np
from datetime import datetime

logger = logging.getLogger("attacks.runner")


class AttackProgress:
    """Tracks attack execution progress for live UI updates."""

    def __init__(self, attack_id, total_steps=100):
        self.attack_id = attack_id
        self.run_id = str(uuid.uuid4())[:8]
        self.total_steps = total_steps
        self.current_step = 0
        self.status = "queued"          # queued → running → computing → done / failed
        self.message = "Waiting..."
        self.started_at = None
        self.finished_at = None
        self.metrics = {}

    def start(self, message="Starting attack..."):
        self.status = "running"
        self.message = message
        self.started_at = time.time()

    def update(self, step, message=None):
        self.current_step = min(step, self.total_steps)
        if message:
            self.message = message

    def finish(self, metrics, message="Complete"):
        self.status = "done"
        self.message = message
        self.metrics = metrics
        self.current_step = self.total_steps
        self.finished_at = time.time()

    def fail(self, error):
        self.status = "failed"
        self.message = str(error)
        self.finished_at = time.time()

    @property
    def progress_pct(self):
        return round(100 * self.current_step / max(self.total_steps, 1), 1)

    @property
    def elapsed(self):
        if not self.started_at:
            return 0
        end = self.finished_at or time.time()
        return round(end - self.started_at, 2)

    def to_dict(self):
        return {
            "run_id": self.run_id,
            "attack_id": self.attack_id,
            "status": self.status,
            "progress": self.progress_pct,
            "message": self.message,
            "elapsed_seconds": self.elapsed,
            "metrics": self.metrics,
        }


class SandboxTarget:
    """Wraps sandbox API calls into a clean interface for attack modules."""

    def __init__(self, sandbox_manager, sandbox_id):
        self.manager = sandbox_manager
        self.sandbox_id = sandbox_id
        self.query_count = 0

    def predict(self, inputs):
        """Black-box: get class predictions. inputs = list of numpy-like arrays."""
        self.query_count += 1
        result = self.manager.proxy_request(
            self.sandbox_id, "/predict", method="POST",
            data={"input": _to_list(inputs)}
        )
        if "error" in result:
            raise RuntimeError(f"Sandbox predict failed: {result['error']}")
        return result["predictions"]

    def predict_proba(self, inputs):
        """Black-box: get probability distributions."""
        self.query_count += 1
        result = self.manager.proxy_request(
            self.sandbox_id, "/predict_proba", method="POST",
            data={"input": _to_list(inputs)}
        )
        if "error" in result:
            raise RuntimeError(f"Sandbox predict_proba failed: {result['error']}")
        return np.array(result["probabilities"])

    def gradient(self, inputs, target_class=None):
        """White-box: compute input gradients."""
        self.query_count += 1
        data = {"input": _to_list(inputs)}
        if target_class is not None:
            data["target_class"] = int(target_class)
        result = self.manager.proxy_request(
            self.sandbox_id, "/gradient", method="POST", data=data
        )
        if "error" in result:
            raise RuntimeError(f"Sandbox gradient failed: {result['error']}")
        return np.array(result["gradients"])

    def model_info(self):
        """Get model metadata."""
        result = self.manager.proxy_request(self.sandbox_id, "/model_info", method="GET")
        if "error" in result:
            raise RuntimeError(f"Sandbox model_info failed: {result['error']}")
        return result


class APITarget:
    """Wraps an external API endpoint for black-box attacks."""

    def __init__(self, url, auth_headers=None):
        import requests
        self.url = url
        self.session = requests.Session()
        if auth_headers:
            self.session.headers.update({"Authorization": auth_headers})
        self.session.headers.update({"Content-Type": "application/json"})
        self.query_count = 0

    def predict(self, inputs):
        self.query_count += 1
        resp = self.session.post(self.url, json={"input": _to_list(inputs)}, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        return data.get("predictions", data.get("output", data))

    def predict_proba(self, inputs):
        self.query_count += 1
        resp = self.session.post(self.url, json={"input": _to_list(inputs)}, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        probs = data.get("probabilities", data.get("output", data))
        return np.array(probs)

    def gradient(self, inputs, target_class=None):
        raise NotImplementedError("External API does not support gradient access (black-box only)")

    def model_info(self):
        return {"type": "external_api", "url": self.url, "access": "black-box"}


# ── Attack Registry ──

ATTACK_REGISTRY = {}


def register_attack(attack_id, layer, fn):
    """Register an attack function."""
    ATTACK_REGISTRY[attack_id] = {"id": attack_id, "layer": layer, "fn": fn}


class AttackRunner:
    """Main attack execution engine."""

    def __init__(self, sandbox_manager=None):
        self.sandbox_manager = sandbox_manager
        self._active_runs = {}   # run_id → AttackProgress

    def _get_target(self, target_config):
        """Create a target interface from config."""
        if target_config["type"] == "sandbox":
            if not self.sandbox_manager:
                raise RuntimeError("SandboxManager not configured")
            return SandboxTarget(self.sandbox_manager, target_config["sandbox_id"])
        elif target_config["type"] == "api":
            return APITarget(target_config["url"], target_config.get("auth"))
        else:
            raise ValueError(f"Unknown target type: {target_config['type']}")

    def run(self, project_id, attack_id, layer, target_config, params=None):
        """Execute an attack and return a Finding dict.

        Args:
            project_id: ID of the project
            attack_id: Attack identifier (e.g. "fgsm", "extract_random")
            layer: Attack surface layer (e.g. "inference", "artifacts")
            target_config: {"type": "sandbox", "sandbox_id": 1} or {"type": "api", "url": "..."}
            params: Attack-specific parameters (epsilon, num_samples, etc.)

        Returns:
            dict with finding data
        """
        if attack_id not in ATTACK_REGISTRY:
            raise ValueError(f"Unknown attack: {attack_id}. Available: {list(ATTACK_REGISTRY.keys())}")

        attack = ATTACK_REGISTRY[attack_id]
        params = params or {}

        progress = AttackProgress(attack_id)
        self._active_runs[progress.run_id] = progress

        try:
            target = self._get_target(target_config)
            progress.start(f"Running {attack_id}...")

            logger.info(f"Attack started: {attack_id} (run={progress.run_id}, project={project_id})")

            # Execute the attack function
            result = attack["fn"](target, progress, **params)

            progress.finish(result.get("metrics", {}), f"{attack_id} complete")

            # Build Finding
            finding = {
                "id": f"F-{datetime.now().strftime('%y%m%d')}-{progress.run_id}",
                "project_id": project_id,
                "layer": layer,
                "attack": attack_id,
                "severity": _compute_severity(attack_id, result.get("metrics", {})),
                "title": result.get("title", f"{attack_id} attack result"),
                "metrics": result.get("metrics", {}),
                "atlas": result.get("atlas"),
                "related": [],
                "status": "open",
                "run_id": progress.run_id,
                "elapsed_seconds": progress.elapsed,
                "target_queries": getattr(target, "query_count", 0),
                "created_at": datetime.now().isoformat(),
            }

            logger.info(
                f"Attack complete: {attack_id} → severity={finding['severity']}, "
                f"elapsed={progress.elapsed}s, queries={finding['target_queries']}"
            )
            return finding

        except Exception as e:
            progress.fail(str(e))
            logger.error(f"Attack failed: {attack_id} — {e}")
            return {
                "id": f"F-{datetime.now().strftime('%y%m%d')}-{progress.run_id}",
                "project_id": project_id,
                "layer": layer,
                "attack": attack_id,
                "severity": "info",
                "title": f"{attack_id} failed: {str(e)}",
                "metrics": {},
                "status": "error",
                "error": str(e),
                "run_id": progress.run_id,
                "created_at": datetime.now().isoformat(),
            }

    def get_progress(self, run_id):
        """Get current progress of a running attack."""
        prog = self._active_runs.get(run_id)
        return prog.to_dict() if prog else None

    def list_active(self):
        """List all active attack runs."""
        return [p.to_dict() for p in self._active_runs.values()
                if p.status in ("queued", "running", "computing")]


# ── Helpers ──

def _to_list(data):
    """Convert numpy arrays to nested lists for JSON serialization."""
    if isinstance(data, np.ndarray):
        return data.tolist()
    if isinstance(data, list) and len(data) > 0 and isinstance(data[0], np.ndarray):
        return [x.tolist() for x in data]
    return data


def _compute_severity(attack_id, metrics):
    """Compute finding severity from attack metrics."""
    # Adversarial attacks
    if "accuracy_drop" in metrics:
        drop = metrics["accuracy_drop"]
        if drop >= 60:
            return "critical"
        if drop >= 30:
            return "high"
        if drop >= 10:
            return "medium"
        return "low"

    # Evasion
    if "evasion_rate" in metrics:
        rate = metrics["evasion_rate"]
        if rate >= 50:
            return "high"
        if rate >= 20:
            return "medium"
        return "low"

    # Model extraction
    if "fidelity" in metrics:
        fid = metrics["fidelity"]
        if fid >= 90:
            return "critical"
        if fid >= 70:
            return "high"
        if fid >= 40:
            return "medium"
        return "low"

    # Prompt injection
    if "injection_asr" in metrics:
        asr = metrics["injection_asr"]
        if asr >= 50:
            return "critical"
        if asr >= 30:
            return "high"
        if asr >= 10:
            return "medium"
        return "low"

    # Backdoor
    if "backdoor_asr" in metrics:
        asr = metrics["backdoor_asr"]
        if asr >= 80:
            return "critical"
        if asr >= 50:
            return "high"
        return "medium"

    return "medium"
