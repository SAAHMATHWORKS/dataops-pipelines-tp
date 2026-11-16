"""Indicateurs quotidiens des taxis de New York (jour 3 après-midi).

Un script PARAMÉTRÉ PAR LA PÉRIODE, comme dans le module d'orchestration du MLOps Zoomcamp :
il ne choisit pas lui-même le jour à traiter (pas de « hier » calculé avec l'horloge), il le
reçoit. C'est l'orchestrateur qui le lui donne : un jour par exécution, et autant d'exécutions
qu'il faut pour rattraper un mois entier (backfill).

Usage : python -m pipeline.taxis_jour 2024-01-15 2024-01-16
        (début inclus, fin exclue : l'intervalle de données d'Airflow)

Écrit rapports/taxis/jour=2024-01-15/indicateurs.parquet. Relancer le même jour réécrit le
même fichier, sans doublon : le script est idempotent. L'écriture passe par un fichier
temporaire renommé à la fin : un lecteur ne voit jamais un fichier à moitié écrit.
"""

from __future__ import annotations

import os
import sys

import duckdb

from .commun import RACINE

SOURCE = RACINE / "data" / "taxis" / "yellow_tripdata_2024-01.parquet"
SORTIE = RACINE / "rapports" / "taxis"

# Le contrat de qualité du matin, appliqué à une seule journée.
REQUETE = """
SELECT
    CAST($debut AS DATE)                                  AS jour,
    count(*)                                              AS courses,
    round(sum(fare_amount), 2)                            AS prix,
    round(sum(tip_amount), 2)                             AS pourboires,
    round(sum(tip_amount) / sum(fare_amount) * 100, 2)    AS taux
FROM read_parquet($source)
WHERE tpep_pickup_datetime >= CAST($debut AS TIMESTAMP)
  AND tpep_pickup_datetime <  CAST($fin AS TIMESTAMP)
  AND payment_type = 1 AND fare_amount > 0 AND tip_amount >= 0
"""


def main(debut: str, fin: str) -> None:
    dossier = SORTIE / f"jour={debut}"
    dossier.mkdir(parents=True, exist_ok=True)
    final = dossier / "indicateurs.parquet"
    provisoire = dossier / "indicateurs.parquet.tmp"

    parametres = {"debut": debut, "fin": fin, "source": str(SOURCE)}
    indicateurs = duckdb.connect().execute(REQUETE, parametres).df()
    indicateurs.to_parquet(provisoire, index=False)
    os.replace(provisoire, final)

    ligne = indicateurs.iloc[0]
    print(f"{debut} : {ligne['courses']} courses valides, taux de pourboire {ligne['taux']} %")
    print(f"écrit : {final.relative_to(RACINE)}")


if __name__ == "__main__":
    main(*sys.argv[1:3])
