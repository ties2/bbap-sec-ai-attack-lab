# BBAP-Sec AI Security Pentest Platform — Project Reference

**Version:** 3.0
**Last Updated:** May 2026
**Status:** Active Development

---

## 1. What This Project Is

BBAP-Sec is an AI security pentest platform for security teams to test ML models and AI applications against real attack techniques. Unlike academic tools that test a single bundled model, BBAP-Sec connects to any target — a deployed API, an uploaded model file, a model registry, or an LLM endpoint — and runs structured attacks across six lifecycle layers.

The platform produces quantified findings (accuracy drop, ASR, fidelity, evasion rate) that map to MITRE ATLAS techniques and feed into compliance reports aligned with NIST AI RMF, OWASP, and EU AI Act.

### Core Capabilities

- Test any ML model via 4 access methods (API endpoint, model upload to Docker sandbox, registry pull, LLM API)
- Execute attacks across 6 AI lifecycle layers (Training, Inference, Artifacts, Data Pipeline, Infrastructure, Output)
- 8 implemented attack modules with quantified metrics
- Docker sandbox for isolated model testing with white-box (gradient) and black-box (predict) access
- 46-control security pipeline across 5 stages
- MITRE ATLAS integration (170 techniques, 16 tactics, case studies)
- NIST AI RMF governance with 5-framework compliance mapping
- Cross-referenced findings system with severity scoring
- Report generator pulling from all layers

---

## 2. Architecture

