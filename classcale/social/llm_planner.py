from __future__ import annotations

import asyncio
from dataclasses import dataclass
import json
import logging
import re
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

from .agent_config import LLMConfig

LOGGER = logging.getLogger(__name__)

CRYPTO_TERMS = re.compile(
    r"\b(?:bitcoin|btc|ethereum|eth|solana|sol|xrp|bnb|crypto|blockchain|stablecoin|defi|etf)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True, slots=True)
class SearchPlan:
    queries: tuple[str, ...]
    accounts: tuple[str, ...]
    reason: str
    generated_by_llm: bool


class OllamaPlanner:
    def __init__(
        self,
        config: LLMConfig,
        seed_queries: tuple[str, ...],
        allowed_accounts: tuple[str, ...],
    ) -> None:
        self.config = config
        self.seed_queries = seed_queries
        self.allowed_accounts = allowed_accounts

    async def plan(self, recent_events: list[dict[str, object]]) -> SearchPlan:
        if not self.config.enabled:
            return self.fallback("LLM desactive")
        try:
            raw = await asyncio.to_thread(self._request, recent_events)
            return self.validate(raw)
        except (OSError, URLError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
            LOGGER.warning("Ollama indisponible, plan deterministe utilise: %s", exc)
            return self.fallback("Ollama indisponible")

    def fallback(self, reason: str) -> SearchPlan:
        return SearchPlan(
            queries=self.seed_queries[: self.config.max_queries],
            accounts=self.allowed_accounts[: self.config.max_queries],
            reason=reason,
            generated_by_llm=False,
        )

    def validate(self, raw: dict[str, Any]) -> SearchPlan:
        queries: list[str] = []
        for candidate in raw.get("queries", []):
            query = " ".join(str(candidate).split())[:180]
            if not query or "javascript:" in query.lower() or "http://" in query.lower() or "https://" in query.lower():
                continue
            if not CRYPTO_TERMS.search(query):
                continue
            if query not in queries:
                queries.append(query)
            if len(queries) >= self.config.max_queries:
                break

        allowed = set(self.allowed_accounts)
        accounts: list[str] = []
        for candidate in raw.get("accounts", []):
            account = str(candidate).lstrip("@").lower()
            if account in allowed and account not in accounts:
                accounts.append(account)
            if len(accounts) >= self.config.max_queries:
                break

        if not queries:
            queries = list(self.seed_queries[: self.config.max_queries])
        if not accounts:
            accounts = list(self.allowed_accounts[: self.config.max_queries])
        return SearchPlan(
            queries=tuple(queries),
            accounts=tuple(accounts),
            reason=str(raw.get("reason", "Plan LLM"))[:500],
            generated_by_llm=True,
        )

    def _request(self, recent_events: list[dict[str, object]]) -> dict[str, Any]:
        schema = {
            "type": "object",
            "properties": {
                "queries": {"type": "array", "items": {"type": "string"}},
                "accounts": {"type": "array", "items": {"type": "string"}},
                "reason": {"type": "string"},
            },
            "required": ["queries", "accounts", "reason"],
        }
        context = [
            {
                "author": event.get("author"),
                "event_types": event.get("event_types"),
                "assets": event.get("assets"),
                "text": str(event.get("text", ""))[:240],
            }
            for event in recent_events[:20]
        ]
        prompt = (
            "Tu pilotes un analyste crypto qui consulte uniquement les pages visibles de X. "
            "Propose des recherches courtes visant des evenements factuels et recents: hacks, "
            "pannes, regulation, ETF, listings, mises a jour de reseau et insolvabilite. "
            "Evite prix, rumeurs, influenceurs, giveaways et predictions. Choisis les comptes "
            "uniquement dans la liste autorisee.\n"
            f"Recherches de base: {json.dumps(self.seed_queries)}\n"
            f"Comptes autorises: {json.dumps(self.allowed_accounts)}\n"
            f"Evenements recents: {json.dumps(context, ensure_ascii=False)}"
        )
        payload = json.dumps(
            {
                "model": self.config.model,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
                "format": schema,
                "options": {"temperature": 0},
            }
        ).encode("utf-8")
        endpoint = self.config.endpoint.rstrip("/") + "/api/chat"
        request = Request(endpoint, data=payload, headers={"Content-Type": "application/json"})
        with urlopen(request, timeout=self.config.timeout_seconds) as response:
            body = json.loads(response.read().decode("utf-8"))
        content = body.get("message", {}).get("content", "")
        return json.loads(content)

