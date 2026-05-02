from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np
import pandas as pd

from .biomarker import top_k_features
from .clustering import run_kmeans
from .metrics import adjusted_rand_index
from .normalization import NORMALIZATION_VARIANTS, normalize


@dataclass(frozen=True)
class PerturbationRun:
    perturbation_type: str
    label: str
    score: float
    labels: list[int]
    sample_indices: list[int]
    top_features: list[str]


@dataclass(frozen=True)
class PerturbationSuiteResult:
    runs: list[PerturbationRun]
    per_type_scores: dict[str, float]
    stability_score: float


ProgressCallback = Callable[[int, int, str], None]


def run_perturbation_suite(
    df: pd.DataFrame,
    baseline_labels: np.ndarray,
    k: int,
    seed: int = 42,
    progress_callback: ProgressCallback | None = None,
) -> PerturbationSuiteResult:
    total = 3 + 3 + 6 + len(NORMALIZATION_VARIANTS) + 1
    completed = 0
    runs: list[PerturbationRun] = []

    def add_run(kind: str, label: str, perturbed_df: pd.DataFrame, sample_indices: list[int], run_seed: int) -> None:
        nonlocal completed
        labels, _ = run_kmeans(perturbed_df, k=k, seed=run_seed)
        reference = baseline_labels[sample_indices]
        score = adjusted_rand_index(reference, labels)
        features = top_k_features(perturbed_df, labels)
        runs.append(
            PerturbationRun(
                perturbation_type=kind,
                label=label,
                score=float(score),
                labels=[int(v) for v in labels],
                sample_indices=sample_indices,
                top_features=features,
            )
        )
        completed += 1
        if progress_callback:
            progress_callback(completed, total, kind)

    base_indices = list(range(len(df)))
    rng = np.random.default_rng(seed)

    for rate in (0.1, 0.2, 0.3):
        keep_count = max(5, int(df.shape[1] * (1.0 - rate)))
        keep_cols = rng.choice(df.columns.to_numpy(), size=keep_count, replace=False)
        perturbed = df.loc[:, keep_cols]
        add_run("missing_feature_dropout", f"drop_{int(rate * 100)}pct", perturbed, base_indices, seed + completed)

    values = df.to_numpy(dtype=float)
    scale = float(np.std(values)) or 1.0
    for sigma in (0.1, 0.5, 1.0):
        noise = rng.normal(0.0, sigma * scale, size=values.shape)
        perturbed = pd.DataFrame(values + noise, index=df.index, columns=df.columns)
        add_run("noisy_sample_injection", f"sigma_{sigma}", perturbed, base_indices, seed + completed)

    for split_seed in (0, 1, 2):
        split_rng = np.random.default_rng(seed + split_seed)
        shuffled = split_rng.permutation(len(df))
        midpoint = len(shuffled) // 2
        for half, indices in enumerate((np.sort(shuffled[:midpoint]), np.sort(shuffled[midpoint:]))):
            perturbed = df.iloc[indices]
            add_run(
                "cohort_split",
                f"seed_{split_seed}_half_{half + 1}",
                perturbed,
                [int(i) for i in indices],
                seed + completed,
            )

    for variant in NORMALIZATION_VARIANTS:
        perturbed = normalize(df, variant)
        add_run("normalization_variant", variant, perturbed, base_indices, seed + completed)

    shifted = df.copy()
    selected = rng.choice(len(df), size=max(1, int(len(df) * 0.3)), replace=False)
    shift = float(df.to_numpy(dtype=float).std()) * 0.65
    shifted.iloc[selected] = shifted.iloc[selected] + shift
    add_run("batch_like_shift", "30pct_samples_mean_shift", shifted, base_indices, seed + completed)

    per_type: dict[str, list[float]] = {}
    for run in runs:
        per_type.setdefault(run.perturbation_type, []).append(run.score)
    per_type_scores = {kind: float(np.mean(scores)) for kind, scores in per_type.items()}
    stability = float(np.mean([run.score for run in runs])) if runs else 0.0

    return PerturbationSuiteResult(runs=runs, per_type_scores=per_type_scores, stability_score=stability)
