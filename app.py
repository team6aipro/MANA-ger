"""Point d'entrée de l'application. Lancer avec :  streamlit run app.py"""
import streamlit as st

from core import auth, style

VERSION = "4"

st.set_page_config(page_title="Panier de la semaine", page_icon="🥙", layout="centered")
style.appliquer()

MOSAIQUE = [("🍳", "t-parve"), ("🥗", "t-halavi"), ("🍗", "t-bassari"), ("🧆", "t-parve"),
            ("🍝", "t-halavi"), ("🍲", "t-parve"), ("🥙", "t-bassari"), ("🍆", "t-halavi")]


def page_connexion():
    st.markdown('<div class="entete"><h1 class="marque">Panier <b>de la semaine</b></h1>'
                "<p>7 dîners pour votre budget d'étudiant, et le supermarché le moins cher de Jérusalem.</p></div>",
                unsafe_allow_html=True)
    st.markdown('<div class="mosaique">' + "".join(f'<div class="{c}">{e}</div>' for e, c in MOSAIQUE)
                + "</div>", unsafe_allow_html=True)
    st.markdown("""
<div class="etapes">
  <div class="etape"><b>1</b><span>Indiquez votre budget, votre colocation et vos préférences (cacherout, végé…)</span></div>
  <div class="etape"><b>2</b><span>Recevez 7 dîners simples, modifiables en un clic</span></div>
  <div class="etape"><b>3</b><span>Comparez Shufersal, Rami Levy et Osher Ad, puis partez avec votre liste</span></div>
</div>""", unsafe_allow_html=True)

    if auth.auth_configuree():
        st.button("Continuer avec Google ou e-mail", type="primary", icon=":material/login:",
                  on_click=st.login, width="stretch")
        st.caption("Pas encore de compte ? Le même bouton permet d'en créer un. "
                   "Connexion sécurisée par Auth0 : l'application ne voit jamais votre mot de passe.")
    else:
        with st.container(border=True):
            st.markdown("**Mode démo local** · aucune connexion Auth0 n'est configurée.")
            with st.form("demo", border=False):
                email = st.text_input("Votre e-mail", placeholder="prenom@exemple.com",
                                      label_visibility="collapsed")
                if st.form_submit_button("Entrer", type="primary", icon=":material/arrow_forward:",
                                         width="stretch"):
                    if "@" in email and "." in email.split("@")[-1]:
                        st.session_state["email_demo"] = email.strip().lower()
                        st.rerun()
                    else:
                        st.error("Cette adresse e-mail ne semble pas valide.")
            st.caption("Sans mot de passe : uniquement pour tester sur votre ordinateur, jamais en ligne.")


utilisateur = auth.utilisateur_courant()
if utilisateur is None:
    st.navigation([st.Page(page_connexion, title="Connexion", icon="🔑")], position="hidden").run()
    st.caption(f"Version {VERSION}")
    st.stop()

st.session_state["utilisateur"] = utilisateur

pages = [
    st.Page("vues/accueil.py", title="Accueil", icon=":material/home:", default=True),
    st.Page("vues/menu_semaine.py", title="Menu", icon=":material/restaurant:"),
    st.Page("vues/comparateur.py", title="Prix", icon=":material/storefront:"),
    st.Page("vues/courses.py", title="Courses", icon=":material/shopping_cart:"),
    st.Page("vues/preferences.py", title="Profil", icon=":material/tune:"),
]
page = st.navigation(pages, position="hidden")

# Barre de navigation maison : toujours visible, même sur téléphone.
with st.container(horizontal=True, key="nav", gap="small"):
    for i, p in enumerate(pages):
        actif = p.url_path == page.url_path
        with st.container(key="navactif" if actif else f"nav{i}", width="content"):
            st.page_link(p, label=p.title, icon=p.icon)
    if st.button("", icon=":material/logout:", help=f"Se déconnecter ({utilisateur['email']})",
                 type="tertiary"):
        auth.deconnexion()

page.run()
st.divider()
st.caption(f"Panier de la semaine · version {VERSION}")
