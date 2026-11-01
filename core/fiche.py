"""Fiche recette détaillée (affichée dans une fenêtre)."""
import html

import streamlit as st

from . import regles, style


def quantite_lisible(q: float, unite: str) -> str:
    """240 -> « 240 g », 1500 -> « 1,5 kg », 0.5 pièce -> « ½ »."""
    if unite == "piece":
        entier, reste = int(q), q - int(q)
        frac = {0.25: "¼", 0.5: "½", 0.75: "¾"}.get(round(reste, 2), "")
        if not frac and reste:
            return f"{q:.1f}".replace(".", ",")
        return (f"{entier} " if entier else "") + frac if frac else str(entier)
    if q >= 1000:
        return f"{q / 1000:.2f}".rstrip("0").rstrip(".").replace(".", ",") + (" kg" if unite == "g" else " L")
    return f"{q:g} {unite}"


def afficher(recette: dict, nb: int, catalogue: dict, prix_txt: str) -> None:
    props = regles.proprietes(recette, catalogue)
    st.markdown(f'<div class="hero t-{props["cacherout"]}">{style.visuel_grand(recette, catalogue)}</div>',
                unsafe_allow_html=True)
    credit = style.credit_photo(recette["id"])
    if credit:
        st.markdown(credit, unsafe_allow_html=True)
    st.markdown(f'<h2 class="fiche-titre">{html.escape(recette["nom"])}</h2>'
                f'<p class="carte-sous">{html.escape(recette.get("description", ""))}</p>'
                + style.chips(props, ia=recette.get("source") == "ia"), unsafe_allow_html=True)

    prep, cuis = recette.get("preparation"), recette.get("cuisson")
    tuiles = []
    if prep is not None:
        tuiles.append(("🔪", "Préparation", f"{prep} min"))
    if cuis is not None:
        tuiles.append(("🔥", "Cuisson", "aucune" if cuis == 0 else f"{cuis} min"))
    if recette.get("minutes"):
        tuiles.append(("⏱", "Total", f"{recette['minutes']} min"))
    tuiles.append(("👥", "Pour", f"{nb} pers."))
    tuiles.append(("💰", "Coût estimé", prix_txt))
    st.markdown('<div class="tuiles">' + "".join(
        f'<div><span>{e}</span><small>{t}</small><b>{v}</b></div>' for e, t, v in tuiles) + "</div>",
        unsafe_allow_html=True)

    st.markdown(f"#### Ingrédients · {nb} personne{'s' if nb > 1 else ''}")
    lignes = []
    for ing in recette["ingredients"]:
        f = catalogue[ing["id"]]
        q = quantite_lisible(ing["quantite"] * nb, f["unite"])
        lignes.append(f'<li><span>{f["emoji"]} {html.escape(f["nom_fr"])}</span><b>{q}</b></li>')
    st.markdown(f'<ul class="ingredients">{"".join(lignes)}</ul>', unsafe_allow_html=True)
    st.caption("Sel, poivre et eau : supposés déjà à la maison.")

    st.markdown("#### Préparation")
    st.caption("Cochez les étapes au fur et à mesure.")
    for n, etape in enumerate(recette["etapes"], 1):
        st.checkbox(f"**{n}.** {etape}", key=f"etape_{recette['id']}_{n}")

    if recette.get("astuce"):
        st.markdown(f'<div class="astuce">💡 <b>Astuce</b> · {html.escape(recette["astuce"])}</div>',
                    unsafe_allow_html=True)


@st.dialog("Recette", width="large")
def ouvrir(recette: dict, nb: int, catalogue: dict, prix_txt: str) -> None:
    afficher(recette, nb, catalogue, prix_txt)
