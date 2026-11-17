---
subtitle: >-
  Des centaines d'outils se disputent chaque étape d'un pipeline de données. Pour ne pas s'y
  perdre, on raisonne par couches : chaque couche répond à une question, et un outil n'est qu'une
  réponse possible. La pile de ColisVert, construite depuis lundi, sert de fil conducteur.
objectives:
  - Nommer les couches de l'écosystème DataOps et la question à laquelle chacune répond
  - Placer les outils de la semaine dans ces couches, avec leurs équivalents Azure, Fabric et Google Cloud
  - Expliquer pourquoi les formats et standards ouverts comptent plus que les outils eux-mêmes
  - Reconnaître les deux grandes manières d'assembler une pile, outils spécialisés ou plateforme intégrée
---

{#pourquoi}
## Pourquoi raisonner par couches ?

**Le problème.** Un panorama des outils de données compte plusieurs centaines de logos. Un responsable qui choisit outil par outil, au gré des démonstrations commerciales, finit avec une pile où trois outils font la même chose et où personne ne sait lequel fait foi.

**L'analogie de la maison.** Une maison se pense par **corps de métier** : fondations, gros œuvre, plomberie, électricité, finitions. On choisit d'abord ce dont chaque corps de métier doit s'occuper, puis l'artisan. Changer de plombier ne doit pas obliger à refaire l'électricité. Dans une pile de données, les corps de métier sont les **couches**, et les artisans sont les outils.

{#couches}
## Les couches de l'écosystème

| Couche | La question | Chez ColisVert cette semaine |
|---|---|---|
| **Intégration** (ingestion) | Comment les données arrivent-elles ? | Le fichier quotidien des livraisons ; `dvc import-url` pour les taxis |
| **Stockage** | Où vivent-elles, sous quel format ? | Fichiers CSV et Parquet, cache et stockage DVC |
| **Traitement** (préparation, calcul) | Avec quel moteur les transforme-t-on ? | pandas ; DuckDB et Spark ce matin |
| **Orchestration** | Qui lance quoi, quand, et que faire en cas d'échec ? | `dvc repro` à la main ; Airflow cet après-midi |
| **Qualité et contrats** | Les données sont-elles conformes à ce qu'on attend ? | Le rapport de qualité et le contrat du jour 1 |
| **Reproductibilité** | Peut-on refaire exactement le même résultat ? | Git, DVC, l'image Docker des TP |
| **Machine learning** | Expériences, modèles, registre, service | MLflow (jour 2) |
| **Déploiement** | Comment une nouvelle version passe-t-elle en production ? | Alias du registre ; GitHub Actions pour la vérification |
| **Surveillance** (observabilité) | Comment sait-on que quelque chose se dégrade ? | Evidently (jour 2) ; alertes Airflow (cet après-midi) |
| **Gouvernance et catalogue** | Qui a le droit, d'où vient la donnée, que signifie-t-elle ? | Provenance DVC, lignage (jour 1) ; gouvernance au jour 5 |
| **Restitution** (BI, applications) | Qui utilise le résultat, et comment ? | Les SMS aux clients, le tableau de bord du service client |

Deux remarques :

- **Une couche peut être vide ou manuelle.** Chez beaucoup d'équipes, la couche « surveillance » est une personne qui regarde un tableau de bord le lundi. Le reconnaître est le début de l'amélioration.
- **Un outil peut couvrir plusieurs couches.** MLflow touche au machine learning, au déploiement et un peu à la surveillance. C'est utile, mais il faut savoir lequel fait foi pour chaque couche.

{#cloud}
## Les mêmes couches chez les fournisseurs cloud

| Couche | Outils libres (cette semaine) | Microsoft Azure | Microsoft Fabric | Google Cloud |
|---|---|---|---|---|
| Intégration | Scripts, `dvc import-url` | Azure Data Factory | Pipelines et flux de données de Fabric | Datastream, Dataflow |
| Stockage | Fichiers Parquet, Delta (jour 5) | Azure Data Lake Storage | OneLake (tables Delta) | Cloud Storage, BigQuery |
| Traitement | pandas, DuckDB, Spark | Azure Databricks, Synapse | Notebooks Spark, entrepôt SQL | Dataproc (Spark), BigQuery |
| Orchestration | Airflow | Data Factory | Pipelines ; tâches Apache Airflow | Managed Service for Apache Airflow (ex-Cloud Composer) |
| Machine learning | MLflow | Azure Machine Learning | Expériences et modèles ML | Vertex AI |
| Surveillance | Evidently, journaux | Azure Monitor, surveillance Azure ML | Hub de surveillance | Cloud Monitoring, Vertex AI Model Monitoring |
| Gouvernance | DVC, conventions | Microsoft Purview | Purview intégré, étiquettes | Dataplex |
| Restitution | Tableaux, SMS | Power BI | Power BI | Looker |

Le tableau montre surtout une chose : **les couches sont les mêmes partout**. Un ingénieur qui comprend les couches change de fournisseur en apprenant des noms ; un ingénieur qui ne connaît que des noms doit tout réapprendre.

{#standards}
## Les standards comptent plus que les outils

Les outils changent tous les trois ans ; les **formats** et les **protocoles** durent. Choisir des standards ouverts, c'est garder la liberté de changer d'outil sans migrer les données.

| Standard | Ce qu'il fixe | Pourquoi il protège |
|---|---|---|
| **Parquet** | Le format de fichier en colonnes | Lu par pandas, DuckDB, Spark, Fabric, BigQuery, Snowflake… |
| **Delta Lake, Apache Iceberg** | Le format de **table** (transactions, historique) au-dessus de Parquet | Plusieurs moteurs lisent et écrivent la même table |
| **Apache Arrow** | Le format des données **en mémoire** | Les moteurs s'échangent des tableaux sans copie ni conversion |
| **SQL** | Le langage de requête | Une requête DuckDB se transpose dans Spark, Fabric ou BigQuery avec peu de changements |
| **Format de modèle MLflow** | L'emballage d'un modèle | Servi par MLflow, Azure ML, Databricks, Fabric |
| **OpenLineage** | La description du lignage | Plusieurs outils de catalogue la comprennent |

::: callout remember À retenir
On choisit d'abord les **formats** (Parquet, Delta ou Iceberg, Arrow, SQL), ensuite les **outils** qui les parlent. Une donnée enfermée dans un format propriétaire coûte cher à libérer le jour où l'outil ne convient plus.
:::

{#assembler}
## Deux manières d'assembler une pile

| | **Outils spécialisés** (« meilleur de chaque catégorie ») | **Plateforme intégrée** |
|---|---|---|
| Exemple | Airflow + DVC + MLflow + DuckDB + un outil de BI | Microsoft Fabric, Databricks, Snowflake |
| Points forts | Le meilleur outil pour chaque couche, indépendance, coût des licences faible | Un seul contrat, une seule sécurité, intégration prête, moins de compétences à réunir |
| Points faibles | Tout l'assemblage est à votre charge : versions, sécurité, raccords entre outils | Dépendance au fournisseur, rythme de ses évolutions, coût à l'usage parfois difficile à prévoir |
| Convient à | Une équipe technique solide, des besoins particuliers | Une équipe qui veut livrer vite, une DSI qui veut standardiser |

Après une période où chaque couche avait sa start-up, le marché a nettement penché vers la **consolidation** : les grandes plateformes ont absorbé l'orchestration, le catalogue, le ML et la BI. Ce n'est ni bien ni mal : c'est un **choix d'architecture**, qui se raisonne. C'est l'objet de la notion suivante.

:::: lab Exercice | Classer les outils d'une autre entreprise | 5 min
Une mutuelle vous décrit sa pile. Pour chaque élément, donnez la couche :

1. Un script Python lancé par une tâche planifiée Windows à 6 h.
2. Des fichiers CSV déposés chaque nuit sur un partage réseau.
3. Un tableau de bord Power BI pour la direction.
4. Une feuille Excel où l'équipe note les incidents de données.
5. Un modèle de détection de fraude entraîné dans un notebook.
6. Un dépôt Git avec le code SQL des transformations.

::: solution Voir le classement
1. Orchestration (rudimentaire : aucune reprise sur échec, aucune alerte). 2. Intégration et stockage (sans format de colonnes ni versioning). 3. Restitution. 4. Surveillance (manuelle). 5. Machine learning (niveau 0 du jour 2 : ni suivi, ni registre). 6. Reproductibilité du traitement.

Ce que le classement révèle : **pas de couche qualité, pas de gouvernance**, et une orchestration fragile. Ce sont les trois chantiers à prioriser, avant d'acheter quoi que ce soit.
:::
::::

{#avance}
## Pour aller plus loin : la bataille des catalogues et la pile « composable »

Ce bloc est pour les profils avancés ; rien ici n'est exigé dans l'évaluation.

**Les formats de table ont déplacé la bataille vers les catalogues.** Quand Delta et Iceberg ont rendu les données lisibles par tous les moteurs, l'enjeu est devenu le **catalogue** : le service qui sait quelles tables existent, où sont leurs fichiers et qui a le droit de les lire. En 2024, Databricks a ouvert le code d'Unity Catalog, et Snowflake a confié le catalogue Polaris, compatible avec le protocole REST d'Iceberg, à la fondation Apache. Un catalogue ouvert permet à plusieurs moteurs (Spark, DuckDB, Trino, Fabric…) de travailler sur les mêmes tables avec les mêmes droits. C'est aujourd'hui le point de contrôle de l'architecture : celui qui tient le catalogue tient les données.

**La pile « composable ».** Arrow (la mémoire), Parquet (le fichier), Iceberg ou Delta (la table), SQL (le langage) et un catalogue ouvert forment des briques standardisées. Un moteur devient alors un composant interchangeable : DuckDB sur un portable pour explorer, Spark sur un cluster pour le traitement de masse, un entrepôt managé pour la BI, **sur les mêmes fichiers**. C'est l'idée qu'illustre le TP de ce matin : trois moteurs, un seul fichier Parquet.

**Le coût caché de l'assemblage.** Chaque outil de plus, c'est une mise à jour de sécurité de plus à suivre, un raccord de plus qui peut casser, une compétence de plus à recruter. Une règle pratique : tout nouvel outil doit **remplacer** quelque chose ou combler une couche vide, jamais doublonner.

{#quiz}
## Quiz de validation

```quiz
- q: Dans quelle couche se range un orchestrateur comme Airflow ?
  options: [Le stockage, Le traitement, L'orchestration, La restitution]
  answer: 2
  explain: Il décide qui lance quoi et quand, et réagit aux échecs. Il ne transforme pas lui-même les données.
- q: Pourquoi choisir d'abord les formats (Parquet, Delta, SQL) avant les outils ?
  options:
    - Parce que les formats sont gratuits
    - Parce que les formats durent plus longtemps que les outils, et permettent d'en changer sans migrer les données
    - Parce que les outils n'ont pas de formats
    - Parce que les formats sont plus rapides
  answer: 1
  explain: Un format ouvert garde la donnée lisible par plusieurs moteurs ; changer d'outil ne coûte alors pas une migration.
- q: Quel est le principal point faible d'une plateforme intégrée ?
  options:
    - Elle ne permet pas de faire du SQL
    - La dépendance au fournisseur et à son rythme d'évolution
    - Elle est toujours plus lente
    - Elle interdit le machine learning
  answer: 1
  explain: En contrepartie, elle épargne tout le travail d'assemblage et de sécurité entre outils.
- q: Une équipe stocke ses données en Parquet. Quels moteurs peuvent les lire sans conversion ?
  options:
    - Seulement Spark
    - Seulement pandas
    - pandas, DuckDB, Spark et la plupart des plateformes cloud
    - Aucun sans import préalable dans une base
  answer: 2
  explain: C'est la force d'un format ouvert. Le TP de ce matin le montre sur le même fichier.
```
