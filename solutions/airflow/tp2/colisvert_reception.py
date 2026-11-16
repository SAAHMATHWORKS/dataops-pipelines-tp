"""TP 2 (jour 3 après-midi) : le producteur. Il reçoit le fichier, le contrôle, le publie.

La dernière tâche déclare l'Asset « livraisons » mis à jour (outlets). Un Asset n'est mis à
jour que si sa tâche RÉUSSIT : un fichier qui viole le contrat n'atteint jamais les DAG qui
en dépendent. L'événement transporte des métadonnées (extra) lisibles en aval.
"""

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
