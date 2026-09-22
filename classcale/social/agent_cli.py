from __future__ import annotations

import argparse
import asyncio
from dataclasses import asdict
import json
import logging

from .agent_config import BrowserAgentConfig
from .browser_agent import XResearchAgent


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="classcale-x-agent")
    parser.add_argument(
        "--config",
        default="config/x-browser-agent.example.json",
        help="Configuration JSON de l'agent navigateur",
    )
    parser.add_argument("--log-level", default="INFO")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("login", help="Ouvrir Chromium pour une connexion X manuelle")
    commands.add_parser("plan", help="Afficher le prochain plan de recherche")
    commands.add_parser("once", help="Executer un cycle de recherche")
    commands.add_parser("run", help="Executer l'agent en continu")
    return parser


async def _run(args: argparse.Namespace) -> int:
    config = BrowserAgentConfig.load(args.config)
    agent = XResearchAgent(config)
    if args.command == "login":
        await agent.login()
        print("Session X conservee dans le profil local ignore par Git.")
        return 0
    if args.command == "plan":
        print(json.dumps(asdict(await agent.make_plan()), ensure_ascii=False))
        return 0
    if args.command == "once":
        print(json.dumps(asdict(await agent.collect_once()), ensure_ascii=False))
        return 0
    await agent.run_forever()
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

