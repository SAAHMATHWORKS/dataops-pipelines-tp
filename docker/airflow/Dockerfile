# Image Airflow des TP DataOps (jour 3 après-midi).
# Construite PAR-DESSUS l'image des TP : les tâches du pipeline tournent avec exactement les
# mêmes bibliothèques que JupyterLab (pandas, scikit-learn, DVC, MLflow, DuckDB…), donc un
# modèle entraîné par Airflow est identique, au bit près, à un modèle entraîné depuis un notebook.
# Publiée par GitHub Actions sous ghcr.io/saahmathworks/dataops-lab:2026.12-airflow.
ARG IMAGE_TP=ghcr.io/saahmathworks/dataops-lab:2026.12
FROM ${IMAGE_TP}

# Airflow a ses propres dépendances, nombreuses et figées : on l'installe dans un environnement
# virtuel séparé (/opt/airflow) pour qu'il ne modifie aucune bibliothèque du pipeline.
# Méthode officielle : toujours avec le fichier de contraintes de la version choisie.
# graphviz (la bibliothèque Python) évite un avertissement à chaque commande « airflow dags ».
ARG AIRFLOW_VERSION=3.4.0
RUN python -m venv /opt/airflow \
 && /opt/airflow/bin/pip install --no-cache-dir "apache-airflow==${AIRFLOW_VERSION}" graphviz \
      --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-3.12.txt" \
 && /opt/airflow/bin/pip freeze > /requirements-airflow.lock \
 && ln -s /opt/airflow/bin/airflow /usr/local/bin/airflow

# La commande airflow vient de /opt/airflow ; « python », « dvc » et « mlflow » restent ceux
# de l'image des TP (/usr/local/bin) : c'est eux que les tâches @task.bash appellent.
EXPOSE 8080
CMD ["airflow", "standalone"]
