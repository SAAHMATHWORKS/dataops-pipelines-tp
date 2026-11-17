#!/usr/bin/env bash
# Rejoue le parcours des jours 1 à 5 dans l'image des TP, avec un vrai serveur MLflow,
# et vérifie les chiffres annoncés dans le support. Lancé par GitHub Actions
# (.github/workflows/verifier-pipeline.yml), ou à la main, depuis la racine du dépôt :
#
#   docker run --rm --add-host mlflow:127.0.0.1 -v "$PWD":/home/lab/projet -w /home/lab/projet \
#     ghcr.io/saahmathworks/dataops-lab:2026.12 bash verification/verifier_pipeline.sh
#
# Les commandes sont celles des TP, dans le même ordre. Si le dossier verification/support
# contient les pages du support (Markdown), leurs cellules Python sont aussi exécutées et
# comparées à leurs « Sortie attendue ». Toute différence fait échouer le script.
set -uo pipefail
cd "$(dirname "$0")/.."
RACINE=$(pwd)
SUPPORT=verification/support
ECHECS=0
echec() { echo "ÉCHEC : $*"; ECHECS=$((ECHECS + 1)); }
titre() { echo; echo "=================== $*"; }

export HOME=/tmp/maison-ci
mkdir -p "$HOME"
git config --global --add safe.directory '*'
git config --global user.name "Stagiaire DataOps"
git config --global user.email "stagiaire@colisvert.example"
git config --global init.defaultBranch main
export MLFLOW_TRACKING_URI=http://mlflow:5000
export GARDER_DATA=1
export PYTHONPATH="$RACINE"

titre "Versions"
python -c "import sys, pandas, sklearn, mlflow, dvc, optuna, evidently; print(sys.version.split()[0], '| pandas', pandas.__version__, '| scikit-learn', sklearn.__version__, '| mlflow', mlflow.__version__, '| dvc', dvc.__version__, '| optuna', optuna.__version__, '| evidently', evidently.__version__)"

titre "Serveur MLflow (comme le service mlflow de docker-compose.yml)"
# Même emplacement que le service mlflow de docker-compose.yml (.mlflow/ dans le dépôt) :
# verifier_airflow.sh, lancé ensuite avec docker compose, retrouve ainsi le registre du jour 2.
mkdir -p /tmp/mlflow .mlflow
MLFLOW_SERVER_ALLOWED_HOSTS="mlflow:5000,localhost:*,127.0.0.1:*" \
  mlflow server --backend-store-uri sqlite:///$RACINE/.mlflow/mlflow.db \
  --artifacts-destination $RACINE/.mlflow/artifacts --host 0.0.0.0 --port 5000 > /tmp/mlflow-serveur.log 2>&1 &
for _ in $(seq 1 60); do curl -s -o /dev/null http://127.0.0.1:5000/health && break; sleep 2; done
curl -s -o /dev/null -w "Host mlflow:5000 -> HTTP %{http_code}\n" http://mlflow:5000/health || echec "serveur MLflow injoignable"

titre "Contrôle : sans MLFLOW_SERVER_ALLOWED_HOSTS, le nom d'hôte mlflow est-il refusé ?"
mlflow server --backend-store-uri sqlite:////tmp/mlflow/temoin.db --host 0.0.0.0 --port 5002 > /tmp/mlflow-temoin.log 2>&1 &
for _ in $(seq 1 60); do curl -s -o /dev/null http://127.0.0.1:5002/health && break; sleep 2; done
curl -s -o /dev/null -w "défaut, Host localhost:5002 -> HTTP %{http_code}\n" -H "Host: localhost:5002" http://127.0.0.1:5002/api/2.0/mlflow/experiments/search?max_results=1
curl -s -o /dev/null -w "défaut, Host mlflow:5002    -> HTTP %{http_code}\n" -H "Host: mlflow:5002" http://127.0.0.1:5002/api/2.0/mlflow/experiments/search?max_results=1

support() {
  # support <fichiers…> : exécute les cellules Python des pages du support, si le dossier
  # de la demi-journée est présent (on peut ne copier qu'une demi-journée pour l'essayer).
  local dossier
  dossier=$(dirname "$1")
  if [ -d "$dossier" ]; then
    python verification/verifier_sorties.py . "$@" || echec "cellules du support : $*"
  else
    echo "(pas de pages du support dans $dossier : cellules non vérifiées)"
  fi
}

titre "Jour 1 après-midi : DVC et Git (TP)"
git switch -c tp-dvc
dvc init -q
dvc config core.analytics false
dvc remote add -d stockage ~/dvc-stockage
git add .dvc .dvcignore
git commit -q -m "Initialiser DVC et son stockage"
python -m colisvert.donnees data
md5sum data/livraisons.csv
dvc add data/livraisons.csv
git add data/livraisons.csv.dvc data/.gitignore
git commit -q -m "Données v1 : 8 semaines"
dvc push
python -c "from colisvert.donnees import generer_livraisons, ecrire_csv; ecrire_csv(generer_livraisons(nb_jours=63), 'data/livraisons.csv')"
dvc add data/livraisons.csv
git commit -q -am "Données v2 : 9 semaines"
dvc push

