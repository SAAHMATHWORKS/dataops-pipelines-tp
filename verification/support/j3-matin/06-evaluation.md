---
subtitle: >-
  La commission des taxis vous confie un audit rapide : combien de courses violent les règles de
  qualité, que valent les courses par arrondissement, et la répartition des paiements est-elle la
  même selon le moteur ? Pour finir, un chiffrage de décision, comme ce matin.
objectives:
  - Compter les violations d'un contrat de qualité en une seule requête SQL
  - Joindre un fichier Parquet et une table de référence, et vérifier un résultat avec un second moteur
  - Exécuter une requête avec Spark et prouver qu'un filtre est poussé jusqu'au fichier
  - Chiffrer deux options et trouver leur point de bascule
# Barème : 14 points pour les étapes (indiqués sur chaque étape) + 6 points pour le QCM
quiz_points: 6
---

{#consignes}
## Consignes

**Scénario.** Avant de publier des statistiques, la commission veut un audit de son fichier de janvier 2024 : la qualité, une première analyse par arrondissement, et un contrôle croisé entre deux moteurs. On vous demande aussi de chiffrer l'hébergement de l'outil d'analyse.

- **Durée :** 30 minutes, en autonomie. Le formateur passe voir chacun.
- **Où :** un notebook neuf `j3-matin-evaluation.ipynb` (dossier `notebooks`). Les données importées ce matin doivent être dans `data/taxis`.
- **Validation :** chaque étape se termine par une **preuve** : collez la sortie demandée et cliquez sur « Envoyer ma preuve ».
- **Barème :** 14 points pour les 4 étapes, 6 points pour le QCM final (une seule tentative par question).
- Les corrections sont là si vous bloquez, mais essayez d'abord.

::: widget task-progress
:::

{#defauts}
## Compter les défauts

:::: task Étape 1 | Les violations du contrat, en une requête | 7 min | 3 pts
Avec DuckDB, en **une seule** requête sur le fichier Parquet, comptez :

1. le nombre total de lignes ;
2. les courses prises en charge **hors** de janvier 2024 ;
3. les courses dont le prix (`fare_amount`) est négatif ou nul ;
4. les courses dont la distance (`trip_distance`) est nulle ;
5. les courses sans nombre de passagers (`passenger_count` manquant).

Affichez le résultat avec `.df().T`, pour avoir une ligne par compteur.

::: proof Collez la sortie complète de votre cellule
:::

::: hint
`count(*) FILTER (WHERE condition)` compte les lignes qui respectent une condition ; DuckDB le comprend, comme PostgreSQL. Une valeur manquante se teste avec `IS NULL`. Donnez un nom à chaque compteur avec `AS`.
:::

::: solution
```python title="Évaluation · Cellule 1"
import duckdb

TAXIS = "/home/lab/projet/data/taxis/yellow_tripdata_2024-01.parquet"
ZONES = "/home/lab/projet/data/taxis/taxi_zone_lookup.csv"

defauts = duckdb.sql(f"""
SELECT count(*) AS lignes,
       count(*) FILTER (WHERE tpep_pickup_datetime < '2024-01-01' OR tpep_pickup_datetime >= '2024-02-01') AS hors_janvier,
       count(*) FILTER (WHERE fare_amount <= 0) AS prix_negatif_ou_nul,
       count(*) FILTER (WHERE trip_distance = 0) AS distance_nulle,
       count(*) FILTER (WHERE passenger_count IS NULL) AS passagers_manquants
FROM read_parquet('{TAXIS}')
""").df()
print(defauts.T)
```

```plaintext title="Sortie attendue"
                           0
lignes               2964624
hors_janvier              18
prix_negatif_ou_nul    38341
distance_nulle         60371
passagers_manquants   140162
```

Une seule lecture du fichier pour cinq compteurs. Les chiffres racontent l'histoire des données : **18 courses hors du mois** (dont une datée du 31 décembre 2002, sans doute une horloge de taximètre déréglée), **38 341 prix négatifs ou nuls** (annulations et remboursements), **60 371 distances nulles** (course annulée sur place, ou compteur non déclenché), et **140 162 courses sans nombre de passagers**. Ce dernier chiffre est exactement celui des courses dont le type de paiement vaut 0 (« inconnu ») : un indice fort que ces lignes arrivent incomplètes par un même circuit, à confirmer en croisant les deux conditions. Un défaut vient rarement seul.
:::
::::

{#arrondissements}
## Analyser par arrondissement

:::: task Étape 2 | Une jointure en SQL, vérifiée avec pandas | 9 min | 4 pts
Pour les courses **valides** (prises en charge en janvier 2024, prix strictement positif, distance strictement positive), calculez par **arrondissement de prise en charge** (`Borough` de la table des zones, reliée par `PULocationID = LocationID`) :

- le nombre de courses ;
- la distance moyenne, arrondie à 2 décimales ;
- le prix moyen de la course, arrondi à 2 décimales.

Triez par nombre de courses décroissant. Faites le calcul **avec DuckDB**, puis refaites-le **avec pandas** (lecture sélective des colonnes utiles, et `merge` avec la table des zones) et affichez si les deux résultats sont identiques.

::: proof Collez la sortie complète de votre cellule
:::

::: hint
En SQL : `JOIN read_csv('…') AS z ON c.PULocationID = z.LocationID`, puis `GROUP BY z.Borough`. En pandas : `pd.read_parquet(TAXIS, columns=[…])`, puis `.merge(zones, left_on="PULocationID", right_on="LocationID")`, puis `.groupby("Borough").agg(…)`. Pour comparer : même ordre de lignes, puis `.equals()` ou une comparaison colonne par colonne.
:::

::: solution
```python title="Évaluation · Cellule 2"
import pandas as pd

par_arrondissement = duckdb.sql(f"""
SELECT z.Borough AS arrondissement,
       count(*) AS courses,
       round(avg(c.trip_distance), 2) AS distance_moyenne,
       round(avg(c.fare_amount), 2) AS prix_moyen
FROM read_parquet('{TAXIS}') AS c
JOIN read_csv('{ZONES}') AS z ON c.PULocationID = z.LocationID
WHERE c.tpep_pickup_datetime >= '2024-01-01' AND c.tpep_pickup_datetime < '2024-02-01'
  AND c.fare_amount > 0 AND c.trip_distance > 0
GROUP BY z.Borough
ORDER BY courses DESC
""").df()
print(par_arrondissement.to_string(index=False))

courses = pd.read_parquet(TAXIS, columns=["tpep_pickup_datetime", "PULocationID", "trip_distance", "fare_amount"])
valides = courses[
    (courses["tpep_pickup_datetime"] >= "2024-01-01") & (courses["tpep_pickup_datetime"] < "2024-02-01")
    & (courses["fare_amount"] > 0) & (courses["trip_distance"] > 0)
]
zones = pd.read_csv(ZONES, keep_default_na=False)   # sinon, l'arrondissement « N/A » devient une valeur manquante
avec_zone = valides.merge(zones, left_on="PULocationID", right_on="LocationID")
verif = (avec_zone.groupby("Borough")
         .agg(courses=("fare_amount", "size"), distance_moyenne=("trip_distance", "mean"), prix_moyen=("fare_amount", "mean"))
         .round(2).sort_values("courses", ascending=False).reset_index())
identique = (verif["Borough"].tolist() == par_arrondissement["arrondissement"].tolist()
             and verif["courses"].tolist() == par_arrondissement["courses"].tolist()
             and (verif["distance_moyenne"] - par_arrondissement["distance_moyenne"]).abs().max() < 0.006
             and (verif["prix_moyen"] - par_arrondissement["prix_moyen"]).abs().max() < 0.006)
print("pandas et DuckDB donnent le même résultat :", identique)
```

```plaintext title="Sortie attendue"
arrondissement  courses  distance_moyenne  prix_moyen
     Manhattan  2573386              2.72       14.92
        Queens   257799             12.82       52.80
      Brooklyn    22282             14.81       28.78
       Unknown     9638              3.31       18.99
         Bronx     5756              7.83       33.11
           N/A      741              9.36       69.75
           EWR       49              5.77       84.37
 Staten Island       46             10.02       46.14
pandas et DuckDB donnent le même résultat : True
```

- **Manhattan concentre près de 90 % des courses**, courtes (2,72 miles) et peu chères (14,92 $) : le taxi jaune est d'abord un transport du centre-ville.
- **Queens** a des courses près de cinq fois plus longues, et plus de trois fois plus chères : c'est l'arrondissement des deux aéroports, JFK et LaGuardia.
- **« Unknown » et « N/A »** ne sont pas des arrondissements : ce sont les deux dernières lignes de la table des zones. Le code 264 (« Unknown ») sert quand la zone n'est pas identifiée, le code 265 (« N/A », zone « Outside of NYC ») quand la course part de l'extérieur de la ville. Des données à traiter avec prudence.
- **Le piège du CSV** : sans `keep_default_na=False`, pandas lit le texte « N/A » comme une valeur **manquante**, l'arrondissement disparaît du `groupby`, et la comparaison avec DuckDB répond `False`. DuckDB, lui, le garde comme du texte. C'est exactement ce genre d'écart silencieux qu'un contrôle croisé entre deux moteurs fait apparaître.
:::
::::

{#spark}
## Contrôler avec Spark

:::: task Étape 3 | La répartition des paiements, et le filtre poussé | 8 min | 4 pts
Avec **Spark SQL**, pour les courses prises en charge en janvier 2024 et de prix strictement positif, comptez les courses par type de paiement (`payment_type`), triées par type. Puis affichez la valeur `PushedFilters` du plan physique, pour prouver que le filtre sur le prix est transmis au lecteur Parquet.

Les codes de paiement de la TLC : 0 inconnu, 1 carte, 2 espèces, 3 gratuit, 4 litige.

::: proof Collez la sortie complète de votre cellule
:::

::: hint
Même démarrage de Spark qu'à la Cellule 13 du TP, puis `createOrReplaceTempView`. Le plan : `explain(mode="formatted")`, capturé comme à la Cellule 14.
:::

::: solution
```python title="Évaluation · Cellule 3"
import contextlib
import io

from pyspark.sql import SparkSession

spark = (SparkSession.builder.master("local[*]").appName("evaluation-j3")
         .config("spark.ui.showConsoleProgress", "false").getOrCreate())
spark.sparkContext.setLogLevel("ERROR")
spark.read.parquet(TAXIS).createOrReplaceTempView("courses")

requete = """
SELECT payment_type, count(*) AS courses
FROM courses
WHERE tpep_pickup_datetime >= '2024-01-01' AND tpep_pickup_datetime < '2024-02-01' AND fare_amount > 0
GROUP BY payment_type
ORDER BY payment_type
"""
print(spark.sql(requete).toPandas().to_string(index=False))
tampon = io.StringIO()
with contextlib.redirect_stdout(tampon):
    spark.sql(requete).explain(mode="formatted")
print([ligne for ligne in tampon.getvalue().splitlines() if ligne.startswith("PushedFilters")][0])
```

```plaintext title="Sortie attendue"
 payment_type  courses
            0   138046
            1  2318848
            2   430621
            3    13712
            4    25039
PushedFilters: [IsNotNull(tpep_pickup_datetime), IsNotNull(fare_amount), GreaterThanOrEqual(tpep_pickup_datetime,2024-01-01T00:00), LessThan(tpep_pickup_datetime,2024-02-01T00:00), GreaterThan(fare_amount,0.0)]
```

Les **paiements par carte** dominent : 2 318 848 courses, exactement le nombre de courses valides du TP (qui ajoutait la règle « pourboire positif ou nul »). Les espèces représentent environ 15 % des courses ; les gratuités et litiges, moins de 2 %. Le plan montre que les deux conditions du contrat, sur la date et sur le prix, sont **transmises au lecteur Parquet**, complétées automatiquement par des tests `IsNotNull` : une valeur manquante ne peut pas satisfaire une comparaison.
:::
::::

{#chiffrer}
## Chiffrer

:::: task Étape 4 | Auto-hébergé ou managé, avec d'autres hypothèses | 6 min | 3 pts
La commission doit héberger l'outil d'analyse. Hypothèses de travail, sur 36 mois :

| | Mise en place | Maintenance | Infrastructure |
|---|---|---|---|
| Auto-hébergé | 10 jours | 2 jours par mois | 150 € par mois |
| Managé | 2 jours | 0,5 jour par mois | 750 € par mois |

1. Avec la fonction `cout_total` de la notion 2 (recopiez-la), calculez le coût des deux options pour un ingénieur à 500 € par jour.
2. Calculez le **taux journalier de bascule**, celui pour lequel les deux options coûtent autant, arrondi à l'euro.

::: proof Collez la sortie complète de votre cellule
:::

::: hint
Écrivez l'égalité des deux coûts : les termes en `t` (le taux) d'un côté, les montants fixes de l'autre. `t = (écart des coûts d'infrastructure sur 36 mois) / (écart des jours sur 36 mois, mise en place comprise)`.
:::

::: solution
```python title="Évaluation · Cellule 4"
def cout_total(option, taux_jour, mois=36):
    return option["mise_en_place_j"] * taux_jour + mois * (option["maintenance_j_mois"] * taux_jour + option["infra_eur_mois"])


auto = {"mise_en_place_j": 10, "maintenance_j_mois": 2.0, "infra_eur_mois": 150}
manage = {"mise_en_place_j": 2, "maintenance_j_mois": 0.5, "infra_eur_mois": 750}
print(f"auto-hébergé : {cout_total(auto, 500):,.0f} €")
print(f"managé       : {cout_total(manage, 500):,.0f} €")

jours = (auto["mise_en_place_j"] + 36 * auto["maintenance_j_mois"]) - (manage["mise_en_place_j"] + 36 * manage["maintenance_j_mois"])
infra = 36 * (manage["infra_eur_mois"] - auto["infra_eur_mois"])
print(f"bascule : {infra / jours:.0f} € par jour")
```

```plaintext title="Sortie attendue"
auto-hébergé : 46,400 €
managé       : 37,000 €
bascule : 348 € par jour
```

L'auto-hébergé demande 10 + 72 = 82 jours sur trois ans, le managé 2 + 18 = 20 jours : 62 jours d'écart. Le managé coûte 600 € de plus par mois, soit 21 600 € sur trois ans. Bascule : 21 600 / 62 ≈ **348 € par jour**. Au-dessus (c'est le cas à 500 €), le managé est moins cher ; en dessous, l'auto-hébergé.
:::
::::

{#quiz}
## Quiz : vos résultats

Répondez à partir de la matinée et de ce que vous venez de faire. **Une seule tentative par question** : votre première réponse est enregistrée et compte pour la note.

```quiz
- q: Que fait count(*) FILTER (WHERE condition) en SQL ?
  options:
    - Il supprime les lignes qui ne respectent pas la condition
    - Il compte seulement les lignes qui respectent la condition, sans filtrer la requête entière
    - Il trie les lignes
    - Il ne fonctionne qu'avec Spark
  answer: 1
  explain: Plusieurs compteurs différents tiennent ainsi dans une seule lecture du fichier.
- q: Pourquoi vérifier un résultat avec un second moteur ?
  options:
    - Pour aller plus vite
    - Parce qu'un écart révèle une erreur dans la traduction du contrat ou de la question
    - Parce que DuckDB se trompe souvent
    - Parce que la commission l'exige par la loi
  answer: 1
  explain: Deux implémentations indépendantes qui concordent, c'est un test fort.
- q: Dans le plan de Spark, où voit-on qu'un filtre est transmis au lecteur Parquet ?
  options: [ReadSchema, PushedFilters, toPandas, createOrReplaceTempView]
  answer: 1
  explain: ReadSchema montre les colonnes lues ; PushedFilters, les conditions transmises.
- q: Les courses payées en espèces ont un pourboire enregistré de 0. Pourquoi les exclure d'une analyse des pourboires ?
  options:
    - Parce qu'elles sont fausses
    - Parce que les pourboires en espèces ne sont pas saisis, ce qui tirerait la moyenne vers le bas à tort
    - Parce qu'elles sont trop nombreuses
    - Parce que Spark ne sait pas les lire
  answer: 1
  explain: Un zéro enregistré n'est pas un zéro réel ; c'est une donnée manquante déguisée.
- q: Avec un ingénieur à 500 € par jour et un point de bascule à 348 €, quelle option est la moins chère ?
  options: [L'auto-hébergé, Le managé, Elles coûtent exactement autant, On ne peut pas savoir]
  answer: 1
  explain: Au-dessus du taux de bascule, le temps humain coûte trop cher pour l'auto-hébergé.
- q: Quel moteur choisir pour explorer en SQL quelques fichiers Parquet de 20 Go sur un portable ?
  options: [Spark sur un cluster, DuckDB, Un tableur, pandas sans précaution]
  answer: 1
  explain: DuckDB est embarqué, lit Parquet directement et déborde sur disque si besoin. Un cluster serait surdimensionné.
```
