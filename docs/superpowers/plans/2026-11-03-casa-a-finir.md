# Casa Binomerie — À finir (anti-gaspi sans saisie) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Dater automatiquement le frais du frigo (date d'entrée + durée de conservation), le signaler sur Aujourd'hui quand aucun repas prévu ne l'utilise à temps, avec des plats du carnet à poser en un tap, et faire passer ces plats en tête dans « Faisable tout de suite » et Proposer.

**Architecture:** Deux modules purs : `conservation.py` (durées) et `a_finir.py` (produits suivis, état, couverture par les repas prévus, plats suggérés, alertes). `db.py` lit le frais et garde les corrections (nouvelle table `a_finir`), plus une reprise une fois (`a-finir-v1`). `serveur.py` assemble ; `casa.py` affiche le bloc « À finir » ; `diners.py` reçoit les produits à finir dans `secours` et `proposer`.

**Tech Stack:** Python 3, Flask, psycopg2, Postgres (local `valise_test` pour les tests, Neon en prod), pytest, JS ES5 inline.

**Spec:** `docs/superpowers/specs/2026-11-03-casa-a-finir-design.md`

## Global Constraints

- Tout se lance depuis `voyage/` : `cd voyage && .venv/bin/python3 -m pytest <fichier> -q`.
- TDD : test qui échoue d'abord, puis le code, puis toute la suite verte (`.venv/bin/python3 -m pytest -q`, 721 tests au départ).
- Tests en base : uniquement `valise_test`. Ne jamais lancer `appliquer_schema.py` sans `--base valise_test`. Ne jamais toucher Neon.
- Ne pas toucher au sous-module `session-01-revolut-analyzer`.
- Les noms se comparent normalisés : `courses.normaliser` (« Crème  Fraîche » → « creme fraiche »).
- `A_FINIR_JOURS = 2` ; `ENCORE_BON_JOURS = 2` ; `MAX_SUGGESTIONS = 3`.
- Produits suivis : placard en stock de zone `frigo` ; habituels des courses rangés (`recurrent` et (`not actif` ou `pris`)) dont `courses.deviner_zone(nom) == "frigo"`.
- Durées par défaut par rayon : boucherie 2, frais 7, fruits-legumes 5, epicerie 30, specialise 14 ; inconnu 7.
- Textes de l'interface en français, apostrophes typographiques non requises ; dans les chaînes Python non brutes qui contiennent du JS, une apostrophe JS s'écrit `\\'`.
- `VERSION_PAGE` (dans `valise.py`) passe de 42 à 43 dans la tâche 5.
- Style du code : comme l'existant (docstrings en français, commentaires rares et utiles, noms français).
- Commits : message `feat: Casa Binomerie — …` / `test: …`, terminé par la ligne `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

## File Structure

- Create `voyage/conservation.py` — `duree(nom)` : jours de conservation d'un produit fermé.
- Create `voyage/a_finir.py` — logique pure : `suivis`, `etat`, `utilise`, `couverture`, `suggestions`, `jour_libre`, `alertes`, `plats_qui_utilisent`, constantes et données de reprise.
- Modify `voyage/schema.sql` — table `a_finir`.
- Modify `voyage/db.py` — `lire_frais`, `finir`, `corriger_a_finir`, `dater_frigo` ; suppression de la correction dans `enregistrer_article` et `enregistrer_placard`.
- Modify `voyage/appliquer_schema.py` — reprise `a-finir-v1`.
- Modify `voyage/diners.py` — `secours(..., a_finir=())`, `proposer(..., a_finir=())`, badge « à finir » dans `SCRIPT_DINERS`.
- Modify `voyage/serveur.py` — `alertes_du_frigo`, Aujourd'hui, `api/diners`, `api/diners/proposer`, `POST api/a-finir/<cle>`.
- Modify `voyage/casa.py` — `bloc_a_finir`, style, `SCRIPT_A_FINIR`, paramètre `a_finir` de `aujourdhui_en_html`.
- Modify `voyage/valise.py` — `VERSION_PAGE = 43`.
- Tests : create `voyage/test_conservation.py`, `voyage/test_a_finir.py`, `voyage/test_a_finir_db.py` ; modify `voyage/test_diners.py`, `voyage/test_casa.py`.

---

### Task 1: Durées de conservation

**Files:**
- Create: `voyage/conservation.py`
- Test: `voyage/test_conservation.py`

**Interfaces:**
- Consumes: `catalogue.cle_catalogue(nom)` (clé singulier/pluriel), `courses.deviner_rayon(nom)` (rayon du catalogue, sinon par mots, sinon `"autre"`).
- Produces: `conservation.duree(nom) -> int` ; constantes `PAR_RAYON`, `DUREE_INCONNUE`.

- [ ] **Step 1: Write the failing test** — `voyage/test_conservation.py`

```python
"""Tests des durées de conservation (conservation.py) : exceptions, défaut du rayon, inconnu."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from conservation import duree, PAR_RAYON, DUREE_INCONNUE


def test_exceptions_par_produit():
    assert duree("steaks hachés") == 1 and duree("Steak haché") == 1 and duree("saumon") == 1
    assert duree("fraises") == 3 and duree("salade") == 4 and duree("burrata") == 5
    assert duree("jambon") == 7 and duree("lait") == 7 and duree("mozzarella") == 10
    assert duree("crème fraîche") == 14 and duree("yaourt grec") == 14
    assert duree("comté") == 21 and duree("œufs") == 28 and duree("beurre demi-sel") == 28


def test_defaut_du_rayon():
    assert duree("cuisses de poulet") == PAR_RAYON["boucherie"] == 2
    assert duree("tomates") == PAR_RAYON["fruits-legumes"] == 5
    assert duree("chèvre") == PAR_RAYON["frais"] == 7
    assert duree("harissa") == PAR_RAYON["epicerie"] == 30
    assert duree("kimchi") == PAR_RAYON["specialise"] == 14


def test_inconnu():
    assert duree("truc introuvable") == DUREE_INCONNUE == 7
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd voyage && .venv/bin/python3 -m pytest test_conservation.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'conservation'`

- [ ] **Step 3: Write the implementation** — `voyage/conservation.py`

```python
"""Casa Binomerie — À finir : combien de jours un produit frais tient au frigo, fermé
(spec docs/superpowers/specs/2026-11-03-casa-a-finir-design.md).

Un défaut par rayon, des exceptions par produit ; des valeurs réalistes pour un frigo domestique, pas la prudence
maximale. Un produit entamé peut tourner plus vite : l'app ne le sait pas, [Fini] et [Encore bon] corrigent.
"""
from catalogue import cle_catalogue
from courses import deviner_rayon

PAR_RAYON = {"boucherie": 2, "frais": 7, "fruits-legumes": 5, "epicerie": 30, "specialise": 14}
DUREE_INCONNUE = 7

_EXCEPTIONS = {
    1: """bœuf haché, porc haché, steak haché, steaks hachés, chair à saucisse, tartare, carpaccio, foies de volaille,
        saumon, pavés de saumon, filets de saumon, cabillaud, dos de cabillaud, lieu noir, colin, merlu, églefin,
        haddock, bar, dorade, sole, sardines fraîches, maquereau, thon frais, truite, lotte, raie, Saint-Jacques,
        crevettes, crevettes crues, gambas, moules, palourdes, coques, huîtres, calamars, encornets, poulpe, seiche,
        crabe, homard, langoustines, bulots""",
    3: """fraises, framboises, myrtilles, mûres, groseilles, cassis, cerises, champignons de Paris, champignons,
        pleurotes, shiitakés, girolles, cèpes, pousses de soja, germes de haricot mungo""",
    4: """salade, sucrine, laitue, batavia, roquette, mâche, mesclun, jeunes pousses, épinards frais, persil,
        persil plat, coriandre, basilic, menthe, ciboulette, aneth, cerfeuil, estragon, basilic thaï""",
    5: "burrata, stracciatella",
    7: "lait, lait entier, lait demi-écrémé, ricotta, jambon, jambon blanc, blanc de dinde",
    10: """mozzarella, mozzarella di bufala, saumon fumé, truite fumée, carottes, chou blanc, chou rouge, chou vert,
        céleri-rave, poireaux, navets, panais, betteraves, radis noir, lardons, lardons fumés, allumettes de bacon,
        saucisses de Strasbourg, saucisses de Francfort, knacks, galettes de sarrasin, crêpes, pâte brisée,
        pâte feuilletée, pâte sablée, pâte à pizza, gnocchi, tortellini, raviolis frais, pâtes fraîches,
        tagliatelles fraîches, ravioles""",
    14: """crème fraîche, crème fraîche épaisse, crème liquide, crème fleurette, crème entière, mascarpone, yaourts,
        yaourt nature, yaourt grec, skyr, fromage blanc, faisselle, petits-suisses, crème dessert, kéfir,
        emmental râpé, fromage râpé, cheddar râpé, feta, halloumi, tofu, tofu fumé, chorizo, gingembre""",
    21: """parmesan, pecorino, pecorino romano, parmigiano reggiano, grana padano, comté, beaufort, emmental, gruyère,
        abondance, cantal, mimolette, gouda, cheddar, saucisson, saucisson sec, rosette, salami, guanciale,
        guanciale entier, pancetta, guanciale ou pancetta""",
    28: "œufs, beurre, beurre doux, beurre demi-sel",
}
_PAR_PRODUIT = {cle_catalogue(nom.strip()): jours for jours, noms in _EXCEPTIONS.items() for nom in noms.split(",")}


def duree(nom):
    """Les jours de conservation d'un produit fermé : son exception, sinon le défaut de son rayon, sinon 7."""
    return _PAR_PRODUIT.get(cle_catalogue(nom)) or PAR_RAYON.get(deviner_rayon(nom), DUREE_INCONNUE)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd voyage && .venv/bin/python3 -m pytest test_conservation.py -q`
Expected: `3 passed`. Si `duree("chèvre")` ou `duree("harissa")` ne tombe pas sur le bon rayon, vérifier `courses.deviner_rayon("chèvre")` (attendu `frais`) et `deviner_rayon("harissa")` (attendu `epicerie`) et remplacer dans le test par un autre produit du même rayon tiré de `catalogue.CATALOGUE` — ne pas changer les durées.

- [ ] **Step 5: Commit**

```bash
git add voyage/conservation.py voyage/test_conservation.py
git commit -m "feat: Casa Binomerie — À finir : durées de conservation par produit et par rayon

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 2: La logique À finir (pure)

