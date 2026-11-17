---
subtitle: >-
  « Tout automatiser » ne veut pas dire tout scripter tout de suite. On fait l'inventaire de ce que la
  semaine a déjà automatisé, de ce qui reste manuel dans la plupart des équipes data, et d'une
  méthode pour passer du geste manuel à la machine qui se répare seule. Exemple réel à l'appui : la
  vérification automatique de ce cours, et la panne d'Airflow qu'elle a révélée.
objectives:
  - Faire l'inventaire de ce qu'une chaîne DataOps automatise, de l'infrastructure à la documentation
  - Choisir quoi automatiser en premier - fréquent, risqué, fastidieux
  - Passer par étapes d'une procédure manuelle à une procédure qui se déclenche et se répare seule
  - Citer les outils d'infrastructure et de déploiement par le code pour Azure et Fabric
---

{#inventaire}
## Ce que la semaine a déjà automatisé

| Ce qui était manuel | Ce qui le fait maintenant | Jour |
|---|---|---|
| « Quelle version des données a servi ? » | DVC : chaque version de données est un fichier `.dvc` dans Git | 1 |
| « Quels paramètres pour ce modèle ? » | MLflow Tracking : chaque run garde paramètres, métriques et modèle | 2 |
| « Le fichier est-il correct ? » | Le contrat de données, exécuté avant chaque entraînement | 1 et 3 |
| « Relancer le pipeline à 6 h 45 » | Airflow, déclenché à l'arrivée du fichier (Asset) | 3 |
| « Faut-il mettre ce modèle en production ? » | La barrière de qualité et la règle de promotion, puis l'alias du registre | 2 et 3 |
| « Le processus dérive-t-il ? » | Les cartes de contrôle et leurs règles d'alerte | 4 |
| « Le nouveau modèle est-il meilleur en vrai ? » | Le déploiement en ombre et son journal | 4 |
| « La documentation est-elle à jour ? » | La fiche du produit de données, vérifiée par du code | 5 |
| « Quelqu'un a écrasé la table » | L'historique Delta Lake et `RESTORE` | 5 |

{#methode}
## Une méthode : cinq niveaux

On n'automatise pas d'un coup. Chaque procédure monte les niveaux un par un :

| Niveau | État | Exemple : le redémarrage d'Airflow |
|---|---|---|
| **0. Dans une tête** | Une personne sait faire | « Quand les runs restent gris, je redémarre le conteneur » |
| **1. Documenté** | Une procédure écrite (*runbook*) que n'importe qui peut suivre | Le conseil de la page du jour 3 : `docker compose restart airflow` |
| **2. Scripté** | Une commande fait tout, sans oubli | Un script qui vérifie l'ordonnanceur et redémarre si besoin |
| **3. Déclenché** | La machine lance le script quand il le faut | Le script tourne en continu, toutes les 10 secondes |
| **4. Autoréparé et vérifié** | La réparation est elle-même testée, régulièrement | La CI arrête volontairement l'ordonnanceur et vérifie qu'il revient |

**Quoi automatiser en premier ?** Ce qui est **fréquent** (chaque jour), **risqué** (une erreur coûte cher) ou **fastidieux** (personne ne le fait bien la 50e fois). Et jamais ce qu'on ne comprend pas encore : automatiser un geste mal compris, c'est produire des erreurs plus vite.

::: callout info Un exemple réel : la vérification de ce cours
Chaque cellule de ce support, avec sa « sortie attendue », est **exécutée automatiquement** dans l'image des TP par GitHub Actions, sous le même utilisateur que vos VM. Une sortie qui diffère d'un seul chiffre fait échouer la vérification. Le parcours complet est rejoué à chaque modification : DVC, MLflow, Airflow, les services.

C'est cette automatisation qui a révélé, la semaine de préparation, une panne rare. L'ordonnanceur d'Airflow s'arrêtait parfois sur une erreur de la base SQLite, et ne redémarrait pas. Le diagnostic a été automatisé (journaux et états des runs recueillis à chaque échec), puis la réparation (le conteneur redémarre seul), puis la **vérification de la réparation**. La CI provoque désormais la panne volontairement, à chaque exécution. C'est le niveau 4 de la méthode.
:::

{#reste}
## Ce qui reste souvent manuel

| Domaine | Le geste manuel | Ce qui l'automatise |
|---|---|---|
| **Infrastructure** | Créer un espace de travail, une capacité, un compte de stockage dans le portail | L'**infrastructure par le code** : Terraform (le fournisseur Terraform pour Microsoft Fabric est disponible en version stable), Bicep pour Azure |
| **Environnements** | « Chez moi, ça marche » | Une **image Docker** figée (celle de vos TP), des dépendances verrouillées |
| **Déploiement** | Copier un notebook de l'espace de développement à la production | L'intégration **Git** et les **pipelines de déploiement** de Fabric (voir la certification DP-700), la CI/CD |
| **Accès** | Un ticket, un mail, une attente | Des demandes d'accès dans le catalogue, accordées selon la classification |
| **Qualité et surveillance** | Regarder un tableau de bord chaque matin | Des alertes sur règles (cartes de contrôle, fraîcheur), envoyées à qui doit agir |
| **Documentation** | Une page wiki écrite une fois, jamais relue | Une documentation générée depuis le code et les fiches, et vérifiée en CI |
| **Secrets** | Un mot de passe dans un fichier partagé | Un coffre-fort (Azure Key Vault), avec une rotation automatique |

**Le principe du Manifeste DataOps qui résume ce bloc :** « Rendre reproductible » (*Make it reproducible*). Tout ce qui produit un résultat doit pouvoir être rejoué à l'identique : les données, le code, l'environnement et la configuration.

{#quiz}
## Quiz

```quiz
- q: Par quoi commencer l'automatisation d'une procédure manuelle ?
  options:
    - Par un script, tout de suite
    - Par l'écrire - une procédure documentée que n'importe qui peut suivre
    - Par un outil du marché
    - Par une réunion
  answer: 1
  explain: On ne scripte bien que ce qu'on a compris et écrit ; le runbook devient ensuite le cahier des charges du script.
- q: Quelle procédure automatiser en premier ?
  options:
    - La plus intéressante techniquement
    - Celle qui est fréquente, risquée ou fastidieuse
    - Celle qu'on fait une fois par an
    - Celle qu'on ne comprend pas
  answer: 1
  explain: Le gain est proportionnel à la fréquence et au coût d'une erreur.
- q: Qu'ajoute le niveau 4 (autoréparé et vérifié) par rapport au niveau 3 ?
  options:
    - Rien
    - La réparation est elle-même testée régulièrement, par exemple en provoquant la panne volontairement
    - Une interface graphique
    - Une documentation
  answer: 1
  explain: Une réparation qui n'est jamais testée finit par ne plus marcher le jour où on en a besoin.
- q: Quel outil crée un espace de travail Fabric par le code ?
  options:
    - DVC
    - Le fournisseur Terraform pour Microsoft Fabric
    - MLflow
    - Delta Lake
  answer: 1
  explain: L'infrastructure par le code rend la création d'un environnement reproductible et relisible.
```
