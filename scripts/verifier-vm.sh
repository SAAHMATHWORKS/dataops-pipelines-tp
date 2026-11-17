#!/usr/bin/env bash
# Vérifie qu'une VM peut faire tourner les TP DataOps.
# À lancer sur la VM de TEST (ou la VM formateur), jamais sur les VM des stagiaires :
#   bash verifier-vm.sh
# Le script n'affiche aucun secret : pour un proxy, il dit seulement s'il est configuré.
# Il écrit un rapport verification-vm.txt dans le dossier courant.
set -uo pipefail

RAPPORT="verification-vm.txt"
OK=0
KO=0
exec > >(tee "$RAPPORT") 2>&1

ok()  { echo "  [OK]  $*"; OK=$((OK + 1)); }
ko()  { echo "  [KO]  $*"; KO=$((KO + 1)); }
info(){ echo "  [..]  $*"; }

echo "Vérification de la VM pour les TP DataOps — $(date '+%Y-%m-%d %H:%M')"
echo

echo "1. Système"
info "$(. /etc/os-release 2>/dev/null && echo "$PRETTY_NAME") · noyau $(uname -r) · $(uname -m)"
CPU=$(nproc)
RAM=$(awk '/MemTotal/ {printf "%d", $2 / 1024 / 1024}' /proc/meminfo)
DISQUE=$(df -BG --output=avail "$HOME" | tail -1 | tr -dc '0-9')
[ "$CPU" -ge 4 ] && ok "$CPU cœurs" || ko "$CPU cœurs (4 minimum)"
[ "$RAM" -ge 15 ] && ok "$RAM Go de RAM" || ko "$RAM Go de RAM (16 Go minimum)"
[ "$DISQUE" -ge 20 ] && ok "$DISQUE Go libres dans $HOME" || ko "$DISQUE Go libres dans $HOME (20 Go minimum)"
info "utilisateur $(id -un), UID $(id -u), GID $(id -g)"
echo

echo "2. Outils"
command -v git >/dev/null && ok "$(git --version)" || ko "git absent"
command -v curl >/dev/null && ok "curl présent" || ko "curl absent"
if command -v docker >/dev/null; then
  ok "$(docker --version)"
  if docker compose version >/dev/null 2>&1; then ok "$(docker compose version)"; else ko "docker compose (v2) absent"; fi
  if docker info >/dev/null 2>&1; then ok "Docker utilisable sans sudo"; else ko "docker info échoue : l'utilisateur n'est pas dans le groupe docker, ou le démon est arrêté"; fi
  DOCKER_ROOT=$(docker info --format '{{.DockerRootDir}}' 2>/dev/null || echo /var/lib/docker)
  DISQUE_DOCKER=$(df -BG --output=avail "$DOCKER_ROOT" 2>/dev/null | tail -1 | tr -dc '0-9')
  [ -n "$DISQUE_DOCKER" ] && { [ "$DISQUE_DOCKER" -ge 20 ] && ok "$DISQUE_DOCKER Go libres pour Docker ($DOCKER_ROOT)" || ko "$DISQUE_DOCKER Go libres pour Docker (20 Go minimum)"; }
else
  ko "docker absent"
fi
echo

echo "3. Proxy (valeurs masquées)"
for var in HTTPS_PROXY https_proxy HTTP_PROXY http_proxy NO_PROXY; do
  if [ -n "${!var:-}" ]; then info "$var est défini"; fi
done
[ -z "${HTTPS_PROXY:-}${https_proxy:-}${HTTP_PROXY:-}${http_proxy:-}" ] && info "aucun proxy défini"
echo

echo "4. Accès Internet (un code HTTP = le site répond)"
verifier_url() {
  local nom="$1" url="$2" code
  code=$(curl -sS -o /dev/null -m 15 -w "%{http_code}" "$url" 2>/dev/null)
  case "$code" in
    ""|000) ko "$nom : aucune réponse ($url)" ;;
    407)    ko "$nom : le proxy demande une authentification (407)" ;;
    403)    info "$nom répond 403 : à vérifier, un proxy filtre peut-être ce site ($url)" ;;
    *)      ok "$nom ($code)" ;;
  esac
}
verifier_url "GitHub"                 https://github.com
verifier_url "Registre GitHub ghcr.io" https://ghcr.io/v2/
verifier_url "Données des taxis de New York (jour 3)" https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv
verifier_url "Docker Hub"             https://registry-1.docker.io/v2/
verifier_url "PyPI"                   https://pypi.org/simple/pip/
verifier_url "Fichiers PyPI"          https://files.pythonhosted.org/
verifier_url "Maven Central (Delta Lake, jour 5)" https://repo1.maven.org/maven2/
verifier_url "Plateforme Training Lab" https://m2i-training-lab.kbc-sarl.com
echo

echo "5. Téléchargements réels"
if docker info >/dev/null 2>&1; then
  if docker pull -q hello-world >/dev/null 2>&1 && docker run --rm hello-world >/dev/null 2>&1; then
    ok "image hello-world téléchargée depuis Docker Hub et exécutée"
  else
    ko "impossible de télécharger ou d'exécuter hello-world depuis Docker Hub"
  fi
  if docker manifest inspect ghcr.io/saahmathworks/dataops-lab:2026.12 >/dev/null 2>&1; then
    ok "image des TP visible sur ghcr.io"
  else
    info "image des TP pas encore visible sur ghcr.io (normal tant qu'elle n'est pas publiée)"
  fi
  if docker manifest inspect ghcr.io/saahmathworks/dataops-lab:2026.12-airflow >/dev/null 2>&1; then
    ok "image Airflow des TP (jour 3) visible sur ghcr.io"
  else
    info "image Airflow des TP pas encore visible sur ghcr.io (normal tant qu'elle n'est pas publiée)"
  fi
fi
TMP_CLONE=$(mktemp -d)
if git clone -q --depth 1 https://github.com/SAAHMATHWORKS/dataops-pipelines-tp.git "$TMP_CLONE/depot" 2>/dev/null; then
  ok "git clone du dépôt des TP"
else
  info "git clone du dépôt des TP impossible (normal tant que le dépôt n'est pas publié)"
fi
rm -rf "$TMP_CLONE"
echo

echo "Bilan : $OK vérification(s) OK, $KO problème(s)."
echo "Rapport : $(pwd)/$RAPPORT"
echo "Nettoyage après le test : rm $RAPPORT && docker image rm hello-world"
[ "$KO" -eq 0 ]
