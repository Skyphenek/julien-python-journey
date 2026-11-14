# Casa — ajuster les quantités au nombre de parts : plan d'implémentation

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Sur la fiche recette, deux compteurs « À table » / « À garder » recalculent instantanément les quantités (ingrédients, poids et volumes des étapes).

**Architecture:** Un nouveau module `voyage/portions.py` repère en Python les quantités multipliables et les rend
sous forme de segments ; `fiche_recette.decouper` les attache à chaque texte affiché. Le même module porte
`SCRIPT_PORTIONS`, quelques fonctions JavaScript pures (arrondi, écriture, `texteAjuste`) testées sous node ; la
fiche de `voyage/diners.py` les utilise pour réafficher à chaque tap, sans aller-retour serveur.

**Tech Stack:** Python 3 (re), pytest, JavaScript sans dépendance (testé avec `node`), Flask existant.

## Global Constraints

- Spec : `docs/superpowers/specs/2026-11-14-casa-portions-design.md`.
- Tests : `cd voyage && .venv/bin/python3 -m pytest -q` (1 019 tests verts au départ, sur `e997368`).
- Aucune migration, aucune écriture en base, aucune nouvelle route.
- Libellés exacts : « À table », « À garder », « = 6 parts (recette écrite pour 2) », bandeau « Quantités ajustées pour 6 parts — temps de cuisson inchangés ; prends une plus grande cocotte, saisis en plus de fournées. »
- Bornes : à table 1 à 12, à garder 0 à 12.
- Arrondis : g et ml à 5 près sous 100, à 10 près au-dessus ; kg et l à 0,1 près (virgule) ; cl à l'unité ; sans unité métrique à la demie (« 1 1/2 ») ; jamais 0 (5 g, 5 ml, 0,1, 1 cl, 1/2).
- Facteur 1 : texte d'origine à l'identique.
- `decouper` ne lève jamais (le `try/except` existant reste).
- `SCRIPT_DINERS` est une chaîne Python non brute : dans le JS ajouté là, une apostrophe dans une chaîne JS s'écrit `\\'`. `SCRIPT_PORTIONS` est une chaîne brute `r"""…"""`.
- VERSION_PAGE : 66 → 67 (`voyage/valise.py:1661`).
- Démo sur la copie de prod (Mac + iPhone en wifi) validée par Julien avant tout push / PR.

## Fichiers

- Create `voyage/portions.py` — `base_parts`, `segmenter`, `SCRIPT_PORTIONS`.
- Create `voyage/test_portions.py` — tests Python et test node du JS.
- Modify `voyage/fiche_recette.py` — attache `base` et les segments `*_s`.
- Modify `voyage/test_fiche_recette.py` — égalités de dict existantes, nouveaux tests.
- Modify `voyage/diners.py` — CSS, JS de la fiche, injection de `SCRIPT_PORTIONS`.
- Modify `voyage/test_diners.py` — marqueurs.
- Modify `voyage/valise.py:1661` — VERSION_PAGE.

---

### Task 1: `portions.py` — base des compteurs et segments

**Files:**
- Create: `voyage/portions.py`
- Test: `voyage/test_portions.py`

**Interfaces:**
- Produces:
  - `base_parts(pour: str) -> dict | None` : `{"table": int, "garder": int}` ou `None`.
  - `segmenter(texte: str, premier: bool = False) -> list[dict]` : segments `{"t": str}` ou
    `{"t": str, "q": float, "u": str}` (+ `"q2": float, "sep": str` pour une plage). `u` ∈ `"g" "kg" "ml" "cl" "l" ""`.
    `"".join(s["t"] for s in segments) == texte`.
  - `SECTIONS_METRIQUES = ("Variante", "Erreurs", "Avec")`.

- [ ] **Step 1: Écrire les tests qui échouent**

`voyage/test_portions.py` :

```python
"""Tests de portions.py : quantités multipliables d'une recette (logique pure + JS sous node)."""
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

from portions import base_parts, segmenter


def bout_a_bout(segments):
    return "".join(s["t"] for s in segments)


def quantites(segments):
    return [(s["q"], s["u"]) for s in segments if "q" in s]


@pytest.mark.parametrize("pour, attendu", [
    ("Pour 2", {"table": 2, "garder": 0}),
    ("Pour 8", {"table": 8, "garder": 0}),
    ("Pour 4 (deux repas à deux)", {"table": 2, "garder": 2}),
    ("Pour 4 (deux repas à deux) — meilleur réchauffé le lendemain", {"table": 2, "garder": 2}),
    ("Pour 4 (deux dîners, ou un dîner à quatre)", {"table": 2, "garder": 2}),
    ("Pour 2, plus 2 parts à congeler", {"table": 2, "garder": 2}),
    ("Pour 4 portions (se congèle)", {"table": 4, "garder": 0}),
    ("Pour 6 — à faire la veille (6 heures de frigo)", {"table": 6, "garder": 0}),
    ("Pour 2 (8 rouleaux)", {"table": 2, "garder": 0}),
])
def test_base_parts_lisible(pour, attendu):
    assert base_parts(pour) == attendu


