"""Définitions partagées par les étapes du pipeline ColisVert.

Les variables explicatives sont connues AU MOMENT DE L'EXPÉDITION : on peut donc
s'en servir pour prédire. delai_reel_h et en_retard ne sont connus qu'à la livraison :
delai_reel_h ne doit JAMAIS figurer parmi les variables (ce serait une fuite de données),
et en_retard est la cible.
"""

from __future__ import annotations

from pathlib import Path

import yaml

RACINE = Path(__file__).resolve().parents[1]
DATA = RACINE / "data"
PREPARE = DATA / "prepared"
MODELS = RACINE / "models"

CATEGORIELLES = ["entrepot", "client", "creneau", "meteo", "jour_semaine"]
NUMERIQUES = ["distance_km", "poids_kg", "delai_promis_h"]
CIBLE = "en_retard"

JOURS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]

PARAMS_DEFAUT = {
    "prepare": {"date_coupure": "2026-10-19"},
    "train": {"C": 1.0, "class_weight": None, "max_iter": 1000},
}


def charger_params() -> dict:
    """params.yaml s'il existe (pipeline DVC), sinon les valeurs par défaut (démos)."""
    fichier = RACINE / "params.yaml"
    params = {section: dict(valeurs) for section, valeurs in PARAMS_DEFAUT.items()}
    if fichier.exists():
        charges = yaml.safe_load(fichier.read_text()) or {}
        for section, valeurs in charges.items():
            params.setdefault(section, {}).update(valeurs or {})
    return params


def ajouter_jour_semaine(df):
    """Ajoute la colonne jour_semaine (lundi, mardi, …) à partir de la date d'expédition."""
    import pandas as pd

    numeros = pd.to_datetime(df["date_expedition"], format="%Y-%m-%d").dt.weekday
    df = df.copy()
    df["jour_semaine"] = numeros.map(dict(enumerate(JOURS)))
    return df
