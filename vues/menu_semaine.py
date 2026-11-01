import os
import random

import streamlit as st

from core import calculs, contexte as cx, db, donnees, fiche, ia, menu, regles, style

u = cx.utilisateur()
prefs = cx.preferences()
catalogue = donnees.catalogue()
prix_chaines = donnees.prix()["chaines"]
recettes = cx.recettes()
semaine, plats = cx.menu_courant()
nb = prefs["nb_personnes"]

style.entete("Menu de la semaine", f"Semaine du {semaine} · {nb} personne{'s' if nb > 1 else ''}")
cx.bandeau_prix_fictifs()


def generer():
    nouveaux, msgs = menu.generer(recettes, prefs, catalogue, prix_chaines, graine=random.randrange(10**9))
    cx.sauver_menu(db.debut_semaine(), nouveaux)
    st.session_state["messages_menu"] = msgs


def modifier(action: str, i: int):
    if action == "retirer":
        plats[i] = menu.nouveau_plat(None)
    elif action == "cuisine":
        plats[i]["cuisine"] = not plats[i]["cuisine"]
    cx.sauver_menu(semaine, plats)


def cout_txt(recette) -> str:
    c = menu.cout_plat(recette, catalogue, prix_chaines, nb)
    return "?" if c is None else cx.shekels(c)


FILTRES = {"moins_cher": "💰 Moins cher d'abord", "rapide": "⏱ 20 min max", "vege": "🌱 Végé"}


@st.dialog("Choisir un plat", width="medium")
def choisir_plat(i: int):
    st.caption(f"Pour {menu.JOURS[i].lower()} · seulement les plats compatibles avec votre profil")
    recherche = st.text_input("Rechercher", placeholder="ex. pâtes, poulet, lentilles…",
                              label_visibility="collapsed", icon=":material/search:")
    filtres = st.pills("Filtres", list(FILTRES), selection_mode="multi", format_func=FILTRES.get,
                       default=["moins_cher"], label_visibility="collapsed")
    deja = {p["recette_id"] for p in plats}
    liste = [recettes[r] for r in menu.candidats(recettes, prefs, catalogue) if r not in deja]
    if recherche:
        mot = recherche.lower()
        liste = [r for r in liste if mot in r["nom"].lower()
                 or any(mot in catalogue[x["id"]]["nom_fr"].lower() for x in r["ingredients"])]
    if "rapide" in filtres:
        liste = [r for r in liste if r.get("minutes") and r["minutes"] <= 20]
    if "vege" in filtres:
        liste = [r for r in liste if regles.proprietes(r, catalogue)["vegetarien"]]
    if "moins_cher" in filtres:
        liste.sort(key=lambda r: menu.cout_plat(r, catalogue, prix_chaines, nb) or 0)
    else:
        liste.sort(key=lambda r: r["nom"])

    if not liste:
        st.info("Aucun plat ne correspond. Essayez moins de filtres, ou créez des recettes avec l'IA (bas de page).")
    for r in liste:
        with st.container(border=True):
            st.markdown(style.carte_plat("", r, regles.proprietes(r, catalogue), catalogue,
                                         prix=cout_txt(r), sous_prix="estimé"), unsafe_allow_html=True)
            if st.button("Choisir ce plat", key=f"choix_{r['id']}", icon=":material/check:", width="stretch"):
                plats[i] = menu.nouveau_plat(r["id"])
                cx.sauver_menu(semaine, plats)
                st.rerun()


if plats is None:
    style.carte('<div class="plat-nom">Pas encore de menu</div>'
                '<div class="carte-sous">On choisit 7 dîners selon votre profil et votre budget. '
                "Vous pourrez ensuite changer chaque plat.</div>")
    st.button("Proposer mon menu", type="primary", on_click=generer, icon=":material/auto_awesome:",
              width="stretch")
    st.stop()

for m in st.session_state.pop("messages_menu", []):
    st.info(m)

