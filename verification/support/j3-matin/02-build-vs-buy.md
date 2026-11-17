---
subtitle: >-
  Faut-il écrire son orchestrateur, installer un outil libre, ou payer un service managé ? La
  réponse n'est jamais idéologique : elle dépend de ce qui différencie l'entreprise, des
  compétences de l'équipe, et d'un coût total qu'on calcule sur plusieurs années, pas sur le prix
  affiché.
objectives:
  - Situer une option sur l'échelle qui va de construire à acheter
  - Évaluer une option avec des critères explicites, au-delà du prix
  - Calculer un coût total de possession sur trois ans et trouver le point de bascule entre deux options
  - Identifier le risque de dépendance au calendrier d'un fournisseur, à partir de cas réels de 2026
---

{#pourquoi}
## Pourquoi la question se pose

**Le problème.** Cet après-midi, ColisVert va orchestrer son pipeline avec Airflow. Mais qui l'exploitera ? L'équipe peut écrire ses propres scripts lancés par une tâche planifiée, installer Airflow sur une machine qu'elle administre, ou louer un Airflow managé chez un fournisseur cloud. Les trois marchent. Les trois coûtent, mais pas de la même façon ni au même moment.

**L'analogie de la cantine.** Une entreprise veut nourrir ses salariés. Elle peut **construire** sa cuisine et embaucher des cuisiniers, **équiper** une cuisine avec du matériel du commerce et un prestataire qui l'utilise, ou **acheter** des repas livrés. Un restaurant gastronomique dont la cuisine **est** le métier construit. Une banque, dont ce n'est pas le métier, achète. La question n'est pas « qu'est-ce qui est le mieux ? », mais « qu'est-ce qui nous différencie ? ».

{#echelle}
## Une échelle, pas un choix binaire

| Option | Ce qu'on fait soi-même | Exemple pour l'orchestration | Exemple pour le stockage |
|---|---|---|---|
| **Construire** | Tout : le code, l'exploitation | Des scripts maison lancés par `cron` | Un serveur de fichiers maison |
| **Libre, auto-hébergé** | L'installation, les mises à jour, la sécurité, l'exploitation | Airflow sur une VM de l'entreprise | MinIO sur des serveurs internes |
| **Libre, managé** | Le contenu (les DAG) ; le fournisseur exploite | Tâches Apache Airflow de Fabric, Managed Service for Apache Airflow de Google | — |
| **Service propriétaire** (SaaS) | Rien d'autre que l'usage | Pipelines de Data Factory, de Fabric | Azure Blob Storage, Cloud Storage |

L'option « libre, managé » est souvent la plus intéressante : on garde un **standard ouvert** (un DAG Airflow reste un DAG Airflow, transportable), sans porter l'exploitation. Mais elle a ses pièges, qu'on verra avec les cas réels.

{#criteres}
## Les critères, au-delà du prix

| Critère | La question à poser | Penche vers |
|---|---|---|
| **Différenciation** | Est-ce ce qui nous distingue de nos concurrents ? | Oui : construire. Non : acheter |
| **Compétences** | L'équipe sait-elle l'exploiter, à 3 h du matin, pendant les vacances ? | Non : acheter |
| **Délai** | Faut-il que ça marche le mois prochain ? | Oui : acheter |
| **Coût total** | Combien sur trois ans, temps humain compris ? | À calculer |
| **Contrôle et conformité** | Où sont les données ? Qui y accède ? Contraintes du secteur (santé, défense) ? | Fortes : construire ou auto-héberger |
| **Réversibilité** | Peut-on en sortir, et à quel prix ? | Format ouvert : acheter sans crainte |
| **Cycle de vie du fournisseur** | Le produit existera-t-il, dans quelle version, dans trois ans ? | Incertain : garder un standard portable |

Pour ColisVert, l'orchestration **n'est pas** ce qui la différencie : un client ne choisira jamais un transporteur pour son orchestrateur. Le **modèle de prédiction**, lui, entraîné sur ses propres données, peut l'être.

{#tco}
## Le coût total de possession

**Le prix affiché trompe.** Un outil libre est gratuit à télécharger, mais pas à exploiter : installation, mises à jour, sécurité, incidents, tout cela coûte des journées d'ingénieur. Le **coût total de possession** (*TCO, total cost of ownership*) additionne tout, sur la durée de vie de la décision, souvent trois ans.

:::: lab Démo | Trois options d'orchestration sur trois ans | 8 min
Les chiffres ci-dessous sont des **hypothèses de travail** pour l'exercice, pas des tarifs : pour une vraie décision, on prend les prix sur les calculateurs des fournisseurs et les temps sur l'historique de l'équipe. Créez le notebook du matin, `j3-matin.ipynb`, dans le dossier `notebooks`.

```python title="Cellule 1 : le coût total de possession"
options = {
    "Construire (scripts + cron)": {"mise_en_place_j": 15, "maintenance_j_mois": 4.0, "infra_eur_mois": 20},
    "Airflow auto-hébergé":        {"mise_en_place_j": 8,  "maintenance_j_mois": 1.5, "infra_eur_mois": 120},
    "Airflow managé (cloud)":      {"mise_en_place_j": 3,  "maintenance_j_mois": 0.5, "infra_eur_mois": 600},
}


def cout_total(option, taux_jour, mois=36):
    """Mise en place + (maintenance + infrastructure) chaque mois, sur la durée."""
    return option["mise_en_place_j"] * taux_jour + mois * (option["maintenance_j_mois"] * taux_jour + option["infra_eur_mois"])


for taux_jour in [400, 600, 800]:
    print(f"Ingénieur à {taux_jour} €/jour :")
    for nom, option in options.items():
        print(f"  {nom:<28} {cout_total(option, taux_jour):>9,.0f} €")
```

```plaintext title="Sortie attendue"
Ingénieur à 400 €/jour :
  Construire (scripts + cron)     64,320 €
  Airflow auto-hébergé            29,120 €
  Airflow managé (cloud)          30,000 €
Ingénieur à 600 €/jour :
  Construire (scripts + cron)     96,120 €
  Airflow auto-hébergé            41,520 €
  Airflow managé (cloud)          34,200 €
Ingénieur à 800 €/jour :
  Construire (scripts + cron)    127,920 €
  Airflow auto-hébergé            53,920 €
  Airflow managé (cloud)          38,400 €
```

Trois enseignements :

- **« Construire » est le plus cher, et de loin**, alors que son infrastructure ne coûte que 20 € par mois. Ce sont les 4 jours de maintenance mensuelle qui pèsent : des scripts maison n'ont ni reprise sur échec, ni alertes, ni historique, et chaque incident se règle à la main.
- **Le managé coûte 30 fois plus cher en infrastructure** (600 € contre 20 €), et pourtant il gagne dès que le temps de l'équipe coûte cher.
- **Entre auto-hébergé et managé, le gagnant dépend du coût du temps** : à 400 € par jour, l'auto-hébergé gagne de peu ; à 600 €, le managé gagne.
::::

**Où est le point de bascule ?** Les deux options coûtent autant quand `8t + 36 × (1,5t + 120) = 3t + 36 × (0,5t + 600)`, avec `t` le taux journalier. On trouve `41t = 17 280`, soit **t ≈ 421 € par jour**. En dessous, l'auto-hébergé est moins cher ; au-dessus, le managé. Ce genre de calcul ne donne pas « la » réponse : il montre **quelle hypothèse décide**, et donc ce qu'il faut vérifier sérieusement.

{#cas-reels}
## Trois cas réels de 2026 : le calendrier du fournisseur

Acheter, c'est aussi accepter le **calendrier** d'un fournisseur. Trois faits, relevés dans les documentations officielles en novembre 2026 :

1. **Azure Data Factory** proposait un Airflow managé (*Workflow Orchestration Manager*). Microsoft a annoncé que depuis le **1er janvier 2026**, on ne peut plus en créer de nouvelles instances, et recommande de migrer vers les **tâches Apache Airflow de Microsoft Fabric**. Les équipes qui l'avaient choisi ont dû planifier une migration qu'elles n'avaient pas décidée.
2. **Dans Fabric**, la documentation des tâches Apache Airflow indique **Airflow 2.10.5**. Les TP de cet après-midi utilisent **Airflow 3**. Or Airflow 3 a changé des points importants (les DAG s'écrivent avec le module `airflow.sdk`, les « datasets » sont devenus des « assets ») : un DAG écrit pour l'un ne tourne pas forcément tel quel sur l'autre. Acheter un service managé, c'est utiliser **sa** version, pas la dernière.
3. **Chez Google**, Cloud Composer est devenu **Managed Service for Apache Airflow** (annonce d'avril 2026). Airflow 3 y est disponible en version stable depuis le 15 avril 2026, et Airflow 3.3.1 depuis le 20 août 2026 ; la version proposée par défaut reste toutefois Airflow 2.

**La leçon :** l'option « libre, managé » garde un standard portable, mais il faut vérifier la **version** offerte et prévoir le jour où le fournisseur change de produit. D'où le dernier critère du tableau : le cycle de vie du fournisseur.

:::: lab Exercice | Construire ou acheter, trois décisions pour ColisVert | 7 min
Pour chaque composant, proposez une option sur l'échelle (construire, libre auto-hébergé, libre managé, propriétaire) et justifiez-la avec deux critères au plus.

1. Le stockage des fichiers de livraisons et des modèles.
2. Le modèle de prédiction des retards.
3. L'envoi des SMS aux clients.

::: solution Une proposition
1. **Propriétaire (stockage objet du cloud).** Aucune différenciation, et un service de stockage objet est une commodité bon marché, fiable, sans exploitation. Réversibilité assurée si l'on garde des formats ouverts (Parquet, Delta).
2. **Construire**, sur des briques libres (scikit-learn, MLflow). C'est le seul composant qui exploite un actif unique de ColisVert : ses données de livraison. Un modèle acheté « sur étagère » ne connaîtrait ni ses entrepôts ni ses clients.
3. **Propriétaire (une API d'envoi de SMS).** Aucune différenciation ; contraintes de délivrabilité et d'opérateurs que seul un spécialiste maîtrise. Attention à la conformité RGPD du prestataire, puisqu'on lui transmet des numéros de téléphone.

On construit là où l'on se différencie, on achète le reste.
:::
::::

{#avance}
## Pour aller plus loin : coûts cachés, plan de sortie et « cœur ou contexte »

Ce bloc est pour les profils avancés ; rien ici n'est exigé dans l'évaluation.

**Les coûts que les comparatifs oublient.**

- L'**astreinte** : qui répond la nuit ? Un outil auto-hébergé critique implique une personne d'astreinte, donc une prime et au moins deux personnes formées.
- Les **montées de version** : Airflow 2 vers 3 a demandé de vrais travaux de migration.
- La **sécurité** : correctifs, audits, gestion des secrets.
- La **sortie** : frais de transfert des données hors du cloud (*egress*), réécriture du code propriétaire.
- La **formation**, et le **recrutement** sur un outil rare.

À l'inverse, un service managé a ses coûts cachés : facturation à l'usage difficile à prévoir, fonctionnalités en retard sur l'outil libre, limites (réseaux privés, journaux) qu'on découvre en production.

**Le plan de sortie.** Toute décision d'achat devrait s'accompagner d'une page « comment en sortir » : quelles données, dans quel format, combien de temps, combien d'argent. Si la réponse est « on ne sait pas », le risque est réel. Garder des formats ouverts (Parquet, Delta, DAG Airflow standards, modèles au format MLflow) est l'assurance la moins chère.

**Cœur ou contexte.** Geoffrey Moore distingue le **cœur** (*core*), ce qui différencie l'entreprise aux yeux de ses clients, et le **contexte** (*context*), tout le reste, nécessaire mais banal. Le contexte doit être fait correctement et au moindre coût, idéalement acheté ; le cœur mérite l'investissement et le contrôle. Les ennuis commencent quand une équipe met son énergie dans le contexte (un orchestrateur maison « parce qu'on peut ») au détriment du cœur.

{#quiz}
## Quiz de validation

```quiz
- q: Pourquoi l'option « Construire » est-elle la plus chère dans l'exemple, alors que son infrastructure ne coûte que 20 € par mois ?
  options:
    - Parce que les serveurs sont plus chers qu'annoncé
    - Parce que le temps de maintenance et d'incidents, 4 jours par mois, pèse bien plus que l'infrastructure
    - Parce que cron est payant
    - Parce que le calcul est faux
  answer: 1
  explain: Le temps humain domine presque toujours le coût total. C'est ce que le prix affiché ne montre pas.
- q: Qu'apporte l'option « libre, managé » par rapport à un service propriétaire ?
  options:
    - Elle est toujours gratuite
    - Elle garde un standard ouvert et portable, sans porter l'exploitation
    - Elle donne accès à la dernière version de l'outil le jour de sa sortie
    - Elle évite de choisir un fournisseur
  answer: 1
  explain: Un DAG Airflow reste transportable - à condition de vérifier la version offerte par le fournisseur.
- q: Que s'est-il passé pour l'Airflow managé d'Azure Data Factory ?
  options:
    - Il est passé à Airflow 3
    - Depuis le 1er janvier 2026, on ne peut plus en créer de nouvelles instances ; Microsoft recommande de migrer vers Fabric
    - Il est devenu gratuit
    - Il a été racheté par Google
  answer: 1
  explain: Un exemple concret du risque lié au cycle de vie d'un produit acheté.
- q: Pour ColisVert, quel composant mérite le plus d'être construit ?
  options:
    - L'orchestrateur
    - Le stockage des fichiers
    - Le modèle de prédiction des retards, entraîné sur ses propres données
    - L'envoi des SMS
  answer: 2
  explain: C'est le seul qui exploite un actif unique de l'entreprise. Le reste est du contexte, à acheter ou louer.
```
