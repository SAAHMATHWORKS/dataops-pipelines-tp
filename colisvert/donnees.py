"""Données du fil rouge ColisVert, un transporteur qui veut prédire ses retards de livraison.

Tout est déterministe : la même graine donne exactement les mêmes données, sur toutes
les machines et avec toutes les versions de Python. On n'utilise ni `random` ni `numpy` :
un petit générateur pseudo-aléatoire (congruence linéaire) est écrit ci-dessous, le même
que dans la formation PySpark.

Utilisation en ligne de commande, depuis la racine du dépôt :

    python -m colisvert.donnees data

crée data/livraisons.csv et data/arrivees.csv, puis affiche un résumé. Dans un notebook :

    from colisvert.donnees import preparer_donnees
    preparer_donnees()
"""

from __future__ import annotations

import csv
import datetime
import sys
from pathlib import Path

DOSSIER_DATA = Path(__file__).resolve().parents[1] / "data"  # le dossier data/ du dépôt
PREMIER_JOUR = datetime.date(2026, 9, 7)  # un lundi
NB_JOURS = 56                             # 8 semaines, jusqu'au dimanche 1er novembre 2026

COLONNES_LIVRAISONS = [
    "id_colis",
    "date_expedition",
    "entrepot",
    "client",
    "creneau",
    "distance_km",
    "poids_kg",
    "meteo",
    "delai_promis_h",
    "delai_reel_h",
    "en_retard",
]


