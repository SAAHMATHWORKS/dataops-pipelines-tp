---
subtitle: >-
  Vous transformez les trois scripts du dépôt en un vrai pipeline : DVC sait dans quel ordre les
  lancer et ce qu'il faut relancer quand quelque chose change, MLflow garde la trace de chaque
  exécution, Git versionne le tout. À la fin, vous prouvez d'où vient votre modèle.
objectives:
  - Externaliser les réglages dans params.yaml
  - Décrire un pipeline en trois étapes dans dvc.yaml et l'exécuter avec dvc repro
  - Retrouver dans MLflow les paramètres, les métriques, le modèle et l'origine de chaque entraînement
  - Versionner le pipeline et ses résultats avec Git et DVC, et vérifier qu'une exécution est reproductible
---

{#principe}
## Le principe

**Pourquoi DVC pour le pipeline ?** Hier, DVC versionnait **un fichier**. Il sait aussi décrire **une chaîne d'étapes** : pour chaque étape, la commande à lancer, ce dont elle dépend (fichiers, code, paramètres) et ce qu'elle produit. Avec cette description, la commande `dvc repro` relance **uniquement** les étapes dont une dépendance a changé, comme `make` pour les développeurs. Et chaque exécution laisse un fichier `dvc.lock` : l'empreinte de chaque entrée et de chaque sortie. C'est le ticket de vestiaire du pipeline entier.

**Et MLflow ?** Les scripts du dépôt appellent `pipeline/suivi.py` : chaque entraînement ouvre un run dans l'expérience `colisvert-retards`, avec ses paramètres, ses métriques, le modèle, le commit Git et l'empreinte des données.

| Outil | Il répond à la question |
|---|---|
| **Git** | Quel code, et quels réglages ? |
| **DVC** | Quelles données, et que faut-il relancer ? |
| **MLflow** | Quels résultats, et quel modèle ? |

Tout se passe dans un **terminal de JupyterLab**, dans `/home/lab/projet`, sur votre branche `tp-dvc`.

{#etape1}
## Étape 1 : repartir de la bonne version des données

:::: lab Étape 1 | Les 8 semaines de livraisons | 5 min
Hier, vous avez fini le TP sur la **version 2** des données (9 semaines). Le modèle de ColisVert, lui, se construit sur les **8 semaines** de référence : la Cellule 2 de ce matin a justement réécrit `data/livraisons.csv` dans cette version. Vérifiez-le, puis demandez à DVC ce qu'il en pense :

```bash title="Terminal JupyterLab"
cd /home/lab/projet
md5sum data/livraisons.csv
dvc status
```

**Vérification :** l'empreinte est `127f20d4baf2636267145a03529220f1`, celle de la version 1. `dvc status` signale que `data/livraisons.csv` est modifié (`modified`) : son ticket désigne encore la version 2.

Enregistrez ce retour à la version 1. DVC reconnaît l'empreinte, déjà présente dans son cache : il n'a rien à copier.

```bash title="Terminal JupyterLab"
dvc add data/livraisons.csv
git add data/livraisons.csv.dvc
git commit -m "Données : retour aux 8 semaines pour le modèle"
```

::: hint
`dvc status` répond `Data and pipelines are up to date.` et `git commit` répond `nothing to commit` : votre ticket désignait déjà la version 1 (c'est le cas après le rattrapage). Tout va bien, passez à l'étape 2.
:::
::::

{#etape2}
## Étape 2 : les réglages dans params.yaml

:::: lab Étape 2 | Externaliser les paramètres | 5 min
Les scripts lisent leurs réglages dans un fichier `params.yaml`, à la racine du dépôt (voir `charger_params` dans `pipeline/commun.py`). Créez-le. La commande `cat > fichier <<'EOF'` écrit dans le fichier toutes les lignes qui suivent, jusqu'à la ligne `EOF` :

```bash title="Terminal JupyterLab"
cat > params.yaml <<'EOF'
prepare:
  date_coupure: "2026-10-19"

train:
  C: 1.0
  class_weight: null
  max_iter: 1000
EOF
cat params.yaml
```

Trois réglages pour l'entraînement :

- **`C`** règle la **régularisation** de la régression logistique : plus `C` est petit, plus le modèle est contraint à rester simple, ce qui limite le surapprentissage.
- **`class_weight`** : `null` (en Python, `None`) traite tous les colis à égalité ; `balanced` donnera plus de poids aux colis en retard, plus rares. On l'essaiera cet après-midi.
- **`max_iter`** : le nombre maximal d'itérations de l'algorithme d'optimisation.

**Vérification :** `cat params.yaml` affiche les sept lignes, sans erreur d'indentation (deux espaces devant chaque réglage).
::::

{#etape3}
## Étape 3 : décrire le pipeline dans dvc.yaml

:::: lab Étape 3 | Trois étapes, leurs dépendances et leurs sorties | 8 min
```bash title="Terminal JupyterLab"
cat > dvc.yaml <<'EOF'
stages:
  prepare:
    cmd: python -m pipeline.prepare
    deps:
      - data/livraisons.csv
      - pipeline/prepare.py
      - pipeline/commun.py
    params:
      - prepare.date_coupure
    outs:
      - data/prepared

  train:
    cmd: python -m pipeline.train
    deps:
      - data/prepared
      - pipeline/train.py
      - pipeline/commun.py
    params:
      - train.C
      - train.class_weight
      - train.max_iter
    outs:
      - models/modele.joblib

  evaluate:
    cmd: python -m pipeline.evaluate
    deps:
      - models/modele.joblib
      - data/prepared
      - pipeline/evaluate.py
    metrics:
      - metrics.json:
          cache: false
EOF
```

Lisez l'étape `train` comme une phrase : « lance `python -m pipeline.train` ; cette commande **dépend** des données préparées, de deux fichiers de code et de trois paramètres ; elle **produit** le modèle ».

| Mot-clé | Rôle | Conséquence |
|---|---|---|
| `cmd` | La commande de l'étape | Si elle change, l'étape est relancée |
| `deps` | Les fichiers dont elle dépend | Si l'un change (son empreinte), l'étape est relancée |
| `params` | Les clés de `params.yaml` qu'elle utilise | Si l'une change, l'étape est relancée ; changer `train.C` ne relance pas `prepare` |
| `outs` | Ce qu'elle produit | DVC le range dans son cache et l'ajoute au `.gitignore` |
| `metrics` | Un fichier de métriques | `cache: false` : le fichier, petit, est versionné **par Git** pour être comparé facilement |

DVC déduit l'**ordre** tout seul : `train` dépend de `data/prepared`, que produit `prepare`, donc `prepare` passe d'abord.

::: hint
Si vous préférez l'éditeur de JupyterLab : **File › New › Text File**, collez le contenu (sans les lignes `cat` et `EOF`), puis enregistrez sous le nom `dvc.yaml` à la racine du dépôt. Attention aux espaces : YAML refuse les tabulations.
:::
::::

{#etape4}
## Étape 4 : lancer le pipeline

:::: lab Étape 4 | dvc repro | 7 min
```bash title="Terminal JupyterLab"
dvc repro
```

DVC vérifie d'abord le ticket des données (`'data/livraisons.csv.dvc' didn't change, skipping`), puis lance les trois étapes dans l'ordre. Pour chacune, il affiche `Running stage '…'`, la commande, puis ce qu'elle imprime. Les lignes importantes :

```plaintext title="Sortie attendue (extrait)"
train : 3805 colis, du 2026-09-07 au 2026-10-18
test  : 1230 colis, du 2026-10-19 au 2026-11-01
taux de retard train : 17.2% | test : 16.9%
modèle entraîné sur 3805 colis, 21 variables après encodage
F1 sur le train : 0.668
modèle écrit dans models/modele.joblib
évaluation sur 1230 colis de test
exactitude : 0.897
precision  : 0.745
rappel     : 0.591
f1         : 0.660
roc_auc    : 0.949
```

Ce sont exactement les chiffres de la Cellule 4 : le pipeline refait, de façon automatique et traçable, ce que vous avez fait à la main. Les **21 variables après encodage** : 3 numériques standardisées, plus une colonne par valeur des 5 variables catégorielles (4 entrepôts, 2 types de client, 3 créneaux, 2 météos, 7 jours).

Pendant l'étape `train`, MLflow annonce la création de l'expérience `colisvert-retards` et affiche le lien du run, `train-C1.0`. À la fin, DVC écrit `dvc.lock` et vous suggère la commande à lancer : `git add models/.gitignore data/.gitignore dvc.lock`.

Affichez maintenant les métriques suivies par DVC :

```bash title="Terminal JupyterLab"
dvc metrics show
```

**Vérification :** un tableau d'une ligne, `metrics.json`, avec `exactitude 0.897`, `f1 0.66`, `precision 0.745`, `rappel 0.591` et `roc_auc 0.949`. DVC affiche les nombres tels qu'ils sont dans `metrics.json` : `0.66` et non `0.660`.

::: hint
`ERROR: failed to reproduce 'train'` suivi d'une erreur de connexion à MLflow : le serveur ne tourne pas ; `docker compose up -d mlflow` dans le terminal de la VM, puis relancez `dvc repro`. Une erreur YAML : un espace manque ou une tabulation s'est glissée dans `dvc.yaml` ou `params.yaml` ; `cat -A dvc.yaml` montre les tabulations sous la forme `^I`.
:::
::::

{#etape5}
## Étape 5 : le run dans MLflow

:::: lab Étape 5 | Ce que MLflow a retenu | 5 min
Sur http://localhost:5000, ouvrez l'expérience **`colisvert-retards`**, puis le run **`train-C1.0`**.

**Vérification :** vous y trouvez :

- trois **paramètres** : `C` = `1.0`, `class_weight` = `None`, `max_iter` = `1000` ;
- six **métriques** : `f1_train` (0.668), notée par `train.py`, puis les cinq métriques du test, ajoutées par `evaluate.py` au même run ;
- deux **tags** : `commit_git` (votre commit de l'étape 1) et `md5_donnees` = `127f20d4baf2636267145a03529220f1` ;
- un **artefact** `metrics.json`, et le **modèle**, relié au run.

`train.py` et `evaluate.py` sont deux programmes distincts. Comment les métriques du second arrivent-elles dans le run du premier ? `train.py` écrit l'identifiant de son run dans `models/run_id.txt`, et `evaluate.py` le relit. Un fichier, comme toujours entre deux étapes.
::::

{#etape6}
## Étape 6 : versionner le pipeline et ses résultats

:::: lab Étape 6 | git commit et dvc push | 5 min
```bash title="Terminal JupyterLab"
git status --short
git add dvc.yaml dvc.lock params.yaml metrics.json data/.gitignore models/.gitignore
git commit -m "Pipeline v1 : prepare, train, evaluate"
dvc push
```

- **Git** reçoit la **recette** et ses résultats légers : `dvc.yaml` (les étapes), `params.yaml` (les réglages), `dvc.lock` (les empreintes de tout ce qui est entré et sorti), `metrics.json` (les métriques) et les deux `.gitignore` écrits par DVC.
- **DVC** envoie au stockage les **produits** lourds : les jeux préparés et le modèle.

**Vérification :** avant le `git add`, `git status --short` montre `dvc.yaml`, `dvc.lock`, `params.yaml` et `metrics.json` précédés de `??` (nouveaux), `data/.gitignore` précédé de ` M` (modifié : DVC y a ajouté `/prepared`) et le dossier `models/`, qui contient le nouveau `models/.gitignore`. D'autres lignes `??` peuvent apparaître (vos notebooks, les autres fichiers de `data`) : on ne les versionne pas. `dvc push` annonce `4 files pushed` : les deux jeux préparés (`train.csv` et `test.csv`), la liste du contenu du dossier `data/prepared` (DVC range un dossier comme un fichier qui énumère ses fichiers et leurs empreintes), et le modèle.
::::

{#etape7}
## Étape 7 : relancer sans rien changer

:::: lab Étape 7 | Reproductible et économe | 4 min
```bash title="Terminal JupyterLab"
dvc repro
dvc dag
```

**Vérification :** `dvc repro` ne relance rien et répond `Data and pipelines are up to date.` : aucune empreinte de `dvc.lock` n'a changé. `dvc dag` dessine le graphe des étapes : `prepare`, puis `train`, puis `evaluate`, avec en tête le fichier `data/livraisons.csv.dvc`.

C'est la règle d'idempotence de ce matin, garantie par l'outil : relancer ne coûte rien et ne change rien. Sur un pipeline de plusieurs heures, c'est ce qui permet de relancer après une panne sans tout recalculer.
::::

{#etape8}
## Étape 8 : prouver l'origine du modèle

:::: lab Étape 8 | Le triangle code, données, modèle | 6 min
Un auditeur vous demande : « sur quelles données exactes ce modèle a-t-il appris ? ». Deux témoins indépendants doivent donner la même réponse : MLflow (le tag du run) et DVC (le fichier `dvc.lock`). Dans votre notebook `j2-matin.ipynb` :

```python title="Cellule 10 : deux témoins, une seule empreinte"
import mlflow
import yaml

dernier = mlflow.search_runs(
    experiment_names=["colisvert-retards"],
    filter_string="params.class_weight = 'None'",
    order_by=["attributes.start_time DESC"],
    max_results=1,
).iloc[0]
print("MLflow :", dernier["tags.md5_donnees"], "| paramètres C =", dernier["params.C"])

verrou = yaml.safe_load(open("/home/lab/projet/dvc.lock"))
entree = next(d for d in verrou["stages"]["prepare"]["deps"] if d["path"] == "data/livraisons.csv")
print("DVC    :", entree["md5"], "| taille :", entree["size"], "octets")
```

```plaintext title="Sortie attendue"
MLflow : 127f20d4baf2636267145a03529220f1 | paramètres C = 1.0
DVC    : 127f20d4baf2636267145a03529220f1 | taille : 320537 octets
```

- `filter_string` filtre les runs comme une clause `WHERE` : ici, ceux dont le paramètre `class_weight` vaut `None`. Les paramètres sont toujours stockés comme du **texte**, d'où les guillemets autour de `'None'`.
- `order_by` et `max_results=1` gardent le plus récent.
- `dvc.lock` est un fichier YAML : on le lit comme un dictionnaire Python.

**Les deux témoins concordent.** Et le troisième sommet, le code, est le tag `commit_git`. Avec ces trois informations, n'importe qui peut reconstruire ce modèle dans six mois : `git checkout <commit>`, `dvc checkout`, `dvc repro`.
::::

::: callout tip Question fréquente : « Faut-il vraiment DVC et MLflow ? Ils semblent faire la même chose. »
Ils se recouvrent un peu, mais leurs centres de gravité diffèrent. **DVC** est centré sur les **fichiers** et le **pipeline** : quelles données, quelles étapes, que relancer. **MLflow** est centré sur les **expériences** et les **modèles** : comparer des centaines de runs, ranger les modèles, les servir. Beaucoup d'équipes utilisent les deux, exactement comme ici. Pour une petite équipe, MLflow seul plus un stockage de données daté peut suffire au début.
:::

{#avance}
## Pour aller plus loin : comment DVC décide de relancer, et ses expériences

Ce bloc est pour les profils avancés ; rien ici n'est exigé dans l'évaluation.

**La décision de relancer.** Pour chaque étape, `dvc.lock` garde l'empreinte de la commande, de chaque dépendance, de chaque paramètre utilisé et de chaque sortie. Avant de lancer une étape, `dvc repro` recalcule ces empreintes et compare. Rien n'a changé : l'étape est sautée. C'est plus fin qu'une comparaison de dates de modification : un fichier réécrit à l'identique (même contenu) ne déclenche rien, et `train` ne se relance pas si l'on modifie seulement `prepare.date_coupure`… sauf que changer la date de coupure modifie `data/prepared`, qui est une dépendance de `train` : la chaîne se propage par les **contenus**, pas par les noms.

**Le cache des exécutions** (*run cache*). DVC garde aussi un historique des exécutions passées. Si vous remettez `C` à une valeur déjà essayée, `dvc repro` peut répondre que l'étape est déjà en cache et **restaurer** ses sorties au lieu de réentraîner. Attention dans ce cas : le script n'est pas réexécuté, donc **aucun run MLflow** n'est créé. C'est une raison de bien distinguer « reproduire un résultat » (DVC) et « tracer une expérience » (MLflow). L'option `dvc repro --force` relance tout, quoi qu'il arrive.

**Les expériences DVC.** `dvc exp run --set-param train.C=0.1` lance le pipeline avec un paramètre modifié, **sans** toucher à votre espace de travail ni créer de commit ; `dvc exp show` compare ensuite toutes les expériences dans un tableau. C'est l'équivalent, côté DVC, de la comparaison de runs dans MLflow. Les deux approches coexistent ; dans cette formation, MLflow tient ce rôle, parce qu'il sert aussi au registre et au déploiement cet après-midi.

**Les métriques qu'on compare dans Git.** Comme `metrics.json` est versionné par Git, `dvc metrics diff` compare les métriques de l'espace de travail à celles du dernier commit, ou entre deux commits ou deux branches. Une revue de code peut ainsi montrer l'**effet** d'une modification sur le modèle, à côté de la modification elle-même. Vous l'utiliserez dans l'évaluation.

{#quiz}
## Quiz de validation

```quiz
- q: Vous modifiez train.C dans params.yaml, puis lancez dvc repro. Quelles étapes sont relancées ?
  options:
    - Toutes les étapes
    - train et evaluate, mais pas prepare
    - prepare seulement
    - Aucune, il faut d'abord faire git commit
  answer: 1
  explain: prepare ne dépend pas de train.C. train dépend de ce paramètre, et evaluate dépend du modèle produit par train.
- q: Que contient le fichier dvc.lock ?
  options:
    - Le mot de passe du stockage DVC
    - Les empreintes de la commande, des dépendances, des paramètres et des sorties de chaque étape
    - Le modèle entraîné
    - La liste des runs MLflow
  answer: 1
  explain: C'est le ticket de vestiaire du pipeline entier. Il est versionné par Git.
- q: Pourquoi metrics.json est-il déclaré avec cache false ?
  options:
    - Parce que DVC ne sait pas lire le JSON
    - Pour qu'il soit versionné par Git, petit et facile à comparer d'un commit à l'autre
    - Pour qu'il ne soit jamais écrit
    - Pour accélérer dvc push
  answer: 1
  explain: Un petit fichier texte se versionne très bien dans Git, et dvc metrics diff peut alors comparer deux commits.
- q: dvc repro répond « Data and pipelines are up to date. ». Que s'est-il passé ?
  options:
    - Une erreur, le pipeline n'a pas tourné
    - Rien à relancer - aucune empreinte de dvc.lock n'a changé depuis la dernière exécution
    - DVC a supprimé les sorties
    - Le serveur MLflow est arrêté
  answer: 1
  explain: C'est l'idempotence garantie par l'outil. Relancer ne coûte rien et ne change rien.
```
