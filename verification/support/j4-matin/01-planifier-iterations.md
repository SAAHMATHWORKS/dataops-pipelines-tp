---
subtitle: >-
  Un produit data se construit par petites livraisons, parce qu'on ne sait pas à l'avance ce que les
  données permettront. Encore faut-il choisir quoi livrer d'abord, et répondre honnêtement à la
  question « quand est-ce que ce sera fini ? ». On priorise le carnet de ColisVert par le coût du
  retard, puis on remplace la promesse au doigt mouillé par une prévision chiffrée, avec sa marge
  d'incertitude.
objectives:
  - Expliquer pourquoi un produit data se livre par itérations courtes
  - Prioriser un carnet avec le coût du retard divisé par la taille (WSJF)
  - Écrire une définition de « terminé » adaptée à un produit data
  - Relier en-cours, débit et délai avec la loi de Little
  - Prévoir une date de livraison par simulation de Monte-Carlo, avec un niveau de confiance
---

{#pourquoi}
## Pourquoi itérer ?

**Le problème.** Au jour 2, on a vu le cycle de vie d'un produit data : idéation, inception, recherche, mise en production. Cette phase de recherche est **incertaine par nature** : on ne sait pas, avant d'avoir essayé, si les données contiennent le signal espéré. ColisVert l'a vécu : le premier modèle manquait 4 retards sur 10, et il a fallu une itération de plus (la pondération des classes) pour franchir la charte.

**L'analogie du GPS.** Un GPS ne calcule pas l'itinéraire une fois pour toutes : il recalcule à chaque carrefour, avec ce qu'il vient d'apprendre (un bouchon, une route fermée). Une itération courte, c'est un carrefour : on livre un petit morceau, on regarde ce qu'il produit, on recalcule la suite.

Le Manifeste DataOps le dit dans son principe 1 (« Satisfaire continuellement le client ») et son principe 18 (« Améliorer les temps de cycle ») : la valeur arrive par **petits lots fréquents**, pas par un grand projet livré au bout d'un an.

| Approche | Cadence | Quand la préférer |
|---|---|---|
| **Scrum** | Itérations de durée fixe (*sprints* de 2 semaines), objectif d'itération, revue et rétrospective | Équipe stable, travail planifiable, besoin de rythme |
| **Kanban** | Flux continu, limite du travail en cours par colonne | Beaucoup de demandes imprévues (support, incidents, demandes d'analyse) |
| **Hybride** | Sprints pour le développement, flux Kanban pour l'exploitation | Le cas le plus fréquent dans une équipe DataOps |

{#prioriser}
## Prioriser par le coût du retard

**Le piège de la « valeur » seule.** Classer le carnet par valeur métier pousse en tête les gros chantiers prestigieux, qui bloquent l'équipe des mois. Ce qui compte, c'est la valeur **perdue chaque semaine où l'élément n'est pas livré** : son **coût du retard** (*cost of delay*).

**WSJF** (*weighted shortest job first*, « le travail le plus court pondéré d'abord ») est la règle popularisée par le cadre SAFe :

> **WSJF = coût du retard ÷ taille**, avec **coût du retard = valeur métier + urgence + réduction de risque ou ouverture d'opportunité**.

Chaque critère est noté par comparaison, sur une échelle de Fibonacci (1, 2, 3, 5, 8, 13, 20) : l'élément le plus faible du lot reçoit 1, les autres sont notés par rapport à lui. On ne cherche pas la précision, mais un **ordre** défendable.

::: callout info L'intuition, avec deux colis
Un colis urgent mais léger part avant un colis peu urgent et lourd. WSJF fait la même chose avec le travail : un petit élément qui coûte cher à attendre passe devant un gros élément qui peut attendre.
:::

:::: lab Démo | Le carnet de ColisVert | 8 min
Ouvrez un notebook neuf `j4-matin.ipynb` dans le dossier `notebooks`. Après le jour 3, l'équipe a noté huit éléments dans son carnet de produit.

```python title="Cellule 1 : prioriser par WSJF"
import pandas as pd

carnet = pd.DataFrame(
    [
        # élément, valeur métier, urgence, risque ou opportunité, taille
        ("Alerte SMS aux clients des colis à risque", 8, 8, 3, 5),
        ("Carte de contrôle du taux de retard", 3, 5, 8, 2),
        ("Fenêtre d'entraînement glissante", 5, 5, 5, 3),
        ("Tableau de bord des retards par entrepôt", 5, 3, 2, 3),
        ("Modèle dédié aux clients pro", 8, 2, 2, 8),
        ("Base MLflow sur PostgreSQL", 1, 2, 5, 5),
        ("Explications pour le service client", 5, 2, 3, 5),
        ("Alerte si le fichier manque à 7 h", 3, 8, 5, 1),
    ],
    columns=["element", "valeur", "urgence", "risque", "taille"],
)
carnet["cout_du_retard"] = carnet[["valeur", "urgence", "risque"]].sum(axis=1)
carnet["wsjf"] = (carnet["cout_du_retard"] / carnet["taille"]).round(2)
ordre = carnet.sort_values("wsjf", ascending=False)
print(ordre[["element", "cout_du_retard", "taille", "wsjf"]].to_string(index=False))
```

```plaintext title="Sortie attendue"
                                  element  cout_du_retard  taille  wsjf
        Alerte si le fichier manque à 7 h              16       1 16.00
      Carte de contrôle du taux de retard              16       2  8.00
         Fenêtre d'entraînement glissante              15       3  5.00
Alerte SMS aux clients des colis à risque              19       5  3.80
 Tableau de bord des retards par entrepôt              10       3  3.33
      Explications pour le service client              10       5  2.00
               Base MLflow sur PostgreSQL               8       5  1.60
             Modèle dédié aux clients pro              12       8  1.50
```
::::

**Ce que l'ordre dit.**

- **Deux petits éléments passent en tête** : l'alerte « fichier absent à 7 h » (taille 1) et la carte de contrôle du taux de retard (taille 2). Peu de travail, beaucoup de risque évité : ce sont des leçons du jour 3 et de ce matin.
- **L'alerte SMS**, qui a le plus gros coût du retard (19), n'arrive qu'en 4e position : elle est plus grosse. On la découpera peut-être (un premier SMS pour un seul entrepôt) pour la faire remonter.
- **Le modèle dédié aux clients pro**, le plus prestigieux, finit dernier : beaucoup de travail pour une urgence faible.

WSJF ne décide pas à votre place : il rend la discussion **explicite**. Si le métier conteste l'ordre, on discute des notes, pas des opinions.

{#termine}
## Une définition de « terminé » pour un produit data

Un élément n'est pas terminé quand le code tourne sur le poste du développeur. Pour un produit data, l'équipe écrit sa **définition de « terminé »** (*definition of done*) une fois pour toutes, et chaque élément la respecte.

| Critère | Pourquoi | Chez ColisVert |
|---|---|---|
| Le code est versionné et relu | Personne ne travaille seul | Git, revue de code |
| Les données sont versionnées | Rejouer un résultat | DVC (jour 1) |
| Le contrat de données est vérifié | Échouer tôt | `pipeline/controle.py` (jour 3) |
| Les métriques sont suivies | Comparer, expliquer | MLflow (jour 2) |
| La charte de qualité est respectée | Ne livrer que ce qui sert | Barrière de qualité (jour 3) |
| L'exécution est orchestrée et surveillée | Tourner sans héros | Airflow (jour 3), carte de contrôle (ce matin) |
| Le retour arrière est possible | Se tromper sans drame | Alias `precedent` du registre (jour 2) |
| La documentation est à jour | Le savoir ne part pas avec une personne | README, ADR (jour 3) |

{#flux}
## Débit, en-cours et loi de Little

Trois mesures suffisent pour piloter le flux de travail d'une équipe :

- le **débit** : combien d'éléments sont terminés par semaine ;
- l'**en-cours** (*work in progress*) : combien d'éléments sont commencés et pas finis ;
- le **délai** (*lead time*) : combien de temps un élément met entre « commencé » et « terminé ».

**La loi de Little** les relie, pour tout système stable : **délai moyen = en-cours moyen ÷ débit moyen**. Si l'équipe de ColisVert termine 2,35 éléments par semaine et en a 7 en cours, chacun met en moyenne 7 ÷ 2,35 ≈ 3 semaines. Pour livrer plus vite, on peut travailler plus vite (difficile), ou **commencer moins de choses à la fois** (immédiat). C'est la raison des limites d'en-cours de Kanban : « arrêter de commencer, commencer à finir ».

{#prevoir}
## Prévoir sans se mentir : la simulation de Monte-Carlo

**La question du sponsor.** « Il reste 24 éléments pour la version 2. Quand sera-t-elle prête ? » La réponse habituelle divise le reste par le débit moyen : 24 ÷ 4,7 éléments par sprint ≈ 5,1 sprints. Mais une moyenne a une chance sur deux d'être dépassée : promettre la moyenne, c'est promettre un retard une fois sur deux.

**La simulation de Monte-Carlo** rejoue l'avenir des milliers de fois à partir du passé : à chaque essai, on tire au hasard, parmi les débits réellement observés, celui de chaque sprint futur, jusqu'à épuiser les 24 éléments. On compte combien de sprints il a fallu. Sur 10 000 essais, on obtient une **distribution** : on peut alors dire « 85 % de chances de finir en N sprints ou moins ».

:::: lab Démo | Quand la version 2 sera-t-elle prête ? | 8 min
```python title="Cellule 2 : 10 000 avenirs possibles"
import numpy as np

debits_passes = np.array([4, 6, 3, 5, 7, 2, 5, 4, 6, 5])   # éléments terminés, 10 derniers sprints
reste = 24
rng = np.random.default_rng(2026)

def sprints_necessaires(rng):
    termine, sprints = 0, 0
    while termine < reste:
        termine += rng.choice(debits_passes)
        sprints += 1
    return sprints

essais = np.array([sprints_necessaires(rng) for _ in range(10_000)])
print(f"débit moyen : {debits_passes.mean():.1f} éléments par sprint ; reste ÷ moyenne = {reste / debits_passes.mean():.1f} sprints")
for niveau in [50, 85, 95]:
    print(f"{niveau} % de chances de finir en {int(np.percentile(essais, niveau))} sprints ou moins")
print(f"probabilité de finir en 5 sprints ou moins : {(essais <= 5).mean():.0%}")
```

```plaintext title="Sortie attendue"
débit moyen : 4.7 éléments par sprint ; reste ÷ moyenne = 5.1 sprints
50 % de chances de finir en 5 sprints ou moins
85 % de chances de finir en 6 sprints ou moins
95 % de chances de finir en 7 sprints ou moins
probabilité de finir en 5 sprints ou moins : 51%
```
::::

**Comment le dire au sponsor.** « En 5 sprints, c'est une chance sur deux. Pour un engagement ferme, comptez 6 sprints : 85 % de chances. » Et on refait la simulation à chaque fin de sprint, avec le débit réel : la prévision se resserre au fil du projet, comme le GPS qui recalcule.

::: callout warn Les points de complexité ne sont pas une monnaie
On convertit souvent les points de complexité en jours, puis en coûts. C'est fragile : un point n'a pas la même valeur d'une équipe à l'autre, ni d'un trimestre à l'autre. Compter les **éléments terminés** (de taille comparable, en découpant les gros) et simuler donne des prévisions au moins aussi bonnes, pour beaucoup moins de débats.
:::

{#quiz}
## Quiz

```quiz
- q: Deux éléments ont le même coût du retard (15). L'un a une taille de 3, l'autre de 8. Lequel passe en premier selon WSJF ?
  options:
    - Celui de taille 8, car il apporte plus
    - Celui de taille 3, son WSJF est de 5 contre 1,9
    - Les deux à égalité
    - On ne peut pas savoir
  answer: 1
  explain: WSJF = coût du retard ÷ taille. À coût du retard égal, le plus petit élément libère la valeur le plus vite.
- q: Une équipe a 12 éléments en cours et en termine 3 par semaine. Quel est le délai moyen d'un élément ?
  options:
    - 3 semaines
    - 4 semaines
    - 12 semaines
    - 36 semaines
  answer: 1
  explain: Loi de Little - délai = en-cours ÷ débit = 12 ÷ 3 = 4 semaines.
- q: Pourquoi ne pas promettre « reste ÷ débit moyen » sprints ?
  options:
    - Parce que la moyenne est toujours fausse
    - Parce qu'on a environ une chance sur deux de la dépasser
    - Parce que le débit ne varie pas
    - Parce que Scrum l'interdit
  answer: 1
  explain: La simulation montre la distribution complète ; on s'engage sur un percentile élevé (85 %), pas sur la moyenne.
- q: Quel critère manque le plus souvent à la définition de « terminé » d'un produit data ?
  options:
    - Le code compile
    - Les données et le modèle sont versionnés, surveillés, et le retour arrière est possible
    - Le développeur est satisfait
    - Le ticket est fermé
  answer: 1
  explain: Un produit data vit avec ses données ; sans versions, sans surveillance et sans retour arrière, il n'est pas exploitable.
```
