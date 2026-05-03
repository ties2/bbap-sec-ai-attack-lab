# ============================================
# BBAP-Sec AI Attack Lab — Dockerfile
# ============================================

FROM python:3.11-slim

LABEL maintainer="BBAP-Sec"
LABEL description="Educational AI Security Testing Pipeline"
LABEL version="1.0.0"

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Download datasets at build time
RUN python datasets/download_datasets.py

# Expose web dashboard port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:5000/ || exit 1

# Default: run the web dashboard
CMD ["python", "webapp/app.py"]
