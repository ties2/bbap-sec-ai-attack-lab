"""
BBAP-Sec AI Attack Lab — Web Dashboard
=======================================
Flask backend serving:
  - React dashboard (/) from frontend/dist/
  - Project management API (/api/v2/...)
  - Attack execution API (/api/run/...)
  - ATLAS API (/api/atlas/...)
  - Prompt injection simulator (/prompt-injection)
  - Legacy Flask dashboard (/old-dashboard)
"""

import json, os, subprocess, threading
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, jsonify, request, send_from_directory

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.utils.logger import setup_logger, get_logger, get_project_root

setup_logger(get_project_root())
logger = get_logger("webapp")

from webapp.routes_attacks import attacks_bp, init_attack_runner
from webapp.routes_sandbox import sandbox_bp, get_manager
from webapp.security import configure_security, setup_rate_limiting, audit_log

app = Flask(__name__)

# ── Phase A security (configure_security sets restricted CORS — do NOT call CORS(app) separately) ──
configure_security(app)
limiter = setup_rate_limiting(app)

# ── Auth blueprints (REQUIRED for login + team) ──
from webapp.routes_auth import auth_bp, team_bp
app.register_blueprint(auth_bp)
app.register_blueprint(team_bp)
# Note: routes_auth uses `import webapp.database as db` directly — no init_auth needed.

# ── Attack + sandbox blueprints ──
app.register_blueprint(sandbox_bp)
app.register_blueprint(attacks_bp)
init_attack_runner(sandbox_manager=get_manager())

# ── Rate limits on sensitive blueprints (Priority 4) ──
if limiter:
    # Brute-force protection on login
    limiter.limit("5 per minute")(auth_bp)
    # Expensive operations
    limiter.limit("10 per minute")(attacks_bp)
    limiter.limit("5 per minute")(sandbox_bp)
    logger.info("Rate limits applied: auth=5/min, attacks=10/min, sandbox=5/min")

# ── React build directory ──
REACT_BUILD_DIR = Path(get_project_root()) / "frontend" / "dist"

# ── Other blueprints ──
from webapp.routes_prompt_injection import register_prompt_injection_routes
register_prompt_injection_routes(app)

from webapp.routes_api import register_api_routes
register_api_routes(app)

RESULTS_DIR = Path("results")
RESULTS_DIR.mkdir(exist_ok=True)

running_jobs = {}


# ══════════════════════════════════
#  REACT FRONTEND (main dashboard)
# ══════════════════════════════════

@app.route("/")
def serve_react():
    """Serve the React dashboard."""
    if REACT_BUILD_DIR.exists():
        logger.debug("Serving React dashboard")
        return send_from_directory(str(REACT_BUILD_DIR), "index.html")
    else:
        # Fallback to legacy Flask template if React not built yet
        logger.warning(f"React build not found at {REACT_BUILD_DIR}, falling back to legacy template")
        return render_template("index.html")


@app.route("/assets/<path:filename>")
def serve_react_assets(filename):
    """Serve Vite-compiled JS/CSS assets."""
    return send_from_directory(str(REACT_BUILD_DIR / "assets"), filename)


@app.route("/old-dashboard")
def old_dashboard():
    """Legacy Flask/Jinja dashboard (ATLAS, checklists, old attack UI)."""
    return render_template("index.html")


# ── React catch-all for client-side routing ──
# This ensures that if React uses client-side routes (e.g. /pipeline, /users),
# they all serve index.html and let React Router handle them.
# IMPORTANT: This must be AFTER all /api/* and /prompt-injection routes.

@app.route("/<path:path>")
def catch_all(path):
    """Catch-all: serve React index.html for any non-API, non-static route."""
    # Don't intercept API calls, prompt-injection, or old-dashboard
    if path.startswith("api/") or path.startswith("prompt-injection") or path == "old-dashboard":
        return jsonify({"error": "not found"}), 404

    # Try to serve as a static file first (e.g. favicon.ico, vite.svg)
    static_file = REACT_BUILD_DIR / path
    if static_file.is_file():
        return send_from_directory(str(REACT_BUILD_DIR), path)

    # Otherwise serve React index.html for client-side routing
    if REACT_BUILD_DIR.exists():
        return send_from_directory(str(REACT_BUILD_DIR), "index.html")
    return jsonify({"error": "not found"}), 404


