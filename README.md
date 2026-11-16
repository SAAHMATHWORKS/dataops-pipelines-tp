# DataOps : concevoir et automatiser des pipelines résilients et scalables

Travaux pratiques de la formation DataOps animée par Thibaut SAAH.

Fil rouge : **ColisVert**, un transporteur fictif qui veut prédire ses retards de livraison.
Toutes les données sont générées par `colisvert/donnees.py` de façon déterministe :
chaque stagiaire obtient exactement les mêmes chiffres.

## Démarrer

Sur une machine Linux avec Docker et Docker Compose :

```bash
git clone https://github.com/SAAHMATHWORKS/dataops-pipelines-tp.git
cd dataops-pipelines-tp
./scripts/demarrer.sh
```

Puis ouvrez **http://localhost:8888** dans le navigateur de la machine.

`demarrer.sh` écrit un fichier `.env` avec votre UID et votre GID, pour que le conteneur
crée les fichiers à votre nom, puis lance JupyterLab. Le port n'est ouvert que sur la
machine elle-même (`127.0.0.1`) : JupyterLab ne demande donc pas de jeton.

## Contenu

| Dossier | Rôle |
|---|---|
| `colisvert/` | Le générateur des données du fil rouge (septembre-octobre, puis décembre) |
| `pipeline/` | Jour 2 : les étapes du pipeline (`prepare`, `train`, `evaluate`), le suivi MLflow et le point d'entrée du projet MLflow |
| `MLproject` | Jour 2 : la description du projet MLflow (`mlflow run .`) |
| `notebooks/` | Vos notebooks, un par demi-journée |
| `data/` | Les données générées (non versionnées par Git) |
| `docker/lab/` | L'image des TP : JupyterLab, Python 3.12, Java 17, Git et les bibliothèques |
| `scripts/` | `demarrer.sh` pour démarrer, `verifier-vm.sh` pour tester une machine |
| `verification/` | La vérification automatique des chiffres du support (GitHub Actions) |

## Jour 2 : le serveur MLflow

```bash
docker compose up -d mlflow
```

Puis ouvrez **http://localhost:5000**. Depuis JupyterLab, le serveur s'appelle `http://mlflow:5000`
(variable `MLFLOW_TRACKING_URI`, déjà réglée). Sa base et ses artefacts sont rangés dans `.mlflow/`.

## Récupérer son travail en fin de formation

Tout ce que vous créez est dans ce dossier, sur votre machine. Pour l'emporter :
`cd .. && tar czf dataops-mon-travail.tar.gz dataops-pipelines-tp`, puis téléchargez
l'archive, ou poussez le dossier vers votre propre dépôt Git.

## L'image des TP

L'image `ghcr.io/saahmathworks/dataops-lab:2026.12` est construite par GitHub Actions
(`.github/workflows/image.yml`) à chaque modification de `docker/lab/`. Pour la construire
soi-même : `docker compose build jupyter`.

## La vérification automatique

À chaque modification du code, GitHub Actions (`.github/workflows/verifier-pipeline.yml`) rejoue
les TP dans l'image, avec un vrai serveur MLflow : DVC, pipeline, projet MLflow, recherche
d'hyperparamètres. Le script `verification/verifier_pipeline.sh` échoue si un chiffre diffère
de celui du support.
