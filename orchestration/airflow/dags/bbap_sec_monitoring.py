from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests
from airflow import DAG
from airflow.operators.python import PythonOperator

DAG_ID = "bbap_sec_monitoring"

API_BASE = os.environ.get("BBAP_API_BASE_URL", "http://webapp:5000").rstrip("/")
API_V2 = f"{API_BASE}/api/v2"

STATIC_TOKEN = os.environ.get("BBAP_API_TOKEN", "").strip()
LOGIN_EMAIL = os.environ.get("BBAP_LOGIN_EMAIL", "").strip()
LOGIN_PASSWORD = os.environ.get("BBAP_LOGIN_PASSWORD", "").strip()

MONITOR_DIR = Path(os.environ.get("BBAP_MONITOR_OUTPUT_DIR", "/opt/airflow/monitoring"))
MONITOR_DIR.mkdir(parents=True, exist_ok=True)
LATEST_FILE = MONITOR_DIR / "bbap_monitoring_latest.json"
EVENTS_FILE = MONITOR_DIR / "bbap_monitoring_events.jsonl"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _token() -> str:
    if STATIC_TOKEN:
        return STATIC_TOKEN

    if not LOGIN_EMAIL or not LOGIN_PASSWORD:
        raise RuntimeError(
            "No BBAP_API_TOKEN and missing BBAP_LOGIN_EMAIL/BBAP_LOGIN_PASSWORD"
        )

    resp = requests.post(
        f"{API_V2}/auth/login",
        json={"email": LOGIN_EMAIL, "password": LOGIN_PASSWORD},
        timeout=20,
    )
    resp.raise_for_status()
    data = resp.json()
    token = (data or {}).get("token")
    if not token:
        raise RuntimeError("Login succeeded but token missing")
    return token


def _get(path: str, token: str) -> dict:
    resp = requests.get(
        f"{API_V2}{path}",
        headers={"Authorization": f"Bearer {token}"},
        timeout=25,
    )
    resp.raise_for_status()
    return resp.json()


def collect_metrics(**context):
    run_id = context["run_id"]
    out: dict = {
        "run_id": run_id,
        "dag_id": DAG_ID,
        "collected_at": _now_iso(),
        "status": "ok",
        "checks": {},
        "errors": [],
    }

    try:
        token = _token()
    except Exception as e:
        out["status"] = "degraded"
        out["errors"].append(f"auth: {e}")
        token = ""

    if token:
        checks = {
            "global_stats": "/stats",
            "knowledge_health": "/knowledge/health",
            "sandbox_list": "/sandbox/list",
            "projects": "/projects",
        }

        for key, path in checks.items():
            try:
                payload = _get(path, token)
                out["checks"][key] = {"ok": True, "payload": payload}
            except Exception as e:
                out["checks"][key] = {"ok": False, "error": str(e)}
                out["status"] = "degraded"
                out["errors"].append(f"{key}: {e}")

    # quick derived indicators
    stats = (out["checks"].get("global_stats") or {}).get("payload") or {}
    out["derived"] = {
        "pipeline_health": stats.get("pipeline_health"),
        "active_alerts": stats.get("active_alerts"),
        "total_results": stats.get("total_results"),
        "active_users": stats.get("active_users"),
    }

    LATEST_FILE.write_text(json.dumps(out, indent=2), encoding="utf-8")
    with EVENTS_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(out) + "\n")


def evaluate_thresholds(**_context):
    if not LATEST_FILE.exists():
        raise RuntimeError("Monitoring latest snapshot missing")

    snap = json.loads(LATEST_FILE.read_text(encoding="utf-8"))
    derived = snap.get("derived", {}) or {}

    # simple guardrails (customize as needed)
    active_alerts = derived.get("active_alerts")
    pipeline_health = derived.get("pipeline_health")

    if isinstance(active_alerts, int) and active_alerts >= 25:
        raise RuntimeError(f"High active alerts detected: {active_alerts}")

    if isinstance(pipeline_health, (int, float)) and pipeline_health < 60:
        raise RuntimeError(f"Pipeline health below threshold: {pipeline_health}")


default_args = {
    "owner": "bbap-sec",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
}

with DAG(
    dag_id=DAG_ID,
    default_args=default_args,
    description="BBAP-Sec platform health monitoring",
    start_date=datetime(2026, 1, 1),
    schedule="*/5 * * * *",
    catchup=False,
    max_active_runs=1,
    tags=["bbap", "monitoring", "security"],
) as dag:
    collect = PythonOperator(task_id="collect_metrics", python_callable=collect_metrics)
    evaluate = PythonOperator(
        task_id="evaluate_thresholds", python_callable=evaluate_thresholds
    )

    collect >> evaluate
