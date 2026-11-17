---
subtitle: >-
  Trois mots qu'on confond souvent en réunion. Ils répondent pourtant à trois questions
  différentes, et ne sont pas portés par les mêmes personnes.
objectives:
  - Distinguer stratégie data, stratégie IT et gouvernance des données
  - Classer une décision dans la bonne catégorie
  - Expliquer pourquoi les trois doivent avancer ensemble
---

{#trois-questions}
## Trois questions différentes

**Pourquoi les distinguer ?** Parce qu'un projet échoue souvent faute d'avoir traité l'une des trois. On achète la plateforme (IT) sans savoir quelles décisions elle doit servir (data), ou on livre un beau modèle que personne n'a le droit d'utiliser (gouvernance).

| | Stratégie data | Stratégie IT | Gouvernance des données |
|---|---|---|---|
| **La question** | Quelles décisions améliorer, avec quelles données ? | Avec quels systèmes, quelle infrastructure, quel budget ? | Qui a le droit de faire quoi, avec quelles règles ? |
| **Qui la porte** | La direction générale et les métiers, souvent un CDO (*Chief Data Officer*) | La DSI (direction des systèmes d'information) | Un comité de gouvernance, des propriétaires et des gestionnaires de données |
| **Horizon** | 2 à 3 ans | 3 à 5 ans | Permanent |
| **Chez ColisVert** | Passer de 17,1 % à moins de 12 % de retards en 2027 grâce à la prédiction | Migrer les serveurs vers le cloud, choisir l'outil d'orchestration | La définition officielle du retard, l'accès aux adresses des clients (RGPD) |

**L'analogie de la ville :**

- la **stratégie data**, c'est l'**urbanisme** : quels quartiers construire, pour quels habitants ;
- la **stratégie IT**, ce sont les **travaux publics** : les routes, les réseaux d'eau et d'électricité ;
- la **gouvernance**, c'est le **code de la route et le cadastre** : qui possède quoi, qui a le droit de circuler où.

Une ville avec de belles routes mais sans plan d'urbanisme, ou sans code de la route, ne fonctionne pas.

{#roles}
## Les rôles de la gouvernance

La gouvernance confie chaque ensemble de données à des personnes nommées :

| Rôle | Responsabilité | Chez ColisVert |
|---|---|---|
| **Propriétaire des données** (*data owner*) | Décide qui accède, valide les définitions, répond de la qualité | Le directeur de l'exploitation, pour les livraisons |
| **Gestionnaire des données** (*data steward*) | Tient le glossaire et le catalogue, suit la qualité au quotidien | Une analyste de l'exploitation |
| **Équipe data** | Construit et fait tourner les pipelines | L'équipe que vous formez cette semaine |

::: callout info À retenir pour la suite
La gouvernance reviendra **le jour 5** (gouvernance, culture DataOps, IA responsable). Ce matin, retenez seulement qu'elle répond à la question « **qui** » ; la stratégie data à la question « **pourquoi** » ; la stratégie IT à la question « **avec quoi** ».
:::

:::: lab Exercice | Classer six décisions | 5 min
Pour chaque décision de ColisVert, dites si elle relève de la stratégie data, de la stratégie IT ou de la gouvernance.

1. « Les adresses des clients ne sont visibles que par le service client. »
2. « On veut prévenir les clients d'un retard avant qu'il ne se produise. »
3. « On remplace les serveurs de l'entrepôt de Lille par des machines dans le cloud. »
4. « Le retard se compte dès la première heure, sans tolérance. »
5. « On mesurera le succès du projet au taux de retard de fin 2027. »
6. « L'équipe data disposera d'un budget de 40 000 € pour les licences. »

::: solution Voir les réponses
1. **Gouvernance** : qui a le droit de voir quoi.
2. **Stratégie data** : la décision qu'on veut améliorer.
3. **Stratégie IT** : l'infrastructure.
4. **Gouvernance** : la définition officielle d'un terme, inscrite au glossaire.
5. **Stratégie data** : l'objectif mesurable lié à la décision.
6. **Stratégie IT** : le budget des systèmes.
:::
::::

{#quiz}
## Quiz de validation

```quiz
- q: « Les adresses des clients ne sont visibles que par le service client. » Cette règle relève…
  options: [de la stratégie data, de la stratégie IT, de la gouvernance des données, du DevOps]
  answer: 2
  explain: La gouvernance répond à la question « qui a le droit de faire quoi ».
- q: Quelle question la stratégie IT pose-t-elle ?
  options:
    - Quelles décisions améliorer ?
    - Avec quels systèmes, quelle infrastructure et quel budget ?
    - Qui est propriétaire des données ?
    - Quelle est la définition d'un retard ?
  answer: 1
  explain: C'est le domaine de la DSI, les « travaux publics » de l'analogie.
- q: Quel rôle tient au quotidien le glossaire et le catalogue des données ?
  options: [Le propriétaire des données, Le gestionnaire des données (data steward), Le directeur financier, Le fournisseur cloud]
  answer: 1
  explain: Le propriétaire décide et répond de la qualité ; le gestionnaire s'occupe des données au jour le jour.
```
