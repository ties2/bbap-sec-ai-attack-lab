# NIST AI RMF Alignment

**BBAP-Sec AI Attack Lab — Reference 19.1 & 19.2**

---

## 1. Core Function Mapping

The NIST AI Risk Management Framework defines four core functions. BBAP-Sec maps to each as follows:

### GOVERN — Policies, Processes, and Accountability

Establishes the organizational context for AI risk management.

| BBAP-Sec Feature | RMF Coverage |
|-------------------|-------------|
| User Management (admin/analyst/viewer roles) | Role-based access control and accountability structures |
| Knowledge Base (policy documentation) | Policy storage, tagging, and retrieval |
| Settings (audit log, compliance config) | Audit trail and configuration governance |
| Pipeline: Authentication (OAuth2/JWT) | Access control enforcement |
| Pipeline: Audit trail | Activity logging for compliance |

### MAP — Identifying and Contextualizing AI Risks

Identifies and categorizes risks across the AI system lifecycle.

| BBAP-Sec Feature | RMF Coverage |
|-------------------|-------------|
| Secure Pipeline (5-stage architecture checks) | Systematic risk identification across data, model, prompt, API, monitoring stages |
| ATLAS Intel (170 techniques, 16 tactics) | Threat identification using MITRE ATLAS knowledge base |
| Project Management (per-project risk scoping) | Risk contextualization per AI system |
| Pipeline: PII scan, source auth, provenance | Data risk identification |

### MEASURE — Quantifying and Benchmarking AI Risks

Produces quantified metrics through standardized testing methodologies.

| BBAP-Sec Feature | RMF Coverage |
|-------------------|-------------|
| Adversarial Attacks (FGSM/PGD) | Robustness measurement at configurable epsilon values |
| Data Poisoning (label-flip, backdoor) | Training data integrity testing |
| Evasion Attacks (pixel, noise, spatial) | Inference-time bypass measurement |
| Model Extraction (random, active learning) | API security and model theft risk quantification |
| Prompt Injection Simulator (10 attacks) | LLM-specific vulnerability testing |
| Results & Reports (quantified metrics) | Standardized metric collection and comparison |

### MANAGE — Responding and Communicating

Tracks remediation, incident response, and stakeholder communication.

| BBAP-Sec Feature | RMF Coverage |
|-------------------|-------------|
| Alerts (severity-based incident tracking) | Risk notification and incident management |
| Pipeline (remediation status tracking) | Risk treatment plan execution |
| Knowledge Base (lessons learned) | Organizational learning and knowledge retention |
| Export All (JSON reports) | Stakeholder reporting and evidence collection |

---

## 2. Sub-Category Mapping

Detailed mapping of NIST AI RMF sub-categories to specific BBAP-Sec implementations:

### GOVERN Sub-Categories

| Sub-Category | RMF Requirement | BBAP-Sec Implementation |
|---|---|---|
| GOVERN 1.1 | Legal and regulatory requirements understood and documented | Knowledge Base for policy documentation; notes tagged with compliance frameworks |
| GOVERN 1.2 | Trustworthy AI characteristics integrated into policies | Pipeline checks enforce trustworthiness across 5 stages; 46 individual controls |
| GOVERN 1.3 | Risk tolerance levels defined and managed | Project-level risk configuration; severity-based alerting (critical/high/medium/low) |
| GOVERN 1.4 | Organizational practices for AI risk are in place | Pipeline stages provide structured security practices |
| GOVERN 1.6 | Policies and procedures are transparent and documented | Audit trail in Settings; Knowledge Base for procedure documentation |
| GOVERN 1.7 | AI supply chain risks managed | Pipeline: Supply chain audit check |
| GOVERN 2.1 | Roles and responsibilities defined | User Management with admin/analyst/viewer roles; MFA tracking |
| GOVERN 2.2 | Personnel are trained in AI risk management | Knowledge Base enables training documentation; attack lab provides hands-on training |

### MAP Sub-Categories

| Sub-Category | RMF Requirement | BBAP-Sec Implementation |
|---|---|---|
| MAP 1.1 | Intended purposes and context documented | Project descriptions and model configurations define scope and context |
| MAP 1.2 | Data sources and provenance documented | Pipeline: Source authentication, provenance tracking checks |
| MAP 1.5 | Input data quality assessed | Pipeline: Schema validation, format check, data integrity controls |
| MAP 1.6 | Privacy risks identified | Pipeline: PII scan identifies personal data exposure |
| MAP 2.1 | AI risks identified and categorized | ATLAS Intel provides 170 technique definitions mapped to 16 tactics |
| MAP 3.1 | Benefits and costs assessed | Results & Reports track attack outcomes; pipeline health shows posture |
| MAP 3.4 | Supply chain risks mapped | Pipeline: Supply chain audit |

### MEASURE Sub-Categories

| Sub-Category | RMF Requirement | BBAP-Sec Implementation |
|---|---|---|
| MEASURE 1.1 | Measurement approaches established | 5 attack modules provide standardized methodologies |
| MEASURE 2.5 | Adversarial robustness tested | FGSM/PGD attacks measure robustness at configurable epsilon values |
| MEASURE 2.6 | Bias and fairness tested | Data poisoning module detects training data integrity issues |
| MEASURE 2.7 | Safety and security tested | Full attack suite covers adversarial, poisoning, evasion, extraction, injection |

### MANAGE Sub-Categories

| Sub-Category | RMF Requirement | BBAP-Sec Implementation |
|---|---|---|
| MANAGE 1.1 | Risk treatment plans defined | Pipeline checks track remediation status; alerts track incident response |
| MANAGE 2.1 | AI system monitored for risks | Monitoring page tracks query rates, latency, error rates, drift scores |
| MANAGE 4.1 | Risk results communicated | Export All generates stakeholder-ready JSON reports with full test history |

---

## 3. Coverage Summary

| RMF Function | Sub-Categories Addressed | Coverage Level |
|---|---|---|
| GOVERN | 8 sub-categories | Moderate — user roles, audit, policy storage in place; automated compliance reporting planned |
| MAP | 7 sub-categories | Strong — ATLAS integration, pipeline checks, and project scoping provide comprehensive risk identification |
| MEASURE | 4 sub-categories | Strong — 5 attack modules with quantified metrics directly implement measurement |
| MANAGE | 3 sub-categories | Moderate — alerts and export in place; automated notifications and GRC integration planned |

---

*Reference: NIST AI 100-1, Artificial Intelligence Risk Management Framework (AI RMF 1.0), January 2023*
