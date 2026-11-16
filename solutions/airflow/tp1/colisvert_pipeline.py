"""TP 1 (jour 3 après-midi) : le pipeline ColisVert du jour 2, orchestré et rendu robuste.

    controler_donnees >> preparer >> entrainer >> evaluer >> barriere_qualite >> proposer_challenger

- Le contrat de données du jour 1 est vérifié AVANT d'entraîner : un fichier invalide arrête
  tout. Pas de nouvelle tentative pour cette tâche : une donnée fausse le restera.
- Chaque étape DVC est une tâche : DVC décide si l'étape doit tourner (rien n'a changé : elle
  est sautée), Airflow décide QUAND elle tourne et ce qu'on fait si elle échoue.
- Les autres tâches ont deux nouvelles tentatives : une panne passagère (serveur MLflow qui
  redémarre, réseau) se répare sans personne.
- La barrière de qualité applique la charte du jour 2 : sans rappel >= 0,80 ET précision
  >= 0,50, pas de challenger. Airflow propose ; promouvoir le champion reste une décision humaine.
"""

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
