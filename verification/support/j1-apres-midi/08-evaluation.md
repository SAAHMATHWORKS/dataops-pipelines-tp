---
subtitle: >-
  La direction de ColisVert veut des chiffres fiables et retrouvables. Vous contrôlez le fichier
  brut, vous le nettoyez, vous versionnez le résultat, et vous prouvez qu'on peut le restaurer
  après une perte.
objectives:
  - Produire un rapport de qualité sur un fichier brut
  - Nettoyer des données avec des règles écrites en code
  - Versionner un fichier avec DVC et Git
  - Restaurer un fichier versionné depuis le stockage DVC
# Barème : 14 points pour les étapes (indiqués sur chaque étape) + 6 points pour le QCM
quiz_points: 6
---

{#consignes}
## Consignes

**Scénario.** Le service client se plaint de chiffres qui changent d'une semaine à l'autre. La direction vous demande un fichier de livraisons **propre**, **versionné** et **restaurable**.

- **Durée :** 30 minutes, en autonomie. Le formateur passe voir chacun.
- **Où :** les étapes 1 et 2 dans un notebook neuf `j1-apres-midi-evaluation.ipynb` (dossier `notebooks`), les étapes 3 et 4 dans le terminal de JupyterLab, dans le dépôt où vous avez fait le TP.
- **Validation :** chaque étape se termine par une **preuve** : collez la sortie demandée et cliquez sur « Envoyer ma preuve ».
- **Barème :** 14 points pour les 4 étapes, 6 points pour le QCM final (une seule tentative par question).
- Les corrections sont là si vous bloquez, mais essayez d'abord.

::: widget task-progress
:::

{#qualite}
## Contrôler

:::: task Étape 1 | Le rapport de qualité du fichier brut | 7 min | 3 pts
Dans la première cellule du notebook :

1. préparez les données (`preparer_donnees()`) et chargez `livraisons_brutes.csv` dans `brutes` ;
2. recopiez la liste `ENTREPOTS` (Cellule 5) et la fonction `rapport_qualite` (Cellule 7) de l'après-midi, et affichez le rapport de `brutes` ;
3. affichez la liste des identifiants (`id_colis`) des colis au **délai réel négatif**.

::: proof Collez la sortie complète de votre cellule
:::

::: hint
Pour la liste des identifiants : on filtre les lignes avec une condition entre crochets, `brutes[brutes["delai_reel_h"] < 0]`, puis on garde la colonne `id_colis` et on la transforme en liste avec `.tolist()`.
:::

::: solution
```python title="Évaluation · Cellule 1"
import pandas as pd
from colisvert.donnees import DOSSIER_DATA, preparer_donnees

dossier = preparer_donnees()
brutes = pd.read_csv(DOSSIER_DATA / "livraisons_brutes.csv")

ENTREPOTS = ["Lille", "Lyon", "Nantes", "Toulouse"]


def rapport_qualite(df):
    """Un contrôle par ligne : dimension, contrôle, nombre et pourcentage de lignes en défaut."""
    controles = [
        ("Unicité", "ligne en double", df.duplicated()),
        ("Complétude", "météo manquante", df["meteo"].isna()),
        ("Complétude", "poids manquant", df["poids_kg"].isna()),
        ("Validité", "entrepôt inconnu", ~df["entrepot"].isin(ENTREPOTS)),
        ("Validité", "date hors format aaaa-mm-jj", ~df["date_expedition"].str.fullmatch(r"\d{4}-\d{2}-\d{2}")),
        ("Validité", "délai réel négatif", df["delai_reel_h"] < 0),
        ("Cohérence", "en_retard contredit les délais",
         df["en_retard"] != (df["delai_reel_h"] > df["delai_promis_h"]).astype(int)),
    ]
    rapport = pd.DataFrame(
        [(dimension, controle, int(defauts.sum())) for dimension, controle, defauts in controles],
        columns=["dimension", "controle", "lignes"],
    )
    rapport["pct"] = (rapport["lignes"] / len(df) * 100).round(2)
    return rapport


print(rapport_qualite(brutes).to_string(index=False))
print(brutes[brutes["delai_reel_h"] < 0]["id_colis"].tolist())
```

```plaintext title="Sortie attendue"
livraisons.csv : 5035 colis, dont 862 en retard
arrivees.csv : 56 jours
livraisons_brutes.csv : les mêmes colis, avec des défauts de qualité
 dimension                       controle  lignes  pct
   Unicité                ligne en double      25 0.49
Complétude                météo manquante      40 0.79
Complétude                 poids manquant      15 0.30
  Validité               entrepôt inconnu      12 0.24
  Validité    date hors format aaaa-mm-jj      20 0.40
  Validité             délai réel négatif       8 0.16
 Cohérence en_retard contredit les délais      10 0.20
['CV00195', 'CV00257', 'CV00834', 'CV01511', 'CV01813', 'CV02969', 'CV03928', 'CV04890']
```
:::
::::

{#nettoyer}
## Nettoyer

:::: task Étape 2 | Appliquer les règles de nettoyage | 9 min | 4 pts
La gouvernance a validé cinq règles. Appliquez-les dans l'ordre, sur une copie de `brutes` appelée `propres` :

1. supprimer les lignes en double ;
2. remplacer l'entrepôt `Lile` par `Lille` ;
3. réécrire les dates `jj/mm/aaaa` au format `aaaa-mm-jj` ;
4. écarter les colis au délai réel négatif (impossible à corriger : on ne connaît pas le vrai délai) ;
5. recalculer `en_retard` à partir des délais.

On **garde** les colis dont la météo ou le poids manque : la donnée est incomplète, pas fausse.

Puis affichez la forme de `propres`, le nombre de colis en retard, et le rapport de qualité de `propres`. Enregistrez le résultat dans `data/livraisons_propres.csv`, sans l'index, et affichez son empreinte MD5.

::: proof Collez la sortie complète de votre cellule
:::

::: hint
Doublons : `drop_duplicates()`. Remplacement : `replace({"Lile": "Lille"})` sur la colonne. Dates : convertissez avec chacun des deux formats (`format="%Y-%m-%d"` puis `format="%d/%m/%Y"`, avec `errors="coerce"`), combinez avec `fillna`, puis réécrivez avec `.dt.strftime("%Y-%m-%d")`. Empreinte : `hashlib.md5(chemin.read_bytes()).hexdigest()`.
:::

::: solution
```python title="Évaluation · Cellule 2"
import hashlib

propres = brutes.drop_duplicates().copy()
propres["entrepot"] = propres["entrepot"].replace({"Lile": "Lille"})

format_iso = pd.to_datetime(propres["date_expedition"], format="%Y-%m-%d", errors="coerce")
format_fr = pd.to_datetime(propres["date_expedition"], format="%d/%m/%Y", errors="coerce")
propres["date_expedition"] = format_iso.fillna(format_fr).dt.strftime("%Y-%m-%d")

propres = propres[propres["delai_reel_h"] >= 0].copy()
propres["en_retard"] = (propres["delai_reel_h"] > propres["delai_promis_h"]).astype(int)

print(propres.shape, "colis en retard :", propres["en_retard"].sum())
print(rapport_qualite(propres).to_string(index=False))

chemin = DOSSIER_DATA / "livraisons_propres.csv"
propres.to_csv(chemin, index=False)
print("MD5 :", hashlib.md5(chemin.read_bytes()).hexdigest())
```

```plaintext title="Sortie attendue"
(5027, 11) colis en retard : 862
 dimension                       controle  lignes  pct
   Unicité                ligne en double       0  0.0
Complétude                météo manquante      40  0.8
Complétude                 poids manquant      15  0.3
  Validité               entrepôt inconnu       0  0.0
  Validité    date hors format aaaa-mm-jj       0  0.0
  Validité             délai réel négatif       0  0.0
 Cohérence en_retard contredit les délais       0  0.0
MD5 : 4065fc3504fb02cc43a0333ed727384e
```

5 060 lignes, moins 25 doublons, moins 8 délais impossibles : **5 027 colis**. Il ne reste que les 55 valeurs manquantes, gardées volontairement. Le pourcentage de météos manquantes passe de 0,79 % à 0,8 % : le nombre ne change pas, mais il y a moins de lignes. pandas n'affiche pas les zéros inutiles : `0.8` pour 0,80.

**Pourquoi deux conversions de dates ?** Une seule conversion « devinée », par exemple `pd.to_datetime(..., format="mixed", dayfirst=True)`, lit aussi les dates `aaaa-mm-jj` en mettant le jour avant le mois : le 7 septembre (`2026-09-07`) devient le 9 juillet. Imposer chaque format explicitement évite ce piège.
:::
::::

{#versionner}
## Versionner et restaurer

:::: task Étape 3 | Versionner le fichier propre | 7 min | 4 pts
Dans le terminal de JupyterLab, dans `/home/lab/projet`, sur la branche `tp-dvc` :

1. confiez `data/livraisons_propres.csv` à DVC ;
2. versionnez le ticket et `data/.gitignore` avec Git, avec le message `Données propres` ;
3. envoyez les données au stockage DVC ;
4. affichez le ticket, puis le message du dernier commit.

**Vérification :** l'empreinte du ticket est celle affichée à la fin de l'étape 2.

::: proof Collez la sortie de : cat data/livraisons_propres.csv.dvc puis git log --format=%s -1
:::

::: hint
Ce sont les commandes de l'étape 3 du TP, avec un autre nom de fichier. `dvc push` vous dit « No remote provided » ? Le stockage n'a pas été configuré : reprenez l'étape 2 du TP.
:::

::: solution
```bash title="Terminal JupyterLab"
cd /home/lab/projet
dvc add data/livraisons_propres.csv
git add data/livraisons_propres.csv.dvc data/.gitignore
git commit -m "Données propres"
dvc push
cat data/livraisons_propres.csv.dvc
git log --format=%s -1
```

Le ticket contient `md5: 4065fc3504fb02cc43a0333ed727384e`, la taille `size: 319817`, `hash: md5` et `path: livraisons_propres.csv`. Le dernier commit s'appelle `Données propres`. `dvc push` annonce `1 file pushed`.
:::
::::

:::: task Étape 4 | Restaurer après une perte | 6 min | 3 pts
Un collègue efface par erreur le fichier propre **et** le cache de DVC. Simulez l'incident, puis restaurez le fichier depuis le stockage.

```bash title="Terminal JupyterLab"
rm data/livraisons_propres.csv
rm -rf .dvc/cache
ls data
```

**Vérification :** `livraisons_propres.csv` n'apparaît plus dans `data`, mais son ticket `livraisons_propres.csv.dvc` est toujours là.

Restaurez maintenant le fichier avec **une seule commande DVC**, puis vérifiez son empreinte avec `md5sum`.

::: proof Collez la sortie de la commande DVC de restauration, puis celle de md5sum data/livraisons_propres.csv
:::

::: hint
Le cache local est vide : DVC doit aller chercher le fichier dans le stockage distant. C'est l'inverse de `dvc push`.
:::

::: solution
```bash title="Terminal JupyterLab"
dvc pull data/livraisons_propres.csv.dvc
md5sum data/livraisons_propres.csv
```

`dvc pull` télécharge le fichier depuis le stockage et le remet en place ; il annonce un fichier ajouté. `md5sum` affiche `4065fc3504fb02cc43a0333ed727384e  data/livraisons_propres.csv` : le fichier restauré est **identique**, octet pour octet, à celui de l'étape 2.

C'est exactement ce que fera un collègue qui clone le dépôt sur une autre machine : `git clone`, puis `dvc pull`.
:::
::::

{#quiz}
## Quiz : vos résultats

Répondez à partir de l'après-midi et de ce que vous venez de faire. **Une seule tentative par question** : votre première réponse est enregistrée et compte pour la note.

```quiz
- q: Combien de colis contient le fichier propre ?
  options: ["5 060", "5 035", "5 027", "5 002"]
  answer: 2
  explain: 5 060 lignes brutes, moins 25 doublons et 8 délais impossibles.
- q: Pourquoi garde-t-on les colis dont la météo manque ?
  options:
    - Parce qu'on a oublié de les supprimer
    - Parce que la donnée est incomplète mais pas fausse ; les supprimer ferait perdre de vrais colis
    - Parce que pandas ne sait pas les supprimer
    - Parce que la météo ne sert à rien
  answer: 1
  explain: Supprimer ces colis fausserait le nombre de colis et le taux de retard. On les garde, et on documente le défaut.
- q: Un ticket .dvc est dans Git, mais le fichier et le cache ont disparu. Quelle commande restaure le fichier ?
  options: [git pull, dvc add, dvc pull, dvc init]
  answer: 2
  explain: dvc pull lit l'empreinte dans le ticket et va chercher le fichier correspondant dans le stockage distant.
- q: Quelle pratique du manifeste DataOps ce TP met-il en œuvre ?
  options:
    - Rendre reproductible, en versionnant les données
    - Des interactions quotidiennes avec le client
    - S'auto-organiser
    - Réduire les temps de cycle par des réunions plus courtes
  answer: 0
  explain: C'est le principe n° 11, tout versionner, données comprises, pour refaire le même calcul plus tard.
- q: Quelle démarche s'occupe en plus des modèles qui se dégradent en silence ?
  options: [DevOps, DataOps, MLOps, Lean]
  answer: 2
  explain: Le MLOps ajoute le modèle aux objets qui peuvent changer, et surveille sa dérive.
- q: Dans Azure, quel service stocke les fichiers de données d'un lac ?
  options: [Azure Key Vault, Azure Data Lake Storage Gen2, Microsoft Entra ID, Azure DevOps]
  answer: 1
  explain: Key Vault garde les secrets, Entra ID les identités, Azure DevOps le code et l'automatisation.
```
