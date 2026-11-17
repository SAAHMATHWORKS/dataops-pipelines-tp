---
subtitle: >-
  Tout processus varie : le fichier n'arrive jamais deux fois à la même minute, le taux de retard
  change d'un jour à l'autre. La maîtrise statistique des procédés sépare la variation normale, qu'il
  ne faut pas commenter, du signal qui mérite qu'on s'arrête. On l'applique à l'heure d'arrivée du
  fichier, puis au taux de retard : la dérive de décembre, qu'Evidently avait mesurée au jour 2, est
  ici détectée dès le deuxième jour.
objectives:
  - Distinguer variation commune et variation spéciale, et ce que chacune exige
  - Construire une carte des valeurs individuelles et des étendues mobiles (I-MR)
  - Construire une carte p pour un taux, avec des limites qui dépendent du volume du jour
  - Appliquer les quatre règles de Western Electric et comparer leurs délais de détection
  - Distinguer limites de contrôle, objectif de service et tolérances
---

{#pourquoi}
## Pourquoi une carte de contrôle ?

**Le problème.** Lundi, le taux de retard est de 18 %. Mardi, de 21 %. Faut-il réunir l'équipe ? Si l'on réagit à chaque hausse, on passe ses journées à expliquer du bruit, et l'on finit par **dérégler** le processus en le corrigeant sans raison. Si l'on ne réagit jamais, on rate la vraie dérive.

**L'idée de Walter Shewhart** (Bell Labs, années 1920), reprise par W. Edwards Deming : il y a deux sortes de variation.

| | Variation **commune** | Variation **spéciale** |
|---|---|---|
| D'où elle vient | Du système lui-même : mille petites causes qui s'additionnent | D'une cause précise, extérieure au fonctionnement habituel |
| Exemple chez ColisVert | Les jours de semaine, le taux de retard oscille entre 12 et 24 % | Décembre : colis plus lourds, pluie un jour sur deux |
| Ce qu'il faut faire | **Ne rien commenter** point par point ; pour la réduire, changer le système | **Chercher la cause**, maintenant, pendant que les indices sont frais |
| L'erreur à éviter | Traiter chaque point haut comme un incident | Attendre « pour voir » |

Une **carte de contrôle** trace la mesure dans le temps, avec une ligne centrale et deux **limites de contrôle**, à trois écarts types de part et d'autre. Tant que les points restent entre les limites sans motif particulier, le processus est **stable** (sous contrôle statistique) : sa variation est commune.

C'est le principe 14 du Manifeste DataOps, « L'analytique, c'est de la fabrication », et le principe 16, « Surveiller la qualité et la performance » : des mesures suivies en continu pour **détecter les variations inattendues**.

::: callout warn Trois lignes qu'on confond
- Les **limites de contrôle** sont calculées à partir des données : elles disent ce que le processus **fait**.
- L'**objectif de service** (au jour 1 : fichier avant 7 h, 95 % des jours) est décidé : il dit ce que le client **veut**.
- Les **tolérances** viennent d'un cahier des charges : elles disent ce qui est **acceptable** pour un produit.

Un processus peut être parfaitement stable et ne jamais tenir son objectif : la carte dit alors qu'il faut **changer le système**, pas chasser des coupables.
:::

{#imr}
## Étape 1 : l'heure d'arrivée du fichier (carte I-MR)

Pour une mesure par jour (une heure, un nombre de lignes), on utilise la carte des **valeurs individuelles et des étendues mobiles** (I-MR). L'étendue mobile est l'écart absolu entre deux jours consécutifs ; sa moyenne estime la variation **à court terme**. Les limites sont : **moyenne ± 2,66 × étendue mobile moyenne**. Le facteur 2,66, c'est 3 ÷ 1,128 : il convertit l'étendue mobile en trois écarts types.

:::: lab TP | Étape 1 | Le fichier arrive-t-il de façon stable ? | 10 min
```python title="Cellule 6 : la carte I-MR des heures d'arrivée"
from colisvert.donnees import generer_arrivees

arrivees = pd.DataFrame(generer_arrivees())
heures = arrivees["heure_arrivee"].str.split(":", expand=True).astype(int)
arrivees["minutes"] = heures[0] * 60 + heures[1]
arrivees["etendue_mobile"] = arrivees["minutes"].diff().abs()


def hhmm(minutes):
    m = round(minutes)
    return f"{m // 60:02d}:{m % 60:02d}"


centre = arrivees["minutes"].mean()
em_moyenne = arrivees["etendue_mobile"].mean()
lsc, lic = centre + 2.66 * em_moyenne, centre - 2.66 * em_moyenne
hors = arrivees[(arrivees["minutes"] > lsc) | (arrivees["minutes"] < lic)]
print(f"ligne centrale {hhmm(centre)}, étendue mobile moyenne {em_moyenne:.1f} min")
print(f"limites de contrôle : de {hhmm(lic)} à {hhmm(lsc)}")
print(f"jours hors limites : {len(hors)} ({', '.join(hors['date'].str[5:])})")
```

```plaintext title="Sortie attendue"
ligne centrale 06:33, étendue mobile moyenne 25.0 min
limites de contrôle : de 05:27 à 07:40
jours hors limites : 1 (09-29)
```

**Un seul jour hors limites, alors que 8 jours dépassent 7 h.** Les incidents eux-mêmes gonflent l'étendue mobile (un saut de 06:20 à 07:24, puis le retour, ajoute deux grandes étendues) : les limites s'élargissent jusqu'à 07:40, et la carte devient aveugle à ce qu'elle devrait voir. C'est l'**effet de masque**.

**La parade : une estimation robuste.** On remplace la moyenne par la médiane, et l'étendue mobile moyenne par l'étendue mobile **médiane**, peu sensible aux sauts. Pour deux valeurs consécutives d'une loi normale, la médiane de l'écart vaut 0,954 écart type, d'où σ ≈ étendue mobile médiane ÷ 0,954.

```python title="Cellule 7 : la même carte, estimée de façon robuste"
centre_r = arrivees["minutes"].median()
sigma_r = arrivees["etendue_mobile"].median() / 0.954
lsc_r = centre_r + 3 * sigma_r
hors_r = arrivees[arrivees["minutes"] > lsc_r]
print(f"ligne centrale {hhmm(centre_r)}, sigma {sigma_r:.1f} min, limite haute {hhmm(lsc_r)}")
print(f"jours hors limites : {len(hors_r)} ({', '.join(hors_r['date'].str[5:])})")
print(f"pour mémoire, jours après 7 h : {(arrivees['minutes'] > 7 * 60).sum()}")
```

```plaintext title="Sortie attendue"
ligne centrale 06:30, sigma 17.8 min, limite haute 07:23
jours hors limites : 4 (09-10, 09-15, 09-29, 10-28)
pour mémoire, jours après 7 h : 8
```
::::

**Ce que l'étape 1 enseigne.** Même estimée proprement, la carte ne signale que 4 des 8 jours au-delà de 7 h. Les quatre autres (07:02, 07:04, 07:19, 07:20) restent dans la variation **habituelle** de ce processus : environ un jour sur dix, le système des entrepôts a un incident, et c'est **le fonctionnement normal** du système actuel. Conclusion de Deming : on ne fera pas tenir l'objectif de 7 h en enquêtant jour par jour, mais en **changeant le système** (un export plus robuste en amont, un engagement de service avec l'équipe des entrepôts). C'est une décision de management, pas un incident d'exploitation.

{#carte-p}
## Étape 2 : le taux de retard (carte p)

Pour une **proportion** (colis en retard sur colis expédiés), on utilise la **carte p**. Le taux moyen p̄ est la ligne centrale. L'écart type d'une proportion dépend du nombre de colis du jour : **σ = √(p̄ (1 − p̄) ÷ n)**. Les limites sont donc **plus larges les jours calmes** (le week-end, 30 à 50 colis) que les jours chargés (90 à 130 colis) : un taux de 30 % sur 34 colis n'a pas la même force de preuve qu'un taux de 30 % sur 130.

:::: lab TP | Étape 2 | Septembre-octobre : la période de référence | 10 min
On calcule les limites sur une période où le processus était jugé normal : les 8 semaines de septembre-octobre. C'est la **phase I**.

```python title="Cellule 8 : la carte p de référence"
from colisvert.donnees import generer_livraisons_decembre


def taux_par_jour(lignes):
    jours = pd.DataFrame(lignes).groupby("date_expedition")["en_retard"].agg(colis="size", retards="sum")
    jours = jours.reset_index()
    jours["p"] = jours["retards"] / jours["colis"]
    return jours


base = taux_par_jour(generer_livraisons())
p_barre = base["retards"].sum() / base["colis"].sum()
base["z"] = (base["p"] - p_barre) / (p_barre * (1 - p_barre) / base["colis"]) ** 0.5
base["lsc"] = p_barre + 3 * (p_barre * (1 - p_barre) / base["colis"]) ** 0.5
print(f"septembre-octobre : {len(base)} jours, taux moyen p = {p_barre:.1%}")
print(f"limite haute : de {base['lsc'].min():.1%} (jour le plus chargé) à {base['lsc'].max():.1%} (jour le plus calme)")
print("jours hors limites :")
print(base.loc[base["z"].abs() > 3, ["date_expedition", "colis", "retards", "p", "lsc"]].round(3).to_string(index=False))
```

```plaintext title="Sortie attendue"
septembre-octobre : 56 jours, taux moyen p = 17.1%
limite haute : de 27.0% (jour le plus chargé) à 37.4% (jour le plus calme)
jours hors limites :
date_expedition  colis  retards     p   lsc
     2026-10-10     34       15 0.441 0.365
```

**Un seul jour hors limites en 56 jours** : le samedi 10 octobre, 15 retards sur 34 colis. Avec des limites à trois sigmas, on attend environ une fausse alerte tous les 370 points ; un point isolé sur 56 jours peut être du hasard. Avant d'en faire un incident, on regarde ce jour-là (un samedi pluvieux, une tournée annulée ?). Sans cause trouvée, on le garde dans la référence. Avec une cause identifiée et corrigée, on le retire et on recalcule les limites.
::::

{#regles}
## Étape 3 : décembre, et les règles de Western Electric

Un point au-delà des trois sigmas est un signal fort, mais tardif : une dérive **modérée et durable** peut rester sous la limite pendant des jours. En 1956, le *Statistical Quality Control Handbook* de Western Electric a fixé quatre règles, appliquées d'un côté de la ligne centrale :

| Règle | Signal | Ce qu'elle attrape |
|---|---|---|
| 1 | Un point au-delà de 3 σ | Un choc soudain |
| 2 | 2 points sur 3 consécutifs au-delà de 2 σ, du même côté | Un décalage net |
| 3 | 4 points sur 5 consécutifs au-delà de 1 σ, du même côté | Un décalage modéré |
| 4 | 8 points consécutifs du même côté de la ligne centrale | Un petit décalage durable |

:::: lab TP | Étape 3 | Quand la dérive de décembre est-elle détectée ? | 15 min
**Phase II** : on garde la ligne centrale et la formule des limites de la phase I, et on y place chaque jour de décembre dès qu'il est connu.

```python title="Cellule 9 : les quatre règles, jour après jour"
def regles(z):
    """Les règles de Western Electric (côté haut), évaluées chaque jour sur les points déjà connus."""
    return pd.DataFrame({
        "1 : un point au-delà de 3 sigma": z > 3,
        "2 : 2 points sur 3 au-delà de 2 sigma": (z > 2).astype(int).rolling(3, min_periods=1).sum() >= 2,
        "3 : 4 points sur 5 au-delà de 1 sigma": (z > 1).astype(int).rolling(5, min_periods=1).sum() >= 4,
        "4 : 8 points de suite au-dessus": (z > 0).astype(int).rolling(8).sum() == 8,
    })


dec = taux_par_jour(generer_livraisons_decembre())
dec["z"] = (dec["p"] - p_barre) / (p_barre * (1 - p_barre) / dec["colis"]) ** 0.5
alertes_dec, alertes_base = regles(dec["z"]), regles(base["z"])
print(f"décembre : taux {dec['retards'].sum() / dec['colis'].sum():.1%}, {(dec['z'] > 0).sum()} jours sur {len(dec)} au-dessus de {p_barre:.1%}")
for regle in alertes_dec.columns:
    jours = dec.loc[alertes_dec[regle], "date_expedition"]
    print(f"règle {regle:<38} : 1re alerte {jours.iloc[0] if len(jours) else 'aucune'}, "
          f"{len(jours):>2} jours en alerte (septembre-octobre : {alertes_base[regle].sum()})")
```

```plaintext title="Sortie attendue"
décembre : taux 23.9%, 27 jours sur 28 au-dessus de 17.1%
règle 1 : un point au-delà de 3 sigma        : 1re alerte 2026-12-07,  5 jours en alerte (septembre-octobre : 1)
règle 2 : 2 points sur 3 au-delà de 2 sigma  : 1re alerte 2026-12-01, 18 jours en alerte (septembre-octobre : 0)
règle 3 : 4 points sur 5 au-delà de 1 sigma  : 1re alerte 2026-12-03, 16 jours en alerte (septembre-octobre : 0)
règle 4 : 8 points de suite au-dessus        : 1re alerte 2026-12-14, 14 jours en alerte (septembre-octobre : 0)
```

**Le graphique**, pour le voir d'un coup d'œil :

```python title="Cellule 10 : la carte p, de septembre à décembre"
import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(11, 4))
for jours, couleur in [(base, "tab:blue"), (dec, "tab:red")]:
    dates = pd.to_datetime(jours["date_expedition"])
    sigma = (p_barre * (1 - p_barre) / jours["colis"]) ** 0.5
    ax.plot(dates, jours["p"], "o-", color=couleur, markersize=3, linewidth=1)
    ax.step(dates, p_barre + 3 * sigma, where="mid", color="grey", linewidth=0.8)
    ax.step(dates, (p_barre - 3 * sigma).clip(lower=0), where="mid", color="grey", linewidth=0.8)
ax.axhline(p_barre, color="black", linewidth=0.8)
ax.set_ylabel("taux de retard du jour")
ax.set_title("Carte p : référence septembre-octobre (bleu), décembre (rouge)")
plt.show()
```
::::

**Ce que montrent ces quatre lignes.**

- **La règle 2 alerte dès le 1er décembre**, deuxième jour de données. La règle 1, la seule qu'on applique souvent, attend le **7 décembre** : six jours de plus, soit environ 700 colis dont les clients n'auront pas été prévenus d'un risque accru.
- La règle 4, conçue pour les **petits** décalages durables, n'alerte que le 14 : le 6 décembre, un dimanche à 16,1 %, a interrompu la série. Ici, le décalage est gros : les règles 2 et 3 le voient plus tôt.
- **Sur septembre-octobre, les règles 2, 3 et 4 n'ont donné aucune fausse alerte** ; la règle 1 en a donné une (le 10 octobre). Ajouter les règles de zone accélère la détection sans noyer l'équipe sous les alertes.
- Au jour 2, Evidently mesurait la dérive en comparant **deux mois entiers** ; la carte de contrôle la signale **au fil de l'eau**, jour après jour. Les deux outils se complètent : la carte dit **quand**, Evidently dit **quelles variables** ont bougé (le poids et la météo).

::: callout info Et les agents IA ?
Une carte de contrôle produit une **alerte** ; un humain doit encore réunir le contexte : quelle règle, quels jours, quelles variables ont bougé (le rapport Evidently du jour 2), quels incidents techniques (les journaux d'Airflow du jour 3). C'est une tâche typique pour un **agent IA** : rassembler ces pièces et rédiger une première analyse, que l'équipe vérifie avant de décider. On en verra les bénéfices et les pièges au jour 5. La décision, elle, reste humaine : l'agent prépare, il ne promeut ni ne retire un modèle.
:::

{#production}
## En production : quoi mettre sous contrôle ?

| Mesure | Carte | Où la calculer |
|---|---|---|
| Heure d'arrivée d'un fichier, durée d'une tâche | I-MR | Métadonnées d'Airflow (début et fin des tâches) |
| Nombre de lignes reçues par jour | I-MR | Tâche de contrôle du pipeline, avant l'entraînement |
| Part de valeurs manquantes, de lignes rejetées par le contrat | p | Le contrat de données (jour 3) |
| Taux de retard réel, taux de colis prédits en retard | p | Après l'étiquetage (réel), dès la prédiction (prédit) |
| Erreur moyenne d'un modèle de régression | I-MR | Après l'étiquetage |

Dans un pipeline orchestré, la carte devient une **tâche** : elle calcule le point du jour, applique les règles, et **publie une alerte** (ou échoue, si l'on veut bloquer la suite). Les limites de la phase I sont un **paramètre versionné**, recalculé seulement quand on a décidé que le processus a changé, par exemple après un réentraînement validé.

{#quiz}
## Quiz

```quiz
- q: Le taux de retard passe de 16 % lundi à 21 % mardi, sans sortir des limites ni déclencher de règle. Que faire ?
  options:
    - Réunir l'équipe pour comprendre la hausse
    - Rien de particulier - c'est de la variation commune ; pour la réduire, il faut changer le système
    - Réentraîner le modèle
    - Recalculer les limites
  answer: 1
  explain: Réagir à la variation commune dérègle le processus et épuise l'équipe. On agit sur le système, pas sur un point.
- q: Pourquoi la carte I-MR classique ne voit-elle qu'un jour hors limites sur les heures d'arrivée ?
  options:
    - Parce que les incidents gonflent l'étendue mobile moyenne, donc élargissent les limites
    - Parce que 2,66 est trop petit
    - Parce que les données sont fausses
    - Parce qu'une carte I-MR ne s'applique pas aux heures
  answer: 0
  explain: C'est l'effet de masque. L'estimation robuste (médiane de l'étendue mobile) le réduit.
- q: Pourquoi les limites d'une carte p sont-elles plus larges le week-end ?
  options:
    - Parce qu'il pleut plus
    - Parce qu'il y a moins de colis - une proportion calculée sur peu de colis varie davantage
    - Parce que la ligne centrale change
    - Par convention
  answer: 1
  explain: σ = racine de p̄(1 − p̄)/n ; quand n diminue, σ augmente.
- q: En décembre, quelle règle a détecté la dérive le plus tôt ?
  options:
    - La règle 1, un point au-delà de 3 sigma
    - La règle 2, deux points sur trois au-delà de 2 sigma
    - La règle 4, huit points de suite
    - Aucune
  answer: 1
  explain: Une dérive modérée et durable se voit d'abord par les règles de zone ; le point hors limites arrive plusieurs jours plus tard.
- q: Les limites de contrôle et l'objectif de 7 h, c'est la même chose ?
  options:
    - Oui
    - Non - les limites décrivent ce que fait le processus, l'objectif ce que veut le client
    - Oui, si le processus est stable
    - Non, l'objectif est toujours plus large
  answer: 1
  explain: Un processus peut être stable et ne pas tenir l'objectif ; il faut alors changer le système.
```
