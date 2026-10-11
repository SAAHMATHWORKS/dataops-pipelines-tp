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
| `colisvert/` | Le générateur des données du fil rouge |
| `notebooks/` | Vos notebooks, un par demi-journée |
| `data/` | Les données générées (non versionnées par Git) |
| `docker/lab/` | L'image des TP : JupyterLab, Python 3.12, Java 17, Git et les bibliothèques |
| `scripts/` | `demarrer.sh` pour démarrer, `verifier-vm.sh` pour tester une machine |

## Récupérer son travail en fin de formation

Tout ce que vous créez est dans ce dossier, sur votre machine. Pour l'emporter :
`cd .. && tar czf dataops-mon-travail.tar.gz dataops-pipelines-tp`, puis téléchargez
l'archive, ou poussez le dossier vers votre propre dépôt Git.

## L'image des TP

L'image `ghcr.io/saahmathworks/dataops-lab:2026.12` est construite par GitHub Actions
(`.github/workflows/image.yml`) à chaque modification de `docker/lab/`. Pour la construire
soi-même : `docker compose build jupyter`.
