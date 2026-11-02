# Casa Binomerie — Repas composés, étape 2 (accords et contenu) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Un plat principal porte 2 à 4 accompagnements qui vont avec (« accords ») : ils sont proposés sous lui dans la Semaine, listés sur sa fiche et modifiables. 15 accompagnements et 6 brunchs viennent remplir le carnet « à tester ».

**Architecture:** Une colonne `plats.accords` (JSONB, ids d'accompagnements). `valider_plat` vérifie la forme, la route `api/plats` ne garde que des accompagnements connus et non archivés, `db.enregistrer_plat` ne touche pas aux accords quand une page d'avant les accords n'en envoie pas. Le contenu vit dans `recettes_accompagnements.py`, ajouté une seule fois (reprise `accompagnements-brunch-v1`), et les accords de départ sont posés une seule fois (reprise `accords-v1`) sans écraser ceux réglés dans l'app. Côté page (JS inline de `diners.py`) : « Avec : » sous un plat dans la Semaine, « Va bien avec » et « Modifier les accords » sur la fiche, une étiquette « Brunch ».

**Tech Stack:** Python 3, Flask, psycopg2, Postgres (local `valise_test` pour les tests, Neon en prod), JS ES5 inline dans une chaîne Python, pytest.

Spec : `docs/superpowers/specs/2026-11-01-casa-repas-composes-design.md`, section « Livraison », étape 2.

## Global Constraints

- Tout se passe dans `voyage/`. Tests : `cd voyage && .venv/bin/python3 -m pytest -q` (base locale `valise_test`, jamais Neon).
- TDD : test qui échoue d'abord, puis le code.
- `accords` : ids de plats de genre accompagnement, non archivés ; 6 au plus.
- Un plat principal porte 2 à 4 accompagnements qui vont avec (contenu de départ).
- Contenu : 15 accompagnements, 6 brunchs (étiquette « Brunch »), reprise `accords-v1`.
- Noms d'ingrédients = noms du catalogue (`catalogue.chercher` les trouve) ; sel, poivre et huile sous-entendus.
- Aucun « jamais » de Laetitia dans ce qui est pour nous deux : poissons (`recettes_mer.JAMAIS_LAETITIA`) et légumes (brocoli, chou-fleur, épinards, aubergine, betterave, céleri).
- Une reprise de contenu ne passe qu'une fois (table `reprises`) et n'écrase jamais ce qui a été corrigé dans l'app.
- `VERSION_PAGE` (dans `valise.py`) passe de 37 à 38.
- JS : ES5 comme le reste de `SCRIPT_DINERS` (`function`, `const`/`let` déjà utilisés), et c'est une chaîne Python normale : une apostrophe dans une chaîne JS entre apostrophes s'écrit `\\'`.
- Migration Neon : à blanc d'abord ; `--appliquer` seulement avec l'accord explicite de Julien, avant le merge. Push, PR et merge seulement à sa demande (`env -u GITHUB_TOKEN gh …`).
- Branche : `feat/casa-accords` (déjà créée depuis `main`).

## Fichiers

- Modifier `voyage/schema.sql` : colonne `accords`.
- Modifier `voyage/diners.py` : `MAX_ACCORDS`, `valider_plat` (accords), `nettoyer_accords`, `proposer` (pas de brunch au dîner), JS et CSS.
- Modifier `voyage/db.py` : `CHAMPS_PLAT`, `_DEFAUTS_PLAT`, `_valeurs_plat`, `enregistrer_plat`, nouvelle `poser_accords`.
- Modifier `voyage/serveur.py` : route `api/plats`.
- Créer `voyage/recettes_accompagnements.py` : `ACCOMPAGNEMENTS`, `BRUNCHS`, `ACCORDS`, `JAMAIS_LEGUMES_LAETITIA`, noms de reprise.
- Modifier `voyage/appliquer_schema.py` : les deux reprises.
- Modifier `voyage/valise.py` : `VERSION_PAGE = 38`.
- Tests : créer `voyage/test_accords.py`, `voyage/test_accompagnements.py` ; modifier `voyage/test_diners.py`.

---

### Task 1: La colonne `accords`, sa validation et son enregistrement

**Files:**
- Modify: `voyage/schema.sql` (après la ligne `ALTER TABLE plats ADD CONSTRAINT plats_pour_check …`)
- Modify: `voyage/diners.py` (constantes en tête, `valider_plat`, nouvelle `nettoyer_accords` juste après `valider_plat`)
- Modify: `voyage/db.py:665-683` (`CHAMPS_PLAT`, `_DEFAUTS_PLAT`, `_valeurs_plat`, `enregistrer_plat`)
- Modify: `voyage/serveur.py` (import depuis `diners`, route `POST /api/plats`)
- Test: `voyage/test_accords.py` (nouveau)

**Interfaces:**
- Produces: `diners.MAX_ACCORDS = 6` ; `valider_plat(corps)` renvoie aussi `"accords"` : une liste d'ids, ou `None` si le corps n'a pas de clé `accords` ; `[]` forcé si le genre n'est pas `plat`. `diners.nettoyer_accords(accords, par_id) -> list[str]`. `db.CHAMPS_PLAT` contient `"accords"` ; `db.lire_plats` renvoie `accords` (liste) ; `db.enregistrer_plat(conn, p)` laisse les accords en base intacts quand `p.get("accords") is None`.

- [ ] **Step 1: Écrire les tests qui échouent**

Créer `voyage/test_accords.py` :

```python
"""Tests des accords d'un plat : validation (diners.py), enregistrement (db.py) et route api/plats."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pytest
from carnet_depart import CARNET_DEPART, A_TESTER
from courses import PLACARD_DEPART
from db import connecter, semer_carnet, semer_placard, lire_plats, enregistrer_plat
from diners import valider_plat, nettoyer_accords, MAX_ACCORDS
from serveur import creer_app

STEAK = {"id": "plat-test-steak", "nom": "Steak", "genre": "plat", "minutes": 15}


@pytest.fixture
def conn():
    c = connecter("valise_test")
    with c.cursor() as cur:
        cur.execute("TRUNCATE repas, soirs, plats, courses, placard, reprises")
    c.commit()
    semer_placard(c, PLACARD_DEPART)
    semer_carnet(c, CARNET_DEPART, A_TESTER)
    yield c
    c.close()


@pytest.fixture
def client(conn):
    return creer_app("valise_test", secret="").test_client()


def plats(conn):
    return {p["id"]: p for p in lire_plats(conn)}


# --- Validation ---

def test_valider_plat_accords():
    assert valider_plat(STEAK)["accords"] is None                       # page d'avant les accords : rien à changer
    assert valider_plat({**STEAK, "accords": []})["accords"] == []
    assert valider_plat({**STEAK, "accords": ["acc-puree-robuchon", "af-frites"]})["accords"] == ["acc-puree-robuchon", "af-frites"]
    acc = {**STEAK, "id": "acc-test-puree", "genre": "accompagnement"}
    assert valider_plat({**acc, "accords": ["acc-puree-robuchon"]})["accords"] == []   # seul un plat porte des accords


@pytest.mark.parametrize("accords", [
    "acc-puree-robuchon",                                   # pas une liste
    ["acc-puree-robuchon", 3],                              # pas un id
    ["x"],                                                  # id trop court
    ["acc-puree-robuchon", "acc-puree-robuchon"],           # doublon
    ["plat-test-steak"],                                    # lui-même
    [f"acc-test-{i:02d}" for i in range(MAX_ACCORDS + 1)],  # 7 : trop
])
def test_valider_plat_refuse_des_accords(accords):
    with pytest.raises(ValueError):
        valider_plat({**STEAK, "accords": accords})


def test_nettoyer_accords():
    par_id = {"acc-puree": {"genre": "accompagnement", "archive": False},
              "acc-vieux": {"genre": "accompagnement", "archive": True},
              "plat-carbo": {"genre": "plat", "archive": False}}
    assert nettoyer_accords(["acc-vieux", "inconnu-01", "plat-carbo", "acc-puree"], par_id) == ["acc-puree"]


# --- Base ---

def test_enregistrer_et_lire_des_accords(conn):
    boucher = plats(conn)["plat-piece-du-boucher"]
    assert boucher["accords"] == []
    enregistrer_plat(conn, {**boucher, "accords": ["acc-pommes-sautees", "acc-puree-robuchon"]})
    assert plats(conn)["plat-piece-du-boucher"]["accords"] == ["acc-pommes-sautees", "acc-puree-robuchon"]


def test_sans_accords_ceux_en_base_restent(conn):
    boucher = plats(conn)["plat-piece-du-boucher"]
    enregistrer_plat(conn, {**boucher, "accords": ["acc-pommes-sautees"]})
    ancien = {k: v for k, v in boucher.items() if k != "accords"}                  # la page d'avant
    enregistrer_plat(conn, valider_plat({**ancien, "nom": "Pièce du boucher"}))
    relu = plats(conn)["plat-piece-du-boucher"]
    assert relu["nom"] == "Pièce du boucher" and relu["accords"] == ["acc-pommes-sautees"]


def test_nouveau_plat_sans_accords(conn):
    enregistrer_plat(conn, valider_plat(STEAK))
    assert plats(conn)["plat-test-steak"]["accords"] == []


# --- Route ---

def test_api_plats_ne_garde_que_des_accompagnements(client, conn):
    boucher = plats(conn)["plat-piece-du-boucher"]
    corps = {**boucher, "accords": ["acc-puree-robuchon", "plat-carbonara", "inconnu-01"]}
    assert client.post("/api/plats", json=corps).status_code == 200
    assert plats(conn)["plat-piece-du-boucher"]["accords"] == ["acc-puree-robuchon"]
    assert client.post("/api/plats", json={**boucher, "accords": "acc-puree-robuchon"}).status_code == 400
    lu = {p["id"]: p for p in client.get("/api/diners").get_json()["plats"]}
    assert lu["plat-piece-du-boucher"]["accords"] == ["acc-puree-robuchon"]
```

- [ ] **Step 2: Lancer les tests, vérifier qu'ils échouent**

Run: `cd voyage && .venv/bin/python3 -m pytest test_accords.py -q`
Expected: FAIL à l'import (`cannot import name 'nettoyer_accords'`).

- [ ] **Step 3: La colonne**

Dans `voyage/schema.sql`, juste après `ALTER TABLE plats ADD CONSTRAINT plats_pour_check CHECK (pour IN ('nous', 'julien', 'laetitia'));` :

```sql
-- Accords (02/11/2026) : les accompagnements qui vont avec un plat (ids de plats, 6 au plus)
ALTER TABLE plats ADD COLUMN IF NOT EXISTS accords JSONB NOT NULL DEFAULT '[]';
```

Appliquer à la base de test : `cd voyage && .venv/bin/python3 appliquer_schema.py --base valise_test --appliquer`
(Les reprises de contenu ajoutent des recettes à `valise_test` : sans effet, chaque test vide les tables.)

- [ ] **Step 4: Validation dans `diners.py`**

Sous `MAX_PLATS = 8`, ajouter :

```python
MAX_ACCORDS = 6
```

Dans `valider_plat`, remplacer la fin :

```python
    p["archive"] = archive
    return p
```

par :

```python
    p["archive"] = archive
    accords = corps.get("accords")            # absent (page d'avant les accords) : None, ceux en base restent
    if accords is not None:
        if (not isinstance(accords, list) or len(accords) > MAX_ACCORDS
                or not all(isinstance(i, str) and _ID.fullmatch(i) for i in accords)):
            raise ValueError("accords invalides")
        if len(set(accords)) != len(accords) or identifiant in accords:
            raise ValueError("accord en double")
        if p["genre"] != "plat":
            accords = []
    p["accords"] = accords
    return p


def nettoyer_accords(accords, par_id):
    """Les accords qui tiennent : des accompagnements connus et non archivés, dans l'ordre donné."""
    return [i for i in accords
            if i in par_id and par_id[i]["genre"] == "accompagnement" and not par_id[i]["archive"]]
```

- [ ] **Step 5: Enregistrement dans `db.py`**

Remplacer :

```python
CHAMPS_PLAT = ("nom", "genre", "minutes", "ingredients", "recette", "lien", "note", "statut", "archive", "pour")
_DEFAUTS_PLAT = {"pour": "nous"}


def _valeurs_plat(p):
    return [Json(p[c]) if c == "ingredients" else p.get(c, _DEFAUTS_PLAT.get(c)) for c in CHAMPS_PLAT]


def enregistrer_plat(conn, p):
    """Crée ou met à jour (même id) une recette validée."""
    valeurs = _valeurs_plat(p)
    with conn.cursor() as cur:
        cur.execute(
            f"""INSERT INTO plats (id, {", ".join(CHAMPS_PLAT)})
                VALUES (%s, {", ".join(["%s"] * len(CHAMPS_PLAT))})
                ON CONFLICT (id) DO UPDATE SET
                {", ".join(f"{c} = EXCLUDED.{c}" for c in CHAMPS_PLAT)}, maj_le = now()""",
            (p["id"], *valeurs))
    conn.commit()
```

par :

```python
CHAMPS_PLAT = ("nom", "genre", "minutes", "ingredients", "recette", "lien", "note", "statut", "archive", "pour",
               "accords")
_DEFAUTS_PLAT = {"pour": "nous", "accords": []}
_JSON_PLAT = ("ingredients", "accords")


def _valeurs_plat(p):
    valeurs = []
    for c in CHAMPS_PLAT:
        v = p.get(c)
        if v is None:
            v = _DEFAUTS_PLAT.get(c)
        valeurs.append(Json(v) if c in _JSON_PLAT else v)
    return valeurs


def enregistrer_plat(conn, p):
    """Crée ou met à jour (même id) une recette validée. Sans accords (None : une page d'avant les accords),
    ceux déjà en base restent."""
    champs = [c for c in CHAMPS_PLAT if not (c == "accords" and p.get("accords") is None)]
    valeurs = dict(zip(CHAMPS_PLAT, _valeurs_plat(p)))
    with conn.cursor() as cur:
        cur.execute(
            f"""INSERT INTO plats (id, {", ".join(champs)})
                VALUES (%s, {", ".join(["%s"] * len(champs))})
                ON CONFLICT (id) DO UPDATE SET
                {", ".join(f"{c} = EXCLUDED.{c}" for c in champs)}, maj_le = now()""",
            (p["id"], *[valeurs[c] for c in champs]))
    conn.commit()
```

(`ajouter_recettes` utilise `_valeurs_plat` sur toute la liste `CHAMPS_PLAT` : un lot de recettes sans `accords` s'insère avec `[]`.)

- [ ] **Step 6: La route `api/plats` dans `serveur.py`**

Ajouter `nettoyer_accords` à l'import `from diners import (…)`. Dans `enregistrer_une_recette`, remplacer :

```python
        conn = emprunter(app.config["NOM_BASE"])
        try:
            enregistrer_plat(conn, plat)
        finally:
            conn.close()
        return jsonify({"ok": True})
```

par :

```python
        conn = emprunter(app.config["NOM_BASE"])
        try:
            if plat["accords"] is not None:           # seulement des accompagnements connus et non archivés
                plat["accords"] = nettoyer_accords(plat["accords"], {p["id"]: p for p in lire_plats(conn)})
            enregistrer_plat(conn, plat)
        finally:
            conn.close()
        return jsonify({"ok": True})
```

- [ ] **Step 7: Lancer les tests**

Run: `cd voyage && .venv/bin/python3 -m pytest test_accords.py -q`
Expected: PASS (12 tests).
Run: `cd voyage && .venv/bin/python3 -m pytest -q`
Expected: tout passe (659 + 12). Si un test existant compare un plat entier lu en base, y ajouter `"accords": []`.

- [ ] **Step 8: Commit**

```bash
git add voyage/schema.sql voyage/diners.py voyage/db.py voyage/serveur.py voyage/test_accords.py
git commit -m "feat: Casa Binomerie — accords d'un plat : colonne, validation, enregistrement et route api/plats"
```

---

### Task 2: Le contenu — 15 accompagnements, 6 brunchs, les accords de départ

**Files:**
- Create: `voyage/recettes_accompagnements.py`
- Modify: `voyage/db.py` (nouvelle `poser_accords`, juste après `ajouter_recettes`)
- Modify: `voyage/appliquer_schema.py` (imports et les deux branches de `appliquer`)
- Modify: `voyage/diners.py` (`proposer` : pas de brunch au dîner)
- Test: `voyage/test_accompagnements.py` (nouveau)

**Interfaces:**
- Consumes: `db.ajouter_recettes(conn, nom_reprise, plats, retirer=())` (existante) ; colonne `accords` et `db.enregistrer_plat` / `db.lire_plats` de la Task 1.
- Produces: `recettes_accompagnements.NOM_REPRISE = "accompagnements-brunch-v1"`, `NOM_REPRISE_ACCORDS = "accords-v1"`, `ACCOMPAGNEMENTS` (15 dicts, ids `acc-…`), `BRUNCHS` (6 dicts, ids `brunch-…`), `ACCORDS` (dict id de plat -> liste d'ids d'accompagnements), `JAMAIS_LEGUMES_LAETITIA`. `db.poser_accords(conn, nom_reprise, accords) -> int | None`. La Task 3 se sert du préfixe d'id `brunch-` pour l'étiquette « Brunch ».

- [ ] **Step 1: Écrire les tests qui échouent**

Créer `voyage/test_accompagnements.py` :

```python
"""Tests des accompagnements, des brunchs et des accords de départ (recettes_accompagnements.py)."""
import sys
from datetime import date
from pathlib import Path
from random import Random
sys.path.insert(0, str(Path(__file__).parent))

import pytest
from carnet_depart import CARNET_DEPART, A_TESTER
from catalogue import chercher
from courses import PLACARD_DEPART, normaliser
from db import connecter, semer_placard, semer_carnet, lire_plats, ajouter_recettes, enregistrer_plat, poser_accords
from diners import valider_plat, proposer, semaine
from recettes_air_fryer import AIR_FRYER
from recettes_legumes import LEGUMES, RETIRES
from recettes_mer import MER, MER_JULIEN, JAMAIS_LAETITIA
from recettes_laetitia import LAETITIA
from recettes_accompagnements import (NOM_REPRISE, NOM_REPRISE_ACCORDS, ACCOMPAGNEMENTS, BRUNCHS, ACCORDS,
                                      JAMAIS_LEGUMES_LAETITIA)

LOTS = AIR_FRYER + LEGUMES + MER + MER_JULIEN + LAETITIA
AUTRES = CARNET_DEPART + A_TESTER + LOTS
TOUS = {p["id"]: p for p in AUTRES + ACCOMPAGNEMENTS + BRUNCHS}
JAMAIS = JAMAIS_LAETITIA + JAMAIS_LEGUMES_LAETITIA


@pytest.fixture
def conn():
    c = connecter("valise_test")
    with c.cursor() as cur:
        cur.execute("TRUNCATE repas, soirs, plats, courses, placard, reprises")
    c.commit()
    semer_placard(c, PLACARD_DEPART)
    semer_carnet(c, CARNET_DEPART, A_TESTER)
    ajouter_recettes(c, "lots-du-test", LOTS)          # la base de prod a aussi ces lots
    c.commit()
    yield c
    c.close()


def a_un_jamais(p):
    return [i for i in p["ingredients"] if any(j in normaliser(i) for j in JAMAIS)]


def test_donnees():
    nouveaux = ACCOMPAGNEMENTS + BRUNCHS
    ids = [p["id"] for p in nouveaux]
    assert len(ACCOMPAGNEMENTS) == 15 and len(BRUNCHS) == 6 and len(set(ids)) == len(ids)
    assert not set(ids) & {p["id"] for p in AUTRES}
    assert all(p["genre"] == "accompagnement" and p["id"].startswith("acc-") for p in ACCOMPAGNEMENTS)
    assert all(p["id"].startswith("brunch-") for p in BRUNCHS)
    for p in nouveaux:
        assert valider_plat({**p, "statut": "a-tester"})["pour"] == "nous"
        assert p["recette"].startswith("Pour "), p["id"]
        assert [i for i in p["ingredients"] if not chercher(i)] == [], p["id"]


def test_rien_de_ses_jamais():
    for p in ACCOMPAGNEMENTS + BRUNCHS:
        assert not a_un_jamais(p), p["id"]


def test_accords_de_depart():
    assert len(ACCORDS) >= 25
    for id_, accords in ACCORDS.items():
        assert TOUS[id_]["genre"] == "plat", id_
        assert 2 <= len(accords) <= 4 and len(set(accords)) == len(accords), id_
        for a in accords:
            acc = TOUS[a]
            assert acc["genre"] == "accompagnement" and acc.get("pour", "nous") == "nous", (id_, a)
            assert a not in RETIRES and not a_un_jamais(acc), (id_, a)


def test_ajout_et_accords_une_seule_fois(conn):
    assert ajouter_recettes(conn, NOM_REPRISE, ACCOMPAGNEMENTS + BRUNCHS) == 21
    assert poser_accords(conn, NOM_REPRISE_ACCORDS, ACCORDS) == len(ACCORDS)
    conn.commit()
    plats = {p["id"]: p for p in lire_plats(conn)}
    assert plats["plat-piece-du-boucher"]["accords"] == ACCORDS["plat-piece-du-boucher"]
    assert plats["acc-riz-pilaf"]["statut"] == "a-tester" and plats["brunch-crepes"]["genre"] == "dessert"
    assert poser_accords(conn, NOM_REPRISE_ACCORDS, ACCORDS) is None


def test_accords_regles_dans_l_app_et_archives(conn):
    ajouter_recettes(conn, NOM_REPRISE, ACCOMPAGNEMENTS)
    conn.commit()
    plats = {p["id"]: p for p in lire_plats(conn)}
    enregistrer_plat(conn, {**plats["plat-roti-de-boeuf"], "accords": ["acc-puree-robuchon"]})   # réglé dans l'app
    enregistrer_plat(conn, {**plats["acc-salade-verte"], "archive": True})                     # retiré dans l'app
    poser_accords(conn, NOM_REPRISE_ACCORDS, ACCORDS)
    conn.commit()
    plats = {p["id"]: p for p in lire_plats(conn)}
    assert plats["plat-roti-de-boeuf"]["accords"] == ["acc-puree-robuchon"]
    assert plats["plat-piece-du-boucher"]["accords"] == [a for a in ACCORDS["plat-piece-du-boucher"]
                                                         if a != "acc-salade-verte"]


def test_pas_de_brunch_propose_au_diner():
    lundi = date(2026, 11, 2)
    plats = [{**p, "statut": "carnet", "archive": False} for p in BRUNCHS if p["genre"] == "plat"]
    assert len(plats) == 3
    assert proposer(plats, [], semaine(lundi), lundi, hasard=Random(1)) == {}
```

- [ ] **Step 2: Lancer les tests, vérifier qu'ils échouent**

Run: `cd voyage && .venv/bin/python3 -m pytest test_accompagnements.py -q`
Expected: FAIL à l'import (`No module named 'recettes_accompagnements'`).

- [ ] **Step 3: Le contenu**

Créer `voyage/recettes_accompagnements.py` :

```python
"""Accompagnements, brunchs et accords de départ (02/11/2026) : la spec repas composés, étape 2.

- 15 accompagnements pour nous deux : féculents, et des légumes que Laetitia accepte (champignons, haricots verts,
  tomate sans condition ; croustillant, cru, rôti). Aucun de ses « jamais ».
- 6 brunchs (ids « brunch- » : l'étiquette Brunch de la page Dîners). Jamais proposés pour un dîner.
- ACCORDS : 2 à 4 accompagnements par plat principal « nu » (viande, poisson, tarte, croque) ; rien pour les plats
  complets (pâtes, risottos, currys avec leur riz). Un plat qui a déjà son féculent reçoit des légumes.
Rédigées par Claude d'après les versions de référence, à corriger dans l'app.
Mêmes conventions que carnet_depart.py : noms d'ingrédients du catalogue, sel, poivre et huile sous-entendus.
Ajoutées une seule fois (table reprises), statut à tester ; accords posés une seule fois, sur les plats sans accords.
"""

NOM_REPRISE = "accompagnements-brunch-v1"
NOM_REPRISE_ACCORDS = "accords-v1"

# Ses « jamais » côté légumes (jeu Légumes Démasqués, 01/11/2026), comparés normalisés (sans accents)
JAMAIS_LEGUMES_LAETITIA = ("brocoli", "chou-fleur", "epinard", "aubergine", "betterave", "celeri")


def _acc(id_, nom, minutes, ingredients, recette, note=""):
    return {"id": "acc-" + id_, "nom": nom, "genre": "accompagnement", "minutes": minutes,
            "ingredients": ingredients, "recette": recette, "lien": "", "note": note}


def _brunch(id_, nom, genre, minutes, ingredients, recette, note=""):
    return {"id": "brunch-" + id_, "nom": nom, "genre": genre, "minutes": minutes, "ingredients": ingredients,
            "recette": recette, "lien": "", "note": note}


ACCOMPAGNEMENTS = [
    _acc("riz-pilaf", "Riz pilaf", 25, ["riz", "oignons", "beurre", "bouillon"],
         """Pour 2
- 150 g de riz long (basmati ou thaï), 1/2 oignon, 1 noix de beurre
- 25 cl de bouillon chaud (une fois et demie le volume du riz)

1. Oignon ciselé fondu 3 min dans le beurre, sans coloration.
2. Riz versé à sec, remué 2 min : les grains deviennent nacrés.
3. Bouillon chaud, couvercle, feu doux 15 min sans soulever.
4. Hors du feu 5 min à couvert, puis égrainer à la fourchette.""",
         "Avec des gambas, un saumon, un chili ou un poisson."),

    _acc("semoule", "Semoule au beurre", 10, ["semoule", "beurre", "bouillon"],
         """Pour 2
- 150 g de semoule moyenne, 15 cl de bouillon, 1 noix de beurre

1. Semoule dans un saladier, bouillon bouillant juste à hauteur, couvrir d'une assiette.
2. 5 min de repos, puis le beurre, et égrainer à la fourchette.
3. Poivre, un filet d'huile d'olive.""",
         "Avec des cuisses de poulet au paprika ou un poulet rôti."),

    _acc("pommes-grenaille", "Pommes grenaille ail-romarin (air fryer)", 30,
         ["pommes de terre grenaille", "ail", "romarin"],
         """Pour 2
- 500 g de pommes de terre grenaille, 3 gousses d'ail en chemise, 2 brins de romarin (ou 1 c. à c. séché)
- 1 c. à s. d'huile

1. Grenailles lavées, coupées en deux, séchées dans un torchon.
2. Huile, sel, romarin, ail en chemise : bien mélanger dans un saladier.
3. Air fryer 200 °C, 20 à 22 min, en secouant le panier à mi-cuisson.
4. Prêtes quand la pointe d'un couteau entre sans résister.""",
         "Croustillant : le registre où Laetitia dit oui."),

    _acc("ecrasee", "Écrasé de pommes de terre à l'huile d'olive", 25, ["pommes de terre", "ciboulette"],
         """Pour 2
- 500 g de pommes de terre à chair ferme, 3 c. à s. d'huile d'olive, ciboulette, fleur de sel

1. Pommes de terre épluchées, en gros morceaux, dans l'eau froide salée ; 18 min après l'ébullition.
2. Égoutter, écraser grossièrement à la fourchette : des morceaux doivent rester.
3. Huile d'olive, ciboulette ciselée, fleur de sel, poivre.""",
         "Pas une purée lisse : des morceaux, rien de mixé."),

    _acc("coquillettes", "Coquillettes au beurre et parmesan", 12, ["coquillettes", "beurre", "parmesan"],
         """Pour 2
- 160 g de coquillettes, 1 belle noix de beurre, 30 g de parmesan râpé

1. Coquillettes dans une grande eau bouillante salée, 1 min de moins que le temps du paquet.
2. Garder une louche d'eau de cuisson, égoutter.
3. Hors du feu, dans la casserole : beurre, parmesan, un peu d'eau de cuisson ; remuer jusqu'à ce que ce soit nappé.""",
         "Avec un bœuf bourguignon ou un osso buco : la sauce a besoin de pâtes."),

    _acc("polenta", "Polenta crémeuse au parmesan", 15, ["polenta", "lait", "beurre", "parmesan"],
         """Pour 2
- 100 g de polenta précuite, 25 cl de lait et 25 cl d'eau, 1 noix de beurre, 30 g de parmesan

1. Lait, eau et une pincée de sel à ébullition.
2. Polenta en pluie en fouettant, puis 5 min à feu doux en remuant à la cuillère en bois.
3. Hors du feu : beurre et parmesan. Elle doit couler comme une purée épaisse ; trop ferme, un trait de lait.""",
         "Avec un saltimbocca, un osso buco ou des polpette."),

    _acc("champignons-persillade", "Champignons poêlés en persillade", 15,
         ["champignons de Paris", "ail", "persil", "beurre"],
         """Pour 2
- 300 g de champignons de Paris, 1 gousse d'ail, persil, 1 noix de beurre

1. Champignons essuyés (pas lavés), en quartiers.
2. Poêle très chaude avec un filet d'huile, champignons en une couche : 3 min sans remuer, ils dorent au lieu de rendre leur eau.
3. Beurre, ail et persil hachés, 1 min. Sel à la fin.""",
         "Champignons : un des légumes que Laetitia aime sans condition."),

    _acc("haricots-amandes", "Haricots verts aux amandes", 15, ["haricots verts", "amandes effilées", "beurre"],
         """Pour 2
- 300 g de haricots verts (frais, ou extra-fins surgelés), 20 g d'amandes effilées, 1 noix de beurre

1. Haricots 6 min dans une grande eau bouillante salée, puis dans l'eau glacée : ils restent verts et croquants.
2. Amandes dorées à sec dans la poêle, 2 min, en surveillant.
3. Beurre, haricots égouttés, 3 min à feu vif. Sel, poivre.""",
         "Haricots verts : l'autre légume que Laetitia aime sans condition."),

    _acc("tomates-provencale", "Tomates à la provençale", 30, ["tomates", "ail", "persil", "chapelure"],
         """Pour 2
- 4 tomates, 1 gousse d'ail, persil, 2 c. à s. de chapelure, huile d'olive

1. Four à 200 °C (ou air fryer 180 °C). Tomates coupées en deux, côté coupé vers le haut, salées.
2. Ail et persil hachés, mélangés à la chapelure et un filet d'huile : en dôme sur chaque moitié.
3. 25 min au four (15 min en air fryer) : le dessus gratine, la tomate confit.""",
         "Tomate : un oui de Laetitia."),

    _acc("salade-verte", "Salade verte, vinaigrette moutarde", 5, ["salade", "moutarde", "vinaigre", "échalotes"],
         """Pour 2
- 1 laitue ou 1/2 batavia, 1 c. à c. de moutarde, 1 c. à s. de vinaigre, 3 c. à s. d'huile, 1/2 échalote

1. Salade lavée et bien essorée : une salade mouillée noie la vinaigrette.
2. Dans le saladier : moutarde, vinaigre, sel, puis l'huile en fouettant, l'échalote ciselée.
3. Mélanger au moment de servir, pas avant.""",
         "Cru : Laetitia dit oui 4 fois sur 5."),

    _acc("frites-courgette", "Frites de courgette au parmesan (air fryer)", 20,
         ["courgettes", "farine", "œufs", "chapelure", "parmesan"],
         """Pour 2
- 2 courgettes, 2 c. à s. de farine, 1 œuf, 50 g de chapelure (panko si possible), 30 g de parmesan râpé

1. Courgettes en bâtonnets de 1 cm, épongées dans un torchon.
2. Farine, œuf battu, puis chapelure mélangée au parmesan.
3. Un peu d'huile en spray, air fryer 200 °C, 10 à 12 min en une couche, retournées à mi-cuisson.""",
         "Croustillant : 3 oui sur 3 chez Laetitia, même quand le légume est un « ça dépend »."),

    _acc("rostis", "Röstis de pommes de terre", 25, ["pommes de terre", "oignons", "œufs"],
         """Pour 2
- 400 g de pommes de terre, 1/2 oignon, 1 œuf

1. Pommes de terre et oignon râpés gros, pressés fort dans un torchon pour sortir l'eau.
2. Œuf, sel, poivre, mélanger.
3. Poêle chaude bien huilée : 4 petits tas aplatis, 5 min par face à feu moyen, jusqu'à ce qu'ils soient dorés.
4. Égoutter sur du papier absorbant.""",
         "Avec un steak, des ailes de poulet, ou des œufs au brunch."),

    _acc("pommes-four", "Pommes de terre au four, crème ciboulette (air fryer)", 45,
         ["pommes de terre", "crème fraîche", "ciboulette"],
         """Pour 2
- 2 grosses pommes de terre (type bintje), 4 c. à s. de crème fraîche, ciboulette

1. Pommes de terre lavées, piquées à la fourchette, frottées d'huile et de gros sel.
2. Air fryer 200 °C, 40 à 45 min, retournées à mi-cuisson : peau croustillante, cœur fondant.
3. Fendre en croix, presser les côtés, crème mélangée à la ciboulette ciselée dans l'ouverture.""",
         "Avec un rôti de bœuf ou une pièce du boucher."),

    _acc("carottes-vichy", "Carottes Vichy", 25, ["carottes", "beurre", "sucre", "persil"],
         """Pour 2
- 4 carottes, 1 noix de beurre, 1 c. à c. de sucre, persil

1. Carottes en rondelles fines.
2. Dans une casserole : carottes, beurre, sucre, sel, eau juste à hauteur.
3. Feu moyen sans couvercle, 20 min : l'eau s'évapore, les carottes finissent glacées et brillantes. Persil.""",
         "Carotte : Laetitia l'aime rôtie, râpée, en velouté ; glacée, à confirmer."),

    _acc("pain-ail", "Pain à l'ail", 10, ["baguettes", "beurre", "ail", "persil"],
         """Pour 2
- 1 baguette, 60 g de beurre mou, 2 gousses d'ail, persil

1. Beurre écrasé avec l'ail haché, le persil et une pincée de sel.
2. Baguette entaillée tous les 2 cm sans couper le dessous, du beurre glissé dans chaque fente.
3. Air fryer 180 °C, 5 à 6 min (ou four 200 °C, 10 min).""",
         "Avec un velouté, des lasagnes ou des polpette."),
]

BRUNCHS = [
    _brunch("avocado-toast", "Avocado toast, œuf poché", "plat", 15,
            ["pain de campagne", "avocats", "œufs", "citrons", "vinaigre", "piment d'Espelette"],
            """Pour 2
- 2 grandes tranches de pain de campagne, 1 avocat bien mûr, 2 œufs très frais, 1/2 citron
- un trait de vinaigre, piment d'Espelette

1. Avocat écrasé à la fourchette avec le jus de citron et du sel.
2. Œufs pochés : eau frémissante (pas bouillante) avec le vinaigre, un tourbillon à la cuillère, l'œuf cassé au centre, 3 min. Égoutter sur du papier absorbant.
3. Pain grillé, avocat, œuf, piment d'Espelette, fleur de sel."""),

    _brunch("oeufs-benedicte", "Œufs Bénédicte", "plat", 30,
            ["muffins anglais", "œufs", "jambon", "beurre", "citrons", "vinaigre"],
            """Pour 2
- 2 muffins anglais, 4 œufs (2 pochés, 2 jaunes pour la sauce), 2 tranches de jambon
- 80 g de beurre, 1/2 citron, un trait de vinaigre

1. Hollandaise : 2 jaunes et 1 c. à s. d'eau au bain-marie, fouetter jusqu'à ce que ça mousse et épaississe ; le beurre fondu en filet sans cesser de fouetter. Citron, sel. Garder au bain-marie éteint.
2. Œufs pochés 3 min dans l'eau frémissante vinaigrée.
3. Muffins coupés et grillés, jambon, œuf, hollandaise."""),

    _brunch("omelette", "Omelette champignons et comté", "plat", 10,
            ["œufs", "champignons de Paris", "comté", "beurre"],
            """Pour 2
- 5 œufs, 150 g de champignons de Paris, 50 g de comté râpé, 1 noix de beurre

1. Champignons émincés dorés à la poêle, réservés.
2. Œufs battus avec sel et poivre, juste mélangés.
3. Beurre mousseux, œufs ; ramener les bords vers le centre pendant 1 min, puis laisser prendre en gardant le dessus baveux.
4. Champignons et comté sur une moitié, replier, glisser dans l'assiette."""),

    _brunch("pain-perdu", "Pain perdu brioché", "dessert", 15, ["brioche", "œufs", "lait", "sucre", "beurre"],
            """Pour 2
- 4 tranches épaisses de brioche (rassie, c'est mieux), 2 œufs, 15 cl de lait, 2 c. à s. de sucre, 1 noix de beurre

1. Œufs, lait et sucre battus dans une assiette creuse.
2. Brioche trempée 10 secondes par face, pas plus : elle doit rester entière.
3. Poêle beurrée à feu moyen, 2 à 3 min par face, jusqu'à ce que ce soit caramélisé.
4. Avec des fruits rouges, du sirop d'érable ou juste du sucre."""),

    _brunch("granola", "Granola maison, yaourt grec et fruits rouges", "dessert", 30,
            ["flocons d'avoine", "amandes", "miel", "yaourt grec", "fruits rouges"],
            """Pour 4 (le granola se garde 2 semaines en bocal)
- 200 g de flocons d'avoine, 60 g d'amandes concassées, 4 c. à s. de miel, 2 c. à s. d'huile neutre
- pour servir : yaourt grec, fruits rouges (surgelés, décongelés la veille)

1. Four à 160 °C. Flocons, amandes, miel, huile et une pincée de sel mélangés.
2. Étalés sur une plaque, 20 à 25 min, en remuant à mi-cuisson, jusqu'à ce que ce soit doré.
3. Refroidir sans toucher : il durcit en grappes. Servir sur le yaourt, avec les fruits.""",
            "Se prépare la veille."),

    _brunch("crepes", "Crêpes", "dessert", 30, ["farine", "œufs", "lait", "beurre", "sucre"],
            """Pour 2 (une dizaine)
- 125 g de farine, 2 œufs, 25 cl de lait, 20 g de beurre fondu, 1 c. à s. de sucre, 1 pincée de sel

1. Farine, sucre, sel ; les œufs au centre ; le lait petit à petit en fouettant : pas de grumeaux.
2. Beurre fondu ; 30 min de repos si possible.
3. Poêle chaude à peine beurrée, une petite louche, tourner la poêle ; 1 min, retourner, 30 s.
4. Sucre, confiture, pâte à tartiner ou citron."""),
]

# Plat principal -> 2 à 4 accompagnements (ids). Un plat qui a déjà son féculent reçoit des légumes.
ACCORDS = {
    # Carnet
    "plat-piece-du-boucher": ["af-frites", "acc-pommes-sautees", "acc-haricots-amandes", "acc-salade-verte"],
    "plat-roti-de-boeuf": ["acc-gratin-dauphinois", "acc-pommes-grenaille", "acc-haricots-amandes",
                           "acc-champignons-persillade"],
    "plat-poulet-roti": ["lg-haricots-lardons", "af-carottes", "acc-salade-verte"],               # pommes de terre dedans
    "plat-blanquette-veau": ["acc-haricots-amandes", "acc-salade-verte"],                         # riz dedans
    "plat-boeuf-bourguignon": ["acc-puree-robuchon", "acc-coquillettes", "acc-ecrasee"],
    "plat-saltimbocca": ["acc-ecrasee", "acc-polenta", "acc-tomates-provencale"],
    "plat-bacon-cheese-burger": ["af-frites", "af-patate-douce", "acc-rostis"],
    "plat-quiche-lorraine": ["acc-salade-verte", "acc-tomates-provencale"],
    "plat-croque-monsieur": ["acc-salade-verte", "af-frites"],
    "plat-baguezza": ["acc-salade-verte", "acc-frites-courgette"],
    "lg-baguezza-champi": ["acc-salade-verte", "acc-frites-courgette"],
    "plat-lasagne-bolognese": ["acc-salade-verte", "acc-pain-ail"],
    # À tester
    "lg-quiche-poireaux": ["acc-salade-verte", "acc-tomates-provencale"],
    "af-croque": ["acc-salade-verte", "af-frites"],
    "af-wings": ["af-frites", "af-patate-douce", "acc-frites-courgette"],
    "af-tenders": ["af-frites", "af-patate-douce", "acc-salade-verte"],
    "af-cuisses": ["acc-pommes-grenaille", "acc-semoule", "af-carottes", "acc-frites-courgette"],
    "af-saumon": ["acc-haricots-amandes", "lg-tempura"],                                          # riz dedans
    "tester-osso-buco": ["acc-polenta", "acc-ecrasee", "acc-coquillettes"],
    "tester-polpette": ["acc-pain-ail", "acc-polenta"],
    "lg-veloute-carotte": ["acc-pain-ail", "acc-salade-verte"],
    "mer-gambas-ail": ["acc-riz-pilaf", "acc-salade-verte"],
    # Pour Julien seul (Laetitia mange l'accompagnement)
    "mer-sole-meuniere": ["acc-haricots-amandes", "acc-salade-verte"],                            # pommes de terre dedans
    "mer-dorade-four": ["acc-tomates-provencale", "acc-salade-verte"],
    "mer-cabillaud-chorizo": ["acc-haricots-amandes", "acc-tomates-provencale"],
    "mer-sardines-grillees": ["acc-pommes-grenaille", "acc-salade-verte"],
    "mer-tenders-cabillaud": ["af-frites", "af-patate-douce"],
    "mer-moules-chorizo": ["af-frites", "acc-salade-verte"],
    # Pour Laetitia seule
    "laet-vitello-tonnato": ["acc-salade-verte", "acc-pommes-grenaille"],
}
```

- [ ] **Step 4: `poser_accords` dans `db.py`**

Juste après la fonction `ajouter_recettes` :

```python
def poser_accords(conn, nom_reprise, accords):
    """Les accords de départ ({id de plat: [ids d'accompagnements]}), une seule fois (table reprises) :
    seulement sur les plats qui n'en ont pas encore (ceux réglés dans l'app restent), et seulement des
    accompagnements présents et non archivés. Sans commit : l'appelant valide ou annule (à blanc).
    Renvoie le nombre de plats réglés, ou None si c'est déjà fait."""
    with conn.cursor() as cur:
        cur.execute("SELECT EXISTS (SELECT 1 FROM reprises WHERE nom = %s)", (nom_reprise,))
        if cur.fetchone()[0]:
            return None
        cur.execute("SELECT id FROM plats WHERE genre = 'accompagnement' AND NOT archive")
        possibles = {ligne[0] for ligne in cur.fetchall()}
        n = 0
        for id_, ids in accords.items():
            gardes = [i for i in ids if i in possibles]
            if gardes:
                cur.execute("""UPDATE plats SET accords = %s, maj_le = now()
                               WHERE id = %s AND genre = 'plat' AND accords = '[]'::jsonb""", (Json(gardes), id_))
                n += cur.rowcount
        cur.execute("INSERT INTO reprises (nom) VALUES (%s)", (nom_reprise,))
    return n
```

- [ ] **Step 5: Pas de brunch au dîner dans `proposer` (`diners.py`)**

Dans `proposer`, remplacer :

```python
    candidats = [p for p in plats if p["genre"] == "plat" and not p["archive"] and p.get("pour", "nous") == "nous"
                 and p["recette"] and p["id"] not in exclus]
```

par :

```python
    candidats = [p for p in plats if p["genre"] == "plat" and not p["archive"] and p.get("pour", "nous") == "nous"
                 and p["recette"] and p["id"] not in exclus and not p["id"].startswith("brunch-")]
```

Et dans sa docstring, remplacer `ni mangés ces 14 derniers jours ;` par `ni mangés ces 14 derniers jours, ni brunchs ;`.

- [ ] **Step 6: Les deux reprises dans `appliquer_schema.py`**

Imports : ajouter `poser_accords` à la ligne `from db import …`, et sous `from recettes_laetitia import …` :

```python
from recettes_accompagnements import (NOM_REPRISE as REPRISE_ACCOMPAGNEMENTS, NOM_REPRISE_ACCORDS,
                                      ACCOMPAGNEMENTS, BRUNCHS, ACCORDS)
```

Branche `if pour_de_bon:` — après `repas = reprendre_soirs(conn)                        # soirs -> repas, une seule fois` :

```python
        accompagnements = ajouter_recettes(conn, REPRISE_ACCOMPAGNEMENTS, ACCOMPAGNEMENTS + BRUNCHS)
        accords = poser_accords(conn, NOM_REPRISE_ACCORDS, ACCORDS)    # après l'ajout : ils existent
```

et après `print(f"Repas composés : {repas} soir(s) repris en dîners.")` (même indentation que son `if`) :

```python
        if accompagnements is not None:
            print(f"Accompagnements et brunchs : {accompagnements} recettes ajoutées à tester.")
        if accords is not None:
            print(f"Accords : {accords} plat(s) avec leurs accompagnements.")
```

Branche `else:` (à blanc) — après `repas = reprendre_soirs(conn)` :

```python
        accompagnements = ajouter_recettes(conn, REPRISE_ACCOMPAGNEMENTS, ACCOMPAGNEMENTS + BRUNCHS)
        accords = poser_accords(conn, NOM_REPRISE_ACCORDS, ACCORDS)
```

et après `print(f"À blanc, repas composés : {repas} soir(s) à reprendre en dîners.")` :

```python
        if accompagnements is not None:
            print(f"À blanc, accompagnements et brunchs : {accompagnements} recettes à ajouter à tester.")
        if accords is not None:
            print(f"À blanc, accords : {accords} plat(s) à régler.")
```

- [ ] **Step 7: Lancer les tests**

Run: `cd voyage && .venv/bin/python3 -m pytest test_accompagnements.py -q`
Expected: PASS (6 tests). Si `test_donnees` signale un ingrédient introuvable au catalogue, remplacer le nom par celui que `catalogue.chercher` connaît (ne pas toucher au catalogue).
Run: `cd voyage && .venv/bin/python3 -m pytest -q`
Expected: tout passe.
Run (à blanc sur la base locale, pour voir les messages) : `cd voyage && .venv/bin/python3 appliquer_schema.py --base valise_test`
Expected: les lignes « À blanc, accompagnements et brunchs : 21 recettes à ajouter à tester. » et « À blanc, accords : … plat(s) à régler. » si `valise_test` ne les a pas déjà (sinon rien : la reprise est faite, c'est normal).

- [ ] **Step 8: Commit**

```bash
git add voyage/recettes_accompagnements.py voyage/db.py voyage/appliquer_schema.py voyage/diners.py voyage/test_accompagnements.py
git commit -m "feat: Casa Binomerie — 15 accompagnements, 6 brunchs et les accords de départ des plats principaux"
```

---

### Task 3: La page — « Avec : » dans la Semaine, « Va bien avec » sur la fiche, l'étiquette Brunch

**Files:**
- Modify: `voyage/diners.py` (`STYLE_DINERS`, `SCRIPT_DINERS`)
- Modify: `voyage/valise.py` (`VERSION_PAGE = 37` → `38`)
- Test: `voyage/test_diners.py` (`test_page_diners`, nouveau `test_version_page_accords`)

**Interfaces:**
- Consumes: `api/diners` renvoie chaque plat avec `accords` (Task 1) ; `api/plats` accepte `accords` et ne garde que des accompagnements (Task 1) ; ids `brunch-…` (Task 2).
- Produces: fonctions JS `accordsDe(p)`, `ouvrirAccords(id)` ; `ouvrirChoix(iso, moment, genre)` accepte `genre = null` (tous les genres).

- [ ] **Step 1: Écrire les tests qui échouent**

Dans `voyage/test_diners.py`, à la fin de `test_page_diners`, ajouter :

```python
    assert "function accordsDe" in html and "function ouvrirAccords" in html                          # accords
    assert "Va bien avec" in html and "Modifier les accords" in html and "'Avec :'" in html
    assert "['brunch', 'Brunch']" in html and "brunch-" in html and "'+ ajouter'" in html            # brunch
```

et après `test_version_page_repas` :

```python
def test_version_page_accords():
    from valise import VERSION_PAGE
    assert VERSION_PAGE >= 38
```

- [ ] **Step 2: Lancer les tests, vérifier qu'ils échouent**

Run: `cd voyage && .venv/bin/python3 -m pytest test_diners.py -q -k "page_diners or version_page"`
Expected: FAIL (`function accordsDe` absent, `VERSION_PAGE` 37).

- [ ] **Step 3: CSS**

Dans `STYLE_DINERS`, juste après la ligne `div.ajouts button.petit { padding: 6px 10px; }` :

```css
ul.plats-repas li.avec { flex-wrap: wrap; gap: 6px; min-height: 0; padding: 0 0 6px; }
ul.plats-repas li.avec button.petit { padding: 6px 10px; }
section.accords div.ingredients { margin-bottom: 8px; }
```

- [ ] **Step 4: Étiquette Brunch et accords dans les constantes et utilitaires JS**

Dans `SCRIPT_DINERS`, remplacer :

```js
    const ETIQUETTES = [['tout', 'Tout'], ['rapide', 'Rapide'], ['nous', 'Nous deux'], ['julien', 'Julien'], ['laetitia', 'Laetitia'],
                        ['air-fryer', 'Air fryer'], ['poisson', 'Poisson'], ['legumes', 'Légumes']];
```

par :

```js
    const ETIQUETTES = [['tout', 'Tout'], ['rapide', 'Rapide'], ['nous', 'Nous deux'], ['julien', 'Julien'], ['laetitia', 'Laetitia'],
                        ['air-fryer', 'Air fryer'], ['poisson', 'Poisson'], ['legumes', 'Légumes'], ['brunch', 'Brunch']];
    // Brunch : les recettes « brunch- » et celles du carnet qui s'y prêtent
    const BRUNCH = ['plat-oeufs-brouilles', 'plat-oeuf-coque', 'plat-oeuf-cocotte', 'tester-pancakes', 'tester-shakshuka', 'mer-bagel-saumon'];
```

Dans `aEtiquette`, juste avant la dernière ligne `return true;` de la fonction :

```js
        if (e === 'brunch') return p.id.indexOf('brunch-') === 0 || BRUNCH.indexOf(p.id) >= 0;
```

Juste après la fonction `platsDeLaSemaine` :

```js
    // Les accords d'un plat qui tiennent encore : des accompagnements non archivés
    function accordsDe(p) {
        return (p.accords || []).map(plat).filter(function (a) { return a && !a.archive && a.genre === 'accompagnement'; });
    }
```

- [ ] **Step 5: « Avec : » sous un plat, et le brunch dans `carteRepas`**

Dans `carteRepas`, remplacer :

```js
            li.append(o, x);
            ul.append(li);
        });
        if (!ul.children.length) ul.append(el('li', 'meta', 'Libre'));
        c.append(ul);
        const a = el('div', 'ajouts');
        AJOUTS.forEach(function (g) { a.append(bouton(g[1], 'petit', function () { ouvrirChoix(iso, moment, g[0]); })); });
```

par :

```js
            li.append(o, x);
            ul.append(li);
            // Ses accords pas encore au menu : un appui les ajoute
            const absents = accordsDe(p).filter(function (acc) { return r.plats.indexOf(acc.id) < 0; });
            if (absents.length && r.plats.length < 8) {
                const avec = el('li', 'avec');
                avec.append(el('span', 'meta', 'Avec :'));
                absents.forEach(function (acc) {
                    avec.append(bouton(acc.nom, 'petit', function () { ajouterPlat(iso, moment, acc.id); }));
                });
                ul.append(avec);
            }
        });
        if (!ul.children.length) ul.append(el('li', 'meta', 'Libre'));
        c.append(ul);
        const a = el('div', 'ajouts');
        // Au brunch, un seul bouton : tous les genres, étiquette Brunch
        (moment === 'brunch' ? [[null, '+ ajouter']] : AJOUTS).forEach(function (g) {
            a.append(bouton(g[1], 'petit', function () { ouvrirChoix(iso, moment, g[0]); }));
        });
```

Dans `vueSemaine`, remplacer :

```js
                        bouton('Brunch', 'petit', function () { ouvrirChoix(iso, 'brunch', 'plat'); }));
```

par :

```js
                        bouton('Brunch', 'petit', function () { ouvrirChoix(iso, 'brunch', null); }));
```

- [ ] **Step 6: `ouvrirChoix` sans genre (brunch)**

Dans `ouvrirChoix`, remplacer :

```js
        haut.append(el('h2', '', MOMENTS[moment] + ' · ' + quand + ' · ' + NOMS_GENRE[genre].toLowerCase()), bouton('Fermer', 'petit', fermer));
```

par :

```js
        haut.append(el('h2', '', MOMENTS[moment] + ' · ' + quand + (genre ? ' · ' + NOMS_GENRE[genre].toLowerCase() : '')),
                    bouton('Fermer', 'petit', fermer));
        if (moment === 'brunch') etiquette.choix = 'brunch';                 // au brunch, d'abord les recettes de brunch
        else if (etiquette.choix === 'brunch') etiquette.choix = 'nous';
```

et remplacer :

```js
        const tous = d.plats.filter(function (p) { return p.genre === genre && !p.archive; });
```

par :

```js
        const tous = d.plats.filter(function (p) { return (!genre || p.genre === genre) && !p.archive; });
```

- [ ] **Step 7: « Va bien avec » sur la fiche, et la feuille des accords**

Dans `ouvrirFiche`, remplacer :

```js
        if (p.note) c.append(el('p', 'meta', p.note));
        const act = el('div', 'actions');
```

par :

```js
        if (p.note) c.append(el('p', 'meta', p.note));
        if (p.genre === 'plat') {
            const va = el('section', 'groupe-ing accords'), liste = el('div', 'ingredients');
            accordsDe(p).forEach(function (a) { liste.append(bouton(a.nom, 'petit', function () { ouvrirFiche(a.id); })); });
            if (!liste.children.length) liste.append(el('span', '', 'Aucun accompagnement choisi.'));
            va.append(el('h3', '', 'Va bien avec'), liste, bouton('Modifier les accords', 'petit', function () { ouvrirAccords(p.id); }));
            c.append(va);
        }
        const act = el('div', 'actions');
```

Juste après la fonction `ouvrirFiche` (avant `function ouvrirEdition`) :

```js
    // Les accords d'un plat : les accompagnements (carnet et à tester), 6 au plus ; un appui coche ou décoche
    function ouvrirAccords(id) {
        const p = plat(id); if (!p) return;
        ouverte = { id: id, edition: true };                // pas de rechargement pendant le choix
        let choisis = accordsDe(p).map(function (a) { return a.id; });
        const c = document.querySelector('#panneau .contenu'); c.replaceChildren();
        const haut = el('div', 'haut');
        haut.append(el('h2', '', 'Avec : ' + p.nom), bouton('Annuler', 'petit', function () { ouvrirFiche(id); }));
        const aide = el('p', 'aide'), ul = el('ul', 'plats'), msg = el('p', 'message');
        const accs = d.plats.filter(function (a) { return a.genre === 'accompagnement' && !a.archive; })
                            .sort(function (a, b) { return a.nom.localeCompare(b.nom, 'fr'); });
        function remplir() {
            aide.textContent = choisis.length + ' choisi(s), 6 au plus.';
            ul.replaceChildren();
            accs.forEach(function (a) {
                const pris = choisis.indexOf(a.id) >= 0;
                function basculer() {
                    if (!pris && choisis.length >= 6) return;
                    choisis = pris ? choisis.filter(function (x) { return x !== a.id; }) : choisis.concat([a.id]);
                    remplir();
                }
                const li = lignePlat(a);
                const o = li.querySelector('button.ouvrir'), o2 = o.cloneNode(true);
                o.replaceWith(o2); o2.addEventListener('click', basculer);
                const b = bouton(pris ? 'Retirer' : 'Ajouter', pris ? 'plein' : 'petit', basculer);
                b.disabled = !pris && choisis.length >= 6;
                b.setAttribute('aria-pressed', String(pris));
                li.append(b);
                ul.append(li);
            });
        }
        remplir();
        const ok = bouton('Enregistrer', 'plein', function () {
            enregistrerPlat(Object.assign({}, p, { accords: choisis })).then(function () { ouvrirFiche(id); },
                function (e) { msg.textContent = 'Refusé par le serveur (' + e.message + ').'; });
        });
        const e = el('div', 'encart'); e.append(ul);
        c.append(haut, aide, ok, msg, e);
        document.getElementById('panneau').hidden = false;
        document.getElementById('panneau').scrollTop = 0;
    }
```

- [ ] **Step 8: VERSION_PAGE**

Dans `voyage/valise.py`, `VERSION_PAGE = 37` devient `VERSION_PAGE = 38`.

- [ ] **Step 9: Lancer les tests**

Run: `cd voyage && .venv/bin/python3 -m pytest -q`
Expected: tout passe.
Contrôle de syntaxe JS : `cd voyage && .venv/bin/python3 -c "from diners import SCRIPT_DINERS; open('/tmp/diners.js','w').write(SCRIPT_DINERS)" && node --check /tmp/diners.js`
Expected: aucune sortie (si `node` manque, le dire dans le rapport ; la Task 4 vérifie dans Chrome).

- [ ] **Step 10: Commit**

```bash
git add voyage/diners.py voyage/valise.py voyage/test_diners.py
git commit -m "feat: Casa Binomerie — accords dans la Semaine et sur la fiche, étiquette Brunch, VERSION_PAGE 38"
```

---

### Task 4: Vérification sur une copie de la prod, puis essai à blanc sur Neon (contrôleur, pas de sous-agent)

**Files:** aucun dans le repo (scripts dans le scratchpad).

- [ ] **Step 1: Copie locale de la prod (Neon en lecture seule)**

Créer la base `valise_copie` avec le schéma de `main` (`git show main:voyage/schema.sql`), puis copier depuis Neon, en session `readonly`, les tables `plats`, `repas`, `soirs`, `courses`, `placard`, `reprises` (colonnes de la source ; `DATABASE_URL` lu avec `dotenv_values`, jamais affiché). `pg_dump` local (v15) refuse Neon (v18) : copie en Python.

- [ ] **Step 2: Migration de la copie**

Run: `cd voyage && .venv/bin/python3 appliquer_schema.py --base valise_copie` puis `--base valise_copie --appliquer`
Expected: « Accompagnements et brunchs : 21 recettes ajoutées à tester. » et « Accords : N plat(s) … » avec N = 29 si aucun plat de `ACCORDS` n'a été archivé ou supprimé en prod.

- [ ] **Step 3: Vérification dans Chrome**

Serveur local sur la copie : `cd voyage && .venv/bin/python3 -c "from serveur import creer_app; creer_app('valise_copie', secret='').run(port=8001)"` (en arrière-plan). Dans Chrome, `http://localhost:8001/diners` :
- Semaine : prévoir « Pièce du boucher » un soir → « Avec : » montre ses 4 accompagnements ; un appui en ajoute un, il disparaît de la ligne « Avec : » et apparaît dans le dîner.
- Fiche de la Pièce du boucher : « Va bien avec » liste les 4, chacun s'ouvre ; « Modifier les accords » : retirer, ajouter, limite à 6, Enregistrer → la fiche montre la nouvelle liste ; recharger la page → elle tient.
- « + déjeuner ou brunch » → Brunch : la feuille montre tous les genres, étiquette Brunch active (les 6 nouveaux + les œufs, pancakes, shakshuka, bagel) ; ajouter des crêpes et un avocado toast ; « + ajouter » sur la carte brunch.
- Proposer ma semaine : aucun brunch proposé au dîner.
- À tester : les 15 accompagnements et 6 brunchs y sont.
- 390 px de large sans débordement horizontal ; console sans erreur.
Puis arrêter le serveur et supprimer `valise_copie`.

- [ ] **Step 4: Essai à blanc sur Neon**

Run: `cd voyage && .venv/bin/python3 appliquer_schema.py`
Expected: « À blanc : table(s) à créer : aucune. », « À blanc, accompagnements et brunchs : 21 recettes à ajouter à tester. », « À blanc, accords : N plat(s) à régler. »

- [ ] **Step 5: S'arrêter et demander à Julien**

Résumer (livré, tests, vérification Chrome, essai à blanc), puis attendre son accord explicite avant : `--appliquer` sur Neon, puis push, PR, merge.
