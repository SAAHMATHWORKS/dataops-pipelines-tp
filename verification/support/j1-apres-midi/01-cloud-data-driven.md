---
subtitle: >-
  Les analytiques transforment les données en décisions, le Cloud fournit la puissance à la
  demande. Encore faut-il une organisation qui s'en serve vraiment : c'est l'organisation data driven.
objectives:
  - Préparer les données de l'après-midi
  - Distinguer analytique descriptive, diagnostique, prédictive et prescriptive
  - Comparer le coût d'un serveur acheté et d'un serveur loué selon l'usage
  - Distinguer IaaS, PaaS et SaaS
  - Reconnaître les signes d'une organisation data driven
---

{#mise-en-place}
## Préparer les données de l'après-midi

:::: lab Mise en place | Créer les données | 3 min
Dans votre notebook `j1-apres-midi.ipynb`, exécutez cette cellule. Elle recrée les fichiers du matin, plus un troisième : `livraisons_brutes.csv`, les mêmes colis **tels qu'ils arrivent vraiment**, avec des défauts. On s'en servira dans la notion suivante.

```python title="Cellule 1 : les données"
import pandas as pd
from colisvert.donnees import DOSSIER_DATA, preparer_donnees

dossier = preparer_donnees()
brutes = pd.read_csv(DOSSIER_DATA / "livraisons_brutes.csv")
print(brutes.shape)
```

```plaintext title="Sortie attendue"
livraisons.csv : 5035 colis, dont 862 en retard
arrivees.csv : 56 jours
livraisons_brutes.csv : les mêmes colis, avec des défauts de qualité
(5060, 11)
```

**Vérification :** 5 060 lignes dans le fichier brut, soit 25 de plus que les 5 035 colis. On verra pourquoi.
::::

{#analytiques}
## Les apports des analytiques : quatre niveaux

**Pourquoi des niveaux ?** Parce que les analytiques ne répondent pas toutes à la même question, et ne demandent pas le même effort. On les classe souvent en quatre niveaux, de plus en plus utiles et de plus en plus difficiles (un modèle popularisé par le cabinet Gartner).

| Niveau | La question | Chez ColisVert | Quand dans la semaine |
|---|---|---|---|
| **Descriptive** | Que s'est-il passé ? | 17,1 % de colis en retard en 8 semaines | Ce matin |
| **Diagnostique** | Pourquoi ? | La pluie et l'entrepôt de Lille | Ce matin |
| **Prédictive** | Que va-t-il se passer ? | Ce colis a de fortes chances d'arriver en retard | Jour 2 |
| **Prescriptive** | Que faut-il faire ? | Ajouter une tournée à Lille demain après-midi | Jours 4 et 5 |

**L'analogie :** la météo. « Il a plu hier » (descriptive), « à cause d'une dépression » (diagnostique), « il pleuvra demain » (prédictive), « prenez un parapluie » (prescriptive).

Plus on monte, plus il faut des données **fraîches, propres et fiables**, livrées **à temps**. C'est exactement le travail d'un pipeline DataOps.

{#cloud}
## Les apports du Cloud : louer plutôt qu'acheter

Le **Cloud** consiste à louer, à la demande et à distance, des serveurs, du stockage ou des logiciels, et à payer ce qu'on consomme. Trois apports reviennent toujours :

- **l'élasticité** : on passe de 2 à 200 machines pour un calcul, puis on revient à 2 ;
- **le paiement à l'usage** : une machine éteinte ne coûte (presque) plus rien ;
- **les services managés** : le fournisseur installe, sauvegarde et met à jour ; l'équipe se concentre sur les données.

Le Cloud n'est pas toujours moins cher. Tout dépend du **temps d'utilisation**.

:::: lab Démo | Acheter ou louer ? | 4 min
ColisVert recalcule ses indicateurs chaque nuit pendant 2 heures, sur 4 machines. Deux options, avec des **prix fictifs** pour l'exercice :

- **acheter** un serveur 12 000 €, amorti sur 3 ans, plus 1 800 € par an d'électricité et de maintenance ;
- **louer** 4 machines dans le Cloud à 0,90 € de l'heure chacune.

```python title="Cellule 2 : acheter ou louer"
achat_par_an = 12000 / 3 + 1800
cloud_2h_par_nuit = 4 * 2 * 365 * 0.90
cloud_24h_sur_24 = 4 * 24 * 365 * 0.90


def euros(montant):
    """12345.6 devient « 12 346 € » : séparateur de milliers, sans décimale."""
    return f"{montant:,.0f} €".replace(",", " ")


print(f"Serveur acheté         : {euros(achat_par_an):>9} par an")
print(f"Cloud, 2 h par nuit    : {euros(cloud_2h_par_nuit):>9} par an")
print(f"Cloud, 24 h sur 24     : {euros(cloud_24h_sur_24):>9} par an")
```

```plaintext title="Sortie attendue"
Serveur acheté         :   5 800 € par an
Cloud, 2 h par nuit    :   2 628 € par an
Cloud, 24 h sur 24     :  31 536 € par an
```

La petite fonction `euros` met en forme un montant à la française. Dans le `print`, `:>9` aligne le texte à droite sur 9 caractères, pour que les montants tombent en colonne.

**Lecture :** pour un calcul de 2 heures par nuit, le Cloud coûte **deux fois moins cher** que l'achat (2 628 € contre 5 800 €). Pour des machines allumées en permanence, il coûte **plus de cinq fois plus cher**. Le Cloud est imbattable pour les besoins **variables** ; il faut éteindre ce qui ne sert pas.
::::

{#iaas-paas-saas}
## IaaS, PaaS, SaaS : ce que l'on loue

| Modèle | On loue… | On gère soi-même | Exemple pour les données |
|---|---|---|---|
| **IaaS** (*Infrastructure as a Service*) | des machines virtuelles, du stockage, du réseau | le système, les logiciels, les données | Une VM où l'on installe soi-même Spark |
| **PaaS** (*Platform as a Service*) | une plateforme prête à l'emploi | ses programmes et ses données | Une base de données ou un cluster Spark managés |
| **SaaS** (*Software as a Service*) | un logiciel complet, dans le navigateur | ses données et ses réglages | Un outil de tableaux de bord en ligne |

**L'analogie du repas :** l'IaaS, c'est louer une cuisine équipée : vous faites les courses et la cuisine. Le PaaS, c'est un traiteur qui livre les plats : vous dressez la table. Le SaaS, c'est le restaurant : vous choisissez sur la carte.

Plus on monte vers le SaaS, moins on a de travail technique, et moins on a de liberté.

{#data-driven}
## Qu'est-ce qu'une organisation data driven ?

Une organisation **data driven** (pilotée par les données) prend ses décisions **à partir de données vérifiées**, plutôt qu'à partir de l'intuition, de l'habitude ou de l'avis de la personne la plus haut placée.

Quatre signes la reconnaissent :

| Signe | Chez ColisVert aujourd'hui | Chez ColisVert data driven |
|---|---|---|
| **Les décisions partent des données** | « On a toujours fait deux tournées à Lille » | « Les jours de pluie, 53 % de retards à Lille : on ajoute une tournée » |
| **Les données sont accessibles** | Il faut demander un export à la DSI et attendre 2 jours | Chacun consulte le tableau de bord, en libre-service |
| **Tout le monde sait les lire** | Seule l'équipe data comprend les chiffres | Les chefs d'entrepôt savent lire un taux et une carte de contrôle |
| **On expérimente** | Les changements se décident en réunion | On teste une tournée de plus à Lille pendant 2 semaines, et on mesure |

::: callout warn Idée reçue
« Être data driven, c'est avoir beaucoup de données. » Non : ColisVert a déjà 5 000 colis par période de 8 semaines. Ce qui lui manque, ce sont des données **fiables**, **accessibles** et **utilisées**. C'est une question de culture et d'organisation autant que d'outils.
:::

{#quiz}
## Quiz de validation

```quiz
- q: « Ce colis a de fortes chances d'arriver en retard. » Quel niveau d'analytique ?
  options: [Descriptive, Diagnostique, Prédictive, Prescriptive]
  answer: 2
  explain: Elle répond à la question « que va-t-il se passer ? ».
- q: Dans la démo, pourquoi le Cloud coûte-t-il beaucoup plus cher pour des machines allumées 24 heures sur 24 ?
  options:
    - Parce que les machines du Cloud sont moins puissantes
    - Parce qu'on paie à l'heure, et qu'une machine permanente accumule les heures
    - Parce que le stockage est plus cher
    - Parce que le Cloud facture le réseau
  answer: 1
  explain: Le paiement à l'usage avantage les besoins variables. Pour un usage permanent, l'achat peut être moins cher.
- q: Une base de données managée, où le fournisseur s'occupe des sauvegardes et des mises à jour, est un exemple de…
  options: [IaaS, PaaS, SaaS, matériel acheté]
  answer: 1
  explain: On loue la plateforme ; on ne gère que ses programmes et ses données.
- q: Lequel de ces signes caractérise le mieux une organisation data driven ?
  options:
    - Elle stocke beaucoup de données
    - Elle a acheté un outil de tableaux de bord
    - Ses décisions partent de données vérifiées, accessibles à ceux qui décident
    - Son équipe data est nombreuse
  answer: 2
  explain: Le volume et les outils ne suffisent pas. Ce qui compte est l'usage des données dans les décisions.
```
