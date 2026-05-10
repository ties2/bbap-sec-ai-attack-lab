# Sandbox Setup — Integration Guide

## Overview

The sandbox provides isolated Docker containers for loading and testing uploaded ML models. Each engagement can spin up a sandbox that wraps a model file with an inference API, enabling both black-box and white-box attack testing.

## File Map

```
# NEW FILES — add to your project:

sandbox/                          # Sandbox container (builds to Docker image)
├── Dockerfile                    # Python 3.11 + PyTorch + ONNX + TF + sklearn
├── sandbox_api.py                # Flask API inside container (/predict, /gradient, etc.)
├── model_loader.py               # Auto-detect framework, load model, unified wrapper
└── requirements.txt              # Sandbox Python dependencies

src/sandbox/                      # Host-side sandbox management
├── __init__.py
└── manager.py                    # Docker SDK — create/destroy/status containers

webapp/
└── routes_sandbox.py             # REST API routes for sandbox CRUD

docker-compose.yml                # Updated with sandbox support
```

## Step 1: Build the Sandbox Image

```bash
cd sandbox
docker build -t bbap-sec-sandbox:latest .
```

This creates a ~4GB image with PyTorch, ONNX Runtime, TensorFlow, and scikit-learn.
For a lighter image, comment out unused frameworks in `sandbox/requirements.txt`.

## Step 2: Install Host Dependencies

The main webapp needs the Docker SDK to manage containers:

```bash
pip install docker requests
```

Add to your `requirements.txt`:
```
docker>=7.0
```

## Step 3: Register the Sandbox Routes

In `webapp/app.py`, register the sandbox blueprint:

```python
from webapp.routes_sandbox import sandbox_bp
app.register_blueprint(sandbox_bp)
```

## Step 4: Mount Docker Socket

The webapp needs access to the Docker daemon to create sandbox containers.

If running the webapp directly (not in Docker):
```bash
# No changes needed — Docker SDK connects via /var/run/docker.sock by default
python -m webapp.app
```

If running the webapp in Docker, mount the socket (already in docker-compose.yml):
```yaml
volumes:
  - /var/run/docker.sock:/var/run/docker.sock
```

## Step 5: Database Migration

Add the sandboxes table to `webapp/database.py`:

```python
def _create_tables(self):
    # ... existing tables ...

    self.conn.execute('''
        CREATE TABLE IF NOT EXISTS sandboxes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            engagement_id INTEGER NOT NULL,
            container_id TEXT,
            status TEXT DEFAULT 'creating',
            framework TEXT,
            model_filename TEXT,
            model_size_bytes INTEGER,
            port INTEGER,
            gpu_enabled BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            destroyed_at TIMESTAMP,
            error TEXT,
            FOREIGN KEY (project_id=1) REFERENCES engagements(id)
        )
    ''')
```

And add these methods:

```python
def save_sandbox(self, sandbox_dict):
    self.conn.execute(
        '''INSERT INTO sandboxes (id, engagement_id, container_id, status,
           framework, model_filename, model_size_bytes, port, gpu_enabled)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
        (sandbox_dict['id'], sandbox_dict['engagement_id'],
         sandbox_dict['container_id'], sandbox_dict['status'],
         sandbox_dict['framework'], sandbox_dict['model_filename'],
         sandbox_dict['model_size_bytes'], sandbox_dict['port'],
         sandbox_dict['gpu_enabled'])
    )
    self.conn.commit()

def update_sandbox_status(self, sandbox_id, status):
    self.conn.execute(
        'UPDATE sandboxes SET status = ?, destroyed_at = CURRENT_TIMESTAMP WHERE id = ?',
        (status, sandbox_id)
    )
    self.conn.commit()

def get_sandboxes(self, engagement_id=None):
    if engagement_id:
        rows = self.conn.execute(
            'SELECT * FROM sandboxes WHERE engagement_id = ? ORDER BY created_at DESC',
            (engagement_id,)
        ).fetchall()
    else:
        rows = self.conn.execute(
            'SELECT * FROM sandboxes ORDER BY created_at DESC'
        ).fetchall()
    return [dict(r) for r in rows]
```

## API Reference

### Sandbox Lifecycle

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v2/sandbox/create` | Upload model file, create sandbox container |
| `GET` | `/api/v2/sandbox/{id}` | Get sandbox status and stats |
| `DELETE` | `/api/v2/sandbox/{id}` | Stop and destroy sandbox |
| `GET` | `/api/v2/sandbox/list` | List all sandboxes (filter: `?engagement_id=1`) |
| `POST` | `/api/v2/sandbox/cleanup` | Destroy expired sandboxes |

### Model Inference (proxied through sandbox)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v2/sandbox/{id}/predict` | Class predictions (black-box) |
| `POST` | `/api/v2/sandbox/{id}/predict_proba` | Probability outputs (black-box) |
| `POST` | `/api/v2/sandbox/{id}/gradient` | Input gradients (white-box, PyTorch/TF only) |
| `GET` | `/api/v2/sandbox/{id}/model_info` | Model metadata (params, architecture, etc.) |

