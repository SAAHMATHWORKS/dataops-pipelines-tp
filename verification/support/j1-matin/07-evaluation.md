---
subtitle: >-
  La direction de ColisVert vous demande un premier diagnostic : des chiffres fiables,
  une définition claire du retard, l'état de la fraîcheur des données et la chaîne de valeur
  des réclamations clients.
objectives:
  - Préparer les données et vérifier leur forme
  - Transformer des données en informations
  - Mesurer l'effet d'une définition sur un indicateur
  - Vérifier un engagement de fraîcheur
  - Calculer les indicateurs d'une chaîne de valeur
# Barème : 14 points pour les étapes (indiqués sur chaque étape) + 6 points pour le QCM
quiz_points: 6
---

{#consignes}
## Consignes

**Scénario.** Vous rejoignez l'équipe data de ColisVert. Avant de lancer le moindre projet, la direction veut un diagnostic chiffré. Vous le produisez dans un notebook neuf.

- **Durée :** 30 minutes, en autonomie. Le formateur passe voir chacun.
- **Où :** dans JupyterLab, créez un notebook `j1-matin-evaluation.ipynb` dans le dossier `notebooks`. Il doit fonctionner seul : n'utilisez pas les variables du notebook de la matinée.
- **Validation :** chaque étape se termine par une **preuve** : collez la sortie de votre cellule et cliquez sur « Envoyer ma preuve ». Le formateur voit vos preuves en direct et s'en sert pour vous noter.
- **Barème :** 14 points pour les 5 étapes, 6 points pour le QCM final (une seule tentative par question).
- Les corrections sont là si vous bloquez, mais essayez d'abord.

::: widget task-progress
:::

{#donnees}
## Les données

:::: task Étape 1 | Préparer et charger les données | 4 min | 2 pts
Dans la première cellule :

1. importez pandas, `DOSSIER_DATA` et `preparer_donnees` depuis `colisvert.donnees` ;
2. appelez `preparer_donnees()` ;
3. chargez `livraisons.csv` dans `livraisons` et `arrivees.csv` dans `arrivees` ;
4. affichez la forme (`shape`) des deux tables, sur une seule ligne.

**Vérification :** 5 035 colis et 56 jours.

::: proof Collez la sortie complète de votre première cellule
:::

::: hint
`print(livraisons.shape, arrivees.shape)` affiche les deux formes sur une ligne. Reprenez les Cellules 1 et 2 de la matinée, et la Cellule 11 pour `arrivees.csv`.
:::

::: solution
```python title="Évaluation · Cellule 1"
import pandas as pd
from colisvert.donnees import DOSSIER_DATA, preparer_donnees

dossier = preparer_donnees()
livraisons = pd.read_csv(DOSSIER_DATA / "livraisons.csv")
arrivees = pd.read_csv(DOSSIER_DATA / "arrivees.csv")
print(livraisons.shape, arrivees.shape)
```

```plaintext title="Sortie attendue"
livraisons.csv : 5035 colis, dont 862 en retard
arrivees.csv : 56 jours
livraisons_brutes.csv : les mêmes colis, avec des défauts de qualité
(5035, 11) (56, 2)
```
:::
::::

{#information}
## De la donnée à l'information

:::: task Étape 2 | Le taux de retard par créneau et par type de client | 7 min | 4 pts
Calculez le **taux de retard en %**, arrondi à une décimale :

1. par **créneau** de livraison (colonne `creneau`) ;
2. par **type de client** (colonne `client`).

Affichez les deux résultats. Puis répondez dans votre notebook, dans une cellule de texte (**Markdown**) : quel créneau pose problème ? Le type de client est-il un facteur de retard ?

::: proof Collez la sortie de votre cellule, suivie de vos deux réponses
:::

::: hint
C'est la Cellule 4 de la matinée, en remplaçant `"entrepot"` par `"creneau"`, puis par `"client"`. La moyenne d'une colonne de 0 et de 1, multipliée par 100, donne un pourcentage.
:::

::: solution
```python title="Évaluation · Cellule 2"
print(livraisons.groupby("creneau")["en_retard"].mean().mul(100).round(1))
print(livraisons.groupby("client")["en_retard"].mean().mul(100).round(1))
```

```plaintext title="Sortie attendue"
creneau
apres-midi    13.4
matin         13.6
soir          24.1
Name: en_retard, dtype: float64
client
particulier    17.2
pro            16.8
Name: en_retard, dtype: float64
```

Le **créneau du soir** a **24,1 %** de retards, presque le double du matin et de l'après-midi (13,6 % et 13,4 %). Le **type de client n'est pas un facteur** : 17,2 % contre 16,8 %, un écart trop faible pour en tirer une règle. Savoir qu'une variable **ne compte pas** est aussi une connaissance : inutile d'en faire un critère de décision.
:::
::::

{#semantique}
## La définition du retard

:::: task Étape 3 | Une tolérance de 2 heures | 6 min | 3 pts
Un directeur propose de ne compter un retard qu'**au-delà de 2 heures** de dépassement du délai promis. Calculez, avec cette définition, le **nombre** de colis en retard et le **taux**, avec **deux décimales** (format `:.2%`).

Comparez au taux officiel (17,1 %) et au résultat clé RC1 (« moins de 12 % »), puis écrivez votre conclusion en une phrase.

::: proof Collez la sortie de votre cellule, suivie de votre conclusion
:::

::: hint
C'est la Cellule 10 de la matinée, avec `+ 2` au lieu de `+ 4`. Le format `f"{valeur:.2%}"` multiplie par 100 et affiche deux décimales suivies de `%`.
:::

::: solution
```python title="Évaluation · Cellule 3"
tolerance_2h = livraisons["delai_reel_h"] > livraisons["delai_promis_h"] + 2
print(f"Retards avec 2 h de tolérance : {tolerance_2h.sum()} colis, {tolerance_2h.mean():.2%}")
```

```plaintext title="Sortie attendue"
Retards avec 2 h de tolérance : 603 colis, 11.98%
```

Avec 2 heures de tolérance, le taux passe de 17,1 % à **11,98 %** : le RC1 « moins de 12 % » serait **atteint sans livrer un seul colis plus vite**. Changer la définition d'un indicateur pour atteindre son objectif est le piège classique : c'est pourquoi la définition officielle est fixée par la **gouvernance**, dans le glossaire, et ne change pas en cours de route.
:::
::::

{#fraicheur}
## La fraîcheur des données

:::: task Étape 4 | Un nouvel engagement de fraîcheur | 5 min | 2 pts
L'équipe propose un engagement plus exigeant : le fichier de la veille arrive **au plus tard à 06:40, au moins 80 % des jours**.

Calculez le nombre de jours où le fichier est arrivé à 06:40 ou avant, le pourcentage correspondant, et le nombre de jours de retard autorisés par le budget d'erreur. L'engagement est-il tenu ?

::: proof Collez la sortie de votre cellule, suivie de votre réponse
:::

::: hint
C'est la Cellule 11 de la matinée, avec `"06:40"` au lieu de `"07:00"` et `0.2` au lieu de `0.05` : le budget d'erreur d'un engagement à 80 % est de 20 % des jours.
:::

::: solution
```python title="Évaluation · Cellule 4"
avant_0640 = arrivees["heure_arrivee"] <= "06:40"
print(f"Fichier à 06:40 au plus tard : {avant_0640.sum()} jours sur {len(arrivees)}, soit {avant_0640.mean():.1%}")
print(f"Jours en retard : {(~avant_0640).sum()}, budget d'erreur : {int(len(arrivees) * 0.2)} jours")
```

```plaintext title="Sortie attendue"
Fichier à 06:40 au plus tard : 45 jours sur 56, soit 80.4%
Jours en retard : 11, budget d'erreur : 11 jours
```

L'engagement est **tenu, de justesse** : 80,4 % pour 80 % demandés, et 11 jours de retard pour 11 autorisés. Un seul incident de plus le ferait échouer : ce n'est pas un engagement sur lequel on peut construire un service.
:::
::::

{#chaine-de-valeur}
## La chaîne de valeur des réclamations

:::: task Étape 5 | Cartographier le traitement d'une réclamation | 8 min | 3 pts
Voici, chronométré, le traitement d'une réclamation client.

| Étape | Traitement | Attente avant | %C/A |
|---|---|---|---|
| Réception de la réclamation | 0,2 h | 0 h | 95 % |
| Recherche du colis | 1,5 h | 8 h | 70 % |
| Question à l'entrepôt | 0,3 h | 4 h | 90 % |
| Réponse de l'entrepôt | 0,5 h | 48 h | 85 % |
| Décision du geste commercial | 0,3 h | 24 h | 100 % |
| Réponse au client | 0,2 h | 6 h | 95 % |

Recopiez la fonction `analyser_flux` de la Cellule 13 dans votre notebook, créez le DataFrame `reclamation`, puis appelez la fonction. Quelle étape faut-il traiter en premier ?

::: proof Collez la sortie de analyser_flux(reclamation), suivie de votre réponse
:::

::: hint
Les quatre colonnes s'appellent `etape`, `traitement_h`, `attente_h` et `ca_pct`. Écrivez les nombres avec un point décimal : `0.2`, pas `0,2`. L'attente de la première étape vaut 0.
:::

::: solution
```python title="Évaluation · Cellule 5"
def analyser_flux(etapes):
    """Affiche les indicateurs Lean d'une chaîne d'étapes."""
    traitement = etapes["traitement_h"].sum()
    attente = etapes["attente_h"].sum()
    total = traitement + attente
    ca_cumule = (etapes["ca_pct"] / 100).prod() * 100
    goulot = etapes.loc[etapes["attente_h"].idxmax(), "etape"]
    print(f"Temps de traitement : {traitement:.1f} h")
    print(f"Temps d'attente     : {attente:.1f} h")
    print(f"Délai total         : {total:.1f} h, soit {total / 24:.1f} jours")
    print(f"Efficacité du flux  : {traitement / total * 100:.1f} %")
    print(f"%C/A cumulé         : {ca_cumule:.1f} %")
    print(f"Plus longue attente : avant « {goulot} »")


reclamation = pd.DataFrame({
    "etape": ["Réception de la réclamation", "Recherche du colis", "Question à l'entrepôt", "Réponse de l'entrepôt", "Décision du geste commercial", "Réponse au client"],
    "traitement_h": [0.2, 1.5, 0.3, 0.5, 0.3, 0.2],
    "attente_h": [0, 8, 4, 48, 24, 6],
    "ca_pct": [95, 70, 90, 85, 100, 95],
})
analyser_flux(reclamation)
```

```plaintext title="Sortie attendue"
Temps de traitement : 3.0 h
Temps d'attente     : 90.0 h
Délai total         : 93.0 h, soit 3.9 jours
Efficacité du flux  : 3.2 %
%C/A cumulé         : 48.3 %
Plus longue attente : avant « Réponse de l'entrepôt »
```

Le client attend **3,9 jours** une réponse qui demande **3 heures** de travail. La priorité est l'attente de **48 h** avant la réponse de l'entrepôt : si le service client pouvait consulter lui-même l'historique du colis (une donnée en libre-service), les étapes « Question à l'entrepôt » et « Réponse de l'entrepôt » disparaîtraient, avec leurs 52 heures d'attente. La « Recherche du colis », à 70 % de C/A, est le second chantier.
:::
::::

{#quiz}
## Quiz : vos résultats

Répondez à partir de la matinée et de ce que vous venez de calculer. **Une seule tentative par question** : votre première réponse est enregistrée et compte pour la note.

```quiz
- q: « Les retards coûtent environ 67 000 € par an à ColisVert. » Sur quelle marche se situe cette phrase ?
  options: [Une donnée, Une information, Une connaissance, Une décision]
  answer: 1
  explain: C'est un regroupement chiffré, mis en contexte. Ce n'est pas encore une règle, ni une action.
- q: Quelle architecture ajoute un journal de transactions aux fichiers ouverts d'un lac de données ?
  options: [Le Data Warehouse, Le Data Mesh, Le Lakehouse, Le tableur partagé]
  answer: 2
  explain: Delta Lake, Iceberg et Hudi apportent écritures tout ou rien, contrôle du schéma et voyage dans le temps.
- q: Avec 2 heures de tolérance, le taux de retard passe sous 12 %. Que faut-il en conclure ?
  options:
    - L'objectif RC1 est atteint
    - Les livraisons se sont améliorées
    - La définition change le chiffre, pas la réalité ; elle doit être fixée par la gouvernance
    - Il faut passer à 4 heures de tolérance
  answer: 2
  explain: Aucun colis n'est arrivé plus vite. La définition officielle est inscrite au glossaire et ne change pas pour atteindre un objectif.
- q: Qui décide de la définition officielle d'un indicateur comme le taux de retard ?
  options:
    - L'équipe qui construit le pipeline
    - La gouvernance des données, avec le propriétaire des données
    - Le fournisseur du logiciel
    - Chaque service, selon ses besoins
  answer: 1
  explain: C'est le rôle de la gouvernance et du propriétaire des données, ici la direction du service client.
- q: Quel est le délai total du traitement d'une réclamation ?
  options: ["3,0 heures", "3,9 jours", "48 heures", "13 jours"]
  answer: 1
  explain: 3 heures de traitement et 90 heures d'attente font 93 heures, soit 3,9 jours.
- q: Dans la chaîne de valeur des réclamations, quelle action réduirait le plus le délai ?
  options:
    - Répondre plus vite au client, qui prend 0,2 h
    - Donner au service client un accès direct à l'historique du colis
    - Ajouter une étape de validation
    - Accélérer la réception de la réclamation
  answer: 1
  explain: Les échanges avec l'entrepôt représentent 52 heures d'attente sur 93. Les supprimer est plus efficace que d'accélérer le travail.
```
