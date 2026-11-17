---
subtitle: >-
  Trois entreprises fictives, trois situations que l'on rencontre partout. Pour chacune, posez
  le diagnostic avec le vocabulaire de la journée, puis proposez la réponse DataOps.
objectives:
  - Reconnaître dans une situation réelle les problèmes vus dans la journée
  - Proposer une réponse DataOps argumentée
  - Relier chaque réponse aux outils de la semaine
---

{#methode}
## La méthode

Pour chaque cas, en binôme ou à tour de rôle, répondez à trois questions :

1. **Quel est le symptôme ?** Ce que l'entreprise constate.
2. **Quelle est la cause ?** Avec les mots de la journée : gaspillage, dimension de qualité, mur de la confusion, héroïsme, absence de versioning…
3. **Quelle réponse DataOps ?** Et avec quel outil de la semaine.

Les trois entreprises sont **fictives**. Les situations, elles, sont courantes.

{#banque}
## Cas 1 : la banque et son rapport réglementaire

:::: lab Cas 1 | Le rapport de fin de mois | 3 min
Chaque mois, une banque régionale doit envoyer un rapport à son autorité de contrôle. Une analyste expérimentée le prépare : elle extrait les données de quatre systèmes, les assemble dans un classeur Excel de 30 onglets et corrige les écarts « de mémoire ». Cela lui prend dix jours. Le mois dernier, elle était en congé : le rapport est parti en retard, avec deux erreurs relevées par l'autorité.

Symptôme, cause, réponse DataOps ?

::: solution Une réponse possible
- **Symptôme :** un rapport lent, fragile, et faux quand une seule personne est absente.
- **Causes :** l'**héroïsme** (principe n° 7 du manifeste), des corrections non écrites, aucun **contrôle de qualité** automatique, aucun **versioning**.
- **Réponse DataOps :** écrire l'assemblage et les corrections **en code** (principe n° 9), ajouter des **contrôles de qualité** comme le rapport de cet après-midi, **versionner** données et code (Git et DVC), puis **orchestrer** le tout chaque mois (Airflow, jour 3). L'analyste passe de « celle qui fait le rapport » à « celle qui améliore le pipeline ».
:::
::::

{#ecommerce}
## Cas 2 : le site marchand et son modèle

:::: lab Cas 2 | Les recommandations qui se dégradent | 3 min
Un site de vente en ligne a mis en production un modèle qui recommande des produits. Au lancement, les ventes issues des recommandations augmentent. Trois mois plus tard, elles ont baissé de moitié. Aucune erreur technique : le modèle répond toujours. Personne ne sait plus avec quelles données il a été entraîné, et le data scientist qui l'a construit a quitté l'entreprise.

Symptôme, cause, réponse DataOps ?

::: solution Une réponse possible
- **Symptôme :** un modèle qui se dégrade **en silence**.
- **Causes :** la **dérive** des données (les habitudes d'achat ont changé, la saison aussi), aucune **surveillance** du modèle, aucun lien entre le modèle et les **données d'entraînement**.
- **Réponse MLOps :** enregistrer chaque entraînement avec ses paramètres, ses résultats et l'empreinte des données (MLflow et DVC, jour 2), **surveiller la dérive** (Evidently, jour 2), et pouvoir réentraîner et redéployer en une commande.
:::
::::

{#hopital}
## Cas 3 : l'hôpital et ses lits disponibles

:::: lab Cas 3 | Le tableau de bord des lits | 3 min
Un hôpital affiche aux urgences le nombre de lits disponibles par service. Le tableau est mis à jour une fois par jour, à la main, à partir de quatre logiciels. Les urgentistes ne s'y fient plus : il est faux dès 10 h, et ils téléphonent aux services. La direction veut une mise à jour toutes les heures. La DSI répond qu'il faut d'abord un projet de 18 mois.

Symptôme, cause, réponse DataOps ?

::: solution Une réponse possible
- **Symptôme :** un indicateur que personne n'utilise, faute d'être frais.
- **Causes :** un problème de **fraîcheur** (dimension de qualité), un traitement **manuel**, et un **mur de la confusion** entre le besoin métier et la DSI.
- **Réponse DataOps :** fixer un **engagement de fraîcheur** chiffré (« à jour à l'heure près, 99 % du temps »), automatiser l'extraction et l'assemblage dans un pipeline **orchestré** toutes les heures (Airflow, jour 3), et livrer **par petits morceaux** (un service hospitalier, puis deux, puis tous) plutôt qu'en 18 mois. Les données de santé demandent en plus une **gouvernance** stricte des accès (jour 5).
:::
::::

{#quiz}
## Quiz de validation

```quiz
- q: Dans le cas de la banque, quel principe du manifeste DataOps est le plus directement en cause ?
  options:
    - Réduire l'héroïsme
    - Des environnements jetables
    - Réutiliser
    - Accueillir le changement
  answer: 0
  explain: Tout repose sur une personne et sa mémoire. Le rapport doit devenir un processus écrit en code et automatisé.
- q: Le modèle du site marchand répond toujours, mais ses recommandations ne vendent plus. Comment appelle-t-on ce phénomène ?
  options: [Un doublon, La dérive, Un plantage, Une fuite de mémoire]
  answer: 1
  explain: Le monde a changé depuis l'entraînement. On la surveille avec des indicateurs, comme on le fera le jour 2.
- q: Pour le tableau de bord de l'hôpital, quelle dimension de la qualité pose problème en premier ?
  options: [L'unicité, La validité, La fraîcheur, La cohérence]
  answer: 2
  explain: Les chiffres sont justes à 8 h et faux à 10 h, faute d'être assez à jour.
```
