# Casa — fiche recette lisible (livraison 1) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Afficher la recette d'un plat en fiche « Magazine » (style C) lisible sur iPhone, à partir du texte existant, sans changer la base.

**Architecture:** Un module Python pur `voyage/fiche_recette.py` découpe `plats.recette` en structure (`decouper`). `/api/diners` ajoute `fiche` à chaque plat. `ouvrirFiche` (JS dans `voyage/diners.py`) affiche la structure ; si `fiche.structuree` est faux, il garde le `pre.recette` actuel.

**Tech Stack:** Python 3.14, Flask, Postgres (Neon / `valise_test` en local), pytest ; JS vanilla dans une chaîne Python (`diners.py`).

**Spec :** `docs/superpowers/specs/2026-11-06-casa-fiche-recette-design.md`

## Global Constraints

- Tests : `cd voyage && .venv/bin/python3 -m pytest -q` ; base de test `valise_test` (TRUNCATE par les tests).
- Le JS de `diners.py` vit dans une chaîne Python non brute : une apostrophe JS s'écrit `\\'` ; **aucune regex JS** (tout le découpage est en Python).
- Rendu : uniquement `el()` / `textContent` / `append` — **jamais `innerHTML`** avec du contenu de recette.
- `VERSION_PAGE` (valise.py:1649) : 45 → 46.
- Aucune migration, aucune écriture en base.
- Démo locale sur copie prod (Mac + iPhone wifi) testée par Julien avant toute PR ; push/PR/merge seulement sur demande, `env -u GITHUB_TOKEN gh`.
- Commits terminés par `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

## Fichiers

- Create `voyage/fiche_recette.py` — `decouper(texte) -> dict` (pur).
- Create `voyage/exemples_fiches/*.txt` — 7 textes réels figés (carbonara, risotto, polpette, hot dog, nems, croque-monsieur, amatriciana).
- Create `voyage/test_fiche_recette.py`.
- Modify `voyage/serveur.py:157` — champ `fiche` dans `/api/diners`.
- Modify `voyage/test_diners_db.py:55-59` — `fiche` présent.
- Modify `voyage/diners.py` — CSS (fin du bloc style, avant `"""` ligne ~456) + `ouvrirFiche` (lignes ~913-960).
- Modify `voyage/test_diners.py:133` — marqueurs de la fiche C dans la page.
- Modify `voyage/valise.py:1649` — `VERSION_PAGE = 46`.

---

### Task 1: Découpage des lignes (pour, ingrédients, sections, tempo, bloc final)

**Files:**
- Create: `voyage/exemples_fiches/` (7 fichiers .txt)
- Create: `voyage/fiche_recette.py`
- Test: `voyage/test_fiche_recette.py`

**Interfaces:**
- Produces: `decouper(texte: str) -> dict` avec les clés `structuree, pour, ingredients, sections, tempo, etapes, difference`. Dans cette tâche, chaque étape est `{"n": int, "texte": str, "si": [str]}` (texte brut) ; la Task 2 la transforme.

- [ ] **Step 1: Figer les textes réels**

```bash
cd ~/Claude/Work/perso/python/julien-python-journey/voyage
mkdir -p exemples_fiches
S=/private/tmp/claude-501/-Users-julien/463b0b76-3ae0-443d-8762-f92647f594a2/scratchpad
for id in plat-carbonara plat-risotto-milanese tester-polpette af-hot-dog tester-nems plat-croque-monsieur plat-amatriciana; do cp $S/$id.txt exemples_fiches/$id.txt; done
ls exemples_fiches | wc -l
```
Expected: `7`. (Si le scratchpad a disparu : `.venv/bin/python chef.py lire <id>` et copier le champ `recette`.)

- [ ] **Step 2: Write the failing tests**

`voyage/test_fiche_recette.py` :

