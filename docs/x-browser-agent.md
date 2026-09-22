# Agent navigateur X pour les evenements crypto

Cet agent ouvre les pages visibles de `x.com` dans Chromium avec Playwright. Il n'utilise ni l'API X payante ni les endpoints GraphQL internes. Un LLM local Ollama choisit un plan de recherche borne, puis le navigateur consulte les pages de resultats et les comptes autorises.

## Ce que fait le LLM

Le LLM recoit les derniers evenements deja conserves, les recherches de base et la liste fermee de comptes autorises. Il renvoie au maximum six recherches et six comptes en JSON structure. Le programme valide ensuite chaque valeur avant de laisser le navigateur agir.

Le LLM ne controle pas librement le navigateur, ne peut pas visiter une URL arbitraire et ne dispose d'aucune cle d'exchange.

Si Ollama est indisponible, un plan deterministe fonde sur les recherches de base est utilise.

## Limites

- L'agent ne voit que les publications chargees dans l'interface Web.
- Il ne peut pas garantir l'exhaustivite de X.
- Les locators de la page peuvent changer.
- Une connexion, un CAPTCHA ou un blocage exige une intervention manuelle.
- Aucun mecanisme de furtivite, rotation de comptes, proxy ou contournement n'est implemente.
- L'utilisation doit rester conforme aux conditions applicables au compte X de l'operateur.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
playwright install chromium
```

Pour un LLM local :

```bash
ollama serve
ollama pull qwen3:8b
```

Le modele peut etre change dans `config/x-browser-agent.example.json`.

## Connexion manuelle

```bash
classcale-x-agent --config config/x-browser-agent.example.json login
```

Une fenetre Chromium s'ouvre. Connectez-vous vous-meme a X, puis revenez au terminal et appuyez sur Entree. Le profil est conserve dans `data/x-browser-profile`, ignore par Git. Ne partagez jamais ce repertoire : il contient une session authentifiee.

## Execution

Afficher le plan sans ouvrir X :

```bash
classcale-x-agent --config config/x-browser-agent.example.json plan
```

Un cycle visible :

```bash
classcale-x-agent --config config/x-browser-agent.example.json once
```

Execution continue :

```bash
classcale-x-agent --config config/x-browser-agent.example.json run
```

Le mode visible est active par defaut. Pour une execution headless apres validation manuelle, passez `browser.headless` a `true`.

## Garde-fous

- 8 pages maximum par cycle ;
- 3 defilements maximum par page ;
- 40 publications maximum par page ;
- pause fixe entre les pages et les defilements ;
- 2 minutes minimum entre les cycles ;
- uniquement les comptes presents dans la configuration ;
- URLs externes et instructions JavaScript rejetees dans les plans LLM ;
- filtrage deterministe avant stockage ;
- aucune execution d'ordre de trading.

## Ancien connecteur

Le connecteur `twscrape` reste disponible uniquement comme dependance optionnelle pour reference :

```bash
pip install -e '.[legacy-x]'
```

Il n'est plus le chemin recommande pour Classcale.