```
bbap-sec-ai-attack-lab/
├── frontend/                    # React dashboard (Vite + Tailwind)
│   ├── src/
│   │   ├── BBAP-Sec-Dashboard.jsx   # Main dashboard (all pages)
│   │   └── components/
│   │       └── GovernancePage.jsx    # Governance component
│   ├── public/
│   │   └── logo.png
│   └── dist/                    # Built frontend (served by Flask)
│
├── webapp/                      # Flask backend
│   ├── app.py                   # Main app, blueprint registration
│   ├── database.py              # SQLite operations
│   ├── routes_api.py            # Core API routes (/api/v2/*)
│   ├── routes_attacks.py        # Attack execution (/api/v2/attacks/*)
│   ├── routes_sandbox.py        # Sandbox management (/api/v2/sandbox/*)
│   └── routes_prompt_injection.py
│
├── src/
│   ├── attacks/                 # Attack modules
│   │   ├── runner.py            # AttackRunner engine
│   │   ├── implementations.py  # 8 attack functions
│   │   ├── adversarial.py       # FGSM/PGD (standalone CLI)
│   │   ├── data_poisoning.py    # Label-flip, backdoor (CLI)
│   │   ├── evasion.py           # Pixel, noise, spatial (CLI)
│   │   ├── model_extraction.py  # Random, active learning (CLI)
│   │   └── prompt_injection.py  # 10-attack catalog (CLI)
│   │
│   ├── sandbox/                 # Sandbox container management
│   │   ├── manager.py           # SandboxManager (Docker SDK)
│   │   └── __init__.py
│   │
│   ├── atlas/                   # MITRE ATLAS integration
│   │   ├── ATLAS.yaml           # Full ATLAS database
│   │   ├── atlas_client.py      # API client
│   │   ├── atlas_data.py        # Data loading
│   │   ├── atlas_mapper.py      # BBAP-Sec → ATLAS mapping
│   │   └── atlas_cli.py         # CLI tool
│   │
│   ├── models/
│   │   └── target_model.py      # SimpleCNN, dataset loading
│   │
│   ├── defenses/
│   │   └── robustness.py        # Adversarial training, input sanitization
│   │
│   └── utils/
│       ├── logger.py            # Structured logging
│       └── metrics.py           # ASR, accuracy, fidelity metrics
│
├── sandbox/                     # Docker sandbox container
│   ├── Dockerfile               # Python 3.11 + PyTorch + ONNX + sklearn
│   ├── sandbox_api.py           # Flask API inside container
│   ├── model_loader.py          # Auto-detect framework, load model
│   └── requirements.txt
│
├── doc/
│   ├── ai-risk-management/      # NIST AI RMF documentation
│   │   ├── README.md
│   │   ├── nist-ai-rmf-alignment.md
│   │   ├── governance-controls.md
│   │   ├── risk-assessment-methodology.md
│   │   └── compliance-mapping.md
│   ├── templates/               # Assessment templates
│   │   ├── threat-model-template.md
│   │   ├── risk-assessment-template.md
│   │   ├── ai-security-test-report-template.md
│   │   └── incident-response-playbook-template.md
│   └── PHASE1_GUIDE.md
│
├── checklists/                  # Per-attack assessment checklists
├── config/config.yaml           # Global configuration
├── datasets/                    # MNIST, CIFAR-10
├── models/                      # Uploaded model files (resnet50.pt)
├── results/                     # Attack result JSON files
├── logs/                        # Per-module log files
├── data/bbap_sec.db             # SQLite database
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

---

## 3. Target Access Methods

The platform supports four ways to connect to a target AI system. Each method determines which attack surface layers and individual attacks are available.

### 3.1 API Endpoint

For testing deployed models via their REST API. Black-box only — no gradient access.

- **Configuration:** URL, authorization header, response format
- **Available attacks:** Evasion (pixel, noise, spatial), model extraction (random, active), rate limit bypass
- **Not available:** FGSM, PGD (require gradients), training-phase attacks

### 3.2 Model Upload (Docker Sandbox)

For testing model files directly. White-box and black-box access.

- **Supported formats:** `.pt`, `.pth` (PyTorch), `.onnx` (ONNX), `.h5`, `.keras`, `.pb` (TensorFlow), `.pkl`, `.joblib` (scikit-learn), `.safetensors`
- **How it works:** File uploaded via multipart form → copied to sandbox directory → Docker container created with model mounted read-only → Flask API wraps model with `/predict`, `/predict_proba`, `/gradient` endpoints
- **Available attacks:** All inference attacks (FGSM, PGD, evasion), extraction, training-phase (poisoning, backdoor)
- **Sandbox properties:** Network-isolated Docker container, non-root user, 4GB memory cap, 2 CPU cores, auto-expiry after 1 hour

### 3.3 Registry Connection

For pulling models from MLflow, HuggingFace, or S3. Same as model upload after pull.

- **Configuration:** Registry URL, model ID, credentials
- **Status:** UI ready, backend pull logic planned for Phase 3

### 3.4 LLM Endpoint

For testing LLM applications via API (OpenAI, Anthropic, Azure, self-hosted).

- **Configuration:** Provider, API key, model name
- **Available attacks:** Prompt injection (direct, indirect), system prompt leakage, jailbreak, hallucination probing, guardrail bypass
- **Status:** UI ready, LLM API integration planned for Phase 2

---

## 4. Docker Sandbox

### 4.1 Container Architecture

```
┌──────────────────────────────────────────────────┐
│  BBAP-Sec Platform (Host)                        │
│                                                  │
│  Flask App ──► SandboxManager ──► Docker SDK      │
│                     │                            │
│         ┌───────────┴───────────┐                │
│         ▼                       ▼                │
│  ┌──────────────┐        ┌──────────────┐        │
│  │ bbap-sbx-001 │        │ bbap-sbx-002 │        │
│  │ (Docker)     │        │ (Docker)     │        │
│  │              │        │              │        │
│  │ Model: .pt   │        │ Model: .onnx │        │
│  │ Port: :5100  │        │ Port: :5101  │        │
│  └──────────────┘        └──────────────┘        │
│    network isolated        network isolated      │
└──────────────────────────────────────────────────┘
```

### 4.2 Sandbox API Endpoints (inside container)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Container health check |
| `/model_info` | GET | Architecture, params, framework, input shape |
| `/predict` | POST | Class predictions (black-box) |
| `/predict_proba` | POST | Probability distributions (black-box) |
| `/gradient` | POST | Input gradients (white-box, PyTorch/TF only) |
| `/stats` | GET | Query count, uptime, queries/min |

### 4.3 Sandbox Management API (host)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v2/sandbox/create` | POST | Upload model file, create container |
| `/api/v2/sandbox/{id}` | GET | Container status and stats |
| `/api/v2/sandbox/{id}` | DELETE | Stop and remove container |
| `/api/v2/sandbox/list` | GET | List all sandboxes |
| `/api/v2/sandbox/{id}/predict` | POST | Proxy prediction request |
| `/api/v2/sandbox/{id}/predict_proba` | POST | Proxy probability request |
| `/api/v2/sandbox/{id}/gradient` | POST | Proxy gradient request |
| `/api/v2/sandbox/{id}/model_info` | GET | Proxy model info |
| `/api/v2/sandbox/cleanup` | POST | Destroy expired sandboxes |

