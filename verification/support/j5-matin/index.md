{#retour time="09:00 – 09:04"}
## Retour sur le jour 4

**Hier**, ColisVert a traduit son modèle en euros, mis ses processus sous carte de contrôle et mesuré ses bénéfices. L'après-midi, la forêt de 20 Mo est passée à 445 Ko, puis la régression logistique de 4,4 Ko a fait aussi bien. Enfin, un service PyFunc unique a servi le champion, gardé la forêt en ombre et préparé les SMS.

**Aujourd'hui, le jour 5 : le DataOps Factory.** L'usine assemble tout ce qu'on a construit, et elle a besoin de règles pour durer.

- **Ce matin :**
  - qui est responsable de quelles données, et comment le vérifier par du code ;
  - comment organiser les équipes et accompagner le changement ;
  - une plateforme bronze, argent, or sur Delta Lake avec Spark ;
  - ce qu'il reste à automatiser ;
  - enfin, ouvrir le modèle pour expliquer ses décisions.
- **Cet après-midi :** les agents IA, et le bilan de la semaine.

{#mise-en-place time="09:04 – 09:10"}
## Mise en place

:::: lab Mise en place | Le dépôt, les services et le notebook | 6 min
**1. Dans un terminal de JupyterLab**, récupérez les nouveautés du dépôt :

```bash title="Terminal JupyterLab"
cd /home/lab/projet
git switch tp-dvc
git pull --no-rebase --no-edit origin main
```

**2. Dans un terminal de la VM**, vérifiez que JupyterLab et MLflow tournent :

```bash title="Terminal de la VM"
cd ~/dataops-pipelines-tp
docker compose up -d jupyter mlflow
docker compose ps
```

**3. Créez le notebook** `j5-matin.ipynb` dans le dossier `notebooks`. La première cellule prépare les données en pandas pour le TP sur le modèle, et les chemins des fichiers bruts pour le TP Delta Lake :

```python title="Cellule 0 : les données du matin"
import pandas as pd
from colisvert.donnees import DOSSIER_DATA, generer_livraisons_decembre, preparer_donnees
from pipeline.commun import CATEGORIELLES, CIBLE, NUMERIQUES, RACINE, ajouter_jour_semaine
from pipeline.train import construire_modele

preparer_donnees()
livraisons = ajouter_jour_semaine(pd.read_csv(DOSSIER_DATA / "livraisons.csv"))
decembre = ajouter_jour_semaine(pd.DataFrame(generer_livraisons_decembre()))
X_COLS = CATEGORIELLES + NUMERIQUES
train = livraisons[livraisons["date_expedition"] < "2026-10-19"]
test = livraisons[livraisons["date_expedition"] >= "2026-10-19"]
LAC = RACINE / "lakehouse"                    # la plateforme Delta Lake du TP
print(f"train {len(train)} | test {len(test)} | décembre {len(decembre)} colis | lac : {LAC}")
```

```plaintext title="Sortie attendue"
livraisons.csv : 5035 colis, dont 862 en retard
arrivees.csv : 56 jours
livraisons_brutes.csv : les mêmes colis, avec des défauts de qualité
train 3805 | test 1230 | décembre 3426 colis | lac : /home/lab/projet/lakehouse
```

::: callout warn Le premier démarrage de Delta Lake télécharge environ 90 Mo
Au TP Delta Lake, la première session Spark télécharge les bibliothèques Java de Delta Lake depuis Maven Central (`repo1.maven.org`). Il y en a environ 90 Mo, et elles sont gardées ensuite dans `.home/.ivy2.5.2` : les sessions suivantes démarrent sans rien télécharger. Si la cellule reste longtemps sans réponse au premier lancement, c'est ce téléchargement.
:::
::::
