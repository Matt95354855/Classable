# Classcale

Plateforme de recherche et de trading algorithmique dediee aux crypto-actifs les plus liquides.

## Etat du projet

Le moteur de trading est [QuantConnect LEAN](https://github.com/QuantConnect/Lean), integre sous `vendor/lean` comme sous-module Git epingle sur un commit precis.

Le code LEAN reste soumis a sa licence Apache 2.0 et a ses mentions de copyright. Le code propre a Classcale est developpe separement afin de pouvoir mettre a jour le moteur sans melanger les modifications.

## Installation

```bash
git clone --recurse-submodules https://github.com/Matt95354855/Classable.git
cd Classable
git submodule update --init --recursive
```

## Agent navigateur X

Le paquet `classcale.social` contient un agent de recherche qui ouvre reellement les pages visibles de `x.com` dans Chromium. Un LLM local via Ollama choisit les recherches et les comptes autorises a consulter. L'agent classe ensuite les incidents de securite, changements reglementaires, listings, pannes, mises a jour reseau et autres evenements significatifs, puis les deduplique dans SQLite.

Consulter [la documentation de l'agent](docs/x-browser-agent.md) pour l'installation, la connexion manuelle et les commandes disponibles.

```bash
pip install -e .
playwright install chromium
classcale-x-agent --config config/x-browser-agent.example.json login
classcale-x-agent --config config/x-browser-agent.example.json once
```

## Perimetre initial

- Crypto-actifs majeurs et liquides
- Stablecoins exclus des actifs speculatifs
- Backtests point-in-time avant tout trading reel
- Paper trading obligatoire
- Moteur de risque independant des strategies
- Actualites et signaux sociaux utilises comme contexte, jamais comme autorite directe d'execution

## Structure

- `vendor/lean/` : moteur QuantConnect LEAN
- `classcale/` : code, strategies, donnees sociales et gestion du risque
- `docs/` : decisions techniques et guides
- `config/` : exemples de configuration sans secrets
- `tests/` : tests locaux sans acces reseau

## Securite

Ne jamais committer de cles d'exchange, jetons API, mots de passe ou cookies de session. Utiliser des secrets locaux et commencer en mode simulation.
