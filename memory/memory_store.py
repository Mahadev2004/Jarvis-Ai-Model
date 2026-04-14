# memory/memory_store.py

from __future__ import annotations

import json
import threading
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Optional


@dataclass
class MemoryItem:
    text: str
    category: str = "note"      # e.g. "fact", "preference", "habit", "skill"
    source: str = "manual"      # e.g. "manual", "auto", "background_learner"
    tags: List[str] | None = None
    ts: float = 0.0             # unix timestamp

    def to_dict(self) -> dict:
        d = asdict(self)
        if d["tags"] is None:
            d["tags"] = []
        if not d["ts"]:
            d["ts"] = time.time()
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "MemoryItem":
        return cls(
            text=d.get("text", ""),
            category=d.get("category", "note"),
            source=d.get("source", "manual"),
            tags=d.get("tags") or [],
            ts=float(d.get("ts") or time.time()),
        )


class MemoryStore:
    """
    Simple JSON-based memory store.
    """

    def __init__(self, path: Path):
        self._path = path
        self._lock = threading.Lock()
        self._items: List[MemoryItem] = []
        self._load()

    def _load(self) -> None:
        if not self._path.exists():
            self._items = []
            return
        try:
            raw = self._path.read_text(encoding="utf-8")
            data = json.loads(raw or "[]")
            self._items = [MemoryItem.from_dict(x) for x in data]
        except Exception as e:
            print("[MemoryStore] Failed to load memory:", e)
            self._items = []

    def _save(self) -> None:
        try:
            data = [m.to_dict() for m in self._items]
            self._path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as e:
            print("[MemoryStore] Failed to save memory:", e)

    def add(self, text: str, category: str = "note", source: str = "manual", tags: Optional[List[str]] = None) -> MemoryItem:
        with self._lock:
            item = MemoryItem(
                text=text.strip(),
                category=category,
                source=source,
                tags=tags or [],
                ts=time.time(),
            )
            self._items.append(item)
            self._save()
        return item

    def all_items(self) -> List[MemoryItem]:
        with self._lock:
            return list(self._items)

    def last_n(self, n: int = 20) -> List[MemoryItem]:
        with self._lock:
            return self._items[-n:]


_store: Optional[MemoryStore] = None


def get_memory_store() -> MemoryStore:
    global _store
    if _store is None:
        base_dir = Path(__file__).resolve().parent
        mem_path = base_dir / "memory_data.json"
        _store = MemoryStore(mem_path)
        print(f"[MemoryStore] Using memory file at: {mem_path}")
    return _store
