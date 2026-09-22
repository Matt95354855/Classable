from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import Source


@dataclass(frozen=True, slots=True)
class LLMConfig:
    enabled: bool
    endpoint: str
    model: str
    max_queries: int
    timeout_seconds: int


@dataclass(frozen=True, slots=True)
class BrowserConfig:
    profile_path: Path
    headless: bool
    max_pages_per_cycle: int
    max_scrolls_per_page: int
    post_limit_per_page: int
    page_timeout_seconds: int
    scroll_pause_ms: int


@dataclass(frozen=True, slots=True)
class BrowserAgentConfig:
    database_path: Path
    poll_interval_seconds: int
    min_event_score: int
    seed_queries: tuple[str, ...]
    sources: tuple[Source, ...]
    browser: BrowserConfig
    llm: LLMConfig

    @classmethod
    def load(cls, path: str | Path) -> "BrowserAgentConfig":
        config_path = Path(path)
        raw: dict[str, Any] = json.loads(config_path.read_text(encoding="utf-8"))
        root = config_path.parent.parent if config_path.parent.name == "config" else Path.cwd()

        def project_path(value: str) -> Path:
            item = Path(value)
            return item if item.is_absolute() else root / item

        browser_raw = raw.get("browser", {})
        llm_raw = raw.get("llm", {})
        browser = BrowserConfig(
            profile_path=project_path(
                str(browser_raw.get("profile_path", "data/x-browser-profile"))
            ),
            headless=bool(browser_raw.get("headless", False)),
            max_pages_per_cycle=int(browser_raw.get("max_pages_per_cycle", 8)),
            max_scrolls_per_page=int(browser_raw.get("max_scrolls_per_page", 3)),
            post_limit_per_page=int(browser_raw.get("post_limit_per_page", 40)),
            page_timeout_seconds=int(browser_raw.get("page_timeout_seconds", 45)),
            scroll_pause_ms=int(browser_raw.get("scroll_pause_ms", 2000)),
        )
        llm = LLMConfig(
            enabled=bool(llm_raw.get("enabled", True)),
            endpoint=str(llm_raw.get("endpoint", "http://127.0.0.1:11434")),
            model=str(llm_raw.get("model", "qwen3:8b")),
            max_queries=int(llm_raw.get("max_queries", 6)),
            timeout_seconds=int(llm_raw.get("timeout_seconds", 60)),
        )
        poll_interval = int(raw.get("poll_interval_seconds", 300))
        if poll_interval < 120:
            raise ValueError("poll_interval_seconds doit etre superieur ou egal a 120")
        if not 1 <= browser.max_pages_per_cycle <= 12:
            raise ValueError("max_pages_per_cycle doit etre compris entre 1 et 12")
        if not 1 <= browser.max_scrolls_per_page <= 5:
            raise ValueError("max_scrolls_per_page doit etre compris entre 1 et 5")
        if not 5 <= browser.post_limit_per_page <= 100:
            raise ValueError("post_limit_per_page doit etre compris entre 5 et 100")
        if not 1 <= llm.max_queries <= 8:
            raise ValueError("llm.max_queries doit etre compris entre 1 et 8")

        sources = tuple(
            Source(
                username=str(item["username"]).lstrip("@").lower(),
                tier=str(item["tier"]),
                score=int(item["score"]),
            )
            for item in raw.get("sources", [])
        )
        queries = tuple(str(query).strip() for query in raw.get("seed_queries", []) if str(query).strip())
        if not sources or not queries:
            raise ValueError("Des sources et des seed_queries sont obligatoires")

        return cls(
            database_path=project_path(str(raw.get("database_path", "data/x_events.db"))),
            poll_interval_seconds=poll_interval,
            min_event_score=int(raw.get("min_event_score", 7)),
            seed_queries=queries,
            sources=sources,
            browser=browser,
            llm=llm,
        )

    @property
    def source_map(self) -> dict[str, Source]:
        return {source.username: source for source in self.sources}

