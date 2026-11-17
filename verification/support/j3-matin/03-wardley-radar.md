---
subtitle: >-
  Deux outils de stratégie, simples et visuels. La carte de Wardley montre où chaque composant en
  est de son évolution, donc ce qu'il faut construire, acheter ou louer. Le radar technologique
  dit, pour chaque outil, s'il faut l'adopter, l'essayer, l'évaluer ou le laisser de côté. Ensemble,
  ils servent à faire évoluer la pile sans à-coups.
objectives:
  - Lire et construire une carte de Wardley (chaîne de valeur et évolution)
  - Déduire d'une carte où construire, où acheter et où louer
  - Tenir un radar technologique avec ses quatre anneaux
  - Décrire un processus pour faire évoluer la pile d'outils d'une équipe
---

{#wardley}
## La carte de Wardley

**Pourquoi une carte ?** Une stratégie écrite en paragraphes se discute mal : chacun imagine autre chose. Simon Wardley, ancien dirigeant dans l'industrie du logiciel, propose de **dessiner** la situation, comme un général regarde une carte avant de décider. Sa carte a deux axes :

- **Verticalement, la chaîne de valeur.** En haut, le besoin du client, très visible pour lui. En dessous, ce dont ce besoin dépend, de moins en moins visible : le client ne voit pas l'orchestrateur, encore moins le serveur.
- **Horizontalement, l'évolution.** Chaque composant progresse de gauche à droite en quatre phases :

| Phase | Ce que c'est | Comment on s'en procure |
|---|---|---|
| **Genèse** | Nouveau, rare, mal compris, incertain | On l'invente, on expérimente |
| **Sur mesure** | Compris par quelques-uns, construit au cas par cas | On le construit |
| **Produit** (ou location) | Répandu, des offres concurrentes, des fonctionnalités comparables | On l'achète ou on le loue |
| **Commodité** (ou service public) | Standard, banal, facturé à l'usage | On le consomme, comme l'électricité |

**L'idée centrale :** la bonne manière de traiter un composant dépend de **sa phase**, pas de vos préférences. Construire une commodité gaspille de l'argent ; acheter un produit sur étagère pour un composant en genèse est impossible, ou trompeur.

::: figure wardley-colisvert.svg
La carte de ColisVert. Le besoin du client est en haut. Le modèle de prédiction et les données de livraison sont « sur mesure » : c'est là que ColisVert se différencie. L'orchestration et le suivi des expériences sont des produits. Le calcul, le stockage et l'envoi de SMS sont des commodités. La flèche indique que l'orchestration glisse vers la commodité, avec les services managés.
:::

**Ce que la carte dit à ColisVert :**

- **Construire** le modèle de prédiction et soigner les données de livraison (la partie « sur mesure ») : c'est le seul endroit où un concurrent ne peut pas simplement acheter la même chose.
- **Acheter ou louer** l'orchestration et le suivi des expériences (produits), en restant sur des standards (Airflow, MLflow).
- **Consommer** le calcul, le stockage et les SMS (commodités), au meilleur prix, sans s'y attacher.

C'est la conclusion de la notion précédente, mais **vue d'un coup d'œil**, et discutable autour d'une table.

:::: lab Démo | Dessiner la carte avec matplotlib | 5 min
Une carte de Wardley n'a besoin d'aucun outil spécial : des points, des traits et quatre zones. Dans votre notebook `j3-matin.ipynb` :

```python title="Cellule 2 : la carte de Wardley de ColisVert"
import matplotlib.pyplot as plt

# (évolution de 0 à 1, visibilité de 0 à 1) : à gauche la genèse, à droite la commodité
composants = {
    "Être prévenu d'un retard": (0.35, 0.92),
    "SMS d'alerte": (0.85, 0.75),
    "Modèle de prédiction": (0.30, 0.60),
    "Données de livraison": (0.33, 0.37),
    "Suivi des expériences": (0.60, 0.45),
    "Orchestration": (0.65, 0.27),
    "Calcul et stockage cloud": (0.88, 0.10),
}
liens = [
    ("Être prévenu d'un retard", "SMS d'alerte"), ("Être prévenu d'un retard", "Modèle de prédiction"),
    ("Modèle de prédiction", "Données de livraison"), ("Modèle de prédiction", "Suivi des expériences"),
    ("Données de livraison", "Orchestration"), ("Orchestration", "Calcul et stockage cloud"),
    ("Suivi des expériences", "Calcul et stockage cloud"), ("SMS d'alerte", "Calcul et stockage cloud"),
]

fig, ax = plt.subplots(figsize=(10, 6))
for haut, bas in liens:
    (x1, y1), (x2, y2) = composants[haut], composants[bas]
    ax.plot([x1, x2], [y1, y2], color="grey", linewidth=1, zorder=1)
for nom, (x, y) in composants.items():
    ax.scatter(x, y, s=80, color="white", edgecolor="black", zorder=2)
    ax.annotate(nom, (x, y), xytext=(6, 6), textcoords="offset points")
for limite in [0.25, 0.5, 0.75]:
    ax.axvline(limite, linestyle="--", color="lightgrey")
ax.set_xticks([0.125, 0.375, 0.625, 0.875], ["Genèse", "Sur mesure", "Produit", "Commodité"])
ax.set_yticks([])
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.set_xlabel("évolution")
ax.set_ylabel("visibilité pour le client")
ax.set_title("Carte de Wardley de ColisVert")
plt.show()
```

Déplacez un point (par exemple, l'orchestration vers 0,85) et relancez : la carte sert à discuter « et si… ? ».
::::

{#radar}
## Le radar technologique

**Pourquoi un radar ?** Dans une équipe, chacun a ses outils préférés, et les nouveautés arrivent chaque semaine. Sans règle commune, on finit avec cinq bibliothèques pour faire la même chose. Le **radar technologique**, popularisé par le cabinet Thoughtworks qui publie le sien deux fois par an, donne à chaque technologie une **position** décidée collectivement.

Le radar a **quatre anneaux** :

| Anneau | Ce qu'il signifie | Conséquence pratique |
|---|---|---|
| **Adopter** | Éprouvé chez nous, c'est le choix par défaut | On l'utilise sans demander |
| **Essayer** | Prometteur, à utiliser sur un vrai projet dont le risque est maîtrisé | Un projet pilote, avec un retour d'expérience |
| **Évaluer** | À explorer, sans engagement | Une étude, une maquette, une démonstration |
| **Suspendre** | À ne plus utiliser pour **les nouveaux** projets | L'existant continue, avec un plan de sortie |

Et **quatre quadrants**, pour ranger les entrées : techniques, outils, plateformes, langages et bibliothèques.

:::: lab Démo | Le radar de ColisVert, en données | 5 min
Un radar est d'abord un **tableau** : une ligne par technologie, avec son quadrant, son anneau et une justification d'une ligne. On peut le versionner dans Git comme le reste.

```python title="Cellule 3 : le radar de ColisVert"
import pandas as pd

radar = pd.DataFrame(
    [
        ("Parquet", "plateformes", "Adopter", "lu par tous nos moteurs, 5 fois plus petit que le CSV"),
        ("Git et DVC", "outils", "Adopter", "toutes les données et tous les modèles sont versionnés"),
        ("MLflow", "outils", "Adopter", "suivi, registre et service en production depuis le jour 2"),
        ("Contrats de données", "techniques", "Adopter", "chaque fichier entrant est contrôlé"),
        ("Airflow 3", "outils", "Essayer", "pilote sur le pipeline des retards"),
        ("DuckDB", "outils", "Essayer", "analyses ad hoc sur Parquet, sans serveur"),
        ("Delta Lake", "plateformes", "Évaluer", "historique et transactions sur nos tables"),
        ("Agents IA de diagnostic", "techniques", "Évaluer", "lire les journaux d'un échec et proposer une cause"),
        ("Scripts lancés par cron", "techniques", "Suspendre", "ni reprise, ni alerte, ni historique"),
        ("CSV comme format d'échange", "techniques", "Suspendre", "sans types, lourd, ambigu sur les dates"),
    ],
    columns=["technologie", "quadrant", "anneau", "justification"],
)
for anneau in ["Adopter", "Essayer", "Évaluer", "Suspendre"]:
    noms = radar.loc[radar["anneau"] == anneau, "technologie"].tolist()
    print(f"{anneau:<10} ({len(noms)}) : {', '.join(noms)}")
```

```plaintext title="Sortie attendue"
Adopter    (4) : Parquet, Git et DVC, MLflow, Contrats de données
Essayer    (2) : Airflow 3, DuckDB
Évaluer    (2) : Delta Lake, Agents IA de diagnostic
Suspendre  (2) : Scripts lancés par cron, CSV comme format d'échange
```

La justification compte autant que la position : elle dit **pourquoi**, et donc ce qui ferait changer d'avis. « 5 fois plus petit que le CSV » pour Parquet : vous vérifierez ce chiffre vous-même dans la notion 4.
::::

{#evoluer}
## Faire évoluer la pile

Une pile d'outils n'est jamais finie : les composants évoluent (la carte de Wardley), les besoins aussi. Le radar sert de **processus** :

1. **Tous les six mois**, l'équipe revoit le radar. Chaque proposition d'entrée ou de déplacement s'appuie sur des faits (un pilote, un incident, une mesure).
2. **Une nouvelle technologie entre par « Évaluer »**, puis « Essayer » sur un projet réel limité, avant « Adopter ». Pas de raccourci : c'est ce qui évite d'adopter un outil sur la foi d'une démonstration.
3. **Toute décision importante est écrite** dans un court document de décision d'architecture (*ADR, architecture decision record*) : le contexte, les options, la décision, ses conséquences. Dans deux ans, quelqu'un demandera « pourquoi Airflow ? » : la réponse sera dans le dépôt.
4. **« Suspendre » vient avec un plan de sortie** : qui migre quoi, avant quand. Sans plan, la pile ne fait que grossir.

::: callout tip Question fréquente : « Le radar de Thoughtworks ne suffit-il pas ? »
Il est excellent pour **découvrir** des tendances, mais il reflète le contexte de leurs clients, pas le vôtre. Un outil « Adopter » chez eux peut être « Suspendre » chez vous, faute de compétences ou parce qu'un équivalent est déjà en place. Thoughtworks fournit d'ailleurs un outil libre pour construire **son propre** radar à partir d'un simple tableau, comme celui de la Cellule 3.
:::

{#avance}
## Pour aller plus loin : les lois de l'évolution et les limites des cartes

Ce bloc est pour les profils avancés ; rien ici n'est exigé dans l'évaluation.

**Tout évolue, sous la pression de la concurrence.** Wardley observe que l'offre et la demande poussent chaque composant vers la droite : ce qui était une innovation rare devient un produit, puis une commodité. Le calcul a suivi ce chemin (des serveurs sur mesure au cloud facturé à la seconde) ; les modèles de langage sont en train de le parcourir à grande vitesse. Conséquence pratique : un avantage construit sur un composant « sur mesure » est **temporaire**. Il faut le réinvestir avant qu'il ne devienne une commodité que tout le monde loue.

**L'inertie.** Les organisations résistent à ce mouvement : on garde son serveur maison parce qu'on l'a payé, son orchestrateur maison parce que son auteur est toujours là. La carte rend cette inertie **visible** : un composant dessiné en commodité mais traité « sur mesure » est un gaspillage qu'on peut chiffrer.

**Pionniers, colons, urbanistes.** Wardley suggère que des profils différents excellent à des phases différentes : des **pionniers** pour la genèse (explorer, accepter l'échec), des **colons** pour transformer l'idée en produit, des **urbanistes** pour industrialiser en commodité. Une équipe data a besoin des trois, et les confondre fait souffrir tout le monde : demander à un pionnier d'écrire des procédures d'exploitation, ou à un urbaniste d'explorer sans cahier des charges.

**Les limites.** Une carte est **subjective** : deux personnes placeront différemment le même composant. Sa valeur est dans la **conversation** qu'elle provoque, pas dans la précision des coordonnées. Même remarque pour le radar : son but est d'aligner une équipe, pas de dire la vérité sur une technologie.

{#quiz}
## Quiz de validation

```quiz
- q: Sur une carte de Wardley, que représente l'axe horizontal ?
  options:
    - Le coût du composant
    - L'évolution du composant, de la genèse à la commodité
    - Le temps écoulé depuis la création de l'entreprise
    - Le nombre d'utilisateurs
  answer: 1
  explain: L'axe vertical est la chaîne de valeur, de la plus visible à la moins visible pour le client.
- q: Un composant est en phase « commodité ». Que recommande la carte ?
  options:
    - Le construire soi-même pour le maîtriser
    - Le consommer comme un service, au meilleur prix
    - L'évaluer pendant six mois
    - L'ignorer
  answer: 1
  explain: Construire une commodité gaspille de l'argent - c'est comme produire sa propre électricité.
- q: Que signifie l'anneau « Suspendre » d'un radar technologique ?
  options:
    - Supprimer immédiatement l'outil partout
    - Ne plus l'utiliser pour les nouveaux projets, avec un plan de sortie pour l'existant
    - L'essayer sur un projet pilote
    - Le recommander à tous
  answer: 1
  explain: L'existant continue de tourner ; on arrête simplement d'en ajouter.
- q: Par quel anneau une nouvelle technologie devrait-elle entrer dans le radar ?
  options: [Adopter, Essayer, Évaluer, Suspendre]
  answer: 2
  explain: Évaluer, puis Essayer sur un vrai projet limité, puis Adopter. Pas de raccourci.
```
