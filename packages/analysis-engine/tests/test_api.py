from __future__ import annotations

from fastapi.testclient import TestClient

from analysis_engine.main import app


client = TestClient(app)


def test_demo_dataset_endpoint() -> None:
    response = client.get("/api/datasets/demo")

    assert response.status_code == 200
    data = response.json()
    assert data["dataset_id"] == "demo"
    assert data["quality"]["sample_count"] == 90


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