titre "Jour 2 matin : cellules des notions 0 à 4"
# Sans les pages du J2 matin, on régénère les données de 8 semaines comme le ferait leur Cellule 0.
if [ -d "$SUPPORT/j2-matin" ]; then
  support $SUPPORT/j2-matin/index.md $SUPPORT/j2-matin/01-*.md $SUPPORT/j2-matin/02-*.md \
          $SUPPORT/j2-matin/03-*.md $SUPPORT/j2-matin/04-*.md
else
  python -m colisvert.donnees data
fi

titre "Jour 2 matin : TP, étape 1"
md5sum data/livraisons.csv
dvc status
dvc add data/livraisons.csv
git add data/livraisons.csv.dvc
git commit -q -m "Données : retour aux 8 semaines pour le modèle"

titre "Jour 2 matin : TP, étapes 2 et 3"
cat > params.yaml <<'EOF'
prepare:
  date_coupure: "2026-10-19"

train:
  C: 1.0
  class_weight: null
  max_iter: 1000
EOF
cat params.yaml
cat > dvc.yaml <<'EOF'
stages:
  prepare:
    cmd: python -m pipeline.prepare
    deps:
      - data/livraisons.csv
      - pipeline/prepare.py
      - pipeline/commun.py
    params:
      - prepare.date_coupure
    outs:
      - data/prepared

  train:
    cmd: python -m pipeline.train
    deps:
      - data/prepared
      - pipeline/train.py
      - pipeline/commun.py
    params:
      - train.C
      - train.class_weight
      - train.max_iter
    outs:
      - models/modele.joblib

  evaluate:
    cmd: python -m pipeline.evaluate
    deps:
      - models/modele.joblib
      - data/prepared
      - pipeline/evaluate.py
    metrics:
      - metrics.json:
          cache: false
EOF

titre "Jour 2 matin : TP, étape 4 (dvc repro)"
dvc repro || echec "dvc repro"
dvc metrics show
python - <<'PY' || echec "métriques v1"
import json
obtenu = json.load(open("metrics.json"))
attendu = json.load(open("verification/metrics.attendu.json"))
assert obtenu == attendu, f"métriques v1 : {obtenu} au lieu de {attendu}"
print("métriques v1 conformes au support")
PY

titre "Jour 2 matin : TP, étape 6 (git et dvc push)"
git status --short
git add dvc.yaml dvc.lock params.yaml metrics.json data/.gitignore models/.gitignore || echec "git add"
git commit -q -m "Pipeline v1 : prepare, train, evaluate"
dvc push

titre "Jour 2 matin : TP, étape 7 (relancer sans rien changer)"
dvc repro | tee /tmp/repro-a-jour.txt
grep -q "Data and pipelines are up to date" /tmp/repro-a-jour.txt || echec "dvc repro aurait dû être à jour"
dvc dag

titre "Jour 2 matin : TP, étape 8"
support $SUPPORT/j2-matin/05-*.md

titre "Jour 2 matin : évaluation, étape 3"
git switch -c eval-balanced
sed -i 's/class_weight: null/class_weight: balanced/' params.yaml
dvc repro | tee /tmp/repro-variante.txt
grep -q "Stage 'prepare' didn't change" /tmp/repro-variante.txt || echo "AVERTISSEMENT : message de saut de prepare non retrouvé"
dvc metrics diff
git commit -q -am "Variante : class_weight balanced"
git switch tp-dvc
dvc checkout
dvc metrics show
python - <<'PY' || echec "retour sur tp-dvc"
import json
assert json.load(open("metrics.json")) == json.load(open("verification/metrics.attendu.json"))
print("retour sur tp-dvc : métriques v1")
PY

titre "Jour 2 matin : évaluation, cellules"
support $SUPPORT/j2-matin/06-*.md

titre "Jour 2 après-midi : redémarrage"
git switch tp-dvc
dvc checkout
dvc metrics show

titre "Jour 2 après-midi : projet MLflow"
mlflow run . -P C=0.1 -P class_weight=balanced --env-manager local --experiment-name colisvert-retards \
  || echec "mlflow run"
python - <<'PY' || echec "run du projet"
import json
import mlflow
run = mlflow.search_runs(experiment_names=["colisvert-retards"], filter_string="params.C = '0.1'",
                         order_by=["attributes.start_time DESC"], max_results=1).iloc[0]
metriques = {k[8:]: run[k] for k in run.index if k.startswith("metrics.")}
print("paramètres :", {k[7:]: run[k] for k in run.index if k.startswith("params.")})
print("tags :", {k[5:]: run[k] for k in run.index if k.startswith("tags.") and run[k] is not None})
attendu = json.load(open("verification/metrics.attendu.v2.json"))
assert {k: metriques[k] for k in attendu} == attendu, f"{metriques} au lieu de {attendu}"
print("métriques du projet conformes au support (v2)")
PY