### 4.4 Security Properties

- Network isolation: `internal` Docker network, no internet access
- Read-only model: mounted as read-only volume
- Non-root: runs as `sandbox` user inside container
- Resource limits: 4GB memory, 2 CPU cores (configurable)
- Auto-expiry: destroyed after timeout (default 1 hour)
- Port isolation: each sandbox gets unique port in 5100–5200 range

---

## 5. Attack Execution Engine

### 5.1 How It Works

```
Dashboard "Execute Attack"
    │
    ▼
POST /api/v2/attacks/run
    │  { project_id, attack_id, layer, target, params }
    ▼
AttackRunner.run()
    │
    ├── Creates SandboxTarget or APITarget
    ├── Calls attack function (e.g. attack_fgsm)
    │     │
    │     ├── target.predict(inputs)       ← black-box
    │     ├── target.gradient(inputs)      ← white-box
    │     └── computes metrics
    │
    ├── Computes severity from metrics
    └── Returns Finding dict
         │
         ▼
Dashboard shows result card with metrics + severity badge
```

### 5.2 Implemented Attacks

| attack_id | Layer | Access | What It Does |
|-----------|-------|--------|-------------|
| `fgsm` | Inference | White-box | Single-step gradient perturbation, measures accuracy drop |
| `pgd` | Inference | White-box | Iterative gradient attack (20 steps), stronger than FGSM |
| `evasion_pixel` | Inference | Black-box | Flips random pixels, measures prediction change rate |
| `evasion_noise` | Inference | Black-box | Adds Gaussian noise, measures prediction change rate |
| `evasion_spatial` | Inference | Black-box | Shifts image rows/cols, measures prediction change rate |
| `extract_random` | Artifacts | Black-box | Random queries → nearest-neighbor substitute → fidelity |
| `extract_active` | Artifacts | Black-box | Iterative augmentation → better fidelity with fewer queries |
| `rate_limit` | Infrastructure | Black-box | Rapid-fire queries, counts blocked vs successful |

### 5.3 Attack Parameters

| Attack | Parameter | Default | Description |
|--------|-----------|---------|-------------|
| fgsm | `epsilon` | 0.03 | Perturbation magnitude (L∞) |
| fgsm/pgd | `num_samples` | 200 | Test samples to generate |
| fgsm/pgd | `input_shape` | [1,28,28] | Model input dimensions |
| pgd | `alpha` | ε/4 | Step size per iteration |
| pgd | `num_steps` | 20 | PGD iterations |
| evasion_pixel | `max_pixels` | 10 | Pixels to flip per image |
| evasion_noise | `noise_std` | 0.1 | Gaussian noise σ |
| extract_random | `num_queries` | 1000 | Total API queries |
| extract_active | `rounds` | 5 | Active learning rounds |
| rate_limit | `burst_size` | 100 | Rapid-fire queries |

