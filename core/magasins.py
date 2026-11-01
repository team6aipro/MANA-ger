"""Magasins de Jérusalem (adresses publiées par les chaînes) et liens Google Maps."""
import json
from functools import lru_cache
from urllib.parse import quote

from .donnees import CHAINES, DOSSIER_DATA


@lru_cache
def tous() -> list[dict]:
    with open(DOSSIER_DATA / "magasins.json", encoding="utf-8") as f:
        return json.load(f)["magasins"]


def de_la_chaine(chaine: str) -> list[dict]:
    return [m for m in tous() if m["chaine"] == chaine]


def trouver(chaine: str, id_magasin: str | None) -> dict | None:
    """Le magasin choisi par l'utilisateur, sinon le premier de la chaîne."""
    liste = de_la_chaine(chaine)
    return next((m for m in liste if m["id"] == id_magasin), liste[0] if liste else None)


def _requete(m: dict) -> str:
    return f'{CHAINES[m["chaine"]]} {m["adresse"]}, ירושלים'


def lien_carte(m: dict) -> str:
    """Lien « Maps URLs » officiel de Google : ouvre la carte (appli ou site)."""
    return "https://www.google.com/maps/search/?api=1&query=" + quote(_requete(m))


def lien_itineraire(m: dict) -> str:
    return "https://www.google.com/maps/dir/?api=1&destination=" + quote(_requete(m))


def libelle(m: dict) -> str:
    return f'{m["nom"]} — {m["adresse"]}'
