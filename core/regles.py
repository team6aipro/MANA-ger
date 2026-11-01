"""Règles sur les recettes : propriétés (cacherout, végétarien, gluten),
validation stricte (utilisée pour les réponses de l'IA) et filtre par préférences.

Tout est calculé par le CODE à partir du catalogue, jamais par l'IA.
"""

# Quantité maximale PAR PERSONNE pour un ingrédient, selon son unité.
QUANTITE_MAX = {"g": 400, "ml": 300, "piece": 4}

NOMS_CACHEROUT = {"bassari": "Bassari (viande)", "halavi": "Halavi (lait)", "parve": "Parvé"}


def proprietes(recette: dict, catalogue: dict) -> dict:
    """Déduit cacherout / végétarien / gluten des ingrédients de la recette."""
    ings = [catalogue[i["id"]] for i in recette["ingredients"] if i["id"] in catalogue]
    types = {ing["cacherout"] for ing in ings}
    if "bassari" in types and "halavi" in types:
        cacherout = "melange_interdit"
    elif "bassari" in types:
        cacherout = "bassari"
    elif "halavi" in types:
        cacherout = "halavi"
    else:
        cacherout = "parve"
    return {
        "cacherout": cacherout,
        "vegetarien": all(ing["vegetarien"] for ing in ings),
        "sans_gluten": not any(ing["gluten"] for ing in ings),
    }


def erreurs_recette(recette, catalogue: dict) -> list[str]:
    """Vérifie une recette (par ex. venant de l'IA). Liste vide = recette valide."""
    if not isinstance(recette, dict):
        return ["la recette n'est pas un objet JSON"]
    erreurs = []
    nom = recette.get("nom")
    if not isinstance(nom, str) or not nom.strip():
        erreurs.append("champ 'nom' manquant ou vide")
    etapes = recette.get("etapes")
    if not isinstance(etapes, list) or not etapes or not all(isinstance(e, str) and e.strip() for e in etapes):
        erreurs.append("champ 'etapes' doit être une liste de textes non vide")
    for champ in ("preparation", "cuisson"):  # temps en minutes
        t = recette.get(champ)
        if isinstance(t, bool) or not isinstance(t, int) or not 0 <= t <= 240:
            erreurs.append(f"champ '{champ}' doit être un nombre entier de minutes entre 0 et 240")
    if not erreurs and recette["preparation"] + recette["cuisson"] == 0:
        erreurs.append("le temps total ne peut pas être 0 minute")
    ingredients = recette.get("ingredients")
    if not isinstance(ingredients, list) or not 2 <= len(ingredients) <= 12:
        erreurs.append("champ 'ingredients' doit être une liste de 2 à 12 éléments")
        return erreurs
    vus = set()
    for ing in ingredients:
        if not isinstance(ing, dict):
            erreurs.append("un ingrédient n'est pas un objet JSON")
            continue
        id_ = ing.get("id")
        q = ing.get("quantite")
        if id_ not in catalogue:
            erreurs.append(f"ingrédient inconnu : {id_!r}")
            continue
        if id_ in vus:
            erreurs.append(f"ingrédient en double : {id_}")
        vus.add(id_)
        # bool est un sous-type de int en Python : on l'exclut explicitement.
        if isinstance(q, bool) or not isinstance(q, (int, float)):
            erreurs.append(f"quantité non numérique pour {id_} : {q!r}")
            continue
        unite = catalogue[id_]["unite"]
        if not 0 < q <= QUANTITE_MAX[unite]:
            erreurs.append(f"quantité invalide pour {id_} : {q} {unite} (attendu entre 0 et {QUANTITE_MAX[unite]})")
    if not erreurs and proprietes(recette, catalogue)["cacherout"] == "melange_interdit":
        erreurs.append("mélange viande et lait interdit (cacherout)")
    return erreurs


def compatible(recette: dict, prefs: dict, catalogue: dict) -> bool:
    """La recette respecte-t-elle les préférences de l'utilisateur ?"""
    p = proprietes(recette, catalogue)
    if p["cacherout"] not in prefs["cacherout"]:
        return False
    if prefs["vegetarien"] and not p["vegetarien"]:
        return False
    if prefs["sans_gluten"] and not p["sans_gluten"]:
        return False
    a_eviter = set(prefs["a_eviter"])
    return not any(i["id"] in a_eviter for i in recette["ingredients"])
