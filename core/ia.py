"""Création de recettes par l'IA (Claude Haiku).

Règles :
- l'IA ne reçoit QUE la liste des ingrédients du catalogue (ids) ;
- elle ne calcule aucun prix ;
- le code valide chaque recette (JSON, ingrédients connus, quantités,
  préférences) et redemande à l'IA en cas d'erreur (3 essais maximum).
"""
import json
import re
import unicodedata

from . import regles

MODELE = "claude-haiku-5-5"   # le modèle le moins cher de la gamme actuelle
ESSAIS_MAX = 3

SYSTEME = """Tu crées des recettes de dîner simples et économiques pour des étudiants à Jérusalem.
Règles strictes :
- Utilise UNIQUEMENT les ids d'ingrédients de la liste fournie. Aucun autre ingrédient (pas même sel, eau ou poivre).
- Les quantités sont PAR PERSONNE, dans l'unité indiquée (g, ml ou piece), nombres positifs.
- Donne un temps de préparation et un temps de cuisson réalistes, en minutes entières.
- Écris 4 à 6 étapes claires et précises (durées, température du four, signes de cuisson).
- Ne mélange jamais un ingrédient "bassari" avec un ingrédient "halavi".
- N'indique aucun prix ni aucune donnée nutritionnelle.
- Réponds UNIQUEMENT avec du JSON valide, sans texte autour, au format :
{"recettes": [{"nom": "...", "description": "une phrase", "preparation": 10, "cuisson": 20, "astuce": "un conseil", "ingredients": [{"id": "...", "quantite": 100}], "etapes": ["...", "..."]}]}"""


class ErreurIA(Exception):
    pass


def _liste_catalogue(catalogue: dict) -> str:
    return "\n".join(f'- {i["id"]} ({i["nom_fr"]}, unité: {i["unite"]}, {i["cacherout"]})'
                     for i in catalogue.values())


def _demande(nb: int, prefs: dict, catalogue: dict) -> str:
    contraintes = [f"types de cacherout autorisés : {', '.join(prefs['cacherout'])}"]
    if prefs["vegetarien"]:
        contraintes.append("végétarien (pas de viande ni de poisson)")
    if prefs["sans_gluten"]:
        contraintes.append("sans gluten (pas de pâtes, boulgour, pita)")
    if prefs["a_eviter"]:
        contraintes.append(f"ingrédients interdits : {', '.join(prefs['a_eviter'])}")
    return (f"Crée {nb} recettes différentes.\nContraintes : {'; '.join(contraintes)}.\n\n"
            f"Ingrédients disponibles :\n{_liste_catalogue(catalogue)}")


def extraire_json(texte: str):
    """Récupère le JSON de la réponse (enlève d'éventuels ```json ... ```)."""
    texte = texte.strip()
    m = re.search(r"```(?:json)?\s*(.*?)```", texte, re.S)
    if m:
        texte = m.group(1)
    return json.loads(texte)


def identifiant(nom: str) -> str:
    s = unicodedata.normalize("NFKD", nom.replace("œ", "oe").replace("Œ", "Oe")).encode("ascii", "ignore").decode().lower()
    return "ia_" + (re.sub(r"[^a-z0-9]+", "_", s).strip("_") or "recette")


def valider_reponse(texte: str, prefs: dict, catalogue: dict) -> tuple[list[dict], list[str]]:
    """Valide la réponse brute de l'IA. Renvoie (recettes_valides, erreurs)."""
    try:
        donnees = extraire_json(texte)
    except (json.JSONDecodeError, TypeError) as e:
        return [], [f"réponse qui n'est pas du JSON valide ({e})"]
    if not isinstance(donnees, dict) or not isinstance(donnees.get("recettes"), list):
        return [], ["le JSON doit contenir une clé 'recettes' (liste)"]
    valides, erreurs = [], []
    for n, rec in enumerate(donnees["recettes"], 1):
        errs = regles.erreurs_recette(rec, catalogue)
        if not errs and not regles.compatible(rec, prefs, catalogue):
            errs = ["ne respecte pas les préférences (cacherout, végétarien, gluten ou ingrédient à éviter)"]
        if errs:
            erreurs.append(f"recette {n} ({rec.get('nom', '?') if isinstance(rec, dict) else '?'}) : " + "; ".join(errs))
            continue
        valides.append({
            "id": identifiant(rec["nom"]),
            "nom": rec["nom"].strip(),
            "description": str(rec.get("description", "")).strip(),
            "ingredients": [{"id": i["id"], "quantite": float(i["quantite"])} for i in rec["ingredients"]],
            "etapes": [e.strip() for e in rec["etapes"]],
            "preparation": rec["preparation"],
            "cuisson": rec["cuisson"],
            "minutes": rec["preparation"] + rec["cuisson"],
            "astuce": str(rec.get("astuce", "")).strip(),
            "source": "ia",
            # Illustration choisie par le code : l'emoji du 1er ingrédient.
            "emoji": catalogue[rec["ingredients"][0]["id"]].get("emoji", "🍽️"),
        })
    return valides, erreurs


def creer_recettes(client, nb: int, prefs: dict, catalogue: dict) -> tuple[list[dict], list[str]]:
    """Demande `nb` recettes à Claude, valide, et redemande si besoin.

    `client` est un anthropic.Anthropic() (ou un faux client dans les tests).
    Renvoie (recettes_valides, journal) où journal décrit chaque essai.
    """
    messages = [{"role": "user", "content": _demande(nb, prefs, catalogue)}]
    obtenues, journal = [], []
    for essai in range(1, ESSAIS_MAX + 1):
        reponse = client.messages.create(
            model=MODELE, max_tokens=4000, system=SYSTEME, messages=messages,
            output_config={"effort": "low"},
        )
        if reponse.stop_reason == "refusal":
            raise ErreurIA("L'IA a refusé la demande.")
        texte = "".join(b.text for b in reponse.content if b.type == "text")
        valides, erreurs = valider_reponse(texte, prefs, catalogue)
        noms = {r["id"] for r in obtenues}
        obtenues += [r for r in valides if r["id"] not in noms]
        journal.append(f"Essai {essai} : {len(valides)} recette(s) acceptée(s), {len(erreurs)} rejetée(s).")
        journal += [f"  ✗ {e}" for e in erreurs]
        manque = nb - len(obtenues)
        if manque <= 0:
            break
        # On renvoie la conversation complète + les erreurs, et on redemande.
        messages += [
            {"role": "assistant", "content": reponse.content},
            {"role": "user", "content": "Certaines recettes ont été rejetées par la validation :\n"
                + "\n".join(erreurs or ["(aucune erreur, mais il en manque)"])
                + f"\nPropose {manque} nouvelle(s) recette(s) corrigée(s), même format JSON, "
                  "uniquement avec les ids de la liste."},
        ]
    return obtenues[:nb], journal
