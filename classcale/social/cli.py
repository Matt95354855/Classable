from __future__ import annotations

import argparse
import asyncio
from dataclasses import asdict
import json
import logging
from pathlib import Path

from .collector import SocialCollector
from .config import CollectorConfig
from .provider import TwscrapeProvider
from .store import EventStore


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="classcale-social")
    parser.add_argument(
        "--config",
        default="config/x-collector.example.json",
        help="Chemin du fichier JSON de configuration",
    )
    parser.add_argument("--log-level", default="INFO")
    commands = parser.add_subparsers(dest="command", required=True)

    setup = commands.add_parser("setup-account", help="Importer les cookies d'un compte X")
    setup.add_argument("--label", default="classcale_operator")
    setup.add_argument("--cookies-file", required=True)

    commands.add_parser("once", help="Executer un cycle de collecte")
    commands.add_parser("run", help="Executer la collecte en continu")

    export = commands.add_parser("export", help="Exporter les derniers evenements en JSONL")
    export.add_argument("--limit", type=int, default=100)

    commands.add_parser("stats", help="Afficher le nombre d'evenements conserves")
    return parser


async def _run(args: argparse.Namespace) -> int:
    config = CollectorConfig.load(args.config)
    if args.command == "setup-account":
        cookies = Path(args.cookies_file).read_text(encoding="utf-8").strip()
        provider = TwscrapeProvider(
            config.accounts_database_path,
            timeout_seconds=config.query_timeout_seconds,
        )
        await provider.add_account_cookies(args.label, cookies)
        print("Compte X importe localement. Le fichier de cookies peut maintenant etre supprime.")
        return 0

    if args.command == "export":
        for event in EventStore(config.database_path).latest(args.limit):
            print(json.dumps(event, ensure_ascii=False))
        return 0

    if args.command == "stats":
        print(json.dumps({"events": EventStore(config.database_path).count()}))
        return 0

    collector = SocialCollector(config)
    if args.command == "once":
        result = await collector.collect_once()
        print(json.dumps(asdict(result)))
        return 0 if result.failed_queries == 0 else 2

    await collector.run_forever()
    return 0


def main() -> None:
    args = _parser().parse_args()
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    raise SystemExit(asyncio.run(_run(args)))


if __name__ == "__main__":
    main()
