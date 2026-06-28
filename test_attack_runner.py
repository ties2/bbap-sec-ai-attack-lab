#!/usr/bin/env python3
"""
BBAP-Sec — Attack Runner Integration Test
===========================================
Tests the full attack execution pipeline:
  Sandbox running → AttackRunner → execute FGSM → get Finding

Prerequisites:
  - Sandbox running (created via /api/v2/sandbox/create)
  - webapp running (python -m webapp.app)

Usage:
    python test_attack_runner.py
    python test_attack_runner.py --sandbox-id 1
    python test_attack_runner.py --api-url http://localhost:5000
"""

import argparse
import json
import sys
import requests

BASE = "http://localhost:5000"


def step(msg):
    print(f"\n{'='*60}")
    print(f"  {msg}")
    print(f"{'='*60}")


def test_list_attacks():
    resp = requests.get(f"{BASE}/api/v2/attacks/list")
    data = resp.json()
    print(f"  Registered attacks: {data['total']}")
    for a in data["attacks"]:
        print(f"    {a['id']:20s}  layer={a['layer']}")
    return data["total"] > 0


def test_run_fgsm(sandbox_id):
    payload = {
        "project_id": 1,
        "attack_id": "fgsm",
        "layer": "inference",
        "target": {"type": "sandbox", "sandbox_id": sandbox_id},
        "params": {
            "epsilon": 0.03,
            "num_samples": 20,
            "input_shape": [3, 224, 224],
        }
    }
    print(f"  Sending FGSM attack request (ε=0.03, 20 samples)...")
    resp = requests.post(f"{BASE}/api/v2/attacks/run", json=payload)
    data = resp.json()
    print(f"  Status: {resp.status_code}")
    print(f"  Finding ID: {data.get('id')}")
    print(f"  Severity: {data.get('severity')}")
    print(f"  Title: {data.get('title')}")
    if "metrics" in data:
        print(f"  Metrics:")
        for k, v in data["metrics"].items():
            print(f"    {k}: {v}")
    print(f"  Elapsed: {data.get('elapsed_seconds', '?')}s")
    print(f"  Queries: {data.get('target_queries', '?')}")
    return resp.status_code == 200 and "metrics" in data


def test_run_evasion(sandbox_id):
    payload = {
        "project_id": 1,
        "attack_id": "evasion_pixel",
        "layer": "inference",
        "target": {"type": "sandbox", "sandbox_id": sandbox_id},
        "params": {"max_pixels": 10, "num_samples": 30, "input_shape": [3, 224, 224]}
    }
    print(f"  Running pixel evasion (10 pixels, 30 samples)...")
    resp = requests.post(f"{BASE}/api/v2/attacks/run", json=payload)
    data = resp.json()
    print(f"  Title: {data.get('title')}")
    if "metrics" in data:
        print(f"  Evasion rate: {data['metrics'].get('evasion_rate')}%")
    return resp.status_code == 200


def test_run_extraction(sandbox_id):
    payload = {
        "project_id": 1,
        "attack_id": "extract_random",
        "layer": "artifacts",
        "target": {"type": "sandbox", "sandbox_id": sandbox_id},
        "params": {"num_queries": 100, "input_shape": [3, 224, 224]}
    }
    print(f"  Running model extraction (100 queries)...")
    resp = requests.post(f"{BASE}/api/v2/attacks/run", json=payload)
    data = resp.json()
    print(f"  Title: {data.get('title')}")
    if "metrics" in data:
        print(f"  Fidelity: {data['metrics'].get('fidelity')}%")
        print(f"  Total queries: {data['metrics'].get('queries')}")
    return resp.status_code == 200


def test_run_rate_limit(sandbox_id):
    payload = {
        "project_id": 1,
        "attack_id": "rate_limit",
        "layer": "infra",
        "target": {"type": "sandbox", "sandbox_id": sandbox_id},
        "params": {"burst_size": 20}
    }
    print(f"  Running rate limit test (20 rapid queries)...")
    resp = requests.post(f"{BASE}/api/v2/attacks/run", json=payload)
    data = resp.json()
    print(f"  Title: {data.get('title')}")
    if "metrics" in data:
        print(f"  Successful: {data['metrics'].get('successful')}/{data['metrics'].get('burst_size')}")
        print(f"  Avg latency: {data['metrics'].get('avg_latency_ms')}ms")
    return resp.status_code == 200


def test_list_results():
    resp = requests.get(f"{BASE}/api/v2/attacks/results?project_id=1")
    data = resp.json()
    print(f"  Total findings: {data['total']}")
    for r in data["results"]:
        sev = r.get("severity", "?")
        print(f"    {r.get('id', '?'):20s}  [{sev:8s}]  {r.get('title', '?')[:50]}")
    return data["total"] > 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sandbox-id", type=int, default=None)
    parser.add_argument("--api-url", type=str, default=BASE)
    args = parser.parse_args()

    base = args.api_url

    # Find active sandbox
    sandbox_id = args.sandbox_id
    if sandbox_id is None:
        step("0. Finding active sandbox")
        resp = requests.get(f"{BASE}/api/v2/sandbox/list")
        sandboxes = resp.json().get("sandboxes", [])
        running = [s for s in sandboxes if s["status"] == "running"]
        if not running:
            print("  No running sandbox found. Create one first:")
            print("  curl -X POST http://localhost:5000/api/v2/sandbox/create \\")
            print('    -F "file=@models/your_model.pt" -F "project_id=1"')
            return 1
        sandbox_id = running[0]["id"]
        print(f"  Using sandbox {sandbox_id} (port {running[0]['port']})")

    passed = 0
    failed = 0
    tests = [
        ("1. List registered attacks",     test_list_attacks),
        ("2. FGSM attack (white-box)",     lambda: test_run_fgsm(sandbox_id)),
        ("3. Pixel evasion (black-box)",   lambda: test_run_evasion(sandbox_id)),
        ("4. Model extraction",            lambda: test_run_extraction(sandbox_id)),
        ("5. Rate limit test",             lambda: test_run_rate_limit(sandbox_id)),
        ("6. List all findings",           test_list_results),
    ]

    for name, fn in tests:
        step(name)
        try:
            if fn():
                print("  ✓ PASSED")
                passed += 1
            else:
                print("  ✗ FAILED")
                failed += 1
        except Exception as e:
            print(f"  ✗ ERROR: {e}")
            failed += 1

    print(f"\n{'='*60}")
    print(f"  RESULTS: {passed} passed, {failed} failed")
    print(f"{'='*60}")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
