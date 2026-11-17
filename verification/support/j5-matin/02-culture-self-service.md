---
subtitle: >-
  Les outils de la semaine ne servent à rien si l'organisation ne change pas. Une équipe qui cache ses
  erreurs, des équipes métier qui attendent trois semaines un tableau de bord, une équipe data qui
  devient un goulet d'étranglement : ce sont des problèmes d'organisation, pas de technique. On voit
  la culture qui fait marcher le DataOps, comment conduire le changement, et comment une plateforme
  en libre-service permet à chacun de se servir sans tout casser.
objectives:
  - Reconnaître une culture favorable au DataOps, et ses signaux
  - Conduire un changement avec une méthode - la peur, le désir, la compétence, puis l'habitude
  - Organiser les équipes autour d'une plateforme, avec les quatre types d'équipes de Team Topologies
  - Concevoir une offre en libre-service avec un chemin balisé et ses garde-fous
---

{#culture}
## La culture qui fait marcher le DataOps

Le chercheur Ron Westrum classe les cultures d'organisation selon la façon dont l'information y circule. Les rapports DORA (jour 4) l'utilisent depuis des années : la culture qu'il appelle **générative** va de pair avec de meilleures performances de livraison.

| Culture | Face à une erreur | Ce qu'on entend |
|---|---|---|
| **Pathologique** (orientée pouvoir) | On cherche un coupable | « Qui a cassé le pipeline ? » |
| **Bureaucratique** (orientée règles) | On applique la procédure | « Ce n'est pas dans mon périmètre » |
| **Générative** (orientée mission) | On cherche ce que le système doit changer | « Qu'est-ce qui a rendu l'erreur possible ? » |

Vous avez déjà pratiqué les gestes d'une culture générative cette semaine :
- **la revue d'incident sans coupable** du jour 4 ;
- **les erreurs rendues visibles tôt** : le contrat de données qui arrête le pipeline, la barrière de qualité ;
- **le travail partagé et versionné** : Git, DVC, MLflow, le registre.

**Les principes du Manifeste DataOps qui portent sur la culture** :
- « Faire de l'analytique un sport d'équipe » ;
- « Réfléchir » (les rétrospectives) ;
- « S'auto-organiser » : les meilleures architectures, exigences et conceptions viennent d'équipes qui s'organisent elles-mêmes.

{#changement}
## Conduire le changement

**L'analogie du nouveau tri.** Le jour où ColisVert installe une nouvelle machine de tri, les agents ne l'adoptent pas parce qu'elle est meilleure. Ils l'adoptent :
- s'ils comprennent **pourquoi** l'ancienne ne suffit plus ;
- s'ils **veulent** le changement ;
- s'ils savent s'en **servir** ;
- et si, la semaine suivante, personne ne les renvoie à l'ancienne méthode.

Le modèle **ADKAR** (Prosci) décrit ces cinq étapes, dans l'ordre :

| Étape | Question | Chez ColisVert, pour passer de cron à Airflow |
|---|---|---|
| **Awareness** (prise de conscience) | Pourquoi changer ? | La revue d'incident du 29/09 : un modèle périmé, découvert trois jours plus tard |
| **Desire** (désir) | Qu'est-ce que j'y gagne ? | Plus d'astreinte le matin pour relancer le pipeline à la main |
| **Knowledge** (connaissance) | Comment fait-on ? | Une formation (comme celle-ci), une page de documentation |
| **Ability** (capacité) | Est-ce que j'y arrive vraiment ? | Un premier DAG accompagné, en binôme |
| **Reinforcement** (ancrage) | Est-ce que ça tient ? | Le tableau de bord DORA du mois suivant, montré en rétrospective |

**Le piège classique :** commencer par la connaissance (une formation) alors que personne n'a compris pourquoi changer. Le modèle de John Kotter, en 8 étapes, dit la même chose avec d'autres mots : créer d'abord un **sentiment d'urgence**, puis obtenir des **victoires rapides** visibles, et enfin **ancrer** le changement dans la culture.

{#topologies}
## Organiser les équipes : Team Topologies

Le livre *Team Topologies* (Matthew Skelton et Manuel Pais, 2019) propose **quatre types d'équipes** et **trois modes d'interaction**. Il s'applique tel quel à une organisation data.

| Type d'équipe | Rôle | Chez ColisVert |
|---|---|---|
| **Alignée sur un flux** (*stream-aligned*) | Livre de la valeur de bout en bout pour un domaine métier | L'équipe « retards et alertes clients » |
| **Plateforme** | Fournit des services internes, utilisables en libre-service | L'équipe qui opère Airflow, MLflow, le lac Delta et le catalogue |
| **Facilitatrice** (*enabling*) | Aide les autres équipes à acquérir une compétence, puis se retire | Un expert MLOps qui accompagne une équipe pendant six semaines |
| **Sous-système complexe** | Maîtrise un composant qui demande une expertise rare | L'équipe d'optimisation des tournées |

| Mode d'interaction | Quand |
|---|---|
| **Collaboration** | Pour découvrir ensemble, pendant une période limitée |
| **En tant que service** (*X-as-a-Service*) | Quand l'offre est stable : l'équipe consomme la plateforme sans en parler à chaque fois |
| **Facilitation** | Quand une équipe en aide une autre à progresser |

**L'idée centrale : la charge cognitive.** Une équipe de 5 à 9 personnes ne peut pas maîtriser à la fois le métier des livraisons, Kubernetes, Spark, la sécurité et le RGPD. La plateforme absorbe une partie de cette charge, pour que l'équipe alignée sur le flux se concentre sur son métier.

{#self-service}
## La plateforme en libre-service

**Le libre-service** veut dire qu'une équipe obtient seule, en minutes, ce qu'elle obtenait avant par un ticket, en semaines. Ce peut être un espace de travail, une table, un pipeline modèle, un accès ou un tableau de bord.

**Le chemin balisé** (*paved road*, ou *golden path*) en est la clé. La plateforme propose une façon **recommandée** de faire, déjà outillée et déjà conforme : un gabarit de pipeline avec son contrat de données, son DAG, sa CI et sa fiche de produit. On n'interdit pas les autres chemins, mais celui-ci est tellement plus simple qu'on le prend naturellement.

Pour ColisVert, le chemin balisé d'un nouveau jeu de données serait :

1. un gabarit de dépôt, avec la structure de la semaine : `params.yaml`, `dvc.yaml`, `dags/`, `verification/` ;
2. une fiche de produit de données (notion 1), vérifiée par la CI ;
3. une table Delta en zone argent, avec ses contraintes (TP qui suit) ;
4. une publication dans le catalogue, avec son propriétaire.

::: callout warn Le libre-service sans gouvernance, ou la gouvernance sans libre-service
**Sans gouvernance**, le libre-service produit des centaines de tables que personne ne possède, ne documente ni ne supprime. **Sans libre-service**, la gouvernance devient un guichet unique engorgé, que les équipes contournent. Les deux vont ensemble : la plateforme rend le chemin conforme **plus facile** que le chemin non conforme.
:::

**Mesurer l'adoption.** Une plateforme se mesure comme un produit, avec ses utilisateurs : délai pour publier un premier jeu de données, part des pipelines qui suivent le chemin balisé, nombre de demandes manuelles restantes, satisfaction des équipes. Les indicateurs DORA du jour 4 s'appliquent aussi aux équipes qui l'utilisent.

{#quiz}
## Quiz

```quiz
- q: Dans une culture générative, que se passe-t-il après un incident ?
  options:
    - On cherche le responsable
    - On applique la procédure
    - On cherche ce que le système doit changer pour que l'erreur ne se reproduise pas
    - On n'en parle pas
  answer: 2
  explain: C'est la revue sans coupable du jour 4 ; DORA associe cette culture à de meilleures performances.
- q: Selon ADKAR, par quoi commence un changement réussi ?
  options:
    - Par une formation aux nouveaux outils
    - Par la prise de conscience - comprendre pourquoi changer
    - Par l'achat d'une plateforme
    - Par une note de la direction
  answer: 1
  explain: Former des gens qui ne voient pas pourquoi changer, c'est former des gens qui n'utiliseront pas l'outil.
- q: Quel est le rôle d'une équipe plateforme dans Team Topologies ?
  options:
    - Livrer les tableaux de bord métier
    - Fournir des services internes en libre-service, pour réduire la charge cognitive des autres équipes
    - Valider chaque déploiement
    - Remplacer les équipes métier
  answer: 1
  explain: Elle absorbe la complexité technique ; les équipes alignées sur un flux consomment ses services.
- q: Qu'est-ce qu'un « chemin balisé » ?
  options:
    - Une procédure obligatoire
    - Une façon recommandée de faire, déjà outillée et conforme, plus simple que les autres
    - Un tableau de bord de suivi
    - Une liste d'interdits
  answer: 1
  explain: On n'interdit pas, on rend le bon chemin le plus facile.
```
