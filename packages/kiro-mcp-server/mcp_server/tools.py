from __future__ import annotations

import sys
from pathlib import Path
from typing import Any


ENGINE_PATH = Path(__file__).resolve().parents[2] / "analysis-engine"
if str(ENGINE_PATH) not in sys.path:
    sys.path.insert(0, str(ENGINE_PATH))

from analysis_engine.core.claim import parse_claim  # noqa: E402
from analysis_engine.core.dataset import compute_quality_metrics, parse_dataset  # noqa: E402
from analysis_engine.core.normalization import normalize  # noqa: E402
from analysis_engine.services import DatasetRegistry, run_baseline_analysis, run_claim_audit  # noqa: E402


_datasets = DatasetRegistry()


def inspect_dataset(dataset_id: str = "demo", file_path: str | None = None) -> dict[str, Any]:
    if file_path:
        path = Path(file_path)
        record = parse_dataset(path.read_bytes(), path.name)
        quality = compute_quality_metrics(record.matrix)
        return {
            "dataset_id": record.dataset_id,
            "dataset_hash": record.dataset_hash,
            "quality": {
                "sample_count": quality.sample_count,
                "feature_count": quality.feature_count,
                "missing_value_count": quality.missing_value_count,
                "missing_value_percentage": quality.missing_value_percentage,
                "warnings": quality.warnings,
            },
        }
    return _datasets.describe(dataset_id)


def run_normalization(dataset_id: str = "demo", variant: str = "z-score") -> dict[str, Any]:
    dataset = _datasets.get(dataset_id)
    normalized = normalize(dataset.matrix, variant)
    return {
        "dataset_id": dataset_id,
        "variant": variant,
        "sample_count": normalized.shape[0],
        "feature_count": normalized.shape[1],
        "feature_means_head": normalized.mean().head(10).round(5).to_dict(),
    }


def run_subtyping(
    dataset_id: str = "demo",
    subtype_count: int = 3,
    normalization_variant: str = "z-score",
    seed: int = 42,
) -> dict[str, Any]:
    dataset = _datasets.get(dataset_id)
    claim = f"These samples form {subtype_count} stable subtypes."
    return run_baseline_analysis(dataset, claim, normalization_variant, seed)


def run_perturbation_suite(
    dataset_id: str = "demo",
    subtype_count: int = 3,
    normalization_variant: str = "z-score",
    seed: int = 42,
) -> dict[str, Any]:
    dataset = _datasets.get(dataset_id)
    claim = f"These samples form {subtype_count} stable subtypes."
    result = run_claim_audit(dataset, claim, normalization_variant, seed)
    return {
        "dataset_id": dataset_id,
        "stability_score": result["stability_score"],
        "per_type_scores": result["per_type_scores"],
        "verdict": result["verdict"],
    }


def rank_robust_biomarkers(
    dataset_id: str = "demo",
    claim_text: str = "These samples form three stable subtypes.",
    normalization_variant: str = "z-score",
    seed: int = 42,
) -> dict[str, Any]:
    dataset = _datasets.get(dataset_id)
    result = run_claim_audit(dataset, claim_text, normalization_variant, seed)
    return {
        "dataset_id": dataset_id,
        "verdict": result["verdict"],
        "top_biomarkers": result["biomarkers"],
    }


def audit_biological_claim(
    claim_text: str,
    dataset_id: str = "demo",
    normalization_variant: str = "z-score",
    seed: int = 42,
) -> dict[str, Any]:
    parse_claim(claim_text)
    dataset = _datasets.get(dataset_id)
    result = run_claim_audit(dataset, claim_text, normalization_variant, seed)
    return {
        "dataset_id": dataset_id,
        "claim_text": claim_text,
        "verdict": result["verdict"],
        "stability_score": result["stability_score"],
        "per_type_scores": result["per_type_scores"],
        "warnings": result["warnings"],
        "report_paths": result["report"].get("paths", {}),
    }


def generate_reproducibility_report(
    claim_text: str = "These samples form three stable subtypes.",
    dataset_id: str = "demo",
    normalization_variant: str = "z-score",
    seed: int = 42,
) -> dict[str, Any]:
    dataset = _datasets.get(dataset_id)
    result = run_claim_audit(dataset, claim_text, normalization_variant, seed)
    return result["report"]
