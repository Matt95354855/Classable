# Collecteur X d'evenements crypto

Ce service collecte des publications X relatives aux principaux crypto-actifs, puis ne conserve que les contenus correspondant a un evenement identifiable et suffisamment fiable.

Il utilise `twscrape` 0.20.1 avec les cookies d'un unique compte X appartenant a l'operateur. Il ne contourne pas les CAPTCHA, ne cree pas de comptes, ne fait pas tourner de comptes ou de proxies et n'essaie pas de depasser les limites imposees par X.

## Limites importantes

- Cette methode n'offre pas le firehose complet de X.
- Les endpoints Web/GraphQL peuvent changer sans preavis.
- X peut refuser ou bloquer l'acces.
- L'operateur doit verifier les conditions applicables avant utilisation.
- Une publication X n'est jamais une preuve suffisante pour declencher seule un ordre.

## Installation

Python 3.11 ou plus recent est requis.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Ajouter le compte operateur

Depuis un navigateur connecte a votre propre compte X, exportez uniquement les cookies `auth_token` et `ct0` dans un fichier local temporaire :

```text
auth_token=...; ct0=...
```

Importez-les dans la base locale de `twscrape` :

```bash
classcale-social --config config/x-collector.example.json setup-account \
  --cookies-file /chemin/local/cookies.txt
```

Supprimez ensuite le fichier temporaire. Ne transmettez jamais ces cookies par messagerie et ne les committez jamais.

## Utilisation

Un cycle :

```bash
classcale-social --config config/x-collector.example.json once
```

Collecte continue :

```bash
classcale-social --config config/x-collector.example.json run
```

Consulter les donnees :

```bash
classcale-social --config config/x-collector.example.json stats
classcale-social --config config/x-collector.example.json export --limit 100
```

## Filtrage

Le score combine :

- le niveau de confiance attribue a la source ;
- la gravite du type d'evenement ;
- le statut de verification disponible ;
- une penalite pour les promesses de rendement, giveaways et contenus promotionnels.

Les types initiaux sont : incident de securite, regulation, listing, changement reseau, panne, structure de marche, offre de jetons, macroeconomie et partenariat.

## Donnees

Les publications retenues sont stockees dans `data/x_events.db`. La base applique une contrainte unique sur l'identifiant X et sur l'empreinte du contenu pour eviter les doublons.

Le repertoire `data/`, les bases SQLite, cookies, secrets et journaux sont ignores par Git.

