from __future__ import annotations

import json
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

import requests


def human_dt(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S UTC")


@dataclass
class JobStatus:
    job_id: str
    progress: List[Dict[str, Any]] = field(default_factory=list)
    done: bool = False
    result: Optional[Dict[str, Any]] = None


class JobManager:
    """
    Tiny in-process job runner so Dash can show live progress.
    """

    def __init__(self):
        self._jobs: Dict[str, JobStatus] = {}
        self._lock = threading.Lock()

    def create_job(self) -> str:
        job_id = uuid.uuid4().hex[:10]
        with self._lock:
            self._jobs[job_id] = JobStatus(job_id=job_id, progress=[])
        return job_id

    def update(self, job_id: str, text: str, done: bool = False, kind: str = "info"):
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return
            job.progress.append({"text": text, "done": done, "kind": kind})

    def set_result(self, job_id: str, result: Dict[str, Any]):
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return
            job.result = result
            job.done = True

    def set_error(self, job_id: str, text: str):
        self.update(job_id, text, done=False, kind="error")
        with self._lock:
            job = self._jobs.get(job_id)
            if job:
                job.done = True

    def get(self, job_id: str) -> Optional[JobStatus]:
        with self._lock:
            return self._jobs.get(job_id)

    def run(self, job_id: str, fn: Callable[[], Dict[str, Any]]):
        def _target():
            try:
                res = fn()
                self.set_result(job_id, res)
            except Exception as e:
                self.set_error(job_id, f"Error: {e}")

        t = threading.Thread(target=_target, daemon=True)
        t.start()


def send_slack(webhook_url: str, text: str) -> bool:
    try:
        resp = requests.post(webhook_url, json={"text": text}, timeout=5)
        return 200 <= resp.status_code < 300
    except Exception:
        return False