@pytest.mark.parametrize("pour", ["", "Pour 2 à 4", "Pour 1 ou 2", "Pour 1 gros appétit ou 2", "Pour 4 en apéro",
                                  "Pour 4 à l'apéro", "Pour 8 tranches (moule à cake de 25 cm)", "Pour 20 nems",
                                  "Pour 14", "Une recette sans portion"])
def test_base_parts_floue(pour):
    assert base_parts(pour) is None


def test_premier_nombre_avec_unite_metrique():
    s = segmenter("320 g de penne", premier=True)
    assert s[0] == {"t": "320", "q": 320.0, "u": "g"}
    assert bout_a_bout(s) == "320 g de penne"


def test_formats_de_quantite():
    assert quantites(segmenter("1,2 kg de veau", premier=True)) == [(1.2, "kg")]
    assert quantites(segmenter("1/2 citron", premier=True)) == [(0.5, "")]
    assert quantites(segmenter("1 1/2 c. à s. de farine", premier=True)) == [(1.5, "")]
    assert quantites(segmenter("12 petits oignons grelots", premier=True)) == [(12.0, "")]
    assert quantites(segmenter("3 cm de gingembre", premier=True)) == [(3.0, "")]


def test_plage():
    s = segmenter("2–3 c. à s. d'eau", premier=True)
    assert s[0] == {"t": "2–3", "q": 2.0, "u": "", "q2": 3.0, "sep": "–"}
    assert bout_a_bout(s) == "2–3 c. à s. d'eau"


def test_premier_nombre_qui_n_est_pas_une_quantite():
    assert quantites(segmenter("5 min à 180 °C", premier=True)) == []
    assert quantites(segmenter("50 % de cacao", premier=True)) == []


def test_dans_une_etape_seuls_poids_et_volumes():
    texte = "Fais réduire 80 cl de bouillon à feu vif 10 min, jusqu'à environ 60 cl, puis 2 œufs et les 40 g de beurre."
    s = segmenter(texte)
    assert quantites(s) == [(80.0, "cl"), (60.0, "cl"), (40.0, "g")]
    assert bout_a_bout(s) == texte


def test_heures_renvois_et_mots_ne_bougent_pas():
    for texte in ("0:12  Viande rincée, eau froide (2).", "Parmigiano Reggiano AOP (24 mois)", "en cubes de 5 cm",
                  "1 l’eau", "B12"):
        s = segmenter(texte)
        assert quantites(s) == [] and bout_a_bout(s) == texte


def test_seconds_nombres_d_une_ligne_d_ingredient():
    s = segmenter("60 g (dont 30 g froid, en dés)", premier=True)
    assert quantites(s) == [(60.0, "g"), (30.0, "g")]
    s = segmenter("4 c. à s. d'huile d'olive (dont 1 crue pour finir)", premier=True)
    assert quantites(s) == [(4.0, "")]


def test_fraction_impossible_reste_du_texte():
    s = segmenter("1/0 citron", premier=True)
    assert quantites(s) == [] and bout_a_bout(s) == "1/0 citron"
```

- [ ] **Step 2: Lancer les tests, constater l'échec**

Run: `cd voyage && .venv/bin/python3 -m pytest test_portions.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'portions'`

- [ ] **Step 3: Écrire `voyage/portions.py`**

```python
"""Portions : les quantités qu'on peut multiplier dans le texte d'une recette (fiche « À table / À garder »).

Python repère et marque (segments) ; le JavaScript de la fiche (SCRIPT_PORTIONS) multiplie et arrondit.
"""
import re

NOMBRE = r"\d+\s+\d+/\d+|\d+/\d+|\d+(?:[.,]\d+)?"                 # « 1 1/2 », « 1/2 », « 1,2 », « 320 »
QUANTITE = re.compile(rf"(?<![\w:/.,])({NOMBRE})(?:\s?([–-])\s?({NOMBRE}))?(?![\w:/]|[.,]\d)")
METRIQUE = re.compile(r"\s?(kg|g|ml|cl|l)(?![\wÀ-ÿ’'])")
PAS_UNE_QUANTITE = re.compile(r"\s?(?:min\b|h\b|°|%)")
BASE = re.compile(r"^Pour (\d+)(?=$|[\s,(—])(.*)$")
SUITE_ADMISE = re.compile(r"^(?:$|\s*[,(—]|\s+(?:portions?|personnes?)\b)")
DEUX_REPAS = re.compile(r"deux (?:repas|dîners)")
PLUS_PARTS = re.compile(r"plus (\d+) parts?")
SECTIONS_METRIQUES = ("Variante", "Erreurs", "Avec")              # là, seuls les g/kg/ml/cl/l bougent


