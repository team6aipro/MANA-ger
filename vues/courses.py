import streamlit as st

from core import calculs, contexte as cx, donnees, magasins, style

prefs = cx.preferences()
semaine, plats = cx.menu_courant()
style.entete("Liste de courses", "Quantités additionnées sur toute la semaine, rangées par rayon.")
cx.bandeau_prix_fictifs()

if not plats:
    st.info("Créez d'abord votre menu.")
    st.stop()

catalogue = donnees.catalogue()
recettes = cx.recettes()

sans_cuisines = st.toggle("Ne pas compter les plats déjà cuisinés", value=True)
a_acheter = [p for p in plats if not (sans_cuisines and p["cuisine"])]
besoins = calculs.besoins_semaine(a_acheter, recettes, prefs["nb_personnes"])
if not besoins:
    st.success("Rien à acheter 🎉")
    st.stop()

comp = calculs.comparer_chaines(besoins, catalogue, donnees.prix()["chaines"])
noms = list(donnees.CHAINES)
chaine = st.segmented_control(
    "Magasin", noms, default=comp["moins_chere"] or noms[0], width="stretch",
    format_func=lambda c: ("🏆 " if c == comp["moins_chere"] else "") + donnees.CHAINES[c]) or noms[0]
pa = comp["paniers"][chaine]

coches = sum(st.session_state.get(f"achat_{semaine}_{l['id']}", False) for l in pa["lignes"])
style.carte(f'<div class="carte-titre">Total chez {donnees.CHAINES[chaine]}</div>'
            f'<div class="carte-valeur">{cx.shekels(pa["total"])}</div>'
            f'<div class="carte-sous">{coches} / {len(pa["lignes"])} produits dans le panier</div>'
            + style.bloc_magasin(mag := magasins.trouver(chaine, prefs["magasins"].get(chaine))))
if mag:
    with st.container(horizontal=True, gap="small"):
        st.link_button("Itinéraire", magasins.lien_itineraire(mag), icon=":material/directions:", type="primary")
        st.link_button("Voir sur la carte", magasins.lien_carte(mag), icon=":material/map:")

rayons = {}
for ligne in pa["lignes"]:
    rayons.setdefault(catalogue[ligne["id"]]["categorie"], []).append(ligne)
for rayon in sorted(rayons):
    with st.container(border=True):
        st.markdown(f"**{rayon}**")
        for l in rayons[rayon]:
            prix = "prix inconnu" if l["cout"] is None else cx.shekels(l["cout"])
            st.checkbox(f"{catalogue[l['id']]['emoji']} **{l['nom']}** · {l['a_acheter']} · {prix}  \n"
                        f":gray[{l['nom_he']}]", key=f"achat_{semaine}_{l['id']}")

texte = f"Courses — {donnees.CHAINES[chaine]}\n" + "\n".join(
    f"[ ] {l['nom']} / {l['nom_he']} : {l['a_acheter']}" for l in pa["lignes"])
st.download_button("Télécharger la liste", texte, file_name=f"courses_{semaine}.txt",
                   icon=":material/download:", width="stretch")
