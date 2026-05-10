# AI Risk Management & Governance

**BBAP-Sec AI Attack Lab — Chapter 19**

This section defines how BBAP-Sec aligns with the NIST AI Risk Management Framework (AI RMF 1.0) and provides a structured approach to AI governance. The platform supports the four core RMF functions through its existing modules and governance features.

---

## Contents

| Document | Description |
|----------|-------------|
| [NIST AI RMF Alignment](nist-ai-rmf-alignment.md) | Core function mapping (Govern, Map, Measure, Manage) and sub-category coverage |
| [Governance Controls Framework](governance-controls.md) | Layered control framework across Input, Model, Output, and Infrastructure domains |
| [Risk Assessment Methodology](risk-assessment-methodology.md) | Quantified risk scoring using attack module metrics |
| [Compliance Mapping](compliance-mapping.md) | Multi-framework mapping: NIST AI RMF, MITRE ATLAS, OWASP, EU AI Act, ISO 42001 |

## Templates

Reusable templates for AI security assessments are in [`doc/templates/`](../templates/):

| Template | Purpose |
|----------|---------|
| [AI Threat Model Template](../templates/threat-model-template.md) | Structured threat modeling for AI/ML systems using STRIDE + ATLAS |
| [AI Risk Assessment Template](../templates/risk-assessment-template.md) | Quantified risk scoring with BBAP-Sec attack metrics |
| [AI Security Test Report Template](../templates/ai-security-test-report-template.md) | Post-assessment report for stakeholder communication |
| [Incident Response Playbook Template](../templates/incident-response-playbook-template.md) | AI-specific incident response procedures |

---

## Quick Reference: RMF Function Coverage

```
┌─────────────────────────────────────────────────────────────┐
│                    NIST AI RMF 1.0                          │
├──────────┬──────────┬──────────────┬────────────────────────┤
│  GOVERN  │   MAP    │   MEASURE    │        MANAGE          │
│          │          │              │                        │
│ Users &  │ Pipeline │ Run Attacks  │ Alerts                 │
│ Roles    │ Checks   │ (FGSM, PGD,  │ Pipeline               │
│          │          │  Poisoning,  │ Remediation            │
│ Knowledge│ ATLAS    │  Evasion,    │                        │
│ Base     │ Intel    │  Extraction) │ Knowledge Base         │
│          │          │              │                        │
│ Settings │ Project  │ Results &    │ Export Reports         │
│ (Audit)  │ Mgmt     │ Reports      │                        │
└──────────┴──────────┴──────────────┴────────────────────────┘
```

## How to Use This Section

1. **Start with the RMF alignment** to understand which BBAP-Sec features map to each NIST function.
2. **Review the governance controls** to see how the 46 pipeline checks map to security domains.
3. **Use the templates** to conduct structured assessments of your AI systems.
4. **Export results** from the dashboard and feed them into the risk assessment template.

## Related Dashboard Pages

- **Secure Pipeline** — 46 controls across 5 stages (implements MAP and GOVERN)
- **Run Attacks** — 5 attack modules (implements MEASURE)
- **Results & Reports** — Quantified metrics and export (implements MANAGE)
- **ATLAS Intel** — Threat identification and technique mapping (implements MAP)
- **Alerts** — Incident tracking and response (implements MANAGE)
- **Governance** — NIST AI RMF dashboard with compliance tracking

---

*BBAP-Sec — Building Better AI Protection*
