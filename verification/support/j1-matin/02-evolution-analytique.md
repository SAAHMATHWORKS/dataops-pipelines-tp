---
subtitle: >-
  Trente ans d'analytique en quatre étapes. Chacune répond aux limites de la précédente,
  et la dernière n'est pas une technologie mais une organisation.
objectives:
  - Expliquer ce qu'est un Data Warehouse et le schéma à l'écriture
  - Expliquer ce qu'est un Data Lake, le schéma à la lecture et le risque de « marécage »
  - Décrire ce qu'un Lakehouse ajoute au Data Lake
  - Énoncer les quatre principes du Data Mesh
---

{#vue}
## Quatre étapes en trente ans

::: figure evolution-analytique.svg
Chaque étape corrige une limite de la précédente. Le Data Mesh change de question : il ne dit pas où stocker, mais qui est responsable.
:::

**Pourquoi connaître cette histoire ?** Parce que vous rencontrerez les quatre dans les entreprises, souvent en même temps. Savoir ce que chacune promet, et ce qu'elle coûte, évite de choisir un outil à la mode pour un problème qu'il ne résout pas.

{#warehouse}
## Le Data Warehouse : la bibliothèque classée

**Le besoin, dans les années 1990 :** les données de l'entreprise sont éparpillées dans des dizaines de logiciels (ventes, stocks, comptabilité). La direction veut des rapports qui les croisent.

**La réponse :** un **entrepôt de données** (*Data Warehouse*), une base centrale où l'on copie chaque nuit les données utiles, **nettoyées et rangées dans des tables**. Bill Inmon et Ralph Kimball en ont posé les méthodes.

**L'analogie :** une bibliothèque où chaque livre reçoit sa **cote** et sa place **avant** d'entrer en rayon. Un livre sans cote reste à la porte.

C'est le **schéma à l'écriture** (*schema on write*) : la structure des tables est fixée à l'avance, et une donnée qui ne la respecte pas est **refusée au chargement**.

| Avantages | Limites |
|---|---|
| Données fiables, requêtes SQL rapides, rapports cohérents | Cher, rigide : ajouter une colonne demande des semaines |
| Une seule version des chiffres | Mal adapté aux données semi-structurées et non structurées |

{#lake}
## Le Data Lake : l'entrepôt de cartons

**Le besoin, dans les années 2010 :** les données explosent (logs, capteurs, JSON, images) et les data scientists veulent **tout** garder, même ce dont on ne connaît pas encore l'usage.

**La réponse :** un **lac de données** (*Data Lake*), un stockage bon marché (HDFS, puis Amazon S3, Azure Data Lake Storage) où l'on dépose les fichiers **bruts**, tels qu'ils arrivent. Le terme a été proposé par James Dixon en 2010.

**L'analogie :** un entrepôt où l'on empile les cartons **sans les ouvrir**. Le rangement est rapide. Retrouver quelque chose est une autre histoire.

C'est le **schéma à la lecture** (*schema on read*) : on interprète la structure **au moment où on lit**.

Le risque porte un nom : le **marécage de données** (*data swamp*). Sans catalogue ni contrôle, plus personne ne sait ce que contient le lac, ni si c'est juste.

:::: lab Démo | Schéma à l'écriture ou à la lecture ? | 5 min
Un fichier contient une valeur inattendue : la distance du colis CV00002 vaut `inconnu`.

**Comme un Data Warehouse :** on impose le type « entier » au chargement.

```python title="Cellule 7 : schéma à l'écriture"
import io

brut = """id_colis,distance_km
CV00001,53
CV00002,inconnu
CV00003,120
"""

try:
    pd.read_csv(io.StringIO(brut), dtype={"distance_km": "int64"})
except ValueError as erreur:
    print("Refusé :", erreur)
```

```plaintext title="Sortie attendue"
Refusé : invalid literal for int() with base 10: 'inconnu'
```

Le chargement **échoue** : la donnée ne respecte pas le schéma, elle reste à la porte.

**Comme un Data Lake :** on stocke tout en texte (`dtype=str`), puis on convertit au moment de lire. `errors="coerce"` remplace ce qui n'est pas un nombre par `NaN` (*Not a Number*, une valeur manquante).

```python title="Cellule 8 : schéma à la lecture"
lac = pd.read_csv(io.StringIO(brut), dtype=str)
lac["distance_km"] = pd.to_numeric(lac["distance_km"], errors="coerce")
print(lac)
```

```plaintext title="Sortie attendue"
  id_colis  distance_km
0  CV00001         53.0
1  CV00002          NaN
2  CV00003        120.0
```

Le fichier est **accepté**. Mais le problème n'a pas disparu : il est **reporté** sur chaque personne qui lira la colonne. Les distances sont devenues des nombres à virgule (`53.0`), parce qu'en pandas une colonne d'entiers ne peut pas contenir `NaN`.
::::

{#lakehouse}
## Le Lakehouse : le lac avec un registre

**Le besoin, vers 2020 :** les entreprises paient deux systèmes, un lac pour la data science et un entrepôt pour les rapports, et copient les données de l'un à l'autre. Les chiffres finissent par diverger.

**La réponse :** le **Lakehouse** garde les fichiers dans le lac, dans un format ouvert (Parquet), et y ajoute un **journal de transactions** : un registre qui note chaque écriture. Grâce à lui, le lac gagne ce qui faisait la force de l'entrepôt :

- des écritures **tout ou rien** (transactions ACID) : jamais de table à moitié écrite ;
- un **contrôle du schéma** à l'écriture, comme dans la Cellule 7 ;
- le **voyage dans le temps** : relire la table telle qu'elle était hier.

Les formats les plus répandus sont **Delta Lake**, **Apache Iceberg** et **Apache Hudi**. Vous construirez un Lakehouse avec Spark et Delta Lake **le jour 5**.

{#mesh}
## Le Data Mesh : une organisation, pas un outil

**Le besoin :** même avec un bon Lakehouse, une **équipe data centrale** devient un goulot d'étranglement. Elle reçoit toutes les demandes, sans connaître le métier de chaque service.

**La réponse :** le **Data Mesh**, proposé par Zhamak Dehghani en 2019, confie les données **aux équipes métier qui les produisent**. Il repose sur quatre principes :

| Principe | Ce que ça veut dire | Chez ColisVert |
|---|---|---|
| **1. Propriété par domaine** | Chaque domaine métier est responsable de ses données | L'exploitation possède les livraisons, le service client les réclamations |
| **2. La donnée comme produit** | Les données publiées sont documentées, fiables et faciles à utiliser, comme un produit | Une table « livraisons » avec sa définition du retard et son heure de mise à jour garantie |
| **3. Une plateforme en libre-service** | Une équipe fournit les outils communs pour que chaque domaine publie seul | Stockage, orchestration et catalogue partagés |
| **4. Une gouvernance fédérée** | Des règles communes, décidées ensemble et vérifiées automatiquement | Même format de date partout, données personnelles masquées |

::: callout warn Idée reçue
« On achète un Data Mesh. » Non : aucun logiciel ne fait d'une entreprise un Data Mesh. C'est une façon de répartir les **responsabilités**. Elle demande une plateforme solide, et une organisation assez mûre pour la porter.
:::

::: callout tip Question fréquente : « Faut-il choisir un seul de ces modèles ? »
Non. Beaucoup d'entreprises ont un entrepôt **et** un lac, et migrent vers un Lakehouse pour n'en garder qu'un. Le Data Mesh se combine avec n'importe lequel des trois : il ne dit pas où stocker, il dit qui est responsable.
:::

{#avance}
## Pour aller plus loin : sous le capot d'un format de table

Ce bloc est pour les profils avancés ; rien ici n'est exigé dans l'évaluation.

**Comment un journal de transactions tient-il ses promesses ?** Prenons Delta Lake, que vous manipulerez le jour 5. Une table Delta est un dossier qui contient deux choses : des fichiers de données **Parquet**, et un sous-dossier `_delta_log/` avec un fichier JSON **par transaction**, numéroté.

```json title="_delta_log/00000000000000000001.json (extrait, ne pas exécuter)"
{"add": {"path": "part-00000-5f2a.snappy.parquet", "size": 320537,
         "stats": "{\"numRecords\": 5035, \"minValues\": {\"distance_km\": 5}, \"maxValues\": {\"distance_km\": 300}}"}}
```

Trois conséquences concrètes :

- **Tout ou rien.** Une écriture n'existe que lorsque son fichier JSON est écrit, en dernier. Si le programme meurt avant, les fichiers Parquet orphelins sont ignorés : aucun lecteur ne verra une table à moitié écrite.
- **Voyage dans le temps.** Lire la version 12, c'est rejouer les JSON 0 à 12. Les anciennes versions restent lisibles tant qu'on n'a pas nettoyé les fichiers (commande `VACUUM`).
- **Lecture plus rapide.** Chaque entrée du journal garde des **statistiques** (nombre de lignes, minimum et maximum par colonne). Pour `WHERE distance_km > 250`, le moteur saute les fichiers dont le maximum est 200 sans les ouvrir : c'est le *data skipping*.

**Et les deux autres formats ?** Iceberg range ses métadonnées en arbre (manifestes) plutôt qu'en journal plat, ce qui aide sur les très grandes tables et fait d'Iceberg le format le plus neutre entre moteurs ; Hudi vise l'ingestion en continu avec des mises à jour ligne à ligne. Les trois reposent sur la même idée : **des fichiers ouverts, plus une couche de métadonnées transactionnelles**. Depuis 2024-2025, la frontière s'estompe : Delta et Iceberg savent s'exposer mutuellement (Delta « UniForm » écrit des métadonnées Iceberg à côté des siennes), et les catalogues managés lisent les deux.

**Les critiques sérieuses du Data Mesh**, à connaître avant de le proposer :

| Critique | Quand elle est fondée |
|---|---|
| Il duplique les compétences : chaque domaine doit recruter des profils data | Entreprises moyennes : quatre domaines qui se partagent deux data engineers ne font pas un mesh |
| Sans plateforme centrale forte, il produit quatre marécages au lieu d'un | Si le principe 3 (libre-service) est négligé, les principes 1 et 2 aggravent le chaos |
| La gouvernance fédérée est lente à mettre en place | Les standards communs (identifiants, formats, sécurité) demandent des mois de négociation |

La règle pratique : le Data Mesh répond à un problème d'**échelle organisationnelle** (beaucoup de domaines, beaucoup d'équipes). Chez ColisVert, 4 entrepôts et une équipe data de 5 personnes, un Lakehouse central bien gouverné suffit largement. Dire « non, pas encore » à un Data Mesh est souvent la réponse experte.

{#quiz}
## Quiz de validation

```quiz
- q: Que signifie « schéma à l'écriture » ?
  options:
    - Les données sont interprétées au moment où on les lit
    - Les données qui ne respectent pas la structure sont refusées au chargement
    - Le schéma est écrit dans un fichier séparé
    - Les données sont écrites sans aucune structure
  answer: 1
  explain: C'est le principe du Data Warehouse, illustré par la Cellule 7.
- q: Qu'est-ce qu'un « marécage de données » ?
  options:
    - Un lac trop petit
    - Un Data Warehouse en panne
    - Un lac où plus personne ne sait ce qu'il contient ni si c'est juste
    - Un format de fichier
  answer: 2
  explain: Sans catalogue ni contrôle, le lac devient inutilisable.
- q: Qu'est-ce qu'un Lakehouse ajoute à un Data Lake ?
  options:
    - Un journal de transactions, qui apporte écritures tout ou rien, contrôle du schéma et voyage dans le temps
    - Des disques plus rapides
    - Une interface graphique
    - Le stockage des images
  answer: 0
  explain: Les fichiers restent dans le lac, en format ouvert. Le journal leur apporte la fiabilité d'un entrepôt.
- q: Lequel n'est PAS un principe du Data Mesh ?
  options:
    - La propriété des données par domaine
    - La donnée comme produit
    - Une équipe data centrale qui traite toutes les demandes
    - Une gouvernance fédérée
  answer: 2
  explain: C'est justement le goulot d'étranglement que le Data Mesh veut supprimer.
```