### 5.4 Attack API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v2/attacks/run` | POST | Execute attack (synchronous), returns Finding |
| `/api/v2/attacks/run-async` | POST | Execute in background, returns run_id |
| `/api/v2/attacks/progress/{run_id}` | GET | Poll progress (status, %) |
| `/api/v2/attacks/result/{run_id}` | GET | Get completed result |
| `/api/v2/attacks/results` | GET | List all results (filter: `?project_id=1`) |
| `/api/v2/attacks/list` | GET | List registered attacks |
| `/api/v2/attacks/active` | GET | List running attacks |

### 5.5 Finding Structure

Every attack produces a Finding with this structure:

```json
{
  "id": "F-260510-a1b2c3d4",
  "project_id": 1,
  "layer": "inference",
  "attack": "fgsm",
  "severity": "high",
  "title": "FGSM at ε=0.03: accuracy drops 56.4%",
  "metrics": {
    "epsilon": 0.03,
    "clean_accuracy": 100.0,
    "adversarial_accuracy": 43.6,
    "accuracy_drop": 56.4,
    "attack_success_rate": 56.4,
    "total_samples": 200,
    "queries": 604
  },
  "atlas": "AML.T0043.001",
  "related": [],
  "status": "open",
  "elapsed_seconds": 12.4,
  "target_queries": 604,
  "created_at": "2026-05-10T14:30:00"
}
```

### 5.6 Severity Computation

Severity is auto-computed from metrics:

| Metric | Critical | High | Medium | Low |
|--------|----------|------|--------|-----|
| accuracy_drop | ≥60% | ≥30% | ≥10% | <10% |
| evasion_rate | — | ≥50% | ≥20% | <20% |
| fidelity | ≥90% | ≥70% | ≥40% | <40% |
| backdoor_asr | ≥80% | ≥50% | <50% | — |
| injection_asr | ≥50% | ≥30% | ≥10% | <10% |

---

## 6. Six Attack Surface Layers

The dashboard organizes attacks by where in the AI lifecycle the vulnerability exists, not by technique name.

### Layer 1: Training Phase

Attacks that compromise the model during training.

| Attack | ATLAS ID | Access Required |
|--------|----------|-----------------|
| Label-flip poisoning | AML.T0020.000 | Upload, Registry |
| Backdoor implant | AML.T0020.001 | Upload, Registry |
| Supply chain compromise | AML.T0010 | Registry |
| Clean-label poisoning | AML.T0020 | Upload |

### Layer 2: Inference Phase

Attacks that manipulate inputs at prediction time.

| Attack | ATLAS ID | Access Required |
|--------|----------|-----------------|
| FGSM | AML.T0043.001 | Upload (white-box) |
| PGD | AML.T0043.001 | Upload (white-box) |
| Pixel perturbation | AML.T0047 | Upload, API |
| Gaussian noise | AML.T0047 | Upload, API |
| Spatial transform | AML.T0047.003 | Upload, API |
| Model inversion | AML.T0024 | API |

### Layer 3: Model Artifacts

Attacks that steal or reverse-engineer the model.

| Attack | ATLAS ID | Access Required |
|--------|----------|-----------------|
| Model extraction (random) | AML.T0044 | API |
| Model extraction (active) | AML.T0044 | API |
| Weight exfiltration | AML.T0024 | Upload, Registry |
| Architecture reverse eng. | AML.T0005 | API |

### Layer 4: Data Pipeline

Attacks that compromise the data supply chain.

| Attack | ATLAS ID | Access Required |
|--------|----------|-----------------|
| Tainted dataset injection | AML.T0020 | Upload, Registry |
| Label corruption | AML.T0020.000 | Upload, Registry |
| Scraping / API abuse | — | API |
| Provenance spoofing | AML.T0010 | Registry |

### Layer 5: Infrastructure

Attacks against the serving infrastructure.

