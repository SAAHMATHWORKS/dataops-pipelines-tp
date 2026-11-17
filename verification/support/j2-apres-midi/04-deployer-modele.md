---
subtitle: >-
  Un modèle dans un registre ne prévient encore aucun client. Le déployer, c'est le rendre
  utilisable par d'autres programmes : à la demande, colis par colis, ou par lots, chaque matin.
  Et c'est prévoir comment on le remplacera sans risque.
objectives:
  - Distinguer prédiction à la demande et prédiction par lots, et choisir selon le besoin
  - Servir le modèle champion comme une API avec mlflow models serve, et l'interroger
  - Appliquer le modèle à un lot de colis et résumer ses prédictions
  - Comparer quatre stratégies de mise en service et choisir celle qui limite le risque
---

{#pourquoi}
## Deux façons de servir un modèle

**L'analogie de la boulangerie, encore.** Le boulanger peut cuire **à la commande** (un client entre, il cuit son pain) ou **par fournées** (tout le pain du matin, cuit à 5 h). La commande demande un four toujours chaud et une réponse rapide ; la fournée est plus économique, mais on ne sert que ce qui a été prévu.

| | Prédiction **à la demande** (*online*) | Prédiction **par lots** (*batch*) |
|---|---|---|
| Comment | Un service web répond à chaque requête | Un traitement planifié prédit pour tout un fichier |
| Délai de réponse | Quelques millisecondes | Minutes ou heures, mais pour des milliers de lignes |
| Chez ColisVert | Le site affiche « risque de retard » quand le client suit son colis | Chaque matin à 7 h, les colis de la veille à risque déclenchent un SMS |
| Ce qu'il faut | Un serveur qui tourne en permanence, surveillé | Un orchestrateur (jour 3) et un stockage |

Les deux utilisent **le même modèle**, chargé depuis le registre par son alias `champion`.

{#servir}
## Servir le champion comme une API

`mlflow models serve` démarre un petit serveur web autour d'un modèle MLflow. Il expose notamment l'adresse `/invocations` : on lui envoie des colis au format JSON, il répond avec les prédictions.

:::: lab Démo | Un service de prédiction en une commande | 10 min
**1. Démarrez le service** dans un **deuxième** terminal de JupyterLab (**File › New › Terminal**). Il reste au premier plan : ce terminal est désormais occupé par le serveur.

```bash title="Terminal JupyterLab n° 2"
cd /home/lab/projet
mlflow models serve -m "models:/colisvert-retards@champion" -p 5001 --env-manager local
```

MLflow résout l'alias (la version 2), télécharge le modèle depuis le serveur de suivi (une barre `Downloading artifacts` : 7 fichiers), puis démarre le serveur web. **Vérification :** la dernière ligne est :

```plaintext title="Sortie attendue (dernière ligne)"
INFO:     Uvicorn running on http://127.0.0.1:5001 (Press CTRL+C to quit)
```

Uvicorn est le serveur web qui fait tourner l'application de MLflow.

**2. Interrogez-le depuis le notebook.** Le format `dataframe_split` décrit un tableau : la liste des colonnes, puis les lignes. `to_json(orient="split", index=False)` le produit directement à partir d'un tableau pandas.

```python title="Cellule 12 : interroger le service"
import json

import requests

colis = decembre.head(5)[X_COLS]
corps = {"dataframe_split": json.loads(colis.to_json(orient="split", index=False))}
reponse = requests.post("http://127.0.0.1:5001/invocations", json=corps, timeout=30)
print(reponse.status_code, reponse.json())
```

```plaintext title="Sortie attendue"
200 {'predictions': [1, 1, 1, 0, 0]}
```

Le code `200` signifie « succès ». Les prédictions sont celles de la Cellule 6 : **le service et le notebook utilisent le même modèle**, à l'octet près. N'importe quel programme (le site web de ColisVert, en Java ou en PHP) peut maintenant obtenir une prédiction avec une simple requête HTTP, sans rien connaître de Python ni de scikit-learn.

**3. Arrêtez le service** : dans le terminal n° 2, **Ctrl + C**.

::: hint
`ConnectionError` ou `Connection refused` : le service n'a pas fini de démarrer (attendez la ligne qui indique l'adresse d'écoute), ou il a été arrêté. Code `400` avec un message sur le schéma : une colonne manque ou n'a pas le bon type ; le modèle vérifie ses entrées d'après l'exemple enregistré avec lui.
:::
::::

::: callout warn Déplacer l'alias ne suffit pas à changer le modèle servi
Le service charge le modèle **une fois**, au démarrage. Si l'on déplace l'alias `champion` sur une autre version, le service en cours continue de servir l'ancienne : il faut le **redémarrer**. En production, c'est la chaîne de déploiement qui s'en charge, avec l'une des stratégies ci-dessous.
:::

{#lots}
## Prédire par lots

:::: lab Démo | Les colis de décembre | 5 min
Pour un lot, pas besoin de serveur : on charge le modèle et on prédit sur tout le tableau. `champion` est le modèle chargé par son alias à la Cellule 6.

```python title="Cellule 13 : le lot de décembre"
decembre["prediction"] = champion.predict(decembre[X_COLS])
print(f"{len(decembre)} colis de décembre, {decembre['prediction'].mean():.1%} prédits en retard")
print(decembre.groupby("entrepot")["prediction"].mean().round(3).to_string())
```

```plaintext title="Sortie attendue"
3426 colis de décembre, 36.6% prédits en retard
entrepot
Lille       0.519
Lyon        0.296
Nantes      0.314
Toulouse    0.303
```

**36,6 % de colis prédits en retard**, contre 26,5 % sur le test d'octobre. Le modèle annonce beaucoup plus de retards en décembre. Est-ce une bonne nouvelle (il voit venir une vague de retards) ou une mauvaise (il se trompe parce que décembre ne ressemble pas à ce qu'il a appris) ? On ne peut pas encore le savoir : les vrais délais de décembre ne seront connus qu'à la livraison. C'est exactement la question de la notion suivante.
::::

{#strategies}
## Mettre en service sans risque

Remplacer un modèle en production est un changement comme un autre : il peut mal tourner. Quatre stratégies, de la plus risquée à la plus prudente :

| Stratégie | Comment | Avantage | Inconvénient |
|---|---|---|---|
| **Remplacement direct** | On arrête l'ancien, on démarre le nouveau | Simple | Si le nouveau se trompe, tout le monde est touché |
| **Bleu-vert** (*blue-green*) | Les deux versions tournent ; on bascule tout le trafic d'un coup, et l'on peut rebasculer | Retour arrière instantané | Deux fois les ressources pendant la bascule |
| **Canari** (*canary*) | Le nouveau reçoit d'abord 5 % des requêtes, puis 25 %, puis tout, si les indicateurs restent bons | Peu de clients exposés à un problème | Il faut des indicateurs fiables, et du temps |
| **Ombre** (*shadow*) | Le nouveau reçoit **toutes** les requêtes, mais ses réponses ne sont pas utilisées : on les compare à celles de l'ancien | Aucun client exposé | Ne mesure pas l'effet réel sur les clients |

Pour ColisVert, une bonne séquence : quelques jours **en ombre** (comparer les alertes du challenger à celles du champion), puis un **canari** sur un entrepôt, puis la bascule. Le nom de l'oiseau vient des mines de charbon, où un canari prévenait les mineurs d'un gaz toxique avant qu'il ne les atteigne.

::: callout info Et dans Azure ou Fabric ?
**Azure Machine Learning** sait déployer un modèle MLflow **sans écrire de code de service** : on le déclare sur un point de terminaison en ligne managé (*managed online endpoint*), et Azure construit l'environnement d'après les fichiers enregistrés avec le modèle. Ces points de terminaison répartissent le trafic entre plusieurs déploiements : c'est le canari, intégré. Pour les lots, Azure ML propose des points de terminaison de traitement par lots. **Microsoft Fabric** applique un modèle MLflow enregistré à une table du Lakehouse avec sa fonction de prédiction par lots (`PREDICT`). Côté Google Cloud, Vertex AI sert les modèles sur des points de terminaison, avec un conteneur adapté.
:::

{#avance}
## Pour aller plus loin : ce que contient un modèle MLflow, et ce que doit surveiller son service

Ce bloc est pour les profils avancés ; rien ici n'est exigé dans l'évaluation.

**Le format MLflow Model.** Un modèle enregistré est un dossier : un fichier `MLmodel` qui décrit les **saveurs** (*flavors*) disponibles (`sklearn` pour le recharger tel quel, `python_function` pour l'interface commune `predict`), la **signature** (les colonnes et types attendus en entrée, et le type de sortie, déduits de l'exemple d'entrée), un exemple d'entrée, et les fichiers d'environnement (`requirements.txt`, `python_env.yaml`). Le service vérifie chaque requête contre la signature : une colonne manquante est refusée avec un message clair, au lieu de produire une prédiction absurde.

**Du service au conteneur.** `mlflow models build-docker -m "models:/colisvert-retards@champion" -n colisvert-api` construit une image Docker qui contient le modèle et son serveur : on la déploie ensuite sur n'importe quelle plateforme de conteneurs (Azure Container Apps, Kubernetes, Cloud Run). C'est la passerelle entre le monde du data scientist et celui de l'exploitation.

**Ce que le service doit journaliser.** Pour surveiller un modèle (notion suivante), il faut ses **entrées** et ses **sorties** : chaque requête, chaque prédiction, horodatées, plus tard rapprochées des vrais délais. Sans ce journal, on ne peut ni détecter la dérive ni mesurer la performance réelle. Penser au journal **dès le déploiement** est l'une des différences entre un prototype et un produit, avec deux précautions : n'y garder que les variables utiles, et respecter le RGPD si des données personnelles y transitent.

**Le service n'est pas le seul risque.** Un modèle peut être techniquement parfait et faire du tort : trop d'alertes fausses envoyées aux clients d'un seul entrepôt, par exemple (un colis sur deux prédit en retard à Lille en décembre). Les indicateurs d'un canari doivent donc inclure des indicateurs **métier** (taux d'alertes par entrepôt, réclamations), pas seulement le temps de réponse.

{#quiz}
## Quiz de validation

```quiz
- q: ColisVert envoie chaque matin à 7 h un SMS aux clients dont le colis de la veille risque d'être en retard. Quel mode de prédiction convient ?
  options: [À la demande, Par lots, Aucun des deux, Les deux obligatoirement]
  answer: 1
  explain: Un traitement planifié prédit pour tous les colis de la veille d'un coup.
- q: On déplace l'alias champion sur une nouvelle version. Que sert le service mlflow models serve déjà démarré ?
  options:
    - Immédiatement la nouvelle version
    - Toujours l'ancienne, jusqu'à son redémarrage
    - Plus rien, il s'arrête
    - Les deux versions à tour de rôle
  answer: 1
  explain: Le service charge le modèle une fois, au démarrage.
- q: Dans quelle stratégie le nouveau modèle reçoit-il toutes les requêtes sans que ses réponses soient utilisées ?
  options: [Remplacement direct, Bleu-vert, Canari, Ombre]
  answer: 3
  explain: En ombre, on compare ses réponses à celles du modèle en service, sans exposer de client.
- q: Pourquoi le service refuse-t-il une requête où manque la colonne meteo ?
  options:
    - Parce que la météo est une donnée personnelle
    - Parce que le modèle vérifie les entrées contre sa signature, enregistrée avec lui
    - Parce que requests ne sait pas envoyer de texte
    - Parce que le port 5001 est réservé
  answer: 1
  explain: La signature, déduite de l'exemple d'entrée, décrit les colonnes et types attendus.
```