```python
"""Tests de fiche_recette.py : découpage du texte d'une recette en fiche (logique pure)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from fiche_recette import decouper

EX = Path(__file__).parent / "exemples_fiches"


def lire(id_):
    return (EX / f"{id_}.txt").read_text(encoding="utf-8")


def test_carbonara_lignes():
    f = decouper(lire("plat-carbonara"))
    assert f["structuree"] is True
    assert f["pour"] == "Pour 2"
    assert f["ingredients"][0] == {"nom": "Spaghetti", "quantite": "320 g"}
    assert f["ingredients"][2] == {"nom": "Jaunes d’œufs", "quantite": "4 (env. 70 g de jaunes)"}
    assert len(f["ingredients"]) == 6
    assert f["sections"][0]["titre"] == "Variantes (acceptables)" and len(f["sections"][0]["lignes"]) == 2
    assert f["tempo"]["titre"].startswith("Tempo (≈ 27 min")
    assert f["tempo"]["lignes"][0]["heure"] == "0:00"
    assert f["tempo"]["lignes"][1]["etapes"] == [1, 2, 3]
    assert [e["n"] for e in f["etapes"]] == list(range(1, 10))
    assert len(f["etapes"][7]["si"]) == 2                     # étape 8 : les deux rattrapages
    assert len(f["difference"]) == 3 and f["difference"][0].startswith("Pâtes finies")


def test_risotto_etapes_en_parenthese_et_secret_libre():
    f = decouper(lire("plat-risotto-milanese"))
    assert len(f["etapes"]) == 10
    assert f["ingredients"][3] == {"nom": "Beurre", "quantite": "60 g (dont 30 g froid, en dés, pour la mantecatura)"}
    libre = [s for s in f["sections"] if s["titre"].startswith("Secret de mamma")]
    assert len(libre) == 1 and libre[0]["lignes"] == []


def test_polpette_sous_liste_et_tiret_long():
    f = decouper(lire("tester-polpette"))
    assert f["pour"] == "Pour 4 (deux repas à deux)"
    assert f["ingredients"][0] == {"nom": "Bœuf haché", "quantite": "350 g"}
    sauce = [s for s in f["sections"] if s["titre"] == "Sauce"][0]
    assert sauce["lignes"][0] == "Passata (coulis de tomate) — 700 g"
    assert f["tempo"]["titre"] == "Tempo (≈ 1 h 10)" and len(f["etapes"]) == 9


def test_hot_dog_sans_tempo():
    f = decouper(lire("af-hot-dog"))
    assert f["tempo"] is None and len(f["etapes"]) == 3
    assert f["ingredients"][0] == {"nom": "4 saucisses de Strasbourg, 4 pains à hot dog, moutarde, ketchup", "quantite": ""}


def test_ancien_format_erreurs_frequentes_et_variante_libre():
    f = decouper(lire("plat-croque-monsieur"))
    assert f["structuree"] is True and len(f["etapes"]) == 5
    titres = [s["titre"] for s in f["sections"]]
    assert "Erreurs fréquentes" in titres
    assert any(t.startswith("Variante madame") for t in titres)
    erreurs = [s for s in f["sections"] if s["titre"] == "Erreurs fréquentes"][0]
    assert len(erreurs["lignes"]) == 2
    assert all(e["si"] == [] for e in f["etapes"])            # les « - » des erreurs ne sont pas des sous-puces
    assert f["difference"] == []


def test_nems_ancien_format():
    f = decouper(lire("tester-nems"))
    assert f["pour"] == "Pour 20 nems" and len(f["etapes"]) == 5 and f["tempo"] is None


def test_textes_non_structures():
    for t in ("", "   ", "Recette à écrire.", "Un texte libre\nsans étape numérotée."):
        f = decouper(t)
        assert f["structuree"] is False and f["etapes"] == []
    assert decouper(None)["structuree"] is False
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `cd voyage && .venv/bin/python3 -m pytest test_fiche_recette.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'fiche_recette'`

- [ ] **Step 4: Write the implementation**

`voyage/fiche_recette.py` :

```python
"""Découpe le texte d'une recette (format chef-casa, ou plus ancien) en fiche structurée pour l'affichage.

Le texte reste la seule source en base : on le relit à chaque affichage, on ne stocke rien.
"""
import re

ETAPE = re.compile(r"^(\d+)[.)]\s+(.*)$")
SOUS_PUCE = re.compile(r"^\s+-\s+(.*)$")
LIGNE_TEMPO = re.compile(r"^-\s+(\d+:\d\d)\s+(.*)$")
RENVOI = re.compile(r"\((\d+)\)")
COUPE_INGREDIENT = re.compile(r"\s+(?::|—)\s+")


def _vide():
    return {"structuree": False, "pour": "", "ingredients": [], "sections": [], "tempo": None,
            "etapes": [], "difference": []}


def _ingredient(ligne):
    morceaux = COUPE_INGREDIENT.split(ligne, maxsplit=1)
    if len(morceaux) == 2:
        return {"nom": morceaux[0].strip(), "quantite": morceaux[1].strip()}
    return {"nom": ligne.strip(), "quantite": ""}


