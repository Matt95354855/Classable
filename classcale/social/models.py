from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class RawPost:
    post_id: str
    url: str
    author: str
    text: str
    created_at: str
    collected_at: str
    language: str | None = None
    verified: bool = False
    reply_count: int = 0
    repost_count: int = 0
    like_count: int = 0
    view_count: int = 0
    query: str = ""


@dataclass(frozen=True, slots=True)
class CryptoEvent:
    post_id: str
    url: str
    author: str
    text: str
    created_at: str
    collected_at: str
    language: str | None
    verified: bool
    source_tier: str
    source_score: int
    event_types: tuple[str, ...]
    assets: tuple[str, ...]
    score: int
    severity: int
    content_hash: str
    metrics: dict[str, int] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["event_types"] = list(self.event_types)
        data["assets"] = list(self.assets)
        return data

