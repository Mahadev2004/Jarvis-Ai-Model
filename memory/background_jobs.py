# memory/background_jobs.py
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Callable, Dict, Optional


@dataclass
class JobResult:
    job_id: str
    title: str
    status: str  # "queued" | "running" | "done" | "error"
    created_ts: float = field(default_factory=lambda: time.time())
    done_ts: float = 0.0
    message: str = ""
    output_text: str = ""


class BackgroundJobManager:
    """
    Minimal background job runner (single-thread worker).
    Keeps results in memory. (You can later persist to JSON if you want.)
    """
    def __init__(self):
        self._lock = threading.Lock()
        self._jobs: Dict[str, JobResult] = {}
        self._queue: list[tuple[str, Callable[[], str]]] = []
        self._worker = threading.Thread(target=self._loop, daemon=True)
        self._started = False

    def start(self) -> None:
        if not self._started:
            self._started = True
            self._worker.start()

    def submit(self, job_id: str, title: str, fn: Callable[[], str]) -> str:
        with self._lock:
            self._jobs[job_id] = JobResult(job_id=job_id, title=title, status="queued")
            self._queue.append((job_id, fn))
        return job_id

    def get(self, job_id: str) -> Optional[JobResult]:
        with self._lock:
            return self._jobs.get(job_id)

    def pop_done_messages(self) -> list[JobResult]:
        """
        Returns completed jobs that haven't been 'announced' yet.
        We'll mark them by clearing message after reading.
        """
        out: list[JobResult] = []
        with self._lock:
            for jid, jr in list(self._jobs.items()):
                if jr.status in ("done", "error") and jr.message:
                    out.append(jr)
                    # mark as announced
                    jr.message = ""
        return out

    def _loop(self) -> None:
        while True:
            job: Optional[tuple[str, Callable[[], str]]] = None
            with self._lock:
                if self._queue:
                    job = self._queue.pop(0)

            if not job:
                time.sleep(0.15)
                continue

            job_id, fn = job
            try:
                with self._lock:
                    self._jobs[job_id].status = "running"
                result_text = fn()
                with self._lock:
                    jr = self._jobs[job_id]
                    jr.status = "done"
                    jr.done_ts = time.time()
                    jr.output_text = result_text
                    jr.message = f"✅ '{jr.title}' complete."
            except Exception as e:
                with self._lock:
                    jr = self._jobs[job_id]
                    jr.status = "error"
                    jr.done_ts = time.time()
                    jr.output_text = ""
                    jr.message = f"❌ '{jr.title}' failed: {e}"
