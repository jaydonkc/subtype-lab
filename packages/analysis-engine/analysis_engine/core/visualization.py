from __future__ import annotations

import numpy as np
import pandas as pd


def heatmap_payload(df: pd.DataFrame, labels: np.ndarray, max_features: int = 50) -> dict:
    """Return a compact heatmap payload for top-variable features."""

    if df.empty:
        return {"samples": [], "features": [], "values": [], "clusters": []}

    feature_count = min(max_features, df.shape[1])
    top_features = df.var(axis=0).sort_values(ascending=False).head(feature_count).index
    ordered_indices = np.lexsort((np.arange(len(labels)), labels))
    ordered = df.loc[:, top_features].iloc[ordered_indices]

    values = ordered.to_numpy(dtype=float)
    means = values.mean(axis=0)
    stds = values.std(axis=0)
    stds[stds == 0] = 1.0
    z_values = ((values - means) / stds).T

    return {
        "samples": [str(sample_id) for sample_id in ordered.index],
        "features": [str(feature) for feature in top_features],
        "values": np.round(z_values, 3).tolist(),
        "clusters": [int(labels[i]) for i in ordered_indices],
    }
