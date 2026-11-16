#!/usr/bin/env bash
# Rejoue le jour 3 après-midi (Airflow) avec docker compose, exactement comme sur la VM :
# services mlflow et airflow du fichier docker-compose.yml, cellules du support exécutées
# dans le service jupyter. Lancé par GitHub Actions APRÈS verifier_pipeline.sh, dans le
# même dossier : on repart de l'état laissé par les jours 1 à 3 matin (branche tp-dvc,
# pipeline DVC, registre MLflow dans .mlflow/).
#
# À lancer depuis la machine hôte (pas dans un conteneur), à la racine du dépôt :
#   bash verification/verifier_airflow.sh
set -uo pipefail
cd "$(dirname "$0")/.."
SUPPORT=verification/support
ECHECS=0
ECHECS_CELLULES=0   # comptées à part : une sortie de cellule fausse n'empêche pas la suite
echec() { echo "ÉCHEC : $*"; ECHECS=$((ECHECS + 1)); }
titre() {
  # Arrêt dès le premier échec : les étapes suivantes en dépendent, et leurs attentes seraient longues.
  if [ "$ECHECS" -gt 0 ]; then
    echo; echo "ARRÊT après $ECHECS échec(s)."; docker compose logs airflow 2>&1 | tail -60; exit 1
  fi
  echo; echo "=================== $*"
}
af() { docker compose exec -T airflow "$@"; }
runs() { af airflow dags list-runs "$1" -o json 2>/dev/null | python3 verification/airflow_runs.py "${@:2}"; }

cellules() {
  # cellules <fichiers…> : exécute les cellules Python des pages du support dans le service jupyter.
  if [ -d "$SUPPORT" ]; then
    # Les blocs de code des DAG et les extraits de scripts ne s'exécutent pas dans JupyterLab.
    docker compose run --rm -T -e GARDER_DATA=1 -e SAUTER='airflow\.sdk|def main\(|@dag\(' jupyter \
      python verification/verifier_sorties.py . "$@" \
      || { echo "ÉCHEC (cellules) : $*"; ECHECS_CELLULES=$((ECHECS_CELLULES + 1)); }
  else
    echo "(pas de pages du support dans $SUPPORT : cellules non vérifiées)"
  fi
}

attendre() {
  # attendre <dag_id> <run_id> [secondes] : attend la fin d'un run, puis affiche ses tâches.
  local dag=$1 run=$2 limite=${3:-600} etat=absent
  for _ in $(seq 1 $((limite / 5))); do
    etat=$(runs "$dag" etat "$run")
    case "$etat" in success|failed) break ;; esac
    sleep 5
  done
  echo "run $dag / $run : $etat"
  af airflow tasks states-for-dag-run "$dag" "$run" -o json 2>/dev/null | python3 verification/airflow_runs.py resume
  [ "$etat" = success ]
}

rattraper() {
  # rattraper <arguments de airflow backfill create> : relance tant qu'un rattrapage précédent
  # du même DAG n'est pas clos (« Another backfill is running »), au plus 3 minutes.
  local debut=$(date +%s) sortie
  for _ in $(seq 1 36); do
    sortie=$(af airflow backfill create "$@" 2>&1)
    if ! grep -q "AlreadyRunningBackfill" <<<"$sortie"; then
      echo "$sortie" | grep -vE "^\s*$" | tail -6
      echo "(rattrapage accepté après $(( $(date +%s) - debut )) s d'attente)"
      return 0
    fi
    sleep 5
  done
  echo "$sortie" | tail -3; return 1
}

journal() {
  # journal <dag_id> <run_id> <task_id> [tentative] : affiche le journal d'une tâche.
  local fichier=".airflow/logs/dag_id=$1/run_id=$2/task_id=$3/attempt=${4:-1}.log"
  if [ -f "$fichier" ]; then
    python3 - "$fichier" <<'PY'
import json, sys
for ligne in open(sys.argv[1], encoding="utf-8"):
    try:
        evenement = json.loads(ligne)
        print(evenement.get("event", ligne.rstrip()))
    except ValueError:
        print(ligne.rstrip())
PY
  else
    echo "(journal absent : $fichier)"; ls -R ".airflow/logs/dag_id=$1" 2>/dev/null | head -30
  fi
}