class Hasard:
    """Générateur pseudo-aléatoire minimal et reproductible."""

    def __init__(self, graine: int):
        self.etat = graine

    def entier(self, n: int) -> int:
        """Entier entre 0 et n - 1."""
        self.etat = (self.etat * 1103515245 + 12345) % 2**31
        return (self.etat // 65536) % n

    def choix(self, valeurs: list):
        """Un élément de la liste. Répéter un élément augmente sa probabilité."""
        return valeurs[self.entier(len(valeurs))]


def generer_livraisons(graine: int = 2026, nb_jours: int = NB_JOURS) -> list[dict]:
    """Les colis expédiés pendant 8 semaines (56 jours), un dictionnaire par colis.

    Avec nb_jours=63, on obtient 9 semaines : les 56 premiers jours sont exactement les mêmes,
    la 9e semaine s'ajoute à la fin.

    Le délai réel dépend de la distance, du poids, de la météo, de l'entrepôt et du créneau,
    plus une part de hasard. Un colis est en retard quand son délai réel dépasse le délai promis.
    """
    hasard = Hasard(graine)
    entrepots = ["Lille"] * 3 + ["Lyon"] * 3 + ["Nantes"] * 2 + ["Toulouse"] * 2
    lignes = []
    for jour in range(nb_jours):
        date = PREMIER_JOUR + datetime.timedelta(days=jour)
        semaine = date.weekday() < 5
        nombre = 90 + hasard.entier(41) if semaine else 30 + hasard.entier(21)
        for _ in range(nombre):
            entrepot = hasard.choix(entrepots)
            client = "pro" if hasard.entier(4) == 0 else "particulier"
            creneau = hasard.choix(["matin", "apres-midi", "soir"])
            distance = 5 + hasard.entier(296)                 # de 5 à 300 km
            poids = round(0.5 + hasard.entier(300) / 10, 1)   # de 0,5 à 30,4 kg
            meteo = "pluie" if hasard.entier(10) < 3 else "sec"
            promis = 24 if distance <= 150 else 48
            reel = (
                1
                + distance // 12
                + int(poids) // 6
                + (8 if meteo == "pluie" else 0)
                + (6 if entrepot == "Lille" else 0)
                + (4 if creneau == "soir" else 0)
                + hasard.entier(14)
            )
            lignes.append(
                {
                    "id_colis": f"CV{len(lignes) + 1:05d}",
                    "date_expedition": date.isoformat(),
                    "entrepot": entrepot,
                    "client": client,
                    "creneau": creneau,
                    "distance_km": distance,
                    "poids_kg": poids,
                    "meteo": meteo,
                    "delai_promis_h": promis,
                    "delai_reel_h": reel,
                    "en_retard": int(reel > promis),
                }
            )
    return lignes


def generer_livraisons_brutes(graine: int = 99) -> list[dict]:
    """Les mêmes livraisons, telles qu'elles arrivent vraiment : avec des défauts de qualité.

    Chaque défaut touche des colis différents, pour que chaque contrôle compte un seul type
    de problème :
    - 40 météos et 15 poids manquants (complétude) ;
    - 12 entrepôts mal orthographiés « Lile » (validité) ;
    - 20 dates au format jj/mm/aaaa au lieu de aaaa-mm-jj (validité) ;
    - 8 délais réels négatifs, impossibles (validité) ;
    - 10 colis dont la colonne en_retard contredit les délais (cohérence) ;
    - 25 lignes en double, chacune juste après sa ligne d'origine (unicité).
    """
    lignes = [dict(ligne) for ligne in generer_livraisons()]
    hasard = Hasard(graine)
    deja_choisies: set[int] = set()

    def tirer(nombre: int, condition=lambda ligne: True) -> list[int]:
        indices: list[int] = []
        while len(indices) < nombre:
            i = (hasard.entier(32768) * 32768 + hasard.entier(32768)) % len(lignes)
            if i not in deja_choisies and condition(lignes[i]):
                deja_choisies.add(i)
                indices.append(i)
        return indices

    for i in tirer(40):
        lignes[i]["meteo"] = ""
    for i in tirer(15):
        lignes[i]["poids_kg"] = ""
    for i in tirer(12, lambda ligne: ligne["entrepot"] == "Lille"):
        lignes[i]["entrepot"] = "Lile"
    for i in tirer(20):
        d = lignes[i]["date_expedition"]
        lignes[i]["date_expedition"] = f"{d[8:10]}/{d[5:7]}/{d[0:4]}"
    for i in tirer(8, lambda ligne: ligne["en_retard"] == 0):
        lignes[i]["delai_reel_h"] = -lignes[i]["delai_reel_h"]
    for i in tirer(10):
        lignes[i]["en_retard"] = 1 - lignes[i]["en_retard"]
    doublons = set(tirer(25))

    resultat = []
    for i, ligne in enumerate(lignes):
        resultat.append(ligne)
        if i in doublons:
            resultat.append(dict(ligne))
    return resultat


def generer_arrivees(graine: int = 7) -> list[dict]:
    """L'heure d'arrivée, chaque matin, du fichier des expéditions de la veille.

    Le fichier arrive normalement entre 06:05 et 06:44. Certains jours, un incident le retarde.
    """
    hasard = Hasard(graine)
    lignes = []
    for jour in range(NB_JOURS):
        date = PREMIER_JOUR + datetime.timedelta(days=jour)
        minutes = 6 * 60 + 5 + hasard.entier(40)
        if hasard.entier(10) == 0:          # environ un jour sur dix : incident
            minutes += 40 + hasard.entier(60)
        lignes.append({"date": date.isoformat(), "heure_arrivee": f"{minutes // 60:02d}:{minutes % 60:02d}"})
    return lignes


def ecrire_csv(lignes: list[dict], chemin: Path | str) -> Path:
    """Écrit les lignes dans un CSV (séparateur virgule, en-tête, UTF-8)."""
    chemin = Path(chemin)
    chemin.parent.mkdir(parents=True, exist_ok=True)
    with chemin.open("w", newline="", encoding="utf-8") as fichier:
        writer = csv.DictWriter(fichier, fieldnames=list(lignes[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(lignes)
    return chemin


def preparer_donnees(dossier: Path | str = DOSSIER_DATA) -> Path:
    """Crée livraisons.csv et arrivees.csv dans le dossier data/ du dépôt et affiche un résumé."""
    dossier = Path(dossier)
    livraisons = generer_livraisons()
    arrivees = generer_arrivees()
    ecrire_csv(livraisons, dossier / "livraisons.csv")
    ecrire_csv(arrivees, dossier / "arrivees.csv")
    ecrire_csv(generer_livraisons_brutes(), dossier / "livraisons_brutes.csv")
    retards = sum(ligne["en_retard"] for ligne in livraisons)
    print(f"livraisons.csv : {len(livraisons)} colis, dont {retards} en retard")
    print(f"arrivees.csv : {len(arrivees)} jours")
    print("livraisons_brutes.csv : les mêmes colis, avec des défauts de qualité")
    return dossier


if __name__ == "__main__":
    preparer_donnees(*sys.argv[1:2])
