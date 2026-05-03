from __future__ import annotations

import numpy as np
import pytest

from analysis_engine.core.agent_findings import collect_agent_evidence
from analysis_engine.core.claim import parse_claim, validate_claim_language
from analysis_engine.core.dataset import DatasetRecord, attach_metadata
from analysis_engine.core.demo_data import generate_demo_dataset
from analysis_engine.core.metrics import adjusted_rand_index
from analysis_engine.core.normalization import normalize
from analysis_engine.core.perturbation import run_perturbation_suite
from analysis_engine.services import DatasetRegistry, run_baseline_analysis, run_claim_audit


def test_demo_dataset_is_deterministic() -> None:
    first = generate_demo_dataset()
    second = generate_demo_dataset()

    assert first.dataset_hash == second.dataset_hash
    assert first.matrix.shape == (90, 300)
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


def test_metadata_alignment_uses_sample_ids() -> None:
    demo = generate_demo_dataset()
    shuffled = demo.metadata.sample(frac=1.0, random_state=7)
    record = DatasetRecord(demo.dataset_id, demo.dataset_hash, demo.matrix, None)

    aligned = attach_metadata(record, shuffled)

    assert aligned.metadata is not None
    assert aligned.metadata.index.tolist() == demo.matrix.index.tolist()
    assert aligned.metadata.iloc[0]["subtype_label"] == "Subtype A"


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
    assert result["heatmap"]["features"]
    assert result["heatmap"]["samples"]


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
    assert result["report"]["report_id"]
    assert "json" in result["report"]["paths"]


def test_normalization_variants_preserve_shape() -> None:
    demo = generate_demo_dataset()
    for variant in ("none", "log2", "z-score", "quantile"):
        normalized = normalize(demo.matrix, variant)
        assert normalized.shape == demo.matrix.shape


def test_adjusted_rand_index_identity() -> None:
    labels = np.array([0, 0, 1, 1, 2, 2])

    assert adjusted_rand_index(labels, labels) == 1.0


def test_perturbation_suite_count_and_determinism() -> None:
    registry = DatasetRegistry()
    baseline = run_baseline_analysis(
        registry.get("demo"),
        "These samples form three stable subtypes.",
    )
    normalized = normalize(registry.get("demo").matrix, "z-score")
    labels = np.array(baseline["cluster_labels"])

    first = run_perturbation_suite(normalized, labels, 3, seed=123)
    second = run_perturbation_suite(normalized, labels, 3, seed=123)

    assert len(first.runs) == 17
    assert [round(run.score, 8) for run in first.runs] == [
        round(run.score, 8) for run in second.runs
    ]


def test_agent_findings_skip_pubmed_for_synthetic_demo_markers(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_literature_lookup(*_args: object, **_kwargs: object) -> dict:
        raise AssertionError("synthetic demo features should not call PubMed")

    monkeypatch.setattr("analysis_engine.core.agent_findings.search_literature", fail_literature_lookup)
    evidence = collect_agent_evidence(
        {
            "claim_text": "These samples form three stable subtypes.",
            "dataset_id": "demo",
            "dataset_hash": "hash",
            "verdict": "robust",
            "stability_score": 1.0,
            "per_type_scores": {},
            "warnings": [],
            "normalization_variant": "z-score",
            "subtype_count": 3,
            "biomarkers": [
                {
                    "feature": "GENE_001",
                    "robustness_score": 0.9,
                    "baseline_score": 12.0,
                    "one_run_artifact": False,
                }
            ],
        },
        marker_limit=1,
        literature_limit=1,
    )

    assert evidence["marker_evidence"][0]["literature"]["status"] == "demo_only"
    assert evidence["marker_evidence"][0]["literature"]["evidence_level"] == "demo_synthetic"
