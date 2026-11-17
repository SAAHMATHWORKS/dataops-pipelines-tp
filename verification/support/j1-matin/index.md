{#positionnement time="09:00 – 09:15"}
## Accueil et positionnement

Tour de table rapide : présentez-vous en une phrase (votre métier, et ce que vous faites aujourd'hui avec des données). Puis remplissez ce questionnaire : il aide votre formateur à adapter le rythme, et l'assistant vous répond avec un message d'accueil personnalisé.

::: widget positioning
:::

## Comment utiliser ce support

- **Ouvrez ce support dans le navigateur de votre VM.** Le copier-coller entre votre poste et la VM ne fonctionne pas toujours : depuis la VM, chaque bloc de code se copie directement.
- **Une page par notion.** Chaque page se termine par un quiz de validation : visez un sans-faute avant de passer à la suite.
- **Copier plutôt que taper.** Chaque bloc de code a un bouton Copier.
- **Indices et corrections** s'affichent à la demande, sous chaque exercice. Cherchez d'abord.
- **Les blocs « Pour aller plus loin »** sont là pour les profils avancés et pour les 30 jours qui suivent la formation : ils ne sont jamais exigés dans les évaluations.
- **Mode présentation.** Le bouton « Présenter » affiche la page en diapositives, une section à la fois. Flèches du clavier pour naviguer, Échap pour quitter.

{#installation time="09:15 – 09:30"}
## Installer l'environnement de la semaine

**Pourquoi ?** Pendant cinq jours, chacun va utiliser les mêmes outils, dans les mêmes versions, sur les mêmes données. Pour cela, tout tourne dans des **conteneurs Docker**. Un conteneur est comme une **boîte de déménagement étiquetée** : on y range un programme avec tout ce dont il a besoin (Python, bibliothèques, réglages). La boîte s'ouvre de la même façon sur n'importe quelle machine.

Ce matin, une seule boîte suffit : **JupyterLab**, pour écrire et exécuter du Python. MLflow s'ajoutera au jour 2 et Airflow au jour 3.

:::: lab Mise en place | Récupérer le dépôt et démarrer JupyterLab | 10 min
**1. Ouvrez un terminal sur votre VM** et vérifiez les outils. Chaque commande doit afficher un numéro de version.

```bash title="Terminal"
git --version
docker --version
docker compose version
```

**2. Récupérez le dépôt des TP.** `git clone` copie le dépôt GitHub dans un dossier `dataops-pipelines-tp` de votre dossier personnel.

```bash title="Terminal"
cd ~
git clone https://github.com/SAAHMATHWORKS/dataops-pipelines-tp.git
cd dataops-pipelines-tp
ls
```

**Vérification :** `ls` affiche `README.md`, `colisvert`, `docker`, `docker-compose.yml`, `notebooks` et `scripts`.

**3. Démarrez l'environnement.**

```bash title="Terminal · ~/dataops-pipelines-tp"
./scripts/demarrer.sh
```

Le premier démarrage télécharge l'image des TP : comptez quelques minutes. Pendant ce temps, on passe à la suite.

**Vérification :** la dernière ligne affichée est :

```plaintext title="Sortie attendue (dernière ligne)"
JupyterLab est prêt : http://localhost:8888
```

**4. Ouvrez http://localhost:8888** dans le navigateur de la VM. Dans le panneau de gauche, double-cliquez sur le dossier `notebooks`, puis créez un notebook (**File › New › Notebook**, noyau **Python 3**). Renommez-le `j1-matin.ipynb` (clic droit sur l'onglet › **Rename**).

::: hint
`permission denied` en lançant le script : tapez `bash scripts/demarrer.sh`. `Cannot connect to the Docker daemon` : Docker n'est pas démarré, ou votre utilisateur n'a pas le droit de l'utiliser ; prévenez le formateur. `port is already allocated` : un autre programme utilise le port 8888 ; `docker ps` montre lequel. Le script attend 60 secondes, puis affiche une erreur si JupyterLab ne répond pas : `docker compose logs jupyter` montre pourquoi.
:::

::: solution Que fait demarrer.sh, ligne par ligne ?
```bash title="scripts/demarrer.sh (l'essentiel)"
./scripts/identite.sh
mkdir -p .home .mlflow .airflow data notebooks
docker compose up -d jupyter
```

1. **`identite.sh`** écrit votre numéro d'utilisateur (UID) et de groupe (GID) dans un fichier `.env`. Docker Compose lit ce fichier et lance le conteneur **avec votre identité**. Sans cela, le conteneur utiliserait un autre numéro et ne pourrait pas écrire dans votre dossier : c'est exactement le problème rencontré sur ces VM, où l'utilisateur a l'UID 1001. Le script écrit aussi, dans `.home`, un petit fichier d'utilisateurs qui donne un **nom** (`lab`) à ce numéro dans le conteneur : certains outils de la semaine (DVC, Airflow, et Java, donc Spark) refusent de travailler pour un numéro sans nom.
2. **`mkdir -p`** crée les dossiers de travail s'ils n'existent pas : `.home` (le dossier personnel du conteneur, pour la configuration de Git), `.mlflow` et `.airflow` (les bases des jours 2 et 3), `data` (les données générées) et `notebooks` (vos notebooks).
3. **`docker compose up -d jupyter`** lit `docker-compose.yml`, télécharge l'image si elle manque, puis démarre le service `jupyter` en arrière-plan (`-d`, pour *detached*).

Le dossier du dépôt est **monté** dans le conteneur : vos notebooks restent sur la VM, même si le conteneur est supprimé. Le port 8888 n'est ouvert que sur la VM elle-même (`127.0.0.1`), c'est pourquoi JupyterLab ne demande pas de mot de passe.
:::
::::

::: callout tip Récupérer son travail en fin de formation
Tout ce que vous créez cette semaine reste dans `~/dataops-pipelines-tp`, sur votre VM. Le dernier jour, on verra comment l'emporter en une commande.
:::
