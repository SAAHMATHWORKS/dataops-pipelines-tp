"""Un LLM simulé : un faux serveur qui parle comme la passerelle LLM de Training Lab.

Pourquoi ? Un vrai LLM répond autre chose à chaque appel, coûte de l'argent et demande un
réseau. Pour tester le code qui l'entoure (la boucle d'agent, les garde-fous, le journal), on
le remplace par une « doublure » qui répond toujours la même chose : les tests deviennent
exacts, gratuits et hors ligne. C'est ce que fait la vérification automatique du cours.

Le LLM simulé ne comprend rien. Il suit des règles fixes :
- avec un schéma JSON (text.format), il remplit les champs à partir de mots-clés ;
- avec des outils, il les appelle tous une fois, puis rédige une note à partir de leurs résultats ;
- pour un SMS de ColisVert, il remplit un gabarit ;
- sinon, il renvoie un texte fixe.

Il refuse les mêmes paramètres que la passerelle, avec les mêmes messages.

Dans un notebook :
    from colisvert.llm_simule import demarrer
    adresse = demarrer()          # http://127.0.0.1:<port>/api/llm/v1, dans un fil d'exécution

En ligne de commande (vérification du cours) :
    python -m colisvert.llm_simule --port 8090
"""

from __future__ import annotations

import argparse
import json
import math
import re
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

MODELE_PASSERELLE = "gpt-6-luna"   # ce qu'annonce la passerelle de la formation (GET /quota)
MODELE = "llm-simule"              # ce qu'annonce chaque réponse du LLM simulé

ACCEPTES = {"model", "input", "instructions", "tools", "tool_choice", "parallel_tool_calls",
            "max_output_tokens", "text", "reasoning", "include", "store", "temperature", "top_p"}
REFUSES = {
    "stream": "la passerelle ne transmet pas de réponse en flux : retirez « stream »",
    "previous_response_id": "rien n'est conservé chez OpenAI (store=false) : renvoyez tout l'historique dans « input »",
    "conversation": "rien n'est conservé chez OpenAI (store=false) : renvoyez tout l'historique dans « input »",
    "background": "les appels en arrière-plan ne sont pas disponibles sur la passerelle",
    "service_tier": "le niveau de service est fixé par la plateforme",
}

REPONSES_FIXES = {
    "carte de contrôle": (
        "Une carte de contrôle suit un indicateur du pipeline jour après jour, par exemple le taux de "
        "retard, et le compare à des limites calculées sur une période normale. Elle signale qu'un "
        "point sort des limites ou qu'une série anormale apparaît, pour qu'on cherche la cause avant "
        "que les clients ne la subissent."
    ),
}
REPONSE_PAR_DEFAUT = "Je suis le LLM simulé de la formation : je renvoie toujours ce texte quand je ne reconnais pas la demande."


# --------------------------------------------------------------------------
# Les règles du LLM simulé


def _texte_entree(entree) -> str:
    """Le dernier message de l'utilisateur, en texte."""
    if isinstance(entree, str):
        return entree
    for element in reversed(entree):
        if element.get("role") == "user":
            contenu = element.get("content")
            if isinstance(contenu, str):
                return contenu
            return " ".join(partie.get("text", "") for partie in contenu or [])
    return ""


def _remplir_schema(schema: dict, texte: str) -> dict:
    bas = texte.lower()
    resultat = {}
    for nom, propriete in schema.get("properties", {}).items():
        if nom == "id_colis":
            trouve = re.search(r"\b[A-Z]{2,3}\d{5}\b", texte)
            resultat[nom] = trouve.group(0) if trouve else None
        elif nom == "motif":
            if re.search(r"écras|abîm|abim|cass", bas):
                resultat[nom] = "colis_abime"
            elif "adresse" in bas:
                resultat[nom] = "adresse"
            elif re.search(r"retard|toujours rien|pas reçu|devait arriver", bas):
                resultat[nom] = "retard"
            else:
                resultat[nom] = "autre"
        elif nom == "urgence":
            resultat[nom] = "haute" if re.search(r"urgent|immédiatement|vite", bas) else "normale"
        elif "enum" in propriete:
            resultat[nom] = propriete["enum"][0]
        else:
            phrase = re.split(r"(?<=[.!?])\s", texte.strip())[0]
            mots = phrase.split()
            resultat[nom] = " ".join(mots[:15])
    return resultat


