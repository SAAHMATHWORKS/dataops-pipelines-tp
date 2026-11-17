{#retour time="13:30 – 13:33"}
## Retour sur le matin

**Ce matin**, on a traduit le modèle de ColisVert en euros. Au seuil de 0,40, l'alerte SMS économise environ 0,96 € par colis, et l'investissement est amorti au dixième mois si un retard non prévenu coûte 15 €. On a aussi vu qu'une équipe se juge sur ses bénéfices, pas sur le nombre de modèles livrés.

**Cet après-midi, la question devient : que coûte le modèle à faire tourner ?** Un modèle consomme du **processeur** à chaque prédiction, de la **mémoire** tant qu'il est chargé et du **stockage** pour chacune de ses versions. Deux TP d'ingénieur :

- **TP 1 :** chercher avec Optuna, et tracer dans MLflow, les modèles qui donnent le meilleur compromis entre qualité et empreinte, puis choisir sous contrainte ;
- **TP 2 :** servir plusieurs modèles derrière **un seul** point d'accès avec MLflow PyFunc. Le champion répond, le challenger tourne en ombre, et un rédacteur prépare le SMS du client. Ce rédacteur est la place réservée au LLM du jour 5.

{#mise-en-place time="13:33 – 13:40"}
## Mise en place

:::: lab Mise en place | Le code du jour, MLflow et le notebook | 7 min
**1. Dans un terminal de JupyterLab**, récupérez les nouveautés du dépôt (le service de prédiction du TP 2) :

```bash title="Terminal JupyterLab"
cd /home/lab/projet
git switch tp-dvc
git pull --no-rebase --no-edit origin main
ls service
```

```plaintext title="Sortie attendue (ls)"
colisvert_service.py
```

**2. Dans un terminal de la VM**, vérifiez que MLflow tourne (Airflow n'est pas utile cet après-midi) :

```bash title="Terminal de la VM"
cd ~/dataops-pipelines-tp
docker compose up -d jupyter mlflow
docker compose ps
```

**Vérification :** `jupyter` (8888) et `mlflow` (5000) sont `Up`. Vous pouvez arrêter Airflow pour libérer de la mémoire : `docker compose stop airflow`.

**3. Créez le notebook** `j4-apres-midi.ipynb` dans le dossier `notebooks`. La première cellule prépare les quatre jeux de données de l'après-midi. Ce sont les découpages du jour 2 : on choisit sur la semaine de **validation** et l'on mesure une seule fois sur le **test**.

```python title="Cellule 0 : les données de l'après-midi"
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
entrainement = train[train["date_expedition"] < "2026-10-12"]
validation = train[train["date_expedition"] >= "2026-10-12"]
print(f"entraînement {len(entrainement)} | validation {len(validation)} | "
      f"test {len(test)} | décembre {len(decembre)} colis")
```

```plaintext title="Sortie attendue"
livraisons.csv : 5035 colis, dont 862 en retard
arrivees.csv : 56 jours
livraisons_brutes.csv : les mêmes colis, avec des défauts de qualité
entraînement 3166 | validation 639 | test 1230 | décembre 3426 colis
```

::: hint
`git pull` répond `Your local changes would be overwritten` : `git stash`, puis relancez `git pull`, puis `git stash pop`. `ModuleNotFoundError: No module named 'colisvert'` : le notebook n'a pas été ouvert depuis le JupyterLab du conteneur.
:::
::::
