---
subtitle: >-
  Un DAG Airflow est un fichier Python ordinaire, posé dans un dossier. On en écrit un petit, qui
  mesure la fraîcheur du fichier des expéditions, pour voir chaque pièce : les tâches, leurs
  dépendances, les valeurs qu'elles se passent, les paramètres. Puis on fixe les règles qui
  rendent un pipeline robuste, celles qu'on appliquera au TP.
objectives:
  - Écrire un DAG avec l'API TaskFlow - @dag, @task, @task.bash
  - Expliquer comment un appel de fonction crée à la fois une dépendance et un passage de valeur (XCom)
  - Savoir quel Python exécute une tâche, et pourquoi le pipeline tourne dans des commandes
  - Tester un DAG en ligne de commande, puis le suivre dans l'interface
  - Énoncer les règles d'un pipeline robuste et leur traduction dans Airflow
---

{#fichier}
## Un DAG est un fichier Python

Voici le DAG `colisvert_fraicheur`. Il fait, chaque fois qu'on le lance, la mesure de la Cellule 1 : combien de jours le fichier est-il arrivé après une heure limite ? Il est dans le dépôt, sous `solutions/airflow/colisvert_fraicheur.py`.

```python title="solutions/airflow/colisvert_fraicheur.py"
from __future__ import annotations

import csv
from datetime import datetime

from airflow.sdk import dag, task

PROJET = "/home/lab/projet"


@dag(
    dag_id="colisvert_fraicheur",
    schedule=None,                          # seulement à la demande
    start_date=datetime(2026, 9, 7),          # premier jour des données ColisVert
    catchup=False,
    params={"heure_limite": "06:45"},       # modifiable à chaque déclenchement
    tags=["colisvert", "jour3"],
)
def colisvert_fraicheur():
    @task
    def lire_arrivees() -> list[dict]:
        with open(f"{PROJET}/data/arrivees.csv", newline="", encoding="utf-8") as fichier:
            return list(csv.DictReader(fichier))

    @task
    def mesurer(arrivees: list[dict], params=None) -> int:
        limite = params["heure_limite"]
        en_retard = [a["date"] for a in arrivees if a["heure_arrivee"] > limite]
        print(f"fichier arrivé après {limite} : {len(en_retard)} jours sur {len(arrivees)}")
        return len(en_retard)

    @task.bash
    def compter_colis() -> str:
        return f"cd {PROJET} && wc -l < data/livraisons.csv"

    mesurer(lire_arrivees())
    compter_colis()


colisvert_fraicheur()
```

**Lecture, de haut en bas.**

| Élément | Rôle |
|---|---|
| `from airflow.sdk import dag, task` | Le module des auteurs de DAG dans Airflow 3. Tout ce qu'il faut pour écrire un DAG vient de là |
| `@dag(...)` | Fait de la fonction `colisvert_fraicheur` un DAG. Ses arguments sont ses **réglages** |
| `dag_id` | Le nom unique du DAG, celui de l'interface et des commandes |
| `schedule=None` | Pas de planification : le DAG ne tourne que si on le déclenche |
| `start_date` | La date à partir de laquelle des exécutions **planifiées** peuvent exister. Toujours dans le passé, et fixe (voir l'encadré) |
| `catchup=False` | Ne pas rattraper les dates passées au premier démarrage (la valeur par défaut d'Airflow 3) |
| `params` | Des paramètres avec une valeur par défaut, qu'on peut changer à chaque déclenchement |
| `@task` | Une tâche Python : la fonction s'exécute dans un processus du worker |
| `@task.bash` | Une tâche shell : la fonction **renvoie une commande**, que le worker exécute |
| `mesurer(lire_arrivees())` | La ligne clé. Voir ci-dessous |
| `colisvert_fraicheur()` | Crée le DAG. Sans cette dernière ligne, Airflow ne trouve rien |

**L'appel de fonction fait deux choses.** Écrire `mesurer(lire_arrivees())` ne lance rien au moment où le fichier est lu : cela **décrit** le graphe. Airflow en déduit :

1. une **dépendance** : `mesurer` attend que `lire_arrivees` ait réussi ;
2. un **passage de valeur** : ce que `lire_arrivees` renvoie est enregistré dans la base (un **XCom**) puis donné à `mesurer` comme argument.

`compter_colis()` n'est relié à rien : elle tourne en parallèle des deux autres. Pour une dépendance **sans** passage de valeur, on écrit `tache_a() >> tache_b()`, qu'on utilisera au TP.

::: callout warn XCom transporte des étiquettes, pas des cargaisons
Un XCom est stocké dans la base de métadonnées. Il convient à une valeur courte : un nombre, une date, un chemin de fichier, un petit dictionnaire. Les 56 lignes d'`arrivees.csv` passent sans peine ; les 5 035 colis des livraisons, non. Pour les données, une tâche écrit un fichier (ou une table) et passe son **chemin** à la suivante.
:::

::: callout warn Un start_date dans le futur : un succès sans rien faire
Pendant la préparation de ce cours, en novembre, un DAG avait `start_date=datetime(2026, 12, 1)`. Résultat : chaque test se terminait **en succès, en une fraction de seconde, sans exécuter une seule tâche**. Airflow ne crée pas les tâches d'une exécution datée d'avant leur `start_date`, et une exécution sans tâche est... réussie. Deux règles : un `start_date` **dans le passé**, et **fixe** (jamais `datetime.now()`, qui change à chaque lecture du fichier).
:::

`params=None` dans la signature de `mesurer` est une convention de TaskFlow : un argument qui porte le nom d'une variable du **contexte** d'exécution (`params`, `logical_date`, `data_interval_start`, `outlet_events`…) est rempli par Airflow au moment de l'exécution.

{#deux-pythons}
## Quel Python exécute la tâche ?

Le conteneur `airflow` contient **deux** installations de Python, et le choix est délibéré :

| | Python d'Airflow | Python du projet |
|---|---|---|
| Où | `/opt/airflow` | `/usr/local/bin/python`, celui de JupyterLab |
| Contient | Airflow et ses dépendances, aux versions qu'il impose | pandas, scikit-learn, DVC, MLflow, DuckDB, aux versions des TP |
| Qui l'utilise | les tâches `@task` | les commandes des tâches `@task.bash` (`python`, `dvc`) |

**Pourquoi ne pas tout mettre ensemble ?** Airflow fige les versions de plusieurs centaines de bibliothèques. Les installer dans l'environnement du projet changerait des versions dont dépend le modèle, et un modèle entraîné par Airflow pourrait différer de celui entraîné dans le notebook. En séparant les deux, `dvc repro` lancé par Airflow utilise **exactement** les bibliothèques de JupyterLab : même code, mêmes versions, même modèle.

**La règle qui en découle :** une tâche `@task` ne fait que du Python standard (lire un petit fichier, comparer des nombres, décider). Le **travail** du pipeline passe par des commandes (`@task.bash`), qui appellent les scripts du projet. C'est aussi ce qu'on fait en production, en plus isolé : chaque tâche lance un conteneur dédié (`KubernetesPodOperator`, `DockerOperator`) ou un environnement virtuel (`@task.virtualenv`, `@task.external_python`).

{#tester}
## Tester le DAG

:::: lab Démo | Poser le DAG, le tester, le regarder | 10 min
**1. Copiez le DAG dans le dossier que lit Airflow**, puis vérifiez qu'il se charge sans erreur. Dans un **terminal de la VM** :

```bash title="Terminal de la VM"
cd ~/dataops-pipelines-tp
cp solutions/airflow/colisvert_fraicheur.py dags/
docker compose exec airflow airflow dags list-import-errors
```

```plaintext title="Sortie attendue"
No data found
```

« Aucune donnée » : aucune erreur d'import. Une faute de frappe dans le fichier apparaîtrait ici, avec la ligne fautive.

**2. Testez-le.** `airflow dags test` exécute toutes les tâches du DAG **tout de suite**, dans le terminal, sans passer par l'ordonnanceur. C'est le premier réflexe après chaque modification. Sa sortie compte plusieurs centaines de lignes ; le script `tester-dag.sh` du dépôt la lance et la **résume** : chaque tâche (▶), ce qu'elle écrit (│), ce qu'elle renvoie (→), puis l'état final des tâches, lu dans la base d'Airflow.

```bash title="Terminal de la VM"
./scripts/tester-dag.sh colisvert_fraicheur
```

```plaintext title="Sortie attendue"
▶ lire_arrivees
  → renvoie [{'date': '2026-09-07', 'heure_arrivee': '06:09'}, {'date': '2026-0...
▶ compter_colis
  │ 5036
▶ mesurer
  │ fichier arrivé après 06:45 : 8 jours sur 56
  → renvoie 8
exécution success ; état des tâches :
  lire_arrivees          success
  compter_colis          success
  mesurer                success
```

- `compter_colis` n'est reliée à rien : selon les exécutions, elle passe avant ou après `lire_arrivees`. L'ordre entre tâches indépendantes n'est pas garanti.
- `lire_arrivees` **renvoie** la liste des 56 jours : c'est l'XCom que `mesurer` reçoit en argument.
- `wc -l` compte 5 036 lignes : l'en-tête et les 5 035 colis des 8 semaines.

**3. Changez le paramètre** pour la limite de 06:30 :

```bash title="Terminal de la VM"
./scripts/tester-dag.sh colisvert_fraicheur -c '{"heure_limite": "06:30"}'
```

```plaintext title="Sortie attendue (extrait)"
▶ mesurer
  │ fichier arrivé après 06:30 : 27 jours sur 56
  → renvoie 27
```

Le même code, une autre exécution, un autre paramètre : 27 jours sur 56 auraient été ratés avec un pipeline lancé à 06:30. Dans l'interface, on fait la même chose avec le bouton **Trigger**, qui affiche un formulaire construit à partir de `params`.

**4. Regardez dans l'interface** (http://localhost:8080) : le DAG `colisvert_fraicheur` est dans la liste. Cliquez dessus, puis :

- onglet **Graph** : les trois tâches, et la flèche de `lire_arrivees` vers `mesurer` ;
- les deux exécutions que vous venez de lancer, avec leurs tâches en vert, dans la vue **Grid** ;
- une tâche, puis **Logs** : son journal, avec la ligne affichée par `print` ;
- une tâche, puis **XCom** : la valeur qu'elle a renvoyée.
::::

{#robuste}
## Les règles d'un pipeline robuste

Un pipeline orchestré tourne sans vous, souvent la nuit. Il sera relancé : après une panne, par un collègue, pour rattraper une semaine. Six règles le rendent sûr. Chacune a sa traduction dans Airflow, et on les appliquera toutes au TP.

| Règle | Pourquoi | Dans Airflow, au TP |
|---|---|---|
| **1. Idempotence** : relancer une tâche donne le même résultat que la lancer une fois | Une tâche sera rejouée, c'est certain (nouvelle tentative, relance manuelle, rattrapage) | `dvc repro` saute ce qui n'a pas changé ; l'enregistrement du challenger ne crée pas de doublon ; une partition est réécrite, pas ajoutée |
| **2. Déterminisme** : la tâche reçoit sa période, elle ne lit pas l'horloge | Pour pouvoir rejouer le 15 janvier dans un an | `data_interval_start`, jamais `datetime.now()` |
| **3. Échouer tôt et fort** : vérifier les entrées avant de calculer | Un modèle faux, publié en silence, coûte plus cher qu'un pipeline arrêté | Le contrat de données du jour 1 devient la première tâche |
| **4. Réessayer les pannes passagères, pas les erreurs permanentes** | Un serveur qui redémarre se répare seul ; un fichier invalide le restera | `retries=2` par défaut, `retries=0` pour le contrôle des données |
| **5. Borner le temps** | Une tâche bloquée bloque toutes les suivantes, et le lendemain | `execution_timeout`, `max_active_runs=1` |
| **6. Écrire de façon atomique** | Un lecteur ne doit jamais voir un fichier à moitié écrit | Écrire dans un fichier temporaire, puis le renommer |

Une septième règle tient au métier plutôt qu'à la technique : **automatiser la proposition, pas la décision**. Le pipeline peut proposer un challenger quand la charte est respectée ; promouvoir le champion reste une décision humaine, prise avec la règle de promotion du jour 2.

::: callout info Alerter
Une panne qui se répare seule n'a pas besoin de vous. Une panne qui persiste après les nouvelles tentatives, si. Airflow appelle une fonction à chaque échec définitif (`on_failure_callback`, souvent un message Teams ou Slack) et, depuis Airflow 3.1, peut prévenir quand une exécution **dépasse une échéance** (*Deadline Alerts*, qui remplacent les anciens SLA ; la fonction est encore marquée expérimentale dans Airflow 3.4). Dans la VM, on se contente de l'interface.
:::

{#quiz}
## Quiz

```quiz
- q: Dans un DAG TaskFlow, que produit l'écriture b(a()) ?
  options:
    - a et b s'exécutent immédiatement, à la lecture du fichier
    - b dépend de a, et reçoit sa valeur de retour par XCom
    - a et b tournent en parallèle
    - b s'exécute avant a
  answer: 1
  explain: L'appel décrit le graphe. Airflow en déduit la dépendance et le passage de valeur ; rien ne s'exécute à la lecture du fichier.
- q: Une tâche doit passer 5 000 lignes de données à la suivante. Que faire ?
  options:
    - Les renvoyer, XCom les transportera
    - Les écrire dans un fichier ou une table, et passer son chemin
    - Les mettre dans une variable globale du fichier DAG
    - Les passer dans params
  answer: 1
  explain: XCom est stocké dans la base de métadonnées - il est fait pour de petites valeurs.
- q: Pourquoi le pipeline ColisVert passe-t-il par @task.bash plutôt que par @task ?
  options:
    - Parce que bash est plus rapide que Python
    - Parce que @task s'exécute avec le Python d'Airflow, qui n'a pas les bibliothèques du projet ; la commande utilise le Python du projet
    - Parce qu'Airflow 3 ne sait plus exécuter de Python
    - Par habitude
  answer: 1
  explain: Les deux environnements sont séparés pour que le modèle soit entraîné avec exactement les versions de JupyterLab.
- q: Le contrôle du contrat de données échoue. Combien de nouvelles tentatives faut-il prévoir ?
  options:
    - Le plus possible
    - Aucune - un fichier invalide le restera, il faut arrêter et alerter
    - Deux, comme les autres tâches
    - Une par heure jusqu'au lendemain
  answer: 1
  explain: Les nouvelles tentatives servent aux pannes passagères. Une erreur de données est permanente tant que le producteur ne corrige pas son fichier.
- q: Quelle tâche est idempotente ?
  options:
    - Ajouter les lignes du jour à la fin d'un fichier
    - Réécrire entièrement la partition du jour
    - Créer une nouvelle version de modèle à chaque passage
    - Envoyer un SMS au client
  answer: 1
  explain: Rejouée deux fois, la réécriture donne le même fichier. L'ajout produirait des doublons.
```
