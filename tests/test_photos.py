"""Teste le tri des photos Wikimedia (sans connexion Internet)."""
import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "telecharger_photos", Path(__file__).resolve().parent.parent / "scripts" / "telecharger_photos.py")
tp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tp)


def page(index, titre, licence, mime="image/jpeg"):
    return {"index": index, "title": titre, "imageinfo": [{
        "thumburl": f"https://x/{titre}.jpg", "mime": mime, "descriptionurl": f"https://c/{titre}",
        "extmetadata": {"LicenseShortName": {"value": licence},
                        "Artist": {"value": "<a href='u'>Dana</a>"}}}]}


def test_licences():
    assert tp.licence_libre("CC BY-SA 4.0") and tp.licence_libre("CC0") and tp.licence_libre("Public domain")
    assert not tp.licence_libre("CC BY-NC 2.0") and not tp.licence_libre("CC BY-ND 3.0")
    assert not tp.licence_libre("All rights reserved")


def test_candidats_filtres_et_ordonnes():
    rep = {"query": {"pages": {
        "1": page(3, "C", "CC BY 2.0"),
        "2": page(1, "A", "CC BY-NC 2.0"),          # non commerciale : refusée
        "3": page(2, "B", "CC0"),
        "4": page(0, "V", "CC0", mime="video/webm"),  # pas une image : refusée
    }}}
    c = tp.candidats(rep)
    assert [x["fichier"] for x in c] == ["B", "C"]
    assert c[0]["auteur"] == "Dana"  # balises HTML retirées
