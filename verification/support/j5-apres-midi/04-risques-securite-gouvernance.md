---
subtitle: >-
  Un LLM dans un système d'information, c'est un nouveau composant, avec de nouvelles façons de
  tomber en panne et d'être attaqué. On fait le tour des pièges à éviter, on range les risques
  avec les listes de l'OWASP, puis on voit comment une entreprise gouverne l'IA : une passerelle,
  des identités pour les agents, des traces, des évaluations, et deux cadres de référence, ISO/IEC
  42001 et le NIST AI RMF.
objectives:
  - Reconnaître les pièges courants d'un projet à base de LLM ou d'agent
  - Citer les principaux risques des listes OWASP 2026 pour les LLM et pour les applications agentiques, et leurs parades
  - Décrire les mesures de sécurité et de gouvernance de l'IA dans un système d'information
  - Situer ISO/IEC 42001, ISO/IEC 42005 et le NIST AI RMF
---

{#pieges}
## Les pièges à éviter

| Piège | À quoi il ressemble | Ce qu'il faut faire |
|---|---|---|
| **La démo qui marche** | Cinq questions réussies en réunion, et l'on déploie | Un jeu de questions de référence, évalué à chaque changement de consigne ou de modèle |
| **La confiance aveugle** | L'humain valide sans relire, parce que « l'IA a raison d'habitude » (biais d'automatisation) | Montrer les sources et les chiffres prouvés ; former les utilisateurs ; garder des contrôles par sondage |
| **L'IA de l'ombre** | Des salariés collent du code ou des données clients dans un outil grand public | Un outil d'entreprise autorisé et commode, une règle claire, une formation |
| **Les clés partout** | Une clé d'API dans un notebook, sur des VM, dans un dépôt Git | Une passerelle, des jetons personnels révocables, un coffre-fort à secrets |
| **L'agent tout-puissant** | Un agent avec les droits d'écriture de son créateur « pour aller plus vite » | Des outils en lecture seule par défaut, des droits minimaux, une approbation humaine pour agir |
| **La facture surprise** | Une boucle qui tourne en rond, un fichier de 300 pages dans chaque appel | Quotas, plafonds de jetons, tours bornés, alertes de dépense |
| **La dépendance** | Le fournisseur change son modèle ou ses prix, et tout le comportement change | Un modèle épinglé par version, un repli, des évaluations pour comparer avant de migrer |

