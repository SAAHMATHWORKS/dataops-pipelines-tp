---
subtitle: >-
  On assemble le service de ColisVert : un seul modèle MLflow, défini par le code, qui contient la
  régression logistique et la forêt compacte du TP 1. Le champion répond, la forêt prédit en ombre
  et écrit au journal, un rédacteur prépare le SMS. On l'enregistre, on le teste dans le notebook,
  on le fait tourner en ombre sur tout décembre, puis on le sert en HTTP avec des paramètres de
  requête.
objectives:
  - Lire un modèle PyFunc défini par le code - load_context, predict, artefacts, configuration
  - Écrire une signature avec des paramètres de requête et enregistrer le service dans le registre
  - Appeler le service avec et sans paramètres, dans le notebook puis en HTTP
  - Exploiter le journal d'un déploiement en ombre pour décider d'une promotion
  - Reconnaître les erreurs de validation renvoyées par le service
---

{#etape1}
## Étape 1 : lire le service

:::: lab Étape 1 | Le fichier du service | 8 min
Ouvrez `service/colisvert_service.py` dans JupyterLab. Le voici en entier :

```python title="service/colisvert_service.py (à lire, ne pas exécuter)"
"""Le service de prédiction de ColisVert : plusieurs modèles derrière un seul point d'accès.

Ce fichier est un modèle MLflow « défini par le code » (models from code) : MLflow enregistre
le fichier lui-même, pas un objet Python sérialisé. Les modèles qu'il combine sont des
« artefacts » du modèle, résolus à l'enregistrement (par exemple models:/colisvert-empreinte@leger)
et copiés avec lui.

Chaque requête reçoit des colis (id_colis + les 8 variables) et, en option, trois paramètres :
- modele  : le modèle qui répond (par défaut "champion") ;
- ombre   : si vrai, les autres modèles prédisent aussi, et leurs réponses vont au journal,
            jamais au client (déploiement en ombre) ;
- message : si vrai, un rédacteur prépare le texte du SMS pour les colis à risque.
"""

from __future__ import annotations

import json
from pathlib import Path

import mlflow
import pandas as pd
from mlflow.models import set_model
from mlflow.pyfunc import PythonModel

VARIABLES = ["entrepot", "client", "creneau", "meteo", "jour_semaine", "distance_km", "poids_kg", "delai_promis_h"]
PARAMETRES = {"modele": "champion", "ombre": True, "message": False}


class RedacteurGabarit:
    """Rédige le SMS d'un colis à risque à partir d'un gabarit.

    Même contrat qu'un rédacteur à base de LLM (jour 5) : un colis et sa probabilité en entrée,
    un texte en sortie. On peut donc remplacer l'un par l'autre sans toucher au service.
    """

    @mlflow.trace(span_type="TOOL")
    def rediger(self, colis: dict, probabilite: float) -> str:
        return (f"ColisVert : votre colis {colis['id_colis']} risque d'arriver en retard. "
                f"Nous suivons sa livraison depuis {colis['entrepot']} et vous tenons informé.")


class ServiceColisVert(PythonModel):
    def load_context(self, context):
        # Chaque artefact est un modèle MLflow (un dossier) : on le charge une fois, au démarrage.
        self.modeles = {nom: mlflow.sklearn.load_model(chemin) for nom, chemin in context.artifacts.items()}
        self.seuil = float(context.model_config["seuil"])
        self.journal = Path(context.model_config["journal"])
        self.redacteur = RedacteurGabarit()

    def predict(self, context, model_input: pd.DataFrame, params: dict | None = None) -> pd.DataFrame:
        params = {**PARAMETRES, **(params or {})}
        nom = params["modele"]
        if nom not in self.modeles:
            raise ValueError(f"modèle inconnu : {nom!r} ; modèles servis : {sorted(self.modeles)}")
        X = model_input[VARIABLES]
        proba = self.modeles[nom].predict_proba(X)[:, 1]
        sortie = pd.DataFrame({
            "id_colis": model_input["id_colis"].to_numpy(),
            "modele": nom,
            "probabilite": proba.round(3),
            "retard": (proba >= self.seuil).astype(int),
        })
        if params["ombre"]:
            self.journaliser_ombre(model_input["id_colis"], nom, proba, X)
        if params["message"]:
            sortie["message"] = [self.redacteur.rediger(colis, p) if p >= self.seuil else ""
                                 for colis, p in zip(model_input.to_dict("records"), proba)]
        else:
            sortie["message"] = ""
        return sortie

    def journaliser_ombre(self, identifiants, nom, proba, X):
        """Les autres modèles prédisent aussi ; leurs réponses vont au journal, pas au client."""
        self.journal.parent.mkdir(parents=True, exist_ok=True)
        with self.journal.open("a", encoding="utf-8") as fichier:
            for autre in sorted(set(self.modeles) - {nom}):
                ombre = self.modeles[autre].predict_proba(X)[:, 1]
                for ident, p_servi, p_ombre in zip(identifiants, proba, ombre):
                    fichier.write(json.dumps({"id_colis": ident, "servi": nom, "p_servi": round(float(p_servi), 3),
                                              "ombre": autre, "p_ombre": round(float(p_ombre), 3)}) + "\n")


set_model(ServiceColisVert())
```

Quatre choses à remarquer :

1. **`load_context` charge chaque modèle une fois.** `context.artifacts` donne le chemin **local** de chaque artefact : MLflow a copié les deux modèles du registre dans le service au moment de l'enregistrement, puis les télécharge avec lui. Le service ne dépend donc plus du registre une fois déployé.
2. **`predict` valide le paramètre `modele`.** Un nom inconnu lève une erreur explicite, avec la liste des modèles servis.
3. **L'ombre ne change pas la réponse.** Les autres modèles prédisent aussi, mais leurs probabilités vont au **journal** (un fichier JSON Lines : une ligne JSON par colis), jamais au client.
4. **La dernière ligne, `set_model(...)`,** désigne l'objet que MLflow doit servir : c'est ce qui fait de ce fichier un modèle « défini par le code ».
::::

{#etape2}
## Étape 2 : la signature et l'enregistrement

:::: lab Étape 2 | Une signature avec paramètres, puis le registre | 8 min
La signature décrit les **colonnes** en entrée (le numéro du colis et ses 8 variables), les colonnes en **sortie**, et les **paramètres** avec leur valeur par défaut. `infer_signature` la déduit d'un exemple de chaque :

```python title="Cellule 11 : la signature du service"
from mlflow.models import infer_signature

entree = decembre.head(5)[["id_colis"] + X_COLS]
exemple_sortie = pd.DataFrame({"id_colis": ["DEC00001"], "modele": ["champion"], "probabilite": [0.5],
                               "retard": [1], "message": [""]})
signature = infer_signature(entree, exemple_sortie,
                            params={"modele": "champion", "ombre": True, "message": False})
print(signature)
```

```plaintext title="Sortie attendue"
inputs:
  ['id_colis': string (required), 'entrepot': string (required), 'client': string (required), 'creneau': string (required), 'meteo': string (required), 'jour_semaine': string (required), 'distance_km': long (required), 'poids_kg': double (required), 'delai_promis_h': long (required)]
outputs:
  ['id_colis': string (required), 'modele': string (required), 'probabilite': double (required), 'retard': long (required), 'message': string (required)]
params:
  ['modele': string (default: champion), 'ombre': boolean (default: True), 'message': boolean (default: False)]
```

Sous la cellule, MLflow affiche un avertissement (`Hint: Inferred schema contains integer column(s)…`) : les colonnes entières ne peuvent pas contenir de valeur manquante. Ici, la distance et le délai promis sont toujours renseignés ; on peut l'ignorer.

On enregistre maintenant le service. Trois arguments font tout le travail :

- `python_model` : le **chemin** du fichier (modèle défini par le code) ;
- `artifacts` : les deux modèles du registre, désignés **par leur alias** ;
- `model_config` : le seuil de décision de ce matin (0,40) et le chemin du journal de l'ombre.

```python title="Cellule 12 : enregistrer le service"
with mlflow.start_run(run_name="service-colisvert"):
    info = mlflow.pyfunc.log_model(
        name="service",
        python_model=str(RACINE / "service" / "colisvert_service.py"),
        artifacts={"champion": "models:/colisvert-empreinte@leger",
                   "challenger": "models:/colisvert-empreinte@foret"},
        model_config={"seuil": 0.4, "journal": str(RACINE / "journal" / "ombre.jsonl")},
        signature=signature,
        input_example=entree,
        registered_model_name="colisvert-service",
    )
client.set_registered_model_alias("colisvert-service", "production", info.registered_model_version)
print(f"colisvert-service, version {info.registered_model_version}, alias production")
```

```plaintext title="Sortie attendue"
colisvert-service, version 1, alias production
```

**Vérification dans l'interface** (http://localhost:5000, **Models › colisvert-service**) : la version 1 porte l'alias `production`. Dans ses fichiers, on retrouve `colisvert_service.py` tel quel, et un dossier `artifacts` qui contient les **deux** modèles.

::: hint
`FileNotFoundError` sur `colisvert_service.py` : la Cellule 0 n'a pas été exécutée (`RACINE` manque), ou le `git pull` de la mise en place n'a pas été fait. `RESOURCE_DOES_NOT_EXIST` sur `colisvert-empreinte@foret` : l'alias n'existe pas ; relancez la Cellule 10 du TP 1.
:::
::::

{#etape3}
## Étape 3 : le service dans le notebook

:::: lab Étape 3 | Avec et sans paramètres | 6 min
On charge le service **par son alias**, comme le fera la mise en production, et on lui donne les 5 premiers colis de décembre :

```python title="Cellule 13 : les valeurs par défaut"
service = mlflow.pyfunc.load_model("models:/colisvert-service@production")
print(service.predict(entree).to_string(index=False))
```

```plaintext title="Sortie attendue"
id_colis   modele  probabilite  retard message
DEC00001 champion        0.910       1
DEC00002 champion        0.995       1
DEC00003 champion        0.945       1
DEC00004 champion        0.071       0
DEC00005 champion        0.013       0
```

Sans paramètre, c'est le **champion** (la régression logistique) qui répond, et la colonne `message` reste vide. Demandons maintenant le challenger **et** les messages :

```python title="Cellule 14 : le challenger, avec le texte des SMS"
reponse = service.predict(entree, params={"modele": "challenger", "message": True})
print(reponse[["id_colis", "modele", "probabilite", "retard"]].to_string(index=False))
print(reponse.loc[0, "message"])
```

```plaintext title="Sortie attendue"
id_colis     modele  probabilite  retard
DEC00001 challenger        0.843       1
DEC00002 challenger        0.935       1
DEC00003 challenger        0.925       1
DEC00004 challenger        0.104       0
DEC00005 challenger        0.011       0
ColisVert : votre colis DEC00001 risque d'arriver en retard. Nous suivons sa livraison depuis Lille et vous tenons informé.
```

La forêt donne d'autres probabilités que la régression logistique (0,843 contre 0,910 pour le premier colis), mais ici les mêmes décisions. Les trois colis à risque (probabilité ≥ 0,40) reçoivent un texte ; les deux autres ont un message vide. Le paramètre `message` a coûté trois appels au rédacteur, pas cinq.
::::

{#etape4}
## Étape 4 : un mois en ombre

Le vrai travail de l'ombre se fait sur la durée. On donne au service **tous les colis de décembre** (3 426) : le champion répond, la forêt prédit en silence et écrit au journal.

:::: lab Étape 4 | Le journal de l'ombre | 10 min
```python title="Cellule 15 : décembre, champion servi, challenger en ombre"
journal = RACINE / "journal" / "ombre.jsonl"
journal.unlink(missing_ok=True)                 # on repart d'un journal vide
lot = service.predict(decembre[["id_colis"] + X_COLS])
ombre = pd.read_json(journal, lines=True)
ombre["alerte_servi"] = (ombre["p_servi"] >= 0.4).astype(int)
ombre["alerte_ombre"] = (ombre["p_ombre"] >= 0.4).astype(int)
print(f"{len(lot)} colis servis par le {lot['modele'].iloc[0]}, {len(ombre)} lignes au journal")
print(f"alertes : champion {ombre['alerte_servi'].mean():.1%}, challenger {ombre['alerte_ombre'].mean():.1%}")
print(f"même décision pour {(ombre['alerte_servi'] == ombre['alerte_ombre']).mean():.1%} des colis")
```

```plaintext title="Sortie attendue"
3426 colis servis par le champion, 3426 lignes au journal
alertes : champion 41.9%, challenger 41.0%
même décision pour 93.1% des colis
```

- **Une ligne au journal par colis** : la forêt a prédit en silence pour les 3 426 colis, et aucun client n'a reçu sa réponse.
- **Des taux d'alertes proches** : 41,9 % pour le champion, 41,0 % pour la forêt. Les deux sont élevés : décembre compte plus de retards (23,9 %, vu ce matin), et le seuil de 0,40 alerte plus tôt que le seuil par défaut de 0,5.
- **Mais 6,9 % des colis, près de 240, recevraient une décision différente.** Des taux proches ne veulent pas dire des modèles équivalents : ce ne sont pas les mêmes colis qui sont signalés. Seule la vérité dira qui a raison.

Fin décembre, les vrais délais sont connus. On peut enfin **comparer** les deux modèles sur les mêmes colis, sans qu'aucun client n'ait été exposé au challenger :

```python title="Cellule 16 : la vérité de décembre"
verite = ombre.merge(decembre[["id_colis", "entrepot", CIBLE]], on="id_colis")
for nom, colonne in [("champion, servi", "alerte_servi"), ("challenger, en ombre", "alerte_ombre")]:
    print(f"{nom:<21} précision {precision_score(verite[CIBLE], verite[colonne]):.3f}  "
          f"rappel {recall_score(verite[CIBLE], verite[colonne]):.3f}  "
          f"F1 {f1_score(verite[CIBLE], verite[colonne]):.3f}")
```

```plaintext title="Sortie attendue"
champion, servi       précision 0.560  rappel 0.982  F1 0.713
challenger, en ombre  précision 0.551  rappel 0.945  F1 0.696
```

**Le champion fait mieux sur les trois mesures** : F1 0,713 contre 0,696, et surtout un rappel de 0,982 contre 0,945. Avec la règle de promotion du jour 2 (au moins 0,01 de mieux), la forêt **n'est pas promue**. L'ombre a fait son travail : on a testé un autre modèle sur un mois réel, sans qu'un seul client en subisse les erreurs.

Une explication possible, à vérifier : en décembre, les colis sont plus lourds (jusqu'à 38 kg, contre 30 kg au plus dans le train). Un arbre ne sait pas extrapoler : il traite un colis de 38 kg comme un colis de 30 kg, celui de la dernière feuille connue. La régression logistique, elle, prolonge sa pente.
::::

{#etape5}
## Étape 5 : le service en HTTP

:::: lab Étape 5 | Servir, interroger, provoquer des erreurs | 8 min
**1. Démarrez le service** dans un **deuxième** terminal de JupyterLab, comme au jour 2 (si le service du champion du jour 2 tourne encore, arrêtez-le d'abord avec **Ctrl + C**) :

```bash title="Terminal JupyterLab n° 2"
cd /home/lab/projet
mlflow models serve -m "models:/colisvert-service@production" -p 5001 --env-manager local
```

**Vérification :** la dernière ligne est `INFO:     Uvicorn running on http://127.0.0.1:5001 (Press CTRL+C to quit)`.

**2. Interrogez-le.** Les paramètres voyagent à côté des données, sous la clé `params` :

```python title="Cellule 17 : une requête HTTP avec paramètres"
import json

import requests

ADRESSE = "http://127.0.0.1:5001/invocations"


def appeler(colis, params=None):
    corps = {"dataframe_split": json.loads(colis.to_json(orient="split", index=False))}
    if params is not None:
        corps["params"] = params
    return requests.post(ADRESSE, json=corps, timeout=30)


reponse = appeler(entree.head(2), {"modele": "challenger", "message": True})
print(reponse.status_code)
for prediction in reponse.json()["predictions"]:
    print(prediction["id_colis"], prediction["modele"], prediction["probabilite"], prediction["message"][:60])
```

```plaintext title="Sortie attendue"
200
DEC00001 challenger 0.843 ColisVert : votre colis DEC00001 risque d'arriver en retard.
DEC00002 challenger 0.935 ColisVert : votre colis DEC00002 risque d'arriver en retard.
```

**3. Provoquez trois erreurs**, pour savoir les reconnaître quand elles viendront d'un vrai client :

```python title="Cellule 18 : ce que le service refuse"
essais = {
    "colonne manquante": appeler(entree.head(2).drop(columns=["poids_kg"])),
    "paramètre mal typé": appeler(entree.head(2), {"ombre": "oui"}),
    "modèle inconnu": appeler(entree.head(2), {"modele": "lille"}),
}
for nom, reponse in essais.items():
    print(f"{nom:<19} HTTP {reponse.status_code}  {reponse.json()['error_code']}")
```

```plaintext title="Sortie attendue"
colonne manquante   HTTP 400  INVALID_PARAMETER_VALUE
paramètre mal typé  HTTP 400  INVALID_PARAMETER_VALUE
modèle inconnu      HTTP 400  BAD_REQUEST
```

- **Les erreurs de schéma et de type** sont attrapées par MLflow **avant** le modèle, grâce à la signature, avec le code `INVALID_PARAMETER_VALUE` et un message qui nomme la colonne ou le paramètre fautif.
- **L'erreur levée dans `predict`** (modèle inconnu) revient avec un code générique, `BAD_REQUEST`, et un message vague (`Encountered an unexpected error while evaluating the model`). Notre message explicite n'est que dans la **pile d'appels** jointe à la réponse.
- **Attention à cette pile d'appels.** Elle révèle des chemins de fichiers et du code interne : très utile pour déboguer, à ne jamais renvoyer tel quel à un client externe. En production, une passerelle filtre les erreurs, et le service les journalise.
- Un paramètre **inconnu** (`{"inconnu": 1}`) n'est pas refusé : il est ignoré, avec un avertissement dans le terminal du service.

**4. Arrêtez le service** : dans le terminal n° 2, **Ctrl + C**.

::: hint
`ConnectionError` : le service n'a pas fini de démarrer (attendez la ligne `Uvicorn running`), ou il a été arrêté. `Address already in use` au démarrage : un autre service occupe déjà le port 5001 (celui du jour 2) ; arrêtez-le, ou choisissez `-p 5002` et changez `ADRESSE`.
:::
::::

{#etape6}
## Étape 6 : les traces du rédacteur

:::: lab Étape 6 | Ce qu'a écrit le rédacteur | 3 min
Chaque appel au rédacteur a été **tracé** (décorateur `@mlflow.trace`). Les traces de la Cellule 14 sont dans l'expérience active, `j4-empreinte` :

```python title="Cellule 19 : les traces"
experience = mlflow.get_experiment_by_name("j4-empreinte")
traces = mlflow.search_traces(locations=[experience.experiment_id])
print(f"{len(traces)} traces")
```

```plaintext title="Sortie attendue"
3 traces
```

Dans l'interface, l'onglet **Traces** de l'expérience `j4-empreinte` montre chaque appel : le colis reçu, la probabilité, le texte produit et la durée. Au jour 5, quand un LLM remplacera le gabarit, c'est là qu'on relira ce qu'il a écrit.
::::

{#avance}
## Pour aller plus loin : de ce service à la production

Ce bloc est pour les profils avancés ; rien ici n'est exigé dans l'évaluation.

- **Le journal.** Un fichier local suffit pour un TP. En production, le journal de l'ombre va dans une table (Delta Lake, jour 5) ou un flux d'événements, avec l'horodatage et la version du service. On le rapproche ensuite des vrais délais, comme à la Cellule 16, chaque semaine.
- **Le coût de l'ombre.** Chaque requête fait travailler les deux modèles : le processeur double, et le temps de réponse aussi si l'ombre est calculée avant de répondre. On peut ne mettre en ombre qu'une partie des requêtes (comme `mirror_traffic` d'Azure, plafonné à 50 %), ou calculer l'ombre après la réponse, dans une file d'attente.
- **Le canari après l'ombre.** Le service sait déjà servir le challenger à la demande (`modele="challenger"`). Un canari, c'est une règle qui envoie 5 % des colis au challenger, par exemple selon un hachage du numéro de colis : le même colis tombe toujours du même côté.
- **Plusieurs versions d'un même service.** Le service est versionné dans le registre comme n'importe quel modèle. Changer le seuil, ajouter un modèle ou passer au LLM, c'est une nouvelle version, avec un retour arrière possible en déplaçant l'alias `production`.

{#quiz}
## Quiz

```quiz
- q: Où le service trouve-t-il les deux modèles une fois déployé ?
  options:
    - Il les télécharge du registre à chaque requête
    - Dans ses propres artefacts, copiés à l'enregistrement et chargés une fois par load_context
    - Dans le dossier models/ du dépôt
    - Il les réentraîne au démarrage
  answer: 1
  explain: Les alias ont été résolus à l'enregistrement ; le service est autonome, et déplacer l'alias leger ne change pas une version déjà enregistrée.
- q: Que reçoit le client quand le champion répond et que le challenger est en ombre ?
  options:
    - Les deux probabilités
    - La réponse du champion seulement ; celle du challenger va au journal
    - La moyenne des deux
    - La réponse du challenger
  answer: 1
  explain: L'ombre mesure sans exposer ; c'est le principe vu au jour 2, et celui de mirror_traffic dans Azure.
- q: Un client envoie "ombre" égal au texte "oui". Que se passe-t-il ?
  options:
    - Le service considère que c'est vrai
    - MLflow refuse la requête (HTTP 400) car le paramètre ne respecte pas le type booléen de la signature
    - Le paramètre est ignoré
    - Le service plante
  answer: 1
  explain: La signature valide les paramètres comme les données ; seul un paramètre inconnu est ignoré, avec un avertissement.
- q: Pourquoi enregistrer le service avec python_model égal au chemin du fichier plutôt qu'avec un objet Python ?
  options:
    - C'est plus rapide à exécuter
    - MLflow garde le code lisible et versionné, et évite pickle et ses risques de sécurité
    - Parce que les objets Python ne peuvent pas avoir de signature
    - Pour pouvoir le servir sans MLflow
  answer: 1
  explain: C'est un modèle « défini par le code » ; on peut le relire et le comparer d'une version à l'autre.
```
