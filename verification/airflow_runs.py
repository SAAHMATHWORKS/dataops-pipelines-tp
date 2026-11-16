"""Petit utilitaire de la vérification : lit la sortie JSON d'une commande airflow (sur
l'entrée standard, éventuellement mêlée de messages) et affiche ce qu'on demande.

  ... list-runs ... -o json | python3 verification/airflow_runs.py etat <run_id>
  ... states-for-dag-run ... -o json | python3 verification/airflow_runs.py tache <task_id>
  ... -o json | python3 verification/airflow_runs.py resume      (une ligne par élément)
"""
import json
import sys

texte = sys.stdin.read()
donnees = []
decodeur = json.JSONDecoder()
for i, caractere in enumerate(texte):
    if caractere in "[{":
        try:
            objet, _ = decodeur.raw_decode(texte[i:])
        except ValueError:
            continue
        if isinstance(objet, list) and (not objet or isinstance(objet[0], dict)):
            donnees = objet
            break
        if isinstance(objet, dict):
            donnees = [objet]
            break

commande = sys.argv[1]
if commande == "etat":
    print(next((r.get("state") for r in donnees if r.get("run_id") == sys.argv[2]), "absent"))
elif commande == "tache":
    print(next((r.get("state") for r in donnees if r.get("task_id") == sys.argv[2]), "absent"))
elif commande == "resume":
    for element in donnees:
        print(" | ".join(f"{cle}={valeur}" for cle, valeur in element.items()))