def _lire_lignes(texte):
    f = _vide()
    zone, etape, section = "ingredients", None, None
    for brute in texte.split("\n"):
        ligne = brute.rstrip()
        if not ligne.strip():
            continue
        if not f["pour"] and zone == "ingredients" and not f["ingredients"] and ligne.startswith("Pour "):
            f["pour"] = ligne.strip()
            continue
        if ligne.startswith("Tempo"):
            zone, f["tempo"] = "tempo", {"titre": ligne.strip(), "lignes": []}
            continue
        if ligne.startswith("Ce qui fait la différence"):
            zone = "difference"
            continue
        m = ETAPE.match(ligne)
        if m:
            zone, etape = "etapes", {"n": int(m.group(1)), "texte": m.group(2).strip(), "si": []}
            f["etapes"].append(etape)
            continue
        if zone == "etapes" and SOUS_PUCE.match(ligne):
            etape["si"].append(SOUS_PUCE.match(ligne).group(1).strip())
            continue
        if zone == "tempo":
            t = LIGNE_TEMPO.match(ligne)
            if t:
                f["tempo"]["lignes"].append({"heure": t.group(1), "texte": t.group(2).strip(),
                                             "etapes": [int(n) for n in RENVOI.findall(t.group(2))]})
                continue
        if zone == "difference" and ligne.startswith("- "):
            f["difference"].append(ligne[2:].strip())
            continue
        if ligne.startswith("- "):
            if section is not None and zone == "sections":
                section["lignes"].append(ligne[2:].strip())
            else:
                f["ingredients"].append(_ingredient(ligne[2:]))
            continue
        # toute autre ligne : un titre de section (ou un paragraphe libre)
        titre = ligne.strip()
        titre = titre[:-1].rstrip() if titre.endswith(":") else titre
        section = {"titre": titre, "lignes": []}
        f["sections"].append(section)
        zone = "sections"
    f["structuree"] = bool(f["etapes"])
    return f


def decouper(texte):
    """Texte brut d'une recette -> fiche (dict). Ne lève jamais : en cas de souci, fiche non structurée."""
    if not texte or not str(texte).strip():
        return _vide()
    try:
        return _lire_lignes(str(texte))
    except Exception:                                    # le texte vient aussi de « Modifier » : tout peut arriver
        return _vide()
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd voyage && .venv/bin/python3 -m pytest test_fiche_recette.py -q`
Expected: `7 passed`. Si `test_carbonara_lignes` échoue sur les apostrophes : le fichier utilise `’` (typographique) — garder l'apostrophe du fichier dans l'assertion.

- [ ] **Step 6: Commit**

```bash
cd ~/Claude/Work/perso/python/julien-python-journey
git add voyage/fiche_recette.py voyage/test_fiche_recette.py voyage/exemples_fiches
git commit -m "feat(casa): fiche recette — découpage des lignes (pour, ingrédients, sections, tempo, bloc final)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 2: Découpage des étapes (action, pourquoi, secrets, rattrapages)

**Files:**
- Modify: `voyage/fiche_recette.py`
- Test: `voyage/test_fiche_recette.py`

**Interfaces:**
- Consumes: `_lire_lignes` (Task 1), étapes `{"n", "texte", "si": [str]}`.
- Produces: chaque étape devient `{"n": int, "action": str, "morceaux": [{"genre": "texte"|"pourquoi", "texte": str}], "secrets": [{"qui": "grand-mere"|"mamma", "texte": str}], "si": [<même forme sans "n">]}`. Fonction publique `decouper_phrase(texte: str) -> dict` (clés `action, morceaux, secrets`).

- [ ] **Step 1: Write the failing tests** (ajouter à `voyage/test_fiche_recette.py`)

```python
from fiche_recette import decouper_phrase


def test_action_coupee_au_premier_point_de_phrase():
    d = decouper_phrase("Râpe le pecorino le plus fin possible — en gros copeaux, il fait des grumeaux au lieu de fondre.")
    assert d["action"] == "Râpe le pecorino le plus fin possible"
    assert d["morceaux"] == [{"genre": "pourquoi", "texte": "— en gros copeaux, il fait des grumeaux au lieu de fondre."}]


def test_abreviations_ne_coupent_pas():
    d = decouper_phrase("Ajoute l’eau 1 c. à s. à la fois. Puis mélange.")
    assert d["action"] == "Ajoute l’eau 1 c. à s. à la fois."
    assert d["morceaux"] == [{"genre": "texte", "texte": " Puis mélange."}]


def test_action_avec_deux_points():
    d = decouper_phrase("Bouillon : mets-le dans une casserole à côté.")
    assert d["action"] == "Bouillon :"
    assert d["morceaux"][0] == {"genre": "texte", "texte": " mets-le dans une casserole à côté."}


def test_secrets_retires_du_texte():
    d = decouper_phrase("Puis les oignons (secret de grand-mère : une bonne pincée d’oignons crispy dessus) en tout dernier.")
    assert d["secrets"] == [{"qui": "grand-mere", "texte": "une bonne pincée d’oignons crispy dessus"}]
    assert "secret" not in d["action"] + "".join(m["texte"] for m in d["morceaux"])
    assert "oignons en tout dernier" in d["action"] + "".join(m["texte"] for m in d["morceaux"])


def test_secret_de_mamma_avec_guillemets():
    d = decouper_phrase("Mélange (secret de mamma : remue fort, la sauce doit « enrober » la pasta).")
    assert d["secrets"] == [{"qui": "mamma", "texte": "remue fort, la sauce doit « enrober » la pasta"}]


def test_pourquoi_au_milieu():
    d = decouper_phrase("Pose les boulettes, espacées de 2 cm — serrées, elles bouillent au lieu de dorer. N’y touche pas.")
    genres = [m["genre"] for m in d["morceaux"]]
    assert genres == ["pourquoi", "texte"]
    assert d["morceaux"][0]["texte"] == "— serrées, elles bouillent au lieu de dorer."


def test_phrase_sans_coupure():
    assert decouper_phrase("Four à 220 °C, grill.") == {"action": "Four à 220 °C, grill.", "morceaux": [], "secrets": []}


def test_carbonara_etapes_decoupees():
    f = decouper(lire("plat-carbonara"))
    e7 = f["etapes"][6]
    assert e7["n"] == 7 and e7["action"].startswith("Au minuteur")
    assert e7["secrets"][0]["qui"] == "grand-mere"
    e8 = f["etapes"][7]
    assert e8["action"] == "Mantecatura."
    assert e8["si"][0]["action"].startswith("Encore liquide après 1 min")
    assert "texte" not in e8
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd voyage && .venv/bin/python3 -m pytest test_fiche_recette.py -q`
Expected: FAIL — `ImportError: cannot import name 'decouper_phrase'`

