---
subtitle: >-
  La responsable du service client veut savoir si un réglage permet d'atteindre le critère de
  succès de la charte. L'auditeur interne, lui, veut la preuve de l'origine de chaque modèle.
  Vous comparez, vous tracez, et vous découvrez une limite du traçage.
objectives:
  - Évaluer une ligne de base contre le critère de succès d'un projet
  - Enregistrer et comparer plusieurs runs dans MLflow
  - Tester une variante du pipeline sur une branche et comparer ses métriques avec dvc metrics diff
  - Vérifier l'origine d'un modèle à partir de ses tags MLflow et de l'historique Git
# Barème : 14 points pour les étapes (indiqués sur chaque étape) + 6 points pour le QCM
quiz_points: 6
---

{#consignes}
## Consignes

**Scénario.** La charte du projet fixe le critère de succès : **rappel ≥ 0,80 et précision ≥ 0,50**. Le premier modèle (rappel 0,591) ne l'atteint pas. On vous demande de tester l'option `class_weight="balanced"`, de comparer proprement, et de prouver l'origine des modèles.

- **Durée :** 30 minutes, en autonomie. Le formateur passe voir chacun.
- **Où :** les étapes 1, 2 et 4 dans un notebook neuf `j2-matin-evaluation.ipynb` (dossier `notebooks`), l'étape 3 dans le terminal de JupyterLab, dans `/home/lab/projet`.
- **Validation :** chaque étape se termine par une **preuve** : collez la sortie demandée et cliquez sur « Envoyer ma preuve ».
- **Barème :** 14 points pour les 4 étapes, 6 points pour le QCM final (une seule tentative par question).
- Les corrections sont là si vous bloquez, mais essayez d'abord.

::: widget task-progress
:::

{#critere}
## Le critère de succès

:::: task Étape 1 | Deux lignes de base face au critère | 3 min | 3 pts
Dans la première cellule du notebook :

1. préparez les données, ajoutez la colonne `jour_semaine` et découpez-les dans le temps (avant le 19 octobre pour le train, à partir du 19 octobre pour le test), comme ce matin ;
2. écrivez une fonction `critere_atteint(rappel, precision)` qui renvoie `True` si le critère de la charte est atteint ;
3. pour les deux lignes de base « tous à l'heure » (que des 0) et « tous en retard » (que des 1), affichez la précision, le rappel et le résultat de `critere_atteint`, arrondis à 3 décimales.

::: proof Collez la sortie complète de votre cellule
:::

::: hint
Pour la ligne de base « tous à l'heure », `precision_score` ne peut pas diviser par zéro (aucun colis signalé) : passez-lui `zero_division=0`. Une liste de 1 de la bonne longueur : `[1] * len(test)`.
:::

::: solution
```python title="Évaluation · Cellule 1"
import pandas as pd
from sklearn.metrics import precision_score, recall_score

from colisvert.donnees import DOSSIER_DATA, preparer_donnees
from pipeline.commun import CATEGORIELLES, CIBLE, NUMERIQUES, ajouter_jour_semaine

preparer_donnees()
livraisons = ajouter_jour_semaine(pd.read_csv(DOSSIER_DATA / "livraisons.csv"))
train = livraisons[livraisons["date_expedition"] < "2026-10-19"]
test = livraisons[livraisons["date_expedition"] >= "2026-10-19"]


def critere_atteint(rappel, precision):
    """Le critère de succès de la charte : rappel >= 0,80 et précision >= 0,50."""
    return rappel >= 0.80 and precision >= 0.50


for nom, valeur in [("tous à l'heure", 0), ("tous en retard", 1)]:
    prediction = [valeur] * len(test)
    precision = round(precision_score(test[CIBLE], prediction, zero_division=0), 3)
    rappel = round(recall_score(test[CIBLE], prediction), 3)
    print(f"{nom} : précision {precision}, rappel {rappel}, critère {critere_atteint(rappel, precision)}")
```

```plaintext title="Sortie attendue"
livraisons.csv : 5035 colis, dont 862 en retard
arrivees.csv : 56 jours
livraisons_brutes.csv : les mêmes colis, avec des défauts de qualité
tous à l'heure : précision 0.0, rappel 0.0, critère False
tous en retard : précision 0.169, rappel 1.0, critère False
```

« Tous en retard » attrape tous les retards (rappel 1,0), mais 83 % de ses alertes sont fausses : le service client appellerait 1 230 clients pour 208 retards. C'est pour cela que la charte exige **les deux** seuils.
:::
::::

{#comparer}
## Comparer dans MLflow

:::: task Étape 2 | Trois runs, un classement | 9 min | 4 pts
Dans une nouvelle cellule, enregistrez trois runs dans une expérience **`j2-evaluation`**, un par réglage :

| Nom du run | `C` | `class_weight` |
|---|---|---|
| `c1-none` | 1.0 | `None` |
| `c1-balanced` | 1.0 | `"balanced"` |
| `c01-balanced` | 0.1 | `"balanced"` |

Pour chaque run : entraînez le modèle avec `construire_modele(C, class_weight, 1000)` sur le train, notez les deux paramètres, les métriques `precision`, `rappel` et `f1` du test (arrondies à 3 décimales), et un tag `critere` qui vaut le résultat de `critere_atteint`.

Puis affichez, avec `search_runs`, le nom, le F1, le rappel, la précision et le tag `critere` des trois runs, **du meilleur F1 au moins bon**.

::: proof Collez la sortie complète de votre cellule
:::

::: hint
La boucle : `for nom, C, class_weight in [("c1-none", 1.0, None), …]:`, puis `with mlflow.start_run(run_name=nom):` à l'intérieur. Un tag est toujours du texte : `mlflow.set_tag("critere", str(...))`. Le tri : `order_by=["metrics.f1 DESC"]`. Les colonnes : `tags.mlflow.runName`, `metrics.f1`, `metrics.rappel`, `metrics.precision`, `tags.critere`.
:::

::: solution
```python title="Évaluation · Cellule 2"
import mlflow
from sklearn.metrics import f1_score

from pipeline.train import construire_modele

X_COLS = CATEGORIELLES + NUMERIQUES
mlflow.set_experiment("j2-evaluation")

for nom, C, class_weight in [("c1-none", 1.0, None), ("c1-balanced", 1.0, "balanced"), ("c01-balanced", 0.1, "balanced")]:
    with mlflow.start_run(run_name=nom):
        modele = construire_modele(C, class_weight, 1000)
        modele.fit(train[X_COLS], train[CIBLE])
        predictions = modele.predict(test[X_COLS])
        precision = round(precision_score(test[CIBLE], predictions), 3)
        rappel = round(recall_score(test[CIBLE], predictions), 3)
        mlflow.log_params({"C": C, "class_weight": class_weight})
        mlflow.log_metrics({"precision": precision, "rappel": rappel,
                            "f1": round(f1_score(test[CIBLE], predictions), 3)})
        mlflow.set_tag("critere", str(critere_atteint(rappel, precision)))

runs = mlflow.search_runs(experiment_names=["j2-evaluation"], order_by=["metrics.f1 DESC"])
colonnes = ["tags.mlflow.runName", "metrics.f1", "metrics.rappel", "metrics.precision", "tags.critere"]
print(runs[colonnes].to_string(index=False))
```

```plaintext title="Sortie attendue"
🏃 View run c1-none at: http://mlflow:5000/#/experiments/3/runs/<id>
🧪 View experiment at: http://mlflow:5000/#/experiments/3
🏃 View run c1-balanced at: http://mlflow:5000/#/experiments/3/runs/<id>
🧪 View experiment at: http://mlflow:5000/#/experiments/3
🏃 View run c01-balanced at: http://mlflow:5000/#/experiments/3/runs/<id>
🧪 View experiment at: http://mlflow:5000/#/experiments/3
tags.mlflow.runName  metrics.f1  metrics.rappel  metrics.precision tags.critere
        c1-balanced       0.692           0.875              0.572         True
       c01-balanced       0.685           0.880              0.561         True
            c1-none       0.660           0.591              0.745        False
```

Le numéro d'expérience (`3` ici) dépend de l'ordre dans lequel vous avez créé vos expériences : seul compte le tableau. **`class_weight="balanced"` fait passer le rappel de 0,591 à 0,875** : en donnant plus de poids aux colis en retard, plus rares, on demande au modèle de moins les manquer, au prix de plus de fausses alertes (précision 0,572). Les deux réglages équilibrés atteignent le critère ; on choisira proprement entre eux cet après-midi, sur une semaine de validation, et non sur le test.
:::
::::

{#variante}
## Une variante du pipeline

:::: task Étape 3 | Tester le réglage dans le pipeline, sur une branche | 10 min | 4 pts
Dans le terminal de JupyterLab, dans `/home/lab/projet` :

1. créez une branche `eval-balanced` à partir de `tp-dvc` ;
2. dans `params.yaml`, remplacez `class_weight: null` par `class_weight: balanced` (la commande `sed -i 's/class_weight: null/class_weight: balanced/' params.yaml` le fait pour vous) ;
3. relancez le pipeline, puis comparez les métriques à celles du dernier commit avec `dvc metrics diff` ;
4. enregistrez la variante sur la branche : `git commit -am "Variante : class_weight balanced"` ;
5. revenez sur `tp-dvc`, remettez les données et le modèle de cette branche en place avec `dvc checkout`, et affichez les métriques avec `dvc metrics show`.

::: proof Collez la sortie de dvc metrics diff (point 3), puis celle de dvc metrics show (point 5)
:::

::: hint
`git switch -c` crée une branche et s'y place. Pendant `dvc repro`, l'étape `prepare` doit être sautée : seuls les paramètres de `train` ont changé. Après `git switch tp-dvc`, Git a remis `params.yaml`, `dvc.lock` et `metrics.json` de la branche ; `dvc checkout` remet le modèle qui correspond à ce `dvc.lock`.
:::

::: solution
```bash title="Terminal JupyterLab"
cd /home/lab/projet
git switch -c eval-balanced
sed -i 's/class_weight: null/class_weight: balanced/' params.yaml
dvc repro
dvc metrics diff
git commit -am "Variante : class_weight balanced"
git switch tp-dvc
dvc checkout
dvc metrics show
```

`dvc repro` saute `prepare` (`Stage 'prepare' didn't change, skipping`), relance `train` puis `evaluate`. `dvc metrics diff` compare le commit (`HEAD`, le pipeline v1) à l'espace de travail (la variante) et n'affiche que ce qui a changé : `exactitude` de 0.897 à 0.868, `f1` de 0.66 à 0.692, `precision` de 0.745 à 0.572, `rappel` de 0.591 à 0.875. L'AUC (0.949 dans les deux cas) n'apparaît pas : elle n'a pas changé.

Après le retour sur `tp-dvc`, `dvc metrics show` affiche de nouveau les métriques du pipeline v1 : `f1 0.66`, `rappel 0.591`. La variante n'est pas perdue : elle vit sur sa branche, avec son `dvc.lock`, et son modèle est dans le cache de DVC. C'est ainsi qu'une équipe teste une idée sans casser la version de référence.
:::
::::

{#origine}
## L'origine d'un modèle

:::: task Étape 4 | Ce que dit, et ne dit pas, le tag du commit | 8 min | 3 pts
L'auditeur prend le run de la variante (expérience `colisvert-retards`, `class_weight` = `balanced`) et veut retrouver son code. Dans une nouvelle cellule du notebook :

1. retrouvez ce run (le plus récent) avec `search_runs` et affichez ses paramètres `C` et `class_weight` ;
2. comparez son tag `commit_git` au commit de **chacune** des deux branches, `tp-dvc` et `eval-balanced` (la commande `git rev-parse --short <branche>`, lancée depuis Python avec `subprocess.run`) ;
3. affichez la valeur de `class_weight` dans le `params.yaml` du commit noté par le tag (la commande `git show <commit>:params.yaml`).

::: proof Collez la sortie complète de votre cellule
:::

::: hint
`subprocess.run(["git", "rev-parse", "--short", "tp-dvc"], capture_output=True, text=True, cwd="/home/lab/projet").stdout.strip()` renvoie le commit court de la branche. `yaml.safe_load` lit le texte renvoyé par `git show`.
:::

::: solution
```python title="Évaluation · Cellule 3"
import subprocess

import yaml


def git(*arguments):
    resultat = subprocess.run(["git", *arguments], capture_output=True, text=True, cwd="/home/lab/projet")
    return resultat.stdout.strip()


variante = mlflow.search_runs(
    experiment_names=["colisvert-retards"],
    filter_string="params.class_weight = 'balanced'",
    order_by=["attributes.start_time DESC"],
    max_results=1,
).iloc[0]
commit = variante["tags.commit_git"]
print("run de la variante : C =", variante["params.C"], "| class_weight =", variante["params.class_weight"])
print("tag commit_git = commit de tp-dvc        :", commit == git("rev-parse", "--short", "tp-dvc"))
print("tag commit_git = commit de eval-balanced :", commit == git("rev-parse", "--short", "eval-balanced"))
print("class_weight dans le params.yaml de ce commit :", yaml.safe_load(git("show", f"{commit}:params.yaml"))["train"]["class_weight"])
```

```plaintext title="Sortie attendue"
run de la variante : C = 1.0 | class_weight = balanced
tag commit_git = commit de tp-dvc        : True
tag commit_git = commit de eval-balanced : False
class_weight dans le params.yaml de ce commit : None
```

**Le piège.** Le run a été entraîné **avant** le commit de la variante : le tag note donc le commit de `tp-dvc`, dont le `params.yaml` dit `class_weight: None`… alors que le modèle a été entraîné avec `balanced`. Le commit seul ne suffit pas quand l'espace de travail contient des modifications non commitées. Ici, le paramètre noté par MLflow sauve la mise ; mais une modification du **code** non commitée, elle, ne laisserait aucune trace.

Les deux parades professionnelles : **committer avant d'entraîner** (et faire refuser par le pipeline un entraînement sur un espace de travail modifié), ou noter en plus un tag qui signale les modifications en cours (`git status --porcelain` non vide).
:::
::::

{#quiz}
## Quiz : vos résultats

Répondez à partir de la matinée et de ce que vous venez de faire. **Une seule tentative par question** : votre première réponse est enregistrée et compte pour la note.

```quiz
- q: Quel réglage du modèle fait passer le rappel de 0,591 à 0,875 ?
  options: ["C = 0.1", "class_weight = balanced", "max_iter = 2000", "date_coupure = 2026-10-12"]
  answer: 1
  explain: Donner plus de poids à la classe rare (les retards) pousse le modèle à moins les manquer.
- q: La ligne de base « tous en retard » a un rappel de 1,0. Pourquoi n'atteint-elle pas le critère ?
  options:
    - Parce que son rappel est trop faible
    - Parce que sa précision (0,169) est sous le seuil de 0,50 - 83 % de ses alertes sont fausses
    - Parce qu'elle n'est pas enregistrée dans MLflow
    - Parce qu'une ligne de base n'a pas de rappel
  answer: 1
  explain: Le critère exige les deux seuils, justement pour écarter ce genre de solution.
- q: Pendant dvc repro sur la branche eval-balanced, quelle étape est sautée ?
  options: [prepare, train, evaluate, Aucune]
  answer: 0
  explain: prepare ne dépend que de prepare.date_coupure, qui n'a pas changé.
- q: Que compare dvc metrics diff, sans argument ?
  options:
    - Deux runs MLflow
    - Les métriques de l'espace de travail et celles du dernier commit
    - Le train et le test
    - Deux versions des données
  answer: 1
  explain: metrics.json est versionné par Git ; DVC compare la version du commit (HEAD) à celle de l'espace de travail.
- q: Le tag commit_git d'un run désigne un commit dont le params.yaml diffère des paramètres du run. Que s'est-il passé ?
  options:
    - MLflow a fait une erreur
    - L'entraînement a été lancé avec des modifications non commitées
    - Le cache de DVC est corrompu
    - Le serveur MLflow a redémarré
  answer: 1
  explain: Le tag note le commit au moment de l'entraînement. Committer avant d'entraîner évite cet écart.
- q: Dans quelle phase du processus agile se trouve le projet ColisVert à la fin de cette matinée ?
  options: [Idéation, Inception, Recherche et développement, Transition et production]
  answer: 2
  explain: Des expériences tracées et un premier pipeline - le modèle candidat n'est pas encore choisi ni déployé.
```
