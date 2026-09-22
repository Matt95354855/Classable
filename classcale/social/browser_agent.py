from __future__ import annotations

import asyncio
from dataclasses import dataclass
import logging

from .agent_config import BrowserAgentConfig
from .classifier import EventClassifier
from .llm_planner import OllamaPlanner, SearchPlan
from .store import EventStore
from .x_browser import XBrowser

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class AgentCycleResult:
    plan: SearchPlan
    scanned: int
    classified: int
    inserted: int


class XResearchAgent:
    def __init__(self, config: BrowserAgentConfig) -> None:
        self.config = config
        self.store = EventStore(config.database_path)
        self.browser = XBrowser(config.browser)
        self.classifier = EventClassifier(config.source_map, config.min_event_score)
        self.planner = OllamaPlanner(
            config.llm,
            config.seed_queries,
            tuple(source.username for source in config.sources),
        )

    async def login(self) -> None:
        await self.browser.interactive_login()

    async def make_plan(self) -> SearchPlan:
        return await self.planner.plan(self.store.latest(20))

    async def collect_once(self) -> AgentCycleResult:
        plan = await self.make_plan()
        scanned = classified = inserted = 0
        async for post in self.browser.collect(plan):
            scanned += 1
            event = self.classifier.classify(post)
            if event is None:
                continue
            classified += 1
            if self.store.insert(event):
                inserted += 1
        return AgentCycleResult(plan, scanned, classified, inserted)

    async def run_forever(self) -> None:
        while True:
            result = await self.collect_once()
            LOGGER.info(
                "Agent X: scanned=%s classified=%s inserted=%s reason=%s",
                result.scanned,
                result.classified,
                result.inserted,
                result.plan.reason,
            )
            await asyncio.sleep(self.config.poll_interval_seconds)

