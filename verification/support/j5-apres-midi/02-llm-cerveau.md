---
subtitle: >-
  Un agent vaut ce que vaut son cerveau. Avant de s'en servir, on regarde ce qu'est un grand modèle
  de langage : un prédicteur de mots, entraîné sur une énorme quantité de textes, qui lit et écrit
  par jetons. On en tire ce qu'il fait très bien, ce qu'il fait mal, et comment on le branche à du
  code : consignes, outils, format imposé, raisonnement.
objectives:
  - Expliquer ce que fait un LLM - jetons, prédiction du jeton suivant, fenêtre de contexte, entraînement
  - Décrire l'interface d'un LLM moderne - consignes, entrée, sortie, outils, format imposé, raisonnement
  - Citer les avantages d'un LLM et ses limites - hallucinations, variabilité, coût, latence, date de connaissance
  - Choisir ce qu'on peut confier à un LLM, et ce qu'on doit garder dans du code
---

{#prediction}
## Un prédicteur de jetons

**L'analogie de la saisie prédictive.** Votre téléphone propose le mot suivant quand vous écrivez un SMS. Un LLM fait la même chose, en beaucoup plus grand : il a appris, sur une partie considérable du texte disponible (livres, sites, code), à prédire **le morceau de texte suivant**. Appliquée mot après mot, cette prédiction produit des réponses, des résumés, du code.

- **Le jeton** (*token*) : l'unité de texte du modèle, un mot court ou un morceau de mot. Il faut compter environ 4 caractères par jeton en anglais, un peu moins de texte par jeton en français. On paie au jeton, en entrée et en sortie.
- **La fenêtre de contexte** : le nombre maximal de jetons que le modèle lit en une fois (consignes, historique, résultats d'outils). Les modèles récents en lisent des centaines de milliers, mais plus le contexte est long, plus l'appel est lent et cher, et plus le modèle risque de négliger une information noyée au milieu.
- **L'entraînement en trois temps** : d'abord prédire le texte (pré-entraînement), puis suivre des consignes sur des exemples de questions et de réponses, enfin préférer les réponses que des humains jugent meilleures. Le modèle ne « consulte » rien : tout ce qu'il sait est figé dans ses paramètres, à une **date de connaissance**.
- **Les modèles qui raisonnent** : avant de répondre, ils écrivent une réflexion intermédiaire, qu'on ne voit pas toujours. Ils sont meilleurs sur les problèmes à plusieurs étapes, mais plus lents, et ces jetons de raisonnement sont facturés comme des jetons de sortie. On règle l'effort : la passerelle de la formation utilise `low` par défaut.

{#interface}
## Comment on le branche à du code

Un appel à l'API Responses d'OpenAI, celle du TP, se lit en cinq champs :

| Champ | Rôle | Dans le TP |
|---|---|---|
| `instructions` | Les consignes : le rôle, le ton, les interdits | « Tu rédiges le SMS envoyé par ColisVert… » |
| `input` | La demande, ou tout l'historique d'une conversation | Le message d'un client, ou l'historique de l'agent |
| `tools` | Les outils que le LLM peut **demander** ; chacun a un nom, une description et un schéma d'arguments | Les trois outils de l'agent |
| `text.format` | Un **schéma JSON** que la réponse doit respecter | Le tri des messages des clients |
| `reasoning.effort` | L'effort de raisonnement | `low`, imposé par la passerelle |

La réponse est une liste d'**éléments** : un `message` (le texte), parfois un `reasoning` (le raisonnement, chiffré quand rien n'est conservé chez le fournisseur), ou des `function_call` (les demandes d'outils). Et `usage` donne les jetons consommés.

**Le point clé : le LLM est sans mémoire.** Chaque appel repart de zéro. Une « conversation », c'est le code qui renvoie l'historique à chaque fois. C'est une bonne nouvelle pour la gouvernance : ce que le modèle voit, c'est exactement ce que votre code lui envoie, et on peut le tracer.

{#forces}
## Ce qu'il fait très bien

- **Lire du texte libre** : un message de client, un journal d'erreurs, un ticket. Là où une expression régulière casse au premier mot inattendu, le LLM comprend l'intention.
- **Rédiger** : résumer, reformuler, adapter le ton, traduire. Le SMS, la note d'analyse, la description d'une colonne.
- **Écrire du code** : une requête SQL, une transformation pandas, un test. À relire, comme le code d'un stagiaire brillant.
- **Choisir entre des outils** : comprendre une demande et décider quelle fonction appeler, avec quels arguments.
- **S'adapter sans réentraînement** : une nouvelle consigne suffit, là où un modèle classique demanderait des données étiquetées.

{#limites}
## Ce qu'il fait mal

| Limite | Ce qui se passe | La parade |
|---|---|---|
| **Hallucinations** | Il écrit des faits plausibles et faux, avec assurance : un chiffre, une référence, une règle qui n'existe pas | Lui donner les faits (outils, documents) et **vérifier** par le code : l'ancrage des chiffres du TP |
| **Variabilité** | Deux appels identiques donnent deux réponses différentes | Format imposé, tests sur la structure plutôt que sur le texte, doublure en CI |
| **Calcul** | Il « devine » le résultat d'une opération au lieu de la faire | Faire calculer le code (un outil), et lui faire citer le résultat |
| **Date de connaissance** | Il ignore ce qui s'est passé après son entraînement, et vos données internes | Les lui fournir à chaque appel (outils, recherche documentaire) |
| **Coût et latence** | Plusieurs secondes et une fraction de centime par appel : le 17 novembre, sur le serveur de la formation, 3,8 s pour un appel simple, 4,8 s pour une demande d'outil | Ne pas l'appeler pour ce qu'une règle fait en quelques microsecondes ; borner les tours ; un repli quand il est lent |
| **Sensibilité à la formulation** | Une consigne un peu différente change le comportement | Versionner les consignes comme du code ; les évaluer sur un jeu de référence à chaque changement |
| **Injection** | Un texte qu'il lit (un message, une page web, un document) peut contenir des ordres | Ne jamais lui donner un pouvoir d'agir que le texte lu pourrait détourner ; vérifier par le code |
| **Biais** | Il reproduit les biais de ses données d'entraînement | Mesurer l'équité sur vos cas, comme ce matin pour le modèle de retard |

::: callout info Et la recherche documentaire (RAG) ?
Pour qu'un LLM réponde à partir de **vos** documents (procédures, contrats, documentation des pipelines), on cherche d'abord les passages utiles et on les met dans `input` : c'est la génération augmentée par la recherche (*Retrieval-Augmented Generation*). Les passages sont retrouvés par sens grâce à des **plongements** (*embeddings*) : des vecteurs de nombres rangés dans un index vectoriel. Le RAG réduit les hallucinations sans les supprimer, et ouvre de nouveaux risques : un document piégé dans l'index, des droits d'accès oubliés. On les retrouve dans la liste de l'OWASP.
:::

{#choisir}
## Ce qu'on lui confie

| Confier au LLM | Garder dans le code |
|---|---|
| Comprendre un texte libre, le classer dans des catégories **fermées** | Les calculs, les seuils, les règles de décision |
| Rédiger un texte **vérifié ensuite** par un garde-fou | L'envoi du texte, et le repli si le garde-fou refuse |
| Choisir parmi des outils en **lecture seule** | L'exécution des outils, la liste blanche, les droits |
| Proposer une action | L'approbation de l'action, par un humain |

{#quiz}
## Quiz

```quiz
- q: Qu'apprend un LLM pendant son pré-entraînement ?
  options:
    - À exécuter du code
    - À prédire le morceau de texte suivant sur un très grand corpus
    - À interroger internet
    - À se souvenir de chaque utilisateur
  answer: 1
  explain: Tout le reste (suivre des consignes, appeler des outils) est construit sur cette prédiction.
- q: Pourquoi faut-il renvoyer tout l'historique à chaque appel ?
  options:
    - Parce que la passerelle l'exige
    - Parce que le LLM est sans mémoire entre deux appels
    - Pour payer moins
    - Pour accélérer la réponse
  answer: 1
  explain: La mémoire d'une conversation est dans le code ; c'est aussi pourquoi les jetons d'entrée grossissent à chaque tour.
- q: Le LLM écrit dans sa note « le retard a augmenté de 54 % ». Que faire ?
  options:
    - Le croire, il a raisonné
    - Vérifier que ce chiffre vient d'un outil ; sinon, le faire calculer par le code
    - Augmenter l'effort de raisonnement
    - Supprimer la note
  answer: 1
  explain: Un calcul fait par le LLM n'est pas prouvé ; c'est le rôle de l'ancrage des chiffres.
- q: Qu'est-ce qu'un jeton de raisonnement ?
  options:
    - Un mot de passe
    - Un jeton de la réflexion intermédiaire d'un modèle qui raisonne, facturé comme un jeton de sortie
    - Un jeton gratuit
    - Une unité de mémoire de la passerelle
  answer: 1
  explain: Plus l'effort est grand, plus ces jetons sont nombreux - meilleure qualité, mais plus lent et plus cher.
```
