import streamlit as st

from core import calculs, contexte as cx, donnees, magasins, style

prefs = cx.preferences()
semaine, plats = cx.menu_courant()
style.entete("Où faire mes courses ?", "Le même panier, dans les 3 chaînes.")
cx.bandeau_prix_fictifs()

if not plats:
    st.info("Créez d'abord votre menu.")
    st.page_link("vues/menu_semaine.py", label="Créer mon menu", icon=":material/arrow_forward:")
    st.stop()

catalogue = donnees.catalogue()
besoins = calculs.besoins_semaine(plats, cx.recettes(), prefs["nb_personnes"])
comp = calculs.comparer_chaines(besoins, catalogue, donnees.prix()["chaines"])
if not comp["moins_chere"]:
    st.warning("Impossible de comparer : il manque des prix ou le menu est vide.")
    st.stop()

meilleur = comp["paniers"][comp["moins_chere"]]["total"]
style.carte(f'<div class="carte-titre">Votre économie cette semaine</div>'
            f'<div class="carte-valeur vert">{cx.shekels(comp["economie"])}</div>'
            f'<div class="carte-sous">en allant chez {donnees.CHAINES[comp["moins_chere"]]} plutôt que chez '
            f'{donnees.CHAINES[comp["plus_chere"]]}</div>')

medailles = ["🥇", "🥈", "🥉"]
classement = sorted(donnees.CHAINES, key=lambda ch: (bool(comp["paniers"][ch]["manquants"]),
                                                     comp["paniers"][ch]["total"]))
for n, ch in enumerate(classement):
    pa = comp["paniers"][ch]
    if pa["manquants"]:
        ecart = f"{len(pa['manquants'])} produit(s) sans prix : non classé"
    elif n == 0:
        ecart = "le moins cher"
    else:
        ecart = f"+{cx.shekels(pa['total'] - meilleur)}"
    style.carte(f'<div class="rang"><span class="medaille">{medailles[n] if not pa["manquants"] else "⚠️"}</span>'
                f'<span class="nom">{donnees.CHAINES[ch]}</span>'
                f'<span class="prix">{cx.shekels(pa["total"])}<span class="ecart">{ecart}</span></span></div>'
                + style.bloc_magasin(m := magasins.trouver(ch, prefs["magasins"].get(ch)),
                                     magasins.lien_itineraire(m) if m else ""),
                "gagnant" if n == 0 else "")

reste = prefs["budget"] - meilleur
st.caption(f"Budget : {cx.shekels(prefs['budget'])} · "
           + (f"il reste {cx.shekels(reste)}" if reste >= 0 else f"dépassé de {cx.shekels(-reste)}")
           + " · Promotions « membres du club » non prises en compte. "
           "Changez de magasin dans votre Profil.")

with st.expander("Détail produit par produit"):
    lignes = []
    for i, ligne in enumerate(comp["paniers"][classement[0]]["lignes"]):
        rangee = {"Produit": f'{catalogue[ligne["id"]]["emoji"]} {ligne["nom"]}', "Quantité": ligne["a_acheter"]}
        for ch, nom in donnees.CHAINES.items():
            rangee[nom] = comp["paniers"][ch]["lignes"][i]["cout"]
        lignes.append(rangee)
    st.dataframe(lignes, hide_index=True, width="stretch",
                 column_config={n: st.column_config.NumberColumn(n, format="%.2f ₪") for n in donnees.CHAINES.values()})
