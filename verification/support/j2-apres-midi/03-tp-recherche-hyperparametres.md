---
subtitle: >-
  Ce matin, on a essayé trois réglages au jugé. Cet après-midi, on cherche méthodiquement, avec un
  budget fixe de 8 essais, et surtout sans jamais regarder le jeu de test : on choisit sur une
  semaine de validation. Trois méthodes s'affrontent : la grille, le hasard, et Optuna.
objectives:
  - Distinguer paramètres appris et hyperparamètres choisis
  - Découper un jeu de validation dans le temps, sans toucher au test
  - Mener une recherche par grille, par tirage aléatoire et avec Optuna, à budget égal
  - Choisir un réglage, le réentraîner sur tout le train et l'évaluer une seule fois sur le test
---

{#pourquoi}
## Paramètres et hyperparamètres

**Les paramètres** sont **appris** par le modèle pendant l'entraînement : pour la régression logistique, les 21 coefficients, un par variable après encodage. **Les hyperparamètres** sont **choisis** avant l'entraînement : `C`, `class_weight`, `max_iter`. Aucun algorithme ne les apprend tout seul : il faut les chercher.

**L'analogie du four.** Une nouvelle recette de pain : quelle température, combien de temps ? On peut tester toutes les combinaisons d'une liste (180, 200, 220 °C × 30, 40 minutes) : c'est la **grille**. On peut tirer des réglages au hasard dans des plages raisonnables : c'est la **recherche aléatoire**. Ou l'on peut faire comme un boulanger expérimenté : après chaque fournée, regarder ce qui a marché et viser la zone prometteuse : c'est la **recherche bayésienne**, celle d'Optuna.

**Le budget.** Chaque essai coûte un entraînement. Pour comparer honnêtement les méthodes, on leur donne **le même budget : 8 essais**.

{#validation}
## La règle d'or : ne jamais choisir sur le test

**Pourquoi ?** Si l'on essaie 8 réglages et qu'on garde le meilleur **sur le test**, le score obtenu est trop optimiste : on a choisi, parmi 8, celui qui a eu de la chance sur ces colis-là. Le test ne mesure plus la performance sur des données inconnues. On dit qu'on a **surappris le jeu de test**.

**La solution :** découper le train une seconde fois, toujours dans le temps. Les 5 premières semaines servent à entraîner chaque essai ; la **6e semaine** (du 12 au 18 octobre) sert à les comparer : c'est le **jeu de validation**. Le test (du 19 octobre au 1er novembre) reste enfermé jusqu'à la toute fin.

| Jeu | Période | Colis | Rôle |
|---|---|---|---|
| Entraînement | 7 septembre → 11 octobre | 3 166 | Apprendre chaque essai |
| Validation | 12 → 18 octobre | 639 | **Choisir** le réglage |
| Test | 19 octobre → 1er novembre | 1 230 | **Mesurer**, une seule fois, le réglage choisi |

{#etape1}
## Étape 1 : la semaine de validation

:::: lab Étape 1 | Découper et définir le score d'un essai | 5 min
Dans votre notebook `j2-apres-midi.ipynb` :

```python title="Cellule 7 : entraînement, validation et score d'un essai"
from sklearn.metrics import f1_score

entrainement = train[train["date_expedition"] < "2026-10-12"]
validation = train[train["date_expedition"] >= "2026-10-12"]
print(f"entraînement : {len(entrainement)} colis | validation : {len(validation)} colis, "
      f"du {validation['date_expedition'].min()} au {validation['date_expedition'].max()}")


def score(C, class_weight):
    """F1 sur la semaine de validation d'un modèle entraîné sur les semaines précédentes."""
    modele = construire_modele(C, class_weight, 1000)
    modele.fit(entrainement[X_COLS], entrainement[CIBLE])
    return round(f1_score(validation[CIBLE], modele.predict(validation[X_COLS])), 3)
```

```plaintext title="Sortie attendue"
entraînement : 3166 colis | validation : 639 colis, du 2026-10-12 au 2026-10-18
```

`score` est la **fonction objectif** : elle reçoit un réglage et renvoie un nombre à maximiser. Les trois méthodes vont l'appeler 8 fois chacune.
::::

{#etape2}
## Étape 2 : la grille

:::: lab Étape 2 | Grid Search : toutes les combinaisons d'une liste | 7 min
4 valeurs de `C` × 2 valeurs de `class_weight` = 8 essais, le budget exact. Les valeurs de `C` sont espacées d'un facteur 10 : on ne sait pas encore si le bon réglage est 0,05 ou 5, on balaie donc les **ordres de grandeur**.

```python title="Cellule 8 : la grille"
grille = [(C, cw, score(C, cw)) for C in [0.01, 0.1, 1.0, 10.0] for cw in [None, "balanced"]]
for C, cw, f1 in grille:
    print(f"C={C:<6} class_weight={str(cw):<9} F1={f1}")
meilleur_grille = max(grille, key=lambda essai: essai[2])
print("meilleur :", meilleur_grille)
```

```plaintext title="Sortie attendue"
C=0.01   class_weight=None      F1=0.508
C=0.01   class_weight=balanced  F1=0.566
C=0.1    class_weight=None      F1=0.62
C=0.1    class_weight=balanced  F1=0.618
C=1.0    class_weight=None      F1=0.607
C=1.0    class_weight=balanced  F1=0.629
C=10.0   class_weight=None      F1=0.597
C=10.0   class_weight=balanced  F1=0.632
meilleur : (10.0, 'balanced', 0.632)
```

Trois enseignements :

- **Trop de régularisation coûte cher** : avec `C=0.01`, le modèle est trop contraint pour apprendre (F1 0,508 et 0,566). C'est le **sous-apprentissage**.
- **`balanced` l'emporte dès que `C` vaut 1 ou plus**, et donne le meilleur score : 0,632 avec `C=10`. À `C=0.1`, les deux options sont au coude à coude (0,62 et 0,618).
- **Les écarts sont faibles au-delà de `C=0.1`** : de 0,597 à 0,632. Sur 639 colis de validation, dont 92 en retard, quelques colis bien ou mal classés suffisent à inverser un classement. Il ne faut pas surinterpréter le troisième chiffre après la virgule.
::::

{#etape3}
## Étape 3 : le hasard

:::: lab Étape 3 | Randomized Search : 8 tirages | 7 min
On tire `C` au hasard entre 0,001 et 100 **sur une échelle logarithmique** (`loguniform`) : chaque ordre de grandeur a la même chance d'être tiré, comme dans la grille. `ParameterSampler`, de scikit-learn, fait les tirages ; `random_state=42` les rend reproductibles.

```python title="Cellule 9 : le tirage aléatoire"
from scipy.stats import loguniform
from sklearn.model_selection import ParameterSampler

espace = {"C": loguniform(1e-3, 1e2), "class_weight": [None, "balanced"]}
tirages = list(ParameterSampler(espace, n_iter=8, random_state=42))
aleatoire = [(round(float(t["C"]), 4), t["class_weight"], score(t["C"], t["class_weight"])) for t in tirages]
for C, cw, f1 in aleatoire:
    print(f"C={C:<7} class_weight={str(cw):<9} F1={f1}")
meilleur_aleatoire = max(aleatoire, key=lambda essai: essai[2])
print("meilleur :", meilleur_aleatoire)
```

```plaintext title="Sortie attendue"
C=0.0746  class_weight=None      F1=0.627
C=0.0083  class_weight=balanced  F1=0.567
C=0.9847  class_weight=None      F1=0.607
C=0.1695  class_weight=None      F1=0.613
C=0.002   class_weight=balanced  F1=0.454
C=0.0466  class_weight=balanced  F1=0.608
C=3.4703  class_weight=balanced  F1=0.632
C=0.0019  class_weight=balanced  F1=0.45
meilleur : (3.4703, 'balanced', 0.632)
```

Le hasard atteint **le même meilleur score que la grille, 0,632**, avec `C=3.4703`. Il a aussi essayé des valeurs que la grille n'a jamais vues, comme `C=0.0746` sans pondération (0,627). Mais il a gaspillé deux essais vers `C=0.002` (0,454 et 0,45), et n'a tiré `balanced` avec un `C` assez grand qu'une seule fois. Avec **deux** hyperparamètres seulement, dont un à deux valeurs, la grille couvre déjà l'espace : le hasard n'a pas d'avantage. Il en prend un quand les hyperparamètres sont nombreux (voir le bloc avancé).

Python affiche `0.45` et non `0.450` : `round` renvoie le nombre 0,45, et Python n'écrit pas les zéros inutiles.
::::

{#etape4}
## Étape 4 : Optuna

:::: lab Étape 4 | Une recherche qui apprend de ses essais | 10 min
**Optuna** est une bibliothèque libre d'optimisation d'hyperparamètres. Son algorithme par défaut, **TPE** (*Tree-structured Parzen Estimator*), commence par quelques essais au hasard pour explorer, puis sépare les essais passés en « bons » et « moins bons » et propose le réglage suivant là où les bons sont plus fréquents. On lui laisse ici **4 essais d'exploration** (`n_startup_trials=4`) sur les 8 du budget.

Le vocabulaire d'Optuna : une **étude** (*study*) est une recherche, un **essai** (*trial*) est une évaluation de la fonction objectif. Dans la fonction, `essai.suggest_…` demande à Optuna une valeur pour chaque hyperparamètre.

```python title="Cellule 10 : Optuna"
import optuna

optuna.logging.set_verbosity(optuna.logging.WARNING)


def objectif(essai):
    C = essai.suggest_float("C", 1e-3, 1e2, log=True)
    class_weight = essai.suggest_categorical("class_weight", [None, "balanced"])
    return score(C, class_weight)


etude = optuna.create_study(direction="maximize",
                            sampler=optuna.samplers.TPESampler(seed=42, n_startup_trials=4))
etude.optimize(objectif, n_trials=8)
for essai in etude.trials:
    print(f"essai {essai.number} : C={essai.params['C']:.4f} "
          f"class_weight={str(essai.params['class_weight']):<9} F1={essai.value}")
print("meilleur :", round(etude.best_params["C"], 4), etude.best_params["class_weight"], etude.best_value)
```

```plaintext title="Sortie attendue"
essai 0 : C=0.0746 class_weight=None      F1=0.627
essai 1 : C=0.9847 class_weight=None      F1=0.607
essai 2 : C=0.0020 class_weight=None      F1=0.0
essai 3 : C=3.4703 class_weight=balanced  F1=0.632
essai 4 : C=86.4414 class_weight=balanced  F1=0.632
essai 5 : C=0.0011 class_weight=balanced  F1=0.435
essai 6 : C=0.5420 class_weight=balanced  F1=0.629
essai 7 : C=0.0318 class_weight=balanced  F1=0.596
meilleur : 3.4703 balanced 0.632
```

`set_verbosity(WARNING)` masque le message qu'Optuna imprime après chaque essai. `log=True` joue le même rôle que `loguniform` : l'échelle logarithmique.

**L'essai 2 a un F1 de 0.** Avec `C=0.002` et sans pondération, le modèle est si contraint qu'il ne prédit plus **aucun** retard : rappel nul, donc F1 nul. scikit-learn affiche à ce moment un avertissement (`UndefinedMetricWarning`) : la précision ne peut pas se calculer quand rien n'est signalé.

**Regardez les essais 4 à 7**, ceux où TPE choisit : **tous** utilisent `balanced`. Après 4 essais d'exploration, dont un seul avec `balanced` (le meilleur, 0,632), Optuna a appris que c'était la bonne valeur, et ne cherche plus que le bon `C`, en sondant des zones différentes (86, 0,001, 0,54, 0,03). Il retrouve 0,632 à l'essai 4, sans faire mieux : sur ce problème simple, **les trois méthodes plafonnent au même score**.
::::

{#etape5}
## Étape 5 : choisir, puis mesurer une seule fois

:::: lab Étape 5 | Le réglage retenu, sur le test | 6 min
| Méthode | Meilleur réglage | F1 de validation |
|---|---|---|
| Grille | `C=10`, `balanced` | 0,632 |
| Hasard | `C=3.4703`, `balanced` | 0,632 |
| Optuna | `C=3.4703`, `balanced` (essai 3), et `C=86.44` (essai 4) | 0,632 |

Trois réglages sont ex aequo à 0,632, tous avec `balanced` : `C` = 3,47, 10 et 86,44. **À score égal, on retient le plus régularisé** (le plus petit `C`, donc le modèle le plus simple, qui a le moins de chances de surapprendre) : **`C=3.4703`**. La leçon de ce TP n'est pas « quelle méthode gagne » : c'est qu'au-delà du bon `class_weight` et d'un `C` pas trop petit, la recherche n'apporte plus rien. Pour progresser, il faudrait d'autres **variables** (par exemple la charge de l'entrepôt ce jour-là), pas d'autres réglages.

Maintenant seulement, on **réentraîne** ce réglage **sur tout le train** (les 6 semaines : plus de données, meilleur modèle) et on l'évalue **une seule fois** sur le test :

```python title="Cellule 11 : le réglage retenu, sur le test"
from sklearn.metrics import precision_score, recall_score

retenu = construire_modele(3.4703, "balanced", 1000).fit(train[X_COLS], train[CIBLE])
predictions = retenu.predict(test[X_COLS])
print(f"précision {precision_score(test[CIBLE], predictions):.3f} | "
      f"rappel {recall_score(test[CIBLE], predictions):.3f} | f1 {f1_score(test[CIBLE], predictions):.3f}")
```

```plaintext title="Sortie attendue"
précision 0.574 | rappel 0.875 | f1 0.693
```

Le réglage retenu atteint le critère de succès, avec un F1 de **0,693**. Le champion actuel, la version 2 (`C=0.1`, réglée au jugé ce matin), fait **0,685**. Faut-il le remplacer pour 0,008 de mieux ? Ce n'est pas au data scientist d'en décider à l'œil : la **règle de promotion** de la notion 2 tranche. Vous l'appliquerez dans l'évaluation de fin de journée.

**Pourquoi le F1 du test (0,693) est-il plus haut que celui de la validation (0,632) ?** Deux raisons : le modèle final a appris sur 6 semaines au lieu de 5, et la semaine de validation n'a que 14,4 % de retards (contre 16,9 % sur le test), ce qui rend les retards plus difficiles à attraper sans fausses alertes. Avec une seule semaine de validation, le score varie beaucoup d'une semaine à l'autre : c'est la limite de cette méthode simple (voir le bloc avancé).
::::

::: callout tip Question fréquente : « Et GridSearchCV, de scikit-learn ? »
`GridSearchCV` et `RandomizedSearchCV` font la même chose en une ligne, avec une **validation croisée** : plusieurs découpages, et la moyenne des scores. Attention : leur découpage par défaut est **aléatoire**. Pour des données datées, passez-leur `cv=TimeSeriesSplit(n_splits=4)`, qui découpe toujours le passé pour entraîner et la suite pour valider, ou un `PredefinedSplit` qui reproduit exactement notre semaine de validation.
:::

{#avance}
## Pour aller plus loin : pourquoi le hasard bat la grille, et comment pense TPE

Ce bloc est pour les profils avancés ; rien ici n'est exigé dans l'évaluation.

**Le hasard et les dimensions inutiles.** Bergstra et Bengio (2012) ont montré que, dans la plupart des problèmes réels, **peu d'hyperparamètres comptent vraiment**. Avec une grille de 3 valeurs sur 4 hyperparamètres (81 essais), on n'essaie que 3 valeurs de l'hyperparamètre important : les 78 autres essais répètent ces 3 valeurs en faisant varier des réglages sans effet. 81 tirages aléatoires essaient 81 valeurs différentes de chaque hyperparamètre, dont l'important. Plus il y a d'hyperparamètres, plus l'avantage du hasard grandit. Notre cas (2 hyperparamètres, dont un binaire) est justement celui où la grille ne perd rien.

**Comment TPE choisit le prochain essai.** Après les essais d'exploration, TPE trie les essais passés : les meilleurs (par exemple le quart supérieur) forment la distribution `l(x)`, les autres la distribution `g(x)`. Il tire de nombreux candidats selon `l(x)` et garde celui qui maximise le rapport `l(x) / g(x)` : un réglage qui ressemble aux bons essais et pas aux mauvais. C'est un compromis automatique entre **exploiter** (chercher près des bons essais) et **explorer** (les zones peu visitées gardent une petite probabilité). Avec un budget de 8, l'avantage est faible ; avec 100 essais et 6 hyperparamètres, il devient net.

**L'élagage** (*pruning*). Pour les modèles qui s'entraînent par itérations (boosting, réseaux de neurones), Optuna peut **arrêter tôt** un essai dont les scores intermédiaires sont mauvais par rapport aux autres (`MedianPruner`). Le budget se mesure alors en temps de calcul, pas en nombre d'essais.

**Surapprendre la validation.** Avec des centaines d'essais, on finit aussi par trouver le réglage qui a eu de la chance sur la semaine de validation. Les parades : une validation croisée temporelle (plusieurs semaines de validation successives, score moyen), un budget raisonnable, et toujours le test final, regardé une seule fois.

**Deux objectifs à la fois.** Le critère de ColisVert a deux seuils : rappel et précision. Optuna sait optimiser plusieurs objectifs (`directions=["maximize", "maximize"]`) : il renvoie alors un **front de Pareto**, l'ensemble des réglages qu'aucun autre ne bat sur les deux objectifs à la fois. Le métier choisit ensuite son compromis sur ce front. Au jour 4, on reliera Optuna à MLflow pour garder la trace de chaque essai.

{#quiz}
## Quiz de validation

```quiz
- q: Pourquoi ne choisit-on pas le meilleur réglage sur le jeu de test ?
  options:
    - Parce que le test est trop petit
    - Parce que le score du réglage choisi serait trop optimiste - on aurait gardé celui qui a eu de la chance sur ces colis-là
    - Parce que scikit-learn l'interdit
    - Parce que le test ne contient pas de retards
  answer: 1
  explain: Le test doit rester inconnu jusqu'à la fin. On choisit sur la validation, on mesure une fois sur le test.
- q: Avec 8 essais chacune, quel meilleur F1 de validation la grille, le hasard et Optuna ont-ils atteint ici ?
  options: ["La grille seule atteint 0,632", "Optuna seul dépasse 0,64", "Les trois plafonnent à 0,632", "Aucune ne dépasse 0,6"]
  answer: 2
  explain: Sur ce problème simple, le bon class_weight compte bien plus que la méthode de recherche.
- q: Que fait l'algorithme TPE d'Optuna après ses essais d'exploration ?
  options:
    - Il recommence la grille complète
    - Il propose le prochain réglage là où les bons essais passés sont plus fréquents que les moins bons
    - Il choisit toujours la plus grande valeur de C
    - Il entraîne sur le jeu de test
  answer: 1
  explain: Il maximise le rapport entre la densité des bons essais et celle des moins bons.
- q: À F1 de validation égal, quel réglage préférer entre C = 3,47 et C = 10 ?
  options:
    - C = 10, parce qu'il est plus grand
    - C = 3,47, le plus régularisé, donc le modèle le plus simple
    - Peu importe, on tire au sort
    - Aucun, il faut recommencer la recherche
  answer: 1
  explain: Plus C est petit, plus la régularisation est forte. À score égal, le modèle le plus simple surapprend moins.
```
