---
subtitle: >-
  Le comité de direction de ColisVert se réunit lundi. Il veut savoir quoi faire ensuite, combien
  rapporterait l'alerte SMS avec les nouveaux chiffres du service client, si la qualité des données
  de décembre est sous contrôle, et si l'équipe d'en face livre mieux que la vôtre. Quatre réponses,
  chiffrées.
objectives:
  - Prioriser un carnet avec WSJF
  - Choisir un seuil de décision rentable avec une nouvelle matrice de coûts
  - Détecter une dérive avec une carte I-MR et dater la première alerte
  - Calculer les indicateurs DORA d'un historique de déploiements
# Barème : 14 points pour les étapes (indiqués sur chaque étape) + 6 points pour le QCM
quiz_points: 6
---

{#consignes}
## Consignes

- **Durée :** 30 minutes, en autonomie. Le formateur passe voir chacun.
- **Où :** un notebook neuf `j4-matin-evaluation.ipynb` (dossier `notebooks`). Commencez par `import pandas as pd`.
- **Validation :** chaque étape se termine par une **preuve** : collez la sortie demandée et cliquez sur « Envoyer ma preuve ».
- **Barème :** 14 points pour les 4 étapes, 6 points pour le QCM final (une seule tentative par question).
- Les corrections sont là si vous bloquez, mais essayez d'abord.

::: widget task-progress
:::

{#prioriser}
## Prioriser

:::: task Étape 1 | Le carnet du trimestre | 5 min | 3 pts
Classez ces cinq éléments par WSJF décroissant (coût du retard = valeur + urgence + risque ; WSJF = coût du retard ÷ taille, arrondi à 2 décimales) et affichez le tableau trié.

| Élément | Valeur | Urgence | Risque | Taille |
|---|---|---|---|---|
| Carte de contrôle du poids moyen | 3 | 5 | 8 | 2 |
| Alerte SMS, entrepôt de Lille seulement | 8 | 8 | 3 | 2 |
| Réévaluer le champion sur les nouvelles données | 5 | 5 | 8 | 3 |
| Tableau de bord du service client | 5 | 3 | 1 | 5 |
| Recalibrer les probabilités du modèle | 3 | 2 | 5 | 3 |

::: proof Collez le tableau trié
:::

::: hint
Reprenez la Cellule 1 du matin. `sort_values("wsjf", ascending=False)`. Deux éléments peuvent avoir le même WSJF : l'ordre entre eux n'est pas noté.
:::

::: solution
```python title="Évaluation : WSJF"
import pandas as pd

carnet = pd.DataFrame(
    [
        ("Carte de contrôle du poids moyen", 3, 5, 8, 2),
        ("Alerte SMS, entrepôt de Lille seulement", 8, 8, 3, 2),
        ("Réévaluer le champion sur les nouvelles données", 5, 5, 8, 3),
        ("Tableau de bord du service client", 5, 3, 1, 5),
        ("Recalibrer les probabilités du modèle", 3, 2, 5, 3),
    ],
    columns=["element", "valeur", "urgence", "risque", "taille"],
)
carnet["cout_du_retard"] = carnet[["valeur", "urgence", "risque"]].sum(axis=1)
carnet["wsjf"] = (carnet["cout_du_retard"] / carnet["taille"]).round(2)
print(carnet.sort_values("wsjf", ascending=False)[["element", "cout_du_retard", "taille", "wsjf"]].to_string(index=False))
```

```plaintext title="Sortie attendue"
                                        element  cout_du_retard  taille  wsjf
        Alerte SMS, entrepôt de Lille seulement              19       2  9.50
               Carte de contrôle du poids moyen              16       2  8.00
Réévaluer le champion sur les nouvelles données              18       3  6.00
          Recalibrer les probabilités du modèle              10       3  3.33
              Tableau de bord du service client               9       5  1.80
```

Découper l'alerte SMS (un seul entrepôt) l'a fait passer de la 4e place du matin à la 1re : c'est l'effet du dénominateur de WSJF.
:::
::::

{#seuil}
## Le seuil rentable

:::: task Étape 2 | Les nouveaux chiffres du service client | 9 min | 4 pts
Le service client a mesuré ses coûts : **20 €** pour un retard non prévenu, **5 €** pour un retard prévenu, **3 €** pour une action préventive (le SMS passe par un prestataire plus cher). Réentraînez le champion du jour 2 sur les 8 semaines (`C = 0.1`, `class_weight="balanced"`, découpe au 19 octobre), puis :

1. calculez l'économie par rapport à « pas de modèle » pour les seuils de 0,05 à 0,95 par pas de 0,05 ;
2. affichez le meilleur seuil, son économie sur les colis de test, et l'économie au seuil de 0,5.

::: proof Collez les deux lignes : meilleur seuil et seuil 0,5
:::

::: hint
Reprenez les Cellules 3 et 4. Un vrai positif rapporte maintenant 20 − 5 − 3 = 12 €, un faux positif coûte 3 €. Utilisez `round(s / 100, 2)` pour les seuils, sinon 0,15000000000000002 ne sera jamais égal à 0,15.
:::

::: solution
```python title="Évaluation : le seuil rentable"
from colisvert.donnees import generer_livraisons
from pipeline.commun import CATEGORIELLES, CIBLE, NUMERIQUES, ajouter_jour_semaine
from pipeline.train import construire_modele

colis = ajouter_jour_semaine(pd.DataFrame(generer_livraisons()))
train = colis[colis["date_expedition"] < "2026-10-19"]
test = colis[colis["date_expedition"] >= "2026-10-19"].copy()
modele = construire_modele(C=0.1, class_weight="balanced", max_iter=1000)
modele.fit(train[CATEGORIELLES + NUMERIQUES], train[CIBLE])
test["proba"] = modele.predict_proba(test[CATEGORIELLES + NUMERIQUES])[:, 1]


def economie(seuil, action=3.0, prevenu=5.0, surprise=20.0):
    agir, retard = test["proba"] >= seuil, test[CIBLE] == 1
    vp, fp = int((agir & retard).sum()), int((agir & ~retard).sum())
    return vp * (surprise - prevenu - action) - fp * action


resultats = {round(s / 100, 2): economie(round(s / 100, 2)) for s in range(5, 100, 5)}
meilleur = max(resultats, key=resultats.get)
print(f"meilleur seuil : {meilleur:.2f}, économie {resultats[meilleur]:.0f} € sur {len(test)} colis")
print(f"seuil 0,5 : économie {resultats[0.5]:.0f} €")
```

```plaintext title="Sortie attendue"
meilleur seuil : 0.40, économie 1776 € sur 1230 colis
seuil 0,5 : économie 1767 €
```

Avec un vrai positif à 12 € et un faux positif à 3 €, le meilleur seuil reste 0,4, et l'économie passe de 1 184 € à 1 776 € sur les deux semaines de test. La courbe reste plate autour de 0,4-0,5 (9 € d'écart) : la décision « déployer avec un seuil vers 0,4 » est robuste à ce changement de coûts.
:::
::::

{#carte}
## La qualité des données de décembre

:::: task Étape 3 | Une carte I-MR du poids moyen | 10 min | 4 pts
Le poids des colis influence le retard (jour 2). Construisez une carte I-MR du **poids moyen par jour** :

1. limites calculées sur septembre-octobre : moyenne ± 2,66 × étendue mobile moyenne ;
2. appliquez-les aux 28 jours de décembre ;
3. affichez les limites, le **premier jour de décembre au-dessus de la limite haute**, et le nombre de jours de décembre au-dessus.

::: proof Collez les trois lignes de résultat
:::

::: hint
`generer_livraisons()` et `generer_livraisons_decembre()` ; `groupby("date_expedition")["poids_kg"].mean()` ; l'étendue mobile est `.diff().abs()`, calculée sur la période de référence seulement.
:::

::: solution
```python title="Évaluation : carte I-MR du poids moyen"
from colisvert.donnees import generer_livraisons_decembre

ref = pd.DataFrame(generer_livraisons()).groupby("date_expedition")["poids_kg"].mean()
dec = pd.DataFrame(generer_livraisons_decembre()).groupby("date_expedition")["poids_kg"].mean()
centre, em = ref.mean(), ref.diff().abs().mean()
lsc, lic = centre + 2.66 * em, centre - 2.66 * em
au_dessus = dec[dec > lsc]
print(f"référence : poids moyen {centre:.2f} kg, limites de {lic:.2f} à {lsc:.2f} kg ({(ref > lsc).sum()} jour hors limites)")
print(f"décembre : premier jour au-dessus de la limite haute : {au_dessus.index[0] if len(au_dessus) else 'aucun'}")
print(f"décembre : {len(au_dessus)} jours sur {len(dec)} au-dessus de la limite haute")
```

```plaintext title="Sortie attendue"
référence : poids moyen 15.28 kg, limites de 12.62 à 17.93 kg (0 jour hors limites)
décembre : premier jour au-dessus de la limite haute : 2026-11-30
décembre : 26 jours sur 28 au-dessus de la limite haute
```

Aucun jour de septembre-octobre ne sort des limites : la référence est stable. En décembre, **dès le premier jour** (lundi 30 novembre), le poids moyen dépasse la limite haute, et 26 jours sur 28 sont au-dessus. Ce n'est pas une variation commune : c'est la cause spéciale déjà vue au jour 2 (les cadeaux de fin d'année). Une carte de contrôle du poids moyen, placée en tâche dans le pipeline, aurait déclenché l'alerte le premier jour, avant même que le taux de retard ne bouge.
:::
::::

{#dora}
## L'équipe d'en face

:::: task Étape 4 | Les indicateurs DORA d'une autre équipe | 6 min | 3 pts
L'équipe « tarifs » a déployé son pipeline 6 fois en 4 semaines. Calculez ses cinq indicateurs DORA, sur le modèle de la Cellule 11.

| Date | Nature | Délai (h) | Incident | Rétablissement (h) |
|---|---|---|---|---|
| 2026-10-05 | prévu | 120 | non | |
| 2026-10-12 | prévu | 96 | oui | 30 |
| 2026-10-13 | correctif | 8 | oui | 10 |
| 2026-10-14 | correctif | 4 | non | |
| 2026-10-26 | prévu | 140 | non | |
| 2026-10-30 | prévu | 110 | non | |

::: proof Collez les cinq lignes
:::

::: hint
Le correctif du 13 a lui-même provoqué un incident : il compte dans le taux d'échec **et** dans le taux de reprise. Médiane du temps de rétablissement : sur les déploiements qui ont eu un incident.
:::

::: solution
```python title="Évaluation : DORA de l'équipe tarifs"
tarifs = pd.DataFrame(
    [
        ("2026-10-05", "prévu", 120, False, None),
        ("2026-10-12", "prévu", 96, True, 30),
        ("2026-10-13", "correctif", 8, True, 10),
        ("2026-10-14", "correctif", 4, False, None),
        ("2026-10-26", "prévu", 140, False, None),
        ("2026-10-30", "prévu", 110, False, None),
    ],
    columns=["date", "nature", "delai_h", "incident", "retablissement_h"],
)
print(f"délai des changements (médiane)      : {tarifs['delai_h'].median():.0f} h")
print(f"fréquence de déploiement             : {len(tarifs) / 4:.1f} par semaine")
print(f"temps de rétablissement (médiane)    : {tarifs['retablissement_h'].median():.0f} h")
print(f"taux d'échec des changements         : {tarifs['incident'].mean():.0%}")
print(f"taux de reprise                      : {(tarifs['nature'] == 'correctif').mean():.0%}")
```

```plaintext title="Sortie attendue"
délai des changements (médiane)      : 103 h
fréquence de déploiement             : 1.5 par semaine
temps de rétablissement (médiane)    : 20 h
taux d'échec des changements         : 33%
taux de reprise                      : 33%
```

Les deux équipes déploient au même rythme (1,5 par semaine), mais l'équipe « tarifs » met plus de trois fois plus de temps à faire passer une modification en production (103 h contre 30 h), échoue deux fois plus souvent (33 % contre 17 %) et passe un tiers de ses déploiements à corriger la production. Pour elle, la priorité n'est pas d'aller plus vite, mais de stabiliser : des tests et un contrat de données en amont du déploiement. Et on compare des **tendances**, jamais des personnes.
:::
::::

{#quiz}
## Quiz de validation

```quiz
- q: Un élément a un coût du retard de 20 et une taille de 8. On peut le découper en deux éléments de taille 3, chacun avec un coût du retard de 12. Que devient le WSJF du premier morceau ?
  options:
    - "2,5"
    - "4"
    - "12"
    - Il ne change pas
  answer: 1
  explain: 12 ÷ 3 = 4, contre 20 ÷ 8 = 2,5. Découper fait remonter la valeur dans le carnet.
- q: Une simulation de Monte-Carlo donne 6 sprints à 85 %. Que promettre au sponsor ?
  options:
    - 5 sprints, la moyenne
    - 6 sprints, avec 85 % de chances de tenir, et une mise à jour à chaque fin de sprint
    - 4 sprints pour motiver l'équipe
    - Rien
  answer: 1
  explain: On s'engage sur un niveau de confiance explicite, et on refait la prévision avec le débit réel.
- q: Un modèle a une F1 de 0,69. Que faut-il pour savoir s'il rapporte ?
  options:
    - Une F1 plus élevée
    - La matrice des coûts des erreurs et de l'action, validée par le métier
    - Plus de données
    - Un seuil de 0,5
  answer: 1
  explain: La valeur naît de la décision ; elle se calcule avec les coûts de chaque situation.
- q: Un point d'une carte p dépasse la limite haute un jour de semaine sans autre signe. Première réaction ?
  options:
    - Réentraîner le modèle
    - Chercher une cause spéciale ce jour-là ; sans cause trouvée, considérer une fausse alerte possible
    - Recalculer les limites en l'incluant
    - L'ignorer
  answer: 1
  explain: Un point hors limites est un signal à examiner ; à trois sigmas, environ une fausse alerte tous les 370 points.
- q: Le taux de reprise d'une équipe passe de 10 % à 35 %. Que signale-t-il ?
  options:
    - Que l'équipe déploie plus souvent
    - Qu'une part croissante des déploiements sert à réparer la production
    - Que les délais raccourcissent
    - Rien de particulier
  answer: 1
  explain: Le taux de reprise mesure l'instabilité - des correctifs non planifiés qui prennent la place du travail prévu.
- q: Dans une revue d'incident sans coupable, que cherche-t-on ?
  options:
    - La personne qui a fait l'erreur
    - Ce qui, dans le système, a rendu l'erreur possible, et les actions pour le changer
    - Un responsable à former
    - Le coût de l'incident uniquement
  answer: 1
  explain: Changer de personne ne change pas le système ; changer le système évite la répétition.
```
