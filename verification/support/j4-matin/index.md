{#retour time="09:00 – 09:05"}
## Retour sur le jour 3

**Hier**, ColisVert a choisi ses outils avec méthode, mesuré trois moteurs sur les taxis de New York, puis confié son pipeline à Airflow. Le pipeline est maintenant **robuste** et démarre **à l'arrivée des données**. Le TP 2 a aussi montré une faiblesse : avec une date de coupure figée, réentraîner chaque matin n'apprenait rien de nouveau.

**Aujourd'hui, le jour 4 du programme : « Produire la valeur ».**

- **Ce matin**, les questions d'un responsable de produit data. Que livrer d'abord, et quand ? Combien rapporte le modèle, en euros ? Comment savoir, jour après jour, que le processus se dégrade ? Comment mesurer les bénéfices, et comment l'équipe s'améliore-t-elle ?
- **Cet après-midi**, deux TP d'ingénieur : réduire l'empreinte des modèles (processeur, mémoire, stockage) avec Optuna et MLflow, et servir plusieurs modèles derrière un seul point d'accès avec MLflow PyFunc.

{#mise-en-place time="09:05 – 09:10"}
## Mise en place

:::: lab Mise en place | Le notebook du jour | 5 min
Ce matin, tout se calcule dans un notebook, à partir du générateur de ColisVert : **rien à télécharger**, et les résultats ne dépendent pas de l'état de votre dépôt après le TP d'hier.

**1. Vérifiez que JupyterLab tourne** : http://localhost:8888. Sinon, dans un terminal de la VM :

```bash title="Terminal de la VM"
cd ~/dataops-pipelines-tp
./scripts/demarrer.sh
```

**2. Créez le notebook** `j4-matin.ipynb` dans le dossier `notebooks`, et vérifiez qu'il voit le code du dépôt :

```python title="Cellule 0 : le générateur est-il là ?"
from colisvert.donnees import generer_livraisons

print(f"{len(generer_livraisons())} colis de septembre-octobre")
```

```plaintext title="Sortie attendue"
5035 colis de septembre-octobre
```

::: hint
`ModuleNotFoundError: No module named 'colisvert'` : le notebook n'a pas été ouvert depuis le JupyterLab du conteneur. Relancez `./scripts/demarrer.sh` et rouvrez http://localhost:8888.
:::
::::