# --- Budget (calculé par le code) ---
besoins = calculs.besoins_semaine(plats, recettes, nb)
comp = calculs.comparer_chaines(besoins, catalogue, prix_chaines)
if comp["moins_chere"]:
    total = comp["paniers"][comp["moins_chere"]]["total"]
    style.jauge_budget(total, prefs["budget"], cx.shekels(total), cx.shekels(abs(prefs["budget"] - total)))
    if total > prefs["budget"]:
        st.error("Le menu dépasse votre budget : remplacez un plat cher (triez par « moins cher d'abord »).")

# --- Les 7 jours ---
for i, plat in enumerate(plats):
    recette = recettes.get(plat["recette_id"])
    with st.container(border=True):
        if recette is None:
            st.markdown(style.carte_plat(menu.JOURS[i], None, None, catalogue), unsafe_allow_html=True)
            if st.button("Ajouter un plat", key=f"aj{i}", icon=":material/add:", width="stretch"):
                choisir_plat(i)
            continue
        props = regles.proprietes(recette, catalogue)
        st.markdown(style.carte_plat(menu.JOURS[i], recette, props, catalogue, prix=cout_txt(recette),
                                     cuisine=plat["cuisine"], sous_prix="estimé"), unsafe_allow_html=True)
        if not regles.compatible(recette, prefs, catalogue):
            st.warning("Ce plat ne correspond plus à votre profil : changez-le.")
        with st.container(horizontal=True, gap="small"):
            if st.button("Recette", key=f"vr{i}", icon=":material/menu_book:", type="primary"):
                fiche.ouvrir(recette, nb, catalogue, cout_txt(recette))
            if st.button("Changer", key=f"re{i}", icon=":material/swap_horiz:"):
                choisir_plat(i)
            st.button("Cuisiné" if not plat["cuisine"] else "Annuler", key=f"cu{i}",
                      icon=":material/check_circle:" if not plat["cuisine"] else ":material/undo:",
                      on_click=modifier, args=("cuisine", i))
            st.button("", key=f"rt{i}", icon=":material/delete:", help="Retirer ce plat",
                      on_click=modifier, args=("retirer", i))

st.caption("Le coût du menu compte les paquets entiers à acheter ; le prix « estimé » d'un plat ne compte "
           "que la part utilisée (les restes servent pour d'autres repas).")

with st.popover("Refaire tout le menu", icon=":material/casino:", width="stretch"):
    st.write("Remplacer les 7 dîners par une nouvelle proposition ?")
    st.button("Oui, nouveau menu", on_click=generer, type="primary")

# --- Recettes créées par l'IA ---
with st.expander("🤖 Inventer de nouvelles recettes avec l'IA"):
    st.write("L'IA invente des recettes **uniquement** avec les ingrédients du catalogue. "
             "Chaque recette est vérifiée par le code avant d'être acceptée ; les prix sont calculés par le code.")
    try:
        cle = st.secrets.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
    except Exception:
        cle = os.environ.get("ANTHROPIC_API_KEY")
    if not cle:
        st.info("Ajoutez `ANTHROPIC_API_KEY` dans `.streamlit/secrets.toml` pour activer cette fonction.")
    else:
        combien = st.slider("Nombre de recettes", 1, 5, 3)
        if st.button("Inventer", type="primary", icon=":material/auto_awesome:"):
            import anthropic
            nouvelles, journal = [], []
            with st.spinner("L'IA cuisine…"):
                try:
                    nouvelles, journal = ia.creer_recettes(anthropic.Anthropic(api_key=cle), combien, prefs, catalogue)
                except ia.ErreurIA as e:
                    st.error(str(e))
                except anthropic.APIStatusError as e:
                    st.error(f"Erreur de l'API Claude ({e.status_code}).")
                except anthropic.APIConnectionError:
                    st.error("Impossible de joindre l'API Claude (connexion).")
            for r in nouvelles:
                db.ajouter_recette_ia(u["id"], r)
            if nouvelles:
                st.success("Recettes ajoutées : " + ", ".join(r["nom"] for r in nouvelles)
                           + ". Retrouvez-les avec le bouton « Changer » d'un plat.")
            if journal:
                st.code("\n".join(journal), language=None)
