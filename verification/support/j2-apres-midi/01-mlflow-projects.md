---
subtitle: >-
  Un projet MLflow est une recette normalisée : un fichier dit quelle commande lancer, avec quels
  paramètres, dans quel environnement. N'importe qui, n'importe où, relance alors le même
  entraînement en une ligne. Et les Recipes, présentes au programme ? Elles ont été retirées de
  MLflow 3 : on verra ce qu'elles étaient et ce qui les remplace.
objectives:
  - Lire un fichier MLproject et nommer ses trois parties
  - Lancer un projet MLflow avec mlflow run en changeant ses paramètres
  - Choisir un gestionnaire d'environnement selon le besoin de reproductibilité
  - Expliquer ce qu'étaient les MLflow Recipes et pourquoi on ne les utilise plus
---

{#pourquoi}
## Pourquoi empaqueter un entraînement ?

**Le problème.** Ce matin, l'entraînement se lançait de trois façons : cellule par cellule dans un notebook, avec `dvc repro`, ou script par script. Chacune suppose de connaître le dépôt : quels fichiers, quel ordre, quels réglages. Un collègue d'une autre équipe, ou un serveur de calcul dans le cloud, ne sait pas tout cela.

**L'analogie de la fiche recette.** Dans une cuisine professionnelle, chaque plat a sa **fiche technique** normalisée : les ingrédients et le matériel, les étapes, et les variantes possibles (« pour 4 ou pour 40 couverts »). N'importe quel cuisinier de la brigade refait le plat sans demander. Un **projet MLflow** est cette fiche pour un entraînement.

{#mlproject}
## Le fichier MLproject

Un projet MLflow est simplement un dossier qui contient un fichier nommé `MLproject` (sans extension). Le dépôt des TP en a un, à la racine :

```yaml title="MLproject"
name: colisvert-retards

# Le projet s'exécute dans l'environnement courant (option --env-manager local) :
# celui de l'image des TP, où tout est déjà installé.

entry_points:
  main:
    parameters:
      C: {type: float, default: 1.0}
      class_weight: {type: string, default: none}
    command: "python -m pipeline.projet --C {C} --class-weight {class_weight}"
```

| Partie | Rôle | Ici |
|---|---|---|
| `name` | Le nom du projet | `colisvert-retards` |
| `entry_points` | Les **points d'entrée** : les commandes qu'on peut lancer. Un projet peut en avoir plusieurs (`prepare`, `train`…) | Un seul, `main` |
| `parameters` | Les paramètres de chaque point d'entrée, avec un **type** et une **valeur par défaut** | `C` (nombre décimal), `class_weight` (texte) |
| `command` | La commande, où `{C}` est remplacé par la valeur reçue | `python -m pipeline.projet …` |

Un projet peut aussi déclarer son **environnement** : un fichier `python_env.yaml` (une version de Python et une liste de bibliothèques), un environnement conda, ou une image Docker. MLflow le construit alors avant de lancer la commande. Ici, on utilise l'environnement de l'image des TP, déjà complet.

Le script `pipeline/projet.py` entraîne **et** évalue en un seul run : il lit les jeux préparés ce matin, note les métriques du test, l'origine (commit et empreinte des données) et le modèle. Il n'écrit rien dans `models/` : il ne dérange pas le pipeline DVC.

{#lancer}
## Lancer le projet

:::: lab Démo | Relancer l'entraînement avec d'autres paramètres | 8 min
Dans un terminal de JupyterLab, à la racine du dépôt, lancez le projet avec les réglages qui ont réussi l'évaluation du matin, `C=0.1` et `class_weight=balanced` :

```bash title="Terminal JupyterLab"
cd /home/lab/projet
mlflow run . -P C=0.1 -P class_weight=balanced --env-manager local --experiment-name colisvert-retards
```

- `.` : le projet est le dossier courant. Ce pourrait être l'adresse d'un dépôt Git distant : MLflow le clonerait d'abord.
- `-P nom=valeur` : un paramètre. Les paramètres non donnés prennent leur valeur par défaut.
- `--env-manager local` : utiliser l'environnement courant, sans en construire un nouveau.
- `--experiment-name` : l'expérience où ranger le run.

MLflow crée un run, y note les paramètres, puis lance la commande en lui transmettant l'identifiant du run. Le script s'y rattache et imprime ses résultats :

```plaintext title="Sortie attendue (extrait)"
projet MLflow : C=0.1, class_weight=balanced
exactitude : 0.863
precision  : 0.561
rappel     : 0.880
f1         : 0.685
roc_auc    : 0.948
```

MLflow encadre ces lignes de messages `INFO`, dont le dernier annonce que le run a réussi (`=== Run (ID '…') succeeded ===`).

**Vérification :** dans l'interface de MLflow, l'expérience `colisvert-retards` contient un nouveau run. Sans nom fourni, MLflow lui en a tiré un au hasard, du genre `awesome-wren-849`. Il a trois paramètres : `C` = `0.1` et `class_weight` = `balanced`, notés par `mlflow run`, et `max_iter` = `1000`, ajouté par le script. Ses tags disent qu'il a été lancé par un projet (`mlflow.source.type` = `PROJECT`, `mlflow.project.entryPoint` = `main`), depuis quel dépôt Git et à quel commit, en plus des tags `commit_git` et `md5_donnees` posés par le script.

Ce run **atteint le critère de succès** : rappel 0,880 ≥ 0,80, précision 0,561 ≥ 0,50. On le retrouvera dans le registre.

::: hint
`No such file or directory: '…/data/prepared/train.csv'` : les jeux préparés manquent. Lancez `dvc checkout` (ou `dvc repro`), puis relancez le projet. `MlflowException: Changing param values is not allowed` : vous avez modifié le script pour noter un paramètre déjà noté par `mlflow run` avec une autre valeur ; MLflow interdit qu'un paramètre change de valeur dans un run.
:::
::::

{#environnements}
## Quel environnement ?

| Option `--env-manager` | Ce que fait MLflow | Quand l'utiliser |
|---|---|---|
| `local` | Rien : la commande tourne dans l'environnement courant | Dans un conteneur déjà complet, comme ici ; pour aller vite |
| `virtualenv` (défaut) | Crée un environnement Python isolé d'après `python_env.yaml` | Pour une vraie reproductibilité sur une autre machine |
| `conda` | Crée un environnement conda d'après `conda.yaml` | Si l'équipe utilise conda, ou des bibliothèques système |

Un projet peut aussi déclarer une **image Docker** (`docker_env` dans le `MLproject`) : la commande tourne alors dans un conteneur. C'est le niveau de reproductibilité le plus élevé, celui que vous avez déjà grâce à l'image des TP.

::: callout warn Attention : « local » n'isole rien
Avec `--env-manager local`, le projet utilise les versions de bibliothèques installées sur la machine qui le lance. Sur un poste différent, avec une autre version de scikit-learn, le même projet peut donner un autre modèle. C'est acceptable ici, parce que tout le monde utilise la même image ; en entreprise, on fixe l'environnement dans le projet.
:::

{#recipes}
## Et les MLflow Recipes ?

Le programme de la formation cite **MLflow Projects et Recipes**. Les Recipes (d'abord appelées *MLflow Pipelines*) proposaient des **modèles de pipeline prêts à remplir**, pour la régression et la classification : des étapes imposées (ingestion, découpage, transformation, entraînement, évaluation, enregistrement), configurées par un fichier YAML. Le data scientist ne fournissait que quelques fonctions.

**Elles ont été complètement retirées de MLflow 3.0** (la liste officielle des changements de MLflow 3 le précise). La documentation recommande à la place le suivi des expériences, le registre et, selon les cas, les Projects. Ce que vous avez construit ce matin est exactement cette alternative :

| Étape d'une Recipe | Ce qui la remplace dans votre dépôt |
|---|---|
| Ingestion et découpage | `pipeline/prepare.py`, déclaré dans `dvc.yaml` |
| Transformation | L'encodage un-parmi-n, **dans** le modèle (`construire_modele`) |
| Entraînement | `pipeline/train.py`, ou le projet MLflow |
| Évaluation | `pipeline/evaluate.py` et `metrics.json` |
| Enregistrement | Le registre des modèles (notion suivante) |
| Enchaînement automatique | `dvc repro` aujourd'hui, Airflow au jour 3 |

La leçon dépasse MLflow : un cadre qui impose sa structure fait gagner du temps au départ, mais devient une contrainte dès que le projet sort du cas prévu. Les briques simples et assemblables (un script par étape, un fichier de description, un outil de suivi) durent plus longtemps.

{#qui-fait-quoi}
## Projects, DVC, Airflow : qui fait quoi ?

| Outil | Il répond à | Il ne fait pas |
|---|---|---|
| **MLflow Projects** | « Comment lancer cet entraînement, avec ces paramètres, n'importe où ? » | Savoir ce qu'il faut relancer, planifier |
| **DVC** | « Quelles étapes relancer, sur quelles données ? » | Planifier, alerter |
| **Airflow** (jour 3) | « Quand lancer, dans quel ordre, et qui prévenir en cas d'échec ? » | Versionner les données |

Ils se combinent : au jour 3, Airflow lancera chaque matin `dvc repro`, dont les étapes noteront leurs runs dans MLflow.

{#avance}
## Pour aller plus loin : projets distants et exécution dans le cloud

Ce bloc est pour les profils avancés ; rien ici n'est exigé dans l'évaluation.

**Un projet à distance.** `mlflow run https://github.com/<organisation>/<depot> -v <commit> -P C=0.1` clone le dépôt **au commit donné**, construit l'environnement déclaré et lance le point d'entrée. Le run garde la trace du dépôt et du commit : c'est une façon simple de garantir que l'entraînement de production utilise exactement le code revu, et pas la copie de travail de quelqu'un.

**Des cibles d'exécution.** Avec l'option `--backend`, la même commande peut envoyer le projet sur un cluster Databricks ou sur Kubernetes (chaque exécution devient un job). Azure Machine Learning propose aussi d'exécuter des projets MLflow sur ses ressources de calcul : le fichier `MLproject` reste le même, seule la cible change.

**Les paramètres transmis au script.** `mlflow run` passe au script l'identifiant du run par la variable d'environnement `MLFLOW_RUN_ID`, et `mlflow.start_run()` s'y rattache au lieu d'ouvrir un nouveau run. Deux pièges classiques : noter dans le script un paramètre que `mlflow run` a déjà noté avec une autre valeur (MLflow refuse : un paramètre ne change pas dans un run, d'où la précaution prise dans `pipeline/projet.py`), et appeler `set_experiment` avec une autre expérience que celle de `--experiment-name` (MLflow refuse de rattacher le run).

**Projets ou pipeline ?** Un `MLproject` peut avoir plusieurs points d'entrée qu'un script principal enchaîne, ce qui en fait un petit orchestrateur. C'est possible, mais on perd ce que DVC et Airflow apportent : relancer seulement ce qui a changé, reprendre après une panne, planifier. Le bon usage : un projet par **unité d'exécution** (un entraînement), et un vrai orchestrateur au-dessus.

{#quiz}
## Quiz de validation

```quiz
- q: Que contient la partie entry_points d'un fichier MLproject ?
  options:
    - Le modèle entraîné
    - Les commandes qu'on peut lancer, avec leurs paramètres typés et leurs valeurs par défaut
    - Les métriques du dernier run
    - La liste des utilisateurs autorisés
  answer: 1
  explain: Chaque point d'entrée est une commande ; mlflow run -e choisit lequel lancer (main par défaut).
- q: Que fait l'option --env-manager local ?
  options:
    - Elle construit un environnement isolé
    - Elle lance la commande dans l'environnement courant, sans rien installer
    - Elle exécute le projet dans le cloud
    - Elle désactive MLflow
  answer: 1
  explain: Rapide, mais sans isolation - la reproductibilité dépend alors de la machine qui lance.
- q: Que sont devenues les MLflow Recipes ?
  options:
    - Elles sont devenues obligatoires dans MLflow 3
    - Elles ont été retirées de MLflow 3.0 ; on assemble à la place suivi, registre, Projects et un orchestrateur
    - Elles ont été renommées MLflow Projects
    - Elles ne servent qu'avec Databricks
  answer: 1
  explain: La liste des changements de MLflow 3 l'indique. Le pipeline DVC du matin joue leur rôle.
- q: Quel outil répond à la question « quand lancer l'entraînement, et qui prévenir en cas d'échec » ?
  options: [MLflow Projects, DVC, Airflow, Git]
  answer: 2
  explain: C'est le rôle d'un orchestrateur, au programme du jour 3.
```
