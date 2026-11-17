---
subtitle: >-
  Un notebook qui marche une fois n'est pas un produit. Un pipeline, c'est le même travail découpé
  en étapes qui lisent des fichiers, en écrivent d'autres, et donnent le même résultat à chaque
  exécution. Et avant tout modèle, deux réflexes : une ligne de base, et aucune fuite de données.
objectives:
  - Découper un projet de machine learning en étapes avec des entrées et des sorties explicites
  - Énoncer six règles de conception d'un pipeline reproductible
  - Comparer un modèle à une ligne de base et expliquer pourquoi l'exactitude trompe
  - Découper les données dans le temps et repérer une fuite de données
---

{#notebook-pipeline}
## Du notebook au pipeline

**Pourquoi ?** Un notebook est parfait pour explorer : on essaie, on revient en arrière, on relance une cellule sur deux. C'est aussi son défaut. Six mois plus tard, personne ne sait dans quel ordre les cellules ont été exécutées, ni avec quel fichier. Le modèle « qui marchait » ne se refait plus.

**L'analogie de la chaîne de montage.** Dans un atelier, chaque poste reçoit une pièce, fait **une** opération, et passe la pièce au poste suivant. Si une pièce est défectueuse, on sait à quel poste regarder. Et l'on peut refaire la même pièce demain, à l'identique. Un pipeline de données est une chaîne de montage : chaque **étape** reçoit des fichiers, fait une opération, et écrit des fichiers pour l'étape suivante.

::: figure pipeline-colisvert.svg
Le pipeline de ColisVert, que vous allez construire dans le TP de 11 h 15 : trois étapes, des fichiers entre elles, des paramètres à part, et un serveur MLflow qui garde la trace de chaque exécution.
:::

{#etapes}
## Les étapes d'un pipeline de machine learning

Un pipeline complet en production enchaîne en général huit étapes. Ce matin, on construit les trois du milieu ; les autres arrivent dans la semaine.

| Étape | Ce qu'elle fait | Chez ColisVert | Quand |
|---|---|---|---|
| Ingestion | Récupérer les nouvelles données | Le fichier des expéditions de la veille | Jour 3 (Airflow) |
| Validation | Contrôler leur qualité | Le rapport de qualité d'hier | Jour 1, puis jour 4 |
| **Préparation** | Construire les jeux d'entraînement et de test | `pipeline/prepare.py` | **Ce matin** |
| **Entraînement** | Apprendre le modèle | `pipeline/train.py` | **Ce matin** |
| **Évaluation** | Mesurer le modèle sur des données jamais vues | `pipeline/evaluate.py` | **Ce matin** |
| Enregistrement | Ranger le modèle validé dans un registre | Le registre MLflow | Cet après-midi |
| Déploiement | Le rendre utilisable | Un service qui répond aux prédictions | Cet après-midi, puis jour 4 |
| Surveillance | Détecter la dérive | Evidently | Cet après-midi |

{#regles}
## Six règles de conception

| Règle | Pourquoi | Chez ColisVert |
|---|---|---|
| **1. Une étape, une responsabilité** | Une erreur se localise en une étape, et une étape se teste seule | `prepare.py` ne fait que découper, `train.py` qu'entraîner |
| **2. Des entrées et des sorties explicites** | Ce qui n'est pas écrit dans un fichier n'existe pas pour l'étape suivante : pas d'état caché en mémoire | `prepare` écrit `data/prepared/train.csv` et `test.csv`, `train` les relit |
| **3. Déterministe** | Relancer donne exactement le même résultat, donc on peut comparer | Données générées avec une graine, `random_state=2026` dans le modèle |
| **4. Idempotente** | Relancer une étape deux fois ne double rien : on **remplace** la sortie, on ne l'ajoute pas | Les fichiers de sortie sont réécrits en entier |
| **5. Paramètres hors du code** | Changer un réglage ne demande pas de toucher au code, et le réglage est versionné | `params.yaml` : date de coupure, `C`, `class_weight` |
| **6. Aucune fuite de données** | Le modèle ne doit utiliser que ce qu'on sait **au moment de prédire** | Pas de `delai_reel_h` : on ne le connaît qu'à la livraison |

Les règles 3 et 4 sont souvent confondues. **Déterministe** : mêmes entrées, même sortie. **Idempotente** : l'exécuter une fois ou dix fois laisse le même état. Une étape qui ajoute ses lignes à la fin d'une table à chaque exécution peut être déterministe, mais elle n'est pas idempotente : relancée deux fois, elle crée des doublons. C'est une cause classique de lignes en double, comme les 25 du fichier brut d'hier.

{#ligne-de-base}
## D'abord, une ligne de base

**Pourquoi ?** Un chiffre seul ne veut rien dire. « 90 % de bonnes réponses », c'est beaucoup ou peu ? Tout dépend de ce qu'on obtiendrait **sans modèle**. Cette référence s'appelle la **ligne de base** (*baseline*).

:::: lab Démo | Découper dans le temps et mesurer la ligne de base | 8 min
Dans votre notebook `j2-matin.ipynb`, chargez les livraisons et découpez-les **dans le temps** : on entraîne sur le passé (avant le 19 octobre), on teste sur les deux semaines suivantes. `ajouter_jour_semaine` ajoute la colonne `jour_semaine` (lundi, mardi…), calculée à partir de la date.

```python title="Cellule 2 : les données, découpées dans le temps"
import pandas as pd
from colisvert.donnees import DOSSIER_DATA, preparer_donnees
from pipeline.commun import CATEGORIELLES, CIBLE, NUMERIQUES, ajouter_jour_semaine

preparer_donnees()
livraisons = ajouter_jour_semaine(pd.read_csv(DOSSIER_DATA / "livraisons.csv"))

train = livraisons[livraisons["date_expedition"] < "2026-10-19"]
test = livraisons[livraisons["date_expedition"] >= "2026-10-19"]
print(f"train : {len(train)} colis, du {train['date_expedition'].min()} au {train['date_expedition'].max()}")
print(f"test  : {len(test)} colis, du {test['date_expedition'].min()} au {test['date_expedition'].max()}")
print(f"en retard : {train[CIBLE].mean():.1%} (train), {test[CIBLE].mean():.1%} (test)")
```

```plaintext title="Sortie attendue"
livraisons.csv : 5035 colis, dont 862 en retard
arrivees.csv : 56 jours
livraisons_brutes.csv : les mêmes colis, avec des défauts de qualité
train : 3805 colis, du 2026-09-07 au 2026-10-18
test  : 1230 colis, du 2026-10-19 au 2026-11-01
en retard : 17.2% (train), 16.9% (test)
```

La ligne de base la plus simple : **prédire que tous les colis arrivent à l'heure**.

```python title="Cellule 3 : la ligne de base « toujours à l'heure »"
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score

toujours_a_l_heure = [0] * len(test)
print("exactitude :", round(accuracy_score(test[CIBLE], toujours_a_l_heure), 3))
print("rappel     :", round(recall_score(test[CIBLE], toujours_a_l_heure), 3))
```

```plaintext title="Sortie attendue"
exactitude : 0.831
rappel     : 0.0
```

**83,1 % de bonnes réponses, sans rien apprendre**, et pas un seul client prévenu. Voilà pourquoi l'**exactitude** (*accuracy*) trompe quand une classe est rare : il faut regarder le rappel et la précision.
::::

{#premier-modele}
## Un premier modèle

Le modèle de ColisVert est une **régression logistique** : elle calcule, pour chaque colis, une probabilité de retard à partir d'un score pondéré de ses caractéristiques. Avant, il faut préparer les variables :

- les variables **catégorielles** (entrepôt, client, créneau, météo, jour) deviennent des colonnes 0 ou 1, une par valeur : c'est l'**encodage un-parmi-n** (*one-hot*) ;
- les variables **numériques** (distance, poids, délai promis) sont **standardisées** : on leur retire leur moyenne et on les divise par leur écart-type, pour qu'elles aient toutes la même échelle.

**Pourquoi standardiser ?** La distance va jusqu'à 300 km, le poids jusqu'à 30 kg. Sans mise à l'échelle, l'algorithme qui cherche les poids du score avance à pas minuscules dans certaines directions et à grands pas dans d'autres : il lui faut des centaines d'itérations, et il s'arrête à un résultat qui varie au millième selon le processeur de la machine. Nous l'avons constaté en préparant ce cours : deux machines donnaient deux F1 différents. Standardisées, toutes les variables pèsent sur la même échelle : l'algorithme converge en une vingtaine d'itérations, et tout le monde obtient exactement les mêmes chiffres.

La fonction `construire_modele` du dépôt assemble les deux préparations et la régression dans un seul objet scikit-learn.

:::: lab Démo | Entraîner, puis lire la matrice de confusion | 7 min
```python title="Cellule 4 : un premier modèle"
from pipeline.train import construire_modele

X_COLS = CATEGORIELLES + NUMERIQUES
modele = construire_modele(C=1.0, class_weight=None, max_iter=1000)
modele.fit(train[X_COLS], train[CIBLE])
predictions = modele.predict(test[X_COLS])

for nom, fonction in [("exactitude", accuracy_score), ("precision", precision_score),
                      ("rappel", recall_score), ("f1", f1_score)]:
    print(f"{nom:<10} : {fonction(test[CIBLE], predictions):.3f}")
```

```plaintext title="Sortie attendue"
exactitude : 0.897
precision  : 0.745
rappel     : 0.591
f1         : 0.660
```

Le tableau des erreurs, la **matrice de confusion**, dit d'où viennent ces chiffres :

```python title="Cellule 5 : la matrice de confusion"
print(pd.crosstab(test[CIBLE], predictions, rownames=["réel"], colnames=["prédit"]))
```

```plaintext title="Sortie attendue"
prédit    0    1
réel
0       980   42
1        85  123
```

Lisez-la ligne par ligne :

- **208 colis** sont réellement en retard (ligne `1`) : le modèle en attrape **123** et en manque **85**. Rappel : 123 / 208 = **0,591**.
- **165 colis** sont signalés en retard (colonne `1`) : **123** le sont vraiment, **42** sont de fausses alertes. Précision : 123 / 165 = **0,745**.
- Le **F1** combine les deux en une seule note (leur moyenne harmonique) : **0,660**.

Comparé au critère de succès de la charte (rappel ≥ 0,80 et précision ≥ 0,50), ce premier modèle est **trop prudent** : peu de fausses alertes, mais 4 retards sur 10 passent inaperçus. On l'améliorera cet après-midi.
::::

{#fuite}
## Le piège n° 1 : la fuite de données

**Une fuite de données** (*data leakage*), c'est donner au modèle, pendant l'entraînement, une information qu'il **n'aura pas** au moment de prédire. Le modèle paraît excellent en test, puis s'effondre en production.

:::: lab Démo | Un modèle « parfait » | 4 min
Ajoutons `delai_reel_h`, le délai réel de livraison, aux variables :

```python title="Cellule 6 : un modèle qui triche"
avec_fuite = X_COLS + ["delai_reel_h"]
tricheur = construire_modele(C=1.0, class_weight=None, max_iter=1000, numeriques=NUMERIQUES + ["delai_reel_h"])
tricheur.fit(train[avec_fuite], train[CIBLE])
predictions_tricheur = tricheur.predict(test[avec_fuite])
print("exactitude :", round(accuracy_score(test[CIBLE], predictions_tricheur), 3))
print("f1         :", round(f1_score(test[CIBLE], predictions_tricheur), 3))
```

```plaintext title="Sortie attendue"
exactitude : 0.996
f1         : 0.988
```

**Un score presque parfait doit toujours inquiéter.** 1 225 colis sur 1 230 bien classés : le modèle a simplement appris que « en retard » veut dire « délai réel nettement supérieur au délai promis ». Or, au moment de l'expédition, le délai réel est inconnu : ce modèle est inutilisable. L'option `numeriques` de `construire_modele` permet d'ajouter la colonne aux variables numériques standardisées.
::::

Les fuites réelles sont rarement aussi visibles. Trois formes fréquentes :

| Forme | Exemple | Le réflexe |
|---|---|---|
| **Une variable du futur** | Le délai réel, la date de réclamation du client | Pour chaque variable, demander : « la connaît-on au moment de prédire ? » |
| **Le futur dans l'entraînement** | Un découpage aléatoire mélange des colis du 1er novembre dans l'entraînement et du 7 septembre dans le test | Découper dans le temps, comme ici |
| **Une préparation calculée sur tout le fichier** | Une moyenne, une normalisation ou un encodage appris sur train **et** test | Apprendre la préparation sur le train seulement : c'est ce que fait le `Pipeline` scikit-learn de `construire_modele` |

::: callout tip Question fréquente : « Pourquoi ne pas découper au hasard, comme dans les tutoriels ? »
Parce qu'en production, on prédit toujours **le futur à partir du passé**. Un découpage aléatoire laisse le modèle « voir » des jours postérieurs à ceux qu'il doit prédire : s'il s'est passé quelque chose de particulier une semaine donnée (une grève, une tempête), le modèle l'aura appris pour le test aussi. Le découpage temporel reproduit les conditions réelles, et donne une estimation honnête.
:::

{#avance}
## Pour aller plus loin : idempotence, partitions et contrats entre étapes

Ce bloc est pour les profils avancés ; rien ici n'est exigé dans l'évaluation.

**L'ingénierie des données « fonctionnelle ».** Une approche popularisée par Maxime Beauchemin, le créateur d'Airflow, applique aux pipelines les idées de la programmation fonctionnelle : chaque tâche est une **fonction pure** de ses entrées, et chaque exécution **écrase une partition entière** (par exemple, la journée du 18 octobre) au lieu d'ajouter des lignes. Conséquences : relancer le traitement d'un jour passé (un *backfill*) est sans danger, et l'historique se recalcule à l'identique. C'est la règle 4 portée à l'échelle d'un entrepôt de données.

**Les contrats entre étapes.** Hier, vous avez écrit un contrat de données pour le fichier brut. Le même principe s'applique **entre deux étapes** du pipeline : `train` attend de `prepare` des colonnes précises, sans valeur manquante, avec une cible à 0 ou 1. Vérifier ce contrat **au début** de chaque étape transforme une erreur obscure (une régression qui échoue sur une colonne de texte) en message clair (« colonne meteo absente du fichier train.csv »). En production, c'est ce qui fait la différence entre trente secondes et trois heures de diagnostic à 6 h du matin.

**Le décalage entre entraînement et service** (*training-serving skew*). La préparation des données est souvent écrite deux fois : en Python pour l'entraînement, puis réécrite par une autre équipe pour la production (en Java, en SQL…). Les deux versions divergent un jour, en silence, et le modèle reçoit en production des données qui ne ressemblent pas à celles de l'entraînement. Le remède est celui que vous utilisez : **la préparation fait partie du modèle** (le `Pipeline` scikit-learn contient l'encodage), et le même objet sert à l'entraînement et à la prédiction.

**Les fuites subtiles des séries temporelles.** Même avec un découpage temporel, une variable construite avec une **fenêtre glissante** (« taux de retard de l'entrepôt sur les 7 derniers jours ») fuit si la fenêtre inclut le jour même ou des colis pas encore livrés au moment de prédire. La règle : chaque variable se calcule « en date de » l'instant de la prédiction (*point-in-time correctness*). Les magasins de variables (*feature stores*) existent en grande partie pour garantir cela.

{#quiz}
## Quiz de validation

```quiz
- q: Un modèle qui répond toujours « à l'heure » obtient 83,1 % d'exactitude sur le test. Qu'en conclut-on ?
  options:
    - Que c'est un bon modèle
    - Que l'exactitude seule trompe quand une classe est rare, et qu'il faut regarder rappel et précision
    - Qu'il faut supprimer les colis en retard du test
    - Que la régression logistique est inutile
  answer: 1
  explain: C'est la ligne de base. Elle ne prévient aucun client - son rappel est nul.
- q: Pourquoi delai_reel_h ne doit-il pas être une variable du modèle ?
  options:
    - Parce qu'il contient des valeurs manquantes
    - Parce qu'il n'est connu qu'à la livraison, pas au moment de prédire
    - Parce que c'est un nombre décimal
    - Parce qu'il rend le modèle trop lent
  answer: 1
  explain: C'est une fuite de données. Le modèle obtient un score parfait en test et serait inutilisable en production.
- q: Une étape ajoute ses résultats à la fin d'une table à chaque exécution. Relancée deux fois, elle crée des doublons. Quelle règle viole-t-elle ?
  options: [Le déterminisme, L'idempotence, La découpe temporelle, Les paramètres hors du code]
  answer: 1
  explain: Une étape idempotente remplace sa sortie au lieu de l'ajouter. L'exécuter une ou dix fois laisse le même état.
- q: Le modèle signale 165 colis, dont 123 sont réellement en retard. Que vaut la précision ?
  options: ["0,591", "0,660", "0,745", "0,897"]
  answer: 2
  explain: 123 / 165 = 0,745. Le rappel, lui, vaut 123 / 208 = 0,591.
```
