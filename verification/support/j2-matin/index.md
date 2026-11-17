{#retour time="09:00 – 09:10"}
## Retour sur le jour 1

**Hier matin**, le diagnostic de ColisVert : 17,1 % de colis en retard, deux définitions du mot « retard », un fichier qui arrive trop tard un jour sur sept, une chaîne de valeur où l'on attend 94 % du temps.

**Hier après-midi**, la première brique technique : les données sont **versionnées** avec DVC et Git. On sait retrouver exactement le fichier d'une date donnée.

**Aujourd'hui**, ColisVert lance son premier produit data : **un modèle qui prédit, au moment de l'expédition, si un colis sera en retard**. Ce matin, on le construit comme un pipeline reproductible et on garde la trace de chaque essai. Cet après-midi, on cherche le meilleur modèle, on le déploie et on surveille sa dérive.

{#mise-a-jour time="09:10 – 09:20"}
## Mettre à jour l'environnement

**Pourquoi ?** Le dépôt des TP s'enrichit chaque jour. Ce matin, il reçoit le code du pipeline (`pipeline/`) et un deuxième service : le **serveur MLflow**, qui va enregistrer vos expériences. Vous allez récupérer ces nouveautés **sans perdre votre travail d'hier**, qui est sur votre branche `tp-dvc`.

:::: lab Mise en place | Récupérer le code du jour et démarrer MLflow | 10 min
**1. Dans un terminal de JupyterLab** (**File › New › Terminal**), placez-vous sur votre branche et fusionnez-y la branche principale du dépôt GitHub :

```bash title="Terminal JupyterLab"
cd /home/lab/projet
git switch tp-dvc
git pull --no-rebase --no-edit origin main
ls pipeline
```

- `git pull origin main` télécharge les nouveautés de la branche `main` du dépôt GitHub et les **fusionne** dans votre branche. `--no-rebase` demande une fusion classique ; `--no-edit` accepte le message de fusion proposé, sans ouvrir d'éditeur.
- Vos commits d'hier (l'initialisation de DVC, les tickets des données) restent intacts : la fusion **ajoute** les fichiers du jour à côté.

**Vérification :** `git pull` se termine par une liste de fichiers ajoutés, dont `pipeline/prepare.py`, `pipeline/train.py` et `MLproject`. Puis `ls pipeline` affiche :

```plaintext title="Sortie attendue (ls pipeline)"
__init__.py  commun.py  evaluate.py  prepare.py  projet.py  suivi.py  train.py
```

**2. Dans un terminal de la VM** (pas celui de JupyterLab : il faut Docker), redémarrez JupyterLab et démarrez MLflow :

```bash title="Terminal de la VM"
cd ~/dataops-pipelines-tp
./scripts/demarrer.sh
docker compose up -d mlflow
docker compose ps
```

- `demarrer.sh` crée au besoin le dossier `.mlflow`, où le serveur rangera sa base. Si la configuration du service `jupyter` a changé depuis votre dernier démarrage, Docker Compose le **recrée** : c'est ainsi qu'il connaît l'adresse du serveur MLflow.
- `docker compose up -d mlflow` démarre le serveur MLflow. Il utilise **la même image** que JupyterLab : rien à télécharger.

**Vérification :** `docker compose ps` montre deux services à l'état `Up` (ou `running`) : `dataops-jupyter-1` sur le port 8888 et `dataops-mlflow-1` sur le port 5000.

**3. Rechargez JupyterLab** (touche **F5**) : le conteneur a été recréé, l'ancien terminal est fermé. Puis ouvrez **http://localhost:5000** dans un nouvel onglet du navigateur de la VM : c'est l'interface de MLflow. Elle est vide pour l'instant, à part une expérience nommée `Default`.

**4. Créez le notebook du matin** `j2-matin.ipynb` dans le dossier `notebooks`, et vérifiez que JupyterLab connaît l'adresse de MLflow :

```python title="Cellule 1 : l'adresse du serveur MLflow"
import os

print(os.environ["MLFLOW_TRACKING_URI"])
```

```plaintext title="Sortie attendue"
http://mlflow:5000
```

Depuis JupyterLab, le serveur s'appelle `mlflow` : c'est le nom du service dans `docker-compose.yml`. Depuis le navigateur de la VM, c'est `localhost:5000`. Même serveur, deux chemins pour y arriver.

::: hint
`KeyError: 'MLFLOW_TRACKING_URI'` : le conteneur JupyterLab n'a pas été recréé. Relancez `./scripts/demarrer.sh` dans le terminal de la VM, puis rechargez la page. `git pull` répond `Your local changes would be overwritten` : un fichier suivi par Git a été modifié ; `git status` le montre, `git stash` le met de côté le temps de la fusion. `fatal: invalid reference: tp-dvc` : vous n'avez pas fait le TP d'hier ; prévenez le formateur, qui vous donnera les commandes de rattrapage.
:::

::: solution Rattrapage : je n'ai pas la branche tp-dvc
Ces commandes refont, en une fois, l'essentiel du TP d'hier après-midi : identité Git, branche, DVC, stockage et première version des données.

```bash title="Terminal JupyterLab"
cd /home/lab/projet
git config --global user.name "Stagiaire DataOps"
git config --global user.email "stagiaire@colisvert.example"
git switch main
git pull --no-rebase --no-edit origin main
git switch -c tp-dvc
dvc init
dvc config core.analytics false
dvc remote add -d stockage ~/dvc-stockage
python -m colisvert.donnees data
dvc add data/livraisons.csv
git add .dvc .dvcignore data/livraisons.csv.dvc data/.gitignore
git commit -m "Rattrapage du jour 1 : DVC et données v1"
dvc push
```
:::
::::

::: callout info Et si ma VM a redémarré ?
Les deux services sont configurés pour redémarrer seuls avec Docker (`restart: unless-stopped`). Si http://localhost:5000 ne répond plus, `docker compose up -d mlflow`, depuis `~/dataops-pipelines-tp`, suffit.
:::
