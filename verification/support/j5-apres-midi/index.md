{#retour time="13:30 – 13:33"}
## Retour sur le matin

**Ce matin**, ColisVert a gagné des règles pour durer : des rôles et une fiche du produit de données vérifiée par du code, une plateforme bronze, argent, or sur Delta Lake qui refuse les écritures fautives et sait revenir en arrière, et un modèle dont on sait expliquer chaque décision.

**Cet après-midi, les agents IA.** Toute la semaine, des encadrés « Et les agents IA ? » ont réservé une place : au jour 2, les traces MLflow ; au jour 4, un agent qui prépare l'analyse d'une alerte, et un rédacteur de SMS prêt pour un LLM ; ce matin, le RGPD. On tient ces rendez-vous :

- **comprendre :** chatbot, assistant et agent ; le LLM, cerveau des agents, ses forces et ses limites ;
- **pratiquer :** un TP avec le LLM de la formation, appelé depuis Python à travers la plateforme ;
- **encadrer :** les risques, la sécurité, la gouvernance, l'AI Act et le RGPD ;
- **voir :** une démonstration des agents de Microsoft Fabric ;
- **conclure :** l'évaluation, puis le bilan de la semaine.

{#mise-en-place time="13:33 – 13:40"}
## Mise en place

:::: lab Mise en place | Le dépôt, votre jeton et le notebook | 7 min
**1. Dans un terminal de JupyterLab**, récupérez les nouveautés du dépôt (le LLM simulé de l'étape 5) :

```bash title="Terminal JupyterLab"
cd /home/lab/projet
git switch tp-dvc
git pull --no-rebase --no-edit origin main
ls colisvert
```

```plaintext title="Sortie attendue (ls)"
__init__.py
donnees.py
llm_simule.py
```

**2. Dans un terminal de la VM**, vérifiez que JupyterLab et MLflow tournent :

```bash title="Terminal de la VM"
cd ~/dataops-pipelines-tp
docker compose up -d jupyter mlflow
docker compose ps
```

**3. Créez votre jeton LLM.** Dans Training Lab, ouvrez **Mon dashboard › Mon accès au LLM**, puis cliquez sur **Créer mon jeton**. Copiez-le : il ne sera plus jamais affiché. Avant de cliquer, **arrêtez le partage d'écran** si vous partagez le vôtre, et ne collez jamais le jeton dans le chat Teams.

**4. Créez le notebook** `j5-apres-midi.ipynb` dans le dossier `notebooks`. La première cellule prépare les données et le champion de ce matin, puis vous demande votre jeton. `getpass` le lit sans l'afficher : il ne sera écrit ni dans le notebook ni dans un fichier.

```python title="Cellule 0 : les données, le champion et la passerelle"
import getpass
import json
import os
import re

import pandas as pd
import requests
from colisvert.donnees import DOSSIER_DATA, generer_livraisons_decembre, preparer_donnees
from pipeline.commun import CATEGORIELLES, CIBLE, NUMERIQUES, ajouter_jour_semaine
from pipeline.train import construire_modele

preparer_donnees()
livraisons = ajouter_jour_semaine(pd.read_csv(DOSSIER_DATA / "livraisons.csv"))
decembre = ajouter_jour_semaine(pd.DataFrame(generer_livraisons_decembre()))
X_COLS = CATEGORIELLES + NUMERIQUES
train = livraisons[livraisons["date_expedition"] < "2026-10-19"]
champion = construire_modele(0.1, "balanced", 1000).fit(train[X_COLS], train[CIBLE])

# L'adresse de la passerelle ; la vérification automatique du cours la remplace par celle du LLM simulé.
PASSERELLE = os.environ.get("LLM_PASSERELLE", "https://m2i-training-lab.kbc-sarl.com/api/llm/v1")
JETON = os.environ.get("LLM_JETON") or getpass.getpass("Votre jeton LLM (il ne s'affiche pas) : ")
ENTETES = {"Authorization": f"Bearer {JETON}"}
quota = requests.get(f"{PASSERELLE}/quota", headers=ENTETES, timeout=30).json()
print(f"passerelle : modèle {quota['modele']}, {quota['appels_max_par_jour']} appels "
      f"et {quota['jetons_max_par_jour']} jetons par jour")
```

```plaintext title="Sortie attendue"
livraisons.csv : 5035 colis, dont 862 en retard
arrivees.csv : 56 jours
livraisons_brutes.csv : les mêmes colis, avec des défauts de qualité
passerelle : modèle gpt-6-luna, 150 appels et 300000 jetons par jour
```

::: hint
`KeyError: 'modele'` : la passerelle a refusé la demande. Affichez `quota` : le message dit pourquoi (`jeton_inconnu` : jeton mal collé, relancez la cellule ; `acces_ferme` : prévenez le formateur, l'accès au LLM n'est pas ouvert pour la session). `ConnectionError` : la VM n'atteint pas la plateforme ; vérifiez dans le navigateur de la VM que https://m2i-training-lab.kbc-sarl.com s'ouvre.
:::
::::
