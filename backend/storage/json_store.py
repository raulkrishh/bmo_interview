import json
import threading
import uuid
from pathlib import Path
from typing import List, Optional

from models import TaskRecord

_LOCK = threading.Lock()


class JsonTaskStore:
    """Simple JSON-file-backed persistence for task records.

    This is deliberately lightweight - it satisfies the "basic persistence"
    requirement with zero external dependencies and is trivial to inspect
    (just open the file). It is not built for high-concurrency writes; a
    production deployment would swap this for SQLite/Postgres behind the
    same add()/list_all()/get() interface.
    """

    def __init__(self, path: str = "data/tasks.json"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text("[]", encoding="utf-8")

    def add(self, record: TaskRecord) -> TaskRecord:
        record.id = str(uuid.uuid4())
        with _LOCK:
            records = self._read()
            records.append(record.model_dump())
            self._write(records)
        return record

    def list_all(self) -> List[TaskRecord]:
        with _LOCK:
            records = self._read()
        records.sort(key=lambda r: r["timestamp"], reverse=True)
        return [TaskRecord(**r) for r in records]

    def get(self, task_id: str) -> Optional[TaskRecord]:
        with _LOCK:
            records = self._read()
        for r in records:
            if r["id"] == task_id:
                return TaskRecord(**r)
        return None

    def _read(self) -> list:
        try:
            return json.loads(self.path.read_text(encoding="utf-8") or "[]")
        except json.JSONDecodeError:
            return []

    def _write(self, records: list) -> None:
        self.path.write_text(json.dumps(records, indent=2), encoding="utf-8")
