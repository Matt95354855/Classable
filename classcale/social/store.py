from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Iterable

from .models import CryptoEvent


class EventStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA busy_timeout=5000")
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS events (
                    post_id TEXT PRIMARY KEY,
                    content_hash TEXT NOT NULL UNIQUE,
                    created_at TEXT NOT NULL,
                    collected_at TEXT NOT NULL,
                    author TEXT NOT NULL,
                    source_tier TEXT NOT NULL,
                    score INTEGER NOT NULL,
                    severity INTEGER NOT NULL,
                    assets_json TEXT NOT NULL,
                    event_types_json TEXT NOT NULL,
                    payload_json TEXT NOT NULL
                )
                """
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_events_created_at ON events(created_at DESC)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_events_score ON events(score DESC)"
            )

    def insert(self, event: CryptoEvent) -> bool:
        payload = json.dumps(event.as_dict(), ensure_ascii=False, separators=(",", ":"))
        try:
            with self._connect() as connection:
                cursor = connection.execute(
                    """
                    INSERT OR IGNORE INTO events (
                        post_id, content_hash, created_at, collected_at, author,
                        source_tier, score, severity, assets_json,
                        event_types_json, payload_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        event.post_id,
                        event.content_hash,
                        event.created_at,
                        event.collected_at,
                        event.author,
                        event.source_tier,
                        event.score,
                        event.severity,
                        json.dumps(event.assets),
                        json.dumps(event.event_types),
                        payload,
                    ),
                )
                return cursor.rowcount == 1
        except sqlite3.IntegrityError:
            return False

    def insert_many(self, events: Iterable[CryptoEvent]) -> int:
        return sum(1 for event in events if self.insert(event))

    def latest(self, limit: int = 100) -> list[dict[str, object]]:
        safe_limit = max(1, min(limit, 10_000))
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT payload_json FROM events ORDER BY created_at DESC LIMIT ?",
                (safe_limit,),
            ).fetchall()
        return [json.loads(row["payload_json"]) for row in rows]

    def count(self) -> int:
        with self._connect() as connection:
            row = connection.execute("SELECT COUNT(*) AS total FROM events").fetchone()
        return int(row["total"])

