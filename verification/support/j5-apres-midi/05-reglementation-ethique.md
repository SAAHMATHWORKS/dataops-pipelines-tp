---
subtitle: >-
  L'IA en Europe a désormais son règlement, l'AI Act, dont le calendrier a été retouché en 2026. Il
  s'ajoute au RGPD, qui s'applique dès qu'une donnée personnelle passe par un LLM. On voit qui doit
  quoi et à partir de quand, ce que la CNIL recommande, puis on regarde des cas réels où l'IA a
  causé du tort, pour en tirer les réflexes d'une équipe DataOps.
objectives:
  - Classer un système d'IA selon les niveaux de risque de l'AI Act, et citer les obligations principales de chaque niveau
  - Donner le calendrier d'application de l'AI Act, y compris les reports de l'omnibus numérique de 2026
  - Appliquer les principes du RGPD à un traitement qui utilise un LLM ou un agent
  - Analyser des cas réels de dommages causés par l'IA, et en tirer des règles de conception
---

::: callout warn Ceci n'est pas un avis juridique
Cette page donne les repères qu'un professionnel de la donnée doit connaître, à jour au 17 novembre 2026. Pour un projet réel, la qualification d'un système et les obligations exactes se décident avec le délégué à la protection des données et le service juridique.
:::

{#ai-act}
## L'AI Act : une approche par les risques

Le **règlement européen sur l'IA** (règlement (UE) 2024/1689) est entré en vigueur le 1er août 2024. Il ne réglemente pas une technologie, mais des **usages**, selon le risque qu'ils font courir aux personnes :

| Niveau | Exemples | Ce qui est exigé |
|---|---|---|
| **Interdit** (article 5) | Notation sociale ; manipulation qui exploite les vulnérabilités ; reconnaissance des émotions au travail et à l'école (sauf raison médicale ou de sécurité) ; collecte massive d'images de visages ; catégorisation biométrique selon des données sensibles | Interdiction pure et simple |
| **Haut risque** (annexes I et III) | Recrutement et gestion des travailleurs ; notation de crédit ; accès aux services publics et essentiels ; éducation ; infrastructures critiques ; composants de sécurité de produits réglementés | Gestion des risques, qualité des données, documentation, journaux, contrôle humain, robustesse, enregistrement ; pour le **déployeur** : usage conforme, contrôle humain par des personnes compétentes, conservation des journaux, information des travailleurs |
| **Risque limité** (article 50) | Chatbot ; contenu généré (images, sons, vidéos, hypertrucages) ; texte généré publié pour informer le public | **Transparence** : dire qu'on parle à une IA, marquer et signaler les contenus générés |
| **Risque minimal** | Filtre anti-spam, prévision de retard de ColisVert, agent d'analyse interne du TP | Pas d'obligation propre ; bonnes pratiques volontaires |

**Deux rôles à ne pas confondre.** Le **fournisseur** développe le système et le met sur le marché ; le **déployeur** l'utilise sous sa responsabilité. ColisVert, qui utilise `gpt-6-luna` pour ses SMS, est **déployeur**. Elle deviendrait fournisseur si elle vendait son agent à d'autres transporteurs.

**Les modèles d'IA à usage général** (les LLM eux-mêmes) ont leurs propres obligations, à la charge de leurs **fournisseurs** (OpenAI, Mistral AI, Google…) : documentation technique, politique de respect du droit d'auteur, résumé des données d'entraînement, et des obligations renforcées pour les modèles à risque systémique.

**La maîtrise de l'IA** (article 4) : fournisseurs et déployeurs doivent favoriser la formation de leur personnel à l'IA. La formation de cette semaine en fait partie.

{#calendrier}
## Le calendrier, modifié en 2026

Le règlement s'applique par étapes. En 2026, le **règlement « omnibus numérique sur l'IA »** (règlement (UE) 2026/1744 du 8 juillet 2026, en vigueur depuis le 27 juillet 2026) a repoussé les obligations des systèmes à haut risque :

| Date | Ce qui s'applique |
|---|---|
| 2 février 2025 | Les **interdictions** (article 5) et la **maîtrise de l'IA** (article 4) |
| 2 août 2025 | Les obligations des **modèles à usage général**, la gouvernance, les sanctions |
| 2 août 2026 | Le reste du règlement, dont la **transparence** de l'article 50 (avec un délai jusqu'au 2 décembre 2026 pour le marquage des contenus générés par les systèmes déjà sur le marché) |
| **2 décembre 2027** | Les systèmes à **haut risque de l'annexe III** (emploi, crédit, éducation…) : initialement le 2 août 2026 |
| **2 août 2028** | Les systèmes à **haut risque de l'annexe I** (composants de sécurité de produits réglementés) : initialement le 2 août 2027 |

**Les sanctions** vont jusqu'à 35 millions d'euros ou 7 % du chiffre d'affaires mondial pour une pratique interdite, et jusqu'à 15 millions d'euros ou 3 % pour les autres manquements.

**Le report n'est pas une pause.** Un système à haut risque qui sera en service en décembre 2027 se conçoit maintenant : journaux, contrôle humain, documentation. Ce sont des exigences d'ingénierie, et elles ressemblent beaucoup à ce qu'on a construit cette semaine.

{#rgpd}
## Le RGPD, dès qu'une donnée personnelle passe par un LLM

Envoyer le message d'un client à un LLM, c'est **traiter** une donnée personnelle. Tout le RGPD s'applique, comme ce matin pour la fiche du produit de données :

| Principe | Avec un LLM | Dans le TP |
|---|---|---|
| **Base légale et finalité** | Un traitement, un objectif écrit ; pas de réutilisation des données pour autre chose | Prévenir le client d'un retard |
| **Minimisation** | N'envoyer que ce qui sert au résultat | Le rédacteur n'envoie que le numéro du colis, l'entrepôt et la météo |
| **Sous-traitance** | Le fournisseur du LLM est un sous-traitant : un contrat (article 28), des garanties de sécurité | La plateforme passe par l'API d'OpenAI, pas par une application grand public |
| **Transferts hors de l'UE** | Vérifier le pays de traitement et le mécanisme de transfert ; préférer un hébergement européen quand c'est possible | À vérifier pour chaque fournisseur |
| **Durée de conservation** | Ne pas laisser les échanges chez le fournisseur sans raison | `store=false`, imposé par la passerelle ; journal sans contenu |
| **Information et droits** | Dire aux personnes que l'IA intervient ; pouvoir répondre à une demande d'accès ou d'effacement | Mention dans la politique de confidentialité |
| **Décisions automatisées** (article 22) | Pas de décision produisant des effets juridiques ou significatifs fondée **uniquement** sur un traitement automatisé, sauf exceptions encadrées | L'agent prépare, l'équipe décide |
| **Analyse d'impact** (AIPD, article 35) | Obligatoire quand le traitement présente un risque élevé : évaluation systématique de personnes, données sensibles à grande échelle, technologie nouvelle | La notation des livreurs en demanderait une |

La **CNIL** a publié des fiches pratiques sur l'IA et le RGPD, finalisées en 2025, avec une **liste de vérification** : un bon point de départ pour un projet.

{#ethique}
## Des cas réels, et ce qu'ils enseignent

| Cas | Ce qui s'est passé | Le réflexe à en tirer |
|---|---|---|
| **Recrutement chez Amazon** (révélé en 2018) | Un modèle de tri des CV, entraîné sur dix ans de recrutements surtout masculins, pénalisait les CV qui mentionnaient « women's ». Le projet a été abandonné | Les biais du passé deviennent les règles de demain : mesurer l'équité par groupe, comme ce matin par entrepôt |
| **Allocations familiales aux Pays-Bas** (*toeslagenaffaire*) | Un système de détection de fraude utilisait notamment la nationalité ; des milliers de familles ont été accusées à tort et sommées de rembourser. Le gouvernement a démissionné en janvier 2021, et l'autorité de protection des données a sanctionné l'administration fiscale | Une variable sensible ne se cache pas dans un modèle ; une décision lourde exige un humain et un recours |
| **Le chatbot d'Air Canada** (2024) | Le chatbot a inventé une règle de remboursement pour un deuil. Un tribunal canadien a jugé la compagnie responsable de ce qu'avait dit son chatbot | Ce que dit votre IA engage l'entreprise : garde-fous et réponses vérifiées pour tout ce qui est un engagement |
| **Les avocats de l'affaire Avianca** (New York, 2023) | Des avocats ont déposé un mémoire citant des décisions de justice inventées par ChatGPT ; ils ont été sanctionnés | Une référence générée se vérifie à la source, toujours |
| **Le code source chez Samsung** (2023) | Des salariés ont collé du code confidentiel dans un outil d'IA grand public ; l'entreprise a restreint ces outils | L'IA de l'ombre est un risque de fuite : proposer un outil autorisé plutôt qu'interdire seulement |
| **L'hypertrucage chez Arup** (Hong Kong, 2024) | Un salarié a viré environ 25 millions de dollars après une visioconférence où ses « collègues » étaient générés par IA | Une demande sensible se confirme par un second canal, quelle que soit la qualité de l'image |

**Et l'empreinte environnementale ?** Entraîner et faire tourner des LLM consomme de l'électricité et de l'eau dans les centres de données. Pour une équipe data, la règle du jour 4 tient toujours : le plus petit modèle qui suffit, et pas de LLM là où une règle fait le travail.

{#quiz}
## Quiz

```quiz
- q: ColisVert utilise gpt-6-luna pour rédiger ses SMS. Quel est son rôle au sens de l'AI Act ?
  options:
    - Fournisseur du modèle
    - Déployeur du système
    - Aucun, l'AI Act ne la concerne pas
    - Autorité de surveillance
  answer: 1
  explain: OpenAI est fournisseur du modèle ; ColisVert l'utilise sous sa responsabilité, elle est déployeur.
- q: Depuis quand les pratiques interdites de l'AI Act s'appliquent-elles ?
  options:
    - 1er août 2024
    - 2 février 2025
    - 2 août 2026
    - 2 décembre 2027
  answer: 1
  explain: Le 1er août 2024 est l'entrée en vigueur ; les interdictions s'appliquent six mois plus tard.
- q: Un système de recrutement par IA mis en service en 2027 doit être conforme aux exigences du haut risque à partir de quand ?
  options:
    - 2 août 2026
    - 2 décembre 2027, depuis l'omnibus numérique de 2026
    - 2 août 2028
    - Jamais, le recrutement n'est pas concerné
  answer: 1
  explain: L'emploi est dans l'annexe III ; l'omnibus a repoussé ces obligations du 2 août 2026 au 2 décembre 2027.
- q: Quel principe du RGPD le rédacteur du TP applique-t-il en n'envoyant que trois champs ?
  options:
    - La portabilité
    - La minimisation
    - Le droit d'opposition
    - La certification
  answer: 1
  explain: Ne transmettre que ce qui sert au traitement ; le nom et l'adresse n'apportent rien au SMS.
- q: Que retenir du cas du chatbot d'Air Canada ?
  options:
    - Les chatbots sont interdits
    - L'entreprise est responsable de ce que dit son IA ; les engagements doivent être vérifiés
    - Il faut un modèle plus gros
    - Le client avait tort
  answer: 1
  explain: C'est pourquoi le garde-fou du TP interdit toute promesse et tout geste commercial dans les SMS.
```
