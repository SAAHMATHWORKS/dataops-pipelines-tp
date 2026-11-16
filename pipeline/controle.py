"""Contrôle du contrat de données des livraisons (jour 3 après-midi).

C'est le contrat exécutable du jour 1 (Cellule bonus C), devenu une étape du pipeline :
l'orchestrateur le vérifie AVANT d'entraîner. Un fichier qui viole le contrat arrête tout,
tôt et fort, au lieu de produire un modèle faux, tard et en silence.

Usage : python -m pipeline.controle data/livraisons.csv
Code de sortie 0 si le contrat est respecté, 1 sinon (la tâche Airflow échoue).
"""

from __future__ import annotations

import sys

import pandas as pd

CONTRAT = {
    "id_colis": {"unique": True},
    "entrepot": {"valeurs": ["Lille", "Lyon", "Nantes", "Toulouse"]},
    "date_expedition": {"format": r"\d{4}-\d{2}-\d{2}"},
    "poids_kg": {"obligatoire": True},
    "meteo": {"obligatoire": True},
    "delai_reel_h": {"minimum": 0},
}


def controler_contrat(df: pd.DataFrame, contrat: dict) -> pd.DataFrame:
    """Vérifie chaque règle du contrat et compte les lignes qui la violent."""
    lignes = []
    for colonne, regles in contrat.items():
        serie = df[colonne]
        if regles.get("unique"):
            lignes.append((colonne, "unique", int(serie.duplicated().sum())))
        if "valeurs" in regles:
            lignes.append((colonne, "valeurs autorisées", int((~serie.isin(regles["valeurs"])).sum())))
        if "format" in regles:
            lignes.append((colonne, "format", int((~serie.str.fullmatch(regles["format"])).sum())))
        if regles.get("obligatoire"):
            lignes.append((colonne, "obligatoire", int(serie.isna().sum())))
        if "minimum" in regles:
            lignes.append((colonne, "minimum", int((serie < regles["minimum"]).sum())))
    return pd.DataFrame(lignes, columns=["colonne", "regle", "violations"])


def main() -> None:
    chemin = sys.argv[1] if len(sys.argv) > 1 else "data/livraisons.csv"
    df = pd.read_csv(chemin)
    rapport = controler_contrat(df, CONTRAT)
    print(f"{chemin} : {len(df)} lignes de données")
    print(rapport.to_string(index=False))
    if (rapport["violations"] == 0).all():
        print("Contrat respecté : le pipeline peut continuer.")
    else:
        print(f"Contrat violé ({int(rapport['violations'].sum())} violations) : arrêt du pipeline.")
        sys.exit(1)


if __name__ == "__main__":
    main()
