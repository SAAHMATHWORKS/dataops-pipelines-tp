---
subtitle: >-
  « Agent » est devenu le mot de l'année, et il recouvre des choses très différentes. On distingue
  trois familles - le chatbot, l'assistant et l'agent - par une seule question : qui décide de la
  prochaine action ? On ouvre ensuite un agent pour voir ses pièces, puis on fait le tour de ce
  qu'un agent peut faire dans une chaîne DataOps, en reprenant les rendez-vous de la semaine.
objectives:
  - Distinguer un chatbot, un assistant et un agent IA par leur autonomie et leur pouvoir d'agir
  - Décrire les pièces d'un agent - LLM, consignes, outils, mémoire, boucle, garde-fous, journal
  - Citer des rôles concrets d'agents dans une chaîne DataOps, et ce qui doit rester une décision humaine
  - Reconnaître quand un agent n'est pas la bonne solution
---

{#trois-familles}
## Chatbot, assistant, agent

**L'analogie du centre de tri.** Un **panneau d'information** répond aux questions fréquentes, toujours de la même façon. Un **collègue expérimenté** vous conseille pendant que vous travaillez, mais c'est vous qui triez. Un **chef d'équipe** reçoit un objectif (« vider le quai 3 avant 18 h ») et organise lui-même le travail. Les trois sont utiles. Ils ne demandent pas le même niveau de confiance.

| | **Chatbot** | **Assistant** (copilote) | **Agent** |
|---|---|---|---|
| Ce qu'il fait | Répond dans une conversation | Aide un humain à faire sa tâche : propose, rédige, explique | Poursuit un **objectif** : choisit ses actions, les enchaîne, observe le résultat |
| Qui décide de l'action suivante ? | Personne : il répond | **L'humain**, qui accepte ou non la proposition | **L'agent**, dans les limites qu'on lui a fixées |
| Outils | Aucun, ou une base de questions | Ceux de l'application où il vit | Les siens : requêtes, API, scripts, autres agents |
| Exemple chez ColisVert | « Où en est mon colis ? » sur le site | Copilot qui écrit une requête SQL dans un notebook Fabric | Un agent qui rassemble les faits d'une alerte et rédige la note pour l'équipe (TP de cet après-midi) |
| Risque principal | Une réponse fausse donnée à un client | L'humain qui valide sans relire | Une **action** fausse, enchaînée sans contrôle |

Un chatbot moderne peut s'appuyer sur un LLM ; un assistant aussi. Ce qui fait l'agent, ce n'est pas le LLM, c'est **la boucle** et **le pouvoir d'agir**.

{#autonomie}
## Des degrés d'autonomie

Comme pour l'automatisation de ce matin, on monte les niveaux un par un. Chaque niveau se gagne par des preuves obtenues au niveau précédent :

| Niveau | L'agent… | Exemple : l'alerte de la carte p |
|---|---|---|
| **1. Suggère** | prépare une analyse, l'humain fait tout le reste | La note du TP, lue par l'équipe |
| **2. Agit avec approbation** | propose une action précise, un humain l'approuve avant exécution | « Relancer le DAG de réentraînement ? » Oui / Non, dans Teams |
| **3. Agit dans un périmètre** | agit seul pour des actions réversibles et bornées, l'humain est prévenu | Ouvrir un ticket d'incident, mettre un rapport en pièce jointe |
| **4. Autonome** | agit seul et rend compte | Rare en entreprise, et jamais pour une décision qui touche des personnes |

**La règle de la semaine :** l'agent **prépare**, l'humain **décide**. Au jour 4, on l'a écrit pour la promotion d'un modèle et pour les coûts d'un retard : ce sont des décisions métier. Monter d'un niveau, c'est une décision de gouvernance, pas une décision technique.

{#anatomie}
## Les pièces d'un agent

::: figure agent-boucle.svg
Le LLM choisit les outils et rédige ; le code de l'agent décide de ce qui s'exécute ; l'équipe décide de ce qu'on fait.
:::

| Pièce | Rôle | Dans le TP |
|---|---|---|
| **Le LLM** | Le « cerveau » : comprend la demande, choisit les outils, rédige | `gpt-6-luna`, à travers la passerelle de la formation |
| **Les consignes** | Le rôle, le ton, les interdits | « Cite uniquement des chiffres donnés par les outils. Tu ne décides rien. » |
| **Les outils** | Les « mains » : des fonctions que le code exécute à la demande du LLM | `carte_controle`, `derive_variables`, `retards_par_entrepot` |
| **La mémoire** | Ce que l'agent sait de la conversation | L'historique, renvoyé **en entier** à chaque tour : le LLM, lui, ne se souvient de rien |
| **La boucle** | Demander, exécuter, recommencer, jusqu'à la réponse | 4 tours au plus |
| **Les garde-fous** | Ce que le code vérifie, quoi que dise le LLM | Liste blanche des outils, arguments vérifiés, ancrage des chiffres |
| **Le journal** | La preuve de ce qui s'est passé | Les traces MLflow, comme au jour 2 |

{#dataops}
## Des agents dans une chaîne DataOps

Toute la semaine, des encadrés « Et les agents IA ? » ont réservé une place. Les voici réunis, avec la limite de chacun :

| Où | Ce que l'agent fait | Ce qui reste humain |
|---|---|---|
| **Surveillance** (jour 4, cartes de contrôle) | Rassemble la règle en alerte, les variables qui ont bougé, les incidents du pipeline ; rédige une première analyse | Décider s'il faut réentraîner, retirer le modèle ou attendre |
| **Incidents de pipeline** (jour 3, Airflow) | Lit les journaux d'une tâche en échec, classe l'erreur (données, code, infrastructure), propose une relance | Relancer en production, corriger le code |
| **Qualité des données** (jours 1 et 3) | Propose des règles pour le contrat de données à partir d'un échantillon ; explique un lot rejeté | Valider les règles : ce sont des engagements avec le métier |
| **Documentation** (jour 5, ce matin) | Rédige la description des colonnes de la fiche du produit de données, propose une classification | Le propriétaire signe la fiche ; la vérification par code reste |
| **Questions en langage naturel** | Traduit « quel entrepôt a le plus de retards en décembre ? » en requête SQL, en lecture seule (agent de données de Fabric, démonstration tout à l'heure) | Interpréter, décider ; vérifier les chiffres qui comptent |
| **Revue de code et de pipeline** | Relit une demande de fusion, signale une fuite de données (`delai_reel_h` parmi les variables, jour 2) | Approuver la fusion |
| **Service client** | Trie les messages et rédige les réponses (TP, étapes 2 et 3) | Les cas sensibles, les gestes commerciaux, les colis inconnus |

**Le point commun :** l'agent fait gagner le temps de **rassembler et rédiger**. Il ne remplace ni les règles déterministes (la carte de contrôle elle-même), ni les décisions.

{#quand-pas}
## Quand ne pas utiliser d'agent

- **Quand une règle suffit.** Les quatre règles de Western Electric s'écrivent en quatre lignes de pandas : exactes, gratuites, instantanées, testables. Un LLM n'y ajouterait que du coût et de l'incertitude.
- **Quand l'erreur coûte cher et ne se rattrape pas.** Un virement, une suppression de données, une décision sur une personne : au mieux, niveau 2 (approbation humaine).
- **Quand on ne sait pas mesurer le résultat.** Sans jeu de questions de référence et sans traces, impossible de savoir si l'agent s'améliore ou se dégrade à chaque changement de consigne ou de modèle.
- **Quand les données ne doivent pas sortir.** Données de santé, secrets industriels : le choix du fournisseur et du lieu d'hébergement vient avant l'agent.

**La règle d'ingénieur :** automatiser d'abord **sans** LLM ce qui peut l'être, puis réserver le LLM à ce que le code ne sait pas faire : lire du texte libre, rédiger, choisir entre des outils.

{#quiz}
## Quiz

```quiz
- q: Qu'est-ce qui fait d'un système un agent, plutôt qu'un assistant ?
  options:
    - Il utilise un LLM
    - Il choisit lui-même ses actions, dans une boucle, pour atteindre un objectif
    - Il parle en français
    - Il est intégré à Teams
  answer: 1
  explain: Un assistant propose et l'humain agit ; un agent enchaîne lui-même les actions, dans les limites fixées.
- q: Un agent propose de relancer le DAG de réentraînement, et un humain clique « Approuver ». Quel niveau d'autonomie ?
  options:
    - Niveau 1, il suggère
    - Niveau 2, il agit avec approbation
    - Niveau 3, il agit dans un périmètre
    - Niveau 4, autonome
  answer: 1
  explain: L'action est précise et n'est exécutée qu'après approbation ; c'est le fonctionnement de l'agent d'opérations de Fabric.
- q: Le LLM d'un agent se souvient-il des tours précédents ?
  options:
    - Oui, il garde la conversation en mémoire chez le fournisseur
    - Non ; c'est le code qui renvoie tout l'historique à chaque appel
    - Seulement s'il est payant
    - Seulement pour les outils
  answer: 1
  explain: Avec store=false, rien n'est conservé ; la mémoire de l'agent, c'est l'historique que la boucle renvoie.
- q: Faut-il un agent pour détecter qu'un point de la carte p dépasse trois sigmas ?
  options:
    - Oui, c'est plus moderne
    - Non ; une règle déterministe est exacte, gratuite et testable
    - Oui, pour expliquer le dépassement
    - Seulement en décembre
  answer: 1
  explain: L'agent intervient après, pour rassembler le contexte et rédiger ; la détection reste une règle.
```
