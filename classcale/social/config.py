from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class Source:
    username: str
    tier: str
    score: int


@dataclass(frozen=True, slots=True)
class CollectorConfig:
    database_path: Path
    accounts_database_path: Path
    poll_interval_seconds: int
    per_query_limit: int
    max_posts_per_cycle: int
    min_event_score: int
    query_timeout_seconds: int
    queries: tuple[str, ...]
    sources: tuple[Source, ...]

    @classmethod
    def load(cls, path: str | Path) -> "CollectorConfig":
        config_path = Path(path)
        raw: dict[str, Any] = json.loads(config_path.read_text(encoding="utf-8"))
        root = config_path.parent.parent if config_path.parent.name == "config" else Path.cwd()

        def project_path(value: str) -> Path:
            item = Path(value)
            return item if item.is_absolute() else root / item

        poll = int(raw.get("poll_interval_seconds", 180))
        per_query = int(raw.get("per_query_limit", 50))
        maximum = int(raw.get("max_posts_per_cycle", 500))
        timeout = int(raw.get("query_timeout_seconds", 45))
        minimum_score = int(raw.get("min_event_score", 7))

        if poll < 60:
            raise ValueError("poll_interval_seconds doit etre superieur ou egal a 60")
        if not 1 <= per_query <= 200:
            raise ValueError("per_query_limit doit etre compris entre 1 et 200")
        if not 1 <= maximum <= 2_000:
            raise ValueError("max_posts_per_cycle doit etre compris entre 1 et 2000")
        if not 10 <= timeout <= 180:
            raise ValueError("query_timeout_seconds doit etre compris entre 10 et 180")

        sources = tuple(
            Source(
                username=str(item["username"]).lstrip("@").lower(),
                tier=str(item["tier"]),
                score=int(item["score"]),
            )
            for item in raw.get("sources", [])
        )
        if not sources:
            raise ValueError("Au moins une source X doit etre configuree")

        return cls(
            database_path=project_path(str(raw.get("database_path", "data/x_events.db"))),
            accounts_database_path=project_path(
                str(raw.get("accounts_database_path", "data/twscrape_accounts.db"))
            ),
            poll_interval_seconds=poll,
            per_query_limit=per_query,
            max_posts_per_cycle=maximum,
            min_event_score=minimum_score,
            query_timeout_seconds=timeout,
            queries=tuple(str(query) for query in raw.get("queries", [])),
            sources=sources,
        )

    @property
    def source_map(self) -> dict[str, Source]:
        return {source.username: source for source in self.sources}


def build_source_queries(sources: tuple[Source, ...], batch_size: int = 8) -> list[str]:
    usernames = [source.username for source in sources]
    queries: list[str] = []
    for offset in range(0, len(usernames), batch_size):
        batch = usernames[offset : offset + batch_size]
        clauses = " OR ".join(f"from:{username}" for username in batch)
        queries.append(f"({clauses}) -filter:replies")
    return queries

