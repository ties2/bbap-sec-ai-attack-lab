"""
BBAP-Sec Sandbox — Model Loader
================================
Auto-detects ML framework from file extension,
loads the model, and provides a unified inference interface.
"""

import os
import json
import logging
import numpy as np

logger = logging.getLogger("sandbox.model_loader")

# Supported frameworks and their extensions
FRAMEWORK_MAP = {
    ".pt":           "pytorch",
    ".pth":          "pytorch",
    ".onnx":         "onnx",
    ".h5":           "tensorflow",
    ".keras":        "tensorflow",
    ".pb":           "tensorflow",
    ".pkl":          "sklearn",
    ".joblib":       "sklearn",
    ".safetensors":  "pytorch",
}


def detect_framework(filename):
    """Detect ML framework from file extension."""
    _, ext = os.path.splitext(filename.lower())
    fw = FRAMEWORK_MAP.get(ext)
    if not fw:
        raise ValueError(f"Unsupported model format: {ext}. Supported: {list(FRAMEWORK_MAP.keys())}")
    return fw


class ModelWrapper:
    """Unified interface for loaded models across frameworks."""

    def __init__(self, model, framework, input_shape=None, num_classes=None):
        self.model = model
        self.framework = framework
        self.input_shape = input_shape
        self.num_classes = num_classes
        self._device = "cpu"

    def predict(self, input_data):
        """Return class predictions."""
        if self.framework == "pytorch":
            return self._predict_pytorch(input_data)
        elif self.framework == "onnx":
            return self._predict_onnx(input_data)
        elif self.framework == "tensorflow":
            return self._predict_tensorflow(input_data)
        elif self.framework == "sklearn":
            return self._predict_sklearn(input_data)

    def predict_proba(self, input_data):
        """Return probability outputs."""
        if self.framework == "pytorch":
            return self._predict_proba_pytorch(input_data)
        elif self.framework == "onnx":
            return self._predict_proba_onnx(input_data)
        elif self.framework == "tensorflow":
            return self._predict_proba_tensorflow(input_data)
        elif self.framework == "sklearn":
            return self._predict_proba_sklearn(input_data)

    def compute_gradient(self, input_data, target_class=None):
        """Compute input gradients (white-box access). Only for PyTorch/TensorFlow."""
        if self.framework == "pytorch":
            return self._gradient_pytorch(input_data, target_class)
        elif self.framework == "tensorflow":
            return self._gradient_tensorflow(input_data, target_class)
        else:
            raise NotImplementedError(f"Gradient computation not supported for {self.framework}")

    def get_model_info(self):
        """Return model metadata."""
        info = {
            "framework": self.framework,
            "input_shape": self.input_shape,
            "num_classes": self.num_classes,
            "device": self._device,
        }
        if self.framework == "pytorch":
            info["parameters"] = sum(p.numel() for p in self.model.parameters())
            info["trainable"] = sum(p.numel() for p in self.model.parameters() if p.requires_grad)
            info["architecture"] = str(type(self.model).__name__)
            info["layers"] = len(list(self.model.modules()))
        elif self.framework == "tensorflow":
            info["parameters"] = self.model.count_params() if hasattr(self.model, "count_params") else None
            info["architecture"] = self.model.name if hasattr(self.model, "name") else "unknown"
        elif self.framework == "sklearn":
            info["type"] = str(type(self.model).__name__)
            info["parameters"] = len(self.model.get_params()) if hasattr(self.model, "get_params") else None
        return info

    # ── PyTorch ──

    def _predict_pytorch(self, input_data):
        import torch
        self.model.eval()
        with torch.no_grad():
            x = torch.tensor(input_data, dtype=torch.float32).to(self._device)
            output = self.model(x)
            return output.argmax(dim=1).cpu().numpy().tolist()

    def _predict_proba_pytorch(self, input_data):
        import torch
        self.model.eval()
        with torch.no_grad():
            x = torch.tensor(input_data, dtype=torch.float32).to(self._device)
            output = torch.softmax(self.model(x), dim=1)
            return output.cpu().numpy().tolist()

    def _gradient_pytorch(self, input_data, target_class=None):
        import torch
        self.model.eval()
        x = torch.tensor(input_data, dtype=torch.float32, requires_grad=True).to(self._device)
        output = self.model(x)
        if target_class is not None:
            loss = output[:, target_class].sum()
        else:
            loss = output.max(dim=1)[0].sum()
        loss.backward()
        return x.grad.cpu().numpy().tolist()

    # ── ONNX ──

    def _predict_onnx(self, input_data):
        x = np.array(input_data, dtype=np.float32)
        input_name = self.model.get_inputs()[0].name
        output = self.model.run(None, {input_name: x})
        return np.argmax(output[0], axis=1).tolist()

    def _predict_proba_onnx(self, input_data):
        x = np.array(input_data, dtype=np.float32)
        input_name = self.model.get_inputs()[0].name
        output = self.model.run(None, {input_name: x})
        from scipy.special import softmax
        return softmax(output[0], axis=1).tolist()

    # ── TensorFlow ──

    def _predict_tensorflow(self, input_data):
        import numpy as np
        x = np.array(input_data, dtype=np.float32)
        output = self.model.predict(x, verbose=0)
        return np.argmax(output, axis=1).tolist()

    def _predict_proba_tensorflow(self, input_data):
        import numpy as np
        x = np.array(input_data, dtype=np.float32)
        output = self.model.predict(x, verbose=0)
        return output.tolist()

    def _gradient_tensorflow(self, input_data, target_class=None):
        import tensorflow as tf
        import numpy as np
        x = tf.Variable(np.array(input_data, dtype=np.float32))
        with tf.GradientTape() as tape:
            output = self.model(x)
            if target_class is not None:
                loss = output[:, target_class]
            else:
                loss = tf.reduce_max(output, axis=1)
        grad = tape.gradient(loss, x)
        return grad.numpy().tolist()

    # ── scikit-learn ──

    def _predict_sklearn(self, input_data):
        x = np.array(input_data, dtype=np.float32)
        if len(x.shape) > 2:
            x = x.reshape(x.shape[0], -1)
        return self.model.predict(x).tolist()

    def _predict_proba_sklearn(self, input_data):
        x = np.array(input_data, dtype=np.float32)
        if len(x.shape) > 2:
            x = x.reshape(x.shape[0], -1)
        if hasattr(self.model, "predict_proba"):
            return self.model.predict_proba(x).tolist()
        else:
            preds = self.model.predict(x)
            return [[1.0 if p == c else 0.0 for c in range(self.num_classes or 10)] for p in preds]


