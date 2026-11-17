---
subtitle: >-
  Un run garde la trace d'une expérience. Le registre garde les modèles qui comptent : chacun a un
  nom, des versions numérotées, et des alias qui disent lequel est en service. Changer de modèle en
  production revient alors à déplacer une étiquette.
objectives:
  - Enregistrer un modèle dans le registre et obtenir une version numérotée
  - Poser et déplacer des alias (champion, challenger) sur les versions
  - Charger un modèle par son alias, sans connaître son numéro de version
  - Expliquer pourquoi les alias ont remplacé les anciennes « étapes » Staging et Production
---

{#pourquoi}
## Pourquoi un registre ?

**Le problème.** L'expérience `colisvert-retards` contient déjà plusieurs runs, et chacun a son modèle. Lequel tourne en production ? Lequel est le prochain candidat ? Si la réponse est « celui du run `3f9a…` », personne ne la retiendra, et le code de production devra changer à chaque nouveau modèle.

**L'analogie de l'équipe de sport.** Un club a un effectif : chaque joueur a un numéro. Le jour du match, l'entraîneur désigne le **titulaire** et le **remplaçant**. Le titulaire peut changer d'un match à l'autre, mais le rôle « titulaire » existe toujours : le reste de l'équipe joue avec « le titulaire », quel qu'il soit.

Le **registre des modèles** de MLflow fonctionne ainsi :

| Concept | Ce que c'est | Chez ColisVert |
|---|---|---|
| **Modèle enregistré** (*registered model*) | Un nom stable, qui regroupe toutes les versions d'un même modèle métier | `colisvert-retards` |
| **Version** | Un modèle précis, issu d'un run, numéroté automatiquement : 1, 2, 3… | version 1 : le modèle du matin |
| **Alias** | Une étiquette mobile posée sur une version | `champion` : celle qui est en service |
| **Tag** | Une information libre sur une version | `validation = critere atteint` |

Le code de production charge **toujours** `models:/colisvert-retards@champion`. Pour mettre un nouveau modèle en service, on déplace l'alias `champion` ; pour revenir en arrière, on le remet sur l'ancienne version. Le code ne change jamais.

::: callout info Et les étapes Staging et Production ?
Les anciennes versions de MLflow rangeaient chaque version dans une **étape** fixe (`Staging`, `Production`, `Archived`). La documentation de MLflow indique que ces étapes sont **dépréciées** et seront retirées dans une future version majeure : on utilise désormais les **alias** (aussi nombreux et nommés qu'on veut) et les **tags**. Si vous croisez `transition_model_version_stage` dans un vieux tutoriel, c'est l'ancienne méthode.
:::

{#enregistrer}
## Enregistrer les deux candidats

:::: lab Démo | Le champion du matin et le challenger du projet | 10 min
**1. Retrouver un run.** Une petite fonction renvoie le run le plus récent qui correspond à un filtre, dans l'expérience `colisvert-retards`. Puis on enregistre le modèle du run du pipeline v1 (`C` = `1.0`, `class_weight` = `None`) sous le nom `colisvert-retards`, et on lui pose l'alias `champion` : c'est le modèle « en service » de référence.

```python title="Cellule 2 : la version 1, champion"
import mlflow
from mlflow import MlflowClient

client = MlflowClient()
NOM = "colisvert-retards"


def dernier_run(filtre):
    """Le run le plus récent de l'expérience colisvert-retards qui correspond au filtre."""
    runs = mlflow.search_runs(experiment_names=["colisvert-retards"], filter_string=filtre,
                              order_by=["attributes.start_time DESC"], max_results=1)
    return runs.iloc[0]


run_v1 = dernier_run("params.C = '1.0' and params.class_weight = 'None'")
version_1 = mlflow.register_model(f"runs:/{run_v1.run_id}/model", NOM)
client.set_registered_model_alias(NOM, "champion", version_1.version)
print(f"version {version_1.version} enregistrée, alias champion")
```

```plaintext title="Sortie attendue"
version 1 enregistrée, alias champion
```

L'adresse `runs:/<id du run>/model` désigne le modèle nommé `model` dans ce run. Sous la cellule, MLflow affiche aussi ses propres messages (en rouge : ils passent par la sortie d'erreur, mais ce ne sont pas des erreurs) :

- `Successfully registered model 'colisvert-retards'.` : le nom est créé dans le registre ;
- un avertissement `Run with id … has no artifacts at artifact path 'model', registering model based on models:/m-… instead` : depuis MLflow 3, le modèle n'est plus rangé **dans** le run mais à part, comme un objet à part entière (le *LoggedModel* vu ce matin, d'identifiant `m-…`). MLflow le retrouve à partir du run et le dit ;
- `Created version '1' of model 'colisvert-retards'.` : la version 1 existe.

**2. Le challenger.** Le run du projet MLflow (`C` = `0.1`, `class_weight` = `balanced`) devient la version 2, avec l'alias `challenger`. Cette fois, MLflow annonce `Registered model 'colisvert-retards' already exists. Creating a new version of this model...` :

```python title="Cellule 3 : la version 2, challenger"
run_v2 = dernier_run("params.C = '0.1' and params.class_weight = 'balanced'")
version_2 = mlflow.register_model(f"runs:/{run_v2.run_id}/model", NOM)
client.set_registered_model_alias(NOM, "challenger", version_2.version)
print(f"version {version_2.version} enregistrée, alias challenger")
```

```plaintext title="Sortie attendue"
version 2 enregistrée, alias challenger
```

**3. Comparer les deux rôles.** `get_model_version_by_alias` renvoie la version qui porte un alias ; son attribut `run_id` mène au run, donc aux métriques.

```python title="Cellule 4 : champion contre challenger"
for alias in ["champion", "challenger"]:
    version = client.get_model_version_by_alias(NOM, alias)
    m = client.get_run(version.run_id).data.metrics
    print(f"{alias:<10} v{version.version} : rappel {m['rappel']}, précision {m['precision']}, f1 {m['f1']}")
```

```plaintext title="Sortie attendue"
champion   v1 : rappel 0.591, précision 0.745, f1 0.66
challenger v2 : rappel 0.88, précision 0.561, f1 0.685
```

**Vérification :** dans l'interface de MLflow, l'onglet **Models** montre `colisvert-retards` avec deux versions et leurs alias. Chaque version mène au run qui l'a produite : c'est la traçabilité du registre.

::: hint
`IndexError: single positional indexer is out-of-bounds` dans `dernier_run` : aucun run ne correspond au filtre. Pour la version 1, il faut le run du pipeline du matin (`dvc repro`) ; pour la version 2, celui du projet MLflow de la notion précédente. Exécuter une cellule deux fois crée une version de plus (3, 4…) : ce n'est pas grave, l'alias désigne toujours la dernière enregistrée par la cellule.
:::
::::

{#decider}
## Décider, puis promouvoir

**La règle de décision s'écrit avant de regarder les chiffres**, comme le critère de succès de la charte. Pour ColisVert :

> Un challenger remplace le champion s'il **atteint le critère de succès** (rappel ≥ 0,80 et précision ≥ 0,50) et si son **F1 dépasse celui du champion d'au moins 0,01**.

La marge de 0,01 évite de changer de modèle pour une différence qui relève du hasard de l'échantillon de test. Ici : le challenger atteint le critère (0,880 et 0,561), le champion non (0,591), et le F1 progresse de 0,025. **Le challenger est promu.**

:::: lab Démo | Déplacer l'alias champion | 5 min
```python title="Cellule 5 : promouvoir la version 2"
client.set_registered_model_alias(NOM, "champion", version_2.version)
client.set_registered_model_alias(NOM, "precedent", version_1.version)
client.delete_registered_model_alias(NOM, "challenger")
client.set_model_version_tag(NOM, version_2.version, "validation", "critere atteint")

# search_model_versions liste les versions, mais sans leurs alias : on relit chacune.
numeros = sorted(int(v.version) for v in client.search_model_versions(f"name = '{NOM}'"))
for numero in numeros:
    version = client.get_model_version(NOM, str(numero))
    print(f"v{version.version} : alias {sorted(version.aliases)}, tags {version.tags}")
```

```plaintext title="Sortie attendue"
v1 : alias ['precedent'], tags {}
v2 : alias ['champion'], tags {'validation': 'critere atteint'}
```

Un alias ne peut désigner qu'**une seule** version à la fois : poser `champion` sur la version 2 l'a retiré de la version 1. L'alias `precedent` garde la trace de l'ancien champion : en cas de problème, le **retour arrière** tient en une ligne, `set_registered_model_alias(NOM, "champion", "1")`.
::::

{#charger}
## Charger un modèle par son alias

:::: lab Démo | Le code de production ne connaît que l'alias | 5 min
`mlflow.pyfunc.load_model` charge n'importe quel modèle MLflow sous une interface commune, `predict`, quelle que soit la bibliothèque qui l'a produit. On l'essaie sur les **cinq premiers colis de décembre**, que le modèle n'a jamais vus. La fonction `generer_livraisons_decembre` du dépôt produit les colis de décembre de ColisVert.

```python title="Cellule 6 : prédire avec le champion"
from colisvert.donnees import generer_livraisons_decembre

decembre = ajouter_jour_semaine(pd.DataFrame(generer_livraisons_decembre()))
champion = mlflow.pyfunc.load_model(f"models:/{NOM}@champion")

colis = decembre.head(5)
print(colis[["id_colis", "entrepot", "distance_km", "poids_kg", "meteo"]].to_string(index=False))
print("prédiction :", champion.predict(colis[X_COLS]).tolist())
print("réalité    :", colis[CIBLE].tolist())
```

```plaintext title="Sortie attendue"
id_colis entrepot  distance_km  poids_kg meteo
DEC00001    Lille           19       9.7 pluie
DEC00002    Lille          150      23.4 pluie
DEC00003     Lyon           80      24.1 pluie
DEC00004    Lille          251      22.5   sec
DEC00005     Lyon          181       9.1 pluie
prédiction : [1, 1, 1, 0, 0]
réalité    : [0, 1, 1, 0, 0]
```

Quatre bonnes réponses sur cinq. Le colis `DEC00001` est une **fausse alerte** : Lille et la pluie poussent le score vers le retard, mais la distance est courte (19 km) et le colis est arrivé à l'heure. C'est le prix d'un rappel élevé, accepté par la charte.
::::

{#avance}
## Pour aller plus loin : le registre comme point de contrôle

Ce bloc est pour les profils avancés ; rien ici n'est exigé dans l'évaluation.

**Plusieurs environnements, un seul registre ?** Deux écoles. Avec **un registre unique**, on distingue les environnements par des alias (`champion-recette`, `champion-production`) ou par des noms (`colisvert-retards-dev`, `colisvert-retards-prod`). Avec **un registre par environnement**, on **copie** une version validée du registre de développement vers celui de production (`copy_model_version` dans MLflow). La seconde école sépare mieux les droits : en production, seule la chaîne de déploiement peut écrire. C'est l'approche des registres d'Azure Machine Learning partagés entre espaces de travail, et du catalogue Unity Catalog de Databricks.

**Qui a le droit de déplacer `champion` ?** Le geste est simple, donc dangereux. En entreprise, on le réserve à la chaîne de CI/CD (niveau 2 de ce matin), qui ne le fait qu'après des contrôles automatiques : critère de succès, marge sur le champion, tests de non-régression sur des cas métier connus, et parfois une validation humaine tracée.

**Ce que le registre garantit, et ce qu'il ne garantit pas.** Il garantit qu'une version désigne un modèle **immuable** et son run d'origine. Il ne garantit pas que les bibliothèques de la machine qui le charge sont les bonnes : c'est le rôle des fichiers d'environnement que MLflow enregistre **avec** le modèle (`requirements.txt`, `python_env.yaml`, dans les artefacts du modèle). Un modèle scikit-learn chargé avec une version très différente de scikit-learn peut échouer, ou pire, prédire autrement sans erreur.

**La marge de promotion, plus rigoureusement.** 0,01 de F1 est une règle simple. Plus rigoureux : estimer l'incertitude du F1 par **bootstrap** (rééchantillonner le jeu de test un millier de fois et observer la dispersion du F1), et ne promouvoir que si l'écart dépasse cette dispersion. Sur les 1 230 colis du test, dont 208 en retard, l'écart-type du F1 estimé par bootstrap est d'environ 0,02 : une différence de 0,008 ne prouve rien.

{#quiz}
## Quiz de validation

```quiz
- q: Que charge le code de production avec l'adresse models:/colisvert-retards@champion ?
  options:
    - Toujours la version 1
    - La version qui porte l'alias champion au moment du chargement
    - La dernière version enregistrée, quelle qu'elle soit
    - Le modèle du dernier run de l'expérience
  answer: 1
  explain: Déplacer l'alias suffit à changer le modèle en service, sans toucher au code.
- q: On pose l'alias champion sur la version 2 alors qu'il était sur la version 1. Que devient la version 1 ?
  options:
    - Elle est supprimée
    - Elle perd l'alias champion, mais reste dans le registre
    - Elle garde aussi l'alias champion
    - Elle devient automatiquement challenger
  answer: 1
  explain: Un alias ne désigne qu'une version à la fois. La version 1 reste disponible pour un retour arrière.
- q: Pourquoi la règle de promotion exige-t-elle une marge minimale sur le F1 ?
  options:
    - Pour ralentir les data scientists
    - Pour ne pas changer de modèle sur une différence due au hasard de l'échantillon de test
    - Parce que MLflow refuse les petites différences
    - Pour économiser de l'espace disque
  answer: 1
  explain: Une très petite différence sur 1 230 colis peut s'inverser sur la semaine suivante.
- q: Que remplacent les alias dans MLflow ?
  options:
    - Les runs
    - Les anciennes étapes Staging et Production, dépréciées
    - Les expériences
    - Les tags
  answer: 1
  explain: Les alias sont plus souples - autant qu'on veut, nommés librement.
```
