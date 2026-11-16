"""Contrôle qualité quotidien des taxis de New York (évaluation du jour 3 après-midi).

Compte, pour UNE journée, les courses qui violent les règles de qualité vues ce matin.
Même principe que pipeline/taxis_jour.py : la période est reçue en paramètre, la partition
du jour est réécrite à chaque passage (idempotent), via un fichier temporaire (atomique).

Usage : python -m pipeline.taxis_qualite 2024-01-15 2024-01-16
Écrit rapports/qualite/jour=2024-01-15/defauts.parquet
"""

from __future__ import annotations

import os
import sys

import duckdb

from .commun import RACINE

SOURCE = RACINE / "data" / "taxis" / "yellow_tripdata_2024-01.parquet"
SORTIE = RACINE / "rapports" / "qualite"

REQUETE = """
SELECT
    CAST($debut AS DATE)                                        AS jour,
    count(*)                                                    AS courses,
    count(*) FILTER (WHERE fare_amount <= 0)                    AS prix_negatif_ou_nul,
    count(*) FILTER (WHERE trip_distance = 0)                   AS distance_nulle,
    count(*) FILTER (WHERE passenger_count IS NULL)             AS passagers_manquants
FROM read_parquet($source)
WHERE tpep_pickup_datetime >= CAST($debut AS TIMESTAMP)
  AND tpep_pickup_datetime <  CAST($fin AS TIMESTAMP)
"""


def main(debut: str, fin: str) -> None:
    dossier = SORTIE / f"jour={debut}"
    dossier.mkdir(parents=True, exist_ok=True)
    final = dossier / "defauts.parquet"
    provisoire = dossier / "defauts.parquet.tmp"

    parametres = {"debut": debut, "fin": fin, "source": str(SOURCE)}
    defauts = duckdb.connect().execute(REQUETE, parametres).df()
    defauts.to_parquet(provisoire, index=False)
    os.replace(provisoire, final)

    ligne = defauts.iloc[0]
    print(f"{debut} : {ligne['courses']} courses, {ligne['prix_negatif_ou_nul']} prix <= 0, "
          f"{ligne['distance_nulle']} distances nulles, {ligne['passagers_manquants']} sans passagers")
    print(f"écrit : {final.relative_to(RACINE)}")


if __name__ == "__main__":
    main(*sys.argv[1:3])
