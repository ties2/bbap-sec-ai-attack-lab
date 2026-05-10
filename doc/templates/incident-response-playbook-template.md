# AI Security Incident Response Playbook

**BBAP-Sec AI Attack Lab**

> AI-specific incident response procedures. Customize this playbook for each AI system under management.

---

## Document Control

| Field | Value |
|-------|-------|
| AI System | |
| Playbook Owner | |
| Last Updated | _YYYY-MM-DD_ |
| Review Cycle | ☐ Quarterly  ☐ Semi-annual  ☐ Annual |
| Approved By | |

---

## 1. Incident Classification

### 1.1 AI-Specific Incident Types

| Code | Incident Type | ATLAS Tactic | Severity Default | Examples |
|:----:|---------------|-------------|:----------------:|---------|
| AI-ADV | Adversarial attack detected | Defense Evasion | High | Misclassified inputs, accuracy degradation in production |
| AI-PSN | Training data poisoning suspected | Persistence | Critical | Model drift without code changes, unexpected behavior on specific inputs |
| AI-EVA | Inference evasion detected | Defense Evasion | Medium | Detection bypass, classification avoidance patterns |
| AI-EXT | Model extraction attempt | Exfiltration | High | Unusual API query patterns, systematic probing |
| AI-INJ | Prompt injection incident | Execution | Critical | System prompt leakage, unauthorized actions, data exfiltration via LLM |
| AI-DFT | Model drift / degradation | — | Medium | Gradual accuracy decline, distribution shift |
| AI-SUP | Supply chain compromise | Initial Access | Critical | Compromised model weights, malicious dependencies |

### 1.2 Severity Matrix

| Severity | Impact | Response Time | Escalation |
|:--------:|--------|:-------------:|------------|
| 🔴 Critical | Production AI making harmful decisions; data exfiltration confirmed; model fully compromised | < 1 hour | Immediate: Security Lead + Business Owner |
| 🟠 High | Attack partially successful; model accuracy degraded; extraction attempt detected | < 4 hours | Same day: Security Team + ML Team |
| 🟡 Medium | Evasion detected but contained; suspicious patterns observed | < 24 hours | Next business day: Security Team |
| 🟢 Low | Informational; failed attack attempt; minor anomaly | < 72 hours | Weekly review |

---

## 2. Response Procedures

### 2.1 Phase 1 — Detection and Triage

**Objective:** Confirm the incident, classify severity, and initiate response.

| Step | Action | Owner | Tool/Reference |
|:----:|--------|-------|----------------|
| 1.1 | Review alert details in BBAP-Sec Alerts page | On-call analyst | Dashboard → Alerts |
| 1.2 | Classify incident type using Section 1.1 | On-call analyst | This playbook |
| 1.3 | Assign severity using Section 1.2 matrix | On-call analyst | This playbook |
| 1.4 | Create incident ticket (reference BBAP-Sec alert ID) | On-call analyst | Ticketing system |
| 1.5 | Notify stakeholders per escalation path | On-call analyst | Contact list (Section 5) |

**Decision Gate:** Is this a confirmed AI security incident?
- ☐ **Yes** → Proceed to Phase 2
- ☐ **No** → Document as false positive, close alert, update detection rules

### 2.2 Phase 2 — Containment

**Objective:** Limit damage and prevent further exploitation.

#### For Adversarial / Evasion Attacks (AI-ADV, AI-EVA)

| Step | Action | Owner |
|:----:|--------|-------|
| 2.1 | Enable input validation bypass logging | ML Engineer |
| 2.2 | Increase monitoring sensitivity (lower anomaly thresholds) | ML Engineer |
| 2.3 | If accuracy drop > __%, switch to fallback model | ML Engineer |
| 2.4 | Collect adversarial samples for analysis | Security Analyst |

#### For Data Poisoning (AI-PSN)

| Step | Action | Owner |
|:----:|--------|-------|
| 2.1 | Halt model retraining immediately | ML Engineer |
| 2.2 | Rollback to last known-good model checkpoint | ML Engineer |
| 2.3 | Quarantine recent training data batches | Data Engineer |
| 2.4 | Run BBAP-Sec Data Poisoning module against suspected data | Security Analyst |

#### For Model Extraction (AI-EXT)

| Step | Action | Owner |
|:----:|--------|-------|
| 2.1 | Enable strict rate limiting on model API | Infrastructure |
| 2.2 | Block/throttle suspicious API keys or IP ranges | Infrastructure |
| 2.3 | Review query logs for systematic probing patterns | Security Analyst |
| 2.4 | Assess fidelity risk using BBAP-Sec extraction module | Security Analyst |

#### For Prompt Injection (AI-INJ)

| Step | Action | Owner |
|:----:|--------|-------|
| 2.1 | Enable enhanced input sanitization | ML Engineer |
| 2.2 | Review conversation logs for data exfiltration | Security Analyst |
| 2.3 | If system prompt leaked, rotate all embedded secrets | Security Analyst |
| 2.4 | Temporarily restrict affected bot/endpoint | Infrastructure |

### 2.3 Phase 3 — Investigation

**Objective:** Determine root cause, scope, and full impact.

