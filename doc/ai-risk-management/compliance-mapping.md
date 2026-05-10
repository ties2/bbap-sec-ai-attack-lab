# Compliance Mapping

**BBAP-Sec AI Attack Lab — Reference 19.5**

The platform maps to multiple AI governance frameworks. This document provides a detailed cross-reference for compliance teams.

---

## 1. Framework Coverage Summary

| Framework | Version | BBAP-Sec Coverage |
|-----------|---------|-------------------|
| NIST AI RMF | 1.0 (2023) | 4 core functions mapped; 13+ sub-categories addressed via pipeline, attacks, and reporting |
| MITRE ATLAS | 5.6.0 (2025) | 16 tactics, 170 techniques indexed; 8/16 tactics covered by attack modules; full search and mapping UI |
| OWASP Top 10 for LLM | 2025 | LLM01 (Prompt Injection), LLM02 (Sensitive Info Disclosure), LLM07 (System Prompt Leakage) |
| EU AI Act | 2024 | Risk classification via project-level tolerance; documentation and transparency via export reports |
| ISO/IEC 42001 | 2023 | AI management system alignment via pipeline controls, user roles, audit trails |
| MIT AI Risk Repository | 2024 | Domains: Privacy & Security, Malicious Actors & Misuse, AI System Safety |

---

## 2. MITRE ATLAS Coverage

### Covered Tactics (8/16)

| Tactic | ATLAS ID | Covered By |
|--------|----------|------------|
| AI Model Access | TA0011 | Model Extraction (VictimAPI class) |
| AI Attack Staging | TA0012 | Adversarial (FGSM/PGD), Data Poisoning |
| Resource Development | TA0001 | Model Extraction (substitute model training) |
| Execution | TA0002 | All attack modules |
| Persistence | TA0003 | Data Poisoning (backdoor injection) |
| Defense Evasion | TA0005 | Evasion module (pixel, noise, spatial) |
| Collection | TA0009 | Model Extraction (query-based data collection) |
| Exfiltration | TA0010 | Model Extraction, Prompt Injection (data exfiltration probes) |

### Module-to-Technique Mapping

| BBAP-Sec Module | ATLAS Techniques | Key Functions |
|---|---|---|
| Adversarial | AML.T0043, AML.T0043.001, AML.T0047 | `fgsm_attack()`, `pgd_attack()`, `evaluate_robustness()` |
| Data Poisoning | AML.T0020, AML.T0020.000, AML.T0020.001, AML.T0043.000 | `label_flip_poison()`, `backdoor_poison()` |
| Evasion | AML.T0047, AML.T0047.000, AML.T0047.003 | `pixel_perturbation_evasion()`, `feature_noise_evasion()`, `spatial_transform_evasion()` |
| Model Extraction | AML.T0005, AML.T0024, AML.T0044 | `VictimAPI`, `random_query_extraction()`, `active_learning_extraction()` |
| Prompt Injection | AML.T0051, AML.T0051.000, AML.T0051.001, AML.T0053, AML.T0054 | A-01 through A-10 attack catalog |

---

## 3. OWASP Top 10 for LLM Applications (2025)

| OWASP ID | Vulnerability | BBAP-Sec Coverage |
|----------|---------------|-------------------|
| LLM01 | Prompt Injection | Prompt Injection simulator with 10 attacks across 5 categories (Direct, Indirect, Exfiltration, Jailbreak, Social Engineering) |
| LLM02 | Sensitive Information Disclosure | Prompt exfiltration probes (A-02, A-09) test system prompt leakage and context window enumeration |
| LLM03 | Supply Chain Vulnerabilities | Pipeline: Supply chain audit check |
| LLM04 | Data and Model Poisoning | Data Poisoning module (label-flip, backdoor); Pipeline: Poison detection |
| LLM05 | Improper Output Handling | Pipeline: Output guardrails, output truncation, context isolation |
| LLM06 | Excessive Agency | Pipeline: Rate limiting, authentication controls |
| LLM07 | System Prompt Leakage | Prompt Injection attacks A-02 (verbatim leak), A-03 (fictional framing), A-04 (base64 smuggling) |
| LLM08 | Vector and Embedding Weaknesses | Not currently covered |
| LLM09 | Misinformation | Not currently covered |
| LLM10 | Unbounded Consumption | Pipeline: Rate limiting; Model Extraction: query budget tracking |

---

## 4. EU AI Act Alignment

| EU AI Act Requirement | BBAP-Sec Implementation |
|---|---|
| Risk classification (Art. 6) | Project-level risk tolerance configuration (critical/high/medium/low) |
| Technical documentation (Art. 11) | Export All generates comprehensive test reports; Knowledge Base stores documentation |
| Transparency (Art. 13) | Results & Reports provide clear metric visualization; pipeline health shows posture |
| Robustness and accuracy (Art. 15) | Adversarial module directly measures robustness; accuracy metrics tracked per attack |
| Human oversight (Art. 14) | User roles enforce human-in-the-loop; alerts require manual acknowledgment |
| Data governance (Art. 10) | Pipeline: Data validation, PII scan, source authentication, provenance tracking |

---

## 5. ISO/IEC 42001:2023 Alignment

| ISO 42001 Clause | Requirement | BBAP-Sec Implementation |
|---|---|---|
| 5.2 | AI policy | Knowledge Base for policy documentation |
| 6.1 | Risk assessment | 5 attack modules provide quantified risk assessment |
| 6.2 | AI objectives | Project management with scope and context definition |
| 7.2 | Competence | Attack lab provides hands-on AI security training |
| 8.1 | Operational planning | Pipeline checks provide structured security controls |
| 8.4 | AI risk treatment | Alerts and pipeline remediation tracking |
| 9.1 | Monitoring and measurement | Monitoring page, Results & Reports |
| 9.2 | Internal audit | Audit trail in Settings; export capability |
| 10.1 | Continual improvement | Knowledge Base for lessons learned; re-testing workflow |

---

## 6. Compliance Evidence Collection

For each framework, the following BBAP-Sec exports provide compliance evidence:

| Evidence Type | How to Collect | Frameworks Served |
|---|---|---|
| Attack test results (JSON) | Export All from Results & Reports | NIST AI RMF, ISO 42001, EU AI Act |
| Pipeline health report | Pipeline page screenshot or API export | NIST AI RMF, ISO 42001 |
| ATLAS coverage matrix | ATLAS Intel page or CLI `coverage` command | MITRE ATLAS |
| User role assignments | User Management page | NIST AI RMF (GOVERN 2.1), ISO 42001 |
| Policy documentation | Knowledge Base export | All frameworks |
| Alert history | Alerts page with acknowledged/unacknowledged status | NIST AI RMF (MANAGE), ISO 42001 |

---

*BBAP-Sec — Building Better AI Protection*