### Create Sandbox — Request

```bash
curl -X POST http://localhost:5000/api/v2/sandbox/create \
  -F "file=@models/resnet50.pt" \
  -F "engagement_id=1" \
  -F "framework=pytorch" \
  -F "gpu=false"
```

### Create Sandbox — Response

```json
{
  "id": 1,
  "engagement_id": 1,
  "container_id": "a1b2c3d4e5f6",
  "port": 5100,
  "framework": "pytorch",
  "model_filename": "resnet50.pt",
  "model_size_bytes": 102456789,
  "gpu_enabled": false,
  "status": "running",
  "api_url": "http://localhost:5100",
  "created_at": "2026-05-09T14:30:00"
}
```

### Predict — Request

```bash
curl -X POST http://localhost:5000/api/v2/sandbox/1/predict \
  -H "Content-Type: application/json" \
  -d '{"input": [[[0.5, 0.3, ...], ...]]}'
```

### Gradient (White-Box) — Request

```bash
curl -X POST http://localhost:5000/api/v2/sandbox/1/gradient \
  -H "Content-Type: application/json" \
  -d '{"input": [[[0.5, 0.3, ...], ...]], "target_class": 7}'
```

## Architecture

```
┌──────────────────────────────────────────────────────┐
│  BBAP-Sec Webapp (host or Docker container)          │
│                                                      │
│  Dashboard ──► routes_sandbox.py ──► SandboxManager  │
│                                          │           │
│                          Docker SDK      │           │
│                                          ▼           │
│  ┌──────────────────┐  ┌──────────────────┐          │
│  │ Sandbox 1        │  │ Sandbox 2        │          │
│  │ (Docker)         │  │ (Docker)         │          │
│  │                  │  │                  │          │
│  │ Model: .pt       │  │ Model: .onnx     │          │
│  │ Port: :5100      │  │ Port: :5101      │          │
│  │ Network: internal│  │ Network: internal│          │
│  │ Memory: 4GB cap  │  │ Memory: 4GB cap  │          │
│  └──────────────────┘  └──────────────────┘          │
│                                                      │
│  Sandbox network: bbap-sec-sandbox-net (no egress)   │
└──────────────────────────────────────────────────────┘
```

## Security Properties

- **Network isolation**: Sandboxes run on an `internal` Docker network (no internet access)
- **Read-only model access**: Model files mounted as read-only volumes
- **Non-root execution**: Sandbox container runs as `sandbox` user
- **Resource limits**: Memory cap (default 4GB), CPU cap (default 2 cores)
- **Auto-expiry**: Sandboxes destroyed after timeout (default 1 hour)
- **Port isolation**: Each sandbox gets a unique port in the 5100–5200 range
- **Audit trail**: All sandbox lifecycle events logged

## How Attack Modules Use the Sandbox

Attack modules interact with sandboxed models through the `SandboxManager.proxy_request()` method:

```python
from src.sandbox.manager import SandboxManager

manager = SandboxManager()

# Black-box attack (model extraction, evasion)
result = manager.proxy_request(sandbox_id, "/predict", method="POST",
    data={"input": random_queries.tolist()})
predictions = result["predictions"]

# White-box attack (FGSM, PGD)
result = manager.proxy_request(sandbox_id, "/gradient", method="POST",
    data={"input": images.tolist(), "target_class": 3})
gradients = result["gradients"]
```

## Verification

After setup, verify the sandbox infrastructure:

```bash
# 1. Build image
docker build -t bbap-sec-sandbox:latest sandbox/

# 2. Start webapp
python -m webapp.app

# 3. Create a test sandbox
curl -X POST http://localhost:5000/api/v2/sandbox/create \
  -F "file=@test_model.pt" \
  -F "engagement_id=1"

# 4. Check status
curl http://localhost:5000/api/v2/sandbox/1

# 5. Test prediction
curl -X POST http://localhost:5000/api/v2/sandbox/1/predict \
  -H "Content-Type: application/json" \
  -d '{"input": [[[0.5]]]}'

# 6. Destroy
curl -X DELETE http://localhost:5000/api/v2/sandbox/1

# 7. Verify cleanup
docker ps | grep bbap-sbx
```
