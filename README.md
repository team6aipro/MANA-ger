# 🥙 Panier de la semaine

Planificateur de 7 dîners pour étudiants à Jérusalem, avec comparateur de prix
Shufersal / Rami Levy / Osher Ad.

> ⚠️ **Les prix actuels sont FICTIFS** (inventés pour tester). Ils sont marqués comme tels
> dans le code (`data/prix_fictifs.json`) et affichés en bandeau jaune dans l'app.

## Organisation du code

| Dossier / fichier | Rôle |
|---|---|
| `app.py` | Point d'entrée : connexion + menu de navigation |
| `vues/` | Les pages : accueil, préférences, menu, comparateur, liste de courses |
| `core/calculs.py` | **Tous les calculs de prix et de budget** (jamais l'IA) |
| `core/regles.py` | Cacherout, végétarien, sans gluten, validation des recettes |
| `core/menu.py` | Choix des 7 dîners en respectant le budget, remplacement d'un plat |
| `core/ia.py` | Appel à Claude Haiku + validation du JSON + nouvel essai si erreur |
| `core/db.py` | Base SQLite (`panier.db`) : utilisateurs, préférences, menus, recettes IA |
| `core/auth.py` | Connexion Auth0 via `st.login()`, ou mode démo local |
| `core/style.py` | Identité visuelle : couleurs, cartes de plats, illustrations |
| `data/` | Catalogue de 30 ingrédients, 16 recettes de base, prix fictifs |
| `data/photos/` | Vos propres photos de plats (voir `LISEZMOI.md` dedans) |
| `scripts/tester_sources_prix.py` | Test des vraies sources de prix (étape 6) |
| `scripts/chercher_produit.py` | Recherche d'un produit dans les prix téléchargés |
| `scripts/telecharger_photos.py` | Vraies photos libres de droits (Wikimedia Commons) + crédits |
| `scripts/maj_magasins.py` | Récupère tous les magasins de Jérusalem (adresses officielles) |
| `core/fiche.py` | Fiche recette (temps, ingrédients, étapes) |
| `core/magasins.py` | Magasins et liens Google Maps |
| `tests/` | Tests automatiques (`pytest`) |

## Étape 1 — Installer et lancer (mode démo)

```bash
python -m venv .venv
source .venv/bin/activate        # Windows : .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Ouvrez http://localhost:8501, entrez n'importe quel e-mail : c'est le **mode démo local**
(pas de mot de passe ; à ne jamais mettre en ligne).

**Pour tester :** Préférences → Enregistrer → Menu → « Proposer mon menu ».
Cliquez « Retirer » sur un plat : le coût doit baisser immédiatement.

## Étape 2 — Lancer les tests automatiques

```bash
python -m pytest -q
```

Résultat attendu : `23 passed`. Ces tests vérifient les calculs (paquets arrondis,
vente au kg, budget, comparaison), la base de données, et que **toute recette de l'IA
avec un ingrédient inconnu, une quantité invalide ou un mélange viande/lait est rejetée**
(avec un faux client IA : aucun appel payant).

## Étape 3 — Secrets (avant tout `git push` !)

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

Remplissez `.streamlit/secrets.toml`. Ce fichier est dans `.gitignore`. Vérifiez :

```bash
git check-ignore -v .streamlit/secrets.toml
```

Si la commande affiche une ligne, c'est bon : le fichier ne partira pas sur GitHub.

## Étape 4 — Connexion Auth0 (e-mail + Google)

1. Créez un compte gratuit sur auth0.com, puis une *Application* de type « Regular Web Application ».
2. *Allowed Callback URLs* : `http://localhost:8501/oauth2callback`
3. Dans *Authentication → Social*, activez Google ; dans *Database*, la connexion par e-mail.
4. Copiez *Domain*, *Client ID*, *Client Secret* dans la section `[auth]` de `secrets.toml`.
5. Relancez `streamlit run app.py` : le bouton « Se connecter » apparaît.

**Pour tester :** créez un compte, faites un menu, déconnectez-vous, reconnectez-vous :
le menu doit être toujours là.

## Étape 5 — Recettes par l'IA

Ajoutez `ANTHROPIC_API_KEY` dans `secrets.toml` (clé sur console.anthropic.com).
Page Menu → « Créer de nouvelles recettes avec l'IA ». Le journal affiche, pour chaque
essai, les recettes acceptées et rejetées (avec la raison). Modèle utilisé :
`claude-haiku-5-5`, le moins cher.

## Étape 6 — (à venir) Vrais prix

Sur **votre** ordinateur (les sites peuvent bloquer les connexions hors d'Israël) :

```bash
pip install israeli-prices==0.2.0
python scripts/tester_sources_prix.py
```

Envoyez le résultat : on décidera ensemble comment brancher les vrais prix
(choix des codes-barres dans le catalogue, cache une fois par jour, promotions « club » ignorées).
