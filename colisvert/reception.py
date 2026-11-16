"""Simule l'arrivée du fichier des expéditions (jour 3 après-midi).

Chaque matin, le système des entrepôts dépose data/livraisons.csv, enrichi des colis de la
veille. Pour le TP, on rejoue l'arrivée d'une nouvelle semaine : les données sont celles du
générateur ColisVert (graine 2026), donc identiques sur toutes les machines.

Usage : python -m colisvert.reception 9      (le fichier contient alors 9 semaines)
"""

from __future__ import annotations

import sys

from .donnees import DOSSIER_DATA, ecrire_csv, generer_livraisons


def main(semaines: int) -> None:
    lignes = generer_livraisons(nb_jours=7 * semaines)
    chemin = ecrire_csv(lignes, DOSSIER_DATA / "livraisons.csv")
    print(f"fichier reçu : {chemin.name}, {semaines} semaines, {len(lignes)} colis")


if __name__ == "__main__":
    main(int(sys.argv[1]))
