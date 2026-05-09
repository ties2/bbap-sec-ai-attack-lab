# BBAP-Sec Sandbox Container
# Isolated environment for loading and testing uploaded ML models.
# Supports PyTorch, ONNX, TensorFlow, and scikit-learn.

FROM python:3.11-slim

LABEL maintainer="BBAP-Sec"
LABEL description="AI model sandbox for security testing"

# Prevent interactive prompts
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd -m -s /bin/bash sandbox
WORKDIR /app

# Install ML frameworks
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy sandbox API code
COPY sandbox_api.py .
COPY model_loader.py .

# Model directory (mounted at runtime)
RUN mkdir -p /model && chown sandbox:sandbox /model

# Switch to non-root
USER sandbox

# Expose inference API port (mapped dynamically by manager)
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')" || exit 1

ENTRYPOINT ["python", "sandbox_api.py"]
