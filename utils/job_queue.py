#job_queue.py
from __future__ import annotations
from collections import deque
from typing import Deque, List, Optional

class JobQueue:
    def __init__(self):
        self._done: Deque[str] = deque()

    def push_done(self, msg: str) -> None:
        if msg:
            self._done.append(msg)

    def pop_done_messages(self) -> List[str]:
        out: List[str] = []
        while self._done:
            out.append(self._done.popleft())
        return out