| Step | Action | Owner | BBAP-Sec Tool |
|:----:|--------|-------|---------------|
| 3.1 | Export relevant attack results from dashboard | Analyst | Results & Reports → Export |
| 3.2 | Run targeted BBAP-Sec attacks to reproduce/quantify | Analyst | Run Attacks page |
| 3.3 | Review ATLAS Intel for related techniques and case studies | Analyst | ATLAS Intel page |
| 3.4 | Check pipeline health for control gaps | Analyst | Secure Pipeline page |
| 3.5 | Document timeline of events | Analyst | Knowledge Base |
| 3.6 | Assess data exposure / exfiltration scope | Analyst | Monitoring page |

### 2.4 Phase 4 — Remediation

**Objective:** Eliminate the vulnerability and restore secure operations.

| Step | Action | Owner |
|:----:|--------|-------|
| 4.1 | Implement specific control fixes based on investigation | ML Engineer |
| 4.2 | Update pipeline checks (toggle failing controls) | Security Analyst |
| 4.3 | Re-run BBAP-Sec attacks to verify fix effectiveness | Security Analyst |
| 4.4 | Update model if retraining was required | ML Engineer |
| 4.5 | Verify pipeline health meets target threshold (__%) | Security Lead |

### 2.5 Phase 5 — Recovery

**Objective:** Return to normal operations with enhanced monitoring.

| Step | Action | Owner |
|:----:|--------|-------|
| 5.1 | Restore full production traffic to remediated model | ML Engineer |
| 5.2 | Maintain elevated monitoring for __ days | Infrastructure |
| 5.3 | Confirm no recurrence for __ hours | On-call analyst |
| 5.4 | Close incident ticket with resolution details | Security Lead |

### 2.6 Phase 6 — Post-Incident Review

**Objective:** Learn and improve.

| Step | Action | Owner |
|:----:|--------|-------|
| 6.1 | Conduct post-incident review within 5 business days | Security Lead |
| 6.2 | Complete the AI Security Test Report template | Lead Assessor |
| 6.3 | Update this playbook with lessons learned | Playbook Owner |
| 6.4 | Create Knowledge Base note with findings | Security Analyst |
| 6.5 | Update BBAP-Sec pipeline checks if new controls needed | Security Analyst |
| 6.6 | Brief stakeholders on findings and improvements | Security Lead |

---

## 3. Incident-Specific Checklists

### 3.1 Prompt Injection Incident Checklist

- [ ] Identify which bot/endpoint was affected
- [ ] Determine attack category (direct / indirect / exfiltration / jailbreak)
- [ ] Check if system prompt was leaked — if yes, rotate all embedded secrets
- [ ] Check if user data was exfiltrated via the LLM response
- [ ] Review conversation logs for the attack window
- [ ] Run BBAP-Sec Prompt Injection simulator against the same bot configuration
- [ ] Update input sanitization rules based on the attack vector used
- [ ] Test updated defenses with the full 10-attack catalog

### 3.2 Model Poisoning Incident Checklist

- [ ] Identify the suspected poisoning window (which training batches)
- [ ] Rollback model to pre-poisoning checkpoint
- [ ] Quarantine and analyze suspected training data
- [ ] Run BBAP-Sec Data Poisoning module to quantify impact
- [ ] Check for backdoor triggers using backdoor scan pipeline check
- [ ] Retrain from clean data if poisoning confirmed
- [ ] Validate retrained model accuracy against baseline
- [ ] Strengthen data ingestion pipeline controls

---

## 4. Communication Templates

### 4.1 Internal Notification (Critical/High)

```
SUBJECT: [AI-SEC] [SEVERITY] AI Security Incident — [System Name]

Incident ID: ___
Severity: ___
System Affected: ___
Detected At: ___
Current Status: ☐ Triaging  ☐ Containing  ☐ Investigating  ☐ Remediating

Summary:
[Brief description of what happened]

Immediate Actions Taken:
[List containment steps already completed]

Next Steps:
[What happens next, expected timeline]

Contact: [Incident lead name and channel]
```

### 4.2 Stakeholder Update

```
SUBJECT: [AI-SEC] Update #___ — [System Name] Incident

Status: ☐ Ongoing  ☐ Contained  ☐ Resolved
Impact: [Business impact description]
ETA to Resolution: ___

Changes Since Last Update:
[What changed]

Action Items:
[Pending actions and owners]
```

---

## 5. Contact List

| Role | Name | Contact | Escalation Trigger |
|------|------|---------|-------------------|
| On-Call AI Security | | | All incidents |
| ML Engineering Lead | | | AI-ADV, AI-PSN, AI-EVA |
| Security Lead | | | High and Critical |
| Infrastructure Lead | | | AI-EXT, rate limiting |
| Business Owner | | | Critical only |
| Legal / Privacy | | | Data exfiltration confirmed |
| Communications | | | External disclosure required |

---

## 6. Revision History

| Version | Date | Author | Changes |
|:-------:|:----:|--------|---------|
| 1.0 | | | Initial playbook |

---

*Template version 1.0 — BBAP-Sec AI Attack Lab*
