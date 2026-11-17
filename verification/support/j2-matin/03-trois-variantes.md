---
subtitle: >-
  Le même modèle peut vivre de trois façons : réentraîné à la main quand quelqu'un y pense,
  réentraîné automatiquement par un pipeline, ou porté par un pipeline lui-même testé et déployé
  automatiquement. Ce sont les trois variantes, ou niveaux d'automatisation, d'un pipeline de machine learning.
objectives:
  - Décrire les trois niveaux d'automatisation d'un pipeline de machine learning
  - Dire, pour chaque niveau, ce qui est livré en production et ce qui déclenche un réentraînement
  - Situer une équipe sur ces niveaux et proposer la marche suivante
  - Expliquer pourquoi le niveau le plus élevé n'est pas toujours le bon choix
---

{#pourquoi}
## Pourquoi parler de niveaux ?

**Le problème.** Deux équipes disent « on a un modèle en production ». Pour la première, un data scientist réentraîne le modèle sur son portable deux fois par an et envoie le fichier par email à la DSI. Pour la seconde, le modèle est réentraîné chaque nuit, comparé automatiquement au précédent, et remplacé seulement s'il est meilleur. Même phrase, deux réalités, deux niveaux de risque.

**Le cadre.** Les architectes de Google Cloud ont décrit trois niveaux d'automatisation des pipelines de machine learning, numérotés de 0 à 2. Ils sont devenus une référence pour dire où en est une équipe, et ce qui lui manque. Microsoft propose une grille voisine, plus fine, en cinq niveaux (de 0 à 4) pour Azure : l'idée est la même.

**L'analogie de la boulangerie.** Niveau 0 : le boulanger refait sa recette de mémoire chaque matin. Niveau 1 : la recette est écrite, le pétrin et le four sont programmés, le pain se fait chaque nuit sans lui. Niveau 2 : quand le boulanger modifie la recette, elle est d'abord testée sur une petite fournée, puis installée automatiquement sur toutes les machines de toutes les boutiques.

{#niveaux}
## Les trois niveaux

| | Niveau 0 : manuel | Niveau 1 : entraînement automatisé | Niveau 2 : CI/CD du pipeline |
|---|---|---|---|
| **Comment on entraîne** | À la main, dans un notebook ou des scripts lancés un par un | Un pipeline enchaîne les étapes sans intervention | Le même pipeline |
| **Ce qui est livré en production** | Un **modèle** (un fichier) | Le **pipeline** d'entraînement, qui produit les modèles | Le pipeline, **via une chaîne d'intégration et de déploiement continus** |
| **Ce qui déclenche un réentraînement** | Quelqu'un qui y pense | Un planning, l'arrivée de nouvelles données, une dérive détectée | Idem, et toute modification du code du pipeline |
| **Tests automatiques** | Aucun | Les données (validation) et le modèle (comparaison au précédent) | Ceux du niveau 1, **plus** le code du pipeline à chaque commit |
| **Fréquence typique des mises à jour** | Quelques fois par an | Chaque jour ou chaque semaine | Plusieurs fois par jour, pour plusieurs modèles |
| **Le risque principal** | Le modèle se dégrade sans que personne ne le voie | Un changement de code casse le pipeline en production | La complexité de l'outillage |

Le mot important du niveau 1 est **entraînement continu** (*continuous training*) : ce qu'on met en production n'est plus un modèle, c'est **la machine qui fabrique les modèles**. C'est une rupture : il faut alors valider automatiquement les données avant d'entraîner, et le modèle avant de le publier, puisque plus personne ne regarde chaque nouvelle version.

Le niveau 2 applique aux pipelines ce que le DevOps applique aux applications : **intégration continue** (chaque modification du code du pipeline est testée automatiquement) et **déploiement continu** (la nouvelle version du pipeline est installée automatiquement si les tests passent).

::: callout remember À retenir
Niveau 0 : on livre un modèle. Niveau 1 : on livre une machine à modèles. Niveau 2 : on livre la machine à modèles avec une chaîne qui la teste et l'installe automatiquement.
:::

{#colisvert}
## ColisVert au fil de la semaine

| Moment | Niveau | Ce qui change |
|---|---|---|
| Hier, avant le TP | 0, et même moins : rien n'est versionné | Les données changent sans trace |
| Ce matin, après le TP | **Entre 0 et 1** | Le pipeline est écrit (`dvc.yaml`) et reproductible, mais on le lance encore à la main avec `dvc repro` |
| Cet après-midi | Toujours entre 0 et 1 | Registre, déploiement, surveillance de la dérive : les briques du niveau 1 |
| Jour 3 | **Niveau 1** | Airflow lance le pipeline chaque matin, et dès que de nouvelles données arrivent |
| Le dépôt des TP lui-même | **Un élément du niveau 2** | À chaque modification, GitHub Actions rejoue le pipeline et vérifie que les chiffres du support sont toujours obtenus |

Le dernier point n'est pas une image : le dépôt que vous utilisez contient un workflow (`.github/workflows/`) qui reconstruit l'image et rejoue le pipeline à chaque modification. C'est ce qui garantit que vos chiffres sont les mêmes que ceux du support.

{#choisir}
## Le bon niveau n'est pas toujours le plus haut

Chaque niveau coûte : de l'outillage à maintenir, des compétences, du temps. Trois questions aident à choisir :

1. **Le monde change-t-il vite ?** Des données qui dérivent chaque semaine (prix, météo, comportements) justifient l'entraînement continu. Un modèle de détection de défauts sur une ligne de production stable, beaucoup moins.
2. **Combien de modèles ?** Un ou deux modèles se gèrent très bien au niveau 1. Des dizaines de modèles, mis à jour par plusieurs équipes, réclament le niveau 2.
3. **Que coûte une erreur ?** Un modèle qui décide d'un crédit ou d'un traitement médical demande des validations automatiques strictes, et une trace de chaque version.

Pour ColisVert, un seul modèle, des données qui dérivent avec les saisons, une erreur peu coûteuse (un client prévenu à tort) : **le niveau 1 est la bonne cible**. C'est celle de la semaine.

:::: lab Exercice | Diagnostiquer trois équipes | 5 min
Pour chaque équipe, donnez son niveau actuel et la prochaine marche.

1. Une assurance : un modèle de tarification réentraîné chaque trimestre par un data scientist, qui dépose le fichier du modèle sur un partage réseau. L'équipe informatique le recopie sur le serveur.
2. Un site de vente en ligne : 40 modèles de recommandation, réentraînés chaque nuit par des pipelines planifiés. Chaque modification du code d'un pipeline est testée à la main par la personne qui l'a écrite, puis installée en production par un ticket à l'équipe d'exploitation.
3. Une start-up : un pipeline Airflow réentraîne chaque semaine son unique modèle, le compare au précédent sur une semaine de test et le publie s'il est meilleur. Le code est dans Git, testé par GitHub Actions à chaque pull request, puis déployé automatiquement.

::: solution Voir le diagnostic
1. **Niveau 0.** Prochaine marche : écrire le pipeline et versionner données et modèles (ce que vous faites ce matin), puis le planifier.
2. **Niveau 1**, avec un vrai besoin du niveau 2 : avec 40 modèles et des tests manuels, chaque modification est un risque. Prochaine marche : tests automatiques du code des pipelines et déploiement automatisé.
3. **Niveau 2**, pour un seul modèle. Ce n'est pas un défaut si l'équipe le maîtrise ; la question à se poser est plutôt « que fait-on si la dérive arrive entre deux réentraînements hebdomadaires ? ».
:::
::::

{#avance}
## Pour aller plus loin : les niveaux dans Azure, Fabric et Google Cloud

Ce bloc est pour les profils avancés ; rien ici n'est exigé dans l'évaluation.

Les outils de la semaine (DVC, MLflow, Airflow, GitHub Actions) sont libres et portables. Dans un cloud, les mêmes briques existent sous forme de services managés :

| Brique | Cette semaine | Microsoft Azure | Microsoft Fabric | Google Cloud |
|---|---|---|---|---|
| Suivi des expériences | MLflow | Azure Machine Learning (compatible MLflow) | Expériences ML (basées sur MLflow) | Vertex AI Experiments |
| Pipeline d'entraînement | DVC | Pipelines Azure Machine Learning | Notebooks enchaînés dans un pipeline de données | Vertex AI Pipelines |
| Planification (niveau 1) | Airflow | Planifications de pipelines Azure ML, Data Factory | Pipelines de données planifiés | Cloud Composer (Airflow managé) |
| Registre des modèles | Registre MLflow | Registre de modèles Azure ML | Éléments « modèle ML » | Vertex AI Model Registry |
| CI/CD (niveau 2) | GitHub Actions | GitHub Actions ou Azure DevOps, avec la CLI Azure ML | Intégration Git et pipelines de déploiement de Fabric | Cloud Build |

Deux remarques d'architecte :

- **Azure Machine Learning et Fabric parlent MLflow.** Le code de suivi que vous écrivez ce matin fonctionne sans modification : seule l'adresse du serveur de suivi change. C'est un argument fort pour MLflow : il évite d'enfermer le suivi des expériences dans un fournisseur.
- **Le passage au niveau 2 est d'abord organisationnel.** Les outils de CI/CD existent partout. Ce qui manque le plus souvent, ce sont des **tests** à exécuter : tests du code de préparation, tests de schéma des données, seuils de performance minimaux. Sans eux, une chaîne de déploiement automatique ne fait qu'installer plus vite des erreurs.

{#quiz}
## Quiz de validation

```quiz
- q: Au niveau 1, que met-on en production ?
  options:
    - Un fichier de modèle, envoyé par email
    - Le pipeline d'entraînement, qui produit les nouveaux modèles
    - Uniquement un tableau de bord
    - Le notebook du data scientist
  answer: 1
  explain: C'est l'entraînement continu. On livre la machine à modèles, pas un modèle.
- q: Qu'ajoute le niveau 2 par rapport au niveau 1 ?
  options:
    - Un modèle plus précis
    - L'intégration et le déploiement continus du code du pipeline lui-même
    - Le versioning des données
    - Un serveur MLflow
  answer: 1
  explain: Chaque modification du pipeline est testée et installée automatiquement, comme une application en DevOps.
- q: Pourquoi faut-il valider automatiquement les données et le modèle dès le niveau 1 ?
  options:
    - Parce que la loi l'impose
    - Parce que plus personne ne regarde chaque nouvelle version avant qu'elle parte en production
    - Parce que MLflow ne fonctionne pas sans
    - Parce que cela accélère l'entraînement
  answer: 1
  explain: Quand le réentraînement est automatique, les contrôles doivent l'être aussi, sinon une erreur part en production sans témoin.
```
