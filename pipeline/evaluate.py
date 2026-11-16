"""Étape 3 du pipeline : évaluer le modèle sur les deux dernières semaines.

Les métriques sont écrites dans metrics.json : DVC les suit (dvc metrics show,
dvc metrics diff) et MLflow les accroche au run de l'entraînement.

Usage : python -m pipeline.evaluate
"""

from __future__ import annotations

import json

import joblib
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score

from . import suivi
from .commun import CATEGORIELLES, CIBLE, MODELS, NUMERIQUES, PREPARE, RACINE


def main() -> None:
    modele = joblib.load(MODELS / "modele.joblib")
    test = pd.read_csv(PREPARE / "test.csv")
    X, y = test[CATEGORIELLES + NUMERIQUES], test[CIBLE]

    predictions = modele.predict(X)
    probabilites = modele.predict_proba(X)[:, 1]

    metriques = {
        "exactitude": round(accuracy_score(y, predictions), 3),
        "precision": round(precision_score(y, predictions), 3),
        "rappel": round(recall_score(y, predictions), 3),
        "f1": round(f1_score(y, predictions), 3),
        "roc_auc": round(roc_auc_score(y, probabilites), 3),
    }

    fichier = RACINE / "metrics.json"
    fichier.write_text(json.dumps(metriques, indent=2) + "\n")
    suivi.journaliser_evaluation(metriques, artefacts=[fichier])

    print(f"évaluation sur {len(test)} colis de test")
    for nom, valeur in metriques.items():
        print(f"{nom:<10} : {valeur:.3f}")


if __name__ == "__main__":
    main()
