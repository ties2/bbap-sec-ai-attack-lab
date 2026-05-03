# ✅ Data Poisoning — Assessment Checklist
### BBAP-Sec AI Attack Lab

---

## Pre-Test Setup

- [ ] Identify training data pipeline and data sources
- [ ] Record baseline model accuracy on clean training data
- [ ] Select poisoning strategy: label-flip / backdoor / clean-label
- [ ] Define poison rates to test: 1%, 5%, 10%, 20%
- [ ] Ensure separate clean and poisoned training runs for comparison

## Label-Flip Attack Testing

- [ ] Poison 1% of training data (random label flips)
- [ ] Poison 5% of training data
- [ ] Poison 10% of training data
- [ ] Poison 20% of training data
- [ ] Test targeted flip (class A → class B) vs random flip
- [ ] Record accuracy degradation at each poison rate
- [ ] Identify the minimum poison rate that causes >5% accuracy drop
- [ ] Test if specific classes are more vulnerable than others

## Backdoor Attack Testing

- [ ] Define trigger pattern (e.g., 4×4 white patch)
- [ ] Select trigger position (corner / center / random)
- [ ] Choose target label for backdoor
- [ ] Train model on backdoor-poisoned data
- [ ] Measure clean accuracy (inputs without trigger)
- [ ] Measure backdoor ASR (inputs with trigger → target label)
- [ ] Verify trigger is visually inconspicuous
- [ ] Test with different trigger sizes (2×2, 4×4, 8×8)

## Measurements to Record

| Metric | Value |
|--------|-------|
| Clean model accuracy | ___% |
| Poisoned accuracy (1%) | ___% |
| Poisoned accuracy (5%) | ___% |
| Poisoned accuracy (10%) | ___% |
| Backdoor ASR | ___% |
| Trigger size | ___px |
| Min poison rate for >5% degradation | ___% |

## Defense Validation

- [ ] Apply statistical outlier detection on training features
- [ ] Test spectral signature defense (SVD on feature covariance)
- [ ] Validate data using cross-validation consistency checks
- [ ] Test STRIP (STRong Intentional Perturbation) defense for backdoor
- [ ] Verify defenses can flag >80% of poisoned samples
- [ ] Test impact of data sanitization on clean accuracy

## Reporting

- [ ] Document all poison rates and corresponding accuracy changes
- [ ] Include backdoor trigger visualization
- [ ] Map to MITRE ATLAS: AML.T0020 (Poison Training Data)
- [ ] Recommend data validation controls for the training pipeline
- [ ] Assess risk based on attacker's access to training data
- [ ] Export results as JSON