- [ ] **Step 3: Write the implementation** (ajouter dans `voyage/fiche_recette.py`, et brancher dans `decouper`)

Ajouter après les constantes :

```python
SECRET = re.compile(r"\s*\(secret de (grand-mère|mamma)\s*:\s*((?:[^()]|\([^()]*\))*)\)", re.IGNORECASE)
FIN_DE_PHRASE = re.compile(r"\.\s(?=[A-ZÀ-ÖØ-Ý«])")       # « c. à s. » n'est pas une fin de phrase
POURQUOI = re.compile(r"\s—\s")


def _coupe_action(texte):
    """Indice de fin de l'action : 1er point de phrase (inclus), « : » (inclus) ou « — » (exclu)."""
    candidats = []
    m = FIN_DE_PHRASE.search(texte)
    if m:
        candidats.append(m.start() + 1)
    i = texte.find(" : ")
    if i > 0:
        candidats.append(i + 2)
    m = POURQUOI.search(texte)
    if m:
        candidats.append(m.start())
    return min(candidats) if candidats else len(texte)


def _morceaux(reste):
    """Le reste de l'étape en morceaux texte / pourquoi (« — … » jusqu'à la fin de phrase ou « ; »)."""
    morceaux, i = [], 0
    while i < len(reste):
        m = POURQUOI.search(reste, i)
        if not m:
            morceaux.append({"genre": "texte", "texte": reste[i:]})
            break
        if m.start() > i:
            morceaux.append({"genre": "texte", "texte": reste[i:m.start()]})
        debut = m.start() + 1                             # garde le « — » dans le pourquoi
        fin_phrase = FIN_DE_PHRASE.search(reste, debut)
        point_virgule = reste.find(";", debut)
        fins = [x for x in (fin_phrase.start() + 1 if fin_phrase else -1, point_virgule) if x != -1]
        fin = min(fins) if fins else len(reste)
        morceaux.append({"genre": "pourquoi", "texte": reste[debut:fin]})
        i = fin
    return [m for m in morceaux if m["texte"].strip()]


def decouper_phrase(texte):
    """Une étape (ou une sous-puce) -> action en gras, morceaux texte/pourquoi, secrets en encadré."""
    secrets = [{"qui": "mamma" if s.group(1).lower() == "mamma" else "grand-mere", "texte": s.group(2).strip()}
               for s in SECRET.finditer(texte)]
    propre = SECRET.sub("", texte).strip()
    coupe = _coupe_action(propre)
    return {"action": propre[:coupe].rstrip(), "morceaux": _morceaux(propre[coupe:]), "secrets": secrets}
```

Remplacer `decouper` par :

```python
def decouper(texte):
    """Texte brut d'une recette -> fiche (dict). Ne lève jamais : en cas de souci, fiche non structurée."""
    if not texte or not str(texte).strip():
        return _vide()
    try:
        f = _lire_lignes(str(texte))
        f["etapes"] = [{"n": e["n"], **decouper_phrase(e["texte"]), "si": [decouper_phrase(s) for s in e["si"]]}
                       for e in f["etapes"]]
        return f
    except Exception:                                    # le texte vient aussi de « Modifier » : tout peut arriver
        return _vide()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd voyage && .venv/bin/python3 -m pytest test_fiche_recette.py -q`
Expected: `15 passed`.

Note pour `test_action_avec_deux_points` : `_coupe_action` renvoie `i + 2` → l'action est `"Bouillon :"` et le reste commence par l'espace — c'est voulu (l'affichage colle les morceaux tels quels).

- [ ] **Step 5: Vérifier sur toutes les recettes réelles que rien ne lève et que le texte est conservé**

```bash
cd voyage && .venv/bin/python3 - <<'EOF'
from pathlib import Path
from fiche_recette import decouper
for p in sorted(Path("exemples_fiches").glob("*.txt")):
    f = decouper(p.read_text(encoding="utf-8"))
    for e in f["etapes"]:
        rendu = e["action"] + "".join(m["texte"] for m in e["morceaux"])
        assert "(secret de" not in rendu.lower(), (p.name, e["n"])
    print(p.name, f["structuree"], len(f["etapes"]))
EOF
```
Expected : 7 lignes, toutes `True`.

