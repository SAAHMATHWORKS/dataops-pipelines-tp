---
subtitle: >-
  Une équipe ne s'améliore pas en travaillant plus, mais en regardant régulièrement comment elle
  travaille. La rétrospective et la revue d'incident sans coupable sont les deux rituels qui
  transforment une erreur en apprentissage. Et une amélioration n'est terminée que lorsqu'on a
  vérifié, chiffres à l'appui, qu'elle a produit son effet.
objectives:
  - Animer une rétrospective avec un format adapté et la directive première
  - Rédiger une revue d'incident sans coupable, avec chronologie, cause racine et actions
  - Remonter d'un symptôme à une cause du système avec les cinq pourquoi
  - Boucler une amélioration avec le cycle PDCA, en mesurant son effet
---

{#retro}
## La rétrospective

Le principe 8 du Manifeste DataOps, « Réfléchir », demande aux équipes de revoir régulièrement leurs retours d'expérience, ceux des clients et leurs statistiques d'exploitation, pour s'améliorer. La **rétrospective** est ce rendez-vous : à la fin de chaque itération, 45 à 90 minutes, toute l'équipe, une seule question, « comment travailler mieux la prochaine fois ? ».

**La directive première** (Norman Kerth, 2001), lue au début de chaque séance : *quoi que nous découvrions, nous comprenons et croyons sincèrement que chacun a fait du mieux qu'il pouvait, compte tenu de ce qu'il savait alors, de ses compétences, des ressources disponibles et de la situation*. Sans elle, personne ne raconte ses erreurs, et l'équipe n'apprend rien.

| Format | Questions | Quand l'utiliser |
|---|---|---|
| **Commencer, arrêter, continuer** | Que commencer ? Qu'arrêter ? Que garder ? | Le plus simple, pour démarrer |
| **4L** | Aimé, appris, manqué, souhaité (*liked, learned, lacked, longed for*) | Après une itération riche en découvertes |
| **Voilier** | Le vent (ce qui pousse), les ancres (ce qui freine), les récifs (les risques), l'île (l'objectif) | Pour parler des risques à venir |
| **Chronologie** | On reconstitue l'itération jour par jour, avec l'humeur de l'équipe | Après une itération difficile |

**La règle d'or : peu d'actions, mais tenues.** Une ou deux actions par rétrospective, chacune avec un responsable et une date, revues au début de la rétrospective suivante. Dix bonnes intentions sans responsable ne changent rien.

