#!/usr/bin/env bash
# Démarre en arrière-plan le service PyFunc de ColisVert (jour 4 après-midi, TP 2) sur le
# port 5001, puis attend qu'il réponde. Arrête d'abord un éventuel service déjà sur ce port
# (celui du champion, démarré au jour 2). Utilisé par la vérification, avant la cellule
# qui interroge le service.
set -euo pipefail
cd "$(dirname "$0")/.."

for processus in /proc/[0-9]*; do
  if tr '\0' ' ' < "$processus/cmdline" 2>/dev/null | grep -Eq "(--port|-p) 5001( |$)"; then
    kill "${processus#/proc/}" 2>/dev/null || true
  fi
done
for _ in $(seq 1 30); do curl -s -o /dev/null http://127.0.0.1:5001/ping || break; sleep 1; done

mlflow models serve -m "models:/colisvert-service@production" -p 5001 --env-manager local \
  > /tmp/service-colisvert.log 2>&1 &

for _ in $(seq 1 90); do
  if curl -s -o /dev/null http://127.0.0.1:5001/ping; then
    echo "service de ColisVert prêt sur le port 5001"
    exit 0
  fi
  sleep 2
done
echo "ERREUR : le service de ColisVert ne répond pas" >&2
cat /tmp/service-colisvert.log >&2
exit 1
