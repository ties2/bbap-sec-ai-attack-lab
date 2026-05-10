"""
BBAP-Sec Sandbox — API Routes
===============================
REST endpoints for sandbox lifecycle management.
Mount on the main Flask app with:
    from webapp.routes_sandbox import sandbox_bp
    app.register_blueprint(sandbox_bp)
"""

import os
import logging
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from src.sandbox.manager import SandboxManager

logger = logging.getLogger("webapp.sandbox")

sandbox_bp = Blueprint("sandbox", __name__, url_prefix="/api/v2/sandbox")

# Upload config
UPLOAD_DIR = os.environ.get("MODEL_UPLOAD_DIR", "/tmp/bbap-sec-models")
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB
ALLOWED_EXTENSIONS = {".pt", ".pth", ".onnx", ".h5", ".keras", ".pb", ".pkl", ".joblib", ".safetensors"}

# Singleton manager (initialized when blueprint is registered)
_manager = None


def get_manager():
    global _manager
    if _manager is None:
        _manager = SandboxManager()
    return _manager


def _validate_model_file(filename):
    """Check if the file extension is supported."""
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"Unsupported file type: {ext}. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
    return True, None


# ── Routes ──


@sandbox_bp.route("/create", methods=["POST"])
def create_sandbox():
    """Create a new sandbox from an uploaded model file.

    Accepts multipart/form-data with:
        - file: The model file (.pt, .onnx, .h5, etc.)
        - engagement_id: ID of the parent engagement
        - framework: (optional) Override framework detection
        - gpu: (optional) "true" to enable GPU
    """
    manager = get_manager()

    # Validate engagement_id
    project_id = request.form.get("project_id")
    if not project_id:
        return jsonify({"error": "project_id is required"}), 400

    try:
        project_id = int(project_id)
    except ValueError:
        return jsonify({"error": "project_id must be an integer"}), 400

    # Check for file upload
    if "file" not in request.files:
        return jsonify({"error": "No model file uploaded. Send as multipart/form-data with field name 'file'"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    # Validate extension
    valid, error = _validate_model_file(file.filename)
    if not valid:
        return jsonify({"error": error}), 400

    # Save uploaded file
    filename = secure_filename(file.filename)
    upload_dir = os.path.join(UPLOAD_DIR, "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    filepath = os.path.join(upload_dir, f"eng{project_id}_{filename}")
    file.save(filepath)

    # Check file size
    file_size = os.path.getsize(filepath)
    if file_size > MAX_FILE_SIZE:
        os.remove(filepath)
        return jsonify({"error": f"File too large ({file_size} bytes). Max: {MAX_FILE_SIZE}"}), 400

    if file_size == 0:
        os.remove(filepath)
        return jsonify({"error": "File is empty"}), 400

    # Optional parameters
    framework = request.form.get("framework", None)
    gpu = request.form.get("gpu", "false").lower() == "true"

    logger.info(f"Creating sandbox: project={project_id}, file={filename}, framework={framework}, gpu={gpu}")

    try:
        result = manager.create(
            project_id=project_id,
            model_path=filepath,
            framework=framework,
            gpu=gpu,
        )
        # Clean up the upload copy (manager copies to its own directory)
        os.remove(filepath)
        return jsonify(result), 201
    except Exception as e:
        logger.error(f"Sandbox creation failed: {e}")
        os.remove(filepath)
        return jsonify({"error": str(e)}), 500


@sandbox_bp.route("/<int:sandbox_id>", methods=["GET"])
def sandbox_status(sandbox_id):
    """Get sandbox status and stats."""
    manager = get_manager()
    result = manager.status(sandbox_id)
    if result is None:
        return jsonify({"error": "Sandbox not found"}), 404
    return jsonify(result)


@sandbox_bp.route("/<int:sandbox_id>", methods=["DELETE"])
def destroy_sandbox(sandbox_id):
    """Stop and remove a sandbox."""
    manager = get_manager()
    result = manager.destroy(sandbox_id)
    if "error" in result:
        return jsonify(result), 404
    return jsonify(result)


@sandbox_bp.route("/list", methods=["GET"])
def list_sandboxes():
    """List all sandboxes, optionally filtered by project_id."""
    manager = get_manager()
    project_id = request.args.get("project_id", type=int)
    sandboxes = manager.list_sandboxes(project_id=project_id)
    return jsonify({"sandboxes": sandboxes, "total": len(sandboxes)})


@sandbox_bp.route("/<int:sandbox_id>/predict", methods=["POST"])
def sandbox_predict(sandbox_id):
    """Forward a prediction request to the sandbox.

    Body: { "input": [[...]] }
    """
    manager = get_manager()
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body required"}), 400
    result = manager.proxy_request(sandbox_id, "/predict", method="POST", data=data)
    if "error" in result:
        return jsonify(result), 502
    return jsonify(result)


@sandbox_bp.route("/<int:sandbox_id>/predict_proba", methods=["POST"])
def sandbox_predict_proba(sandbox_id):
    """Forward a probability prediction request to the sandbox."""
    manager = get_manager()
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body required"}), 400
    result = manager.proxy_request(sandbox_id, "/predict_proba", method="POST", data=data)
    if "error" in result:
        return jsonify(result), 502
    return jsonify(result)


@sandbox_bp.route("/<int:sandbox_id>/gradient", methods=["POST"])
def sandbox_gradient(sandbox_id):
    """Forward a gradient computation request to the sandbox (white-box).

    Body: { "input": [[...]], "target_class": 3 }
    """
    manager = get_manager()
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body required"}), 400
    result = manager.proxy_request(sandbox_id, "/gradient", method="POST", data=data)
    if "error" in result:
        return jsonify(result), 502
    return jsonify(result)


@sandbox_bp.route("/<int:sandbox_id>/model_info", methods=["GET"])
def sandbox_model_info(sandbox_id):
    """Get model metadata from the sandbox."""
    manager = get_manager()
    result = manager.proxy_request(sandbox_id, "/model_info", method="GET")
    if "error" in result:
        return jsonify(result), 502
    return jsonify(result)


@sandbox_bp.route("/cleanup", methods=["POST"])
def cleanup_expired():
    """Destroy all expired sandboxes."""
    manager = get_manager()
    destroyed = manager.cleanup_expired()
    return jsonify({"destroyed": destroyed})
