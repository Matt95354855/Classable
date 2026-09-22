from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass

from .classifier import EventClassifier
from .config import CollectorConfig, build_source_queries
from .provider import TwscrapeProvider
from .store import EventStore

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class CycleResult:
    scanned: int
    classified: int
    inserted: int
    failed_queries: int


class SocialCollector:
    def __init__(self, config: CollectorConfig) -> None:
        self.config = config
        self.provider = TwscrapeProvider(
            config.accounts_database_path,
            timeout_seconds=config.query_timeout_seconds,
        )
        self.classifier = EventClassifier(config.source_map, config.min_event_score)
        self.store = EventStore(config.database_path)

    @property
    def queries(self) -> list[str]:
        return [*build_source_queries(self.config.sources), *self.config.queries]

    async def collect_once(self) -> CycleResult:
        scanned = classified = inserted = failed_queries = 0
        seen: set[str] = set()

        for query in self.queries:
            if scanned >= self.config.max_posts_per_cycle:
                break
            remaining = self.config.max_posts_per_cycle - scanned
            limit = min(self.config.per_query_limit, remaining)
            try:
                async for post in self.provider.search(query, limit):
                    if post.post_id in seen:
                        continue
                    seen.add(post.post_id)
                    scanned += 1
                    event = self.classifier.classify(post)
                    if event is None:
                        continue
                    classified += 1
                    if self.store.insert(event):
                        inserted += 1
                    if scanned >= self.config.max_posts_per_cycle:
                        break
            except Exception as exc:
                failed_queries += 1
                LOGGER.error("Echec de la requete X %r: %s", query, exc)
                break

            # Intentionally sequential and slow: no account rotation or burst scraping.
            await asyncio.sleep(2)

        return CycleResult(scanned, classified, inserted, failed_queries)

    async def run_forever(self) -> None:
        while True:
            result = await self.collect_once()
            LOGGER.info(
                "Cycle termine: scanned=%s classified=%s inserted=%s failed_queries=%s",
                result.scanned,
                result.classified,
                result.inserted,
                result.failed_queries,
            )
            if result.failed_queries:
                raise RuntimeError(
                    "Collecte suspendue apres une erreur X; intervention manuelle requise"
                )
            await asyncio.sleep(self.config.poll_interval_seconds)
