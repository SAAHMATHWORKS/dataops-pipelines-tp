---
subtitle: >-
  La responsable du service client de ColisVert veut mettre le rédacteur de SMS et l'agent d'analyse
  en service. Avant de signer, elle demande trois preuves : un garde-fou de plus sur les SMS, un outil
  de plus pour l'agent, et le classement de quatre projets d'IA de l'entreprise au regard de l'AI Act.
  À la suite de votre notebook.
objectives:
  - Ajouter une règle à un garde-fou, et prouver qu'elle bloque les textes fautifs sans gêner les bons
  - Donner un nouvel outil à un agent, et vérifier qu'il l'utilise et que sa note reste prouvée
  - Classer des systèmes d'IA selon les niveaux de risque de l'AI Act, avec leurs obligations et leurs dates
# Barème : 14 points pour les étapes (indiqués sur chaque étape) + 6 points pour le QCM
quiz_points: 6
---

{#consignes}
## Consignes

- **Durée :** 20 minutes, en autonomie. Le formateur passe voir chacun.
- **Où :** **à la suite** de votre notebook `j5-apres-midi.ipynb` : l'évaluation réutilise `appeler`, `verifier_sms`, `RedacteurLLM`, les outils et la fonction `agent`. Si le noyau a redémarré, relancez toutes les cellules (**Run › Run All Cells**) et recollez votre jeton.
- **Validation :** chaque étape se termine par une **preuve** : collez la sortie demandée et cliquez sur « Envoyer ma preuve ».
- **Barème :** 14 points pour les 3 étapes, 6 points pour le QCM final (une seule tentative par question).
- Les corrections sont là si vous bloquez, mais essayez d'abord.

::: widget task-progress
:::

{#garde-fou}
## Aucun geste commercial

:::: task Étape 1 | Une règle de plus dans le garde-fou | 6 min | 5 pts
Le service client a reçu un SMS qui promettait le remboursement des frais de port : personne ne l'avait décidé. Ajoutez à `verifier_sms` une règle qui refuse tout **geste commercial** (remboursement, gratuité, bon d'achat, dédommagement, cadeau offert). Testez-la sur ces trois textes ; seul le dernier doit être conforme :

```python title="Évaluation : les trois textes à tester (à copier tels quels)"
TEXTES = [
    "ColisVert : votre colis DEC00001 risque d'arriver en retard. Les frais de port vous seront remboursés.",
    "ColisVert : votre colis DEC00001 risque d'arriver en retard. Un bon d'achat de 5 euros vous est offert.",
    "ColisVert : votre colis DEC00001 risque d'arriver en retard. Nous suivons sa livraison.",
]
colis = {"id_colis": "DEC00001", "entrepot": "Lille", "meteo": "pluie"}
```

::: proof Collez le résultat du garde-fou pour les trois textes
:::

::: hint
Redéfinissez `verifier_sms` en entier, avec la nouvelle règle à la fin : `RedacteurLLM` appelle `verifier_sms` à chaque SMS, il utilisera donc la nouvelle version sans rien changer d'autre. Une expression régulière avec `\w*` attrape les variantes : `rembours\w*` couvre « remboursé », « remboursement »…
:::

::: solution
```python title="Évaluation : le garde-fou sans geste commercial"
GESTE = re.compile(r"rembours\w*|gratuit\w*|bon d'achat|dédommag\w*|offert\w*|geste commercial", re.IGNORECASE)


def verifier_sms(sms, colis):
    """La liste des problèmes du SMS ; vide s'il est conforme."""
    problemes = []
    if len(sms) > 160:
        problemes.append(f"{len(sms)} caractères (160 au plus)")
    if colis["id_colis"] not in sms:
        problemes.append("numéro du colis absent")
    promesse = PROMESSE.search(sms)
    if promesse:
        problemes.append(f"promesse : « {promesse.group(0)} »")
    geste = GESTE.search(sms)
    if geste:
        problemes.append(f"geste commercial : « {geste.group(0)} »")
    return problemes


for sms in TEXTES:
    print(verifier_sms(sms, colis) or "conforme")
```

```plaintext title="Sortie attendue"
['geste commercial : « remboursés »']
["geste commercial : « bon d'achat »"]
conforme
```

Le deuxième texte contient deux mots interdits (« bon d'achat » et « offert ») ; le garde-fou signale le premier trouvé, cela suffit pour rejeter le texte. La règle est dans le **code** : la consigne du LLM interdisait déjà tout geste commercial, mais une consigne se contourne, un code ne se contourne pas.
:::
::::

{#outil}
## Un outil de plus pour l'agent

:::: task Étape 2 | Les retards par créneau | 8 min | 5 pts
L'équipe veut savoir si un **créneau de livraison** (matin, après-midi, soir) souffre plus que les autres. Écrivez un outil `retards_par_creneau(jusqu_au)` sur le modèle de `retards_par_entrepot`, ajoutez-le aux outils de l'agent, puis relancez l'agent sur la même question, avec **votre** LLM. Vérifiez l'ancrage de la nouvelle note.

::: proof Collez les outils appelés, la note et le résultat de l'ancrage
:::

::: hint
Trois choses : la fonction (avec sa docstring : c'est la description que lit le LLM), son ajout au dictionnaire `OUTILS`, puis la reconstruction de `SCHEMAS` (copiez la ligne de la Cellule 9). La fonction `agent` lit `OUTILS` et `SCHEMAS` à chaque appel.
:::

::: solution
```python title="Évaluation : l'outil retards_par_creneau"
@mlflow.trace(span_type="TOOL")
def retards_par_creneau(jusqu_au):
    """Taux de retard par créneau de livraison, en décembre (jusqu'à cette date) et en septembre-octobre."""
    dec = _decembre_jusqua(jusqu_au)
    return {creneau: {"reference_pct": round(100 * REFERENCE.loc[REFERENCE["creneau"] == creneau, "en_retard"].mean(), 1),
                      "decembre_pct": round(100 * dec.loc[dec["creneau"] == creneau, "en_retard"].mean(), 1)}
            for creneau in sorted(REFERENCE["creneau"].unique())}


OUTILS["retards_par_creneau"] = retards_par_creneau
SCHEMAS = [{"type": "function", "name": nom, "description": fonction.__doc__, "parameters": ARGUMENTS, "strict": True}
           for nom, fonction in OUTILS.items()]
note2, journal2 = agent(QUESTION, appeler)
print("outils appelés :", [j["outil"] for j in journal2])
print(note2)
print("non prouvés :", non_prouves(note2, journal2) or "aucun")
```

```plaintext title="Sortie avec le LLM simulé"
outils appelés : ['carte_controle', 'derive_variables', 'retards_par_entrepot', 'retards_par_creneau']
Au 2026-12-07, le taux de retard du jour est de 26.4 % pour une référence de 17.1 % ; règles en alerte : règle 1, règle 2, règle 3 (première alerte de décembre : 2026-12-01).
Ce qui a changé depuis septembre-octobre : poids_kg_moyen 15.2 → 19.7, part_pluie_pct 29.0 → 51.5, distance_km_moyenne 151.9 → 152.9, colis_par_jour 89.9 → 119.5.
La plus forte hausse par entrepôt : Lyon, de 12.0 % à 19.8 %.
La plus forte hausse par créneau : apres-midi, de 13.4 % à 22.2 %.
À vérifier par l'équipe : l'effet de la météo et du poids sur les tournées, avant toute décision sur le modèle.
non prouvés : aucun
```

**Ce qui doit rester vrai avec votre LLM :** `retards_par_creneau` fait partie des outils appelés, avec la date du 7 décembre, et la note parle des créneaux. Si l'ancrage signale un nombre non prouvé, dites dans votre preuve d'où il vient (souvent un écart calculé par le LLM).
:::
::::

{#ai-act}
## Quatre projets au regard de l'AI Act

:::: task Étape 3 | Classer et dater | 6 min | 4 pts
ColisVert a quatre projets d'IA. Pour chacun, donnez son **niveau de risque** dans l'AI Act (interdit, haut risque, risque limité, risque minimal), **l'obligation principale** de ColisVert, et **la date** à laquelle elle s'applique.

1. Un **chatbot** sur le site de ColisVert, qui répond aux clients sur le suivi de leur colis.
2. **L'agent du TP**, qui prépare des notes internes pour l'équipe data quand une carte de contrôle alerte.
3. Un système qui **note les livreurs** à partir de leurs tournées, pour décider des primes et des fins de contrat.
4. Des caméras qui **détectent les émotions** des agents de tri pendant leur travail, pour mesurer leur stress.

::: proof Collez vos quatre réponses (niveau, obligation, date)
:::

::: hint
Relisez la notion « Réglementation et éthique » : les pratiques interdites de l'article 5, les domaines à haut risque de l'annexe III (dont l'emploi), l'article 50 sur la transparence, et le calendrier modifié par l'omnibus numérique de 2026.
:::

::: solution
| Projet | Niveau de risque | Obligation principale de ColisVert | Depuis ou à partir du |
|---|---|---|---|
| 1. Chatbot du site | **Risque limité** (transparence) | Informer le client qu'il échange avec une IA (article 50) | 2 août 2026 : déjà applicable |
| 2. Agent d'analyse interne | **Risque minimal** | Aucune obligation propre à l'AI Act ; maîtrise de l'IA du personnel (article 4) et bonnes pratiques : traces, décision humaine | Article 4 : 2 février 2025 |
| 3. Notation des livreurs | **Haut risque** (annexe III, emploi et gestion des travailleurs) | En tant que déployeur : contrôle humain, journaux conservés, information des travailleurs et de leurs représentants, surveillance du fonctionnement | 2 décembre 2027 (date repoussée par l'omnibus numérique) ; le RGPD s'applique déjà, dont l'article 22 sur les décisions automatisées |
| 4. Émotions des agents de tri | **Interdit** (article 5 : reconnaissance des émotions sur le lieu de travail, sauf raison médicale ou de sécurité) | Ne pas le faire | 2 février 2025 |

**Barème :** 1 point par projet, si le niveau est juste et l'obligation ou la date cohérente. Pour le projet 3, accepter aussi « 2 août 2026 » avec la remarque que la date a été repoussée : c'était la date initiale.
:::
::::

{#quiz}
## Quiz de validation

```quiz
- q: Qu'est-ce qui distingue un agent IA d'un assistant ?
  options:
    - L'agent utilise un plus gros modèle
    - L'agent poursuit un objectif en choisissant lui-même ses actions (outils) dans une boucle ; l'assistant répond, et l'humain agit
    - L'assistant est gratuit
    - L'agent ne fait jamais d'erreur
  answer: 1
  explain: Le degré d'autonomie fait la différence, et avec lui le niveau de risque et de contrôle nécessaire.
- q: Pourquoi le TP passe-t-il par une passerelle plutôt que de mettre la clé OpenAI sur les VM ?
  options:
    - Pour aller plus vite
    - Pour garder la clé sur le serveur, imposer le modèle et les plafonds, compter les appels de chacun, et couper l'accès en un geste
    - Parce que requests ne sait pas appeler OpenAI
    - Pour que le LLM soit plus intelligent
  answer: 1
  explain: C'est le schéma d'une passerelle d'IA d'entreprise, comme Azure API Management devant Azure OpenAI.
- q: Quel est le premier risque de la liste OWASP 2026 pour les applications à base de LLM ?
  options:
    - La consommation illimitée
    - L'injection de requête (prompt injection)
    - La chaîne d'approvisionnement
    - La désinformation
  answer: 1
  explain: L'injection reste première ; l'agentivité excessive monte à la troisième place.
- q: Pourquoi la note de l'agent est-elle vérifiée par l'ancrage des chiffres ?
  options:
    - Pour la raccourcir
    - Parce qu'un LLM peut écrire un chiffre plausible mais faux ; seuls les chiffres présents dans les sorties des outils sont prouvés
    - Pour économiser des jetons
    - Parce que l'AI Act l'impose pour tous les systèmes
  answer: 1
  explain: Un chiffre montré à un humain doit venir d'un calcul, pas d'une génération.
- q: ColisVert envoie le nom et l'adresse du client au LLM pour « personnaliser » le SMS. Quel principe du RGPD est en cause ?
  options:
    - La portabilité
    - La minimisation - ne transmettre que les données nécessaires au traitement
    - Le droit à l'oubli
    - Aucun, OpenAI est un sous-traitant
  answer: 1
  explain: Le rédacteur du TP n'envoie que trois champs ; le nom et l'adresse n'apportent rien au texte.
- q: Que reste-t-il au LLM simulé de tester, et que ne teste-t-il pas ?
  options:
    - Il teste tout
    - Il teste la boucle, les outils et les garde-fous, pas la qualité des réponses du vrai LLM
    - Il teste la qualité, pas la boucle
    - Il ne teste rien
  answer: 1
  explain: La qualité se mesure avec le vrai LLM sur un jeu de référence, avant chaque mise en service.
```
