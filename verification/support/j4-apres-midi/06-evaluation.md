---
subtitle: >-
  L'équipe d'exploitation de ColisVert a quatre questions avant de valider le service. Un modèle peut-il
  tenir dans le terminal des livreurs ? Faut-il promouvoir la forêt, au moins dans un entrepôt ? Que
  se passe-t-il si l'on change le seuil, et peut-on revenir en arrière ? Et combien la mise en ombre
  coûte-t-elle en mémoire ? Quatre réponses, chiffrées, à la suite de votre notebook.
objectives:
  - Choisir un modèle sur un front de Pareto avec un budget de taille
  - Décider d'une promotion, entrepôt par entrepôt, à partir du journal d'un déploiement en ombre
  - Publier une nouvelle version d'un service PyFunc et revenir en arrière avec un alias
  - Chiffrer l'empreinte mémoire et disque d'un service composite
# Barème : 14 points pour les étapes (indiqués sur chaque étape) + 6 points pour le QCM
quiz_points: 6
---

{#consignes}
## Consignes

- **Durée :** 30 minutes, en autonomie. Le formateur passe voir chacun.
- **Où :** **à la suite** de votre notebook `j4-apres-midi.ipynb` : l'évaluation réutilise les résultats du TP 1 (`front_foret`, `finales`) et du TP 2 (`verite`, `signature`). Si le noyau a redémarré, relancez toutes les cellules (**Run › Run All Cells**).
- **Validation :** chaque étape se termine par une **preuve** : collez la sortie demandée et cliquez sur « Envoyer ma preuve ».
- **Barème :** 14 points pour les 4 étapes, 6 points pour le QCM final (une seule tentative par question).
- Les corrections sont là si vous bloquez, mais essayez d'abord.

::: widget task-progress
:::

{#budget}
## Un modèle pour le terminal des livreurs

:::: task Étape 1 | Choisir sous un budget de 150 Ko | 5 min | 3 pts
Le terminal des livreurs peut embarquer un modèle de **150 Ko au plus**, qui doit tenir l'engagement de rappel. Parmi les forêts du front de la Cellule 6, laquelle a le meilleur F1 dans ce budget ? Comparez-la à la régression logistique, puis dites en une phrase lequel des deux vous embarquez.

::: proof Collez la sortie et votre choix
:::

::: hint
Le front est dans `front_foret`, trié par taille ; `essai.values` vaut `(F1, taille)`. Les essais du front sont tous admissibles. La régression logistique est dans `mesures["logistique"]`.
:::

::: solution
```python title="Évaluation : le budget de 150 Ko"
dans_le_budget = [essai for essai in front_foret if essai.values[1] <= 150]
meilleure = max(dans_le_budget, key=lambda essai: essai.values[0])
print(f"meilleure forêt sous 150 Ko : essai {meilleure.number}, F1 {meilleure.values[0]:.3f}, "
      f"{meilleure.values[1]:.1f} Ko")
print(f"régression logistique       : F1 {mesures['logistique']['f1']:.3f}, {mesures['logistique']['taille_ko']:.1f} Ko")
```

```plaintext title="Sortie attendue"
meilleure forêt sous 150 Ko : essai 9, F1 0.573, 135.3 Ko
régression logistique       : F1 0.618, 4.4 Ko
```

La meilleure forêt sous 150 Ko est l'essai 9 (135,3 Ko, F1 0,573). La régression logistique est **plus de 30 fois plus légère et nettement meilleure** (F1 0,618) : c'est elle qu'on embarque. Le budget de 150 Ko n'est même pas une contrainte pour elle.
:::
::::

{#promotion}
## Promouvoir la forêt, entrepôt par entrepôt ?

:::: task Étape 2 | Le journal de l'ombre, par entrepôt | 8 min | 4 pts
La règle de promotion du jour 2 : un challenger remplace le champion s'il fait **au moins 0,01 de F1 de plus**. Calculez, pour chaque entrepôt, le F1 de décembre du champion (servi) et de la forêt (en ombre), et l'écart. Dans quels entrepôts la règle autorise-t-elle la promotion ?

::: proof Collez le tableau et votre décision
:::

::: hint
`verite` (Cellule 16) contient, pour chaque colis, l'entrepôt, le vrai retard (`en_retard`) et les deux décisions (`alerte_servi`, `alerte_ombre`). `verite.groupby("entrepot")`, puis `f1_score` sur chaque groupe.
:::

::: solution
```python title="Évaluation : promotion par entrepôt"
for entrepot, groupe in verite.groupby("entrepot"):
    f1_champion = f1_score(groupe[CIBLE], groupe["alerte_servi"])
    f1_foret = f1_score(groupe[CIBLE], groupe["alerte_ombre"])
    decision = "promouvoir" if f1_foret - f1_champion >= 0.01 else "garder le champion"
    print(f"{entrepot:<9} champion {f1_champion:.3f}  forêt {f1_foret:.3f}  écart {f1_foret - f1_champion:+.3f}  {decision}")
```

```plaintext title="Sortie attendue"
Lille     champion 0.777  forêt 0.761  écart -0.016  garder le champion
Lyon      champion 0.675  forêt 0.663  écart -0.012  garder le champion
Nantes    champion 0.679  forêt 0.672  écart -0.007  garder le champion
Toulouse  champion 0.642  forêt 0.602  écart -0.040  garder le champion
```

La forêt ne gagne **dans aucun entrepôt** : l'écart va de -0,007 (Nantes) à -0,040 (Toulouse). On garde le champion partout. Regarder par entrepôt était quand même nécessaire : un modèle moins bon en moyenne peut être meilleur sur un segment, et c'est exactement ce que permettrait le routage d'un service composite.
:::
::::

{#version}
## Une version 2, et le retour arrière

:::: task Étape 3 | Changer le seuil, puis revenir en arrière | 10 min | 4 pts
Le service client trouve qu'il y a trop d'alertes en décembre. Enregistrez une **version 2** du service, identique à la version 1 sauf le seuil, porté à **0,5**, et déplacez sur elle l'alias `production`. Mesurez le taux d'alertes de décembre avec la version servie (sans ombre, pour ne pas remplir le journal). Puis **revenez** à la version 1 en déplaçant l'alias, et affichez la version qui porte `production`.

::: proof Collez les deux taux d'alertes et la version finale de production
:::

::: hint
Reprenez la Cellule 12 en changeant `model_config`. Chargez `models:/colisvert-service@production` après chaque déplacement d'alias : un modèle chargé ne change pas quand l'alias bouge (jour 2). `params={"ombre": False}`. `client.get_model_version_by_alias("colisvert-service", "production").version`.
:::

::: solution
```python title="Évaluation : version 2, puis retour arrière"
with mlflow.start_run(run_name="service-colisvert-seuil-0.5"):
    info_v2 = mlflow.pyfunc.log_model(
        name="service",
        python_model=str(RACINE / "service" / "colisvert_service.py"),
        artifacts={"champion": "models:/colisvert-empreinte@leger",
                   "challenger": "models:/colisvert-empreinte@foret"},
        model_config={"seuil": 0.5, "journal": str(RACINE / "journal" / "ombre.jsonl")},
        signature=signature,
        input_example=entree,
        registered_model_name="colisvert-service",
    )
lot_decembre = decembre[["id_colis"] + X_COLS]
for version in [info_v2.registered_model_version, info.registered_model_version]:
    client.set_registered_model_alias("colisvert-service", "production", version)
    servi = mlflow.pyfunc.load_model("models:/colisvert-service@production")
    taux = servi.predict(lot_decembre, params={"ombre": False})["retard"].mean()
    print(f"production = version {version} : {taux:.1%} d'alertes en décembre")
print("version finale de production :",
      client.get_model_version_by_alias("colisvert-service", "production").version)
```

```plaintext title="Sortie attendue"
production = version 2 : 36.6% d'alertes en décembre
production = version 1 : 41.9% d'alertes en décembre
version finale de production : 1
```

- Au seuil de 0,5, la version 2 n'alerte plus que pour **36,6 %** des colis de décembre, contre **41,9 %** au seuil de 0,40. On retrouve les 36,6 % du jour 2 : le champion d'alors prédisait au seuil par défaut, 0,5.
- Moins d'alertes, c'est aussi moins de retards attrapés. Ce matin, le seuil de 0,40 était le plus rentable sur octobre : la demande du service client se chiffre, elle ne se décide pas à l'œil.
- **Le retour arrière n'a demandé qu'un déplacement d'alias** : la version 1 sert de nouveau, sans rien réentraîner ni réenregistrer. La version 2 reste dans le registre, prête si la décision change.
:::
::::

{#memoire}
## Combien coûte l'ombre ?

:::: task Étape 4 | L'empreinte du service | 7 min | 3 pts
Le service charge **deux** modèles. Pour chacun (`finales`, Cellule 10), affichez sa taille sérialisée et sa mémoire au chargement, puis le total, et la part de la mémoire qui ne sert qu'à l'ombre. Le service est déployé avec 4 processus : quelle mémoire faut-il prévoir pour les seuls modèles ?

::: proof Collez la sortie et la mémoire pour 4 processus
:::

::: hint
`taille_ko` et `ram_mo` (Cellule 1). `finales[alias][0]` est le modèle entraîné sur tout le train.
:::

::: solution
```python title="Évaluation : l'empreinte du service"
empreinte = {alias: (taille_ko(modele), ram_mo(modele)) for alias, (modele, _) in finales.items()}
for alias, (taille, ram) in empreinte.items():
    print(f"{alias:<5} {taille:>6.1f} Ko  {ram:.2f} Mo")
ram_totale = sum(ram for _, ram in empreinte.values())
print(f"total : {sum(taille for taille, _ in empreinte.values()):.1f} Ko, {ram_totale:.2f} Mo ; "
      f"part de l'ombre : {empreinte['foret'][1] / ram_totale:.0%}")
print(f"4 processus : {4 * ram_totale:.2f} Mo pour les modèles")
```

```plaintext title="Sortie attendue"
leger    4.4 Ko  0.03 Mo
foret  483.1 Ko  0.60 Mo
total : 487.5 Ko, 0.63 Mo ; part de l'ombre : 95%
4 processus : 2.51 Mo pour les modèles
```

Le service pèse 487,5 Ko et occupe 0,63 Mo de mémoire pour ses modèles, dont **95 % pour la forêt en ombre**. Avec 4 processus, il faut prévoir 2,51 Mo. C'est peu, parce que la forêt a été allégée au TP 1 : mettre en ombre la forêt de départ aurait coûté près de 88 Mo pour 4 processus. **L'ombre a un prix**, en mémoire comme en calcul ; on la limite dans le temps, et l'on retire le challenger dès que la décision est prise.
:::
::::

{#quiz}
## Quiz de validation

```quiz
- q: Sur un front de Pareto (F1, taille), un modèle de 135 Ko a un F1 de 0,573 et un autre de 445 Ko un F1 de 0,619. Lequel est le meilleur ?
  options:
    - Celui de 445 Ko, il a le meilleur F1
    - Celui de 135 Ko, il est plus léger
    - Aucun ne domine l'autre - le choix dépend de la contrainte de budget ou de qualité
    - Il faut faire la moyenne
  answer: 2
  explain: Sur le front, chaque gain sur un objectif se paie sur l'autre ; c'est la règle écrite à l'avance qui tranche.
- q: Pourquoi la forêt de départ, à 20 Mo, n'est-elle pas un bon choix, même si son F1 est le plus haut des quatre familles ?
  options:
    - Parce qu'elle est trop lente à entraîner
    - Parce qu'elle ne tient pas la contrainte de rappel, et qu'un modèle cent fois plus léger fait aussi bien
    - Parce que MLflow ne sait pas l'enregistrer
    - Parce qu'une forêt ne peut pas être servie
  answer: 1
  explain: Elle est non admissible (rappel 0,772), et son poids ne lui apporte rien.
- q: Pourquoi mesure-t-on la latence sur la même machine, avec le même lot, pour comparer deux modèles ?
  options:
    - Parce que la latence dépend de la machine, de sa charge et de la taille du lot
    - Parce que c'est plus rapide
    - Parce que la taille du lot n'a pas d'importance
    - Pour avoir des chiffres identiques à ceux du support
  answer: 0
  explain: Une latence n'a de sens qu'en comparaison, dans les mêmes conditions.
- q: Quelle architecture permet de choisir le modèle selon l'entrepôt du colis ?
  options:
    - La répartition du trafic en pourcentages d'Azure Machine Learning
    - Un modèle composite PyFunc qui lit la colonne entrepot
    - Un point d'accès par modèle, choisi au hasard
    - Aucune
  answer: 1
  explain: Seul un composant qui lit la requête peut router selon son contenu.
- q: Après avoir déplacé l'alias production sur la version 2, le service déjà démarré sert...
  options:
    - La version 2, immédiatement
    - Toujours la version qu'il a chargée au démarrage, jusqu'à son redémarrage
    - Une erreur
    - Les deux versions
  answer: 1
  explain: Un modèle est chargé une fois ; c'est la chaîne de déploiement qui redémarre le service quand l'alias bouge.
- q: Le rédacteur de SMS sera remplacé par un LLM au jour 5. Qu'est-ce qui doit rester identique pour que le service ne change pas ?
  options:
    - Le texte exact des messages
    - Le contrat - un colis et sa probabilité en entrée, un texte en sortie
    - La durée d'un appel
    - Le nombre de modèles
  answer: 1
  explain: Avec un contrat stable, on remplace l'implémentation sans toucher au reste, et le gabarit reste disponible comme repli.
```
