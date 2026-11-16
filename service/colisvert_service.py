"""Le service de prédiction de ColisVert : plusieurs modèles derrière un seul point d'accès.

Ce fichier est un modèle MLflow « défini par le code » (models from code) : MLflow enregistre
le fichier lui-même, pas un objet Python sérialisé. Les modèles qu'il combine sont des
« artefacts » du modèle, résolus à l'enregistrement (par exemple models:/colisvert-empreinte@leger)
et copiés avec lui.

Chaque requête reçoit des colis (id_colis + les 8 variables) et, en option, trois paramètres :
- modele  : le modèle qui répond (par défaut "champion") ;
- ombre   : si vrai, les autres modèles prédisent aussi, et leurs réponses vont au journal,
            jamais au client (déploiement en ombre) ;
- message : si vrai, un rédacteur prépare le texte du SMS pour les colis à risque.
"""

from __future__ import annotations

import json
from pathlib import Path

import mlflow
import pandas as pd
from mlflow.models import set_model
from mlflow.pyfunc import PythonModel

VARIABLES = ["entrepot", "client", "creneau", "meteo", "jour_semaine", "distance_km", "poids_kg", "delai_promis_h"]
PARAMETRES = {"modele": "champion", "ombre": True, "message": False}


class RedacteurGabarit:
    """Rédige le SMS d'un colis à risque à partir d'un gabarit.

    Même contrat qu'un rédacteur à base de LLM (jour 5) : un colis et sa probabilité en entrée,
    un texte en sortie. On peut donc remplacer l'un par l'autre sans toucher au service.
    """

    @mlflow.trace(span_type="TOOL")
    def rediger(self, colis: dict, probabilite: float) -> str:
        return (f"ColisVert : votre colis {colis['id_colis']} risque d'arriver en retard. "
                f"Nous suivons sa livraison depuis {colis['entrepot']} et vous tenons informé.")


class ServiceColisVert(PythonModel):
    def load_context(self, context):
        # Chaque artefact est un modèle MLflow (un dossier) : on le charge une fois, au démarrage.
        self.modeles = {nom: mlflow.sklearn.load_model(chemin) for nom, chemin in context.artifacts.items()}
        self.seuil = float(context.model_config["seuil"])
        self.journal = Path(context.model_config["journal"])
        self.redacteur = RedacteurGabarit()

    def predict(self, context, model_input: pd.DataFrame, params: dict | None = None) -> pd.DataFrame:
        params = {**PARAMETRES, **(params or {})}
        nom = params["modele"]
        if nom not in self.modeles:
            raise ValueError(f"modèle inconnu : {nom!r} ; modèles servis : {sorted(self.modeles)}")
        X = model_input[VARIABLES]
        proba = self.modeles[nom].predict_proba(X)[:, 1]
        sortie = pd.DataFrame({
            "id_colis": model_input["id_colis"].to_numpy(),
            "modele": nom,
            "probabilite": proba.round(3),
            "retard": (proba >= self.seuil).astype(int),
        })
        if params["ombre"]:
            self.journaliser_ombre(model_input["id_colis"], nom, proba, X)
        if params["message"]:
            sortie["message"] = [self.redacteur.rediger(colis, p) if p >= self.seuil else ""
                                 for colis, p in zip(model_input.to_dict("records"), proba)]
        else:
            sortie["message"] = ""
        return sortie

    def journaliser_ombre(self, identifiants, nom, proba, X):
        """Les autres modèles prédisent aussi ; leurs réponses vont au journal, pas au client."""
        self.journal.parent.mkdir(parents=True, exist_ok=True)
        with self.journal.open("a", encoding="utf-8") as fichier:
            for autre in sorted(set(self.modeles) - {nom}):
                ombre = self.modeles[autre].predict_proba(X)[:, 1]
                for ident, p_servi, p_ombre in zip(identifiants, proba, ombre):
                    fichier.write(json.dumps({"id_colis": ident, "servi": nom, "p_servi": round(float(p_servi), 3),
                                              "ombre": autre, "p_ombre": round(float(p_ombre), 3)}) + "\n")


set_model(ServiceColisVert())
