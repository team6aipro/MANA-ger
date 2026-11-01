"""Télécharge de VRAIES photos libres de droits pour les plats (Wikimedia Commons).

À lancer sur VOTRE ordinateur (Internet nécessaire) :

    python scripts/telecharger_photos.py              # toutes les recettes sans photo
    python scripts/telecharger_photos.py --refaire shakshuka   # photo suivante pour un plat

Pour chaque plat, le script :
1. cherche des photos sur Wikimedia Commons (banque d'images libres) ;
2. garde UNIQUEMENT les licences libres (domaine public, CC0, CC BY, CC BY-SA) ;
3. enregistre la photo dans data/photos/<id>.jpg ;
4. note l'auteur et la licence dans data/photos/credits.json : l'application affiche
   ce crédit sous la photo, comme l'exigent les licences CC BY.

⚠️ Le choix est AUTOMATIQUE (premier résultat valable) : regardez chaque photo dans
l'application. Si une photo ne correspond pas au plat, lancez --refaire <id>.
"""
import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
PHOTOS = RACINE / "data" / "photos"
CREDITS = PHOTOS / "credits.json"
API = "https://commons.wikimedia.org/w/api.php"
# Wikimedia demande un User-Agent qui décrit l'outil.
ENTETES = {"User-Agent": "PanierDeLaSemaine/1.0 (projet etudiant; script telecharger_photos.py)"}

LICENCES_OK = ("public domain", "pd", "cc0", "cc by", "cc-by")
TYPES_OK = ("image/jpeg", "image/png", "image/webp")

# Mots de recherche (en anglais : bien plus de résultats sur Commons).
RECHERCHES = {
    "shakshuka": "shakshuka",
    "pates_tomate_fromage": "pasta tomato sauce cheese",
    "mujadara": "mujaddara",
    "poulet_pommes_de_terre": "roast chicken potatoes",
    "taboule_pois_chiches": "tabbouleh",
    "houmous_pita": "hummus pita",
    "boulettes_boeuf": "meatballs tomato sauce",
    "omelette_courgettes": "zucchini omelette",
    "aubergine_tahini_boulgour": "roasted eggplant tahini",
    "gratin_pommes_de_terre": "gratin dauphinois",
    "pates_thon": "pasta tuna",
    "salade_feta_pita": "greek salad feta",
    "soupe_lentilles": "lentil soup",
    "poulet_riz_poivrons": "chicken stir fry peppers",
    "pita_fromage_blanc": "pita sandwich vegetables",
    "riz_saute_legumes": "fried rice vegetables egg",
}


def texte_simple(html_ou_texte: str) -> str:
    """Enlève les balises HTML (le champ « Artist » de Commons en contient souvent)."""
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", html_ou_texte or "")).strip()


def licence_libre(nom_licence: str) -> bool:
    n = nom_licence.lower()
    return any(n.startswith(l) for l in LICENCES_OK) and "nc" not in n and "nd" not in n


def candidats(reponse_api: dict) -> list[dict]:
    """Transforme la réponse de l'API en liste de photos utilisables, dans l'ordre de pertinence."""
    pages = sorted(reponse_api.get("query", {}).get("pages", {}).values(), key=lambda p: p.get("index", 0))
    out = []
    for p in pages:
        info = (p.get("imageinfo") or [{}])[0]
        meta = info.get("extmetadata", {})
        licence = meta.get("LicenseShortName", {}).get("value", "")
        if info.get("mime") not in TYPES_OK or not licence_libre(licence) or not info.get("thumburl"):
            continue
        out.append({
            "fichier": p.get("title", ""),
            "url_image": info["thumburl"],
            "page": info.get("descriptionurl", ""),
            "auteur": texte_simple(meta.get("Artist", {}).get("value", "")) or "auteur inconnu",
            "licence": licence,
            "url_licence": meta.get("LicenseUrl", {}).get("value", ""),
        })
    return out


def chercher(mots: str) -> list[dict]:
    params = {"action": "query", "format": "json", "generator": "search",
              "gsrsearch": f"{mots} filetype:bitmap", "gsrnamespace": "6", "gsrlimit": "15",
              "prop": "imageinfo", "iiprop": "url|mime|extmetadata", "iiurlwidth": "800"}
    req = urllib.request.Request(API + "?" + urllib.parse.urlencode(params), headers=ENTETES)
    with urllib.request.urlopen(req, timeout=30) as r:
        return candidats(json.load(r))


def main():
    PHOTOS.mkdir(parents=True, exist_ok=True)
    credits = json.loads(CREDITS.read_text(encoding="utf-8")) if CREDITS.exists() else {}
    a_refaire = sys.argv[sys.argv.index("--refaire") + 1] if "--refaire" in sys.argv else None
    if a_refaire and a_refaire not in RECHERCHES:
        sys.exit(f"Identifiant inconnu : {a_refaire}. Choix : {', '.join(RECHERCHES)}")

    for id_recette, mots in RECHERCHES.items():
        if a_refaire and id_recette != a_refaire:
            continue
        deja = [f for f in PHOTOS.glob(f"{id_recette}.*")]
        if deja and not a_refaire:
            print(f"✓ {id_recette} : photo déjà présente")
            continue
        refuses = credits.get(id_recette, {}).get("refuses", [])
        if a_refaire and id_recette in credits:
            refuses.append(credits[id_recette]["fichier"])
        try:
            choix = next((c for c in chercher(mots) if c["fichier"] not in refuses), None)
        except Exception as e:
            print(f"✗ {id_recette} : ÉCHEC de la recherche ({type(e).__name__}: {e})")
            continue
        if choix is None:
            print(f"✗ {id_recette} : aucune photo libre trouvée")
            continue
        req = urllib.request.Request(choix["url_image"], headers=ENTETES)
        with urllib.request.urlopen(req, timeout=60) as r:
            donnees = r.read()
        for f in deja:
            f.unlink()
        ext = ".png" if choix["url_image"].lower().endswith(".png") else ".jpg"
        (PHOTOS / f"{id_recette}{ext}").write_bytes(donnees)
        credits[id_recette] = {**choix, "refuses": refuses}
        print(f"✓ {id_recette} : {choix['fichier']} — {choix['auteur']} ({choix['licence']})")

    CREDITS.write_text(json.dumps(credits, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\nTerminé. Relancez l'application et vérifiez chaque photo.")


if __name__ == "__main__":
    main()
