# Reproducibility Steering

Every analysis should be reproducible by default.

Required evidence:

- dataset hash
- normalization variant
- random seed
- perturbation parameters
- subtype count
- stability score
- per-perturbation scores
- computed verdict

Synthetic data generation, clustering, perturbations, and biomarker ranking must use fixed seeds when a seed is provided.
