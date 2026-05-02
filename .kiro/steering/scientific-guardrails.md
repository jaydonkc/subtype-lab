# Scientific Guardrails

The LLM must not invent biomarker claims or biological conclusions.

Rules:

- Claim verdicts must be computed from deterministic metrics.
- Reports must cite dataset hash, parameters, perturbation scores, and artifact paths.
- Do not present demo biomarkers as validated biological findings.
- Do not use clinical wording such as diagnostic, clinically proven, clinical validation, FDA approved, patient diagnosis, or treatment recommendation.
- If evidence is missing, report that the result is unsupported instead of filling gaps with prose.
