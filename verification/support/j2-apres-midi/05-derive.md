---
subtitle: >-
  Un modèle apprend le monde tel qu'il était. Quand le monde change, ses entrées ne ressemblent plus
  à ce qu'il a vu, et ses réponses peuvent se dégrader sans la moindre erreur technique. Détecter
  cette dérive tôt, la mesurer variable par variable, puis l'interpréter : c'est la surveillance d'un modèle.
objectives:
  - Distinguer dérive des données, dérive de la cible, dérive du concept et dérive des prédictions
  - Mesurer la dérive de chaque variable avec une distance adaptée à son type
  - Produire un rapport de dérive avec Evidently et le ranger dans MLflow
  - Interpréter une alerte de dérive et décider de la suite, avant et après l'arrivée des étiquettes
---

{#pourquoi}
## Pourquoi un modèle se dégrade-t-il ?

**L'analogie du GPS.** Un GPS calcule les temps de trajet à partir de ce qu'il a observé. Le jour où une nouvelle zone piétonne ferme une rue, il continue de proposer l'ancien itinéraire, avec assurance. Il n'a pas « planté » : le monde a changé, pas lui.

Chez ColisVert, le modèle a appris sur les colis de septembre et d'octobre. En décembre arrivent les fêtes : des colis plus lourds (des cadeaux), plus de pluie. Le modèle reçoit des colis qui **ne ressemblent pas** à ceux qu'il a appris. C'est la **dérive** (*drift*). On l'a vu au jour 1 : c'est le risque propre au MLOps, celui d'un modèle qui se dégrade **en silence**.

{#quatre-derives}
## Quatre dérives à ne pas confondre

Notons `X` les variables d'entrée (entrepôt, météo, poids…) et `y` la cible (en retard ou non).

| Dérive | Ce qui change | Exemple chez ColisVert | Se voit-elle sans attendre les étiquettes ? |
|---|---|---|---|
| **Des données** (*data drift*), variable par variable : **dérive des variables** (*feature drift*) | La distribution des entrées `X` | Plus de pluie, des colis plus lourds | **Oui** : on compare les entrées |
| **De la cible** (*label drift*) | La part de chaque classe de `y` | Le taux de retard passe de 17 % à 24 % | Non : il faut les vrais délais |
| **Du concept** (*concept drift*) | La **relation** entre `X` et `y` | Un nouveau sous-traitant à Lille : à conditions égales, plus de retards | Non : il faut les vrais délais |
| **Des prédictions** (*prediction drift*) | La distribution des réponses du modèle | 36,6 % de colis prédits en retard au lieu de 26,5 % | **Oui** : on compare les prédictions |

La dérive du concept est la plus dangereuse : les entrées peuvent ne pas bouger du tout, alors que le modèle se trompe de plus en plus. Mais elle ne se voit qu'avec les étiquettes, qui arrivent **en retard** (ici, à la livraison). C'est pourquoi on surveille d'abord ce qui se voit tout de suite : les **données** et les **prédictions**, comme signaux d'alerte précoces.

{#a-la-main}
## Mesurer à la main

:::: lab Démo | Octobre et décembre, côte à côte | 5 min
La **référence** est ce que le modèle a appris : le train, du 7 septembre au 18 octobre. On la compare au test d'octobre (le modèle y fonctionnait) et à décembre.

```python title="Cellule 14 : trois périodes, trois portraits"
reference = train
for nom, donnees in [("référence (train)", reference), ("test d'octobre", test), ("décembre", decembre)]:
    print(f"{nom:<18} : {len(donnees)} colis | pluie {(donnees['meteo'] == 'pluie').mean():.1%} | "
          f"poids moyen {donnees['poids_kg'].mean():.1f} kg | distance moyenne {donnees['distance_km'].mean():.0f} km")
```

```plaintext title="Sortie attendue"
référence (train)  : 3805 colis | pluie 28.9% | poids moyen 15.3 kg | distance moyenne 152 km
test d'octobre     : 1230 colis | pluie 29.1% | poids moyen 15.0 kg | distance moyenne 151 km
décembre           : 3426 colis | pluie 49.3% | poids moyen 19.7 kg | distance moyenne 153 km
```

Le test d'octobre ressemble à la référence. Décembre, non : **la pluie passe de 29 % à 49 % des colis, le poids moyen de 15,3 à 19,7 kg**. La distance, elle, ne bouge pas.
::::

Comparer des moyennes à l'œil marche pour trois variables. Pour huit variables, chaque jour, il faut **un nombre par variable et un seuil**. Deux distances, selon le type de variable :

- **Variable catégorielle** (entrepôt, météo…) : la **distance de Jensen-Shannon** compare les proportions de chaque valeur. Elle vaut 0 si les proportions sont identiques, et au plus 1 (avec le logarithme naturel, au plus 0,83).
- **Variable numérique** (distance, poids) : la **distance de Wasserstein**, divisée par l'écart-type de la référence. Intuitivement : le chemin moyen qu'il faut faire parcourir aux valeurs de la référence pour obtenir la nouvelle distribution, mesuré en écarts-types. D'où son autre nom, « distance du terrassier » (*earth mover's distance*) : la quantité de terre à déplacer pour transformer un tas en un autre.

Le seuil habituel est **0,1** pour les deux : au-delà, on considère que la variable a dérivé. Ce sont les choix par défaut d'Evidently quand la référence dépasse 1 000 lignes.

:::: lab Démo | Une distance par variable | 7 min
```python title="Cellule 15 : la dérive de chaque variable"
import numpy as np
from scipy.spatial.distance import jensenshannon
from scipy.stats import wasserstein_distance


def distance_categorielle(ref, cur):
    """Distance de Jensen-Shannon entre les proportions de chaque valeur."""
    valeurs = sorted(set(ref) | set(cur))
    return jensenshannon([(ref == v).mean() for v in valeurs], [(cur == v).mean() for v in valeurs])


def distance_numerique(ref, cur):
    """Distance de Wasserstein, en écarts-types de la référence."""
    return wasserstein_distance(ref, cur) / np.std(ref)


CONTINUES = ["distance_km", "poids_kg"]
for colonne in X_COLS:
    mesure = distance_numerique if colonne in CONTINUES else distance_categorielle
    d = mesure(reference[colonne], decembre[colonne])
    print(f"{colonne:<15} {mesure.__name__:<22} {d:.3f}  {'DÉRIVE' if d >= 0.1 else ''}")
```

```plaintext title="Sortie attendue"
entrepot        distance_categorielle  0.020
client          distance_categorielle  0.003
creneau         distance_categorielle  0.008
meteo           distance_categorielle  0.148  DÉRIVE
jour_semaine    distance_categorielle  0.029
distance_km     distance_numerique     0.023
poids_kg        distance_numerique     0.515  DÉRIVE
delai_promis_h  distance_categorielle  0.001
```

**Deux variables sur huit dérivent : `meteo` et `poids_kg`.** Le poids dérive fortement (0,515 écart-type de déplacement moyen). `delai_promis_h` est numérique, mais ne prend que deux valeurs (24 ou 48 heures) : on le traite comme une catégorie, comme le fait Evidently pour les variables numériques à très peu de valeurs distinctes.
::::

{#evidently}
## Le rapport Evidently

**Evidently** est une bibliothèque libre de surveillance des modèles. Elle fait les calculs précédents pour toutes les colonnes, choisit la méthode selon le type et la taille des données, et produit un **rapport HTML** interactif, lisible par toute l'équipe.

:::: lab Démo | Un rapport de dérive, rangé dans MLflow | 10 min
Dans Evidently, on décrit d'abord les colonnes (`DataDefinition`), on enveloppe chaque tableau dans un `Dataset`, puis on lance un `Report` avec le préréglage `DataDriftPreset`, qui mesure la dérive de chaque colonne et de l'ensemble. `run` renvoie le résultat (un *Snapshot*) : on le lit, on l'enregistre en HTML, et on le range dans MLflow avec la part de colonnes en dérive comme métrique.

```python title="Cellule 16 : le rapport Evidently"
from pathlib import Path

import mlflow
from evidently import DataDefinition, Dataset, Report
from evidently.presets import DataDriftPreset

definition = DataDefinition(numerical_columns=NUMERIQUES, categorical_columns=CATEGORIELLES)
ref = Dataset.from_pandas(reference[X_COLS], data_definition=definition)
cur = Dataset.from_pandas(decembre[X_COLS], data_definition=definition)
resultat = Report([DataDriftPreset()]).run(current_data=cur, reference_data=ref)

for metrique in resultat.dict()["metrics"]:
    config, valeur = metrique["config"], metrique["value"]
    if "column" in config:
        print(f"{config['column']:<15} {config['method']:<30} {valeur:.3f}")
    else:
        part_en_derive = valeur["share"]
        print(f"colonnes en dérive : {valeur['count']:.0f} sur {len(X_COLS)}, soit {part_en_derive:.0%}")

Path("/home/lab/projet/rapports").mkdir(exist_ok=True)
fichier = "/home/lab/projet/rapports/derive-decembre.html"
resultat.save_html(fichier)
mlflow.set_experiment("colisvert-surveillance")
with mlflow.start_run(run_name="derive-decembre"):
    mlflow.log_metric("part_colonnes_en_derive", part_en_derive)
    mlflow.log_artifact(fichier)
```

```plaintext title="Sortie attendue"
colonnes en dérive : 2 sur 8, soit 25%
distance_km     Wasserstein distance (normed)  0.023
poids_kg        Wasserstein distance (normed)  0.515
delai_promis_h  Jensen-Shannon distance        0.001
entrepot        Jensen-Shannon distance        0.020
client          Jensen-Shannon distance        0.003
creneau         Jensen-Shannon distance        0.008
meteo           Jensen-Shannon distance        0.148
jour_semaine    Jensen-Shannon distance        0.029
🏃 View run derive-decembre at: http://mlflow:5000/#/experiments/4/runs/<id>
🧪 View experiment at: http://mlflow:5000/#/experiments/4
```

`resultat.dict()` renvoie le rapport sous forme de dictionnaire : une liste de métriques, chacune avec sa configuration (`config` : la colonne, la méthode, le seuil) et sa valeur (`value`). La première, `DriftedColumnsCount`, compte les colonnes en dérive ; les suivantes, `ValueDrift`, donnent la distance de chaque colonne.

**Evidently retrouve exactement les distances calculées à la main**, avec les mêmes méthodes : Wasserstein normalisée pour la distance et le poids, Jensen-Shannon pour les catégories, et aussi pour `delai_promis_h`, numérique mais à deux valeurs seulement. 2 colonnes sur 8 dérivent, soit 25 % : sous le seuil de 50 % (`drift_share`), Evidently ne déclare pas une dérive **du jeu entier**, mais signale bien les deux colonnes.

**Vérification :** dans le panneau de gauche de JupyterLab, ouvrez `rapports/derive-decembre.html` (clic droit › **Open in New Browser Tab**). Le rapport montre, pour chaque colonne, la méthode utilisée, la distance, le verdict et les deux distributions superposées. Le même fichier est rangé comme artefact du run `derive-decembre`, dans l'expérience `colisvert-surveillance` de MLflow : l'historique des rapports se construit run après run.

::: hint
`ModuleNotFoundError: No module named 'evidently'` : vous utilisez un ancien conteneur ; relancez `./scripts/demarrer.sh` dans le terminal de la VM. Le rapport s'affiche vide dans l'onglet JupyterLab : le visualiseur bloque les scripts du fichier ; ouvrez-le dans un nouvel onglet du navigateur, ou cliquez sur **Trust HTML**.
:::
::::

{#interpreter}
## Interpréter l'alerte

La dérive est détectée. Que faire ? **Une alerte de dérive déclenche une enquête, pas automatiquement un réentraînement.** Trois questions, dans l'ordre :

1. **Est-ce un problème de données ?** Une variable qui dérive brutalement est souvent un **bug** : un capteur en panne, une unité changée (des grammes au lieu de kilos), un champ vide rempli par une valeur par défaut. Ici, non : les cadeaux de Noël sont plus lourds et décembre est pluvieux. La dérive est **réelle**.
2. **Le modèle sait-il extrapoler ?** Les colis de 30,5 à 38,4 kg n'existaient pas dans la référence. Une régression logistique prolonge la tendance apprise (plus lourd, plus de risque) ; un modèle à base d'arbres, lui, plafonnerait à la valeur du plus gros colis vu.
3. **La performance a-t-elle baissé ?** On ne le sait qu'avec les étiquettes. Fin décembre, les vrais délais sont connus : on mesure.

:::: lab Démo | Les étiquettes arrivent | 5 min
```python title="Cellule 17 : le champion, en octobre puis en décembre"
from sklearn.metrics import precision_score, recall_score

for nom, donnees in [("test d'octobre", test), ("décembre", decembre)]:
    p = champion.predict(donnees[X_COLS])
    print(f"{nom:<15} : retards réels {donnees[CIBLE].mean():.1%} | précision {precision_score(donnees[CIBLE], p):.3f} | "
          f"rappel {recall_score(donnees[CIBLE], p):.3f} | f1 {f1_score(donnees[CIBLE], p):.3f}")
```

```plaintext title="Sortie attendue"
test d'octobre  : retards réels 16.9% | précision 0.561 | rappel 0.880 | f1 0.685
décembre        : retards réels 23.9% | précision 0.623 | rappel 0.952 | f1 0.753
```

**Surprise : le modèle fait mieux en décembre.** Les retards réels montent à 23,9 % (dérive de la cible), le modèle en prédit plus (dérive des prédictions)… et il a raison. La pluie et le poids allongent vraiment les délais, exactement comme il l'avait appris. **Les données ont dérivé, mais pas le concept** : la relation entre les caractéristiques d'un colis et son retard est restée la même.

**La décision :** pas de réentraînement en urgence. Le modèle reste en service, la surveillance continue, et l'on note pour l'an prochain : prévenir l'équipe que décembre gonflera le nombre d'alertes (et donc de SMS), ce qui est un sujet **métier**, pas un défaut du modèle.
::::

::: callout remember À retenir
La dérive des données se détecte **tout de suite**, sans étiquettes : c'est un signal d'alerte. La performance ne se mesure qu'**avec** les étiquettes. Une dérive n'implique pas une baisse de performance, et une performance qui baisse n'est pas toujours précédée d'une dérive visible (dérive du concept). On surveille donc les deux.
:::

{#avance}
## Pour aller plus loin : seuils, grands échantillons et surveillance en production

Ce bloc est pour les profils avancés ; rien ici n'est exigé dans l'évaluation.

**Tests statistiques ou distances ?** Avec une petite référence (moins de 1 000 lignes), Evidently utilise par défaut des **tests statistiques** : Kolmogorov-Smirnov pour les variables numériques, khi-deux pour les catégorielles, qui répondent « les deux échantillons viennent-ils de la même distribution ? » avec une p-valeur. Avec de grands échantillons, ces tests deviennent **trop sensibles** : sur un million de lignes, la moindre différence sans importance pratique est « significative ». D'où le passage aux **distances** (Wasserstein, Jensen-Shannon), qui mesurent l'**ampleur** de l'écart et non sa seule existence. C'est la même distinction qu'entre significativité statistique et taille d'effet.

**L'indice de stabilité de la population (PSI).** Très utilisé en banque et en assurance, il découpe une variable en tranches et somme `(p_cur − p_ref) × ln(p_cur / p_ref)` sur les tranches. Règle empirique répandue : moins de 0,1, stable ; de 0,1 à 0,25, à surveiller ; plus de 0,25, dérive importante. Evidently le propose parmi ses méthodes.

**Les fenêtres et la saisonnalité.** Comparer décembre à septembre-octobre fait forcément sonner l'alarme : décembre est **toujours** différent. En production, on choisit la référence avec soin : la période d'entraînement (« le modèle a-t-il vu ça ? »), la semaine précédente (« quelque chose a-t-il cassé hier ? »), ou le même mois l'an dernier (« est-ce la saison habituelle ? »). Les trois répondent à des questions différentes.

**L'alerte qui sonne trop.** Huit variables testées chaque jour, c'est près de 3 000 tests par an : même sans dérive, certains dépasseront le seuil par hasard. On évite la lassitude des alertes en exigeant une dérive sur plusieurs jours consécutifs, ou sur une part des colonnes (le `drift_share` d'Evidently, 50 % par défaut, pour déclarer que le **jeu entier** a dérivé : ici, 2 colonnes sur 8, soit 25 %, ne suffisent pas).

**En production.** Le service de prédiction journalise ses entrées et ses sorties ; un traitement quotidien (au jour 3, une tâche Airflow) calcule les distances sur la journée et les note comme métriques dans MLflow ou dans un outil de supervision ; les étiquettes, quand elles arrivent, permettent de calculer la vraie performance avec quelques jours de décalage. Azure Machine Learning propose cette surveillance intégrée (signaux de dérive des données et des prédictions sur les modèles déployés), et Evidently offre aussi une interface de suivi dans le temps.

{#quiz}
## Quiz de validation

```quiz
- q: Quelle dérive se détecte sans attendre les vrais délais de livraison ?
  options:
    - La dérive du concept
    - La dérive des données (des variables d'entrée)
    - La dérive de la cible
    - Aucune
  answer: 1
  explain: On compare les entrées de décembre à celles de la référence ; les étiquettes ne sont pas nécessaires.
- q: Quelles variables dérivent en décembre, avec un seuil de 0,1 ?
  options:
    - Toutes les variables
    - meteo et poids_kg
    - distance_km et entrepot
    - Aucune
  answer: 1
  explain: La pluie passe de 29 % à 49 % des colis, et le poids moyen de 15,3 à 19,7 kg.
- q: La dérive est détectée. Quelle est la bonne première réaction ?
  options:
    - Réentraîner le modèle immédiatement
    - Enquêter - est-ce un bug de données, la saison, et la performance a-t-elle baissé ?
    - Arrêter le modèle
    - Augmenter le seuil pour ne plus voir l'alerte
  answer: 1
  explain: Une alerte déclenche une enquête. Ici, la dérive est réelle et la performance a même progressé.
- q: En décembre, le F1 du champion passe de 0,685 à 0,753. Qu'en conclut-on ?
  options:
    - Que les données n'ont pas dérivé
    - Que les données ont dérivé, mais pas la relation entre les variables et le retard
    - Que le modèle a été réentraîné
    - Que le test d'octobre était faux
  answer: 1
  explain: Dérive des données sans dérive du concept - le modèle avait appris la bonne relation.
```
