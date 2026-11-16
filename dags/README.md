# dags/

Le dossier que lit Airflow (variable `AIRFLOW__CORE__DAGS_FOLDER` du service `airflow`
dans `docker-compose.yml`). Vos DAG du jour 3 après-midi s'écrivent ici ; ils se versionnent
dans Git comme le reste du code.

Les corrigés sont dans `solutions/airflow/` : ne les copiez ici qu'en cas de blocage, car deux
fichiers qui déclarent le même `dag_id` produisent une erreur d'import.
