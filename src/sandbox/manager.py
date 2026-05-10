"""
BBAP-Sec Sandbox — Container Manager
======================================
Manages sandbox Docker containers via the Docker SDK.
Each engagement can have one active sandbox.

Usage:
    manager = SandboxManager()
    sandbox = manager.create(engagement_id, model_path, framework="pytorch")
    status  = manager.status(sandbox_id)
    manager.destroy(sandbox_id)
"""

import os
import time
import json
import logging
import shutil
import requests
from pathlib import Path
from datetime import datetime

logger = logging.getLogger("sandbox.manager")

# Try Docker SDK — gracefully degrade if not installed
try:
    import docker
    DOCKER_AVAILABLE = True
except ImportError:
    DOCKER_AVAILABLE = False
    logger.warning("Docker SDK not installed. Install with: pip install docker")


# ── Configuration ──
SANDBOX_IMAGE = os.environ.get("SANDBOX_IMAGE", "bbap-sec-sandbox:latest")
SANDBOX_NETWORK = os.environ.get("SANDBOX_NETWORK", "bbap-sec-sandbox-net")
MODEL_UPLOAD_DIR = os.environ.get("MODEL_UPLOAD_DIR", "/tmp/bbap-sec-models")
SANDBOX_PORT_RANGE_START = int(os.environ.get("SANDBOX_PORT_START", "5100"))
SANDBOX_PORT_RANGE_END = int(os.environ.get("SANDBOX_PORT_END", "5200"))
SANDBOX_TIMEOUT = int(os.environ.get("SANDBOX_TIMEOUT", "3600"))      # 1 hour default
SANDBOX_MEMORY_LIMIT = os.environ.get("SANDBOX_MEMORY_LIMIT", "4g")
SANDBOX_CPU_LIMIT = float(os.environ.get("SANDBOX_CPU_LIMIT", "2.0"))  # CPU cores


class SandboxInfo:
    """Holds sandbox state and metadata."""

    def __init__(self, sandbox_id, project_id, container_id, port,
                 framework, model_filename, model_size, gpu_enabled=False):
        self.id = sandbox_id
        self.project_id = project_id
        self.container_id = container_id
        self.port = port
        self.framework = framework
        self.model_filename = model_filename
        self.model_size = model_size
        self.gpu_enabled = gpu_enabled
        self.status = "creating"
        self.created_at = datetime.now().isoformat()
        self.destroyed_at = None
        self.error = None

    def to_dict(self):
        return {
            "id": self.id,
            "project_id": self.project_id,
            "container_id": self.container_id[:12] if self.container_id else None,
            "port": self.port,
            "framework": self.framework,
            "model_filename": self.model_filename,
            "model_size_bytes": self.model_size,
            "gpu_enabled": self.gpu_enabled,
            "status": self.status,
            "created_at": self.created_at,
            "destroyed_at": self.destroyed_at,
            "api_url": f"http://localhost:{self.port}" if self.status == "running" else None,
            "error": self.error,
        }


