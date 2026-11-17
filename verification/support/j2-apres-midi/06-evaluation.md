---
subtitle: >-
  Un collègue propose un nouveau réglage. Vous le cherchez proprement sur la semaine de validation,
  vous l'enregistrez comme candidat, vous appliquez la règle de promotion sans tricher, puis vous
  mesurez la dérive que le modèle en service va affronter en décembre.
objectives:
  - Mener une recherche d'hyperparamètres sur un jeu de validation temporel
  - Enregistrer un modèle candidat dans MLflow et dans le registre, avec un alias
  - Appliquer une règle de promotion écrite à l'avance
  - Mesurer la dérive des données et des prédictions entre deux périodes
# Barème : 14 points pour les étapes (indiqués sur chaque étape) + 6 points pour le QCM
quiz_points: 6
---

{#consignes}
## Consignes

**Scénario.** Une collègue pense qu'un `C` plus grand, avec `class_weight="balanced"`, ferait mieux que le champion actuel (la version 2, `C=0.1`). Vous testez son idée selon les règles de l'équipe : choix sur la semaine de validation, mesure unique sur le test, règle de promotion écrite à l'avance. Puis vous préparez la surveillance de décembre.

- **Durée :** 30 minutes, en autonomie. Le formateur passe voir chacun.
- **Où :** toutes les étapes dans un notebook neuf `j2-apres-midi-evaluation.ipynb` (dossier `notebooks`). Le serveur MLflow doit tourner, et le registre doit contenir les versions 1 et 2 de l'après-midi.
- **Validation :** chaque étape se termine par une **preuve** : collez la sortie demandée et cliquez sur « Envoyer ma preuve ».
- **Barème :** 14 points pour les 4 étapes, 6 points pour le QCM final (une seule tentative par question).
- Les corrections sont là si vous bloquez, mais essayez d'abord.

::: widget task-progress
:::

{#rechercher}
## Rechercher

:::: task Étape 1 | Trois valeurs de C, choisies sur la validation | 8 min | 4 pts
Dans la première cellule :

1. préparez les données et les jeux `train` (avant le 19 octobre) et `test`, puis, dans le train, `entrainement` (avant le 12 octobre) et `validation` (à partir du 12 octobre) ;
2. pour `C` = 0,03, 0,3 et 3,0, avec `class_weight="balanced"`, entraînez sur `entrainement` et affichez le F1 sur `validation`, arrondi à 3 décimales ;
3. gardez le `C` au meilleur F1 de validation, réentraînez-le sur tout le `train`, et affichez sa précision, son rappel et son F1 sur le `test`.

::: proof Collez la sortie complète de votre cellule
:::

::: hint
C'est la fonction `score` de la Cellule 7 du TP, avec une liste de trois valeurs. `max(resultats, key=lambda essai: essai[1])` renvoie le couple `(C, f1)` au meilleur F1.
:::

::: solution
```python title="Évaluation · Cellule 1"
import pandas as pd
from sklearn.metrics import f1_score, precision_score, recall_score

from colisvert.donnees import DOSSIER_DATA, preparer_donnees
from pipeline.commun import CATEGORIELLES, CIBLE, NUMERIQUES, ajouter_jour_semaine
from pipeline.train import construire_modele

preparer_donnees()
livraisons = ajouter_jour_semaine(pd.read_csv(DOSSIER_DATA / "livraisons.csv"))
X_COLS = CATEGORIELLES + NUMERIQUES
train = livraisons[livraisons["date_expedition"] < "2026-10-19"]
test = livraisons[livraisons["date_expedition"] >= "2026-10-19"]
entrainement = train[train["date_expedition"] < "2026-10-12"]
validation = train[train["date_expedition"] >= "2026-10-12"]

resultats = []
for C in [0.03, 0.3, 3.0]:
    modele = construire_modele(C, "balanced", 1000).fit(entrainement[X_COLS], entrainement[CIBLE])
    f1 = round(f1_score(validation[CIBLE], modele.predict(validation[X_COLS])), 3)
    resultats.append((C, f1))
    print(f"C={C} : F1 de validation {f1}")

meilleur_C = max(resultats, key=lambda essai: essai[1])[0]
candidat = construire_modele(meilleur_C, "balanced", 1000).fit(train[X_COLS], train[CIBLE])
predictions = candidat.predict(test[X_COLS])
metriques = {
    "precision": round(precision_score(test[CIBLE], predictions), 3),
    "rappel": round(recall_score(test[CIBLE], predictions), 3),
    "f1": round(f1_score(test[CIBLE], predictions), 3),
}
print(f"retenu : C={meilleur_C} | test : {metriques}")
```

```plaintext title="Sortie attendue"
livraisons.csv : 5035 colis, dont 862 en retard
arrivees.csv : 56 jours
livraisons_brutes.csv : les mêmes colis, avec des défauts de qualité
C=0.03 : F1 de validation 0.594
C=0.3 : F1 de validation 0.619
C=3.0 : F1 de validation 0.632
retenu : C=3.0 | test : {'precision': 0.574, 'rappel': 0.875, 'f1': 0.693}
```

Le réglage de la collègue, `C=3.0`, gagne sur la validation. Sur le test, il atteint le critère de succès (rappel 0,875, précision 0,574) avec un F1 de 0,693.
:::
::::

{#enregistrer}
## Enregistrer

:::: task Étape 2 | Le candidat dans MLflow et dans le registre | 7 min | 4 pts
Dans une nouvelle cellule :

1. dans l'expérience `colisvert-retards`, ouvrez un run nommé `candidat-C3` ; notez-y les paramètres `C` et `class_weight`, les trois métriques de l'étape 1, et le modèle `candidat` sous le nom `model` ;
2. enregistrez ce modèle dans le registre `colisvert-retards` et posez-lui l'alias `challenger` ;
3. affichez chaque version du registre avec ses alias, de la plus ancienne à la plus récente.

::: proof Collez la sortie complète de votre cellule
:::

::: hint
Dans le bloc `with mlflow.start_run(run_name="candidat-C3") as run:`, `run.info.run_id` donne l'identifiant du run, utile pour l'adresse `runs:/<id>/model`. Pour lister les versions : `client.search_model_versions("name = 'colisvert-retards'")`, puis `client.get_model_version(nom, numero).aliases` pour chacune.
:::

::: solution
```python title="Évaluation · Cellule 2"
import mlflow
from mlflow import MlflowClient
from mlflow import sklearn as mlflow_sklearn

client = MlflowClient()
NOM = "colisvert-retards"

mlflow.set_experiment("colisvert-retards")
with mlflow.start_run(run_name="candidat-C3") as run:
    mlflow.log_params({"C": meilleur_C, "class_weight": "balanced"})
    mlflow.log_metrics(metriques)
    mlflow_sklearn.log_model(candidat, name="model", input_example=train[X_COLS].head(2))

version_3 = mlflow.register_model(f"runs:/{run.info.run_id}/model", NOM)
client.set_registered_model_alias(NOM, "challenger", version_3.version)

numeros = sorted(int(v.version) for v in client.search_model_versions(f"name = '{NOM}'"))
for numero in numeros:
    print(f"v{numero} : {sorted(client.get_model_version(NOM, str(numero)).aliases)}")
```

```plaintext title="Sortie attendue"
🏃 View run candidat-C3 at: http://mlflow:5000/#/experiments/2/runs/<id>
🧪 View experiment at: http://mlflow:5000/#/experiments/2
v1 : ['precedent']
v2 : ['champion']
v3 : ['challenger']
```

Si vous avez exécuté des cellules plusieurs fois pendant l'après-midi, vous aurez des versions en plus : seul compte que la dernière porte `challenger`, et que `champion` reste sur la version issue du run `C=0.1`.
:::
::::

{#decider}
## Décider

:::: task Étape 3 | Appliquer la règle de promotion | 7 min | 3 pts
La règle de l'équipe (notion 2) : **un challenger remplace le champion s'il atteint le critère de succès (rappel ≥ 0,80 et précision ≥ 0,50) et si son F1 dépasse celui du champion d'au moins 0,01.**

Dans une nouvelle cellule :

1. lisez, dans leurs runs, les métriques des versions qui portent les alias `champion` et `challenger`, et affichez-les ;
2. écrivez une fonction `promouvoir(challenger, champion)` qui applique la règle à deux dictionnaires de métriques, et affichez sa réponse avec l'écart de F1, arrondi à 3 décimales ;
3. si la réponse est oui, déplacez l'alias `champion` ; dans tous les cas, affichez la version qui porte `champion` après la décision.

::: proof Collez la sortie complète de votre cellule
:::

::: hint
`client.get_model_version_by_alias(NOM, "champion")` renvoie la version ; son `run_id` mène au run, et `client.get_run(run_id).data.metrics` au dictionnaire des métriques.
:::

::: solution
```python title="Évaluation · Cellule 3"
def metriques_de(alias):
    version = client.get_model_version_by_alias(NOM, alias)
    return version.version, client.get_run(version.run_id).data.metrics


def promouvoir(challenger, champion):
    """La règle de l'équipe : critère de succès atteint et F1 supérieur d'au moins 0,01."""
    critere = challenger["rappel"] >= 0.80 and challenger["precision"] >= 0.50
    return critere and challenger["f1"] >= champion["f1"] + 0.01


numero_champion, champion = metriques_de("champion")
numero_challenger, challenger = metriques_de("challenger")
for alias, numero, m in [("champion", numero_champion, champion), ("challenger", numero_challenger, challenger)]:
    print(f"{alias:<10} v{numero} : f1 {m['f1']}, rappel {m['rappel']}, précision {m['precision']}")

decision = promouvoir(challenger, champion)
print(f"promotion : {decision} (écart de F1 : {round(challenger['f1'] - champion['f1'], 3)})")
if decision:
    client.set_registered_model_alias(NOM, "champion", numero_challenger)
print("champion après décision : v" + client.get_model_version_by_alias(NOM, "champion").version)
```

```plaintext title="Sortie attendue"
champion   v2 : f1 0.685, rappel 0.88, précision 0.561
challenger v3 : f1 0.693, rappel 0.875, précision 0.574
promotion : False (écart de F1 : 0.008)
champion après décision : v2
```

**Le challenger est meilleur, mais pas assez.** Il atteint le critère, mais son F1 ne dépasse celui du champion que de 0,008, moins que la marge de 0,01. Sur 1 230 colis de test, une telle différence peut s'inverser la semaine suivante : la règle évite de changer de modèle en production pour du bruit. Le champion reste la version 2. La version 3 reste dans le registre, avec son alias `challenger`, si de nouvelles données venaient à la départager.
:::
::::

{#surveiller}
## Surveiller

:::: task Étape 4 | La dérive entre octobre et décembre | 8 min | 3 pts
Le modèle en service va affronter décembre. Prenez cette fois **le test d'octobre comme référence** (la dernière période où le modèle a été mesuré). Dans une nouvelle cellule :

1. chargez les colis de décembre (`generer_livraisons_decembre`, puis `ajouter_jour_semaine`) ;
2. calculez la distance de Jensen-Shannon de `meteo` et la distance de Wasserstein normalisée de `poids_kg` entre le test d'octobre et décembre, arrondies à 3 décimales, avec leur verdict au seuil de 0,1 ;
3. chargez le champion par son alias, et affichez la part de colis qu'il prédit en retard en octobre (test) et en décembre.

::: proof Collez la sortie complète de votre cellule
:::

::: hint
Recopiez `distance_categorielle` et `distance_numerique` de la Cellule 15 de l'après-midi. Le champion : `mlflow.pyfunc.load_model("models:/colisvert-retards@champion")`. La part prédite en retard est la moyenne des prédictions (des 0 et des 1).
:::

::: solution
```python title="Évaluation · Cellule 4"
import numpy as np
from scipy.spatial.distance import jensenshannon
from scipy.stats import wasserstein_distance

from colisvert.donnees import generer_livraisons_decembre


def distance_categorielle(ref, cur):
    valeurs = sorted(set(ref) | set(cur))
    return jensenshannon([(ref == v).mean() for v in valeurs], [(cur == v).mean() for v in valeurs])


def distance_numerique(ref, cur):
    return wasserstein_distance(ref, cur) / np.std(ref)


decembre = ajouter_jour_semaine(pd.DataFrame(generer_livraisons_decembre()))
for colonne, mesure in [("meteo", distance_categorielle), ("poids_kg", distance_numerique)]:
    d = round(mesure(test[colonne], decembre[colonne]), 3)
    print(f"{colonne} : {d} -> {'dérive' if d >= 0.1 else 'stable'}")

modele_en_service = mlflow.pyfunc.load_model(f"models:/{NOM}@champion")
for nom, donnees in [("octobre", test), ("décembre", decembre)]:
    print(f"prédits en retard en {nom} : {modele_en_service.predict(donnees[X_COLS]).mean():.1%}")
```

```plaintext title="Sortie attendue"
meteo : 0.147 -> dérive
poids_kg : 0.534 -> dérive
prédits en retard en octobre : 26.5%
prédits en retard en décembre : 36.6%
```

Les deux variables dérivent aussi par rapport au test d'octobre, et les **prédictions** dérivent avec elles : de 26,5 % à 36,6 % de colis signalés. Ce sont les deux signaux qu'on peut lire **dès le premier jour de décembre**, sans attendre les livraisons. La conduite à tenir : enquêter, prévenir le service client que le volume d'alertes va augmenter, et mesurer la performance dès que les vrais délais arrivent.
:::
::::

{#quiz}
## Quiz : vos résultats

Répondez à partir de l'après-midi et de ce que vous venez de faire. **Une seule tentative par question** : votre première réponse est enregistrée et compte pour la note.

```quiz
- q: Sur quel jeu avez-vous choisi la valeur de C à l'étape 1 ?
  options: [Le test, La semaine de validation, Le train complet, Les colis de décembre]
  answer: 1
  explain: Le test n'a servi qu'une fois, pour mesurer le réglage retenu.
- q: Pourquoi le challenger (F1 0,693) n'a-t-il pas remplacé le champion (F1 0,685) ?
  options:
    - Parce qu'il n'atteint pas le critère de succès
    - Parce que l'écart de F1 (0,008) est inférieur à la marge de 0,01 fixée par la règle
    - Parce que MLflow interdit d'avoir trois versions
    - Parce que son rappel est plus faible
  answer: 1
  explain: La règle, écrite avant de voir les chiffres, évite de changer de modèle pour du bruit.
- q: Que charge mlflow.pyfunc.load_model("models:/colisvert-retards@champion") après votre décision ?
  options: [La version 1, La version 2, La version 3, La dernière version créée]
  answer: 1
  explain: L'alias champion n'a pas bougé - il désigne toujours la version 2.
- q: Quel est l'intérêt d'avoir enregistré la version 3 si elle n'est pas promue ?
  options:
    - Aucun, il aurait fallu la supprimer
    - Elle reste disponible et traçable, avec son run, si de nouvelles données venaient à la départager
    - Elle remplace automatiquement le champion la semaine suivante
    - Elle libère de l'espace dans le registre
  answer: 1
  explain: Le registre garde l'historique des candidats ; l'alias challenger dit lequel est en attente.
- q: La part de colis prédits en retard passe de 26,5 % à 36,6 %. Comment appelle-t-on ce signal ?
  options: [Une dérive du concept, Une dérive des prédictions, Une fuite de données, Un surapprentissage]
  answer: 1
  explain: Elle se lit sans étiquettes, dès les premiers jours de décembre.
- q: Quelle commande démarre un service web autour du modèle champion ?
  options:
    - mlflow run . -P C=0.1
    - mlflow models serve -m "models:/colisvert-retards@champion" -p 5001
    - dvc repro
    - mlflow server --port 5001
  answer: 1
  explain: mlflow run lance un projet, mlflow server démarre le serveur de suivi, dvc repro le pipeline.
```
