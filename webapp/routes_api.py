"""
BBAP-Sec AI Attack Lab — Project API Routes
=============================================
REST API for managing projects, pipeline checks, running attacks,
alerts, users, and knowledge base notes.

Register in app.py:
    from webapp.routes_api import register_api_routes
    register_api_routes(app)
"""

import json
import os
import sys
import threading
from pathlib import Path
from flask import Blueprint, jsonify, request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from webapp.database import (
    init_db, create_project, list_projects, get_project, update_project, delete_project,
    get_pipeline, toggle_check, update_check,
    save_result, get_results,
    create_alert, get_alerts, acknowledge_alert, acknowledge_all_alerts,
    create_user, list_users, update_user, delete_user,
    create_note, list_notes, update_note, delete_note,
    get_dashboard_stats,
)

bp = Blueprint("api_v2", __name__, url_prefix="/api/v2")


def register_api_routes(app):
    init_db()
    app.register_blueprint(bp)


# ══════════════════════════════════
#  PROJECTS
# ══════════════════════════════════

@bp.route("/projects", methods=["GET"])
def api_list_projects():
    return jsonify(list_projects())


@bp.route("/projects", methods=["POST"])
def api_create_project():
    d = request.get_json(force=True)
    name = d.get("name", "").strip()
    if not name:
        return jsonify({"error": "name is required"}), 400
    pid = create_project(
        name=name,
        description=d.get("description", ""),
        dataset=d.get("dataset", "mnist"),
        architecture=d.get("architecture", "simple_cnn"),
    )
    return jsonify({"id": pid, "status": "created"}), 201


@bp.route("/projects/<int:pid>", methods=["GET"])
def api_get_project(pid):
    p = get_project(pid)
    if not p:
        return jsonify({"error": "not found"}), 404
    return jsonify(p)


@bp.route("/projects/<int:pid>", methods=["PUT"])
def api_update_project(pid):
    d = request.get_json(force=True)
    update_project(pid, **d)
    return jsonify({"status": "updated"})


@bp.route("/projects/<int:pid>", methods=["DELETE"])
def api_delete_project(pid):
    delete_project(pid)
    return jsonify({"status": "deleted"})


# ══════════════════════════════════
#  DASHBOARD STATS
# ══════════════════════════════════

@bp.route("/projects/<int:pid>/stats", methods=["GET"])
def api_project_stats(pid):
    return jsonify(get_dashboard_stats(pid))


@bp.route("/stats", methods=["GET"])
def api_global_stats():
    return jsonify(get_dashboard_stats())


# ══════════════════════════════════
#  PIPELINE
# ══════════════════════════════════

@bp.route("/projects/<int:pid>/pipeline", methods=["GET"])
def api_pipeline(pid):
    return jsonify(get_pipeline(pid))


@bp.route("/pipeline/check/<int:check_id>/toggle", methods=["POST"])
def api_toggle_check(check_id):
    toggle_check(check_id)
    return jsonify({"status": "toggled"})


# ══════════════════════════════════
#  ATTACKS — wired to real modules
# ══════════════════════════════════

@bp.route("/projects/<int:pid>/attack", methods=["POST"])
def api_run_attack(pid):
    """
    Run an attack against a project's model.
    POST body: { "attack_type": "adversarial", "params": { "attack": "fgsm", "epsilon": 0.03 } }
    Runs in a background thread. Returns job_id for polling.
    """
    project = get_project(pid)
    if not project:
        return jsonify({"error": "project not found"}), 404

    d = request.get_json(force=True)
    attack_type = d.get("attack_type", "")
    params = d.get("params", {})

    if attack_type not in ("adversarial", "data_poisoning", "evasion", "model_extraction", "prompt_injection"):
        return jsonify({"error": f"unknown attack type: {attack_type}"}), 400

    job_id = f"{pid}_{attack_type}_{int(__import__('time').time())}"

    def run():
        try:
            result = _execute_attack(project, attack_type, params)
            save_result(pid, attack_type, params, result)
            # Create alert if attack succeeded
            if result.get("attack_success_rate", 0) > 50 or result.get("injected", 0) > 0:
                create_alert(
                    title=f"{attack_type} test: vulnerability detected",
                    severity="high",
                    source=attack_type,
                    project_id=pid,
                )
            _attack_jobs[job_id] = {"status": "completed", "result": result}
        except Exception as e:
            _attack_jobs[job_id] = {"status": "failed", "error": str(e)}

    _attack_jobs[job_id] = {"status": "running"}
    threading.Thread(target=run, daemon=True).start()
    return jsonify({"job_id": job_id, "status": "started"})


