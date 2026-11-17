---
subtitle: >-
  Une donnée a de la valeur quand elle change une décision, et elle n'est utile que si tout le
  monde lui donne le même sens. La stratégie des données organise ces deux conditions.
objectives:
  - Chiffrer la valeur d'une donnée à partir du coût d'un problème métier
  - Montrer qu'un même mot peut produire deux chiffres différents
  - Expliquer le rôle d'un glossaire métier
  - Relier les données au processus métier qui les produit (BPM)
  - Définir ce qu'est une stratégie des données
---

{#valeur}
## Ce que vaut une donnée

**Pourquoi chiffrer ?** Parce qu'un projet data coûte : des personnes, des serveurs, des licences. La direction le financera si l'on montre **ce qu'il rapporte**. Et une donnée rapporte quand elle permet d'éviter un coût ou de gagner un client.

Chez ColisVert, chaque retard coûte : un appel au service client, un geste commercial, parfois un client perdu. Pour l'exercice, on retient **12 € par retard**. C'est une hypothèse, à valider avec le service financier.

:::: lab Démo | Combien coûtent les retards ? | 4 min
Le fichier couvre 8 semaines, soit 56 jours. On extrapole à une année de 365 jours.

```python title="Cellule 9 : le coût des retards"
nb_retards = int(livraisons["en_retard"].sum())
cout_par_retard = 12                       # hypothèse de l'exercice, en euros
cout_8_semaines = nb_retards * cout_par_retard
cout_annuel = cout_8_semaines / 56 * 365

print(f"Retards en 8 semaines : {nb_retards}")
print(f"Coût en 8 semaines    : {cout_8_semaines:,} €".replace(",", " "))
print(f"Coût sur un an        : {cout_annuel:,.0f} €".replace(",", " "))
print(f"Gain si on évite un retard sur quatre : {cout_annuel / 4:,.0f} € par an".replace(",", " "))
```

```plaintext title="Sortie attendue"
Retards en 8 semaines : 862
Coût en 8 semaines    : 10 344 €
Coût sur un an        : 67 421 €
Gain si on évite un retard sur quatre : 16 855 € par an
```

Le format `:,` sépare les milliers par une virgule ; `.replace(",", " ")` la remplace par une espace, à la française.

**Lecture :** les retards coûtent environ **67 000 € par an**. Un modèle qui permettrait d'en éviter un sur quatre rapporterait près de **17 000 € par an**. C'est le budget maximal raisonnable pour le construire et le faire tourner. Cette question reviendra le jour 3 (acheter ou construire ?) et le jour 4 (mesurer les bénéfices).
::::

{#semantique}
## Un mot, deux chiffres : la sémantique

**La sémantique d'une donnée, c'est son sens.** Et le même mot peut avoir deux sens dans la même entreprise.

Chez ColisVert, deux services parlent de « retard » :

- le **service client** compte un retard **dès la première heure** de dépassement : c'est ce que voit le client ;
- l'**exploitation** accorde **4 heures de tolérance** : selon elle, un colis livré 3 heures après l'heure promise est « à l'heure ».

:::: lab Démo | Le même mot, deux définitions | 4 min
On compare un délai réel à un délai promis. Chaque comparaison donne `True` (vrai) ou `False` (faux) pour chaque colis. `sum()` compte les `True`, `mean()` donne leur proportion.

```python title="Cellule 10 : deux définitions du retard"
service_client = livraisons["delai_reel_h"] > livraisons["delai_promis_h"]
exploitation = livraisons["delai_reel_h"] > livraisons["delai_promis_h"] + 4

print(f"Service client (dès la 1re heure) : {service_client.sum()} colis, {service_client.mean():.1%}")
print(f"Exploitation (4 h de tolérance)   : {exploitation.sum()} colis, {exploitation.mean():.1%}")
```

```plaintext title="Sortie attendue"
Service client (dès la 1re heure) : 862 colis, 17.1%
Exploitation (4 h de tolérance)   : 400 colis, 7.9%
```

En réunion de direction, le service client annonce **17,1 %** de retards, l'exploitation **7,9 %**. Les deux ont raison, avec leur définition. La réunion tourne au dialogue de sourds.
::::

La solution n'est pas technique : c'est un **glossaire métier**, un document partagé qui donne **une seule définition officielle** à chaque terme, avec son propriétaire.

| Terme | Définition officielle | Calcul | Propriétaire |
|---|---|---|---|
| **Retard** | Colis livré après le délai promis au client, sans tolérance | `delai_reel_h > delai_promis_h` | Direction du service client |
| **Taux de retard** | Part des colis en retard sur une période | `retards / colis expédiés` | Direction du service client |

::: callout remember À retenir
Avant d'automatiser un calcul, on se met d'accord sur sa **définition**. Un pipeline parfaitement automatisé qui calcule la mauvaise chose produit des erreurs plus vite, c'est tout.
:::

{#bpm}
## Les données naissent dans les processus (BPM)

**Pourquoi parler de processus ?** Parce qu'une donnée n'apparaît pas toute seule : elle est **produite par une étape** du travail de quelqu'un. Le **BPM** (*Business Process Management*, gestion des processus métier) consiste à décrire ces étapes, les mesurer et les améliorer. On les dessine souvent avec la notation **BPMN**.

::: figure processus-livraison.svg
Chaque étape du processus de livraison produit une partie des colonnes de `livraisons.csv`.
:::

Conséquence pratique : si le livreur scanne les colis en fin de tournée plutôt qu'à chaque livraison, `delai_reel_h` est faux, et aucun nettoyage ne le rattrapera. **Pour améliorer une donnée, on améliore souvent l'étape qui la produit.**

{#strategie}
## La stratégie des données

Une **stratégie des données** est le plan qui relie **les objectifs de l'entreprise** aux **données**. Elle répond à quatre questions, dans cet ordre :

| Question | Chez ColisVert |
|---|---|
| **1. Quelles décisions veut-on améliorer ?** | Prévenir les clients et renforcer les tournées avant un retard |
| **2. Quelles données faut-il pour cela ?** | Livraisons, météo prévue, charge des entrepôts |
| **3. Qui en est responsable ?** | L'exploitation pour les livraisons, le service client pour la définition du retard |
| **4. Avec quelle plateforme ?** | Le pipeline automatisé que vous construirez cette semaine |

::: callout warn L'erreur la plus fréquente
Commencer par la question 4 : « On achète tel outil, puis on verra. » L'outil vient **en dernier**, quand on sait quelles décisions il doit servir.
:::

{#avance}
## Pour aller plus loin : évaluer les priorités, pas seulement les idées

Ce bloc est pour les profils avancés ; rien ici n'est exigé dans l'évaluation.

**Le problème réel d'un comité data n'est pas de trouver des idées, c'est d'en refuser.** Deux outils servent à décider.

**1. Un modèle de maturité**, pour savoir d'où l'on part. Les cabinets en proposent beaucoup ; tous racontent la même progression :

| Niveau | L'entreprise | ColisVert aujourd'hui |
|---|---|---|
| 1. Initial | Des extractions à la main, des chiffres qui divergent | ✔ c'est ici |
| 2. Reproductible | Les calculs clés sont en code, versionnés | objectif de cette semaine |
| 3. Automatisé | Pipelines orchestrés, contrôles de qualité, alertes | objectif à 6 mois |
| 4. Mesuré | Engagements chiffrés tenus, coûts et bénéfices suivis | |
| 5. Optimisé | Expérimentation continue, libre-service généralisé | |

L'intérêt n'est pas le score : c'est d'**interdire de sauter des marches**. Proposer du temps réel (niveau 5) à une entreprise qui recopie des chiffres dans Excel (niveau 1) échoue presque toujours : chaque niveau s'appuie sur les réflexes du précédent.

**2. Une matrice valeur × faisabilité**, pour classer le portefeuille de projets. On note chaque projet candidat : valeur annuelle estimée, coût de construction, faisabilité de 1 (données absentes, équipe à recruter) à 5 (données prêtes, compétences internes).

```python title="Cellule bonus A : prioriser le portefeuille data de ColisVert"
projets = pd.DataFrame({
    "projet": ["Contrôles qualité automatisés", "Prédiction des retards", "Chatbot état des colis",
               "Tableau de bord temps réel", "Optimisation des tournées"],
    "valeur_keur_an": [12, 17, 25, 30, 90],
    "cout_keur": [8, 25, 40, 60, 150],
    "faisabilite": [5, 4, 3, 3, 2],
})
projets["priorite"] = (projets["valeur_keur_an"] / projets["cout_keur"] * projets["faisabilite"]).round(1)
print(projets.sort_values("priorite", ascending=False).to_string(index=False))
```

```plaintext title="Sortie attendue"
                       projet  valeur_keur_an  cout_keur  faisabilite  priorite
Contrôles qualité automatisés              12          8            5       7.5
       Prédiction des retards              17         25            4       2.7
       Chatbot état des colis              25         40            3       1.9
   Tableau de bord temps réel              30         60            3       1.5
    Optimisation des tournées              90        150            2       1.2
```

**Lecture :** le projet le plus « spectaculaire » (l'optimisation des tournées, 90 k€ de valeur) finit **dernier** : trop cher, trop incertain aujourd'hui. Le premier est le moins visible : les contrôles de qualité. C'est le classement typique d'une organisation au niveau 1 ou 2 de maturité : **les fondations d'abord**, parce qu'elles rendent tous les autres projets moins chers et plus sûrs. Et c'est exactement l'ordre de cette semaine.

Trois mises en garde d'expérience : les valeurs sont des **hypothèses à dater et à réviser** (le score sert à discuter, pas à trancher seul) ; un projet réglementaire obligatoire court-circuite la matrice ; et un score ne remplace pas la question du **coût d'opportunité**, ce que l'équipe ne fera pas pendant ce temps.

{#quiz}
## Quiz de validation

```quiz
- q: D'où vient la valeur d'une donnée ?
  options:
    - De son volume
    - De la décision qu'elle permet de prendre, et du coût évité ou du gain obtenu
    - De son ancienneté
    - De l'outil qui la stocke
  answer: 1
  explain: Chez ColisVert, éviter un retard sur quatre vaudrait environ 17 000 € par an.
- q: Le service client annonce 17,1 % de retards, l'exploitation 7,9 %. Pourquoi ?
  options:
    - L'un des deux s'est trompé dans son calcul
    - Ils n'utilisent pas les mêmes données
    - Ils n'ont pas la même définition du mot « retard »
    - Les données ont changé entre-temps
  answer: 2
  explain: Même données, même calcul, mais une tolérance de 4 heures d'un côté. C'est un problème de sémantique.
- q: À quoi sert un glossaire métier ?
  options:
    - À traduire les données en anglais
    - À donner une seule définition officielle à chaque terme, avec son propriétaire
    - À stocker les données
    - À lister les tables de la base
  answer: 1
  explain: Il évite que deux services calculent deux chiffres différents sous le même nom.
- q: Par quelle question une stratégie des données doit-elle commencer ?
  options:
    - Quel outil acheter ?
    - Quelles décisions veut-on améliorer ?
    - Combien de données stocker ?
    - Quel cloud choisir ?
  answer: 1
  explain: L'outil vient en dernier, quand on sait quelles décisions il doit servir.
```