| Attack | ATLAS ID | Access Required |
|--------|----------|-----------------|
| Rate limit bypass | AML.T0005 | API |
| Authentication bypass | — | API |
| Registry access audit | AML.T0010 | Registry |
| Serving misconfiguration | — | API |

### Layer 6: Output Layer

Attacks against LLM outputs and guardrails.

| Attack | ATLAS ID | Access Required |
|--------|----------|-----------------|
| Direct prompt injection | AML.T0051.000 | LLM |
| Indirect injection | AML.T0051.001 | LLM |
| System prompt leakage | AML.T0053 | LLM |
| LLM jailbreak | AML.T0054 | LLM |
| Output guardrail bypass | — | LLM, API |
| Hallucination probing | — | LLM |

---

## 7. Dashboard Pages

The React dashboard (`frontend/src/BBAP-Sec-Dashboard.jsx`) contains all pages in a single file.

| Page | Sidebar Label | Status | What It Does |
|------|--------------|--------|-------------|
| Overview | Overview | ✅ Working | Risk score, findings count, layer health, critical findings list |
| Target Setup | Target Setup | ✅ Working | 4 access methods, file upload, sandbox creation, scope selection |
| Training Phase | Training Phase | ✅ Working | Attack catalog + execute + findings (filtered by project) |
| Inference Phase | Inference Phase | ✅ Working | FGSM/PGD/evasion with params → execute via API → result card |
| Model Artifacts | Model Artifacts | ✅ Working | Extraction attacks with query count params |
| Data Pipeline | Data Pipeline | ✅ Working | Data integrity attacks |
| Infrastructure | Infrastructure | ✅ Working | Rate limit and auth bypass tests |
| Output Layer | Output Layer | ✅ Working | Prompt injection, jailbreak (LLM attacks) |
| Findings | Findings | ✅ Working | All findings for current project, layer filter, cross-references |
| Pipeline | Pipeline | ✅ Working | 46 controls across 5 stages, toggleable PASS/FAIL, health % |
| ATLAS Intel | ATLAS Intel | ✅ Working | Search, module mappings, tactic coverage, technique/case-study detail |
| Report Generator | Report Generator | ✅ Working | 11-section report structure, preview, export buttons |
| Governance | Governance | ✅ Working | NIST AI RMF (4 functions), controls, risk scores, compliance |
| Monitoring | Monitoring | ✅ Working | Query rate, latency, error rate, drift, sandbox resources |
| Team | Team | 🔲 Placeholder | User management |
| Knowledge Base | Knowledge Base | 🔲 Placeholder | Notes, policies |
| Alerts | Alerts | 🔲 Placeholder | Severity notifications |
| Settings | Settings | 🔲 Placeholder | API keys, sandbox config |

### Project Selector

The sidebar has a dropdown that switches between projects. Each project has its own target type, scope, and findings. Creating a new project navigates to Target Setup. Findings, overview stats, and layer findings all filter by the active project.

---

## 8. Secure Pipeline (46 Controls)

| Stage | Controls | Purpose |
|-------|----------|---------|
| **Data Ingestion** (9) | Schema validation, format check, data integrity, PII scan, source auth, provenance tracking, poison detection, outlier detection, volume validation | Validate data entering the system |
| **Model Validation** (10) | Architecture review, weight integrity, backdoor scan, version control, supply chain audit, performance baseline, robustness check, fairness check, reproducibility, dependency scan | Validate the model itself |
| **Prompt Filtering** (8) | Input sanitization, injection detection, encoding bypass check, length validation, language filter, context boundary, jailbreak detection, token budget | Filter LLM inputs |
| **API Security** (9) | Authentication, rate limiting, TLS enforcement, encryption at rest, CORS policy, input size limit, API versioning, key rotation, IP allowlisting | Secure the serving infrastructure |
| **Monitoring** (10) | Query logging, output guardrails, response watermarking, output truncation, context isolation, drift detection, anomaly alerting, audit trail, latency monitoring, error rate tracking | Monitor production behavior |