- [ ] **Step 6: Commit**

```bash
cd ~/Claude/Work/perso/python/julien-python-journey
git add voyage/fiche_recette.py voyage/test_fiche_recette.py
git commit -m "feat(casa): fiche recette — étapes en action, pourquoi, secrets, rattrapages

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 3: `/api/diners` envoie la fiche

**Files:**
- Modify: `voyage/serveur.py` (import + ligne `"plats": [...]` dans `lire_les_diners`, ~l.157)
- Test: `voyage/test_diners_db.py:55-59`

**Interfaces:**
- Consumes: `decouper(texte) -> dict` (Tasks 1-2).
- Produces: chaque plat de `/api/diners` a une clé `fiche` (dict de `decouper`).

- [ ] **Step 1: Write the failing test** — dans `test_api_diners` (`voyage/test_diners_db.py`), ajouter à la fin :

```python
    carbo = next(p for p in d["plats"] if p["id"] == "plat-carbonara")
    assert carbo["fiche"]["structuree"] is True and carbo["fiche"]["etapes"]
    assert all("fiche" in p for p in d["plats"])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd voyage && .venv/bin/python3 -m pytest test_diners_db.py::test_api_diners -q`
Expected: FAIL — `KeyError: 'fiche'`

- [ ] **Step 3: Implement** — dans `voyage/serveur.py`, ajouter l'import en tête avec les autres imports locaux :

```python
from fiche_recette import decouper
```

et remplacer la ligne :

```python
            "plats": [{**p, "cout": cout_repas(p["ingredients"], p["recette"])} for p in plats],
```

par :

```python
            "plats": [{**p, "cout": cout_repas(p["ingredients"], p["recette"]), "fiche": decouper(p["recette"])}
                      for p in plats],
```

- [ ] **Step 4: Run tests**

Run: `cd voyage && .venv/bin/python3 -m pytest test_diners_db.py -q`
Expected: tous verts.

- [ ] **Step 5: Commit**

```bash
cd ~/Claude/Work/perso/python/julien-python-journey
git add voyage/serveur.py voyage/test_diners_db.py
git commit -m "feat(casa): /api/diners envoie la fiche découpée de chaque plat

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 4: La fiche C dans la page Dîners

**Files:**
- Modify: `voyage/diners.py` — CSS (ajout à la fin du bloc de style, juste avant le `"""` qui suit `form.edition .deux { … }`, ~l.455) ; `ouvrirFiche` (~l.913-960).
- Modify: `voyage/valise.py:1649` — `VERSION_PAGE = 46`.
- Test: `voyage/test_diners.py` — `test_page_diners`.

**Interfaces:**
- Consumes: `p.fiche` côté JS : `{structuree, pour, ingredients:[{nom, quantite}], sections:[{titre, lignes}], tempo:{titre, lignes:[{heure, texte, etapes}]}|null, etapes:[{n, action, morceaux:[{genre, texte}], secrets:[{qui, texte}], si:[…]}], difference:[…]}`.
- Produces: fonctions JS `uneFiche(p)`, `bandeauCourses(p)`, `ingredientsFiche(f)`, `tempoFiche(f)`, `etapesFiche(f)`, `phraseFiche(d)` dans la chaîne de `diners.py`.

- [ ] **Step 1: Write the failing test** — dans `test_page_diners` (`voyage/test_diners.py`), ajouter :

```python
    for marqueur in ("function uneFiche", "function bandeauCourses", "function ingredientsFiche",
                     "function tempoFiche", "function etapesFiche", "function phraseFiche",
                     "div.une-fiche", "details.courses-fiche", "ol.etapes-fiche", "div.tempo-fiche"):
        assert marqueur in html, marqueur
    assert "innerHTML" not in html.split("function uneFiche")[1].split("function ouvrirAccords")[0]
```

et dans `voyage/test_cabine.py` rien ; ajouter dans `voyage/test_fiche_recette.py` :

```python
def test_version_page_montee():
    from valise import VERSION_PAGE
    assert VERSION_PAGE >= 46
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd voyage && .venv/bin/python3 -m pytest test_diners.py::test_page_diners test_fiche_recette.py::test_version_page_montee -q`
Expected: FAIL — `AssertionError: function uneFiche` et `assert 45 >= 46`.

- [ ] **Step 3: CSS** — dans `voyage/diners.py`, juste avant le `"""` qui ferme le bloc de style (après `form.edition .deux { … }`), ajouter :