class SandboxManager:
    """Manages sandbox Docker containers."""

    def __init__(self, db=None):
        self.db = db
        self._sandboxes = {}   # in-memory cache: sandbox_id → SandboxInfo
        self._next_id = 1
        self._client = None

        if DOCKER_AVAILABLE:
            try:
                self._client = docker.from_env()
                self._client.ping()
                logger.info("Docker client connected")
                self._ensure_network()
                self._ensure_image()
            except Exception as e:
                logger.error(f"Docker connection failed: {e}")
                self._client = None

        # Ensure upload directory exists
        Path(MODEL_UPLOAD_DIR).mkdir(parents=True, exist_ok=True)

    def _ensure_network(self):
        """Create the sandbox network if it doesn't exist."""
        try:
            self._client.networks.get(SANDBOX_NETWORK)
        except docker.errors.NotFound:
            self._client.networks.create(
                SANDBOX_NETWORK,
                driver="bridge",
                internal=True,  # No external internet access
            )
            logger.info(f"Created sandbox network: {SANDBOX_NETWORK} (internal, no egress)")

    def _ensure_image(self):
        """Check if sandbox image exists, warn if not."""
        try:
            self._client.images.get(SANDBOX_IMAGE)
            logger.info(f"Sandbox image found: {SANDBOX_IMAGE}")
        except docker.errors.ImageNotFound:
            logger.warning(
                f"Sandbox image '{SANDBOX_IMAGE}' not found. "
                f"Build it with: cd sandbox && docker build -t {SANDBOX_IMAGE} ."
            )

    def _find_free_port(self):
        """Find an available port in the sandbox range."""
        used_ports = {s.port for s in self._sandboxes.values() if s.status == "running"}
        for port in range(SANDBOX_PORT_RANGE_START, SANDBOX_PORT_RANGE_END):
            if port not in used_ports:
                return port
        raise RuntimeError("No free ports in sandbox range")

    def create(self, project_id, model_path, framework=None, gpu=False):
        """Create a new sandbox container.

        Args:
            engagement_id: ID of the engagement this sandbox belongs to
            model_path: Path to the uploaded model file
            framework: Override auto-detection (pytorch, onnx, tensorflow, sklearn)
            gpu: Enable GPU passthrough

        Returns:
            SandboxInfo dict
        """
        if not self._client:
            raise RuntimeError("Docker is not available. Install Docker and the Docker SDK.")

        # Validate model file
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found: {model_path}")

        model_filename = os.path.basename(model_path)
        model_size = os.path.getsize(model_path)

        # Auto-detect framework if not provided
        if framework is None:
            from sandbox.model_loader import detect_framework
            framework = detect_framework(model_filename)

        # Copy model to a dedicated directory for this sandbox
        sandbox_id = self._next_id
        self._next_id += 1
        model_dir = os.path.join(MODEL_UPLOAD_DIR, f"sandbox-{sandbox_id}")
        Path(model_dir).mkdir(parents=True, exist_ok=True)
        dest_path = os.path.join(model_dir, model_filename)
        shutil.copy2(model_path, dest_path)

        port = self._find_free_port()

        sandbox_info = SandboxInfo(
            sandbox_id=sandbox_id,
            project_id=project_id,
            container_id=None,
            port=port,
            framework=framework,
            model_filename=model_filename,
            model_size=model_size,
            gpu_enabled=gpu,
        )

        try:
            # Container configuration
            container_config = {
                "image": SANDBOX_IMAGE,
                "name": f"bbap-sbx-{sandbox_id:03d}",
                "detach": True,
                "ports": {"5000/tcp": ('127.0.0.1', port)},
                "volumes": {
                    os.path.abspath(model_dir): {
                        "bind": "/model",
                        "mode": "ro",   # Read-only model access
                    }
                },
                "environment": {
                    "MODEL_FILE": model_filename,
                    "DEVICE": "cuda" if gpu else "cpu",
                    "PORT": "5000",
                    "MAX_BATCH_SIZE": "128",
                },
                "mem_limit": SANDBOX_MEMORY_LIMIT,
                "nano_cpus": int(SANDBOX_CPU_LIMIT * 1e9),
                # "network": SANDBOX_NETWORK,
                "labels": {
                    "bbap-sec": "sandbox",
                    "project_id": str(project_id),
                    "sandbox_id": str(sandbox_id),
                },
            }

            # GPU support via NVIDIA runtime
            if gpu:
                container_config["runtime"] = "nvidia"
                container_config["environment"]["NVIDIA_VISIBLE_DEVICES"] = "all"

            container = self._client.containers.run(**container_config)

            sandbox_info.container_id = container.id
            sandbox_info.status = "starting"

            logger.info(
                f"Sandbox created: id={sandbox_id}, container={container.short_id}, "
                f"port={port}, framework={framework}, model={model_filename}"
            )

            # Wait for container to be healthy (up to 30 seconds)
            for attempt in range(15):
                time.sleep(2)
                container.reload()
                if container.status == "running":
                    try:
                        resp = requests.get(f"http://localhost:{port}/health", timeout=3)
                        if resp.status_code == 200:
                            sandbox_info.status = "running"
                            logger.info(f"Sandbox {sandbox_id} is healthy")
                            break
                    except requests.ConnectionError:
                        pass
                elif container.status in ("exited", "dead"):
                    logs = container.logs(tail=20).decode()
                    sandbox_info.status = "failed"
                    sandbox_info.error = f"Container exited: {logs[-500:]}"
                    logger.error(f"Sandbox {sandbox_id} failed: {logs[-200:]}")
                    break

            if sandbox_info.status == "starting":
                sandbox_info.status = "running"  # Assume OK if container is still up

        except Exception as e:
            sandbox_info.status = "failed"
            sandbox_info.error = str(e)
            logger.error(f"Sandbox creation failed: {e}")
            # Clean up model directory on failure
            shutil.rmtree(model_dir, ignore_errors=True)

        self._sandboxes[sandbox_id] = sandbox_info

        # Persist to DB if available
        if self.db:
            self.db.save_sandbox(sandbox_info.to_dict())

        return sandbox_info.to_dict()

    def status(self, sandbox_id):
        """Get sandbox status."""
        info = self._sandboxes.get(sandbox_id)
        if not info:
            return None

        # Refresh container status from Docker
        if self._client and info.container_id and info.status == "running":
            try:
                container = self._client.containers.get(info.container_id)
                if container.status != "running":
                    info.status = "stopped"
                else:
                    # Also check API health
                    try:
                        resp = requests.get(f"http://localhost:{info.port}/stats", timeout=3)
                        stats = resp.json()
                        result = info.to_dict()
                        result["api_stats"] = stats
                        return result
                    except Exception:
                        pass
            except docker.errors.NotFound:
                info.status = "destroyed"
            except Exception as e:
                logger.warning(f"Status check failed for sandbox {sandbox_id}: {e}")

        return info.to_dict()

    def destroy(self, sandbox_id):
        """Stop and remove a sandbox container."""
        info = self._sandboxes.get(sandbox_id)
        if not info:
            return {"error": "Sandbox not found"}

        if self._client and info.container_id:
            try:
                container = self._client.containers.get(info.container_id)
                container.stop(timeout=10)
                container.remove(force=True)
                logger.info(f"Sandbox {sandbox_id} container destroyed")
            except docker.errors.NotFound:
                logger.info(f"Sandbox {sandbox_id} container already gone")
            except Exception as e:
                logger.error(f"Error destroying sandbox {sandbox_id}: {e}")

        # Clean up model directory
        model_dir = os.path.join(MODEL_UPLOAD_DIR, f"sandbox-{sandbox_id}")
        shutil.rmtree(model_dir, ignore_errors=True)

        info.status = "destroyed"
        info.destroyed_at = datetime.now().isoformat()

        if self.db:
            self.db.update_sandbox_status(sandbox_id, "destroyed")

        return info.to_dict()

    def list_sandboxes(self, project_id=None):
        """List all sandboxes, optionally filtered by engagement."""
        sandboxes = list(self._sandboxes.values())
        if project_id is not None:
            sandboxes = [s for s in sandboxes if s.project_id == project_id]
        return [s.to_dict() for s in sandboxes]

    def cleanup_expired(self):
        """Destroy sandboxes that exceeded their timeout."""
        now = time.time()
        destroyed = 0
        for sid, info in list(self._sandboxes.items()):
            if info.status == "running":
                created = datetime.fromisoformat(info.created_at).timestamp()
                if now - created > SANDBOX_TIMEOUT:
                    logger.info(f"Sandbox {sid} expired (timeout={SANDBOX_TIMEOUT}s)")
                    self.destroy(sid)
                    destroyed += 1
        return destroyed

    def proxy_request(self, sandbox_id, endpoint, method="GET", data=None):
        """Forward a request to a sandbox's internal API.

        This is the primary way attack modules interact with sandboxed models —
        they call this proxy rather than connecting directly to the container port.
        """
        info = self._sandboxes.get(sandbox_id)
        if not info or info.status != "running":
            return {"error": f"Sandbox {sandbox_id} is not running"}

        url = f"http://localhost:{info.port}/{endpoint.lstrip('/')}"
        try:
            if method == "GET":
                resp = requests.get(url, timeout=30)
            else:
                resp = requests.post(url, json=data, timeout=60)
            return resp.json()
        except requests.ConnectionError:
            return {"error": f"Sandbox {sandbox_id} is not reachable"}
        except requests.Timeout:
            return {"error": f"Sandbox {sandbox_id} request timed out"}
        except Exception as e:
            return {"error": str(e)}
