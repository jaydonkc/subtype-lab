from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class ClusterResult:
    labels: list[int]
    wcss: float
    silhouette_score: float
    pca: list[dict[str, float | int | str]]


def run_kmeans(df: pd.DataFrame, k: int, seed: int = 42, max_iter: int = 100) -> tuple[np.ndarray, float]:
    values = df.to_numpy(dtype=float)
    if k < 2:
        raise ValueError("Subtype count must be at least 2.")
    if len(values) < k:
        raise ValueError("Subtype count cannot exceed sample count.")

    rng = np.random.default_rng(seed)
    first = int(rng.integers(0, len(values)))
    centers = [values[first]]
    for _ in range(1, k):
        dist_sq = np.min(_squared_distances(values, np.array(centers)), axis=1)
        if float(dist_sq.sum()) == 0.0:
            candidate = int(rng.integers(0, len(values)))
        else:
            probabilities = dist_sq / dist_sq.sum()
            candidate = int(rng.choice(len(values), p=probabilities))
        centers.append(values[candidate])

    centers_array = np.array(centers, dtype=float)
    labels = np.zeros(len(values), dtype=int)

    for _ in range(max_iter):
        distances = _squared_distances(values, centers_array)
        next_labels = np.argmin(distances, axis=1)
        next_centers = centers_array.copy()
        for cluster in range(k):
            cluster_values = values[next_labels == cluster]
            if len(cluster_values):
                next_centers[cluster] = cluster_values.mean(axis=0)
        if np.array_equal(next_labels, labels):
            centers_array = next_centers
            break
        labels = next_labels
        centers_array = next_centers

    wcss = float(np.sum((values - centers_array[labels]) ** 2))
    return labels, wcss


def cluster_dataframe(df: pd.DataFrame, k: int, seed: int = 42) -> ClusterResult:
    labels, wcss = run_kmeans(df, k=k, seed=seed)
    silhouette = compute_silhouette(df, labels)
    pca_rows = run_pca(df, labels)
    return ClusterResult(
        labels=[int(v) for v in labels],
        wcss=wcss,
        silhouette_score=silhouette,
        pca=pca_rows,
    )


def compute_silhouette(df: pd.DataFrame, labels: np.ndarray) -> float:
    values = df.to_numpy(dtype=float)
    unique_labels = np.unique(labels)
    if len(unique_labels) < 2 or len(unique_labels) >= len(values):
        return 0.0

    distances = np.sqrt(_squared_distances(values, values))
    scores = []
    for idx, label in enumerate(labels):
        same_mask = labels == label
        other_mask = labels != label
        same_distances = distances[idx, same_mask]
        a = float(same_distances[same_distances > 0].mean()) if same_distances.size > 1 else 0.0
        b = min(
            float(distances[idx, labels == other].mean())
            for other in unique_labels
            if other != label and np.any(labels == other)
        )
        denom = max(a, b)
        scores.append(0.0 if denom == 0 else (b - a) / denom)
        if not np.any(other_mask):
            scores[-1] = 0.0
    return float(np.mean(scores))


def run_pca(df: pd.DataFrame, labels: np.ndarray) -> list[dict[str, float | int | str]]:
    values = df.to_numpy(dtype=float)
    centered = values - values.mean(axis=0)
    _, _, vt = np.linalg.svd(centered, full_matrices=False)
    components = centered @ vt[:2].T
    if components.shape[1] == 1:
        components = np.column_stack([components[:, 0], np.zeros(len(components))])
    return [
        {
            "sample_id": str(sample_id),
            "pc1": float(components[i, 0]),
            "pc2": float(components[i, 1]),
            "cluster": int(labels[i]),
        }
        for i, sample_id in enumerate(df.index)
    ]


def _squared_distances(values: np.ndarray, centers: np.ndarray) -> np.ndarray:
    diff = values[:, None, :] - centers[None, :, :]
    return np.sum(diff * diff, axis=2)