**Files:**
- Create: `voyage/a_finir.py`
- Test: `voyage/test_a_finir.py`

**Interfaces:**
- Consumes: `conservation.duree(nom)` (tâche 1) ; `courses.normaliser`, `courses.deviner_zone`.
- Produces (utilisés par les tâches 3 à 5) :
  - `A_FINIR_JOURS = 2`, `ENCORE_BON_JOURS = 2`, `MAX_SUGGESTIONS = 3`, `NOM_REPRISE = "a-finir-v1"`, `JOUR_REPRISE = date(2026, 11, 3)`, `FRIGO_CONNU = {nom: (achete_le, jusqu_au ou None)}`.
  - `suivis(placard, courses, derniers_achats, corrections) -> [{"cle", "nom", "origine", "jusqu_au"}]` — `placard` : `[{"cle","nom","en_stock","zone","entre_le"}]` ; `courses` : articles `{"nom","recurrent","actif","pris", ...}` ; `derniers_achats` : `{cle: date}` ; `corrections` : `{cle: date}`.
  - `etat(jusqu_au, aujourd_hui) -> "a-verifier" | "a-finir" | None`.
  - `utilise(plat, cle) -> bool`.
  - `couverture(cle, jusqu_au, repas, par_id, aujourd_hui) -> (bool couvert, date trop_tard ou None)`.
  - `suggestions(cle, cles_a_finir, plats, stock) -> [{"plat": plat, "manquants": [noms]}]` (3 au plus).
  - `jour_libre(repas, aujourd_hui, jusqu_au) -> date | None`.
  - `alertes(produits, repas, plats, stock, aujourd_hui) -> [{"cle","nom","origine","jusqu_au","etat","trop_tard","suggestions","jour"}]`.
  - `plats_qui_utilisent(plats, cles) -> [ids]`.

- [ ] **Step 1: Write the failing tests** — `voyage/test_a_finir.py`

```python
"""Tests de a_finir.py : le frais suivi et daté, son état, les repas prévus, les plats suggérés (logique pure)."""
import sys
from datetime import date, timedelta
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from a_finir import (suivis, etat, utilise, couverture, suggestions, jour_libre, alertes, plats_qui_utilisent,
                     A_FINIR_JOURS)
from conservation import duree
from courses import normaliser

AUJ = date(2026, 11, 3)                       # un mardi
J = lambda n: AUJ + timedelta(days=n)


def element(nom, entre_le=AUJ, en_stock=True, zone="frigo"):
    return {"cle": normaliser(nom), "nom": nom, "en_stock": en_stock, "zone": zone, "entre_le": entre_le}


def habituel(nom, actif=False, pris=False):
    return {"nom": nom, "recurrent": True, "actif": actif, "pris": pris}


def plat(id_, nom, ingredients, minutes=20, statut="carnet", archive=False, pour="nous", genre="plat"):
    return {"id": id_, "nom": nom, "ingredients": list(ingredients), "minutes": minutes, "statut": statut,
            "archive": archive, "pour": pour, "genre": genre}


def repas(jour, *plats, issue=None, moment="diner"):
    return {"jour": jour, "moment": moment, "plats": list(plats), "issue": issue}


# --- suivis ---

def test_suivis_placard_du_frigo_seulement():
    p = suivis([element("steaks hachés", J(-1)), element("petits pois", zone="congelateur"),
                element("comté", en_stock=False)], [], {}, {})
    assert [(x["cle"], x["origine"], x["jusqu_au"]) for x in p] == [("steaks haches", "placard", J(-1) + timedelta(days=1))]


def test_suivis_date_d_entree_la_plus_recente():
    p = suivis([element("jambon", J(-5))], [], {"jambon": J(-1)}, {})
    assert p[0]["jusqu_au"] == J(-1) + timedelta(days=duree("jambon"))


def test_suivis_habituels_ranges_du_frigo():
    courses = [habituel("mozzarella"), habituel("yaourt grec", actif=True, pris=True), habituel("lait", actif=True),
               habituel("citrons"), {"nom": "jambon", "recurrent": False, "actif": True, "pris": True}]
    p = suivis([], courses, {"mozzarella": J(-2), "yaourt grec": AUJ, "lait": AUJ, "citrons": AUJ, "jambon": AUJ}, {})
    assert {x["cle"]: x["origine"] for x in p} == {"mozzarella": "habituel", "yaourt grec": "habituel"}


def test_suivis_sans_date_non_suivi_sauf_correction():
    assert suivis([], [habituel("beurre")], {}, {}) == []
    assert suivis([], [habituel("beurre")], {}, {"beurre": J(5)})[0]["jusqu_au"] == J(5)


def test_suivis_la_correction_l_emporte_et_tri_par_date():
    p = suivis([element("comté", J(-30)), element("salade", J(-1))], [], {}, {"comte": J(9)})
    assert [(x["cle"], x["jusqu_au"]) for x in p] == [("salade", J(-1) + timedelta(days=4)), ("comte", J(9))]


def test_suivis_un_produit_du_placard_et_habituel_compte_une_fois():
    p = suivis([element("jambon", J(-1))], [habituel("jambon")], {}, {})
    assert len(p) == 1 and p[0]["origine"] == "placard"


# --- état ---

def test_etat():
    assert etat(J(-1), AUJ) == "a-verifier"
    assert etat(AUJ, AUJ) == "a-finir" and etat(J(A_FINIR_JOURS), AUJ) == "a-finir"
    assert etat(J(A_FINIR_JOURS + 1), AUJ) is None


# --- couverture par les repas prévus ---

POULET = plat("plat-poulet-01", "Poulet rôti", ["cuisses de poulet", "thym"])
SALADE = plat("plat-salade-01", "Salade César", ["salade", "cuisses de poulet", "parmesan"], minutes=15)
PAR_ID = {p["id"]: p for p in (POULET, SALADE)}


def test_couverture():
    assert utilise(POULET, "cuisses de poulet") and not utilise(POULET, "salade")
    assert couverture("cuisses de poulet", J(1), [repas(J(1), POULET["id"])], PAR_ID, AUJ) == (True, None)
    assert couverture("cuisses de poulet", J(1), [repas(J(3), POULET["id"]), repas(J(2), SALADE["id"])],
                      PAR_ID, AUJ) == (False, J(2))
    assert couverture("cuisses de poulet", J(1), [], PAR_ID, AUJ) == (False, None)
    vecu = [repas(AUJ, POULET["id"], issue="commande"), repas(J(1), POULET["id"], moment="dejeuner")]
    assert couverture("cuisses de poulet", J(1), vecu, PAR_ID, AUJ) == (True, None)       # le déjeuner compte
    assert couverture("cuisses de poulet", J(1), vecu[:1], PAR_ID, AUJ) == (False, None)  # vécu : ne compte pas


# --- suggestions ---

def test_suggestions_filtres_tri_et_maximum():
    plats = [POULET, SALADE,
             plat("plat-poulet-02", "Poulet curry", ["cuisses de poulet", "curry", "lait de coco"], minutes=30),
             plat("plat-poulet-03", "Poulet basquaise", ["cuisses de poulet", "poivrons"], minutes=40),
             plat("plat-poulet-jul", "Poulet piquant", ["cuisses de poulet"], pour="julien"),
             plat("plat-poulet-arc", "Vieux poulet", ["cuisses de poulet"], archive=True),
             plat("plat-poulet-tst", "Poulet à tester", ["cuisses de poulet"], statut="a-tester"),
             plat("acc-poulet-001", "Accompagnement", ["cuisses de poulet"], genre="accompagnement")]
    stock = {"cuisses de poulet", "thym", "salade", "parmesan", "curry"}
    s = suggestions("cuisses de poulet", ["cuisses de poulet", "salade"], plats, stock)
    assert [x["plat"]["id"] for x in s] == ["plat-salade-01", "plat-poulet-01", "plat-poulet-02"]
    assert s[0]["manquants"] == [] and s[2]["manquants"] == ["lait de coco"]


# --- jour libre ---

def test_jour_libre():
    assert jour_libre([], AUJ, J(2)) == AUJ
    assert jour_libre([repas(AUJ, "plat-x-000001"), repas(J(1), issue="dehors")], AUJ, J(2)) == J(2)
    assert jour_libre([repas(AUJ, "plat-x-000001", moment="dejeuner")], AUJ, J(1)) == AUJ
    assert jour_libre([repas(AUJ, "plat-x-000001")], AUJ, AUJ) is None


# --- alertes ---

def test_alertes():
    produits = [{"cle": "steaks haches", "nom": "steaks hachés", "origine": "placard", "jusqu_au": J(-1)},
                {"cle": "cuisses de poulet", "nom": "cuisses de poulet", "origine": "placard", "jusqu_au": J(1)},
                {"cle": "salade", "nom": "salade", "origine": "placard", "jusqu_au": J(2)},
                {"cle": "comte", "nom": "comté", "origine": "placard", "jusqu_au": J(20)}]
    a = alertes(produits, [repas(J(4), POULET["id"]), repas(J(1), SALADE["id"]), repas(AUJ, "plat-autre-01")],
                [POULET, SALADE], {"thym", "parmesan"}, AUJ)
    # la salade est utilisée demain (Salade César) : couverte ; le poulet aussi (même repas) ; le comté : loin
    assert [(x["cle"], x["etat"]) for x in a] == [("steaks haches", "a-verifier")]
    assert a[0]["suggestions"] == [] and a[0]["jour"] is None and a[0]["trop_tard"] is None

    b = alertes(produits[:2], [repas(J(4), POULET["id"]), repas(AUJ, "plat-autre-01")], [POULET, SALADE],
                {"thym", "salade", "parmesan"}, AUJ)
    poulet = b[1]
    assert poulet["cle"] == "cuisses de poulet" and poulet["etat"] == "a-finir" and poulet["trop_tard"] == J(4)
    assert [x["plat"]["id"] for x in poulet["suggestions"]] == ["plat-salade-01", "plat-poulet-01"]
    assert poulet["jour"] == J(1)                                     # ce soir est déjà pris


def test_plats_qui_utilisent():
    assert plats_qui_utilisent([POULET, SALADE], {"salade"}) == ["plat-salade-01"]
    assert plats_qui_utilisent([POULET, SALADE], set()) == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd voyage && .venv/bin/python3 -m pytest test_a_finir.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'a_finir'`

