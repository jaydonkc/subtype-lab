from __future__ import annotations

import hashlib
import io
from dataclasses import dataclass, field

import numpy as np
import pandas as pd


@dataclass
class DatasetRecord:
    dataset_id: str
    dataset_hash: str
    matrix: pd.DataFrame
    metadata: pd.DataFrame | None = None
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class QualityMetrics:
    sample_count: int
    feature_count: int
    missing_value_count: int
    missing_value_percentage: float
    feature_summaries: list[dict[str, float | str]]
    warnings: list[str]


def compute_dataset_hash(file_bytes: bytes) -> str:
    return hashlib.sha256(file_bytes).hexdigest()


def parse_dataset(file_bytes: bytes, filename: str) -> DatasetRecord:
    sep = _separator_for(filename)
    try:
        df = pd.read_csv(io.BytesIO(file_bytes), sep=sep)
    except Exception as exc:  # pragma: no cover - pandas message varies
        raise ValueError(f"Could not parse {filename} as CSV/TSV: {exc}") from exc

    if df.empty:
        raise ValueError("Dataset is empty.")

    first_col = str(df.columns[0]).lower()
    if first_col in {"sample_id", "sample", "id", "index"}:
        df = df.set_index(df.columns[0])
    else:
        df.index = [f"S{i + 1:03d}" for i in range(len(df))]

    df.index = df.index.map(str)
    df.columns = df.columns.map(str)
    df = df.apply(pd.to_numeric, errors="coerce")
    validate_dataset(df)
    dataset_hash = compute_dataset_hash(file_bytes)
    return DatasetRecord(dataset_hash[:12], dataset_hash, df)


def parse_metadata(file_bytes: bytes, filename: str) -> pd.DataFrame:
    sep = _separator_for(filename)
    metadata = pd.read_csv(io.BytesIO(file_bytes), sep=sep)
    if metadata.empty:
        raise ValueError("Metadata file is empty.")
    if "sample_id" in metadata.columns:
        metadata = metadata.set_index("sample_id")
    else:
        first_col = str(metadata.columns[0]).lower()
        if first_col in {"sample", "id", "index"}:
            metadata = metadata.set_index(metadata.columns[0])
    metadata.index = metadata.index.map(str)
    return metadata


def attach_metadata(record: DatasetRecord, metadata: pd.DataFrame) -> DatasetRecord:
    matrix_index = record.matrix.index.map(str)
    metadata = metadata.copy()
    metadata.index = metadata.index.map(str)

    if set(matrix_index).issubset(set(metadata.index)):
        aligned = metadata.loc[matrix_index]
    elif len(metadata) == len(record.matrix):
        aligned = metadata.copy()
        aligned.index = matrix_index
    else:
        missing = [sample_id for sample_id in matrix_index if sample_id not in set(metadata.index)]
        preview = ", ".join(missing[:5])
        raise ValueError(f"Metadata does not align to dataset samples. Missing sample IDs: {preview}.")

    return DatasetRecord(
        dataset_id=record.dataset_id,
        dataset_hash=record.dataset_hash,
        matrix=record.matrix,
        metadata=aligned,
        warnings=record.warnings,
    )


def validate_dataset(df: pd.DataFrame) -> None:
    if df.shape[0] < 10 or df.shape[1] < 5:
        raise ValueError("Dataset must contain at least 10 samples and 5 features.")
    if not np.isfinite(df.fillna(0).to_numpy(dtype=float)).all():
        raise ValueError("Dataset contains non-finite values.")


def compute_quality_metrics(df: pd.DataFrame) -> QualityMetrics:
    sample_count, feature_count = df.shape
    missing_count = int(df.isna().sum().sum())
    total_values = sample_count * feature_count
    missing_pct = (missing_count / total_values * 100.0) if total_values else 0.0

    summaries: list[dict[str, float | str]] = []
    warnings: list[str] = []
    for name in df.columns:
        series = df[name]
        zero_pct = float((series.fillna(0) == 0).mean() * 100.0)
        std = float(series.std(skipna=True) or 0.0)
        if zero_pct > 80.0 or std < 1e-9:
            warnings.append(f"{name} has low variation or high zero percentage.")
        summaries.append(
            {
                "feature": str(name),
                "mean": float(series.mean(skipna=True)),
                "std": std,
                "zero_value_percentage": zero_pct,
            }
        )

    if missing_pct > 20.0:
        warnings.append("High missingness: more than 20% of values are missing.")

    return QualityMetrics(
        sample_count=sample_count,
        feature_count=feature_count,
        missing_value_count=missing_count,
        missing_value_percentage=missing_pct,
        feature_summaries=summaries,
        warnings=warnings,
    )


def dataframe_payload(df: pd.DataFrame, max_rows: int | None = None) -> dict:
    view = df if max_rows is None else df.head(max_rows)
    return {
        "index": [str(i) for i in view.index],
        "columns": [str(c) for c in view.columns],
        "values": view.fillna(0).round(5).values.tolist(),
    }


def _separator_for(filename: str) -> str:
    lower = filename.lower()
    if lower.endswith(".tsv") or lower.endswith(".tab"):
        return "\t"
    if lower.endswith(".csv"):
        return ","
    raise ValueError("Uploaded file must be CSV or TSV.")
