"""
BBAP-Sec — Auth & Team API Routes
====================================
"""

import logging
from flask import Blueprint, request, jsonify, g
from webapp.auth import (
    hash_password, verify_password, create_token,
    login_required, role_required, bbap_only,
    ROLES, DEFAULT_PERMISSIONS
)
import webapp.database as db
from webapp.security import audit_log

logger = logging.getLogger("webapp.auth")

auth_bp = Blueprint("auth", __name__, url_prefix="/api/v2/auth")
team_bp = Blueprint("team", __name__, url_prefix="/api/v2/team")


# ═══════════════════════════════════
#  AUTH ROUTES
# ═══════════════════════════════════

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400

    user = db.get_user_by_email(email)
    if not user or not verify_password(password, user["password_hash"]):
        audit_log("LOGIN_FAILED", user=email, ip=request.remote_addr)   # ADD
        return jsonify({"error": "Invalid email or password"}), 401

    if not user.get("active", True):
        return jsonify({"error": "Account is disabled"}), 403

    token = create_token(user)
    db.update_user_last_login(user["id"])
    #update
    audit_log("LOGIN_SUCCESS", user=email, ip=request.remote_addr)      # ADD

    return jsonify({
            "token": token,
            "user": {
                "id": user["id"],
                "name": user["name"],
                "email": user["email"],
                "role": user["role"],
                "group": ROLES.get(user["role"], {}).get("group", "client"),
                "group_name": user.get("group_name", ""),
            }
        })


@auth_bp.route("/me", methods=["GET"])
@login_required
def me():
    user = db.get_user(g.current_user["user_id"])
    if not user:
        return jsonify({"error": "User not found"}), 404

    role_info = ROLES.get(user["role"], {})
    return jsonify({
        "id": user["id"],
        "name": user["name"],
        "email": user["email"],
        "role": user["role"],
        "role_label": role_info.get("label", user["role"]),
        "group": role_info.get("group", "client"),
        "group_name": user.get("group_name", ""),
        "permissions": DEFAULT_PERMISSIONS.get(user["role"], []),
        "active": user.get("active", True),
    })


@auth_bp.route("/change-password", methods=["POST"])
@login_required
def change_password():
    data = request.get_json()
    current = data.get("current_password", "")
    new_pw = data.get("new_password", "")

    if len(new_pw) < 8:
        return jsonify({"error": "Password must be at least 8 characters"}), 400

    user = db.get_user(g.current_user["user_id"])
    if not verify_password(current, user["password_hash"]):
        return jsonify({"error": "Current password is incorrect"}), 401

    db.update_user_password(user["id"], hash_password(new_pw))
    return jsonify({"message": "Password updated"})


# ═══════════════════════════════════
#  USER MANAGEMENT
# ═══════════════════════════════════

@team_bp.route("/users", methods=["GET"])
@login_required
def list_users():
    group = g.current_user.get("group", "")
    users = db.get_all_users()

    if group != "bbap-sec":
        user = db.get_user(g.current_user["user_id"])
        my_group = user.get("group_name", "")
        users = [u for u in users if u.get("group_name") == my_group]

    safe_users = []
    for u in users:
        role_info = ROLES.get(u["role"], {})
        safe_users.append({
            "id": u["id"],
            "name": u["name"],
            "email": u["email"],
            "role": u["role"],
            "role_label": role_info.get("label", u["role"]),
            "group": role_info.get("group", "client"),
            "group_name": u.get("group_name", ""),
            "active": bool(u.get("active", True)),
            "last_login": u.get("last_login"),
            "created_at": u.get("created_at"),
        })

    return jsonify({"users": safe_users, "total": len(safe_users)})


@team_bp.route("/users", methods=["POST"])
@role_required("bbap_admin", "bbap_lead", "client_admin")
def create_user():
    data = request.get_json()
    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    role = data.get("role", "client_viewer")
    group_name = data.get("group_name", "")

    if not name or not email or not password:
        return jsonify({"error": "name, email, and password required"}), 400

    if len(password) < 8:
        return jsonify({"error": "Password must be at least 8 characters"}), 400

    if role not in ROLES:
        return jsonify({"error": f"Invalid role. Options: {list(ROLES.keys())}"}), 400

    caller_group = g.current_user.get("group", "")
    role_group = ROLES[role]["group"]
    if caller_group == "client" and role_group == "bbap-sec":
        return jsonify({"error": "Cannot create BBAP-Sec internal users"}), 403

    if db.get_user_by_email(email):
        return jsonify({"error": "Email already registered"}), 409

    user_id = db.create_user(name, email, hash_password(password), role, group_name)
    return jsonify({"id": user_id, "message": f"User {email} created with role {role}"}), 201


