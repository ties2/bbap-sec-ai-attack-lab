"""
BBAP-Sec — Database Auth Methods
==================================
ADD these to your existing webapp/database.py class.

1. Add the SQL in create_auth_tables() to your _create_tables() method
2. Add all the methods below to your Database class
3. Call create_auth_tables() once (or add to _create_tables)
"""

import json
from datetime import datetime


# ─── ADD THIS SQL TO YOUR _create_tables() METHOD ───

AUTH_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'client_viewer',
    group_name TEXT DEFAULT '',
    active BOOLEAN DEFAULT 1,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS project_members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    role TEXT DEFAULT 'viewer',
    allowed_sections TEXT,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(project_id, user_id)
);

-- Seed default admin (password: admin123 — CHANGE IN PRODUCTION)
INSERT OR IGNORE INTO users (id, name, email, password_hash, role, group_name)
VALUES (1, 'Admin', 'admin@bbap-sec.com',
        '$2b$12$LJ3m4ys3Lz0QFz3GrXdYZe5Y5Z5Z5Z5Z5Z5Z5Z5Z5Z5Z5Z5Z5Z',
        'bbap_admin', 'BBAP-Sec');

INSERT OR IGNORE INTO groups (id, name, description)
VALUES (1, 'BBAP-Sec', 'BBAP-Sec internal team');
"""


# ─── ADD THESE METHODS TO YOUR Database CLASS ───


def create_auth_tables(self):
    """Run once to create auth tables. Call from _create_tables() or separately."""
    self.conn.executescript(AUTH_TABLES_SQL)
    self.conn.commit()


# ── Users ──

def create_user(self, name, email, password_hash, role, group_name=""):
    cursor = self.conn.execute(
        '''INSERT INTO users (name, email, password_hash, role, group_name)
           VALUES (?, ?, ?, ?, ?)''',
        (name, email, password_hash, role, group_name)
    )
    self.conn.commit()
    return cursor.lastrowid


def get_user(self, user_id):
    row = self.conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    return dict(row) if row else None


def get_user_by_email(self, email):
    row = self.conn.execute('SELECT * FROM users WHERE email = ?', (email.lower(),)).fetchone()
    return dict(row) if row else None


def get_all_users(self):
    rows = self.conn.execute('SELECT * FROM users ORDER BY created_at DESC').fetchall()
    return [dict(r) for r in rows]


def update_user(self, user_id, **kwargs):
    allowed = {"name", "role", "group_name", "active"}
    fields = {k: v for k, v in kwargs.items() if k in allowed}
    if not fields:
        return
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [user_id]
    self.conn.execute(f'UPDATE users SET {set_clause} WHERE id = ?', values)
    self.conn.commit()


def update_user_password(self, user_id, password_hash):
    self.conn.execute('UPDATE users SET password_hash = ? WHERE id = ?', (password_hash, user_id))
    self.conn.commit()


def update_user_last_login(self, user_id):
    self.conn.execute('UPDATE users SET last_login = ? WHERE id = ?',
                      (datetime.now().isoformat(), user_id))
    self.conn.commit()


# ── Groups ──

def get_groups(self):
    rows = self.conn.execute('SELECT * FROM groups ORDER BY name').fetchall()
    result = []
    for r in rows:
        g = dict(r)
        g["member_count"] = self.conn.execute(
            'SELECT COUNT(*) FROM users WHERE group_name = ?', (g["name"],)
        ).fetchone()[0]
        result.append(g)
    return result


def create_group(self, name, description=""):
    cursor = self.conn.execute(
        'INSERT INTO groups (name, description) VALUES (?, ?)', (name, description)
    )
    self.conn.commit()
    return cursor.lastrowid


# ── Project Members ──

def get_project_members(self, project_id):
    rows = self.conn.execute('''
        SELECT pm.*, u.name, u.email, u.role as user_role, u.group_name
        FROM project_members pm
        JOIN users u ON pm.user_id = u.id
        WHERE pm.project_id = ?
        ORDER BY pm.assigned_at
    ''', (project_id,)).fetchall()
    return [dict(r) for r in rows]


def assign_project_member(self, project_id, user_id, role="viewer", allowed_sections=None):
    sections_json = json.dumps(allowed_sections) if allowed_sections else None
    self.conn.execute('''
        INSERT OR REPLACE INTO project_members (project_id, user_id, role, allowed_sections)
        VALUES (?, ?, ?, ?)
    ''', (project_id, user_id, role, sections_json))
    self.conn.commit()


def remove_project_member(self, project_id, user_id):
    self.conn.execute(
        'DELETE FROM project_members WHERE project_id = ? AND user_id = ?',
        (project_id, user_id)
    )
    self.conn.commit()


def set_project_permissions(self, project_id, user_id, sections):
    self.conn.execute('''
        UPDATE project_members SET allowed_sections = ?
        WHERE project_id = ? AND user_id = ?
    ''', (json.dumps(sections), project_id, user_id))
    self.conn.commit()


def get_user_project_permissions(self, project_id, user_id):
    row = self.conn.execute('''
        SELECT allowed_sections FROM project_members
        WHERE project_id = ? AND user_id = ?
    ''', (project_id, user_id)).fetchone()
    if row and row["allowed_sections"]:
        return json.loads(row["allowed_sections"])
    return None