Each control has a name, description, and toggleable PASS/FAIL status. The pipeline health percentage and per-stage health update live.

---

## 9. MITRE ATLAS Integration

### Backend

- `src/atlas/ATLAS.yaml` — Full ATLAS database (16 tactics, 170+ techniques, mitigations, case studies)
- `src/atlas/atlas_mapper.py` — Maps BBAP-Sec's 5 attack modules to ATLAS techniques
- `src/atlas/atlas_cli.py` — CLI for lookup, search, coverage analysis

### API Endpoints

| Endpoint | Description |
|----------|-------------|
| `/api/atlas/stats` | Version, tactic/technique/mitigation/case-study counts |
| `/api/atlas/tactics` | List all 16 tactics |
| `/api/atlas/coverage` | Which modules cover which tactics |
| `/api/atlas/search?q=...` | Search techniques, mitigations, case studies |
| `/api/atlas/mapping/{module}` | ATLAS mapping for a specific attack module |
| `/api/atlas/technique/{id}` | Technique detail + subtechniques + mitigations |
| `/api/atlas/case-study/{id}` | Case study detail + attack chain |

### CLI

```bash
python -m src.atlas.atlas_cli stats
python -m src.atlas.atlas_cli tactics
python -m src.atlas.atlas_cli lookup AML.T0043
python -m src.atlas.atlas_cli search "prompt injection"
python -m src.atlas.atlas_cli mapping adversarial
python -m src.atlas.atlas_cli coverage
python -m src.atlas.atlas_cli chain AML.CS0000
python -m src.atlas.atlas_cli mitigations AML.T0043
```

---

## 10. AI Risk Management & Governance

### NIST AI RMF Alignment

| Function | Sub-Categories | Coverage |
|----------|---------------|----------|
| GOVERN | 7 (roles, policies, audit, supply chain) | 71% (5 met, 2 partial) |
| MAP | 7 (risk ID, data sources, privacy, ATLAS) | 86% (6 met, 1 partial) |
| MEASURE | 4 (robustness, bias, safety testing) | 75% (3 met, 1 partial) |
| MANAGE | 3 (treatment plans, monitoring, reporting) | 100% (3 met) |

### Compliance Mapping

| Framework | Version | Coverage |
|-----------|---------|----------|
| NIST AI RMF | 1.0 (2023) | 85% |
| MITRE ATLAS | 5.6.0 (2025) | 50% (8/16 tactics) |
| OWASP LLM Top 10 | 2025 | 60% (LLM01, LLM02, LLM07) |
| EU AI Act | 2024 | 45% |
| ISO/IEC 42001 | 2023 | 55% |

### Risk Scoring

```
adversarial_risk = (accuracy_drop / 100) × (ASR / 100) × 100
poisoning_risk   = (accuracy_drop / 100) × poison_rate × 100
evasion_risk     = evasion_rate
extraction_risk  = (fidelity / 100) × (1 - queries / max_queries) × 100
injection_risk   = injection_asr

composite_risk   = Σ(weight × score) / Σ(weight)
adjusted_risk    = composite × (1 - pipeline_health / 200)
```

Weights: adversarial=1.0, poisoning=1.2, evasion=0.8, extraction=1.0, injection=1.5

---

## 11. Assessment Templates

Located in `doc/templates/`:

| Template | Purpose |
|----------|---------|
| `threat-model-template.md` | STRIDE + MITRE ATLAS threat modeling with trust boundaries |
| `risk-assessment-template.md` | Quantified scoring with per-attack tables and composite score |
| `ai-security-test-report-template.md` | Stakeholder report with findings, compliance, remediation |
| `incident-response-playbook-template.md` | AI-specific IR procedures for 7 incident types |

---

## 12. CLI Attack Modules