_attack_jobs = {}


@bp.route("/attack/status/<job_id>", methods=["GET"])
def api_attack_status(job_id):
    job = _attack_jobs.get(job_id)
    if not job:
        return jsonify({"error": "job not found"}), 404
    return jsonify(job)


def _execute_attack(project, attack_type, params):
    """Execute an attack module and return results dict."""
    dataset = project.get("dataset", "mnist")

    if attack_type == "adversarial":
        from src.attacks.adversarial import fgsm_attack, pgd_attack, evaluate_robustness
        from src.models.target_model import SimpleCNN, load_dataset, train_model, get_device
        import torch

        device = get_device()
        train_loader, test_loader, in_ch = load_dataset(dataset)
        model = SimpleCNN(num_classes=10, in_channels=in_ch).to(device)
        model = train_model(model, train_loader, epochs=3, device=device)

        attack = params.get("attack", "fgsm")
        eps = float(params.get("epsilon", 0.03))

        if attack == "fgsm":
            result = evaluate_robustness(model, test_loader, fgsm_attack, device, epsilon=eps)
        else:
            result = evaluate_robustness(model, test_loader, pgd_attack, device,
                                         epsilon=eps, alpha=eps / 4, num_steps=int(params.get("steps", 20)))
        result["attack"] = attack
        result["epsilon"] = eps
        return result

    elif attack_type == "data_poisoning":
        from src.attacks.data_poisoning import label_flip_poison, backdoor_poison, evaluate_backdoor
        from src.models.target_model import SimpleCNN, load_dataset, train_model, evaluate_model, get_device
        import torch

        device = get_device()
        train_loader, test_loader, in_ch = load_dataset(dataset)

        clean_model = SimpleCNN(num_classes=10, in_channels=in_ch)
        clean_model = train_model(clean_model, train_loader, epochs=3, device=device)
        clean_acc = evaluate_model(clean_model, test_loader, device=device)

        strategy = params.get("strategy", "label_flip")
        poison_rate = float(params.get("poison_rate", 0.1))

        if strategy == "label_flip":
            poisoned_ds, idx = label_flip_poison(train_loader.dataset, poison_rate=poison_rate)
        else:
            poisoned_ds, idx, _ = backdoor_poison(train_loader.dataset, poison_rate=poison_rate)

        poisoned_loader = torch.utils.data.DataLoader(poisoned_ds, batch_size=64, shuffle=True)
        poisoned_model = SimpleCNN(num_classes=10, in_channels=in_ch)
        poisoned_model = train_model(poisoned_model, poisoned_loader, epochs=3, device=device)
        poisoned_acc = evaluate_model(poisoned_model, test_loader, device=device)

        result = {
            "strategy": strategy, "poison_rate": poison_rate,
            "clean_accuracy": round(clean_acc, 2), "poisoned_accuracy": round(poisoned_acc, 2),
            "accuracy_drop": round(clean_acc - poisoned_acc, 2), "num_poisoned": len(idx),
        }
        if strategy == "backdoor":
            result["backdoor_asr"] = round(evaluate_backdoor(poisoned_model, test_loader, 4, 0, device), 2)
        return result

    elif attack_type == "evasion":
        from src.attacks.evasion import pixel_perturbation_evasion, feature_noise_evasion, spatial_transform_evasion, evaluate_evasion
        from src.models.target_model import SimpleCNN, load_dataset, train_model, get_device

        device = get_device()
        train_loader, test_loader, in_ch = load_dataset(dataset)
        model = SimpleCNN(num_classes=10, in_channels=in_ch).to(device)
        model = train_model(model, train_loader, epochs=3, device=device)

        method = params.get("method", "pixel")
        fns = {"pixel": (pixel_perturbation_evasion, {"max_pixels": 10}),
               "noise": (feature_noise_evasion, {"noise_std": 0.1}),
               "spatial": (spatial_transform_evasion, {"max_rotation": 15})}
        fn, kw = fns.get(method, fns["pixel"])
        result = evaluate_evasion(model, test_loader, fn, device, **kw)
        result["method"] = method
        return result

    elif attack_type == "model_extraction":
        from src.attacks.model_extraction import VictimAPI, random_query_extraction, compute_fidelity
        from src.models.target_model import SimpleCNN, load_dataset, train_model, evaluate_model, get_device

        device = get_device()
        train_loader, test_loader, in_ch = load_dataset(dataset)
        img_size = 28 if dataset == "mnist" else 32

        victim = SimpleCNN(num_classes=10, in_channels=in_ch)
        victim = train_model(victim, train_loader, epochs=3, device=device)
        victim_acc = evaluate_model(victim, test_loader, device=device)
        api = VictimAPI(victim, device=device)

        substitute = SimpleCNN(num_classes=10, in_channels=in_ch)
        queries = int(params.get("queries", 500))
        substitute = random_query_extraction(api, substitute, queries, in_channels=in_ch, img_size=img_size, device=device)
        fidelity = compute_fidelity(api, substitute, test_loader, device)
        sub_acc = evaluate_model(substitute, test_loader, device=device)

        return {"victim_accuracy": round(victim_acc, 2), "substitute_accuracy": round(sub_acc, 2),
                "fidelity": round(fidelity, 2), "queries_used": api.query_count}

    elif attack_type == "prompt_injection":
        # Return test catalog for dry-run mode
        from src.attacks.prompt_injection import PromptInjectionTester
        catalog = PromptInjectionTester.get_attack_catalog()
        return {"mode": "dry_run", "tests": len(catalog), "note": "Use /prompt-injection for live simulation"}

    return {"error": "not implemented"}