# ══════════════════════════════════
#  LEGACY ATTACK API (v1 — kept for backward compat)
# ══════════════════════════════════

@app.route("/api/attacks", methods=["GET"])
def list_attacks():
    attacks = [
        {"id": "adversarial", "name": "Adversarial Attacks", "description": "FGSM & PGD robustness testing",
         "params": ["attack_type", "epsilon", "dataset"]},
        {"id": "data_poisoning", "name": "Data Poisoning", "description": "Label-flip & backdoor injection",
         "params": ["strategy", "poison_rate", "dataset"]},
        {"id": "evasion", "name": "Evasion Attacks", "description": "Inference-time input manipulation",
         "params": ["method", "dataset"]},
        {"id": "model_extraction", "name": "Model Extraction", "description": "API-based model stealing",
         "params": ["strategy", "num_queries", "dataset"]},
        {"id": "prompt_injection", "name": "Prompt Injection", "description": "LLM prompt security testing",
         "params": ["test_suite"]},
    ]
    return jsonify(attacks)


@app.route("/api/run/<attack_id>", methods=["POST"])
def run_attack(attack_id):
    params = request.json or {}
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = str(RESULTS_DIR / f"{attack_id}_{timestamp}.json")

    logger.info(f"API: launching attack '{attack_id}' with params={params}")

    commands = {
        "adversarial": ["python", "-m", "src.attacks.adversarial",
                        "--attack", params.get("attack_type", "both"), "--epsilon", str(params.get("epsilon", 0.03)),
                        "--dataset", params.get("dataset", "mnist"), "--sweep", "--output", output_file],
        "data_poisoning": ["python", "-m", "src.attacks.data_poisoning",
                           "--strategy", params.get("strategy", "label_flip"), "--poison-rate", str(params.get("poison_rate", 0.1)),
                           "--dataset", params.get("dataset", "mnist"), "--output", output_file],
        "evasion": ["python", "-m", "src.attacks.evasion",
                    "--method", params.get("method", "all"), "--dataset", params.get("dataset", "mnist"), "--output", output_file],
        "model_extraction": ["python", "-m", "src.attacks.model_extraction",
                             "--strategy", params.get("strategy", "random"), "--queries", str(params.get("num_queries", 1000)),
                             "--dataset", params.get("dataset", "mnist"), "--output", output_file],
        "prompt_injection": ["python", "-m", "src.attacks.prompt_injection",
                             "--test-suite", params.get("test_suite", "all"), "--output", output_file],
    }

    if attack_id not in commands:
        return jsonify({"error": f"Unknown attack: {attack_id}"}), 400

    cmd = commands[attack_id]
    job_id = f"{attack_id}_{timestamp}"

    def run_cmd():
        logger.info(f"Job {job_id}: starting subprocess")
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            status = "completed" if result.returncode == 0 else "failed"
            running_jobs[job_id] = {"status": status, "output": result.stdout, "error": result.stderr, "result_file": output_file}
            logger.info(f"Job {job_id}: {status}")
            if result.returncode != 0:
                logger.error(f"Job {job_id} stderr: {result.stderr[:500]}")
        except subprocess.TimeoutExpired:
            running_jobs[job_id] = {"status": "timeout", "output": "", "error": "Timed out after 600s"}
            logger.error(f"Job {job_id}: timed out")

    running_jobs[job_id] = {"status": "running"}
    threading.Thread(target=run_cmd, daemon=True).start()

    return jsonify({"job_id": job_id, "status": "started"})


@app.route("/api/status/<job_id>")
def job_status(job_id):
    if job_id not in running_jobs:
        return jsonify({"error": "Job not found"}), 404
    return jsonify(running_jobs[job_id])


