"""Identité visuelle : CSS, en-têtes, cartes de plats, étiquettes.

Les « images » des plats sont des illustrations originales (dégradé + emoji),
sauf si une vraie photo existe dans data/photos/<id_recette>.jpg|png|webp.
On n'utilise aucune image copiée d'un autre site.
"""
import base64
import html
from pathlib import Path

import streamlit as st

DOSSIER_PHOTOS = Path(__file__).resolve().parent.parent / "data" / "photos"
TYPES_PHOTOS = {".jpg": "jpeg", ".jpeg": "jpeg", ".png": "png", ".webp": "webp"}

CSS = """
<style>
:root {
  --terre: #C2562F; --terre-clair: #F6E3D8; --olive: #5E7A3A; --olive-clair: #E7EEDB;
  --ciel: #3E6E8E; --ciel-clair: #DDE9F1; --pierre: #FBF7F0; --sable: #F1E9DC;
  --encre: #2B2622; --gris: #7A7068; --ombre: 0 2px 10px rgba(60, 40, 20, .07);
}
.block-container {padding-top: 1.2rem; padding-bottom: 4rem; max-width: 760px;}
header[data-testid="stHeader"] {background: transparent;}

/* Barre de navigation (liens en « pastilles ») */
.st-key-nav {gap: .5rem !important; row-gap: .55rem !important; margin-bottom: .2rem;}
.st-key-nav [data-testid="stPageLink"] a {
  background: white; border: 1px solid #EADFD0; border-radius: 999px;
  padding: .15rem .65rem; box-shadow: var(--ombre);
}
.st-key-nav [data-testid="stPageLink"] p {font-size: .9rem;}
.st-key-nav .st-key-navactif [data-testid="stPageLink"] a {background: var(--terre); border-color: var(--terre);}
.st-key-navactif [data-testid="stPageLink"] a span, .st-key-navactif [data-testid="stPageLink"] a p {color: white !important;}

/* En-tête de page */
.entete {margin: .4rem 0 1rem;}
.entete h1 {font-size: 1.9rem; font-weight: 800; letter-spacing: -.02em; margin: 0; padding: 0; line-height: 1.15;}
.entete p {color: var(--gris); margin: .25rem 0 0;}
.marque {font-weight: 800; letter-spacing: -.02em;}
.marque b {color: var(--terre);}

/* Cartes */
.carte {background: white; border: 1px solid #EFE6DA; border-radius: 18px; padding: 1rem 1.1rem;
        box-shadow: var(--ombre); margin-bottom: .6rem;}
.carte-titre {font-size: .8rem; text-transform: uppercase; letter-spacing: .06em; color: var(--gris); font-weight: 600;}
.carte-valeur {font-size: 1.9rem; font-weight: 800; letter-spacing: -.02em; line-height: 1.2;}
.carte-sous {color: var(--gris); font-size: .9rem;}
.jauge {height: 10px; background: var(--sable); border-radius: 999px; overflow: hidden; margin: .6rem 0 .3rem;}
.jauge > div {height: 100%; border-radius: 999px;}
.vert {color: var(--olive);} .rouge {color: #B3261E;}

/* Carte d'un plat */
.plat {display: flex; gap: .9rem; align-items: center;}
.plat-visuel {flex: 0 0 76px; height: 76px; border-radius: 16px; display: flex; align-items: center;
              justify-content: center; position: relative; overflow: hidden;}
.plat-visuel .e {font-size: 2.4rem; filter: drop-shadow(0 2px 3px rgba(0,0,0,.15));}
.plat-visuel .mini {position: absolute; bottom: 3px; right: 5px; font-size: .8rem; letter-spacing: -2px;}
.plat-visuel img {width: 100%; height: 100%; object-fit: cover;}
.t-parve {background: linear-gradient(135deg, #E7EEDB, #C9DBAE);}
.t-halavi {background: linear-gradient(135deg, #DDE9F1, #B5CFE1);}
.t-bassari {background: linear-gradient(135deg, #F6E3D8, #EDB99D);}
.t-vide {background: repeating-linear-gradient(45deg, #F1E9DC, #F1E9DC 8px, #F8F2E8 8px, #F8F2E8 16px);}
.plat-info {flex: 1; min-width: 0;}
.plat-jour {font-size: .75rem; text-transform: uppercase; letter-spacing: .07em; color: var(--terre); font-weight: 700;}
.plat-nom {font-size: 1.08rem; font-weight: 700; line-height: 1.25; margin: .1rem 0 .3rem;}
.plat-nom.fait {text-decoration: line-through; color: var(--gris);}
.plat-prix {font-weight: 800; white-space: nowrap; font-size: 1rem;}
.plat-prix small {display: block; font-weight: 400; color: var(--gris); font-size: .7rem; text-align: right;}

/* Étiquettes */
.chips {display: flex; flex-wrap: wrap; gap: .3rem;}
.chip {font-size: .72rem; padding: .1rem .5rem; border-radius: 999px; background: var(--sable); color: var(--encre);}
.chip.parve {background: var(--olive-clair); color: var(--olive);}
.chip.halavi {background: var(--ciel-clair); color: var(--ciel);}
.chip.bassari {background: var(--terre-clair); color: var(--terre);}
.chip.ok {background: #DFF1E3; color: #2E6B3B;}

/* Classement des magasins */
.rang {display: flex; align-items: center; gap: .8rem;}
.rang .medaille {font-size: 1.8rem;}
.rang .nom {flex: 1; font-weight: 700; font-size: 1.05rem;}
.rang .prix {font-weight: 800; font-size: 1.15rem; text-align: right;}
.rang .ecart {display: block; font-size: .75rem; color: var(--gris); font-weight: 400;}
.carte.gagnant {border: 2px solid var(--olive); background: #FAFCF6;}

/* Écran de connexion */
.mosaique {display: grid; grid-template-columns: repeat(4, 1fr); gap: .5rem; margin: 1rem 0 1.2rem;}
.mosaique div {aspect-ratio: 1; border-radius: 16px; display: flex; align-items: center; justify-content: center; font-size: 2rem;}
.etapes {display: flex; flex-direction: column; gap: .5rem; margin: .5rem 0 1.2rem;}
.etape {display: flex; gap: .7rem; align-items: center;}
.etape b {flex: 0 0 28px; height: 28px; border-radius: 50%; background: var(--terre); color: white;
          display: flex; align-items: center; justify-content: center; font-size: .85rem;}

.stButton button, .stDownloadButton button, .stFormSubmitButton button {border-radius: 12px; font-weight: 600;}
div[data-testid="stExpander"] details {border-radius: 14px; background: white;}

/* Fiche recette */
.hero {height: 170px; border-radius: 20px; display: flex; align-items: center; justify-content: center;
       overflow: hidden; position: relative; margin-bottom: .8rem;}
.hero .e {font-size: 5rem; filter: drop-shadow(0 4px 8px rgba(0,0,0,.18));}
.hero .mini {position: absolute; bottom: 10px; right: 14px; font-size: 1.4rem; letter-spacing: 2px;}
.hero img {width: 100%; height: 100%; object-fit: cover;}
.fiche-titre {font-size: 1.6rem; font-weight: 800; letter-spacing: -.02em; margin: 0 0 .2rem; padding: 0;}
.tuiles {display: grid; grid-template-columns: repeat(auto-fit, minmax(92px, 1fr)); gap: .5rem; margin: 1rem 0;}
.tuiles div {background: white; border: 1px solid #EFE6DA; border-radius: 14px; padding: .55rem .6rem;
             display: flex; flex-direction: column; align-items: flex-start;}
.tuiles span {font-size: 1.1rem;} .tuiles small {color: var(--gris); font-size: .72rem;}
.tuiles b {font-size: .98rem;}
ul.ingredients {list-style: none; padding: 0; margin: 0;}
ul.ingredients li {display: flex; justify-content: space-between; padding: .45rem 0;
                   border-bottom: 1px dashed #E6DCCD;}
ul.ingredients li b {white-space: nowrap; margin-left: 1rem;}
.credit {font-size: .72rem; color: var(--gris); margin: -.5rem 0 .6rem; text-align: right;}
.credit a {color: var(--gris);}
.astuce {background: #FFF6DB; border-radius: 14px; padding: .8rem 1rem; margin-top: .8rem;}

/* Magasin */
.magasin {display: flex; gap: .8rem; align-items: flex-start; margin-top: .55rem; padding-top: .55rem;
          border-top: 1px solid #F1E9DC; font-size: .88rem; color: var(--gris);}
.magasin a {color: var(--terre); font-weight: 600; text-decoration: none; white-space: nowrap;}
.adresse {direction: rtl; unicode-bidi: plaintext;}
</style>
"""


