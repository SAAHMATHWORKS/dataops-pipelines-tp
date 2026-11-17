---
subtitle: >-
  Un F1 de 0,685 ne paie aucune facture. La valeur d'un modèle naît d'une décision qu'il change :
  ici, prévenir un client avant que son colis n'arrive en retard. On écrit ce que coûte chaque
  erreur, on cherche le seuil de décision qui rapporte le plus, et on vérifie que la conclusion
  résiste quand les hypothèses de coût changent.
objectives:
  - Décrire la chaîne qui va de la donnée au résultat métier, et où la valeur se perd
  - Écrire une matrice de coûts pour une décision prise à partir d'un modèle
  - Choisir le seuil de décision qui maximise l'économie, plutôt que 0,5 par défaut
  - Mesurer la sensibilité d'une conclusion aux hypothèses de coût
  - Expliquer pourquoi la pondération des classes déforme les probabilités
---

{#chaine}
## De la donnée au résultat : où la valeur se perd

La valeur suit une chaîne. Chaque maillon peut la laisser fuir :

| Maillon | Chez ColisVert | Fuite typique |
|---|---|---|
| **Donnée** | Le fichier des expéditions de la veille | Fichier en retard, colonnes manquantes (jours 1 et 3) |
| **Prédiction** | Probabilité de retard de chaque colis | Modèle dégradé par une dérive (jour 2) |
| **Décision** | Prévenir ou non le client | Seuil mal choisi : trop d'alertes inutiles, ou trop de retards manqués |
| **Action** | Le SMS part, l'entrepôt replanifie | Personne n'a branché la prédiction sur l'outil d'envoi |
| **Résultat** | Moins d'appels au service client, moins de clients perdus | Résultat jamais mesuré, donc valeur jamais démontrée |

Le Manifeste DataOps le résume dans son principe 2 : « Valoriser l'analytique qui fonctionne », c'est-à-dire mesurer la performance d'une équipe data à la qualité des **décisions** qu'elle rend possibles, pas au nombre de modèles livrés.

{#couts}
## La matrice de coûts de ColisVert

Le service client a chiffré trois coûts. Ce sont des **hypothèses** : on les écrit, on les date, on les fait valider par le métier, et on teste leur sensibilité.

| Situation | Coût | D'où vient ce chiffre |
|---|---|---|
| Un colis en retard **sans prévenir** le client | 15 € | Appel au service client, geste commercial, risque de perdre le client |
| Un colis en retard, client **prévenu** | 5 € | Le client a pu s'organiser : moins d'appels, pas de geste commercial |
| Une **action préventive** (SMS et replanification), retard ou pas | 2 € | Coût du SMS et du temps de l'entrepôt |

Ce qui donne, pour chaque colis où le modèle déclenche l'action :

- s'il était vraiment en retard (vrai positif) : 15 € évités, 5 + 2 = 7 € payés, soit **8 € gagnés** ;
- s'il était à l'heure (faux positif) : **2 € perdus**.

Un retard manqué (faux négatif) coûte 15 €, comme sans modèle : il ne gagne rien, il ne perd rien de plus. Le modèle rapporte donc **8 × vrais positifs − 2 × faux positifs**.

::: callout tip Le seuil théorique
Si les probabilités du modèle étaient fiables, il faudrait agir dès que la probabilité de retard × 10 € (le coût évité : 15 − 5) dépasse les 2 € de l'action, soit dès **p ≥ 0,2**. On va voir que ce n'est pas le cas ici, et pourquoi.
:::

{#seuil}
## Chercher le seuil qui rapporte le plus

:::: lab Démo | Le champion du jour 2, en euros | 12 min
**1. Le modèle et ses probabilités.** On réentraîne le champion du jour 2 (`C = 0.1`, `class_weight = "balanced"`) sur les huit semaines, directement depuis le générateur : la cellule ne dépend pas de l'état de votre dépôt.

```python title="Cellule 3 : les probabilités du champion"
from colisvert.donnees import generer_livraisons
from pipeline.commun import CATEGORIELLES, CIBLE, NUMERIQUES, ajouter_jour_semaine
from pipeline.train import construire_modele

colis = ajouter_jour_semaine(pd.DataFrame(generer_livraisons()))
train = colis[colis["date_expedition"] < "2026-10-19"]
test = colis[colis["date_expedition"] >= "2026-10-19"].copy()

modele = construire_modele(C=0.1, class_weight="balanced", max_iter=1000)
modele.fit(train[CATEGORIELLES + NUMERIQUES], train[CIBLE])
test["proba"] = modele.predict_proba(test[CATEGORIELLES + NUMERIQUES])[:, 1]
print(f"test : {len(test)} colis, dont {test[CIBLE].sum()} en retard ({test[CIBLE].mean():.1%})")
print(f"probabilité moyenne prédite : {test['proba'].mean():.1%}")
```

```plaintext title="Sortie attendue"
test : 1230 colis, dont 208 en retard (16.9%)
probabilité moyenne prédite : 29.2%
```

**Premier constat :** le modèle annonce en moyenne 29,2 % de risque de retard, alors que 16,9 % des colis sont réellement en retard. Ses probabilités sont **gonflées**. On y revient en fin de page.

**2. Le bilan à chaque seuil.**

```python title="Cellule 4 : l'économie selon le seuil"
COUTS = {"action": 2.0, "retard_prevenu": 5.0, "retard_surprise": 15.0}


def bilan(seuil, couts=COUTS):
    """Économie en euros par rapport à « pas de modèle », sur les colis de test."""
    agir = test["proba"] >= seuil
    retard = test[CIBLE] == 1
    vp, fp, fn = int((agir & retard).sum()), int((agir & ~retard).sum()), int((~agir & retard).sum())
    sans_modele = couts["retard_surprise"] * int(retard.sum())
    avec_modele = couts["action"] * (vp + fp) + couts["retard_prevenu"] * vp + couts["retard_surprise"] * fn
    return {"seuil": seuil, "actions": vp + fp, "vp": vp, "fp": fp, "fn": fn, "economie": sans_modele - avec_modele}


courbe = pd.DataFrame([bilan(round(s / 100, 2)) for s in range(5, 100, 5)])
print(courbe[courbe["seuil"].isin([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9])].to_string(index=False))
meilleur = courbe.loc[courbe["economie"].idxmax()]
par_colis = meilleur["economie"] / len(test)
print(f"meilleur seuil : {meilleur['seuil']:.2f}, économie {meilleur['economie']:.0f} € sur {len(test)} colis, "
      f"soit {par_colis:.2f} € par colis")
print(f"sur un an (environ {5035 / 56 * 365:,.0f} colis) : environ {par_colis * 5035 / 56 * 365:,.0f} €")
```

```plaintext title="Sortie attendue"
 seuil  actions  vp  fp  fn  economie
   0.1      674 208 466   0     732.0
   0.2      534 208 326   0    1012.0
   0.3      457 208 249   0    1166.0
   0.4      388 196 192  12    1184.0
   0.5      326 183 143  25    1178.0
   0.6      270 168 102  40    1140.0
   0.7      203 148  55  60    1074.0
   0.8      158 120  38  88     884.0
   0.9       95  75  20 133     560.0
meilleur seuil : 0.40, économie 1184 € sur 1230 colis, soit 0.96 € par colis
sur un an (environ 32,817 colis) : environ 31,590 €
```
::::

**Lire la courbe.**

- **Avec un seuil bas** (0,1), on prévient les clients de tous les retards (aucun faux négatif), mais on envoie 466 SMS inutiles : l'économie tombe à 732 €.
- **Avec un seuil haut** (0,9), presque chaque SMS est justifié, mais on rate 133 retards sur 208 : 560 € seulement.
- **Le maximum est vers 0,4** : 1 184 € économisés sur deux semaines de colis, soit environ **0,96 € par colis**, et **environ 31 600 € par an** au volume actuel. C'est ce chiffre, et non le F1, qu'on présente au comité de direction.
- La courbe est **plate** entre 0,3 et 0,6 (de 1 140 à 1 184 €) : le choix exact du seuil compte peu. Le seuil théorique de 0,2 coûte en revanche 172 € par rapport au meilleur, parce que les probabilités sont gonflées.

{#sensibilite}
## Et si les hypothèses sont fausses ?

Les 15 € du retard non prévenu sont une estimation. Avant de présenter un chiffre au comité de direction, on vérifie que la **décision** (déployer ou non, avec quel seuil) ne change pas quand l'hypothèse bouge raisonnablement.

:::: lab Démo | Analyse de sensibilité | 5 min
```python title="Cellule 5 : trois hypothèses pour le retard non prévenu"
for cout_retard in [8.0, 15.0, 25.0]:
    couts = {**COUTS, "retard_surprise": cout_retard}
    essai = pd.DataFrame([bilan(round(s / 100, 2), couts) for s in range(5, 100, 5)])
    top = essai.loc[essai["economie"].idxmax()]
    a_05 = essai.loc[essai["seuil"] == 0.5, "economie"].iloc[0]
    print(f"retard non prévenu à {cout_retard:>4.0f} € : meilleur seuil {top['seuil']:.2f}, "
          f"économie {top['economie']:>6.0f} € (au seuil 0,5 : {a_05:>6.0f} €)")
```

```plaintext title="Sortie attendue"
retard non prévenu à    8 € : meilleur seuil 0.85, économie     47 € (au seuil 0,5 :   -103 €)
retard non prévenu à   15 € : meilleur seuil 0.40, économie   1184 € (au seuil 0,5 :   1178 €)
retard non prévenu à   25 € : meilleur seuil 0.30, économie   3246 € (au seuil 0,5 :   3008 €)
```
::::

**La conclusion dépend fortement d'une seule hypothèse.**

- Si un retard non prévenu coûte **25 €**, le projet rapporte près de trois fois plus, et le meilleur seuil descend à 0,3 : on a intérêt à prévenir plus largement.
- S'il ne coûte que **8 €**, le gain d'un vrai positif tombe à 1 € (8 − 5 − 2), et le modèle ne rapporte presque rien (47 € au mieux). Au seuil de 0,5, il **fait perdre** 103 € : les SMS inutiles coûtent plus que les retards évités.

Avant de déployer l'alerte SMS, l'action utile n'est donc pas d'améliorer le modèle, mais de **mesurer le vrai coût d'un retard non prévenu** (appels, gestes commerciaux, clients perdus). C'est une donnée que le service client peut produire en quelques semaines.

{#calibration}
## Pour aller plus loin : des probabilités fiables

Le seuil théorique de 0,2 suppose que « probabilité 0,3 » signifie « 30 % de ces colis arrivent en retard ». C'est la **calibration** d'un modèle. La pondération `class_weight="balanced"`, qui a permis de franchir la charte au jour 2, la casse délibérément : elle fait comme si les retards étaient aussi nombreux que les colis à l'heure, et gonfle toutes les probabilités.

Deux façons de faire :

1. **Garder le modèle et chercher le seuil sur des données** (ce qu'on vient de faire), sur un jeu de validation distinct du test final pour ne pas surestimer l'économie.
2. **Recalibrer** le modèle (`CalibratedClassifierCV` de scikit-learn, méthode isotonique ou sigmoïde), puis appliquer le seuil théorique. C'est la méthode à préférer quand les coûts changent souvent : il suffit de recalculer le seuil, sans rechercher.

::: callout info Et les agents IA ?
Ce raisonnement en euros est exactement ce qu'un agent IA ne sait pas inventer : il peut calculer une courbe d'économie si on lui donne la matrice de coûts, mais les coûts eux-mêmes sont des décisions métier. Au jour 5, on verra où un agent peut aider (préparer l'analyse, rédiger la note au comité) et où il ne doit pas décider.
:::

{#quiz}
## Quiz

```quiz
- q: Selon la matrice de ColisVert, que rapporte un vrai positif (retard prédit, client prévenu) par rapport à l'absence de modèle ?
  options:
    - 15 €
    - 8 € - 15 € évités, 5 € de retard prévenu et 2 € d'action payés
    - 2 €
    - 0 €
  answer: 1
  explain: 15 − (5 + 2) = 8 €. Un faux positif coûte 2 €, un faux négatif ne change rien par rapport à l'absence de modèle.
- q: Pourquoi le meilleur seuil n'est-il pas 0,5 ?
  options:
    - Parce que 0,5 est réservé aux modèles calibrés
    - Parce que le bon seuil dépend des coûts des erreurs, pas d'une convention
    - Parce que scikit-learn l'interdit
    - Par hasard
  answer: 1
  explain: 0,5 suppose qu'un faux positif et un faux négatif coûtent pareil, ce qui est rarement vrai.
- q: Pourquoi le seuil théorique de 0,2 ne s'applique-t-il pas tel quel au champion ?
  options:
    - Parce que le calcul est faux
    - Parce que class_weight="balanced" gonfle les probabilités - le modèle n'est pas calibré
    - Parce que le test est trop petit
    - Parce que les coûts sont en euros
  answer: 1
  explain: Le seuil théorique suppose des probabilités fiables. Il faut recalibrer, ou chercher le seuil sur des données.
- q: Que vérifie une analyse de sensibilité ?
  options:
    - Que le modèle est précis
    - Que la décision recommandée tient quand les hypothèses de coût varient raisonnablement
    - Que les données sont propres
    - Que le seuil est 0,5
  answer: 1
  explain: Un chiffre d'économie dépend d'hypothèses ; la décision doit rester la même dans la plage plausible.
```