titre "Démarrage : services mlflow et airflow"
docker compose ps
for _ in $(seq 1 60); do
  curl -s -o /dev/null http://127.0.0.1:8080/api/v2/monitor/health && break
  sleep 5
done
curl -s http://127.0.0.1:8080/api/v2/monitor/health; echo
af airflow version
af bash -c 'which python dvc mlflow airflow; python --version; python -c "import sklearn, pandas; print(sklearn.__version__, pandas.__version__)"'
af airflow config get-value core executor
docker compose logs airflow 2>&1 | grep -iE "password|login|executor|error" | head -20

titre "Notion 1 : cellules du support"
cellules $SUPPORT/j3-apres-midi/01-*.md $SUPPORT/j3-apres-midi/02-*.md

titre "Notion 2 : premier DAG (colisvert_fraicheur)"
mkdir -p dags
cp solutions/airflow/colisvert_fraicheur.py dags/
af airflow dags list-import-errors
./scripts/tester-dag.sh colisvert_fraicheur 2>&1 | tee /tmp/fraicheur.txt
if ! grep -q "fichier arrivé après 06:45 : 8 jours sur 56" /tmp/fraicheur.txt; then
  echec "fraîcheur 06:45 : Airflow ne fonctionne pas, arrêt de la vérification"
  docker compose logs airflow 2>&1 | tail -80
  exit 1
fi
./scripts/tester-dag.sh colisvert_fraicheur -c '{"heure_limite": "06:30"}' 2>&1 | tee /tmp/fraicheur-0630.txt
grep -q "fichier arrivé après 06:30 : 27 jours sur 56" /tmp/fraicheur-0630.txt || echec "fraîcheur 06:30"
af airflow dags list -o json 2>/dev/null | python3 verification/airflow_runs.py resume

titre "TP 1, étape 1 : le pipeline orchestré, état du jour 2"
git status --short
cat params.yaml
cp solutions/airflow/tp1/colisvert_pipeline.py dags/
af airflow dags list-import-errors
./scripts/tester-dag.sh colisvert_pipeline 2>&1 | tee /tmp/tp1-1.txt
grep -q "barrière fermée" /tmp/tp1-1.txt || echec "TP1 étape 1 : barrière fermée attendue"
runs colisvert_pipeline resume

titre "TP 1, étape 2 : le réglage du jour 2 (balanced, C=0.1)"
sed -i 's/class_weight: null/class_weight: balanced/; s/C: 1.0/C: 0.1/' params.yaml
cat params.yaml
./scripts/tester-dag.sh colisvert_pipeline 2>&1 | tee /tmp/tp1-2.txt
grep -q "barrière franchie" /tmp/tp1-2.txt || echec "TP1 étape 2 : barrière franchie attendue"
cat metrics.json
python3 - <<'PY' || echec "métriques v2 du pipeline orchestré"
import json
assert json.load(open("metrics.json")) == json.load(open("verification/metrics.attendu.v2.json"))
print("métriques v2 conformes")
PY

cellules $SUPPORT/j3-apres-midi/03-*.md

titre "TP 1, étape 3 : relancer sans rien changer (idempotence)"
./scripts/tester-dag.sh colisvert_pipeline 2>&1 | tee /tmp/tp1-3.txt
grep -q "déjà enregistré" /tmp/tp1-3.txt || echec "TP1 étape 3 : registre idempotent"

titre "TP 1, étape 4 : panne passagère de MLflow, réparée par les nouvelles tentatives"
af airflow dags unpause colisvert_pipeline
sleep 10
runs colisvert_pipeline resume
docker compose stop mlflow
af airflow dags trigger colisvert_pipeline -r panne_mlflow -o json 2>/dev/null | python3 verification/airflow_runs.py resume
for _ in $(seq 1 25); do
  etat=$(af airflow tasks states-for-dag-run colisvert_pipeline panne_mlflow -o json 2>/dev/null \
         | python3 verification/airflow_runs.py tache proposer_challenger)
  echo "proposer_challenger : $etat"
  [ "$etat" = up_for_retry ] && break
  sleep 3
