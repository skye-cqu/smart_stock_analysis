from __future__ import annotations

import hashlib
import json
import logging
import sqlite3
import time
from pathlib import Path

from src.config import settings

logger = logging.getLogger(__name__)


class CacheManager:
    def __init__(self, db_path: str | None = None, ttl_minutes: int | None = None):
        self.db_path = db_path or settings.data.sqlite_db_path
        self.ttl_seconds = (
            ttl_minutes if ttl_minutes is not None else settings.data.cache_ttl_minutes
        ) * 60
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    expires_at REAL NOT NULL
                )
            """)

    def _make_key(self, namespace: str, **kwargs) -> str:
        raw = f"{namespace}:{json.dumps(kwargs, sort_keys=True)}"
        return hashlib.md5(raw.encode()).hexdigest()

    def get(self, namespace: str, **kwargs) -> dict | list | None:
        key = self._make_key(namespace, **kwargs)
        now = time.time()
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT value, expires_at FROM cache WHERE key = ?", (key,)
            ).fetchone()
            if row is None:
                return None
            value, expires_at = row
            if now > expires_at:
                return None
            return json.loads(value)

    def set(self, namespace: str, value: dict | list, **kwargs) -> None:
        key = self._make_key(namespace, **kwargs)
        now = time.time()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO cache (key, value, created_at, expires_at) VALUES (?, ?, ?, ?)",
                (
                    key,
                    json.dumps(value, ensure_ascii=False, default=str),
                    now,
                    now + self.ttl_seconds,
                ),
            )

    def invalidate(self, namespace: str, **kwargs) -> None:
        key = self._make_key(namespace, **kwargs)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM cache WHERE key = ?", (key,))

    def clear_expired(self) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM cache WHERE expires_at < ?", (time.time(),))
            return cursor.rowcount
