# ✅ Evasion Attacks — Assessment Checklist
### BBAP-Sec AI Attack Lab

---

## Pre-Test Setup

- [ ] Identify the inference pipeline and model endpoint
- [ ] Determine input modality: image / tabular / text / multimodal
- [ ] Record baseline detection/classification accuracy
- [ ] Identify real-world attack surface (e.g., invoice scanning, spam filter)
- [ ] Define acceptable perturbation constraints (imperceptible to human)

## Image Evasion Testing

- [ ] Single-pixel perturbation attack
- [ ] Multi-pixel perturbation (5, 10, 20 pixels)
- [ ] Gaussian noise injection at various sigma values
- [ ] Spatial transformation (rotation ±5°, ±15°)
- [ ] Color-space manipulation (brightness, contrast)
- [ ] Patch overlay attack (small adversarial patch)
- [ ] Record evasion rate for each method

## Tabular/Feature Evasion Testing

- [ ] Modify single feature within valid range
- [ ] Modify multiple features simultaneously
- [ ] Test boundary-case inputs (edge of valid ranges)
- [ ] Simulate real-world manipulation (e.g., invoice amount change)

## Text Evasion Testing

- [ ] Character-level perturbation (typos, homoglyphs)
- [ ] Word-level substitution (synonyms)
- [ ] Invisible character injection (zero-width chars)
- [ ] Encoding manipulation (unicode normalization)

## Measurements to Record

| Metric | Value |
|--------|-------|
| Baseline detection accuracy | ___% |
| Evasion rate (pixel attack) | ___% |
| Evasion rate (noise injection) | ___% |
| Evasion rate (spatial transform) | ___% |
| Min perturbation for >50% evasion | ___ |

## Defense Validation

- [ ] Feature squeezing (detect by comparing squeezed vs original)
- [ ] Ensemble detection (multiple models vote)
- [ ] Input validation (reject out-of-distribution inputs)
- [ ] Anomaly detection on input features
- [ ] Test defense detection rate for each evasion method

## Reporting

- [ ] Document all evasion methods and success rates
- [ ] Include visual comparison of original vs evaded inputs
- [ ] Map to MITRE ATLAS: AML.T0015 (Evade ML Model)
- [ ] Recommend input validation and ensemble defenses
- [ ] Export results as JSON
