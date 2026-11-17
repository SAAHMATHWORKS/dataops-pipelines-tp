---
subtitle: >-
  Planifier, c'est répondre à deux questions qu'on confond souvent : quand l'exécution part-elle,
  et quelle période traite-t-elle ? Airflow 3 a changé sa réponse par défaut. On écrit un script
  qui reçoit sa journée, comme dans le MLOps Zoomcamp, un DAG qui la lui donne, puis on rattrape
  tout janvier 2024 en une commande. La somme des 31 jours doit redonner le chiffre de ce matin.
objectives:
  - Choisir une forme de planification - aucune, horaire, intervalle, donnée, combinaison
  - Distinguer le moment d'une exécution et la période qu'elle traite (intervalle de données)
  - Expliquer catchup, start_date et end_date
  - Rattraper une période passée avec airflow backfill create, et en contrôler le résultat
  - Écrire des partitions idempotentes et atomiques
---

{#formes}
## Les formes de planification

L'argument `schedule` du DAG accepte six formes :

| Forme | Exemple | Sens |
|---|---|---|
| Aucune | `schedule=None` | Seulement à la demande (interface, commande, API) |
| Expression cron ou raccourci | `"45 6 * * *"`, `"@daily"` | À ces instants précis |
| Durée | `timedelta(hours=6)` | Toutes les 6 heures, depuis `start_date` |
| Objet *timetable* | `CronTriggerTimetable(...)`, `CronDataIntervalTimetable(...)` | Le contrôle complet : instants, fuseau horaire, intervalle de données |
| Données | `schedule=LIVRAISONS` (un Asset) | Dès que la donnée est mise à jour (TP 2) |
| Combinaison | `AssetOrTimeSchedule(...)` | Dès que la donnée arrive, **et aussi** à heure fixe (TP 2) |

**Lire une expression cron.** Cinq champs : minute, heure, jour du mois, mois, jour de la semaine. `45 6 * * *` : à 6 h 45, tous les jours. `0 7 * * 1-5` : à 7 h, du lundi au vendredi. `0 0 1 * *` : le 1er de chaque mois à minuit. Précisez **toujours** le fuseau horaire (`timezone="Europe/Paris"`) : sans lui, l'heure est en UTC, et 06:45 UTC est 07:45 à Paris en hiver.

{#intervalle}
## Quand part l'exécution, et quelle journée traite-t-elle ?

**L'analogie du relevé bancaire.** Le relevé de janvier est édité le 1er février : il **couvre** du 1er au 31 janvier et **paraît** une fois le mois terminé. On ne peut pas éditer le relevé de janvier le 15 janvier. Un traitement quotidien, c'est pareil : celui du 15 janvier ne peut tourner qu'une fois le 15 terminé, donc le 16 à 00:00 au plus tôt.

Airflow propose deux familles de planification :

| | **Déclenchement** (*trigger*) | **Intervalle de données** (*data interval*) |
|---|---|---|
| Classe | `CronTriggerTimetable` | `CronDataIntervalTimetable` |
| Question à laquelle elle répond | « À quelle heure lancer ? » | « Quelle période traiter ? » |
| `data_interval_start`, `data_interval_end` | égaux, tous deux à l'instant du déclenchement | le début et la fin de la période |
| Usage typique | « réentraîner chaque matin à 06:45 » | « calculer les indicateurs de chaque journée » |
| Valeur par défaut d'une expression cron | **Airflow 3** | Airflow 2 |

::: callout warn Le piège de la migration vers Airflow 3
Dans Airflow 2, `schedule="@daily"` donnait un intervalle d'un jour : le run « du 15 » traitait le 15 et partait le 16. Dans Airflow 3, la même ligne donne un **déclenchement** : un run le 15 à 00:00, avec un intervalle vide. Un DAG migré tel quel qui lit `data_interval_start` et `data_interval_end` filtre alors une période vide et produit **zéro ligne, sans erreur**. Quand un DAG traite des périodes, déclarez la planification explicitement, comme ci-dessous.
:::

{#catchup}
## catchup, start_date, end_date

- `start_date` : la première date pour laquelle une exécution planifiée peut exister.
- `end_date` : la dernière ; au-delà, l'ordonnanceur ne crée plus rien. Nos données de taxis s'arrêtent fin janvier 2024 : on borne le DAG.
- `catchup` : au premier démarrage d'un DAG dont `start_date` est passée, faut-il créer **toutes** les exécutions manquées ? `False` par défaut dans Airflow 3. Avec `catchup=True` et un `start_date` en 2024, un DAG quotidien activé aujourd'hui lancerait d'un coup plus de 1 000 exécutions.

**Le rattrapage se fait donc à la demande**, avec une période choisie : c'est le **backfill**. Airflow 3 en a fait une fonction de premier plan : il est créé par la commande `airflow backfill create` ou depuis l'interface, exécuté par l'ordonnanceur comme n'importe quelle exécution, et visible dans l'historique.

{#script}
## Un script qui reçoit sa journée

Le Zoomcamp transforme son notebook en script qui reçoit `--year` et `--month`. Le nôtre reçoit une journée, sous la forme d'un intervalle `[début, fin[` : exactement ce qu'Airflow fournit.

```python title="pipeline/taxis_jour.py (extrait)"
REQUETE = """
SELECT
    CAST($debut AS DATE)                                  AS jour,
    count(*)                                              AS courses,
    round(sum(fare_amount), 2)                            AS prix,
    round(sum(tip_amount), 2)                             AS pourboires,
    round(sum(tip_amount) / sum(fare_amount) * 100, 2)    AS taux
FROM read_parquet($source)
WHERE tpep_pickup_datetime >= CAST($debut AS TIMESTAMP)
  AND tpep_pickup_datetime <  CAST($fin AS TIMESTAMP)
  AND payment_type = 1 AND fare_amount > 0 AND tip_amount >= 0
"""


def main(debut: str, fin: str) -> None:
    dossier = SORTIE / f"jour={debut}"
    dossier.mkdir(parents=True, exist_ok=True)
    final = dossier / "indicateurs.parquet"
    provisoire = dossier / "indicateurs.parquet.tmp"

    parametres = {"debut": debut, "fin": fin, "source": str(SOURCE)}
    indicateurs = duckdb.connect().execute(REQUETE, parametres).df()
    indicateurs.to_parquet(provisoire, index=False)
    os.replace(provisoire, final)
```

Trois choix font sa robustesse :

1. **Le contrat de qualité du matin**, réutilisé à l'identique : le total des 31 journées devra redonner les 2 318 848 courses valides de ce matin.
2. **Une partition par journée** (`rapports/taxis/jour=2024-01-15/`) : relancer le 15 **réécrit** sa partition, sans toucher aux autres et sans doublon. C'est l'idempotence. Le nommage `colonne=valeur` est celui des partitions Hive, que DuckDB, Spark et pandas savent relire comme une colonne.
3. **Une écriture atomique** : le fichier est écrit sous un nom provisoire, puis renommé (`os.replace`). Un renommage dans un même dossier est instantané : un lecteur voit l'ancien fichier ou le nouveau, jamais un fichier à moitié écrit.

Le DAG, lui, se contente de passer l'intervalle au script :

```python title="solutions/airflow/taxis_journalier.py (extrait)"
@dag(
    dag_id="taxis_journalier",
    # Un intervalle de données par jour, de minuit à minuit (UTC) ; l'exécution part à la fin.
    schedule=CronDataIntervalTimetable("0 0 * * *", timezone="UTC"),
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 1, 31),   # nos données s'arrêtent fin janvier 2024
    catchup=False,                    # le rattrapage se fait à la demande, avec backfill
    max_active_runs=4,
    tags=["taxis", "jour3"],
)
def taxis_journalier():
    @task.bash
    def indicateurs_du_jour(data_interval_start=None, data_interval_end=None) -> str:
        debut = data_interval_start.strftime("%Y-%m-%d")
        fin = data_interval_end.strftime("%Y-%m-%d")
        return f"cd {PROJET} && python -m pipeline.taxis_jour {debut} {fin}"

    indicateurs_du_jour()
```

{#backfill}
## Rattraper janvier 2024

Le DAG `taxis_journalier` traite une journée par exécution. Rattraper janvier, c'est lui demander **31 exécutions**, une par intervalle de données. On commence par un seul jour, pour vérifier, puis le mois entier.

:::: lab TP guidé | Un jour, puis tout le mois | 18 min
**1. Posez le DAG et activez-le.** Dans le terminal de la VM :

```bash title="Terminal de la VM"
cd ~/dataops-pipelines-tp
cp solutions/airflow/taxis_journalier.py dags/
docker compose exec airflow airflow dags list-import-errors
docker compose exec airflow airflow dags unpause taxis_journalier
```

Si `unpause` répond `No paused DAGs were found`, Airflow n'a pas encore lu le nouveau fichier (cela prend quelques secondes) : relancez la commande, ou attendez que `taxis_journalier` apparaisse dans l'interface. Une fois activé, rien ne démarre : `end_date` est passée depuis longtemps, et `catchup=False`. L'ordonnanceur n'a rien à planifier. Le travail viendra du rattrapage.

**2. Un seul jour, le 15 janvier.** Un rattrapage d'une journée est la façon la plus sûre de tester un DAG qui traite des périodes : l'exécution est créée exactement comme le seront les 30 autres.

```bash title="Terminal de la VM"
docker compose exec airflow airflow backfill create --dag-id taxis_journalier \
  --from-date 2024-01-15 --to-date 2024-01-15
```

Dans l'interface, le DAG `taxis_journalier` montre une exécution dont la **date logique** est le 15 janvier, et dont l'identifiant se termine par `2024-01-16` : elle couvre le 15, et serait partie le 16 à minuit. Le journal de sa tâche (onglet **Logs**) contient :

```plaintext title="Journal de indicateurs_du_jour (extrait)"
2024-01-15 : 61260 courses valides, taux de pourboire 22.35 %
écrit : rapports/taxis/jour=2024-01-15/indicateurs.parquet
```

**3. Le mois entier, d'abord à blanc.** `--dry-run` affiche ce que ferait le rattrapage, sans rien créer :

```bash title="Terminal de la VM"
docker compose exec airflow airflow backfill create --dag-id taxis_journalier \
  --from-date 2024-01-01 --to-date 2024-01-31 --dry-run
```

```plaintext title="Sortie attendue (extrait)"
Performing dry run of backfill.
Printing params:
    - dag_id = taxis_journalier
    - from_date = 2024-01-01 00:00:00+00:00
    - to_date = 2024-01-31 00:00:00+00:00
    - max_active_runs = None
    - reverse = False
    - dag_run_conf = None
    - reprocess_behavior = None
    - run_on_latest_version = True
Runs to be attempted:
…
| 2024-01-14 00:00:00+00:00 |                 |                  |
+---------------------------+-----------------+------------------+
| 2024-01-16 00:00:00+00:00 |                 |                  |
+---------------------------+-----------------+------------------+
…
| 2024-01-31 00:00:00+00:00 |                 |                  |
+---------------------------+-----------------+------------------+
```

Le tableau liste **30** dates logiques, du 1er au 31 janvier : il en manque une, le 15, qui a déjà une exécution réussie. Les colonnes `partition_key` et `partition_date` servent aux DAG partitionnés, une nouveauté d'Airflow 3.4 qu'on n'utilise pas ici.

**4. Puis pour de vrai,** avec au plus 4 journées en parallèle :

```bash title="Terminal de la VM"
docker compose exec airflow airflow backfill create --dag-id taxis_journalier \
  --from-date 2024-01-01 --to-date 2024-01-31 --max-active-runs 4
```

Si Airflow répond `AlreadyRunningBackfill: Another backfill is running for Dag taxis_journalier`, le rattrapage du 15 n'est pas encore **clos** : l'ordonnanceur le ferme quelques secondes après le passage au vert. Un seul rattrapage à la fois par DAG : attendez un instant et relancez la commande. Même remède pour `database is locked` : la base SQLite de la VM est occupée par l'ordonnanceur ; en production, Airflow utilise PostgreSQL, qui accepte les écritures simultanées.

Dans l'interface (vue **Grid**), les colonnes se remplissent de vert, quatre par quatre : moins d'une minute au total. Le 15 n'est **pas** refait : il existe déjà une exécution réussie pour lui, et le comportement par défaut (`--reprocess-behavior none`) ne refait que ce qui manque. Avec `failed`, on referait aussi les échecs ; avec `completed`, tout.

::: hint
Les runs restent en file (`queued`, gris) plus d'une minute ? L'ordonnanceur s'est peut-être arrêté sur une erreur de la base SQLite : cela arrive, rarement, quand plusieurs commandes y écrivent en même temps. Le service `airflow` le surveille et redémarre seul en une à deux minutes (`docker compose ps` le montre de nouveau `Up`), puis les runs en file reprennent. S'il ne revient pas : `docker compose restart airflow`. En production, ce risque disparaît avec une base PostgreSQL et un ordonnanceur supervisé (Kubernetes, systemd).
:::

**5. Relisez les 31 partitions** dans le notebook `j3-apres-midi.ipynb`. DuckDB lit tous les fichiers d'un coup grâce au motif `*` :

```python title="Cellule 3 : les 31 journées de janvier"
import duckdb
from pipeline.commun import RACINE

jours = duckdb.sql(
    f"SELECT * FROM read_parquet('{RACINE}/rapports/taxis/*/indicateurs.parquet') ORDER BY jour"
).df()
print(f"{len(jours)} journées, {jours['courses'].sum():,} courses valides")
print(f"taux de pourboire sur le mois : {jours['pourboires'].sum() / jours['prix'].sum() * 100:.2f} %")
print("les 3 journées les plus chargées :")
print(jours.nlargest(3, "courses")[["jour", "courses", "taux"]].to_string(index=False))
print("les 3 plus calmes :")
print(jours.nsmallest(3, "courses")[["jour", "courses", "taux"]].to_string(index=False))
```

```plaintext title="Sortie attendue"
31 journées, 2,318,848 courses valides
taux de pourboire sur le mois : 22.47 %
les 3 journées les plus chargées :
      jour  courses  taux
2024-01-25    88590 22.78
2024-01-27    87838 22.26
2024-01-18    87158 22.81
les 3 plus calmes :
      jour  courses  taux
2024-01-07    52631 21.93
2024-01-01    53573 21.45
2024-01-02    55725 21.34
```

**La somme des 31 partitions redonne exactement les 2 318 848 courses valides de ce matin**, calculées alors d'une seule requête sur tout le mois. C'est la meilleure vérification d'un rattrapage : aucun jour oublié, aucun jour compté deux fois. Les journées calmes se comprennent avec un calendrier : le 1er janvier, férié, le 2, encore en vacances pour beaucoup, et le dimanche 7. Les plus chargées sont des jeudis et un samedi. Le pipeline compte ; l'explication reste un travail d'analyste.

::: hint
`Dag 'taxis_journalier' not found` : le processeur de DAG n'a pas encore lu le fichier ; attendez quelques secondes. Les exécutions restent grises (*queued*) : le DAG est en pause, relancez `airflow dags unpause taxis_journalier`. `No files found that match the pattern` dans la Cellule 3 : le rattrapage n'est pas terminé, ou les données des taxis ne sont pas dans `data/taxis` (TP du matin).
:::
::::

::: callout warn Le piège du test manuel d'un DAG à intervalles
`airflow dags test taxis_journalier 2024-01-15` traite le **14** janvier, pas le 15. Pour un test manuel, Airflow considère la date donnée comme le moment où l'exécution **part**, et lui attribue l'intervalle qui se **termine** à cet instant : le relevé édité le 15 couvre le 14. Les exécutions planifiées et les rattrapages, eux, sont datés du **début** de leur intervalle. D'où le conseil de l'étape 2 : tester un DAG à intervalles par un rattrapage d'une journée.
:::

{#quiz}
## Quiz

```quiz
- q: Un DAG planifié par CronDataIntervalTimetable("0 0 * * *") a une exécution de date logique 2024-01-15. Quelle période traite-t-elle, et quand part-elle ?
  options:
    - Le 14 janvier ; elle part le 15 à minuit
    - Le 15 janvier ; elle part le 16 à minuit
    - Le 15 janvier ; elle part le 15 à minuit
    - Tout janvier
  answer: 1
  explain: Pour une exécution planifiée ou un rattrapage, la date logique est le début de l'intervalle ; l'exécution part une fois l'intervalle terminé.
- q: Un DAG migré d'Airflow 2, planifié par schedule="@daily", filtre ses données entre data_interval_start et data_interval_end. Sous Airflow 3, il produit zéro ligne. Pourquoi ?
  options:
    - Airflow 3 ne lit plus les dates
    - Par défaut, une expression cron donne un déclenchement sans intervalle - début et fin sont égaux, la période est vide
    - Le fuseau horaire a changé
    - catchup est désactivé
  answer: 1
  explain: Il faut déclarer explicitement CronDataIntervalTimetable, ou changer le réglage create_cron_data_intervals.
- q: On rattrape janvier alors que le 15 a déjà une exécution réussie. Avec le comportement par défaut, que devient le 15 ?
  options:
    - Il est refait
    - Il est conservé tel quel ; seules les journées manquantes sont créées
    - Le rattrapage échoue
    - Le 15 est supprimé
  answer: 1
  explain: --reprocess-behavior vaut none par défaut. failed refait aussi les échecs, completed refait tout.
- q: Pourquoi une partition par journée, réécrite à chaque passage ?
  options:
    - Pour gagner de la place
    - Pour que rejouer un jour remplace son résultat sans doublon et sans toucher aux autres jours
    - Parce que Parquet l'impose
    - Pour aller plus vite
  answer: 1
  explain: C'est l'idempotence appliquée aux données - la condition pour pouvoir rattraper et relancer sans risque.
- q: Pourquoi borner taxis_journalier avec end_date ?
  options:
    - Pour accélérer le rattrapage
    - Parce que les données s'arrêtent fin janvier 2024 - sans borne, l'ordonnanceur pourrait planifier des journées sans données
    - Parce qu'Airflow l'exige
    - Pour éviter les nouvelles tentatives
  answer: 1
  explain: Une exécution pour un jour sans données produirait une partition vide - un résultat faux qui a l'air juste.
```
