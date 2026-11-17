---
subtitle: >-
  Un projet data ne va pas en ligne droite de l'idée au modèle en production. Il traverse quatre
  phases, chacune avec sa question, son livrable et son critère de passage. Le plus important :
  savoir s'arrêter tôt quand une idée ne tient pas ses promesses.
objectives:
  - Nommer les quatre phases d'un projet data agile et la question de chacune
  - Associer à chaque phase un livrable et un critère de passage mesurable
  - Rédiger le critère de succès du modèle de ColisVert en langage métier puis en métrique
  - Expliquer pourquoi la recherche et développement se planifie en durée fixe
---

{#pourquoi}
## Pourquoi un processus ?

**Le problème.** Beaucoup de projets data s'arrêtent au prototype. Un data scientist obtient un bon résultat dans un notebook, tout le monde est content, puis plus rien : personne n'avait prévu qui ferait tourner le modèle chaque nuit, avec quelles données, ni comment on saurait qu'il se trompe. À l'inverse, d'autres projets tournent pendant des mois sans jamais montrer de résultat, parce que personne n'a fixé le moment où l'on décide d'arrêter.

**L'idée du DataOps.** Découper le projet en **phases courtes**, chacune avec **une question à trancher**, **un livrable** et **un critère de passage** chiffré. À chaque passage, on décide : continuer, revenir en arrière, ou arrêter. C'est l'esprit agile appliqué aux données : livrer petit, montrer souvent, décider sur des faits.

{#analogie}
## L'analogie du restaurant

Un chef veut ajouter un plat à la carte. Il ne le sert pas directement à cent clients :

1. **L'idée** : « un plat végétarien d'hiver ». Est-ce que ça vaut la peine ? Les clients en demandent-ils ?
2. **Le cadrage** : quels ingrédients, à quel coût, à quel prix de vente ? Combien de temps en cuisine pendant le coup de feu ?
3. **Les essais** : dix versions en cuisine, des dégustations, des ajustements. Peut-être l'abandon, si aucun essai n'est assez bon.
4. **La mise à la carte** : la fiche recette écrite, la brigade formée, l'approvisionnement organisé, et les retours des clients suivis chaque semaine.

Personne ne trouve étrange qu'un plat soit abandonné à l'étape 3. Dans un projet data, c'est pareil : **un modèle abandonné tôt est un succès du processus**, pas un échec.

{#phases}
## Les quatre phases

| Phase | La question | Ce qu'on fait | Le livrable | Critère de passage |
|---|---|---|---|---|
| **1. Idéation** | Quel problème vaut la peine d'être résolu ? | Recenser les idées, estimer valeur et faisabilité, choisir | Une fiche d'opportunité d'une page | La direction choisit l'idée et lui donne un budget |
| **2. Inception** (cadrage) | Peut-on le faire, et comment saura-t-on qu'on a réussi ? | Vérifier les données, fixer la métrique de succès et la ligne de base, lister les risques | Une charte de projet : objectif, métrique, seuil, données, équipe, critère d'arrêt | Les données existent et la métrique est acceptée par le métier |
| **3. Recherche et développement** | Atteint-on le seuil ? | Des expériences courtes et tracées, un premier pipeline | Un modèle candidat et son rapport d'expériences | Le seuil est atteint sur des données jamais vues, ou l'on arrête |
| **4. Transition et production** | Le modèle tient-il dans la durée ? | Automatiser, tester, déployer, surveiller, documenter, transmettre | Un service en production, une procédure d'exploitation, un tableau de suivi | Les engagements de service sont tenus plusieurs semaines de suite |

::: callout remember À retenir
Les phases ne sont pas des cases à cocher une fois pour toutes. Une dérive détectée en production (phase 4) renvoie en recherche et développement (phase 3) ; une donnée introuvable en phase 2 renvoie en idéation. Le processus est une **boucle**, et c'est voulu.
:::

{#colisvert}
## Le projet de ColisVert, phase par phase

**Idéation (hier matin).** Dans la matrice valeur × faisabilité, deux projets sont sortis en tête : les **contrôles qualité automatisés**, lancés hier après-midi (rapport de qualité, nettoyage, versioning), et la **prédiction des retards**, qui découle directement de la vision : « d'ici fin 2027, chaque client ColisVert est prévenu d'un retard avant qu'il ne se produise ».

**Inception (maintenant).** La charte du projet tient en quelques lignes :

| Rubrique | Contenu |
|---|---|
| Objectif métier | Prévenir le client dès l'expédition quand son colis risque d'être en retard |
| Moment de la prédiction | À l'expédition : on n'utilise **que** ce qu'on sait à ce moment-là |
| Données | `livraisons.csv`, version `127f20d4…` : 5 035 colis du 7 septembre au 1er novembre 2026 |
| Ligne de base | Ne rien prédire (« tous les colis arrivent à l'heure ») : aucun client prévenu |
| Critère de succès | Attraper **au moins 8 retards sur 10**, avec **au plus une fausse alerte sur deux** |
| Critère d'arrêt | Seuil non atteint après deux itérations de R&D d'une semaine : on arrête et on revient aux contrôles qualité |
| Équipe | Un data scientist, un data engineer, une responsable du service client (côté métier) |

**Du langage métier à la métrique.** « Attraper 8 retards sur 10 », c'est le **rappel** : parmi les colis réellement en retard, la part que le modèle a signalée. « Au plus une fausse alerte sur deux », c'est la **précision** : parmi les colis signalés, la part réellement en retard. Le critère devient : **rappel ≥ 0,80 et précision ≥ 0,50**.

Pourquoi pas « 90 % de bonnes réponses » ? Parce que 83 % des colis arrivent à l'heure : un modèle qui répond toujours « à l'heure » aurait déjà 83 % de bonnes réponses, sans prévenir un seul client. On le vérifiera en chiffres dans la notion suivante.

**Recherche et développement (ce matin et cet après-midi).** Des expériences courtes, toutes enregistrées dans MLflow, sur un pipeline versionné.

**Transition et production (jours 3 à 5).** Le pipeline sera automatisé avec Airflow, le modèle servi et surveillé, et la gouvernance posée.

{#rd-duree-fixe}
## Pourquoi la R&D se planifie en durée fixe

En développement logiciel, on peut estimer le travail : « ce formulaire prendra trois jours ». En R&D data, **on ne sait pas d'avance si le seuil est atteignable** : peut-être que les données ne contiennent tout simplement pas l'information.

On inverse donc la planification : au lieu de fixer le résultat et d'estimer la durée, on **fixe la durée** (une itération d'une ou deux semaines) et l'on mesure le résultat atteint. À la fin de chaque itération : démonstration des chiffres au métier, puis décision. C'est ce que dit le critère d'arrêt de la charte.

::: callout tip Question fréquente : « Et si le seuil est atteint à moitié ? »
C'est la situation la plus courante. On présente au métier ce que le modèle permet déjà : par exemple, prévenir 6 clients sur 10 au lieu de 8, avec moins de fausses alertes. Parfois, cela suffit à lancer une première version en production, et la R&D continue en parallèle. La décision appartient au métier, mais elle se prend sur des chiffres, pas sur une impression.
:::

:::: lab Exercice | Dans quelle phase sommes-nous ? | 5 min
Classez ces huit activités du projet ColisVert dans les quatre phases.

1. Comparer six réglages du modèle et noter leurs résultats dans MLflow.
2. Vérifier que l'heure d'expédition et la météo sont connues au moment de prédire.
3. Rédiger la procédure à suivre quand le pipeline de la nuit échoue.
4. Estimer combien coûtent les gestes commerciaux liés aux retards.
5. Fixer le seuil « rappel ≥ 0,80, précision ≥ 0,50 » avec le service client.
6. Surveiller chaque semaine la part de colis prédits en retard.
7. Classer cinq idées de projets dans une matrice valeur × faisabilité.
8. Abandonner une piste : un modèle de réseau de neurones, pas meilleur que la régression logistique et dix fois plus long à entraîner.

::: solution Voir le classement
| Phase | Activités |
|---|---|
| Idéation | 4, 7 |
| Inception | 2, 5 |
| Recherche et développement | 1, 8 |
| Transition et production | 3, 6 |

L'activité 8 est souvent mal classée : abandonner une piste fait **partie** de la R&D. C'est même ce qui la distingue d'un projet qui s'enlise.
:::
::::

{#avance}
## Pour aller plus loin : CRISP-DM, TDSP et le coût des projets qui ne s'arrêtent pas

Ce bloc est pour les profils avancés ; rien ici n'est exigé dans l'évaluation.

**Les méthodes de référence.** Deux cadres sont très cités en entreprise. Ils se superposent bien aux quatre phases :

| Quatre phases | CRISP-DM (1999) | TDSP (Microsoft) |
|---|---|---|
| Idéation | Compréhension du métier | Compréhension du métier |
| Inception | Compréhension des données | Acquisition et compréhension des données |
| R&D | Préparation des données, modélisation, évaluation | Modélisation |
| Transition et production | Déploiement | Déploiement, acceptation par le client |

**La critique classique de CRISP-DM** : il s'arrête au déploiement. Rien sur la surveillance, la dérive, le réentraînement, ni sur l'équipe qui exploite. C'est précisément le trou que comblent le MLOps et le DataOps : la phase 4 n'est pas une fin, c'est le début de la vie du modèle. Le TDSP (*Team Data Science Process*) de Microsoft ajoute des rôles et des livrables types (charte de projet, rapport de sortie), utiles pour structurer une équipe qui démarre.

**Les coûts irrécupérables.** Plus un projet a coûté, plus il est difficile de l'arrêter : on a « déjà investi six mois ». C'est un biais bien connu en économie comportementale (*sunk cost fallacy*). Le critère d'arrêt écrit **avant** de commencer, en phase d'inception, est la seule protection efficace : il transforme une décision émotionnelle en constat.

**La valeur d'une expérience.** Une expérience de R&D ne vaut pas par son résultat, mais par la **décision** qu'elle permet. Une expérience dont aucun résultat possible ne changerait la suite du projet ne vaut rien, même si elle est intéressante. Avant chaque itération, une bonne question à poser : « quel résultat nous ferait changer de plan ? ».

{#quiz}
## Quiz de validation

```quiz
- q: Dans quelle phase fixe-t-on la métrique de succès et le critère d'arrêt ?
  options: [Idéation, Inception, Recherche et développement, Transition et production]
  answer: 1
  explain: L'inception cadre le projet. Fixer le seuil avant les expériences évite de l'ajuster à ce qu'on a obtenu.
- q: Le service client veut « attraper au moins 8 retards sur 10 ». Quelle métrique traduit cette phrase ?
  options: [L'exactitude, La précision, Le rappel, L'aire sous la courbe ROC]
  answer: 2
  explain: Le rappel est la part des vrais retards que le modèle signale.
- q: Pourquoi planifie-t-on la R&D data en durée fixe ?
  options:
    - Parce que les data scientists travaillent plus vite sous pression
    - Parce qu'on ne sait pas d'avance si le seuil est atteignable, donc on fixe le temps et on mesure le résultat
    - Parce que MLflow impose des sprints de deux semaines
    - Parce que la production attend toujours le vendredi
  answer: 1
  explain: À la fin de chaque itération, on décide sur des chiffres - continuer, ajuster ou arrêter.
- q: Une dérive est détectée sur le modèle en production. Que prévoit le processus ?
  options:
    - Rien, le modèle a déjà passé la phase de R&D
    - Un retour en recherche et développement pour enquêter et, si besoin, réentraîner
    - Un retour en idéation pour choisir un autre projet
    - Supprimer le modèle immédiatement
  answer: 1
  explain: Le processus est une boucle. La production renvoie en R&D quand le monde change.
```
