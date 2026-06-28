"""
BBAP-Sec — Attack Execution API Routes
========================================
REST endpoints for running attacks and tracking progress.

Mount on the main Flask app with:
    from webapp.routes_attacks import attacks_bp, init_attack_runner
    init_attack_runner(sandbox_manager)
    app.register_blueprint(attacks_bp)
"""

import logging
import threading
from flask import Blueprint, request, jsonify, g
from src.attacks.runner import AttackRunner, ATTACK_REGISTRY
from webapp.auth import login_required, role_required
from webapp.security import audit_log


logger = logging.getLogger("webapp.attacks")

attacks_bp = Blueprint("attacks", __name__, url_prefix="/api/v2/attacks")

_runner = None
_results_store = {}  # run_id → finding dict (in-memory, replace with DB in Phase 2)


def init_attack_runner(sandbox_manager=None):
    """Initialize the attack runner with the sandbox manager."""
    global _runner
    _runner = AttackRunner(sandbox_manager=sandbox_manager)
    logger.info("Attack runner initialized")


def get_runner():
    global _runner
    if _runner is None:
        _runner = AttackRunner()
    return _runner


@attacks_bp.route("/list", methods=["GET"])
def list_attacks():
    """List all registered attacks."""
    attacks = []
    for attack_id, info in ATTACK_REGISTRY.items():
        attacks.append({
            "id": attack_id,
            "layer": info["layer"],
        })
    return jsonify({"attacks": attacks, "total": len(attacks)})


@attacks_bp.route("/run", methods=["POST"])
@login_required
def run_attack():
    """Execute an attack.

    Body:
    {
        "project_id": 1,
        "attack_id": "fgsm",
        "layer": "inference",
        "target": {
            "type": "sandbox",
            "sandbox_id": 1
        },
        "params": {
            "epsilon": 0.03,
            "num_samples": 200,
            "input_shape": [1, 28, 28]
        }
    }
    """
    runner = get_runner()
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body required"}), 400

    project_id = data.get("project_id")
    attack_id = data.get("attack_id")
    layer = data.get("layer")
    target_config = data.get("target")
    params = data.get("params", {})

    if not all([project_id, attack_id, layer, target_config]):
        return jsonify({"error": "Missing required fields: project_id, attack_id, layer, target"}), 400

    if attack_id not in ATTACK_REGISTRY:
        return jsonify({
            "error": f"Unknown attack: {attack_id}",
            "available": list(ATTACK_REGISTRY.keys())
        }), 400

    logger.info(f"Attack request: {attack_id} for project {project_id}")

    try:
        finding = runner.run(
            project_id=project_id,
            attack_id=attack_id,
            layer=layer,
            target_config=target_config,
            params=params,
        )

        # Store result
        run_id = finding.get("run_id", "unknown")
        #update
        audit_log("ATTACK_RUN", user=g.current_user.get("email"),
                  ip=request.remote_addr, detail=f"attack={attack_id} project={project_id}")
        _results_store[run_id] = finding

        return jsonify(finding), 200 if finding.get("status") != "error" else 500

    except Exception as e:
        logger.error(f"Attack execution error: {e}")
        return jsonify({"error": str(e)}), 500


@attacks_bp.route("/run-async", methods=["POST"])
@login_required
def run_attack_async():
    """Execute an attack in background thread. Returns run_id for polling.

    Same body as /run. Poll /progress/{run_id} for status.
    Result available at /result/{run_id} when done.
    """
    runner = get_runner()
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body required"}), 400

    project_id = data.get("project_id")
    attack_id = data.get("attack_id")
    layer = data.get("layer")
    target_config = data.get("target")
    params = data.get("params", {})

    if not all([project_id, attack_id, layer, target_config]):
        return jsonify({"error": "Missing required fields"}), 400

    if attack_id not in ATTACK_REGISTRY:
        return jsonify({"error": f"Unknown attack: {attack_id}"}), 400

    # Create a run_id and start in background
    import uuid
    run_id = str(uuid.uuid4())[:8]

    def _run_in_thread():
        finding = runner.run(project_id, attack_id, layer, target_config, params)
        finding["run_id"] = run_id
        _results_store[run_id] = finding

    thread = threading.Thread(target=_run_in_thread, daemon=True)
    thread.start()

    return jsonify({
        "run_id": run_id,
        "attack_id": attack_id,
        "status": "started",
        "message": f"Attack {attack_id} started in background",
        "poll_url": f"/api/v2/attacks/progress/{run_id}",
    }), 202


@attacks_bp.route("/progress/<run_id>", methods=["GET"])
def attack_progress(run_id):
    """Get progress of a running attack."""
    runner = get_runner()
    progress = runner.get_progress(run_id)
    if progress:
        return jsonify(progress)
    # Check if result is available
    if run_id in _results_store:
        return jsonify({"status": "done", "run_id": run_id})
    return jsonify({"error": "Run not found"}), 404


@attacks_bp.route("/result/<run_id>", methods=["GET"])
def attack_result(run_id):
    """Get the result of a completed attack."""
    if run_id in _results_store:
        return jsonify(_results_store[run_id])
    return jsonify({"error": "Result not found"}), 404


@attacks_bp.route("/results", methods=["GET"])
def list_results():
    """List all attack results, optionally filtered by project_id."""
    project_id = request.args.get("project_id", type=int)
    results = list(_results_store.values())
    if project_id is not None:
        results = [r for r in results if r.get("project_id") == project_id]
    return jsonify({"results": results, "total": len(results)})


@attacks_bp.route("/active", methods=["GET"])
def list_active():
    """List currently running attacks."""
    runner = get_runner()
    return jsonify({"active": runner.list_active()})
