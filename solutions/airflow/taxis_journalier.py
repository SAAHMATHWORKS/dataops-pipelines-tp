"""Un DAG quotidien et son rattrapage (jour 3 après-midi, notion 4).

Chaque exécution traite UNE journée : son intervalle de données [début, fin[. Le script
pipeline/taxis_jour.py reçoit ces deux dates ; il ne lit jamais l'horloge. On peut donc
rejouer n'importe quel jour passé, autant de fois qu'on veut, avec le même résultat.

Rattraper janvier 2024 (31 exécutions) :
    airflow backfill create --dag-id taxis_journalier --from-date 2024-01-01 --to-date 2024-01-31
"""

from __future__ import annotations

from datetime import datetime

from airflow.sdk import CronDataIntervalTimetable, dag, task

PROJET = "/home/lab/projet"


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


taxis_journalier()