```css
/* Fiche recette « magazine » (06/11/2026) */
div.une-fiche { background: var(--diners); color: #fff; border-radius: 28px; padding: 20px 18px; }
div.une-fiche .meta { color: rgba(255,255,255,.85); }
div.une-fiche h2 { font-size: 36px; color: #fff; margin: 4px 0 0; }
div.une-fiche .haut button { background: rgba(255,255,255,.2); color: #fff; }
div.une-fiche ul { list-style: none; margin: 14px 0 0; padding: 12px 0 0; border-top: 1px solid rgba(255,255,255,.35); }
div.une-fiche li { font-size: 16px; line-height: 1.45; margin: 6px 0; }
details.courses-fiche { background: var(--carte); border-radius: 18px; padding: 12px 16px; }
details.courses-fiche summary { font-weight: 800; cursor: pointer; }
details.courses-fiche[open] summary { margin-bottom: 10px; }
h3.titre-fiche { font-size: 13px; font-weight: 800; color: var(--doux); text-transform: uppercase; letter-spacing: .08em; margin: 18px 0 8px; }
ul.ing-fiche { list-style: none; padding: 0; margin: 0; columns: 2; column-gap: 18px; }
ul.ing-fiche li { break-inside: avoid; padding: 7px 0; border-bottom: 1px dashed var(--ligne); font-size: 15px; line-height: 1.35;
                  display: flex; gap: 8px; align-items: flex-start; }
ul.ing-fiche input { width: 20px; height: 20px; margin: 1px 0 0; accent-color: var(--courses); flex: none; }
ul.ing-fiche b { display: block; font-size: 16px; }
ul.ing-fiche li.coche { color: var(--doux); text-decoration: line-through; }
p.para-fiche { font-size: 16px; line-height: 1.5; margin: 6px 0; }
div.tempo-fiche { display: flex; gap: 8px; overflow-x: auto; padding-bottom: 6px; scroll-snap-type: x mandatory; }
div.tempo-fiche button { flex: none; width: 72%; max-width: 260px; text-align: left; border: none; background: var(--carte);
                         color: var(--texte); border-radius: 18px; padding: 12px 14px; scroll-snap-align: start;
                         font-family: inherit; font-size: 15px; line-height: 1.4; }
div.tempo-fiche b { display: block; font-family: 'DM Mono', ui-monospace, monospace; font-size: 22px; color: var(--diners); }
ol.etapes-fiche { list-style: none; padding: 0; margin: 0; }
ol.etapes-fiche > li { position: relative; padding: 16px 0 16px 54px; border-top: 1px solid var(--ligne); font-size: 17.5px;
                       line-height: 1.55; scroll-margin-top: 16px; transition: background .4s; border-radius: 12px; }
ol.etapes-fiche > li.vise { background: var(--diners-doux); }
ol.etapes-fiche span.num { position: absolute; left: 0; top: 10px; font-size: 42px; font-weight: 800; color: var(--diners);
                           line-height: 1; letter-spacing: -0.04em; }
ol.etapes-fiche strong { font-weight: 800; }
ol.etapes-fiche em { color: var(--doux); }
ol.etapes-fiche div.secret { margin-top: 10px; padding-left: 12px; border-left: 4px solid var(--or, #b7791f); font-size: 16px; }
ol.etapes-fiche div.secret b { color: var(--or, #b7791f); }
ol.etapes-fiche div.secret.mamma { border-color: var(--courses); }
ol.etapes-fiche div.secret.mamma b { color: var(--courses); }
ol.etapes-fiche ul { padding-left: 18px; margin: 8px 0 0; }
ol.etapes-fiche ul li { font-size: 16px; margin-top: 6px; }
```

- [ ] **Step 4: JS** — dans `voyage/diners.py`, juste avant `function ouvrirFiche(id) {`, ajouter :

