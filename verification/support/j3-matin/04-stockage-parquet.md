---
subtitle: >-
  Le même tableau peut peser 5 fois moins et se lire vingt fois plus vite, simplement parce qu'il est
  rangé autrement sur le disque. Parquet range les données par colonnes, les compresse, et note
  pour chaque bloc le minimum et le maximum de chaque colonne. On ouvre le fichier des taxis pour
  le vérifier.
objectives:
  - Expliquer la différence entre un stockage en lignes et un stockage en colonnes
  - Décrire l'organisation d'un fichier Parquet (groupes de lignes, colonnes, pages, métadonnées)
  - Lire les métadonnées d'un fichier Parquet avec pyarrow
  - Mesurer l'écart de taille et de lecture entre CSV et Parquet
---

{#pourquoi}
## Lignes ou colonnes ?

**L'analogie de la bibliothèque.** Une bibliothèque peut ranger ses fiches **par livre** : une fiche par livre, avec titre, auteur, année, nombre de pages. Pour connaître le nombre moyen de pages de toute la collection, il faut sortir **chaque** fiche et y chercher une seule information. Elle peut aussi tenir **un registre par information** : un registre des titres, un registre des années, un registre des nombres de pages. La moyenne des pages se calcule alors en ouvrant **un seul** registre.

- Le **stockage en lignes** (CSV, une base de données transactionnelle classique) range les fiches par livre. Parfait pour lire ou modifier **un enregistrement entier** : « affiche la commande n° 4217 ».
- Le **stockage en colonnes** (Parquet, les entrepôts de données) range par registre. Parfait pour **analyser** : « le pourboire moyen de 3 millions de courses » ne lit que la colonne des pourboires.

Deux bonus du rangement par colonne :

- **Il se compresse beaucoup mieux.** Une colonne contient des valeurs du même type, souvent répétées : la colonne `payment_type` des taxis ne contient que 5 valeurs différentes sur 3 millions de lignes. On la stocke comme un **dictionnaire** (0 = inconnu, 1 = carte…) suivi de petits numéros, puis on code les répétitions (« 1, 1, 1, 1 » devient « 4 fois 1 »).
- **Chaque bloc porte ses statistiques.** Le fichier peut noter, pour chaque bloc d'une colonne, son minimum et son maximum. Un moteur qui cherche les courses du 15 janvier peut alors **sauter** les blocs dont les dates ne contiennent pas le 15 janvier, sans les lire.

{#structure}
## L'intérieur d'un fichier Parquet

| Niveau | Ce que c'est | Ordre de grandeur |
|---|---|---|
| **Fichier** | Un fichier `.parquet`, avec à la fin un pied de page (les métadonnées) | Quelques Mo à quelques Go |
| **Groupe de lignes** (*row group*) | Un paquet de lignes consécutives, stocké colonne par colonne | Souvent 100 000 à 1 million de lignes |
| **Morceau de colonne** (*column chunk*) | Les valeurs d'une colonne pour un groupe de lignes | Compressé, avec ses statistiques |
| **Page** | L'unité de lecture et de compression à l'intérieur d'un morceau | Environ 1 Mo |

Les **métadonnées**, en fin de fichier, décrivent tout cela : le schéma (noms et **types** des colonnes), le nombre de lignes, l'emplacement et la taille de chaque morceau, la compression, les statistiques. Un moteur commence toujours par les lire : en quelques kilo-octets, il sait exactement quoi aller chercher, et où.

{#lire}
## Ouvrir le fichier des taxis

:::: lab Démo | Les métadonnées, sans lire les données | 8 min
`pyarrow` est la bibliothèque de référence pour Parquet en Python ; pandas l'utilise en coulisses. `ParquetFile` ouvre le fichier et lit seulement son pied de page.

```python title="Cellule 4 : la carte d'identité du fichier"
import pyarrow.parquet as pq

TAXIS = "/home/lab/projet/data/taxis/yellow_tripdata_2024-01.parquet"
fichier = pq.ParquetFile(TAXIS)
meta = fichier.metadata
print(f"{meta.num_rows:,} lignes, {meta.num_columns} colonnes, {meta.num_row_groups} groupes de lignes")
print("écrit par :", meta.created_by)
for i in range(meta.num_row_groups):
    groupe = meta.row_group(i)
    print(f"groupe {i} : {groupe.num_rows:,} lignes, compression {groupe.column(0).compression}")
```

```plaintext title="Sortie attendue"
2,964,624 lignes, 19 colonnes, 3 groupes de lignes
écrit par : parquet-cpp-arrow version 14.0.2
groupe 0 : 1,048,576 lignes, compression ZSTD
groupe 1 : 1,048,576 lignes, compression ZSTD
groupe 2 : 867,472 lignes, compression ZSTD
```

Près de 3 millions de courses, en **3 groupes de lignes** : deux de 1 048 576 lignes (2²⁰, la taille par défaut de pyarrow), et le reste. Le fichier a été écrit par **pyarrow** (la bibliothèque C++ d'Apache Arrow), compressé en **ZSTD**.

Le schéma est **typé** : `fichier.schema_arrow` montre que les dates sont de vrais horodatages, les montants des nombres décimaux. Un CSV, lui, ne contient que du texte : chaque lecteur doit deviner les types, et se trompe parfois (souvenez-vous des dates au format `jj/mm/aaaa` du jour 1).

**Combien pèse chaque colonne ?** Additionnons, pour chaque colonne, la taille compressée de ses morceaux :

```python title="Cellule 5 : le poids de chaque colonne"
tailles = {}
for i in range(meta.num_row_groups):
    for j in range(meta.num_columns):
        morceau = meta.row_group(i).column(j)
        tailles[morceau.path_in_schema] = tailles.get(morceau.path_in_schema, 0) + morceau.total_compressed_size
total = sum(tailles.values())
for nom, taille in sorted(tailles.items(), key=lambda kv: -kv[1])[:5]:
    print(f"{nom:<22} {taille / 1e6:5.1f} Mo  {taille / total:6.1%}")
utiles = ["tpep_pickup_datetime", "payment_type", "fare_amount", "tip_amount"]
print(f"les 4 colonnes du TP : {sum(tailles[c] for c in utiles) / 1e6:.1f} Mo, {sum(tailles[c] for c in utiles) / total:.1%} du fichier")
```

```plaintext title="Sortie attendue"
tpep_dropoff_datetime   13.0 Mo   26.1%
tpep_pickup_datetime    12.8 Mo   25.6%
total_amount             4.9 Mo    9.8%
trip_distance            4.1 Mo    8.2%
tip_amount               3.4 Mo    6.8%
les 4 colonnes du TP : 19.9 Mo, 39.8% du fichier
```

**Les deux colonnes de dates pèsent à elles seules la moitié du fichier.** Ce sont des horodatages à la microseconde, presque tous différents : rien à répéter, donc presque rien à compresser. À l'inverse, `payment_type` (5 valeurs possibles) pèse moins de 0,5 Mo pour 3 millions de lignes, grâce au dictionnaire. Le TP n'aura besoin que de 4 colonnes : un moteur qui sait lire par colonne ne lira que 40 % du fichier, et cette part serait bien plus faible sans la date de prise en charge.

**Les statistiques sont-elles là ?** Regardons, dans le premier groupe, quelles colonnes portent un minimum et un maximum :

```python title="Cellule 6 : les statistiques du premier groupe"
groupe = meta.row_group(0)
for j in range(meta.num_columns):
    morceau = groupe.column(j)
    stats = morceau.statistics
    if morceau.path_in_schema in ["tpep_pickup_datetime", "payment_type", "fare_amount", "PULocationID"]:
        print(f"{morceau.path_in_schema:<22} statistiques : {morceau.is_stats_set}"
              + (f", min {stats.min}, max {stats.max}" if morceau.is_stats_set and stats.has_min_max else ""))
```

```plaintext title="Sortie attendue"
tpep_pickup_datetime   statistiques : False
PULocationID           statistiques : False
payment_type           statistiques : False
fare_amount            statistiques : False
```

**Surprise : le fichier publié par la TLC ne contient aucune statistique.** Son producteur ne les a pas écrites. Conséquence : un moteur ne pourra **sauter aucun groupe de lignes** sur ce fichier ; il pourra seulement ne lire que les colonnes utiles, et rejeter les lignes non voulues pendant la lecture, sans les construire en mémoire. Leçon de terrain : les avantages d'un format ne sont là que si le producteur les utilise. **Vérifiez les métadonnées, ne les supposez pas.** La cellule suivante montre qu'un fichier réécrit par pandas, lui, porte bien ses statistiques.
::::

{#csv-parquet}
## CSV contre Parquet, mesuré

:::: lab Démo | Le même million de lignes, deux formats | 8 min
On prend le premier groupe de lignes (1 048 576 courses), on l'écrit en CSV et en Parquet, puis on compare la taille et le temps de lecture. Les fichiers vont dans `/tmp` : ils ne concernent pas le dépôt.

```python title="Cellule 7 : CSV contre Parquet"
import os
import time

import pandas as pd

courses = fichier.read_row_group(0).to_pandas()
courses.to_csv("/tmp/courses.csv", index=False)
courses.to_parquet("/tmp/courses.parquet", index=False)
print(f"CSV     : {os.path.getsize('/tmp/courses.csv') / 1e6:6.1f} Mo")
print(f"Parquet : {os.path.getsize('/tmp/courses.parquet') / 1e6:6.1f} Mo")

for nom, lire in [
    ("CSV, tout", lambda: pd.read_csv("/tmp/courses.csv")),
    ("Parquet, tout", lambda: pd.read_parquet("/tmp/courses.parquet")),
    ("Parquet, 1 colonne", lambda: pd.read_parquet("/tmp/courses.parquet", columns=["tip_amount"])),
]:
    debut = time.perf_counter()
    tableau = lire()
    print(f"{nom:<20} {time.perf_counter() - debut:.2f} s")
print("type de la date relue depuis le CSV :", pd.read_csv("/tmp/courses.csv", nrows=5)["tpep_pickup_datetime"].dtype)
print("statistiques dans le Parquet réécrit :", pq.ParquetFile("/tmp/courses.parquet").metadata.row_group(0).column(1).is_stats_set)
```

```plaintext title="Sortie attendue (les durées varient selon la machine)"
CSV     :  106.3 Mo
Parquet :   21.7 Mo
CSV, tout            1.47 s
Parquet, tout        0.08 s
Parquet, 1 colonne   0.02 s
type de la date relue depuis le CSV : str
statistiques dans le Parquet réécrit : True
```

Les durées viennent de la machine de vérification (4 cœurs) ; sur votre VM, elles seront différentes, mais les **rapports** entre elles resteront du même ordre :

- **Taille :** le CSV pèse **5 fois plus** (106,3 Mo contre 21,7 Mo). Et ce Parquet est compressé en Snappy, l'option par défaut de pandas ; en ZSTD, comme l'original, il serait encore plus petit.
- **Lecture :** relire le CSV est **une vingtaine de fois plus lent** : il faut découper le texte et convertir chaque valeur. Lire une seule colonne du Parquet est encore plus rapide.
- **Types :** la date relue depuis le CSV est du **texte** (`str`), plus une date. Il faudrait la reconvertir, et deviner son format.
- **Statistiques :** le fichier réécrit par pandas (avec pyarrow) les contient, contrairement à l'original.
::::

::: callout info Et dans Azure, Fabric ou Google Cloud ?
Parquet est partout. Les tables du Lakehouse de **Microsoft Fabric** sont des tables **Delta**, c'est-à-dire des fichiers Parquet plus un journal de transactions (on y revient au jour 5). **Azure Data Lake Storage** et **Google Cloud Storage** stockent les fichiers ; **BigQuery** sait les interroger directement en table externe. Savoir lire un fichier Parquet, c'est savoir lire le stockage de toutes ces plateformes.
:::

{#avance}
## Pour aller plus loin : taille des groupes, tri et petits fichiers

Ce bloc est pour les profils avancés ; rien ici n'est exigé dans l'évaluation.

**La taille des groupes de lignes est un compromis.** Des groupes trop petits multiplient les métadonnées et les lectures ; des groupes trop grands empêchent de sauter finement des blocs et demandent beaucoup de mémoire à l'écriture. Les valeurs courantes vont de 128 Mo à 1 Go non compressés par groupe pour les traitements massifs ; pyarrow découpe par défaut par nombre de lignes, comme dans ce fichier.

**Le tri rend les statistiques utiles.** Les statistiques min/max ne servent que si les valeurs sont **regroupées** : si chaque groupe contient des courses de tout le mois, son minimum est le 1er janvier et son maximum le 31, et aucun groupe ne peut être sauté. Trier les données par date avant de les écrire (ou les **partitionner** par jour, un dossier par date) rend le saut efficace. Les formats de table vont plus loin : Delta Lake propose le **Z-ordering** et le *liquid clustering*, qui regroupent les lignes selon plusieurs colonnes à la fois.

**Le problème des petits fichiers.** Un pipeline qui écrit un fichier Parquet par minute produit 525 600 fichiers par an. Chaque lecture doit alors ouvrir des milliers de pieds de page : les performances s'effondrent. D'où les opérations de **compactage** (`OPTIMIZE` dans Delta Lake), qui fusionnent les petits fichiers en gros. C'est un travail d'exploitation récurrent, qu'un orchestrateur planifie.

**Compression : ZSTD, Snappy, Gzip.** Snappy compresse peu mais très vite ; Gzip compresse bien mais lentement ; ZSTD offre un bon compromis et devient le choix par défaut de nombreux outils. Le fichier de la TLC est en ZSTD. Quand pandas réécrit un fichier, il utilise Snappy par défaut : c'est une des raisons pour lesquelles un fichier réécrit n'a pas forcément la même taille que l'original.

{#quiz}
## Quiz de validation

```quiz
- q: Pourquoi le stockage en colonnes accélère-t-il l'analyse ?
  options:
    - Parce qu'il trie automatiquement les données
    - Parce qu'une requête ne lit que les colonnes dont elle a besoin, mieux compressées
    - Parce qu'il interdit les valeurs manquantes
    - Parce qu'il est toujours stocké en mémoire
  answer: 1
  explain: Une moyenne de pourboires ne lit que la colonne des pourboires, pas les 18 autres.
- q: Où se trouvent les métadonnées d'un fichier Parquet ?
  options:
    - Dans un fichier séparé obligatoire
    - Dans le pied de page, à la fin du fichier
    - Dans la première ligne, comme l'en-tête d'un CSV
    - Nulle part, Parquet n'en a pas
  answer: 1
  explain: Le moteur lit d'abord ce pied de page, qui décrit le schéma, les groupes de lignes et leurs statistiques.
- q: À quoi servent les statistiques min/max d'un groupe de lignes ?
  options:
    - À afficher un résumé du fichier
    - À sauter, sans les lire, les groupes qui ne peuvent pas contenir les valeurs cherchées
    - À compresser les données
    - À vérifier les droits d'accès
  answer: 1
  explain: Elles ne sont efficaces que si les valeurs sont regroupées, par exemple triées par date.
- q: Quel avantage Parquet a-t-il sur le CSV, en plus de la taille ?
  options:
    - Il est lisible dans un éditeur de texte
    - Il garde les types des colonnes - une date reste une date
    - Il ne peut pas contenir d'erreurs
    - Il est plus facile à modifier ligne par ligne
  answer: 1
  explain: Le CSV ne contient que du texte ; chaque lecteur doit deviner les types.
```
