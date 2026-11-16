"""Proposer le dernier modèle entraîné comme challenger dans le registre MLflow (jour 3).

Appelé par Airflow, seulement si la barrière de qualité est franchie. Le script est
IDEMPOTENT : relancé dix fois sur le même run d'entraînement, il crée une seule version.
C'est indispensable dans un pipeline orchestré, où une tâche peut être rejouée (nouvelle
tentative après une panne, relance manuelle, rattrapage).

Il propose, il ne promeut pas : l'alias champion reste une décision humaine, prise avec la
règle de promotion du jour 2.

Usage : python -m pipeline.registre
"""

from __future__ import annotations

import mlflow
from mlflow import MlflowClient

from .suivi import FICHIER_RUN

NOM = "colisvert-retards"
ALIAS = "challenger"


def main() -> None:
    run_id = FICHIER_RUN.read_text().strip()
    client = MlflowClient()
    deja = [v for v in client.search_model_versions(f"run_id = '{run_id}'") if v.name == NOM]
    if deja:
        version = max(int(v.version) for v in deja)
        print(f"ce run d'entraînement est déjà enregistré (version {version}) : aucune nouvelle version")
    else:
        version = int(mlflow.register_model(f"runs:/{run_id}/model", NOM, tags={"source": "airflow"}).version)
        print(f"nouvelle version enregistrée : {version}")
    client.set_registered_model_alias(NOM, ALIAS, str(version))
    print(f"alias {ALIAS} -> version {version}")


if __name__ == "__main__":
    main()
