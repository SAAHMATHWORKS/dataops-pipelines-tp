---
subtitle: >-
  Les plateformes de données intègrent maintenant leurs propres agents. Démonstration dans Microsoft
  Fabric, sur les colis de ColisVert : Copilot comme assistant, un agent de données qui répond en
  lecture seule à des questions en langage naturel, et un agent d'opérations qui surveille des
  données en temps réel et propose des actions à approuver. Puis un tour des autres plateformes.
objectives:
  - Situer Copilot, l'agent de données et l'agent d'opérations de Fabric sur l'échelle chatbot, assistant, agent
  - Décrire la configuration d'un agent de données - sources, consignes, exemples de requêtes - et vérifier ses réponses
  - Décrire le fonctionnement d'un agent d'opérations - règles, recommandations, approbation, identité
  - Comparer l'offre d'agents de Fabric, Copilot Studio et Power Automate, Snowflake et Databricks avec le TP
---

::: callout info Démonstration du formateur
Cette partie est une démonstration : vous regardez, vous posez des questions. Les prérequis de Fabric (capacité payante, paramètres du locataire) ne permettent pas de la faire sur chaque poste.
:::

{#trois-visages}
## Trois visages de l'IA dans Fabric

| Dans Fabric | Famille | Ce qu'il fait | Pouvoir d'agir |
|---|---|---|---|
| **Copilot** (notebooks, Power BI, Data Factory) | Assistant | Écrit du code, une formule, un rapport, à la demande ; l'utilisateur accepte ou non | Aucun : l'humain exécute |
| **Agent de données** (*data agent*) | Agent | Répond en langage naturel à partir des données : choisit la source, écrit la requête (SQL, DAX ou KQL), l'exécute, met en forme | **Lecture seule** |
| **Agent d'opérations** (*operations agent*, Real-Time Intelligence) | Agent | Surveille des données en temps réel selon des règles, recommande des actions dans Teams | Agit **après approbation** d'un humain |

{#prerequis}
## Prérequis, à vérifier avant le jour J

- **Une capacité Fabric payante**, F2 au minimum, pour l'agent de données. L'agent d'opérations ne fonctionne pas sur une capacité d'essai. Une capacité F2 se met en pause hors des démonstrations : on ne paie que les heures où elle tourne.
- **Les paramètres du locataire** : Copilot et Azure OpenAI activés pour l'organisation, l'agent de données et les agents d'opérations autorisés. Pour une capacité hors des régions États-Unis et Union européenne, le traitement inter-régions doit aussi être autorisé.
- **La langue** : la documentation de l'agent de données indique que les langues autres que l'anglais ne sont pas encore prises en charge. La démonstration pose donc ses questions **en anglais**.
- **Pour l'agent d'opérations** : un eventhouse (base KQL) ou une ontologie dans l'espace de travail, et un compte Microsoft Teams.

{#donnees}
## Les données de la démonstration

Le formateur a préparé un fichier unique, avec les colis de septembre-octobre et de décembre, et une colonne `periode` :

```python title="Démonstration : le fichier pour Fabric"
lignes_fabric = pd.concat([
    livraisons.drop(columns="jour_semaine").assign(periode="sept-oct"),
    decembre.drop(columns="jour_semaine").assign(periode="decembre"),
])
lignes_fabric.to_csv(DOSSIER_DATA / "livraisons_fabric.csv", index=False)
print(f"{len(lignes_fabric)} colis, {lignes_fabric.shape[1]} colonnes")
print((100 * lignes_fabric.groupby(["entrepot", "periode"])["en_retard"].mean()).round(1).unstack())
```

```plaintext title="Sortie attendue"
8461 colis, 12 colonnes
periode   decembre  sept-oct
entrepot                    
Lille         38.0      27.5
Lyon          18.0      12.0
Nantes        19.8      12.2
Toulouse      16.9      13.9
```

Dans Fabric, le fichier est chargé dans le lakehouse `lh_colisvert` (**Get data › Upload files**, puis **Load to tables › New table** : `livraisons`). Le tableau ci-dessus est la **réponse de référence** : on va la demander à l'agent, et comparer.

{#agent-donnees}
## Démonstration 1 : l'agent de données

1. **Créer l'agent** : dans l'espace de travail, **New item › Data agent**, nom `agent-colisvert`.
2. **Ajouter la source** : le lakehouse `lh_colisvert`, table `livraisons` (jusqu'à cinq sources : lakehouses, entrepôts, modèles sémantiques Power BI, bases KQL, ontologies).
3. **Écrire les consignes de l'agent**, en anglais, comme une fiche de produit de données :

```plaintext title="Consignes de l'agent de données (en anglais)"
ColisVert is a parcel carrier. Table livraisons has one row per parcel.
en_retard = 1 means the parcel arrived after the promised delay (delai_promis_h).
periode is 'sept-oct' (reference period) or 'decembre'.
A late delivery rate is AVG(en_retard) * 100, rounded to one decimal.
Never use delai_reel_h to explain or predict a delay: it is only known after delivery.
```

4. **Ajouter des exemples de requêtes** (paires question et SQL, jusqu'à 100 par source) : ils montrent à l'agent les calculs « maison ».
5. **Poser les questions**, et lire la requête générée à chaque fois :
   - *What is the late delivery rate per warehouse in each period?* La réponse doit correspondre au tableau de référence : Lille 27,5 % puis 38,0 %, Lyon 12,0 % puis 18,0 %, Nantes 12,2 % puis 19,8 %, Toulouse 13,9 % puis 16,9 %.
   - *Which warehouse got worse the most in December?* Lille en points (+10,5), Nantes en proportion.
   - *Delete the December rows.* L'agent ne génère que des requêtes de lecture : il ne peut rien supprimer.

**Ce qu'on vérifie, comme au TP :** la requête générée (le bon filtre, la bonne colonne), et les chiffres face à une référence calculée par le code. Une question ambiguë donne une réponse ambiguë : les consignes et les exemples de requêtes sont le **contrat** de l'agent, à versionner et à tester comme le reste.

**Où on le retrouve ensuite :** publié, l'agent de données s'utilise depuis Microsoft 365 Copilot, Teams, Copilot Studio ou Microsoft Foundry, toujours avec les droits de l'utilisateur qui pose la question.

{#agent-operations}
## Démonstration 2 : l'agent d'opérations

Si la capacité le permet, en direct ; sinon, sur les écrans préparés.

1. **Les données** : les colis arrivent en continu dans un eventhouse (base KQL), par exemple depuis un flux d'événements.
2. **La configuration** : des consignes en langage naturel (« prévenir l'équipe quand le taux de retard de la dernière heure dépasse 27 % à Lille »), la base KQL, et les actions permises.
3. **Le plan de jeu** (*playbook*) : Fabric en déduit les règles et les requêtes KQL qui les calculent. **On les relit avant de démarrer l'agent**, comme une revue de code.
4. **En marche** : chaque règle est évaluée toutes les cinq minutes. Quand elle se déclenche, l'agent envoie une recommandation dans Teams ; un humain l'**approuve** ou non, et l'action s'exécute seulement après.
5. **L'identité et le journal** : l'agent reçoit sa propre identité Microsoft Entra ; il agit avec les droits de son créateur, mais ses actions sont attribuées à l'agent, et le journal d'activité garde chaque règle évaluée, chaque recommandation et chaque réponse.

**Le lien avec la semaine :** c'est la carte de contrôle du jour 4, branchée sur un flux, avec l'agent du TP pour rédiger et le niveau 2 d'autonomie, l'action avec approbation.

{#plateformes}
## Les autres plateformes

| Plateforme | Ce qu'elle propose pour les agents | Le lien avec le TP |
|---|---|---|
| **Copilot Studio et Power Automate** | Des agents avec des déclencheurs (un courriel, un fichier, un évènement) et des « flux d'agent » qui enchaînent des étapes ; ils peuvent consulter un agent de données de Fabric | La boucle, les outils (des connecteurs), l'approbation humaine |
| **Snowflake** | Cortex Agents (disponibles depuis novembre 2025) et Snowflake Intelligence : des agents qui interrogent les tables et les documents de Snowflake | Des outils sur les données, en lecture, avec les droits de l'utilisateur |
| **Databricks** | Agent Bricks pour construire et évaluer des agents sur ses données, Genie pour les questions en langage naturel, MLflow pour tracer et évaluer | Les traces et l'évaluation du TP, avec le même MLflow |
| **Microsoft Foundry** | La plateforme de Microsoft pour construire ses propres agents, avec les modèles, les outils et l'évaluation | Ce que fait notre code, en service géré |

**Ce qui ne change pas d'une plateforme à l'autre :** un LLM qui choisit, des outils que la plateforme exécute, des droits, un journal, et un humain pour les décisions. Les questions à poser à un éditeur sont celles de l'après-midi : quelles données sortent, où ; quels droits a l'agent ; qu'est-ce qui est tracé ; comment évalue-t-on la qualité avant de mettre en service ?

{#quiz}
## Quiz

```quiz
- q: L'agent de données de Fabric peut-il supprimer des lignes d'une table ?
  options:
    - Oui, s'il est bien configuré
    - Non, il ne génère que des requêtes de lecture
    - Oui, avec Copilot
    - Seulement dans un eventhouse
  answer: 1
  explain: Lecture seule par construction ; c'est le principe des droits minimaux.
- q: Comment vérifier les réponses d'un agent de données pendant la démonstration ?
  options:
    - On lui fait confiance
    - On lit la requête générée et l'on compare les chiffres à une référence calculée par le code
    - On lui repose la même question jusqu'à obtenir le même chiffre
    - On augmente la capacité
  answer: 1
  explain: Même méthode que l'ancrage du TP - un chiffre doit venir d'un calcul vérifiable.
- q: Que fait un humain dans le fonctionnement de l'agent d'opérations ?
  options:
    - Rien, l'agent est autonome
    - Il approuve ou non la recommandation avant que l'action s'exécute
    - Il écrit le code KQL à la main
    - Il redémarre l'agent toutes les cinq minutes
  answer: 1
  explain: C'est le niveau 2 d'autonomie - l'agent propose une action précise, l'humain l'approuve.
```
