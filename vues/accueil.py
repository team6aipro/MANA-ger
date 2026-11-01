from datetime import date

import streamlit as st

from core import calculs, contexte as cx, db, donnees, fiche, magasins, menu, regles, style

u = cx.utilisateur()
prenom = u["nom"].split("@")[0].split(" ")[0].capitalize()
style.entete(f"Bonjour {prenom} 👋", "Voici votre semaine en un coup d'œil.")
cx.bandeau_prix_fictifs()

prefs = db.lire_preferences(u["id"])
if prefs is None:
    style.carte('<div class="carte-titre">Bienvenue</div>'
                '<div class="plat-nom">Commençons par votre profil</div>'
                '<div class="carte-sous">Budget, nombre de personnes et préférences : 30 secondes.</div>')
    st.page_link("vues/preferences.py", label="Créer mon profil", icon=":material/arrow_forward:")
    st.stop()

semaine, plats = cx.menu_courant()
if not plats:
    style.carte('<div class="carte-titre">Étape suivante</div>'
                '<div class="plat-nom">Votre menu de la semaine vous attend</div>'
                '<div class="carte-sous">7 dîners choisis selon votre budget et vos préférences.</div>')
    st.page_link("vues/menu_semaine.py", label="Créer mon menu", icon=":material/arrow_forward:")
    st.stop()

catalogue = donnees.catalogue()
recettes = cx.recettes()

# Le dîner de ce soir (dimanche = 0, comme en Israël)
aujourdhui = (date.today().weekday() + 1) % 7
plat = plats[aujourdhui]
recette = recettes.get(plat["recette_id"])
st.markdown('<div class="carte-titre" style="margin:.2rem 0 .4rem">Ce soir</div>', unsafe_allow_html=True)
style.carte(style.carte_plat(menu.JOURS[aujourdhui], recette,
                             regles.proprietes(recette, catalogue) if recette else None,
                             catalogue, cuisine=plat["cuisine"]))
if recette and st.button("Voir la recette de ce soir", icon=":material/menu_book:", type="primary",
                         width="stretch"):
    c = menu.cout_plat(recette, catalogue, donnees.prix()["chaines"], prefs["nb_personnes"])
    fiche.ouvrir(recette, prefs["nb_personnes"], catalogue, "?" if c is None else cx.shekels(c))

besoins = calculs.besoins_semaine(plats, recettes, prefs["nb_personnes"])
comp = calculs.comparer_chaines(besoins, catalogue, donnees.prix()["chaines"])
if comp["moins_chere"]:
    total = comp["paniers"][comp["moins_chere"]]["total"]
    style.jauge_budget(total, prefs["budget"], cx.shekels(total), cx.shekels(abs(prefs["budget"] - total)))
    style.carte(f'<div class="carte-titre">Magasin conseillé</div>'
                f'<div class="carte-valeur">🏆 {donnees.CHAINES[comp["moins_chere"]]}</div>'
                f'<div class="carte-sous">{cx.shekels(comp["economie"])} économisés par rapport à '
                f'{donnees.CHAINES[comp["plus_chere"]]}</div>'
                + style.bloc_magasin(m := magasins.trouver(comp["moins_chere"], prefs["magasins"].get(comp["moins_chere"])),
                                     magasins.lien_itineraire(m) if m else ""), "gagnant")

nb_plats = sum(p["recette_id"] is not None for p in plats)
nb_cuisines = sum(p["recette_id"] is not None and p["cuisine"] for p in plats)
st.progress(nb_cuisines / nb_plats if nb_plats else 0.0, text=f"{nb_cuisines} / {nb_plats} dîners cuisinés")

with st.container(horizontal=True):
    st.page_link("vues/menu_semaine.py", label="Voir le menu", icon=":material/restaurant:")
    st.page_link("vues/courses.py", label="Liste de courses", icon=":material/shopping_cart:")
