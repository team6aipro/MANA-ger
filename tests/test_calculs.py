from core import calculs, donnees, menu

CAT = donnees.catalogue()


def test_paquets_arrondis_au_superieur():
    # 600 g de pâtes, vendues par 500 g -> 2 paquets
    ligne = calculs.ligne_achat(CAT["pates"], 600, 5.0)
    assert ligne["a_acheter"].startswith("2 ×")
    assert ligne["cout"] == 10.0


def test_vente_au_poids_avec_pieces():
    # 5 tomates de 120 g = 0,6 kg à 10 ₪/kg = 6 ₪
    ligne = calculs.ligne_achat(CAT["tomate"], 5, 10.0)
    assert ligne["cout"] == 6.0
    assert ligne["a_acheter"] == "600 g"
    assert calculs.ligne_achat(CAT["tomate"], 10, 10.0)["a_acheter"] == "1,20 kg"


def test_besoins_additionnes_et_plats_retires_ignores():
    recettes = {"a": {"ingredients": [{"id": "riz", "quantite": 100}]},
                "b": {"ingredients": [{"id": "riz", "quantite": 50}, {"id": "oeufs", "quantite": 1}]}}
    plats = [{"recette_id": "a"}, {"recette_id": "b"}, {"recette_id": None}]
    assert calculs.besoins_semaine(plats, recettes, 2) == {"riz": 300, "oeufs": 2}


def test_comparaison_et_economie():
    besoins = {"riz": 1000}
    prix = {"x": {"riz": 10.0}, "y": {"riz": 7.5}, "z": {}}
    comp = calculs.comparer_chaines(besoins, CAT, prix)
    assert comp["moins_chere"] == "y"
    assert comp["economie"] == 2.5
    assert comp["paniers"]["z"]["manquants"] == ["riz"]  # chaîne incomplète non classée


def test_budget():
    assert calculs.etat_budget(120, 100)["depasse"]
    assert calculs.etat_budget(80, 100)["reste"] == 20


def test_menu_genere_respecte_preferences_et_budget():
    prefs = {"budget": 1000, "nb_personnes": 2, "cacherout": ["parve", "halavi"],
             "vegetarien": True, "sans_gluten": False, "a_eviter": ["tahini"]}
    recettes = {r["id"]: r for r in donnees.recettes_base()}
    prix = donnees.prix()["chaines"]
    plats, _ = menu.generer(recettes, prefs, CAT, prix, graine=1)
    assert len(plats) == 7
    for p in plats:
        ids = [i["id"] for i in recettes[p["recette_id"]]["ingredients"]]
        assert "tahini" not in ids and "poulet" not in ids and "boeuf_hache" not in ids
    assert menu.cout_semaine(plats, recettes, prefs, CAT, prix) <= 1000


def test_menu_budget_serre_choisit_moins_cher():
    prefs = {"budget": 1, "nb_personnes": 1, "cacherout": ["parve", "halavi", "bassari"],
             "vegetarien": False, "sans_gluten": False, "a_eviter": []}
    recettes = {r["id"]: r for r in donnees.recettes_base()}
    _, messages = menu.generer(recettes, prefs, CAT, donnees.prix()["chaines"], graine=1)
    assert any("budget" in m for m in messages)


def test_donnees_coherentes():
    assert len(CAT) == 30
    p = donnees.prix()
    assert p["fictif"] is True
    for chaine in donnees.CHAINES:
        assert set(p["chaines"][chaine]) == set(CAT)
    for r in donnees.recettes_base():
        from core import regles
        assert regles.erreurs_recette(r, CAT) == [], r["id"]


def test_magasins_et_liens_maps():
    from core import magasins
    for chaine in donnees.CHAINES:
        assert magasins.de_la_chaine(chaine), chaine
    m = magasins.trouver("rami_levy", "inexistant")  # repli sur le premier magasin
    assert m["chaine"] == "rami_levy"
    assert magasins.lien_carte(m).startswith("https://www.google.com/maps/search/?api=1&query=")
    assert " " not in magasins.lien_itineraire(m)