```javascript
    // --- Fiche « magazine » : affiche p.fiche (découpée en Python, fiche_recette.py) ---
    function phraseFiche(d, parent) {
        if (d.action) parent.append(el('strong', '', d.action));
        d.morceaux.forEach(function (m) { parent.append(m.genre === 'pourquoi' ? el('em', '', ' ' + m.texte) : document.createTextNode(m.texte)); });
        d.secrets.forEach(function (s) {
            const b = el('div', 'secret' + (s.qui === 'mamma' ? ' mamma' : ''));
            b.append(el('b', '', s.qui === 'mamma' ? 'Secret de mamma' : 'Secret de grand-mère'), document.createTextNode(' · ' + s.texte));
            parent.append(b);
        });
    }
    function uneFiche(p) {
        const f = p.fiche, une = el('div', 'une-fiche'), haut = el('div', 'haut');
        haut.append(el('span', 'meta', NOMS_GENRE[p.genre] + ' · ' + duree(p.minutes) + (f.pour ? ' · ' + f.pour : '')), bouton('Fermer', 'petit', fermer));
        une.append(haut, el('h2', '', p.nom));
        if (f.difference.length) {
            const ul = el('ul');
            f.difference.forEach(function (x) { ul.append(el('li', '', '« ' + x + ' »')); });
            une.append(ul);
        }
        return une;
    }
    function bandeauCourses(p, groupes) {
        const manque = groupes[2][2], det = el('details', 'courses-fiche');
        const total = manque.reduce(function (t, i) { const pr = prixDe(i); return t + (pr ? pr[1] : 0); }, 0);
        det.append(el('summary', '', manque.length ? manque.length + ' à acheter' + (total ? ' · ≈ ' + euros(total) : '') : 'Tout est au placard'));
        groupes.forEach(function (g) {
            if (!g[2].length) return;
            const sec = el('section', 'groupe-ing'), ing = el('div', 'ingredients');
            g[2].forEach(function (i) {
                const t = el('span', g[0], i), pr = prixDe(i);
                if (g[0] === 'manque' && pr) t.append(el('small', '', euros(pr[1])));
                ing.append(t);
            });
            sec.append(el('h3', '', g[1] + ' · ' + g[2].length), ing);
            det.append(sec);
        });
        if (p.cout) det.append(el('p', 'meta', '≈ ' + euros(p.cout) + ' le repas pour deux · en livraison ≈ ' + euros(d.livraison)));
        return det;
    }
    function ingredientsFiche(f) {
        const frag = document.createDocumentFragment();
        function liste(lignes) {
            const ul = el('ul', 'ing-fiche');
            lignes.forEach(function (x) {
                const li = el('li'), c = el('input'), t = el('span');
                c.type = 'checkbox';
                c.addEventListener('change', function () { li.classList.toggle('coche', c.checked); });
                if (x.quantite) t.append(el('b', '', x.nom), document.createTextNode(x.quantite)); else t.append(el('b', '', x.nom));
                li.append(c, t); ul.append(li);
            });
            return ul;
        }
        if (f.ingredients.length) frag.append(el('h3', 'titre-fiche', 'Ingrédients'), liste(f.ingredients));
        f.sections.forEach(function (s) {
            if (!s.lignes.length) { frag.append(el('p', 'para-fiche', s.titre)); return; }
            frag.append(el('h3', 'titre-fiche', s.titre),
                        liste(s.lignes.map(function (l) { return { nom: l, quantite: '' }; })));
        });
        return frag;
    }
    function tempoFiche(f) {
        const frag = document.createDocumentFragment();
        if (!f.tempo || !f.tempo.lignes.length) return frag;
        const bande = el('div', 'tempo-fiche');
        f.tempo.lignes.forEach(function (l) {
            const b = el('button');
            b.type = 'button';
            b.append(el('b', '', l.heure), document.createTextNode(l.texte));
            if (l.etapes.length) b.addEventListener('click', function () {
                const cible = document.getElementById('etape-' + l.etapes[0]);
                if (!cible) return;
                cible.scrollIntoView({ behavior: 'smooth', block: 'start' });
                cible.classList.add('vise');
                setTimeout(function () { cible.classList.remove('vise'); }, 2000);
            });
            bande.append(b);
        });
        frag.append(el('h3', 'titre-fiche', f.tempo.titre), bande);
        return frag;
    }
    function etapesFiche(f) {
        const ol = el('ol', 'etapes-fiche');
        f.etapes.forEach(function (e) {
            const li = el('li');
            li.id = 'etape-' + e.n;
            li.append(el('span', 'num', String(e.n)));
            phraseFiche(e, li);
            if (e.si.length) {
                const ul = el('ul');
                e.si.forEach(function (s) { const x = el('li'); phraseFiche(s, x); ul.append(x); });
                li.append(ul);
            }
            ol.append(li);
        });
        const frag = document.createDocumentFragment();
        frag.append(el('h3', 'titre-fiche', 'Étapes'), ol);
        return frag;
    }
```

- [ ] **Step 5: Brancher dans `ouvrirFiche`** — remplacer le début de `ouvrirFiche` jusqu'à la ligne `if (p.note) c.append(el('p', 'meta', p.note));` incluse par :