- [ ] **Step 3: Write the implementation** — `voyage/a_finir.py`

```python
"""Casa Binomerie — À finir : ce qu'il faut manger avant que ça tourne, sans rien saisir
(spec docs/superpowers/specs/2026-11-03-casa-a-finir-design.md).

- suivis : le frais du frigo (placard de zone frigo en stock, habituels rangés de zone frigo) et sa date « à finir
  avant » : la correction s'il y en a une, sinon la date d'entrée (dernier achat, remise en stock) + la durée ;
- alertes (page Aujourd'hui) : à vérifier (date passée), et à finir d'ici A_FINIR_JOURS qu'aucun repas prévu n'utilise
  à temps, avec les plats du carnet qui l'utilisent et le premier soir libre pour en poser un.
"""
from datetime import date, timedelta

from conservation import duree
from courses import normaliser, deviner_zone

A_FINIR_JOURS = 2           # à finir d'ici après-demain (aujourd'hui compris) : on le signale
ENCORE_BON_JOURS = 2        # [Encore bon] : deux jours de plus
MAX_SUGGESTIONS = 3

# La reprise du frigo (03/11/2026) : ce qu'on sait déjà, {nom : (acheté le, à finir avant ou None = calculé)}
NOM_REPRISE = "a-finir-v1"
JOUR_REPRISE = date(2026, 11, 3)
FRIGO_CONNU = {"cuisses de poulet": (date(2026, 11, 1), None),
               "galettes de sarrasin": (date(2026, 11, 3), date(2026, 11, 9))}     # date imprimée


def suivis(placard, courses, derniers_achats, corrections):
    """Le frais du frigo daté, trié par date puis nom : [{cle, nom, origine ('placard' | 'habituel'), jusqu_au}].
    Sans date d'entrée ni correction (un habituel jamais acheté depuis le journal) : pas suivi."""
    produits = {}
    for p in placard:
        if p["en_stock"] and p["zone"] == "frigo":
            produits[p["cle"]] = ({"cle": p["cle"], "nom": p["nom"], "origine": "placard"}, p["entre_le"])
    for a in courses:
        cle = normaliser(a["nom"])
        if (a["recurrent"] and (not a["actif"] or a["pris"]) and cle not in produits
                and deviner_zone(a["nom"]) == "frigo"):
            produits[cle] = ({"cle": cle, "nom": a["nom"], "origine": "habituel"}, None)
    resultat = []
    for cle, (p, entre_le) in produits.items():
        dates = [d for d in (entre_le, derniers_achats.get(cle)) if d]
        if cle in corrections:
            jusqu_au = corrections[cle]
        elif dates:
            jusqu_au = max(dates) + timedelta(days=duree(p["nom"]))
        else:
            continue
        resultat.append({**p, "jusqu_au": jusqu_au})
    return sorted(resultat, key=lambda p: (p["jusqu_au"], p["nom"]))


def etat(jusqu_au, aujourd_hui):
    """'a-verifier' (date passée), 'a-finir' (d'ici A_FINIR_JOURS), ou None."""
    if jusqu_au < aujourd_hui:
        return "a-verifier"
    if jusqu_au <= aujourd_hui + timedelta(days=A_FINIR_JOURS):
        return "a-finir"
    return None


def utilise(plat, cle):
    return any(normaliser(i) == cle for i in plat["ingredients"])


def couverture(cle, jusqu_au, repas, par_id, aujourd_hui):
    """(couvert, trop tard) : un repas prévu (sans issue, tous moments) d'aujourd'hui à jusqu_au l'utilise ; sinon,
    le premier jour prévu après jusqu_au qui l'utilise, ou None."""
    jours = sorted(r["jour"] for r in repas if not r["issue"] and r["jour"] >= aujourd_hui
                   and any(i in par_id and utilise(par_id[i], cle) for i in r["plats"]))
    if any(j <= jusqu_au for j in jours):
        return True, None
    return False, (jours[0] if jours else None)


def suggestions(cle, cles_a_finir, plats, stock):
    """Les plats du carnet pour nous deux qui utilisent le produit : ceux qui finissent le plus de produits d'abord,
    puis ceux à qui il manque le moins, puis les plus rapides. [{plat, manquants}], MAX_SUGGESTIONS au plus."""
    resultat = []
    for p in plats:
        if (p["genre"] == "plat" and p["statut"] == "carnet" and not p["archive"]
                and p.get("pour", "nous") == "nous" and utilise(p, cle)):
            manquants = [i for i in p["ingredients"] if normaliser(i) not in stock]
            finis = sum(1 for c in cles_a_finir if utilise(p, c))
            resultat.append(((-finis, len(manquants), p["minutes"], p["nom"]), {"plat": p, "manquants": manquants}))
    return [s for _, s in sorted(resultat, key=lambda x: x[0])][:MAX_SUGGESTIONS]


def jour_libre(repas, aujourd_hui, jusqu_au):
    """Le premier soir d'aujourd'hui à jusqu_au sans dîner (ni plat ni issue), ou None."""
    pris = {r["jour"] for r in repas if r["moment"] == "diner" and (r["plats"] or r["issue"])}
    jour = aujourd_hui
    while jour <= jusqu_au:
        if jour not in pris:
            return jour
        jour += timedelta(days=1)
    return None


def alertes(produits, repas, plats, stock, aujourd_hui):
    """Ce que la page Aujourd'hui signale : les produits à vérifier (sans plats : [Fini] ou [Encore bon] d'abord), et
    les produits à finir qu'aucun repas prévu n'utilise à temps (trop_tard : le jour où il est prévu, trop tard), avec
    leurs plats suggérés et le premier soir libre. À vérifier d'abord, puis par date."""
    par_id = {p["id"]: p for p in plats}
    signales = [(p, etat(p["jusqu_au"], aujourd_hui)) for p in produits]
    signales = [(p, e) for p, e in signales if e]
    cles = [p["cle"] for p, _ in signales]
    resultat = []
    for p, e in signales:
        if e == "a-verifier":
            resultat.append({**p, "etat": e, "trop_tard": None, "suggestions": [], "jour": None})
            continue
        couvert, trop_tard = couverture(p["cle"], p["jusqu_au"], repas, par_id, aujourd_hui)
        if not couvert:
            resultat.append({**p, "etat": e, "trop_tard": trop_tard,
                             "suggestions": suggestions(p["cle"], cles, plats, stock),
                             "jour": jour_libre(repas, aujourd_hui, p["jusqu_au"])})
    return sorted(resultat, key=lambda a: (a["etat"] != "a-verifier", a["jusqu_au"], a["nom"]))


def plats_qui_utilisent(plats, cles):
    """Les ids des plats qui utilisent au moins un de ces produits (badge « à finir » de la page Dîners)."""
    return [p["id"] for p in plats if any(utilise(p, c) for c in cles)]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd voyage && .venv/bin/python3 -m pytest test_a_finir.py -q`
