from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path
import re
from typing import Any
from urllib.parse import quote

from .agent_config import BrowserConfig
from .llm_planner import SearchPlan
from .models import RawPost

STATUS_URL = re.compile(r"https://x\.com/([^/]+)/status/(\d+)")


class AuthenticationRequired(RuntimeError):
    pass


def parse_status_url(url: str) -> tuple[str, str] | None:
    match = STATUS_URL.search(url)
    return (match.group(1), match.group(2)) if match else None


class XBrowser:
    def __init__(self, config: BrowserConfig) -> None:
        self.config = config

    async def interactive_login(self) -> None:
        async with self._context(headless=False) as context:
            page = context.pages[0] if context.pages else await context.new_page()
            await page.goto("https://x.com/home", wait_until="domcontentloaded")
            print("Connectez-vous manuellement dans Chromium, puis revenez ici.")
            await asyncio.to_thread(input, "Appuyez sur Entree une fois la connexion terminee: ")
            if self._looks_logged_out(page.url):
                raise AuthenticationRequired("La session X ne semble pas connectee")

    async def collect(self, plan: SearchPlan) -> AsyncIterator[RawPost]:
        targets = [*plan.queries, *(f"from:{account} -filter:replies" for account in plan.accounts)]
        targets = targets[: self.config.max_pages_per_cycle]
        seen: set[str] = set()
        async with self._context(headless=self.config.headless) as context:
            page = context.pages[0] if context.pages else await context.new_page()
            page.set_default_timeout(self.config.page_timeout_seconds * 1000)
            for query in targets:
                async for post in self._search_page(page, query):
                    if post.post_id in seen:
                        continue
                    seen.add(post.post_id)
                    yield post
                await asyncio.sleep(self.config.scroll_pause_ms / 1000)

    async def _search_page(self, page: Any, query: str) -> AsyncIterator[RawPost]:
        url = f"https://x.com/search?q={quote(query)}&src=typed_query&f=live"
        await page.goto(url, wait_until="domcontentloaded")
        if self._looks_logged_out(page.url):
            raise AuthenticationRequired("Connexion X requise; executez la commande login")

        tweets = page.get_by_test_id("tweet")
        try:
            await tweets.first.wait_for(timeout=self.config.page_timeout_seconds * 1000)
        except Exception as exc:
            raise RuntimeError("Aucune publication visible ou page X bloquee") from exc

        emitted: set[str] = set()
        for _ in range(self.config.max_scrolls_per_page):
            count = min(await tweets.count(), self.config.post_limit_per_page)
            for index in range(count):
                data = await tweets.nth(index).evaluate(
                    """element => {
                      const textNode = element.querySelector('[data-testid="tweetText"]');
                      const timeNode = element.querySelector('time');
                      const statusLinks = [...element.querySelectorAll('a[href*="/status/"]')];
                      const statusUrl = statusLinks.map(node => node.href).find(Boolean) || '';
                      return {
                        text: textNode ? textNode.innerText : '',
                        lang: textNode ? textNode.getAttribute('lang') : null,
                        createdAt: timeNode ? timeNode.getAttribute('datetime') : '',
                        statusUrl,
                        verified: Boolean(element.querySelector('[data-testid="icon-verified"]'))
                      };
                    }"""
                )
                post = self._normalize(data, query)
                if post is None or post.post_id in emitted:
                    continue
                emitted.add(post.post_id)
                yield post
                if len(emitted) >= self.config.post_limit_per_page:
                    return
            await page.mouse.wheel(0, 1800)
            await asyncio.sleep(self.config.scroll_pause_ms / 1000)

    @staticmethod
    def _normalize(data: dict[str, Any], query: str) -> RawPost | None:
        parsed = parse_status_url(str(data.get("statusUrl", "")))
        text = " ".join(str(data.get("text", "")).split())
        if parsed is None or not text:
            return None
        author, post_id = parsed
        return RawPost(
            post_id=post_id,
            url=str(data["statusUrl"]),
            author=author,
            text=text,
            created_at=str(data.get("createdAt", "")),
            collected_at=datetime.now(UTC).isoformat(),
            language=data.get("lang"),
            verified=bool(data.get("verified", False)),
            query=query,
        )

    @asynccontextmanager
    async def _context(self, headless: bool) -> AsyncIterator[Any]:
        from playwright.async_api import async_playwright

        self.config.profile_path.mkdir(parents=True, exist_ok=True)
        async with async_playwright() as playwright:
            context = await playwright.chromium.launch_persistent_context(
                user_data_dir=str(self.config.profile_path),
                headless=headless,
                viewport={"width": 1440, "height": 1000},
                locale="fr-FR",
            )
            try:
                yield context
            finally:
                await context.close()

    @staticmethod
    def _looks_logged_out(url: str) -> bool:
        return "/i/flow/login" in url or url.rstrip("/").endswith("/login")

