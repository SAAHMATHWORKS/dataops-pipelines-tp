---
subtitle: >-
  Une donnée sans responsable finit fausse, dupliquée ou exposée. Gouverner, c'est décider qui
  répond de chaque donnée, ce qu'on a le droit d'en faire, et comment le vérifier. On voit les rôles,
  le catalogue, la classification et ce qu'impose le RGPD, puis on écrit la fiche du produit de
  données « livraisons » et un contrôle automatique qui la vérifie, comme un test.
objectives:
  - Expliquer à quoi sert la gouvernance des données, et ce qu'elle n'est pas
  - Distinguer propriétaire, intendant, dépositaire et consommateur d'une donnée
  - Classer des colonnes selon leur sensibilité, et appliquer les exigences du RGPD aux données personnelles
  - Écrire une politique de gouvernance sous forme de code, vérifiée automatiquement
  - Situer Microsoft Purview, le catalogue OneLake de Fabric et Unity Catalog
---

{#pourquoi}
## Pourquoi gouverner

**L'analogie du cadastre.** Une ville sans cadastre peut fonctionner tant qu'elle est petite. Mais dès qu'elle grandit, plus personne ne sait à qui appartient quel terrain, où passent les canalisations, ni qui doit réparer le trottoir. La gouvernance des données, c'est le cadastre de l'entreprise : qui possède quoi, ce que chaque donnée contient, d'où elle vient, et qui a le droit d'y toucher.

Sans elle, ColisVert aurait vite trois problèmes :

- **la confiance** : deux tableaux de bord donnent deux taux de retard différents, et personne ne sait lequel est juste ;
- **la conformité** : une adresse de client se retrouve dans un fichier partagé, et personne ne sait depuis quand ni pourquoi ;
- **le coût** : on stocke cinq copies d'un même fichier, dont quatre périmées.

::: callout warn La gouvernance n'est pas un comité qui dit non
Une gouvernance qui ne fait que ralentir pousse les équipes à contourner les règles (fichiers Excel partagés, copies privées : le *shadow IT*). Une bonne gouvernance **rend le bon chemin le plus facile** : la donnée certifiée est la plus simple à trouver, l'accès se demande en un clic, les contrôles tournent tout seuls. C'est le même esprit que le DataOps : des garde-fous automatiques plutôt que des validations manuelles.
:::

{#roles}
## Les rôles

| Rôle | Ce qu'il fait | Chez ColisVert, pour « livraisons » |
|---|---|---|
| **Propriétaire** (*data owner*) | Répond de la donnée devant l'entreprise : définit son usage, accorde les accès, arbitre | La responsable des opérations |
| **Intendant** (*data steward*) | Fait vivre la donnée au quotidien : définitions, qualité, glossaire, lignage | L'analyste qualité des opérations |
| **Dépositaire** (*data custodian*) | Gère la technique : stockage, sauvegardes, sécurité, pipelines | L'équipe data (vous) |
| **Consommateur** | Utilise la donnée, signale les problèmes | Le service client, la direction, les data scientists |
| **Bureau central** | Fixe les politiques communes et suit la santé de l'ensemble | Le responsable des données de l'entreprise |

Le point clé : **le propriétaire est au métier, pas à l'informatique**. C'est celui qui sait ce que veut dire « en retard », et qui subit les conséquences quand la donnée est fausse.

{#objets}
## Les objets de la gouvernance

- **Le catalogue et le glossaire.** Le catalogue liste les jeux de données et leurs colonnes ; le glossaire définit les mots du métier (« un colis est en retard si son délai réel dépasse le délai promis »). Sans glossaire, deux équipes calculent deux « taux de retard ».
- **Le produit de données.** Un jeu de données publié pour d'autres, avec un propriétaire, une documentation, un contrat de qualité et un engagement de fraîcheur. C'est l'unité de base du Data Mesh (jour 1).
- **La classification.** Chaque colonne reçoit un niveau de sensibilité : publique, interne, confidentielle, personnelle. Le niveau décide des règles d'accès, de chiffrement et de conservation.
- **Le lignage.** D'où vient une donnée, et où va-t-elle ? Au jour 1, OpenLineage ; aujourd'hui, l'historique des tables Delta.
- **La qualité.** Le contrat de données du jour 1, exécuté à chaque arrivée de fichier (jour 3).

{#rgpd}
## Les données personnelles et le RGPD

Une donnée est **personnelle** si elle permet d'identifier une personne, directement (nom, adresse) ou **indirectement**. Le numéro de colis de ColisVert ne contient pas de nom, mais il permet de retrouver le client dans le système des commandes : c'est une donnée **pseudonyme**, et le RGPD la traite comme une donnée personnelle.

Pour chaque traitement de données personnelles, le RGPD impose notamment :

- **une base légale** : ici, l'exécution du contrat de livraison ;
- **la minimisation** : ne collecter que ce qui sert au traitement (le modèle n'a pas besoin du nom du client) ;
- **une durée de conservation** limitée et justifiée ;
- **la transparence** envers les personnes, et le respect de leurs droits (accès, rectification, effacement).

On y reviendra cet après-midi pour les LLM et les agents : envoyer des données personnelles à un service d'IA est un traitement comme un autre.

{#code}
## La gouvernance par le code

Une politique écrite dans un document est lue une fois. Une politique écrite **en code** est vérifiée à chaque modification, comme un test. C'est ce que le Data Mesh appelle la **gouvernance fédérée et calculée** : les règles sont communes, mais elles sont exécutées automatiquement dans chaque domaine.

:::: lab Démo | La fiche du produit « livraisons » et sa vérification | 10 min
La fiche décrit le produit de données et chacune de ses colonnes. La fonction `verifier` applique quatre politiques de ColisVert :

1. un produit a un propriétaire, un intendant, une description et un engagement de fraîcheur ;
2. chaque colonne a une description et une classification connue ;
3. une colonne personnelle a une base légale et une durée de conservation ;
4. la fiche décrit **toutes** les colonnes réelles du fichier, et rien d'autre.

```python title="Cellule 1 : la fiche du produit de données, vérifiée par du code"
PRODUIT = {
    "nom": "livraisons",
    "domaine": "Opérations",
    "description": "Un colis par ligne : expédition, conditions, délais promis et réels",
    "proprietaire": "Responsable des opérations",
    "intendant": "Analyste qualité des opérations",
    "emplacement": "lakehouse/argent/livraisons (Delta Lake)",
    "fraicheur": "chaque jour avant 07:00",
    "colonnes": {
        "id_colis": {"description": "Numéro du colis, relié au client dans le système des commandes",
                     "classification": "personnelle", "base_legale": "exécution du contrat"},
        "date_expedition": {"description": "Jour d'expédition", "classification": "interne"},
        "entrepot": {"description": "Entrepôt de départ", "classification": "interne"},
        "client": {"description": "Type de client : particulier ou professionnel", "classification": "interne"},
        "creneau": {"classification": "interne"},
        "distance_km": {"description": "Distance de l'entrepôt au client", "classification": "interne"},
        "poids_kg": {"description": "Poids du colis", "classification": "interne"},
        "meteo": {"description": "Météo le jour de la livraison", "classification": "publique"},
        "delai_promis_h": {"description": "Délai promis au client, en heures", "classification": "interne"},
        "delai_reel_h": {"description": "Délai constaté, en heures", "classification": "interne"},
    },
}
CLASSIFICATIONS = {"publique", "interne", "confidentielle", "personnelle"}

def verifier(produit, colonnes_reelles):
    """Renvoie la liste des écarts aux politiques de gouvernance (vide si tout est conforme)."""
    ecarts = []
    for champ in ["proprietaire", "intendant", "description", "fraicheur"]:
        if not produit.get(champ):
            ecarts.append(f"produit : « {champ} » manquant")
    for nom, colonne in produit["colonnes"].items():
        if not colonne.get("description"):
            ecarts.append(f"{nom} : description manquante")
        if colonne.get("classification") not in CLASSIFICATIONS:
            ecarts.append(f"{nom} : classification absente ou inconnue")
        if colonne.get("classification") == "personnelle":
            for exigence in ["base_legale", "conservation"]:
                if not colonne.get(exigence):
                    ecarts.append(f"{nom} : donnée personnelle sans « {exigence} »")
    for nom in sorted(set(colonnes_reelles) - set(produit["colonnes"])):
        ecarts.append(f"{nom} : colonne du fichier absente de la fiche")
    for nom in sorted(set(produit["colonnes"]) - set(colonnes_reelles)):
        ecarts.append(f"{nom} : colonne de la fiche absente du fichier")
    return ecarts

colonnes_reelles = list(pd.read_csv(DOSSIER_DATA / "livraisons.csv", nrows=0).columns)
ecarts = verifier(PRODUIT, colonnes_reelles)
print(f"{len(ecarts)} écart(s) aux politiques :")
for ecart in ecarts:
    print(" -", ecart)
```

```plaintext title="Sortie attendue"
3 écart(s) aux politiques :
 - id_colis : donnée personnelle sans « conservation »
 - creneau : description manquante
 - en_retard : colonne du fichier absente de la fiche
```

Trois écarts, trois cas réels :
- **une documentation incomplète** : `creneau` n'a pas de description ;
- **une exigence du RGPD oubliée** : la durée de conservation de `id_colis` ;
- **une dérive entre la documentation et la donnée** : la colonne `en_retard` existe dans le fichier, mais personne ne l'a décrite.

Vous les corrigerez à l'évaluation.
::::

**En production**, cette vérification tourne dans la CI à chaque modification de la fiche ou du schéma, et bloque la publication tant qu'un écart subsiste. Les mêmes politiques peuvent aussi s'écrire dans le moteur de règles d'un catalogue.

{#plateformes}
## Les plateformes de gouvernance

::: callout info Vérifié dans la documentation des éditeurs, novembre 2026
- **Microsoft Purview, Unified Catalog** : un catalogue construit sur les métadonnées que la *Data Map* collecte en analysant les sources. On y organise des **domaines de gouvernance** (des zones de responsabilité) et des **produits de données**, rattachés à des termes du glossaire et à des objectifs (OKR). On y suit aussi la **qualité** et la **santé** des données, et le lignage. Les rôles cités sont le bureau central des données, les propriétaires, les intendants et les consommateurs. Purview ne stocke que des métadonnées : un rôle dans Purview ne donne pas accès aux données elles-mêmes.
- **Microsoft Fabric, catalogue OneLake** : l'onglet **Govern** donne aux administrateurs et aux propriétaires une vue d'ensemble de leurs éléments. On y voit la couverture des étiquettes de sensibilité, la part d'éléments **certifiés ou promus** (*endorsement*), décrits et fraîchement mis à jour, ainsi que des actions recommandées. Il est déployé région par région.
- **Unity Catalog** (Databricks, publié en open source en 2024) : un catalogue et un système de droits unique pour les tables, les fichiers, les modèles et les fonctions, avec le lignage par colonne.
:::

{#quiz}
## Quiz

```quiz
- q: Qui doit être propriétaire du produit de données « livraisons » ?
  options:
    - L'équipe data qui écrit le pipeline
    - La responsable des opérations - celle qui répond de l'usage et de la justesse de la donnée
    - Le service informatique
    - Le data scientist qui entraîne le modèle
  answer: 1
  explain: Le propriétaire est au métier ; l'équipe data est dépositaire, elle gère la technique.
- q: Le numéro de colis ne contient aucun nom. Est-ce une donnée personnelle au sens du RGPD ?
  options:
    - Non, puisqu'il n'y a pas de nom
    - Oui - il permet de retrouver le client dans un autre système, c'est une donnée pseudonyme
    - Seulement s'il est chiffré
    - Seulement pour les clients professionnels
  answer: 1
  explain: Une donnée qui identifie une personne indirectement reste personnelle ; seule l'anonymisation véritable la fait sortir du RGPD.
- q: Pourquoi écrire les politiques de gouvernance sous forme de code ?
  options:
    - Pour remplacer le propriétaire
    - Pour qu'elles soient vérifiées automatiquement à chaque modification, comme des tests
    - Parce que c'est obligatoire dans le RGPD
    - Pour aller plus vite à écrire
  answer: 1
  explain: Une règle exécutée à chaque changement ne s'oublie pas ; c'est la gouvernance « calculée » du Data Mesh.
- q: Que révèle l'écart « en_retard - colonne du fichier absente de la fiche » ?
  options:
    - Une erreur de saisie dans le fichier
    - Une dérive entre la documentation et la donnée réelle
    - Une donnée personnelle non déclarée
    - Rien d'important
  answer: 1
  explain: La fiche décrit le produit tel qu'on le croit ; la vérification la confronte au produit tel qu'il est.
```
