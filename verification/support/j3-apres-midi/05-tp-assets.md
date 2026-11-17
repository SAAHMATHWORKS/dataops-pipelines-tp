---
subtitle: >-
  Retour au problème du début : à 06:45, un jour sur sept, le fichier n'est pas encore là. On
  sépare le pipeline en deux DAG reliés par une donnée déclarée, un Asset. Le producteur reçoit le
  fichier, le contrôle et le publie ; le pipeline démarre parce que la donnée est arrivée, plus
  parce que l'horloge a sonné. L'horaire reste, mais comme filet de sécurité.
objectives:
  - Déclarer un Asset et le relier à la tâche qui le produit (outlets)
  - Planifier un DAG sur un Asset, seul ou combiné à un horaire
  - Transmettre des métadonnées avec l'événement et les lire en aval
  - Expliquer pourquoi un Asset n'est publié que si sa tâche réussit
  - Situer les déclenchements externes - capteurs, surveillance de files de messages, événements de stockage
---

{#idee}
## Producteur, consommateur, et une donnée entre les deux

**L'analogie de la boîte aux lettres.** Plutôt que d'aller voir toutes les cinq minutes si le courrier est arrivé (ou d'y aller à 06:45 en espérant), on demande au facteur de sonner. Un **Asset** est cette sonnette : une tâche déclare « j'ai mis à jour cette donnée », et tous les DAG qui attendaient cette donnée démarrent.

| Rôle | DAG | Ce qu'il fait |
|---|---|---|
| **Producteur** | `colisvert_reception` | Reçoit le fichier, vérifie le contrat, le versionne avec DVC, puis **publie** l'Asset `livraisons` |
| **Consommateur** | `colisvert_pipeline` | Démarre quand l'Asset `livraisons` est publié : prépare, entraîne, évalue, propose un challenger |

Trois propriétés rendent ce découpage robuste :

1. **Un Asset n'est publié que si sa tâche réussit.** Si le contrat échoue, la tâche `publier` ne tourne pas : aucun événement, aucun réentraînement. Les consommateurs sont protégés **par construction**.
2. **Le producteur ne connaît pas ses consommateurs.** Demain, un DAG de tableau de bord peut s'abonner à `livraisons` sans toucher au producteur.
3. **L'événement transporte des métadonnées** (`extra`) : ici le nombre de colis reçus, lisible par le consommateur.

{#code}
## Le code

**Le producteur.** Quatre tâches ; seule la dernière déclare l'Asset (`outlets`), et elle ne tourne que si les trois premières ont réussi.

```python title="dags/colisvert_reception.py"
"""Le producteur : reçoit le fichier des livraisons, le contrôle, le versionne, le publie."""

from __future__ import annotations

from datetime import datetime

from airflow.sdk import Asset, dag, task

PROJET = "/home/lab/projet"
LIVRAISONS = Asset(name="livraisons", uri="file:///home/lab/projet/data/livraisons.csv")


@dag(
    dag_id="colisvert_reception",
    schedule=None,                 # en vrai : déclenché par le dépôt du fichier (voir le support)
    start_date=datetime(2026, 9, 7),          # premier jour des données ColisVert
    catchup=False,
    params={"semaines": 9},
    tags=["colisvert", "jour3"],
)
def colisvert_reception():
    @task.bash
    def recevoir_fichier(params=None) -> str:
        return f"cd {PROJET} && python -m colisvert.reception {params['semaines']}"

    @task.bash
    def controler_contrat() -> str:
        return f"cd {PROJET} && python -m pipeline.controle data/livraisons.csv"

    @task.bash
    def versionner() -> str:
        return f"cd {PROJET} && dvc add data/livraisons.csv"

    @task(outlets=[LIVRAISONS])
    def publier(*, outlet_events=None) -> None:
        with open(f"{PROJET}/data/livraisons.csv", encoding="utf-8") as fichier:
            colis = sum(1 for _ in fichier) - 1
        outlet_events[LIVRAISONS].extra = {"colis": colis}
        print(f"Asset livraisons publié : {colis} colis")

    recevoir_fichier() >> controler_contrat() >> versionner() >> publier()


colisvert_reception()
```

Trois nouveautés :

- `Asset(name=..., uri=...)` : la donnée déclarée. Le **nom** l'identifie dans Airflow ; l'**URI** dit où elle est. Airflow ne lit pas le fichier : l'Asset est une **promesse**, publiée par la tâche qui l'a produit.
- `@task(outlets=[LIVRAISONS])` : quand cette tâche réussit, Airflow enregistre un **événement** sur l'Asset.
- `outlet_events[LIVRAISONS].extra = {...}` : des métadonnées jointes à l'événement. Ici, le nombre de colis ; en production, une empreinte, une période, le nom du fichier source.

Le paramètre `semaines` simule l'arrivée d'une nouvelle semaine d'expéditions : le script `colisvert.reception` régénère le fichier avec le nombre de semaines demandé (le générateur ColisVert, graine 2026 : les mêmes données pour tous).

**Le consommateur.** Le DAG du TP 1 change en trois endroits : l'import, la déclaration de l'Asset (identique à celle du producteur), et la planification ; plus une première tâche qui affiche l'origine de l'exécution.

```python title="dags/colisvert_pipeline.py (les modifications)"
from airflow.sdk import Asset, AssetOrTimeSchedule, CronTriggerTimetable, dag, task

LIVRAISONS = Asset(name="livraisons", uri="file:///home/lab/projet/data/livraisons.csv")


@dag(
    dag_id="colisvert_pipeline",
    schedule=AssetOrTimeSchedule(
        timetable=CronTriggerTimetable("45 6 * * *", timezone="Europe/Paris"),   # filet de sécurité
        assets=LIVRAISONS,                                                       # ou dès l'arrivée
    ),
    # … le reste des réglages ne change pas …
)
def colisvert_pipeline():
    @task
    def origine(*, triggering_asset_events=None) -> None:
        evenements = [e for liste in (triggering_asset_events or {}).values() for e in liste]
        if not evenements:
            print("déclenché par l'horaire ou à la main")
        for evenement in evenements:
            print(f"déclenché par l'Asset {evenement.asset.name}, publié par "
                  f"{evenement.source_dag_id} : {evenement.extra}")

    # … les six tâches du TP 1 ne changent pas …

    (origine() >> controler_donnees() >> preparer() >> entrainer() >> evaluer()
     >> barriere_qualite() >> proposer_challenger())
```

| Planification | Démarre quand… |
|---|---|
| `schedule=LIVRAISONS` | l'Asset est publié, et seulement alors |
| `schedule=(A & B)` | A **et** B ont été publiés depuis la dernière exécution |
| `schedule=(A \| B)` | A **ou** B est publié |
| `AssetOrTimeSchedule(timetable=..., assets=...)` | l'Asset est publié, **et aussi** à chaque horaire : le filet de sécurité si le producteur se tait |
| `AssetAndTimeSchedule(...)` (nouveau dans Airflow 3.4) | à l'horaire, **à condition que** l'Asset ait été publié depuis la dernière exécution ; sinon, l'exécution attend l'Asset |

::: callout info Ce qui a changé dans Airflow 3.4
Si le producteur publie trois fois pendant qu'une exécution du consommateur tourne, Airflow 3.4 crée désormais **une exécution par événement** (auparavant, les événements étaient regroupés en une seule). Pour revenir au regroupement, on passe `batch_asset_events=True` à la planification. Avec `max_active_runs=1`, les exécutions en surnombre attendent leur tour.
:::

{#tp}
## TP

:::: lab TP 2 | Le pipeline démarre quand les données arrivent | 22 min
**1. Créez le producteur** `dags/colisvert_reception.py` (le code ci-dessus), et **modifiez** `dags/colisvert_pipeline.py` comme indiqué. Corrigés en cas de blocage : `solutions/airflow/tp2/`.

**2. Vérifiez**, dans le terminal de la VM :

```bash title="Terminal de la VM"
docker compose exec airflow airflow dags list-import-errors
docker compose exec airflow airflow assets list
```

```plaintext title="Sortie attendue (assets list)"
name       | uri                                         | group | extra
===========+=============================================+=======+======
livraisons | file:///home/lab/projet/data/livraisons.csv | asset | {}
```

Dans l'interface, le menu **Assets** montre `livraisons` et le graphe qui relie le producteur au consommateur.

**3. Activez le producteur** (le consommateur l'est depuis le TP 1), puis faites « arriver » la 9e semaine :

```bash title="Terminal de la VM"
docker compose exec airflow airflow dags unpause colisvert_reception
docker compose exec airflow airflow dags trigger colisvert_reception
```

**4. Observez, sans rien toucher.** `colisvert_reception` passe au vert (environ 5 secondes), puis **`colisvert_pipeline` démarre tout seul**. Dans sa liste d'exécutions, le type de celle-ci est *asset triggered* (icône d'Asset), et non *manual* ou *scheduled*. Ouvrez les journaux de ses tâches :

```plaintext title="Journaux (extraits), dans l'ordre des tâches"
origine
  déclenché par l'Asset livraisons, publié par colisvert_reception : {'colis': 5627}
controler_donnees
  data/livraisons.csv : 5627 lignes de données
  …
  Contrat respecté : le pipeline peut continuer.
preparer
  train : 3805 colis, du 2026-09-07 au 2026-10-18
  test  : 1822 colis, du 2026-10-19 au 2026-11-08
  taux de retard train : 17.2% | test : 16.6%
entrainer
  modèle entraîné sur 3805 colis, 21 variables après encodage
  F1 sur le train : 0.692
evaluer
  évaluation sur 1822 colis de test
  exactitude : 0.862
  precision  : 0.553
  rappel     : 0.894
  f1         : 0.683
  roc_auc    : 0.951
barriere_qualite
  rappel : 0.894 (seuil 0.80)
  precision : 0.553 (seuil 0.50)
  barrière franchie
proposer_challenger
  nouvelle version enregistrée : 5
  alias challenger -> version 5
```

- `origine` lit les métadonnées de l'événement : 5 627 colis, publiés par `colisvert_reception`.
- Le contrat est vérifié une seconde fois : la défense en profondeur coûte une demi-seconde.
- Les données ont changé : DVC rejoue les trois étapes, et une **nouvelle** version devient challenger.
- **Mais lisez `preparer` et `entrainer`.** Le train compte toujours 3 805 colis, jusqu'au 18 octobre : la date de coupure de `params.yaml` est **fixe**, et toute la nouvelle semaine est partie dans le jeu de **test** (1 822 colis au lieu de 1 230). Le modèle a appris exactement les mêmes données qu'hier : c'est **le même modèle**, seule son évaluation a changé.

**5. Faut-il le promouvoir ?** La règle du jour 2 compare les F1 :

```python title="Cellule 4 : le challenger de la 9e semaine"
from mlflow import MlflowClient

client = MlflowClient()           # déjà fait à la Cellule 2 ; utile si le noyau a redémarré
NOM = "colisvert-retards"
for alias in ["champion", "challenger"]:
    version = client.get_model_version_by_alias(NOM, alias)
    run = client.get_run(version.run_id)
    m = run.data.metrics
    print(f"{alias:<10} v{version.version} : f1 {m['f1']}, rappel {m['rappel']}, "
          f"données {run.data.tags['md5_donnees'][:8]}")
```

```plaintext title="Sortie attendue (vos numéros de version peuvent différer)"
champion   v2 : f1 0.685, rappel 0.88, données 127f20d4
challenger v5 : f1 0.683, rappel 0.894, données 71d9f04a
```

Le F1 « baisse » de 0,685 à 0,683 alors que le modèle n'a pas changé : seul le jeu de test a changé (l'empreinte des données diffère). Deux leçons :

1. **Deux métriques ne se comparent que sur le même jeu de test.** Une règle de promotion automatique doit réévaluer le champion sur les nouvelles données avant de comparer.
2. **Un pipeline de réentraînement doit faire glisser sa fenêtre.** Avec une date de coupure figée, réentraîner chaque matin n'apprend rien de nouveau. Il faut la calculer à partir des données reçues (par exemple : les trois dernières semaines pour le test, tout ce qui précède pour l'entraînement), ou la recevoir de l'orchestrateur, comme les journées des taxis. L'automatisation exécute fidèlement ce qu'on lui a dit ; elle ne vérifie pas que c'était utile.

**6. Versionnez :** la réception a mis à jour le ticket DVC des données.

```bash title="Terminal JupyterLab"
cd /home/lab/projet
git status --short
git add dags/ data/livraisons.csv.dvc dvc.lock metrics.json
git commit -m "Pipeline déclenché par l'Asset livraisons ; données de 9 semaines"
```

::: hint
`unpause` répond `No paused DAGs were found` : Airflow n'a pas encore lu le nouveau fichier, relancez la commande quelques secondes plus tard. `colisvert_pipeline` ne démarre pas : il est en pause (activez-le), ou le DAG n'a pas été relu depuis votre modification (`airflow dags list-import-errors`, puis attendez quelques secondes). Le producteur échoue sur `controler_contrat` : le fichier reçu viole le contrat, et c'est voulu que rien ne parte en aval. `KeyError: 'md5_donnees'` dans la Cellule 4 : la version a été enregistrée depuis un notebook, sans ce tag ; seule la ligne challenger compte ici.
:::
::::

{#au-dela}
## Au-delà du TP : d'où vient l'événement ?

Dans le TP, on déclenche le producteur à la main : c'est le rôle que joue, en vrai, l'arrivée du fichier. En production, trois mécanismes le font sans vous :

| Mécanisme | Principe | Exemple |
|---|---|---|
| **Capteur** (*sensor*) | Une tâche qui vérifie régulièrement une condition (un fichier existe, une partition est là). En mode différé (*deferrable*), l'attente est confiée au triggerer et n'occupe pas de worker | `FileSensor`, `S3KeySensor`, `WasbBlobSensor` (Azure) |
| **Surveillance d'Asset** (*AssetWatcher*) | Airflow 3 écoute une file de messages et publie l'Asset dès qu'un message arrive : plus de sondage | Une notification de dépôt de fichier envoyée dans une file (Kafka, Amazon SQS…) |
| **Appel d'API** | Le système qui dépose le fichier appelle l'API REST d'Airflow pour publier l'événement de l'Asset | Le système des entrepôts de ColisVert, en fin d'export |

Côté cloud, on retrouve la même idée : les **déclencheurs d'événements de stockage** de Data Factory et de Fabric (un fichier arrive dans un compte de stockage ou un lakehouse, le pipeline démarre), **Eventarc** chez Google.

{#quiz}
## Quiz

```quiz
- q: La tâche controler_contrat de colisvert_reception échoue. Que se passe-t-il pour colisvert_pipeline ?
  options:
    - Il démarre avec les données invalides
    - Rien - la tâche publier ne tourne pas, aucun événement n'est émis sur l'Asset
    - Il démarre et échoue
    - Il démarre à 06:45 avec les données invalides
  answer: 1
  explain: Un Asset n'est mis à jour que si sa tâche productrice réussit. Seul le filet de sécurité de 06:45 relancerait le pipeline, qui retrouverait le contrat en première tâche.
- q: Quelle planification fait démarrer le pipeline dès que les données arrivent, avec un horaire de secours ?
  options:
    - schedule=LIVRAISONS
    - AssetOrTimeSchedule(timetable=CronTriggerTimetable(...), assets=LIVRAISONS)
    - AssetAndTimeSchedule(...)
    - schedule="45 6 * * *"
  answer: 1
  explain: AssetOrTimeSchedule crée des exécutions pour chaque événement de l'Asset ET à chaque horaire.
- q: Que contient l'extra d'un événement d'Asset ?
  options:
    - Le fichier de données lui-même
    - De petites métadonnées choisies par le producteur, lisibles par le consommateur
    - Le code du DAG producteur
    - Les journaux du producteur
  answer: 1
  explain: Comme XCom, l'extra transporte des étiquettes, pas des données.
- q: Après l'arrivée de la 9e semaine, le challenger a un F1 de 0,683 contre 0,685 pour le champion. Que s'est-il passé ?
  options:
    - Le nouveau modèle est moins bon
    - Le modèle est le même - la date de coupure fixe a envoyé toute la nouvelle semaine dans le jeu de test ; seule l'évaluation a changé
    - Le contrat de données a modifié les données
    - MLflow a mal calculé le F1
  answer: 1
  explain: Le train est identique (3 805 colis). Il faut faire glisser la date de coupure avec les données, et comparer les modèles sur le même jeu de test.
- q: Dans le TP, qu'est-ce qui joue le rôle de l'arrivée réelle du fichier ?
  options:
    - L'ordonnanceur
    - Votre commande airflow dags trigger colisvert_reception ; en production, un capteur, une file de messages ou un appel d'API
    - Le triggerer
    - MLflow
  answer: 1
  explain: Le producteur doit être déclenché par quelque chose - c'est le rôle des mécanismes de la dernière section.
```
