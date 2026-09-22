from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

from .config import Source
from .models import CryptoEvent, RawPost


@dataclass(frozen=True, slots=True)
class EventRule:
    name: str
    severity: int
    pattern: re.Pattern[str]


def _words(*values: str) -> re.Pattern[str]:
    escaped = "|".join(re.escape(value) for value in values)
    return re.compile(r"(?:\b|\$)(?:" + escaped + r")(?:\b|\$)", re.IGNORECASE)


def _asset(names: tuple[str, ...], tickers: tuple[str, ...]) -> re.Pattern[str]:
    names_pattern = "|".join(re.escape(value) for value in names)
    tickers_pattern = "|".join(re.escape(value) for value in tickers)
    return re.compile(
        rf"(?:(?i:\b(?:{names_pattern})\b)|(?:\$?(?:{tickers_pattern})\b))"
    )


ASSET_RULES: dict[str, re.Pattern[str]] = {
    "BTC": _asset(("bitcoin", "btc", "xbt"), ("BTC", "XBT")),
    "ETH": _asset(("ethereum", "ether", "eth"), ("ETH",)),
    "SOL": _asset(("solana",), ("SOL",)),
    "XRP": _asset(("ripple", "xrp"), ("XRP",)),
    "BNB": _asset(("bnb", "bnbchain", "binance chain"), ("BNB",)),
    "ADA": _asset(("cardano",), ("ADA",)),
    "DOGE": _asset(("dogecoin", "doge"), ("DOGE",)),
}

EVENT_RULES: tuple[EventRule, ...] = (
    EventRule(
        "security_incident",
        5,
        _words("hack", "hacked", "exploit", "exploited", "breach", "stolen", "drain", "drained", "vulnerability"),
    ),
    EventRule(
        "regulation",
        4,
        _words("regulation", "regulator", "lawsuit", "court", "settlement", "approved", "approval", "ban", "sanction", "enforcement"),
    ),
    EventRule(
        "listing",
        3,
        _words("listing", "listed", "delisting", "delisted", "launchpool", "spot market"),
    ),
    EventRule(
        "network_change",
        3,
        _words("upgrade", "hardfork", "hard fork", "mainnet", "testnet", "validator", "governance vote", "proposal"),
    ),
    EventRule(
        "outage",
        4,
        _words("outage", "downtime", "halted", "paused", "suspended", "degraded", "incident"),
    ),
    EventRule(
        "market_structure",
        4,
        _words("etf", "custody", "reserve", "proof of reserves", "institutional", "liquidation", "bankruptcy", "insolvency"),
    ),
    EventRule(
        "token_supply",
        3,
        _words("token unlock", "unlock", "burn", "mint", "airdrop", "issuance", "supply"),
    ),
    EventRule(
        "macro",
        3,
        _words("inflation", "interest rate", "rate cut", "rate hike", "fomc", "cpi", "employment", "recession"),
    ),
    EventRule(
        "partnership",
        2,
        _words("partnership", "partnered", "integration", "integrates", "adoption", "launches"),
    ),
)

PROMOTION_PATTERN = _words(
    "guaranteed",
    "100x",
    "1000x",
    "giveaway",
    "dm me",
    "free money",
    "risk free",
    "pump",
    "signals vip",
)


class EventClassifier:
    def __init__(self, sources: dict[str, Source], min_score: int = 7) -> None:
        self.sources = sources
        self.min_score = min_score

    def classify(self, post: RawPost) -> CryptoEvent | None:
        text = " ".join(post.text.split())
        if not text or text.lower().startswith("rt @"):
            return None

        source = self.sources.get(post.author.lower())
        source_tier = source.tier if source else "discovered"
        source_score = source.score if source else (1 if post.verified else 0)

        matches = tuple(rule for rule in EVENT_RULES if rule.pattern.search(text))
        if not matches:
            return None

        assets = tuple(symbol for symbol, pattern in ASSET_RULES.items() if pattern.search(text))
        if not assets and not re.search(r"\b(?:crypto|blockchain|digital asset)s?\b", text, re.I):
            return None

        severity = max(rule.severity for rule in matches)
        score = source_score + severity
        if post.verified:
            score += 1
        if PROMOTION_PATTERN.search(text):
            score -= 5
        if source is None and not post.verified:
            score -= 2

        if score < self.min_score:
            return None

        normalized = text.lower()
        content_hash = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
        return CryptoEvent(
            post_id=post.post_id,
            url=post.url,
            author=post.author,
            text=text,
            created_at=post.created_at,
            collected_at=post.collected_at,
            language=post.language,
            verified=post.verified,
            source_tier=source_tier,
            source_score=source_score,
            event_types=tuple(rule.name for rule in matches),
            assets=assets,
            score=score,
            severity=severity,
            content_hash=content_hash,
            metrics={
                "replies": post.reply_count,
                "reposts": post.repost_count,
                "likes": post.like_count,
                "views": post.view_count,
            },
            metadata={"query": post.query},
        )
