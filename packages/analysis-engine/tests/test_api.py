from __future__ import annotations

from fastapi.testclient import TestClient
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
