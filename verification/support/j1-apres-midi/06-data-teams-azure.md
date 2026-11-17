---
subtitle: >-
  Un pipeline DataOps se construit à plusieurs : chacun a un rôle, et l'organisation de l'équipe
  compte autant que ses outils. Côté cloud, Microsoft Azure propose un service pour chaque étape
  de ce que vous allez construire cette semaine.
objectives:
  - Décrire les principaux rôles d'une équipe data
  - Comparer trois façons d'organiser les équipes data
  - Proposer des moyens de former une équipe et le reste de l'entreprise
  - Situer les concepts de base d'Azure et ses principaux services data
  - Faire correspondre les outils de la semaine aux services d'Azure et de Fabric
---

{#roles}
## Les rôles d'une équipe data

**Pourquoi plusieurs rôles ?** Parce qu'un pipeline va de la source brute jusqu'à la décision, et qu'aucune personne ne maîtrise tout ce chemin. Les intitulés varient d'une entreprise à l'autre ; les responsabilités, elles, se retrouvent partout.

| Rôle | Sa responsabilité | Chez ColisVert, cette semaine |
|---|---|---|
| **Data engineer** | Construire et faire tourner les pipelines : ingestion, nettoyage, stockage | Le pipeline Airflow, la plateforme Delta Lake |
| **Analytics engineer** | Transformer les données propres en tables prêtes à l'analyse, documentées et testées | La table des retards par entrepôt et par jour |
| **Data analyst** | Répondre aux questions métier, construire les tableaux de bord | Le taux de retard par créneau |
| **Data scientist** | Construire des modèles qui prédisent ou expliquent | Le modèle de prédiction des retards (jour 2) |
| **ML engineer** | Mettre les modèles en production et les surveiller | Le service du modèle, la détection de dérive |
| **Data product owner** | Décider quoi construire en premier, selon la valeur métier | Prioriser la prévention des retards à Lille |
| **Data steward** | Tenir le glossaire et suivre la qualité au quotidien | La définition officielle du retard |

{#organisation}
## Trois façons d'organiser l'équipe

| Organisation | Comment | Avantages | Risques |
|---|---|---|---|
| **Centralisée** | Une seule équipe data sert toute l'entreprise | Des standards communs, des experts qui s'entraident | Un goulot d'étranglement, loin du métier |
| **Décentralisée** | Chaque service a ses propres profils data | Proche du métier, réactive | Des outils et des chiffres différents partout |
| **Hybride** (en étoile) | Une équipe centrale fournit la plateforme et les règles ; des profils data travaillent dans chaque service | Le meilleur des deux | Demande une coordination réelle |

L'organisation hybride est la plus répandue dans les entreprises qui avancent sur le sujet. C'est aussi la traduction concrète du Data Mesh vu ce matin : une **plateforme en libre-service** au centre, des **domaines** autour.

{#former}
## Constituer et former les équipes

Recruter des experts ne suffit pas. Il faut aussi que **le reste de l'entreprise sache lire les données** : c'est la **littératie des données**.

- **Pour l'équipe data :** du travail en binôme, la relecture du code des autres (revue de code), des TP comme ceux de cette semaine, une communauté de pratique qui se réunit chaque mois.
- **Pour le métier :** des formations courtes à la lecture d'un taux, d'un graphique, d'une carte de contrôle ; des tableaux de bord en libre-service.
- **Pour les managers :** savoir poser une question à laquelle les données peuvent répondre, et accepter qu'un chiffre contredise leur intuition.

::: callout tip Question fréquente : « Faut-il recruter des licornes ? »
Le profil qui maîtrise à la fois les données, le machine learning, le cloud et le métier est rare et cher. Une équipe de profils complémentaires, avec des pratiques communes (Git, tests, revue de code), va plus loin qu'une personne exceptionnelle : c'est le principe « réduire l'héroïsme » du manifeste DataOps.
:::

{#azure-concepts}
## Introduction à Microsoft Azure : les concepts de base

**Microsoft Azure** est le cloud de Microsoft, l'un des trois grands avec Amazon Web Services et Google Cloud. Quatre notions suffisent pour s'y repérer :

| Notion | Ce que c'est | L'analogie |
|---|---|---|
| **Abonnement** | Le contrat de facturation : tout ce qu'on crée y est facturé | Le compte en banque |
| **Groupe de ressources** | Un dossier qui regroupe les ressources d'un même projet | Un classeur par projet : on le supprime, tout ce qu'il contient disparaît |
| **Région** | Le centre de données où tournent les ressources | L'adresse de l'entrepôt : plus proche, plus rapide ; et elle compte pour le RGPD |
| **Microsoft Entra ID** | L'annuaire des utilisateurs et de leurs droits (anciennement Azure Active Directory) | Le badge d'accès |

{#azure-services}
## Les services data d'Azure, en face des outils de la semaine

Cette semaine, vous utilisez des outils libres, sur votre VM. Chacun a un équivalent managé dans Azure : savoir faire la correspondance permet de passer de l'un à l'autre. Pour mémoire, les équivalents chez Google Cloud sont donnés dans la dernière colonne.

| Ce que vous faites cette semaine | Avec | Dans Azure | Chez Google Cloud |
|---|---|---|---|
| Stocker les fichiers de données | Le dossier `data/`, DVC | **Azure Data Lake Storage Gen2** | Cloud Storage |
| Orchestrer le pipeline | Airflow (jour 3) | **Azure Data Factory**, ou Data Factory dans **Microsoft Fabric** | Cloud Composer (Airflow managé) |
| Traiter avec Spark, stocker en Delta Lake | Spark et Delta Lake (jour 5) | **Azure Databricks**, ou Spark dans **Microsoft Fabric** | Dataproc, BigQuery |
| Suivre les expériences et les modèles | MLflow (jour 2) | **Azure Machine Learning**, qui accepte directement le suivi MLflow | Vertex AI |
| Cataloguer et gouverner les données | Le glossaire, la gouvernance (jour 5) | **Microsoft Purview** | Dataplex |
| Garder les secrets (mots de passe, clés) | Le fichier `.env` | **Azure Key Vault** | Secret Manager |
| Versionner et automatiser | Git, GitHub Actions | **GitHub** ou **Azure DevOps** | Cloud Build |

**Microsoft Fabric** mérite une mention à part. C'est une plateforme d'analytique **en SaaS** qui réunit, dans une même interface, l'ingestion (Data Factory), Spark, un entrepôt SQL, le temps réel et Power BI. Toutes ses données sont rangées dans un stockage unique, **OneLake**, au format Delta Lake : c'est un Lakehouse prêt à l'emploi. Microsoft y concentre aujourd'hui ses nouveautés ; Azure Synapse Analytics, le service précédent, reste proposé à côté.

:::: lab Démo du formateur | ColisVert dans Microsoft Fabric | 6 min
Le formateur montre, dans un environnement Fabric de démonstration, le même travail que ce matin, mais dans le cloud :

1. créer un espace de travail et un **Lakehouse** ;
2. y importer `livraisons.csv` et l'enregistrer comme **table Delta** ;
3. calculer le taux de retard par entrepôt en SQL.

Observez ce que vous n'avez **pas** eu à faire : installer Spark, gérer un serveur, configurer un stockage. C'est l'apport du SaaS. Observez aussi ce que vous avez **toujours** à faire : nettoyer les données, définir le retard, contrôler la qualité.

::: solution Le résultat attendu
Le même que la Cellule 4 du matin : **Lille 27,5 %**, Toulouse 13,9 %, Nantes 12,2 %, Lyon 12,0 %. Les données sont les mêmes ; seul l'outil change.
:::
::::

{#quiz}
## Quiz de validation

```quiz
- q: Quel rôle met les modèles en production et surveille leur dérive ?
  options: [Le data analyst, Le data steward, Le ML engineer, Le data product owner]
  answer: 2
  explain: Le data scientist construit le modèle ; le ML engineer le fait tourner et le surveille.
- q: Quel est le principal risque d'une organisation décentralisée ?
  options:
    - Un goulot d'étranglement dans l'équipe centrale
    - Des outils et des chiffres différents d'un service à l'autre
    - Un coût de licence plus élevé
    - L'absence de profils data
  answer: 1
  explain: Sans plateforme ni règles communes, chaque service calcule ses propres chiffres.
- q: Dans Azure, à quoi sert un groupe de ressources ?
  options:
    - À facturer les clients
    - À regrouper les ressources d'un même projet, pour les gérer et les supprimer ensemble
    - À choisir le centre de données
    - À stocker les mots de passe
  answer: 1
  explain: C'est le classeur du projet. La facturation relève de l'abonnement, les secrets de Key Vault.
- q: Quel service Azure correspond le mieux au suivi des expériences fait avec MLflow ?
  options: [Azure Key Vault, Microsoft Purview, Azure Machine Learning, Azure Data Lake Storage]
  answer: 2
  explain: Azure Machine Learning accepte directement le suivi des expériences au format MLflow.
```
