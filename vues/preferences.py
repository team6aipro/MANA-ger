import streamlit as st

from core import contexte as cx, db, donnees, magasins, style

u = cx.utilisateur()
premiere_fois = db.lire_preferences(u["id"]) is None
style.entete("Mon profil", "Ces réglages servent à choisir vos dîners et à vérifier votre budget.")
prefs = cx.preferences()
catalogue = donnees.catalogue()

TYPES = {"parve": "🥕 Parvé", "halavi": "🧀 Halavi (lait)", "bassari": "🍗 Bassari (viande)"}
REGIMES = {"vegetarien": "🌱 Végétarien", "sans_gluten": "🌾 Sans gluten"}
PERSONNES = {1: "🧍 Seul", 2: "👥 2", 3: "👥 3", 4: "👥 4"}

with st.form("prefs", border=False):
    with st.container(border=True):
        st.markdown("**💰 Budget de la semaine**")
        budget = st.slider("Budget (₪)", 50, 1000, int(prefs["budget"]), step=10, format="%d ₪",
                           label_visibility="collapsed")
        st.markdown("**🏠 Combien de personnes mangent ?**")
        nb = st.segmented_control("Personnes", list(PERSONNES), format_func=PERSONNES.get,
                                  default=prefs["nb_personnes"], label_visibility="collapsed")

    with st.container(border=True):
        st.markdown("**✡️ Cacherout : types de plats acceptés**")
        cacherout = st.pills("Cacherout", list(TYPES), selection_mode="multi", format_func=TYPES.get,
                             default=prefs["cacherout"], label_visibility="collapsed")
        st.caption("Un plat ne mélange jamais viande et lait : c'est vérifié par le code.")
        st.markdown("**🥗 Régime**")
        regimes = st.pills("Régime", list(REGIMES), selection_mode="multi", format_func=REGIMES.get,
                           default=[r for r in REGIMES if prefs[r]], label_visibility="collapsed")

    with st.container(border=True):
        st.markdown("**🚫 Ingrédients à éviter** · touchez pour exclure")
        a_eviter = []
        categories = {}
        for ing in catalogue.values():
            categories.setdefault(ing["categorie"], []).append(ing["id"])
        for cat, ids in categories.items():
            choix = st.pills(cat, ids, selection_mode="multi",
                             format_func=lambda i: f'{catalogue[i]["emoji"]} {catalogue[i]["nom_fr"]}',
                             default=[i for i in ids if i in prefs["a_eviter"]], key=f"eviter_{cat}")
            a_eviter += choix

    with st.container(border=True):
        st.markdown("**🏪 Mes magasins** · le plus proche de chez vous")
        choix_magasins = {}
        for ch, nom_ch in donnees.CHAINES.items():
            liste = magasins.de_la_chaine(ch)
            ids = [m["id"] for m in liste]
            actuel = prefs.get("magasins", {}).get(ch)
            choix_magasins[ch] = st.selectbox(
                nom_ch, ids, index=ids.index(actuel) if actuel in ids else 0,
                format_func=lambda i, l=liste: magasins.libelle(next(m for m in l if m["id"] == i)))
        st.caption("Adresses publiées par les chaînes. Liste partielle pour l'instant "
                   "(scripts/maj_magasins.py récupère la liste complète).")

    envoye = st.form_submit_button("Enregistrer mon profil", type="primary", icon=":material/check:",
                                   width="stretch")

if envoye:
    if not cacherout:
        st.error("Choisissez au moins un type de plat (parvé, halavi ou bassari).")
    else:
        db.ecrire_preferences(u["id"], {
            "budget": float(budget), "nb_personnes": nb or 1, "cacherout": cacherout,
            "vegetarien": "vegetarien" in regimes, "sans_gluten": "sans_gluten" in regimes,
            "a_eviter": a_eviter, "magasins": choix_magasins})
        st.success("Profil enregistré ✔")
        if premiere_fois:
            st.page_link("vues/menu_semaine.py", label="Créer mon menu", icon=":material/arrow_forward:")
        else:
            st.caption("Les plats du menu qui ne correspondent plus à votre profil sont signalés dans le Menu.")
