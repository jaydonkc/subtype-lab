from __future__ import annotations

import hashlib
from dataclasses import dataclass

import numpy as np
import pandas as pd


DEMO_SEED = 42


@dataclass(frozen=True)
class DemoDataset:
    dataset_id: str
    dataset_hash: str
    matrix: pd.DataFrame
    metadata: pd.DataFrame


def generate_demo_dataset(seed: int = DEMO_SEED) -> DemoDataset:
    """Generate a deterministic synthetic expression-style dataset.

    The data has three strong subtype signals, a smaller fragile signal, and
    batch labels. It is synthetic and contains no patient-derived values.
    """

    rng = np.random.default_rng(seed)
    n_subtypes = 3
    samples_per_subtype = 30
    n_samples = n_subtypes * samples_per_subtype
    n_features = 210

    labels = np.repeat(np.arange(n_subtypes), samples_per_subtype)
    sample_ids = [f"S{i + 1:03d}" for i in range(n_samples)]
    feature_names = [f"GENE_{i + 1:03d}" for i in range(n_features)]

    matrix = rng.normal(loc=0.0, scale=0.55, size=(n_samples, n_features))

    # Robust subtype signal: each subtype owns a distinct 35-gene block.
    for subtype in range(n_subtypes):
        rows = labels == subtype
        start = subtype * 35
        end = start + 35
        matrix[rows, start:end] += 4.2

    # Fragile biomarker-looking signal: smaller effect, intentionally sensitive
    # to feature dropout and noise.
    for subtype in range(n_subtypes):
        rows = labels == subtype
        start = 105 + subtype * 10
        end = start + 10
        matrix[rows, start:end] += 1.15

    batch_labels = np.where(np.arange(n_samples) % 2 == 0, "batch_1", "batch_2")
    batch_shift_features = slice(150, 180)
    matrix[batch_labels == "batch_2", batch_shift_features] += 0.45

    df = pd.DataFrame(matrix, index=sample_ids, columns=feature_names)
    metadata = pd.DataFrame(
        {
            "sample_id": sample_ids,
            "subtype_label": [f"Subtype {chr(65 + i)}" for i in labels],
            "batch_label": batch_labels,
        }
    ).set_index("sample_id")

    raw = df.to_csv().encode("utf-8")
    dataset_hash = hashlib.sha256(raw).hexdigest()

    return DemoDataset(
        dataset_id="demo",
        dataset_hash=dataset_hash,
        matrix=df,
        metadata=metadata,
    )
