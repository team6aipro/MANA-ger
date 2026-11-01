"""Teste la validation des réponses de l'IA, avec un FAUX client (aucun appel réel)."""
import json
from types import SimpleNamespace

from core import donnees, ia, regles

CAT = donnees.catalogue()
PREFS = {"budget": 200, "nb_personnes": 1, "cacherout": ["parve", "halavi", "bassari"],
         "vegetarien": False, "sans_gluten": False, "a_eviter": []}
BONNE = {"nom": "Riz aux œufs", "description": "x", "etapes": ["cuire"], "preparation": 5, "cuisson": 15,
         "ingredients": [{"id": "riz", "quantite": 80}, {"id": "oeufs", "quantite": 2}]}


def rep(obj):
    texte = obj if isinstance(obj, str) else json.dumps(obj)
    return SimpleNamespace(stop_reason="end_turn", content=[SimpleNamespace(type="text", text=texte)])


class FauxClient:
    def __init__(self, reponses):
        self.reponses = list(reponses)
        self.appels = []
        self.messages = self

    def create(self, **kw):
        self.appels.append(kw)
        return self.reponses.pop(0)


def test_ingredient_inconnu_rejete():
    r = dict(BONNE, ingredients=[{"id": "caviar", "quantite": 10}, {"id": "riz", "quantite": 80}])
    assert any("inconnu" in e for e in regles.erreurs_recette(r, CAT))


def test_quantites_invalides_rejetees():
    for q in [0, -5, "100", None, True, 99999]:
        r = dict(BONNE, ingredients=[{"id": "riz", "quantite": q}, {"id": "oeufs", "quantite": 1}])
        assert regles.erreurs_recette(r, CAT), q


def test_melange_viande_lait_rejete():
    r = dict(BONNE, ingredients=[{"id": "poulet", "quantite": 150}, {"id": "lait", "quantite": 100}])
    assert any("viande et lait" in e for e in regles.erreurs_recette(r, CAT))


def test_json_avec_balises_markdown_accepte():
    valides, erreurs = ia.valider_reponse("```json\n" + json.dumps({"recettes": [BONNE]}) + "\n```", PREFS, CAT)
    assert len(valides) == 1 and not erreurs
    assert valides[0]["id"] == "ia_riz_aux_oeufs"


def test_texte_non_json_rejete():
    valides, erreurs = ia.valider_reponse("Voici une recette : du riz !", PREFS, CAT)
    assert not valides and "JSON" in erreurs[0]


def test_preferences_verifiees_par_le_code():
    prefs = dict(PREFS, vegetarien=True)
    r = dict(BONNE, nom="Poulet", ingredients=[{"id": "poulet", "quantite": 150}, {"id": "riz", "quantite": 80}])
    valides, erreurs = ia.valider_reponse(json.dumps({"recettes": [r]}), prefs, CAT)
    assert not valides and "préférences" in erreurs[0]


def test_redemande_apres_rejet():
    mauvaise = dict(BONNE, nom="Mauvaise", ingredients=[{"id": "caviar", "quantite": 1}, {"id": "riz", "quantite": 1}])
    client = FauxClient([rep({"recettes": [mauvaise]}), rep({"recettes": [BONNE]})])
    recettes, journal = ia.creer_recettes(client, 1, PREFS, CAT)
    assert [r["nom"] for r in recettes] == ["Riz aux œufs"]
    assert len(client.appels) == 2
    assert "caviar" in client.appels[1]["messages"][-1]["content"]  # l'erreur est renvoyée à l'IA
    assert client.appels[0]["model"] == "claude-haiku-5-5"


def test_abandon_apres_3_essais():
    client = FauxClient([rep("pas du json")] * 3)
    recettes, journal = ia.creer_recettes(client, 2, PREFS, CAT)
    assert recettes == [] and len(client.appels) == 3


def test_temps_invalides_rejetes():
    for prep, cuis in [(-1, 10), ("10", 5), (5.5, 5), (0, 0), (300, 0), (None, 10)]:
        r = dict(BONNE, preparation=prep, cuisson=cuis)
        assert regles.erreurs_recette(r, CAT), (prep, cuis)


def test_temps_conserves():
    valides, _ = ia.valider_reponse(json.dumps({"recettes": [BONNE]}), PREFS, CAT)
    assert valides[0]["minutes"] == 20 and valides[0]["preparation"] == 5
