---
subtitle: >-
  Git versionne le code, mais il n'est pas fait pour les gros fichiers de données. DVC complète
  Git : il range les données à part et ne laisse dans Git qu'un petit ticket. Ensemble, ils
  permettent de retrouver n'importe quelle version des données, comme on retrouve une version du code.
objectives:
  - Expliquer pourquoi versionner les données, et pourquoi Git seul ne suffit pas
  - Initialiser DVC dans un dépôt Git et configurer un stockage distant
  - Versionner un fichier de données avec dvc add, git commit et dvc push
  - Enregistrer une nouvelle version, puis revenir à la précédente
---

{#pourquoi}
## Pourquoi versionner les données ?

**Le problème.** En octobre, le modèle de ColisVert prédisait bien les retards. En novembre, il se trompe. Qu'est-ce qui a changé : le code, les données, ou les deux ? Si l'on ne peut pas retrouver **les données exactes** d'octobre, on ne le saura jamais.

C'est le principe n° 11 du manifeste DataOps : **tout versionner, données comprises**, pour pouvoir refaire exactement le même calcul plus tard.

**Pourquoi pas Git seul ?** Git est conçu pour des fichiers texte de quelques kilo-octets, modifiés ligne par ligne. Il garde **chaque version complète** de chaque fichier dans le dépôt, pour toujours. Avec des fichiers de données de plusieurs gigaoctets, le dépôt devient vite énorme et lent, et les plateformes comme GitHub refusent les fichiers trop gros.

**La réponse : DVC** (*Data Version Control*), un outil libre qui travaille **avec** Git.

{#vestiaire}
## L'analogie du vestiaire

Au théâtre, vous déposez votre manteau au **vestiaire** et l'on vous donne un **ticket**. Le ticket est petit et tient dans la poche ; le manteau, lui, reste au vestiaire. Avec le ticket, vous récupérez exactement **votre** manteau.

DVC fait la même chose :

- le **manteau**, c'est le gros fichier `data/livraisons.csv` ;
- le **vestiaire**, c'est le cache de DVC (`.dvc/cache`), puis un stockage distant ;
- le **ticket**, c'est un petit fichier `data/livraisons.csv.dvc` qui contient l'**empreinte** du fichier. C'est lui que Git versionne.

::: figure dvc-git.svg
DVC déplace les gros fichiers entre votre dossier, son cache et le stockage distant. Git versionne les tickets.
:::

L'**empreinte** (ici un calcul *MD5*) est une suite de 32 caractères calculée à partir du contenu du fichier. Le même contenu donne toujours la même empreinte ; un seul caractère modifié en donne une complètement différente. Comme vos données sont identiques à celles de vos voisins, **vos empreintes aussi**.

{#etape1}
## Étape 1 : préparer Git

:::: lab Étape 1 | Ouvrir un terminal et créer une branche | 5 min
Dans JupyterLab, ouvrez un terminal (**File › New › Terminal**). Toutes les commandes du TP s'y tapent.

**1. Donnez une identité à Git.** Chaque commit porte un nom et un email. On utilise une identité fictive : aucune donnée personnelle sur la VM.

```bash title="Terminal JupyterLab"
cd /home/lab/projet
git config --global user.name "Stagiaire DataOps"
git config --global user.email "stagiaire@colisvert.example"
```

**2. Créez une branche de travail.** Une **branche** est une ligne de travail séparée : vos commits y restent, et la branche principale (`main`) reste propre pour récupérer les mises à jour du formateur.

```bash title="Terminal JupyterLab"
git switch -c tp-dvc
```

```plaintext title="Sortie attendue"
Switched to a new branch 'tp-dvc'
```

::: hint
Le terminal affiche `I have no name!` devant le dossier : c'est normal. Le conteneur tourne avec votre numéro d'utilisateur de la VM, qu'il ne connaît pas par son nom. Git et DVC fonctionnent quand même.
:::
::::

{#etape2}
## Étape 2 : initialiser DVC et son stockage

:::: lab Étape 2 | dvc init et dvc remote | 7 min
**1. Initialisez DVC** dans le dépôt. `dvc init` crée un dossier `.dvc` (configuration et cache) et un fichier `.dvcignore`. La deuxième commande désactive l'envoi de statistiques d'utilisation anonymes à l'éditeur de DVC.

```bash title="Terminal JupyterLab"
dvc init
dvc config core.analytics false
```

**2. Déclarez un stockage distant.** En entreprise, ce serait un compartiment S3, un conteneur Azure Blob ou un serveur partagé. Ici, un simple dossier : `~/dvc-stockage`. L'option `-d` en fait le stockage par défaut.

```bash title="Terminal JupyterLab"
dvc remote add -d stockage ~/dvc-stockage
cat .dvc/config
```

**Vérification :** `.dvc/config` contient une section `[core]` avec `analytics = false` et `remote = stockage`, puis une section pour le stockage `stockage` avec une ligne `url = /home/lab/projet/.home/dvc-stockage`.

**3. Enregistrez cette configuration dans Git.**

```bash title="Terminal JupyterLab"
git add .dvc .dvcignore
git commit -m "Initialiser DVC et son stockage"
```

::: hint
`~` désigne le dossier personnel du conteneur, `/home/lab/projet/.home`. Il est dans le dépôt, mais ignoré par Git (voir `.gitignore`) : le stockage survit à un redémarrage du conteneur sans polluer Git.
:::
::::

{#etape3}
## Étape 3 : versionner les données

:::: lab Étape 3 | La version 1 : 8 semaines de livraisons | 8 min
**1. Recréez les données** depuis le terminal, puis calculez leur empreinte avec `md5sum`.

```bash title="Terminal JupyterLab"
python -m colisvert.donnees data
md5sum data/livraisons.csv
```

```plaintext title="Sortie attendue"
livraisons.csv : 5035 colis, dont 862 en retard
arrivees.csv : 56 jours
livraisons_brutes.csv : les mêmes colis, avec des défauts de qualité
127f20d4baf2636267145a03529220f1  data/livraisons.csv
```

**2. Confiez le fichier à DVC.** `dvc add` copie le fichier dans le cache, écrit le ticket `data/livraisons.csv.dvc`, et ajoute le fichier à `data/.gitignore` pour que Git l'ignore. DVC termine en vous suggérant la commande `git add` à lancer.

```bash title="Terminal JupyterLab"
dvc add data/livraisons.csv
cat data/livraisons.csv.dvc
cat data/.gitignore
```

Le ticket contient l'empreinte et la taille du fichier, en octets :

```yaml title="data/livraisons.csv.dvc (attendu)"
outs:
- md5: 127f20d4baf2636267145a03529220f1
  size: 320537
  hash: md5
  path: livraisons.csv
```

et `data/.gitignore` contient la ligne `/livraisons.csv`.

**3. Versionnez le ticket avec Git, puis envoyez les données au stockage.**

```bash title="Terminal JupyterLab"
git add data/livraisons.csv.dvc data/.gitignore
git commit -m "Données v1 : 8 semaines"
dvc push
find ~/dvc-stockage -type f
```

**Vérification :** `dvc push` annonce `1 file pushed` (un fichier envoyé), et `find` montre un fichier dont le chemin se termine par `127f20d4baf2636267145a03529220f1` découpé en deux : un dossier `12`, puis un fichier `7f20d4baf2636267145a03529220f1`. DVC range les fichiers **par empreinte**, pas par nom.
::::

{#etape4}
## Étape 4 : une nouvelle version

:::: lab Étape 4 | La version 2 : une semaine de plus | 7 min
Une semaine a passé : le fichier contient maintenant **9 semaines**. Les 8 premières sont identiques ; la 9e s'ajoute à la fin.

```bash title="Terminal JupyterLab"
python -c "from colisvert.donnees import generer_livraisons, ecrire_csv; ecrire_csv(generer_livraisons(nb_jours=63), 'data/livraisons.csv')"
wc -l data/livraisons.csv
dvc status
```

```plaintext title="Sortie attendue (wc -l)"
5628 data/livraisons.csv
```

5 627 colis plus la ligne d'en-tête. `dvc status` signale que `data/livraisons.csv` a changé depuis son dernier `dvc add`.

**Enregistrez la version 2**, exactement comme la version 1 :

```bash title="Terminal JupyterLab"
dvc add data/livraisons.csv
git diff data/livraisons.csv.dvc
git commit -am "Données v2 : 9 semaines"
dvc push
```

**Vérification :** sous l'en-tête de `git diff`, deux lignes commencent par `-` (l'ancienne empreinte `127f20d4…` et l'ancienne taille `320537`) et deux par `+` (la nouvelle empreinte `71d9f04a390a607f350ac7d26df037b6` et la nouvelle taille `358204`). Seul le **ticket** a changé dans Git : 2 lignes, pas 600 lignes de CSV.
::::

{#etape5}
## Étape 5 : voyager dans le temps

:::: lab Étape 5 | Revenir à la version 1, puis à la version 2 | 8 min
**1. Regardez l'historique.** `--format=%s` n'affiche que le message de chaque commit, `-3` les trois derniers.

```bash title="Terminal JupyterLab"
git log --format=%s -3
```

```plaintext title="Sortie attendue"
Données v2 : 9 semaines
Données v1 : 8 semaines
Initialiser DVC et son stockage
```

**2. Revenez à la version 1.** Deux temps, comme au vestiaire : Git ressort l'**ancien ticket** (celui du commit précédent, `HEAD~1`), puis DVC va chercher le **manteau** correspondant dans son cache.

```bash title="Terminal JupyterLab"
git checkout HEAD~1 -- data/livraisons.csv.dvc
dvc checkout data/livraisons.csv.dvc
wc -l data/livraisons.csv
md5sum data/livraisons.csv
```

```plaintext title="Sortie attendue (wc et md5sum)"
5036 data/livraisons.csv
127f20d4baf2636267145a03529220f1  data/livraisons.csv
```

Le fichier est **exactement** celui de la version 1 : même nombre de lignes, même empreinte.

**3. Revenez à la version 2**, celle du dernier commit (`HEAD`).

```bash title="Terminal JupyterLab"
git checkout HEAD -- data/livraisons.csv.dvc
dvc checkout data/livraisons.csv.dvc
wc -l data/livraisons.csv
```

```plaintext title="Sortie attendue (wc -l)"
5628 data/livraisons.csv
```

::: hint
`dvc checkout` refuse d'écraser le fichier, ou rien ne change ? Vérifiez d'abord que le ticket a bien changé : `cat data/livraisons.csv.dvc` doit montrer l'empreinte de la version voulue. Une erreur dit que le fichier ou le ticket est introuvable : vous n'êtes pas dans `/home/lab/projet` (tapez `cd /home/lab/projet`).
:::

::: solution Ce qu'il faut retenir
| Je veux… | Git | DVC |
|---|---|---|
| Enregistrer une version | `git add` puis `git commit` le ticket | `dvc add` le fichier, puis `dvc push` |
| Revenir à une version | `git checkout <commit> -- fichier.dvc` | `dvc checkout` |
| Récupérer les données sur une autre machine | `git clone` ou `git pull` | `dvc pull` |

**La règle d'or :** les deux vont ensemble. Un `git commit` sans `dvc push`, c'est un ticket sans manteau au vestiaire : votre collègue aura le ticket, mais pas les données.
:::
::::

::: callout warn Attention avec le notebook du matin
La Cellule 1 du matin (`preparer_donnees()`) réécrit `data/livraisons.csv` en version 8 semaines. Si vous la relancez, `dvc status` signalera un changement. Pour retrouver la version enregistrée : `dvc checkout data/livraisons.csv.dvc`.
:::

::: callout tip Question fréquente : « Et pour des données dans une base, ou de plusieurs téraoctets ? »
DVC convient très bien aux fichiers (CSV, Parquet, images, modèles) jusqu'à plusieurs centaines de gigaoctets. Pour des tables de plusieurs téraoctets mises à jour en continu, on versionne plutôt **dans le format de stockage** lui-même : c'est le voyage dans le temps de Delta Lake, que vous verrez le jour 5.
:::

{#avance}
## Pour aller plus loin : comment DVC range le vestiaire

Ce bloc est pour les profils avancés ; rien ici n'est exigé dans l'évaluation.

**Le cache est adressé par le contenu** (*content-addressable storage*), exactement comme le stockage interne de Git : le nom d'un fichier dans le cache **est** son empreinte. Cette idée simple a trois conséquences puissantes :

- **La déduplication est automatique.** Dix tickets peuvent pointer la même empreinte : le fichier n'existe qu'une fois dans le cache et une fois dans le stockage distant. Revenir à la version 1 n'a rien retéléchargé : l'empreinte `127f20d4…` était déjà dans le cache.
- **L'intégrité est vérifiable.** Si un octet du cache est corrompu, l'empreinte recalculée ne correspond plus au nom du fichier : DVC le détecte au lieu de livrer silencieusement des données fausses.
- **Un même contenu sous deux noms ne coûte qu'une place.** Renommer un fichier de données ne duplique rien.

**Pourquoi `dvc add` est-il rapide même sur de gros fichiers ?** Parce que DVC évite de copier quand il peut **lier**. Selon le système de fichiers, il choisit automatiquement parmi quatre stratégies (`cache.type`) :

| Stratégie | Ce que c'est | À savoir |
|---|---|---|
| `reflink` | Une copie « paresseuse » : les octets ne sont dupliqués que si l'un des deux fichiers change | Le meilleur des mondes, mais il faut un système de fichiers qui le permet (XFS, Btrfs, APFS) |
| `hardlink` | Deux noms pour le même contenu sur le disque | Instantané et sans double stockage, mais **modifier le fichier corromprait le cache** : DVC le protège en le rendant accessible en lecture seule |
| `symlink` | Un raccourci vers le cache | Mêmes vertus et mêmes précautions que le lien dur |
| `copy` | Une vraie copie | Le plus lent et le plus gourmand, mais toujours sûr : c'est souvent le choix par défaut sur ext4 |

C'est pour cela que la documentation de DVC recommande, sur les très gros jeux de données, de ne **jamais modifier un fichier suivi en place**, mais de le remplacer (comme l'a fait notre `ecrire_csv`) ou de configurer `cache.type` explicitement.

**`.dvc` ou `dvc.lock` ?** Vous avez créé aujourd'hui des tickets `.dvc`, un par fichier suivi à la main. Demain, le pipeline (`dvc.yaml`) produira ses sorties lui-même : leurs empreintes seront alors notées dans un fichier unique, **`dvc.lock`**, écrit par `dvc repro`. Même mécanique de vestiaire, mais le ticket est rédigé par le pipeline, plus par vous : c'est lui qui prouvera que telle version du modèle vient de telle version des données.

**Les trois pièges classiques en équipe**, à connaître avant d'y mettre les doigts :

1. **Le push oublié.** Le ticket part avec `git push`, les données ne partent qu'avec `dvc push`. Le collègue qui fait `git pull` puis `dvc pull` reçoit alors `WARNING: Some of the cache files do not exist`. Le réflexe : vérifier avec `dvc status --cloud`, qui compare le cache local au stockage distant. En entreprise, on ajoute un garde-fou en CI qui refuse un commit dont les données ne sont pas poussées.
2. **Deux versions en même temps.** Deux personnes font `dvc add` du même fichier sur deux branches : Git signalera un **conflit sur le ticket** (deux empreintes pour `md5:`). C'est sain : le conflit est visible et se résout en choisissant une empreinte, ou en régénérant les données après fusion. Ce qu'il ne faut pas faire : choisir une empreinte « au hasard » sans savoir quelle version elle désigne ; le message de commit du ticket est là pour ça.
3. **Le stockage partagé sans ménage.** Le stockage distant accumule **toutes** les versions : c'est le but, mais il enfle. La commande `dvc gc` (garbage collect) supprime les contenus que plus aucun ticket des branches choisies ne référence ; on ne la lance qu'avec les options qui protègent l'historique voulu, et jamais à la légère sur un stockage commun.

{#quiz}
## Quiz de validation

```quiz
- q: Que contient le fichier data/livraisons.csv.dvc ?
  options:
    - Une copie compressée des données
    - L'empreinte et la taille du fichier de données, et son nom
    - Le code qui a produit les données
    - La liste des colis en retard
  answer: 1
  explain: C'est le ticket du vestiaire. Il pèse quelques octets, et c'est lui que Git versionne.
- q: Pourquoi vos empreintes MD5 sont-elles identiques à celles de vos voisins ?
  options:
    - Parce que DVC utilise la même graine pour tout le monde
    - Parce que vos fichiers ont exactement le même contenu
    - Parce que l'empreinte ne dépend que du nom du fichier
    - Par hasard
  answer: 1
  explain: L'empreinte est calculée à partir du contenu. Les données sont générées de façon déterministe, donc identiques partout.
- q: Pour revenir à la version 1 des données, quelles commandes faut-il ?
  options:
    - dvc push puis git push
    - git checkout de l'ancien ticket, puis dvc checkout
    - git revert puis git push
    - dvc add puis dvc commit
  answer: 1
  explain: Git ressort l'ancien ticket, DVC va chercher le fichier correspondant dans son cache.
- q: Un collègue fait git pull et obtient le ticket de la version 2, mais pas les données. Qu'a-t-on oublié ?
  options: [git commit, dvc push, dvc init, git switch]
  answer: 1
  explain: Le ticket est dans Git, mais les données ne sont pas parties au stockage. Ensuite, le collègue devra lancer dvc pull.
```
