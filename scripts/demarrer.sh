#!/usr/bin/env bash
# Démarre l'environnement des TP. À lancer depuis n'importe où : ./scripts/demarrer.sh
set -euo pipefail
cd "$(dirname "$0")/.."

# 1. Le conteneur doit écrire dans ce dossier avec les droits de l'utilisateur de la VM.
printf "UID_HOTE=%s\nGID_HOTE=%s\n" "$(id -u)" "$(id -g)" > .env
mkdir -p .home .mlflow .airflow data notebooks

# 2. Télécharge l'image si besoin, puis démarre JupyterLab en arrière-plan.
docker compose up -d jupyter

# 3. Attend que JupyterLab réponde (au plus 60 secondes).
for _ in $(seq 1 30); do
  if curl -s -o /dev/null http://127.0.0.1:8888/api; then
    echo "JupyterLab est prêt : http://localhost:8888"
    exit 0
  fi
  sleep 2
done
echo "JupyterLab ne répond pas encore. Regardez les messages avec : docker compose logs jupyter" >&2
exit 1