{#owasp-llm}
## Les risques des applications à base de LLM (OWASP 2026)

L'OWASP, la fondation de référence en sécurité des applications web, publie depuis 2023 une liste des dix risques principaux des applications à base de LLM. L'édition 2026 est sortie en août 2026 :

| Rang | Risque | Chez ColisVert | Parade |
|---|---|---|---|
| LLM01 | **Injection de requête** (*prompt injection*), y compris cachée dans une image ou un document | Le message piégé du TP | Schéma fermé, vérification par le code, aucun pouvoir d'agir laissé au texte lu |
| LLM02 | **Divulgation d'informations sensibles** | Le nom et l'adresse d'un client envoyés au LLM | Minimisation (trois champs dans le rédacteur), pas de conservation chez le fournisseur |
| LLM03 | **Agentivité excessive** (*excessive agency*), en hausse de la 6e à la 3e place | Un agent qui pourrait promouvoir un modèle ou envoyer des SMS seul | Outils en lecture seule, liste blanche, approbation humaine |
| LLM04 | **Chaîne d'approvisionnement** | Un modèle ou une bibliothèque téléchargés sans contrôle | Sources vérifiées, versions épinglées, comme l'image figée des TP |
| LLM05 | **Empoisonnement des données et du modèle** | Des données d'entraînement ou d'ajustement trafiquées | Contrats de données, traçabilité (DVC, lignage) |
| LLM06 | **Consommation illimitée** | Une boucle d'agent sans fin | Quotas de la passerelle, tours bornés |
| LLM07 | **Désinformation** (hallucinations présentées comme des faits) | Un chiffre inventé dans la note | Ancrage des chiffres, sources affichées |
| LLM08 | **Exposition du contexte caché** (anciennement fuite du prompt système) | Les consignes ou des données internes récitées à un client | Rien de secret dans les consignes ; les droits se vérifient dans le code |
| LLM09 | **Faiblesses des vecteurs et des plongements** | Un document piégé dans l'index d'un RAG, des droits d'accès perdus | Contrôle des sources indexées, filtrage par droits à la recherche |
| LLM10 | **Mauvais traitement des sorties** | Une sortie du LLM exécutée comme du SQL ou affichée comme du HTML | Traiter toute sortie comme une donnée non fiable : valider, échapper |

{#owasp-agents}
## Les risques propres aux agents

En décembre 2025, l'OWASP a ajouté une liste dédiée aux **applications agentiques**. Ses premiers risques parlent d'eux-mêmes : le **détournement d'objectif** de l'agent (ASI01), le **mauvais usage des outils** (ASI02), l'**abus d'identité et de privilèges** (ASI03). On y trouve aussi l'empoisonnement de la **mémoire** de l'agent, les communications non sécurisées entre agents, les **défaillances en cascade** (une erreur d'un agent reprise par un autre) et l'exploitation de la **confiance** des humains.

Les parades se retrouvent toutes dans la boucle du TP : liste blanche, arguments vérifiés, erreurs rendues au LLM plutôt qu'exécutées, tours bornés, journal complet, et une identité propre à l'agent pour savoir qui a fait quoi.

{#gouvernance}
## Sécurité et gouvernance de l'IA dans le SI

**L'analogie du badge.** Dans un entrepôt, chaque personne a un badge à son nom, qui n'ouvre que les portes utiles, et chaque passage est enregistré. Un agent doit être traité comme un salarié de plus : une identité, des droits limités, un journal.

| Mesure | Ce qu'elle apporte | Ce qu'on a vu cette semaine |
|---|---|---|
| **Une passerelle d'IA** | Un point d'entrée unique : clés centralisées, modèles autorisés, quotas, journal, filtrage | La passerelle de Training Lab ; en entreprise, Azure API Management devant Azure OpenAI, ou la passerelle de la plateforme |
| **Une identité par agent** | Savoir qui a fait quoi, et retirer les droits d'un agent sans toucher à ceux d'un humain | L'agent d'opérations de Fabric reçoit une identité Microsoft Entra (Agent ID) |
| **Des droits minimaux** | Un agent compromis ne peut faire que peu de dégâts | L'agent de données de Fabric ne fait que des requêtes de lecture |
| **Des traces** | Comprendre une réponse, reproduire un incident, auditer | Les traces MLflow du TP |
| **Des évaluations** | Mesurer la qualité avant chaque mise en service | Le LLM simulé en CI, un jeu de référence pour le vrai LLM |
| **La classification des données** | Savoir ce qui peut partir chez un fournisseur | La fiche du produit de données de ce matin, et les étiquettes de Microsoft Purview |
| **Un inventaire des systèmes d'IA** | Savoir ce qui tourne, qui en est responsable, à quel niveau de risque | Exigé de fait par l'AI Act : on ne classe que ce qu'on connaît |

{#cadres}
## Deux cadres de référence

- **ISO/IEC 42001:2023** : la norme de **système de management de l'IA**. Elle fait pour l'IA ce qu'ISO/IEC 27001 fait pour la sécurité de l'information : une politique, des rôles, une appréciation des risques, des contrôles (son annexe A), et l'amélioration continue (planifier, faire, vérifier, agir : le PDCA du jour 4). Une entreprise peut se faire **certifier**. Deux normes l'accompagnent : ISO/IEC 23894 pour la gestion des risques de l'IA, et **ISO/IEC 42005:2025** pour l'**étude d'impact** d'un système d'IA sur les personnes et la société.
- **Le NIST AI RMF** (*AI Risk Management Framework*, États-Unis, 2023) : un cadre gratuit et non contraignant, en quatre fonctions. **Gouverner** (rôles, politiques), **cartographier** (contexte, usages), **mesurer** (tests, métriques) et **gérer** (traiter les risques, suivre). Un profil complémentaire, publié en 2024, traite de l'IA générative.

Les deux se combinent bien avec l'AI Act : la norme donne l'organisation, le règlement donne les obligations.

{#quiz}
## Quiz

```quiz
- q: Quel risque de l'OWASP correspond à un agent qui peut promouvoir un modèle en production sans contrôle ?
  options:
    - La chaîne d'approvisionnement
    - L'agentivité excessive
    - Les faiblesses des vecteurs
    - La désinformation
  answer: 1
  explain: Trop de droits, trop d'autonomie ; la parade est la lecture seule, la liste blanche et l'approbation humaine.
- q: Pourquoi donner une identité propre à chaque agent ?
  options:
    - Pour le facturer
    - Pour savoir qui a fait quoi, limiter ses droits et les lui retirer sans toucher à ceux des humains
    - Parce que le LLM l'exige
    - Pour qu'il ait un nom sympathique
  answer: 1
  explain: C'est le badge de l'entrepôt ; sans identité, une action d'agent se confond avec celle de son créateur.
- q: Une sortie de LLM est insérée telle quelle dans une requête SQL. Quel risque ?
  options:
    - Aucun, le LLM est fiable
    - Le mauvais traitement des sorties - une sortie doit être traitée comme une donnée non fiable
    - La consommation illimitée
    - La divulgation d'informations
  answer: 1
  explain: Comme une saisie d'utilisateur, la sortie se valide et s'échappe ; mieux, le LLM choisit des paramètres, pas du SQL.
- q: Que fournit ISO/IEC 42001 ?
  options:
    - Une liste de modèles autorisés
    - Un système de management de l'IA - politique, rôles, risques, contrôles, amélioration continue - certifiable
    - Une loi européenne
    - Un outil de traçage
  answer: 1
  explain: C'est l'équivalent d'ISO/IEC 27001 pour l'IA ; l'AI Act, lui, est un règlement.
```
