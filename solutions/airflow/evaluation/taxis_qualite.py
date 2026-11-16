"""Corrigé de l'évaluation du jour 3 après-midi : le contrôle qualité quotidien des taxis."""

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
