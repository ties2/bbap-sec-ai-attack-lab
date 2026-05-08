"""
BBAP-Sec AI Attack Lab — Database Layer
========================================
SQLite persistence for projects, pipeline checks, attack results,
alerts, users, and knowledge base notes.
"""

import sqlite3
import json
import os
from datetime import datetime
from pathlib import Path
from contextlib import contextmanager

DB_PATH = os.environ.get("BBAP_DB_PATH", "data/bbap_sec.db")


def get_db_path():
    p = Path(DB_PATH)
    p.parent.mkdir(parents=True, exist_ok=True)
    return str(p)


@contextmanager
def get_db():
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    """Create all tables if they don't exist."""
    with get_db() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT DEFAULT '',
            dataset TEXT DEFAULT 'mnist',
            architecture TEXT DEFAULT 'simple_cnn',
            model_path TEXT DEFAULT '',
            status TEXT DEFAULT 'active',
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS pipeline_checks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
            stage TEXT NOT NULL,
            check_name TEXT NOT NULL,
            passed INTEGER DEFAULT 0,
            details TEXT DEFAULT '',
            checked_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS attack_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
            attack_type TEXT NOT NULL,
            attack_params TEXT DEFAULT '{}',
            result_data TEXT DEFAULT '{}',
            status TEXT DEFAULT 'completed',
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER REFERENCES projects(id) ON DELETE SET NULL,
            severity TEXT DEFAULT 'medium',
            title TEXT NOT NULL,
            source TEXT DEFAULT '',
            acknowledged INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            role TEXT DEFAULT 'viewer',
            status TEXT DEFAULT 'active',
            mfa INTEGER DEFAULT 0,
            last_login TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER REFERENCES projects(id) ON DELETE SET NULL,
            title TEXT NOT NULL,
            content TEXT DEFAULT '',
            tags TEXT DEFAULT '[]',
            pinned INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now'))
        );
        """)

        # Seed default admin if no users exist
        count = db.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        if count == 0:
            db.execute("INSERT INTO users (name, email, role, status, mfa) VALUES (?, ?, ?, ?, ?)",
                       ("Admin User", "admin@bbap-sec.io", "admin", "active", 1))


# ── Helper: dict from Row ──
def row_to_dict(row):
    if row is None:
        return None
    return dict(row)


def rows_to_list(rows):
    return [dict(r) for r in rows]


# ══════════════════════════════════
#  PROJECTS
# ══════════════════════════════════

def create_project(name, description="", dataset="mnist", architecture="simple_cnn"):
    with get_db() as db:
        cur = db.execute(
            "INSERT INTO projects (name, description, dataset, architecture) VALUES (?, ?, ?, ?)",
            (name, description, dataset, architecture))
        pid = cur.lastrowid
        _init_pipeline_checks(db, pid)
        return pid


def _init_pipeline_checks(db, project_id):
    """Seed default pipeline checks for a new project."""
    stages = {
        "data_ingestion": ["Schema validation", "Poison detection", "Source auth", "Integrity hash",
                           "Outlier detection", "Format check", "Volume anomaly", "PII scan",
                           "Label consistency", "Duplicate detection", "Provenance tracking", "Encryption at rest"],
        "model_validation": ["Architecture review", "Weight integrity", "Adversarial robustness",
                             "Bias evaluation", "Performance benchmark", "Backdoor scan", "Supply chain audit", "Version control"],
        "prompt_filtering": ["Input sanitization", "Injection detection", "Encoding bypass prevention",
                             "Delimiter enforcement", "Role boundary validation", "Context isolation",
                             "Token limit enforcement", "Language detection", "Intent classification", "Output guardrails"],
        "api_security": ["Authentication", "Rate limiting", "Query logging", "IP allowlist",
                         "Output truncation", "CORS policy", "TLS enforcement", "Input schema validation", "Response watermarking"],
        "monitoring": ["Query pattern analysis", "Output anomaly detection", "Drift tracking",
                       "Latency monitoring", "Error rate alerting", "Audit trail", "Real-time dashboard"],
    }
    for stage, checks in stages.items():
        for check_name in checks:
            db.execute("INSERT INTO pipeline_checks (project_id, stage, check_name, passed) VALUES (?, ?, ?, 0)",
                       (project_id, stage, check_name))


def list_projects():
    with get_db() as db:
        return rows_to_list(db.execute("SELECT * FROM projects ORDER BY created_at DESC").fetchall())


def get_project(project_id):
    with get_db() as db:
        return row_to_dict(db.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone())


def update_project(project_id, **kwargs):
    allowed = {"name", "description", "dataset", "architecture", "status", "model_path"}
    fields = {k: v for k, v in kwargs.items() if k in allowed}
    if not fields:
        return
    sets = ", ".join(f"{k} = ?" for k in fields)
    vals = list(fields.values()) + [project_id]
    with get_db() as db:
        db.execute(f"UPDATE projects SET {sets} WHERE id = ?", vals)


def delete_project(project_id):
    with get_db() as db:
        db.execute("DELETE FROM projects WHERE id = ?", (project_id,))


# ══════════════════════════════════
#  PIPELINE
# ══════════════════════════════════

def get_pipeline(project_id):
    """Get pipeline checks grouped by stage."""
    with get_db() as db:
        rows = rows_to_list(db.execute(
            "SELECT * FROM pipeline_checks WHERE project_id = ? ORDER BY stage, id", (project_id,)).fetchall())

    stages = {}
    for r in rows:
        s = r["stage"]
        if s not in stages:
            stages[s] = {"stage": s, "checks": [], "total": 0, "passed": 0}
        stages[s]["checks"].append(r)
        stages[s]["total"] += 1
        if r["passed"]:
            stages[s]["passed"] += 1

    return list(stages.values())


def update_check(check_id, passed, details=""):
    with get_db() as db:
        db.execute("UPDATE pipeline_checks SET passed = ?, details = ?, checked_at = datetime('now') WHERE id = ?",
                   (1 if passed else 0, details, check_id))


def toggle_check(check_id):
    with get_db() as db:
        row = db.execute("SELECT passed FROM pipeline_checks WHERE id = ?", (check_id,)).fetchone()
        if row:
            db.execute("UPDATE pipeline_checks SET passed = ?, checked_at = datetime('now') WHERE id = ?",
                       (0 if row["passed"] else 1, check_id))


# ══════════════════════════════════
#  ATTACK RESULTS
# ══════════════════════════════════

def save_result(project_id, attack_type, params, result_data, status="completed"):
    with get_db() as db:
        db.execute(
            "INSERT INTO attack_results (project_id, attack_type, attack_params, result_data, status) VALUES (?, ?, ?, ?, ?)",
            (project_id, attack_type, json.dumps(params), json.dumps(result_data), status))


def get_results(project_id, limit=50):
    with get_db() as db:
        rows = rows_to_list(db.execute(
            "SELECT * FROM attack_results WHERE project_id = ? ORDER BY created_at DESC LIMIT ?",
            (project_id, limit)).fetchall())
    for r in rows:
        r["attack_params"] = json.loads(r["attack_params"])
        r["result_data"] = json.loads(r["result_data"])
    return rows


# ══════════════════════════════════
#  ALERTS
# ══════════════════════════════════

def create_alert(title, severity="medium", source="", project_id=None):
    with get_db() as db:
        db.execute("INSERT INTO alerts (project_id, severity, title, source) VALUES (?, ?, ?, ?)",
                   (project_id, severity, title, source))


def get_alerts(project_id=None, limit=50):
    with get_db() as db:
        if project_id:
            return rows_to_list(db.execute(
                "SELECT * FROM alerts WHERE project_id = ? ORDER BY created_at DESC LIMIT ?",
                (project_id, limit)).fetchall())
        return rows_to_list(db.execute(
            "SELECT * FROM alerts ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall())


def acknowledge_alert(alert_id):
    with get_db() as db:
        db.execute("UPDATE alerts SET acknowledged = 1 WHERE id = ?", (alert_id,))


def acknowledge_all_alerts(project_id=None):
    with get_db() as db:
        if project_id:
            db.execute("UPDATE alerts SET acknowledged = 1 WHERE project_id = ?", (project_id,))
        else:
            db.execute("UPDATE alerts SET acknowledged = 1")


# ══════════════════════════════════
#  USERS
# ══════════════════════════════════

def create_user(name, email, role="viewer"):
    with get_db() as db:
        db.execute("INSERT INTO users (name, email, role) VALUES (?, ?, ?)", (name, email, role))
        return db.execute("SELECT last_insert_rowid()").fetchone()[0]


def list_users():
    with get_db() as db:
        return rows_to_list(db.execute("SELECT * FROM users ORDER BY created_at").fetchall())


def update_user(user_id, **kwargs):
    allowed = {"name", "email", "role", "status", "mfa"}
    fields = {k: v for k, v in kwargs.items() if k in allowed}
    if not fields:
        return
    sets = ", ".join(f"{k} = ?" for k in fields)
    vals = list(fields.values()) + [user_id]
    with get_db() as db:
        db.execute(f"UPDATE users SET {sets} WHERE id = ?", vals)


def delete_user(user_id):
    with get_db() as db:
        db.execute("DELETE FROM users WHERE id = ?", (user_id,))


# ══════════════════════════════════
#  NOTES (Knowledge Base)
# ══════════════════════════════════

def create_note(title, content="", tags=None, project_id=None, pinned=False):
    with get_db() as db:
        db.execute("INSERT INTO notes (project_id, title, content, tags, pinned) VALUES (?, ?, ?, ?, ?)",
                   (project_id, title, content, json.dumps(tags or []), 1 if pinned else 0))
        return db.execute("SELECT last_insert_rowid()").fetchone()[0]


def list_notes(project_id=None):
    with get_db() as db:
        if project_id:
            rows = rows_to_list(db.execute(
                "SELECT * FROM notes WHERE project_id = ? OR project_id IS NULL ORDER BY pinned DESC, created_at DESC",
                (project_id,)).fetchall())
        else:
            rows = rows_to_list(db.execute("SELECT * FROM notes ORDER BY pinned DESC, created_at DESC").fetchall())
    for r in rows:
        r["tags"] = json.loads(r["tags"])
    return rows


def update_note(note_id, **kwargs):
    allowed = {"title", "content", "tags", "pinned", "project_id"}
    fields = {}
    for k, v in kwargs.items():
        if k in allowed:
            fields[k] = json.dumps(v) if k == "tags" else v
    if not fields:
        return
    sets = ", ".join(f"{k} = ?" for k in fields)
    vals = list(fields.values()) + [note_id]
    with get_db() as db:
        db.execute(f"UPDATE notes SET {sets} WHERE id = ?", vals)


def delete_note(note_id):
    with get_db() as db:
        db.execute("DELETE FROM notes WHERE id = ?", (note_id,))


# ── Dashboard Stats ──

def get_dashboard_stats(project_id=None):
    with get_db() as db:
        if project_id:
            total_checks = db.execute("SELECT COUNT(*) FROM pipeline_checks WHERE project_id = ?", (project_id,)).fetchone()[0]
            passed_checks = db.execute("SELECT COUNT(*) FROM pipeline_checks WHERE project_id = ? AND passed = 1", (project_id,)).fetchone()[0]
            total_alerts = db.execute("SELECT COUNT(*) FROM alerts WHERE project_id = ?", (project_id,)).fetchone()[0]
            unack_alerts = db.execute("SELECT COUNT(*) FROM alerts WHERE project_id = ? AND acknowledged = 0", (project_id,)).fetchone()[0]
            total_results = db.execute("SELECT COUNT(*) FROM attack_results WHERE project_id = ?", (project_id,)).fetchone()[0]
        else:
            total_checks = db.execute("SELECT COUNT(*) FROM pipeline_checks").fetchone()[0]
            passed_checks = db.execute("SELECT COUNT(*) FROM pipeline_checks WHERE passed = 1").fetchone()[0]
            total_alerts = db.execute("SELECT COUNT(*) FROM alerts").fetchone()[0]
            unack_alerts = db.execute("SELECT COUNT(*) FROM alerts WHERE acknowledged = 0").fetchone()[0]
            total_results = db.execute("SELECT COUNT(*) FROM attack_results").fetchone()[0]

        total_users = db.execute("SELECT COUNT(*) FROM users WHERE status = 'active'").fetchone()[0]
        health = round(passed_checks / total_checks * 100) if total_checks > 0 else 0

        return {
            "pipeline_health": health,
            "total_checks": total_checks,
            "passed_checks": passed_checks,
            "active_alerts": unack_alerts,
            "total_alerts": total_alerts,
            "total_results": total_results,
            "active_users": total_users,
        }
