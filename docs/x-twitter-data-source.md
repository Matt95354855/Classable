# Source de données X / Twitter

Décision enregistrée le 22 septembre 2026.

## Décision

Classcale utilisera une interface `SocialFeedProvider` indépendante du moteur de trading. Deux implémentations pourront exister :

1. `XApiProvider` — option de production recommandée, fondée sur l'API officielle X et protégée par un plafond de dépenses.
2. `TwscrapeProvider` — option expérimentale locale uniquement, désactivée par défaut.

L'API officielle X fonctionne actuellement au paiement à l'usage. Il n'existe pas de solution officielle, gratuite, générale et durable pour lire les publications en production.

## Option gratuite expérimentale

La bibliothèque open source `twscrape` peut techniquement lire les interfaces Web/GraphQL avec un compte X autorisé. Cette solution est fragile, dépend des changements internes de X et peut être incompatible avec les conditions du service.

Règles impératives :

- utiliser uniquement un compte appartenant à l'opérateur ;
- ne pas créer ni faire tourner des comptes pour contourner des limites ;
- ne pas contourner CAPTCHA, blocage ou contrôle technique ;
- ne jamais committer mots de passe, cookies ou jetons ;
- respecter les suppressions et ne pas republier les contenus collectés ;
- interrompre automatiquement la collecte en cas de 401, 403, 429 ou changement de schéma ;
- ne jamais permettre à cette source d'envoyer directement un ordre.

`snscrape` n'est pas retenu : son support de recherche Twitter est cassé depuis les changements d'accès de X.

## Sources gratuites complémentaires

Pour que le système continue à fonctionner sans X :

- flux RSS et communiqués officiels des exchanges et projets ;
- GDELT pour les événements mondiaux ;
- publications officielles des régulateurs ;
- sources ouvertes comme Bluesky ou Mastodon lorsque pertinentes.

## Format normalisé

Chaque message collecté doit devenir un événement contenant au minimum :

- identifiant de source et URL ;
- auteur et statut de vérification disponible ;
- horodatage de publication et d'ingestion ;
- actifs mentionnés ;
- type d'événement ;
- sentiment, nouveauté et confiance ;
- empreinte de déduplication ;
- texte brut séparé des signaux calculés.

## Utilisation par le bot

Les événements sociaux ne sont qu'une feature. Ils peuvent réduire, renforcer ou bloquer un signal quantitatif après validation par le moteur de risque. Un LLM ou un scraper ne dispose jamais des clés d'exécution du broker ou de l'exchange.

## Références

- API X : https://docs.x.com/x-api/introduction
- Tarification X : https://docs.x.com/x-api/getting-started/pricing
- Politique développeur X : https://docs.x.com/developer-terms/policy
- twscrape : https://github.com/vladkens/twscrape
- snscrape, état du support Twitter : https://github.com/JustAnotherArchivist/snscrape/issues/1037
