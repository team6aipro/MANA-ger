"""Base de données SQLite : utilisateurs, préférences, menus, recettes créées par l'IA.

Le fichier panier.db est créé automatiquement (et ignoré par git).
"""
import json
import os
import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path

CHEMIN_DB = Path(os.environ.get("PANIER_DB", Path(__file__).resolve().parent.parent / "panier.db"))

PREFS_DEFAUT = {
    "budget": 200.0,
    "nb_personnes": 1,
    "cacherout": ["parve", "halavi", "bassari"],
    "vegetarien": False,
    "sans_gluten": False,
    "a_eviter": [],
    "magasins": {},   # {chaine: id du magasin préféré}
}

SCHEMA = """
CREATE TABLE IF NOT EXISTS utilisateurs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    nom TEXT,
    cree_le TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS preferences (
    utilisateur_id INTEGER PRIMARY KEY REFERENCES utilisateurs(id),
    donnees TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS menus (
    utilisateur_id INTEGER NOT NULL REFERENCES utilisateurs(id),
    semaine TEXT NOT NULL,          -- date du dimanche qui commence la semaine
    plats TEXT NOT NULL,            -- JSON : liste de 7 plats
    maj_le TEXT NOT NULL,
    PRIMARY KEY (utilisateur_id, semaine)
);
CREATE TABLE IF NOT EXISTS recettes_ia (
    id TEXT PRIMARY KEY,
    utilisateur_id INTEGER NOT NULL REFERENCES utilisateurs(id),
    donnees TEXT NOT NULL,
    cree_le TEXT NOT NULL
);
"""


def connexion() -> sqlite3.Connection:
    con = sqlite3.connect(CHEMIN_DB)
    con.row_factory = sqlite3.Row
    con.executescript(SCHEMA)
    return con


def _maintenant() -> str:
    return datetime.now().isoformat(timespec="seconds")


def debut_semaine(jour: date | None = None) -> str:
    """En Israël la semaine commence le dimanche."""
    jour = jour or date.today()
    return (jour - timedelta(days=(jour.weekday() + 1) % 7)).isoformat()


def utilisateur(email: str, nom: str | None = None) -> int:
    """Renvoie l'id de l'utilisateur, en le créant si besoin."""
    email = email.strip().lower()
    with connexion() as con:
        ligne = con.execute("SELECT id FROM utilisateurs WHERE email = ?", (email,)).fetchone()
        if ligne:
            return ligne["id"]
        cur = con.execute("INSERT INTO utilisateurs (email, nom, cree_le) VALUES (?, ?, ?)",
                          (email, nom, _maintenant()))
        return cur.lastrowid


def lire_preferences(uid: int) -> dict | None:
    with connexion() as con:
        ligne = con.execute("SELECT donnees FROM preferences WHERE utilisateur_id = ?", (uid,)).fetchone()
    return None if ligne is None else {**PREFS_DEFAUT, **json.loads(ligne["donnees"])}


def ecrire_preferences(uid: int, prefs: dict) -> None:
    with connexion() as con:
        con.execute("INSERT INTO preferences (utilisateur_id, donnees) VALUES (?, ?) "
                    "ON CONFLICT(utilisateur_id) DO UPDATE SET donnees = excluded.donnees",
                    (uid, json.dumps(prefs, ensure_ascii=False)))


def lire_menu(uid: int, semaine: str) -> list[dict] | None:
    with connexion() as con:
        ligne = con.execute("SELECT plats FROM menus WHERE utilisateur_id = ? AND semaine = ?",
                            (uid, semaine)).fetchone()
    return None if ligne is None else json.loads(ligne["plats"])


def dernier_menu(uid: int) -> tuple[str, list[dict]] | None:
    with connexion() as con:
        ligne = con.execute("SELECT semaine, plats FROM menus WHERE utilisateur_id = ? "
                            "ORDER BY semaine DESC LIMIT 1", (uid,)).fetchone()
    return None if ligne is None else (ligne["semaine"], json.loads(ligne["plats"]))


def ecrire_menu(uid: int, semaine: str, plats: list[dict]) -> None:
    with connexion() as con:
        con.execute("INSERT INTO menus (utilisateur_id, semaine, plats, maj_le) VALUES (?, ?, ?, ?) "
                    "ON CONFLICT(utilisateur_id, semaine) DO UPDATE SET plats = excluded.plats, "
                    "maj_le = excluded.maj_le",
                    (uid, semaine, json.dumps(plats, ensure_ascii=False), _maintenant()))


def ajouter_recette_ia(uid: int, recette: dict) -> None:
    with connexion() as con:
        con.execute("INSERT OR REPLACE INTO recettes_ia (id, utilisateur_id, donnees, cree_le) "
                    "VALUES (?, ?, ?, ?)",
                    (recette["id"], uid, json.dumps(recette, ensure_ascii=False), _maintenant()))


def recettes_ia(uid: int) -> list[dict]:
    with connexion() as con:
        lignes = con.execute("SELECT donnees FROM recettes_ia WHERE utilisateur_id = ? ORDER BY cree_le",
                             (uid,)).fetchall()
    return [json.loads(l["donnees"]) for l in lignes]
