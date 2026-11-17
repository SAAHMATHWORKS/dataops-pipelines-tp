---
subtitle: >-
  Le pipeline du jour 2 devient un DAG de six tâches. Il contrôle le contrat de données, rejoue les
  étapes DVC, applique la charte de qualité, et propose un challenger au registre sans jamais créer
  de doublon. Puis on le malmène : un serveur MLflow arrêté en pleine exécution, un fichier de
  données corrompu. Le premier incident se répare seul ; le second arrête tout, comme il se doit.
objectives:
  - Transformer les étapes d'un pipeline DVC en tâches Airflow, avec leurs dépendances
  - Placer un contrôle du contrat de données en tête de pipeline, sans nouvelle tentative
  - Écrire une barrière de qualité qui saute les tâches suivantes quand la charte n'est pas respectée
  - Vérifier qu'une tâche est idempotente en la relançant
  - Observer une panne passagère réparée par les nouvelles tentatives, et une erreur de données qui arrête le pipeline
---

{#objectif}
## Ce qu'on construit

```plaintext title="Le DAG colisvert_pipeline"
controler_donnees >> preparer >> entrainer >> evaluer >> barriere_qualite >> proposer_challenger
```

| Tâche | Type | Ce qu'elle fait | Règle de robustesse |
|---|---|---|---|
| `controler_donnees` | `@task.bash` | Le contrat de données du jour 1 (`python -m pipeline.controle`) | Échouer tôt ; **aucune** nouvelle tentative |
| `preparer`, `entrainer`, `evaluer` | `@task.bash` | `dvc repro --single-item <étape>` : DVC saute l'étape si rien n'a changé | Idempotence ; deux nouvelles tentatives |
| `barriere_qualite` | `@task.short_circuit` | Lit `metrics.json` et applique la charte : rappel ≥ 0,80 **et** précision ≥ 0,50 | Si la condition est fausse, les tâches suivantes sont **sautées**, pas en échec |
| `proposer_challenger` | `@task.bash` | `python -m pipeline.registre` : enregistre le modèle et pose l'alias `challenger` | Idempotent : jamais deux versions pour le même entraînement |

Deux scripts ont été ajoutés au dépôt pour ce TP (vous les avez reçus avec `git pull`) : `pipeline/controle.py`, qui est le contrat exécutable de la Cellule bonus C du jour 1, et `pipeline/registre.py`, dont voici le cœur :

```python title="pipeline/registre.py (extrait)"
def main() -> None:
    run_id = FICHIER_RUN.read_text().strip()
    client = MlflowClient()
    deja = [v for v in client.search_model_versions(f"run_id = '{run_id}'") if v.name == NOM]
    if deja:
        version = max(int(v.version) for v in deja)
        print(f"ce run d'entraînement est déjà enregistré (version {version}) : aucune nouvelle version")
    else:
        version = int(mlflow.register_model(f"runs:/{run_id}/model", NOM, tags={"source": "airflow"}).version)
        print(f"nouvelle version enregistrée : {version}")
    client.set_registered_model_alias(NOM, ALIAS, str(version))
    print(f"alias {ALIAS} -> version {version}")
```

**Pourquoi ce test « déjà enregistré » ?** Sans lui, chaque nouvelle tentative, chaque relance manuelle, chaque exécution du matin où rien n'a changé créerait une version de plus du **même** modèle. Au bout d'un mois, trente versions identiques dans le registre, et plus personne ne sait laquelle compte.

{#etape1}
## Étape 1 : écrire le DAG et le tester

:::: lab Étape 1 | Le DAG du pipeline, état du jour 2 | 12 min
**1. Dans JupyterLab, créez le fichier `dags/colisvert_pipeline.py`** (menu **File > New > Python File**, puis renommez-le) avec ce contenu. Lisez-le en l'écrivant : chaque ligne correspond à une règle du tableau.

```python title="dags/colisvert_pipeline.py"
"""Le pipeline ColisVert du jour 2, orchestré et rendu robuste (TP 1 du jour 3)."""

from __future__ import annotations

import json
from datetime import datetime, timedelta

from airflow.sdk import CronTriggerTimetable, dag, task

PROJET = "/home/lab/projet"
SEUILS = {"rappel": 0.80, "precision": 0.50}   # la charte du jour 2


@dag(
    dag_id="colisvert_pipeline",
    schedule=CronTriggerTimetable("45 6 * * *", timezone="Europe/Paris"),   # chaque jour à 06:45
    start_date=datetime(2026, 9, 7),          # premier jour des données ColisVert
    catchup=False,               # au premier démarrage, ne pas rejouer les jours passés
    max_active_runs=1,           # deux entraînements en même temps se marcheraient dessus
    default_args={
        "retries": 2,                                  # deux nouvelles tentatives…
        "retry_delay": timedelta(seconds=20),          # …espacées de 20 secondes
        "execution_timeout": timedelta(minutes=10),    # une tâche bloquée est arrêtée
    },
    tags=["colisvert", "jour3"],
)
def colisvert_pipeline():
    @task.bash(retries=0)
    def controler_donnees() -> str:
        return f"cd {PROJET} && python -m pipeline.controle data/livraisons.csv"

    @task.bash
    def preparer() -> str:
        return f"cd {PROJET} && dvc repro --single-item prepare"

    @task.bash
    def entrainer() -> str:
        return f"cd {PROJET} && dvc repro --single-item train"

    @task.bash
    def evaluer() -> str:
        return f"cd {PROJET} && dvc repro --single-item evaluate && cat metrics.json"

    @task.short_circuit
    def barriere_qualite() -> bool:
        with open(f"{PROJET}/metrics.json", encoding="utf-8") as fichier:
            metriques = json.load(fichier)
        for nom, seuil in SEUILS.items():
            print(f"{nom} : {metriques[nom]:.3f} (seuil {seuil:.2f})")
        franchie = all(metriques[nom] >= seuil for nom, seuil in SEUILS.items())
        print("barrière franchie" if franchie else "barrière fermée : pas de challenger")
        return franchie

    @task.bash
    def proposer_challenger() -> str:
        return f"cd {PROJET} && python -m pipeline.registre"

    (controler_donnees() >> preparer() >> entrainer() >> evaluer()
     >> barriere_qualite() >> proposer_challenger())


colisvert_pipeline()
```

**2. Vérifiez que le DAG se charge, puis testez-le.** Dans un terminal de la VM :

```bash title="Terminal de la VM"
cd ~/dataops-pipelines-tp
docker compose exec airflow airflow dags list-import-errors
./scripts/tester-dag.sh colisvert_pipeline
```

`list-import-errors` doit répondre `No data found`. Le script `tester-dag.sh` lance `airflow dags test` (toutes les tâches, tout de suite, sans l'ordonnanceur) et **résume** sa sortie, qui fait sinon plusieurs centaines de lignes : chaque tâche (▶), ce qu'elle écrit (│), ce qu'elle renvoie (→), puis l'état final de chaque tâche.

```plaintext title="Sortie attendue"
▶ controler_donnees
  │ data/livraisons.csv : 5035 lignes de données
  │         colonne              regle  violations
  │        id_colis             unique           0
  │        entrepot valeurs autorisées           0
  │ date_expedition             format           0
  │        poids_kg        obligatoire           0
  │           meteo        obligatoire           0
  │    delai_reel_h            minimum           0
  │ Contrat respecté : le pipeline peut continuer.
▶ preparer
  │ Stage 'prepare' didn't change, skipping
  │ Data and pipelines are up to date.
▶ entrainer
  │ Stage 'train' didn't change, skipping
  │ Data and pipelines are up to date.
▶ evaluer
  │ Stage 'evaluate' didn't change, skipping
  │ Data and pipelines are up to date.
  │ {
  │   "exactitude": 0.897,
  │   "precision": 0.745,
  │   "rappel": 0.591,
  │   "f1": 0.66,
  │   "roc_auc": 0.949
  │ }
▶ barriere_qualite
  │ rappel : 0.591 (seuil 0.80)
  │ precision : 0.745 (seuil 0.50)
  │ barrière fermée : pas de challenger
  → renvoie False
  ⏭ condition fausse : les tâches suivantes sont sautées
exécution success ; état des tâches :
  controler_donnees      success
  preparer               success
  entrainer              success
  evaluer                success
  barriere_qualite       success
  proposer_challenger    skipped
```

**3. Lisez ce résultat.**

- Les trois étapes DVC répondent `didn't change, skipping` : depuis hier, ni les données, ni le code, ni les paramètres n'ont bougé. Les tâches **réussissent** sans travail inutile.
- La barrière lit les métriques de `params.yaml` d'hier (`C: 1.0`, pas de pondération) : le rappel de 0,591 est sous le seuil. Elle renvoie `False`.
- `proposer_challenger` est `skipped` (sautée), et l'exécution est un **succès**. C'est voulu : un modèle insuffisant n'est pas une panne du pipeline, c'est un résultat. Une panne rendrait l'exécution rouge et réveillerait l'astreinte pour rien.

**4. Regardez dans l'interface** (http://localhost:8080, DAG `colisvert_pipeline`, onglet **Graph**) : cinq tâches vertes, la dernière en rose (*skipped*).

::: hint
`list-import-errors` affiche une erreur : lisez la dernière ligne de la trace, elle donne le fichier et la ligne (souvent une indentation ou un import). `Dag 'colisvert_pipeline' could not be found` : le fichier n'est pas dans `dags/`, ou il ne se termine pas par `colisvert_pipeline()`. Un test qui réussit en une fraction de seconde sans afficher de tâche : vérifiez que `start_date` est dans le passé.
:::
::::

{#etape2}
## Étape 2 : le réglage gagnant du jour 2

:::: lab Étape 2 | Franchir la barrière | 8 min
**1. Hier, la recherche d'hyperparamètres a retenu `C = 0.1` avec `class_weight: balanced`.** Reportez ce réglage dans `params.yaml`, section `train` :

```yaml title="params.yaml"
prepare:
  date_coupure: "2026-10-19"

train:
  C: 0.1
  class_weight: balanced
  max_iter: 1000
```

**2. Relancez le test :**

```bash title="Terminal de la VM"
./scripts/tester-dag.sh colisvert_pipeline
```

```plaintext title="Sortie attendue (extrait : les trois dernières tâches et le bilan)"
▶ entrainer
  │ Running stage 'train':
  │ > python -m pipeline.train
  │ 🏃 View run train-C0.1 at: http://mlflow:5000/#/experiments/2/runs/…
  │ 🧪 View experiment at: http://mlflow:5000/#/experiments/2
  │ modèle entraîné sur 3805 colis, 21 variables après encodage
  │ F1 sur le train : 0.692
  │ modèle écrit dans models/modele.joblib
  │ Updating lock file 'dvc.lock'
▶ evaluer
  │ Running stage 'evaluate':
  │ > python -m pipeline.evaluate
  │ évaluation sur 1230 colis de test
  │ exactitude : 0.863
  │ precision  : 0.561
  │ rappel     : 0.880
  │ f1         : 0.685
  │ roc_auc    : 0.948
  │ Updating lock file 'dvc.lock'
  │ …
▶ barriere_qualite
  │ rappel : 0.880 (seuil 0.80)
  │ precision : 0.561 (seuil 0.50)
  │ barrière franchie
  → renvoie True
▶ proposer_challenger
  │ Registered model 'colisvert-retards' already exists. Creating a new version of this model...
  │ WARNING mlflow.tracking._model_registry.fluent: Run with id … has no artifacts at artifact path 'model', registering model based on models:/m-… instead
  │ INFO mlflow.store.model_registry.abstract_store: Waiting up to 300 seconds for model version to finish creation. Model name: colisvert-retards, version 4
  │ Created version '4' of model 'colisvert-retards'.
  │ nouvelle version enregistrée : 4
  │ alias challenger -> version 4
exécution success ; état des tâches :
  controler_donnees      success
  preparer               success
  entrainer              success
  evaluer                success
  barriere_qualite       success
  proposer_challenger    success
```

- `preparer` saute son étape (les données n'ont pas changé), `entrainer` et `evaluer` la rejouent (les paramètres ont changé) : DVC ne refait que ce qui doit l'être.
- Les métriques sont **exactement** celles du projet MLflow d'hier avec le même réglage (0,880 de rappel, 0,561 de précision) : même code, mêmes données, mêmes bibliothèques.
- La barrière laisse passer ; le modèle est enregistré et reçoit l'alias `challenger`. Le numéro de version dépend de ce que contient votre registre depuis hier : 4 chez le formateur, qui a enregistré trois versions au jour 2. MLflow affiche un avertissement sur l'emplacement du modèle (`registering model based on models:/m-… instead`) : c'est le comportement normal de MLflow 3, déjà vu hier.

**3. Champion ou challenger ?** Le pipeline a **proposé** ; décider reste à vous, avec la règle de promotion du jour 2 (critère de succès atteint, et F1 supérieur d'au moins 0,01 à celui du champion). Dans le notebook `j3-apres-midi.ipynb` :

```python title="Cellule 2 : le challenger proposé par Airflow face au champion"
from mlflow import MlflowClient

client = MlflowClient()
NOM = "colisvert-retards"
for alias in ["champion", "challenger"]:
    version = client.get_model_version_by_alias(NOM, alias)
    m = client.get_run(version.run_id).data.metrics
    source = version.tags.get("source", "notebook")
    print(f"{alias:<10} v{version.version} ({source}) : rappel {m['rappel']}, précision {m['precision']}, f1 {m['f1']}")
```

```plaintext title="Sortie attendue (vos numéros de version peuvent différer)"
champion   v2 (notebook) : rappel 0.88, précision 0.561, f1 0.685
challenger v4 (airflow) : rappel 0.88, précision 0.561, f1 0.685
```

Même réglage, mêmes données : le challenger est **le même modèle** que le champion, à un F1 identique. La règle ne le promeut pas, et c'est exactement ce qu'on attend d'elle. L'alias `champion` ne bouge pas.
::::

{#etape3}
## Étape 3 : relancer sans rien changer

:::: lab Étape 3 | L'idempotence, vérifiée | 4 min
Relancez le test une troisième fois, sans rien modifier :

```bash title="Terminal de la VM"
./scripts/tester-dag.sh colisvert_pipeline
```

```plaintext title="Sortie attendue (extrait)"
▶ preparer
  │ Stage 'prepare' didn't change, skipping
  │ Data and pipelines are up to date.
▶ entrainer
  │ Stage 'train' didn't change, skipping
  │ Data and pipelines are up to date.
▶ evaluer
  │ Stage 'evaluate' didn't change, skipping
  │ …
▶ barriere_qualite
  │ …
  │ barrière franchie
  → renvoie True
▶ proposer_challenger
  │ ce run d'entraînement est déjà enregistré (version 4) : aucune nouvelle version
  │ alias challenger -> version 4
```

Trois étapes sautées par DVC, et **aucune nouvelle version** dans le registre : relancer le pipeline ne change rien quand rien n'a changé. C'est la garantie qui permet de le relancer sans réfléchir, après une panne ou un doute.
::::

{#etape4}
## Étape 4 : une panne passagère

:::: lab Étape 4 | Arrêter MLflow en pleine exécution | 10 min
Jusqu'ici, `tester-dag.sh` exécutait le DAG à la main. Passons par l'**ordonnanceur**, comme en production : c'est lui qui gère les nouvelles tentatives.

**1. Activez le DAG.** Dans l'interface, sur la ligne de `colisvert_pipeline`, basculez l'interrupteur à gauche du nom. Ou, dans le terminal de la VM :

```bash title="Terminal de la VM"
docker compose exec airflow airflow dags unpause colisvert_pipeline
```

Une exécution démarre **aussitôt**, marquée *scheduled* et datée de ce matin 06:45. Avec `catchup=False`, Airflow ne rattrape pas tout le passé, mais il lance **la dernière** occurrence manquée. Elle réussit (rien n'a changé).

**2. Provoquez la panne,** puis déclenchez une exécution :

```bash title="Terminal de la VM"
docker compose stop mlflow
docker compose exec airflow airflow dags trigger colisvert_pipeline
```

**3. Observez dans l'interface** (vue **Grid** du DAG, rafraîchissez) : les cinq premières tâches passent au vert, puis `proposer_challenger` passe en **orange** (*up_for_retry*) : elle a échoué, et attend sa nouvelle tentative, 20 secondes plus tard.

**4. Pendant ces 20 secondes, réparez :**

```bash title="Terminal de la VM"
docker compose start mlflow
```

**5. Constatez :** `proposer_challenger` repasse en vert, et l'exécution est un succès. Cliquez sur la tâche, onglet **Logs** : la liste déroulante des tentatives en montre **deux**.

```plaintext title="Journal de la tentative 1 (extrait)"
Running command: ['/usr/bin/bash', '-c', 'cd /home/lab/projet && python -m pipeline.registre']
…
mlflow.exceptions.MlflowException: API request to http://mlflow:5000/api/2.0/mlflow/model-versions/search failed with exception HTTPConnectionPool(host='mlflow', port=5000): Max retries exceeded …
Command exited with return code 1
Task failed with exception
```

```plaintext title="Journal de la tentative 2"
Running command: ['/usr/bin/bash', '-c', 'cd /home/lab/projet && python -m pipeline.registre']
ce run d'entraînement est déjà enregistré (version 4) : aucune nouvelle version
alias challenger -> version 4
Command exited with return code 0
```

Personne n'a relancé le pipeline : il s'est réparé seul. Et grâce à l'idempotence, la tentative 2 n'a rien dupliqué. Si MLflow était resté arrêté, la tâche aurait échoué définitivement après la 3e tentative (1 + 2 nouvelles), et c'est **alors** qu'il faudrait alerter quelqu'un.

::: hint
Rien ne démarre après `dags trigger` : le DAG est en pause (interrupteur à gauche du nom). La tâche est déjà verte quand vous regardez : MLflow a été redémarré trop tôt, recommencez en attendant l'orange. `Connection refused` dans JupyterLab ensuite : MLflow n'est pas redémarré, `docker compose start mlflow`.
:::
::::

{#etape5}
## Étape 5 : des données corrompues

:::: lab Étape 5 | Le contrat arrête tout | 8 min
**1. Remplacez le fichier des livraisons par la version brute du jour 1,** celle qui contient des défauts de qualité, puis testez :

```bash title="Terminal de la VM"
cp data/livraisons_brutes.csv data/livraisons.csv
./scripts/tester-dag.sh colisvert_pipeline
```

```plaintext title="Sortie attendue"
▶ controler_donnees
  │ data/livraisons.csv : 5060 lignes de données
  │         colonne              regle  violations
  │        id_colis             unique          25
  │        entrepot valeurs autorisées          12
  │ date_expedition             format          20
  │        poids_kg        obligatoire          15
  │           meteo        obligatoire          40
  │    delai_reel_h            minimum           8
  │ Contrat violé (120 violations) : arrêt du pipeline.
  ✗ la commande a échoué (code 1)
  ✗ la tâche a échoué
  │ DagRun failed
exécution failed ; état des tâches :
  controler_donnees      failed
  preparer               upstream_failed
  entrainer              upstream_failed
  evaluer                upstream_failed
  barriere_qualite       upstream_failed
  proposer_challenger    upstream_failed
```

- Les six violations sont **exactement** celles du rapport de contrat du jour 1 : c'est le même contrat, devenu une tâche.
- `controler_donnees` échoue **tout de suite**, sans nouvelle tentative (`retries=0`) : réessayer ne réparerait pas un fichier faux.
- Les tâches suivantes sont `upstream_failed` : **rien** n'a été entraîné ni proposé avec ces données. Le registre est intact.

**2. Remettez les bonnes données,** dans un terminal de **JupyterLab** : DVC les a dans son cache depuis hier.

```bash title="Terminal JupyterLab"
cd /home/lab/projet
dvc checkout --force data/livraisons.csv.dvc
dvc status
```

Sans `--force`, DVC refuse : `Can't remove the following unsaved files without confirmation`. Il protège un fichier modifié qui n'est dans aucun cache ; ici, on veut justement l'écraser. `dvc status` doit ensuite répondre `Data and pipelines are up to date.`

**3. Enregistrez votre travail :**

```bash title="Terminal JupyterLab"
git add dags/colisvert_pipeline.py params.yaml dvc.lock metrics.json
git commit -m "Pipeline orchestré par Airflow, réglage C=0.1 balanced"
```

Le DAG est du code : il se versionne, se relit et se déploie comme le reste.
::::

{#bilan}
## Ce que le TP a montré

| Incident | Ce qui s'est passé | Grâce à |
|---|---|---|
| Rien n'a changé depuis hier | Tâches réussies, aucun calcul, aucune version créée | Idempotence (DVC, registre) |
| Modèle sous la charte | Pas de challenger ; exécution réussie, pas d'alerte | `@task.short_circuit` |
| Serveur MLflow arrêté | Réparé seul à la 2e tentative | `retries=2`, idempotence |
| Fichier corrompu | Arrêt immédiat, rien de publié | Contrat de données, `retries=0` |

{#quiz}
## Quiz

```quiz
- q: La barrière de qualité renvoie False. Quel est l'état de l'exécution ?
  options:
    - En échec, car le modèle est mauvais
    - Réussie ; la tâche proposer_challenger est sautée (skipped)
    - En attente d'une nouvelle tentative
    - Suspendue jusqu'à une décision humaine
  answer: 1
  explain: Un modèle insuffisant est un résultat, pas une panne. short_circuit saute les tâches suivantes sans faire échouer l'exécution.
- q: Pourquoi relancer le pipeline sans changement ne crée-t-il pas de nouvelle version du modèle ?
  options:
    - Parce que MLflow refuse les doublons
    - Parce que DVC saute l'entraînement et que pipeline/registre.py vérifie si ce run est déjà enregistré
    - Parce qu'Airflow mémorise les tâches réussies
    - Par hasard
  answer: 1
  explain: L'idempotence est construite à deux niveaux - DVC ne réentraîne pas, et l'enregistrement teste l'existence avant de créer.
- q: Pendant la panne de MLflow, quelle tâche a échoué puis réussi ?
  options:
    - entrainer
    - proposer_challenger, la seule qui parlait à MLflow ce jour-là
    - controler_donnees
    - Toutes
  answer: 1
  explain: Rien n'avait changé, donc DVC a sauté l'entraînement et l'évaluation - aucune n'a contacté MLflow. Seul l'enregistrement l'a fait.
- q: Après l'échec du contrat de données, quel est l'état de la tâche entrainer ?
  options:
    - failed
    - upstream_failed - elle n'a jamais été lancée car une tâche en amont a échoué
    - skipped
    - up_for_retry
  answer: 1
  explain: upstream_failed signale qu'une dépendance a échoué. skipped est réservé aux tâches sautées volontairement, comme par short_circuit.
```
