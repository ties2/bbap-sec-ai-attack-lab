# ✅ Model Extraction — Assessment Checklist
### BBAP-Sec AI Attack Lab

---

## Pre-Test Setup

- [ ] Identify the model API endpoint being tested
- [ ] Determine API output type: labels-only / confidence scores / logits
- [ ] Check existing rate limiting and authentication controls
- [ ] Select substitute model architecture (same family / different)
- [ ] Define query budget: 100, 500, 1000, 5000, 10000

## Random Query Extraction

- [ ] Generate random inputs within valid input space
- [ ] Query victim API and collect responses
- [ ] Train substitute model on victim labels
- [ ] Measure substitute vs victim fidelity (agreement rate)
- [ ] Test at 100, 500, 1000, 5000 query budgets
- [ ] Record fidelity improvement per additional query

## Active Learning Extraction

- [ ] Initialize with small random seed set
- [ ] Use Jacobian-based augmentation for informative queries
- [ ] Compare active vs random query efficiency
- [ ] Measure fidelity at each active learning round
- [ ] Check if active learning converges faster

## Measurements to Record

| Metric | Value |
|--------|-------|
| Victim model accuracy | ___% |
| Substitute accuracy (random, 1000q) | ___% |
| Substitute accuracy (active, 1000q) | ___% |
| Fidelity (random, 1000q) | ___% |
| Fidelity (active, 1000q) | ___% |
| Total API queries used | ___ |
| Queries needed for >90% fidelity | ___ |

## Defense Validation

- [ ] Test rate limiting: does it block excessive queries?
- [ ] Test query pattern detection (anomaly detection on API logs)
- [ ] Verify API only returns labels (not full probability vectors)
- [ ] Test model watermarking detection in substitute
- [ ] Test PRADA defense (detect distribution shift in queries)
- [ ] Assess authentication and access controls

## API Security Controls Checklist

- [ ] API key / token authentication required
- [ ] Rate limiting enforced (requests per minute/hour)
- [ ] Query logging and monitoring active
- [ ] Output limited to labels only (no confidence scores)
- [ ] Anomalous query pattern alerting configured
- [ ] Input validation rejects out-of-distribution queries

## Reporting

- [ ] Document fidelity curves (queries vs agreement rate)
- [ ] Compare random vs active learning efficiency
- [ ] Map to MITRE ATLAS: AML.T0024 (Exfiltration via ML Inference API)
- [ ] Recommend rate limiting thresholds and monitoring rules
- [ ] Export results as JSON
