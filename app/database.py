from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse


def _db_path(database_url: str) -> Path:
    parsed = urlparse(database_url)
    if parsed.scheme != "sqlite":
        raise ValueError("Only sqlite database URLs are supported")
    if parsed.path.startswith("/") and parsed.netloc:
        return Path(f"/{parsed.netloc}{parsed.path}")
    return Path(parsed.path.lstrip("/"))


class HistoryRepository:
    def __init__(self, database_url: str) -> None:
        self.path = _db_path(database_url)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    @contextmanager
    def _connect(self):
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _initialize(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS analysis_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    timeframe TEXT NOT NULL,
                    mode TEXT NOT NULL,
                    signal TEXT NOT NULL,
                    trend TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )

    def insert(self, symbol: str, timeframe: str, mode: str, signal: str, trend: str, confidence: float) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO analysis_history (symbol, timeframe, mode, signal, trend, confidence, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (symbol, timeframe, mode, signal, trend, confidence, datetime.utcnow().isoformat()),
            )

    def latest(self, limit: int = 20) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, symbol, timeframe, mode, signal, trend, confidence, created_at
                FROM analysis_history
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]