{#incident}
## La revue d'incident sans coupable

Quand un incident a un impact réel, on écrit une **revue d'incident** (*postmortem*). « Sans coupable » (*blameless*) ne veut pas dire « sans responsabilité » : on cherche **ce qui, dans le système, a rendu l'erreur possible**, parce qu'une personne remplacée par une autre aurait fait la même erreur dans le même système.

Voici celle que l'équipe de ColisVert aurait pu écrire avant le jour 3 :

| Rubrique | Contenu |
|---|---|
| **Résumé** | Le 29 septembre, le modèle a été réentraîné à 06:45 sur les données de la veille ; les prévisions de la journée ont ignoré les 120 colis expédiés le 28. |
| **Impact** | Prévisions de retard calculées sur des données périmées ; aucune alerte ; découvert trois jours plus tard en relisant les journaux. |
| **Chronologie** | 06:45 : le pipeline démarre (horaire fixe). 06:46 : `dvc repro` répond « à jour », rien n'a changé. 08:02 : le fichier arrive. 1er octobre : un analyste remarque l'écart. |
| **Cause racine** | Voir les cinq pourquoi ci-dessous. |
| **Ce qui a bien marché** | Le versionnement (DVC, MLflow) a permis de reconstituer exactement ce qui s'était passé. |
| **Actions** | Déclencher le pipeline à l'arrivée du fichier (fait au jour 3, TP 2). Alerter si le fichier manque à 7 h (en tête du carnet, notion 1). Demander un engagement de service à l'équipe des entrepôts. |

**Les cinq pourquoi**, pour remonter du symptôme à une cause du **système** :

1. Pourquoi le modèle du 29 était-il périmé ? Parce qu'il a été entraîné avant l'arrivée du fichier.
2. Pourquoi avant ? Parce que le pipeline démarre à heure fixe, 06:45.
3. Pourquoi à heure fixe ? Parce que l'outil de l'époque (cron) ne sait déclencher que sur l'horloge.
4. Pourquoi personne ne l'a vu ? Parce qu'un pipeline qui n'a rien à faire répond « succès » : aucun contrôle ne vérifiait la **fraîcheur** des données.
5. Pourquoi aucun contrôle de fraîcheur ? Parce que la définition de « terminé » ne demandait pas de surveiller la fraîcheur.

On s'arrête quand on atteint une cause **sur laquelle l'équipe peut agir**. Ici, deux : le déclenchement (corrigé par l'Asset) et la définition de « terminé » (complétée par la surveillance).

{#pdca}
## Boucler l'amélioration : le cycle PDCA

Le cycle de Deming, **planifier, faire, vérifier, agir** (*plan, do, check, act*), rappelle qu'une action n'est pas terminée quand elle est faite, mais quand son effet est **vérifié**.

| Étape | Pour l'action « déclencher par l'Asset » |
|---|---|
| **Planifier** | Hypothèse : le modèle sera frais tous les jours, et prêt plus tôt |
| **Faire** | TP 2 du jour 3 |
| **Vérifier** | Mesurer, sur les 56 jours d'arrivées, ce qui change (cellule ci-dessous) |
| **Agir** | Garder si l'effet est là ; sinon, comprendre et recommencer. Puis attaquer la cause suivante |

:::: lab Démo | L'action a-t-elle produit son effet ? | 5 min
On rejoue les 56 jours d'arrivées avec les deux déclenchements, en comptant 5 minutes de pipeline.

```python title="Cellule 13 : horaire fixe contre Asset, sur les mêmes jours"
duree = 5                                   # minutes de pipeline
horaire = 6 * 60 + 45                       # 06:45
frais_horaire = arrivees["minutes"] <= horaire
pret_asset = arrivees["minutes"] + duree
print(f"horaire 06:45 : modèle frais {frais_horaire.sum()} jours sur {len(arrivees)}, prêt à {hhmm(horaire + duree)}")
print(f"Asset         : modèle frais {len(arrivees)} jours sur {len(arrivees)}, prêt à {hhmm(pret_asset.median())} en médiane")
print(f"modèle frais et prêt avant 7 h : {frais_horaire.sum()} jours avec l'horaire, {(pret_asset <= 7 * 60).sum()} avec l'Asset")
```

```plaintext title="Sortie attendue"
horaire 06:45 : modèle frais 48 jours sur 56, prêt à 06:50
Asset         : modèle frais 56 jours sur 56, prêt à 06:35 en médiane
modèle frais et prêt avant 7 h : 48 jours avec l'horaire, 48 avec l'Asset
```
::::

**Vérifier, c'est aussi découvrir ce qui n'a pas changé.**

- **Effet obtenu :** le modèle est frais **tous les jours** (56 sur 56 au lieu de 48), et disponible plus tôt : 06:35 en médiane au lieu de 06:50.
- **Effet non obtenu :** le nombre de jours où le modèle est frais **avant 7 h** ne bouge pas (48). L'Asset ne fait pas arriver le fichier plus tôt ; il évite seulement de travailler sur des données périmées.
- **Agir :** on garde l'Asset, et la cause suivante est en amont, chez l'équipe des entrepôts. C'est exactement la conclusion de la carte de contrôle de la notion 3 : pour tenir 7 h, il faut changer le système qui produit le fichier.

{#atelier}
## Atelier : la rétrospective des trois premiers jours

En groupe, 8 minutes, format « voilier » sur un tableau partagé de Teams :

- **le vent** : ce qui vous a fait avancer depuis lundi ;
- **les ancres** : ce qui vous a freinés (environnement, notions, rythme) ;
- **les récifs** : ce qui vous inquiète pour l'appliquer dans votre entreprise ;
- **l'île** : ce que vous voulez savoir faire vendredi soir.

Le formateur choisit avec le groupe **une** action pour les jours 4 et 5, et la note en haut du tableau.

{#quiz}
## Quiz

```quiz
- q: Que signifie « sans coupable » dans une revue d'incident ?
  options:
    - Que personne n'est responsable de rien
    - Qu'on cherche ce qui, dans le système, a rendu l'erreur possible, plutôt que la personne qui l'a commise
    - Qu'on ne nomme pas les systèmes
    - Qu'on n'écrit pas de revue
  answer: 1
  explain: Une autre personne, dans le même système, aurait fait la même erreur ; c'est le système qu'il faut changer.
- q: Quand s'arrêter dans les cinq pourquoi ?
  options:
    - Toujours au cinquième
    - Quand on atteint une cause sur laquelle l'équipe peut agir
    - Quand on trouve un coupable
    - Au premier pourquoi
  answer: 1
  explain: Le chiffre cinq est indicatif ; le critère est d'arriver à une cause du système, actionnable.
- q: Quelle étape du PDCA oublie-t-on le plus souvent ?
  options:
    - Planifier
    - Faire
    - Vérifier - mesurer que l'action a produit l'effet attendu
    - Agir
  answer: 2
  explain: Sans vérification, on accumule des actions sans savoir lesquelles marchent.
- q: Après le passage à l'Asset, le fichier arrive toujours après 7 h certains jours. Quelle est la prochaine action ?
  options:
    - Revenir à l'horaire fixe
    - Agir en amont - obtenir un engagement de service de l'équipe qui produit le fichier
    - Réentraîner le modèle plus souvent
    - Rien
  answer: 1
  explain: L'Asset a supprimé le modèle périmé, pas le retard du fichier ; la cause suivante est en amont.
```
