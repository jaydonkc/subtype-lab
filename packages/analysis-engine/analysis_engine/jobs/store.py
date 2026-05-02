from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from threading import Lock
from typing import Any


@dataclass
class JobRecord:
    job_id: str
    state: str = "queued"
    phase: str = "queued"
    completed: int = 0
    total: int = 1
    started_at: float = field(default_factory=time.time)
    finished_at: float | None = None
    error: str | None = None
    result: dict[str, Any] | None = None

    def status(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "state": self.state,
            "phase": self.phase,
            "completed": self.completed,
            "total": self.total,
            "elapsed_seconds": round((self.finished_at or time.time()) - self.started_at, 2),
            "error": self.error,
        }


class JobStore:
    def __init__(self) -> None:
        self._jobs: dict[str, JobRecord] = {}
        self._lock = Lock()

    def create(self) -> JobRecord:
        job = JobRecord(job_id=str(uuid.uuid4()))
        with self._lock:
            self._jobs[job.job_id] = job
        return job

    def get(self, job_id: str) -> JobRecord:
        with self._lock:
            if job_id not in self._jobs:
                raise KeyError(f"Unknown job_id: {job_id}")
            return self._jobs[job_id]

    def update(self, job_id: str, **changes: Any) -> JobRecord:
        with self._lock:
            job = self._jobs[job_id]
            for key, value in changes.items():
                setattr(job, key, value)
            return job
