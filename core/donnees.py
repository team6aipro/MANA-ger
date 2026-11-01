"""Chargement des données : catalogue d'ingrédients, recettes de base, prix.

Les prix actuels sont FICTIFS (voir data/prix_fictifs.json).
"""
import json
from functools import lru_cache
from pathlib import Path

DOSSIER_DATA = Path(__file__).resolve().parent.parent / "data"

# Les 3 chaînes comparées. Clé interne -> nom affiché.
CHAINES = {
    "shufersal": "Shufersal",
    "rami_levy": "Rami Levy",
    "osher_ad": "Osher Ad",
}


def _lire_json(nom: str) -> dict:
    with open(DOSSIER_DATA / nom, encoding="utf-8") as f:
        return json.load(f)


@lru_cache
def catalogue() -> dict[str, dict]:
    """Renvoie {id_ingredient: fiche_ingredient}."""
    return {ing["id"]: ing for ing in _lire_json("catalogue.json")["ingredients"]}


@lru_cache
def recettes_base() -> list[dict]:
    return _lire_json("recettes_base.json")["recettes"]


@lru_cache
def prix() -> dict:
    """Renvoie {"fictif": bool, "date": str, "chaines": {chaine: {id_ingredient: prix}}}.

    Pour un produit vendu au poids : prix au kg. Sinon : prix d'un paquet.
    Plus tard, cette fonction lira le cache des vrais prix (voir scripts/).
    """
    donnees = _lire_json("prix_fictifs.json")
    return {"fictif": donnees.get("fictif", True), "date": donnees.get("date", "?"),
            "chaines": donnees["chaines"]}
