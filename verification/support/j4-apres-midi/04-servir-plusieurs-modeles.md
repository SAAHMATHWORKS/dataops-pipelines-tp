---
subtitle: >-
  En production, un modèle est rarement seul. Le champion répond pendant qu'un challenger fait ses
  preuves, un entrepôt a son propre modèle, une règle métier ou un générateur de texte complète la
  prédiction. Faut-il un point d'accès par modèle, ou un seul pour tous ? On compare les
  architectures, on regarde ce que proposent Azure, Databricks, Google Cloud et Fabric, puis on
  ouvre le format PyFunc de MLflow, qui permet d'assembler plusieurs modèles en un seul.
objectives:
  - Citer les raisons de servir plusieurs modèles à la fois
  - Comparer quatre architectures de service et leurs compromis
  - Situer la répartition du trafic et l'ombre dans Azure Machine Learning, Databricks, Vertex AI et Fabric
  - Décrire l'anatomie d'un modèle PyFunc - load_context, predict, artefacts, configuration, signature avec paramètres
  - Expliquer comment préparer un composant de texte pour qu'un LLM puisse le remplacer sans risque
---

{#pourquoi}
## Pourquoi plusieurs modèles à la fois

| Situation | Exemple chez ColisVert |
|---|---|
| **Mettre en service sans risque** (jour 2) | Le challenger tourne **en ombre** à côté du champion, puis reçoit 5 % du trafic (canari) |
| **Des segments différents** | Lille, où le temps et le volume de décembre changent tout, a son propre modèle |
| **Des exigences différentes** | Le site de suivi veut une réponse en quelques millisecondes ; le lot de 7 h peut prendre son temps et utiliser un modèle plus lourd |
| **Une réponse composée** | La probabilité de retard, plus le texte du SMS, plus une règle métier (jamais d'alerte pour un colis déjà livré) |

{#architectures}
## Quatre architectures

**L'analogie du centre de tri.** On peut ouvrir un guichet par service (colis, courrier, recommandés), et le client choisit sa file. On peut aussi ouvrir un guichet unique, derrière lequel un agent oriente chaque demande. Les deux marchent ; ils ne coûtent pas la même chose et ne tombent pas en panne de la même façon.

| Architecture | Comment | Avantages | Inconvénients |
|---|---|---|---|
| **Un point d'accès par modèle** | Chaque modèle est un service à part | Isolation : une panne ne touche qu'un modèle ; chacun se dimensionne seul | N services à exploiter ; c'est le client qui choisit le modèle |
| **Répartition par la plateforme** | Un point d'accès, plusieurs déploiements, des pourcentages de trafic | Canari et ombre sans code ; retour arrière en changeant un pourcentage | Le tirage est **aléatoire** : on ne choisit pas le modèle selon le contenu de la requête |
| **Un modèle composite** (PyFunc) | Un seul modèle MLflow contient plusieurs modèles et la logique qui les combine | Routage selon le contenu (l'entrepôt), ombre, réponse composée ; une seule version à déployer | Tous les modèles sont livrés ensemble ; la mémoire est la **somme** des modèles ; on ne dimensionne pas un modèle seul |
| **Serveur multi-modèles** | Un serveur charge à la demande des centaines de modèles (un par client, par exemple) | Très économe quand chaque modèle sert peu | Premier appel lent (chargement) ; outillage spécifique |

**Comment choisir.** Pour un champion et un challenger, la répartition par la plateforme est la plus simple. Dès que le choix du modèle dépend **du contenu** de la requête, ou que la réponse **combine** plusieurs modèles, le modèle composite s'impose. Le TP 2 en construit un.

{#plateformes}
## Ce que proposent les plateformes

::: callout info Vérifié dans la documentation des éditeurs, novembre 2026
- **Azure Machine Learning**, points de terminaison en ligne managés : un point de terminaison porte plusieurs déploiements (`blue`, `green`). La propriété `traffic` répartit les requêtes en pourcentages (`--traffic "blue=90 green=10"`). La propriété `mirror_traffic` **copie** une part du trafic vers un déploiement en ombre : les clients ne reçoivent que les réponses du déploiement principal. On ne peut copier que vers **un** déploiement, et au plus **50 %** du trafic. L'en-tête `azureml-model-deployment` force un déploiement précis.
- **Databricks Model Serving** : un point de terminaison sert plusieurs « entités servies », avec une configuration de trafic en pourcentages (par exemple `current` 90 %, `challenger` 10 %). On ne mélange pas des types de modèles différents sur le même point.
- **Google Cloud Vertex AI** : plusieurs modèles déployés sur un même point de terminaison, avec une répartition du trafic en pourcentages.
- **Microsoft Fabric**, points de terminaison de modèles ML (**en préversion**) : chaque version enregistrée a sa propre adresse (`…/versions/1/score`), et un point par défaut sert la version choisie. Au plus **cinq** versions actives à la fois ; mise en veille après cinq minutes sans requête. Les saveurs prises en charge sont citées : Keras, LightGBM, scikit-learn, XGBoost. La page ne parle ni de répartition du trafic ni de modèles PyFunc personnalisés.

Les quatre plateformes savent servir un modèle MLflow. Un modèle composite PyFunc reste un modèle MLflow : on peut le déployer sur chacune de celles qui acceptent les modèles PyFunc personnalisés, ou le conteneuriser (`mlflow models build-docker`, jour 2).
:::

{#pyfunc}
## Le format PyFunc

**PyFunc** (*Python function*) est la saveur commune de tous les modèles MLflow : quelle que soit la bibliothèque d'origine, le modèle chargé expose une méthode `predict`. Au jour 2, `mlflow models serve` servait la saveur PyFunc d'un modèle scikit-learn. On peut aussi **écrire** son propre modèle PyFunc, en dérivant la classe `mlflow.pyfunc.PythonModel` :

| Élément | Rôle | Dans le service de ColisVert |
|---|---|---|
| `load_context(self, context)` | Appelée **une fois**, au chargement : on y charge ce qui coûte cher | Charge les deux modèles du registre |
| `context.artifacts` | Les fichiers et modèles livrés avec le modèle, téléchargés en local | `champion` → `models:/colisvert-empreinte@leger` ; `challenger` → `…@foret` |
| `context.model_config` | Un dictionnaire de réglages, enregistré avec le modèle | Le seuil de décision (0,40, ce matin) et le chemin du journal |
| `predict(self, context, model_input, params)` | Appelée à **chaque** requête | Choisit le modèle, journalise l'ombre, rédige le SMS |
| La **signature** avec **paramètres** | Décrit les colonnes en entrée et en sortie, et les paramètres acceptés, avec leur type et leur valeur par défaut | `modele` (texte, `champion`), `ombre` (booléen, vrai), `message` (booléen, faux) |

**Un modèle « défini par le code ».** On passe à MLflow le **chemin d'un fichier Python** qui se termine par `set_model(ServiceColisVert())`, au lieu d'un objet Python sérialisé. MLflow enregistre le fichier lui-même : on peut le relire dans l'interface, le comparer d'une version à l'autre, et l'on évite `pickle` et ses risques (notion 1). C'est la forme que recommande la documentation de MLflow pour les modèles personnalisés.

**Les paramètres de requête.** Les **données** décrivent les colis ; les **paramètres** décrivent ce qu'on veut en faire. Ils voyagent à côté des données dans la requête HTTP (`{"dataframe_split": …, "params": {"modele": "challenger"}}`). MLflow les valide contre la signature : un type faux est refusé avec un message clair, un paramètre inconnu est ignoré, avec un avertissement dans le journal du service.

{#llm}
## Préparer la place d'un LLM

Le service a un troisième composant : le **rédacteur**, qui prépare le texte du SMS pour les colis à risque. Aujourd'hui, il remplit un **gabarit** (un texte à trous). Au jour 5, on le remplacera par un **LLM**, appelé à travers la plateforme Training Lab, jamais depuis les VM. Le service est écrit pour que ce remplacement ne touche à rien d'autre :

- **Un contrat stable.** Le rédacteur reçoit un colis et sa probabilité, et renvoie un texte. Le gabarit et le LLM respectent le même contrat : on change l'un pour l'autre en une ligne.
- **Une trace de chaque appel.** La méthode `rediger` porte le décorateur `@mlflow.trace` : chaque appel est enregistré dans MLflow avec ses entrées, sa sortie et sa durée. Pour un gabarit, c'est un luxe ; pour un LLM, c'est indispensable, car il faut pouvoir relire ce qu'il a écrit, et à qui.
- **Un repli.** Un LLM peut être lent (des secondes, contre des microsecondes pour le gabarit), indisponible, ou écrire n'importe quoi. Le service devra donc vérifier la réponse (longueur d'un SMS, pas de date de livraison promise) et revenir au gabarit en cas de problème.
- **Le minimum de données.** On n'envoie au LLM que ce qui sert au texte (le numéro du colis, l'entrepôt), jamais un nom ni une adresse : c'est le principe de minimisation du RGPD, détaillé au jour 5.

{#quiz}
## Quiz

```quiz
- q: Le choix du modèle dépend de l'entrepôt du colis. Quelle architecture convient ?
  options:
    - La répartition du trafic par la plateforme, en pourcentages
    - Un modèle composite qui route chaque colis selon son entrepôt
    - Un seul modèle pour tous
    - Un serveur multi-modèles à chargement dynamique
  answer: 1
  explain: La répartition par pourcentages tire au hasard ; seul un composant qui lit la requête peut router selon son contenu.
- q: Dans Azure Machine Learning, que reçoit le client quand 10 % du trafic est copié vers un déploiement en ombre (mirror_traffic) ?
  options:
    - La réponse du déploiement en ombre pour 10 % des requêtes
    - Toujours la réponse du déploiement principal
    - Les deux réponses
    - Une erreur
  answer: 1
  explain: L'ombre ne change pas ce que reçoit le client ; elle sert à mesurer le nouveau déploiement sans risque.
- q: Quand la méthode load_context d'un modèle PyFunc est-elle appelée ?
  options:
    - À chaque requête
    - Une fois, au chargement du modèle
    - À l'enregistrement seulement
    - Jamais, c'est facultatif
  answer: 1
  explain: On y charge ce qui coûte cher (les modèles) ; predict, appelée à chaque requête, doit rester rapide.
- q: Quel est l'inconvénient principal d'un modèle composite qui contient deux modèles ?
  options:
    - Il ne peut pas être servi par MLflow
    - Les deux modèles sont livrés ensemble, et la mémoire est la somme des deux
    - Il ne peut pas avoir de signature
    - Il est forcément plus lent qu'un seul modèle
  answer: 1
  explain: C'est le prix de la souplesse - une seule unité de déploiement, donc une seule unité de dimensionnement.
- q: Pourquoi le rédacteur de SMS a-t-il le même contrat qu'un futur rédacteur à base de LLM ?
  options:
    - Pour pouvoir remplacer l'un par l'autre sans toucher au reste du service
    - Parce que MLflow l'exige
    - Pour que le gabarit soit plus rapide
    - Pour éviter la signature
  answer: 0
  explain: Un contrat stable isole le changement ; le service, ses tests et ses clients ne bougent pas.
```
