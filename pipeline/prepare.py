"""Étape 1 du pipeline : préparer les jeux d'entraînement et de test.

Découpe TEMPORELLE, jamais aléatoire : on entraîne sur le passé, on teste sur la suite.
Un découpage aléatoire mélangerait des colis de la même journée dans les deux jeux et
donnerait une performance trop optimiste par rapport à la réalité.

Usage : python -m pipeline.prepare
"""

from __future__ import annotations

import pandas as pd

from .commun import CATEGORIELLES, CIBLE, DATA, NUMERIQUES, PREPARE, ajouter_jour_semaine, charger_params


def main() -> None:
    params = charger_params()["prepare"]
    date_coupure = params["date_coupure"]

    livraisons = pd.read_csv(DATA / "livraisons.csv")
    livraisons = ajouter_jour_semaine(livraisons)
    colonnes = CATEGORIELLES + NUMERIQUES + [CIBLE]

    train = livraisons[livraisons["date_expedition"] < date_coupure]
    test = livraisons[livraisons["date_expedition"] >= date_coupure]

    PREPARE.mkdir(parents=True, exist_ok=True)
    train[colonnes].to_csv(PREPARE / "train.csv", index=False)
    test[colonnes].to_csv(PREPARE / "test.csv", index=False)

    print(f"train : {len(train)} colis, du {train['date_expedition'].min()} au {train['date_expedition'].max()}")
    print(f"test  : {len(test)} colis, du {test['date_expedition'].min()} au {test['date_expedition'].max()}")
    print(f"taux de retard train : {train[CIBLE].mean():.1%} | test : {test[CIBLE].mean():.1%}")


if __name__ == "__main__":
    main()
