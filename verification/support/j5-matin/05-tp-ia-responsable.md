---
subtitle: >-
  Un client demande pourquoi il a reçu un SMS de retard. Un auditeur demande sur quoi repose le
  modèle. Un responsable d'entrepôt demande si ses clients sont aussi bien protégés que ceux des
  autres. Trois questions, trois outils : SHAP pour l'explication globale et locale, LIME pour une
  approximation locale, un modèle transparent avec interpretML. Puis une vérification d'équité, et
  la fiche du modèle, enregistrée dans MLflow.
objectives:
  - Expliquer ce que mesure une valeur de Shapley, et la lire pour tout le modèle et pour un colis
  - Comparer SHAP et LIME, et savoir quand se méfier d'une explication locale
  - Entraîner un modèle transparent (EBM) avec interpretML et le comparer au champion
  - Vérifier l'équité d'un modèle entre groupes avec la même mesure que l'engagement métier
  - Enregistrer explications, mesures d'équité et fiche du modèle dans MLflow
---

{#pourquoi}
## Pourquoi expliquer un modèle

Trois publics, trois besoins :

| Qui | Question | Type d'explication |
|---|---|---|
| **Le client** | « Pourquoi moi ? » | **Locale** : ce qui a compté pour **ce** colis |
| **L'auditeur, le propriétaire** | « Sur quoi repose le modèle ? Est-il raisonnable ? » | **Globale** : ce qui compte en moyenne |
| **Le responsable d'entrepôt** | « Mes clients sont-ils traités comme les autres ? » | **Équité** : les performances par groupe |

Le cadre légal arrive cet après-midi : l'AI Act européen impose de la transparence et une documentation technique aux systèmes d'IA à haut risque. Le RGPD encadre les décisions automatisées qui affectent une personne. L'alerte SMS de ColisVert n'est pas un système à haut risque, mais les bonnes pratiques sont les mêmes, et elles coûtent peu quand on les prend tôt.

{#shap}
## SHAP : partager la prédiction entre les variables

**L'analogie de l'addition au restaurant.** Quatre amis partagent une note. Comment savoir ce que chacun « doit » ? La valeur de Shapley (Lloyd Shapley, prix Nobel d'économie 2012) répond équitablement. On imagine toutes les façons d'arriver un par un à table, et on fait la moyenne de ce que chaque arrivée ajoute à la note. SHAP fait la même chose avec les variables. La **valeur de base** est la prédiction moyenne ; chaque variable ajoute ou retire sa part ; et **la somme des parts redonne exactement la prédiction du colis**.

Pour un modèle **linéaire** comme notre régression logistique, et des variables supposées indépendantes, le calcul devient simple. La part d'une variable vaut son **coefficient × (sa valeur − sa valeur moyenne)**, en logit (le logarithme de la cote, avant la transformation en probabilité). `shap.LinearExplainer` le calcule exactement, en une fraction de seconde.

:::: lab Étape 1 | SHAP, pour tout le modèle | 8 min
Le modèle travaille sur 21 colonnes encodées (une par modalité : `entrepot_Lille`, `entrepot_Lyon`…). Pour parler métier, on **regroupe** les parts par variable d'origine : la somme des parts des 4 colonnes d'entrepôt est la part de « l'entrepôt ».

```python title="Cellule 11 : le champion et son explication globale"
import numpy as np
import shap

champion = construire_modele(0.1, "balanced", 1000).fit(train[X_COLS], train[CIBLE])
preparation, regression = champion[:-1], champion[-1]
colonnes = preparation.get_feature_names_out()
origine = [c.split("__")[1].rsplit("_", 1)[0] if c.startswith("categories__") else c.split("__")[1]
           for c in colonnes]
fond = preparation.transform(train[X_COLS])
explicateur = shap.LinearExplainer(regression, shap.maskers.Independent(fond, max_samples=len(fond)))

def parts_par_variable(lignes):
    """Valeurs SHAP regroupées par variable d'origine (une colonne par variable)."""
    valeurs = explicateur(preparation.transform(lignes[X_COLS])).values
    return pd.DataFrame(valeurs, columns=colonnes).T.groupby(origine).sum().T

importance = parts_par_variable(test).abs().mean().sort_values(ascending=False)
print("importance moyenne (|part SHAP| en logit, sur les 1230 colis du test) :")
print(importance.round(3).to_string())
```

```plaintext title="Sortie attendue"
importance moyenne (|part SHAP| en logit, sur les 1230 colis du test) :
delai_promis_h    3.847
distance_km       1.920
meteo             1.071
entrepot          0.763
creneau           0.536
poids_kg          0.453
jour_semaine      0.048
client            0.015
```

- **Le délai promis domine** (3,85), devant la **distance** (1,92). C'est cohérent avec la règle de ColisVert : jusqu'à 150 km, on promet 24 h, au-delà 48 h. Un colis loin dans la tranche des 24 h est très souvent en retard ; un colis juste au-dessus de 150 km, presque jamais.
- **La météo, l'entrepôt, le créneau et le poids** viennent ensuite.
- **Le jour de la semaine et le type de client ne pèsent presque rien** (0,048 et 0,015). Ce sont des candidats à retirer du modèle : moins de données à collecter, c'est le principe de **minimisation**, et un modèle plus simple à expliquer.
::::

:::: lab Étape 2 | SHAP, pour un colis | 7 min
Le premier colis de décembre, `DEC00001`, a reçu une alerte. Pourquoi ?

```python title="Cellule 12 : pourquoi ce colis ?"
colis = decembre[decembre["id_colis"] == "DEC00001"]
print(colis[X_COLS].to_string(index=False))
parts = parts_par_variable(colis).iloc[0].sort_values(key=abs, ascending=False)
base = float(np.ravel(explicateur.expected_value)[0])
logit = base + parts.sum()
print(f"valeur de base (logit moyen) : {base:+.3f}")
for variable, part in parts.items():
    print(f"  {variable:<15} {part:+.3f}")
print(f"logit du colis : {logit:+.3f}  →  probabilité {1 / (1 + np.exp(-logit)):.3f} "
      f"(modèle : {champion.predict_proba(colis[X_COLS])[0, 1]:.3f})")
```

```plaintext title="Sortie attendue"
entrepot      client creneau meteo jour_semaine  distance_km  poids_kg  delai_promis_h
   Lille particulier    soir pluie        lundi           19       9.7              24
valeur de base (logit moyen) : -1.791
  delai_promis_h  +3.853
  distance_km     -3.362
  meteo           +1.849
  entrepot        +1.263
  creneau         +0.786
  poids_kg        -0.333
  jour_semaine    +0.034
  client          +0.010
logit du colis : +2.308  →  probabilité 0.910 (modèle : 0.910)
```

- **La valeur de base** (-1,791 en logit, soit environ 14 % de probabilité) est le point de départ commun à tous les colis.
- **Le délai promis de 24 h** pousse fortement vers le retard (+3,853). Mais **la distance très courte** (19 km) tire dans l'autre sens (-3,362) : un colis proche est rarement en retard.
- **La pluie** (+1,849), **Lille** (+1,263) et **le soir** (+0,786) font pencher la balance.
- **L'addition est exacte** : -1,791 + la somme des parts = +2,308, soit une probabilité de 0,910, celle que donne le modèle. C'est la propriété qui rend SHAP fiable pour un audit.

**Ce qu'on dit au client :** « Votre colis part de notre entrepôt de Lille, qui est très chargé, un jour de pluie, pour une livraison le soir : ces conditions rendent un retard probable. » On ne lui parle pas de logit, et on ne lui cite pas les variables qui ont joué en sa faveur.
::::

{#lime}
## LIME : une approximation locale

**LIME** (*Local Interpretable Model-agnostic Explanations*) part d'une autre idée. On crée des milliers de colis **voisins** du colis à expliquer, en modifiant ses variables au hasard, puis on demande au modèle de les prédire. On ajuste enfin, sur ce voisinage, un petit modèle linéaire facile à lire. LIME marche avec n'importe quel modèle, mais son explication dépend du tirage et de la façon de définir le voisinage.

:::: lab Étape 3 | LIME sur le même colis | 7 min
LIME travaille sur des nombres : on code chaque catégorie par un entier, et la fonction `predire` décode avant d'appeler le champion.

```python title="Cellule 13 : LIME"
from lime.lime_tabular import LimeTabularExplainer

modalites = {c: sorted(train[c].astype(str).unique()) for c in CATEGORIELLES}

def encoder(df):
    codes = df[X_COLS].copy()
    for c in CATEGORIELLES:
        codes[c] = codes[c].astype(str).map({m: i for i, m in enumerate(modalites[c])})
    return codes.to_numpy(dtype=float)

def predire(tableau):
    df = pd.DataFrame(tableau, columns=X_COLS)
    for c in CATEGORIELLES:
        df[c] = [modalites[c][int(round(v))] for v in df[c]]
    return champion.predict_proba(df)

lime_explicateur = LimeTabularExplainer(
    encoder(train), feature_names=X_COLS, categorical_features=list(range(len(CATEGORIELLES))),
    categorical_names={i: modalites[c] for i, c in enumerate(CATEGORIELLES)},
    class_names=["à l'heure", "en retard"], random_state=2026)
explication = lime_explicateur.explain_instance(encoder(colis)[0], predire, num_features=5, num_samples=2000)
for condition, poids in explication.as_list():
    print(f"  {condition:<28} {poids:+.3f}")
print(f"qualité de l'approximation locale (R²) : {explication.score:.2f}")
```

```plaintext title="Sortie attendue"
  delai_promis_h <= 24.00      +0.954
  meteo=pluie                  +0.038
  entrepot=Lille               +0.029
  distance_km <= 78.00         -0.029
  creneau=soir                 +0.015
qualité de l'approximation locale (R²) : 0.98
```

- **LIME et SHAP s'accordent sur l'essentiel** : le délai promis de 24 h est la première raison de l'alerte, la pluie, Lille et le soir suivent.
- **Les valeurs ne se comparent pas.** LIME travaille en **probabilité**, sur un voisinage tiré au hasard ; SHAP travaille en **logit**, de façon exacte. Ici, la probabilité est déjà de 0,91, une zone où la courbe sigmoïde est presque plate : chaque variable y bouge très peu la probabilité, d'où les petits poids de LIME.
- **Le R² local de 0,98** dit que le petit modèle de LIME imite bien le champion autour de ce colis. Un R² faible serait un signal d'alarme.
- **Comparez les classements, pas les chiffres**, et préférez l'explication exacte quand le modèle le permet.
::::

{#ebm}
## Un modèle transparent par construction : interpretML

Plutôt qu'expliquer après coup un modèle opaque, on peut choisir un modèle **lisible par construction**. L'**EBM** (*Explainable Boosting Machine*) de la bibliothèque interpretML (Microsoft) est un modèle additif. Sa prédiction est une somme de fonctions d'une variable (et de quelques paires de variables), chacune apprise par boosting et **affichable en graphique**. On lit directement l'effet de la distance, du délai promis ou de la pluie.

:::: lab Étape 4 | EBM contre le champion | 8 min
L'entraînement prend une quinzaine de secondes. D'une machine à l'autre, les résultats de l'EBM peuvent différer au troisième chiffre (vérifié sur deux machines de la vérification automatique), même avec la même graine : on n'affiche que deux chiffres pour les mesures, un pour l'importance des termes.

```python title="Cellule 14 : un modèle transparent, aussi bon ?"
from interpret.glassbox import ExplainableBoostingClassifier
from sklearn.metrics import f1_score, precision_score, recall_score

ebm = ExplainableBoostingClassifier(random_state=2026).fit(train[X_COLS], train[CIBLE])
proba_ebm = ebm.predict_proba(test[X_COLS])[:, 1]
proba_lr = champion.predict_proba(test[X_COLS])[:, 1]
for nom, proba in [("champion (logistique)", proba_lr), ("EBM (interpretML)", proba_ebm)]:
    for seuil in [0.5, 0.4]:
        decision = (proba >= seuil).astype(int)
        print(f"{nom:<22} seuil {seuil} : précision {precision_score(test[CIBLE], decision):.2f}  "
              f"rappel {recall_score(test[CIBLE], decision):.2f}  F1 {f1_score(test[CIBLE], decision):.2f}")
termes = ebm.explain_global().data()
print("termes les plus importants de l'EBM :")
for nom, score in sorted(zip(termes["names"], termes["scores"]), key=lambda t: -t[1])[:6]:
    print(f"  {nom:<24} {score:.1f}")
```

```plaintext title="Sortie attendue"
champion (logistique)  seuil 0.5 : précision 0.56  rappel 0.88  F1 0.69
champion (logistique)  seuil 0.4 : précision 0.51  rappel 0.94  F1 0.66
EBM (interpretML)      seuil 0.5 : précision 0.76  rappel 0.60  F1 0.67
EBM (interpretML)      seuil 0.4 : précision 0.72  rappel 0.67  F1 0.70
termes les plus importants de l'EBM :
  delai_promis_h           1.8
  meteo                    1.3
  distance_km              1.1
  entrepot                 0.9
  creneau                  0.7
  poids_kg                 0.5
```

- **L'EBM est compétitif** : au seuil de 0,4, son F1 (0,70) dépasse celui du champion (0,69 au seuil de 0,5). Sa précision est bien plus haute (0,76 au seuil de 0,5, contre 0,56).
- **Mais il ne tient pas l'engagement de rappel**, ni à 0,5 (0,60) ni à 0,4 (0,67). Pour atteindre 0,80, il faudrait descendre son seuil, puis vérifier sa précision. C'est un vrai challenger, à évaluer comme au jour 2, avec la règle de promotion.
- **Ses termes se lisent directement**, dans le même ordre que les importances SHAP du champion : délai promis, météo, distance, entrepôt, créneau, poids. Il a aussi appris quelques petites interactions (par exemple « météo × délai promis »), qu'une régression logistique ne voit pas.
- **Le choix d'aujourd'hui** : le champion reste en production, parce qu'il tient l'engagement. Mais on sait désormais qu'on peut avoir un modèle **transparent par construction** sans perdre en qualité.
::::

{#equite}
## L'équité entre entrepôts

L'engagement de la charte est d'attraper **au moins 8 retards sur 10**. Un modèle peut le tenir **en moyenne** et le manquer pour un groupe de clients. Ici, les groupes sont les entrepôts. Ce ne sont pas des caractéristiques protégées par la loi, mais la question est la même que pour l'âge ou le sexe : le modèle protège-t-il tout le monde de la même façon ?

:::: lab Étape 5 | Le rappel, entrepôt par entrepôt | 5 min
```python title="Cellule 15 : l'engagement tient-il partout ?"
decision = champion.predict(test[X_COLS])
equite = (test.assign(alerte=decision).groupby("entrepot")
          .apply(lambda g: pd.Series({
              "colis": len(g), "taux_retard": g[CIBLE].mean(),
              "rappel": recall_score(g[CIBLE], g["alerte"]), "precision": precision_score(g[CIBLE], g["alerte"]),
              "taux_alerte": g["alerte"].mean()}), include_groups=False)
          .round(3))
print(equite.to_string())
print("entrepôts sous l'engagement de rappel (0,80) :", list(equite.index[equite["rappel"] < 0.80]))
```

```plaintext title="Sortie attendue"
          colis  taux_retard  rappel  precision  taux_alerte
entrepot
Lille     354.0        0.266   0.926      0.604        0.407
Lyon      377.0        0.133   0.760      0.559        0.180
Nantes    241.0        0.116   0.857      0.533        0.187
Toulouse  258.0        0.140   0.944      0.493        0.267
entrepôts sous l'engagement de rappel (0,80) : ['Lyon']
```

- **En moyenne, l'engagement tient** (rappel de 0,880 sur le test). **Mais pas à Lyon** : 0,760. Les clients lyonnais en retard sont moins souvent prévenus que les autres.
- **Toulouse manque l'autre seuil de la charte** : une précision de 0,493, sous 0,50. Un SMS sur deux y est une fausse alerte.
- **Pourquoi ?** Lyon a peu de retards (13,3 %, contre 26,6 % à Lille). Un seuil unique, réglé sur l'ensemble des colis, n'est pas bien placé pour Lyon.
- **Quoi faire ?** D'abord le **documenter** comme limite du modèle (Cellule 16), puis chercher la cause avant de choisir un remède. Les pistes : un seuil par entrepôt, une variable qui manque pour Lyon, ou plus de données. Un seuil par entrepôt améliore l'équité du rappel, mais traite les clients différemment selon leur ville : c'est une **décision de gouvernance**, à prendre par le propriétaire, pas seulement par l'équipe data.
::::

{#fiche}
## La fiche du modèle, dans MLflow

Une **fiche de modèle** (*model card*, Mitchell et al., 2019) documente un modèle comme la fiche du produit de données documente une table. On y met l'usage prévu, les données, les performances **par groupe**, les limites connues et le responsable. On l'enregistre avec les explications, dans le même run MLflow : l'audit retrouve tout au même endroit.

:::: lab Étape 6 | Explications, équité et fiche dans un run | 5 min
```python title="Cellule 16 : tout dans MLflow"
import os

import mlflow

os.environ["MLFLOW_SUPPRESS_PRINTING_URL_TO_STDOUT"] = "true"
mlflow.set_experiment("j5-ia-responsable")
fiche = {
    "modele": "Régression logistique C=0.1, class_weight=balanced (champion du jour 2)",
    "usage_prevu": "Prévenir par SMS les clients dont le colis risque d'arriver en retard",
    "usage_exclu": "Toute décision sur une personne (tarif, refus de livraison)",
    "donnees": "Livraisons du 7/09 au 18/10/2026, 3805 colis ; test du 19/10 au 1/11, 1230 colis",
    "performances_test": {"precision": 0.561, "rappel": 0.880, "f1": 0.685},
    "limites": ["Rappel de Lyon sous l'engagement de 0,80 (0.760)",
                "Précision de Toulouse sous la charte de 0,50 (0.493)",
                "Données de décembre en dérive (jour 2)"],
    "explications": "SHAP (global et local), LIME, comparaison avec un EBM interpretML",
    "proprietaire": "Responsable des opérations",
}
with mlflow.start_run(run_name="explications-champion") as run:
    mlflow.log_metrics({"f1_champion": f1_score(test[CIBLE], decision),
                        "f1_ebm": f1_score(test[CIBLE], (proba_ebm >= 0.5).astype(int)),
                        "rappel_min_entrepot": float(equite["rappel"].min())})
    mlflow.log_table(importance.rename_axis("variable").reset_index(name="importance"), "shap_importance.json")
    mlflow.log_table(equite.reset_index(), "equite_par_entrepot.json")
    mlflow.log_dict(fiche, "fiche_modele.json")
artefacts = [a.path for a in mlflow.MlflowClient().list_artifacts(run.info.run_id)]
print("artefacts du run :", sorted(artefacts))
```

```plaintext title="Sortie attendue"
artefacts du run : ['equite_par_entrepot.json', 'fiche_modele.json', 'shap_importance.json']
```

Dans l'interface (http://localhost:5000, expérience `j5-ia-responsable`), les artefacts du run contiennent la fiche et les deux tables. À chaque nouvelle version du modèle, un nouveau run avec les mêmes artefacts permet de suivre l'équité dans le temps.
::::

{#avance}
## Pour aller plus loin : les limites des explications

Ce bloc est pour les profils avancés ; rien ici n'est exigé dans l'évaluation.

- **Expliquer n'est pas justifier.** SHAP dit ce qui a compté pour le **modèle**, pas ce qui cause le retard dans le monde réel. Une variable corrélée à la vraie cause peut recevoir sa part.
- **Les variables corrélées.** SHAP « indépendant » et LIME modifient une variable en gardant les autres : ils peuvent fabriquer des colis impossibles (200 km avec un délai promis de 24 h). Les variantes conditionnelles de SHAP corrigent en partie ce biais, au prix de calculs plus lourds.
- **L'instabilité de LIME.** Deux tirages peuvent changer l'ordre des variables de faible poids. Fixer la graine rend le résultat reproductible, pas plus vrai. Un R² local faible signale une approximation à ne pas croire.
- **L'équité a plusieurs définitions**, souvent incompatibles entre elles : même taux d'alerte pour chaque groupe (parité démographique), même rappel (égalité des chances), même précision. Il faut choisir celle qui correspond à l'engagement. Ici, c'est le rappel, parce que c'est la promesse faite aux clients.

{#quiz}
## Quiz

```quiz
- q: Que vaut la somme de la valeur de base et des parts SHAP d'un colis ?
  options:
    - Zéro
    - Exactement la prédiction du modèle pour ce colis (ici, en logit)
    - La moyenne des prédictions
    - L'importance globale
  answer: 1
  explain: C'est la propriété d'additivité des valeurs de Shapley ; la Cellule 12 la vérifie.
- q: Pourquoi LIME peut-il donner deux explications un peu différentes du même colis ?
  options:
    - Parce que le modèle change
    - Parce qu'il tire au hasard les colis voisins sur lesquels il ajuste son petit modèle
    - Parce que SHAP intervient
    - Il donne toujours la même
  answer: 1
  explain: La graine rend le tirage reproductible, mais l'explication reste une approximation locale.
- q: Qu'est-ce qui distingue un EBM d'une forêt aléatoire, pour l'explication ?
  options:
    - Il est plus lent
    - Il est additif - chaque variable a sa propre fonction, lisible en graphique, sans outil d'explication après coup
    - Il n'utilise pas de boosting
    - Il ne fonctionne qu'avec des nombres
  answer: 1
  explain: C'est un modèle « boîte de verre » ; la forêt doit être expliquée de l'extérieur.
- q: Le modèle tient l'engagement de rappel en moyenne. Pourquoi vérifier par entrepôt ?
  options:
    - Pour la forme
    - Parce qu'une moyenne peut cacher un groupe pour lequel l'engagement n'est pas tenu
    - Parce que la loi l'impose pour les entrepôts
    - Pour comparer les responsables
  answer: 1
  explain: Ici, Lyon est sous 0,80 ; les clients lyonnais sont moins bien prévenus que les autres.
```
