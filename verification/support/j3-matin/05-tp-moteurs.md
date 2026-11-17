---
subtitle: >-
  Une seule question métier, posée à trois moteurs : pandas, DuckDB et Spark. Même fichier, même
  contrat de qualité, même réponse attendue. Ce qui change : la mémoire consommée, le temps, et la
  manière dont chaque moteur évite de lire ce dont il n'a pas besoin. À la fin, vous saurez lequel
  choisir, et quand.
objectives:
  - Traduire une question métier et un contrat de qualité en filtres
  - Réduire la mémoire de pandas en lisant seulement les colonnes et les lignes utiles
  - Interroger directement un fichier Parquet en SQL avec DuckDB, et lire son plan d'exécution
  - Exécuter la même requête SQL avec Spark et y repérer les filtres poussés jusqu'au fichier
  - Choisir un moteur selon le volume, l'infrastructure et l'usage
---

{#question}
## La question et le contrat

**La question métier.** Une application de VTC veut conseiller ses chauffeurs : **à quelle heure de la journée les clients laissent-ils les pourboires les plus généreux ?** On la pose aux courses de taxi de janvier 2024. La mesure : pour chaque heure, le **total des pourboires divisé par le total des prix des courses**, en pourcentage.

::: callout warn Pourquoi un rapport de totaux, et pas la moyenne des pourcentages ?
La moyenne des pourcentages course par course est fragile : une course facturée 0,01 $ avec 5 $ de pourboire compte pour 50 000 %, et suffit à fausser la moyenne d'une heure entière. Le rapport des totaux répond à la vraie question (« sur 100 $ de courses, combien de pourboire ? ») et n'est pas sensible à ces cas extrêmes. Choisir la bonne mesure fait partie du contrat, au même titre que les filtres.
:::

**Le contrat de qualité.** Les données ont des défauts. On ne garde que les courses qui respectent quatre règles, écrites **avant** de calculer, comme au jour 1 :

| Règle | Pourquoi |
|---|---|
| Prise en charge en janvier 2024 | Le fichier contient quelques courses datées de 2002 ou de février |
| Paiement par carte (`payment_type = 1`) | Les pourboires en espèces ne sont pas enregistrés : pour eux, le pourboire vaut toujours 0 |
| Prix de la course strictement positif | Les montants négatifs sont des annulations ou des remboursements ; on ne divise pas par zéro |
| Pourboire positif ou nul | Un pourboire négatif est une correction comptable, pas un pourboire |

**Le moteur ne change pas la réponse.** Les trois moteurs doivent trouver **exactement** les mêmes chiffres. Si ce n'est pas le cas, l'un d'eux applique mal le contrat : c'est un test en soi.

{#etape1}
## Étape 1 : pandas, sans précaution

:::: lab Étape 1 | Tout charger, puis filtrer | 8 min
Dans votre notebook `j3-matin.ipynb`, une fonction affiche le résumé d'un résultat, pour comparer les moteurs sur la même présentation :

```python title="Cellule 8 : la fonction de résumé"
def resumer(resultat):
    """resultat : un tableau pandas avec les colonnes heure, courses et taux (en %)."""
    resultat = resultat.sort_values("heure").reset_index(drop=True)
    meilleure = resultat.loc[resultat["taux"].idxmax()]
    pire = resultat.loc[resultat["taux"].idxmin()]
    print(f"{int(resultat['courses'].sum()):,} courses valides, réparties sur {len(resultat)} heures")
    print(f"taux le plus haut : {meilleure['taux']:.2f} % à {int(meilleure['heure'])} h ({int(meilleure['courses']):,} courses)")
    print(f"taux le plus bas  : {pire['taux']:.2f} % à {int(pire['heure'])} h ({int(pire['courses']):,} courses)")
    return resultat
```

Puis la version la plus simple : on charge **tout** le fichier, on applique le contrat, on regroupe par heure.

```python title="Cellule 9 : pandas, tout le fichier"
import time

debut = time.perf_counter()
tout = pd.read_parquet(TAXIS)
valides = tout[
    (tout["tpep_pickup_datetime"] >= "2024-01-01") & (tout["tpep_pickup_datetime"] < "2024-02-01")
    & (tout["payment_type"] == 1) & (tout["fare_amount"] > 0) & (tout["tip_amount"] >= 0)
]
par_heure = (
    valides.groupby(valides["tpep_pickup_datetime"].dt.hour)
    .agg(courses=("tip_amount", "size"), pourboires=("tip_amount", "sum"), prix=("fare_amount", "sum"))
    .assign(taux=lambda t: t["pourboires"] / t["prix"] * 100)
    .reset_index(names="heure")
)
duree_pandas = time.perf_counter() - debut
print(f"mémoire du tableau chargé : {tout.memory_usage(deep=True).sum() / 1e6:.0f} Mo, durée {duree_pandas:.2f} s")
res_pandas = resumer(par_heure)
```

```plaintext title="Sortie attendue (les durées varient selon la machine)"
mémoire du tableau chargé : 418 Mo, durée 0.38 s
2,318,848 courses valides, réparties sur 24 heures
taux le plus haut : 24.23 % à 18 h (170,450 courses)
taux le plus bas  : 18.04 % à 5 h (12,579 courses)
```

Les durées affichées dans ce TP viennent de la machine de vérification (4 cœurs) ; les vôtres seront différentes, mais les écarts entre moteurs resteront du même ordre.

- **418 Mo en mémoire** pour un fichier de 50 Mo : le tableau pandas est décompressé, et contient les 19 colonnes, alors que la question n'en utilise que 4.
- **2 318 848 courses valides**, sur près de 3 millions.
- **La réponse :** c'est à **18 h** que les clients sont les plus généreux (24,23 % du prix de la course), à **5 h** qu'ils le sont le moins (18,04 %). Les données disent « quand », pas « pourquoi » : sortie du bureau d'un côté, trajets de l'aube de l'autre ? Une analyse par zone de départ permettrait de tester cette hypothèse.
::::

{#etape2}
## Étape 2 : pandas, en lisant moins

:::: lab Étape 2 | Seulement les colonnes et les lignes utiles | 7 min
La question n'utilise que **4 colonnes sur 19**. Et elle ne garde que les paiements par carte. `read_parquet` sait le dire au lecteur Parquet :

- `columns=` : la **projection**, on ne lit que ces colonnes ;
- `filters=` : le **filtre**, appliqué pendant la lecture, avant de construire le tableau pandas.

```python title="Cellule 10 : pandas, lecture sélective"
debut = time.perf_counter()
selection = pd.read_parquet(
    TAXIS,
    columns=["tpep_pickup_datetime", "payment_type", "fare_amount", "tip_amount"],
    filters=[("payment_type", "==", 1)],
)
valides = selection[
    (selection["tpep_pickup_datetime"] >= "2024-01-01") & (selection["tpep_pickup_datetime"] < "2024-02-01")
    & (selection["fare_amount"] > 0) & (selection["tip_amount"] >= 0)
]
par_heure = (
    valides.groupby(valides["tpep_pickup_datetime"].dt.hour)
    .agg(courses=("tip_amount", "size"), pourboires=("tip_amount", "sum"), prix=("fare_amount", "sum"))
    .assign(taux=lambda t: t["pourboires"] / t["prix"] * 100)
    .reset_index(names="heure")
)
duree_selective = time.perf_counter() - debut
print(f"mémoire du tableau chargé : {selection.memory_usage(deep=True).sum() / 1e6:.0f} Mo, durée {duree_selective:.2f} s")
res_selectif = resumer(par_heure)
```

```plaintext title="Sortie attendue (les durées varient selon la machine)"
mémoire du tableau chargé : 74 Mo, durée 0.18 s
2,318,848 courses valides, réparties sur 24 heures
taux le plus haut : 24.23 % à 18 h (170,450 courses)
taux le plus bas  : 18.04 % à 5 h (12,579 courses)
```

**Même réponse, 74 Mo au lieu de 418 Mo**, plus de 5 fois moins de mémoire, et un temps divisé par deux. Sur un fichier dix fois plus gros, c'est la différence entre un notebook qui tourne et un notebook qui plante. Le filtre `payment_type == 1` est appliqué pendant la lecture : les paiements en espèces ne sont jamais construits en mémoire.
::::

{#etape3}
## Étape 3 : DuckDB, du SQL sur le fichier

:::: lab Étape 3 | Une base de données dans le notebook | 10 min
**DuckDB** est un moteur SQL **embarqué** : pas de serveur à installer, il tourne dans le processus Python, comme pandas. Il est conçu pour l'analyse : stockage en colonnes, calcul vectorisé, tous les cœurs du processeur. Et il lit Parquet directement.

On écrit la question **une seule fois en SQL**, dans une variable : on la réutilisera telle quelle avec Spark.

```python title="Cellule 11 : la requête, et DuckDB"
import duckdb

REQUETE = """
SELECT hour(tpep_pickup_datetime) AS heure,
       count(*) AS courses,
       sum(tip_amount) / sum(fare_amount) * 100 AS taux
FROM courses
WHERE tpep_pickup_datetime >= '2024-01-01' AND tpep_pickup_datetime < '2024-02-01'
  AND payment_type = 1 AND fare_amount > 0 AND tip_amount >= 0
GROUP BY hour(tpep_pickup_datetime)
"""

duckdb.sql(f"CREATE OR REPLACE VIEW courses AS SELECT * FROM read_parquet('{TAXIS}')")
debut = time.perf_counter()
par_heure = duckdb.sql(REQUETE).df()
duree_duckdb = time.perf_counter() - debut
print(f"durée {duree_duckdb:.2f} s")
res_duckdb = resumer(par_heure)
```

```plaintext title="Sortie attendue (les durées varient selon la machine)"
durée 0.12 s
2,318,848 courses valides, réparties sur 24 heures
taux le plus haut : 24.23 % à 18 h (170,450 courses)
taux le plus bas  : 18.04 % à 5 h (12,579 courses)
```

- `read_parquet(...)` lit le fichier sans l'importer ; la **vue** `courses` lui donne un nom pour la requête.
- `.df()` convertit le résultat (24 lignes) en tableau pandas.

**Comment DuckDB a-t-il évité de tout lire ?** `EXPLAIN` affiche son **plan d'exécution**, de bas en haut :

```python title="Cellule 12 : le plan de DuckDB"
plan = duckdb.sql("EXPLAIN " + REQUETE).fetchall()[0][1]
lecture = plan[plan.index("Projections"):]          # la case du bas : la lecture du fichier
for ligne in lecture.splitlines():
    texte = ligne.strip(" │┌┐└┘─┬┴")
    if texte:
        print(texte)
```

```plaintext title="Sortie attendue"
Projections:
tpep_pickup_datetime
fare_amount
tip_amount
Filters:
tpep_pickup_datetime>=
'2024-01-01 00:00:00':
:TIMESTAMP AND
tpep_pickup_datetime<
'2024-02-01 00:00:00':
:TIMESTAMP
payment_type=1
fare_amount>0.0
tip_amount>=0.0
~592,924 rows
```

Le cadre du plan coupe les lignes longues : `'2024-01-01 00:00:00'::TIMESTAMP` est écrit sur deux lignes. Trois observations :

- **`Projections`** : DuckDB ne lit que **3 colonnes**. Même `payment_type` n'y est pas : le test `payment_type = 1` est fait pendant la lecture, et la colonne n'est plus utile ensuite.
- **`Filters`** : les cinq conditions du contrat sont **poussées dans la lecture du fichier**. Vous n'avez rien demandé : l'optimiseur l'a fait seul, à partir du SQL.
- **`~592,924 rows`** : l'**estimation** du nombre de lignes après filtrage, soit exactement 20 % des lignes du fichier. Faute de statistiques dans le fichier, DuckDB applique une estimation par défaut ; la vraie valeur est 2 318 848. Sur une requête plus complexe, une mauvaise estimation peut conduire à un mauvais plan : les statistiques servent aussi à cela.
::::

{#etape4}
## Étape 4 : Spark, la même requête

:::: lab Étape 4 | Le moteur des clusters, sur une seule machine | 12 min
**Spark** est conçu pour répartir un calcul sur des dizaines de machines. Ici, il tourne en mode **local** : un seul processus Java, qui utilise les cœurs de la VM comme autant de « machines ». Son démarrage prend quelques secondes : c'est une machine virtuelle Java qui se lance.

```python title="Cellule 13 : Spark, la même requête SQL"
from pyspark.sql import SparkSession

spark = (SparkSession.builder.master("local[*]").appName("tp-moteurs")
         .config("spark.ui.showConsoleProgress", "false").getOrCreate())
spark.sparkContext.setLogLevel("ERROR")
spark.read.parquet(TAXIS).createOrReplaceTempView("courses")

debut = time.perf_counter()
par_heure = spark.sql(REQUETE).toPandas()
duree_spark = time.perf_counter() - debut
print(f"durée {duree_spark:.2f} s")
res_spark = resumer(par_heure)
```

```plaintext title="Sortie attendue (les durées varient selon la machine)"
durée 2.46 s
2,318,848 courses valides, réparties sur 24 heures
taux le plus haut : 24.23 % à 18 h (170,450 courses)
taux le plus bas  : 18.04 % à 5 h (12,579 courses)
```

**La requête SQL est mot pour mot celle de DuckDB.** Seule la manière de déclarer la table `courses` change. C'est l'intérêt d'un standard : la logique métier ne dépend pas du moteur.

**Qu'est-ce que Spark a poussé jusqu'au fichier ?** Son plan physique contient la ligne de lecture du fichier (`FileScan parquet`), avec deux informations :

```python title="Cellule 14 : ce que Spark lit vraiment"
import contextlib
import io

tampon = io.StringIO()
with contextlib.redirect_stdout(tampon):
    spark.sql(REQUETE).explain(mode="formatted")
for ligne in tampon.getvalue().splitlines():
    if ligne.startswith(("PushedFilters", "ReadSchema")):
        print(ligne)
```

```plaintext title="Sortie attendue"
PushedFilters: [IsNotNull(tpep_pickup_datetime), IsNotNull(payment_type), IsNotNull(fare_amount), IsNotNull(tip_amount), GreaterThanOrEqual(tpep_pickup_datetime,2024-01-01T00:00), LessThan(tpep_pickup_datetime,2024-02-01T00:00), EqualTo(payment_type,1), GreaterThan(fare_amount,0.0), GreaterThanOrEqual(tip_amount,0.0)]
ReadSchema: struct<tpep_pickup_datetime:timestamp_ntz,payment_type:bigint,fare_amount:double,tip_amount:double>
```

- **`ReadSchema`** : les colonnes que Spark lit dans le fichier. C'est la projection.
- **`PushedFilters`** : les conditions transmises au lecteur Parquet, qui s'en sert pour sauter des blocs grâce aux statistiques.

`explain(mode="formatted")` affiche le plan complet, nœud par nœud ; la cellule capture ce texte (`redirect_stdout`) pour n'en garder que les deux lignes utiles. Lancez `spark.sql(REQUETE).explain(mode="formatted")` seul pour voir le plan entier.
::::

{#etape5}
## Étape 5 : comparer

:::: lab Étape 5 | Mêmes chiffres, coûts différents | 5 min
```python title="Cellule 15 : le bilan"
import numpy as np

for nom, res in [("pandas sélectif", res_selectif), ("DuckDB", res_duckdb), ("Spark", res_spark)]:
    identique = (res["courses"].tolist() == res_pandas["courses"].tolist()
                 and np.allclose(res["taux"], res_pandas["taux"]))
    print(f"{nom:<16} même résultat que pandas : {identique}")

for nom, duree in [("pandas, tout", duree_pandas), ("pandas sélectif", duree_selective),
                   ("DuckDB", duree_duckdb), ("Spark", duree_spark)]:
    print(f"{nom:<16} {duree:.2f} s")
```

```plaintext title="Sortie attendue (les durées varient selon la machine)"
pandas sélectif  même résultat que pandas : True
DuckDB           même résultat que pandas : True
Spark            même résultat que pandas : True
pandas, tout     0.38 s
pandas sélectif  0.18 s
DuckDB           0.12 s
Spark            2.46 s
```

**Les quatre calculs donnent exactement la même réponse** : le contrat est appliqué de la même façon partout. Pour le coût, sur ce fichier de 3 millions de lignes :

- **DuckDB est le plus rapide**, sans avoir rien chargé en mémoire au préalable ;
- **pandas sélectif** le suit de près, à condition d'avoir pensé à `columns=` et `filters=` ;
- **Spark est environ 20 fois plus lent que DuckDB** : il a lancé une machine Java, découpé le fichier en tâches et coordonné leur exécution, pour un calcul qui tient dans une seule machine.

Ce classement **s'inverse** quand les données ne tiennent plus sur une machine : DuckDB et pandas atteignent alors leurs limites, et Spark répartit le travail sur un cluster. Le bon moteur dépend du volume.
::::

{#choisir}
## Quel moteur, quand ?

| Moteur | Il excelle quand… | Il souffre quand… | Dans le cloud |
|---|---|---|---|
| **pandas** | Les données tiennent largement en mémoire ; on explore, on prépare, on entraîne un modèle scikit-learn | Le tableau dépasse la moitié de la mémoire ; il n'utilise qu'un cœur pour la plupart des opérations | Partout (notebooks Fabric, Azure ML, Vertex AI) |
| **DuckDB** | Des fichiers Parquet de quelques Go à quelques centaines de Go, sur une machine ; SQL ad hoc ; tests de pipelines | Il faut répartir le calcul sur plusieurs machines, ou écrire beaucoup en parallèle | Notebooks Python de Fabric ; partout où tourne Python |
| **Spark** | Des volumes qui dépassent une machine ; traitements répartis ; tables Delta à grande échelle | Les petits volumes : son démarrage et sa coordination coûtent plus que le calcul | Notebooks Spark de Fabric, Azure Databricks, Dataproc |

**La règle pratique :** commencez par le moteur le plus simple qui suffit. Passer à Spark pour 3 millions de lignes, c'est prendre un semi-remorque pour aller chercher le pain. Mais quand les données dépassent la mémoire d'une machine, c'est le seul qui ne cale pas.

{#avance}
## Pour aller plus loin : ce qui fait la vitesse d'un moteur analytique

Ce bloc est pour les profils avancés ; rien ici n'est exigé dans l'évaluation.

**Exécution vectorisée.** pandas et DuckDB traitent les données par **vecteurs** (des milliers de valeurs d'un coup, avec les instructions SIMD du processeur) plutôt que ligne par ligne. DuckDB pousse l'idée plus loin : il découpe le travail en morceaux qui tiennent dans le cache du processeur, et répartit ces morceaux sur tous les cœurs (*morsel-driven parallelism*).

**Optimiseur de requêtes.** Une requête SQL décrit **quoi** obtenir, pas **comment**. L'optimiseur choisit l'ordre des opérations, pousse les filtres et les projections jusqu'au fichier, choisit l'algorithme de jointure. Avec pandas, c'est vous l'optimiseur : la différence entre les étapes 1 et 2 est exactement ce que DuckDB et Spark font tout seuls. Des bibliothèques comme **Polars** offrent à Python une API de tableaux avec un optimiseur (l'évaluation « paresseuse » : on décrit tout le calcul, puis on l'exécute).

**Spark : Catalyst et AQE.** L'optimiseur de Spark s'appelle Catalyst ; il produit le plan physique que vous avez lu. Depuis Spark 3, l'**exécution adaptative** (AQE) réajuste le plan pendant l'exécution, par exemple en fusionnant des partitions trop petites. Sur un cluster, le coût dominant est souvent le **brassage** (*shuffle*) : redistribuer les lignes entre machines pour un `GROUP BY` ou une jointure. Un bon plan Spark est d'abord un plan qui brasse peu.

**Hors mémoire.** Quand le résultat intermédiaire dépasse la mémoire, DuckDB et Spark **débordent sur disque** (*spill*) au lieu d'échouer ; pandas, lui, s'arrête avec une erreur de mémoire. C'est souvent ce critère, plus que la vitesse, qui impose de quitter pandas.

{#quiz}
## Quiz de validation

```quiz
- q: Que fait l'option columns= de pd.read_parquet ?
  options:
    - Elle renomme les colonnes
    - Elle ne lit que les colonnes demandées dans le fichier (projection)
    - Elle trie les colonnes
    - Elle convertit les colonnes en texte
  answer: 1
  explain: Le format en colonnes permet de ne lire que les morceaux utiles du fichier.
- q: La même requête SQL tourne dans DuckDB et dans Spark. Qu'est-ce qui change entre les deux ?
  options:
    - Le résultat
    - Seulement la manière de déclarer la table courses
    - La syntaxe des filtres
    - Rien du tout, même le code Python est identique
  answer: 1
  explain: SQL est un standard ; la logique métier ne dépend pas du moteur.
- q: Que signifie PushedFilters dans le plan de Spark ?
  options:
    - Les filtres ignorés par Spark
    - Les conditions transmises au lecteur Parquet, qui s'en sert pour éviter de lire des blocs
    - Les colonnes lues
    - Les erreurs de la requête
  answer: 1
  explain: C'est la version Spark de l'option filters= de pandas.
- q: Pourquoi Spark n'est-il pas le plus rapide sur ce fichier de 3 millions de lignes ?
  options:
    - Parce qu'il est mal programmé
    - Parce que son démarrage et sa coordination coûtent plus que le calcul sur un si petit volume
    - Parce qu'il ne sait pas lire Parquet
    - Parce qu'il n'utilise qu'un cœur
  answer: 1
  explain: Spark est conçu pour les volumes qui dépassent une machine. Ici, c'est un semi-remorque pour aller chercher le pain.
```