@app.route("/api/results")
def list_results():
    files = sorted(RESULTS_DIR.glob("*.json"), reverse=True)
    results = []
    for f in files[:20]:
        try:
            with open(f) as fh:
                data = json.load(fh)
            results.append({"file": f.name, "data": data})
        except (json.JSONDecodeError, IOError):
            pass
    return jsonify(results)


@app.route("/api/checklists")
def get_checklists():
    checklists_dir = Path("checklists")
    items = []
    for f in sorted(checklists_dir.glob("*.md")):
        items.append({"name": f.stem, "content": f.read_text()})
    return jsonify(items)


# ══════════════════════════════════
#  ATLAS API
# ══════════════════════════════════

_atlas_db = None
_atlas_mapper = None


def _get_atlas():
    global _atlas_db, _atlas_mapper
    if _atlas_db is None:
        from src.atlas.atlas_data import ATLASDatabase
        from src.atlas.atlas_mapper import ATLASMapper
        _atlas_db = ATLASDatabase()
        _atlas_db.load()
        _atlas_mapper = ATLASMapper(_atlas_db)
    return _atlas_db, _atlas_mapper


@app.route("/api/atlas/stats")
def atlas_stats():
    db, _ = _get_atlas()
    return jsonify(db.get_stats())


@app.route("/api/atlas/tactics")
def atlas_tactics():
    db, _ = _get_atlas()
    return jsonify(sorted(db.tactics.values(), key=lambda t: t["id"]))


@app.route("/api/atlas/search")
def atlas_search():
    query = request.args.get("q", "")
    if not query:
        return jsonify({"error": "Missing ?q= parameter"}), 400
    db, _ = _get_atlas()
    techniques = db.search_techniques(query)
    cases = db.search_case_studies(query)
    mitigations = db.search_mitigations(query)
    return jsonify({"query": query, "techniques": techniques, "case_studies": cases, "mitigations": mitigations})


@app.route("/api/atlas/technique/<tech_id>")
def atlas_technique(tech_id):
    db, _ = _get_atlas()
    tech = db.get_technique(tech_id)
    if not tech:
        return jsonify({"error": f"Not found: {tech_id}"}), 404
    mits = db.get_mitigations_for_technique(tech_id)
    subs = db.get_subtechniques(tech_id)
    return jsonify({"technique": tech, "mitigations": mits, "subtechniques": subs})


@app.route("/api/atlas/case-study/<cs_id>")
def atlas_case_study(cs_id):
    db, _ = _get_atlas()
    cs = db.get_case_study(cs_id)
    if not cs:
        return jsonify({"error": f"Not found: {cs_id}"}), 404
    chain = db.get_case_study_chain(cs_id)
    return jsonify({"case_study": cs, "attack_chain": chain})


@app.route("/api/atlas/mapping/<module_name>")
def atlas_mapping(module_name):
    _, mapper = _get_atlas()
    if module_name == "all":
        return jsonify(mapper.get_all_mappings())
    mapping = mapper.get_mapping(module_name)
    if not mapping:
        return jsonify({"error": f"No mapping for: {module_name}"}), 404
    return jsonify(mapping)


@app.route("/api/atlas/coverage")
def atlas_coverage():
    _, mapper = _get_atlas()
    return jsonify(mapper.get_coverage_matrix())


@app.route("/api/atlas/report")
def atlas_report():
    _, mapper = _get_atlas()
    return jsonify(mapper.get_full_report())


# ══════════════════════════════════
#  START
# ══════════════════════════════════

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV") == "development"
    logger.info("=" * 50)
    logger.info("BBAP-Sec AI Attack Lab — Web Dashboard")
    logger.info(f"React build: {REACT_BUILD_DIR} ({'found' if REACT_BUILD_DIR.exists() else 'NOT FOUND'})")
    logger.info(f"Running on http://0.0.0.0:{port}")
    logger.info("=" * 50)
    app.run(host="0.0.0.0", port=port, debug=debug)