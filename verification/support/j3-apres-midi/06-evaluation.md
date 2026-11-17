---
subtitle: >-
  La commission des taxis veut un contrôle qualité quotidien de ses données : chaque jour, le nombre
  de courses et le nombre de défauts. Vous écrivez le DAG, vous le testez sur une journée, vous
  rattrapez la première semaine de janvier, vous prouvez que le résultat est juste, puis qu'il est
  idempotent.
objectives:
  - Écrire un DAG quotidien à intervalles de données, avec ses réglages de robustesse
  - Tester un DAG par un rattrapage d'une journée, puis rattraper une semaine
  - Vérifier un rattrapage en le comparant à un calcul direct
  - Prouver l'idempotence d'une tâche par l'empreinte de son résultat
# Barème : 14 points pour les étapes (indiqués sur chaque étape) + 6 points pour le QCM
quiz_points: 6
---

{#consignes}
## Consignes

**Scénario.** Ce matin, vous avez compté les défauts du fichier de janvier en une requête. La commission veut maintenant ce contrôle **chaque jour**, rattrapé depuis le 1er janvier, pour suivre la qualité dans le temps. Le script est prêt : `pipeline/taxis_qualite.py` reçoit une journée et écrit `rapports/qualite/jour=AAAA-MM-JJ/defauts.parquet`, avec cinq colonnes : `jour`, `courses`, `prix_negatif_ou_nul`, `distance_nulle`, `passagers_manquants`.

```bash title="Utilisation du script"
python -m pipeline.taxis_qualite 2024-01-15 2024-01-16
```

- **Durée :** 30 minutes, en autonomie. Le formateur passe voir chacun.
- **Où :** le fichier `dags/taxis_qualite.py`, le terminal de la VM, et un notebook neuf `j3-apres-midi-evaluation.ipynb` (dossier `notebooks`).
- **Validation :** chaque étape se termine par une **preuve** : collez la sortie demandée et cliquez sur « Envoyer ma preuve ».
- **Barème :** 14 points pour les 4 étapes, 6 points pour le QCM final (une seule tentative par question).
- Les corrections sont là si vous bloquez, mais essayez d'abord.

::: widget task-progress
:::

{#dag}
## Écrire le DAG

:::: task Étape 1 | Le DAG taxis_qualite, testé sur le 15 janvier | 10 min | 4 pts
Écrivez `dags/taxis_qualite.py` :

1. `dag_id` : `taxis_qualite` ; une exécution par journée, de minuit à minuit UTC, **avec intervalle de données** ;
2. du 1er au 31 janvier 2024, sans rattrapage automatique, au plus 4 exécutions en parallèle ;
3. une nouvelle tentative après 30 secondes, et une tâche arrêtée au-delà de 5 minutes ;
4. une seule tâche, `compter_defauts`, qui lance le script avec les bornes de l'intervalle.

Puis, dans le terminal de la VM : vérifiez qu'il se charge, activez-le, et testez-le par un rattrapage **d'une seule journée**, le 15 janvier.

::: proof Collez les deux lignes du journal de la tâche compter_defauts (onglet Logs de l'exécution du 15 janvier)
:::

::: hint
Repartez de `taxis_journalier` (notion 4) : la structure est la même. Les réglages de robustesse vont dans `default_args`. Pour le test : `airflow backfill create` avec la même date en `--from-date` et `--to-date`. Un rattrapage qui reste gris (*queued*) : le DAG est en pause ; si `unpause` a répondu `No paused DAGs were found`, le fichier n'était pas encore lu, relancez-le. Pas `airflow dags test … 2024-01-15`, qui traiterait le 14.
:::

::: solution
```python title="dags/taxis_qualite.py"
from __future__ import annotations

from datetime import datetime, timedelta

from airflow.sdk import CronDataIntervalTimetable, dag, task

PROJET = "/home/lab/projet"


@dag(
    dag_id="taxis_qualite",
    schedule=CronDataIntervalTimetable("0 0 * * *", timezone="UTC"),
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 1, 31),
    catchup=False,
    max_active_runs=4,
    default_args={"retries": 1, "retry_delay": timedelta(seconds=30),
                  "execution_timeout": timedelta(minutes=5)},
    tags=["taxis", "evaluation"],
)
def taxis_qualite():
    @task.bash
    def compter_defauts(data_interval_start=None, data_interval_end=None) -> str:
        debut = data_interval_start.strftime("%Y-%m-%d")
        fin = data_interval_end.strftime("%Y-%m-%d")
        return f"cd {PROJET} && python -m pipeline.taxis_qualite {debut} {fin}"

    compter_defauts()


taxis_qualite()
```

```bash title="Terminal de la VM"
docker compose exec airflow airflow dags list-import-errors
docker compose exec airflow airflow dags unpause taxis_qualite
docker compose exec airflow airflow backfill create --dag-id taxis_qualite \
  --from-date 2024-01-15 --to-date 2024-01-15
```

```plaintext title="Journal de compter_defauts (extrait)"
2024-01-15 : 77033 courses, 958 prix <= 0, 1413 distances nulles, 2865 sans passagers
écrit : rapports/qualite/jour=2024-01-15/defauts.parquet
```
:::
::::

{#rattrapage}
## Rattraper la première semaine

:::: task Étape 2 | Du 1er au 7 janvier | 5 min | 3 pts
Rattrapez la première semaine de janvier (du 1er au 7 inclus), avec au plus 4 journées en parallèle. Quand toutes les exécutions sont vertes, listez les partitions écrites.

::: proof Collez la sortie de : ls rapports/qualite
:::

::: hint
`--from-date 2024-01-01 --to-date 2024-01-07 --max-active-runs 4`. `Another backfill is running` : le rattrapage de l'étape 1 n'est pas encore clos, relancez quelques secondes plus tard. Le 15, fait à l'étape 1, est toujours là : il doit apparaître dans la liste.
:::

::: solution
```bash title="Terminal de la VM"
docker compose exec airflow airflow backfill create --dag-id taxis_qualite \
  --from-date 2024-01-01 --to-date 2024-01-07 --max-active-runs 4
ls rapports/qualite
```

```plaintext title="Sortie attendue (ls)"
jour=2024-01-01
jour=2024-01-02
jour=2024-01-03
jour=2024-01-04
jour=2024-01-05
jour=2024-01-06
jour=2024-01-07
jour=2024-01-15
```
:::
::::

{#verifier}
## Vérifier le rattrapage

:::: task Étape 3 | Les partitions contre un calcul direct | 9 min | 4 pts
Dans le notebook, calculez de deux façons les totaux de la **première semaine** (du 1er au 7 janvier inclus) pour les quatre compteurs :

1. en additionnant les partitions écrites par le DAG ;
2. par une requête directe sur le fichier source, avec les mêmes règles.

Affichez les deux résultats côte à côte, puis s'ils sont identiques.

::: proof Collez la sortie de votre cellule
:::

::: hint
`read_parquet('…/rapports/qualite/*/defauts.parquet')` lit toutes les partitions ; filtrez `jour < DATE '2024-01-08'` pour exclure le 15. Les sommes de DuckDB sont de très grands entiers : convertissez-les avec `::BIGINT` pour comparer proprement. `count(*) FILTER (WHERE …)` compte les lignes qui vérifient une condition.
:::

::: solution
```python title="Évaluation : partitions contre calcul direct"
import duckdb
import pandas as pd
from pipeline.commun import RACINE

partitions = duckdb.sql(f"""
    SELECT sum(courses)::BIGINT AS courses,
           sum(prix_negatif_ou_nul)::BIGINT AS prix_negatif_ou_nul,
           sum(distance_nulle)::BIGINT AS distance_nulle,
           sum(passagers_manquants)::BIGINT AS passagers_manquants
    FROM read_parquet('{RACINE}/rapports/qualite/*/defauts.parquet')
    WHERE jour < DATE '2024-01-08'
""").df()
direct = duckdb.sql(f"""
    SELECT count(*) AS courses,
           count(*) FILTER (WHERE fare_amount <= 0) AS prix_negatif_ou_nul,
           count(*) FILTER (WHERE trip_distance = 0) AS distance_nulle,
           count(*) FILTER (WHERE passenger_count IS NULL) AS passagers_manquants
    FROM read_parquet('{RACINE}/data/taxis/yellow_tripdata_2024-01.parquet')
    WHERE tpep_pickup_datetime >= '2024-01-01' AND tpep_pickup_datetime < '2024-01-08'
""").df()
comparaison = pd.concat([partitions, direct], keys=["partitions", "direct"]).droplevel(1).T
print(comparaison)
print("identiques :", bool((partitions.values == direct.values).all()))
```

```plaintext title="Sortie attendue"
                     partitions  direct
courses                  609698  609698
prix_negatif_ou_nul        8606    8606
distance_nulle            14175   14175
passagers_manquants       28098   28098
identiques : True
```

Si les deux colonnes différaient, l'une des journées manquerait ou serait comptée deux fois : c'est le contrôle d'un rattrapage.
:::
::::

{#idempotence}
## Prouver l'idempotence

:::: task Étape 4 | Rejouer le 3 janvier | 6 min | 3 pts
Notez l'empreinte MD5 de la partition du 3 janvier, puis **refaites** le rattrapage de cette seule journée en forçant le retraitement d'une exécution réussie. Quand l'exécution est à nouveau verte, reprenez l'empreinte et comptez les partitions.

::: proof Collez les deux empreintes et le nombre de partitions
:::

::: hint
`md5sum rapports/qualite/jour=2024-01-03/defauts.parquet`. Par défaut, un rattrapage ne refait pas une journée déjà réussie : regardez les valeurs de `--reprocess-behavior`. Dans l'interface, la vue Grid montre l'exécution du 3 repartir.
:::

::: solution
```bash title="Terminal de la VM"
md5sum rapports/qualite/jour=2024-01-03/defauts.parquet
docker compose exec airflow airflow backfill create --dag-id taxis_qualite \
  --from-date 2024-01-03 --to-date 2024-01-03 --reprocess-behavior completed
md5sum rapports/qualite/jour=2024-01-03/defauts.parquet
ls rapports/qualite | wc -l
```

```plaintext title="Sortie attendue (les trois lignes utiles)"
a2e545200d3d274ddcf684638789afd1  rapports/qualite/jour=2024-01-03/defauts.parquet
a2e545200d3d274ddcf684638789afd1  rapports/qualite/jour=2024-01-03/defauts.parquet
8
```

Même empreinte, au bit près, et toujours 8 partitions : la journée a été recalculée et **remplacée**, sans doublon. C'est ce qui permet de rattraper et de relancer sans crainte.
:::
::::

{#quiz}
## Quiz de validation

```quiz
- q: Quel est le rôle de l'ordonnanceur d'Airflow ?
  options:
    - Exécuter le code des tâches
    - Créer les exécutions au bon moment et mettre en file les tâches dont les dépendances sont satisfaites
    - Afficher l'interface web
    - Stocker les journaux
  answer: 1
  explain: Les workers exécutent, le serveur d'API sert l'interface, la base garde l'état ; l'ordonnanceur décide.
- q: Une tâche lit un fichier de 2 Go et doit passer son contenu à la suivante. Que faire ?
  options:
    - Le renvoyer par XCom
    - Écrire le résultat dans un fichier ou une table, et passer seulement son chemin
    - L'envoyer dans l'extra d'un Asset
    - Le mettre dans params
  answer: 1
  explain: XCom et l'extra des Assets sont stockés dans la base de métadonnées - pour de petites valeurs seulement.
- q: Un DAG a start_date=datetime(2026, 12, 15). On le teste le 1er décembre. Que se passe-t-il ?
  options:
    - Il échoue avec une erreur claire
    - L'exécution réussit sans exécuter aucune tâche
    - Il attend le 15 décembre
    - Il traite le 1er décembre
  answer: 1
  explain: Les tâches d'une exécution datée d'avant leur start_date ne sont pas créées - et une exécution sans tâche est réussie. Un start_date toujours dans le passé, et fixe.
- q: Quelle tâche faut-il configurer avec retries=0 ?
  options:
    - L'appel à un serveur distant
    - Le contrôle du contrat de données
    - L'écriture d'une partition
    - L'enregistrement d'un modèle
  answer: 1
  explain: Une donnée invalide le restera ; réessayer retarde seulement l'alerte.
- q: Le rattrapage de janvier tourne avec --max-active-runs 4. Que limite ce réglage ?
  options:
    - Le nombre de nouvelles tentatives
    - Le nombre d'exécutions de ce rattrapage menées en parallèle
    - Le nombre de jours rattrapés
    - Le nombre de workers
  answer: 1
  explain: Il protège les ressources partagées (base, machine, source de données) pendant un rattrapage massif.
- q: Pourquoi le pipeline ColisVert est-il déclenché par l'Asset livraisons plutôt qu'à 06:45 ?
  options:
    - Parce que c'est plus rapide
    - Parce que le fichier arrive à une heure variable - un horaire fixe entraîne parfois sur les données de la veille, sans erreur visible
    - Parce qu'Airflow 3 ne gère plus les horaires
    - Parce que les Assets sont gratuits
  answer: 1
  explain: 8 jours sur 56, le fichier arrivait après 06:45. Déclencher par la donnée supprime ces succès trompeurs ; l'horaire reste en filet de sécurité.
```
