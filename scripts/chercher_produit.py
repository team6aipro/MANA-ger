"""Chercher un produit dans les prix téléchargés (cache/), pour choisir son code-barres.

À lancer APRÈS scripts/tester_sources_prix.py (qui remplit le dossier cache/).

    python scripts/chercher_produit.py עגבני
    python scripts/chercher_produit.py "אורז פרסי"

Affiche, pour chaque chaîne, les produits dont le nom COMMENCE par les mots
cherchés (puis ceux qui les contiennent), avec code-barres, prix, quantité
et « au poids » si le produit est vendu au kilo.
"""
import json
import sys
from pathlib import Path

CACHE = Path(__file__).resolve().parent.parent / "cache"

if len(sys.argv) < 2:
    sys.exit('Usage : python scripts/chercher_produit.py <mot en hébreu>')
mot = " ".join(sys.argv[1:]).strip()

# Le fichier le plus récent pour chaque (chaîne, magasin).
fichiers = sorted(CACHE.glob("*.json"))
if not fichiers:
    sys.exit("Le dossier cache/ est vide : lancez d'abord python scripts/tester_sources_prix.py")
derniers = {}
for f in fichiers:
    chaine_magasin = f.stem.rsplit("_", 1)[0]  # ex. "shufersal_42"
    derniers[chaine_magasin] = f

for chaine_magasin, f in sorted(derniers.items()):
    items = [i for i in json.loads(f.read_text(encoding="utf-8")) if i.get("nom")]
    debut = [i for i in items if i["nom"].startswith(mot)]
    dedans = [i for i in items if mot in i["nom"] and i not in debut]
    resultats = (debut + dedans)[:15]
    print(f"\n=== {chaine_magasin} ({f.stem.rsplit('_', 1)[1]}) : {len(debut) + len(dedans)} résultat(s) ===")
    for i in resultats:
        poids = " · AU POIDS (prix/kg)" if i.get("au_poids") in (True, "True") else ""
        print(f"   [{i['code']}] {i['nom']} — {i['prix']} ₪ · {i['quantite']} {i['unite'] or ''}{poids}")
