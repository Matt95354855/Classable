from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .models import RawPost


class TwscrapeProvider:
    """Thin, deliberately conservative wrapper around one authorized X account."""

    def __init__(
        self,
        accounts_database_path: str | Path,
        timeout_seconds: int = 45,
    ) -> None:
        from twscrape import API

        path = Path(accounts_database_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.api = API(
            str(path),
            raise_when_no_account=True,
            wait_timeout=10,
            wait_interval=1,
        )
        self.timeout_seconds = timeout_seconds

    async def add_account_cookies(self, label: str, cookies: str) -> None:
        if "auth_token=" not in cookies or "ct0=" not in cookies:
            raise ValueError("Les cookies doivent contenir auth_token et ct0")
        await self.api.pool.add_account_cookies(label, cookies)

    async def search(self, query: str, limit: int) -> AsyncIterator[RawPost]:
        async with asyncio.timeout(self.timeout_seconds):
            async for tweet in self.api.search(query, limit=limit):
                post = self._normalize(tweet, query)
                if post is not None:
                    yield post

    @staticmethod
    def _normalize(tweet: Any, query: str) -> RawPost | None:
        user = getattr(tweet, "user", None)
        author = str(getattr(user, "username", "")).lstrip("@")
        text = str(getattr(tweet, "rawContent", "") or "")
        post_id = str(getattr(tweet, "id", "") or "")
        if not author or not text or not post_id:
            return None

        created = getattr(tweet, "date", None)
        if isinstance(created, datetime):
            if created.tzinfo is None:
                created = created.replace(tzinfo=UTC)
            created_at = created.astimezone(UTC).isoformat()
        else:
            created_at = str(created or "")

        url = str(getattr(tweet, "url", "") or f"https://x.com/{author}/status/{post_id}")
        return RawPost(
            post_id=post_id,
            url=url,
            author=author,
            text=text,
            created_at=created_at,
            collected_at=datetime.now(UTC).isoformat(),
            language=getattr(tweet, "lang", None),
            verified=bool(
                getattr(user, "verified", False) or getattr(user, "blue", False)
            ),
            reply_count=int(getattr(tweet, "replyCount", 0) or 0),
            repost_count=int(getattr(tweet, "retweetCount", 0) or 0),
            like_count=int(getattr(tweet, "likeCount", 0) or 0),
            view_count=int(getattr(tweet, "viewCount", 0) or 0),
            query=query,
        )

