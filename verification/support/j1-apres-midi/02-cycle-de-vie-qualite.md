---
subtitle: >-
  Une donnée naît, vit, sert, puis disparaît. À chaque étape, la gouvernance fixe des règles,
  et la qualité se mesure : pas « à l'œil », mais avec des contrôles chiffrés.
objectives:
  - Décrire les sept étapes du cycle de vie d'une donnée
  - Dire quelle règle de gouvernance s'applique à chaque étape
  - Citer six dimensions de la qualité des données
  - Écrire un contrôle chiffré pour l'unicité, la complétude, la validité et la cohérence
  - Produire un rapport de qualité
---

{#cycle}
## Le cycle de vie d'une donnée

**Pourquoi parler de cycle de vie ?** Parce que les problèmes d'une donnée apparaissent à une étape précise, et que les règles changent d'une étape à l'autre : on ne protège pas une donnée de la même façon quand on la collecte et quand on l'archive.

| Étape | Ce qui se passe | Chez ColisVert | La règle de gouvernance |
|---|---|---|---|
| **1. Créer, collecter** | La donnée naît dans un processus | Le scanner enregistre la livraison | Ne collecter que le nécessaire (minimisation, RGPD) |
| **2. Stocker** | On la range | Le fichier des expéditions arrive dans le lac | Où, en quel format, avec quelle sauvegarde |
| **3. Traiter** | On la nettoie, on la transforme | Le pipeline calcule le retard | Des contrôles de qualité à chaque passage |
| **4. Utiliser** | Elle sert à décider | Le tableau de bord des retards | Une définition officielle, au glossaire |
| **5. Partager** | D'autres en profitent | Le service client consulte l'historique | Qui a le droit de voir quoi |
| **6. Archiver** | On la garde sans l'utiliser | Les livraisons de l'an dernier | Pendant combien de temps |
| **7. Détruire** | On l'efface | Les adresses des anciens clients | Effacer à la fin de la durée de conservation |

::: callout info Gouvernance et RGPD
Pour les données personnelles (le nom ou l'adresse d'un client), le RGPD impose notamment de ne collecter que le nécessaire et de fixer une **durée de conservation**. C'est la gouvernance qui transforme ces obligations en règles concrètes, étape par étape.
:::

{#dimensions}
## Six dimensions de la qualité

« Ces données sont de mauvaise qualité » ne permet pas d'agir. On découpe la qualité en **dimensions**, chacune mesurable par un contrôle.

| Dimension | La question | Un contrôle chez ColisVert |
|---|---|---|
| **Unicité** | Chaque colis apparaît-il une seule fois ? | Compter les lignes en double |
| **Complétude** | Les valeurs attendues sont-elles là ? | Compter les météos et les poids manquants |
| **Validité** | Les valeurs respectent-elles les règles ? | Entrepôt dans la liste, date au bon format, délai positif |
| **Cohérence** | Les valeurs sont-elles d'accord entre elles ? | `en_retard` doit valoir 1 exactement quand le délai réel dépasse le délai promis |
| **Exactitude** | Les valeurs sont-elles vraies ? | Comparer à une source de référence, par exemple le scanner du livreur |
| **Fraîcheur** | Les données sont-elles à jour ? | Le fichier est arrivé avant 7 h (ce matin, notion 5) |

Les quatre premières se contrôlent avec le fichier seul. L'exactitude demande une **autre source**, et la fraîcheur une **heure de référence**.

{#controles}
## Contrôler le fichier brut

`livraisons_brutes.csv` contient les mêmes colis que ce matin, tels qu'ils arrivent vraiment du système des entrepôts. Contrôlons-le, dimension par dimension.

:::: lab Démo | Quatre dimensions, cinq contrôles | 12 min
**Unicité.** `duplicated()` marque chaque ligne identique à une ligne déjà vue ; `sum()` compte les `True`.

```python title="Cellule 3 : unicité"
print("Lignes en double     :", brutes.duplicated().sum())
print("Identifiants répétés :", brutes["id_colis"].duplicated().sum())
```

```plaintext title="Sortie attendue"
Lignes en double     : 25
Identifiants répétés : 25
```

25 lignes en double, et 25 identifiants répétés : ce sont les mêmes. Une coupure réseau a fait renvoyer un lot de lignes. C'est l'origine des 25 lignes en trop de la Cellule 1.

**Complétude.** `isna()` repère les valeurs manquantes ; on n'affiche que les colonnes concernées.

```python title="Cellule 4 : complétude"
manquants = brutes.isna().sum()
print(manquants[manquants > 0])
```

```plaintext title="Sortie attendue"
poids_kg    15
meteo       40
dtype: int64
```

**Validité.** Trois règles : l'entrepôt est l'un des quatre connus, la date s'écrit `aaaa-mm-jj`, le délai réel n'est pas négatif. `isin` teste l'appartenance à une liste, `~` inverse le résultat, et `str.fullmatch` vérifie qu'un texte suit exactement un motif (`\d{4}` signifie « quatre chiffres »).

```python title="Cellule 5 : validité"
ENTREPOTS = ["Lille", "Lyon", "Nantes", "Toulouse"]

entrepot_inconnu = ~brutes["entrepot"].isin(ENTREPOTS)
date_invalide = ~brutes["date_expedition"].str.fullmatch(r"\d{4}-\d{2}-\d{2}")
delai_negatif = brutes["delai_reel_h"] < 0

print("Entrepôt inconnu  :", entrepot_inconnu.sum(), list(brutes.loc[entrepot_inconnu, "entrepot"].unique()))
print("Date mal écrite   :", date_invalide.sum(), list(brutes.loc[date_invalide, "date_expedition"].head(2)))
print("Délai négatif     :", delai_negatif.sum())
```

```plaintext title="Sortie attendue"
Entrepôt inconnu  : 12 ['Lile']
Date mal écrite   : 20 ['07/09/2026', '08/09/2026']
Délai négatif     : 8
```

Une faute de frappe (`Lile`), un autre format de date, et des délais impossibles : un colis ne peut pas arriver avant d'être parti.

**Cohérence.** On recalcule le retard à partir des délais, puis on compare à la colonne `en_retard`. `astype(int)` transforme `True` et `False` en 1 et 0.

```python title="Cellule 6 : cohérence"
retard_recalcule = (brutes["delai_reel_h"] > brutes["delai_promis_h"]).astype(int)
incoherent = brutes["en_retard"] != retard_recalcule
print("en_retard contredit les délais :", incoherent.sum())
```

```plaintext title="Sortie attendue"
en_retard contredit les délais : 10
```
::::

{#rapport}
## Un rapport de qualité

Des contrôles éparpillés dans un notebook ne servent qu'une fois. On les regroupe dans **une fonction**, qu'un pipeline pourra exécuter à chaque nouveau fichier. C'est le principe que le manifeste DataOps appelle « commencer par tester les données ».

:::: lab Démo | Une fonction, un tableau | 5 min
Chaque contrôle est un triplet : la dimension, le nom du contrôle, et une série de `True` / `False` (une valeur par ligne). La fonction compte les lignes en défaut et calcule leur pourcentage.

```python title="Cellule 7 : le rapport de qualité"
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
```

```plaintext title="Sortie attendue"
 dimension                       controle  lignes  pct
   Unicité                ligne en double      25 0.49
Complétude                météo manquante      40 0.79
Complétude                 poids manquant      15 0.30
  Validité               entrepôt inconnu      12 0.24
  Validité    date hors format aaaa-mm-jj      20 0.40
  Validité             délai réel négatif       8 0.16
 Cohérence en_retard contredit les délais      10 0.20
```

**Lecture :** 130 défauts sur 5 060 lignes. Chaque contrôle touche moins de 1 % des lignes : on pourrait croire que ce n'est rien. Pourtant, les 25 doublons gonflent le nombre de colis, les 10 incohérences faussent le taux de retard, et les 12 « Lile » disparaissent des chiffres de Lille. Vous nettoierez ce fichier pendant l'évaluation.
::::

::: callout tip Question fréquente : « Pourquoi ne pas corriger directement dans le fichier ? »
Parce qu'on perdrait la trace de ce qui a été changé, et que le même défaut reviendra demain. On garde le fichier brut intact, on écrit les corrections **dans le code**, et on produit un nouveau fichier propre. Le pipeline peut alors refaire exactement le même nettoyage chaque nuit.
:::

{#avance}
## Pour aller plus loin : du rapport de qualité au contrat de données

Ce bloc est pour les profils avancés ; rien ici n'est exigé dans l'évaluation.

**Le rapport de qualité constate ; le contrat de données engage.** Un **contrat de données** (*data contract*) est un accord écrit entre l'équipe qui **produit** un jeu de données (ici, le système des entrepôts) et celles qui le **consomment** : schéma, règles de validité, fraîcheur promise, procédure en cas de changement. Comme un contrat d'interface entre deux logiciels, il déplace la responsabilité **en amont** : un fichier qui viole le contrat est refusé à l'entrée, au lieu d'être nettoyé en silence à chaque étape aval.

Le contrat s'écrit dans un format lisible par une machine, pour être **vérifié automatiquement**. Écrivons celui des livraisons et son vérificateur :

```python title="Cellule bonus C : un contrat de données exécutable"
CONTRAT = {
    "id_colis": {"unique": True},
    "entrepot": {"valeurs": ["Lille", "Lyon", "Nantes", "Toulouse"]},
    "date_expedition": {"format": r"\d{4}-\d{2}-\d{2}"},
    "poids_kg": {"obligatoire": True},
    "meteo": {"obligatoire": True},
    "delai_reel_h": {"minimum": 0},
}


def controler_contrat(df, contrat):
    """Vérifie chaque règle du contrat et compte les lignes qui la violent."""
    lignes = []
    for colonne, regles in contrat.items():
        serie = df[colonne]
        if regles.get("unique"):
            lignes.append((colonne, "unique", int(serie.duplicated().sum())))
        if "valeurs" in regles:
            lignes.append((colonne, "valeurs autorisées", int((~serie.isin(regles["valeurs"])).sum())))
        if "format" in regles:
            lignes.append((colonne, "format", int((~serie.str.fullmatch(regles["format"])).sum())))
        if regles.get("obligatoire"):
            lignes.append((colonne, "obligatoire", int(serie.isna().sum())))
        if "minimum" in regles:
            lignes.append((colonne, "minimum", int((serie < regles["minimum"]).sum())))
    return pd.DataFrame(lignes, columns=["colonne", "regle", "violations"])


rapport_contrat = controler_contrat(brutes, CONTRAT)
print(rapport_contrat.to_string(index=False))
print("Contrat respecté :", bool((rapport_contrat["violations"] == 0).all()))
```

```plaintext title="Sortie attendue"
        colonne              regle  violations
       id_colis             unique          25
       entrepot valeurs autorisées          12
date_expedition             format          20
       poids_kg        obligatoire          15
          meteo        obligatoire          40
   delai_reel_h            minimum           8
Contrat respecté : False
```

**Ce qui change par rapport à la Cellule 7 :** le contrat est une **donnée**, pas du code. On peut le publier dans le catalogue, le faire signer au propriétaire des données, le versionner dans Git, et générer les contrôles à partir de lui. Quand le producteur veut renommer une colonne, le contrat force la conversation **avant** la casse, plus la nuit de l'incident.

En production, on n'écrit pas ce vérificateur soi-même : des outils spécialisés portent cette idée, avec des catalogues de règles prêtes à l'emploi et des rapports HTML : **Great Expectations** et **Soda** côté contrôles, **pandera** pour valider des DataFrames dans le code, les **tests dbt** côté entrepôt, et la spécification **Open Data Contract Standard** pour le format du contrat lui-même. Le principe reste exactement celui de cette cellule : des règles déclarées, vérifiées à chaque passage, qui cassent le pipeline **tôt et fort** plutôt que les chiffres **tard et en silence**.

Deux règles d'expérience pour choisir la sévérité :

- **bloquant** quand la règle protège un invariant métier (un délai négatif, un doublon d'identifiant) : mieux vaut un pipeline arrêté qu'un rapport faux ;
- **avertissement** quand la règle mesure une dégradation tolérable (la part de météos manquantes passe de 0,8 % à 1,2 %) : on alerte, on n'arrête pas. Le seuil entre les deux est une décision du **propriétaire des données**, pas de l'ingénieur.

{#quiz}
## Quiz de validation

```quiz
- q: À quelle étape du cycle de vie s'applique la règle « effacer les adresses à la fin de la durée de conservation » ?
  options: [Créer, Utiliser, Partager, Détruire]
  answer: 3
  explain: La destruction est une étape à part entière, encadrée par la gouvernance et le RGPD.
- q: Un entrepôt écrit « Lile » au lieu de « Lille » est un défaut de…
  options: [unicité, complétude, validité, fraîcheur]
  answer: 2
  explain: La valeur ne respecte pas la règle « l'entrepôt fait partie de la liste des quatre entrepôts ».
- q: La colonne en_retard vaut 0 alors que le délai réel dépasse le délai promis. Quelle dimension est touchée ?
  options: [Unicité, Cohérence, Complétude, Fraîcheur]
  answer: 1
  explain: Deux informations du même colis se contredisent.
- q: Quelle dimension ne peut pas se contrôler avec le fichier seul ?
  options: [L'unicité, La complétude, La validité, L'exactitude]
  answer: 3
  explain: Pour savoir si une valeur est vraie, il faut la comparer à une autre source, par exemple le scanner du livreur.
```
