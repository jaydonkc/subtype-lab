from __future__ import annotations

from fastapi.testclient import TestClient
import pytest
import time

from analysis_engine.core.demo_data import generate_demo_dataset
from analysis_engine.main import app


client = TestClient(app)


def test_demo_dataset_endpoint() -> None:
    response = client.get("/api/datasets/demo")

    assert response.status_code == 200
    data = response.json()
    assert data["dataset_id"] == "demo"
    assert data["quality"]["sample_count"] == 90
    assert data["quality"]["feature_count"] == 300


def test_wdbc_dataset_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("analysis_engine.core.real_data.fetch_wdbc_data", lambda: (_ for _ in ()).throw(RuntimeError("offline")))

    response = client.get("/api/datasets/wdbc")

    assert response.status_code == 200
    data = response.json()
    assert data["dataset_id"] == "wdbc"
    assert data["quality"]["sample_count"] == 569
    assert data["quality"]["feature_count"] == 30
    assert data["source"]["license"] == "CC BY 4.0"
    assert data["source"]["loaded_from"] == "bundled_snapshot"
    assert data["metadata"]["columns"] == ["diagnosis_label", "dataset_source"]


def test_spec_route_aliases() -> None:
    response = client.post("/datasets/demo")
    assert response.status_code == 200

    response = client.post(
        "/analysis/baseline",
        json={
            "dataset_id": "demo",
            "claim_text": "These samples form three stable subtypes.",
            "normalization_variant": "zscore",
        },
    )
    assert response.status_code == 200
    assert response.json()["normalization_variant"] == "zscore"


def test_upload_dataset_with_metadata() -> None:
    demo = generate_demo_dataset()
    expression_csv = demo.matrix.to_csv(index_label="sample_id")
    metadata_csv = demo.metadata.to_csv(index_label="sample_id")

    response = client.post(
        "/api/datasets/upload",
        files={
            "file": ("expression.csv", expression_csv, "text/csv"),
            "metadata_file": ("metadata.csv", metadata_csv, "text/csv"),
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["quality"]["sample_count"] == 90
    assert payload["metadata"]["columns"] == ["subtype_label", "batch_label"]
    assert payload["metadata"]["index"][0] == "S001"


def test_report_endpoint_after_audit_job() -> None:
    response = client.post(
        "/analysis/audit",
        json={
            "dataset_id": "demo",
            "claim_text": "These samples form three stable subtypes.",
            "normalization_variant": "z-score",
        },
    )
    assert response.status_code == 202
    job_id = response.json()["job_id"]

    status = {}
    for _ in range(30):
        status = client.get(f"/jobs/{job_id}/status").json()
        if status["state"] == "completed":
            break
        time.sleep(0.05)

    assert status["state"] == "completed"
    result = client.get(f"/jobs/{job_id}/result").json()["result"]
    report_id = result["report"]["report_id"]

    explanation = client.get(f"/api/jobs/{job_id}/kiro-explanation")
    assert explanation.status_code == 200
    explanation_payload = explanation.json()
    assert explanation_payload["mode"] == "kiro_guided_explanation"
    assert explanation_payload["verdict_source"] == "computed_metrics"
    assert "computed" in explanation_payload["evidence"][0]["value"]

    report = client.get(f"/api/reports/{report_id}")
    assert report.status_code == 200
    assert report.json()["report_id"] == report_id

    html = client.get(f"/api/reports/{report_id}/html")
    assert html.status_code == 200
    assert "SubtypeLab Reproducibility Report" in html.text


def test_claim_guardrail_endpoint() -> None:
    response = client.post(
        "/api/jobs/audit",
        json={
            "dataset_id": "demo",
            "claim_text": "This is a diagnostic biomarker.",
            "normalization_variant": "z-score",
        },
    )

    assert response.status_code == 400
    assert "Clinical interpretation language" in response.json()["detail"]


def test_literature_evidence_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_search_literature(marker: str, context: str, limit: int) -> dict:
        assert marker == "TP53"
        assert context == "cancer subtype biomarker"
        assert limit == 3
        return {
            "marker": marker,
            "context": context,
            "query": "TP53[Title/Abstract] AND (cancer subtype biomarker)",
            "source": "PubMed E-utilities",
            "status": "ok",
            "evidence_level": "known",
            "total_hits": 42,
            "works_examined": 1,
            "summary": "TP53 appears frequently in PubMed for this context.",
            "caveats": ["Literature evidence maps prior mentions."],
            "hits": [
                {
                    "title": "TP53 and cancer subtypes",
                    "journal": "Example Journal",
                    "year": "2024",
                    "authors": ["Researcher A"],
                    "url": "https://pubmed.ncbi.nlm.nih.gov/123/",
                    "source": "PubMed",
                }
            ],
        }

    monkeypatch.setattr("analysis_engine.main.search_literature", fake_search_literature)

    response = client.post(
        "/api/literature/evidence",
        json={"marker": "TP53", "context": "cancer subtype biomarker", "limit": 3},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["evidence_level"] == "known"
    assert payload["total_hits"] == 42
    assert payload["hits"][0]["url"].startswith("https://pubmed.ncbi.nlm.nih.gov/")


def test_literature_evidence_skips_synthetic_demo_features() -> None:
    response = client.post(
        "/api/literature/evidence",
        json={"marker": "GENE_073", "context": "cancer subtype biomarker", "limit": 3},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "demo_only"
    assert payload["evidence_level"] == "demo_synthetic"
    assert payload["total_hits"] == 0
    assert "synthetic demo feature" in payload["summary"]


def test_agent_findings_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_build_agent_findings(result: dict) -> dict:
        assert result["verdict"] in {"robust", "suspicious", "fragile"}
        return {
            "mode": "deterministic_agent",
            "provider": "local",
            "model": "rules+literature",
            "headline": "Research agent findings: robust claim.",
            "executive_summary": "Evidence-grounded summary.",
            "findings": [
                {
                    "title": "Subtype claim is robust",
                    "finding_type": "claim",
                    "confidence": "high",
                    "evidence": "Computed stability score is high.",
                    "interpretation": "The agent summarized deterministic evidence.",
                    "recommended_next_step": "Validate in an independent cohort.",
                }
            ],
            "agent_trace": ["Read completed audit artifact."],
            "guardrails": ["No clinical claims."],
            "warnings": [],
            "evidence_snapshot": {"marker_evidence": []},
        }

    monkeypatch.setattr("analysis_engine.main.build_agent_findings", fake_build_agent_findings)
    response = client.post(
        "/analysis/audit",
        json={
            "dataset_id": "demo",
            "claim_text": "These samples form three stable subtypes.",
            "normalization_variant": "z-score",
        },
    )
    assert response.status_code == 202
    job_id = response.json()["job_id"]

    status = {}
    for _ in range(30):
        status = client.get(f"/jobs/{job_id}/status").json()
        if status["state"] == "completed":
            break
        time.sleep(0.05)

    assert status["state"] == "completed"
    response = client.get(f"/api/jobs/{job_id}/agent-findings")

    assert response.status_code == 200
    payload = response.json()
    assert payload["mode"] == "deterministic_agent"
    assert payload["findings"][0]["finding_type"] == "claim"
