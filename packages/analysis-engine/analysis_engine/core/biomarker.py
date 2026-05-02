from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class BiomarkerRank:
    feature: str
    robustness_score: float
    baseline_score: float
    one_run_artifact: bool


def differential_scores(df: pd.DataFrame, labels: np.ndarray) -> pd.Series:
    values = df.to_numpy(dtype=float)
    unique_labels = np.unique(labels)
    overall_mean = values.mean(axis=0)
    between = np.zeros(values.shape[1])
    within = np.zeros(values.shape[1])
    for label in unique_labels:
        group = values[labels == label]
        if len(group) == 0:
            continue
        group_mean = group.mean(axis=0)
        between += len(group) * (group_mean - overall_mean) ** 2
        within += ((group - group_mean) ** 2).sum(axis=0)
    scores = between / (within + 1e-9)
    return pd.Series(scores, index=df.columns)


def top_k_features(df: pd.DataFrame, labels: np.ndarray, k_features: int | None = None) -> list[str]:
    k = k_features or max(1, min(20, int(df.shape[1] * 0.1)))
    scores = differential_scores(df, labels)
    return [str(feature) for feature in scores.sort_values(ascending=False).head(k).index]


def rank_biomarkers(
    df: pd.DataFrame,
    labels: np.ndarray,
    perturbation_top_features: list[list[str]],
    k_features: int | None = None,
) -> list[BiomarkerRank]:
    baseline_scores = differential_scores(df, labels)
    k = k_features or max(1, min(20, int(df.shape[1] * 0.1)))
    baseline_top = [str(f) for f in baseline_scores.sort_values(ascending=False).head(k).index]
    all_candidates = set(baseline_top)
    for features in perturbation_top_features:
        all_candidates.update(features)

    total_runs = max(1, len(perturbation_top_features))
    rankings: list[BiomarkerRank] = []
    for feature in sorted(all_candidates):
        count = sum(1 for features in perturbation_top_features if feature in features)
        robustness = count / total_runs
        rankings.append(
            BiomarkerRank(
                feature=feature,
                robustness_score=float(robustness),
                baseline_score=float(baseline_scores.get(feature, 0.0)),
                one_run_artifact=robustness < 0.5,
            )
        )
    rankings.sort(key=lambda item: (item.robustness_score, item.baseline_score), reverse=True)
    return rankings[:20]
