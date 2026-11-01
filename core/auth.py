"""Connexion des utilisateurs.

- Si .streamlit/secrets.toml contient une section [auth] : connexion Auth0
  via st.login() (e-mail + Google, configurés dans Auth0).
- Sinon : « mode démo local » (simple e-mail, sans mot de passe) pour tester
  sur votre ordinateur. NE PAS utiliser ce mode en ligne.
"""
import streamlit as st

from . import db


def auth_configuree() -> bool:
    try:
        return "auth" in st.secrets
    except Exception:  # pas de fichier secrets.toml
        return False


def utilisateur_courant() -> dict | None:
    """Renvoie {"id", "email", "nom"} si connecté, sinon None."""
    if auth_configuree():
        if not st.user.is_logged_in:
            return None
        email, nom = st.user.get("email"), st.user.get("name")
    else:
        email = st.session_state.get("email_demo")
        nom = email
        if not email:
            return None
    return {"id": db.utilisateur(email, nom), "email": email, "nom": nom or email}


def deconnexion() -> None:
    if auth_configuree():
        st.logout()
    else:
        st.session_state.pop("email_demo", None)
        st.rerun()
