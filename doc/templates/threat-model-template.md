# AI Threat Model Template

**BBAP-Sec AI Attack Lab**

> Fill in each section for the AI/ML system under assessment. This template combines STRIDE methodology with MITRE ATLAS AI-specific threats.

---

## Document Control

| Field | Value |
|-------|-------|
| System Name | _(e.g., Invoice Classifier v2.1)_ |
| Assessment Date | _YYYY-MM-DD_ |
| Assessor(s) | _(names and roles)_ |
| BBAP-Sec Project ID | _(from dashboard)_ |
| Classification | ☐ Internal  ☐ Confidential  ☐ Restricted |
| Review Cycle | ☐ Quarterly  ☐ Semi-annual  ☐ Annual  ☐ Event-driven |

---

## 1. System Description

### 1.1 Purpose and Scope

_Describe what the AI system does, its business function, and the decisions it influences._

| Item | Description |
|------|-------------|
| Business function | |
| Model type | ☐ Classification  ☐ Regression  ☐ NLP/LLM  ☐ Generative  ☐ Reinforcement Learning  ☐ Other: ___ |
| Deployment mode | ☐ Cloud API  ☐ Edge/On-device  ☐ Batch processing  ☐ Real-time inference |
| Autonomy level | ☐ Human-in-the-loop  ☐ Human-on-the-loop  ☐ Fully autonomous |
| Risk tier (EU AI Act) | ☐ Unacceptable  ☐ High  ☐ Limited  ☐ Minimal |

### 1.2 Data Flow

_Describe how data moves through the system. Include data sources, preprocessing, model inference, and output destinations._

```
[Data Source] → [Preprocessing] → [Model] → [Post-processing] → [Output/Action]
     ↑                                              ↓
[Feedback Loop] ←──────────────────────────── [Monitoring]
```

| Stage | Description | Data Types |
|-------|-------------|------------|
| Input | | |
| Preprocessing | | |
| Model inference | | |
| Post-processing | | |
| Output/action | | |

### 1.3 Trust Boundaries

_Identify where trust levels change. Each boundary is a potential attack surface._

| Boundary | Between | Trust Level Change |
|----------|---------|-------------------|
| B1 | | |
| B2 | | |
| B3 | | |

---

## 2. Threat Identification

### 2.1 STRIDE Analysis

For each component in the data flow, assess these six threat categories:

| Component | **S**poofing | **T**ampering | **R**epudiation | **I**nfo Disclosure | **D**enial of Service | **E**levation of Privilege |
|-----------|:-:|:-:|:-:|:-:|:-:|:-:|
| Data input | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| Preprocessing | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| Model | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| API/Interface | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| Output | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| Training pipeline | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |

### 2.2 AI-Specific Threats (MITRE ATLAS)

For each applicable threat, check if it applies and note the relevant ATLAS technique ID:

#### Training-Time Threats

| Threat | Applies? | ATLAS ID | Notes |
|--------|:--------:|----------|-------|
| Training data poisoning (label flip) | ☐ | AML.T0020 | |
| Backdoor injection (trigger pattern) | ☐ | AML.T0020.001 | |
| Supply chain compromise (pretrained model) | ☐ | AML.T0010 | |
| Data provenance spoofing | ☐ | AML.T0020.000 | |

#### Inference-Time Threats

| Threat | Applies? | ATLAS ID | Notes |
|--------|:--------:|----------|-------|
| Adversarial examples (FGSM/PGD) | ☐ | AML.T0043 | |
| Evasion attacks (input manipulation) | ☐ | AML.T0047 | |
| Model extraction (API queries) | ☐ | AML.T0044 | |
| Prompt injection (direct) | ☐ | AML.T0051.000 | |
| Prompt injection (indirect) | ☐ | AML.T0051.001 | |
| System prompt leakage | ☐ | AML.T0053 | |
| LLM jailbreak | ☐ | AML.T0054 | |

#### Infrastructure Threats

| Threat | Applies? | ATLAS ID | Notes |
|--------|:--------:|----------|-------|
| ML inference API abuse | ☐ | AML.T0005 | |
| Model weight exfiltration | ☐ | AML.T0024 | |
| Training environment compromise | ☐ | AML.T0012 | |

---

## 3. Risk Assessment

### 3.1 Threat-Risk Register

For each identified threat, assess impact and likelihood:

| Threat ID | Threat Description | Impact (1–5) | Likelihood (1–5) | Risk Score | Rating | BBAP-Sec Module |
|-----------|-------------------|:---:|:---:|:---:|--------|-----------------|
| T-01 | | | | | | |
| T-02 | | | | | | |
| T-03 | | | | | | |
| T-04 | | | | | | |
| T-05 | | | | | | |

**Risk Score** = Impact × Likelihood

| Score | Rating |
|-------|--------|
| 1–5 | 🟢 Low |
| 6–12 | 🟡 Medium |
| 13–19 | 🟠 High |
| 20–25 | 🔴 Critical |

### 3.2 BBAP-Sec Test Results

_Paste or reference BBAP-Sec attack results for each applicable threat:_

| Threat ID | Attack Module | Key Metric | Value | Supports Rating? |
|-----------|--------------|------------|-------|:-:|
| T-01 | Adversarial | Accuracy drop | __%  | ☐ |
| T-02 | Data Poisoning | Backdoor ASR | __% | ☐ |
| T-03 | Evasion | Evasion rate | __% | ☐ |
| T-04 | Model Extraction | Fidelity | __% | ☐ |
| T-05 | Prompt Injection | Injection ASR | __% | ☐ |

---

## 4. Mitigations

### 4.1 Control Mapping

For each identified threat, map to existing or required controls:

| Threat ID | Control | Pipeline Stage | Status | Owner | Target Date |
|-----------|---------|---------------|:------:|-------|-------------|
| T-01 | | | ☐ Implemented  ☐ Planned  ☐ Gap | | |
| T-02 | | | ☐ Implemented  ☐ Planned  ☐ Gap | | |
| T-03 | | | ☐ Implemented  ☐ Planned  ☐ Gap | | |

### 4.2 ATLAS Mitigations

_Reference MITRE ATLAS mitigations for each technique. Use `python -m src.atlas.atlas_cli mitigations <technique_id>` to look up specific mitigations._

| ATLAS Technique | ATLAS Mitigation | Implementation Notes |
|---|---|---|
| | | |

---

## 5. Residual Risk

After mitigations are applied, reassess:

| Threat ID | Original Rating | Mitigation Applied | Residual Rating | Accepted? |
|-----------|:-:|---|:-:|:-:|
| T-01 | | | | ☐ |
| T-02 | | | | ☐ |
| T-03 | | | | ☐ |

---

## 6. Recommendations

| Priority | Recommendation | Effort | Impact |
|----------|---------------|:------:|:------:|
| 1 | | ☐ Low  ☐ Med  ☐ High | ☐ Low  ☐ Med  ☐ High |
| 2 | | ☐ Low  ☐ Med  ☐ High | ☐ Low  ☐ Med  ☐ High |
| 3 | | ☐ Low  ☐ Med  ☐ High | ☐ Low  ☐ Med  ☐ High |

---

## 7. Sign-Off

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Assessor | | | |
| Model Owner | | | |
| Security Lead | | | |
| Risk Approver | | | |

---

*Template version 1.0 — BBAP-Sec AI Attack Lab*
