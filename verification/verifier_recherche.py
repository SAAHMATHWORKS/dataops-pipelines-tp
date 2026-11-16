"""Vérifie les tableaux de la recherche d'hyperparamètres du jour 2 après-midi.

Même budget pour chaque méthode : 8 essais, score F1 sur la semaine de validation
(du 12 au 18 octobre). Les résultats de la grille et du tirage aléatoire sont
déterministes ; ceux d'Optuna (graine 42) sont vérifiés s'il est installé.
"""

import sys

import pandas as pd
from scipy.stats import loguniform
from sklearn.metrics import f1_score
from sklearn.model_selection import ParameterSampler

from pipeline.commun import CATEGORIELLES, CIBLE, NUMERIQUES, ajouter_jour_semaine
from pipeline.train import construire_modele

X_COLS = CATEGORIELLES + NUMERIQUES

livraisons = ajouter_jour_semaine(pd.read_csv("data/livraisons.csv"))
entrainement = livraisons[livraisons["date_expedition"] < "2026-10-12"]
validation = livraisons[(livraisons["date_expedition"] >= "2026-10-12") & (livraisons["date_expedition"] < "2026-10-19")]
assert (len(entrainement), len(validation)) == (3166, 639), (len(entrainement), len(validation))


def score(C, class_weight):
    modele = construire_modele(C, class_weight, 1000)
    modele.fit(entrainement[X_COLS], entrainement[CIBLE])
    return round(f1_score(validation[CIBLE], modele.predict(validation[X_COLS])), 3)


print("-- grille (4 valeurs de C x 2 class_weight)")
grille = [(C, cw, score(C, cw)) for C in [0.01, 0.1, 1.0, 10.0] for cw in [None, "balanced"]]
for ligne in grille:
    print(ligne)
attendu_grille = [
    (0.01, None, 0.545), (0.01, "balanced", 0.588),
    (0.1, None, 0.599), (0.1, "balanced", 0.634),
    (1.0, None, 0.597), (1.0, "balanced", 0.634),
    (10.0, None, 0.597), (10.0, "balanced", 0.632),
]
assert grille == attendu_grille, "la grille ne correspond plus au support"
print("grille conforme au support")

print("-- tirage aléatoire (8 essais, graine 42)")
tirages = list(ParameterSampler({"C": loguniform(1e-3, 1e2), "class_weight": [None, "balanced"]}, n_iter=8, random_state=42))
aleatoire = [(round(float(t["C"]), 4), t["class_weight"], score(t["C"], t["class_weight"])) for t in tirages]
for ligne in aleatoire:
    print(ligne)
# Relevé dans l'image des TP (x86-64) : deux valeurs diffèrent au millième sur d'autres
# machines (convergence de l'optimiseur sensible aux bibliothèques de calcul).
attendu_aleatoire = [
    (0.0746, None, 0.61), (0.0083, "balanced", 0.582), (0.9847, None, 0.597), (0.1695, None, 0.603),
    (0.002, "balanced", 0.523), (0.0466, "balanced", 0.613), (3.4703, "balanced", 0.634), (0.0019, "balanced", 0.523),
]
assert aleatoire == attendu_aleatoire, "le tirage aléatoire ne correspond plus au support"
print("tirage aléatoire conforme au support")

try:
    import optuna
except ImportError:
    print("optuna absent : vérification Optuna sautée (faite dans l'image des TP)")
    sys.exit(0)

print("-- Optuna (8 essais, TPE, graine 42, 4 essais d'exploration)")
optuna.logging.set_verbosity(optuna.logging.WARNING)


def objectif(essai):
    C = essai.suggest_float("C", 1e-3, 1e2, log=True)
    class_weight = essai.suggest_categorical("class_weight", [None, "balanced"])
    return score(C, class_weight)


etude = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=42, n_startup_trials=4))
etude.optimize(objectif, n_trials=8)
for essai in etude.trials:
    print((round(essai.params["C"], 4), essai.params["class_weight"], round(essai.value, 3)))
print("meilleur essai Optuna :", round(etude.best_params["C"], 4), etude.best_params["class_weight"], round(etude.best_value, 3))
print("RELEVER ces valeurs pour le support (bloc Optuna du jour 2 après-midi).")
