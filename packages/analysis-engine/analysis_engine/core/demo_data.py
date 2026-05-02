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
    n_features = 300

    labels = np.repeat(np.arange(n_subtypes), samples_per_subtype)
    sample_ids = [f"S{i + 1:03d}" for i in range(n_samples)]
    feature_names = [f"GENE_{i + 1:03d}" for i in range(n_features)]

    matrix = rng.normal(loc=0.0, scale=0.55, size=(n_samples, n_features))

    # Robust subtype signal: each subtype owns a distinct 55-gene block.
    for subtype in range(n_subtypes):
        rows = labels == subtype
        start = subtype * 55
        end = start + 55
        matrix[rows, start:end] += 4.2

    # Fragile biomarker-looking signal: smaller effect, intentionally sensitive
    # to feature dropout and noise.
    for subtype in range(n_subtypes):
        rows = labels == subtype
        start = 165 + subtype * 15
        end = start + 15
        matrix[rows, start:end] += 1.15

    batch_labels = np.array([f"batch_{(i % 3) + 1}" for i in range(n_samples)])
    batch_shift_features = slice(240, 270)
    matrix[batch_labels == "batch_2", batch_shift_features] += 0.45
    matrix[batch_labels == "batch_3", batch_shift_features] -= 0.35

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


def save_demo_data(output_dir: str | "Path", seed: int = DEMO_SEED) -> DemoDataset:
    from pathlib import Path

    demo = generate_demo_dataset(seed)
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)
    demo.matrix.to_csv(path / "expression.csv", index_label="sample_id")
    demo.metadata.to_csv(path / "metadata.csv", index_label="sample_id")
    return demo