@team_bp.route("/users/<int:user_id>", methods=["PUT"])
@role_required("bbap_admin", "bbap_lead")
def update_user(user_id):
    data = request.get_json()
    updates = {}
    if "role" in data:
        if data["role"] not in ROLES:
            return jsonify({"error": f"Invalid role: {data['role']}"}), 400
        updates["role"] = data["role"]
    if "active" in data:
        updates["active"] = 1 if data["active"] else 0
    if "group_name" in data:
        updates["group_name"] = data["group_name"]
    if "name" in data:
        updates["name"] = data["name"]

    if not updates:
        return jsonify({"error": "No fields to update"}), 400

    db.update_user(user_id, **updates)
    return jsonify({"message": "User updated"})


@team_bp.route("/users/<int:user_id>", methods=["DELETE"])
@role_required("bbap_admin")
def deactivate_user(user_id):
    db.update_user(user_id, active=0)
    return jsonify({"message": "User deactivated"})


# ═══════════════════════════════════
#  GROUPS
# ═══════════════════════════════════

@team_bp.route("/groups", methods=["GET"])
@login_required
def list_groups():
    groups = db.get_groups()
    return jsonify({"groups": groups})


@team_bp.route("/groups", methods=["POST"])
@role_required("bbap_admin", "bbap_lead")
def create_group():
    data = request.get_json()
    name = data.get("name", "").strip()
    if not name:
        return jsonify({"error": "Group name required"}), 400
    group_id = db.create_group(name, data.get("description", ""))
    return jsonify({"id": group_id, "message": f"Group '{name}' created"}), 201


# ═══════════════════════════════════
#  PROJECT ASSIGNMENTS
# ═══════════════════════════════════

@team_bp.route("/projects/<int:project_id>/members", methods=["GET"])
@login_required
def project_members(project_id):
    members = db.get_project_members(project_id)
    return jsonify({"members": members, "project_id": project_id})


@team_bp.route("/projects/<int:project_id>/members", methods=["POST"])
@role_required("bbap_admin", "bbap_lead", "bbap_engineer")
def assign_member(project_id):
    data = request.get_json()
    user_id = data.get("user_id")
    role_in_project = data.get("role", "viewer")
    allowed_sections = data.get("allowed_sections", None)

    if not user_id:
        return jsonify({"error": "user_id required"}), 400

    db.assign_project_member(project_id, user_id, role_in_project, allowed_sections)
    return jsonify({"message": f"User {user_id} assigned to project {project_id}"}), 201


@team_bp.route("/projects/<int:project_id>/members/<int:user_id>", methods=["DELETE"])
@role_required("bbap_admin", "bbap_lead")
def remove_member(project_id, user_id):
    db.remove_project_member(project_id, user_id)
    return jsonify({"message": "Member removed"})


@team_bp.route("/projects/<int:project_id>/permissions", methods=["PUT"])
@role_required("bbap_admin")
def update_project_permissions(project_id):
    data = request.get_json()
    user_id = data.get("user_id")
    sections = data.get("sections", [])

    if not user_id:
        return jsonify({"error": "user_id required"}), 400

    db.set_project_permissions(project_id, user_id, sections)
    return jsonify({"message": f"Permissions updated for user {user_id} on project {project_id}"})


# ═══════════════════════════════════
#  ROLES INFO
# ═══════════════════════════════════

@team_bp.route("/roles", methods=["GET"])
@login_required
def list_roles():
    roles = []
    for role_id, info in ROLES.items():
        roles.append({
            "id": role_id,
            "label": info["label"],
            "group": info["group"],
            "level": info["level"],
            "default_sections": DEFAULT_PERMISSIONS.get(role_id, []),
        })
    return jsonify({"roles": sorted(roles, key=lambda r: -r["level"])})
