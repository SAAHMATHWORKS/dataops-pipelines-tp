"""Suivi MLflow du pipeline ColisVert.

Tout le dialogue avec MLflow passe par ce module. Deux raisons :
- les scripts du pipeline restent lisibles : préparer, entraîner, évaluer ;
- sans serveur MLflow (variable MLFLOW_TRACKING_URI absente), le pipeline fonctionne
  quand même : le suivi est simplement désactivé, et un message l'indique sur la sortie
  d'erreur. Les métriques imprimées sont identiques dans les deux cas.

Le fichier models/run_id.txt relie les étapes : train.py y écrit l'identifiant de son
run MLflow, evaluate.py le relit pour accrocher ses métriques au même run.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

try:
    import mlflow
except ImportError:  # l'image des TP l'installe toujours ; utile hors conteneur
    mlflow = None

RACINE = Path(__file__).resolve().parents[1]
FICHIER_RUN = RACINE / "models" / "run_id.txt"
EXPERIENCE = "colisvert-retards"


def actif() -> bool:
    """Le suivi est actif quand MLflow est installé et qu'un serveur est déclaré."""
    if mlflow is None or not os.environ.get("MLFLOW_TRACKING_URI"):
        print("Suivi MLflow désactivé (MLFLOW_TRACKING_URI absent).", file=sys.stderr)
        return False
    return True


def _empreinte_donnees() -> str:
    """L'empreinte MD5 du fichier de données, lue dans son ticket DVC s'il existe."""
    ticket = RACINE / "data" / "livraisons.csv.dvc"
    if ticket.exists():
        for ligne in ticket.read_text().splitlines():
            ligne = ligne.strip()
            if ligne.startswith("- md5:") or ligne.startswith("md5:"):
                return ligne.split(":", 1)[1].strip()
    return "non suivi par DVC"


def _commit_git() -> str:
    try:
        resultat = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, cwd=RACINE, check=True,
        )
        return resultat.stdout.strip()
    except Exception:
        return "hors depot git"


def demarrer_entrainement(params: dict) -> None:
    """Ouvre un run MLflow, y note les paramètres, le commit Git et l'empreinte des données."""
    if not actif():
        FICHIER_RUN.parent.mkdir(parents=True, exist_ok=True)
        FICHIER_RUN.write_text("local")
        return
    mlflow.set_experiment(EXPERIENCE)
    run = mlflow.start_run(run_name=f"train-C{params.get('C')}")
    mlflow.log_params(params)
    mlflow.set_tags({"commit_git": _commit_git(), "md5_donnees": _empreinte_donnees()})
    FICHIER_RUN.parent.mkdir(parents=True, exist_ok=True)
    FICHIER_RUN.write_text(run.info.run_id)


def enregistrer_modele(modele, exemple_entree=None) -> None:
    """Attache le modèle entraîné au run ouvert."""
    if mlflow is None or mlflow.active_run() is None:
        return
    from mlflow import sklearn as mlflow_sklearn

    mlflow_sklearn.log_model(modele, name="model", input_example=exemple_entree)


def terminer_entrainement(metriques: dict) -> None:
    if mlflow is None or mlflow.active_run() is None:
        return
    mlflow.log_metrics(metriques)
    mlflow.end_run()


def journaliser_evaluation(metriques: dict, artefacts: list[Path] = ()) -> None:
    """Accroche les métriques d'évaluation au run écrit par train.py."""
    if not actif():
        return
    run_id = FICHIER_RUN.read_text().strip() if FICHIER_RUN.exists() else ""
    if not run_id or run_id == "local":
        print("Pas de run MLflow à compléter (models/run_id.txt absent).", file=sys.stderr)
        return
    client = mlflow.MlflowClient()
    for nom, valeur in metriques.items():
        client.log_metric(run_id, nom, valeur)
    for artefact in artefacts:
        client.log_artifact(run_id, str(artefact))