Expected: `13 passed`. Note sur `test_alertes` (premier appel) : le poulet est couvert parce que la Salade César de demain contient « cuisses de poulet » — c'est voulu.

- [ ] **Step 5: Commit**

```bash
git add voyage/a_finir.py voyage/test_a_finir.py
git commit -m "feat: Casa Binomerie — À finir : frais suivi et daté, repas prévus, plats suggérés

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 3: La base — table, lecture, corrections, reprise

**Files:**
- Modify: `voyage/schema.sql` (à la fin du fichier)
- Modify: `voyage/db.py` (section « Casa Binomerie : courses et placard » : `enregistrer_article`, `enregistrer_placard`, nouvelles fonctions après `lire_achats` ; `dater_frigo` à la fin du fichier)
- Modify: `voyage/appliquer_schema.py`
- Test: `voyage/test_a_finir_db.py`

**Interfaces:**
- Consumes: `a_finir.suivis`, `a_finir.NOM_REPRISE`, `a_finir.JOUR_REPRISE`, `a_finir.FRIGO_CONNU` (tâche 2) ; `conservation.duree` (tâche 1).
- Produces :
  - `db.lire_frais(conn) -> {"placard": [{"cle","nom","en_stock","zone","entre_le"}], "derniers_achats": {cle: date}, "corrections": {cle: date}}` (placard : zone frigo seulement).
  - `db.finir(conn, cle) -> bool` (commit).
  - `db.corriger_a_finir(conn, cle, jusqu_au)` (commit).
  - `db.dater_frigo(conn, nom_reprise, jour, connus) -> {cle: jusqu_au} | None` (sans commit).

- [ ] **Step 1: Write the failing tests** — `voyage/test_a_finir_db.py`

```python
"""Tests d'À finir en base (db.py) : lecture du frais, corrections, [Fini], reprise du frigo."""
import sys
from datetime import date, timedelta
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pytest
from db import (connecter, enregistrer_article, enregistrer_placard, lire_courses, lire_frais, finir,
                corriger_a_finir, dater_frigo)
from conservation import duree

JOUR = date(2026, 11, 3)


def article(id_, nom, **reste):
    return {"id": id_, "nom": nom, "rayon": "frais", "pris": False, "recurrent": False, "actif": True,
            "source": "", **reste}


def element(nom, en_stock=True, zone="frigo"):
    from courses import normaliser
    return {"cle": normaliser(nom), "nom": nom, "en_stock": en_stock, "bientot": False, "zone": zone}


@pytest.fixture
def conn():
    c = connecter("valise_test")
    with c.cursor() as cur:
        cur.execute("TRUNCATE courses, placard, achats, a_finir")
        cur.execute("DELETE FROM reprises WHERE nom = 'a-finir-test'")
    c.commit()
    yield c
    c.close()


