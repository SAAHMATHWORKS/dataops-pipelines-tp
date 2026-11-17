---
subtitle: >-
  Le pipeline du jour 2 est reproductible, mais quelqu'un doit encore taper dvc repro. Le confier à
  une tâche planifiée à 06:45 semble suffire... jusqu'au matin où le fichier arrive à 07:24. Un
  orchestrateur fait ce qu'une horloge ne sait pas faire : enchaîner, réessayer, rattraper, attendre
  les données, et garder la trace de tout.
objectives:
  - Distinguer le pipeline (ce qu'il faut faire) de l'orchestration (quand et comment le faire tourner)
  - Citer ce qu'un orchestrateur apporte par rapport à une tâche planifiée (cron)
  - Définir DAG, tâche, exécution et intervalle de données
  - Décrire les composants d'Airflow 3 et ce qui a changé par rapport à Airflow 2
  - Situer Airflow parmi les orchestrateurs et les services managés de 2026
---

{#probleme}
## Le problème : une horloge ne voit pas les données

**Où en est ColisVert.** Le pipeline existe (`dvc.yaml` : préparer, entraîner, évaluer), il est suivi par MLflow, et un registre garde les versions du modèle. Mais il ne tourne que si quelqu'un tape `dvc repro`. Le métier veut un modèle **réentraîné chaque matin** sur les expéditions de la veille.

**La première idée : une tâche planifiée.** Sous Linux, le planificateur `cron` lance une commande à heure fixe. Une ligne suffit :

```plaintext title="crontab : chaque jour à 06:45"
45 6 * * *  cd /home/lab/projet && dvc repro
```

Pourquoi 06:45 ? Parce que le fichier des expéditions arrive « vers 06:30 ». Au jour 1, on a mesuré son heure d'arrivée réelle pendant 56 jours (`arrivees.csv`). Confrontons l'horaire aux faits.

:::: lab Démo | Un horaire fixe face à un fichier qui arrive quand il peut | 4 min
Ouvrez un notebook neuf `j3-apres-midi.ipynb` dans le dossier `notebooks`.

```python title="Cellule 1 : à quelle heure lancer le pipeline ?"
import pandas as pd
from pipeline.commun import DATA

arrivees = pd.read_csv(DATA / "arrivees.csv")
for horaire in ["06:45", "07:00", "08:00"]:
    pas_encore_la = arrivees["heure_arrivee"] > horaire
    print(f"pipeline lancé à {horaire} : fichier absent {pas_encore_la.sum()} fois sur {len(arrivees)} jours")
retards = arrivees[arrivees["heure_arrivee"] > "06:45"]
print("jours concernés à 06:45 :", ", ".join(retards["date"].str[5:]))
```

```plaintext title="Sortie attendue"
pipeline lancé à 06:45 : fichier absent 8 fois sur 56 jours
pipeline lancé à 07:00 : fichier absent 8 fois sur 56 jours
pipeline lancé à 08:00 : fichier absent 1 fois sur 56 jours
jours concernés à 06:45 : 09-10, 09-12, 09-15, 09-29, 10-13, 10-25, 10-28, 10-31
```
::::

**Ce que ces chiffres disent.**

- À 06:45, **un jour sur sept**, le modèle est réentraîné sur le fichier de **l'avant-veille**. Et personne ne le sait : `dvc repro` constate que rien n'a changé et répond « à jour ». Le pire des échecs : un succès apparent.
- Reculer l'horaire ne règle rien. À 08:00, il reste un jour raté (le 29 septembre, fichier arrivé à 08:02) et l'on a perdu une heure et quart **tous les autres jours**.
- La bonne question n'est pas « à quelle heure ? » mais « **quand le fichier est-il là ?** ». Une horloge ne peut pas y répondre. Un orchestrateur, si : on le verra au TP 2 avec les *Assets*.

{#cron}
## Ce que cron ne fait pas

**L'analogie du réveil et du chef de gare.** `cron` est un réveil : il sonne à l'heure, que le train soit en gare ou non, et ne sait pas si vous vous êtes levé. Un orchestrateur est un chef de gare : il connaît l'ordre des départs, attend que la voie soit libre, fait repartir un train en panne, tient le registre de tous les passages, et prévient quand un train n'arrive pas.

| Besoin | Tâche planifiée (cron) | Orchestrateur |
|---|---|---|
| **Enchaîner** des étapes dépendantes | Un seul script qui fait tout, ou des horaires décalés « au jugé » | Un graphe de tâches : chacune démarre quand les précédentes ont réussi |
| **Réessayer** après une panne passagère | Rien : l'échec attend le lendemain | Nouvelles tentatives automatiques, avec délai |
| **Savoir** ce qui s'est passé | Un fichier de log, si on y a pensé | L'historique de chaque exécution et de chaque tâche, avec ses journaux |
| **Rattraper** des jours manqués | À la main, jour par jour | Une commande de rattrapage (*backfill*) |
| **Attendre les données** | Impossible : seulement l'heure | Déclenchement par l'arrivée d'une donnée |
| **Alerter** | Rien | Notifications en cas d'échec ou de retard |
| **Voir** l'état d'ensemble | Rien | Une interface web : ce qui tourne, ce qui a échoué, depuis quand |

**Le principe :** un orchestrateur ne fait pas le travail lui-même. Il **décide quand** chaque étape tourne, **surveille** son résultat et **réagit**. Le travail reste fait par vos scripts : `pipeline/prepare.py`, `dvc repro`, une requête SQL.

{#pipeline-orchestration}
## Le pipeline et l'orchestration : deux métiers

Le module d'orchestration du MLOps Zoomcamp de DataTalks.Club fait une distinction utile : **le pipeline décrit le travail et ses dépendances ; l'orchestration est la couche d'exploitation qui le fait tourner.** Chez ColisVert, les deux métiers ont déjà chacun leur outil :

| Question | Qui répond | Où c'est écrit |
|---|---|---|
| Quelles étapes, dans quel ordre, avec quelles entrées et sorties ? | **DVC** | `dvc.yaml` |
| Cette étape doit-elle tourner, ou rien n'a changé depuis la dernière fois ? | **DVC** | `dvc.lock` (les empreintes) |
| **Quand** lancer le pipeline ? Après quel événement ? | **Airflow** | un fichier DAG en Python |
| Que faire si une étape échoue ? Combien de fois réessayer ? | **Airflow** | les options du DAG |
| Qu'est-il arrivé mardi dernier à 06:45 ? | **Airflow** | sa base de métadonnées, son interface |
| Quels paramètres et quelles métriques pour ce modèle ? | **MLflow** | le serveur de suivi |

Le Zoomcamp insiste sur une seconde règle, qu'on appliquera tout l'après-midi : **un script de pipeline reçoit sa période en paramètre**, il ne la devine pas. Un script qui calcule « hier » avec l'horloge ne peut pas être rejoué pour le 15 janvier ; un script qui reçoit `2024-01-15` peut l'être, aujourd'hui comme dans un an. C'est ce qui rend possibles les nouvelles tentatives et le rattrapage.

{#vocabulaire}
## Le vocabulaire d'Airflow

| Terme | Définition | Chez ColisVert |
|---|---|---|
| **DAG** (*directed acyclic graph*, graphe orienté sans cycle) | Un ensemble de tâches et leurs dépendances, écrit dans un fichier Python. « Sans cycle » : une tâche ne peut pas dépendre, même indirectement, d'elle-même | `colisvert_pipeline` |
| **Tâche** (*task*) | Une étape du DAG : une fonction Python, une commande, une requête | `entrainer` lance `dvc repro --single-item train` |
| **Exécution** (*DAG run*) | Une exécution du DAG entier, pour une date donnée | le run du 8 décembre à 06:45 |
| **Instance de tâche** | Une tâche dans une exécution, avec son état (en file, en cours, réussie, échouée, en attente de nouvelle tentative, sautée) | `entrainer` du 8 décembre, réussie à la 2e tentative |
| **Planification** (*schedule*) | Ce qui déclenche les exécutions : un horaire, un intervalle, une donnée, rien (à la demande) | chaque jour à 06:45, ou à l'arrivée du fichier |
| **Date logique et intervalle de données** | La période que l'exécution traite, qui n'est pas forcément le moment où elle tourne | le run qui traite le 15 janvier tourne le 16 à 00:00 |
| **XCom** (*cross-communication*) | Une petite valeur passée d'une tâche à la suivante, stockée dans la base | un nombre de jours, un chemin de fichier ; jamais un tableau de données |
| **Asset** | Une donnée déclarée (fichier, table) dont la mise à jour peut déclencher des DAG | `data/livraisons.csv` |

{#architecture}
## L'architecture d'Airflow 3

::: figure airflow3-architecture.svg
Les composants d'Airflow 3. Le processeur de DAG lit vos fichiers ; l'ordonnanceur décide ; les workers exécutent ; le serveur d'API sert l'interface et reçoit les comptes rendus des tâches ; la base garde tout l'historique. Sur la VM de formation, la commande airflow standalone lance tout dans un seul conteneur.
:::

| Composant | Rôle | Point d'attention |
|---|---|---|
| **Processeur de DAG** (*dag-processor*) | Relit régulièrement le dossier `dags/`, exécute chaque fichier Python pour y trouver les DAG, et les enregistre dans la base | Le code au **niveau du module** (hors des tâches) est exécuté à chaque lecture, toutes les quelques secondes : jamais de calcul ni d'accès réseau à cet endroit |
| **Ordonnanceur** (*scheduler*) | Crée les exécutions à l'heure prévue ou à l'arrivée d'une donnée, et met en file les tâches dont les dépendances sont satisfaites | Le cœur du système : s'il s'arrête, plus rien ne démarre |
| **Exécuteur et workers** | Font tourner les tâches. L'exécuteur local lance des processus sur la même machine ; Celery ou Kubernetes répartissent sur plusieurs machines | Ici, l'exécuteur local suffit |
| **Serveur d'API** (*api-server*) | Sert l'interface web, l'API REST, et l'**API d'exécution** des tâches | Nouveau rôle dans Airflow 3 |
| **Triggerer** | Surveille les attentes longues (un fichier, un travail distant) sans bloquer un worker | Utile pour les capteurs « différés » (*deferrable*) |
| **Base de métadonnées** | Tout l'état : DAG, exécutions, tâches, XCom, événements des Assets | SQLite pour la formation ; PostgreSQL en production |

**Ce qui a changé avec Airflow 3 (avril 2025).** C'est la plus grosse version depuis 2020. Quatre changements comptent pour cet après-midi :

1. **Les tâches ne parlent plus à la base.** Dans Airflow 2, chaque tâche ouvrait une connexion directe à la base de métadonnées : un risque de sécurité, et une limite pour exécuter des tâches ailleurs (un autre cloud, un autre langage). Dans Airflow 3, elles rendent compte au serveur d'API (le *Task SDK*). On écrit donc les DAG avec le module `airflow.sdk`.
2. **Les *datasets* sont devenus des *Assets*,** avec des déclenchements plus riches (combinaisons, métadonnées transportées, surveillance de files de messages).
3. **Une nouvelle interface** et une **API REST v2**.
4. **Des valeurs par défaut plus prudentes :** pas de rattrapage automatique (`catchup=False`), et une planification « cron » sans intervalle de données. On verra pourquoi cela compte, à la notion 4.

::: callout warn Airflow 2 n'est pas mort
Beaucoup d'entreprises, et certains services managés, tournent encore sous Airflow 2 (on l'a vu ce matin : la documentation des tâches Apache Airflow de Fabric indiquait Airflow 2.10.5 en juin 2026). Les tutoriels du web mélangent les deux versions. Repères rapides : `from airflow.sdk import dag, task` et `Asset` signalent Airflow 3 ; `from airflow.decorators import dag` et `Dataset` signalent Airflow 2.
:::

{#marche}
## Airflow parmi les orchestrateurs

Ce matin, le radar technologique de ColisVert a placé **Airflow 3** dans l'anneau **« Essayer », avec un pilote sur le pipeline des retards**. Cet après-midi est ce pilote. Pourquoi Airflow plutôt qu'un autre ?

| Outil | Idée maîtresse | Quand le préférer |
|---|---|---|
| **Apache Airflow** | Des tâches et leurs dépendances, en Python ; le standard de fait, projet de la fondation Apache | Pipelines de données d'entreprise ; écosystème de centaines de connecteurs ; compétence la plus répandue |
| **Prefect** | Des fonctions Python décorées, sans notion de DAG figé | Workflows dynamiques, équipes très Python |
| **Dagster** | Les **données** d'abord (*software-defined assets*), les tâches ensuite | Plateformes où le lignage des données est central |
| **Kestra** | Des workflows déclarés en YAML | Équipes qui préfèrent la configuration au code |
| **Fabric Data Factory, Azure Data Factory** | Pipelines visuels, sans code | Copie et intégration de données, équipes peu développeuses |

**Les services managés d'Airflow**, vus ce matin : les tâches Apache Airflow de **Microsoft Fabric** (qui remplacent le *Workflow Orchestration Manager* d'Azure Data Factory, fermé aux nouvelles instances depuis le 1er janvier 2026), **Managed Service for Apache Airflow** chez Google (ex-Cloud Composer), Amazon MWAA chez AWS, ou Astronomer, l'éditeur spécialiste. Un DAG écrit aujourd'hui se transporte d'un service à l'autre, **à condition que la version d'Airflow suive**.

::: callout info L'histoire du Zoomcamp, une leçon de radar
Le module d'orchestration du MLOps Zoomcamp a utilisé **Prefect** en 2022 et 2023, **Mage** en 2024, puis a laissé le choix de l'outil en 2025 (Airflow, Prefect ou autre). Les outils tournent ; les concepts (graphe de tâches, paramètres, nouvelles tentatives, rattrapage) restent. C'est pour cela qu'on les nomme toujours avant de montrer l'outil.
:::

{#quiz}
## Quiz

```quiz
- q: Le pipeline lancé par cron à 06:45 répond « Data and pipelines are up to date » un jour où le fichier arrive à 07:24. Que s'est-il passé ?
  options:
    - Le pipeline a planté
    - Il a constaté que les données de la veille n'avaient pas changé, et n'a rien réentraîné, en silence
    - Il a attendu le fichier
    - Il a entraîné sur le nouveau fichier
  answer: 1
  explain: Le fichier du jour n'était pas encore là. DVC a vu les mêmes données que la veille et a, à raison, sauté toutes les étapes. Le problème n'est pas DVC, c'est le déclenchement à l'aveugle.
- q: Qui décide si l'étape « train » doit réellement recalculer le modèle ?
  options:
    - Airflow, selon l'heure
    - DVC, en comparant les empreintes des entrées à celles de dvc.lock
    - MLflow
    - Le worker
  answer: 1
  explain: Airflow décide QUAND lancer la tâche ; DVC décide si le travail est nécessaire. Les deux rôles se complètent.
- q: Pourquoi ne faut-il pas lire un gros fichier au niveau du module d'un fichier DAG (en dehors des tâches) ?
  options:
    - Parce qu'Airflow l'interdit
    - Parce que le processeur de DAG exécute ce code à chaque relecture du dossier, toutes les quelques secondes
    - Parce que le fichier serait copié dans XCom
    - Parce que le worker n'y a pas accès
  answer: 1
  explain: Le code de niveau module tourne à chaque analyse du fichier, pas seulement quand le DAG s'exécute. Le travail se met dans les tâches.
- q: Dans Airflow 3, comment une tâche enregistre-t-elle son état ?
  options:
    - Elle écrit directement dans la base de métadonnées
    - Elle rend compte au serveur d'API, par l'API d'exécution
    - Elle écrit un fichier lu par l'ordonnanceur
    - Elle envoie un courriel
  answer: 1
  explain: C'est le principal changement d'architecture d'Airflow 3, qui isole les tâches de la base et permet de les exécuter ailleurs.
```
