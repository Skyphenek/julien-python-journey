# Casa — sous-hub Sortir — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Un sous-hub Sortir (pile à trier par personne, Envies communes, tirage « ce week-end », rappels sur Aujourd'hui) alimenté par la routine « Idées couple » via l'API de la Casa.

**Architecture:** Même découpage que la Cave : `voyage/sortir.py` (règles pures + page HTML/JS), table `sorties` dans `schema.sql` + fonctions dans `db.py`, routes dans `serveur.py`, encart dans `casa.py`, reprise unique `sorties_depart.py` posée par `appliquer_schema.py`. Le tri, le tirage et l'anti-doublon sont en Python (testés) ; la page appelle l'API.

**Tech Stack:** Python 3, Flask, psycopg2, Postgres (`valise_test` pour les tests), JS vanilla inline, pytest.

## Global Constraints

- Spec : `docs/superpowers/specs/2026-11-11-casa-sortir-design.md`.
- Pré-requis : branche `feat/casa-popote` mergée (barre à 4 entrées) ; travailler sur `feat/casa-sortir` depuis `main`.
- États : `a-trier`, `envie`, `prevue`, `faite`, `ecartee`. Avis : `None`, `"oui"`, `"non"`. Personnes : `"julien"`, `"laetitia"`.
- Types : `cine`, `theatre`, `concert`, `expo`, `resto-bar`, `balade`, `atelier`, `escapade` (libellés : Ciné, Théâtre, Concert, Expo, Resto / bar, Balade, Atelier, Escapade). Budgets : `gratuit`, `moyen`, `premium` (Gratuit, ~30 €, ~80 € +). Réservation : `non`, `conseillee`, `obligatoire`.
- Barre du bas : Aujourd'hui · Popote · Sortir · Budget · Vadrouille. Couleur `--sortir` : `#6d28d9` clair, `#b794f6` sombre (et `--sortir-doux` : `#f1eafe` / `#2a1a47`).
- `localStorage` : clé `casa-qui` (`julien` / `laetitia`), toujours dans un `try`. Pas d'emoji, pas d'`innerHTML`.
- Commandes depuis `voyage/` : `.venv/bin/python -m pytest`. Pas de push / PR sans OK de Julien après la démo.

---

### Task 1: Règles pures (`sortir.py`)

**Files:** Create `voyage/sortir.py`, `voyage/test_sortir.py`.

