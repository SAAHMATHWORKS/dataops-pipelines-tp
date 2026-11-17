---
subtitle: >-
  Cinq jours, un même fil rouge : ColisVert, qui voulait prévenir ses clients avant un retard. On
  relit ce que l'entreprise a gagné jour après jour, on se situe face aux cinq objectifs de la
  formation, et l'on prépare la suite : ce qu'on peut appliquer dès lundi, et les trente jours
  d'accompagnement.
objectives:
  - Relier chaque jour de la semaine à ce qu'il a apporté à la chaîne DataOps de ColisVert
  - Évaluer soi-même sa maîtrise des cinq objectifs de la formation
  - Choisir une première action à mener dans son propre contexte
---

{#semaine}
## Ce que ColisVert a gagné en cinq jours

| Jour | La question de ColisVert | Ce qu'on a construit | Les outils |
|---|---|---|---|
| **1** | Que vaut notre donnée, et quelle version a servi ? | Une vision, une chaîne de valeur cartographiée, des données versionnées comme du code | Value Stream Mapping, Git, DVC |
| **2** | Comment construire et comparer des modèles sans se perdre ? | Un pipeline en étapes, chaque expérience tracée, un registre avec des alias, la recherche d'hyperparamètres, la surveillance de la dérive | MLflow, Optuna, Evidently |
| **3** | Quels outils choisir, et comment tout faire tourner seul ? | Une carte de Wardley et un radar technologique, des moteurs comparés sur les taxis de New York, un pipeline orchestré et déclenché par l'arrivée des données | DuckDB, Spark, Airflow 3 |
| **4** | Combien le modèle rapporte-t-il, et combien coûte-t-il ? | Le seuil en euros, des cartes de contrôle, les indicateurs DORA ; puis un compromis qualité-empreinte, et un service unique avec ombre et rédacteur | MSP, Optuna multi-objectif, MLflow PyFunc |
| **5** | Comment durer, rester responsable, et accueillir les agents ? | La gouvernance par le code, bronze-argent-or avec retour arrière, un modèle expliqué et vérifié par entrepôt ; un rédacteur et un agent à base de LLM, encadrés | Delta Lake, SHAP, LIME, interpretML, LLM, MLflow Tracing |

**Le fil de la semaine, en une phrase :** tout ce qui produit un résultat doit pouvoir être **rejoué**, **vérifié** et **expliqué** : les données, le code, les modèles, et maintenant les textes d'un LLM.

{#objectifs}
## Les cinq objectifs, pour s'auto-évaluer

Pour chaque objectif, placez-vous honnêtement : **1** j'ai compris, **2** je saurais le refaire avec le support, **3** je saurais l'adapter chez moi.

| Objectif de la formation | Où on l'a travaillé | Je sais… |
|---|---|---|
| Définir une stratégie data ambitieuse et réaliste | Jour 1 matin | formuler une vision, relier un cas d'usage à une valeur mesurable |
| Évaluer les priorités data selon l'état des lieux et la vision | Jours 1 et 4 | cartographier une chaîne de valeur, prioriser par WSJF, chiffrer un bénéfice |
| Identifier et pratiquer les technologies et leur complémentarité | Jours 1 à 5 | dire ce que font Git, DVC, MLflow, Airflow, Optuna, Evidently et Delta Lake, et lequel choisir pour quel problème |
| Construire des plateformes DataOps pour réduire le délai de mise en valeur | Jours 3 à 5 | orchestrer, surveiller, servir, gouverner ; automatiser par niveaux |
| Préparer l'intégration des agents IA dans les pipelines data | Jour 5 après-midi | dire où un agent aide, l'encadrer (outils, droits, traces, évaluation), et vérifier ses obligations (AI Act, RGPD) |

Un objectif à 1 ? Notez-le : c'est un bon sujet pour les trente jours qui viennent.

{#lundi}
## Et lundi ?

Une seule action, petite et visible, vaut mieux qu'un grand plan. Quelques idées, selon votre point de départ :

- **Vos données ne sont pas versionnées :** placez le jeu de données d'un projet sous DVC, avec un stockage partagé (jour 1).
- **Vos expériences sont dans des notebooks épars :** tracez le prochain entraînement dans MLflow, avec ses paramètres et ses métriques (jour 2).
- **Vos traitements partent à la main :** écrivez le DAG d'un seul pipeline, avec des tentatives et une alerte (jour 3).
- **Personne ne sait si le modèle rapporte :** chiffrez une matrice de coûts avec le métier, et mettez un indicateur sous carte de contrôle (jour 4).
- **Vos tables s'écrasent :** passez une table critique en Delta Lake, avec deux contraintes CHECK (jour 5).
- **Des LLM arrivent dans vos équipes :** faites l'inventaire des usages, mettez une passerelle devant les clés, et écrivez le garde-fou du premier cas d'usage (cet après-midi).

**Un conseil de méthode :** choisissez un problème **fréquent** et **visible**, mesurez l'avant, faites le changement, mesurez l'après. C'est ce résultat chiffré qui ouvre la porte à la suite.

{#apres}
## Après la formation

- **Le support** de la semaine reste votre référence : les blocs « Pour aller plus loin » sont écrits pour être lus maintenant, à votre rythme.
- **Le dépôt des TP** (`dataops-pipelines-tp`) est à vous : clonez-le sur votre poste ou dans votre entreprise, il fonctionne avec Docker seul.
- **Les trente jours d'accompagnement (M2i BOOST)** : jusqu'à quatre échanges avec votre formateur sur myM2i, pour une question, un blocage, ou un retour sur votre action du lundi.
- **Votre jeton LLM** cesse de fonctionner à la fin de la session : rien à faire de votre côté.

{#quiz}
## Quiz de la semaine

```quiz
- q: Quel outil répond à « quelle version des données a servi à entraîner ce modèle ? »
  options:
    - Airflow
    - DVC, avec Git
    - Evidently
    - Delta Lake
  answer: 1
  explain: Le ticket .dvc versionné dans Git pointe vers la version exacte des données (jour 1).
- q: Quel outil déclenche le pipeline à l'arrivée d'un nouveau fichier ?
  options:
    - MLflow
    - Airflow, avec les Assets
    - Optuna
    - DVC
  answer: 1
  explain: Le déclenchement par les données du jour 3 remplace un horaire fixe.
- q: Quelle méthode signale au fil de l'eau qu'un processus dérive ?
  options:
    - La recherche par grille
    - La carte de contrôle et ses règles d'alerte
    - Le front de Pareto
    - Le voyage dans le temps de Delta Lake
  answer: 1
  explain: La carte dit quand ; Evidently dit quelles variables ont bougé (jours 2 et 4).
- q: Dans le TP de cet après-midi, qui décide de ce qui s'exécute ?
  options:
    - Le LLM
    - Le code de l'agent - liste blanche, arguments vérifiés, tours bornés
    - OpenAI
    - Personne
  answer: 1
  explain: Le LLM demande ; le code exécute ou refuse ; l'équipe décide de ce qu'on fait de la note.
```
