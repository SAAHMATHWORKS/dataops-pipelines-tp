"""Point d'entrée du projet MLflow (fichier MLproject, jour 2 après-midi).

Entraîne et évalue le modèle en un seul run MLflow, avec les hyperparamètres reçus
en arguments. Lancement normal, depuis la racine du dépôt :

    mlflow run . -P C=0.1 -P class_weight=balanced --env-manager local --experiment-name colisvert-retards

`mlflow run` crée le run, y note les paramètres, puis lance ce script en lui donnant
l'identifiant du run (variable MLFLOW_RUN_ID) : mlflow.start_run() s'y rattache.
Le script lit les jeux préparés par l'étape prepare (data/prepared) et n'écrit rien
dans models/ : il ne dérange pas le pipeline DVC.
"""

from __future__ import annotations

import argparse

import mlflow
import pandas as pd
from mlflow import sklearn as mlflow_sklearn
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score

from .commun import CATEGORIELLES, CIBLE, NUMERIQUES, PREPARE
from .suivi import _commit_git, _empreinte_donnees
from .train import construire_modele


def main() -> None:
    lecteur = argparse.ArgumentParser(description="Entraîner et évaluer le modèle ColisVert")
    lecteur.add_argument("--C", type=float, default=1.0)
    lecteur.add_argument("--class-weight", default="none", help="none ou balanced")
    lecteur.add_argument("--max-iter", type=int, default=1000)
    arguments = lecteur.parse_args()
    class_weight = None if arguments.class_weight == "none" else arguments.class_weight

    train = pd.read_csv(PREPARE / "train.csv")
    test = pd.read_csv(PREPARE / "test.csv")
    colonnes = CATEGORIELLES + NUMERIQUES

    with mlflow.start_run() as run:
        # mlflow run a déjà noté les paramètres du MLproject : on n'ajoute que ceux qui manquent
        # (MLflow refuse qu'un paramètre change de valeur dans un run).
        deja_notes = mlflow.get_run(run.info.run_id).data.params
        params = {"C": arguments.C, "class_weight": arguments.class_weight, "max_iter": arguments.max_iter}
        mlflow.log_params({nom: valeur for nom, valeur in params.items() if nom not in deja_notes})
        mlflow.set_tags({"commit_git": _commit_git(), "md5_donnees": _empreinte_donnees()})

        modele = construire_modele(arguments.C, class_weight, arguments.max_iter)
        modele.fit(train[colonnes], train[CIBLE])

        predictions = modele.predict(test[colonnes])
        probabilites = modele.predict_proba(test[colonnes])[:, 1]
        metriques = {
            "exactitude": round(accuracy_score(test[CIBLE], predictions), 3),
            "precision": round(precision_score(test[CIBLE], predictions), 3),
            "rappel": round(recall_score(test[CIBLE], predictions), 3),
            "f1": round(f1_score(test[CIBLE], predictions), 3),
            "roc_auc": round(roc_auc_score(test[CIBLE], probabilites), 3),
        }
        mlflow.log_metrics(metriques)
        mlflow_sklearn.log_model(modele, name="model", input_example=train[colonnes].head(2))

    print(f"projet MLflow : C={arguments.C}, class_weight={class_weight}")
    for nom, valeur in metriques.items():
        print(f"{nom:<10} : {valeur:.3f}")


if __name__ == "__main__":
    main()
