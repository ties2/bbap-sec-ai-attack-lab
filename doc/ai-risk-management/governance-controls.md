# AI Governance Controls Framework

**BBAP-Sec AI Attack Lab — Reference 19.3**

BBAP-Sec implements a layered control framework across four domains. Each control maps to a specific pipeline check, attack module, or platform feature, and is aligned to the NIST AI RMF.

---

## 1. Input Controls

Controls applied to data entering the AI system.

| Control | Pipeline Stage | BBAP-Sec Feature | RMF Alignment | Validates Against |
|---------|---------------|-------------------|---------------|-------------------|
| Data validation | Data Ingestion | Schema validation, format check | MAP 1.5, MEASURE 2.6 | Malformed input, schema drift |
| Poison detection | Data Ingestion | Poison detection, outlier detection | MAP 2.1, MEASURE 2.5 | Label-flip attacks, backdoor injection |
| PII scanning | Data Ingestion | PII scan | GOVERN 1.1, MAP 1.6 | GDPR/privacy violations |
| Source authentication | Data Ingestion | Source auth, provenance tracking | GOVERN 1.4, MAP 1.2 | Untrusted data sources |
| Prompt filtering | Prompt Filtering | Input sanitization | MEASURE 2.5 | Direct prompt injection |
| Injection detection | Prompt Filtering | Injection detection | MEASURE 2.5 | Indirect prompt injection |
| Encoding bypass prevention | Prompt Filtering | Encoding bypass check | MEASURE 2.5 | Base64/Unicode obfuscation |

### Testing Input Controls with BBAP-Sec

- **Data Poisoning module** → validates poison detection and outlier detection controls
- **Prompt Injection simulator** → validates input sanitization, injection detection, encoding bypass controls
- **Evasion module** → validates data validation controls against adversarial modifications

---

## 2. Model Controls

Controls applied to the AI model itself.

| Control | Pipeline Stage | BBAP-Sec Feature | RMF Alignment | Validates Against |
|---------|---------------|-------------------|---------------|-------------------|
| Adversarial robustness | Model Validation | FGSM/PGD testing | MEASURE 2.5 | Gradient-based adversarial attacks |
| Backdoor detection | Model Validation | Backdoor scan | MEASURE 2.5, MAP 2.1 | Trojan/backdoor models |
| Architecture review | Model Validation | Architecture review check | MAP 1.1, MEASURE 1.1 | Insecure model architectures |
| Weight integrity | Model Validation | Weight integrity check | MEASURE 2.5 | Model tampering |
| Version control | Model Validation | Version control check | GOVERN 1.2, MANAGE 2.1 | Untracked model changes |
| Supply chain audit | Model Validation | Supply chain audit | MAP 3.4, GOVERN 1.7 | Compromised dependencies |

### Testing Model Controls with BBAP-Sec

- **Adversarial module (FGSM/PGD)** → quantifies robustness at multiple epsilon values
- **Data Poisoning module (backdoor)** → tests backdoor detection with trigger patterns
- **Model Extraction module** → validates that model weights cannot be reconstructed via API

---

## 3. Output Controls

Controls applied to AI system outputs.

| Control | Pipeline Stage | BBAP-Sec Feature | RMF Alignment | Validates Against |
|---------|---------------|-------------------|---------------|-------------------|
| Output guardrails | Monitoring | Output guardrails | MEASURE 2.5, MANAGE 1.1 | Harmful/unintended outputs |
| Response watermarking | Monitoring | Response watermarking | GOVERN 1.2 | Output attribution |
| Output truncation | Monitoring | Output truncation | MANAGE 2.1 | Excessive information disclosure |
| Context isolation | Monitoring | Context isolation | MEASURE 2.5 | Cross-context data leakage |

### Testing Output Controls with BBAP-Sec

- **Prompt Injection simulator** → tests output guardrails, context isolation, and system prompt leakage
- **Model Extraction module** → validates output truncation and rate limiting prevent model theft

---

## 4. Infrastructure Controls

Controls applied to supporting infrastructure.

| Control | Pipeline Stage | BBAP-Sec Feature | RMF Alignment | Validates Against |
|---------|---------------|-------------------|---------------|-------------------|
| Authentication | API Security | Authentication (OAuth2/JWT) | GOVERN 2.1 | Unauthorized access |
| Rate limiting | API Security | Rate limiting | MANAGE 2.1 | API abuse, model extraction |
| Encryption at rest | API Security | Encryption at rest | GOVERN 1.1 | Data exposure at rest |
| Query logging | Monitoring | Query logging | MANAGE 2.1, GOVERN 1.6 | Undetected malicious queries |
| TLS enforcement | API Security | TLS enforcement | GOVERN 1.1 | Data interception in transit |
| Audit trail | Monitoring | Audit trail | GOVERN 1.6, MANAGE 4.1 | Accountability gaps |

### Testing Infrastructure Controls with BBAP-Sec

- **Model Extraction module** → tests rate limiting effectiveness against query-based attacks
- **Prompt Injection simulator** → tests authentication and privilege escalation controls

---

## 5. Control Maturity Levels

Each control can be assessed at four maturity levels:

| Level | Name | Description |
|-------|------|-------------|
| 0 | Not Implemented | Control does not exist |
| 1 | Initial | Control exists but is ad hoc, not consistently applied |
| 2 | Managed | Control is documented, repeatable, and consistently applied |
| 3 | Optimized | Control is automated, monitored, and continuously improved |

Use the pipeline check pass/fail status to track maturity. A passing check at minimum indicates Level 1. Documentation in the Knowledge Base elevates to Level 2. Automated testing via the attack modules achieves Level 3.

---

## 6. Control-to-Attack Module Cross-Reference

| Attack Module | Tests Controls In |
|---|---|
| Adversarial (FGSM/PGD) | Model Controls (robustness), Input Controls (validation) |
| Data Poisoning | Input Controls (poison detection, source auth), Model Controls (backdoor detection) |
| Evasion | Input Controls (validation), Model Controls (robustness) |
| Model Extraction | Infrastructure Controls (rate limiting, auth), Output Controls (truncation) |
| Prompt Injection | Input Controls (filtering, injection detection), Output Controls (guardrails, isolation) |

---

*BBAP-Sec — Building Better AI Protection*
