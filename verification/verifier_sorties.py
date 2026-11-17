"""Exécute les blocs Python d'un support Markdown, dans l'ordre, comme un notebook,
et compare chaque sortie au bloc « Sortie attendue » qui le suit.

Usage : python3 verifier_sorties.py <dépôt des TP> fichier1.md [fichier2.md ...]

Variables d'environnement facultatives :
- SAUTER : expression régulière ; les blocs dont le code y correspond ne sont pas exécutés ;
- AVANT_BLOC : "motif du titre::commande" (plusieurs règles séparées par ;;) ;
- GARDER_DATA : ne pas effacer le dossier data/ à la fin.
Les identifiants de runs MLflow (32 caractères hexadécimaux) et les durées (« 0.13 s », « 7.30 ms ») sont neutralisés avant comparaison.
Les blocs dont le titre contient « ne pas exécuter » ou « (extrait » ne sont pas exécutés.
Les blocs « Sortie avec le LLM simulé » sont comparés comme les « Sortie attendue » : la vérification
fait tourner le LLM simulé (colisvert/llm_simule.py) à la place du vrai LLM.
"""
import contextlib
import io
import os
import re
import shutil
import subprocess
import sys
import traceback
from pathlib import Path

depot = Path(sys.argv[1]).resolve()
fichiers = [Path(f).resolve() for f in sys.argv[2:]]
sys.path.insert(0, str(depot))
os.chdir(depot)

BLOC = re.compile(r"^[ \t]*```(\w+)([^\n]*)\n(.*?)^[ \t]*```[ \t]*$", re.S | re.M)
espace = {"__name__": "__main__"}
erreurs = 0
blocs_python = 0

for fichier in fichiers:
    texte = fichier.read_text(encoding="utf-8")
    blocs = [(m.group(1), m.group(2), m.group(3)) for m in BLOC.finditer(texte)]
    attente = None
    for langue, info, code in blocs:
        if langue == "python":
            if attente and attente[2].strip():
                print(f"[sans sortie attendue] {attente[0]} · {attente[1]}\n{attente[2]}")
            sauter = os.environ.get("SAUTER")
            if "ne pas exécuter" in info or "(extrait" in info or (sauter and re.search(sauter, code)):
                if sauter and re.search(sauter, code):
                    print("[sauté]", info.strip())
                attente = None
                continue
            blocs_python += 1
            titre = re.search(r'title="([^"]*)"', info)
            titre = titre.group(1) if titre else "(sans titre)"
            # Crochet : AVANT_BLOC="Cellule 12::bash script.sh" lance une commande avant ce bloc.
            for regle in filter(None, os.environ.get("AVANT_BLOC", "").split(";;")):
                motif, commande = regle.split("::", 1)
                if motif in titre:
                    subprocess.run(commande, shell=True, check=True)
            sortie = io.StringIO()
            with contextlib.redirect_stdout(sortie):
                try:
                    exec(compile(code, f"{fichier.name}:{titre}", "exec"), espace)
                except Exception:
                    traceback.print_exc(file=sys.stdout)
            attente = (fichier.name, titre, sortie.getvalue())
        elif langue == "plaintext" and ("Sortie attendue" in info or "LLM simulé" in info) and attente:
            nom, titre, obtenu = attente
            # Les identifiants de runs MLflow et les durées (« 0.13 s », « 7.30 ms ») varient d'une exécution à l'autre.
            norm = lambda t: "\n".join(re.sub(r"\b\d+\.\d+ (m?s)\b", r"<durée> \1", re.sub(r"\b[0-9a-f]{32}\b", "<id>", l)).rstrip() for l in t.strip("\n").splitlines())
            if norm(obtenu) != norm(code):
                erreurs += 1
                print(f"\n=== DIFFÉRENCE · {nom} · {titre}\n--- attendu\n{code}--- obtenu\n{obtenu}")
            attente = None
        elif langue == "python" or (langue == "plaintext" and attente is None):
            pass
    if attente and attente[2].strip():
        print(f"[sans sortie attendue] {attente[0]} · {attente[1]}\n{attente[2]}")
if not os.environ.get("GARDER_DATA"):
    shutil.rmtree(depot / "data", ignore_errors=True)
print(f"\n{blocs_python} blocs Python exécutés, {erreurs} différence(s).")
sys.exit(1 if erreurs else 0)
