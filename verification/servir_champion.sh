#!/usr/bin/env bash
# Démarre en arrière-plan le service de prédiction du modèle champion (jour 2 après-midi),
# puis attend qu'il réponde. Utilisé par verifier_pipeline.sh, juste avant la cellule qui
# interroge le service.
set -euo pipefail
cd "$(dirname "$0")/.."

mlflow models serve -m "models:/colisvert-retards@champion" -p 5001 --env-manager local \
  > /tmp/service-champion.log 2>&1 &

for _ in $(seq 1 90); do
  if curl -s -o /dev/null http://127.0.0.1:5001/ping; then
    echo "service du champion prêt sur le port 5001"
    tail -n 5 /tmp/service-champion.log
    exit 0
  fi
  sleep 2
done
echo "ERREUR : le service du champion ne répond pas" >&2
cat /tmp/service-champion.log >&2
exit 1
