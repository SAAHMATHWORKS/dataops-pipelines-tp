{#retour time="09:00 – 09:05"}
## Retour sur le jour 2

**Hier**, ColisVert a construit son premier produit data :

- un **pipeline** reproductible (DVC), suivi par **MLflow** ;
- un **registre** de modèles, avec une règle de promotion écrite à l'avance ;
- un modèle **en service** ;
- une **surveillance de la dérive**, qui a montré que décembre ne ressemble pas à octobre.

**Aujourd'hui**, deux questions d'architecte :

- **Ce matin :** avec quels outils faire grandir tout cela ? Les construire, les acheter, ou les louer à un cloud ? Et sur quel moteur faire tourner les calculs quand les données passent de quelques milliers à quelques millions de lignes ?
- **Cet après-midi :** comment faire tourner le pipeline seul, chaque matin, avec un orchestrateur (Airflow).

{#donnees time="09:05 – 09:15"}
## Les données du jour : les taxis de New York

**Pourquoi d'autres données ?** Les 5 035 colis de ColisVert tiennent dans n'importe quel outil : pandas, DuckDB ou Spark répondent en une fraction de seconde, et l'on ne voit aucune différence. Pour comparer des moteurs, il faut du volume.

La commission des taxis de New York (TLC) publie chaque mois le détail de toutes les courses de taxi, au format **Parquet**. Janvier 2024 pour les taxis jaunes, c'est **près de 3 millions de courses** dans un fichier de 50 Mo. Ce sont des données réelles, avec de vrais défauts, comme toutes les données d'entreprise. On les télécharge maintenant, pour qu'elles soient prêtes au TP de 11 h 10.

:::: lab Mise en place | Importer les données avec leur provenance | 10 min
**1. Dans un terminal de JupyterLab**, placez-vous sur votre branche :

```bash title="Terminal JupyterLab"
cd /home/lab/projet
git switch tp-dvc
git status --short
```

**2. Importez les deux fichiers avec DVC.** Au jour 1, `dvc add` versionnait un fichier que vous aviez déjà. `dvc import-url` va plus loin : il **télécharge** le fichier, le range dans le cache, et note **d'où il vient** (l'adresse et l'étiquette de version donnée par le serveur). C'est la **provenance** de la donnée, écrite dans le dépôt.

```bash title="Terminal JupyterLab"
mkdir -p data/taxis
dvc import-url https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2024-01.parquet data/taxis/
dvc import-url https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv data/taxis/
md5sum data/taxis/yellow_tripdata_2024-01.parquet data/taxis/taxi_zone_lookup.csv
```

- Le premier fichier contient les courses ; le second, la table des **265 zones** de la ville (numéro, arrondissement, nom du quartier).
- Le téléchargement prend de quelques secondes à une minute selon le réseau.

**Vérification :** `md5sum` affiche exactement ces deux empreintes :

```plaintext title="Sortie attendue"
10dff36f5a2fc325274438bf361c70f0  data/taxis/yellow_tripdata_2024-01.parquet
c6064b7c144c716450641f769659d178  data/taxis/taxi_zone_lookup.csv
```

**3. Regardez le ticket**, puis versionnez-le :

```bash title="Terminal JupyterLab"
cat data/taxis/yellow_tripdata_2024-01.parquet.dvc
git add data/taxis/*.dvc data/taxis/.gitignore
git commit -m "Données externes : taxis de New York, janvier 2024"
```

Le ticket a deux parties. Sous `deps`, la **source** : l'adresse du fichier et son étiquette de version (`etag`). Sous `outs`, la **copie locale** : son empreinte MD5 et sa taille, 49 961 641 octets. Si la ville republie un jour le fichier, `dvc update data/taxis/yellow_tripdata_2024-01.parquet.dvc` le détectera par l'étiquette et téléchargera la nouvelle version, qui deviendra un nouveau commit. Sans provenance, on ne saurait même pas que la donnée a changé.

::: hint
`ERROR: … Connection` ou `Max retries exceeded` : la VM n'atteint pas le serveur de la TLC ; prévenez le formateur, qui a une copie de secours. `fatal: invalid reference: tp-dvc` : vous n'avez pas la branche du TP ; le rattrapage est dans la page d'accueil du jour 2. Une autre empreinte MD5 : le téléchargement a été coupé ; supprimez le fichier et son ticket (`rm data/taxis/yellow_tripdata_2024-01.parquet*`), puis relancez l'import.
:::
::::

::: callout info Les données et leur licence
Les données de la TLC sont publiques et gratuites ; la TLC précise qu'elle ne garantit pas leur exactitude, car elles sont transmises par les prestataires techniques des taxis. On le constatera ce matin : courses de 2002, montants négatifs, distances de plusieurs centaines de milliers de miles. Exactement le genre de défauts que le contrat de données du jour 1 sert à attraper.
:::
