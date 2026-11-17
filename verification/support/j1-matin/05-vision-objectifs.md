---
subtitle: >-
  Une vision dit où l'on va. Des objectifs mesurables disent si l'on avance. Et chaque pipeline
  reçoit ses propres engagements, chiffrés, au service de ces objectifs.
objectives:
  - Rédiger une vision courte, ambitieuse et datée
  - Décliner une vision en objectifs et résultats clés (OKR)
  - Traduire un résultat clé en engagements de pipeline (fraîcheur, complétude, exactitude)
  - Mesurer le respect d'un engagement de fraîcheur
---

{#vision}
## Définir la vision

**Pourquoi une vision ?** Sans cap commun, chaque équipe optimise son propre morceau : l'IT veut des serveurs stables, l'exploitation des tournées pleines, le service client moins d'appels. La vision donne **une direction que tout le monde comprend**.

Une bonne vision tient **en une phrase**, elle est **ambitieuse** et **datée**. Elle parle du client ou du métier, pas de technologie.

| Vision trop vague | Vision utilisable |
|---|---|
| « Devenir une entreprise data driven. » | « **D'ici fin 2027, chaque client ColisVert est prévenu d'un retard avant qu'il ne se produise.** » |

La première phrase ne dit ni quoi faire, ni quand on aura réussi. La seconde permet de vérifier.

{#okr}
## Des objectifs mesurables : les OKR

On décline la vision en **objectifs et résultats clés** (*OKR, Objectives and Key Results*) : un objectif qualitatif, et 2 à 4 résultats clés **chiffrés**.

**Objectif :** prévenir les clients avant le retard.

| Résultat clé | Aujourd'hui | Cible fin 2027 |
|---|---|---|
| **RC1.** Taux de retard | 17,1 % | moins de 12 % |
| **RC2.** Part des retards annoncés au client au moins 6 h à l'avance | 0 % | 80 % |
| **RC3.** Jours où les données de la veille sont prêtes avant 7 h | à mesurer | 95 % |

Le RC3 n'intéresse pas directement le client. Il est pourtant **indispensable** : sans données fraîches à 7 h, impossible de prédire les retards du jour et de prévenir les clients le matin.

{#engagements}
## Aligner les pipelines : leurs engagements

**L'analogie :** l'horaire d'un train est une **promesse**. La SNCF mesure sa **ponctualité** : la part des trains arrivés à l'heure. Un pipeline de données aussi fait des promesses, et on les mesure.

Ces promesses s'appellent des **engagements de niveau de service** (*SLO, Service Level Objectives*). Les plus courants pour un pipeline :

| Engagement | La question | Exemple chez ColisVert |
|---|---|---|
| **Fraîcheur** | Les données sont-elles prêtes à temps ? | Le fichier de la veille est arrivé avant 7 h, 95 % des jours |
| **Complétude** | Toutes les données sont-elles là ? | Au moins 99 % des colis expédiés figurent dans le fichier |
| **Exactitude** | Les valeurs sont-elles justes ? | Aucun délai réel négatif, aucun entrepôt inconnu |
| **Disponibilité** | Peut-on consulter le résultat ? | Le tableau de bord répond 99,5 % du temps |

Chaque engagement est relié à un résultat clé : c'est ce qui **aligne le pipeline avec la vision**. Un engagement que personne ne relie à un objectif est un engagement inutile.

:::: lab Démo | Le pipeline tient-il son engagement de fraîcheur ? | 6 min
`arrivees.csv` donne, pour chacun des 56 jours, l'heure d'arrivée du fichier des expéditions de la veille. L'engagement : **avant 7 h, 95 % des jours**.

```python title="Cellule 11 : mesurer la fraîcheur"
arrivees = pd.read_csv(DOSSIER_DATA / "arrivees.csv")
a_l_heure = arrivees["heure_arrivee"] <= "07:00"

print(f"Jours mesurés     : {len(arrivees)}")
print(f"Fichier avant 7 h : {a_l_heure.sum()} jours, soit {a_l_heure.mean():.1%}")
print(f"Engagement 95 %   : au plus {int(len(arrivees) * 0.05)} jours en retard autorisés")
```

```plaintext title="Sortie attendue"
Jours mesurés     : 56
Fichier avant 7 h : 48 jours, soit 85.7%
Engagement 95 %   : au plus 2 jours en retard autorisés
```

Quels sont les jours en retard ? Le `~` inverse la condition : on garde les lignes où `a_l_heure` est faux.

```python title="Cellule 12 : les jours en retard"
print(arrivees[~a_l_heure].to_string(index=False))
```

```plaintext title="Sortie attendue"
      date heure_arrivee
2026-09-10         07:24
2026-09-12         07:02
2026-09-15         07:27
2026-09-29         08:02
2026-10-13         07:19
2026-10-25         07:20
2026-10-28         07:30
2026-10-31         07:04
```

**Lecture :** 85,7 % au lieu de 95 %. L'engagement autorisait **2 jours** de retard sur 56 ; il y en a eu **8**. Ce « droit à l'erreur » s'appelle le **budget d'erreur** : il est dépassé de 6 jours. Tant que ce n'est pas réglé, le RC2 (prévenir les clients le matin) est hors de portée.
::::

::: callout tip Question fréquente : « Pourquoi comparer des heures écrites en texte ? »
`"07:24" > "07:00"` compare les deux textes caractère par caractère, comme l'ordre du dictionnaire. Cela fonctionne **parce que** les heures sont toujours écrites sur deux chiffres (`06:09`, jamais `6:09`). Avec un format irrégulier, il faudrait d'abord convertir en vraies heures.
:::

::: callout remember À retenir
Vision (une phrase) → objectifs et résultats clés (des chiffres) → engagements de chaque pipeline (fraîcheur, complétude, exactitude, disponibilité). Ce qui n'est pas mesuré ne peut pas être tenu.
:::

{#avance}
## Pour aller plus loin : vivre avec un budget d'erreur

Ce bloc est pour les profils avancés ; rien ici n'est exigé dans l'évaluation.

**Un taux global cache le rythme des incidents.** 85,7 % sur 8 semaines, est-ce une mauvaise passe au début, ou un problème chronique ? Les équipes de fiabilité (la discipline s'appelle le **SRE**, *Site Reliability Engineering*, née chez Google) regardent le budget d'erreur **par fenêtre**, avec un indicateur simple : le **taux de combustion** (*burn rate*), c'est-à-dire la vitesse à laquelle on consomme le budget. Un burn de 1 signifie « au rythme exactement autorisé » ; 3, « trois fois trop vite ».

```python title="Cellule bonus B : le budget d'erreur, semaine par semaine"
arrivees["date"] = pd.to_datetime(arrivees["date"])
arrivees["semaine"] = arrivees["date"].dt.isocalendar().week.astype(int)
arrivees["rate"] = (arrivees["heure_arrivee"] > "07:00").astype(int)

par_semaine = arrivees.groupby("semaine")["rate"].agg(["sum", "count"])
par_semaine["taux"] = (par_semaine["sum"] / par_semaine["count"] * 100).round(1)
par_semaine["burn"] = (par_semaine["sum"] / par_semaine["count"] / 0.05).round(1)
print(par_semaine.to_string())
```

```plaintext title="Sortie attendue"
         sum  count  taux  burn
semaine                        
37         2      7  28.6   5.7
38         1      7  14.3   2.9
39         0      7   0.0   0.0
40         1      7  14.3   2.9
41         0      7   0.0   0.0
42         1      7  14.3   2.9
43         1      7  14.3   2.9
44         2      7  28.6   5.7
```

**Lecture :** le problème n'est pas une mauvaise passe, il est **chronique** : six semaines sur huit brûlent le budget au moins trois fois trop vite (burn ≥ 2,9), et aucune tendance à l'amélioration. Conclusion d'expert, contre-intuitive : **ne déclenchez pas une alerte à chaque incident**. Avec un objectif à 95 %, un incident isolé est prévu par le contrat. On alerte sur le **burn** (par exemple : burn ≥ 3 sur 7 jours = ticket ; burn ≥ 10 sur 24 h = réveil), et on dépense le budget restant en toute connaissance : si le mois est déjà « brûlé », on gèle les changements risqués sur ce pipeline.

Deux usages avancés du même outil :

- **Négocier l'objectif.** Si le métier exige 99 % et que l'historique montre 85,7 %, la conversation devient factuelle : quel investissement pour gagner 13 points ? Un objectif qu'on n'a jamais tenu n'est pas un engagement, c'est un vœu.
- **Choisir la fenêtre.** Un budget mensuel pardonne un gros incident isolé ; un budget hebdomadaire détecte vite une dégradation. Beaucoup d'équipes suivent les deux à la fois : une fenêtre courte pour réagir, une longue pour rendre compte.

{#quiz}
## Quiz de validation

```quiz
- q: Laquelle de ces phrases est une vision utilisable ?
  options:
    - « Devenir une entreprise data driven. »
    - « Installer Airflow avant juin. »
    - « D'ici fin 2027, chaque client est prévenu d'un retard avant qu'il ne se produise. »
    - « Avoir plus de données. »
  answer: 2
  explain: Elle tient en une phrase, elle est ambitieuse, datée, et parle du client.
- q: « Le fichier de la veille est arrivé avant 7 h, 95 % des jours. » Quel type d'engagement ?
  options: [Fraîcheur, Complétude, Exactitude, Disponibilité]
  answer: 0
  explain: Il dit si les données sont prêtes à temps.
- q: Sur 56 jours, avec un engagement de 95 %, combien de jours de retard le budget d'erreur autorise-t-il ?
  options: ["0", "2", "5", "8"]
  answer: 1
  explain: 5 % de 56 jours font 2,8 jours, donc au plus 2 jours entiers. ColisVert en a eu 8.
```
