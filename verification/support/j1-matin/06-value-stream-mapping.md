---
subtitle: >-
  On suit une demande de bout en bout, et on chronomètre. La surprise est presque toujours la
  même : le travail prend quelques heures, l'attente prend des jours.
objectives:
  - Définir temps de traitement, temps d'attente, délai total et efficacité du flux
  - Calculer le %C/A cumulé d'une chaîne d'étapes
  - Cartographier une chaîne de valeur et repérer la plus longue attente
  - Expliquer ce que DataOps cherche à supprimer dans une chaîne de valeur
---

{#principe}
## Suivre une demande de bout en bout

**Pourquoi cartographier ?** Parce qu'on améliore souvent ce qu'on voit (« Excel est lent, achetons un meilleur outil »), alors que le temps perdu est ailleurs : **entre** les étapes, quand le travail attend quelqu'un.

La **cartographie de la chaîne de valeur** (*Value Stream Mapping*, VSM) vient du **Lean**, la méthode de production de Toyota. On suit **une demande** depuis le moment où elle est exprimée jusqu'au moment où le client reçoit le résultat, et on note pour chaque étape combien de temps on **travaille** et combien de temps on **attend**.

**L'analogie :** un renouvellement de passeport. Le guichet traite votre dossier en 10 minutes. Mais entre la prise de rendez-vous, l'instruction et la fabrication, vous attendez 5 semaines. Accélérer le guichet ne changerait presque rien.

{#vocabulaire}
## Cinq mesures

| Mesure | Définition | Comment on la calcule |
|---|---|---|
| **Temps de traitement** | Le temps où quelqu'un travaille vraiment sur la demande | Somme des temps de chaque étape |
| **Temps d'attente** | Le temps où la demande attend entre deux étapes | Somme des attentes |
| **Délai total** (*lead time*) | Ce que voit le client : de la demande au résultat | Traitement + attente |
| **Efficacité du flux** | La part du délai pendant laquelle on travaille | Traitement ÷ délai total |
| **%C/A** (complet et exact) | La part des livrables qu'une étape reçoit utilisables sans les renvoyer | Estimée par l'étape suivante, en % |

Le **%C/A cumulé** est le produit des %C/A de toutes les étapes : c'est la part des demandes qui traversent toute la chaîne **sans aucune reprise**.

{#demo}
## La chaîne de valeur du rapport des retards

Aujourd'hui, chez ColisVert, le directeur des opérations demande chaque semaine un **rapport des retards**. Voici ce qui se passe, chronométré par l'équipe.

::: figure vsm-rapport.svg
Cinq étapes. Sur la ligne du temps, les créneaux du haut sont des attentes, ceux du bas du travail. L'étape en rouge est précédée de la plus longue attente.
:::

:::: lab Démo | Calculer les indicateurs de la chaîne | 8 min
On décrit chaque étape dans un DataFrame : son nom, son temps de traitement, l'**attente avant** l'étape, et son %C/A. Puis une fonction calcule les cinq mesures. On la réutilisera dans l'exercice et dans l'évaluation.

```python title="Cellule 13 : la chaîne de valeur du rapport"
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


rapport = pd.DataFrame({
    "etape": ["Demande du rapport", "Extraction des données", "Nettoyage dans Excel", "Validation qualité", "Mise en forme et envoi"],
    "traitement_h": [0.5, 2, 4, 1, 2],
    "attente_h": [0, 40, 24, 72, 16],
    "ca_pct": [90, 80, 70, 95, 100],
})
analyser_flux(rapport)
```

```plaintext title="Sortie attendue"
Temps de traitement : 9.5 h
Temps d'attente     : 152.0 h
Délai total         : 161.5 h, soit 6.7 jours
Efficacité du flux  : 5.9 %
%C/A cumulé         : 47.9 %
Plus longue attente : avant « Validation qualité »
```

**Ligne par ligne :**

- `etapes["traitement_h"].sum()` additionne la colonne : 0,5 + 2 + 4 + 1 + 2 = **9,5 h** de travail.
- Le délai total ajoute les **152 h** d'attente : **161,5 h**, presque **une semaine** pour un rapport qui demande un peu plus d'une journée de travail.
- L'efficacité du flux vaut 9,5 ÷ 161,5 = **5,9 %** : pendant 94 % du délai, la demande attend.
- `prod()` multiplie les %C/A : 0,90 × 0,80 × 0,70 × 0,95 × 1,00 = **0,479**. Moins d'un rapport sur deux traverse la chaîne sans reprise.
- `idxmax()` donne la ligne de la plus grande attente : **72 h avant la validation qualité**. Le responsable qualité ne valide que le jeudi.
::::

{#lecture}
## Ce que DataOps va supprimer

La carte montre où agir, et ce n'est pas Excel :

| Constat | Réponse DataOps | Quand |
|---|---|---|
| 152 h d'attente entre équipes | Un pipeline qui enchaîne les étapes tout seul, chaque nuit | Jour 3, Airflow |
| Un nettoyage manuel à 70 % de C/A | Des contrôles de qualité automatiques, au même endroit à chaque fois | Jours 1 et 4 |
| Une validation qui attend le jeudi | Des contrôles automatiques qui valident à chaque exécution, une alerte seulement en cas d'anomalie | Jour 4, MSP |
| Un rapport refait à la main chaque semaine | Un tableau de bord en libre-service | Jour 5 |

L'objectif n'est pas de travailler plus vite : c'est de **ne plus attendre**. C'est exactement ce que le programme appelle **minimiser le Time To Value** : le temps entre une question et sa réponse utile.

:::: lab Exercice | La chaîne de valeur d'une correction | 7 min
Un utilisateur signale une erreur dans le tableau de bord. Voici les étapes jusqu'à la mise en production de la correction. Créez le DataFrame, puis appelez `analyser_flux`.

| Étape | Traitement | Attente avant | %C/A |
|---|---|---|---|
| Signalement de l'erreur | 0,5 h | 0 h | 85 % |
| Analyse du ticket | 1 h | 24 h | 90 % |
| Correction du code | 3 h | 48 h | 75 % |
| Tests manuels | 2 h | 16 h | 80 % |
| Validation du chef de projet | 0,5 h | 96 h | 100 % |
| Mise en production | 1 h | 120 h | 90 % |

Questions : quel est le délai total en jours ? L'efficacité du flux ? Où agir en premier ?

::: hint
Reprenez la structure de la Cellule 13 : un dictionnaire avec les quatre colonnes `etape`, `traitement_h`, `attente_h`, `ca_pct`, une liste de six valeurs par colonne, dans l'ordre du tableau.
:::

::: solution
```python title="Cellule 14 : la correction"
correction = pd.DataFrame({
    "etape": ["Signalement de l'erreur", "Analyse du ticket", "Correction du code", "Tests manuels", "Validation du chef de projet", "Mise en production"],
    "traitement_h": [0.5, 1, 3, 2, 0.5, 1],
    "attente_h": [0, 24, 48, 16, 96, 120],
    "ca_pct": [85, 90, 75, 80, 100, 90],
})
analyser_flux(correction)
```

```plaintext title="Sortie attendue"
Temps de traitement : 8.0 h
Temps d'attente     : 304.0 h
Délai total         : 312.0 h, soit 13.0 jours
Efficacité du flux  : 2.6 %
%C/A cumulé         : 41.3 %
Plus longue attente : avant « Mise en production »
```

**13 jours** pour 8 heures de travail : l'efficacité du flux est de **2,6 %**. La plus longue attente (120 h) précède la mise en production : l'équipe ne déploie qu'une fois par semaine, dans un créneau fixe. Ensuite viennent les 96 h d'attente de la validation. Des tests automatiques et un déploiement automatisé (le principe du **CI/CD**, vu cet après-midi avec DevOps) supprimeraient la majeure partie de ces 216 heures.
:::
::::

::: callout tip Question fréquente : « Les temps d'attente sont-ils en heures ouvrées ? »
Ici, non : ce sont des heures **calendaires**, celles que vit le client (un week-end compte). C'est le choix le plus courant en VSM, parce que le délai total doit correspondre à ce que le client constate. L'important est de garder la même convention pour toute la carte.
:::

{#quiz}
## Quiz de validation

```quiz
- q: Comment calcule-t-on l'efficacité du flux ?
  options:
    - Temps d'attente ÷ temps de traitement
    - Temps de traitement ÷ délai total
    - Nombre d'étapes ÷ délai total
    - Délai total ÷ 24
  answer: 1
  explain: C'est la part du délai pendant laquelle quelqu'un travaille vraiment sur la demande.
- q: Une chaîne a trois étapes avec des %C/A de 90 %, 80 % et 50 %. Quel est le %C/A cumulé ?
  options: ["36 %", "50 %", "73 %", "220 %"]
  answer: 0
  explain: 0,9 × 0,8 × 0,5 = 0,36. Un peu plus d'une demande sur trois passe sans reprise.
- q: Le rapport des retards prend 9,5 h de travail et 161,5 h de délai total. Que faut-il améliorer en premier ?
  options:
    - La vitesse d'Excel
    - Les attentes entre les étapes, surtout les 72 h avant la validation
    - Le temps de mise en forme
    - Le nombre de colonnes du rapport
  answer: 1
  explain: 94 % du délai est de l'attente. Accélérer le travail ne changerait presque rien.
```
