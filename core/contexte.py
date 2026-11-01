"""Fonctions partagées par toutes les pages Streamlit."""
import streamlit as st

from . import db, donnees, menu


def utilisateur() -> dict:
    return st.session_state["utilisateur"]


def preferences() -> dict:
    return db.lire_preferences(utilisateur()["id"]) or dict(db.PREFS_DEFAUT)


def recettes() -> dict:
    """Recettes de base + recettes IA de l'utilisateur, par id."""
    tout = {r["id"]: r for r in donnees.recettes_base()}
    tout.update({r["id"]: r for r in db.recettes_ia(utilisateur()["id"])})
    return tout


def menu_courant() -> tuple[str, list[dict] | None]:
    """(semaine, plats) : le menu le plus récent de l'utilisateur."""
    dernier = db.dernier_menu(utilisateur()["id"])
    return dernier if dernier else (db.debut_semaine(), None)


def sauver_menu(semaine: str, plats: list[dict]) -> None:
    db.ecrire_menu(utilisateur()["id"], semaine, plats)


def bandeau_prix_fictifs() -> None:
    p = donnees.prix()
    if p["fictif"]:
        st.warning("⚠️ **PRIX FICTIFS** — données d'essai inventées pour tester l'application. "
                   "Ce ne sont pas les vrais prix des magasins.", icon=None)
    else:
        st.caption(f"Prix publiés par les chaînes, mis à jour le {p['date']}. "
                   "Promotions réservées aux membres de club non appliquées.")


def shekels(x: float) -> str:
    return f"{x:,.2f} ₪".replace(",", " ").replace(".", ",")


def lien_jour(i: int) -> str:
    return menu.JOURS[i]
