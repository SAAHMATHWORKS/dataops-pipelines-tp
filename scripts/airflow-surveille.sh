#!/usr/bin/env bash
# Lance « airflow standalone » et surveille son planificateur (commande du service airflow).
#
# airflow standalone démarre ses composants (planificateur, API, traitement des DAG,
# déclencheur), mais ne relance pas un composant qui s'arrête. Avec la base SQLite, le
# planificateur peut s'arrêter sur une erreur d'écriture concurrente (vu en vérification :
# « FOREIGN KEY constraint failed », puis « ObjectDeletedError ») ; les runs restent alors
# « queued » indéfiniment, sans message dans l'interface.
#
# Ce script vérifie toutes les 10 secondes que le planificateur tourne. S'il a disparu
# trois fois de suite, il arrête Airflow et sort en erreur : Docker relance le conteneur
# (restart: unless-stopped), et les runs en file reprennent. En production, on utilise
# PostgreSQL et un planificateur supervisé (Kubernetes, systemd) plutôt que ce script.
set -u

airflow standalone &
principal=$!
trap 'kill "$principal" 2>/dev/null; wait "$principal"; exit 0' TERM INT

planificateur_actif() {
  local processus
  for processus in /proc/[0-9]*; do
    # « schedule[r] » : le motif ne se reconnaît pas lui-même dans la ligne de commande de grep.
    tr '\0' ' ' 2>/dev/null < "$processus/cmdline" | grep -q "bin/airflow schedule[r]" && return 0
  done
  return 1
}

attendre() { sleep "$1" & wait $!; }   # interruptible par docker stop

attendre 90                             # premier démarrage : migration de la base, puis composants
absences=0
while kill -0 "$principal" 2>/dev/null; do
  if planificateur_actif; then absences=0; else absences=$((absences + 1)); fi
  if [ "$absences" -ge 3 ]; then
    echo "SURVEILLANCE : le planificateur d'Airflow s'est arrêté ; redémarrage du conteneur." >&2
    kill "$principal" 2>/dev/null
    wait "$principal" 2>/dev/null
    exit 1
  fi
  attendre 10
done
wait "$principal"