def _appels_outils(outils: list, texte: str) -> list:
    date = re.search(r"\d{4}-\d{2}-\d{2}", texte)
    appels = []
    for numero, outil in enumerate(outils, start=1):
        arguments = {}
        for parametre in outil.get("parameters", {}).get("required", []):
            arguments[parametre] = date.group(0) if date else ""
        appels.append({"type": "function_call", "id": f"fc_simule_{numero}", "call_id": f"appel_{numero}",
                       "name": outil["name"], "arguments": json.dumps(arguments, ensure_ascii=False),
                       "status": "completed"})
    return appels


ETIQUETTES = {"retards_par_entrepot": "par entrepôt", "retards_par_creneau": "par créneau"}


def _note(resultats: dict) -> str:
    """Une note de quelques lignes, qui ne cite que des chiffres donnés par les outils."""
    lignes = []
    carte = resultats.get("carte_controle")
    if carte and "erreur" not in carte:
        regles = carte.get("regles_en_alerte") or ["aucune"]
        lignes.append(
            f"Au {carte['jour']}, le taux de retard du jour est de {carte['taux_du_jour_pct']} % "
            f"pour une référence de {carte['taux_reference_pct']} % ; règles en alerte : {', '.join(regles)} "
            f"(première alerte de décembre : {carte['premiere_alerte']})."
        )
    derive = resultats.get("derive_variables")
    if derive and "erreur" not in derive:
        morceaux = [f"{nom} {valeurs['reference']} → {valeurs['decembre']}" for nom, valeurs in derive.items()]
        lignes.append("Ce qui a changé depuis septembre-octobre : " + ", ".join(morceaux) + ".")
    for nom in ("retards_par_entrepot", "retards_par_creneau"):
        groupes = resultats.get(nom)
        if groupes and "erreur" not in groupes:
            pire = max(groupes, key=lambda cle: groupes[cle]["decembre_pct"] - groupes[cle]["reference_pct"])
            lignes.append(
                f"La plus forte hausse {ETIQUETTES[nom]} : {pire}, de "
                f"{groupes[pire]['reference_pct']} % à {groupes[pire]['decembre_pct']} %."
            )
    for nom, sortie in resultats.items():
        if nom not in ("carte_controle", "derive_variables", "retards_par_entrepot", "retards_par_creneau"):
            lignes.append(f"Résultat de {nom} : {json.dumps(sortie, ensure_ascii=False)}.")
    lignes.append("À vérifier par l'équipe : l'effet de la météo et du poids sur les tournées, avant toute décision sur le modèle.")
    return "\n".join(lignes)


def repondre(corps: dict) -> dict:
    """La réponse du LLM simulé à une requête déjà validée."""
    entree = corps["input"]
    texte = _texte_entree(entree)
    consignes = corps.get("instructions") or ""
    sortie = []
    format_ = (corps.get("text") or {}).get("format") or {}
    resultats = {}
    if isinstance(entree, list):
        appels = {e["call_id"]: e["name"] for e in entree if e.get("type") == "function_call"}
        for element in entree:
            if element.get("type") == "function_call_output":
                resultats[appels.get(element["call_id"], element["call_id"])] = json.loads(element["output"])

    if format_.get("type") == "json_schema":
        message = json.dumps(_remplir_schema(format_["schema"], texte), ensure_ascii=False)
    elif corps.get("tools") and not resultats:
        sortie = _appels_outils(corps["tools"], texte)
        message = None
    elif resultats:
        message = _note(resultats)
    elif "SMS" in consignes:
        donnees = json.loads(texte)
        cause = {"pluie": " à cause de la pluie"}.get(donnees.get("meteo"), "")
        message = (f"ColisVert : votre colis {donnees['id_colis']} pourrait arriver en retard{cause}. "
                   f"Nous suivons sa livraison depuis {donnees['entrepot']}.")
    else:
        message = next((reponse for cle, reponse in REPONSES_FIXES.items() if cle in texte.lower()), REPONSE_PAR_DEFAUT)

    if message is not None:
        sortie.append({"type": "message", "id": "msg_simule", "role": "assistant", "status": "completed",
                       "content": [{"type": "output_text", "text": message, "annotations": []}]})
    entree_jetons = math.ceil(len(consignes + json.dumps(entree, ensure_ascii=False)) / 4)
    sortie_jetons = math.ceil(len(json.dumps(sortie, ensure_ascii=False)) / 4)
    return {"object": "response", "model": MODELE, "status": "completed", "output": sortie,
            "usage": {"input_tokens": entree_jetons, "output_tokens": sortie_jetons,
                      "total_tokens": entree_jetons + sortie_jetons}}


