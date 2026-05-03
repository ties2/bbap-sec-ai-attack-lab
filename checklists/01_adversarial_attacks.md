# ✅ Adversarial Attacks — Assessment Checklist
### BBAP-Sec AI Attack Lab

---

## Pre-Test Setup

- [ ] Identify target model architecture and framework (PyTorch, TensorFlow, etc.)
- [ ] Confirm model is loaded and inference is working on clean inputs
- [ ] Record baseline clean accuracy on test set
- [ ] Select perturbation budget (epsilon) range: typical 0.01–0.3 for L∞
- [ ] Ensure GPU/compute resources are available for iterative attacks

## FGSM Testing (Fast Gradient Sign Method)

- [ ] Run FGSM with epsilon = 0.01 (minimal perturbation)
- [ ] Run FGSM with epsilon = 0.03 (standard benchmark)
- [ ] Run FGSM with epsilon = 0.1 (moderate perturbation)
- [ ] Run FGSM with epsilon = 0.3 (strong perturbation)
- [ ] Record accuracy drop at each epsilon level
- [ ] Visually inspect adversarial examples — are perturbations perceptible?
- [ ] Calculate Attack Success Rate (ASR) at each epsilon
- [ ] Test with both targeted and untargeted variants

## PGD Testing (Projected Gradient Descent)

- [ ] Configure step size alpha (typically epsilon/4)
- [ ] Test with 10, 20, 40 iteration steps
- [ ] Enable random start initialization
- [ ] Compare PGD results against FGSM at same epsilon
- [ ] Verify PGD achieves higher ASR than FGSM (expected behavior)
- [ ] Test L2 norm variant in addition to L∞
- [ ] Record convergence — does more steps = more success?

## Measurements to Record

| Metric | Value |
|--------|-------|
| Clean accuracy | ___% |
| Adversarial accuracy (FGSM, ε=0.03) | ___% |
| Adversarial accuracy (PGD, ε=0.03) | ___% |
| ASR (FGSM) | ___% |
| ASR (PGD) | ___% |
| Max perturbation (L∞) | ___ |
| Avg perturbation (L2) | ___ |

## Defense Validation

- [ ] Apply adversarial training and re-evaluate
- [ ] Test feature squeezing (bit depth reduction)
- [ ] Test input smoothing / Gaussian blur defense
- [ ] Compare defended model accuracy on clean vs adversarial inputs
- [ ] Verify defense does not significantly degrade clean accuracy (< 3% drop acceptable)
- [ ] Test ensemble of defenses (adversarial training + input preprocessing)

## Reporting

- [ ] Document all epsilon values tested and corresponding accuracy drops
- [ ] Include adversarial example visualizations (clean vs perturbed)
- [ ] Note the epsilon threshold where model accuracy drops below 50%
- [ ] Map findings to MITRE ATLAS: AML.T0043 (Craft Adversarial Data)
- [ ] Recommend specific defenses based on acceptable accuracy trade-off
- [ ] Export results as JSON for pipeline integration
