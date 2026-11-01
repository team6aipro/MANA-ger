"""Tous les calculs de prix et de budget. C'est le CODE qui calcule, jamais l'IA.

Unités :
- dans les recettes, chaque ingrédient a une unité : "g", "ml" ou "piece" ;
- en magasin, il est vendu soit « au poids » (prix au kg), soit « en paquet »
  (prix d'un paquet de `contenu` unités ; on achète des paquets entiers).
"""
import math
from collections import defaultdict


def besoins_semaine(plats: list[dict], recettes: dict, nb_personnes: int) -> dict[str, float]:
    """Additionne les quantités de tous les plats du menu.

    plats : [{"recette_id": str|None, "cuisine": bool}, ...]
    Renvoie {id_ingredient: quantité totale dans l'unité du catalogue}.
    """
    total = defaultdict(float)
    for plat in plats:
        recette = recettes.get(plat.get("recette_id"))
        if recette is None:  # plat retiré
            continue
        for ing in recette["ingredients"]:
            total[ing["id"]] += ing["quantite"] * nb_personnes
    return dict(total)


def en_grammes(ingredient: dict, quantite: float) -> float:
    """Convertit une quantité en grammes, pour les produits vendus au poids."""
    if ingredient["unite"] == "piece":
        return quantite * ingredient["poids_piece_g"]
    return quantite  # g (ou ml, ~1 g/ml)


def ligne_achat(ingredient: dict, quantite: float, prix_unitaire: float | None) -> dict:
    """Ce qu'il faut acheter pour une quantité donnée, et combien ça coûte."""
    vente = ingredient["vente"]
    if vente["type"] == "poids":
        kg = en_grammes(ingredient, quantite) / 1000
        a_acheter = f"{kg:.2f} kg".replace(".", ",") if kg >= 1 else f"{max(round(kg * 1000), 1)} g"
        cout = None if prix_unitaire is None else kg * prix_unitaire
    else:
        nb = math.ceil(round(quantite / vente["contenu"], 6))  # paquets entiers
        a_acheter = f"{nb} × {vente['libelle']}"
        cout = None if prix_unitaire is None else nb * prix_unitaire
    return {
        "id": ingredient["id"],
        "nom": ingredient["nom_fr"],
        "nom_he": ingredient["nom_he"],
        "quantite": quantite,
        "unite": ingredient["unite"],
        "a_acheter": a_acheter,
        "cout": None if cout is None else round(cout, 2),
    }


def panier(besoins: dict[str, float], catalogue: dict, prix_chaine: dict) -> dict:
    """Prix du panier dans une chaîne.

    Renvoie {"total": float, "lignes": [...], "manquants": [ids sans prix]}.
    """
    lignes, manquants, total = [], [], 0.0
    for id_, quantite in sorted(besoins.items(), key=lambda kv: catalogue[kv[0]]["nom_fr"]):
        ligne = ligne_achat(catalogue[id_], quantite, prix_chaine.get(id_))
        if ligne["cout"] is None:
            manquants.append(id_)
        else:
            total += ligne["cout"]
        lignes.append(ligne)
    return {"total": round(total, 2), "lignes": lignes, "manquants": manquants}


def comparer_chaines(besoins: dict, catalogue: dict, prix_par_chaine: dict) -> dict:
    """Compare le même panier dans toutes les chaînes.

    Seules les chaînes qui ont un prix pour TOUS les ingrédients sont classées
    (sinon la comparaison serait injuste).
    """
    paniers = {ch: panier(besoins, catalogue, p) for ch, p in prix_par_chaine.items()}
    complets = {ch: pa["total"] for ch, pa in paniers.items() if not pa["manquants"]}
    if not complets or not besoins:
        return {"paniers": paniers, "moins_chere": None, "plus_chere": None, "economie": 0.0}
    moins = min(complets, key=complets.get)
    plus = max(complets, key=complets.get)
    return {
        "paniers": paniers,
        "moins_chere": moins,
        "plus_chere": plus,
        "economie": round(complets[plus] - complets[moins], 2),
    }


def cout_part_recette(recette: dict, catalogue: dict, prix_chaine: dict, nb_personnes: int) -> float | None:
    """Coût « consommé » d'un plat (au prorata, sans arrondir aux paquets).

    Sert à classer les plats du moins cher au plus cher. None si un prix manque.
    """
    total = 0.0
    for ing in recette["ingredients"]:
        fiche = catalogue[ing["id"]]
        p = prix_chaine.get(ing["id"])
        if p is None:
            return None
        q = ing["quantite"] * nb_personnes
        if fiche["vente"]["type"] == "poids":
            total += en_grammes(fiche, q) / 1000 * p
        else:
            total += q / fiche["vente"]["contenu"] * p
    return round(total, 2)


def etat_budget(cout: float, budget: float) -> dict:
    """Compare un coût au budget."""
    reste = round(budget - cout, 2)
    return {"cout": cout, "budget": budget, "reste": reste, "depasse": reste < 0,
            "ratio": 0.0 if budget <= 0 else min(cout / budget, 1.0)}
