---
subtitle: >-
  Le DataOps n'invente presque rien : il applique aux données trois méthodes qui ont fait leurs
  preuves ailleurs. Le Lean chasse les gaspillages, l'Agilité livre par petits morceaux, le DevOps
  automatise. Le manifeste DataOps rassemble le tout.
objectives:
  - Reconnaître les sept gaspillages du Lean dans un travail sur les données
  - Expliquer ce que l'Agilité change dans un projet data
  - Expliquer le principe du DevOps et du CI/CD
  - Définir le DataOps et citer plusieurs principes de son manifeste
  - Énoncer les apports du DataOps pour une organisation
---

{#lean}
## Le Lean : chasser les gaspillages

**D'où ça vient ?** Le Lean est né dans les usines Toyota. Son idée centrale : tout ce qui n'apporte pas de valeur au client est un **gaspillage**, à réduire. Ce matin, la cartographie de la chaîne de valeur était déjà un outil du Lean.

Le Lean distingue **sept gaspillages**. Ils existent tous dans un travail sur les données :

| Gaspillage | À l'usine | Dans les données |
|---|---|---|
| **Surproduction** | Fabriquer plus que demandé | Un rapport de 40 pages dont personne ne lit que la page 1 |
| **Attente** | Une pièce attend la machine suivante | Un fichier attend 72 h la validation du jeudi |
| **Transport** | Déplacer des pièces inutilement | Copier les mêmes données entre cinq systèmes |
| **Traitements inutiles** | Polir une face cachée | Recalculer chaque nuit des indicateurs que plus personne n'utilise |
| **Stocks** | Des pièces en attente dans l'entrepôt | Des données collectées « au cas où », jamais exploitées |
| **Mouvements** | L'ouvrier cherche ses outils | L'analyste cherche dans quel dossier se trouve le bon fichier |
| **Défauts** | Une pièce à refaire | Un doublon ou une date mal écrite qui fausse un chiffre |

{#agile}
## L'Agilité : livrer par petits morceaux

**Le problème :** un projet data de 12 mois, spécifié au début, livré à la fin. Entre-temps, le besoin a changé, et l'on découvre trop tard que les données ne permettent pas ce qui était prévu.

**La réponse Agile** (le *Manifeste agile* de 2001, écrit pour le logiciel) : livrer **un petit résultat utile** toutes les 2 à 3 semaines (un **sprint**), le montrer aux utilisateurs, et ajuster.

Chez ColisVert, au lieu d'un « grand projet de prédiction des retards » :

| Sprint | Ce qui est livré | Utile tout de suite ? |
|---|---|---|
| 1 | Le taux de retard par entrepôt, chaque matin | Oui : les chefs d'entrepôt le consultent |
| 2 | Le même, par météo et par créneau | Oui : Lille adapte ses tournées les jours de pluie |
| 3 | Un premier modèle qui prédit les retards du lendemain | Oui : le service client prévient les clients concernés |

{#devops}
## Le DevOps : automatiser de bout en bout

**Le problème, dans le logiciel des années 2000 :** les développeurs écrivent le code, puis le « lancent par-dessus le mur » à l'équipe d'exploitation qui doit le faire tourner. Les mises en production sont rares, manuelles et risquées.

**La réponse DevOps** (le mot apparaît en 2009) : une seule équipe responsable du code **et** de son exploitation, et des tâches répétitives **automatisées** :

- **tout est versionné** : le code, la configuration, l'infrastructure ;
- **l'intégration continue** (*CI*) : à chaque modification, des tests automatiques vérifient que rien n'est cassé ;
- **le déploiement continu** (*CD*) : si les tests passent, la mise en production se fait automatiquement ;
- **la mesure** : on surveille ce qui tourne en production, et l'on apprend des incidents.

Ce matin, la mise en production d'une correction prenait **13 jours** pour 8 heures de travail. Le CI/CD vise à la ramener à quelques heures.

{#dataops}
## Le DataOps : les trois réunis, pour les données

Le **DataOps** applique aux pipelines de données le Lean (chasser les gaspillages, mesurer la qualité), l'Agilité (livrer souvent) et le DevOps (versionner, tester, automatiser). Avec une difficulté en plus : **les données changent même quand le code ne change pas**. Un pipeline peut casser un lundi matin parce que le fichier du week-end contient des doublons.

Le **manifeste DataOps**, publié en 2017 par l'entreprise DataKitchen, énonce 18 principes. Six d'entre eux, appliqués à ColisVert :

| Principe du manifeste | Ce que ça veut dire chez ColisVert |
|---|---|
| **N° 7, réduire l'héroïsme** | Le rapport ne doit plus dépendre de l'analyste qui « sait comment faire » |
| **N° 9, l'analytique, c'est du code** | Le nettoyage s'écrit en Python, pas en clics dans Excel |
| **N° 11, rendre reproductible** | Données, code et configuration sont versionnés : on refait le même calcul dans 6 mois |
| **N° 12, des environnements jetables** | Chacun a son environnement isolé, recréé en une commande (votre conteneur Docker) |
| **N° 15, la qualité est primordiale** | Le pipeline détecte seul les anomalies, comme le rapport de qualité de la notion précédente |
| **N° 18, améliorer les temps de cycle** | Réduire le délai entre une question et sa réponse : le Time To Value |

Le manifeste ajoute un dernier conseil : **commencer par tester les données**. Ses auteurs le résument ainsi : aucun client n'a jamais demandé plus d'erreurs dans ses données.

{#apports}
## Les apports du DataOps

| Sans DataOps | Avec DataOps |
|---|---|
| Un rapport en 6,7 jours, dont 94 % d'attente | Des indicateurs mis à jour chaque nuit, sans intervention |
| Les erreurs découvertes par la direction, en réunion | Les erreurs arrêtées par les contrôles, avant publication |
| « Ça marchait la semaine dernière » : impossible de savoir ce qui a changé | Chaque version des données et du code est retrouvable |
| Une personne indispensable, qui ne peut pas partir en vacances | Un processus documenté, automatisé, que toute l'équipe peut faire tourner |

:::: lab Exercice | Retrouver les gaspillages | 5 min
Pour chaque situation de ColisVert, dites de quel gaspillage du Lean il s'agit.

1. Chaque nuit, un script recalcule 30 indicateurs ; la direction en regarde 4.
2. L'analyste passe une heure à chercher la dernière version du fichier « livraisons_final_v3_OK.xlsx ».
3. 25 lignes en double gonflent le nombre de colis du rapport.
4. Les données des scanners sont copiées du système des entrepôts vers un serveur FTP, puis vers le lac, puis vers Excel.
5. Le rapport attend la validation du responsable qualité, qui ne valide que le jeudi.

::: solution Voir les réponses
1. **Traitements inutiles** (et un peu de surproduction) : 26 indicateurs calculés pour rien.
2. **Mouvements** : chercher son outil. Le versioning, au programme du TP, règle ce problème.
3. **Défauts** : une donnée à corriger, qui fausse le résultat.
4. **Transport** : trois copies, trois occasions d'erreur.
5. **Attente** : le gaspillage le plus coûteux de la chaîne de valeur de ce matin.
:::
::::

{#quiz}
## Quiz de validation

```quiz
- q: Des données collectées « au cas où » et jamais exploitées correspondent à quel gaspillage du Lean ?
  options: [Attente, Stocks, Mouvements, Défauts]
  answer: 1
  explain: Comme des pièces qui dorment dans un entrepôt, elles coûtent sans rapporter.
- q: Que fait l'intégration continue (CI) ?
  options:
    - Elle met en production chaque nuit, sans test
    - Elle lance des tests automatiques à chaque modification du code
    - Elle sauvegarde les données
    - Elle écrit la documentation
  answer: 1
  explain: Les tests automatiques vérifient à chaque modification que rien n'est cassé.
- q: Qu'est-ce que le DataOps ajoute au DevOps ?
  options:
    - Rien, ce sont deux noms pour la même chose
    - La prise en compte des données, qui changent même quand le code ne change pas
    - Le remplacement de Git par Excel
    - La suppression des tests
  answer: 1
  explain: Un pipeline peut casser à cause des données seules. Il faut donc tester les données, pas seulement le code.
- q: Selon le manifeste DataOps, que veut dire « rendre reproductible » ?
  options:
    - Imprimer les rapports en plusieurs exemplaires
    - Versionner données, code et configuration pour refaire exactement le même calcul plus tard
    - Copier les données sur plusieurs serveurs
    - Recruter des profils similaires
  answer: 1
  explain: C'est le principe n° 11, et le sujet du TP qui suit.
```
