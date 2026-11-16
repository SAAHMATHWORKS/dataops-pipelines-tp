"""Résume la sortie de « airflow dags test » (appelé par scripts/tester-dag.sh).

Garde : le début de chaque tâche, ce qu'elle affiche (print, sortie des commandes), ce qu'elle
renvoie, ses échecs ; puis l'état final de chaque tâche, lu dans la base d'Airflow.
Code de sortie : 0 si l'exécution a réussi, 1 sinon.
"""

import json
import re
import subprocess
import sys

LIGNE = re.compile(r"^\d{4}-\d\d-\d\dT[\d:.]+Z \[(?P<niveau>\w+)\s*\] (?P<message>.*)$")
LOGGER = re.compile(r"\s+\[(?P<logger>[\w.]+)\](?: \S+=\S*)*\s*$")
HORODATAGE = re.compile(r"^\d{4}/\d\d/\d\d \d\d:\d\d:\d\d ")
IGNORER = ("Running command:", "Output:", "Command exited with return code 0", "Tmp dir root location")
# Bruit omis du résumé : avertissements de MLflow sur les schémas, conseils de DVC après chaque étape.
BRUIT = ("UserWarning", "warnings.warn(", "To track the changes with git", "git add dvc.lock",
         "To enable auto staging", "dvc config core.autostage", "Use `dvc push`")

taches, dag_id, run_id, etat_run = [], None, None, None
dans_trace = False

for brute in sys.stdin:
    brute = brute.rstrip("\n")
    m = LIGNE.match(brute)
    if not m:
        # Une ligne sans horodatage : un print() de tâche, ou une trace d'erreur.
        if brute.startswith("Traceback"):
            dans_trace = True
        elif dans_trace or brute.startswith((" ", "airflow.", "During handling")) or not brute.strip():
            continue
        elif brute.startswith(("You might need", "Run `pip")):
            continue
        else:
            print(f"  │ {brute}")
        continue
    dans_trace = False
    niveau, message = m.group("niveau"), m.group("message")
    l = LOGGER.search(message)
    logger = l.group("logger") if l else ""
    if l:
        message = message[: l.start()].rstrip()
    if message.startswith("[DAG TEST] starting task_id="):
        tache = message.split("task_id=")[1].split()[0]
        taches.append(tache)
        print(f"▶ {tache}")
    elif "SubprocessHook" in logger:
        if message.startswith(IGNORER) or not message.strip() or any(b in message for b in BRUIT):
            continue
        if message.startswith("Command exited with return code"):
            print(f"  ✗ la commande a échoué (code {message.rsplit(' ', 1)[-1]})")
        else:
            print(f"  │ {HORODATAGE.sub('', message)}")
    elif message.startswith("Done. Returned value was:"):
        valeur = message.split(":", 1)[1].strip()
        print(f"  → renvoie {valeur if len(valeur) <= 70 else valeur[:67] + '...'}")
    elif message.startswith("Skipping downstream tasks") and "short_circuit" in logger:
        print("  ⏭ condition fausse : les tâches suivantes sont sautées")
    elif message == "Task failed with exception":
        print("  ✗ la tâche a échoué")
    elif message.startswith("DagRun Finished:"):
        dag_id = re.search(r"dag_id=([^,]+)", message).group(1)
        run_id = re.search(r"run_id=([^,]+)", message).group(1)
        etat_run = re.search(r"state=([^,]+)", message).group(1)

if run_id is None:
    print("Pas d'exécution : le DAG existe-t-il ? (airflow dags list-import-errors)")
    sys.exit(1)

try:
    sortie = subprocess.run(
        ["airflow", "tasks", "states-for-dag-run", dag_id, run_id, "-o", "json"],
        capture_output=True, text=True,
    ).stdout
except OSError:
    sortie = ""
etats = {}
for i, caractere in enumerate(sortie):
    if caractere == "[":
        try:
            etats = {t["task_id"]: t["state"] for t in json.JSONDecoder().raw_decode(sortie[i:])[0]}
            break
        except ValueError:
            continue
print(f"exécution {etat_run} ; état des tâches :")
for tache in taches + [t for t in etats if t not in taches]:
    print(f"  {tache:<22} {etats.get(tache) or '-'}")
sys.exit(0 if etat_run == "success" else 1)