def load_model(filepath, framework=None, device="cpu"):
    """Load a model file and return a ModelWrapper.

    Args:
        filepath: Path to the model file
        framework: Override auto-detection (pytorch, onnx, tensorflow, sklearn)
        device: Device for PyTorch models (cpu or cuda)

    Returns:
        ModelWrapper instance
    """
    if framework is None:
        framework = detect_framework(filepath)

    logger.info(f"Loading model: {filepath} (framework={framework}, device={device})")

    if framework == "pytorch":
        import torch
        if filepath.endswith(".safetensors"):
            from safetensors.torch import load_file
            state_dict = load_file(filepath)
            # Without architecture info, we can only load state_dict
            # The user needs to provide architecture separately
            raise NotImplementedError(
                "SafeTensors requires model architecture definition. "
                "Please upload a full .pt file with torch.save(model, path)."
            )
        else:
            model = torch.load(filepath, map_location=device, weights_only=False)
            if isinstance(model, dict):
                # It's a state_dict, not a full model
                raise ValueError(
                    "File contains a state_dict, not a full model. "
                    "Save with torch.save(model, path), not torch.save(model.state_dict(), path)."
                )
            model.eval()
            model.to(device)

            # Try to infer input shape by inspecting first layer
            input_shape = None
            num_classes = None
            for name, layer in model.named_modules():
                if hasattr(layer, "in_channels") and input_shape is None:
                    input_shape = [layer.in_channels]
                if hasattr(layer, "out_features"):
                    num_classes = layer.out_features

            wrapper = ModelWrapper(model, framework, input_shape, num_classes)
            wrapper._device = device
            return wrapper

    elif framework == "onnx":
        import onnxruntime as ort
        session = ort.InferenceSession(filepath)
        input_info = session.get_inputs()[0]
        input_shape = input_info.shape
        output_info = session.get_outputs()[0]
        num_classes = output_info.shape[-1] if len(output_info.shape) > 1 else None
        return ModelWrapper(session, framework, input_shape, num_classes)

    elif framework == "tensorflow":
        import tensorflow as tf
        model = tf.keras.models.load_model(filepath)
        input_shape = list(model.input_shape[1:]) if model.input_shape else None
        num_classes = model.output_shape[-1] if model.output_shape else None
        return ModelWrapper(model, framework, input_shape, num_classes)

    elif framework == "sklearn":
        import joblib
        model = joblib.load(filepath)
        num_classes = len(model.classes_) if hasattr(model, "classes_") else None
        return ModelWrapper(model, framework, None, num_classes)

    else:
        raise ValueError(f"Unknown framework: {framework}")