done
docker compose start mlflow
attendre colisvert_pipeline panne_mlflow 300 || echec "TP1 étape 4 : le run aurait dû réussir après la nouvelle tentative"
journal colisvert_pipeline panne_mlflow proposer_challenger 1 | tail -15
journal colisvert_pipeline panne_mlflow proposer_challenger 2 | tail -8
af airflow dags pause colisvert_pipeline

titre "TP 1, étape 5 : des données invalides (le contrat arrête tout, sans nouvelle tentative)"
cp data/livraisons_brutes.csv data/livraisons.csv
./scripts/tester-dag.sh colisvert_pipeline 2>&1 | tee /tmp/tp1-5.txt
grep -q "Contrat violé" /tmp/tp1-5.txt || echec "TP1 étape 5 : le contrat aurait dû arrêter le pipeline"
docker compose run --rm -T jupyter bash -c "dvc checkout --force data/livraisons.csv.dvc && md5sum data/livraisons.csv && dvc status" \
  || echec "TP1 étape 5 : restauration des données avec dvc checkout"

titre "Notion 4 : un jour de taxis, puis le rattrapage de janvier 2024"
cp solutions/airflow/taxis_journalier.py dags/
af airflow dags list-import-errors
af airflow dags unpause taxis_journalier
sleep 10
echo "--- un seul jour : le 15 janvier"
af airflow backfill create --dag-id taxis_journalier --from-date 2024-01-15 --to-date 2024-01-15 2>&1 | grep -vE "^\s*$" | tail -12
attendre taxis_journalier "backfill__2024-01-16T00:00:00+00:00" 300 || echec "taxis : rattrapage du 15"
journal taxis_journalier "backfill__2024-01-16T00:00:00+00:00" indicateurs_du_jour 1 | grep -E "courses valides|écrit"
echo "--- le mois entier, à blanc"
af airflow backfill create --dag-id taxis_journalier --from-date 2024-01-01 --to-date 2024-01-31 --dry-run 2>&1 | grep -vE "^\s*$" > /tmp/dry.txt
head -14 /tmp/dry.txt; echo "[…]"; tail -4 /tmp/dry.txt; echo "lignes : $(wc -l < /tmp/dry.txt)"
echo "--- le mois entier"
debut=$(date +%s)
rattraper --dag-id taxis_journalier --from-date 2024-01-01 --to-date 2024-01-31 --max-active-runs 4 || echec "taxis : rattrapage du mois refusé"
for _ in $(seq 1 120); do
  restants=$(runs taxis_journalier resume | grep -cE "state=(queued|running)")
  [ "$restants" -eq 0 ] && break
  sleep 5
done
echo "rattrapage terminé en $(( $(date +%s) - debut )) s"
echo "runs réussis : $(runs taxis_journalier resume | grep -c state=success)"
[ "$(ls rapports/taxis | wc -l)" -eq 31 ] || echec "taxis : 31 partitions attendues"
ls rapports/taxis | head -3; ls rapports/taxis | wc -l
md5sum rapports/taxis/jour=2024-01-15/indicateurs.parquet
cellules $SUPPORT/j3-apres-midi/04-*.md

titre "TP 2 : planification par les données (Assets)"
cp solutions/airflow/tp2/colisvert_pipeline.py solutions/airflow/tp2/colisvert_reception.py dags/
af airflow dags reserialize
af airflow dags list-import-errors
af airflow assets list 2>/dev/null
af airflow dags unpause colisvert_reception
af airflow dags unpause colisvert_pipeline
sleep 10
af airflow dags trigger colisvert_reception -r reception_semaine9 -o json 2>/dev/null | python3 verification/airflow_runs.py resume
attendre colisvert_reception reception_semaine9 300 || echec "TP2 : réception"
journal colisvert_reception reception_semaine9 publier | tail -10
for _ in $(seq 1 60); do
  declenche=$(runs colisvert_pipeline resume | grep -E "run_id=asset_triggered" | head -1)
  [ -n "$declenche" ] && break
  sleep 5
