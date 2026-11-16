"""Premier DAG (jour 3 après-midi, notion 2) : le fichier arrive-t-il à l'heure ?

Trois tâches, deux façons d'écrire une tâche :
- @task : une fonction Python, exécutée par l'interpréteur d'Airflow ;
- @task.bash : une commande, exécutée par le shell, avec le Python du projet.
Ce que lire_arrivees() renvoie passe à mesurer() par XCom : c'est l'appel de fonction
qui crée à la fois la dépendance et le passage de la donnée.
"""

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
