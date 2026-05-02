from __future__ import annotations

import numpy as np

from analysis_engine.core.claim import parse_claim, validate_claim_language
from analysis_engine.core.demo_data import generate_demo_dataset
from analysis_engine.core.metrics import adjusted_rand_index
from analysis_engine.core.normalization import normalize
from analysis_engine.services import DatasetRegistry, run_baseline_analysis, run_claim_audit


def test_demo_dataset_is_deterministic() -> None:
    first = generate_demo_dataset()
    second = generate_demo_dataset()

    assert first.dataset_hash == second.dataset_hash
    assert first.matrix.shape == (90, 210)
    assert first.metadata.shape[0] == 90


def test_claim_parser_extracts_subtype_count() -> None:
    parsed = parse_claim("These samples form 3 stable subtypes.")

    assert parsed.claim_type == "subtype-count"
    assert parsed.subtype_count == 3


def test_clinical_language_is_rejected() -> None:
    try:
        validate_claim_language("This is a diagnostic biomarker.")
    except ValueError as exc:
        assert "Clinical interpretation language" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("clinical language should be rejected")


def test_baseline_analysis_on_demo_dataset() -> None:
    registry = DatasetRegistry()
    result = run_baseline_analysis(
        registry.get("demo"),
        "These samples form three stable subtypes.",
    )

    assert result["subtype_count"] == 3
    assert len(result["cluster_labels"]) == 90
    assert result["silhouette_score"] > 0.35
    assert result["top_biomarkers"]


def test_audit_result_has_computed_verdict_and_report() -> None:
    registry = DatasetRegistry()
    result = run_claim_audit(
        registry.get("demo"),
        "These samples form three stable subtypes.",
    )

    assert result["verdict"] in {"robust", "suspicious", "fragile"}
    assert 0 <= result["stability_score"] <= 1
    assert result["per_type_scores"]
    assert result["report"]["dataset_hash"] == result["dataset_hash"]
    assert "json" in result["report"]["paths"]


def test_normalization_variants_preserve_shape() -> None:
    demo = generate_demo_dataset()
    for variant in ("none", "log2", "z-score", "quantile"):
        normalized = normalize(demo.matrix, variant)
        assert normalized.shape == demo.matrix.shape


def test_adjusted_rand_index_identity() -> None:
    labels = np.array([0, 0, 1, 1, 2, 2])

    assert adjusted_rand_index(labels, labels) == 1.0