done
runs colisvert_pipeline resume
run_asset=$(runs colisvert_pipeline resume | grep -oE "run_id=asset_triggered[^ |]*" | head -1 | cut -d= -f2)
echo "run déclenché par l'Asset : ${run_asset:-aucun}"
[ -n "$run_asset" ] || echec "TP2 : aucun run déclenché par l'Asset"
if [ -n "$run_asset" ]; then
  attendre colisvert_pipeline "$run_asset" 600 || echec "TP2 : pipeline déclenché"
  journal colisvert_pipeline "$run_asset" origine | tail -8
  journal colisvert_pipeline "$run_asset" preparer | grep -vE "^##|Pre Execute|Post Execute|bundles|DagBag|startup parse|xcom" | tail -8
  journal colisvert_pipeline "$run_asset" entrainer | grep -vE "^##|Pre Execute|Post Execute|bundles|DagBag|startup parse|xcom|warn" | tail -12
  journal colisvert_pipeline "$run_asset" evaluer | grep -vE "^##|Pre Execute|Post Execute|bundles|DagBag|startup parse|xcom" | tail -20
  journal colisvert_pipeline "$run_asset" barriere_qualite | tail -10
  journal colisvert_pipeline "$run_asset" proposer_challenger | tail -8
  journal colisvert_pipeline "$run_asset" controler_donnees | tail -14
fi
cat metrics.json
git status --short
cellules $SUPPORT/j3-apres-midi/05-*.md
af airflow dags pause colisvert_pipeline
af airflow dags pause colisvert_reception

titre "Évaluation : le DAG taxis_qualite"
cp solutions/airflow/evaluation/taxis_qualite.py dags/
af airflow dags list-import-errors
af airflow dags unpause taxis_qualite
sleep 10
af airflow backfill create --dag-id taxis_qualite --from-date 2024-01-15 --to-date 2024-01-15 2>&1 | tail -3
attendre taxis_qualite "backfill__2024-01-16T00:00:00+00:00" 300 || echec "évaluation : le 15"
journal taxis_qualite "backfill__2024-01-16T00:00:00+00:00" compter_defauts 1 | grep -E "courses,|écrit"
rattraper --dag-id taxis_qualite --from-date 2024-01-01 --to-date 2024-01-07 --max-active-runs 4 || echec "évaluation : semaine refusée"
for _ in $(seq 1 60); do
  restants=$(runs taxis_qualite resume | grep -cE "state=(queued|running)")
  [ "$restants" -eq 0 ] && break
  sleep 5
done
runs taxis_qualite resume | sort
ls rapports/qualite
md5sum rapports/qualite/jour=2024-01-03/defauts.parquet
rattraper --dag-id taxis_qualite --from-date 2024-01-03 --to-date 2024-01-03 --reprocess-behavior completed || echec "évaluation : retraitement du 3 refusé"
sleep 5
for _ in $(seq 1 30); do
  restants=$(runs taxis_qualite resume | grep -cE "state=(queued|running)")
  [ "$restants" -eq 0 ] && break
  sleep 5
done
ls rapports/qualite | wc -l
md5sum rapports/qualite/jour=2024-01-03/defauts.parquet
cellules $SUPPORT/j3-apres-midi/06-*.md
echo "--- le piège du test manuel : airflow dags test taxis_qualite 2024-01-20 traite le 19"
./scripts/tester-dag.sh taxis_qualite 2024-01-20 2>&1 | tee /tmp/piege.txt
grep -q "2024-01-19 :" /tmp/piege.txt || echec "piège du test manuel"
af airflow dags pause taxis_qualite

titre "Registre en fin de parcours"
docker compose run --rm -T jupyter python - <<'PY'
from mlflow import MlflowClient
client = MlflowClient()
for v in sorted(client.search_model_versions("name = 'colisvert-retards'"), key=lambda v: int(v.version)):
    complet = client.get_model_version("colisvert-retards", v.version)
    print(f"v{v.version} : alias {sorted(complet.aliases)}, tags {complet.tags}, run {complet.run_id is not None}")
PY

echo
ECHECS=$((ECHECS + ECHECS_CELLULES))
if [ "$ECHECS" -eq 0 ]; then
  echo "AIRFLOW : TOUT EST CONFORME."
else
  echo "AIRFLOW : $ECHECS ÉCHEC(S)."
  docker compose logs airflow 2>&1 | tail -80
  exit 1
fi
