from __future__ import annotations

from contextlib import asynccontextmanager
from dataclasses import asdict

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from .core.claim import find_prohibited_terms, parse_claim
from .core.dataset import attach_metadata, compute_quality_metrics, parse_dataset, parse_metadata
from .core.demo_data import save_demo_data
from .core.literature import search_literature
from .jobs.executor import AuditExecutor
from .jobs.store import JobStore
from .services import DatasetRegistry, get_report, get_report_html, run_baseline_analysis


@asynccontextmanager
async def lifespan(_app: FastAPI):
    save_demo_data("demo-data")
    yield


app = FastAPI(title="SubtypeLab Analysis Engine", version="0.1.0", lifespan=lifespan)
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


class ReportRequest(BaseModel):
    job_id: str


class LiteratureRequest(BaseModel):
    marker: str
    context: str = "cancer subtype biomarker"
    limit: int = Field(default=5, ge=1, le=10)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/")
def root() -> dict[str, str]:
    return {"name": "SubtypeLab", "status": "ready"}


@app.get("/api/datasets/demo")
def get_demo_dataset() -> dict:
    return datasets.describe("demo")


@app.post("/datasets/demo")
def post_demo_dataset() -> dict:
    return datasets.describe("demo")


@app.post("/api/datasets/upload")
async def upload_dataset(
    file: UploadFile = File(...),
    metadata_file: UploadFile | None = File(default=None),
) -> dict:
    try:
        content = await file.read()
        record = parse_dataset(content, file.filename or "dataset.csv")
        if metadata_file is not None:
            metadata_content = await metadata_file.read()
            metadata = parse_metadata(metadata_content, metadata_file.filename or "metadata.csv")
            record = attach_metadata(record, metadata)
        datasets.add(record)
        return datasets.describe(record.dataset_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/datasets/upload")
async def upload_dataset_alias(
    file: UploadFile = File(...),
    metadata_file: UploadFile | None = File(default=None),
) -> dict:
    return await upload_dataset(file, metadata_file)


@app.get("/api/datasets/{dataset_id}/quality")
def dataset_quality(dataset_id: str) -> dict:
    try:
        dataset = datasets.get(dataset_id)
        return asdict(compute_quality_metrics(dataset.matrix))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/datasets/{dataset_id}/quality")
def dataset_quality_alias(dataset_id: str) -> dict:
    return dataset_quality(dataset_id)


@app.post("/api/claims/parse")
def parse_claim_endpoint(request: ClaimRequest) -> dict:
    try:
        parsed = parse_claim(request.claim_text)
        return asdict(parsed)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/claims/parse")
def parse_claim_alias(request: ClaimRequest) -> dict:
    return parse_claim_endpoint(request)


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


@app.post("/analysis/baseline")
def baseline_alias(request: ClaimRequest) -> dict:
    return baseline(request)


@app.post("/api/literature/evidence")
def literature_evidence(request: LiteratureRequest) -> dict:
    try:
        return search_literature(request.marker, request.context, request.limit)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/literature/evidence")
def literature_evidence_alias(request: LiteratureRequest) -> dict:
    return literature_evidence(request)


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


@app.post("/analysis/audit", status_code=202)
def start_audit_alias(request: ClaimRequest) -> dict:
    return start_audit(request)


@app.get("/api/jobs/{job_id}/status")
def job_status(job_id: str) -> dict:
    try:
        return jobs.get(job_id).status()
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/jobs/{job_id}/status")
def job_status_alias(job_id: str) -> dict:
    return job_status(job_id)


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


@app.get("/api/jobs/{job_id}/result")
def job_result(job_id: str) -> dict:
    return job_artifacts(job_id)


@app.get("/jobs/{job_id}/result")
def job_result_alias(job_id: str) -> dict:
    return job_artifacts(job_id)


@app.get("/jobs/{job_id}/artifacts")
def job_artifacts_alias(job_id: str) -> dict:
    return job_artifacts(job_id)


@app.post("/api/reports/generate")
def generate_existing_report(request: ReportRequest) -> dict:
    try:
        job = jobs.get(request.job_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if job.state != "completed" or not job.result:
        raise HTTPException(status_code=409, detail="Job is not complete yet.")
    return job.result["report"]


@app.post("/reports/generate")
def generate_existing_report_alias(request: ReportRequest) -> dict:
    return generate_existing_report(request)


@app.get("/api/reports/{report_id}")
def fetch_report(report_id: str) -> dict:
    try:
        return get_report(report_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/reports/{report_id}")
def fetch_report_alias(report_id: str) -> dict:
    return fetch_report(report_id)


@app.get("/api/reports/{report_id}/html", response_class=HTMLResponse)
def fetch_report_html(report_id: str) -> HTMLResponse:
    try:
        return HTMLResponse(get_report_html(report_id))
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/reports/{report_id}/html", response_class=HTMLResponse)
def fetch_report_html_alias(report_id: str) -> HTMLResponse:
    return fetch_report_html(report_id)
