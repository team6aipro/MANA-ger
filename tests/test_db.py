import importlib
from datetime import date


def test_sauvegarde_et_relecture(tmp_path, monkeypatch):
    monkeypatch.setenv("PANIER_DB", str(tmp_path / "test.db"))
    from core import db
    importlib.reload(db)
    uid = db.utilisateur("Etudiant@Example.com")
    assert db.utilisateur("etudiant@example.com") == uid  # même compte
    assert db.lire_preferences(uid) is None
    db.ecrire_preferences(uid, {"budget": 150, "nb_personnes": 2})
    assert db.lire_preferences(uid)["budget"] == 150
    plats = [{"recette_id": "mujadara", "cuisine": False}] * 7
    db.ecrire_menu(uid, "2026-11-01", plats)
    assert db.dernier_menu(uid) == ("2026-11-01", plats)


def test_semaine_commence_dimanche():
    from core import db
    assert db.debut_semaine(date(2026, 11, 4)) == "2026-11-01"  # mercredi -> dimanche
    assert db.debut_semaine(date(2026, 11, 1)) == "2026-11-01"
