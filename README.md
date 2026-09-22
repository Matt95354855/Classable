# Classcale

Plateforme de recherche et de trading algorithmique dédiée aux crypto-actifs les plus liquides.

## État du projet

Le moteur de trading est [QuantConnect LEAN](https://github.com/QuantConnect/Lean), intégré sous `vendor/lean` comme sous-module Git épinglé sur un commit précis.

Le code LEAN reste soumis à sa licence Apache 2.0 et à ses mentions de copyright. Le code propre à Classcale sera développé séparément afin de pouvoir mettre à jour le moteur sans mélanger les modifications.

## Installation

```bash
git clone --recurse-submodules https://github.com/Matt95354855/Classable.git
cd Classable
git submodule update --init --recursive
```

Si le dépôt a déjà été cloné :

```bash
git submodule update --init --recursive
```

## Périmètre initial

- Crypto-actifs majeurs et liquides
- Stablecoins exclus des actifs spéculatifs
- Backtests point-in-time avant tout trading réel
- Paper trading obligatoire
- Moteur de risque indépendant des stratégies
- Actualités et signaux sociaux utilisés comme contexte, jamais comme autorité directe d'exécution

## Structure prévue

- `vendor/lean/` : moteur QuantConnect LEAN
- `classcale/` : stratégies, sélection de régime et gestion du risque
- `docs/` : décisions techniques et sources de données
- `config/` : exemples de configuration sans secrets

## Sécurité

Ne jamais committer de clés d'exchange, jetons API, mots de passe ou cookies de session. Utiliser des variables d'environnement et commencer en mode simulation.
