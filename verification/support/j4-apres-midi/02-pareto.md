---
subtitle: >-
  Choisir un modèle, c'est rarement maximiser un seul nombre. On veut une bonne qualité ET une
  petite empreinte, et les deux tirent en sens contraire. Plutôt que de les fondre dans une note
  arbitraire, on dessine le front de Pareto, les compromis qu'on ne peut pas améliorer sans rien
  sacrifier, puis on y applique les contraintes du métier. Optuna 5 sait chercher ce front.
objectives:
  - Définir la dominance et le front de Pareto
  - Distinguer un objectif d'une contrainte, et choisir sur un front avec une règle explicite
  - Expliquer pourquoi une somme pondérée des objectifs est une mauvaise idée
  - Configurer une étude Optuna à plusieurs objectifs avec des contraintes
---

{#probleme}
## Deux objectifs qui tirent en sens contraire

**L'analogie de la camionnette.** ColisVert renouvelle sa flotte. Une camionnette consomme peu, une autre charge davantage. Aucune n'est « la meilleure » dans l'absolu : tout dépend de la tournée. En revanche, une camionnette qui consomme **plus** et charge **moins** qu'une autre est simplement à écarter. Le choix se fait parmi celles qu'**aucune autre ne bat sur les deux critères à la fois**.

C'est exactement la situation de la notion 1 : on veut un F1 élevé **et** un modèle léger.

- **Dominance.** Un modèle A **domine** un modèle B s'il est au moins aussi bon que B sur tous les objectifs, et strictement meilleur sur au moins un.
- **Front de Pareto.** C'est l'ensemble des modèles qu'aucun autre ne domine. Tous les autres sont à écarter, quelles que soient les préférences.

Le nom vient de l'économiste Vilfredo Pareto. Sur le front, on ne peut plus gagner sur un objectif sans perdre sur l'autre.

:::: lab Démo | Le front des quatre familles | 5 min
```python title="Cellule 4 : qui domine qui ?"
def domine(a, b):
    """a domine b : au moins aussi bon sur les deux objectifs, et strictement meilleur sur l'un."""
    au_moins_aussi_bon = a["f1"] >= b["f1"] and a["taille_ko"] <= b["taille_ko"]
    strictement_meilleur = a["f1"] > b["f1"] or a["taille_ko"] < b["taille_ko"]
    return au_moins_aussi_bon and strictement_meilleur


front = [nom for nom in mesures
         if not any(domine(mesures[autre], mesures[nom]) for autre in mesures if autre != nom)]
print("front de Pareto :", front)
admissibles = [nom for nom in front if mesures[nom]["rappel"] >= 0.80]
print("sur le front, avec un rappel d'au moins 0,80 :", admissibles)
```

```plaintext title="Sortie attendue"
front de Pareto : ['forêt de départ', 'logistique']
sur le front, avec un rappel d'au moins 0,80 : ['logistique']
```

- **Deux modèles sur le front.** La régression logistique domine l'arbre et le boosting : elle est à la fois meilleure et plus légère. Elle ne domine pas la forêt de départ, à cause de ses deux millièmes de F1 en moins. Le front ne dit pas quel modèle choisir ; il dit lesquels **ne sont pas absurdes**.
- **La contrainte tranche.** La forêt de départ ne tient pas le rappel de 0,80 : il ne reste que la régression logistique.
::::

{#objectif-contrainte}
## Objectif ou contrainte ?

Tout ce qu'on souhaite n'est pas un objectif. La charte du jour 2 dit : **attraper au moins 8 retards sur 10**. Ce n'est pas « le plus de rappel possible », c'est un **seuil à respecter** : une **contrainte**. Un modèle qui ne la tient pas est **non admissible**, même s'il est léger et précis.

| | Objectif | Contrainte |
|---|---|---|
| Forme | « le plus possible » ou « le moins possible » | « au moins » ou « au plus » |
| Chez ColisVert | F1 le plus haut, taille la plus petite | rappel ≥ 0,80 ; taille ≤ 500 Ko pour le terminal du livreur |
| Effet | On cherche le front | On écarte les modèles non admissibles |

**Trois règles pour choisir sur le front**, à écrire **avant** de regarder les résultats, pour ne pas choisir ce qui arrange :

1. **Budget fixé** : le meilleur F1 parmi les modèles qui tiennent dans le budget (« au plus 150 Ko »).
2. **Qualité fixée** : le modèle le plus léger parmi ceux qui atteignent la qualité visée (« F1 au moins égal à celui du modèle actuel, à 0,005 près »).
3. **Le coude** : le point où le front s'aplatit, là où gagner encore un peu de qualité coûte beaucoup de poids. C'est la règle la plus intuitive, mais la plus subjective.

::: callout warn Pourquoi pas une note unique, comme « F1 − 0,001 × taille » ?
C'est tentant : une seule note, donc un seul gagnant. Mais le poids 0,001 est **arbitraire**, et il décide à votre place sans le dire : un autre poids donnerait un autre gagnant. Pire, une somme pondérée ne peut pas atteindre certains points du front, ceux qui se trouvent dans un « creux » de la courbe, quel que soit le poids choisi. On cherche donc d'abord le front, puis on applique une règle écrite et justifiée.
:::

{#optuna}
## Plusieurs objectifs avec Optuna 5

Au jour 2, l'étude Optuna avait **une** direction (`direction="maximize"`). Pour plusieurs objectifs, la fonction objectif renvoie **un tuple**, et l'étude reçoit **une liste** de directions :

```python title="Une étude à deux objectifs (extrait, ne pas exécuter)"
def objectif(essai):
    n_arbres = essai.suggest_int("n_estimators", 10, 300, log=True)
    f1, rappel, taille = entrainer_et_mesurer(n_arbres)   # écrite au TP 1
    essai.set_constraint("rappel", 0.80 - rappel)         # admissible si la valeur est ≤ 0
    return f1, taille                                     # deux valeurs, dans l'ordre des directions

etude = optuna.create_study(directions=["maximize", "minimize"],
                            sampler=optuna.samplers.TPESampler(seed=2026))
etude.optimize(objectif, n_trials=30)
etude.best_trials                                         # le front de Pareto des essais admissibles
```

Trois nouveautés d'Optuna 5, vérifiées dans l'image des TP (Optuna 5.0.0) :

- **`trial.set_constraint(nom, valeur)`** déclare une contrainte dans l'essai lui-même. L'essai est **admissible** quand toutes ses valeurs de contrainte sont **nulles ou négatives**. D'où l'écriture `0.80 - rappel` : elle est négative quand le rappel dépasse 0,80. Avant la version 5, on passait une fonction `constraints_func` à l'échantillonneur ; cette forme est désormais **dépréciée**.
- **`study.best_trials`** renvoie le front de Pareto, sans les essais non admissibles.
- **TPE devient l'échantillonneur par défaut** des études à plusieurs objectifs, à la place de NSGA-II. On le fixe quand même explicitement, avec une graine, pour que tout le monde obtienne les mêmes essais.

| Échantillonneur | Idée | Quand le préférer |
|---|---|---|
| **TPE** (*Tree-structured Parzen Estimator*) | Sépare les essais passés en bons et moins bons, et propose là où les bons sont fréquents (jour 2) | Peu d'essais (quelques dizaines), cas par défaut |
| **NSGA-II** | Algorithme génétique : une population d'essais qui se croisent et mutent, sélectionnés par rang de Pareto | Beaucoup d'essais (des centaines), essais en parallèle |

{#avance}
## Pour aller plus loin : comparer deux fronts

Ce bloc est pour les profils avancés ; rien ici n'est exigé dans l'évaluation.

Comment dire qu'une recherche a trouvé un **meilleur front** qu'une autre ? L'indicateur le plus utilisé est l'**hypervolume** : l'aire (en deux dimensions) de la région dominée par le front, mesurée à partir d'un point de référence choisi pire que tous les essais (par exemple F1 = 0 et taille = 25 Mo). Plus l'hypervolume est grand, mieux le front couvre l'espace des compromis. Optuna le calcule (`optuna.visualization.plot_hypervolume_history`), ce qui permet de tracer sa progression d'essai en essai et de savoir quand arrêter de chercher.

NSGA-II trie la population par **rangs** : le rang 1 est le front, le rang 2 le front des essais restants, etc. À rang égal, il préfère les essais **isolés** sur le front (distance d'encombrement), pour garder des compromis variés plutôt que dix variantes du même.

{#quiz}
## Quiz

```quiz
- q: Le modèle A a un F1 de 0,62 et pèse 500 Ko ; le modèle B a un F1 de 0,60 et pèse 800 Ko. Que peut-on dire ?
  options:
    - Rien, il faut une somme pondérée
    - A domine B - meilleur F1 et plus léger
    - B domine A
    - Ils sont tous deux sur le front
  answer: 1
  explain: A est meilleur sur les deux objectifs ; B n'a aucune raison d'être choisi.
- q: « Attraper au moins 8 retards sur 10 » est...
  options:
    - Un objectif à maximiser
    - Une contrainte - un seuil à respecter, qui rend un modèle admissible ou non
    - Une métrique de taille
    - Un hyperparamètre
  answer: 1
  explain: On ne cherche pas le rappel maximal, on exige un rappel minimal ; au-delà, on optimise les vrais objectifs.
- q: Avec Optuna 5, quand un essai est-il admissible ?
  options:
    - Quand ses valeurs de contrainte sont toutes nulles ou négatives
    - Quand ses valeurs de contrainte sont positives
    - Quand il est sur le front
    - Toujours
  answer: 0
  explain: D'où l'écriture 0.80 - rappel, négative dès que le rappel dépasse 0,80.
- q: Pourquoi écrire la règle de choix sur le front avant de lancer la recherche ?
  options:
    - Pour aller plus vite
    - Pour ne pas choisir après coup le compromis qui arrange, et pouvoir justifier le choix
    - Parce qu'Optuna l'exige
    - Ce n'est pas nécessaire
  answer: 1
  explain: C'est la même discipline que « ne jamais choisir sur le test » - décider de la règle avant de voir les résultats.
```