# ══════════════════════════════════
#  RESULTS
# ══════════════════════════════════

@bp.route("/projects/<int:pid>/results", methods=["GET"])
def api_results(pid):
    return jsonify(get_results(pid))


# ══════════════════════════════════
#  ALERTS
# ══════════════════════════════════

@bp.route("/projects/<int:pid>/alerts", methods=["GET"])
def api_project_alerts(pid):
    return jsonify(get_alerts(pid))


@bp.route("/alerts", methods=["GET"])
def api_all_alerts():
    return jsonify(get_alerts())


@bp.route("/alerts/<int:aid>/ack", methods=["POST"])
def api_ack_alert(aid):
    acknowledge_alert(aid)
    return jsonify({"status": "acknowledged"})


@bp.route("/alerts/ack-all", methods=["POST"])
def api_ack_all():
    pid = request.args.get("project_id", type=int)
    acknowledge_all_alerts(pid)
    return jsonify({"status": "all acknowledged"})


# ══════════════════════════════════
#  USERS
# ══════════════════════════════════

@bp.route("/users", methods=["GET"])
def api_list_users():
    return jsonify(list_users())


@bp.route("/users", methods=["POST"])
def api_create_user():
    d = request.get_json(force=True)
    if not d.get("name") or not d.get("email"):
        return jsonify({"error": "name and email required"}), 400
    try:
        uid = create_user(d["name"], d["email"], d.get("role", "viewer"))
        return jsonify({"id": uid, "status": "created"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@bp.route("/users/<int:uid>", methods=["PUT"])
def api_update_user(uid):
    d = request.get_json(force=True)
    update_user(uid, **d)
    return jsonify({"status": "updated"})


@bp.route("/users/<int:uid>", methods=["DELETE"])
def api_delete_user(uid):
    delete_user(uid)
    return jsonify({"status": "deleted"})


# ══════════════════════════════════
#  NOTES (Knowledge Base)
# ══════════════════════════════════

@bp.route("/notes", methods=["GET"])
def api_list_notes():
    pid = request.args.get("project_id", type=int)
    return jsonify(list_notes(pid))


@bp.route("/notes", methods=["POST"])
def api_create_note():
    d = request.get_json(force=True)
    if not d.get("title"):
        return jsonify({"error": "title required"}), 400
    nid = create_note(
        title=d["title"], content=d.get("content", ""),
        tags=d.get("tags", []), project_id=d.get("project_id"),
        pinned=d.get("pinned", False),
    )
    return jsonify({"id": nid, "status": "created"}), 201


@bp.route("/notes/<int:nid>", methods=["PUT"])
def api_update_note(nid):
    d = request.get_json(force=True)
    update_note(nid, **d)
    return jsonify({"status": "updated"})


@bp.route("/notes/<int:nid>", methods=["DELETE"])
def api_delete_note(nid):
    delete_note(nid)
    return jsonify({"status": "deleted"})
