"""
BBAP-Sec AI Attack Lab — Flask routes for Prompt Injection module.
Add these routes to your existing webapp/app.py

Usage in app.py:
    from webapp.routes_prompt_injection import register_prompt_injection_routes
    register_prompt_injection_routes(app)
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Blueprint, jsonify, render_template, request
from src.attacks.prompt_injection import PromptInjectionTester

bp = Blueprint("prompt_injection", __name__)


def register_prompt_injection_routes(app):
    """Call this in app.py: register_prompt_injection_routes(app)"""
    app.register_blueprint(bp)


@bp.route("/prompt-injection")
def prompt_injection_lab():
    """Render the interactive prompt injection lab dashboard."""
    return render_template("prompt_injection.html")


@bp.route("/api/prompt-injection/catalog")
def get_catalog():
    """Return all attack definitions and bot targets for the frontend."""
    return jsonify({
        "attacks": PromptInjectionTester.get_attack_catalog(),
        "bots": PromptInjectionTester.get_bot_catalog(),
    })


@bp.route("/api/prompt-injection/fire", methods=["POST"])
def fire_attack():
    """
    Fire a single attack against a target bot.
    POST body: { "attack_id": "A-01", "bot": "finbot" }
    """
    data = request.get_json(force=True)
    attack_id = data.get("attack_id")
    bot_name = data.get("bot", "finbot")

    if not attack_id:
        return jsonify({"error": "attack_id is required"}), 400

    try:
        tester = PromptInjectionTester(bot_name=bot_name)
        result = tester.fire_single(attack_id)
        return jsonify(result)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"API error: {str(e)}"}), 500


@bp.route("/api/prompt-injection/run-suite", methods=["POST"])
def run_suite():
    """
    Run a full attack suite.
    POST body: { "suite": "all", "bot": "finbot" }
    Suites: all | direct | indirect | exfiltration | jailbreak
    """
    data = request.get_json(force=True)
    suite = data.get("suite", "all")
    bot_name = data.get("bot", "finbot")

    SUITE_MAP = {
        "all": None,
        "direct": ["A-01", "A-02", "A-06", "A-08", "A-09"],
        "indirect": ["A-05", "A-07", "A-10"],
        "exfiltration": ["A-02", "A-09"],
        "jailbreak": ["A-03", "A-04", "A-08"],
    }

    attack_ids = SUITE_MAP.get(suite)
    if suite not in SUITE_MAP:
        return jsonify({"error": f"Unknown suite '{suite}'"}), 400

    try:
        tester = PromptInjectionTester(bot_name=bot_name)
        summary = tester.run_all(attack_ids=attack_ids, verbose=False, delay=0.3)
        tester.save_report()
        return jsonify(summary)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
