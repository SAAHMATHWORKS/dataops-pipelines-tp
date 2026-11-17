---
subtitle: >-
  Trois mots en « Ops », trois objets différents à faire tourner en production : du logiciel,
  des pipelines de données, des modèles. Et un même ennemi : le mur entre ceux qui construisent
  et ceux qui exploitent.
objectives:
  - Distinguer DevOps, DataOps et MLOps par ce qu'ils livrent et ce qu'ils testent
  - Situer les outils de la semaine dans chacune des trois démarches
  - Expliquer le mur de la confusion entre analytiques et opérations
  - Citer quatre pratiques qui le font tomber
---

{#comparaison}
## Trois démarches, trois objets

**Pourquoi les distinguer ?** Parce qu'on entend les trois mots dans les mêmes réunions, souvent comme des synonymes. Ils partagent la même philosophie (automatiser, versionner, mesurer), mais ils ne livrent pas la même chose, et ne testent pas la même chose.

| | DevOps | DataOps | MLOps |
|---|---|---|---|
| **Ce qu'on livre** | Une application | Des données fiables, à l'heure | Un modèle qui prédit, en production |
| **Ce qui peut changer** | Le code | Le code **et les données** | Le code, les données **et le modèle** |
| **Ce qu'on teste** | Le code fonctionne | Les données sont complètes, valides, fraîches | Le modèle reste performant, les données ne dérivent pas |
| **Le signal d'alerte** | L'application plante | Le fichier du matin a des doublons ou arrive en retard | Les prédictions se dégradent sans que rien ne plante |
| **Outils de la semaine** | Git, Docker | DVC, contrôles qualité, Airflow, Delta Lake | MLflow, Optuna, Evidently |
| **Quand** | Tous les jours | Jours 1, 3, 4 et 5 | Jours 2 et 4 |

Le MLOps est le cas le plus difficile : un modèle peut **se dégrader en silence**. Il ne plante pas, il continue de répondre, mais ses réponses deviennent fausses parce que le monde a changé. Chez ColisVert, un modèle entraîné en septembre risque de mal prédire les retards de décembre, avec ses colis de Noël plus lourds et sa pluie plus fréquente. C'est la **dérive**, que vous détecterez le jour 2.

::: callout remember À retenir
« Le MLOps contient le DataOps, qui contient le DevOps » n'est pas tout à fait juste, mais c'est un bon repère : chaque démarche reprend la précédente et ajoute un objet qui peut changer tout seul.
:::

{#mur}
## Le mur de la confusion

L'expression vient du DevOps. D'un côté du mur, les développeurs veulent **changer** vite. De l'autre, l'exploitation veut que **rien ne casse**. Le code est « lancé par-dessus le mur », et quand il plante en production, chacun accuse l'autre : « ça marche sur ma machine ».

Dans les données, le même mur sépare **les analytiques** (analystes, data scientists) **des opérations** (DSI, équipes de production) :

| Côté analytiques | Côté opérations |
|---|---|
| Un notebook sur un portable, avec ses propres versions de bibliothèques | Un serveur de production, avec d'autres versions |
| Un fichier exporté à la main, nettoyé dans Excel | Des données qui arrivent chaque nuit, avec des défauts nouveaux |
| « Mon modèle a 85 % de précision » | « Comment on le fait tourner chaque nuit ? Qui est prévenu s'il plante ? » |
| Le travail est fini quand le résultat est bon | Le travail commence quand le résultat doit tourner tous les jours |

Résultat : des mois entre un prototype prometteur et sa mise en production, quand elle arrive.

{#briser}
## Briser le mur

Quatre pratiques, que vous mettez en œuvre cette semaine :

| Pratique | Ce qu'elle supprime | Où vous la pratiquez |
|---|---|---|
| **Les mêmes environnements partout** | « Ça marche sur ma machine » | Votre conteneur Docker : mêmes versions pour tous, du TP à la production |
| **Tout en code, tout versionné** | Les étapes manuelles que personne ne sait refaire | Git et DVC, cet après-midi |
| **Le pipeline comme livrable** | Le prototype qui ne tourne qu'une fois | MLflow (jour 2), Airflow (jour 3) |
| **Des indicateurs partagés** | Chacun son tableau de bord, chacun sa vérité | Les engagements de fraîcheur et la MSP (jour 4) |

Et une pratique humaine : **une équipe responsable de bout en bout**, qui construit le pipeline et répond de son fonctionnement. C'est le sujet de la notion suivante.

::: callout info Et les agents IA ?
Un troisième « opérateur » arrive dans les équipes : l'**agent IA**, un programme qui s'appuie sur un grand modèle de langage pour diagnostiquer un échec de pipeline, proposer un correctif ou documenter une table. Il ne change pas la règle du jeu, il la renforce : un agent n'est utile que sur un pipeline **versionné, testé et observable**, exactement ce que vous construisez cette semaine. Le jour 5 lui est en partie consacré : rôles possibles, limites des LLM, risques, et cadres de gouvernance (AI Act, ISO 42001).
:::

:::: lab Exercice | De quel côté du mur ? | 4 min
Pour chaque phrase entendue chez ColisVert, dites si elle trahit le mur de la confusion, et quelle pratique y répondrait.

1. « Le modèle marchait dans mon notebook, je ne comprends pas pourquoi il plante sur le serveur. »
2. « Le rapport de lundi est faux, mais on ne sait pas quel fichier a été utilisé. »
3. « La DSI nous a dit qu'il faudrait trois mois pour mettre le modèle en production. »

::: solution Voir les réponses
1. **Oui** : environnements différents. Réponse : le même conteneur partout.
2. **Oui** : rien n'est versionné. Réponse : Git et DVC, avec l'empreinte du fichier utilisé.
3. **Oui** : le prototype n'a pas été pensé pour la production. Réponse : construire dès le départ un pipeline automatisé et versionné, avec l'exploitation dans l'équipe.
:::
::::

{#avance}
## Pour aller plus loin : savoir d'où vient chaque chiffre (lineage)

Ce bloc est pour les profils avancés ; rien ici n'est exigé dans l'évaluation.

Quand le mur tombe, une question reste : **« ce chiffre du tableau de bord, il vient d'où ? »**. La réponse s'appelle la **traçabilité des données** (*data lineage*) : le graphe qui relie chaque table, chaque fichier et chaque colonne aux traitements qui les ont produits.

- **À quoi ça sert, concrètement ?** À trois moments précis : pour **diagnostiquer** (le taux de retard est bizarre ce matin : quels traitements ont touché cette table cette nuit ?), pour **évaluer l'impact d'un changement** (si je renomme cette colonne, quels rapports cassent ?), et pour **répondre à un auditeur** (RGPD : où vont les adresses des clients ?).
- **Comment on l'obtient ?** Au début, à la main : un schéma comme celui du processus de ce matin. Puis automatiquement : les orchestrateurs et les outils de transformation peuvent **émettre un évènement à chaque exécution** (« la tâche T a lu le fichier A et écrit la table B »). Le standard ouvert de ces évènements s'appelle **OpenLineage** ; des outils comme Marquez ou les catalogues d'entreprise (Microsoft Purview, Unity Catalog, DataHub) les collectent et dessinent le graphe.
- **Le lien avec cette semaine :** vous construisez déjà du lineage sans le savoir. Le ticket DVC dit quelle donnée exacte entre dans le pipeline ; demain, MLflow notera quel commit et quelle empreinte de données ont produit chaque modèle ; au jour 3, Airflow saura quelle tâche a écrit quel fichier. La traçabilité n'est pas un outil à acheter : c'est un sous-produit d'un pipeline bien construit.

{#quiz}
## Quiz de validation

```quiz
- q: Qu'est-ce qui peut changer en MLOps, et pas en DevOps ?
  options:
    - Le code seulement
    - Les données et le modèle, en plus du code
    - Le système d'exploitation
    - Le nombre d'utilisateurs
  answer: 1
  explain: Un modèle dépend des données sur lesquelles il a été entraîné. Quand le monde change, il se dégrade.
- q: Pourquoi dit-on qu'un modèle peut « se dégrader en silence » ?
  options:
    - Parce qu'il plante sans message d'erreur
    - Parce qu'il continue de répondre, mais de moins en moins juste, sans aucune erreur technique
    - Parce qu'il ne produit pas de journaux
    - Parce qu'il s'arrête la nuit
  answer: 1
  explain: C'est la dérive. Il faut la surveiller avec des indicateurs, comme on le fera le jour 2.
- q: Quelle pratique répond le mieux à « ça marche sur ma machine » ?
  options:
    - Écrire plus de documentation
    - Utiliser les mêmes environnements partout, par exemple le même conteneur Docker
    - Acheter des machines plus puissantes
    - Tester moins souvent
  answer: 1
  explain: Si le développement et la production utilisent le même conteneur, les versions sont les mêmes.
```
