# Image des TP DataOps : JupyterLab + Python 3.12 + Java 17 (pour Spark) + Git.
# Construite par GitHub Actions et publiée sur ghcr.io/saahmathworks/dataops-lab.
FROM python:3.12-slim-bookworm

# Git pour le versioning, Java pour Spark (jour 5), procps pour la commande ps.
RUN apt-get update \
 && apt-get install -y --no-install-recommends git default-jre-headless procps curl \
 && rm -rf /var/lib/apt/lists/*
ENV JAVA_HOME=/usr/lib/jvm/default-java

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt \
 && pip freeze > /requirements.lock

# Le conteneur tourne avec l'UID de l'utilisateur de la VM (1001 chez M2i) :
# /home/lab doit donc être accessible à n'importe quel utilisateur.
RUN mkdir -p /home/lab/projet && chmod 1777 /home/lab
ENV PYTHONPATH=/home/lab/projet \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1
WORKDIR /home/lab/projet
EXPOSE 8888

# Pas de jeton : le port n'est ouvert que sur la VM elle-même (127.0.0.1, voir docker-compose.yml).
CMD ["jupyter", "lab", "--ip=0.0.0.0", "--port=8888", "--no-browser", \
     "--ServerApp.token=", "--ServerApp.password=", "--ServerApp.root_dir=/home/lab/projet"]