Each attack module in `src/attacks/` can run standalone via CLI:

```bash
# Adversarial
python -m src.attacks.adversarial --attack fgsm --epsilon 0.03 --dataset mnist
python -m src.attacks.adversarial --attack pgd --epsilon 0.03 --steps 40 --sweep

# Data poisoning
python -m src.attacks.data_poisoning --strategy label_flip --poison-rate 0.1
python -m src.attacks.data_poisoning --strategy backdoor --trigger-size 4 --target-label 0

# Evasion
python -m src.attacks.evasion --method all --dataset mnist

# Model extraction
python -m src.attacks.model_extraction --strategy random --queries 1000
python -m src.attacks.model_extraction --strategy active --queries 500

# Prompt injection
python -m src.attacks.prompt_injection --test-suite all
```

Results are saved to `results/` as timestamped JSON files.

---

## 13. Database

SQLite at `data/bbap_sec.db`. Managed by `webapp/database.py`.

### Tables

| Table | Purpose |
|-------|---------|
| `projects` | Project definitions with target type, config, scope, status |
| `pipeline_checks` | 46 controls with pass/fail status per project |
| `attack_results` | Attack execution results with metrics |
| `alerts` | Severity-based notifications |
| `notes` | Knowledge base entries |
| `users` | User accounts with roles |
| `sandboxes` | Sandbox container lifecycle tracking |

---

## 14. Deployment

### Local Development

```bash
conda activate bbap-sec
python datasets/download_datasets.py     # One-time dataset download
cd frontend && npm run build && cd ..     # Build React dashboard
python webapp/app.py                      # Start Flask on :5000
```

### Docker

```bash
# Build sandbox image (one-time)
cd sandbox && docker build -t bbap-sec-sandbox:latest . && cd ..

# Start platform
docker-compose up --build

# Or run app locally with Docker sandbox support
pip install docker
python webapp/app.py
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MODEL_UPLOAD_DIR` | `./data/sandbox-models` | Where uploaded models are stored |
| `SANDBOX_IMAGE` | `bbap-sec-sandbox:latest` | Docker image for sandboxes |
| `SANDBOX_PORT_START` | `5100` | Start of port range for sandboxes |
| `SANDBOX_PORT_END` | `5200` | End of port range |
| `SANDBOX_TIMEOUT` | `3600` | Auto-destroy timeout (seconds) |
| `SANDBOX_MEMORY_LIMIT` | `4g` | Container memory cap |
| `SANDBOX_CPU_LIMIT` | `2.0` | Container CPU cores |

---

## 15. What's Next

### Phase 2 — Persistence + LLM Attacks

- Migrate mock data to SQLite (projects, findings, pipeline state)
- Dashboard pages fetch from API instead of reading constants
- Connect prompt injection attacks to real LLM APIs (OpenAI, Anthropic)
- Score LLM responses automatically

### Phase 3 — AI Agent Security

- 7th attack surface layer for agent architectures
- Tool-use abuse testing
- Multi-step injection chains
- Agent hijacking via retrieved documents
- Memory poisoning
- Model inversion attacks
- Infrastructure scanning module

### Phase 4 — Production

- PDF/JSON report export
- Team page with user roles and project assignments
- Alerts with webhook/email notifications
- Settings page (API keys, sandbox config, audit log)
- CI integration (`bbap-sec scan --project 1 --layer inference`)

---

## 16. Tech Stack

| Component | Technology |
|-----------|-----------|
| Frontend | React 18 + Vite + Tailwind CSS + Lucide icons |
| Backend | Python 3.12 + Flask |
| Database | SQLite |
| ML | PyTorch, ONNX Runtime, scikit-learn |
| Containerization | Docker + Docker SDK for Python |
| Threat framework | MITRE ATLAS 5.6.0 |
| Governance | NIST AI RMF 1.0 |

---

*BBAP-Sec — Building Better AI Protection*