**Interfaces (Produces):**
- `TYPES`, `BUDGETS`, `RESERVATIONS`, `ETATS`, `QUI` (listes de couples `(clé, libellé)` sauf `ETATS`/`QUI` : tuples de clés).
- `valider_sortie(corps: dict, aujourd_hui: date) -> dict` ; lève `ValueError` (message en français).
- `cle_titre(titre: str) -> str` ; `cle_lien(lien: str) -> str`.
- `doublon(nouvelle: dict, existantes: list[dict]) -> str | None` (id de l'existante).
- `apres_avis(s: dict, qui: str, avis: str) -> dict` (nouvelle sortie, état recalculé).
- `tirer_weekend(sorties: list[dict], jour: date, hasard: random.Random) -> list[dict]`.
- `rappels(sorties: list[dict], jour: date) -> dict` : `{"finissent": [...], "prevues": [...], "weekend": bool}`.

- [ ] **Step 1: Tests** — `voyage/test_sortir.py` :

```python
"""Tests de sortir.py : validation, anti-doublon, avis, tirage du week-end, rappels (logique pure)."""
import sys
from datetime import date, timedelta
from pathlib import Path
from random import Random
sys.path.insert(0, str(Path(__file__).parent))

import pytest
from sortir import valider_sortie, cle_titre, cle_lien, doublon, apres_avis, tirer_weekend, rappels

J = date(2026, 11, 13)          # un vendredi


def s(id_, titre="Idée", etat="envie", type_="balade", budget="gratuit", fin=None, le=None, **k):
    return {"id": id_, "titre": titre, "etat": etat, "type": type_, "budget": budget, "debut": None, "fin": fin,
            "le": le, "lien": "", "avis_julien": "oui", "avis_laetitia": "oui", **k}


def test_valider_minimal_et_source():
    v = valider_sortie({"titre": "  Refuge des Fondus ", "source": "julien"}, J)
    assert v["titre"] == "Refuge des Fondus" and v["etat"] == "a-trier"
    assert v["avis_julien"] == "oui" and v["avis_laetitia"] is None          # ajout à la main = son « ça me tente »
    assert valider_sortie({"titre": "X", "source": "routine"}, J)["avis_julien"] is None


@pytest.mark.parametrize("modif", [{"titre": ""}, {"titre": "x" * 201}, {"type": "piscine"}, {"budget": "cher"},
                                   {"reservation": "peut-etre"}, {"lien": "ftp://x"}, {"source": "chat"},
                                   {"fin": "2026-13-01"}, {"debut": "2026-12-10", "fin": "2026-12-01"}])
def test_valider_refuse(modif):
    with pytest.raises(ValueError):
        valider_sortie({"titre": "X", "source": "routine", **modif}, J)


def test_cles_de_doublon():
    assert cle_titre("Le Refuge des Fondus !") == cle_titre("refuge  des fondus")
    assert cle_lien("https://www.x.fr/expo/?utm=1") == cle_lien("http://www.x.fr/expo")
    existantes = [s("a", "Atelier cosmétiques en duo chez Aroma-Zone", etat="ecartee", lien="https://aroma-zone.com/atelier")]
    assert doublon({"titre": "atelier cosmetiques en duo chez aroma zone", "lien": ""}, existantes) == "a"
    assert doublon({"titre": "Autre", "lien": "https://aroma-zone.com/atelier/"}, existantes) == "a"
    assert doublon({"titre": "Autre", "lien": ""}, existantes) is None


def test_avis():
    x = s("a", etat="a-trier", avis_julien="oui", avis_laetitia=None)
    assert apres_avis(x, "laetitia", "oui")["etat"] == "envie"
    assert apres_avis(x, "laetitia", "non")["etat"] == "ecartee"
    assert apres_avis(s("b", etat="a-trier", avis_julien=None, avis_laetitia=None), "julien", "oui")["etat"] == "a-trier"
    with pytest.raises(ValueError):
        apres_avis(x, "gaia", "oui")


def test_tirage_priorite_fin_proche_une_premium_types_varies():
    envies = [s("fin", type_="expo", fin=J + timedelta(days=10)), s("p1", type_="concert", budget="premium"),
              s("p2", type_="theatre", budget="premium"), s("b1", type_="balade"), s("b2", type_="balade"),
              s("faite", etat="faite")]
    for graine in range(30):
        t = tirer_weekend(envies, J, Random(graine))
        ids = [x["id"] for x in t]
        assert 2 <= len(t) <= 3 and ids[0] == "fin" and "faite" not in ids
        assert sum(x["budget"] == "premium" for x in t) <= 1
        assert len({x["type"] for x in t}) == len(t)


def test_tirage_ignore_fin_passee_et_rend_ce_qu_il_peut():
    assert tirer_weekend([s("vieux", fin=J - timedelta(days=1))], J, Random(1)) == []
    assert [x["id"] for x in tirer_weekend([s("seul")], J, Random(1))] == ["seul"]


def test_rappels():
    sorties = [s("fin", fin=J + timedelta(days=5)), s("loin", fin=J + timedelta(days=20)),
               s("prevue", etat="prevue", le=J + timedelta(days=1)), s("passee", etat="prevue", le=J - timedelta(days=2))]
    r = rappels(sorties, J)
    assert [x["id"] for x in r["finissent"]] == ["fin"] and [x["id"] for x in r["prevues"]] == ["prevue"]
    assert r["weekend"] is True and rappels(sorties, J - timedelta(days=4))["weekend"] is False
```

- [ ] **Step 2:** `.venv/bin/python -m pytest test_sortir.py -q` → FAIL (`No module named 'sortir'`).

- [ ] **Step 3: Implémentation** — `voyage/sortir.py` (en-tête de module puis le code) :

```python
"""Casa Binomerie — Sortir : les envies du couple. Une pile à trier par personne, les Envies (ça plaît aux deux), le
tirage « ce week-end », les rappels de fin et de date prévue. Règles pures ici ; la page plus bas (sortir_en_html)."""
import re
import unicodedata
from datetime import date, timedelta
from urllib.parse import urlsplit

TYPES = [("cine", "Ciné"), ("theatre", "Théâtre"), ("concert", "Concert"), ("expo", "Expo"),
         ("resto-bar", "Resto / bar"), ("balade", "Balade"), ("atelier", "Atelier"), ("escapade", "Escapade")]
BUDGETS = [("gratuit", "Gratuit"), ("moyen", "~30 €"), ("premium", "~80 € +")]
RESERVATIONS = [("non", "Sans réservation"), ("conseillee", "Réservation conseillée"), ("obligatoire", "À réserver")]
ETATS = ("a-trier", "envie", "prevue", "faite", "ecartee")
QUI = ("julien", "laetitia")
MOTS_VIDES = {"le", "la", "les", "l", "un", "une", "des", "de", "du", "d", "au", "aux", "a", "et", "en", "chez"}
FIN_PROCHE = 15          # jours : priorité au tirage
RAPPEL = 7               # jours : encart d'Aujourd'hui


def _date(valeur, cle):
    if not valeur:
        return None
    try:
        return date.fromisoformat(str(valeur)[:10])
    except ValueError:
        raise ValueError(f"{cle} : date invalide")


def _choix(corps, cle, options, defaut=None):
    v = corps.get(cle) or defaut
    if v is not None and v not in [o[0] if isinstance(o, tuple) else o for o in options]:
        raise ValueError(f"{cle} invalide")
    return v


def valider_sortie(corps, aujourd_hui):
    """Une idée validée, prête pour la base. Ajoutée par Julien ou Laetitia : leur avis est « oui »."""
    titre = " ".join(str(corps.get("titre") or "").split())
    if not 1 <= len(titre) <= 200:
        raise ValueError("titre : 1 à 200 caractères")
    lien = str(corps.get("lien") or "").strip()
    if lien and not re.match(r"https?://", lien):
        raise ValueError("lien : http ou https")
    source = _choix(corps, "source", ("routine",) + QUI)
    if source is None:
        raise ValueError("source manquante")
    debut, fin = _date(corps.get("debut"), "debut"), _date(corps.get("fin"), "fin")
    if debut and fin and fin < debut:
        raise ValueError("fin avant le début")
    return {"titre": titre, "type": _choix(corps, "type", TYPES), "budget": _choix(corps, "budget", BUDGETS),
            "reservation": _choix(corps, "reservation", RESERVATIONS), "debut": debut, "fin": fin, "lien": lien,
            "infos": str(corps.get("infos") or "").strip()[:1000], "source": source, "etat": "a-trier",
            "avis_julien": "oui" if source == "julien" else None,
            "avis_laetitia": "oui" if source == "laetitia" else None}


def _sans_accents(texte):
    texte = texte.lower().replace("œ", "oe").replace("æ", "ae")
    return "".join(c for c in unicodedata.normalize("NFD", texte) if unicodedata.category(c) != "Mn")


def cle_titre(titre):
    """« Le Refuge des Fondus ! » -> « refuge fondus » : casse, accents, ponctuation et mots vides retirés."""
    mots = re.findall(r"[a-z0-9]+", _sans_accents(titre))
    return " ".join(m for m in mots if m not in MOTS_VIDES)


def cle_lien(lien):
    """L'adresse sans protocole, sans « www. », sans query string ni « / » final."""
    if not lien:
        return ""
    p = urlsplit(lien.strip().lower())
    return (p.netloc.removeprefix("www.") + p.path).rstrip("/")


def doublon(nouvelle, existantes):
    """L'id d'une idée déjà en base (tout état) au même titre ou au même lien, sinon None."""
    t, l = cle_titre(nouvelle["titre"]), cle_lien(nouvelle.get("lien", ""))
    for e in existantes:
        if cle_titre(e["titre"]) == t or (l and cle_lien(e.get("lien", "")) == l):
            return e["id"]
    return None


def apres_avis(s, qui, avis):
    """L'idée après l'avis de qui : un « non » l'écarte, deux « oui » en font une Envie."""
    if qui not in QUI or avis not in ("oui", "non"):
        raise ValueError("avis invalide")
    s = {**s, f"avis_{qui}": avis}
    if avis == "non":
        s["etat"] = "ecartee"
    elif s["etat"] == "a-trier" and s["avis_julien"] == "oui" and s["avis_laetitia"] == "oui":
        s["etat"] = "envie"
    return s


def tirer_weekend(sorties, jour, hasard):
    """2 à 3 Envies : celles qui finissent dans FIN_PROCHE jours d'abord, puis au hasard ; une Premium au plus,
    jamais deux du même type. Une Envie déjà finie est ignorée."""
    envies = [s for s in sorties if s["etat"] == "envie" and not (s.get("fin") and s["fin"] < jour)]
    proches = sorted((s for s in envies if s.get("fin") and s["fin"] <= jour + timedelta(days=FIN_PROCHE)),
                     key=lambda s: s["fin"])
    reste = [s for s in envies if s not in proches]
    hasard.shuffle(reste)
    choix = []
    for s in proches + reste:
        if len(choix) == 3:
            break
        if s["type"] in {c["type"] for c in choix}:
            continue
        if s["budget"] == "premium" and any(c["budget"] == "premium" for c in choix):
            continue
        choix.append(s)
    return choix


def rappels(sorties, jour):
    """Pour Aujourd'hui : les Envies qui finissent dans RAPPEL jours, les sorties prévues dans RAPPEL jours, et si
    c'est le moment du tirage (vendredi, samedi)."""
    limite = jour + timedelta(days=RAPPEL)
    finissent = sorted((s for s in sorties if s["etat"] == "envie" and s.get("fin") and jour <= s["fin"] <= limite),
                       key=lambda s: s["fin"])
    prevues = sorted((s for s in sorties if s["etat"] == "prevue" and s.get("le") and jour <= s["le"] <= limite),
                     key=lambda s: s["le"])
    return {"finissent": finissent, "prevues": prevues, "weekend": jour.weekday() in (4, 5)}
```

Note : `test_valider_refuse` avec `{"type": "piscine"}` passe par `_choix` ; avec `{"titre": ""}` par la longueur.

- [ ] **Step 4:** `.venv/bin/python -m pytest test_sortir.py -q` → PASS.
- [ ] **Step 5: Commit** — `git add voyage/sortir.py voyage/test_sortir.py && git commit -m "feat(sortir): règles (validation, anti-doublon, avis, tirage, rappels)"`.

---

### Task 2: Table et fonctions de base

**Files:** Modify `voyage/schema.sql` (à la fin), `voyage/db.py` (section nouvelle en fin de fichier) ; Create `voyage/test_sortir_db.py`.

**Interfaces:**
- Consumes: `sortir.valider_sortie`, `sortir.doublon`, `sortir.apres_avis`.
- Produces: `db.lire_sorties(conn) -> list[dict]` ; `db.creer_sortie(conn, s: dict) -> tuple[str, bool]` (id, créée ? — `False` = doublon, id de l'existante) ; `db.donner_avis(conn, id, qui, avis) -> dict | None` ; `db.maj_sortie(conn, id, champs: dict) -> dict | None` (champs ∈ `etat`, `le`, `pouce`, `retour`) ; `db.poser_sorties(conn, nom_reprise, sorties) -> int | None`.

- [ ] **Step 1: Schéma** — fin de `schema.sql` :

```sql
-- Sortir : les envies du couple (ajouté le 11/11/2026)
CREATE TABLE IF NOT EXISTS sorties (
    id            TEXT        PRIMARY KEY,
    titre         TEXT        NOT NULL,
    type          TEXT,
    budget        TEXT,
    reservation   TEXT,
    debut         DATE,
    fin           DATE,
    lien          TEXT        NOT NULL DEFAULT '',
    infos         TEXT        NOT NULL DEFAULT '',
    source        TEXT        NOT NULL,
    avis_julien   TEXT        CHECK (avis_julien IN ('oui', 'non')),
    avis_laetitia TEXT        CHECK (avis_laetitia IN ('oui', 'non')),
    etat          TEXT        NOT NULL DEFAULT 'a-trier'
                              CHECK (etat IN ('a-trier', 'envie', 'prevue', 'faite', 'ecartee')),
    le            DATE,
    pouce         TEXT        CHECK (pouce IN ('haut', 'bas')),
    retour        TEXT        NOT NULL DEFAULT '',
    cree_le       TIMESTAMPTZ NOT NULL DEFAULT now(),
    maj_le        TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

Vérifier comment les tests créent le schéma dans `valise_test` (fixture ou `appliquer_schema`) et que la nouvelle table y est créée ; ajouter `sorties` au `TRUNCATE` de la fixture du nouveau fichier de test.

- [ ] **Step 2: Tests** — `voyage/test_sortir_db.py` (même fixture `conn` que `test_cave_db.py`, `TRUNCATE sorties, reprises`) :

```python
def test_creer_lire_et_doublon(conn):
    from db import creer_sortie, lire_sorties
    id1, cree = creer_sortie(conn, valider_sortie({"titre": "Refuge des Fondus", "source": "routine"}, J))
    assert cree and id1.startswith("sortie-")
    id2, cree2 = creer_sortie(conn, valider_sortie({"titre": "le refuge des fondus", "source": "julien"}, J))
    assert (id2, cree2) == (id1, False)
    (x,) = lire_sorties(conn)
    assert x["titre"] == "Refuge des Fondus" and x["etat"] == "a-trier" and x["avis_julien"] is None


def test_avis_jusqu_a_l_envie_puis_maj(conn):
    from db import creer_sortie, donner_avis, maj_sortie
    i, _ = creer_sortie(conn, valider_sortie({"titre": "Catch Impro", "source": "julien"}, J))
    assert donner_avis(conn, i, "laetitia", "oui")["etat"] == "envie"
    assert maj_sortie(conn, i, {"etat": "prevue", "le": "2026-11-21"})["le"] == date(2026, 11, 21)
    f = maj_sortie(conn, i, {"etat": "faite", "pouce": "haut", "retour": "Génial"})
    assert (f["etat"], f["pouce"], f["retour"]) == ("faite", "haut", "Génial")
    assert donner_avis(conn, "inconnue", "julien", "oui") is None
    with pytest.raises(ValueError):
        maj_sortie(conn, i, {"etat": "volee"})


def test_poser_sorties_une_seule_fois(conn):
    from db import poser_sorties, lire_sorties
    depart = [{"titre": "Balade Campagne à Paris", "source": "routine", "type": "balade", "budget": "gratuit"}]
    assert poser_sorties(conn, "sorties-test", depart) == 1
    assert poser_sorties(conn, "sorties-test", depart) is None and len(lire_sorties(conn)) == 1
```

(imports en tête : `pytest`, `date` de `datetime`, `valider_sortie` de `sortir`, `J = date(2026, 11, 13)`.)

- [ ] **Step 3:** FAIL attendu (`cannot import name 'creer_sortie'`).

- [ ] **Step 4: Implémentation** — fin de `db.py` :

```python
# --- Casa Binomerie : Sortir --------------------------------------------------------------------

CHAMPS_SORTIE = ("titre", "type", "budget", "reservation", "debut", "fin", "lien", "infos", "source", "avis_julien",
                 "avis_laetitia", "etat", "le", "pouce", "retour")


def lire_sorties(conn):
    """Toutes les idées de sorties, les plus récentes d'abord (la page trie)."""
    with conn.cursor() as cur:
        cur.execute(f"SELECT id, {', '.join(CHAMPS_SORTIE)}, cree_le FROM sorties ORDER BY cree_le DESC, id")
        return [dict(zip(("id", *CHAMPS_SORTIE, "cree_le"), l)) for l in cur.fetchall()]


def creer_sortie(conn, s):
    """Une idée validée (sortir.valider_sortie). Déjà là (sortir.doublon, tout état) : (id existant, False)."""
    from sortir import doublon
    import uuid
    existant = doublon(s, lire_sorties(conn))
    if existant:
        return existant, False
    identifiant = "sortie-" + uuid.uuid4().hex[:12]
    champs = [c for c in CHAMPS_SORTIE if c in s]
    with conn.cursor() as cur:
        cur.execute(f"INSERT INTO sorties (id, {', '.join(champs)}) VALUES (%s, {', '.join(['%s'] * len(champs))})",
                    (identifiant, *[s[c] for c in champs]))
    conn.commit()
    return identifiant, True


def _une_sortie(conn, identifiant):
    return next((s for s in lire_sorties(conn) if s["id"] == identifiant), None)


def donner_avis(conn, identifiant, qui, avis):
    """L'avis de qui (sortir.apres_avis) ; None si l'idée n'existe pas."""
    from sortir import apres_avis
    s = _une_sortie(conn, identifiant)
    if s is None:
        return None
    n = apres_avis(s, qui, avis)
    with conn.cursor() as cur:
        cur.execute(f"UPDATE sorties SET avis_{qui} = %s, etat = %s, maj_le = now() WHERE id = %s",
                    (n[f"avis_{qui}"], n["etat"], identifiant))
    conn.commit()
    return _une_sortie(conn, identifiant)


def maj_sortie(conn, identifiant, champs):
    """État, date prévue, pouce, retour. ValueError sur une valeur invalide ; None si l'idée n'existe pas."""
    from sortir import ETATS
    from datetime import date as _d
    permis = {}
    if "etat" in champs:
        if champs["etat"] not in ETATS:
            raise ValueError("état invalide")
        permis["etat"] = champs["etat"]
    if "le" in champs:
        permis["le"] = _d.fromisoformat(champs["le"]) if champs["le"] else None
    if "pouce" in champs:
        if champs["pouce"] not in (None, "haut", "bas"):
            raise ValueError("pouce invalide")
        permis["pouce"] = champs["pouce"]
    if "retour" in champs:
        permis["retour"] = str(champs["retour"] or "").strip()[:500]
    if _une_sortie(conn, identifiant) is None:
        return None
    if permis:
        with conn.cursor() as cur:
            cur.execute(f"UPDATE sorties SET {', '.join(f'{c} = %s' for c in permis)}, maj_le = now() WHERE id = %s",
                        (*permis.values(), identifiant))
        conn.commit()
    return _une_sortie(conn, identifiant)


def poser_sorties(conn, nom_reprise, sorties):
    """Les sorties de départ (sorties_depart.py), une seule fois (table reprises) ; renvoie le nombre ajouté, ou None
    si la reprise est déjà passée. Les doublons sont ignorés."""
    from sortir import valider_sortie
    from casa import aujourd_hui_paris
    with conn.cursor() as cur:
        cur.execute("SELECT EXISTS (SELECT 1 FROM reprises WHERE nom = %s)", (nom_reprise,))
        if cur.fetchone()[0]:
            return None
    n = sum(creer_sortie(conn, valider_sortie(s, aujourd_hui_paris()))[1] for s in sorties)
    with conn.cursor() as cur:
        cur.execute("INSERT INTO reprises (nom) VALUES (%s)", (nom_reprise,))
    conn.commit()
    return n
```

Vérifier les colonnes réelles de `reprises` (`grep -n "CREATE TABLE IF NOT EXISTS reprises" -A5 schema.sql`) et le style de `poser_cave` (db.py ~1118) ; s'aligner dessus (nom de colonne, commit).

- [ ] **Step 5:** `.venv/bin/python -m pytest test_sortir_db.py -q` → PASS ; suite complète → PASS.
- [ ] **Step 6: Commit** — `feat(sortir): table sorties et fonctions de base`.

---

### Task 3: API

**Files:** Modify `voyage/serveur.py` (imports + nouvelle section « Sortir » après la Cave) ; tests dans `voyage/test_sortir_db.py` (fixture `client` comme `test_cave_db.py`).

**Interfaces (Produces):** `GET /api/sorties` → `{"sorties": [...], "aujourd_hui": "YYYY-MM-DD"}` (dates en ISO) ; `POST /api/sorties` (JSON) → 201 `{"id"}` / 409 `{"id", "doublon": true}` / 400 `{"erreur"}` ; `POST /api/sorties/<id>/avis` `{"qui", "avis"}` → 200 sortie / 400 / 404 ; `POST /api/sorties/<id>` `{etat?, le?, pouce?, retour?}` → 200 / 400 / 404 ; `GET /api/sorties/weekend` → `{"tirage": [...]}` (hasard du serveur).

- [ ] **Step 1: Tests** :

```python
def test_api_sorties(client):
    r = client.post("/api/sorties", json={"titre": "Refuge des Fondus", "source": "routine", "type": "resto-bar"})
    assert r.status_code == 201 and r.get_json()["id"].startswith("sortie-")
    i = r.get_json()["id"]
    r2 = client.post("/api/sorties", json={"titre": "refuge des fondus", "source": "julien"})
    assert r2.status_code == 409 and r2.get_json() == {"id": i, "doublon": True}
    assert client.post("/api/sorties", json={"titre": "", "source": "julien"}).status_code == 400
    assert client.post(f"/api/sorties/{i}/avis", json={"qui": "julien", "avis": "oui"}).get_json()["etat"] == "a-trier"
    assert client.post(f"/api/sorties/{i}/avis", json={"qui": "laetitia", "avis": "oui"}).get_json()["etat"] == "envie"
    assert client.post(f"/api/sorties/{i}", json={"etat": "prevue", "le": "2026-11-21"}).get_json()["le"] == "2026-11-21"
    assert client.post("/api/sorties/inconnue/avis", json={"qui": "julien", "avis": "oui"}).status_code == 404
    assert client.post(f"/api/sorties/{i}", json={"etat": "volee"}).status_code == 400
    d = client.get("/api/sorties").get_json()
    assert [x["id"] for x in d["sorties"]] == [i] and "aujourd_hui" in d
    assert client.get("/api/sorties/weekend").status_code == 200
```

- [ ] **Step 2:** FAIL (404).
- [ ] **Step 3: Routes** — suivre le motif des routes de la Cave (`emprunter(app.config["NOM_BASE"])`, `try/finally conn.close()`, `jsonify`). Sérialiser les `date` en ISO (helper local `_iso(s)` qui convertit `debut`, `fin`, `le`, `cree_le`). `weekend` : `tirer_weekend(lire_sorties(conn), aujourd_hui_paris(), random.Random())`.
- [ ] **Step 4:** PASS ; suite complète PASS.
- [ ] **Step 5: Commit** — `feat(sortir): API (lire, créer avec anti-doublon, avis, mise à jour, tirage)`.

---

### Task 4: Page Sortir et barre du bas

**Files:** Modify `voyage/sortir.py` (`STYLE_SORTIR`, `SCRIPT_SORTIR`, `sortir_en_html()`), `voyage/design.py` (`HUB`, `ICONES_HUB["sortir"]`, `--sortir` dans `STYLE_NAV_HUB` clair + `sombre(...)`, règle `nav.hub a[data-hub="sortir"]`), `voyage/serveur.py` (`GET /sortir`), `voyage/valise.py` (`VERSION_PAGE = 49`) ; tests `voyage/test_sortir.py`, `voyage/test_casa.py`, `voyage/test_design.py` (`test_aucun_emoji_dans_les_pages` : ajouter `sortir_en_html()`).

**Interfaces:** Consumes the API of Task 3. Produces `sortir_en_html() -> str`.

- [ ] **Step 1: Tests** :

```python
def test_page_sortir():
    from sortir import sortir_en_html
    html = sortir_en_html()
    assert "<title>Sortir · Casa Binomerie</title>" in html and 'data-hub="sortir" class="actif"' in html
    for v in ("a-trier", "envies", "faites"):
        assert f'data-vue="{v}"' in html
    for f in ("function vueATrier", "function vueEnvies", "function vueFaites", "function tirage", "function quiSuisJe",
              "function ajouterIdee", "api/sorties", "casa-qui"):
        assert f in html, f
    for mot in ("Bof", "Ça me tente", "Ce week-end ?", "On y va", "Plus envie", "+ Ajouter une idée",
                "Alors, c'était comment ?", "Rien à trier."):
        assert mot in html, mot
    assert "innerHTML" not in html
```

et dans `test_casa.py`, la liste attendue de la barre devient `["aujourdhui", "popote", "sortir", "budget", "vadrouille"]`.

- [ ] **Step 2:** FAIL.
- [ ] **Step 3: Barre** — `HUB` : insérer `("sortir", "Sortir", "sortir")` après Popote. Icône billet : `_TRAIT.format('<path d="M3 8a2 2 0 0 0 2-2h14a2 2 0 0 0 2 2v2a2 2 0 0 0 0 4v2a2 2 0 0 0-2 2H5a2 2 0 0 0-2-2v-2a2 2 0 0 0 0-4z"/><path d="M14 6v12" stroke-dasharray="2 2"/>')`. Couleurs : ajouter `--sortir: #6d28d9; --sortir-doux: #f1eafe;` au `:root` de `STYLE_NAV_HUB` et `--sortir: #b794f6; --sortir-doux: #2a1a47;` dans son bloc `sombre(...)` ; règle `nav.hub a[data-hub="sortir"] { --c: var(--sortir); --c-doux: var(--sortir-doux); }`.
- [ ] **Step 4: Page** — `sortir_en_html()` sur le modèle de `cave_en_html()` (tête PWA + police, `STYLE_D`, `STYLE_NAV_HUB`, `STYLE_HORS_LIGNE`, `STYLE_SORTIR`, `body class="accueil hub-page sortir"`, `<h1>Sortir</h1>`, `nav.vues` à 3 onglets — réutiliser le style des onglets de Dîners : copier ses règles `nav.vues` en les préfixant `body.sortir` —, zone `#vue`, `{nav_hub("sortir")}`, `SCRIPT_FILE` pour la file hors ligne comme Dîners/Cave, `SCRIPT_SORTIR`). JS (vanilla, `el()` comme Dîners, aucune chaîne HTML) :
  - `quiSuisJe()` : lit `casa-qui` (try) ; absent → carte « Qui es-tu ? » [Julien] [Laetitia], écrit `casa-qui`, puis `afficher()`. Petit lien « Changer » sous le titre.
  - `vueATrier` : les idées `etat === 'a-trier'` dont `avis_<qui>` est null, plus anciennes d'abord ; une carte (titre, libellés type/budget/réservation, « jusqu'au JJ/MM » si `fin`, infos, lien « Voir » `target=_blank rel=noopener`) ; boutons **Bof** / **Ça me tente** → `POST api/sorties/<id>/avis` via la file, mise à jour locale optimiste ; vide → « Rien à trier. ». Compteur sur l'onglet.
  - `vueEnvies` : `etat === 'envie'` ou `'prevue'` (prévues en tête avec leur date), puis fin proche, puis récentes ; bouton **Ce week-end ?** → `tirage()` (`GET api/sorties/weekend`, affiche 2-3 cartes, **Retirer** relance) ; par carte **On y va** (champ date natif → `etat: prevue, le`), **Fait** (→ faite, puis pouce + retour), **Plus envie** (→ ecartee) ; **+ Ajouter une idée** → `ajouterIdee()` (formulaire : titre obligatoire, type, budget, fin, lien ; `source = qui` ; 409 → « Déjà dans la liste »).
  - `vueFaites` : prévues dont la date est passée en tête avec « Alors, c'était comment ? » (pouce haut/bas + retour → faite) ; puis faites, récentes d'abord, avec pouce et retour.
  - Libellés des types/budgets/réservations injectés en JSON depuis `TYPES`, `BUDGETS`, `RESERVATIONS`.
- [ ] **Step 5: Route** `GET /sortir` → `Response(sortir_en_html(), mimetype="text/html")` ; `VERSION_PAGE = 49`.
- [ ] **Step 6:** tests PASS ; suite complète PASS ; `node --check` du `SCRIPT_SORTIR` extrait (fichier temporaire dans le scratchpad).
- [ ] **Step 7: Commit** — `feat(sortir): page Sortir (À trier, Envies, Faites) et entrée dans la barre`.

---

### Task 5: Encart sur Aujourd'hui

**Files:** Modify `voyage/casa.py` (`bloc_sortir`, `aujourdhui_en_html` paramètre `sortir=None`, style), `voyage/serveur.py` (page d'accueil : `rappels(lire_sorties(conn), jour)`) ; tests `voyage/test_casa.py`.

**Interfaces:** Consumes `sortir.rappels`. Produces `casa.bloc_sortir(r: dict, aujourd_hui: date) -> str` ("" si rien).

- [ ] **Step 1: Tests** :

```python
def test_bloc_sortir():
    from casa import bloc_sortir
    j = date(2026, 11, 13)
    vide = {"finissent": [], "prevues": [], "weekend": False}
    assert bloc_sortir(vide, j) == ""
    r = {"finissent": [{"id": "a", "titre": "Expo X", "fin": j + timedelta(days=5)}],
         "prevues": [{"id": "b", "titre": "Refuge des Fondus", "le": j + timedelta(days=1)}], "weekend": True}
    html = bloc_sortir(r, j)
    assert 'class="bloc-sortir"' in html and "Expo X" in html and "finit dans 5 jours" in html
    assert "Refuge des Fondus" in html and "demain" in html and 'href="sortir#envies"' in html and "Ce week-end ?" in html
    assert "<script" not in html
```

- [ ] **Step 2:** FAIL.
- [ ] **Step 3: Implémentation** — `bloc_sortir` : titres échappés (`echapper`), « finit dans N jours » / « finit aujourd'hui », date prévue via le helper existant `_quand(jour, aujourd_hui)` (« demain », « samedi »…) ; si `weekend`, un lien « Ce week-end ? » vers `sortir#envies` ; style `div.bloc-sortir` calqué sur `div.bloc-a-finir` avec `--sortir`. Placé après `bloc_a_finir` dans `aujourdhui_en_html`. Côté serveur, lire les sorties dans le même `try` que le reste et passer `sortir=rappels(...)`.
- [ ] **Step 4:** PASS ; suite complète PASS.
- [ ] **Step 5: Commit** — `feat(sortir): rappels et « ce week-end » sur Aujourd'hui`.

---

### Task 6: Reprise des idées Notion

**Files:** Create `voyage/sorties_depart.py` (fourni par le contrôleur : `NOM_REPRISE = "sorties-v1"`, `SORTIES_DEPART = [...]`, sorties uniquement, dédoublonnées, `source: "routine"`, champs `titre/type/budget/reservation/lien/infos/fin`) ; Modify `voyage/appliquer_schema.py` (poser comme `poser_cave`, mode à blanc compris) ; test dans `voyage/test_sortir_db.py`.

- [ ] **Step 1: Test** — `SORTIES_DEPART` valide (chaque entrée passe `valider_sortie`), aucun doublon entre elles (`doublon`), et aucun titre ne contient « bon cadeau » / « soin » / « spa day » (cadeaux exclus).
- [ ] **Step 2:** brancher `poser_sorties(conn, NOM_REPRISE, SORTIES_DEPART)` dans `appliquer_schema.py` (appliquer et à blanc), avec le message « Sortir : N idée(s) de départ ajoutée(s). ».
- [ ] **Step 3:** suite complète PASS. **Commit** — `feat(sortir): reprise des idées de sorties Notion`.

---

### Task 7: Démo

- [ ] Copie de prod → `valise_copie`, `appliquer_schema` sur la copie (table + reprise), serveur `:8001`.
- [ ] Julien + Laetitia : barre à 5 entrées ; « Qui es-tu ? » sur chaque téléphone ; trier quelques idées chacun → une Envie apparaît quand les deux ont dit oui ; Bof l'écarte ; Ce week-end ? ; On y va → date → Aujourd'hui l'annonce ; ajout à la main → part dans la pile de l'autre ; doublon refusé ; thème clair / sombre ; 375 px.

### Task 8 (contrôleur, après merge et déploiement) : routine « Idées couple »

- [ ] Montrer à Julien la nouvelle consigne avant toute modification ; avec son OK, `RemoteTrigger update` de `trig_01VKgD8QDkxndhNCmDSZRhU6` : sorties → `POST https://<app>/v/<secret>/api/sorties` (URL dans une variable d'environnement de la routine, pas dans le texte) après `GET api/sorties` (écartées, faites, retours) ; 5 idées dont au plus 1 Premium ; cadeaux toujours dans Notion. Puis `run` une fois et vérifier qu'elles arrivent dans la pile.
