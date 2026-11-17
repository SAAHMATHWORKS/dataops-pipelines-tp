{#redemarrage time="13:30 – 13:40"}
## Retour sur le matin et redémarrage

**Ce matin**, le diagnostic de ColisVert a montré trois choses : 17,1 % de colis en retard, deux définitions du mot « retard » qui donnent deux chiffres, et une chaîne de valeur où l'on attend 94 % du temps.

**Cet après-midi**, on se demande comment travailler autrement : avec quelles méthodes, quelle organisation, quels outils. Et on pose la première brique technique : **versionner les données**.

:::: lab Mise en place | Redémarrer l'environnement | 5 min
Si JupyterLab ne répond plus sur http://localhost:8888, relancez-le depuis un terminal de la VM :

```bash title="Terminal"
cd ~/dataops-pipelines-tp
./scripts/demarrer.sh
```

Puis, dans JupyterLab, créez un notebook `j1-apres-midi.ipynb` dans le dossier `notebooks`.

Le TP de l'après-midi se fait dans un **terminal de JupyterLab** (**File › New › Terminal**) : il s'ouvre directement dans le conteneur, où Git et DVC sont installés, dans le dossier du dépôt.

::: hint
JupyterLab ne démarre pas : `docker compose logs jupyter`, depuis `~/dataops-pipelines-tp`, montre pourquoi. Si votre machine a changé de réseau pendant la pause déjeuner, `docker compose restart jupyter` suffit souvent.
:::
::::
