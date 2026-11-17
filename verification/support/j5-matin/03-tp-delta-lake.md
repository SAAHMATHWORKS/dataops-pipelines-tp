---
subtitle: >-
  Un lac de fichiers Parquet ne sait ni refuser une ligne fausse, ni revenir en arrière, ni dire qui
  a modifié quoi. Delta Lake ajoute tout cela par-dessus Parquet, avec un journal de transactions. On
  construit avec Spark les trois couches de ColisVert : bronze (ce qui arrive), argent (ce qui
  respecte le contrat), or (ce que lit le métier). On pose les règles dans la table elle-même, on
  corrige des délais par MERGE, puis on répare un incident en une commande.
objectives:
  - Expliquer ce que le journal de transactions de Delta Lake ajoute à des fichiers Parquet
  - Construire une architecture en médaillon - bronze, argent, or - avec Spark
  - Poser des contraintes CHECK dans une table, et reconnaître le schéma imposé et l'évolution de schéma
  - Mettre à jour une table par MERGE, lire son historique et voyager dans le temps
  - Réparer un incident avec RESTORE, et savoir ce que font OPTIMIZE et VACUUM
---

{#pourquoi}
## Pourquoi Delta Lake

Au jour 3, les taxis de New York étaient des fichiers Parquet : rapides à lire, mais **inertes**. Écrire à moitié un dossier de Parquet laisse des fichiers incomplets. Deux écritures simultanées se marchent dessus. Et rien n'empêche d'ajouter une colonne fausse.

**L'analogie du registre des colis.** Les fichiers Parquet sont les colis dans l'entrepôt. Delta Lake ajoute le **registre** : un cahier où chaque mouvement est noté, numéroté, horodaté, et qui seul fait foi. Un colis posé sur une étagère mais absent du registre n'existe pas encore. Pour savoir ce qu'il y avait hier, on relit le registre jusqu'à la page d'hier.

Concrètement, une table Delta est un dossier qui contient :
- les fichiers **Parquet** des données ;
- un dossier **`_delta_log`**, où chaque écriture ajoute un fichier JSON numéroté (`00000000000000000000.json`, puis `…01.json`) qui liste les fichiers ajoutés et retirés.

Ce journal apporte quatre choses :

| Propriété | Ce que ça veut dire chez ColisVert |
|---|---|
| **Transactions ACID** | Une écriture est entière ou n'a pas eu lieu ; un lecteur ne voit jamais une table à moitié écrite |
| **Schéma imposé** | Une colonne inattendue ou un mauvais type est refusé, sauf évolution demandée explicitement |
| **Historique** | Chaque version de la table reste lisible : on peut relire celle d'hier, ou y revenir |
| **Mises à jour** | `UPDATE`, `DELETE` et `MERGE` sur des fichiers qui, eux, ne se modifient jamais : Delta écrit de nouveaux fichiers et note le changement |

**Où on le retrouve.** C'est le format de table par défaut des Lakehouses de **Microsoft Fabric** et de **Databricks**. Les commandes de ce TP sont celles qu'on taperait dans un notebook Fabric, où la session Spark est déjà configurée.

{#medaillon}
## L'architecture en médaillon

| Couche | Contenu | Règle |
|---|---|---|
| **Bronze** | Les données **telles qu'elles arrivent**, défauts compris, avec l'origine et l'heure de réception | On ne corrige rien : on garde la preuve |
| **Argent** | Les données **nettoyées, typées, conformes au contrat** | Le contrat de données du jour 1, appliqué et inscrit dans la table |
| **Or** | Les données **prêtes pour le métier** : agrégats, indicateurs | Ce que lisent les tableaux de bord et le modèle |

Garder le bronze permet de **rejouer** l'argent quand une règle change, sans redemander les fichiers aux entrepôts.

{#session}
## Étape 1 : une session Spark avec Delta Lake

:::: lab Étape 1 | Démarrer Spark avec Delta Lake | 5 min
`configure_spark_with_delta_pip` ajoute à la session les bibliothèques Java de Delta Lake qui correspondent au paquet Python installé. Les deux options `spark.sql.extensions` et `spark.sql.catalog.spark_catalog` activent les commandes SQL de Delta (`MERGE`, `RESTORE`, contraintes).

```python title="Cellule 2 : Spark et Delta Lake"
import importlib.metadata
import re
import shutil

import pyspark
from delta import configure_spark_with_delta_pip
from delta.tables import DeltaTable
from pyspark.sql import functions as F

constructeur = (
    pyspark.sql.SparkSession.builder.master("local[*]").appName("j5-delta")
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
    .config("spark.ui.showConsoleProgress", "false")
)
spark = configure_spark_with_delta_pip(constructeur).getOrCreate()
spark.sparkContext.setLogLevel("ERROR")
print("Spark", spark.version, "| Delta Lake", importlib.metadata.version("delta-spark"))
```

```plaintext title="Sortie attendue"
Spark 4.1.1 | Delta Lake 4.3.1
```

Au premier lancement, la cellule prend une à deux minutes : elle télécharge les bibliothèques de Delta Lake (voir la mise en place). Ensuite, une vingtaine de secondes.
::::

{#bronze}
## Étape 2 : la couche bronze

:::: lab Étape 2 | Garder ce qui arrive, tel quel | 5 min
On lit le fichier **brut** du jour 1, avec ses défauts. Toutes les colonnes restent en **texte** : convertir, c'est déjà corriger, et le bronze ne corrige rien. On ajoute deux colonnes techniques, l'origine du fichier et l'heure de réception.

```python title="Cellule 3 : bronze"
BRONZE = str(LAC / "bronze" / "livraisons")
ARGENT = str(LAC / "argent" / "livraisons")
OR = str(LAC / "or" / "retards_par_semaine")
shutil.rmtree(LAC, ignore_errors=True)          # on repart d'un lac vide à chaque exécution

bruts = spark.read.csv(str(DOSSIER_DATA / "livraisons_brutes.csv"), header=True)
(bruts.withColumn("_fichier", F.lit("livraisons_brutes.csv"))
      .withColumn("_recu_le", F.current_timestamp())
      .write.format("delta").mode("overwrite").save(BRONZE))
bronze = spark.read.format("delta").load(BRONZE)
print(f"bronze : {bronze.count()} lignes, {len(bronze.columns)} colonnes")
print("types des colonnes du fichier :", sorted({type_ for _, type_ in bruts.dtypes}))
```

```plaintext title="Sortie attendue"
bronze : 5060 lignes, 13 colonnes
types des colonnes du fichier : ['string']
```

Ouvrez le dossier `lakehouse/bronze/livraisons` dans l'explorateur de JupyterLab : un fichier Parquet, et le dossier `_delta_log` avec son premier fichier JSON.
::::

{#argent}
## Étape 3 : la couche argent, conforme au contrat

:::: lab Étape 3 | Appliquer le contrat avec Spark | 10 min
Ce sont les règles du contrat du jour 1, plus une règle de **cohérence** : `en_retard` doit valoir 1 exactement quand le délai réel dépasse le délai promis. On compte ce que chaque règle écarte, puis on **type** les colonnes.

```python title="Cellule 4 : argent"
ENTREPOTS = ["Lille", "Lyon", "Nantes", "Toulouse"]
METIER = [c for c in bruts.columns]                       # les colonnes du fichier, sans les colonnes techniques
regles = [
    ("doublons exacts", lambda df: df.dropDuplicates(METIER)),
    ("entrepôt inconnu", lambda df: df.filter(F.col("entrepot").isin(ENTREPOTS))),
    ("date mal formée", lambda df: df.filter(F.col("date_expedition").rlike(r"^\d{4}-\d{2}-\d{2}$"))),
    ("poids manquant", lambda df: df.filter(F.col("poids_kg").isNotNull())),
    ("météo manquante", lambda df: df.filter(F.col("meteo").isNotNull())),
    ("délai réel négatif", lambda df: df.filter(F.col("delai_reel_h").cast("int") >= 0)),
    ("retard incohérent", lambda df: df.filter(
        F.col("en_retard").cast("int")
        == (F.col("delai_reel_h").cast("int") > F.col("delai_promis_h").cast("int")).cast("int"))),
]
donnees = bronze
for nom, regle in regles:
    avant = donnees.count()
    donnees = regle(donnees)
    print(f"{nom:<20} {avant - donnees.count():>3} ligne(s) écartée(s)")

argent = donnees.select(
    "id_colis", F.to_date("date_expedition").alias("date_expedition"), "entrepot", "client", "creneau",
    F.col("distance_km").cast("int"), F.col("poids_kg").cast("double"), "meteo",
    F.col("delai_promis_h").cast("int"), F.col("delai_reel_h").cast("int"), F.col("en_retard").cast("int"),
)
argent.write.format("delta").mode("overwrite").save(ARGENT)
table = DeltaTable.forPath(spark, ARGENT)
lue = table.toDF()
print(f"argent : {lue.count()} colis, {lue.select('id_colis').distinct().count()} numéros distincts, "
      f"{lue.agg(F.sum('en_retard')).first()[0]} en retard")
```

```plaintext title="Sortie attendue"
doublons exacts       25 ligne(s) écartée(s)
entrepôt inconnu      12 ligne(s) écartée(s)
date mal formée       20 ligne(s) écartée(s)
poids manquant        15 ligne(s) écartée(s)
météo manquante       40 ligne(s) écartée(s)
délai réel négatif     8 ligne(s) écartée(s)
retard incohérent     10 ligne(s) écartée(s)
argent : 4930 colis, 4930 numéros distincts, 844 en retard
```

- **130 lignes écartées**, chacune par une seule règle : au jour 1, chaque défaut a été placé sur un colis différent. On retrouve exactement les défauts du fichier brut : 25 doublons, 12 « Lile », 20 dates au format jj/mm/aaaa, 15 poids et 40 météos manquants, 8 délais négatifs, et 10 retards incohérents, que le contrat du jour 1 ne voyait pas.
- **L'argent compte 4 930 colis**, et non les 5 035 du fichier propre. On n'a rien **réparé**, on a **écarté**. En production, les lignes écartées iraient dans une table de **quarantaine**, avec la règle violée, pour être corrigées avec l'entrepôt ; le bronze, lui, les garde toutes.
- **Chaque numéro de colis est unique** : 4 930 lignes, 4 930 numéros.
::::

{#contraintes}
## Étape 4 : des règles dans la table elle-même

Le nettoyage de l'étape 3 protège ce pipeline. Mais demain, un autre pipeline, ou un collègue pressé dans un notebook, pourra écrire dans la même table. Une **contrainte CHECK** inscrit la règle **dans la table** : toute écriture qui la viole est refusée, d'où qu'elle vienne. C'est le contrat de données, devenu impossible à contourner.

:::: lab Étape 4 | Contraintes CHECK, schéma imposé, évolution de schéma | 10 min
```python title="Cellule 5 : trois contraintes, deux écritures fautives"
contraintes = {
    "poids_positif": "poids_kg > 0",
    "delai_reel_positif": "delai_reel_h >= 0",
    "retard_coherent": "en_retard = CASE WHEN delai_reel_h > delai_promis_h THEN 1 ELSE 0 END",
}
for nom, regle in contraintes.items():
    spark.sql(f"ALTER TABLE delta.`{ARGENT}` ADD CONSTRAINT {nom} CHECK ({regle})")

def tenter(ecriture):
    """Exécute une écriture et dit si Delta Lake l'a acceptée ou refusée, avec le code d'erreur."""
    try:
        ecriture()
        return "acceptée"
    except Exception as erreur:
        texte = str(erreur)
        code = re.search(r"\[(DELTA_[A-Z_]+)\]", texte)
        regle = re.search(r"CHECK constraint (\w+)", texte)
        return "refusée : " + (code.group(1) if code else type(erreur).__name__) + (f" ({regle.group(1)})" if regle else "")

un_colis = table.toDF().filter(F.col("id_colis") == table.toDF().agg(F.min("id_colis")).first()[0])
incoherent = un_colis.withColumn("en_retard", 1 - F.col("en_retard"))
poids_negatif = un_colis.withColumn("poids_kg", F.lit(-2.5))
print("retard incohérent :", tenter(lambda: incoherent.write.format("delta").mode("append").save(ARGENT)))
print("poids négatif     :", tenter(lambda: poids_negatif.write.format("delta").mode("append").save(ARGENT)))
print("colis dans la table :", table.toDF().count())
```

```plaintext title="Sortie attendue"
retard incohérent : refusée : DELTA_VIOLATE_CONSTRAINT_WITH_VALUES (retard_coherent)
poids négatif     : refusée : DELTA_VIOLATE_CONSTRAINT_WITH_VALUES (poids_positif)
colis dans la table : 4930
```

Les deux écritures sont refusées en bloc : pas une ligne n'est entrée. Le message complet nomme la contrainte et donne les valeurs fautives (`CHECK constraint retard_coherent (…) violated by row with values: …`).

**Le schéma est imposé, lui aussi.** Une colonne inattendue ou un mauvais type sont refusés. Pour ajouter une colonne **volontairement**, on le demande avec l'option `mergeSchema` : c'est l'**évolution de schéma**. Ici, on ajoute la colonne `transporteur` sans écrire une seule ligne (un DataFrame vide), pour que la table soit prête à la recevoir.

```python title="Cellule 6 : schéma imposé, puis évolution voulue"
deux_colis = table.toDF().orderBy("id_colis").limit(2)
en_plus = deux_colis.withColumn("transporteur", F.lit("Colis Express"))
type_faux = deux_colis.withColumn("poids_kg", F.lit("lourd"))
print("colonne inattendue :", tenter(lambda: en_plus.write.format("delta").mode("append").save(ARGENT)))
print("type faux          :", tenter(lambda: type_faux.write.format("delta").mode("append").save(ARGENT)))

vide = table.toDF().limit(0).withColumn("transporteur", F.lit(None).cast("string"))
vide.write.format("delta").mode("append").option("mergeSchema", "true").save(ARGENT)
table = DeltaTable.forPath(spark, ARGENT)        # le schéma a changé : on relit la table
print("dernières colonnes :", table.toDF().columns[-2:], "| colis :", table.toDF().count())
```

```plaintext title="Sortie attendue"
colonne inattendue : refusée : DELTA_METADATA_MISMATCH
type faux          : refusée : DELTA_CONSTRAINT_DATA_TYPE_MISMATCH
dernières colonnes : ['en_retard', 'transporteur'] | colis : 4930
```
::::

{#merge}
## Étape 5 : corriger par MERGE, relire l'historique

L'entrepôt de Lyon s'aperçoit que trois délais réels ont été mal saisis : les colis sont en fait arrivés **6 heures après** le délai promis. Il envoie un fichier de corrections, qui contient aussi par erreur un numéro de colis qui n'existe pas. `MERGE` rapproche les deux tables sur `id_colis`. Il met à jour ce qui correspond, ignore le reste, et recalcule `en_retard` pour rester conforme à la contrainte.

:::: lab Étape 5 | MERGE, historique, voyage dans le temps | 10 min
```python title="Cellule 7 : les corrections de Lyon"
lyon = [ligne.id_colis for ligne in
        table.toDF().filter("entrepot = 'Lyon' AND en_retard = 0").orderBy("id_colis").limit(3).collect()]
corrections = spark.createDataFrame([(i,) for i in lyon + ["CV99999"]], ["id_colis"])
resultat = (
    table.alias("t").merge(corrections.alias("c"), "t.id_colis = c.id_colis")
    .whenMatchedUpdate(set={"delai_reel_h": "t.delai_promis_h + 6", "en_retard": "1"})
    .execute()
    .first()
)
print("colis corrigés :", lyon)
print(f"lignes mises à jour : {resultat.num_updated_rows}, insérées : {resultat.num_inserted_rows}")
```

```plaintext title="Sortie attendue"
colis corrigés : ['CV00003', 'CV00005', 'CV00009']
lignes mises à jour : 3, insérées : 0
```

Chaque écriture a laissé une version dans le journal. On peut les lister, et **relire n'importe laquelle** : c'est le voyage dans le temps (*time travel*).

```python title="Cellule 8 : l'historique et le voyage dans le temps"
for version in table.history().orderBy("version").collect():
    print(f"version {version.version} : {version.operation}")

def retards(version):
    return (spark.read.format("delta").option("versionAsOf", version).load(ARGENT)
            .agg(F.sum("en_retard")).first()[0])

derniere = table.history(1).first().version
print(f"colis en retard : {retards(0)} à la version 0, {retards(derniere)} à la version {derniere}")
```

```plaintext title="Sortie attendue"
version 0 : WRITE
version 1 : ADD CONSTRAINT
version 2 : ADD CONSTRAINT
version 3 : ADD CONSTRAINT
version 4 : WRITE
version 5 : MERGE
colis en retard : 844 à la version 0, 847 à la version 5
```

- **Chaque écriture est une version**, y compris l'ajout d'une contrainte (version 1 à 3), qui ne change que les métadonnées, et l'évolution de schéma (version 4), qui n'a ajouté aucune ligne.
- **La version 0 reste lisible** : 844 retards avant la correction de Lyon, 847 après. Un tableau de bord d'hier peut être recalculé à l'identique, et une différence s'explique en comparant deux versions.
- **C'est aussi un outil de gouvernance.** L'historique complet (`table.history()`) donne pour chaque version l'heure, l'opération, ses paramètres et ses chiffres (lignes mises à jour, fichiers ajoutés). C'est le lignage et l'audit de la table, sans rien installer de plus.
::::

{#incident}
## Étape 6 : un incident, et le retour arrière

:::: lab Étape 6 | RESTORE | 5 min
Un pipeline mal configuré écrase la table argent avec les seuls colis de Lille. En Parquet, il faudrait retrouver une sauvegarde. Avec Delta Lake, on revient à la version d'avant, en une commande :

```python title="Cellule 9 : l'écrasement, puis le retour arrière"
saine = table.history(1).first().version
table.toDF().filter("entrepot = 'Lille'").write.format("delta").mode("overwrite").save(ARGENT)
print(f"après l'incident : {table.toDF().count()} colis (version {table.history(1).first().version})")
table.restoreToVersion(saine)
print(f"après RESTORE    : {table.toDF().count()} colis (version {table.history(1).first().version})")
```

```plaintext title="Sortie attendue"
après l'incident : 1488 colis (version 6)
après RESTORE    : 4930 colis (version 7)
```

L'écrasement a créé la version 6, qui ne contient que les 1 488 colis de Lille. `RESTORE` ne l'efface pas : il crée une **version 7**, identique à la version 5. L'incident reste visible dans l'historique, ce qui est voulu : on peut en faire la revue sans coupable (jour 4). Une commande, quelques secondes, aucune sauvegarde à retrouver.
::::

{#or}
## Étape 7 : la couche or

:::: lab Étape 7 | Ce que lit le métier | 5 min
La couche or contient le taux de retard **par entrepôt et par semaine**. La table est **partitionnée** par entrepôt : un dossier par entrepôt, pour que le tableau de bord de Lille ne lise que les fichiers de Lille.

```python title="Cellule 10 : or"
table.toDF().createOrReplaceTempView("livraisons")
spark.sql("""
    SELECT entrepot, weekofyear(date_expedition) AS semaine, count(*) AS colis,
           round(avg(en_retard), 3) AS taux_retard
    FROM livraisons
    GROUP BY entrepot, weekofyear(date_expedition)
""").write.format("delta").mode("overwrite").partitionBy("entrepot").save(OR)
indicateurs = spark.read.format("delta").load(OR)
print(f"or : {indicateurs.count()} lignes (entrepôt × semaine)")
print(indicateurs.groupBy("entrepot").agg(F.sum("colis").alias("colis"),
                                          F.min("taux_retard").alias("meilleure_semaine"),
                                          F.max("taux_retard").alias("pire_semaine"))
      .orderBy("entrepot").toPandas().to_string(index=False))
```

```plaintext title="Sortie attendue"
or : 32 lignes (entrepôt × semaine)
entrepot  colis  meilleure_semaine  pire_semaine
   Lille   1488              0.238         0.328
    Lyon   1467              0.091         0.174
  Nantes   1017              0.065         0.143
Toulouse    958              0.088         0.193
```

La table or compte 32 lignes : 4 entrepôts × 8 semaines. Lille a le taux de retard le plus élevé **chaque** semaine (de 23,8 % à 32,8 %), loin devant les autres : on le retrouvera dans l'explication du modèle. Dans l'explorateur, le dossier `lakehouse/or/retards_par_semaine` contient un sous-dossier par entrepôt (`entrepot=Lille`…) : c'est le partitionnement.
::::

{#entretien}
## L'entretien d'une table : OPTIMIZE et VACUUM

Chaque écriture ajoute des fichiers ; aucune ne supprime physiquement les anciens, puisqu'ils servent au voyage dans le temps. Deux commandes entretiennent la table :

- **`OPTIMIZE`** regroupe les petits fichiers en gros fichiers. Une table alimentée toutes les minutes finit avec des milliers de fichiers minuscules, que Spark lit lentement.
- **`VACUUM`** supprime physiquement les fichiers qui ne servent plus à la version courante **et** qui sont plus vieux que la durée de rétention : **7 jours par défaut**. Après un VACUUM, on ne peut plus voyager avant cette limite.

::: callout warn VACUUM et le voyage dans le temps
`VACUUM` avec une rétention de 0 heure est refusé par défaut, avec l'erreur `DELTA_VACUUM_RETENTION_PERIOD_TOO_SHORT` (vérifiée dans l'image des TP). Une écriture en cours pourrait encore avoir besoin de ces fichiers. La rétention est donc un **choix de gouvernance** : elle fixe jusqu'où on peut revenir après un incident, mais aussi combien de temps une donnée effacée reste sur le disque. Pour une donnée personnelle à effacer (RGPD), il faut un DELETE **puis** un VACUUM.
:::

{#quiz}
## Quiz

```quiz
- q: Qu'est-ce que le journal de transactions (_delta_log) ajoute à des fichiers Parquet ?
  options:
    - Une compression plus forte
    - Les transactions, l'historique des versions, le schéma imposé et les mises à jour
    - Un index pour les requêtes
    - Le chiffrement des données
  answer: 1
  explain: Les données restent en Parquet ; le journal dit quels fichiers forment chaque version de la table.
- q: Pourquoi garder les colonnes en texte dans la couche bronze ?
  options:
    - Pour gagner de la place
    - Parce que convertir, c'est déjà corriger - le bronze garde la preuve de ce qui est arrivé
    - Parce que Spark ne sait pas lire les nombres
    - Pour aller plus vite
  answer: 1
  explain: Si une règle de l'argent change, on la rejoue depuis le bronze sans redemander les fichiers.
- q: Quelle différence entre le nettoyage de l'étape 3 et une contrainte CHECK ?
  options:
    - Aucune
    - Le nettoyage protège un pipeline ; la contrainte protège la table contre toute écriture, d'où qu'elle vienne
    - La contrainte est plus rapide
    - Le nettoyage est obligatoire, la contrainte facultative
  answer: 1
  explain: La règle inscrite dans la table ne peut pas être oubliée par un autre pipeline ou un notebook.
- q: Après un VACUUM avec la rétention par défaut, que perd-on ?
  options:
    - Rien
    - La possibilité de revenir aux versions dont les fichiers ont plus de 7 jours
    - La version courante
    - Le schéma de la table
  answer: 1
  explain: VACUUM supprime physiquement les anciens fichiers ; le journal ne peut plus les relire.
```
