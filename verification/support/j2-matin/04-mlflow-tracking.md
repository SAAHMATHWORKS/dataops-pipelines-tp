---
subtitle: >-
  Un chimiste note chaque expérience dans son cahier de laboratoire : les produits, les réglages,
  le résultat. MLflow Tracking est ce cahier pour le machine learning, à ceci près qu'il se remplit
  tout seul depuis le code, et qu'on peut y chercher, trier et comparer.
objectives:
  - Définir expérience, run, paramètre, métrique, tag, artefact et modèle dans MLflow
  - Enregistrer un run depuis Python et le retrouver dans l'interface
  - Comparer des runs avec mlflow.search_runs
  - Expliquer comment relier un modèle au code et aux données qui l'ont produit
---

{#pourquoi}
## Pourquoi suivre ses expériences ?

**Le problème.** En R&D, on essaie beaucoup : un réglage, une variable de plus, un autre modèle. Au bout de deux jours, la question revient toujours : « le bon résultat de mardi, c'était avec quels réglages ? Et sur quelle version des données ? ». Les noms de fichiers du type `modele_v3_final_vraiment_final.joblib` ne répondent pas.

**L'analogie du cahier de laboratoire.** En chimie, chaque expérience est notée : date, produits utilisés et leurs lots, conditions (température, durée), résultat. Une expérience non notée n'a pas eu lieu, car personne ne pourra la refaire. **MLflow Tracking** joue ce rôle : chaque exécution de votre code y laisse une page, avec ses réglages, ses résultats et ses fichiers.

{#concepts}
## Le vocabulaire de MLflow

| Concept | Ce que c'est | Dans le cahier de labo | Chez ColisVert |
|---|---|---|---|
| **Expérience** (*experiment*) | Un dossier qui regroupe des runs sur un même sujet | Le cahier d'un projet | `colisvert-retards` |
| **Run** | Une exécution du code | Une page du cahier | « l'entraînement de mardi 10 h » |
| **Paramètre** (*param*) | Un réglage fixé **avant** l'exécution | Les conditions de l'expérience | `C = 1.0`, `class_weight = None` |
| **Métrique** (*metric*) | Un nombre **mesuré** pendant ou après l'exécution | Le résultat | `rappel = 0.591` |
| **Tag** | Une étiquette libre, pour chercher et tracer | Une note dans la marge | le commit Git, l'empreinte des données |
| **Artefact** | Un fichier produit par le run | Une photo du résultat, collée dans le cahier | `metrics.json`, une matrice de confusion |
| **Modèle** | Le modèle entraîné, enregistré dans un format standard et rechargeable | Le produit obtenu, mis en flacon et étiqueté | la régression logistique, prête à prédire |

Deux distinctions à bien faire :

- **Paramètre ou métrique ?** Un paramètre est un **choix** (on le décide), une métrique est une **mesure** (on la constate). Un paramètre ne change plus une fois le run lancé ; une métrique peut être notée plusieurs fois, par exemple à chaque époque d'un entraînement.
- **Depuis MLflow 3, le modèle est un objet à part entière** (*LoggedModel*), avec son propre identifiant, relié au run qui l'a produit. On peut ainsi retrouver un modèle, ses métriques et son origine, même quand plusieurs modèles naissent d'un même run.

{#architecture}
## Où vont les informations ?

Votre notebook ne range rien lui-même. Il **envoie** chaque information au **serveur MLflow** (le service `mlflow` démarré ce matin), qui la répartit dans deux magasins :

| Magasin | Ce qu'il garde | Ici, sur votre VM | En entreprise |
|---|---|---|---|
| **Base de suivi** (*backend store*) | Expériences, runs, paramètres, métriques, tags : des petites valeurs | Une base SQLite, `.mlflow/mlflow.db` | PostgreSQL ou MySQL |
| **Magasin d'artefacts** (*artifact store*) | Les fichiers : modèles, graphiques, rapports | Le dossier `.mlflow/artifacts` | Azure Blob Storage, S3, Google Cloud Storage |

Le serveur sert aussi l'interface web que vous avez ouverte sur http://localhost:5000. Le code qui envoie les informations s'appelle le **client** : il connaît l'adresse du serveur grâce à la variable `MLFLOW_TRACKING_URI`, vérifiée en début de matinée.

{#premier-run}
## Enregistrer ses premiers runs

:::: lab Démo | Le cahier de laboratoire de la matinée | 10 min
On reprend la ligne de base et le premier modèle de la notion précédente, et on les note dans une expérience `j2-demo-suivi`.

**1. Un run pour la ligne de base.** `set_experiment` choisit l'expérience, et la crée si elle n'existe pas. `start_run` ouvre une page du cahier ; le bloc `with` la referme automatiquement à la fin, même en cas d'erreur.

```python title="Cellule 7 : le run de la ligne de base"
import mlflow

mlflow.set_experiment("j2-demo-suivi")

with mlflow.start_run(run_name="ligne-de-base"):
    mlflow.log_param("modele", "toujours a l'heure")
    mlflow.log_metric("exactitude", round(accuracy_score(test[CIBLE], toujours_a_l_heure), 3))
    mlflow.log_metric("rappel", round(recall_score(test[CIBLE], toujours_a_l_heure), 3))
```

```plaintext title="Sortie attendue"
🏃 View run ligne-de-base at: http://mlflow:5000/#/experiments/1/runs/<id>
🧪 View experiment at: http://mlflow:5000/#/experiments/1
```

À la fermeture du run, MLflow affiche deux liens : celui du run et celui de l'expérience. `<id>` est l'**identifiant du run** : 32 caractères, différents chez chacun. Les liens utilisent l'adresse `mlflow:5000`, celle que voit JupyterLab ; dans le navigateur de la VM, remplacez `mlflow` par `localhost`.

**2. Un run pour le modèle, avec un artefact et le modèle lui-même.** `log_params` et `log_metrics` notent plusieurs valeurs d'un coup ; `log_text` enregistre un texte comme fichier du run ; `log_model` enregistre le modèle dans le format standard de MLflow, avec un exemple d'entrée.

```python title="Cellule 8 : le run du modèle"
from mlflow import sklearn as mlflow_sklearn

with mlflow.start_run(run_name="regression-logistique"):
    mlflow.log_params({"C": 1.0, "class_weight": None, "max_iter": 1000})
    mlflow.log_metrics({
        "exactitude": round(accuracy_score(test[CIBLE], predictions), 3),
        "precision": round(precision_score(test[CIBLE], predictions), 3),
        "rappel": round(recall_score(test[CIBLE], predictions), 3),
        "f1": round(f1_score(test[CIBLE], predictions), 3),
    })
    matrice = pd.crosstab(test[CIBLE], predictions, rownames=["réel"], colnames=["prédit"])
    mlflow.log_text(matrice.to_string(), "matrice_confusion.txt")
    mlflow_sklearn.log_model(modele, name="model", input_example=train[X_COLS].head(2))
```

```plaintext title="Sortie attendue"
🏃 View run regression-logistique at: http://mlflow:5000/#/experiments/1/runs/<id>
🧪 View experiment at: http://mlflow:5000/#/experiments/1
```

On importe le module sous le nom `mlflow_sklearn` (et non `import mlflow.sklearn`) : c'est la même chose, mais cette forme évite une erreur sournoise quand l'import est écrit à l'intérieur d'une fonction.

**3. Regardez dans l'interface.** Sur http://localhost:5000, ouvrez l'expérience `j2-demo-suivi` : deux runs. Cliquez sur `regression-logistique` : paramètres, métriques, puis l'onglet des artefacts avec `matrice_confusion.txt`. Le modèle apparaît aussi dans la partie **Models** de l'expérience, relié à ce run. Cochez les deux runs, puis cliquez sur **Compare** : MLflow aligne leurs paramètres et leurs métriques.

**4. Comparer depuis le code.** `search_runs` renvoie un tableau pandas, une ligne par run ; les colonnes s'appellent `params.…`, `metrics.…` et `tags.…`.

```python title="Cellule 9 : comparer les runs"
runs = mlflow.search_runs(experiment_names=["j2-demo-suivi"], order_by=["metrics.rappel DESC"])
print(runs[["tags.mlflow.runName", "metrics.exactitude", "metrics.rappel"]].to_string(index=False))
```

```plaintext title="Sortie attendue"
  tags.mlflow.runName  metrics.exactitude  metrics.rappel
regression-logistique               0.897           0.591
        ligne-de-base               0.831           0.000
```

Le nom du run est un tag réservé, `mlflow.runName`, que MLflow pose lui-même. Le tableau confirme ce qu'on a dit de la ligne de base : la meilleure exactitude n'est pas loin, mais le rappel est nul.

::: hint
`MlflowException` ou erreur de connexion : le serveur MLflow ne tourne pas (`docker compose ps` dans le terminal de la VM). Le tableau a plus de deux lignes : vous avez exécuté une cellule plusieurs fois, et chaque exécution crée un run ; c'est normal, on peut supprimer les runs en trop depuis l'interface. Des messages en rouge s'affichent sous les cellules : ce sont des informations, pas des erreurs. `Experiment with name 'j2-demo-suivi' does not exist. Creating a new experiment.` annonce la création de l'expérience ; l'avertissement `Hint: Inferred schema contains integer column(s)` rappelle qu'une colonne d'entiers (ici `distance_km` et `delai_promis_h`) ne pourra pas recevoir de valeur manquante en prédiction. Nos données n'en ont pas.
:::
::::

{#triangle}
## Relier le modèle à son code et à ses données

**Pourquoi ?** Un modèle n'est reproductible que si l'on connaît **trois** choses : le **code** qui l'a produit, les **données** sur lesquelles il a appris, et ses **réglages**. C'est le triangle du versioning :

| Sommet | Qui le garde | La trace à noter dans le run |
|---|---|---|
| Le code | Git | Le commit (`git rev-parse --short HEAD`) |
| Les données | DVC | L'empreinte MD5 du fichier, lue dans son ticket `.dvc` |
| Les réglages et le modèle | MLflow | Les paramètres, et le modèle lui-même |

Dans le pipeline du dépôt, c'est le rôle de `pipeline/suivi.py`. Au début de chaque entraînement, il ouvre un run et y note les trois sommets :

```python title="pipeline/suivi.py (extrait)"
def demarrer_entrainement(params: dict) -> None:
    """Ouvre un run MLflow, y note les paramètres, le commit Git et l'empreinte des données."""
    if not actif():
        FICHIER_RUN.parent.mkdir(parents=True, exist_ok=True)
        FICHIER_RUN.write_text("local")
        return
    mlflow.set_experiment(EXPERIENCE)
    run = mlflow.start_run(run_name=f"train-C{params.get('C')}")
    mlflow.log_params(params)
    mlflow.set_tags({"commit_git": _commit_git(), "md5_donnees": _empreinte_donnees()})
    FICHIER_RUN.parent.mkdir(parents=True, exist_ok=True)
    FICHIER_RUN.write_text(run.info.run_id)
```

Avec ces deux tags, on peut répondre en une minute à un auditeur qui demande « d'où vient ce modèle ? » : `git checkout <commit>`, puis `dvc checkout`, et l'on retrouve exactement le code et les données. C'est ce que vous ferez dans le TP.

::: callout info Et dans Azure ou Fabric ?
**Azure Machine Learning** et **Microsoft Fabric** utilisent MLflow comme format de suivi. Dans un notebook Fabric, `mlflow` est déjà configuré : `set_experiment`, `start_run`, `log_metric` créent directement une **expérience ML** dans votre espace de travail. Avec Azure ML, on donne au client l'adresse de suivi de l'espace de travail, et le même code fonctionne. Côté Google Cloud, Vertex AI a son propre outil de suivi (Vertex AI Experiments) ; on y garde MLflow en hébergeant soi-même son serveur.
:::

::: callout info Et les agents IA ?
MLflow 3 ne suit plus seulement des modèles classiques. Il sait aussi **tracer** les applications construites sur de grands modèles de langage, agents compris : chaque appel au LLM, chaque outil utilisé, chaque réponse, avec sa durée et son coût. Même idée que ce matin, appliquée à un agent : sans trace, impossible de comprendre pourquoi il a répondu ce qu'il a répondu. On y revient au jour 5.
:::

{#avance}
## Pour aller plus loin : un serveur MLflow en entreprise

Ce bloc est pour les profils avancés ; rien ici n'est exigé dans l'évaluation.

**Le serveur de la VM est volontairement minimal.** SQLite ne supporte pas bien les écritures simultanées de plusieurs utilisateurs, et les artefacts restent sur un disque local. En entreprise, on sépare : une base PostgreSQL managée pour la base de suivi, un stockage objet (Azure Blob, S3) pour les artefacts, et le serveur lui-même derrière un proxy qui gère l'authentification.

**Le serveur sert d'intermédiaire pour les fichiers.** Avec l'option `--artifacts-destination` (celle du `docker-compose.yml`), le client n'écrit jamais directement dans le stockage : il envoie les fichiers au serveur, qui les range. Avantage : les postes des data scientists n'ont besoin d'aucun accès direct au compte de stockage, seulement d'un accès au serveur.

**La sécurité, sans raccourci.** Trois points à connaître :

- **Par défaut, MLflow n'a pas d'authentification.** Quiconque atteint le port peut lire et modifier toutes les expériences. Sur la VM, le port n'est ouvert que sur la machine elle-même (`127.0.0.1`). En entreprise : un proxy d'authentification devant le serveur, ou l'application d'authentification intégrée (`mlflow server --app-name basic-auth`), ou un service managé.
- **Les noms d'hôtes autorisés.** Depuis les versions 3.x récentes, le serveur refuse les requêtes adressées à un nom d'hôte qu'il ne connaît pas, pour se protéger d'une attaque appelée *DNS rebinding*. Par défaut, il n'accepte que `localhost` et les adresses IP privées. C'est pourquoi le `docker-compose.yml` du dépôt déclare `MLFLOW_SERVER_ALLOWED_HOSTS` avec le nom du service, `mlflow:5000`. Sans cette ligne, JupyterLab recevrait un refus.
- **Les mises à jour comptent.** En août 2026, une faille de MLflow (CVE-2026-64849) a été exploitée pour voler des identifiants cloud : un point d'accès de test des webhooks, accessible sans authentification, permettait de faire envoyer par le serveur des requêtes vers l'adresse interne des métadonnées du cloud. Elle touchait les versions antérieures à 3.15.0. L'image des TP utilise MLflow 3.17.0. Leçon générale : un serveur MLflow exposé sur Internet et non mis à jour est une porte d'entrée vers tout le compte cloud.

**L'enregistrement automatique** (*autolog*). `mlflow.sklearn.autolog()` note automatiquement les paramètres, les métriques d'entraînement et le modèle de chaque appel à `fit`. Pratique pour explorer ; dans un pipeline de production, on préfère souvent noter explicitement ce qui compte, pour garder des runs lisibles et des noms de métriques stables d'une version à l'autre.

{#quiz}
## Quiz de validation

```quiz
- q: Quelle est la différence entre un paramètre et une métrique ?
  options:
    - Aucune, ce sont deux noms pour la même chose
    - Un paramètre est un réglage choisi avant le run, une métrique est une mesure constatée pendant ou après
    - Un paramètre est un nombre, une métrique est un texte
    - Une métrique est fixée avant le run, un paramètre après
  answer: 1
  explain: C ou class_weight sont des paramètres ; le rappel ou le F1 sont des métriques.
- q: Où MLflow range-t-il le fichier du modèle ?
  options:
    - Dans la base de suivi, avec les métriques
    - Dans le magasin d'artefacts
    - Dans le dépôt Git
    - Dans le notebook
  answer: 1
  explain: La base de suivi garde les petites valeurs ; les fichiers vont dans le magasin d'artefacts.
- q: Quelles traces permettent de relier un modèle au code et aux données qui l'ont produit ?
  options:
    - Le nom du run et sa date
    - Le commit Git et l'empreinte MD5 des données, notés comme tags du run
    - La taille du fichier du modèle
    - Le nom de l'expérience
  answer: 1
  explain: Avec le commit et l'empreinte, git checkout puis dvc checkout redonnent exactement le code et les données.
- q: Le même code de suivi peut-il servir avec Azure Machine Learning ?
  options:
    - Non, il faut tout réécrire avec le SDK Azure
    - Oui, Azure ML utilise MLflow pour le suivi, seule l'adresse du serveur change
    - Seulement pour les modèles de deep learning
    - Seulement depuis Microsoft Fabric
  answer: 1
  explain: C'est l'un des intérêts de MLflow - le suivi ne dépend pas d'un fournisseur.
```
