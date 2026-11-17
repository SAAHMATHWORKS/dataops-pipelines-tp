{#redemarrage time="13:30 – 13:40"}
## Retour sur le matin et redémarrage

**Ce matin**, ColisVert a fixé son critère de succès (attraper au moins 8 retards sur 10, avec au plus une fausse alerte sur deux), construit un pipeline reproductible et tracé chaque essai. Le premier modèle est **trop prudent** : rappel 0,591. L'évaluation a montré qu'en donnant plus de poids aux retards (`class_weight="balanced"`), on dépasse 0,80.

**Cet après-midi**, on passe de « un bon réglage trouvé à la main » à une démarche industrielle : un projet relançable, un registre des versions, une recherche méthodique du meilleur réglage, une mise en service, et une surveillance.

:::: lab Mise en place | Vérifier l'environnement et ouvrir le notebook | 5 min
**1. Les deux services tournent-ils ?** Dans un terminal de la VM :

```bash title="Terminal de la VM"
cd ~/dataops-pipelines-tp
docker compose ps
```

**Vérification :** `dataops-jupyter-1` et `dataops-mlflow-1` sont `Up`. Sinon : `docker compose up -d jupyter mlflow`.

**2. Êtes-vous sur la bonne branche ?** Dans un terminal de JupyterLab :

```bash title="Terminal JupyterLab"
cd /home/lab/projet
git switch tp-dvc
dvc checkout
dvc metrics show
```

**Vérification :** `dvc metrics show` affiche les métriques du pipeline v1 (`f1 0.66`). Si vous avez fini l'évaluation du matin, vous y étiez déjà.

**3. Créez le notebook** `j2-apres-midi.ipynb` dans le dossier `notebooks`, et préparez les données dans la première cellule :

```python title="Cellule 1 : les données de l'après-midi"
import pandas as pd
from colisvert.donnees import DOSSIER_DATA, preparer_donnees
from pipeline.commun import CATEGORIELLES, CIBLE, NUMERIQUES, ajouter_jour_semaine
from pipeline.train import construire_modele

preparer_donnees()
livraisons = ajouter_jour_semaine(pd.read_csv(DOSSIER_DATA / "livraisons.csv"))
X_COLS = CATEGORIELLES + NUMERIQUES
train = livraisons[livraisons["date_expedition"] < "2026-10-19"]
test = livraisons[livraisons["date_expedition"] >= "2026-10-19"]
print(f"train : {len(train)} colis | test : {len(test)} colis | {len(X_COLS)} variables")
```

```plaintext title="Sortie attendue"
livraisons.csv : 5035 colis, dont 862 en retard
arrivees.csv : 56 jours
livraisons_brutes.csv : les mêmes colis, avec des défauts de qualité
train : 3805 colis | test : 1230 colis | 8 variables
```
::::
