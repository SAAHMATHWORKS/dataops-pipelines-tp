#!/usr/bin/env bash
# Écrit l'identité de l'utilisateur de la VM pour les conteneurs (appelé par demarrer.sh).
#
# Les conteneurs tournent avec l'UID et le GID de l'utilisateur de la VM (1001 chez M2i), pour que
# les fichiers créés lui appartiennent. Mais ce numéro n'existe pas dans l'image : sans nom
# d'utilisateur ni dossier personnel, DVC, Airflow et Java (donc Spark) refusent de démarrer.
# On écrit donc un /etc/passwd et un /etc/group minimaux, montés dans les conteneurs par
# docker-compose.yml, où « lab » porte l'UID et le GID de la VM.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p .home
printf "UID_HOTE=%s\nGID_HOTE=%s\n" "$(id -u)" "$(id -g)" > .env
printf "root:x:0:0:root:/root:/bin/bash\nlab:x:%s:%s:Stagiaire DataOps:/home/lab/projet/.home:/bin/bash\n" \
  "$(id -u)" "$(id -g)" > .home/passwd
printf "root:x:0:\nlab:x:%s:\n" "$(id -g)" > .home/group
