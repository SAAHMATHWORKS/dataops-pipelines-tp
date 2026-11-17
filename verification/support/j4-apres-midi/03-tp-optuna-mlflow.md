---
subtitle: >-
  La forêt de départ pèse 20 Mo et ne tient même pas l'engagement de rappel. Peut-on garder sa
  qualité pour une fraction de son poids ? Optuna cherche, sur 30 essais, les réglages de forêt qui
  donnent le meilleur compromis entre F1 et taille, sous la contrainte de la charte. Chaque essai est
  tracé dans MLflow. On choisit avec une règle écrite à l'avance, puis on change de point de vue :
  et si la meilleure façon d'alléger un modèle était de changer de famille ?
objectives:
  - Écrire une fonction objectif à deux valeurs, avec une contrainte, pour Optuna 5
  - Tracer chaque essai d'une recherche comme un run MLflow imbriqué
  - Lire un front de Pareto et choisir un modèle avec une règle fixée à l'avance
  - Mesurer le gain d'empreinte obtenu, sur les trois ressources
  - Enregistrer les modèles retenus dans le registre, y compris un modèle à arbres au format skops
---

{#etape1}
## Étape 1 : une fonction objectif tracée dans MLflow

:::: lab Étape 1 | Deux objectifs, une contrainte, un run par essai | 10 min
On cherche parmi les **forêts aléatoires** : nombre d'arbres, profondeur maximale, taille minimale des feuilles. Chaque essai :

1. entraîne une forêt sur les 5 premières semaines et la mesure sur la semaine de validation (fonction `qualite` de la notion 1) ;
2. déclare la **contrainte** de la charte : un rappel d'au moins 0,80 ;
3. ouvre un **run MLflow imbriqué** (`nested=True`) où il note son réglage et ses trois mesures ;
4. renvoie ses **deux objectifs**, arrondis : le F1 (à maximiser) et la taille en Ko (à minimiser).

```python title="Cellule 5 : la fonction objectif"
import os

import mlflow
import optuna

os.environ["MLFLOW_SUPPRESS_PRINTING_URL_TO_STDOUT"] = "true"   # pas de lien « View run » par essai
optuna.logging.set_verbosity(optuna.logging.WARNING)
mlflow.set_experiment("j4-empreinte")


def foret(reglage):
    return avec(RandomForestClassifier(**reglage, class_weight="balanced", random_state=2026, n_jobs=1))


def objectif(essai):
    reglage = {
        "n_estimators": essai.suggest_int("n_estimators", 10, 300, log=True),
        "max_depth": essai.suggest_int("max_depth", 3, 20),
        "min_samples_leaf": essai.suggest_int("min_samples_leaf", 1, 50, log=True),
    }
    modele = foret(reglage)
    f1, rappel = qualite(modele)
    taille = taille_ko(modele)
    essai.set_constraint("rappel", 0.80 - rappel)        # admissible si le rappel atteint 0,80
    with mlflow.start_run(run_name=f"essai-{essai.number}", nested=True):
        mlflow.log_params(reglage)
        mlflow.log_metrics({"f1": f1, "rappel": rappel, "taille_ko": taille})
    return round(f1, 3), round(taille, 1)
```

- `log=True` sur le nombre d'arbres et la taille des feuilles : chaque **ordre de grandeur** a la même chance d'être essayé (10 à 30 arbres autant que 100 à 300), comme au jour 2.
- `n_jobs=1` et `random_state=2026` : une forêt construite sur un seul cœur, avec une graine fixe, donne **le même modèle** sur toutes les VM. Sans cela, vos essais différeraient de ceux du support.
- La variable d'environnement `MLFLOW_SUPPRESS_PRINTING_URL_TO_STDOUT` évite que MLflow imprime deux lignes de liens à la fin de **chacun** des 30 runs.
- On arrondit les objectifs pour qu'Optuna ne départage pas deux essais sur la douzième décimale : une différence de F1 inférieure au millième ne veut rien dire sur 639 colis.
::::

{#etape2}
## Étape 2 : 30 essais, un front

:::: lab Étape 2 | Lancer la recherche dans un run parent | 10 min
Le run **parent** `foret-sous-contrainte` regroupe les 30 runs d'essais : dans l'interface de MLflow, ils apparaissent repliés sous lui.

```python title="Cellule 6 : la recherche"
with mlflow.start_run(run_name="foret-sous-contrainte"):
    etude = optuna.create_study(directions=["maximize", "minimize"],
                                sampler=optuna.samplers.TPESampler(seed=2026))
    etude.optimize(objectif, n_trials=30)
    front_foret = sorted(etude.best_trials, key=lambda essai: essai.values[1])
    mlflow.log_metric("essais_sur_le_front", len(front_foret))

non_admissibles = [essai.number for essai in etude.trials if essai.constraints["rappel"] > 0]
print(f"{len(etude.trials)} essais, non admissibles : {non_admissibles}, {len(front_foret)} sur le front")
for essai in front_foret:
    print(f"essai {essai.number:>2} : F1 {essai.values[0]:.3f} {essai.values[1]:>8.1f} Ko  {essai.params}")
```

```plaintext title="Sortie attendue"
30 essais, non admissibles : [4, 6, 8, 28], 7 sur le front
essai  1 : F1 0.560     73.3 Ko  {'n_estimators': 13, 'max_depth': 11, 'min_samples_leaf': 48}
essai 19 : F1 0.567    100.7 Ko  {'n_estimators': 10, 'max_depth': 13, 'min_samples_leaf': 18}
essai  9 : F1 0.573    135.3 Ko  {'n_estimators': 11, 'max_depth': 11, 'min_samples_leaf': 12}
essai 14 : F1 0.584    264.1 Ko  {'n_estimators': 15, 'max_depth': 16, 'min_samples_leaf': 7}
essai  2 : F1 0.589    327.5 Ko  {'n_estimators': 19, 'max_depth': 19, 'min_samples_leaf': 7}
essai 25 : F1 0.619    445.0 Ko  {'n_estimators': 17, 'max_depth': 9, 'min_samples_leaf': 2}
essai 21 : F1 0.637   2418.9 Ko  {'n_estimators': 58, 'max_depth': 13, 'min_samples_leaf': 2}
```

La recherche dure quelques secondes : les forêts sont petites et les données aussi.
::::

**Lecture du front.**

- **4 essais sur 30 sont non admissibles** (rappel sous 0,80) : ils sont absents du front, quel que soit leur F1.
- **Le front compte 7 forêts**, de 73 Ko (F1 0,560) à 2,4 Mo (F1 0,637). Vers le bas de la liste, chaque gain de F1 se paie en poids.
- **Le coude est à l'essai 25** : 445 Ko pour un F1 de 0,619. Au-delà, gagner encore 0,018 de F1 (essai 21) coûte une taille multipliée par 5,4.
- **Aucune forêt du front n'a plus de 58 arbres.** Les 300 arbres du départ n'ont jamais servi à rien. Les feuilles plus grandes (`min_samples_leaf`) allègent beaucoup : un arbre qui s'arrête dès qu'il reste peu de colis a moins de nœuds.

::: callout tip Voir le front dans MLflow
Ouvrez http://localhost:5000, expérience `j4-empreinte`, et dépliez le run `foret-sous-contrainte`. Sélectionnez les 30 runs d'essais, puis passez à la vue graphique de l'expérience et ajoutez un **nuage de points** avec `taille_ko` en abscisse et `f1` en ordonnée : le front est le bord supérieur gauche du nuage. Vous pouvez aussi trier les runs par `f1`, ou filtrer avec `metrics.rappel >= 0.8`.
:::

{#etape3}
## Étape 3 : choisir avec la règle écrite à l'avance

La règle, fixée **avant** la recherche : **le modèle le plus léger du front dont le F1 est au moins celui de la forêt de départ, à 0,005 près**. On ne veut pas perdre de qualité ; on veut perdre du poids.

:::: lab Étape 3 | Appliquer la règle, puis mesurer le gain | 10 min
```python title="Cellule 7 : la règle de choix"
depart = mesures["forêt de départ"]
retenu = min((essai for essai in front_foret if essai.values[0] >= depart["f1"] - 0.005),
             key=lambda essai: essai.values[1])
print(f"départ : F1 {depart['f1']:.3f}, rappel {depart['rappel']:.3f}, {depart['taille_ko']:.1f} Ko")
print(f"retenu : essai {retenu.number}, F1 {retenu.values[0]:.3f}, "
      f"rappel {0.80 - retenu.constraints['rappel']:.3f}, {retenu.values[1]:.1f} Ko, {retenu.params}")
print(f"{depart['taille_ko'] / retenu.values[1]:.0f} fois plus léger")
```

```plaintext title="Sortie attendue"
départ : F1 0.620, rappel 0.772, 20677.2 Ko
retenu : essai 25, F1 0.619, rappel 0.891, 445.0 Ko, {'n_estimators': 17, 'max_depth': 9, 'min_samples_leaf': 2}
46 fois plus léger
```

La taille n'est qu'une des trois ressources. Vérifions les deux autres sur le modèle retenu :

```python title="Cellule 8 : les trois ressources, avant et après"
compacte = foret(retenu.params)
qualite(compacte)
for nom, modele in [("forêt de départ", candidats["forêt de départ"]), ("forêt compacte", compacte),
                    ("logistique", candidats["logistique"])]:
    print(f"{nom:<16} {taille_ko(modele):>8.1f} Ko  {ram_mo(modele):>5.2f} Mo  "
          f"{latence_ms(modele, decembre[X_COLS]):.2f} ms")
```

```plaintext title="Sortie attendue"
forêt de départ   20677.2 Ko  21.91 Mo  67.57 ms
forêt compacte      445.0 Ko   0.56 Mo  8.80 ms
logistique            4.4 Ko   0.03 Mo  4.23 ms
```

La forêt compacte (essai 25) est **46 fois plus légère** sur le disque, occupe **39 fois moins de mémoire** (0,56 Mo contre 21,91 Mo) et prédit environ **huit fois plus vite**, avec le même F1 et un rappel qui tient la charte (0,891). Avec 4 processus de service, la forêt de départ immobilisait près de 88 Mo de mémoire ; la forêt compacte en prend un peu plus de 2. La régression logistique reste la plus légère et la plus rapide.
::::

{#etape4}
## Étape 4 : et si l'on changeait de famille ?

Optuna a cherché **parmi les forêts**, parce que c'était la question posée. Mais la notion 1 avait déjà mesuré une régression logistique. Plaçons-la à côté du modèle retenu :

:::: lab Étape 4 | La forêt compacte face à la régression logistique | 5 min
```python title="Cellule 9 : deux familles, même semaine de validation"
f1_c, rappel_c = qualite(compacte)
lr = mesures["logistique"]
print(f"forêt compacte : F1 {f1_c:.3f}  rappel {rappel_c:.3f}  {taille_ko(compacte):>6.1f} Ko")
print(f"logistique     : F1 {lr['f1']:.3f}  rappel {lr['rappel']:.3f}  {lr['taille_ko']:>6.1f} Ko")
```

```plaintext title="Sortie attendue"
forêt compacte : F1 0.619  rappel 0.891   445.0 Ko
logistique     : F1 0.618  rappel 0.924     4.4 Ko
```

**Même F1, à un millième près ; meilleur rappel pour la régression logistique (0,924 contre 0,891) ; et 100 fois moins de poids.** La plus grosse réduction d'empreinte ne vient pas des hyperparamètres, mais du **choix de la famille**.

Pourquoi ? Dans les données de ColisVert, le délai réel est presque une **somme** de contributions : la distance, le poids, la pluie, l'entrepôt, le créneau. Une régression logistique représente directement une somme pondérée. Une forêt doit l'approcher par des centaines de marches d'escalier, et chaque marche coûte des nœuds. Quand la structure du problème est simple, le modèle simple est à la fois le plus juste et le plus sobre.
::::

::: callout info Une recherche sur toutes les familles à la fois
On aurait pu laisser Optuna choisir aussi la famille (`suggest_categorical("famille", [...])`, puis des hyperparamètres propres à chaque famille). C'est ce qu'on appelle une recherche d'**architecture** ou de **pipeline**, et c'est le principe des outils d'AutoML. Essayé sur ces données avec 40 essais, le front se réduit à **un seul point** : la régression logistique, à la fois la plus précise et la plus légère. On a choisi de procéder en deux temps pour **voir** le compromis à l'intérieur d'une famille, puis la leçon : changer de famille.
:::

{#etape5}
## Étape 5 : mesurer une seule fois, puis enregistrer

On garde **deux** modèles pour le TP 2 :

- **`leger`** : la régression logistique (`C=0.1`, `balanced`), le réglage du champion du jour 2. Elle reste le modèle **servi**.
- **`foret`** : la forêt compacte. Elle sera le **challenger**, observé en ombre sur les colis de décembre. Une autre famille peut se comporter autrement quand les données dérivent.

On les réentraîne sur **tout le train** (6 semaines), on les mesure **une seule fois** sur le test, puis on les enregistre dans un nouveau nom du registre, `colisvert-empreinte`, avec un alias chacun.

:::: lab Étape 5 | Le test, puis le registre | 10 min
```python title="Cellule 10 : le test, puis le registre"
from sklearn.metrics import precision_score

client = mlflow.MlflowClient()
finales = {
    "leger": (construire_modele(0.1, "balanced", 1000), {}),
    "foret": (foret(retenu.params), {"skops_trusted_types": ["sklearn.tree._tree.Tree"]}),
}
for alias, (modele, options) in finales.items():
    modele.fit(train[X_COLS], train[CIBLE])
    predictions = modele.predict(test[X_COLS])
    scores = {"precision": precision_score(test[CIBLE], predictions),
              "rappel": recall_score(test[CIBLE], predictions), "f1": f1_score(test[CIBLE], predictions)}
    with mlflow.start_run(run_name=f"final-{alias}"):
        mlflow.log_metrics({**scores, "taille_ko": taille_ko(modele)})
        info = mlflow.sklearn.log_model(modele, name="modele", input_example=train[X_COLS].head(3),
                                        registered_model_name="colisvert-empreinte", **options)
    client.set_registered_model_alias("colisvert-empreinte", alias, info.registered_model_version)
    print(f"{alias:<5} version {info.registered_model_version} | test : précision {scores['precision']:.3f}  "
          f"rappel {scores['rappel']:.3f}  F1 {scores['f1']:.3f}")
```

```plaintext title="Sortie attendue"
leger version 1 | test : précision 0.561  rappel 0.880  F1 0.685
foret version 2 | test : précision 0.534  rappel 0.875  F1 0.663
```

Sous la cellule, MLflow écrit aussi ses propres messages (en rouge : ils passent par la sortie d'erreur, mais ce ne sont pas des erreurs) : `Successfully registered model 'colisvert-empreinte'.` puis `Created version '1'…` et `Created version '2'…`.

- **La régression logistique** retrouve exactement les chiffres du champion du jour 2 (0,561 / 0,880 / 0,685) : c'est le même réglage, sur les mêmes données. Rien n'a bougé, c'est rassurant.
- **La forêt compacte** tient la charte sur le test (rappel 0,875 ≥ 0,80, précision 0,534 ≥ 0,50), mais son F1 est inférieur de 0,022.
- **Décision :** la régression logistique reste le modèle servi. La forêt devient le **challenger**, à observer en ombre sur décembre : on va vérifier si une autre famille résiste mieux aux données qui dérivent.

::: hint
`MlflowException: The saved sklearn model references untrusted types` : l'option `skops_trusted_types` manque pour la forêt. Elle déclare fiable le type `sklearn.tree._tree.Tree`, que skops refuse par défaut (notion 1). Des numéros de version plus élevés (3 et 4) : vous avez relancé la cellule, et chaque relance crée deux nouvelles versions. Ce n'est pas grave : les alias pointent sur les dernières.
:::
::::

{#avance}
## Pour aller plus loin : chercher plus vite, chercher plus loin

Ce bloc est pour les profils avancés ; rien ici n'est exigé dans l'évaluation.

- **Arrêter tôt les mauvais essais.** Pour un boosting ou un réseau de neurones, l'entraînement se fait par étapes. `essai.report(score, étape)` puis `essai.should_prune()` permettent d'abandonner un essai qui part mal (élagage, *pruning*). Optuna ne sait élaguer que les études à **un** objectif.
- **Paralléliser.** Plusieurs processus peuvent travailler sur la même étude s'ils partagent un stockage (`storage="postgresql://…"`). C'est là que la stratégie *constant liar* de TPE, activée par défaut depuis Optuna 5, sert : elle évite que deux processus proposent le même réglage en même temps.
- **Mesurer la latence pendant la recherche.** On l'a laissée de côté parce qu'elle dépend de la machine : deux VM auraient obtenu deux fronts différents. En production, on la mesure sur la machine cible, et on l'utilise plutôt comme **contrainte** (« p95 sous 50 ms ») que comme objectif.
- **L'intégration MLflow d'Optuna.** Le paquet `optuna-integration` fournit un rappel (*callback*) qui crée un run par essai. On l'a écrit à la main pour voir ce qu'il fait, et pour y ajouter nos propres métriques.

{#quiz}
## Quiz

```quiz
- q: Pourquoi chaque essai est-il un run MLflow imbriqué dans un run parent ?
  options:
    - Parce qu'Optuna l'exige
    - Pour retrouver, comparer et filtrer les 30 essais dans l'interface, regroupés sous la recherche qui les a produits
    - Pour accélérer la recherche
    - Pour enregistrer les modèles dans le registre
  answer: 1
  explain: Le run parent est la recherche ; les runs enfants sont ses essais, avec leurs réglages et leurs mesures.
- q: La forêt de départ est-elle sur le front de la Cellule 6 ?
  options:
    - Oui, c'est le meilleur F1
    - Non - elle n'a pas été essayée par Optuna, et elle ne tient pas la contrainte de rappel
    - Oui, c'est la plus grosse
    - On ne peut pas savoir
  answer: 1
  explain: Le front ne contient que des essais admissibles de la recherche ; la forêt de départ a un rappel de 0,772.
- q: Pourquoi ne pas utiliser la latence comme objectif d'Optuna dans ce TP ?
  options:
    - Parce qu'elle n'a pas d'importance
    - Parce qu'elle dépend de la machine - deux VM obtiendraient deux fronts différents
    - Parce qu'Optuna ne sait pas la mesurer
    - Parce qu'elle est toujours nulle
  answer: 1
  explain: Une mesure non reproductible fait d'une recherche un tirage au sort ; on la mesure sur la machine cible et on l'utilise en contrainte.
- q: Pourquoi déclarer skops_trusted_types pour enregistrer la forêt ?
  options:
    - Pour la compresser
    - Parce que skops refuse par défaut le type d'arbre de scikit-learn, et qu'on déclare fiable un modèle qu'on a entraîné soi-même
    - Pour l'enregistrer plus vite
    - Pour qu'elle soit servie en ombre
  answer: 1
  explain: C'est une décision de sécurité explicite, à ne prendre que pour des fichiers dont on connaît l'origine.
```
