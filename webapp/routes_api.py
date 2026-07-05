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
import subprocess
import sys
import threading
from pathlib import Path

import requests
from flask import Blueprint, g, jsonify, request

from webapp.auth import decode_token, login_required, role_required
from webapp.knowledge_rag import get_knowledge_rag_service

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from webapp.database import (
    acknowledge_alert,
    acknowledge_all_alerts,
    create_alert,
    create_note,
    create_project,
    create_user,
    delete_note,
    delete_project,
    delete_user,
    get_alerts,
    get_all_users,
    get_dashboard_stats,
    get_pipeline,
    get_project,
    get_results,
    init_db,
    list_notes,
    list_projects,
    save_result,
    toggle_check,
    update_check,
    update_note,
    update_project,
    update_user,
)

bp = Blueprint("api_v2", __name__, url_prefix="/api/v2")


@bp.before_request
def require_auth_for_api_v2():
    """Defense-in-depth auth guard for /api/v2 routes."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return jsonify({"error": "Authentication required"}), 401

    payload = decode_token(auth_header[7:])
    if not payload:
        return jsonify({"error": "Invalid or expired token"}), 401

    g.current_user = payload
    return None


def register_api_routes(app):
    init_db()
    app.register_blueprint(bp)


# ══════════════════════════════════
#  PROJECTS
# ══════════════════════════════════
# Reads can stay @login_required (all authed users)
@bp.route("/projects", methods=["GET"])
@login_required
def api_list_projects():
    return jsonify(list_projects())


# Project create/update/delete — staff only
@bp.route("/projects", methods=["POST"])
@role_required("bbap_admin", "bbap_lead", "bbap_engineer")  # ADD
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
@login_required
def api_get_project(pid):
    p = get_project(pid)
    if not p:
        return jsonify({"error": "not found"}), 404
    return jsonify(p)


@bp.route("/projects/<int:pid>", methods=["PUT"])
@role_required("bbap_admin", "bbap_lead", "bbap_engineer")
def api_update_project(pid):
    d = request.get_json(force=True)
    update_project(pid, **d)
    return jsonify({"status": "updated"})


@bp.route("/projects/<int:pid>", methods=["DELETE"])
@role_required("bbap_admin", "bbap_lead")
def api_delete_project(pid):
    delete_project(pid)
    return jsonify({"status": "deleted"})


# ══════════════════════════════════
#  DASHBOARD STATS
# ══════════════════════════════════


@bp.route("/projects/<int:pid>/stats", methods=["GET"])
@login_required
def api_project_stats(pid):
    return jsonify(get_dashboard_stats(pid))


@bp.route("/stats", methods=["GET"])
@login_required
def api_global_stats():
    return jsonify(get_dashboard_stats())


# ══════════════════════════════════
#  PIPELINE
# ══════════════════════════════════


@bp.route("/projects/<int:pid>/pipeline", methods=["GET"])
@login_required
def api_pipeline(pid):
    return jsonify(get_pipeline(pid))


@bp.route("/pipeline/check/<int:check_id>/toggle", methods=["POST"])
@role_required(
    "bbap_admin", "bbap_lead", "bbap_engineer", "bbap_analyst", "client_admin"
)
def api_toggle_check(check_id):
    toggle_check(check_id)
    return jsonify({"status": "toggled"})


# ══════════════════════════════════
#  ATTACKS — wired to real modules
# ══════════════════════════════════


@bp.route("/projects/<int:pid>/attack", methods=["POST"])
@role_required("bbap_admin", "bbap_lead", "bbap_engineer", "bbap_analyst")
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

    if attack_type not in (
        "adversarial",
        "data_poisoning",
        "evasion",
        "model_extraction",
        "prompt_injection",
    ):
        return jsonify({"error": f"unknown attack type: {attack_type}"}), 400

    job_id = f"{pid}_{attack_type}_{int(__import__('time').time())}"

    def run():
        try:
            result = _execute_attack(project, attack_type, params)
            save_result(pid, attack_type, params, result)
            # Create alert if attack succeeded
            if (
                result.get("attack_success_rate", 0) > 50
                or result.get("injected", 0) > 0
            ):
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
@login_required
def api_attack_status(job_id):
    job = _attack_jobs.get(job_id)
    if not job:
        return jsonify({"error": "job not found"}), 404
    return jsonify(job)


def _execute_attack(project, attack_type, params):
    """Execute an attack module and return results dict."""
    dataset = project.get("dataset", "mnist")

    if attack_type == "adversarial":
        import torch

        from src.attacks.adversarial import evaluate_robustness, fgsm_attack, pgd_attack
        from src.models.target_model import (
            SimpleCNN,
            get_device,
            load_dataset,
            train_model,
        )

        device = get_device()
        train_loader, test_loader, in_ch = load_dataset(dataset)
        model = SimpleCNN(num_classes=10, in_channels=in_ch).to(device)
        model = train_model(model, train_loader, epochs=3, device=device)

        attack = params.get("attack", "fgsm")
        eps = float(params.get("epsilon", 0.03))

        if attack == "fgsm":
            result = evaluate_robustness(
                model, test_loader, fgsm_attack, device, epsilon=eps
            )
        else:
            result = evaluate_robustness(
                model,
                test_loader,
                pgd_attack,
                device,
                epsilon=eps,
                alpha=eps / 4,
                num_steps=int(params.get("steps", 20)),
            )
        result["attack"] = attack
        result["epsilon"] = eps
        return result

    elif attack_type == "data_poisoning":
        import torch

        from src.attacks.data_poisoning import (
            backdoor_poison,
            evaluate_backdoor,
            label_flip_poison,
        )
        from src.models.target_model import (
            SimpleCNN,
            evaluate_model,
            get_device,
            load_dataset,
            train_model,
        )

        device = get_device()
        train_loader, test_loader, in_ch = load_dataset(dataset)

        clean_model = SimpleCNN(num_classes=10, in_channels=in_ch)
        clean_model = train_model(clean_model, train_loader, epochs=3, device=device)
        clean_acc = evaluate_model(clean_model, test_loader, device=device)

        strategy = params.get("strategy", "label_flip")
        poison_rate = float(params.get("poison_rate", 0.1))

        if strategy == "label_flip":
            poisoned_ds, idx = label_flip_poison(
                train_loader.dataset, poison_rate=poison_rate
            )
        else:
            poisoned_ds, idx, _ = backdoor_poison(
                train_loader.dataset, poison_rate=poison_rate
            )

        poisoned_loader = torch.utils.data.DataLoader(
            poisoned_ds, batch_size=64, shuffle=True
        )
        poisoned_model = SimpleCNN(num_classes=10, in_channels=in_ch)
        poisoned_model = train_model(
            poisoned_model, poisoned_loader, epochs=3, device=device
        )
        poisoned_acc = evaluate_model(poisoned_model, test_loader, device=device)

        result = {
            "strategy": strategy,
            "poison_rate": poison_rate,
            "clean_accuracy": round(clean_acc, 2),
            "poisoned_accuracy": round(poisoned_acc, 2),
            "accuracy_drop": round(clean_acc - poisoned_acc, 2),
            "num_poisoned": len(idx),
        }
        if strategy == "backdoor":
            result["backdoor_asr"] = round(
                evaluate_backdoor(poisoned_model, test_loader, 4, 0, device), 2
            )
        return result

    elif attack_type == "evasion":
        from src.attacks.evasion import (
            evaluate_evasion,
            feature_noise_evasion,
            pixel_perturbation_evasion,
            spatial_transform_evasion,
        )
        from src.models.target_model import (
            SimpleCNN,
            get_device,
            load_dataset,
            train_model,
        )

        device = get_device()
        train_loader, test_loader, in_ch = load_dataset(dataset)
        model = SimpleCNN(num_classes=10, in_channels=in_ch).to(device)
        model = train_model(model, train_loader, epochs=3, device=device)

        method = params.get("method", "pixel")
        fns = {
            "pixel": (pixel_perturbation_evasion, {"max_pixels": 10}),
            "noise": (feature_noise_evasion, {"noise_std": 0.1}),
            "spatial": (spatial_transform_evasion, {"max_rotation": 15}),
        }
        fn, kw = fns.get(method, fns["pixel"])
        result = evaluate_evasion(model, test_loader, fn, device, **kw)
        result["method"] = method
        return result

    elif attack_type == "model_extraction":
        from src.attacks.model_extraction import (
            VictimAPI,
            compute_fidelity,
            random_query_extraction,
        )
        from src.models.target_model import (
            SimpleCNN,
            evaluate_model,
            get_device,
            load_dataset,
            train_model,
        )

        device = get_device()
        train_loader, test_loader, in_ch = load_dataset(dataset)
        img_size = 28 if dataset == "mnist" else 32

        victim = SimpleCNN(num_classes=10, in_channels=in_ch)
        victim = train_model(victim, train_loader, epochs=3, device=device)
        victim_acc = evaluate_model(victim, test_loader, device=device)
        api = VictimAPI(victim, device=device)

        substitute = SimpleCNN(num_classes=10, in_channels=in_ch)
        queries = int(params.get("queries", 500))
        substitute = random_query_extraction(
            api,
            substitute,
            queries,
            in_channels=in_ch,
            img_size=img_size,
            device=device,
        )
        fidelity = compute_fidelity(api, substitute, test_loader, device)
        sub_acc = evaluate_model(substitute, test_loader, device=device)

        return {
            "victim_accuracy": round(victim_acc, 2),
            "substitute_accuracy": round(sub_acc, 2),
            "fidelity": round(fidelity, 2),
            "queries_used": api.query_count,
        }

    elif attack_type == "prompt_injection":
        # Return test catalog for dry-run mode
        from src.attacks.prompt_injection import PromptInjectionTester

        catalog = PromptInjectionTester.get_attack_catalog()
        return {
            "mode": "dry_run",
            "tests": len(catalog),
            "note": "Use /prompt-injection for live simulation",
        }

    return {"error": "not implemented"}


# ══════════════════════════════════
#  RESULTS
# ══════════════════════════════════


@bp.route("/projects/<int:pid>/results", methods=["GET"])
@login_required
def api_results(pid):
    return jsonify(get_results(pid))


# ══════════════════════════════════
#  ALERTS
# ══════════════════════════════════


@bp.route("/projects/<int:pid>/alerts", methods=["GET"])
@login_required
def api_project_alerts(pid):
    return jsonify(get_alerts(pid))


@bp.route("/alerts", methods=["GET"])
@login_required
def api_all_alerts():
    return jsonify(get_alerts())


@bp.route("/alerts/<int:aid>/ack", methods=["POST"])
@login_required
def api_ack_alert(aid):
    acknowledge_alert(aid)
    return jsonify({"status": "acknowledged"})


@bp.route("/alerts/ack-all", methods=["POST"])
@login_required
def api_ack_all():
    pid = request.args.get("project_id", type=int)
    acknowledge_all_alerts(pid)
    return jsonify({"status": "all acknowledged"})


# ══════════════════════════════════
#  USERS
# ══════════════════════════════════


@bp.route("/users", methods=["GET"])
def api_list_users():
    return jsonify({"error": "Deprecated endpoint. Use /api/v2/team/users"}), 410


@bp.route("/users", methods=["POST"])
def api_create_user():
    return jsonify({"error": "Deprecated endpoint. Use /api/v2/team/users"}), 410


@bp.route("/users/<int:uid>", methods=["PUT"])
def api_update_user(uid):
    return jsonify({"error": "Deprecated endpoint. Use /api/v2/team/users/<id>"}), 410


@bp.route("/users/<int:uid>", methods=["DELETE"])
def api_delete_user(uid):
    return jsonify({"error": "Deprecated endpoint. Use /api/v2/team/users/<id>"}), 410


# ══════════════════════════════════
#  MONITORING (Airflow integration)
# ══════════════════════════════════


def _airflow_api_base() -> str:
    return os.environ.get("AIRFLOW_API_BASE", "http://127.0.0.1:8081/api/v1").rstrip(
        "/"
    )


def _airflow_auth() -> tuple[str, str]:
    user = os.environ.get("AIRFLOW_USERNAME", "airflow")
    pw = os.environ.get("AIRFLOW_PASSWORD", "airflow")
    return user, pw


def _airflow_monitor_file() -> Path:
    return Path(
        os.environ.get(
            "AIRFLOW_MONITOR_FILE",
            "logs/airflow-monitoring/bbap_monitoring_latest.json",
        )
    )


def _airflow_events_file() -> Path:
    return Path(
        os.environ.get(
            "AIRFLOW_EVENTS_FILE",
            "logs/airflow-monitoring/bbap_monitoring_events.jsonl",
        )
    )


def _airflow_get(path: str) -> tuple[dict, int]:
    try:
        r = requests.get(
            f"{_airflow_api_base()}{path}",
            auth=_airflow_auth(),
            timeout=8,
        )
        return (r.json() if r.content else {}), r.status_code
    except Exception as e:
        return {"error": str(e)}, 0


def _airflow_post(path: str, payload: dict) -> tuple[dict, int]:
    try:
        r = requests.post(
            f"{_airflow_api_base()}{path}",
            auth=_airflow_auth(),
            json=payload,
            timeout=10,
        )
        return (r.json() if r.content else {}), r.status_code
    except Exception as e:
        return {"error": str(e)}, 0


@bp.route("/monitoring/airflow/overview", methods=["GET"])
@login_required
def api_monitoring_airflow_overview():
    health_data, health_code = _airflow_get("/health")
    dag_id = os.environ.get("AIRFLOW_MONITOR_DAG_ID", "bbap_sec_monitoring")
    dag_data, dag_code = _airflow_get(f"/dags/{dag_id}")
    runs_data, runs_code = _airflow_get(
        f"/dags/{dag_id}/dagRuns?limit=10&order_by=-logical_date"
    )

    latest_file = _airflow_monitor_file()
    latest_snapshot = None
    latest_error = ""
    if latest_file.exists():
        try:
            latest_snapshot = json.loads(latest_file.read_text(encoding="utf-8"))
        except Exception as e:
            latest_error = str(e)

    return jsonify(
        {
            "configured": True,
            "airflow": {
                "api_base": _airflow_api_base(),
                "reachable": health_code in (200, 401, 403),
                "health": health_data,
                "dag": dag_data if dag_code == 200 else None,
                "runs": runs_data.get("dag_runs", []) if runs_code == 200 else [],
                "errors": {
                    "health": health_data.get("error") if health_code == 0 else None,
                    "dag": dag_data.get("error") if dag_code == 0 else None,
                    "runs": runs_data.get("error") if runs_code == 0 else None,
                },
            },
            "latest_snapshot": latest_snapshot,
            "latest_snapshot_error": latest_error,
        }
    )


@bp.route("/monitoring/airflow/events", methods=["GET"])
@login_required
def api_monitoring_airflow_events():
    limit = request.args.get("limit", 30, type=int)
    limit = min(max(limit or 30, 1), 200)

    events_file = _airflow_events_file()
    if not events_file.exists():
        return jsonify({"events": [], "count": 0})

    events = []
    try:
        with events_file.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    events.append(json.loads(line))
                except Exception:
                    continue
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    trimmed = list(reversed(events[-limit:]))
    return jsonify({"events": trimmed, "count": len(trimmed)})


@bp.route("/monitoring/airflow/trigger", methods=["POST"])
@role_required("bbap_admin", "bbap_lead", "bbap_engineer")
def api_monitoring_airflow_trigger():
    dag_id = os.environ.get("AIRFLOW_MONITOR_DAG_ID", "bbap_sec_monitoring")
    payload = request.get_json(silent=True) or {}
    conf = payload.get("conf") or {}

    body = {"conf": conf}
    out, code = _airflow_post(f"/dags/{dag_id}/dagRuns", body)

    if code not in (200, 201):
        return (
            jsonify(
                {
                    "error": "Failed to trigger DAG",
                    "status_code": code,
                    "details": out,
                }
            ),
            502,
        )

    return jsonify({"status": "triggered", "dag_id": dag_id, "run": out}), 201


# ══════════════════════════════════
#  NOTES (Knowledge Base)
# ══════════════════════════════════


@bp.route("/projects/<int:pid>/notes", methods=["GET"])
@login_required
def api_list_notes(pid):
    return jsonify(list_notes(pid))


@bp.route("/notes", methods=["POST"])
@login_required
def api_create_note():
    d = request.get_json(force=True)
    if not d.get("title"):
        return jsonify({"error": "title required"}), 400
    nid = create_note(
        title=d["title"],
        content=d.get("content", ""),
        tags=d.get("tags", []),
        project_id=d.get("project_id"),
        pinned=d.get("pinned", False),
    )
    return jsonify({"id": nid, "status": "created"}), 201


@bp.route("/notes/<int:nid>", methods=["PUT"])
@login_required
def api_update_note(nid):
    d = request.get_json(force=True)
    update_note(nid, **d)
    return jsonify({"status": "updated"})


@bp.route("/notes/<int:nid>", methods=["DELETE"])
@login_required
def api_delete_note(nid):
    delete_note(nid)
    return jsonify({"status": "deleted"})


# ══════════════════════════════════
#  KNOWLEDGE HUB (External repo integration)
# ══════════════════════════════════


def _knowledge_hub_root() -> Path:
    default_path = Path("external") / "BBAP-Sec-Knowledge-Hub"
    return Path(os.environ.get("BBAP_KNOWLEDGE_HUB_PATH", str(default_path)))


def _is_markdown(path: Path) -> bool:
    return path.suffix.lower() in {".md", ".markdown", ".mdx", ".txt"}


@bp.route("/knowledge/files", methods=["GET"])
@login_required
def api_knowledge_files():
    root = _knowledge_hub_root()
    if not root.exists() or not root.is_dir():
        return jsonify(
            {
                "error": "Knowledge hub not found",
                "path": str(root),
                "hint": "Run scripts/sync_knowledge_hub.sh first",
            }
        ), 404

    files = []
    for p in sorted(root.rglob("*")):
        if p.is_file() and _is_markdown(p):
            rel = p.relative_to(root)
            # skip hidden and build/system folders
            parts = set(rel.parts)
            if any(part.startswith(".") for part in rel.parts):
                continue
            if parts.intersection(
                {
                    ".git",
                    "node_modules",
                    "dist",
                    "build",
                    "venv",
                    ".venv",
                    "__pycache__",
                }
            ):
                continue
            files.append(str(rel))

    return jsonify({"root": str(root), "count": len(files), "files": files})


@bp.route("/knowledge/file", methods=["GET"])
@login_required
def api_knowledge_file():
    rel_path = request.args.get("path", "").strip()
    if not rel_path:
        return jsonify({"error": "Missing 'path' query param"}), 400

    root = _knowledge_hub_root().resolve()
    target = (root / rel_path).resolve()

    # path traversal guard
    if root not in [target, *target.parents]:
        return jsonify({"error": "Invalid path"}), 400

    if not target.exists() or not target.is_file() or not _is_markdown(target):
        return jsonify({"error": "File not found"}), 404

    try:
        content = target.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return jsonify({"error": f"Failed to read file: {e}"}), 500

    return jsonify(
        {
            "path": str(target.relative_to(root)),
            "size": len(content.encode("utf-8")),
            "content": content,
        }
    )


@bp.route("/knowledge/sync", methods=["POST"])
@role_required("bbap_admin", "bbap_lead", "bbap_engineer")
def api_knowledge_sync():
    root = _knowledge_hub_root()
    repo_url = os.environ.get(
        "BBAP_KNOWLEDGE_HUB_REPO", "https://github.com/ties2/BBAP-Sec-Knowledge-Hub.git"
    )
    branch = os.environ.get("BBAP_KNOWLEDGE_HUB_BRANCH", "main")

    try:
        if (root / ".git").exists():
            cmd = ["git", "-C", str(root), "pull", "--ff-only", "origin", branch]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        else:
            root.parent.mkdir(parents=True, exist_ok=True)
            cmd = [
                "git",
                "clone",
                "--depth",
                "1",
                "--branch",
                branch,
                repo_url,
                str(root),
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)

        if result.returncode != 0:
            return jsonify(
                {
                    "error": "Sync failed",
                    "command": cmd,
                    "stdout": result.stdout[-1200:],
                    "stderr": result.stderr[-1200:],
                }
            ), 500

        rag_stats = None
        try:
            rag_stats = get_knowledge_rag_service().reindex()
        except Exception as reindex_err:
            rag_stats = {"ok": False, "error": str(reindex_err)}

        return jsonify(
            {
                "status": "ok",
                "path": str(root),
                "repo": repo_url,
                "branch": branch,
                "stdout": result.stdout[-1200:],
                "rag": rag_stats,
            }
        )
    except subprocess.TimeoutExpired:
        return jsonify({"error": "Sync timed out"}), 504
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/knowledge/reindex", methods=["POST"])
@role_required("bbap_admin", "bbap_lead", "bbap_engineer")
def api_knowledge_reindex():
    try:
        stats = get_knowledge_rag_service().reindex()
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/knowledge/health", methods=["GET"])
@login_required
def api_knowledge_health():
    return jsonify(get_knowledge_rag_service().health())


@bp.route("/knowledge/ask", methods=["POST"])
@login_required
def api_knowledge_ask():
    d = request.get_json(force=True) or {}
    question = (d.get("question") or "").strip()
    top_k = int(d.get("top_k") or 5)

    if not question:
        return jsonify({"error": "question is required"}), 400

    if top_k < 1 or top_k > 15:
        return jsonify({"error": "top_k must be between 1 and 15"}), 400

    try:
        out = get_knowledge_rag_service().ask(question, top_k=top_k)
        return jsonify(out)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
