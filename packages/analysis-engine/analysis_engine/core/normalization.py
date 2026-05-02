from __future__ import annotations

import numpy as np
import pandas as pd


NORMALIZATION_VARIANTS = ("none", "log2", "z-score", "quantile")


def normalize(df: pd.DataFrame, variant: str) -> pd.DataFrame:
    variant = variant.lower()
    if variant not in NORMALIZATION_VARIANTS:
        raise ValueError(f"Unsupported normalization variant: {variant}")

    clean = df.astype(float).copy()
    clean = clean.fillna(clean.mean(numeric_only=True)).fillna(0.0)

    if variant == "none":
        return clean

    values = clean.to_numpy(dtype=float)

    if variant == "log2":
        min_value = float(np.nanmin(values))
        shifted = values - min_value + 1.0 if min_value <= 0 else values + 1.0
        return pd.DataFrame(np.log2(shifted), index=clean.index, columns=clean.columns)

    if variant == "z-score":
        means = values.mean(axis=0)
        stds = values.std(axis=0)
        stds[stds == 0] = 1.0
        normalized = (values - means) / stds
        return pd.DataFrame(normalized, index=clean.index, columns=clean.columns)

    # Simple quantile normalization across features.
    sorted_values = np.sort(values, axis=0)
    rank_means = sorted_values.mean(axis=1)
    ranks = np.argsort(np.argsort(values, axis=0), axis=0)
    normalized = np.zeros_like(values)
    for col_idx in range(values.shape[1]):
        normalized[:, col_idx] = rank_means[ranks[:, col_idx]]
    return pd.DataFrame(normalized, index=clean.index, columns=clean.columns)
