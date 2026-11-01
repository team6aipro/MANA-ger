"""ÉTAPE 7 — Test rapide des vraies sources de prix (à lancer sur VOTRE ordinateur).

But : vérifier AVANT d'en dépendre que la bibliothèque israeli-prices arrive
à télécharger les prix de Shufersal, Rami Levy et Osher Ad.

    pip install israeli-prices==0.2.0
    python scripts/tester_sources_prix.py

Ce script :
1. liste les magasins de chaque chaîne situés à Jérusalem ;
2. télécharge le fichier PriceFull d'un magasin (au plus une fois par jour : cache/) ;
3. cherche quelques produits du catalogue par leur nom hébreu, pour vous aider
   à choisir les codes-barres à mettre dans data/catalogue.json.

Il ne modifie PAS l'application : les prix affichés restent FICTIFS tant que
nous n'avons pas validé ces données ensemble.
"""
import json
import sys
from datetime import date
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
CACHE = RACINE / "cache"
# Noms (« slugs ») utilisés par la bibliothèque — lus dans son code source v0.2.0.
CHAINES = {"shufersal": "Shufersal", "rami-levy": "Rami Levy", "osher-ad": "Osher Ad"}

try:
    import israeli_prices as ilp
except ImportError:
    sys.exit("Installez d'abord la bibliothèque :  pip install israeli-prices==0.2.0")


# Code officiel (Bureau central des statistiques) de la ville de Jérusalem.
# Rami Levy et Osher Ad écrivent ce code au lieu du nom (confirmé par test le 2026-11-01).
CODE_JERUSALEM = "3000"


def magasins_jerusalem(slug):
    stores = ilp.get_stores(slug).stores
    trouves = [s for s in stores
               if "ירושלים" in f"{s.city} {s.address} {s.name}" or "Jerusalem" in f"{s.city}"
               or str(s.city or "").strip() == CODE_JERUSALEM]
    if not trouves:  # diagnostic : on montre comment la chaîne écrit ses magasins
        print(f"   Aucun magasin reconnu à Jérusalem parmi {len(stores)}. Exemples bruts :")
        for s in stores[:8]:
            print(f"     id={s.store_id!r} nom={s.name!r} adresse={s.address!r} ville={s.city!r}")
    return trouves


def prix_magasin(slug, store_id):
    """Télécharge les prix d'un magasin, au maximum une fois par jour."""
    CACHE.mkdir(exist_ok=True)
    fichier = CACHE / f"{slug}_{store_id}_{date.today()}.json"
    if fichier.exists():
        print("   (lu depuis le cache du jour)")
        return json.loads(fichier.read_text(encoding="utf-8"))
    pf = ilp.get_prices(slug, store_id=store_id)
    items = [{"code": it.item_code, "nom": it.name, "prix": str(it.price),
              "quantite": str(it.quantity), "unite": it.unit_qty, "au_poids": it.is_weighted}
             for it in pf.items]
    fichier.write_text(json.dumps(items, ensure_ascii=False), encoding="utf-8")
    return items


catalogue = json.loads((RACINE / "data" / "catalogue.json").read_text(encoding="utf-8"))["ingredients"]
for slug, nom in CHAINES.items():
    print(f"\n=== {nom} ({slug}) ===")
    try:
        mags = magasins_jerusalem(slug)
        print(f"   {len(mags)} magasin(s) trouvé(s) à Jérusalem")
        for s in mags[:5]:
            print(f"   - {s.store_id} : {s.name} — {s.address}")
        if not mags:
            continue
        items = prix_magasin(slug, mags[0].store_id)
        print(f"   {len(items)} produits dans le magasin {mags[0].store_id}")
        for ing in catalogue[:5]:
            trouves = [i for i in items if i["nom"] and i["nom"].startswith(ing["nom_he"][:4])][:3]
            print(f"   « {ing['nom_he']} » ({ing['nom_fr']}) : "
                  + (", ".join(f"{t['nom']} [{t['code']}] {t['prix']} ₪" for t in trouves) or "aucun résultat"))
        print("   → Pour chercher un produit précis : python scripts/chercher_produit.py <mot en hébreu>")
    except Exception as e:  # on veut voir l'erreur exacte pour chaque chaîne
        print(f"   ÉCHEC : {type(e).__name__}: {e}")
print("\nNotez les résultats (succès / échec par chaîne) et envoyez-les-moi.")
