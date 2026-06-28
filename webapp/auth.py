"""
BBAP-Sec — Authentication & Authorization
===========================================
JWT-based auth with bcrypt password hashing.
Two group types: bbap-sec (internal) and client.
"""

import os
import jwt
import bcrypt
import logging
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, g

logger = logging.getLogger("auth")

SECRET_KEY = os.environ.get("JWT_SECRET", "bbap-sec-change-this-in-production")
TOKEN_EXPIRY_HOURS = int(os.environ.get("TOKEN_EXPIRY_HOURS", "8"))

# ── Role Definitions ──

ROLES = {
    # BBAP-Sec internal roles
    "bbap_admin":    {"group": "bbap-sec", "level": 100, "label": "BBAP-Sec Admin"},
    "bbap_lead":     {"group": "bbap-sec", "level": 80,  "label": "BBAP-Sec Lead"},
    "bbap_engineer": {"group": "bbap-sec", "level": 60,  "label": "BBAP-Sec Engineer"},
    "bbap_analyst":  {"group": "bbap-sec", "level": 40,  "label": "BBAP-Sec Analyst"},

    # Client roles
    "client_admin":  {"group": "client", "level": 50,  "label": "Client Admin"},
    "client_viewer": {"group": "client", "level": 20,  "label": "Client Viewer"},
}

# ── Section Permissions ──
# Which sections each role can access by default.
# bbap_admin can override client access per-project.

DEFAULT_PERMISSIONS = {
    "bbap_admin":    ["*"],  # everything
    "bbap_lead":     ["overview", "target", "layers", "findings", "pipeline", "atlas",
                      "report", "governance", "monitoring", "team", "knowledge", "alerts", "settings"],
    "bbap_engineer": ["overview", "target", "layers", "findings", "pipeline", "atlas",
                      "report", "governance", "monitoring", "knowledge"],
    "bbap_analyst":  ["overview", "findings", "pipeline", "atlas", "report",
                      "governance", "monitoring", "knowledge"],
    "client_admin":  ["overview", "findings", "pipeline", "report", "governance"],
    "client_viewer": ["overview", "findings", "report"],
}


# ── Password Hashing ──

def hash_password(password):
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password, hashed):
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


# ── JWT ──

def create_token(user):
    """Create a JWT token for a user dict."""
    payload = {
        "user_id": user["id"],
        "email": user["email"],
        "role": user["role"],
        "group": ROLES.get(user["role"], {}).get("group", "client"),
        "exp": datetime.utcnow() + timedelta(hours=TOKEN_EXPIRY_HOURS),
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")


def decode_token(token):
    """Decode and validate a JWT token."""
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


# ── Decorators ──

def login_required(f):
    """Require valid JWT token."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]

        if not token:
            return jsonify({"error": "Authentication required"}), 401

        payload = decode_token(token)
        if not payload:
            return jsonify({"error": "Invalid or expired token"}), 401

        g.current_user = payload
        return f(*args, **kwargs)
    return decorated


def role_required(*allowed_roles):
    """Require specific roles."""
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated(*args, **kwargs):
            user_role = g.current_user.get("role", "")
            if user_role not in allowed_roles and "bbap_admin" != user_role:
                return jsonify({"error": "Insufficient permissions"}), 403
            return f(*args, **kwargs)
        return decorated
    return decorator


def bbap_only(f):
    """Restrict to BBAP-Sec internal users."""
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        group = g.current_user.get("group", "")
        if group != "bbap-sec":
            return jsonify({"error": "BBAP-Sec internal access only"}), 403
        return f(*args, **kwargs)
    return decorated


def can_access_section(user_payload, section, project_permissions=None):
    """Check if a user can access a specific dashboard section.

    Args:
        user_payload: decoded JWT payload
        section: section id (e.g. "findings", "target", "layers")
        project_permissions: optional per-project overrides from DB
    """
    role = user_payload.get("role", "")
    defaults = DEFAULT_PERMISSIONS.get(role, [])

    if "*" in defaults:
        return True

    # Check per-project overrides (admin can restrict/grant sections per client)
    if project_permissions:
        allowed = project_permissions.get(str(user_payload.get("user_id")), None)
        if allowed is not None:
            return section in allowed

    return section in defaults
