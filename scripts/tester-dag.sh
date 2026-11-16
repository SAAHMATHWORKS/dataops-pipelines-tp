#!/usr/bin/env bash
# Teste un DAG tout de suite (airflow dags test, sans l'ordonnanceur) et résume sa sortie, très
# bavarde : chaque tâche, ce qu'elle écrit, ce qu'elle renvoie, puis l'état final des tâches.
# Dans un terminal de la VM, depuis le dossier du dépôt :
#   ./scripts/tester-dag.sh colisvert_fraicheur
#   ./scripts/tester-dag.sh colisvert_fraicheur -c '{"heure_limite": "06:30"}'
# Sortie complète, sans résumé : docker compose exec airflow airflow dags test colisvert_fraicheur
set -uo pipefail
cd "$(dirname "$0")/.."
docker compose exec -T airflow bash -c \
  'airflow dags test "$@" 2>&1 | python /home/lab/projet/scripts/resumer_test.py' _ "$@"
