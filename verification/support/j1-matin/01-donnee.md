---
subtitle: >-
  Le mot « donnée » semble évident. Pourtant, une donnée seule ne sert à rien : elle prend de la
  valeur quand elle devient une information, puis une connaissance, puis une décision.
objectives:
  - Présenter le fil rouge ColisVert et préparer ses données
  - Distinguer donnée, information, connaissance et décision
  - Classer une donnée en structurée, semi-structurée ou non structurée
  - Expliquer le rôle des métadonnées
---

{#colisvert}
## Le fil rouge de la semaine : ColisVert

**ColisVert** est un transporteur fictif. Il expédie des colis depuis **4 entrepôts** : Lille, Lyon, Nantes et Toulouse. Chaque colis a un **délai promis** au client : 24 heures jusqu'à 150 km, 48 heures au-delà.

Le problème : **un colis sur six arrive en retard**. Les clients appellent, le service client offre des gestes commerciaux, et la direction veut que ça change.

Pendant cinq jours, vous allez aider ColisVert, étape par étape :

| Jour | Ce que vous construisez pour ColisVert |
|---|---|
| 1 | Le diagnostic, puis le versioning des données |
| 2 | Un modèle qui prédit les retards, suivi avec MLflow |
| 3 | Le pipeline automatisé avec Airflow |
| 4 | La surveillance de la qualité et le service du modèle |
| 5 | La gouvernance, la plateforme Delta Lake et les agents IA |

::: callout info Des données fictives, mais des chiffres vrais
Les données sont produites par un programme (`colisvert/donnees.py`) avec une **graine** fixe : tout le monde obtient exactement les mêmes colis, au même endroit, avec les mêmes retards. Les chiffres de ce support sont ceux que vous allez obtenir.
:::

{#mise-en-place}
## Préparer les données

:::: lab Mise en place | Créer les données de ColisVert | 5 min
Dans votre notebook `j1-matin.ipynb`, exécutez cette cellule (**Maj + Entrée**). Elle crée trois fichiers dans le dossier `data` du dépôt ; ce matin, on utilise les deux premiers.

```python title="Cellule 1 : les données"
from colisvert.donnees import preparer_donnees

dossier = preparer_donnees()
```

```plaintext title="Sortie attendue"
livraisons.csv : 5035 colis, dont 862 en retard
arrivees.csv : 56 jours
livraisons_brutes.csv : les mêmes colis, avec des défauts de qualité
```

Puis chargez les livraisons avec pandas. `shape` donne le nombre de lignes et de colonnes.

```python title="Cellule 2 : charger les livraisons"
import pandas as pd
from colisvert.donnees import DOSSIER_DATA

livraisons = pd.read_csv(DOSSIER_DATA / "livraisons.csv")
print(livraisons.shape)
```

```plaintext title="Sortie attendue"
(5035, 11)
```

**Vérification :** 5 035 lignes (une par colis) et 11 colonnes.

::: hint
`ModuleNotFoundError: No module named 'colisvert'` : le notebook n'a pas été ouvert depuis JupyterLab du conteneur, ou le conteneur a été démarré sans le script. Relancez `./scripts/demarrer.sh` et rouvrez http://localhost:8888.
:::
::::

Les deux fichiers du matin :

| Fichier | Contenu |
|---|---|
| `livraisons.csv` | 5 035 colis expédiés du lundi 7 septembre au dimanche 1er novembre 2026 (8 semaines) : entrepôt, client, créneau, distance, poids, météo, délai promis, délai réel, retard (1) ou non (0) |
| `arrivees.csv` | Chaque matin, l'heure d'arrivée du fichier des expéditions de la veille |

{#dikw}
## Donnée, information, connaissance, décision

**Pourquoi distinguer ces quatre mots ?** Parce qu'une entreprise ne paie pas pour stocker des données : elle paie pour **prendre de meilleures décisions**. Entre les deux, il y a trois marches.

Une analogie médicale :

| Marche | Exemple médical | Définition |
|---|---|---|
| **Donnée** | Le thermomètre affiche 38,7 | Un fait brut, sans contexte |
| **Information** | « Paul a de la fièvre depuis hier » | Une donnée mise en contexte, regroupée, comparée |
| **Connaissance** | « Fièvre et toux en hiver : probablement la grippe » | Une règle, une relation entre des informations |
| **Décision** | « Paul reste à la maison et se repose » | Une action, choisie grâce à la connaissance |

Faisons monter les données de ColisVert sur ces quatre marches.

:::: lab Démo | Monter les quatre marches avec ColisVert | 8 min
**Marche 1, la donnée.** Une ligne du fichier : un colis, des faits bruts.

```python title="Cellule 3 : une donnée"
print(livraisons.iloc[0])
```

```plaintext title="Sortie attendue"
id_colis               CV00001
date_expedition     2026-09-07
entrepot              Toulouse
client             particulier
creneau                   soir
distance_km                 53
poids_kg                  16.0
meteo                      sec
delai_promis_h              24
delai_reel_h                18
en_retard                    0
Name: 0, dtype: object
```

Ce colis a été livré en 18 heures pour 24 promises : pas de retard (`en_retard` vaut 0). Seul, ce fait ne dit rien sur l'entreprise.

**Marche 2, l'information.** On regroupe les colis par entrepôt et on calcule le pourcentage de retards. La moyenne d'une colonne de 0 et de 1 donne la part de 1 : on la multiplie par 100 pour avoir un pourcentage.

```python title="Cellule 4 : une information"
taux = livraisons.groupby("entrepot")["en_retard"].mean().mul(100).round(1)
print(taux.sort_values(ascending=False))
```

```plaintext title="Sortie attendue"
entrepot
Lille       27.5
Toulouse    13.9
Nantes      12.2
Lyon        12.0
Name: en_retard, dtype: float64
```

Lille a **27,5 %** de retards, plus du double des trois autres entrepôts.

**Marche 3, la connaissance.** On croise deux informations : l'entrepôt et la météo. `crosstab` construit un tableau à double entrée.

```python title="Cellule 5 : une connaissance"
croise = pd.crosstab(livraisons["entrepot"], livraisons["meteo"], values=livraisons["en_retard"], aggfunc="mean")
print(croise.mul(100).round(1))
```

```plaintext title="Sortie attendue"
meteo     pluie   sec
entrepot
Lille      53.2  17.7
Lyon       25.9   6.5
Nantes     26.9   6.0
Toulouse   31.0   6.2
```

La règle apparaît : **la pluie multiplie le risque de retard par 3 à 5**, et à Lille, sous la pluie, **plus d'un colis sur deux** arrive en retard (53,2 %).

**Marche 4, la décision.** Par exemple : les jours de pluie, Lille prévient ses clients le matin et ajoute une tournée l'après-midi. La donnée a fini par changer une action.
::::

::: callout remember À retenir
Une donnée ne vaut que par la **décision** qu'elle permet de prendre. Un pipeline DataOps sert à faire monter les données de la première à la dernière marche, **vite** et **sans erreur**.
:::

{#formes}
## Structurée, semi-structurée, non structurée

**Pourquoi les distinguer ?** Parce qu'elles ne se stockent et ne se traitent pas avec les mêmes outils.

| Forme | Ce que c'est | Exemple chez ColisVert | Où on la range |
|---|---|---|---|
| **Structurée** | Des lignes et des colonnes, un type par colonne | `livraisons.csv`, la table des clients | Base SQL, Data Warehouse |
| **Semi-structurée** | Des champs nommés, mais souples et imbriqués | Le message JSON envoyé par le scanner du livreur | Data Lake, base de documents |
| **Non structurée** | Ni lignes ni champs | La photo d'un colis abîmé, le texte d'une réclamation | Data Lake, stockage d'objets |

Le message d'un scanner ressemble à ceci : des champs nommés, dont un objet imbriqué (`position`) que n'a pas forcément chaque message.

```json title="Un évènement du scanner (semi-structuré)"
{"id_colis": "CV00001", "evenement": "livre", "heure": "2026-09-08T12:14:00",
 "position": {"lat": 43.60, "lon": 1.44}, "signature": true}
```

{#metadonnees}
## Les métadonnées : le catalogue de la bibliothèque

Une **métadonnée** est une **donnée sur la donnée** : son nom, son type, son unité, sa source, sa date de mise à jour, son propriétaire.

**L'analogie :** dans une bibliothèque, les livres sont les données. La **fiche du catalogue** (titre, auteur, rayon, date d'achat) est la métadonnée. Sans catalogue, les livres sont là, mais personne ne les trouve.

La première métadonnée est technique : le **type** de chaque colonne. pandas le devine en lisant le fichier.

```python title="Cellule 6 : les types des colonnes"
print(livraisons.dtypes)
```

```plaintext title="Sortie attendue"
id_colis               str
date_expedition        str
entrepot               str
client                 str
creneau                str
distance_km          int64
poids_kg           float64
meteo                  str
delai_promis_h       int64
delai_reel_h         int64
en_retard            int64
dtype: object
```

`str` désigne du texte, `int64` un nombre entier et `float64` un nombre à virgule. La date d'expédition est lue comme du texte : pandas ne la reconnaît pas tout seul. On la convertira quand on en aura besoin.

La seconde métadonnée est métier : le **dictionnaire des données**, qui explique chaque colonne en français.

| Colonne | Signification | Unité |
|---|---|---|
| `delai_promis_h` | Délai annoncé au client à l'expédition | heures |
| `delai_reel_h` | Temps écoulé entre l'expédition et la livraison | heures |
| `en_retard` | 1 si le délai réel dépasse le délai promis, sinon 0 | 0 ou 1 |

::: callout tip Question fréquente : « Pourquoi ne pas tout faire dans Excel ? »
Excel convient pour regarder 5 000 lignes une fois. Il ne convient plus quand le même calcul doit être refait **chaque nuit**, **à l'identique**, sur des millions de lignes, avec une trace de ce qui a été fait. C'est le sujet de la semaine.
:::

{#quiz}
## Quiz de validation

```quiz
- q: « Le colis CV00001 a été livré en 18 heures. » De quelle marche s'agit-il ?
  options: [Une donnée, Une information, Une connaissance, Une décision]
  answer: 0
  explain: C'est un fait brut sur un seul colis, sans regroupement ni comparaison.
- q: « Sous la pluie, le risque de retard est multiplié par 3 à 5. » De quelle marche s'agit-il ?
  options: [Une donnée, Une information, Une connaissance, Une décision]
  answer: 2
  explain: C'est une règle qui relie deux informations, la météo et le retard.
- q: Le message JSON envoyé par le scanner d'un livreur est une donnée…
  options: [structurée, semi-structurée, non structurée, binaire]
  answer: 1
  explain: Ses champs sont nommés, mais souples et parfois imbriqués.
- q: Qu'est-ce qu'une métadonnée ?
  options:
    - Une donnée très volumineuse
    - Une donnée sur la donnée, comme son type, sa source ou son propriétaire
    - Une donnée supprimée
    - Une donnée calculée par un modèle
  answer: 1
  explain: C'est la fiche du catalogue de la bibliothèque. Sans elle, on ne retrouve pas les données.
```
