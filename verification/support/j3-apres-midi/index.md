{#retour time="13:30 – 13:33"}
## Retour sur le matin

**Ce matin**, on a choisi des outils avec méthode : couches de l'écosystème, construire ou acheter, carte de Wardley, radar technologique. Le radar a placé **Airflow 3** dans l'anneau « Essayer », avec une mission : **un pilote sur le pipeline des retards**. On a aussi mesuré trois moteurs sur les 3 millions de courses de taxi de janvier 2024 : 2 318 848 courses valides selon le contrat de qualité.

**Cet après-midi, c'est le pilote.** Le pipeline du jour 2 tourne quand quelqu'un tape `dvc repro`. On va le confier à Airflow, le rendre robuste, puis le faire démarrer **quand les données arrivent**, plus à heure fixe. Les taxis reviennent pour apprendre à rattraper un mois entier.

{#demarrage time="13:33 – 13:40"}
## Démarrer Airflow

:::: lab Mise en place | Récupérer le code du jour et démarrer Airflow | 7 min
**1. Dans un terminal de JupyterLab**, récupérez les nouveautés du dépôt (le service Airflow, les scripts, les corrigés) :

```bash title="Terminal JupyterLab"
cd /home/lab/projet
git switch tp-dvc
git pull --no-rebase --no-edit origin main
ls dags solutions/airflow
```

```plaintext title="Sortie attendue (ls)"
dags:
README.md

solutions/airflow:
colisvert_fraicheur.py  taxis_journalier.py  tp1  tp2
```

**2. Dans un terminal de la VM** (il faut Docker), démarrez Airflow :

```bash title="Terminal de la VM"
cd ~/dataops-pipelines-tp
./scripts/demarrer.sh
docker compose up -d mlflow airflow
docker compose ps
```

- L'image d'Airflow (`dataops-lab:2026.12-airflow`) est construite **par-dessus** l'image des TP : Docker ne télécharge que la couche qui contient Airflow.
- Au premier démarrage, Airflow crée sa base dans `.airflow/` : comptez une à deux minutes avant que l'interface réponde.

**Vérification :** `docker compose ps` montre trois services `Up` : `jupyter` (8888), `mlflow` (5000) et `airflow` (8080). Puis :

```bash title="Terminal de la VM"
docker compose exec airflow airflow version
```

```plaintext title="Sortie attendue"
3.4.0
```

**3. Ouvrez http://localhost:8080** dans le navigateur de la VM. Pas d'identifiant à saisir : le port n'est ouvert que sur la VM elle-même. La liste des DAG est vide ; c'est normal, le dossier `dags/` ne contient encore que son `README.md`.

::: hint
`localhost:8080` ne répond pas : Airflow démarre encore ; `docker compose logs airflow --tail 20` montre où il en est. `Error response from daemon: … pull access denied` : la VM n'atteint pas `ghcr.io` ; prévenez le formateur. `git pull` répond `Your local changes would be overwritten` : `git stash`, puis relancez `git pull`, puis `git stash pop`.
:::
::::

::: callout info Les commandes d'Airflow
Airflow tourne dans son conteneur. Ses commandes se lancent donc depuis le terminal de la VM, précédées de `docker compose exec airflow` : « exécute, dans le service airflow, la commande… ». Les fichiers, eux, sont partagés : un DAG écrit dans `dags/` depuis JupyterLab est vu immédiatement par Airflow.
:::