def aujourd_hui(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT (now() AT TIME ZONE 'Europe/Paris')::date")
        return cur.fetchone()[0]


def test_lire_frais(conn):
    enregistrer_placard(conn, element("steaks hachés"))
    enregistrer_placard(conn, element("riz", zone="placard-sec"))
    enregistrer_article(conn, article("jamb-0001", "jambon", pris=True))
    corriger_a_finir(conn, "comte", JOUR)
    f = lire_frais(conn)
    assert [(p["cle"], p["entre_le"]) for p in f["placard"]] == [("steaks haches", aujourd_hui(conn))]
    assert f["derniers_achats"] == {"jambon": aujourd_hui(conn)} and f["corrections"] == {"comte": JOUR}


def test_corriger_remplace(conn):
    corriger_a_finir(conn, "comte", JOUR)
    corriger_a_finir(conn, "comte", JOUR + timedelta(days=2))
    assert lire_frais(conn)["corrections"] == {"comte": JOUR + timedelta(days=2)}


def test_fini_sort_du_stock_ou_remet_l_habituel_sur_la_liste(conn):
    enregistrer_placard(conn, element("steaks hachés"))
    enregistrer_article(conn, article("mozz-0001", "mozzarella", recurrent=True, actif=False))
    corriger_a_finir(conn, "steaks haches", JOUR)
    assert finir(conn, "steaks haches") and finir(conn, "mozzarella")
    lu = lire_courses(conn)
    assert not lu["placard"][0]["en_stock"] and lu["articles"][0]["actif"] and not lu["articles"][0]["pris"]
    assert lire_frais(conn)["corrections"] == {}
    assert not finir(conn, "inconnu")


def test_le_rachat_et_la_remise_en_stock_effacent_la_correction(conn):
    enregistrer_placard(conn, element("lardons", en_stock=False))
    corriger_a_finir(conn, "lardons", JOUR)
    corriger_a_finir(conn, "jambon", JOUR)
    corriger_a_finir(conn, "comte", JOUR)
    enregistrer_placard(conn, element("lardons"))                       # remis en stock
    enregistrer_article(conn, article("jamb-0001", "jambon", pris=True))  # racheté
    enregistrer_placard(conn, element("comté"))                         # pas en stock avant : nouveau
    assert lire_frais(conn)["corrections"] == {}
    corriger_a_finir(conn, "comte", JOUR)
    enregistrer_placard(conn, {**element("comté"), "bientot": True})    # déjà en stock : la correction reste
    assert lire_frais(conn)["corrections"] == {"comte": JOUR}


def test_dater_frigo_une_seule_fois(conn):
    enregistrer_article(conn, article("beur-0001", "beurre", recurrent=True, actif=False))
    enregistrer_article(conn, article("lait-0001", "lait", recurrent=True, actif=True))       # sur la liste
    enregistrer_article(conn, article("jamb-0001", "jambon", recurrent=True, pris=True))      # acheté : daté
    enregistrer_article(conn, article("citr-0001", "citrons", recurrent=True, actif=False))   # pas au frigo
    connus = {"cuisses de poulet": (date(2026, 11, 1), None), "galettes de sarrasin": (JOUR, date(2026, 11, 9))}
    dates = dater_frigo(conn, "a-finir-test", JOUR, connus)
    assert dates == {"cuisses de poulet": date(2026, 11, 3), "galettes de sarrasin": date(2026, 11, 9),
                     "beurre": JOUR + timedelta(days=duree("beurre"))}
    conn.commit()
    assert lire_frais(conn)["corrections"] == dates
    assert {p["cle"] for p in lire_courses(conn)["placard"] if p["en_stock"]} == {"cuisses de poulet",
                                                                                   "galettes de sarrasin"}
    assert dater_frigo(conn, "a-finir-test", JOUR, connus) is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd voyage && .venv/bin/python3 -m pytest test_a_finir_db.py -q`
Expected: FAIL — `ImportError: cannot import name 'lire_frais' from 'db'`

- [ ] **Step 3: Add the table** — à la fin de `voyage/schema.sql` :

```sql
-- À finir (03/11/2026) : les dates « à finir avant » corrigées à la main ([Encore bon], reprise du frigo). Effacée
-- quand le produit repart de zéro : racheté, remis en stock, [Fini].
CREATE TABLE IF NOT EXISTS a_finir (
    cle         TEXT        PRIMARY KEY,             -- nom normalisé du produit
    jusqu_au    DATE        NOT NULL
);
```

Puis appliquer à la base de test : `cd voyage && .venv/bin/python3 appliquer_schema.py --base valise_test --appliquer`
Expected: la ligne « Schéma appliqué ; table(s) créée(s) : a_finir … ».

- [ ] **Step 4: Write the db code** — dans `voyage/db.py`

4a. Dans `enregistrer_article`, dans le bloc du journal, effacer la correction au rachat. Remplacer :

```python
        if a["pris"] and not etait_pris:
            from prix_paris import prix_de
            prix = prix_de(a["nom"])
```

par :

```python
        if a["pris"] and not etait_pris:
            from prix_paris import prix_de
            cur.execute("DELETE FROM a_finir WHERE cle = %s", (normaliser(a["nom"]),))    # racheté : repart de zéro
            prix = prix_de(a["nom"])
```

4b. Remplacer `enregistrer_placard` en entier par :

```python
def enregistrer_placard(conn, p):
    """Un élément du placard. Remis en stock alors qu'il ne l'était pas : il repart de zéro (À finir)."""
    with conn.cursor() as cur:
        cur.execute("SELECT en_stock FROM placard WHERE cle = %s", (p["cle"],))
        avant = cur.fetchone()
        if p["en_stock"] and not (avant and avant[0]):
            cur.execute("DELETE FROM a_finir WHERE cle = %s", (p["cle"],))
        cur.execute("""INSERT INTO placard (cle, nom, en_stock, bientot, zone) VALUES (%s, %s, %s, %s, %s)
                       ON CONFLICT (cle) DO UPDATE SET nom = EXCLUDED.nom, en_stock = EXCLUDED.en_stock,
                       bientot = EXCLUDED.bientot, zone = EXCLUDED.zone, maj_le = now()""",
                    (p["cle"], p["nom"], p["en_stock"], p["bientot"], p["zone"]))
    conn.commit()
```

4c. Juste après `lire_achats`, ajouter :

```python
def lire_frais(conn):
    """De quoi dater le frais (a_finir.suivis) : le placard du frigo avec sa date d'entrée (dernière mise à jour, à
    Paris), le dernier achat de chaque produit {clé : jour}, les dates corrigées {clé : jusqu_au}."""
    from courses import normaliser
    with conn.cursor() as cur:
        cur.execute("""SELECT cle, nom, en_stock, zone, (maj_le AT TIME ZONE 'Europe/Paris')::date FROM placard
                       WHERE zone = 'frigo' ORDER BY nom""")
        placard = [dict(zip(("cle", "nom", "en_stock", "zone", "entre_le"), ligne)) for ligne in cur.fetchall()]
        cur.execute("SELECT nom, max(jour) FROM achats GROUP BY nom")
        derniers = {}
        for nom, jour in cur.fetchall():
            cle = normaliser(nom)
            derniers[cle] = max(jour, derniers.get(cle, jour))
        cur.execute("SELECT cle, jusqu_au FROM a_finir")
        corrections = dict(cur.fetchall())
    return {"placard": placard, "derniers_achats": derniers, "corrections": corrections}


def finir(conn, cle):
    """[Fini] : l'élément du placard n'est plus en stock ; sinon l'habituel revient sur la liste, comme quand il en
    manque. Sa date corrigée part. False si aucun des deux ne correspond."""
    from courses import normaliser
    with conn.cursor() as cur:
        cur.execute("""UPDATE placard SET en_stock = false, bientot = false, maj_le = now()
                       WHERE cle = %s AND en_stock""", (cle,))
        trouve = cur.rowcount > 0
        if not trouve:
            cur.execute("SELECT id, nom FROM courses WHERE recurrent")
            ids = [i for i, nom in cur.fetchall() if normaliser(nom) == cle]
            if ids:
                cur.execute("UPDATE courses SET actif = true, pris = false, maj_le = now() WHERE id = ANY(%s)", (ids,))
                trouve = True
        cur.execute("DELETE FROM a_finir WHERE cle = %s", (cle,))
    conn.commit()
    return trouve


def corriger_a_finir(conn, cle, jusqu_au):
    """La date « à finir avant » d'un produit, corrigée ([Encore bon])."""
    with conn.cursor() as cur:
        cur.execute("""INSERT INTO a_finir (cle, jusqu_au) VALUES (%s, %s)
                       ON CONFLICT (cle) DO UPDATE SET jusqu_au = EXCLUDED.jusqu_au""", (cle, jusqu_au))
    conn.commit()
```

4d. À la fin de `voyage/db.py`, ajouter :

```python
def dater_frigo(conn, nom_reprise, jour, connus):
    """La reprise À finir, une seule fois (table reprises) : ce qu'on sait du frigo (`connus`, {nom : (acheté le, à
    finir avant ou None)}) entre au placard, en stock, avec sa date ; les habituels du frigo rangés jamais achetés
    depuis le journal partent de `jour`. Sans commit : l'appelant valide ou annule (à blanc).
    Renvoie {clé : jusqu_au} des produits datés, ou None si c'est déjà fait."""
    from datetime import timedelta
    from conservation import duree
    from courses import normaliser, deviner_zone
    with conn.cursor() as cur:
        cur.execute("SELECT EXISTS (SELECT 1 FROM reprises WHERE nom = %s)", (nom_reprise,))
        if cur.fetchone()[0]:
            return None
        dates = {}
        for nom, (achete_le, jusqu_au) in connus.items():
            cle = normaliser(nom)
            cur.execute("""INSERT INTO placard (cle, nom, zone, en_stock) VALUES (%s, %s, 'frigo', true)
                           ON CONFLICT (cle) DO UPDATE SET en_stock = true, bientot = false""", (cle, nom))
            dates[cle] = jusqu_au or achete_le + timedelta(days=duree(nom))
        frais = lire_frais(conn)
        en_stock = {p["cle"] for p in frais["placard"] if p["en_stock"]}
        for a in lire_courses(conn)["articles"]:
            cle = normaliser(a["nom"])
            if (a["recurrent"] and (not a["actif"] or a["pris"]) and deviner_zone(a["nom"]) == "frigo"
                    and cle not in frais["derniers_achats"] and cle not in en_stock and cle not in dates):
                dates[cle] = jour + timedelta(days=duree(a["nom"]))
        for cle, jusqu_au in dates.items():
            cur.execute("""INSERT INTO a_finir (cle, jusqu_au) VALUES (%s, %s)
                           ON CONFLICT (cle) DO UPDATE SET jusqu_au = EXCLUDED.jusqu_au""", (cle, jusqu_au))
        cur.execute("INSERT INTO reprises (nom) VALUES (%s)", (nom_reprise,))
    return dates
```

- [ ] **Step 5: Wire the reprise** — dans `voyage/appliquer_schema.py`

5a. Imports : ajouter `dater_frigo` à l'import depuis `db`, et la ligne :

```python
from a_finir import NOM_REPRISE as REPRISE_A_FINIR, JOUR_REPRISE, FRIGO_CONNU
```

5b. Branche `--appliquer` : juste après `accords = poser_accords(conn, NOM_REPRISE_ACCORDS, ACCORDS)    # après l'ajout : ils existent`, ajouter :

```python
        frigo = dater_frigo(conn, REPRISE_A_FINIR, JOUR_REPRISE, FRIGO_CONNU)    # une seule fois
```

et après le dernier `print` de cette branche (`Accords : … plat(s) avec leurs accompagnements.`) :

```python
        if frigo is not None:
            print(f"À finir : {len(frigo)} produit(s) du frigo datés : "
                  + ", ".join(f"{cle} {d:%d/%m}" for cle, d in sorted(frigo.items())) + ".")
```

5c. Branche à blanc : juste après `accords = poser_accords(conn, NOM_REPRISE_ACCORDS, ACCORDS)` (avant `conn.rollback()`), ajouter :

```python
        frigo = dater_frigo(conn, REPRISE_A_FINIR, JOUR_REPRISE, FRIGO_CONNU)
```

et à la fin de la branche :

```python
        if frigo is not None:
            print(f"À blanc, À finir : {len(frigo)} produit(s) du frigo à dater : "
                  + ", ".join(f"{cle} {d:%d/%m}" for cle, d in sorted(frigo.items())) + ".")
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `cd voyage && .venv/bin/python3 -m pytest test_a_finir_db.py test_courses_db.py -q`
Expected: tout passe (`5 passed` pour le nouveau fichier).

- [ ] **Step 7: Full suite and commit**

Run: `cd voyage && .venv/bin/python3 -m pytest -q 2>&1 | tail -2` — attendu : `... passed`, 0 failed.

```bash
git add voyage/schema.sql voyage/db.py voyage/appliquer_schema.py voyage/test_a_finir_db.py
git commit -m "feat: Casa Binomerie — À finir : table des corrections, lecture du frais, Fini, reprise du frigo

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 4: Faisable tout de suite et Proposer servent d'abord ce qui est à finir

**Files:**
- Modify: `voyage/diners.py` (`secours`, `proposer`)
- Test: `voyage/test_diners.py` (ajouts en fin de fichier)

**Interfaces:**
- Consumes: rien des tâches précédentes (les clés à finir arrivent en paramètre, normalisées).
- Produces :
  - `secours(plats, placard, courses=(), a_finir=())` — `a_finir` : ensemble de clés normalisées ; à nombre de manquants égal (faisables, puis presque), les plats qui en utilisent passent en tête.
  - `proposer(plats, repas, jours, aujourd_hui, remplacer=(), cible=CIBLE_SOIRS, hasard=None, a_finir=())` — `a_finir` : liste de `(cle, jusqu_au)`.

- [ ] **Step 1: Write the failing tests** — à la fin de `voyage/test_diners.py`

```python
# --- À finir : d'abord ce qui va tourner ---

def test_secours_met_en_tete_ce_qui_finit_un_produit():
    plats = [plat("plat-omelette", "Omelette", minutes=10, ingredients=["œufs"]),
             plat("plat-salade-1", "Salade jambon", minutes=15, ingredients=["salade", "jambon"])]
    stock = placard("œufs", "salade", "jambon")
    assert [p["id"] for p in secours(plats, stock)[0]] == ["plat-omelette", "plat-salade-1"]
    assert [p["id"] for p in secours(plats, stock, a_finir={"jambon"})[0]] == ["plat-salade-1", "plat-omelette"]


def test_proposer_place_d_abord_un_plat_qui_finit_un_produit():
    plats = carte() + [{**plat("plat-poulet-01", "Poulet rôti", minutes=40, ingredients=["cuisses de poulet"]),
                        "recette": "1.", "pour": "nous"},
                       {**plat("plat-poulet-02", "Poulet lent", minutes=90, ingredients=["cuisses de poulet"]),
                        "recette": "1.", "pour": "nous"}]
    mar = LUN + timedelta(days=1)
    for graine in range(10):
        p = proposer(plats, [diner(LUN, "plat-carnet-00")], SEMAINE, LUN, hasard=Random(graine),
                     a_finir=[("cuisses de poulet", mar)])
        assert p[mar] == "plat-poulet-01" and len(p) == 3           # lundi déjà pris : mardi, ≤ 45 min


def test_proposer_a_finir_respecte_reproposer_et_la_cible():
    plats = carte() + [{**plat("plat-poulet-01", "Poulet rôti", minutes=40, ingredients=["cuisses de poulet"]),
                        "recette": "1.", "pour": "nous"}]
    p = proposer(plats, [], SEMAINE, LUN, hasard=Random(3))
    jour = sorted(p)[-1]
    soirs = [diner(j, v) for j, v in p.items()]
    q = proposer(plats, soirs, SEMAINE, LUN, remplacer=[jour], hasard=Random(4),
                 a_finir=[("cuisses de poulet", LUN + timedelta(days=1))])
    assert list(q) == [jour]                                         # Reproposer ne touche qu'au jour demandé
    plein = [diner(LUN + timedelta(days=i), f"plat-carnet-{i:02d}") for i in range(4)]
    assert proposer(plats, plein, SEMAINE, LUN, a_finir=[("cuisses de poulet", LUN + timedelta(days=5))]) == {}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd voyage && .venv/bin/python3 -m pytest test_diners.py -q -k "finit or a_finir"`
Expected: FAIL — `TypeError: secours() got an unexpected keyword argument 'a_finir'` (et idem pour `proposer`).

- [ ] **Step 3: Update `secours`** — remplacer la fonction par :

```python
def secours(plats, placard, courses=(), a_finir=()):
    """(faisables, presque) : plats du carnet ≤ SECOURS_MINUTES, tout disponible / 1-2 manquants. `a_finir` : les
    clés des produits à finir (a_finir.py) ; les plats qui en utilisent passent en tête."""
    stock = disponibles(placard, courses)
    faisables, presque = [], []
    candidats = sorted((p for p in plats if p["genre"] == "plat" and p["statut"] == "carnet" and not p["archive"]
                        and p["minutes"] <= SECOURS_MINUTES and p["ingredients"]),
                       key=lambda p: (not any(normaliser(i) in a_finir for i in p["ingredients"]), p["minutes"], p["nom"]))
    for p in candidats:
        manquants = [i for i in p["ingredients"] if normaliser(i) not in stock]
        if not manquants:
            faisables.append(p)
        elif len(manquants) <= 2:
            presque.append({"plat": p, "manquants": manquants})
    return faisables, presque
```

- [ ] **Step 4: Update `proposer`** — signature et docstring :

```python
def proposer(plats, repas, jours, aujourd_hui, remplacer=(), cible=CIBLE_SOIRS, hasard=None, a_finir=()):
    """{jour: id du plat} pour compléter la semaine jusqu'à `cible` dîners prévus.

    Dîners libres seulement (ni plat ni issue), vendredi et samedi en dernier recours (souvent dehors), répartis
    dans la semaine. Plats pour nous deux, avec recette ; rapides (≤ 45 min) du lundi au jeudi ; ni déjà prévus
    (tous moments), ni mangés ces 14 derniers jours, ni brunchs ; un plat à tester s'il n'y en a pas déjà un. `remplacer` :
    des jours à tirer au sort de nouveau, avec un autre plat (s'ils sont encore tels que proposés). `a_finir` :
    [(clé, à finir avant)] des produits qu'aucun repas prévu n'utilise à temps (a_finir.alertes) — pour chacun, d'abord,
    le plus rapide des plats du carnet qui l'utilisent, au premier soir à remplir avant sa date (avec Reproposer,
    seulement sur les jours à remplacer). L'accompagnement : voir accompagner. Déjeuners et brunchs ne remplissent
    pas un soir."""
```

Puis remplacer le corps, de la ligne `besoin = max(0, cible - len(prevus))` jusqu'à `return dict(sorted(choix.items()))` inclus, par :

```python
    besoin = max(0, cible - len(prevus))
    libres = [j for j in jours if j not in prevus and j not in remplacer
              and not (j in diners and diners[j]["issue"])]

    manges = {i for r in repas if r["issue"] == "fait" and 0 <= (aujourd_hui - r["jour"]).days < RECENT
              for i in r["plats"]}
    deja = {i for r in repas if r["jour"] in jours and r["jour"] not in remplacer for i in r["plats"]}
    exclus = deja | manges | {i for j in remplacer if j in diners for i in diners[j]["plats"]}
    candidats = [p for p in plats if p["genre"] == "plat" and not p["archive"] and p.get("pour", "nous") == "nous"
                 and p["recette"] and p["id"] not in exclus and not p["id"].startswith("brunch-")]
    hasard.shuffle(candidats)
    a_tester = any(p["statut"] == "a-tester" and p["genre"] == "plat" for p in plats if p["id"] in deja)

    choix = {}
    possibles = sorted(remplacer[:besoin]) if remplacer else libres         # anti-gaspi : où poser un plat à finir
    for cle, jusqu_au in sorted(a_finir, key=lambda x: (x[1], x[0])):
        if len(choix) >= besoin:
            break
        for j in possibles:
            if j > jusqu_au or j in choix:
                continue
            p = next((p for p in sorted(candidats, key=lambda p: (p["minutes"], p["nom"]))
                      if p["statut"] == "carnet" and p["id"] not in choix.values()
                      and any(normaliser(i) == cle for i in p["ingredients"])
                      and not (j.weekday() < 4 and p["minutes"] > MINUTES_SEMAINE)), None)
            if p:
                choix[j] = p["id"]
                break

    restant = besoin - len(choix)
    a_remplir = [j for j in remplacer if j not in choix][:restant]
    reste = restant - len(a_remplir)
    preferes = [j for j in libres if j.weekday() not in (4, 5) and j not in choix]
    autres = [j for j in libres if j.weekday() in (4, 5) and j not in choix]
    if reste > 0:
        if len(preferes) > reste:                       # répartis : au milieu de chaque tranche, pas d'affilée
            a_remplir += [preferes[(2 * i + 1) * len(preferes) // (2 * reste)] for i in range(reste)]
        else:
            a_remplir += preferes + autres[:reste - len(preferes)]
    if not a_remplir and not choix:
        return {}

    for j in sorted(a_remplir, key=lambda j: j.weekday() != 6):     # le plat à tester, le dimanche s'il y en a un
        rapide = j.weekday() < 4
        ordre = sorted(candidats, key=lambda p: (p["statut"] == "a-tester") == a_tester)
        for p in ordre:
            if p["id"] in choix.values() or (rapide and p["minutes"] > MINUTES_SEMAINE):
                continue
            choix[j] = p["id"]
            a_tester = a_tester or p["statut"] == "a-tester"
            break
    return dict(sorted(choix.items()))
```

(Les lignes `diners = …`, `par_id = …`, `remplacer = …`, `prevus = …` au début de la fonction ne changent pas.)

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd voyage && .venv/bin/python3 -m pytest test_diners.py test_accords.py test_repas.py -q`
Expected: tout passe — les anciens tests de `proposer` (sans `a_finir`) gardent leur comportement exact.

- [ ] **Step 6: Commit**

```bash
git add voyage/diners.py voyage/test_diners.py
git commit -m "feat: Casa Binomerie — À finir : Faisable tout de suite et Proposer servent d'abord ce qui va tourner

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 5: Serveur, page Aujourd'hui, badge Dîners

**Files:**
- Modify: `voyage/serveur.py` (imports ; nouvelle fonction `alertes_du_frigo` après `articles_et_achats_recents` ; route `/` ; `api/diners` ; `api/diners/proposer` ; nouvelle route `api/a-finir/<cle>`)
- Modify: `voyage/casa.py` (style, `bloc_a_finir`, `SCRIPT_A_FINIR`, `aujourdhui_en_html`)
- Modify: `voyage/diners.py` (`lignePlat` dans `SCRIPT_DINERS`)
- Modify: `voyage/valise.py` (`VERSION_PAGE = 43`)
- Test: `voyage/test_casa.py` (ajouts), `voyage/test_a_finir_db.py` (ajouts : routes)

**Interfaces:**
- Consumes: `a_finir.suivis`, `a_finir.alertes`, `a_finir.plats_qui_utilisent`, `a_finir.ENCORE_BON_JOURS` (tâche 2) ; `db.lire_frais`, `db.finir`, `db.corriger_a_finir` (tâche 3) ; `secours(..., a_finir=)`, `proposer(..., a_finir=)` (tâche 4).
- Produces : `casa.bloc_a_finir(alertes, aujourd_hui) -> str` ; `aujourdhui_en_html(..., a_finir=())` ; `POST api/a-finir/<cle>` avec `{"action": "fini" | "encore-bon"}` → 200 `{"ok": true}`, 400 action inconnue, 404 produit non suivi ; `api/diners` renvoie en plus `"a_finir": [ids de plats]`.

- [ ] **Step 1: Write the failing page tests** — à la fin de `voyage/test_casa.py`

```python
# --- À finir ---
from casa import bloc_a_finir


def alerte(nom, jusqu_au, etat="a-finir", trop_tard=None, suggestions=(), jour=None):
    from courses import normaliser
    return {"cle": normaliser(nom), "nom": nom, "origine": "placard", "jusqu_au": jusqu_au, "etat": etat,
            "trop_tard": trop_tard, "suggestions": list(suggestions), "jour": jour}


def test_bloc_a_finir_vide():
    assert bloc_a_finir([], AUJOURD_HUI) == ""


def test_bloc_a_finir():
    demain = AUJOURD_HUI + timedelta(days=1)
    salade = {"id": "plat-salade-01", "nom": "Salade César"}
    html = bloc_a_finir([alerte("steaks hachés", AUJOURD_HUI - timedelta(days=1), etat="a-verifier"),
                         alerte("cuisses de poulet", demain, trop_tard=AUJOURD_HUI + timedelta(days=2),
                                suggestions=[{"plat": salade, "manquants": ["crème"]}], jour=AUJOURD_HUI),
                         alerte("salade", AUJOURD_HUI + timedelta(days=2), suggestions=[{"plat": salade, "manquants": []}])],
                        AUJOURD_HUI)
    assert "À finir" in html and "steaks hachés" in html and "à vérifier" in html
    assert 'data-cle="steaks haches"' in html and 'data-action="encore-bon"' in html
    assert "à finir demain" in html and "prévu vendredi, trop tard" in html          # 28/10/2026 : un mercredi
    assert "Salade César" in html and "il manque : crème" in html
    assert f'data-plat="plat-salade-01" data-jour="{AUJOURD_HUI.isoformat()}">Ce soir</button>' in html
    assert "d'ici vendredi" in html and "rien de prévu" in html and "soirs pris jusqu'à vendredi" in html
    assert html.count('data-action="fini"') == 3 and html.count('data-action="encore-bon"') == 1


def test_page_aujourd_hui_avec_a_finir():
    html = aujourdhui_en_html([], AUJOURD_HUI, a_finir=[alerte("salade", AUJOURD_HUI)])
    assert "bloc-a-finir" in html and "api/a-finir/" in html
    assert "bloc-a-finir" not in aujourdhui_en_html([], AUJOURD_HUI)
```

- [ ] **Step 2: Write the failing route tests** — à la fin de `voyage/test_a_finir_db.py`

```python
# --- Routes ---
from serveur import creer_app


@pytest.fixture
def client(conn):
    with conn.cursor() as cur:
        cur.execute("TRUNCATE plats, repas")
    conn.commit()
    return creer_app("valise_test", secret="").test_client()


def test_api_a_finir(client, conn):
    enregistrer_placard(conn, element("steaks hachés"))
    assert client.post("/api/a-finir/steaks%20haches", json={"action": "encore-bon"}).status_code == 200
    assert lire_frais(conn)["corrections"] == {"steaks haches": aujourd_hui(conn) + timedelta(days=2)}
    assert client.post("/api/a-finir/steaks%20haches", json={"action": "fini"}).status_code == 200
    assert not lire_courses(conn)["placard"][0]["en_stock"]
    assert client.post("/api/a-finir/steaks%20haches", json={"action": "fini"}).status_code == 404   # plus suivi
    assert client.post("/api/a-finir/steaks%20haches", json={"action": "jeter"}).status_code == 400
    assert client.post("/api/a-finir/steaks%20haches", json=["fini"]).status_code == 400


def test_aujourd_hui_et_diners_montrent_ce_qui_est_a_finir(client, conn):
    enregistrer_placard(conn, element("steaks hachés"))           # entré aujourd'hui, 1 jour : à finir demain
    client.post("/api/plats", json={"id": "plat-burger-01", "nom": "Burger", "genre": "plat", "minutes": 15,
                                    "ingredients": ["steaks hachés", "pains burger"], "recette": "1.",
                                    "statut": "carnet"})
    html = client.get("/").get_data(as_text=True)
    assert "bloc-a-finir" in html and "steaks hachés" in html and "Burger" in html
    assert client.get("/api/diners").get_json()["a_finir"] == ["plat-burger-01"]
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `cd voyage && .venv/bin/python3 -m pytest test_casa.py test_a_finir_db.py -q`
Expected: FAIL — `ImportError: cannot import name 'bloc_a_finir'`, et 404 sur `/api/a-finir/…`.

- [ ] **Step 4: Write `casa.py`**

4a. Ajouter à la fin de `STYLE_CASA` (avant le `"""` de fermeture, après la ligne `p.attente …`) :

```css
div.bloc-a-finir { background: var(--carte); border-radius: 24px; padding: 18px 20px; margin: 16px 0; }
div.bloc-a-finir .titre { font-size: 13px; font-weight: 800; letter-spacing: .06em; text-transform: uppercase;
                          color: var(--diners); }
div.bloc-a-finir ul { list-style: none; margin: 8px 0 0; padding: 0; }
div.bloc-a-finir > ul > li { padding: 12px 0; border-top: 1px solid var(--ligne); }
div.bloc-a-finir .produit { display: flex; flex-direction: column; gap: 2px; }
div.bloc-a-finir .produit strong { font-size: 17px; font-weight: 800; }
div.bloc-a-finir .produit span, div.bloc-a-finir p.pris, div.bloc-a-finir small { color: var(--doux); font-size: 14px; }
div.bloc-a-finir .actions { display: flex; gap: 8px; margin: 8px 0 0; }
div.bloc-a-finir button { min-height: 40px; border-radius: 14px; border: 2px solid var(--ligne); background: var(--blanc);
                          color: var(--texte); font-family: inherit; font-weight: 700; font-size: 14px; padding: 0 12px; }
div.bloc-a-finir ul.plats li { display: flex; align-items: center; justify-content: space-between; gap: 8px; padding: 6px 0; }
div.bloc-a-finir ul.plats li span { display: flex; flex-direction: column; min-width: 0; }
div.bloc-a-finir ul.plats button { border-color: var(--diners); color: var(--diners); flex: none; }
div.bloc-a-finir p.pris { margin: 6px 0 0; }
div.bloc-a-finir .message { margin: 8px 0 0; color: var(--diners); font-weight: 700; font-size: 14px; }
```

4b. Après `bloc_compteur`, ajouter :

```python
def _quand(jour, aujourd_hui):
    """« Ce soir », « Demain », ou le jour de la semaine (« Jeudi ») : le libellé d'un bouton."""
    ecart = (jour - aujourd_hui).days
    return "Ce soir" if ecart == 0 else "Demain" if ecart == 1 else JOURS[jour.weekday()].capitalize()


def _a_finir_quand(jusqu_au, aujourd_hui):
    ecart = (jusqu_au - aujourd_hui).days
    return "à finir aujourd'hui" if ecart == 0 else "à finir demain" if ecart == 1 else f"à finir d'ici {JOURS[jusqu_au.weekday()]}"


def bloc_a_finir(alertes, aujourd_hui):
    """Le frais qui va tourner (a_finir.alertes) : à vérifier ([Fini], [Encore bon]) ; à finir sans repas prévu à temps
    ([Fini], et jusqu'à 3 plats du carnet à poser au premier soir libre). Rien à signaler : rien."""
    if not alertes:
        return ""
    lignes = []
    for a in alertes:
        if a["etat"] == "a-verifier":
            etat = "à vérifier"
            boutons = ('<button type="button" data-action="fini">Fini</button>'
                       '<button type="button" data-action="encore-bon">Encore bon</button>')
        else:
            prevu = f'prévu {JOURS[a["trop_tard"].weekday()]}, trop tard' if a["trop_tard"] else "rien de prévu"
            etat = f'{_a_finir_quand(a["jusqu_au"], aujourd_hui)} · {prevu}'
            boutons = '<button type="button" data-action="fini">Fini</button>'
        plats = ""
        if a["suggestions"]:
            items = []
            for s in a["suggestions"]:
                manque = f'<small>il manque : {echapper(", ".join(s["manquants"]))}</small>' if s["manquants"] else ""
                bouton = (f'<button type="button" data-plat="{echapper(s["plat"]["id"])}" '
                          f'data-jour="{a["jour"].isoformat()}">{_quand(a["jour"], aujourd_hui)}</button>'
                          if a["jour"] else "")
                items.append(f'<li><span>{echapper(s["plat"]["nom"])}{manque}</span>{bouton}</li>')
            plats = f'<ul class="plats">{"".join(items)}</ul>'
            if not a["jour"]:
                plats += f'<p class="pris">soirs pris jusqu\'à {JOURS[a["jusqu_au"].weekday()]}</p>'
        lignes.append(f'<li data-cle="{echapper(a["cle"])}"><div class="produit"><strong>{echapper(a["nom"])}</strong>'
                      f'<span>{etat}</span></div><div class="actions">{boutons}</div>{plats}</li>')
    return (f'<div class="bloc-a-finir"><span class="titre">À finir</span><ul>{"".join(lignes)}</ul>'
            f'<p class="message" aria-live="polite"></p></div>')
```

4c. Après `SCRIPT_HIER`, ajouter :

```python
SCRIPT_A_FINIR = """
(function () {
    const bloc = document.querySelector('div.bloc-a-finir');
    if (!bloc) return;
    function envoyer(url, corps) {
        bloc.querySelectorAll('button').forEach(function (x) { x.disabled = true; });
        fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(corps) })
            .then(function (r) { if (!r.ok) throw new Error(r.status); location.reload(); })
            .catch(function () {
                bloc.querySelector('.message').textContent = 'Pas envoyé : réessaie une fois connecté.';
                bloc.querySelectorAll('button').forEach(function (x) { x.disabled = false; });
            });
    }
    bloc.querySelectorAll('button[data-action]').forEach(function (b) {
        b.addEventListener('click', function () {
            const cle = b.closest('li[data-cle]').dataset.cle;
            envoyer('api/a-finir/' + encodeURIComponent(cle), { action: b.dataset.action });
        });
    });
    bloc.querySelectorAll('button[data-plat]').forEach(function (b) {
        b.addEventListener('click', function () {
            envoyer('api/repas', { jour: b.dataset.jour, moment: 'diner', plats: [b.dataset.plat], issue: null });
        });
    });
})();
"""
```

4d. `aujourdhui_en_html` : nouvelle signature et assemblage (le bloc « À finir » juste avant « À acheter pour aujourd'hui »), script ajouté :

```python
def aujourdhui_en_html(voyages, aujourd_hui, a_acheter=(), plats_du_soir=(), diner_hier=None, compte=None,
                       semaine_budget=None, a_finir=()):
    """L'accueil du hub : ce soir, hier soir, ce qui est à finir, ce qu'il faut acheter aujourd'hui, le budget de la
    semaine, le prochain voyage, le compteur Deliveroo."""
    v = prochain_voyage(voyages, aujourd_hui)
    blocs = (bloc_ce_soir(list(plats_du_soir)) + (bloc_hier(diner_hier) if diner_hier else "")
             + bloc_a_finir(list(a_finir), aujourd_hui) + bloc_courses(list(a_acheter))
             + bloc_budget(semaine_budget)
             + (bloc_vadrouille(v, aujourd_hui) if v else "") + bloc_compteur(compte))
```

et dans le gabarit, après `<script>{SCRIPT_HIER}</script>` :

```html
<script>{SCRIPT_A_FINIR}</script>
```

- [ ] **Step 5: Write `serveur.py`**

5a. Imports : ajouter `lire_frais, finir, corriger_a_finir` à l'import existant depuis `db` (ligne `from db import …`), et :

```python
from a_finir import suivis, alertes, plats_qui_utilisent, ENCORE_BON_JOURS
```

5b. Après `articles_et_achats_recents`, ajouter :

```python
def alertes_du_frigo(conn, jour, plats, lu, articles):
    """(produits suivis, alertes du jour) — a_finir.py : le frais daté, et ce qu'aucun repas prévu (d'aujourd'hui à
    FENETRE_FUTUR) n'utilise à temps. `lu` : lire_courses ; `articles` : articles_et_achats_recents."""
    frais = lire_frais(conn)
    produits = suivis(frais["placard"], lu["articles"], frais["derniers_achats"], frais["corrections"])
    a_venir = lire_repas(conn, jour, jour + timedelta(days=FENETRE_FUTUR))
    return produits, alertes(produits, a_venir, plats, disponibles(lu["placard"], articles), jour)
```

5c. Route `/` (accueil) : remplacer le calcul de `html` par (les lignes avant `html = …` ne changent pas) :

```python
                articles = articles_et_achats_recents(conn, lu["articles"], jour, achats)
                _, a_finir = alertes_du_frigo(conn, jour, list(plats.values()), lu, articles)
                html = aujourdhui_en_html(lister_voyages(conn), jour,
                                          a_acheter_aujourd_hui(du_jour, lu["placard"], articles),
                                          ce_soir, hier, compteur(repas, jour), cette_semaine, a_finir)
```

5d. `lire_les_diners` : dans le `try`, après `articles = articles_et_achats_recents(conn, lu["articles"], jour)`, ajouter `_, a_finir = alertes_du_frigo(conn, jour, plats, lu, articles)` ; puis remplacer `faisables, presque = secours(plats, lu["placard"], articles)` par :

```python
        cles_a_finir = {a["cle"] for a in a_finir}
        faisables, presque = secours(plats, lu["placard"], articles, a_finir=cles_a_finir)
```

et ajouter au dictionnaire renvoyé, après la ligne `"secours": …` (avant `"compteur"`) :

```python
            "a_finir": plats_qui_utilisent(plats, cles_a_finir),
```

5e. `proposer_la_semaine` : dans le `try`, après `repas = lire_repas(...)`, ajouter :

```python
            lu = lire_courses(conn)
            _, a_finir = alertes_du_frigo(conn, jour, plats, lu, articles_et_achats_recents(conn, lu["articles"], jour))
```

et remplacer `proposes = proposer(plats, repas, semaine(jour), jour, remplacer=remplacer)` par :

```python
            proposes = proposer(plats, repas, semaine(jour), jour, remplacer=remplacer,
                                a_finir=[(a["cle"], a["jusqu_au"]) for a in a_finir if a["etat"] == "a-finir"])
```

5f. Après la route `retirer_un_basique`, ajouter :

```python
    @routes.post("/api/a-finir/<path:cle>")
    def corriger_un_produit(cle):
        """[Fini] ou [Encore bon] sur un produit du frais suivi (a_finir.py)."""
        corps = request.get_json(silent=True)
        action = corps.get("action") if isinstance(corps, dict) else None
        if action not in ("fini", "encore-bon"):
            return jsonify({"erreur": "action inconnue"}), 400
        jour = aujourd_hui_paris()
        conn = emprunter(app.config["NOM_BASE"])
        try:
            frais = lire_frais(conn)
            produits = suivis(frais["placard"], lire_courses(conn)["articles"], frais["derniers_achats"],
                              frais["corrections"])
            if cle not in {p["cle"] for p in produits}:
                return jsonify({"erreur": "produit non suivi"}), 404
            if action == "fini":
                finir(conn, cle)
            else:
                corriger_a_finir(conn, cle, jour + timedelta(days=ENCORE_BON_JOURS))
        finally:
            conn.close()
        return jsonify({"ok": True})
```

- [ ] **Step 6: Badge Dîners** — dans `voyage/diners.py`, fonction JS `lignePlat` de `SCRIPT_DINERS`, juste après la ligne `if (d.secours.faisables.indexOf(p.id) >= 0) nom.append(el('span', 'badge', 'secours'));` ajouter :

```js
        if ((d.a_finir || []).indexOf(p.id) >= 0) nom.append(el('span', 'badge', 'à finir'));
```

- [ ] **Step 7: VERSION_PAGE** — dans `voyage/valise.py`, `VERSION_PAGE = 42` devient `VERSION_PAGE = 43`.

- [ ] **Step 8: Run tests to verify they pass**

Run: `cd voyage && .venv/bin/python3 -m pytest test_casa.py test_a_finir_db.py test_serveur.py test_diners_db.py -q`
Expected: tout passe.

- [ ] **Step 9: Full suite**

Run: `cd voyage && .venv/bin/python3 -m pytest -q 2>&1 | tail -2` — attendu : `... passed`, 0 failed.

- [ ] **Step 10: Commit**

```bash
git add voyage/serveur.py voyage/casa.py voyage/diners.py voyage/valise.py voyage/test_casa.py voyage/test_a_finir_db.py
git commit -m "feat: Casa Binomerie — À finir sur Aujourd'hui (Fini, Encore bon, plats à poser), badge Dîners, v43

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

## Après les tâches (contrôleur, pas un sous-agent)

1. Revue finale de la branche.
2. Démo : copie de prod en lecture seule dans `valise_copie` (script `copier_prod.py` du scratchpad, en ajoutant `achats` et `a_finir` aux tables copiées), `appliquer_schema.py --base valise_copie --appliquer` (crée `a_finir` et date le frigo), serveur `creer_app('valise_copie', secret='').run(host='0.0.0.0', port=8001)` ; liens Mac et iPhone ; Julien vérifie la liste datée.
3. Neon : à blanc d'abord, `--appliquer` seulement avec le feu vert de Julien ; push/PR/merge seulement à sa demande.
