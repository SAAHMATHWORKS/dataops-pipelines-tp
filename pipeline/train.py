"""Étape 2 du pipeline : entraîner le modèle de prédiction des retards.

Le modèle est une régression logistique précédée d'un encodage un-parmi-n
(one-hot) des variables catégorielles. Le tout est un Pipeline scikit-learn :
l'encodage appris sur le train s'applique tel quel à toute donnée future,
et le fichier modele.joblib contient l'ensemble.

Usage : python -m pipeline.train
"""

from __future__ import annotations

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from . import suivi
from .commun import CATEGORIELLES, CIBLE, MODELS, NUMERIQUES, PREPARE, charger_params


def construire_modele(C: float, class_weight, max_iter: int) -> Pipeline:
    """Encodage un-parmi-n des catégories + régression logistique."""
    encodage = ColumnTransformer(
        [("categories", OneHotEncoder(handle_unknown="ignore"), CATEGORIELLES)],
        remainder="passthrough",  # les colonnes numériques passent telles quelles
    )
    modele = LogisticRegression(C=C, class_weight=class_weight, max_iter=max_iter, random_state=2026)
    return Pipeline([("encodage", encodage), ("regression", modele)])


def main() -> None:
    params = charger_params()["train"]
    train = pd.read_csv(PREPARE / "train.csv")
    X, y = train[CATEGORIELLES + NUMERIQUES], train[CIBLE]

    suivi.demarrer_entrainement(params)

    modele = construire_modele(params["C"], params["class_weight"], params["max_iter"])
    modele.fit(X, y)

    f1_train = f1_score(y, modele.predict(X))
    nb_variables = modele.named_steps["encodage"].transform(X.head(1)).shape[1]

    MODELS.mkdir(parents=True, exist_ok=True)
    joblib.dump(modele, MODELS / "modele.joblib")

    suivi.enregistrer_modele(modele, exemple_entree=X.head(2))
    suivi.terminer_entrainement({"f1_train": f1_train})

    print(f"modèle entraîné sur {len(train)} colis, {nb_variables} variables après encodage")
    print(f"F1 sur le train : {f1_train:.3f}")
    print("modèle écrit dans models/modele.joblib")


if __name__ == "__main__":
    main()
