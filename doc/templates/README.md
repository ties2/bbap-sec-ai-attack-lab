# BBAP-Sec Templates

Reusable templates for AI security assessment, risk management, and incident response.

## Available Templates

| Template | File | Purpose | When to Use |
|----------|------|---------|-------------|
| **AI Threat Model** | [threat-model-template.md](threat-model-template.md) | Structured threat modeling using STRIDE + MITRE ATLAS | Before deploying a new AI system or when the threat landscape changes |
| **AI Risk Assessment** | [risk-assessment-template.md](risk-assessment-template.md) | Quantified risk scoring with BBAP-Sec attack metrics | After running BBAP-Sec attack modules against a system |
| **AI Security Test Report** | [ai-security-test-report-template.md](ai-security-test-report-template.md) | Stakeholder-ready assessment report | When communicating results to management, compliance, or auditors |
| **Incident Response Playbook** | [incident-response-playbook-template.md](incident-response-playbook-template.md) | AI-specific incident response procedures | Customize per AI system; reference during security incidents |

## Workflow

```
1. THREAT MODEL        — Identify what could go wrong
   └── threat-model-template.md

2. SECURITY TESTING    — Measure how bad it actually is
   └── Use BBAP-Sec attack modules

3. RISK ASSESSMENT     — Score and prioritize
   └── risk-assessment-template.md

4. STAKEHOLDER REPORT  — Communicate findings
   └── ai-security-test-report-template.md

5. INCIDENT RESPONSE   — Be ready when it happens
   └── incident-response-playbook-template.md
```

## Usage

1. Copy the template you need
2. Fill in your system-specific details
3. Reference BBAP-Sec dashboard results where indicated
4. Use the ATLAS CLI (`python -m src.atlas.atlas_cli`) to look up technique details
5. Store completed documents in the Knowledge Base for team access

## Framework Alignment

All templates align with:
- **NIST AI RMF 1.0** — Govern, Map, Measure, Manage functions
- **MITRE ATLAS** — AI-specific threat techniques and mitigations
- **OWASP Top 10 for LLM** — LLM vulnerability coverage
- **EU AI Act** — Documentation and transparency requirements
- **ISO/IEC 42001** — AI management system alignment

---

*BBAP-Sec — Building Better AI Protection*