```javascript
    function ouvrirFiche(id) {
        const p = plat(id); if (!p) return;
        ouverte = { id: id, edition: false };
        const c = document.querySelector('#panneau .contenu'); c.replaceChildren();
        const groupes = [['ok', 'Au placard', p.ingredients.filter(enStock)],
                         ['liste', 'Déjà sur la liste', p.ingredients.filter(function (i) { return !enStock(i) && surLaListe(i); })],
                         ['manque', 'À acheter', p.ingredients.filter(function (i) { return !enStock(i) && !surLaListe(i); })]];
        if (p.fiche && p.fiche.structuree) {
            c.append(uneFiche(p), bandeauCourses(p, groupes), ingredientsFiche(p.fiche), tempoFiche(p.fiche), etapesFiche(p.fiche));
            if (p.lien) { const m = el('p', 'meta'); const a = el('a', '', 'Recette d\\'origine'); a.href = p.lien; a.target = '_blank'; a.rel = 'noopener'; m.append(a); c.append(m); }
        } else {
            const haut = el('div', 'haut');
            haut.append(el('span', 'meta', NOMS_GENRE[p.genre] + ' · ' + duree(p.minutes)), bouton('Fermer', 'petit', fermer));
            c.append(haut, el('h2', '', p.nom));
            if (p.lien) { const m = el('p', 'meta'); const a = el('a', '', 'Recette d\\'origine'); a.href = p.lien; a.target = '_blank'; a.rel = 'noopener'; m.append(a); c.append(m); }
            groupes.forEach(function (g) {
                if (!g[2].length) return;
                const sec = el('section', 'groupe-ing'), ing = el('div', 'ingredients');
                g[2].forEach(function (i) {
                    const t = el('span', g[0], i), pr = prixDe(i);
                    if (g[0] === 'manque' && pr) t.append(el('small', '', euros(pr[1])));
                    ing.append(t);
                });
                sec.append(el('h3', '', g[1] + ' · ' + g[2].length), ing);
                c.append(sec);
            });
            if (p.cout) c.append(el('p', 'meta', '≈ ' + euros(p.cout) + ' le repas pour deux (part utilisée de chaque produit) · en livraison ≈ ' + euros(d.livraison)));
            c.append(el('pre', 'recette', p.recette || 'Recette à écrire : demande à Claude, ou écris la tienne avec « Modifier ».'));
        }
        if (p.note) c.append(el('p', 'meta', p.note));
```

(Le reste de `ouvrirFiche` — « Va bien avec », actions, `verrouiller()` — ne change pas.)

- [ ] **Step 6: VERSION_PAGE** — `voyage/valise.py:1649` : `VERSION_PAGE = 46`.

- [ ] **Step 7: Run the whole suite**

Run: `cd voyage && .venv/bin/python3 -m pytest -q`
Expected: tout vert (849 + nouveaux ≈ 866).

- [ ] **Step 8: Vérifier le JS dans un vrai navigateur (syntaxe)**

```bash
cd voyage && .venv/bin/python3 -c "from diners import diners_en_html; open('/private/tmp/claude-501/-Users-julien/463b0b76-3ae0-443d-8762-f92647f594a2/scratchpad/diners-test.html','w').write(diners_en_html())" && node -e "
const h=require('fs').readFileSync('/private/tmp/claude-501/-Users-julien/463b0b76-3ae0-443d-8762-f92647f594a2/scratchpad/diners-test.html','utf8');
const s=h.split('<script>').slice(1).map(x=>x.split('</script>')[0]);
s.forEach((x,i)=>{try{new Function(x)}catch(e){console.log('script',i,e.message);process.exit(1)}});console.log('JS OK',s.length)"
```
Expected : `JS OK …` (si `node` absent : ouvrir la page en local à l'étape Task 5 et lire la console).

- [ ] **Step 9: Commit**

```bash
cd ~/Claude/Work/perso/python/julien-python-journey
git add voyage/diners.py voyage/valise.py voyage/test_diners.py voyage/test_fiche_recette.py
git commit -m "feat(casa): fiche recette magazine — une, courses repliées, ingrédients à cocher, tempo → étape (v46)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 5: Démo locale sur copie prod, validation Julien

**Files:** aucun (vérification).

- [ ] **Step 1: Copier la prod dans `valise_copie`** (lecture seule de Neon ; `valise_test` reste aux tests)

```bash
cd ~/Claude/Work/perso/python/julien-python-journey/voyage
NEON=$(grep '^DATABASE_URL=' .env | cut -d= -f2-)
createdb valise_copie 2>/dev/null || true
DATABASE_URL="" .venv/bin/python3 appliquer_schema.py --base valise_copie --appliquer
psql -q valise_copie -c "TRUNCATE repas, plats, courses, placard, reprises, achats, a_finir, cave"
pg_dump "$NEON" --data-only --no-owner --no-privileges -t plats -t courses -t placard -t repas -t reprises -t achats -t a_finir -t cave | psql -q valise_copie
psql -tA valise_copie -c "select count(*) from plats"
```
Expected : environ `132`. (Si une table n'existe pas en local, l'enlever des deux listes et relancer.)

- [ ] **Step 2: Lancer le serveur pour Mac + iPhone**

```bash
cd voyage && DATABASE_URL="" .venv/bin/python3 -c "from serveur import creer_app; creer_app('valise_copie', secret='').run(host='0.0.0.0', port=8001)"
```
URL iPhone : `http://192.168.1.15:8001/diners` (même wifi). Arrêter d'abord le serveur de démo statique s'il tient encore le port 8001.

- [ ] **Step 3: Contrôles avec Julien** — carbonara (une, tempo → étape 7 surlignée, secrets, rattrapages), polpette (sous-liste Sauce), hot dog (pas de tempo), croque-monsieur (Erreurs fréquentes en section), une recette sans étapes (texte brut), cocher/décocher, bandeau courses, mode sombre, puis « Modifier » toujours sur le texte brut.

- [ ] **Step 4: Retour Julien** — corrections éventuelles (nouveau cycle test → code), puis push/PR seulement sur sa demande.
