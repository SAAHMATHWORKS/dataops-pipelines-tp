---
subtitle: >-
  L'auditeur interne de ColisVert passe vérifier la plateforme et le modèle avant leur généralisation.
  Il provoque un incident pour voir si l'équipe sait réparer. Il demande qu'une règle de plus soit
  inscrite dans la table, et qu'on lui explique une alerte précise. Enfin, il exige que la fiche du
  produit de données soit conforme aux politiques. Quatre preuves, à la suite de votre notebook.
objectives:
  - Réparer une table Delta après une suppression accidentelle, avec l'historique et RESTORE
  - Inscrire une règle de validité dans une table, et prouver qu'elle bloque une écriture fautive
  - Expliquer la prédiction d'un colis avec SHAP
  - Mettre une fiche de produit de données en conformité avec des politiques vérifiées par du code
# Barème : 14 points pour les étapes (indiqués sur chaque étape) + 6 points pour le QCM
quiz_points: 6
---

{#consignes}
## Consignes

- **Durée :** 35 minutes, en autonomie. Le formateur passe voir chacun.
- **Où :** **à la suite** de votre notebook `j5-matin.ipynb` : l'évaluation réutilise la session Spark, la table `table` (argent), la fonction `tenter`, l'explicateur SHAP et la fiche `PRODUIT`. Si le noyau a redémarré, relancez toutes les cellules (**Run › Run All Cells**).
- **Validation :** chaque étape se termine par une **preuve** : collez la sortie demandée et cliquez sur « Envoyer ma preuve ».
- **Barème :** 14 points pour les 4 étapes, 6 points pour le QCM final (une seule tentative par question).
- Les corrections sont là si vous bloquez, mais essayez d'abord.

::: widget task-progress
:::

{#incident}
## Une suppression accidentelle

:::: task Étape 1 | Réparer la table argent | 8 min | 4 pts
L'auditeur exécute cette cellule, qui supprime par erreur tous les colis livrés sous la pluie :

```python title="Évaluation : l'incident (à exécuter tel quel)"
table.delete("meteo = 'pluie'")
print(f"colis dans la table : {table.toDF().count()}")
```

```plaintext title="Sortie attendue"
colis dans la table : 3495
```

Retrouvez dans l'historique la version d'avant la suppression, revenez-y, et prouvez que la table a retrouvé tous ses colis et tous ses retards.

::: proof Collez la version restaurée, le nombre de colis et le nombre de retards
:::

::: hint
`table.history()` liste les versions et leurs opérations ; la suppression est une opération `DELETE`. `table.restoreToVersion(n)`. Le nombre de retards : `table.toDF().agg(F.sum("en_retard")).first()[0]`.
:::

::: solution
```python title="Évaluation : retour avant le DELETE"
version_delete = max(v.version for v in table.history().collect() if v.operation == "DELETE")
table.restoreToVersion(version_delete - 1)
print(f"restaurée à la version {version_delete - 1} : {table.toDF().count()} colis, "
      f"{table.toDF().agg(F.sum('en_retard')).first()[0]} en retard")
```

```plaintext title="Sortie attendue"
restaurée à la version 7 : 4930 colis, 847 en retard
```

La suppression a créé la version 8 (3 495 colis : les 1 435 colis livrés sous la pluie ont disparu). On revient à la version 7, d'avant la suppression : 4 930 colis et 847 retards, comme à la fin du TP. Si vous avez relancé des cellules, vos numéros de version sont plus élevés. C'est pourquoi la correction cherche la dernière opération `DELETE` dans l'historique au lieu d'écrire un numéro en dur.
:::
::::

{#regle}
## Une règle de plus dans la table

:::: task Étape 2 | Les entrepôts autorisés | 7 min | 3 pts
Le nettoyage de l'étape 3 du TP écarte les entrepôts inconnus, mais rien n'empêche un autre pipeline d'en écrire. Ajoutez à la table argent une contrainte `entrepot_connu`, qui n'accepte que les quatre entrepôts. Prouvez ensuite qu'une écriture avec l'entrepôt « Lile » est refusée.

::: proof Collez le résultat de l'écriture fautive et le nombre de colis de la table
:::

::: hint
Même syntaxe qu'à la Cellule 5, avec `entrepot IN ('Lille', 'Lyon', 'Nantes', 'Toulouse')`. Pour l'écriture fautive, partez d'un colis de la table et changez son entrepôt avec `withColumn`, puis passez l'écriture à `tenter`.
:::

::: solution
```python title="Évaluation : la contrainte entrepot_connu"
spark.sql(f"ALTER TABLE delta.`{ARGENT}` ADD CONSTRAINT entrepot_connu "
          "CHECK (entrepot IN ('Lille', 'Lyon', 'Nantes', 'Toulouse'))")
faute = table.toDF().orderBy("id_colis").limit(1).withColumn("entrepot", F.lit("Lile"))
print("entrepôt « Lile » :", tenter(lambda: faute.write.format("delta").mode("append").save(ARGENT)))
print("colis dans la table :", table.toDF().count())
```

```plaintext title="Sortie attendue"
entrepôt « Lile » : refusée : DELTA_VIOLATE_CONSTRAINT_WITH_VALUES (entrepot_connu)
colis dans la table : 4930
```

La contrainte `entrepot_connu` refuse l'écriture, en bloc, et la table garde ses 4 930 colis. Le nettoyage de l'argent et la contrainte disent la même chose, mais la contrainte vaut pour **tous** les pipelines, présents et futurs.
:::
::::

{#explication}
## Expliquer une alerte

:::: task Étape 3 | Le colis DEC00002 | 10 min | 4 pts
Le client du colis `DEC00002` a reçu un SMS et demande pourquoi. Affichez ses variables et sa probabilité de retard, puis les **trois** variables qui ont le plus pesé (parts SHAP regroupées), avec leur signe. Rédigez en une phrase l'explication à donner au service client.

::: proof Collez la sortie et votre phrase
:::

::: hint
Reprenez la Cellule 12 avec `DEC00002`, et gardez les 3 premières lignes de `parts` (déjà triées par valeur absolue).
:::

::: solution
```python title="Évaluation : pourquoi DEC00002 ?"
colis2 = decembre[decembre["id_colis"] == "DEC00002"]
print(colis2[X_COLS].to_string(index=False))
print(f"probabilité de retard : {champion.predict_proba(colis2[X_COLS])[0, 1]:.3f}")
parts2 = parts_par_variable(colis2).iloc[0].sort_values(key=abs, ascending=False)
for variable, part in parts2.head(3).items():
    print(f"  {variable:<15} {part:+.3f}")
```

```plaintext title="Sortie attendue"
entrepot      client    creneau meteo jour_semaine  distance_km  poids_kg  delai_promis_h
   Lille particulier apres-midi pluie        lundi          150      23.4              24
probabilité de retard : 0.995
  delai_promis_h  +3.853
  meteo           +1.849
  entrepot        +1.263
```

**Probabilité de 0,995.** Trois raisons :
- le délai promis de 24 h (+3,853), alors que le colis est à **150 km**, tout au bout de la tranche des 24 h ;
- la pluie (+1,849) ;
- l'entrepôt de Lille (+1,263).

Contrairement au colis `DEC00001`, la distance ne compense plus rien.

**Phrase pour le service client :** « Votre colis part de Lille un jour de pluie, avec une promesse de livraison en 24 heures sur 150 km : ces trois éléments rendent un retard très probable. »
:::
::::

{#fiche}
## Une fiche conforme

:::: task Étape 4 | Zéro écart aux politiques | 7 min | 3 pts
Corrigez la fiche `PRODUIT` de la notion 1 pour que `verifier` ne trouve **aucun** écart :
- décrivez `creneau` ;
- donnez une durée de conservation à `id_colis` ;
- documentez et classez `en_retard`.

Arrêtez ensuite la session Spark, qui n'est plus utile.

::: proof Collez la sortie de la vérification
:::

::: hint
Modifiez le dictionnaire en place (`PRODUIT["colonnes"]["creneau"]["description"] = …`), ou recopiez-le corrigé. Une durée de conservation est un texte : par exemple « 3 ans après la livraison ».
:::

::: solution
```python title="Évaluation : la fiche mise en conformité"
PRODUIT["colonnes"]["creneau"]["description"] = "Créneau de livraison choisi : matin, après-midi ou soir"
PRODUIT["colonnes"]["id_colis"]["conservation"] = "3 ans après la livraison"
PRODUIT["colonnes"]["en_retard"] = {"description": "1 si le délai réel dépasse le délai promis, sinon 0",
                                    "classification": "interne"}
ecarts = verifier(PRODUIT, colonnes_reelles)
print(f"{len(ecarts)} écart(s) aux politiques")
spark.stop()
```

```plaintext title="Sortie attendue"
0 écart(s) aux politiques
```

En production, la fiche corrigée serait un fichier du dépôt, et la CI rejouerait `verifier` à chaque modification.
:::
::::

{#quiz}
## Quiz de validation

```quiz
- q: Qui doit répondre de la justesse du produit de données « livraisons » ?
  options:
    - L'équipe data, qui écrit les pipelines
    - Son propriétaire, au métier - ici la responsable des opérations
    - Le fournisseur du cloud
    - Le catalogue
  answer: 1
  explain: L'équipe data est dépositaire ; le propriétaire décide de l'usage et arbitre la qualité.
- q: Pourquoi garder une couche bronze, avec les défauts ?
  options:
    - Par obligation légale
    - Pour pouvoir rejouer la couche argent quand une règle change, sans redemander les fichiers
    - Pour les tableaux de bord
    - Pour économiser de la place
  answer: 1
  explain: Le bronze est la preuve de ce qui est arrivé ; l'argent en est une interprétation.
- q: Une écriture viole une contrainte CHECK d'une table Delta. Que se passe-t-il ?
  options:
    - Les lignes fautives sont écartées, les autres écrites
    - Toute l'écriture est refusée, aucune ligne n'entre
    - Les lignes sont écrites avec un avertissement
    - La contrainte est supprimée
  answer: 1
  explain: Une transaction Delta est entière ou n'a pas lieu.
- q: Dans Team Topologies, quelle équipe opère Airflow, MLflow et le lac Delta pour les autres ?
  options:
    - L'équipe alignée sur un flux
    - L'équipe plateforme
    - L'équipe facilitatrice
    - L'équipe sous-système complexe
  answer: 1
  explain: Elle fournit ces services en libre-service et réduit la charge des équipes métier.
- q: Pour un modèle linéaire, à quoi correspond la part SHAP d'une variable ?
  options:
    - À son coefficient seul
    - À son coefficient multiplié par l'écart entre sa valeur et sa valeur moyenne
    - À sa corrélation avec la cible
    - À son nombre de modalités
  answer: 1
  explain: C'est le calcul exact de LinearExplainer avec des variables supposées indépendantes.
- q: Le rappel de Lyon est de 0,760 alors que l'engagement est de 0,80. Que faire en premier ?
  options:
    - Rien, la moyenne tient l'engagement
    - Le noter comme limite dans la fiche du modèle, et en chercher la cause avant de choisir un remède
    - Supprimer Lyon des données
    - Changer de modèle sans analyse
  answer: 1
  explain: Documenter, puis comprendre - données, seuil par entrepôt, variable manquante - avant d'agir.
```
