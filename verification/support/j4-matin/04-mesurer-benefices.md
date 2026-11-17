---
subtitle: >-
  « Combien ça rapporte ? » est la question qui décide si une équipe data grandit ou disparaît. On
  distingue ce qu'on produit de ce que ça change, on mesure la santé de la chaîne de livraison avec
  les cinq indicateurs DORA, puis on calcule le retour sur investissement de l'alerte SMS, avec son
  délai d'amortissement et ses scénarios défavorables.
objectives:
  - Distinguer production, résultat et bénéfice, et indicateurs avancés et retardés
  - Calculer les cinq indicateurs DORA sur l'historique des déploiements d'un pipeline
  - Calculer un retour sur investissement et un délai d'amortissement
  - Présenter un bénéfice avec ses hypothèses et un scénario défavorable
  - Savoir comment prouver qu'un bénéfice vient bien du produit data
---

{#niveaux}
## Ce qu'on produit, ce que ça change

| Niveau | Question | Exemple chez ColisVert | Qui le suit |
|---|---|---|---|
| **Production** (*output*) | Qu'a-t-on livré ? | Un modèle, un DAG, un tableau de bord | L'équipe |
| **Résultat** (*outcome*) | Qu'est-ce qui a changé dans le comportement ? | 80 % des clients en retard prévenus avant la livraison | Le métier |
| **Bénéfice** (*impact*) | Que vaut ce changement ? | 31 600 € d'économies par an, moins de réclamations | La direction |

Une équipe qui ne rend compte que de sa **production** (« 12 modèles livrés ce trimestre ») sera jugée sur son coût. Une équipe qui montre ses **bénéfices** sera jugée sur sa valeur.

**Indicateurs avancés et retardés.** Le bénéfice en euros est un indicateur **retardé** : on ne le connaît qu'au bout de plusieurs mois. Pour piloter, on suit aussi des indicateurs **avancés**, qui le précèdent et l'annoncent : la part des clients prévenus, le taux d'appels au service client, le délai de mise en production d'une amélioration.

{#dora}
## La santé de la chaîne de livraison : les indicateurs DORA

Le programme de recherche DORA (*DevOps Research and Assessment*, aujourd'hui chez Google Cloud) mesure depuis 2014 ce qui distingue les équipes logicielles performantes. Son rapport 2025 retient **cinq indicateurs**, en deux familles. Ils s'appliquent tels quels à un pipeline de données, où un « déploiement » est la mise en production d'une nouvelle version (code, paramètres ou modèle).

| Famille | Indicateur | Définition |
|---|---|---|
| **Débit** | Délai des changements | Temps entre le commit et la mise en production |
| | Fréquence de déploiement | Nombre de mises en production par période |
| | Temps de rétablissement après un déploiement raté | Temps pour revenir à un état sain |
| **Instabilité** | Taux d'échec des changements | Part des déploiements qui provoquent un incident ou un retour arrière |
| | Taux de reprise (nouveau en 2025) | Part des déploiements non planifiés, faits pour corriger un problème de production |

:::: lab Démo | Les indicateurs DORA du pipeline de ColisVert | 8 min
L'équipe a noté chaque mise en production du pipeline pendant les 8 semaines de septembre-octobre.

```python title="Cellule 11 : les cinq indicateurs DORA"
deploiements = pd.DataFrame(
    [
        # date, nature, heures entre le commit et la production, a provoqué un incident, heures pour rétablir
        ("2026-09-08", "prévu", 30, False, None),
        ("2026-09-11", "prévu", 52, False, None),
        ("2026-09-15", "prévu", 44, True, 6),
        ("2026-09-15", "correctif", 3, False, None),
        ("2026-09-22", "prévu", 70, False, None),
        ("2026-09-29", "prévu", 26, False, None),
        ("2026-10-02", "prévu", 48, True, 20),
        ("2026-10-03", "correctif", 5, False, None),
        ("2026-10-09", "prévu", 36, False, None),
        ("2026-10-16", "prévu", 22, False, None),
        ("2026-10-23", "prévu", 30, False, None),
        ("2026-10-30", "prévu", 18, False, None),
    ],
    columns=["date", "nature", "delai_h", "incident", "retablissement_h"],
)
semaines = 8
print(f"délai des changements (médiane)      : {deploiements['delai_h'].median():.0f} h")
print(f"fréquence de déploiement             : {len(deploiements) / semaines:.1f} par semaine")
print(f"temps de rétablissement (médiane)    : {deploiements['retablissement_h'].median():.0f} h")
print(f"taux d'échec des changements         : {deploiements['incident'].mean():.0%}")
print(f"taux de reprise                      : {(deploiements['nature'] == 'correctif').mean():.0%}")
```

```plaintext title="Sortie attendue"
délai des changements (médiane)      : 30 h
fréquence de déploiement             : 1.5 par semaine
temps de rétablissement (médiane)    : 13 h
taux d'échec des changements         : 17%
taux de reprise                      : 17%
```
::::

**Lecture.** L'équipe déploie une fois et demie par semaine, une modification met un peu plus d'une journée à atteindre la production, et un déploiement sur six provoque un incident, rétabli en une demi-journée environ. Ces valeurs n'ont de sens qu'**en tendance** : on les recalcule chaque mois, et l'on vérifie que les améliorations (le contrat de données, la barrière de qualité, le retour arrière par alias) font baisser le taux d'échec et le temps de rétablissement.

::: callout warn Un indicateur devient une cible, puis cesse d'être un bon indicateur
C'est la loi de Goodhart. Si l'on récompense la fréquence de déploiement, on découpera les changements à l'infini ; si l'on punit le taux d'échec, on cessera de déployer. Les indicateurs DORA servent à l'équipe pour **s'améliorer**, en tendance, jamais à comparer des personnes ou des équipes entre elles.
:::

{#roi}
## Le retour sur investissement de l'alerte SMS

Le **retour sur investissement** (ROI) rapporte le gain net à ce qu'on a dépensé : **ROI = (bénéfices − coûts) ÷ coûts**. Le **délai d'amortissement** est le mois où les bénéfices cumulés dépassent les coûts cumulés.

Les hypothèses de ColisVert, écrites et datées :

| Poste | Montant | Source |
|---|---|---|
| Construction (modèle, pipeline, intégration SMS) | 30 jours × 550 € = 16 500 € | Estimation de l'équipe |
| Exploitation | 1,5 jour par mois × 550 € + 120 € d'infrastructure = 945 € par mois | Airflow auto-hébergé, chiffré au jour 3 |
| Bénéfice | 0,96 € par colis × 2 735 colis par mois | Notion 2, seuil 0,4, retard non prévenu à 15 € |

:::: lab Démo | Amortissement et scénario défavorable | 8 min
```python title="Cellule 12 : amortissement sur 24 mois"
colis_par_mois = 5035 / 56 * 365 / 12
construction = 30 * 550
exploitation = 1.5 * 550 + 120


def amortissement(economie_par_colis, mois=24):
    gain_mensuel = economie_par_colis * colis_par_mois
    cumul = [-construction + m * (gain_mensuel - exploitation) for m in range(1, mois + 1)]
    mois_rentable = next((m for m, c in enumerate(cumul, start=1) if c >= 0), None)
    roi = {m: cumul[m - 1] / (construction + m * exploitation) for m in (12, 24)}
    return gain_mensuel, mois_rentable, roi


for nom, cout_retard in [("hypothèse centrale", 15.0), ("scénario défavorable", 8.0)]:
    couts = {**COUTS, "retard_surprise": cout_retard}
    meilleur_bilan = max((bilan(round(s / 100, 2), couts) for s in range(5, 100, 5)), key=lambda b: b["economie"])
    gain, mois_rentable, roi = amortissement(meilleur_bilan["economie"] / len(test))
    print(f"{nom} (retard non prévenu à {cout_retard:.0f} €) : gain {gain:,.0f} € par mois, "
          f"amorti {'au mois ' + str(mois_rentable) if mois_rentable else 'jamais en 24 mois'}, "
          f"ROI à 12 mois {roi[12]:.0%}, à 24 mois {roi[24]:.0%}")
```

```plaintext title="Sortie attendue"
hypothèse centrale (retard non prévenu à 15 €) : gain 2,633 € par mois, amorti au mois 10, ROI à 12 mois 13%, à 24 mois 61%
scénario défavorable (retard non prévenu à 8 €) : gain 104 € par mois, amorti jamais en 24 mois, ROI à 12 mois -95%, à 24 mois -94%
```
::::

**Ce qu'on présente au comité de direction.**

- **Hypothèse centrale :** 2 633 € de gain par mois, l'investissement est **amorti au 10e mois**. Le ROI est modeste la première année (13 %), puis atteint 61 % sur deux ans, parce que la construction n'est payée qu'une fois.
- **Scénario défavorable :** si un retard non prévenu ne coûte que 8 €, le projet **ne s'amortit jamais** : il perd presque tout ce qu'il coûte.
- **La recommandation qui en découle :** lancer d'abord la mesure du coût réel d'un retard non prévenu, et l'alerte SMS sur un seul entrepôt (un petit lot, qui produit la mesure). Généraliser seulement si le coût mesuré dépasse une dizaine d'euros. C'est une décision **réversible et peu chère**, plutôt qu'un pari à 16 500 €.

{#preuve}
## Prouver que le bénéfice vient du produit data

Les appels au service client baissent de 20 % après le lancement des SMS. Est-ce grâce aux SMS, ou parce que décembre est passé ? Pour **attribuer** un bénéfice, trois méthodes, de la plus solide à la plus fragile :

1. **Expérience contrôlée** (test A/B) : pendant un mois, une moitié des colis à risque, tirée au hasard, reçoit le SMS, l'autre non. La différence entre les deux groupes est l'effet du SMS, et lui seul. C'est l'étalon-or, quand il est éthique et possible.
2. **Groupe témoin naturel** : l'alerte démarre à Lille et Lyon, pas encore à Nantes et Toulouse. On compare l'évolution des deux groupes d'entrepôts avant et après (méthode des « différences de différences »).
3. **Avant-après** sans témoin : le plus simple, et le plus trompeur, car tout ce qui a changé en même temps (saison, météo, prix) est attribué au produit.

La carte de contrôle de la notion 3 aide pour la troisième : si l'indicateur sort durablement des limites **après** le lancement, et dans le bon sens, le système a changé. Mais elle ne dit pas **pourquoi**.

{#quiz}
## Quiz

```quiz
- q: « 80 % des clients en retard sont prévenus avant la livraison. » De quel niveau s'agit-il ?
  options:
    - Production
    - Résultat - un changement de comportement ou de situation
    - Bénéfice financier
    - Indicateur DORA
  answer: 1
  explain: La production est le modèle ou le SMS ; le résultat est ce qui change chez le client ; le bénéfice est sa valeur.
- q: Quel indicateur DORA a été ajouté en 2025 ?
  options:
    - La fréquence de déploiement
    - Le taux de reprise - la part des déploiements non planifiés pour corriger la production
    - Le délai des changements
    - Le taux d'échec des changements
  answer: 1
  explain: Les quatre indicateurs historiques sont complétés par le taux de reprise, dans la famille de l'instabilité.
- q: Pourquoi présenter un scénario défavorable avec le ROI ?
  options:
    - Pour montrer qu'on est prudent
    - Parce que le ROI dépend d'hypothèses incertaines, et que la décision doit tenir compte de leur variation
    - Parce que c'est obligatoire
    - Pour réduire le budget
  answer: 1
  explain: Ici, l'amortissement passe du 10e mois à « jamais » selon le coût d'un retard, et c'est l'information la plus utile pour décider.
- q: Quelle méthode attribue le plus sûrement une baisse des réclamations à l'alerte SMS ?
  options:
    - Comparer avant et après le lancement
    - Un test A/B - un groupe tiré au hasard reçoit le SMS, l'autre non
    - Demander l'avis du service client
    - Regarder la carte de contrôle
  answer: 1
  explain: Le tirage au hasard élimine les autres causes possibles ; l'avant-après les mélange toutes.
```
