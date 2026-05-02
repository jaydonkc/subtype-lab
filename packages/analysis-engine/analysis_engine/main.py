from __future__ import annotations

from dataclasses import asdict

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .core.claim import find_prohibited_terms, parse_claim
from .core.dataset import compute_quality_metrics, parse_dataset
from .jobs.executor import AuditExecutor
from .jobs.store import JobStore
from .services import DatasetRegistry, run_baseline_analysis


app = FastAPI(title="SubtypeLab Analysis Engine", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

datasets = DatasetRegistry()
jobs = JobStore()
executor = AuditExecutor(datasets, jobs)


class ClaimRequest(BaseModel):
    dataset_id: str = "demo"
    claim_text: str = Field(default="These samples form three stable subtypes.")
    normalization_variant: str = "z-score"
    seed: int = 42


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/datasets/demo")
def get_demo_dataset() -> dict:
    return datasets.describe("demo")


@app.post("/api/datasets/upload")
async def upload_dataset(file: UploadFile = File(...)) -> dict:
    try:
        content = await file.read()
        record = parse_dataset(content, file.filename or "dataset.csv")
        datasets.add(record)
        return datasets.describe(record.dataset_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/datasets/{dataset_id}/quality")
def dataset_quality(dataset_id: str) -> dict:
    try:
        dataset = datasets.get(dataset_id)
        return asdict(compute_quality_metrics(dataset.matrix))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/claims/parse")
def parse_claim_endpoint(request: ClaimRequest) -> dict:
    try:
        parsed = parse_claim(request.claim_text)
        return asdict(parsed)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/baseline")
def baseline(request: ClaimRequest) -> dict:
    try:
        dataset = datasets.get(request.dataset_id)
        return run_baseline_analysis(
            dataset,
            request.claim_text,
            request.normalization_variant,
            request.seed,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/jobs/audit", status_code=202)
def start_audit(request: ClaimRequest) -> dict:
    prohibited = find_prohibited_terms(request.claim_text)
    if prohibited:
        raise HTTPException(
            status_code=400,
            detail=f"Clinical interpretation language is not supported: {', '.join(prohibited)}.",
        )
    try:
        datasets.get(request.dataset_id)
        job_id = executor.submit(
            request.dataset_id,
            request.claim_text,
            request.normalization_variant,
            request.seed,
        )
        return {"job_id": job_id, "state": "queued"}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/api/jobs/{job_id}/status")
def job_status(job_id: str) -> dict:
    try:
        return jobs.get(job_id).status()
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/api/jobs/{job_id}/artifacts")
def job_artifacts(job_id: str) -> dict:
    try:
        job = jobs.get(job_id)
        if job.state == "failed":
            return {"status": job.status(), "result": job.result}
        if job.state != "completed":
            raise HTTPException(status_code=409, detail="Job is not complete yet.")
        return {"status": job.status(), "result": job.result}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
