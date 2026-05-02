from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor

from ..services import DatasetRegistry, run_claim_audit
from .store import JobStore


class AuditExecutor:
    def __init__(self, datasets: DatasetRegistry, jobs: JobStore) -> None:
        self._datasets = datasets
        self._jobs = jobs
        self._executor = ThreadPoolExecutor(max_workers=2)

    def submit(self, dataset_id: str, claim_text: str, normalization_variant: str, seed: int = 42) -> str:
        job = self._jobs.create()
        self._executor.submit(self._run, job.job_id, dataset_id, claim_text, normalization_variant, seed)
        return job.job_id

    def _run(self, job_id: str, dataset_id: str, claim_text: str, normalization_variant: str, seed: int) -> None:
        self._jobs.update(job_id, state="running", phase="starting", total=17)

        def progress(completed: int, total: int, phase: str) -> None:
            self._jobs.update(job_id, completed=completed, total=total, phase=phase)

        try:
            dataset = self._datasets.get(dataset_id)
            result = run_claim_audit(dataset, claim_text, normalization_variant, seed, progress)
            self._jobs.update(
                job_id,
                state="completed",
                phase="completed",
                completed=17,
                total=17,
                result=result,
                finished_at=time.time(),
            )
        except Exception as exc:  # pragma: no cover - exercised through API manually
            current = self._jobs.get(job_id)
            self._jobs.update(
                job_id,
                state="failed",
                phase=current.phase,
                error=str(exc),
                finished_at=time.time(),
            )