titre "Jour 2 après-midi : recherche d'hyperparamètres (grille et hasard)"
python verification/verifier_recherche.py || echec "recherche"

titre "Jour 2 après-midi : cellules des notions 0 à 5"
export AVANT_BLOC="Cellule 12::bash verification/servir_champion.sh"
support $SUPPORT/j2-apres-midi/index.md $SUPPORT/j2-apres-midi/0[1-5]-*.md
unset AVANT_BLOC

titre "Jour 2 après-midi : évaluation"
support $SUPPORT/j2-apres-midi/06-*.md

titre "Jour 3 matin : données des taxis (dvc import-url)"
git switch tp-dvc
git status --short
mkdir -p data/taxis
dvc import-url https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2024-01.parquet data/taxis/ \
  || echec "import des courses de taxi"
dvc import-url https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv data/taxis/ \
  || echec "import des zones de taxi"
md5sum data/taxis/yellow_tripdata_2024-01.parquet data/taxis/taxi_zone_lookup.csv
cat data/taxis/yellow_tripdata_2024-01.parquet.dvc
git add data/taxis/*.dvc data/taxis/.gitignore
git commit -q -m "Données externes : taxis de New York, janvier 2024"
python - <<'PY' || echec "empreintes des taxis"
import hashlib
attendu = {
    "data/taxis/yellow_tripdata_2024-01.parquet": "10dff36f5a2fc325274438bf361c70f0",
    "data/taxis/taxi_zone_lookup.csv": "c6064b7c144c716450641f769659d178",
}
for chemin, md5 in attendu.items():
    obtenu = hashlib.md5(open(chemin, "rb").read()).hexdigest()
    assert obtenu == md5, f"{chemin} : {obtenu} au lieu de {md5} (la TLC a-t-elle republié le fichier ?)"
print("empreintes des taxis conformes au support du jour 3")
PY

titre "Jour 3 matin : cellules du support"
support $SUPPORT/j3-matin/index.md $SUPPORT/j3-matin/0[1-5]-*.md
support $SUPPORT/j3-matin/06-*.md

titre "Jour 4 matin : cellules du support (indépendantes de l'état du dépôt)"
support $SUPPORT/j4-matin/index.md $SUPPORT/j4-matin/0[1-6]-*.md

titre "Jour 4 après-midi : empreinte, Optuna et service PyFunc (cellules du support)"
# Noms propres au jour 4 (expérience j4-empreinte, modèles colisvert-empreinte et colisvert-service) :
# les cellules ne dépendent pas de l'état du registre laissé par les jours 2 et 3.
export AVANT_BLOC="Cellule 17::bash verification/servir_service.sh"
support $SUPPORT/j4-apres-midi/index.md $SUPPORT/j4-apres-midi/0[1-6]-*.md
unset AVANT_BLOC

titre "Jour 5 matin : gouvernance, Delta Lake avec Spark, IA responsable (cellules du support)"
# Noms propres au jour 5 (lakehouse/, expérience j5-ia-responsable) : indépendant de l'état du dépôt.
support $SUPPORT/j5-matin/index.md $SUPPORT/j5-matin/0[1-6]-*.md

titre "Jour 5 après-midi : LLM et agents, contre le LLM simulé (cellules du support)"
# Le TP appelle la passerelle LLM de Training Lab ; ici, le LLM simulé du dépôt la remplace
# (même adresse en /api/llm/v1, mêmes refus), et les sorties « avec le LLM simulé » sont comparées.
python -m colisvert.llm_simule --port 8090 > /tmp/llm-simule.log 2>&1 &
LLM_SIMULE=$!
for _ in $(seq 1 30); do curl -s -o /dev/null http://127.0.0.1:8090/api/llm/v1/quota && break; sleep 1; done
export LLM_PASSERELLE=http://127.0.0.1:8090/api/llm/v1 LLM_JETON=jeton-de-la-verification
support $SUPPORT/j5-apres-midi/index.md $SUPPORT/j5-apres-midi/0[1-8]-*.md
unset LLM_PASSERELLE LLM_JETON
kill "$LLM_SIMULE" 2>/dev/null || true

titre "Registre en fin de parcours"
python - <<'PY'
from mlflow import MlflowClient
client = MlflowClient()
for v in sorted(client.search_model_versions("name = 'colisvert-retards'"), key=lambda v: int(v.version)):
    complet = client.get_model_version("colisvert-retards", v.version)
    print(f"v{v.version} : alias {sorted(complet.aliases)} (search_model_versions : {sorted(v.aliases)})")
PY

echo
if [ "$ECHECS" -eq 0 ]; then
  echo "TOUT EST CONFORME."
else
  echo "$ECHECS ÉCHEC(S) : voir les messages ÉCHEC et DIFFÉRENCE ci-dessus."
  exit 1
fi
