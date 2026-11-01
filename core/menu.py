"""Création et modification du menu de la semaine (7 dîners)."""
import random

from . import calculs, regles

JOURS = ["Dimanche", "Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi"]


def nouveau_plat(recette_id: str | None) -> dict:
    return {"recette_id": recette_id, "cuisine": False}


def candidats(recettes: dict, prefs: dict, catalogue: dict) -> list[str]:
    """Ids des recettes compatibles avec les préférences."""
    return [rid for rid, r in recettes.items() if regles.compatible(r, prefs, catalogue)]


def cout_plat(recette: dict, catalogue: dict, prix_chaines: dict, nb_personnes: int) -> float | None:
    """Coût d'une part de plat dans la chaîne la moins chère pour ce plat."""
    couts = [c for p in prix_chaines.values()
             if (c := calculs.cout_part_recette(recette, catalogue, p, nb_personnes)) is not None]
    return min(couts) if couts else None


def cout_semaine(plats, recettes, prefs, catalogue, prix_chaines) -> float:
    """Prix du panier de la semaine dans la chaîne la moins chère."""
    besoins = calculs.besoins_semaine(plats, recettes, prefs["nb_personnes"])
    comp = calculs.comparer_chaines(besoins, catalogue, prix_chaines)
    if comp["moins_chere"] is None:
        return 0.0
    return comp["paniers"][comp["moins_chere"]]["total"]


def generer(recettes: dict, prefs: dict, catalogue: dict, prix_chaines: dict,
            graine: int | None = None) -> tuple[list[dict], list[str]]:
    """Propose 7 dîners qui respectent les préférences et, si possible, le budget.

    Renvoie (plats, messages). Le budget est vérifié par le code.
    """
    messages = []
    rng = random.Random(graine)
    ids = candidats(recettes, prefs, catalogue)
    if not ids:
        return [nouveau_plat(None) for _ in JOURS], [
            "Aucune recette ne correspond à vos préférences. Assouplissez-les ou créez des recettes avec l'IA."]
    rng.shuffle(ids)
    if len(ids) < 7:
        messages.append(f"Seulement {len(ids)} recettes compatibles : certains plats reviennent plusieurs fois. "
                        "Créez de nouvelles recettes avec l'IA pour plus de variété.")
    choix = [ids[i % len(ids)] for i in range(7)]

    cout = {rid: cout_plat(recettes[rid], catalogue, prix_chaines, prefs["nb_personnes"]) or 0.0 for rid in ids}
    # Tant que le panier dépasse le budget : on remplace le plat le plus cher
    # par le moins cher des plats pas encore choisis.
    for _ in range(20):
        plats = [nouveau_plat(r) for r in choix]
        if cout_semaine(plats, recettes, prefs, catalogue, prix_chaines) <= prefs["budget"]:
            break
        libres = sorted((r for r in ids if r not in choix), key=cout.get)
        i_cher = max(range(7), key=lambda i: cout[choix[i]])
        if not libres or cout[libres[0]] >= cout[choix[i_cher]]:
            messages.append("Impossible de tenir le budget avec les recettes disponibles : "
                            "voici le menu le moins cher trouvé.")
            break
        choix[i_cher] = libres[0]
    return [nouveau_plat(r) for r in choix], messages


def remplacer(plats: list[dict], index: int, recettes: dict, prefs: dict, catalogue: dict,
              graine: int | None = None) -> bool:
    """Remplace le plat `index` par une autre recette compatible. Renvoie False si impossible."""
    deja = {p["recette_id"] for p in plats}
    possibles = [r for r in candidats(recettes, prefs, catalogue) if r not in deja]
    if not possibles:
        return False
    plats[index] = nouveau_plat(random.Random(graine).choice(possibles))
    return True
