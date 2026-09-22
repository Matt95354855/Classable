# Source de donnees X / Twitter

Cette decision remplace l'approche initiale fondee sur `twscrape`.

Le chemin recommande pour Classcale est l'agent navigateur decrit dans [`x-browser-agent.md`](x-browser-agent.md) : Chromium ouvre les pages visibles de `x.com`, l'operateur se connecte manuellement dans un profil local et un LLM Ollama produit un plan de recherche borne.

L'ancien connecteur `twscrape` reste disponible comme dependance optionnelle uniquement. Aucun des deux modes ne garantit l'exhaustivite du flux X.