def base_parts(pour):
    """« Pour … » -> {"table", "garder"} de départ des compteurs, ou None : portion floue, pas de compteurs."""
    m = BASE.match(pour or "")
    if not m or not SUITE_ADMISE.match(m.group(2)):
        return None
    n, suite = int(m.group(1)), m.group(2)
    if not 1 <= n <= 12:
        return None
    if DEUX_REPAS.search(suite) and n % 2 == 0:
        return {"table": n // 2, "garder": n // 2}
    plus = PLUS_PARTS.search(suite)
    if plus:
        return {"table": n, "garder": int(plus.group(1))}
    return {"table": n, "garder": 0}


def _valeur(nombre):
    """« 1 1/2 » -> 1.5, « 1,2 » -> 1.2 ; None si illisible (1/0)."""
    n = re.sub(r"\s+", " ", nombre.strip()).replace(",", ".")
    try:
        if "/" in n:
            entier, _, fraction = n.rpartition(" ")
            haut, bas = fraction.split("/")
            return (float(entier) if entier else 0.0) + int(haut) / int(bas)
        return float(n)
    except (ValueError, ZeroDivisionError):
        return None


def segmenter(texte, premier=False):
    """Texte -> segments {"t"} ou {"t", "q", "u"} (+ "q2", "sep" pour une plage) ; les "t" bout à bout redonnent
    le texte. premier : le 1er nombre est la quantité de la ligne, quelle que soit son unité (sauf min, h, °, %) ;
    les autres nombres ne comptent que suivis de g, kg, ml, cl, l."""
    segments, i, vu = [], 0, False
    for m in QUANTITE.finditer(texte):
        apres = texte[m.end():]
        unite = METRIQUE.match(apres)
        if premier and not vu:
            vu = True
            garde = not PAS_UNE_QUANTITE.match(apres)
        else:
            garde = unite is not None
        q = _valeur(m.group(1))
        q2 = _valeur(m.group(3)) if m.group(3) else None
        if not garde or q is None or (m.group(3) and q2 is None):
            continue
        if m.start() > i:
            segments.append({"t": texte[i:m.start()]})
        s = {"t": m.group(0), "q": q, "u": unite.group(1) if unite else ""}
        if m.group(3):
            s.update({"q2": q2, "sep": texte[m.end(1):m.start(3)]})
        segments.append(s)
        i = m.end()
    if i < len(texte):
        segments.append({"t": texte[i:]})
    return segments
```

- [ ] **Step 4: Lancer les tests**

Run: `cd voyage && .venv/bin/python3 -m pytest test_portions.py -q`
Expected: PASS (tous). Si `test_heures_renvois_et_mots_ne_bougent_pas` échoue sur « 1 l’eau » : vérifier que
`METRIQUE` exclut bien `’` après l'unité.

- [ ] **Step 5: Commit**

```bash
git add voyage/portions.py voyage/test_portions.py
git commit -m "feat(casa): portions.py, base des compteurs et quantités multipliables d'une recette"
```

---

### Task 2: `SCRIPT_PORTIONS` — arrondir et réécrire (JS testé sous node)

**Files:**
- Modify: `voyage/portions.py` (ajout en fin de fichier)
- Test: `voyage/test_portions.py` (ajout)

**Interfaces:**
- Consumes: le format de segments de la Task 1.
- Produces: `SCRIPT_PORTIONS: str` (JS) définissant `arrondiPortion(q, u) -> number`,
  `ecrirePortion(n, u) -> string`, `texteAjuste(segments, facteur) -> string`.

- [ ] **Step 1: Écrire le test qui échoue**

Ajouter à `voyage/test_portions.py` :

```python
VERIFS_JS = r"""
const echecs = [];
function ok(obtenu, attendu) { if (obtenu !== attendu) echecs.push(JSON.stringify(obtenu) + ' au lieu de ' + JSON.stringify(attendu)); }
const penne = [{t: '320', q: 320, u: 'g'}, {t: ' g de penne'}];
ok(texteAjuste(penne, 1), '320 g de penne');
ok(texteAjuste(penne, 3), '960 g de penne');
ok(texteAjuste([{t: '43', q: 43, u: 'g'}, {t: ' g'}], 3), '130 g');
ok(texteAjuste([{t: '32', q: 32, u: 'g'}, {t: ' g'}], 3), '95 g');
ok(texteAjuste([{t: '1', q: 1, u: 'g'}, {t: ' g'}], 0.5), '5 g');
ok(texteAjuste([{t: '1,2', q: 1.2, u: 'kg'}, {t: ' kg'}], 3), '3,6 kg');
ok(texteAjuste([{t: '80', q: 80, u: 'cl'}, {t: ' cl'}], 1.5), '120 cl');
ok(texteAjuste([{t: '1/2', q: 0.5, u: ''}, {t: ' citron'}], 3), '1 1/2 citron');
ok(texteAjuste([{t: '1/4', q: 0.25, u: ''}, {t: ' de chou'}], 0.5), '1/2 de chou');
ok(texteAjuste([{t: '12', q: 12, u: ''}, {t: ' oignons'}], 3), '36 oignons');
ok(texteAjuste([{t: '2–3', q: 2, u: '', q2: 3, sep: '–'}, {t: ' c. à s.'}], 2), '4–6 c. à s.');
ok(texteAjuste([{t: 'Sel'}], 3), 'Sel');
if (echecs.length) { console.error(echecs.join('\n')); process.exit(1); }
"""


def test_script_portions_sous_node(tmp_path):
    from portions import SCRIPT_PORTIONS
    node = shutil.which("node")
    if node is None:
        pytest.skip("node absent")
    fichier = tmp_path / "portions.js"
    fichier.write_text(SCRIPT_PORTIONS + VERIFS_JS, encoding="utf-8")
    r = subprocess.run([node, str(fichier)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
```

- [ ] **Step 2: Lancer le test, constater l'échec**

Run: `cd voyage && .venv/bin/python3 -m pytest test_portions.py::test_script_portions_sous_node -q`
Expected: FAIL — `ImportError: cannot import name 'SCRIPT_PORTIONS'`

- [ ] **Step 3: Ajouter `SCRIPT_PORTIONS` à la fin de `voyage/portions.py`**

```python
SCRIPT_PORTIONS = r"""
    // --- Portions (portions.py) : multiplier les quantités repérées en Python, arrondir pour la cuisine ---
    function arrondiPortion(q, u) {
        if (u === 'g' || u === 'ml') { const pas = q < 100 ? 5 : 10; return Math.max(Math.round(q / pas) * pas, pas); }
        if (u === 'kg' || u === 'l') return Math.max(Math.round(q * 10) / 10, 0.1);
        if (u === 'cl') return Math.max(Math.round(q), 1);
        return Math.max(Math.round(q * 2) / 2, 0.5);                 // à la pièce, à la cuillère : à la demie
    }
    function ecrirePortion(n, u) {
        if (u !== '') return String(n).replace('.', ',');
        const entier = Math.floor(n), demi = n - entier >= 0.5;
        if (!entier) return '1/2';
        return demi ? entier + ' 1/2' : String(entier);
    }
    function texteAjuste(segments, facteur) {
        return segments.map(function (s) {
            if (s.q === undefined || facteur === 1) return s.t;
            let t = ecrirePortion(arrondiPortion(s.q * facteur, s.u), s.u);
            if (s.q2 !== undefined) t += s.sep + ecrirePortion(arrondiPortion(s.q2 * facteur, s.u), s.u);
            return t;
        }).join('');
    }
"""
```

- [ ] **Step 4: Lancer les tests**

Run: `cd voyage && .venv/bin/python3 -m pytest test_portions.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add voyage/portions.py voyage/test_portions.py
git commit -m "feat(casa): SCRIPT_PORTIONS, arrondis de cuisine testés sous node"
```

---

### Task 3: `decouper` attache la base et les segments

**Files:**
- Modify: `voyage/fiche_recette.py` (imports en tête ; fonction `decouper`, l. 125-135 ; nouvelle fonction `_segments_ligne`)
- Test: `voyage/test_fiche_recette.py`

**Interfaces:**
- Consumes: `base_parts`, `segmenter`, `SECTIONS_METRIQUES` (Task 1).
- Produces (dans la fiche renvoyée par `decouper`, en plus des champs actuels) :
  - `f["base"]` : `{"table", "garder"}` ou `None` ;
  - chaque ingrédient : `nom_s`, `quantite_s` ;
  - chaque section : `lignes_s` (une liste de segments par ligne) ;
  - chaque ligne de tempo : `s` ;
  - chaque étape et chaque sous-puce (`si`) : `action_s` ; chaque morceau : `s` ; chaque secret : `s`.
  Les « t » de chaque liste, bout à bout, égalent le texte du champ correspondant (`nom`, `quantite`, ligne,
  `texte`, `action`).

- [ ] **Step 1: Adapter les égalités de dict existantes**

Dans `voyage/test_fiche_recette.py`, les ingrédients gagnent des clés : remplacer chaque
`f["ingredients"][k] == {"nom": A, "quantite": B}` par
`(f["ingredients"][k]["nom"], f["ingredients"][k]["quantite"]) == (A, B)`. Les quatre lignes concernées :

```python
    assert (f["ingredients"][0]["nom"], f["ingredients"][0]["quantite"]) == ("Spaghetti", "320 g")
    assert (f["ingredients"][2]["nom"], f["ingredients"][2]["quantite"]) == ("Jaunes d’œufs", "4 (env. 70 g de jaunes)")
```
```python
    assert (f["ingredients"][3]["nom"], f["ingredients"][3]["quantite"]) == ("Beurre", "60 g (dont 30 g froid, en dés, pour la mantecatura)")
```
```python
    assert (f["ingredients"][0]["nom"], f["ingredients"][0]["quantite"]) == ("Bœuf haché", "350 g")
```
```python
    assert (f["ingredients"][0]["nom"], f["ingredients"][0]["quantite"]) == ("4 saucisses de Strasbourg, 4 pains à hot dog, moutarde, ketchup", "")
```

Puis chercher d'autres comparaisons de dict de fiche dans les tests :
Run: `cd voyage && grep -rn '"quantite":' test_*.py`
Expected: plus aucune égalité de dict complète sur un ingrédient (les autres usages se lisent clé par clé).

- [ ] **Step 2: Écrire les tests qui échouent**

Ajouter à `voyage/test_fiche_recette.py` :

```python
def joint(segments):
    return "".join(s["t"] for s in segments)


def chiffres(segments):
    return [(s["q"], s["u"]) for s in segments if "q" in s]


def test_base_des_compteurs():
    assert decouper(lire("plat-carbonara"))["base"] == {"table": 2, "garder": 0}
    assert decouper(lire("tester-polpette"))["base"] == {"table": 2, "garder": 2}
    assert decouper(lire("tester-nems"))["base"] is None                    # « Pour 20 nems »
    assert decouper("")["base"] is None


def test_segments_des_ingredients_et_sections():
    f = decouper(lire("plat-carbonara"))
    assert chiffres(f["ingredients"][0]["quantite_s"]) == [(320.0, "g")]
    assert chiffres(f["ingredients"][2]["quantite_s"]) == [(4.0, ""), (70.0, "g")]
    sauce = [s for s in decouper(lire("tester-polpette"))["sections"] if s["titre"] == "Sauce"][0]
    assert chiffres(sauce["lignes_s"][0]) == [(700.0, "g")]


def test_variantes_seuls_poids_et_volumes():
    f = decouper("Pour 2\n- Riz : 160 g\n\nVariantes :\n- 2 œufs en plus\n- 30 g de comté\n\nSauce :\n"
                 "- Oignon — 1 petit\n\n1. Cuis le riz : 10 min dans 50 cl d'eau.")   # « : » coupe l'action
    variantes = [s for s in f["sections"] if s["titre"] == "Variantes"][0]
    assert chiffres(variantes["lignes_s"][0]) == [] and chiffres(variantes["lignes_s"][1]) == [(30.0, "g")]
    sauce = [s for s in f["sections"] if s["titre"] == "Sauce"][0]
    assert chiffres(sauce["lignes_s"][0]) == [(1.0, "")]
    etape = f["etapes"][0]
    assert chiffres(etape["action_s"]) == [] and joint(etape["action_s"]) == etape["action"]
    tout = [s for m in etape["morceaux"] for s in m["s"]]
    assert chiffres(tout) == [(50.0, "cl")]


def _verifie_bout_a_bout(f):
    for x in f["ingredients"]:
        assert joint(x["nom_s"]) == x["nom"] and joint(x["quantite_s"]) == x["quantite"]
    for s in f["sections"]:
        assert [joint(l) for l in s["lignes_s"]] == s["lignes"]
    for l in (f["tempo"] or {"lignes": []})["lignes"]:
        assert joint(l["s"]) == l["texte"]
    for e in f["etapes"]:
        for p in [e, *e["si"]]:
            assert joint(p["action_s"]) == p["action"]
            assert all(joint(m["s"]) == m["texte"] for m in p["morceaux"])
            assert all(joint(s["s"]) == s["texte"] for s in p["secrets"])


def test_segments_bout_a_bout_sur_tous_les_exemples():
    for fichier in sorted(EX.glob("*.txt")):
        f = decouper(fichier.read_text(encoding="utf-8"))
        assert f["structuree"], fichier.name
        _verifie_bout_a_bout(f)
```

- [ ] **Step 3: Lancer les tests, constater l'échec**

Run: `cd voyage && .venv/bin/python3 -m pytest test_fiche_recette.py -q`
Expected: FAIL — `KeyError: 'base'` (et `'quantite_s'`, `'lignes_s'`…)

- [ ] **Step 4: Implémenter dans `voyage/fiche_recette.py`**

En tête, après `import re` :

```python
from portions import SECTIONS_METRIQUES, base_parts, segmenter
```

Dans `_vide()`, ajouter la clé `base` :

```python
def _vide():
    return {"structuree": False, "pour": "", "base": None, "ingredients": [], "sections": [], "tempo": None,
            "etapes": [], "difference": []}
```

Avant `def decouper`, ajouter :

```python
def _segments_ligne(ligne):
    """Une ligne d'ingrédient (« Passata — 700 g ») : la quantité est après le séparateur s'il y en a un."""
    m = COUPE_INGREDIENT.search(ligne)
    if not m:
        return segmenter(ligne, premier=True)
    return segmenter(ligne[:m.end()]) + segmenter(ligne[m.end():], premier=True)


def _segments_phrase(p):
    """Une étape ou une sous-puce découpée : segments de l'action, de chaque morceau et de chaque secret."""
    return {**p, "action_s": segmenter(p["action"]),
            "morceaux": [{**m, "s": segmenter(m["texte"])} for m in p["morceaux"]],
            "secrets": [{**s, "s": segmenter(s["texte"])} for s in p["secrets"]]}


def _ajouter_portions(f):
    """Base des compteurs et quantités multipliables (portions.py) sur chaque texte affiché par la fiche."""
    f["base"] = base_parts(f["pour"])
    for x in f["ingredients"]:
        x["nom_s"] = segmenter(x["nom"], premier=not x["quantite"])
        x["quantite_s"] = segmenter(x["quantite"], premier=True)
    for s in f["sections"]:
        metrique = s["titre"].startswith(SECTIONS_METRIQUES)
        s["lignes_s"] = [segmenter(l) if metrique else _segments_ligne(l) for l in s["lignes"]]
    for l in (f["tempo"] or {"lignes": []})["lignes"]:
        l["s"] = segmenter(l["texte"])
    f["etapes"] = [{**_segments_phrase(e), "si": [_segments_phrase(s) for s in e["si"]]} for e in f["etapes"]]
    return f
```

Dans `decouper`, juste avant `return f` du bloc `try` :

```python
        f["etapes"] = [{"n": e["n"], **decouper_phrase(e["texte"]), "si": [decouper_phrase(s) for s in e["si"]]}
                       for e in f["etapes"]]
        return _ajouter_portions(f)
```

- [ ] **Step 5: Lancer les tests de la fiche**

Run: `cd voyage && .venv/bin/python3 -m pytest test_fiche_recette.py test_portions.py -q`
Expected: PASS

- [ ] **Step 6: Vérifier sur toutes les recettes de la copie de prod**

La base locale `valise_copie` est une copie de prod du 14/11 (si absente : `casa/copier_prod.py`, voir STATUS).

Run:
```bash
cd voyage && DATABASE_URL="" .venv/bin/python3 - <<'EOF'
from db import connecter, lire_plats
from fiche_recette import decouper
from test_fiche_recette import _verifie_bout_a_bout
plats = lire_plats(connecter("valise_copie"))
sans, total = [], 0
for p in plats:
    f = decouper(p["recette"])
    if not f["structuree"]:
        continue
    _verifie_bout_a_bout(f)
    total += 1
    if f["base"] is None:
        sans.append(f"{p['id']} | {f['pour']}")
print(total, "fiches vérifiées bout à bout ;", len(sans), "sans compteurs :")
print("\n".join(sans))
EOF
```
Expected: aucune `AssertionError` ; une douzaine de fiches sans compteurs, toutes à portion floue (« à 4 », « ou 2 », « apéro », « tranches », « nems »…). Une « Pour 2 » ou « Pour 4 » dans la liste = bug de `base_parts` : ajouter le cas au test paramétré et corriger.

- [ ] **Step 7: Lancer toute la suite**

Run: `cd voyage && .venv/bin/python3 -m pytest -q`
Expected: tout vert (1 019 + les nouveaux).

- [ ] **Step 8: Commit**

```bash
git add voyage/fiche_recette.py voyage/test_fiche_recette.py
git commit -m "feat(casa): la fiche découpée porte la base des compteurs et les quantités multipliables"
```

---

### Task 4: la fiche — compteurs, texte ajusté, bandeau (version 67)

**Files:**
- Modify: `voyage/diners.py` — import en tête ; CSS après `ul.ing-fiche li.coche` (l. 667) ; JS de la fiche
  (`phraseFiche`, `ingredientsFiche`, `tempoFiche`, `etapesFiche`, branche structurée de `ouvrirFiche`, l. 1309-1430) ;
  template, ligne `<script>{SCRIPT_DINERS}</script>` (l. 1894)
- Modify: `voyage/valise.py:1661`
- Test: `voyage/test_diners.py` (marqueurs de `test_fiche_magazine…`, l. 199-202)

**Interfaces:**
- Consumes: `SCRIPT_PORTIONS` et `texteAjuste(segments, facteur)` (Task 2) ; champs `base`, `nom_s`, `quantite_s`,
  `lignes_s`, `s`, `action_s` (Task 3).
- Produces: fonctions JS `compteursParts(f, etat, rafraichir)`, `bandeauParts(etat)` ; signatures
  `phraseFiche(x, parent, facteur)`, `ingredientsFiche(f, facteur, coches)`, `tempoFiche(f, facteur)`,
  `etapesFiche(f, facteur)`.

- [ ] **Step 1: Écrire le test qui échoue**

Dans `voyage/test_diners.py`, compléter la boucle de marqueurs (l. 199-202) :

```python
    for marqueur in ("function uneFiche", "function bandeauCourses", "function ingredientsFiche",     # fiche magazine
                     "function tempoFiche", "function etapesFiche", "function phraseFiche",
                     "div.une-fiche", "details.courses-fiche", "ol.etapes-fiche", "div.tempo-fiche",
                     "function texteAjuste", "function compteursParts", "function bandeauParts",       # portions
                     "div.parts-fiche", "p.bandeau-parts", "'À table'", "'À garder'",
                     "recette écrite pour", "Quantités ajustées pour"):
        assert marqueur in html, marqueur
```

Et ajouter un test de version :

```python
def test_version_page_portions():
    from valise import VERSION_PAGE
    assert VERSION_PAGE >= 67
```

- [ ] **Step 2: Lancer, constater l'échec**

Run: `cd voyage && .venv/bin/python3 -m pytest test_diners.py -q`
Expected: FAIL — `AssertionError: function texteAjuste` et `VERSION_PAGE >= 67`.

- [ ] **Step 3: Injecter `SCRIPT_PORTIONS` et ajouter le CSS**

En tête de `voyage/diners.py`, avec les autres imports :

```python
from portions import SCRIPT_PORTIONS
```

Dans le template (l. 1894), juste avant `<script>{SCRIPT_DINERS}</script>` :

```html
<script>{SCRIPT_PORTIONS}</script>
```

Après la ligne `ul.ing-fiche li.coche { … }` (l. 667) :

```css
div.parts-fiche { display: flex; flex-wrap: wrap; align-items: center; gap: 8px 16px; margin: 12px 0; }
div.parts-fiche .compteur { display: inline-flex; align-items: center; gap: 6px; }
div.parts-fiche .compteur b { min-width: 1.6em; text-align: center; font-size: 17px; }
p.bandeau-parts { margin: 12px 0; padding: 8px 10px; border-left: 3px solid var(--courses); font-size: 14px; }
```

- [ ] **Step 4: Texte ajusté dans les quatre fonctions de la fiche**

Remplacer `phraseFiche` :

```js
    function phraseFiche(x, parent, facteur) {
        if (x.action) parent.append(el('strong', '', texteAjuste(x.action_s, facteur)));
        x.morceaux.forEach(function (m) {
            const t = texteAjuste(m.s, facteur);
            parent.append(m.genre === 'pourquoi' ? el('em', '', ' ' + t) : document.createTextNode(t));
        });
        x.secrets.forEach(function (s) {
            const b = el('div', 'secret' + (s.qui === 'mamma' ? ' mamma' : ''));
            b.append(el('b', '', s.qui === 'mamma' ? 'Secret de mamma' : 'Secret de grand-mère'), document.createTextNode(' · ' + texteAjuste(s.s, facteur)));
            parent.append(b);
        });
    }
```

Vérifier qu'aucun autre appel ne l'utilise sans facteur :
Run: `cd voyage && grep -n "phraseFiche(" diners.py`
Expected: la définition + les deux appels de `etapesFiche` (mis à jour ci-dessous).

Remplacer `ingredientsFiche` :

```js
    function ingredientsFiche(f, facteur, coches) {
        const frag = document.createDocumentFragment();
        function liste(lignes, prefixe) {
            const ul = el('ul', 'ing-fiche');
            lignes.forEach(function (x, i) {
                const li = el('li'), c = el('input'), t = el('span'), cle = prefixe + i;
                c.type = 'checkbox';
                c.checked = !!coches[cle];                          // la case reste cochée quand les parts changent
                li.classList.toggle('coche', c.checked);
                c.addEventListener('change', function () { coches[cle] = c.checked; li.classList.toggle('coche', c.checked); });
                t.append(el('b', '', texteAjuste(x.nom_s, facteur)));
                if (x.quantite) t.append(document.createTextNode(texteAjuste(x.quantite_s, facteur)));
                li.append(c, t); ul.append(li);
            });
            return ul;
        }
        if (f.ingredients.length) frag.append(el('h3', 'titre-fiche', 'Ingrédients'), liste(f.ingredients, 'i'));
        f.sections.forEach(function (s, k) {
            if (!s.lignes.length) { frag.append(el('p', 'para-fiche', s.titre)); return; }
            frag.append(el('h3', 'titre-fiche', s.titre),
                        liste(s.lignes.map(function (l, i) { return { nom: l, nom_s: s.lignes_s[i], quantite: '', quantite_s: [] }; }), 's' + k + '-'));
        });
        return frag;
    }
```

Dans `tempoFiche`, la signature devient `function tempoFiche(f, facteur) {` et la ligne du bouton :

```js
            b.append(el('b', '', l.heure), document.createTextNode(texteAjuste(l.s, facteur)));
```

Dans `etapesFiche`, la signature devient `function etapesFiche(f, facteur) {` et les deux appels :

```js
            phraseFiche(e, li, facteur);
```
```js
                e.si.forEach(function (s) { const x = el('li'); phraseFiche(s, x, facteur); ul.append(x); });
```

- [ ] **Step 5: Compteurs, bandeau et branche structurée de `ouvrirFiche`**

Juste avant `function lienOrigine`, ajouter :

```js
    function compteursParts(f, etat, rafraichir) {
        const bloc = el('div', 'parts-fiche');
        function compteur(libelle, cle, min) {
            const g = el('span', 'compteur');
            g.append(el('span', '', libelle),
                     bouton('–', 'petit', function () { if (etat[cle] > min) { etat[cle]--; rafraichir(); } }),
                     el('b', '', String(etat[cle])),
                     bouton('+', 'petit', function () { if (etat[cle] < 12) { etat[cle]++; rafraichir(); } }));
            return g;
        }
        const total = etat.table + etat.garder;
        bloc.append(compteur('À table', 'table', 1), compteur('À garder', 'garder', 0),
                    el('span', 'meta', '= ' + total + (total > 1 ? ' parts' : ' part') + ' (recette écrite pour ' + (f.base.table + f.base.garder) + ')'));
        return bloc;
    }
    function bandeauParts(etat) {
        const total = etat.table + etat.garder;
        return el('p', 'bandeau-parts', 'Quantités ajustées pour ' + total + (total > 1 ? ' parts' : ' part') +
                  ' — temps de cuisson inchangés ; prends une plus grande cocotte, saisis en plus de fournées.');
    }
```

Dans `ouvrirFiche`, remplacer le bloc :

```js
        if (p.fiche && p.fiche.structuree) {
            c.append(uneFiche(p), bandeauCourses(p, groupes), ingredientsFiche(p.fiche), tempoFiche(p.fiche), etapesFiche(p.fiche));
            lienOrigine(p, c);
        } else {
```

par :

```js
        if (p.fiche && p.fiche.structuree) {
            const f = p.fiche, corps = el('div', 'corps-fiche'), coches = {};
            const etat = f.base ? { table: f.base.table, garder: f.base.garder } : null;   // rien n'est mémorisé
            const rafraichir = function () {
                const facteur = etat ? (etat.table + etat.garder) / (f.base.table + f.base.garder) : 1;
                corps.replaceChildren();
                if (etat) corps.append(compteursParts(f, etat, rafraichir));
                corps.append(ingredientsFiche(f, facteur, coches), tempoFiche(f, facteur));
                if (facteur !== 1) corps.append(bandeauParts(etat));
                corps.append(etapesFiche(f, facteur));
            };
            rafraichir();
            c.append(uneFiche(p), bandeauCourses(p, groupes), corps);
            lienOrigine(p, c);
        } else {
```

- [ ] **Step 6: Version de page**

`voyage/valise.py:1661` :

```python
VERSION_PAGE = 67
```

- [ ] **Step 7: Lancer toute la suite et vérifier la syntaxe JS**

Run: `cd voyage && .venv/bin/python3 -m pytest -q`
Expected: tout vert. Le test existant qui passe le script de la page sous `node --check` (s'il couvre
`SCRIPT_DINERS`) doit rester vert ; sinon :

```bash
cd voyage && .venv/bin/python3 -c "
from diners import SCRIPT_DINERS; from portions import SCRIPT_PORTIONS
open('/tmp/fiche.js','w').write(SCRIPT_PORTIONS + SCRIPT_DINERS)" && node --check /tmp/fiche.js && echo JS OK
```
Expected: `JS OK`

- [ ] **Step 8: Commit**

```bash
git add voyage/diners.py voyage/valise.py voyage/test_diners.py
git commit -m "feat(casa): fiche recette, compteurs À table / À garder et quantités ajustées (version 67)"
```

---

### Task 5: démo sur la copie de prod

**Files:** aucun.

- [ ] **Step 1: Lancer l'app sur la copie**

```bash
cd voyage && DATABASE_URL="" .venv/bin/python3 -c "
from serveur import creer_app
creer_app('valise_copie', secret='').run(host='0.0.0.0', port=8001)"
```
Expected: serveur sur le port 8001 ; ouvrir `http://<ip du Mac>:8001/recettes` sur l'iPhone (même wifi).

- [ ] **Step 2: Parcours à faire valider par Julien (et Laetitia)**

1. Blanquette : compteurs à « À table 2 · À garder 2 = 4 parts (recette écrite pour 4) ». Passer « À table » à 4 :
   « 1,2 kg » → « 1,8 kg », « 80 cl » de l'étape 5 → « 120 cl », bandeau visible ; temps inchangés.
2. Arrabbiata « Pour 2 » : « À garder » +2 → 640 g de penne, « 1/2 bouquet » → « 1 bouquet ».
3. Cocher deux ingrédients, changer les compteurs : les cases restent cochées.
4. Revenir à la base : bandeau masqué, texte identique à l'origine.
5. Nems (« Pour 20 nems ») : pas de compteurs, fiche comme avant.
6. Fermer et rouvrir une fiche : retour à la base.

- [ ] **Step 3: Après le OK de Julien seulement**

Push de `feat/casa-portions`, PR, merge sur demande ; attendre Render (`sw.js` en `valise-v67`) ; MAJ
`~/Claude/Work/perso/casa/STATUS.md` et `~/Claude/TASKS.md`.
