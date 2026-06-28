# Phase 1 — Attack Execution Engine

## Files to Add

```
src/attacks/
├── __init__.py              # Module init, imports runner + implementations
├── runner.py                # AttackRunner, SandboxTarget, APITarget, progress tracking
└── implementations.py       # 8 attack functions (FGSM, PGD, 3 evasion, 2 extraction, rate limit)

webapp/
└── routes_attacks.py        # API routes: /run, /run-async, /progress, /result

test_attack_runner.py        # End-to-end test: sandbox → attack → finding
```

## Integration

### Step 1: Copy files into your project

```bash
cp -r src/attacks/ /path/to/bbap-sec-ai-attack-lab/src/attacks/
cp webapp/routes_attacks.py /path/to/bbap-sec-ai-attack-lab/webapp/
cp test_attack_runner.py /path/to/bbap-sec-ai-attack-lab/
```

### Step 2: Register the routes in webapp/app.py

```python
from webapp.routes_attacks import attacks_bp, init_attack_runner
from webapp.routes_sandbox import sandbox_bp, get_manager

app.register_blueprint(attacks_bp)

# After sandbox_bp is registered, connect the attack runner to it:
with app.app_context():
    init_attack_runner(sandbox_manager=get_manager())
```

### Step 3: Test

```bash
# Terminal 1: Start the app
python webapp/app.py

# Terminal 2: Create a sandbox (if not already running)
curl -X POST http://localhost:5000/api/v2/sandbox/create \
  -F "file=@models/resnet50.pt" \
  -F "project_id=1" \
  -F "framework=pytorch"

# Terminal 2: Run the test
python test_attack_runner.py
```

## API Reference

### Execute attack (synchronous)

```
POST /api/v2/attacks/run
```

```json
{
  "project_id": 1,
  "attack_id": "fgsm",
  "layer": "inference",
  "target": {
    "type": "sandbox",
    "sandbox_id": 1
  },
  "params": {
    "epsilon": 0.03,
    "num_samples": 200,
    "input_shape": [3, 224, 224]
  }
}
```

Response (Finding):

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
  "severity": "high",
  "status": "open",
  "elapsed_seconds": 12.4,
  "target_queries": 604
}
```

### Execute attack (async, for long-running attacks)

```
POST /api/v2/attacks/run-async    → {"run_id": "abc123", "status": "started"}
GET  /api/v2/attacks/progress/abc123  → {"status": "running", "progress": 45.0}
GET  /api/v2/attacks/result/abc123    → {finding}
```

### Available attacks

| attack_id | Layer | Access | Description |
|-----------|-------|--------|-------------|
| `fgsm` | inference | White-box (gradient) | Fast Gradient Sign Method |
| `pgd` | inference | White-box (gradient) | Projected Gradient Descent |
| `evasion_pixel` | inference | Black-box (predict) | Random pixel perturbation |
| `evasion_noise` | inference | Black-box (predict) | Gaussian noise injection |
| `evasion_spatial` | inference | Black-box (predict) | Spatial shift transform |
| `extract_random` | artifacts | Black-box (predict) | Random query model extraction |
| `extract_active` | artifacts | Black-box (predict) | Active learning extraction |
| `rate_limit` | infra | Black-box (predict) | Rate limit bypass test |

### Parameters by attack

| Attack | Parameter | Default | Description |
|--------|-----------|---------|-------------|
| fgsm | `epsilon` | 0.03 | Perturbation magnitude |
| fgsm | `num_samples` | 200 | Number of test samples |
| fgsm | `input_shape` | [1,28,28] | Model input dimensions |
| pgd | `epsilon` | 0.03 | Perturbation budget |
| pgd | `alpha` | ε/4 | Step size |
| pgd | `num_steps` | 20 | PGD iterations |
| evasion_pixel | `max_pixels` | 10 | Pixels to flip per image |
| evasion_noise | `noise_std` | 0.1 | Gaussian noise σ |
| evasion_spatial | `max_rotation` | 15 | Max rotation degrees |
| extract_random | `num_queries` | 1000 | Queries to send |
| extract_active | `initial_queries` | 200 | Seed query count |
| extract_active | `rounds` | 5 | Refinement rounds |
| rate_limit | `burst_size` | 100 | Rapid-fire queries |

## Dashboard Wiring

Update the LayerPage "Execute Attack" button to call the API.

In the `LayerPage` component, replace the static button:

```jsx
// BEFORE (static):
<button className="..."><Play size={13}/>Execute Attack</button>

// AFTER (functional):
<button
  onClick={async () => {
    setRunning(true);
    setRunResult(null);
    try {
      const resp = await fetch("/api/v2/attacks/run", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
          project_id: project.id,
          attack_id: sel.id,
          layer: layerKey,
          target: { type: "sandbox", sandbox_id: 1 },
          params: { ...attackParams, input_shape: [3, 224, 224] }
        })
      });
      const data = await resp.json();
      setRunResult(data);
    } catch (e) { setRunResult({error: e.message}); }
    setRunning(false);
  }}
  disabled={running}
  className="..."
>
  {running
    ? <><Loader2 size={13} className="animate-spin"/>Running...</>
    : <><Play size={13}/>Execute Attack</>
  }
</button>
```

Then display the result below:

```jsx
{runResult && !runResult.error && (
  <div className={`${G} rounded-lg p-4 mt-4`}>
    <div className="flex items-center gap-3 mb-2">
      <CheckCircle2 size={14} className="text-emerald-400"/>
      <span className="text-[12px] text-white/70">{runResult.title}</span>
      <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-orange-500/10 text-orange-400">
        {runResult.severity}
      </span>
    </div>
    <div className="flex gap-3 flex-wrap">
      {Object.entries(runResult.metrics || {}).map(([k,v]) => (
        <span key={k} className="text-[9px] font-mono bg-white/[0.03] text-white/35 px-2 py-0.5 rounded">
          {k}: {typeof v === 'number' ? v.toFixed?.(2) ?? v : v}
        </span>
      ))}
    </div>
  </div>
)}
```