def appliquer() -> None:
    st.html(CSS)  # st.html : le CSS est injecté tel quel (pas d'interprétation Markdown)


def entete(titre: str, sous_titre: str = "") -> None:
    st.markdown(f'<div class="entete"><h1>{titre}</h1>'
                + (f"<p>{sous_titre}</p>" if sous_titre else "") + "</div>", unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def _lire_photo(chemin: str, _date_modif: float) -> str:
    # _date_modif fait partie de la clé du cache : une photo remplacée est relue.
    return base64.b64encode(Path(chemin).read_bytes()).decode()


def _photo_base64(id_recette: str) -> tuple[str, str] | None:
    for ext, mime in TYPES_PHOTOS.items():
        f = DOSSIER_PHOTOS / f"{id_recette}{ext}"
        if f.exists():
            return mime, _lire_photo(str(f), f.stat().st_mtime)
    return None


def credit_photo(id_recette: str) -> str:
    """Crédit (auteur, licence) d'une photo téléchargée depuis Wikimedia Commons."""
    import json
    f = DOSSIER_PHOTOS / "credits.json"
    if not f.exists() or _photo_base64(id_recette) is None:
        return ""
    try:
        c = json.loads(f.read_text(encoding="utf-8")).get(id_recette)
    except (ValueError, OSError):
        return ""
    if not c:
        return ""
    return (f'<div class="credit">Photo : {html.escape(c["auteur"])} · '
            f'<a href="{html.escape(c["page"])}" target="_blank" rel="noopener">{html.escape(c["licence"])}, '
            f'Wikimedia Commons</a></div>')


def visuel(recette: dict | None, cacherout: str, catalogue: dict) -> str:
    """HTML du carré illustré d'un plat (photo si disponible)."""
    if recette is None:
        return '<div class="plat-visuel t-vide"><span class="e">🍽️</span></div>'
    photo = _photo_base64(recette["id"])
    if photo:
        return (f'<div class="plat-visuel t-{cacherout}"><img alt="" '
                f'src="data:image/{photo[0]};base64,{photo[1]}"></div>')
    mini = "".join(catalogue[i["id"]].get("emoji", "") for i in recette["ingredients"][:3] if i["id"] in catalogue)
    return (f'<div class="plat-visuel t-{cacherout}"><span class="e">{recette.get("emoji", "🍽️")}</span>'
            f'<span class="mini">{mini}</span></div>')


def visuel_grand(recette: dict, catalogue: dict) -> str:
    """Contenu de la grande image d'en-tête d'une fiche recette."""
    photo = _photo_base64(recette["id"])
    if photo:
        return f'<img alt="" src="data:image/{photo[0]};base64,{photo[1]}">'
    mini = "".join(catalogue[i["id"]].get("emoji", "") for i in recette["ingredients"][:5] if i["id"] in catalogue)
    return f'<span class="e">{recette.get("emoji", "🍽️")}</span><span class="mini">{mini}</span>'


def bloc_magasin(m: dict | None, lien_itineraire: str = "") -> str:
    """Ligne « adresse + itinéraire » d'un magasin (adresse publiée par la chaîne)."""
    if m is None:
        return ""
    lien = (f'<a href="{lien_itineraire}" target="_blank" rel="noopener">📍 Itinéraire</a>'
            if lien_itineraire else "")
    return (f'<div class="magasin"><span style="flex:1"><span class="adresse">{html.escape(m["nom"])} · '
            f'{html.escape(m["adresse"])}</span></span>{lien}</div>')


def chips(props: dict, minutes: int | None = None, ia: bool = False) -> str:
    noms = {"parve": "Parvé", "halavi": "Halavi", "bassari": "Bassari"}
    out = [f'<span class="chip {props["cacherout"]}">{noms.get(props["cacherout"], "?")}</span>']
    if props["vegetarien"]:
        out.append('<span class="chip">🌱 Végé</span>')
    if props["sans_gluten"]:
        out.append('<span class="chip">Sans gluten</span>')
    if minutes:
        out.append(f'<span class="chip">⏱ {minutes} min</span>')
    if ia:
        out.append('<span class="chip">🤖 IA</span>')
    return f'<div class="chips">{"".join(out)}</div>'


def carte_plat(jour: str, recette: dict | None, props: dict | None, catalogue: dict,
               prix: str = "", cuisine: bool = False, sous_prix: str = "") -> str:
    """HTML complet de l'en-tête d'une carte de plat."""
    if recette is None:
        return (f'<div class="plat">{visuel(None, "vide", catalogue)}<div class="plat-info">'
                f'<div class="plat-jour">{jour}</div><div class="plat-nom fait">Pas de dîner prévu</div>'
                '</div></div>')
    nom = html.escape(recette["nom"])  # le nom peut venir de l'IA : on l'échappe
    coche = "✅ " if cuisine else ""
    return (f'<div class="plat">{visuel(recette, props["cacherout"], catalogue)}'
            f'<div class="plat-info">'
            + (f'<div class="plat-jour">{jour}</div>' if jour else "")
            + f'<div class="plat-nom{" fait" if cuisine else ""}">{coche}{nom}</div>'
            f'{chips(props, recette.get("minutes"), recette.get("source") == "ia")}</div>'
            + (f'<div class="plat-prix">{prix}<small>{sous_prix}</small></div>' if prix else "")
            + "</div>")


def carte(html_interne: str, classe: str = "") -> None:
    st.markdown(f'<div class="carte {classe}">{html_interne}</div>', unsafe_allow_html=True)


def jauge_budget(cout: float, budget: float, texte_cout: str, texte_reste: str) -> None:
    ratio = 0 if budget <= 0 else cout / budget
    couleur = "#5E7A3A" if ratio <= 0.85 else ("#D98E04" if ratio <= 1 else "#B3261E")
    reste = budget - cout
    phrase = (f'<span class="vert">Il reste {texte_reste}</span>' if reste >= 0
              else f'<span class="rouge">Dépassement de {texte_reste}</span>')
    carte(f'<div class="carte-titre">Coût du menu</div>'
          f'<div class="carte-valeur">{texte_cout}</div>'
          f'<div class="jauge"><div style="width:{min(ratio, 1) * 100:.0f}%;background:{couleur}"></div></div>'
          f'<div class="carte-sous">{phrase} sur votre budget</div>')
