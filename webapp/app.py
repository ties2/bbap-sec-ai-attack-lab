"""
BBAP-Sec AI Attack Lab — Web Dashboard
=======================================
Flask-based web interface for running attack modules and viewing results.
"""

import json
import os
import subprocess
import threading
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

RESULTS_DIR = Path("results")
RESULTS_DIR.mkdir(exist_ok=True)

# Track running jobs
running_jobs = {}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/attacks", methods=["GET"])
def list_attacks():
    attacks = [
        {
            "id": "adversarial",
            "name": "Adversarial Attacks",
            "description": "FGSM & PGD robustness testing",
            "icon": "🎯",
            "params": ["attack_type", "epsilon", "dataset"],
        },
        {
            "id": "data_poisoning",
            "name": "Data Poisoning",
            "description": "Label-flip & backdoor injection",
            "icon": "☠️",
            "params": ["strategy", "poison_rate", "dataset"],
        },
        {
            "id": "evasion",
            "name": "Evasion Attacks",
            "description": "Inference-time input manipulation",
            "icon": "🕵️",
            "params": ["method", "dataset"],
        },
        {
            "id": "model_extraction",
            "name": "Model Extraction",
            "description": "API-based model stealing",
            "icon": "🔓",
            "params": ["strategy", "num_queries", "dataset"],
        },
        {
            "id": "prompt_injection",
            "name": "Prompt Injection",
            "description": "LLM prompt security testing",
            "icon": "💉",
            "params": ["test_suite"],
        },
    ]
    return jsonify(attacks)


@app.route("/api/run/<attack_id>", methods=["POST"])
def run_attack(attack_id):
    params = request.json or {}
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = str(RESULTS_DIR / f"{attack_id}_{timestamp}.json")

    # Build CLI command
    commands = {
        "adversarial": [
            "python", "-m", "src.attacks.adversarial",
            "--attack", params.get("attack_type", "both"),
            "--epsilon", str(params.get("epsilon", 0.03)),
            "--dataset", params.get("dataset", "mnist"),
            "--sweep",
            "--output", output_file,
        ],
        "data_poisoning": [
            "python", "-m", "src.attacks.data_poisoning",
            "--strategy", params.get("strategy", "label_flip"),
            "--poison-rate", str(params.get("poison_rate", 0.1)),
            "--dataset", params.get("dataset", "mnist"),
            "--output", output_file,
        ],
        "evasion": [
            "python", "-m", "src.attacks.evasion",
            "--method", params.get("method", "all"),
            "--dataset", params.get("dataset", "mnist"),
            "--output", output_file,
        ],
        "model_extraction": [
            "python", "-m", "src.attacks.model_extraction",
            "--strategy", params.get("strategy", "random"),
            "--queries", str(params.get("num_queries", 1000)),
            "--dataset", params.get("dataset", "mnist"),
            "--output", output_file,
        ],
        "prompt_injection": [
            "python", "-m", "src.attacks.prompt_injection",
            "--test-suite", params.get("test_suite", "all"),
            "--output", output_file,
        ],
    }

    if attack_id not in commands:
        return jsonify({"error": f"Unknown attack: {attack_id}"}), 400

    cmd = commands[attack_id]
    job_id = f"{attack_id}_{timestamp}"

    def run_cmd():
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            running_jobs[job_id] = {
                "status": "completed" if result.returncode == 0 else "failed",
                "output": result.stdout,
                "error": result.stderr,
                "result_file": output_file,
            }
        except subprocess.TimeoutExpired:
            running_jobs[job_id] = {"status": "timeout", "output": "", "error": "Timed out"}

    running_jobs[job_id] = {"status": "running"}
    thread = threading.Thread(target=run_cmd)
    thread.start()

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


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV") == "development"
    print("=" * 50)
    print("  BBAP-Sec AI Attack Lab — Web Dashboard")
    print(f"  Running on http://0.0.0.0:{port}")
    print("=" * 50)
    app.run(host="0.0.0.0", port=port, debug=debug)
