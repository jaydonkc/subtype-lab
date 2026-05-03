from __future__ import annotations

import os
from dataclasses import asdict
from pathlib import Path
from typing import Callable

import numpy as np

from .core.biomarker import rank_biomarkers
from .core.claim import parse_claim, validate_claim_language
from .core.clustering import cluster_dataframe
from .core.dataset import DatasetRecord, compute_quality_metrics, dataframe_payload
from .core.demo_data import generate_demo_dataset
from .core.normalization import normalize
from .core.perturbation import run_perturbation_suite
from .core.real_data import load_wdbc_dataset
from .core.report import find_report, find_report_html, generate_report
from .core.verdict import compute_verdict
from .core.visualization import heatmap_payload


ARTIFACT_ROOT = Path(os.environ.get("ARTIFACT_ROOT", Path.cwd() / "artifacts"))


class DatasetRegistry:
    def __init__(self) -> None:
        demo = generate_demo_dataset()
        self._datasets: dict[str, DatasetRecord] = {
            "demo": DatasetRecord(demo.dataset_id, demo.dataset_hash, demo.matrix, demo.metadata)
        }

    def add(self, record: DatasetRecord) -> DatasetRecord:
        self._datasets[record.dataset_id] = record
        return record

    def load_wdbc(self) -> DatasetRecord:
        public_dataset = load_wdbc_dataset()
        return self.add(
            DatasetRecord(
                public_dataset.dataset_id,
                public_dataset.dataset_hash,
                public_dataset.matrix,
                public_dataset.metadata,
                source=public_dataset.source,
            )
        )

    def get(self, dataset_id: str) -> DatasetRecord:
        if dataset_id not in self._datasets:
            raise KeyError(f"Unknown dataset_id: {dataset_id}")
        return self._datasets[dataset_id]

    def describe(self, dataset_id: str) -> dict:
        record = self.get(dataset_id)
        metrics = compute_quality_metrics(record.matrix)
        return {
            "dataset_id": record.dataset_id,
            "dataset_hash": record.dataset_hash,
            "quality": asdict(metrics),
            "preview": dataframe_payload(record.matrix, max_rows=8),
            "metadata": dataframe_payload(record.metadata, max_rows=8) if record.metadata is not None else None,
            "source": record.source,
        }


def run_baseline_analysis(
    dataset: DatasetRecord,
    claim_text: str,
    normalization_variant: str = "z-score",
    seed: int = 42,
) -> dict:
    parsed = parse_claim(claim_text)
    normalized = normalize(dataset.matrix, normalization_variant)
    cluster = cluster_dataframe(normalized, parsed.subtype_count, seed=seed)
    labels = np.array(cluster.labels)
    biomarkers = rank_biomarkers(normalized, labels, [])
    return {
        "dataset_id": dataset.dataset_id,
        "dataset_hash": dataset.dataset_hash,
        "claim_text": parsed.text,
        "claim_type": parsed.claim_type,
        "subtype_count": parsed.subtype_count,
        "normalization_variant": normalization_variant,
        "cluster_labels": cluster.labels,
        "wcss": cluster.wcss,
        "silhouette_score": cluster.silhouette_score,
        "pca": cluster.pca,
        "heatmap": heatmap_payload(normalized, labels),
        "top_biomarkers": [asdict(item) for item in biomarkers],
    }


def run_claim_audit(
    dataset: DatasetRecord,
    claim_text: str,
    normalization_variant: str = "z-score",
    seed: int = 42,
    progress_callback: Callable[[int, int, str], None] | None = None,
) -> dict:
    validate_claim_language(claim_text)
    baseline = run_baseline_analysis(dataset, claim_text, normalization_variant, seed)
    normalized = normalize(dataset.matrix, normalization_variant)
    labels = np.array(baseline["cluster_labels"])
    suite = run_perturbation_suite(
        normalized,
        labels,
        baseline["subtype_count"],
        seed=seed,
        progress_callback=progress_callback,
    )
    biomarkers = rank_biomarkers(
        normalized,
        labels,
        [run.top_features for run in suite.runs],
    )
    verdict = compute_verdict(suite.stability_score)
    weakest = min(suite.per_type_scores, key=suite.per_type_scores.get) if suite.per_type_scores else "none"
    warnings = []
    if verdict != "robust":
        warnings.append(f"Lowest consistency came from {weakest}. Review this before trusting the claim.")
    one_run_count = sum(1 for item in biomarkers if item.one_run_artifact)
    if one_run_count:
        warnings.append(
            f"{one_run_count} of the top {len(biomarkers)} candidate biomarkers behaved like one-run artifacts."
        )

    result = {
        **baseline,
        "stability_score": suite.stability_score,
        "per_type_scores": suite.per_type_scores,
        "perturbation_runs": [asdict(run) for run in suite.runs],
        "verdict": verdict,
        "warnings": warnings,
        "biomarkers": [asdict(item) for item in biomarkers],
        "perturbation_parameters": {
            "dropout_rates": [0.1, 0.2, 0.3],
            "noise_sigmas": [0.1, 0.5, 1.0],
            "cohort_split_seeds": [0, 1, 2],
            "batch_shift_fraction": 0.3,
            "random_seed": seed,
        },
        "artifact_links": [],
    }

    report = generate_report(result, ARTIFACT_ROOT)
    result["report"] = report
    return result


def get_report(report_id: str) -> dict:
    return find_report(ARTIFACT_ROOT, report_id)


def get_report_html(report_id: str) -> str:
    return find_report_html(ARTIFACT_ROOT, report_id)
