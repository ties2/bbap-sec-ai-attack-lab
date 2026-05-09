"""
BBAP-Sec Sandbox — Inference API
=================================
Runs inside the Docker sandbox container.
Exposes /predict, /predict_proba, /gradient, /model_info endpoints.
The model file is mounted at /model/model_file by the sandbox manager.
"""

import os
import sys
import json
import time
import logging
import traceback
from flask import Flask, request, jsonify
from model_loader import load_model, detect_framework

# ── Configuration ──
MODEL_DIR = os.environ.get("MODEL_DIR", "/model")
MODEL_FILE = os.environ.get("MODEL_FILE", "")
DEVICE = os.environ.get("DEVICE", "cpu")
PORT = int(os.environ.get("PORT", "5000"))
MAX_BATCH_SIZE = int(os.environ.get("MAX_BATCH_SIZE", "128"))

# ── Setup ──
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("sandbox_api")

app = Flask(__name__)
model_wrapper = None
query_count = 0
start_time = time.time()


def get_model():
    """Load the model on first request (lazy loading)."""
    global model_wrapper
    if model_wrapper is not None:
        return model_wrapper

    model_path = os.path.join(MODEL_DIR, MODEL_FILE)
    if not MODEL_FILE or not os.path.exists(model_path):
        # Try to find any model file in the directory
        for f in os.listdir(MODEL_DIR):
            ext = os.path.splitext(f)[1].lower()
            if ext in (".pt", ".pth", ".onnx", ".h5", ".keras", ".pb", ".pkl", ".joblib", ".safetensors"):
                model_path = os.path.join(MODEL_DIR, f)
                logger.info(f"Auto-detected model file: {f}")
                break
        else:
            raise FileNotFoundError(f"No model file found in {MODEL_DIR}")

    model_wrapper = load_model(model_path, device=DEVICE)
    logger.info(f"Model loaded: {model_wrapper.get_model_info()}")
    return model_wrapper


@app.route("/health", methods=["GET"])
def health():
    """Health check."""
    uptime = round(time.time() - start_time, 1)
    model_loaded = model_wrapper is not None
    return jsonify({
        "status": "healthy",
        "model_loaded": model_loaded,
        "uptime_seconds": uptime,
        "query_count": query_count,
        "device": DEVICE,
    })


@app.route("/model_info", methods=["GET"])
def model_info():
    """Return model metadata."""
    try:
        wrapper = get_model()
        info = wrapper.get_model_info()
        info["query_count"] = query_count
        info["uptime_seconds"] = round(time.time() - start_time, 1)
        return jsonify(info)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/predict", methods=["POST"])
def predict():
    """Black-box prediction: returns class labels."""
    global query_count
    try:
        wrapper = get_model()
        data = request.get_json()
        if not data or "input" not in data:
            return jsonify({"error": "Missing 'input' field in request body"}), 400

        input_data = data["input"]

        # Validate batch size
        if isinstance(input_data, list) and len(input_data) > MAX_BATCH_SIZE:
            return jsonify({"error": f"Batch size {len(input_data)} exceeds max {MAX_BATCH_SIZE}"}), 400

        query_count += 1
        predictions = wrapper.predict(input_data)
        return jsonify({
            "predictions": predictions,
            "query_id": query_count,
        })
    except Exception as e:
        logger.error(f"Predict error: {e}\n{traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500


@app.route("/predict_proba", methods=["POST"])
def predict_proba():
    """Black-box prediction: returns probability distributions."""
    global query_count
    try:
        wrapper = get_model()
        data = request.get_json()
        if not data or "input" not in data:
            return jsonify({"error": "Missing 'input' field in request body"}), 400

        input_data = data["input"]
        if isinstance(input_data, list) and len(input_data) > MAX_BATCH_SIZE:
            return jsonify({"error": f"Batch size exceeds max {MAX_BATCH_SIZE}"}), 400

        query_count += 1
        probabilities = wrapper.predict_proba(input_data)
        return jsonify({
            "probabilities": probabilities,
            "query_id": query_count,
        })
    except Exception as e:
        logger.error(f"Predict_proba error: {e}\n{traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500


@app.route("/gradient", methods=["POST"])
def gradient():
    """White-box access: compute input gradients."""
    global query_count
    try:
        wrapper = get_model()
        if wrapper.framework not in ("pytorch", "tensorflow"):
            return jsonify({"error": f"Gradient not supported for {wrapper.framework}"}), 400

        data = request.get_json()
        if not data or "input" not in data:
            return jsonify({"error": "Missing 'input' field"}), 400

        input_data = data["input"]
        target_class = data.get("target_class", None)

        if isinstance(input_data, list) and len(input_data) > MAX_BATCH_SIZE:
            return jsonify({"error": f"Batch size exceeds max {MAX_BATCH_SIZE}"}), 400

        query_count += 1
        gradients = wrapper.compute_gradient(input_data, target_class)
        return jsonify({
            "gradients": gradients,
            "query_id": query_count,
        })
    except NotImplementedError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Gradient error: {e}\n{traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500


@app.route("/stats", methods=["GET"])
def stats():
    """Query statistics for rate-limit monitoring."""
    return jsonify({
        "query_count": query_count,
        "uptime_seconds": round(time.time() - start_time, 1),
        "queries_per_minute": round(query_count / max((time.time() - start_time) / 60, 0.01), 2),
    })


if __name__ == "__main__":
    logger.info("=" * 50)
    logger.info("BBAP-Sec Sandbox API starting")
    logger.info(f"  Model dir:  {MODEL_DIR}")
    logger.info(f"  Model file: {MODEL_FILE or '(auto-detect)'}")
    logger.info(f"  Device:     {DEVICE}")
    logger.info(f"  Port:       {PORT}")
    logger.info(f"  Max batch:  {MAX_BATCH_SIZE}")
    logger.info("=" * 50)

    # Pre-load model at startup
    try:
        get_model()
        logger.info("Model pre-loaded successfully")
    except Exception as e:
        logger.warning(f"Model pre-load failed (will retry on first request): {e}")

    app.run(host="0.0.0.0", port=PORT, debug=False)
