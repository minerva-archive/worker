import json
from typing import Any
from urllib.parse import unquote

from minerva.constants import CACHE_FILE


class JobCache:
    _instance: Any | None = None

    def __new__(cls) -> Any:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance

    def _init(self) -> None:
        self._data: dict[str, dict[str, Any]] = {}
        if CACHE_FILE.exists():
            try:
                self._data = json.loads(CACHE_FILE.read_text(encoding="utf8"))
            except Exception:
                self._data = {}

    def _save(self) -> None:
        CACHE_FILE.write_text(json.dumps(self._data), encoding="utf8")

    def list(self) -> list[dict[str, Any]]:
        return list(self._data.values())

    def get(self, job: dict[str, Any]) -> dict[str, Any]:
        key = unquote(job["url"])
        return self._data.get(key) or {}

    def set(self, job: dict[str, Any]) -> None:
        key = unquote(job["url"])
        self._data[key] = {**job, "is_cached": True}
        self._save()

    def remove(self, job: dict[str, Any]) -> None:
        key = unquote(job["url"])
        if key in self._data:
            del self._data[key]
            self._save()


job_cache = JobCache()


__all__ = ["job_cache"]
