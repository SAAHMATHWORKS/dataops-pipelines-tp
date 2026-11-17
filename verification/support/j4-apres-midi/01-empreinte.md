---
subtitle: >-
  Un modèle n'a pas seulement une qualité, il a un poids. Il occupe du disque pour chaque version,
  de la mémoire tant qu'il est chargé, et du processeur à chaque prédiction. On apprend à mesurer ces
  trois ressources correctement, puis on met face à face quatre familles de modèles sur les colis
  de ColisVert. Le résultat surprend : le plus lourd n'est pas le meilleur.
objectives:
  - Expliquer pourquoi l'empreinte d'un modèle compte - coût, latence, déploiement, énergie
  - Mesurer la taille sérialisée, la mémoire de pointe au chargement et la durée d'une prédiction
  - Rendre une mesure de durée fiable - appel à blanc, répétitions, médiane, même machine
  - Comparer des familles de modèles sur la qualité et sur l'empreinte
---

{#pourquoi}
## Pourquoi l'empreinte compte

**L'analogie de la livraison.** ColisVert ne livre pas une enveloppe avec un semi-remorque. Le camion arriverait aussi, mais il coûte plus cher en carburant, il se gare mal et il roule moins vite en ville. Un modèle surdimensionné, c'est le semi-remorque : il prédit aussi bien, mais il coûte plus cher à chaque trajet.

| Ressource | Ce qu'on mesure | Pourquoi ça coûte |
|---|---|---|
| **Stockage** | La taille du modèle sérialisé (le fichier) | Chaque version est gardée dans le registre ; l'image de service grossit ; le déploiement télécharge le fichier à chaque démarrage |
| **Mémoire** (RAM) | Le pic de mémoire quand on charge le modèle | Le modèle reste en mémoire tant que le service tourne, **une copie par processus** de service : 4 processus, 4 copies |
| **Processeur** (CPU) | La durée d'une prédiction | La page de suivi d'un colis attend la réponse ; sur un lot, la durée se paie en temps de calcul facturé |

S'y ajoutent deux raisons qui ne se voient pas sur la facture :

- **L'énergie.** Le calcul consomme de l'électricité, à chaque prédiction et pendant toute la vie du modèle. Un modèle cent fois plus lourd pour le même résultat est un gaspillage.
- **Les endroits contraints.** Un modèle embarqué dans le terminal du livreur, ou dans une fonction serverless limitée en mémoire, a un budget fixe. Il tient dedans ou il ne sert à rien.

::: callout info Ce que mesure chaque ressource, et ce qu'elle ne mesure pas
La **taille du fichier** ne dit pas tout de la mémoire : un fichier compressé se décompresse au chargement. La **mémoire au chargement** ne dit pas tout du service : pendant une prédiction, les données en entrée et leurs transformations (l'encodage un-parmi-n, par exemple) occupent aussi de la mémoire. La **durée** dépend de la machine, de sa charge et de la taille du lot. On compare donc des modèles **entre eux, sur la même machine, avec le même lot**, jamais des chiffres pris sur des machines différentes.
:::

{#mesurer}
## Mesurer correctement

Trois fonctions suffisent. Chacune mesure une ressource, et chacune a son piège.

- **Le stockage** : on sérialise le modèle avec `joblib` (comme `modele.joblib` dans le pipeline) dans un tampon en mémoire, et l'on compte les octets. C'est **déterministe** : le même modèle donne la même taille, à l'octet près, sur toutes les machines.
- **La mémoire** : le module `tracemalloc`, de la bibliothèque standard de Python, note chaque allocation de mémoire, celles de NumPy comprises. On relève le **pic** pendant le chargement du modèle. À quelques kilo-octets près, le résultat est stable d'une exécution à l'autre.
- **Le processeur** : `time.perf_counter()` est l'horloge la plus précise de Python. Le premier appel d'une fonction est souvent plus lent : il faut charger du code, remplir des caches. On fait donc un **appel à blanc**, puis plusieurs mesures, et l'on garde la **médiane**. Elle ne se laisse pas tirer par une mesure isolée, ralentie par un autre programme.

:::: lab Démo | Trois fonctions de mesure | 5 min
Dans votre notebook `j4-apres-midi.ipynb` :

```python title="Cellule 1 : mesurer la qualité et les trois ressources"
import io
import statistics
import time
import tracemalloc

import joblib
from sklearn.metrics import f1_score, recall_score


def taille_ko(modele):
    """Stockage : la taille du modèle sérialisé avec joblib, en kilo-octets."""
    tampon = io.BytesIO()
    joblib.dump(modele, tampon)
    return len(tampon.getvalue()) / 1024


def ram_mo(modele):
    """Mémoire : le pic de mémoire pendant le chargement du modèle, en mégaoctets."""
    tampon = io.BytesIO()
    joblib.dump(modele, tampon)
    tampon.seek(0)
    tracemalloc.start()
    joblib.load(tampon)
    _, pic = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return pic / 1024**2


def latence_ms(modele, X, repetitions=7):
    """Processeur : la durée médiane d'une prédiction sur tout le lot X, en millisecondes."""
    modele.predict(X)                              # l'appel à blanc
    durees = []
    for _ in range(repetitions):
        debut = time.perf_counter()
        modele.predict(X)
        durees.append(time.perf_counter() - debut)
    return statistics.median(durees) * 1000


def qualite(modele):
    """Entraîne sur les 5 premières semaines, mesure F1 et rappel sur la semaine de validation."""
    modele.fit(entrainement[X_COLS], entrainement[CIBLE])
    predictions = modele.predict(validation[X_COLS])
    return f1_score(validation[CIBLE], predictions), recall_score(validation[CIBLE], predictions)
```

La cellule ne produit pas de sortie : elle définit les outils de l'après-midi.
::::

{#familles}
## Quatre familles face à face

Un collègue a entraîné une **forêt aléatoire de 300 arbres**, sans limite de profondeur, « parce que les forêts gagnent les concours ». C'est le **modèle de départ**. On le compare à trois autres familles, toutes précédées de la même préparation des variables que le pipeline :

| Famille | Idée | Ce qui fait son poids |
|---|---|---|
| **Régression logistique** | Une somme pondérée des variables, transformée en probabilité | Un coefficient par variable encodée : 21 nombres |
| **Arbre de décision** | Une suite de questions (« distance > 150 km ? ») | Le nombre de nœuds, fixé par la profondeur |
| **Forêt aléatoire** | Des centaines d'arbres profonds, chacun appris sur un tirage des colis, qui votent | Arbres × nœuds : des centaines de milliers de nœuds |
| **Boosting de gradient** | Des petits arbres ajoutés un à un, chacun corrigeant les erreurs des précédents | Itérations × feuilles |

:::: lab Démo | Qualité et empreinte de quatre modèles | 8 min
La fonction `avec` remplace la régression logistique du pipeline par un autre estimateur, en gardant l'encodage des variables. La latence se mesure sur le lot de décembre (3 426 colis), comme une prédiction par lots.

```python title="Cellule 2 : quatre familles, cinq mesures"
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier


def avec(estimateur):
    """La préparation des variables du pipeline, suivie de l'estimateur donné."""
    return construire_modele(1.0, None, 1000).set_params(regression=estimateur)


candidats = {
    "forêt de départ": avec(RandomForestClassifier(n_estimators=300, class_weight="balanced",
                                                   random_state=2026, n_jobs=1)),
    "logistique": construire_modele(0.1, "balanced", 1000),
    "arbre": avec(DecisionTreeClassifier(max_depth=6, min_samples_leaf=10, class_weight="balanced",
                                         random_state=2026)),
    "boosting": avec(HistGradientBoostingClassifier(class_weight="balanced", random_state=2026)),
}
mesures = {}
for nom, modele in candidats.items():
    f1, rappel = qualite(modele)
    mesures[nom] = {"f1": round(f1, 3), "rappel": round(rappel, 3), "taille_ko": round(taille_ko(modele), 1),
                    "ram_mo": round(ram_mo(modele), 2), "latence_ms": latence_ms(modele, decembre[X_COLS])}
    m = mesures[nom]
    print(f"{nom:<16} F1 {m['f1']:.3f}  rappel {m['rappel']:.3f}  {m['taille_ko']:>8.1f} Ko  "
          f"{m['ram_mo']:>5.2f} Mo  {m['latence_ms']:.2f} ms")
```

```plaintext title="Sortie attendue"
forêt de départ  F1 0.620  rappel 0.772   20677.2 Ko  21.91 Mo  71.32 ms
logistique       F1 0.618  rappel 0.924       4.4 Ko   0.03 Mo  5.93 ms
arbre            F1 0.560  rappel 0.891      11.7 Ko   0.04 Mo  4.66 ms
boosting         F1 0.603  rappel 0.793     364.4 Ko   0.72 Mo  11.99 ms
```

Les durées (dernière colonne) dépendent de votre VM : les vôtres seront différentes, mais les écarts d'ordre de grandeur resteront (la forêt de départ est de loin la plus lente). Les autres colonnes sont identiques partout.
::::

**Lecture.**

- **La forêt de départ pèse 20 677 Ko, soit 20 Mo**, plus de 4 600 fois la régression logistique (4,4 Ko). Une fois chargée, elle occupe 22 Mo de mémoire, et elle prédit le lot de décembre une dizaine de fois plus lentement. Tout cela pour un F1 de 0,620 contre 0,618 : deux millièmes, soit moins d'un colis bien classé sur les 639 de la semaine.
- **Elle ne tient même pas l'engagement de la charte** : son rappel est de 0,772, sous 0,80. La régression logistique attrape 92 % des retards.
- **Pourquoi un tel poids ?** Une forêt stocke chaque nœud de chaque arbre. 300 arbres sans limite de profondeur, appris sur 3 166 colis, cela fait des centaines de milliers de nœuds. La régression logistique, elle, ne garde que 21 coefficients, plus l'encodage des variables.
- **Le boosting** est intermédiaire (364 Ko, F1 0,603), mais son rappel (0,793) manque lui aussi la barre. **L'arbre** seul est léger et rapide, mais c'est le moins bon (F1 0,560).
- Pour ces modèles, **la mémoire au chargement suit la taille du fichier** : ce qui est stocké est ce qui est chargé.

{#format}
## La taille dépend aussi du format

Le même modèle peut s'écrire de plusieurs façons. `joblib` sait **compresser** : le fichier rapetisse, mais il faut le décompresser à chaque chargement, donc démarrer le service prend un peu plus de temps.

:::: lab Démo | Compresser le fichier | 3 min
```python title="Cellule 3 : le fichier brut et le fichier compressé"
for nom in ["logistique", "forêt de départ"]:
    tampon = io.BytesIO()
    joblib.dump(candidats[nom], tampon, compress=3)
    print(f"{nom:<16} brut {mesures[nom]['taille_ko']:>8.1f} Ko | compressé {len(tampon.getvalue()) / 1024:>7.1f} Ko")
```

```plaintext title="Sortie attendue"
logistique       brut      4.4 Ko | compressé     1.9 Ko
forêt de départ  brut  20677.2 Ko | compressé  3872.2 Ko
```

La compression divise le fichier de la forêt par plus de 5 (de 20 677 à 3 872 Ko). Elle allège le **stockage** et le téléchargement au déploiement, mais pas la **mémoire** : au chargement, le modèle est décompressé, et il occupe toujours 22 Mo. Elle ne change rien non plus à la durée des prédictions. Compresser cache le problème ; seul un modèle plus petit le résout.
::::

::: callout warn MLflow 3.17 n'enregistre plus les modèles scikit-learn avec pickle
Depuis les versions récentes de MLflow, `mlflow.sklearn.log_model` écrit le modèle au format **skops** par défaut, et non plus avec `pickle`. La raison est la sécurité : charger un fichier `pickle` peut **exécuter du code arbitraire**, donc un modèle piégé est une porte d'entrée. skops n'accepte que des types qu'il sait vérifier. Deux conséquences, vérifiées dans l'image des TP :

- **La taille change.** La régression logistique occupe environ 3 Ko en `pickle` et 110 Ko en skops (une archive avec ses métadonnées). Comparez des formats identiques.
- **Les arbres sont refusés par défaut.** Pour un arbre ou une forêt, MLflow s'arrête sur `Untrusted types found in the file: ['sklearn.tree._tree.Tree']` (le boosting est refusé de la même façon, pour un autre type). Il faut déclarer ce type comme fiable (`skops_trusted_types`) : on le fera au TP 1, pour un modèle que l'on a entraîné soi-même.
:::

{#avance}
## Pour aller plus loin : réduire l'empreinte sans changer de modèle

Ce bloc est pour les profils avancés ; rien ici n'est exigé dans l'évaluation.

- **Moins de variables.** Chaque variable supprimée allège l'encodage, la mémoire des lots et la collecte des données en amont. Une analyse d'importance (permutation, jour 5) dit lesquelles ne servent à rien.
- **Des nombres plus courts.** Passer des flottants de 64 bits à 32 bits divise par deux la mémoire des tableaux. La **quantification** va plus loin (8 bits, voire moins) : elle est courante pour les réseaux de neurones et les LLM, et se fait souvent après conversion au format **ONNX**, un format d'échange que des moteurs d'inférence optimisés (ONNX Runtime) exécutent sans Python.
- **La distillation.** Un gros modèle « professeur » étiquette beaucoup de données, et un petit modèle « élève » apprend à l'imiter. C'est ainsi qu'on obtient des versions compactes de grands modèles de langage.
- **Élaguer.** Pour une forêt : moins d'arbres, moins profonds, des feuilles plus grandes. C'est exactement ce que va chercher Optuna au TP 1.

**Mesurer en production.** La latence d'un service se suit en **percentiles** : la médiane (p50) dit l'expérience habituelle, le 95e ou le 99e percentile (p95, p99) dit l'expérience des clients malchanceux. Un service peut avoir une bonne médiane et un p99 catastrophique, par exemple à cause du ramasse-miettes ou d'un lot plus gros que les autres.

{#quiz}
## Quiz

```quiz
- q: Pourquoi faire un appel « à blanc » avant de mesurer la durée d'une prédiction ?
  options:
    - Pour vérifier que le modèle fonctionne
    - Parce que le premier appel est souvent plus lent - chargement de code, caches à remplir - et fausserait la mesure
    - Pour réchauffer le processeur
    - Ce n'est pas utile
  answer: 1
  explain: On mesure le régime de croisière du service, pas son démarrage ; la médiane de plusieurs mesures écarte aussi les mesures isolées.
- q: Un service tourne avec 4 processus de travail. Combien de copies du modèle sont en mémoire ?
  options:
    - Une, partagée
    - Quatre - une par processus
    - Aucune, le modèle est lu sur le disque à chaque requête
    - Deux
  answer: 1
  explain: Chaque processus charge sa propre copie ; un modèle de 20 Mo coûte donc 80 Mo de mémoire, multipliés par le nombre de répliques.
- q: Quelle mesure est identique, à l'octet près, sur toutes les machines ?
  options:
    - La durée d'une prédiction
    - La taille du modèle sérialisé
    - Le pic de mémoire pendant une prédiction sur un lot quelconque
    - Le temps d'entraînement
  answer: 1
  explain: La sérialisation d'un même modèle donne le même fichier ; les durées, elles, dépendent de la machine et de sa charge.
- q: Pourquoi MLflow 3.17 refuse-t-il par défaut d'enregistrer une forêt aléatoire au format skops ?
  options:
    - Parce que les forêts sont trop grosses
    - Parce que skops n'accepte que les types qu'il sait vérifier, et que l'arbre de scikit-learn doit être déclaré fiable explicitement
    - Parce que MLflow ne connaît pas les forêts
    - Parce qu'il faut une licence
  answer: 1
  explain: Un fichier de modèle est du code potentiel ; on ne déclare fiable que ce qu'on a produit soi-même ou vérifié.
```
