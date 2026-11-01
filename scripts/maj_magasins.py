"""Met à jour data/magasins.json avec TOUS les magasins de Jérusalem des 3 chaînes.

    pip install israeli-prices==0.2.0
    python scripts/maj_magasins.py

Les adresses viennent des fichiers « Stores » publiés par les chaînes.
"""
import json
import sys
from datetime import date
from pathlib import Path

try:
    import israeli_prices as ilp
except ImportError:
    sys.exit("Installez d'abord la bibliothèque :  pip install israeli-prices==0.2.0")

FICHIER = Path(__file__).resolve().parent.parent / "data" / "magasins.json"
CHAINES = {"shufersal": "shufersal", "rami-levy": "rami_levy", "osher-ad": "osher_ad"}
CODE_JERUSALEM = "3000"  # confirmé par test le 2026-11-01

magasins = []
for slug, cle in CHAINES.items():
    try:
        stores = ilp.get_stores(slug).stores
    except Exception as e:
        print(f"{slug} : ÉCHEC {type(e).__name__}: {e} — chaîne ignorée")
        continue
    jer = [s for s in stores if "ירושלים" in f"{s.city} {s.address} {s.name}"
           or str(s.city or "").strip() == CODE_JERUSALEM]
    print(f"{slug} : {len(jer)} magasin(s) à Jérusalem")
    magasins += [{"chaine": cle, "id": s.store_id, "nom": (s.name or "").strip(),
                  "adresse": (s.address or "").strip()} for s in jer]

if not magasins:
    sys.exit("Aucun magasin récupéré : fichier inchangé.")
FICHIER.write_text(json.dumps({
    "_source": "Fichiers « Stores » publiés par les chaînes, relevés avec scripts/maj_magasins.py.",
    "date": str(date.today()), "magasins": magasins}, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"OK : {len(magasins)} magasins écrits dans {FICHIER.name}")