def valider(corps) -> tuple[int, str, str] | None:
    """Les mêmes refus que la passerelle : (statut, code, message), ou None si la requête est acceptée."""
    if not isinstance(corps, dict):
        return 400, "parametre_invalide", "Le corps de la requête doit être un objet JSON."
    for cle, raison in REFUSES.items():
        if cle in corps:
            return 400, "parametre_refuse", f"Paramètre « {cle} » refusé : {raison}."
    inconnus = sorted(set(corps) - ACCEPTES - set(REFUSES))
    if inconnus:
        return 400, "parametre_refuse", (f"Paramètre(s) non accepté(s) par la passerelle : {', '.join(inconnus)}. "
                                         f"Paramètres acceptés : {', '.join(sorted(ACCEPTES))}.")
    if not corps.get("input") or not isinstance(corps["input"], (str, list)):
        return 400, "parametre_invalide", "« input » est obligatoire : un texte, ou une liste de messages."
    for outil in corps.get("tools") or []:
        if not isinstance(outil, dict) or outil.get("type") != "function":
            genre = outil.get("type") if isinstance(outil, dict) else type(outil).__name__
            return 400, "outil_refuse", (f"Outil « {genre} » refusé : seuls les outils de type « function » sont "
                                         "acceptés (vos propres fonctions Python, exécutées chez vous).")
    return None


# --------------------------------------------------------------------------
# Le serveur HTTP


class _Gestionnaire(BaseHTTPRequestHandler):
    def _json(self, statut: int, donnees: dict) -> None:
        corps = json.dumps(donnees, ensure_ascii=False).encode("utf-8")
        self.send_response(statut)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(corps)))
        self.end_headers()
        self.wfile.write(corps)

    def _erreur(self, statut: int, code: str, message: str) -> None:
        self._json(statut, {"error": {"message": message, "type": "invalid_request_error", "code": code, "param": None}})

    def _authentifie(self) -> bool:
        schema, _, jeton = self.headers.get("Authorization", "").partition(" ")
        if schema.lower() != "bearer" or not jeton.strip():
            self._erreur(401, "jeton_manquant", "Jeton manquant : ajoutez l'en-tête « Authorization: Bearer <votre jeton> ».")
            return False
        return True

    def do_GET(self):  # noqa: N802 (nom imposé par http.server)
        if not self.path.endswith("/quota"):
            return self._erreur(404, "introuvable", "Adresse inconnue.")
        if self._authentifie():
            self._json(200, {"modele": MODELE_PASSERELLE, "appels_aujourdhui": 0, "appels_max_par_jour": 150,
                             "jetons_aujourdhui": 0, "jetons_max_par_jour": 300000, "appels_max_par_minute": 10,
                             "jetons_sortie_max_par_appel": 4000, "effort_par_defaut": "low"})

    def do_POST(self):  # noqa: N802
        if not self.path.endswith("/responses"):
            return self._erreur(404, "introuvable", "Adresse inconnue.")
        if not self._authentifie():
            return None
        try:
            corps = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)).decode("utf-8"))
        except ValueError:
            return self._erreur(400, "json_invalide", "Le corps de la requête n'est pas du JSON valide.")
        refus = valider(corps)
        if refus:
            return self._erreur(*refus)
        return self._json(200, repondre(corps))

    def log_message(self, *args):  # pas de journal sur la sortie standard
        pass


def demarrer(port: int = 0) -> str:
    """Démarre le LLM simulé dans un fil d'exécution et renvoie son adresse (même forme que la passerelle)."""
    serveur = ThreadingHTTPServer(("127.0.0.1", port), _Gestionnaire)
    threading.Thread(target=serveur.serve_forever, daemon=True).start()
    return f"http://127.0.0.1:{serveur.server_address[1]}/api/llm/v1"


if __name__ == "__main__":
    analyse = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    analyse.add_argument("--port", type=int, default=8090)
    port = analyse.parse_args().port
    print(f"LLM simulé : http://127.0.0.1:{port}/api/llm/v1", flush=True)
    ThreadingHTTPServer(("127.0.0.1", port), _Gestionnaire).serve_forever()
