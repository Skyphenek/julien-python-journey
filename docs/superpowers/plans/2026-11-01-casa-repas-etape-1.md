# Casa Binomerie — Repas composés, étape 1 : plan d'implémentation

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal :** passer de « un soir = un plat » (table `soirs`) à « un repas = plusieurs plats » (table `repas`), avec déjeuner et brunch à la demande, sans perdre l'historique du compteur Deliveroo.

**Architecture :** nouvelle table `repas` (clé `jour, moment`, `plats` en JSONB) remplie une fois depuis `soirs` (reprise `repas-v1`). Toute la logique (validation, compteur, courses, coût, proposer) passe sur des dicts `{jour, moment, plats, issue}`. `POST api/repas` remplace `api/soirs` ; la page Dîners affiche des cartes composées.

**Tech Stack :** Python 3 + Flask, psycopg2 (Postgres local `valise_test`, Neon en prod), pytest, JS vanilla ES5 (style `function`, pas de flèches) inline dans `diners.py`.

**Spec :** `docs/superpowers/specs/2026-11-01-casa-repas-composes-design.md` (étape 1 seulement ; les accords = étape 2).

## Global Constraints

- Branche : `feat/casa-repas` (déjà créée, la spec y est commitée). Tout se fait dans `voyage/`.
- Tests : `cd voyage && .venv/bin/python3 -m pytest -q` — 636 verts au départ ; tout doit rester vert à chaque commit.
- Après un changement de `schema.sql` : `DATABASE_URL="" .venv/bin/python3 appliquer_schema.py --base valise_test --appliquer`.
- Moments : `diner`, `dejeuner`, `brunch`. Issues : `fait`, `commande`, `dehors`, `autre` (ou `None`).
- Validation d'un repas : jour de −60 à +30 jours, moment connu, `plats` = liste de 0 à 8 ids (format `_ID`) sans doublon, issue connue ou nulle.
- Un repas sans plat ni issue est supprimé de la base.
- Ordre d'affichage : entrée, plat, accompagnement, dessert ; au brunch, ordre d'ajout.
- Compteur Deliveroo : repas `diner` seulement.
- `VERSION_PAGE` (valise.py) : 36 → 37.
- Migration Neon : à blanc d'abord ; `--appliquer` sur Neon seulement avec l'accord explicite de Julien, juste AVANT le merge. Push / PR / merge seulement sur demande (`env -u GITHUB_TOKEN gh …`).
- `soirs` n'est plus écrite ni lue par l'app après cette étape (suppression de la table : livraison ultérieure).
- Commits en français, préfixe `feat:` / `test:` / `docs:`, terminés par `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

## Fichiers

| Fichier | Rôle dans l'étape |
|---|---|
| `voyage/schema.sql` | + table `repas` |
| `voyage/db.py` | + `enregistrer_repas`, `lire_repas`, `reprendre_soirs` ; − `enregistrer_soir`, `lire_soirs` |
| `voyage/appliquer_schema.py` | lance la reprise `repas-v1` |
| `voyage/diners.py` | + `MOMENTS`, `valider_repas`, `ranger`, `repas_prevus` ; `compteur`, `proposer`, `cout_semaine` sur les repas ; − `valider_soir` ; JS/CSS de la page |
| `voyage/serveur.py` | `GET api/diners` (clé `repas`), `POST api/repas`, courses, proposer, accueil |
| `voyage/casa.py` | Aujourd'hui : « Ce soir » liste le dîner, « Hier soir ? » poste sur `api/repas` |
| `voyage/valise.py` | `VERSION_PAGE = 37` |
| `voyage/test_repas.py` (nouveau) | validation, rangement, base, reprise |
| `voyage/test_diners.py`, `test_diners_db.py`, `test_casa.py`, `test_serveur.py` | adaptés |

**Risque accepté :** une page Dîners encore en cache sur un téléphone au moment du déploiement posterait sur `api/soirs` (404 → l'envoi est abandonné, le choix disparaît au rechargement, on le refait). `VERSION_PAGE` +1 force la mise à jour du service worker.

---

### Task 1 : table `repas`, lecture/écriture en base, reprise `repas-v1`

**Files:**
- Modify: `voyage/schema.sql` (après la table `soirs`, fin de fichier)
- Modify: `voyage/db.py` (section « Casa Binomerie : dîners », après `lire_soirs` ~l. 714)
- Modify: `voyage/appliquer_schema.py`
- Modify: `voyage/test_diners_db.py:22` et `voyage/test_serveur.py:15` (TRUNCATE)
- Create: `voyage/test_repas.py`

**Interfaces:**
- Produces :
  - `db.enregistrer_repas(conn, r: dict) -> None` — `r = {"jour": date, "moment": str, "plats": list[str], "issue": str|None}` ; supprime si `plats` vide et `issue` nulle ; issue `fait` → chaque plat « à tester » du repas passe au carnet ; commit.
  - `db.lire_repas(conn, debut: date, fin: date) -> list[dict]` — mêmes clés, triés par jour puis moment.
  - `db.reprendre_soirs(conn) -> int | None` — sans commit ; `None` si la reprise `repas-v1` est déjà faite.

- [ ] **Step 1 : le schéma**

Ajouter à la fin de `voyage/schema.sql` :

```sql
-- Un repas = plusieurs plats (01/11/2026) : le dîner de chaque jour, un déjeuner ou un brunch à la demande.
-- plats : ids de plats, dans l'ordre d'ajout. Remplace `soirs` (gardée en lecture, reprise repas-v1).
CREATE TABLE IF NOT EXISTS repas (
    jour        DATE        NOT NULL,
    moment      TEXT        NOT NULL CHECK (moment IN ('diner', 'dejeuner', 'brunch')),
    plats       JSONB       NOT NULL DEFAULT '[]',
    issue       TEXT        CHECK (issue IN ('fait', 'commande', 'dehors', 'autre')),
    maj_le      TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (jour, moment)
);
```

Puis : `cd voyage && DATABASE_URL="" .venv/bin/python3 appliquer_schema.py --base valise_test --appliquer`
Attendu : `Schéma appliqué ; table(s) créée(s) : repas.`

- [ ] **Step 2 : les TRUNCATE des tests**

`voyage/test_diners_db.py:22` : `cur.execute("TRUNCATE soirs, plats, courses, placard, reprises")` → `cur.execute("TRUNCATE repas, soirs, plats, courses, placard, reprises")`.
`voyage/test_serveur.py:15` : ajouter `repas` juste avant `soirs` dans la liste du TRUNCATE.

- [ ] **Step 3 : écrire les tests en base (échouent)**

Créer `voyage/test_repas.py` :

```python
"""Tests des repas composés : validation, rangement (diners.py), base et reprise depuis soirs (db.py)."""
import sys
from datetime import date, timedelta
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pytest
from casa import aujourd_hui_paris
from carnet_depart import CARNET_DEPART, A_TESTER
from courses import PLACARD_DEPART
from db import connecter, semer_carnet, semer_placard, lire_plats, enregistrer_repas, lire_repas, reprendre_soirs

J = aujourd_hui_paris()


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


def statut(conn, id_):
    return next(p for p in lire_plats(conn) if p["id"] == id_)["statut"]


# --- Base ---

def test_enregistrer_et_lire_un_repas(conn):
    enregistrer_repas(conn, {"jour": J, "moment": "diner", "plats": ["plat-carbonara", "tester-pesto"], "issue": None})
    enregistrer_repas(conn, {"jour": J, "moment": "brunch", "plats": ["tester-shakshuka"], "issue": None})
    assert lire_repas(conn, J, J) == [
        {"jour": J, "moment": "brunch", "plats": ["tester-shakshuka"], "issue": None},
        {"jour": J, "moment": "diner", "plats": ["plat-carbonara", "tester-pesto"], "issue": None}]
    enregistrer_repas(conn, {"jour": J, "moment": "diner", "plats": ["plat-carbonara"], "issue": "commande"})
    assert lire_repas(conn, J, J)[1] == {"jour": J, "moment": "diner", "plats": ["plat-carbonara"], "issue": "commande"}


def test_un_repas_vide_est_supprime(conn):
    enregistrer_repas(conn, {"jour": J, "moment": "dejeuner", "plats": ["plat-carbonara"], "issue": None})
    enregistrer_repas(conn, {"jour": J, "moment": "dejeuner", "plats": [], "issue": None})
    assert lire_repas(conn, J, J) == []
    enregistrer_repas(conn, {"jour": J, "moment": "diner", "plats": [], "issue": "dehors"})     # une issue suffit
    assert lire_repas(conn, J, J) == [{"jour": J, "moment": "diner", "plats": [], "issue": "dehors"}]


def test_fait_maison_fait_entrer_au_carnet_tous_les_plats_a_tester(conn):
    r = {"jour": J, "moment": "diner", "plats": ["tester-pesto", "tester-shakshuka", "plat-carbonara"], "issue": None}
    enregistrer_repas(conn, r)
    assert statut(conn, "tester-pesto") == "a-tester"
    enregistrer_repas(conn, {**r, "issue": "fait"})
    assert statut(conn, "tester-pesto") == statut(conn, "tester-shakshuka") == "carnet"


def test_reprise_des_soirs_une_seule_fois(conn):
    hier, avant = J - timedelta(days=1), J - timedelta(days=2)
    with conn.cursor() as cur:
        cur.execute("""INSERT INTO soirs (jour, plat, issue) VALUES (%s, 'plat-carbonara', 'fait'),
                       (%s, NULL, 'commande'), (%s, NULL, NULL)""", (avant, hier, J))
    conn.commit()
    assert reprendre_soirs(conn) == 2                        # le soir sans plat ni issue ne devient rien
    conn.commit()
    assert lire_repas(conn, avant, J) == [
        {"jour": avant, "moment": "diner", "plats": ["plat-carbonara"], "issue": "fait"},
        {"jour": hier, "moment": "diner", "plats": [], "issue": "commande"}]
    assert reprendre_soirs(conn) is None                     # une seule fois (table reprises)
```

- [ ] **Step 4 : lancer, vérifier l'échec**

Run : `cd voyage && .venv/bin/python3 -m pytest test_repas.py -q`
Attendu : erreur d'import `cannot import name 'enregistrer_repas' from 'db'`.

- [ ] **Step 5 : écrire `db.py`**

Dans `voyage/db.py`, après `lire_soirs` :

```python
def enregistrer_repas(conn, r):
    """Un repas (jour, moment) : ses plats et son issue. Vide (ni plat ni issue) : supprimé.
    Fait maison : chacun de ses plats à tester passe au carnet."""
    with conn.cursor() as cur:
        if not r["plats"] and not r["issue"]:
            cur.execute("DELETE FROM repas WHERE jour = %s AND moment = %s", (r["jour"], r["moment"]))
        else:
            cur.execute("""INSERT INTO repas (jour, moment, plats, issue) VALUES (%s, %s, %s, %s)
                           ON CONFLICT (jour, moment) DO UPDATE SET plats = EXCLUDED.plats, issue = EXCLUDED.issue,
                           maj_le = now()""", (r["jour"], r["moment"], Json(r["plats"]), r["issue"]))
        if r["issue"] == "fait" and r["plats"]:
            cur.execute("""UPDATE plats SET statut = 'carnet', maj_le = now()
                           WHERE id = ANY(%s) AND statut = 'a-tester'""", (list(r["plats"]),))
    conn.commit()


def lire_repas(conn, debut, fin):
    with conn.cursor() as cur:
        cur.execute("""SELECT jour, moment, plats, issue FROM repas WHERE jour BETWEEN %s AND %s
                       ORDER BY jour, moment""", (debut, fin))
        return [dict(zip(("jour", "moment", "plats", "issue"), ligne)) for ligne in cur.fetchall()]


def reprendre_soirs(conn):
    """La reprise repas-v1, une seule fois (table reprises) : chaque soir renseigné devient un dîner
    (même plat, même issue). Sans commit : l'appelant valide ou annule (à blanc).
    Renvoie le nombre de dîners repris, ou None si la reprise est déjà faite."""
    with conn.cursor() as cur:
        cur.execute("SELECT EXISTS (SELECT 1 FROM reprises WHERE nom = 'repas-v1')")
        if cur.fetchone()[0]:
            return None
        cur.execute("""INSERT INTO repas (jour, moment, plats, issue, maj_le)
                       SELECT jour, 'diner', CASE WHEN plat IS NULL THEN '[]'::jsonb ELSE jsonb_build_array(plat) END,
                              issue, maj_le
                       FROM soirs WHERE plat IS NOT NULL OR issue IS NOT NULL
                       ON CONFLICT (jour, moment) DO NOTHING""")
        n = cur.rowcount
        cur.execute("INSERT INTO reprises (nom) VALUES ('repas-v1')")
    return n
```

Mettre à jour le titre de section : `# --- Casa Binomerie : dîners (carnet et soirs) ---` → `# --- Casa Binomerie : dîners (carnet et repas) ---`.

- [ ] **Step 6 : lancer, vérifier le vert**

Run : `cd voyage && .venv/bin/python3 -m pytest test_repas.py -q` → `4 passed`.

- [ ] **Step 7 : la reprise dans `appliquer_schema.py`**

Import : ajouter `reprendre_soirs` à la ligne `from db import (...)`.
Dans `appliquer()`, branche `pour_de_bon`, juste avant le `conn.commit()` qui suit `laetitia = ajouter_recettes(...)` :

```python
        repas = reprendre_soirs(conn)                        # soirs -> repas, une seule fois
```

et après les autres `print` de cette branche :

```python
        if repas is not None:
            print(f"Repas composés : {repas} soir(s) repris en dîners.")
```

Branche à blanc, juste avant `conn.rollback()` :

```python
        repas = reprendre_soirs(conn)
```

et après `conn.rollback()` :

```python
        if repas is not None:
            print(f"À blanc, repas composés : {repas} soir(s) à reprendre en dîners.")
```

Vérif : `cd voyage && DATABASE_URL="" .venv/bin/python3 appliquer_schema.py --base valise_test`
Attendu : une ligne `À blanc, repas composés : … soir(s) à reprendre en dîners.` (0 : la base de test est vide) et aucune erreur.

- [ ] **Step 8 : suite complète puis commit**

Run : `cd voyage && .venv/bin/python3 -m pytest -q` → 640 verts.

```bash
git add voyage/schema.sql voyage/db.py voyage/appliquer_schema.py voyage/test_repas.py voyage/test_diners_db.py voyage/test_serveur.py
git commit -m "feat: Casa Binomerie — table repas (plusieurs plats par repas) et reprise des soirs"
```

---

### Task 2 : logique des repas dans `diners.py`

**Files:**
- Modify: `voyage/diners.py` (validation ~l. 86-104, logique ~l. 107-220, docstring du module)
- Modify: `voyage/test_diners.py`
- Modify: `voyage/test_repas.py`

**Interfaces:**
- Consumes : rien de la Task 1 (logique pure).
- Produces :
  - `MOMENTS = [("diner", "Dîner"), ("dejeuner", "Déjeuner"), ("brunch", "Brunch")]`
  - `valider_repas(corps, aujourd_hui) -> {"jour": date, "moment": str, "plats": list[str], "issue": str|None}` (lève `ValueError`)
  - `ranger(plats: list[dict], moment: str) -> list[dict]`
  - `repas_prevus(repas: list[dict], par_id: dict, jours: list[date]) -> list[list[dict]]` — un élément par repas sans issue des `jours`, ses plats connus ; repas sans plat connu exclus.
  - `compteur(repas, aujourd_hui)` — mêmes clés qu'avant, dîners seulement.
  - `proposer(plats, repas, jours, aujourd_hui, remplacer=(), cible=CIBLE_SOIRS, hasard=None) -> {date: id}`
  - `cout_semaine(prevus: list[list[dict]], placard, courses) -> {"nb_repas", "cout", "a_acheter", "courses", "livraison"}`
  - `valider_soir` est supprimée ici ; `serveur.py` l'importe encore jusqu'à la Task 3, d'où un seul commit pour les Tasks 2 et 3 (voir Step 6).

- [ ] **Step 1 : tests de validation et de rangement (échouent)**

Ajouter à `voyage/test_repas.py`, après les imports :

```python
from diners import valider_repas, ranger

AUJ = date(2026, 10, 28)


def test_valider_repas():
    assert valider_repas({"jour": "2026-10-30", "moment": "brunch", "plats": ["plat-carbonara", "tester-pesto"]}, AUJ) == {
        "jour": date(2026, 10, 30), "moment": "brunch", "plats": ["plat-carbonara", "tester-pesto"], "issue": None}
    assert valider_repas({"jour": "2026-10-27", "moment": "diner", "issue": "commande"}, AUJ)["plats"] == []


@pytest.mark.parametrize("corps", [
    None, {"moment": "diner"}, {"jour": "2026-12-31", "moment": "diner"}, {"jour": "2026-10-28", "moment": "gouter"},
    {"jour": "2026-10-28", "moment": "diner", "plats": "plat-carbonara"},
    {"jour": "2026-10-28", "moment": "diner", "plats": ["plat-carbonara", "plat-carbonara"]},
    {"jour": "2026-10-28", "moment": "diner", "plats": [f"plat-numero-{i}" for i in range(9)]},
    {"jour": "2026-10-28", "moment": "diner", "plats": ["x"]},
    {"jour": "2026-10-28", "moment": "diner", "issue": "livre"}])
def test_valider_repas_refuse(corps):
    with pytest.raises(ValueError):
        valider_repas(corps, AUJ)


def test_ranger_dans_l_ordre_du_service():
    dessert, plat, entree, accomp = ({"id": g, "genre": g} for g in ("dessert", "plat", "entree", "accompagnement"))
    assert [p["genre"] for p in ranger([dessert, plat, entree, accomp], "diner")] == [
        "entree", "plat", "accompagnement", "dessert"]
    assert [p["genre"] for p in ranger([dessert, plat, entree], "brunch")] == ["dessert", "plat", "entree"]
```

Run : `cd voyage && .venv/bin/python3 -m pytest test_repas.py -q` → erreur d'import `valider_repas`.

- [ ] **Step 2 : `valider_repas`, `MOMENTS`, `ranger`**

Dans `voyage/diners.py`, après `ISSUES = [...]` :

```python
MOMENTS = [("diner", "Dîner"), ("dejeuner", "Déjeuner"), ("brunch", "Brunch")]
ORDRE_GENRES = ("entree", "plat", "accompagnement", "dessert")
MAX_PLATS = 8
```

Remplacer la fonction `valider_soir` entière par :

```python
def valider_repas(corps, aujourd_hui):
    """Un repas : {jour, moment, plats (0 à 8 ids sans doublon), issue (ou None)} ; de -60 à +30 jours."""
    if not isinstance(corps, dict):
        raise ValueError("repas invalide")
    try:
        jour = date.fromisoformat(corps.get("jour"))
    except (TypeError, ValueError):
        raise ValueError("jour invalide") from None
    if not -60 <= (jour - aujourd_hui).days <= FENETRE_FUTUR:
        raise ValueError("jour hors limites")
    if corps.get("moment") not in dict(MOMENTS):
        raise ValueError("moment invalide")
    plats = corps.get("plats") or []
    if (not isinstance(plats, list) or len(plats) > MAX_PLATS
            or not all(isinstance(i, str) and _ID.fullmatch(i) for i in plats)):
        raise ValueError("plats invalides")
    if len(set(plats)) != len(plats):
        raise ValueError("plat en double")
    issue = corps.get("issue") or None
    if issue is not None and issue not in dict(ISSUES):
        raise ValueError("issue invalide")
    return {"jour": jour, "moment": corps["moment"], "plats": plats, "issue": issue}


def ranger(plats, moment):
    """Les plats d'un repas dans l'ordre du service ; au brunch, dans l'ordre d'ajout."""
    if moment == "brunch":
        return list(plats)
    return sorted(plats, key=lambda p: ORDRE_GENRES.index(p["genre"]))
```

Docstring du module, remplacer les lignes 3-6 par :

```python
- plats : le carnet (statut 'carnet') et les envies du Match des Recettes ('a-tester'). Un plat à
  tester passe au carnet quand un repas où on l'a prévu est marqué « fait maison » (db.enregistrer_repas).
- repas : un dîner par jour, un déjeuner ou un brunch à la demande — plusieurs plats, et ce qui s'est vraiment
  passé (fait, commandé, dehors, autre). Le dîner est la mesure du succès : ≤ 1 commande par semaine
  (départ : 3, le 28/10/2026).
```

- [ ] **Step 3 : réécrire les tests existants sur des repas (échouent)**

Dans `voyage/test_diners.py` :

1. Ligne 8, import : remplacer `valider_soir` par `repas_prevus`.
2. Après la fonction `habituel`, ajouter :

```python
def diner(jour, *plats, issue=None, moment="diner"):
    return {"jour": jour, "moment": moment, "plats": list(plats), "issue": issue}
```

3. Supprimer `test_valider_soir` (lignes 53-61 ; couvert par `test_valider_repas`).
4. Remplacer `test_compteur` par :

```python
def test_compteur():
    repas = [diner(AUJ - timedelta(days=d), issue="commande") for d in (1, 3, 10, 20, 41, 42)]
    repas += [diner(AUJ - timedelta(days=2), issue="fait"),
              diner(AUJ - timedelta(days=1), issue="commande", moment="dejeuner")]     # le déjeuner ne compte pas
    c = compteur(repas, AUJ)
```

(garder les `assert` qui suivent dans le test actuel tels quels.)

5. Dans les tests `proposer`, convertir chaque soir en dîner :
   - `test_proposer_quatre_soirs_varies` : `[{"jour": LUN + timedelta(days=6), "plat": "plat-carnet-00", "issue": None}]` → `[diner(LUN + timedelta(days=6), "plat-carnet-00")]`
   - `test_proposer_complete_ce_qui_est_prevu` : `soirs = [diner(LUN + timedelta(days=1), "plat-carnet-00"), diner(LUN, issue="dehors")]`
   - `test_proposer_sans_ce_qu_on_a_mange_recemment` : `soirs = [diner(LUN - timedelta(days=3), "plat-carnet-00", issue="fait")]`
   - `test_proposer_remplacer_un_soir` : `soirs = [diner(j, v) for j, v in p.items()]`
   - `test_proposer_rien_si_deja_quatre` : `soirs = [diner(LUN + timedelta(days=i), f"plat-carnet-{i:02d}") for i in range(4)]`

6. Ajouter à la suite des tests `proposer` :

```python
def test_proposer_ignore_dejeuner_et_brunch():
    repas = [diner(LUN + timedelta(days=i), f"plat-carnet-{i:02d}", moment="brunch") for i in range(4)]
    p = proposer(carte(), repas, SEMAINE, LUN, hasard=Random(6))
    assert len(p) == 4                                              # un brunch ne remplit pas le soir


def test_proposer_un_diner_compose_compte_comme_prevu():
    repas = [diner(LUN + timedelta(days=i), f"plat-carnet-{i:02d}", f"plat-carnet-{i + 6:02d}") for i in range(4)]
    assert proposer(carte(), repas, SEMAINE, LUN, hasard=Random(7)) == {}
```

7. Remplacer `test_cout_semaine` par :

```python
def test_cout_semaine():
    carbo = plat("plat-carbonara", "Carbonara", ingredients=["spaghetti", "œufs", "pecorino"])
    saumon = plat("plat-saumon-01", "Saumon", ingredients=["pavés de saumon", "riz basmati"])
    tiramisu = plat("dessert-tira-01", "Tiramisu", genre="dessert", ingredients=["mascarpone", "œufs"])
    c = cout_semaine([[carbo, tiramisu], [saumon]], placard("spaghetti", "riz basmati"), [habituel("œufs", actif=True)])
    assert c["nb_repas"] == 2 and c["livraison"] == 2 * LIVRAISON_DEUX
    assert 0 < c["cout"] < c["livraison"]
    assert c["a_acheter"] == ["pecorino", "mascarpone", "pavés de saumon"]     # les œufs sont déjà sur la liste
    assert c["courses"] == round(sum(prix_de(n)[1] for n in c["a_acheter"] if prix_de(n)), 2)


def test_repas_prevus():
    par_id = {i: plat(i, i) for i in ("plat-aaaa-01", "plat-bbbb-01", "plat-cccc-01")}
    repas = [diner(LUN, "plat-aaaa-01", "plat-bbbb-01"),
             diner(LUN + timedelta(days=1), "plat-cccc-01", moment="dejeuner"),
             diner(LUN + timedelta(days=2), "plat-aaaa-01", issue="commande"),     # déjà passé : pas aux courses
             diner(LUN + timedelta(days=3), "plat-inconnu-01"),                     # plat disparu : repas ignoré
             diner(LUN + timedelta(days=9), "plat-aaaa-01")]                        # hors semaine
    assert [[p["id"] for p in r] for r in repas_prevus(repas, par_id, SEMAINE)] == [
        ["plat-aaaa-01", "plat-bbbb-01"], ["plat-cccc-01"]]
```

et compléter l'import de cette section : `from diners import cout_semaine, LIVRAISON_DEUX` → ajouter la ligne `from prix_paris import prix_de`.

Run : `cd voyage && .venv/bin/python3 -m pytest test_diners.py test_repas.py -q` → échecs attendus sur `repas_prevus` (import), `compteur`, `proposer`, `cout_semaine`.

- [ ] **Step 4 : `repas_prevus`, `compteur`, `proposer`, `cout_semaine`**

Dans `voyage/diners.py`, après `a_acheter` :

```python
def repas_prevus(repas, par_id, jours):
    """Les repas encore à venir des `jours` (sans issue) : pour chacun, ses plats connus ; les vides sont omis."""
    prevus = []
    for r in repas:
        if r["jour"] in jours and not r["issue"]:
            plats = [par_id[i] for i in r["plats"] if i in par_id]
            if plats:
                prevus.append(plats)
    return prevus
```

Remplacer `proposer` entière par :

```python
def proposer(plats, repas, jours, aujourd_hui, remplacer=(), cible=CIBLE_SOIRS, hasard=None):
    """{jour: id du plat} pour compléter la semaine jusqu'à `cible` dîners prévus.

    Dîners libres seulement (ni plat ni issue), vendredi et samedi en dernier recours (souvent dehors), répartis
    dans la semaine. Plats pour nous deux, avec recette ; rapides (≤ 45 min) du lundi au jeudi ; ni déjà prévus
    (tous moments), ni mangés ces 14 derniers jours ; un plat à tester s'il n'y en a pas déjà un. `remplacer` :
    des jours à tirer au sort de nouveau, avec un autre plat. Déjeuners et brunchs ne remplissent pas un soir."""
    from random import Random
    hasard = hasard or Random()
    remplacer = [j for j in remplacer if j in jours]
    diners = {r["jour"]: r for r in repas if r["moment"] == "diner"}
    prevus = {j: diners[j]["plats"] for j in jours if j in diners and diners[j]["plats"] and j not in remplacer}
    besoin = max(0, cible - len(prevus))
    libres = [j for j in jours if j not in prevus and j not in remplacer
              and not (j in diners and diners[j]["issue"])]
    preferes = [j for j in libres if j.weekday() not in (4, 5)]
    autres = [j for j in libres if j.weekday() in (4, 5)]
    a_remplir = remplacer[:besoin]
    reste = besoin - len(a_remplir)
    if reste > 0:
        if len(preferes) > reste:                       # répartis : au milieu de chaque tranche, pas d'affilée
            a_remplir += [preferes[(2 * i + 1) * len(preferes) // (2 * reste)] for i in range(reste)]
        else:
            a_remplir += preferes + autres[:reste - len(preferes)]
    if not a_remplir:
        return {}

    manges = {i for r in repas if r["issue"] == "fait" and 0 <= (aujourd_hui - r["jour"]).days < RECENT
              for i in r["plats"]}
    deja = {i for r in repas if r["jour"] in jours and r["jour"] not in remplacer for i in r["plats"]}
    exclus = deja | manges | {i for j in remplacer if j in diners for i in diners[j]["plats"]}
    candidats = [p for p in plats if p["genre"] == "plat" and not p["archive"] and p.get("pour", "nous") == "nous"
                 and p["recette"] and p["id"] not in exclus]
    hasard.shuffle(candidats)
    a_tester = any(p["statut"] == "a-tester" for p in plats if p["id"] in deja)
    choix = {}
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

Remplacer `cout_semaine` entière par :

```python
def cout_semaine(prevus, placard, courses):
    """Les repas prévus ([[plat, …], …], voir repas_prevus) : leur coût estimé (somme des prix_paris.cout_repas
    de leurs plats), les courses qui restent à faire pour eux (prix entier des produits ni au placard ni sur la
    liste) et le même nombre de repas en livraison."""
    from prix_paris import cout_repas, prix_de
    plats = [p for r in prevus for p in r]
    a_acheter_ = [nom for nom, _ in a_acheter(plats, placard, courses)]
    return {"nb_repas": len(prevus), "cout": round(sum(cout_repas(p["ingredients"], p["recette"]) for p in plats), 2),
            "a_acheter": a_acheter_,
            "courses": round(sum(prix_de(n)[1] for n in a_acheter_ if prix_de(n)), 2),
            "livraison": len(prevus) * LIVRAISON_DEUX}
```

Remplacer `compteur` entière par :

```python
def compteur(repas, aujourd_hui):
    """Commandes des 7 derniers jours, moyenne hebdomadaire sur 6 semaines, dîners renseignés (dîners seuls)."""
    recents = [r for r in repas if r["moment"] == "diner" and r["issue"]
               and 0 <= (aujourd_hui - r["jour"]).days < FENETRE_PASSE]
    commandes = [r for r in recents if r["issue"] == "commande"]
    return {"semaine": sum(1 for r in commandes if (aujourd_hui - r["jour"]).days < 7),
            "moyenne": len(commandes) / 6 if recents else 0,
            "renseignes": len(recents)}
```

`FENETRE_PASSE = 42           # jours de soirs lus` → `# jours de repas lus`.

- [ ] **Step 5 : lancer**

Run : `cd voyage && .venv/bin/python3 -m pytest test_diners.py test_repas.py -q` → tout vert.

- [ ] **Step 6 : ne pas commiter tout de suite**

`serveur.py` importe encore `valider_soir` et appelle `cout_semaine`/`compteur`/`proposer` avec l'ancien format : la suite complète est rouge jusqu'à la Task 3. Les Tasks 2 et 3 forment **un seul commit** (Task 3, Step 8). Ne pas lancer la suite complète ici.

---

### Task 3 : routes et page Aujourd'hui sur les repas

**Files:**
- Modify: `voyage/serveur.py` (imports l. 27 et 40-41 ; routes l. 53-166)
- Modify: `voyage/casa.py` (l. 91-146)
- Modify: `voyage/db.py` (supprimer `enregistrer_soir`, `lire_soirs`)
- Modify: `voyage/test_diners_db.py`, `voyage/test_casa.py`

**Interfaces:**
- Consumes : `enregistrer_repas`, `lire_repas` (Task 1) ; `valider_repas`, `ranger`, `repas_prevus`, `compteur`, `proposer`, `cout_semaine` (Task 2).
- Produces (contrat pour le JS de la Task 4) :
  - `GET api/diners` → mêmes clés qu'avant, sauf `soirs` remplacée par `repas: [{jour: "YYYY-MM-DD", moment, plats: [ids], issue}]` et `cout_semaine: {nb_repas, cout, a_acheter, courses, livraison}`.
  - `POST api/repas` `{jour, moment, plats, issue}` → `{"ok": true}` ou 400 `{"erreur": …}` (plat inconnu compris).
  - `POST api/diners/proposer` → inchangé (`{"proposes": {iso: id}}`), écrit des dîners `plats: [id]`.
  - `casa.aujourdhui_en_html(voyages, aujourd_hui, a_prendre=0, plats_du_soir=(), diner_hier=None, compte=None)`.

- [ ] **Step 1 : tests de routes (échouent)**

Dans `voyage/test_diners_db.py` :

1. Import l. 11-12 : remplacer `enregistrer_soir, lire_soirs` par `enregistrer_repas, lire_repas`.
2. Supprimer `test_fait_maison_fait_entrer_au_carnet` (couvert par `test_repas.py`).
3. Remplacer `test_planifier_et_courses_de_la_semaine` par :

```python
def test_planifier_et_courses_de_la_semaine(client):
    corps = {"jour": J.isoformat(), "moment": "diner", "plats": ["plat-amatriciana"]}
    assert client.post("/api/repas", json=corps).status_code == 200
    assert client.post("/api/repas", json={**corps, "plats": ["plat-inconnu-01"]}).status_code == 400
    assert client.post("/api/repas", json={**corps, "moment": "gouter"}).status_code == 400
    r = client.post("/api/diners/courses").get_json()
    assert r["ajoutes"] == ["vin blanc"]                              # le reste est au placard
    assert client.post("/api/diners/courses").get_json()["ajoutes"] == []     # deux fois : pas de doublon
    assert [a["nom"] for a in client.get("/api/courses").get_json()["articles"]] == ["vin blanc"]


def test_api_repas_compose_et_brunch(client):
    jour = J.isoformat()
    client.post("/api/repas", json={"jour": jour, "moment": "diner", "plats": ["plat-carbonara", "tester-pesto"]})
    client.post("/api/repas", json={"jour": jour, "moment": "brunch", "plats": ["tester-shakshuka"]})
    d = client.get("/api/diners").get_json()
    assert {(r["moment"], tuple(r["plats"])) for r in d["repas"] if r["jour"] == jour} == {
        ("diner", ("plat-carbonara", "tester-pesto")), ("brunch", ("tester-shakshuka",))}
    assert d["cout_semaine"]["nb_repas"] == 2
    client.post("/api/repas", json={"jour": jour, "moment": "brunch", "plats": []})          # retirer le brunch
    assert [r["moment"] for r in client.get("/api/diners").get_json()["repas"]] == ["diner"]
```

4. Remplacer `test_hier_soir_et_compteur_sur_aujourd_hui` par :

```python
def test_hier_soir_et_compteur_sur_aujourd_hui(client):
    hier = (J - timedelta(days=1)).isoformat()
    assert "Hier soir ?" in client.get("/").get_data(as_text=True)
    assert client.post("/api/repas", json={"jour": hier, "moment": "diner", "issue": "commande"}).status_code == 200
    html = client.get("/").get_data(as_text=True)
    assert "Hier soir ?" not in html and "1 commande ces 7 jours" in html


def test_ce_soir_compose_sur_aujourd_hui(client):
    client.post("/api/repas", json={"jour": J.isoformat(), "moment": "diner", "plats": ["plat-carbonara"]})
    html = client.get("/").get_data(as_text=True)
    assert "<strong>Carbonara</strong>" in html
```

5. Dans `test_api_proposer`, remplacer les deux lignes `soirs = …` / `assert all(…)` par :

```python
    diners = {r["jour"]: r["plats"] for r in client.get("/api/diners").get_json()["repas"] if r["moment"] == "diner"}
    assert all(diners[j] == [id_] for j, id_ in proposes.items())
```

6. Dans `test_api_diners_couts` : `{"diners", "repas", "courses", "livraison", "a_acheter"}` → `{"nb_repas", "cout", "courses", "livraison", "a_acheter"}`.

Dans `voyage/test_casa.py`, remplacer `test_ce_soir` et `test_hier_soir_tant_que_pas_renseigne` par :

```python
def test_ce_soir():
    vide = aujourdhui_en_html([], AUJOURD_HUI)
    assert '<a class="bloc-ce-soir vide" href="diners#ce-soir">' in vide and "Rien de prévu" in vide
    html = aujourdhui_en_html([], AUJOURD_HUI, plats_du_soir=[{"nom": "Carbonara", "minutes": 20, "genre": "plat"}])
    assert "<strong>Carbonara</strong><span>20 min" in html


def test_ce_soir_compose():
    plats = [{"nom": "Salade de chèvre", "minutes": 10, "genre": "entree"},
             {"nom": "Carbonara", "minutes": 20, "genre": "plat"},
             {"nom": "Tiramisu", "minutes": 30, "genre": "dessert"}]
    html = aujourdhui_en_html([], AUJOURD_HUI, plats_du_soir=plats)
    assert "<strong>Carbonara</strong>" in html and "avec Salade de chèvre, Tiramisu" in html


def test_hier_soir_tant_que_pas_renseigne():
    hier = {"jour": AUJOURD_HUI - timedelta(days=1), "moment": "diner", "plats": ["plat-carbonara"], "issue": None}
    html = aujourdhui_en_html([], AUJOURD_HUI, diner_hier=hier)
    assert "Hier soir ?" in html and 'data-issue="commande"' in html and "api/repas" in html
    assert ("&quot;jour&quot;: &quot;2026-10-27&quot;, &quot;moment&quot;: &quot;diner&quot;, "
            "&quot;plats&quot;: [&quot;plat-carbonara&quot;]") in html
    assert "Hier soir ?" not in aujourdhui_en_html([], AUJOURD_HUI, diner_hier={**hier, "issue": "fait"})
```

(Vérifier que `AUJOURD_HUI` de `test_casa.py` est bien le 28/10/2026 : le test actuel attend `2026-10-27` pour hier.)

Run : `cd voyage && .venv/bin/python3 -m pytest test_diners_db.py test_casa.py -q` → échecs attendus.

- [ ] **Step 2 : `casa.py`**

Remplacer `bloc_ce_soir`, `bloc_hier`, le `fetch('api/soirs'…)` de `SCRIPT_HIER` et la signature de `aujourdhui_en_html` :

```python
def bloc_ce_soir(plats):
    """Le dîner de ce soir : le plat principal en grand, les autres plats à la suite."""
    if plats:
        principal = next((p for p in plats if p.get("genre") == "plat"), plats[0])
        autres = [p["nom"] for p in plats if p is not principal]
        avec = f'avec {echapper(", ".join(autres))} · ' if autres else ""
        return (f'<a class="bloc-ce-soir" href="diners#ce-soir"><span class="titre">Ce soir</span>'
                f'<strong>{echapper(principal["nom"])}</strong><span>{principal["minutes"]} min · {avec}voir la recette</span></a>')
    return ('<a class="bloc-ce-soir vide" href="diners#ce-soir"><span class="titre">Ce soir</span>'
            '<strong>Rien de prévu</strong><span>Voir ce que le placard permet en 20 minutes</span></a>')
```

Attention : le test `test_ce_soir` attend `<strong>Carbonara</strong><span>20 min` ; avec un seul plat, `avec` est vide → `20 min · voir la recette`. OK.

```python
def bloc_hier(diner_hier):
    """« Hier soir ? » tant que le dîner d'hier n'est pas renseigné : c'est ce qui compte les Deliveroo."""
    if diner_hier["issue"]:
        return ""
    corps = json.dumps({"jour": diner_hier["jour"].isoformat(), "moment": "diner", "plats": diner_hier["plats"]})
    boutons = "".join(f'<button type="button" data-issue="{c}">{t}</button>' for c, t in ISSUES_HIER)
    return (f'<div class="bloc-hier" data-repas="{echapper(corps)}"><strong>Hier soir ?</strong>'
            f'<div class="choix">{boutons}</div><p class="message" aria-live="polite"></p></div>')
```

Dans `SCRIPT_HIER` : `const soir = JSON.parse(bloc.dataset.soir);` → `const repas = JSON.parse(bloc.dataset.repas);` ; `fetch('api/soirs', …` → `fetch('api/repas', …` ; `Object.assign({}, soir, …` → `Object.assign({}, repas, …`.

```python
def aujourdhui_en_html(voyages, aujourd_hui, a_prendre=0, plats_du_soir=(), diner_hier=None, compte=None):
    """L'accueil du hub : ce soir, hier soir, les courses, le prochain voyage, le compteur Deliveroo."""
    v = prochain_voyage(voyages, aujourd_hui)
    blocs = (bloc_ce_soir(list(plats_du_soir)) + (bloc_hier(diner_hier) if diner_hier else "") + bloc_courses(a_prendre)
             + (bloc_vadrouille(v, aujourd_hui) if v else "") + bloc_compteur(compte))
```

(le reste de la fonction est inchangé.)

- [ ] **Step 3 : `serveur.py` — imports**

Ligne 27 : `enregistrer_soir, lire_soirs` → `enregistrer_repas, lire_repas`.
Lignes 40-41 :

```python
from diners import (disponibles, valider_plat, valider_repas, secours, a_acheter, compteur, semaine, diners_en_html,
                    proposer, cout_semaine, repas_prevus, ranger, LIVRAISON_DEUX, FENETRE_PASSE, FENETRE_FUTUR)
```

- [ ] **Step 4 : `serveur.py` — accueil**

Dans `accueil()`, remplacer le bloc `try:` par :

```python
            try:
                repas = lire_repas(conn, jour - timedelta(days=FENETRE_PASSE), jour)
                plats = {p["id"]: p for p in lire_plats(conn)}
                diners = {r["jour"]: r for r in repas if r["moment"] == "diner"}
                ce_soir = ranger([plats[i] for i in diners.get(jour, {"plats": []})["plats"] if i in plats], "diner")
                veille = jour - timedelta(days=1)
                hier = diners.get(veille, {"jour": veille, "moment": "diner", "plats": [], "issue": None})
                html = aujourdhui_en_html(lister_voyages(conn), jour, compter_a_prendre(conn),
                                          ce_soir, hier, compteur(repas, jour))
```

- [ ] **Step 5 : `serveur.py` — `api/diners`, `api/repas`, courses, proposer**

Dans `lire_les_diners()` : `soirs = lire_soirs(…)` → `repas = lire_repas(conn, jour - timedelta(days=FENETRE_PASSE), jour + timedelta(days=FENETRE_FUTUR))` ; remplacer les lignes `prevus = [...]` puis le dict renvoyé :

```python
        prevus = repas_prevus(repas, par_id, jours)
        return jsonify({
            "aujourd_hui": jour.isoformat(), "semaine": [j.isoformat() for j in jours],
            "plats": [{**p, "cout": cout_repas(p["ingredients"], p["recette"])} for p in plats],
            "repas": [{**r, "jour": r["jour"].isoformat()} for r in repas],
            "liste": sorted({normaliser(a["nom"]) for a in lu["articles"] if a["actif"] and not a["pris"]}),
            "livraison": LIVRAISON_DEUX, "cout_semaine": cout_semaine(prevus, lu["placard"], lu["articles"]),
            "stock": sorted(disponibles(lu["placard"], lu["articles"])),
            "secours": {"faisables": [p["id"] for p in faisables],
                        "presque": [{"plat": x["plat"]["id"], "manquants": x["manquants"]} for x in presque]},
            "compteur": compteur(repas, jour)})
```

Remplacer la route `api/soirs` entière par :

```python
    @routes.post("/api/repas")
    def enregistrer_un_repas():
        try:
            repas = valider_repas(request.get_json(silent=True), aujourd_hui_paris())
        except ValueError as e:
            return jsonify({"erreur": str(e)}), 400
        conn = emprunter(app.config["NOM_BASE"])
        try:
            if not all(plat_existe(conn, i) for i in repas["plats"]):
                return jsonify({"erreur": "plat inconnu"}), 400
            enregistrer_repas(conn, repas)
        finally:
            conn.close()
        return jsonify({"ok": True})
```

Dans `courses_de_la_semaine()` :

```python
            plats = {p["id"]: p for p in lire_plats(conn)}
            prevus = [p for r in repas_prevus(lire_repas(conn, jour, jour + timedelta(days=6)), plats, semaine(jour))
                      for p in r]
```

(docstring : « Les ingrédients des repas prévus cette semaine, ni au placard ni déjà sur la liste. »)

Dans `proposer_la_semaine()` :

```python
            plats = lire_plats(conn)
            repas = lire_repas(conn, jour - timedelta(days=FENETRE_PASSE), jour + timedelta(days=6))
            proposes = proposer(plats, repas, semaine(jour), jour, remplacer=remplacer)
            for j, id_plat in proposes.items():
                enregistrer_repas(conn, {"jour": j, "moment": "diner", "plats": [id_plat], "issue": None})
```

(docstring : « … et enregistre les dîners proposés … ».)

- [ ] **Step 6 : supprimer le code mort de `db.py`**

Supprimer `enregistrer_soir` et `lire_soirs` de `voyage/db.py`. Vérifier : `grep -n "soir" voyage/db.py voyage/serveur.py voyage/test_*.py` ne doit plus montrer que des commentaires, les TRUNCATE et l'INSERT du test de reprise.

- [ ] **Step 7 : suite complète**

Run : `cd voyage && .venv/bin/python3 -m pytest -q` → tout vert sauf, éventuellement, `test_page_diners` (le JS parle encore de `api/soirs` mais le test ne le vérifie pas : il doit passer). Si un test casse ailleurs, lire l'erreur avant de toucher quoi que ce soit.

- [ ] **Step 8 : commit (Tasks 2 + 3)**

```bash
git add voyage/diners.py voyage/serveur.py voyage/casa.py voyage/db.py voyage/test_diners.py voyage/test_repas.py voyage/test_diners_db.py voyage/test_casa.py
git commit -m "feat: Casa Binomerie — repas composés côté serveur : api/repas, compteur, courses, coût et proposer sur les repas"
```

---

### Task 4 : la page Dîners en repas composés

**Files:**
- Modify: `voyage/diners.py` (`STYLE_DINERS`, `SCRIPT_DINERS`)
- Modify: `voyage/valise.py:1649` (`VERSION_PAGE = 37`)
- Modify: `voyage/test_diners.py` (`test_page_diners`)

**Interfaces:**
- Consumes : le contrat `api/diners` / `api/repas` de la Task 3.
- Produces : rien pour d'autres tasks.

- [ ] **Step 1 : le test de page (échoue)**

À la fin de `test_page_diners` dans `voyage/test_diners.py` :

```python
    assert "api/repas" in html and "api/soirs" not in html and "d.soirs" not in html                  # repas composés
    for f in ("function ajouterPlat", "function retirerPlat", "function ranges", "function carteRepas"):
        assert f in html
    assert "+ déjeuner ou brunch" in html and "+ accompagnement" in html and "'brunch'" in html
```

et dans un nouveau test :

```python
def test_version_page_repas():
    from valise import VERSION_PAGE
    assert VERSION_PAGE >= 37
```

Run : `cd voyage && .venv/bin/python3 -m pytest test_diners.py -q -k "page"` → FAIL.

- [ ] **Step 2 : les fonctions de données du script**

Dans `SCRIPT_DINERS` :

1. Après `const JOURS = [...]` :

```js
    const MOMENTS = { diner: 'Dîner', dejeuner: 'Déjeuner', brunch: 'Brunch' };
    const ORDRE_GENRES = ['entree', 'plat', 'accompagnement', 'dessert'];
    const AJOUTS = [['plat', '+ plat'], ['entree', '+ entrée'], ['accompagnement', '+ accompagnement'], ['dessert', '+ dessert']];
```

2. Remplacer `function soir(iso) {…}` par :

```js
    function repas(iso, moment) {
        return d.repas.find(function (r) { return r.jour === iso && r.moment === moment; })
            || { jour: iso, moment: moment, plats: [], issue: null };
    }
    // Les plats d'un repas, dans l'ordre du service (au brunch : l'ordre d'ajout)
    function ranges(r) {
        const ps = r.plats.map(plat).filter(Boolean);
        if (r.moment === 'brunch') return ps;
        return ps.sort(function (a, b) { return ORDRE_GENRES.indexOf(a.genre) - ORDRE_GENRES.indexOf(b.genre); });
    }
    function platsDeLaSemaine() {
        return d.repas.filter(function (r) { return d.semaine.indexOf(r.jour) >= 0; })
                      .reduce(function (t, r) { return t.concat(r.plats); }, []);
    }
```

3. Remplacer `function planifier(iso, idPlat) {…}` par :

```js
    function enregistrerRepas(r) {
        const vide = !r.plats.length && !r.issue;
        d.repas = d.repas.filter(function (x) { return !(x.jour === r.jour && x.moment === r.moment); }).concat(vide ? [] : [r]);
        garder(); afficher();
        envoyer({ url: 'api/repas', methode: 'POST', corps: r, cle: 'repas:' + r.jour + ':' + r.moment }).then(relire, relire);
    }
    function ajouterPlat(iso, moment, id) {
        const r = repas(iso, moment);
        if (r.plats.indexOf(id) >= 0 || r.plats.length >= 8) return;
        enregistrerRepas(Object.assign({}, r, { plats: r.plats.concat([id]) }));
    }
    function retirerPlat(iso, moment, id) {
        const r = repas(iso, moment);
        enregistrerRepas(Object.assign({}, r, { plats: r.plats.filter(function (x) { return x !== id; }) }));
    }
```

4. Remplacer chaque appel restant à `planifier(d.aujourd_hui, X)` (liste « Faisable tout de suite », bouton « Ce soir » de la fiche) par `ajouterPlat(d.aujourd_hui, 'diner', X)`. Vérifier avec `grep -n "planifier\|soir(" voyage/diners.py` qu'il n'en reste aucun.

- [ ] **Step 3 : la vue Ce soir**

Remplacer dans `vueCeSoir` le début jusqu'au `}` du `else` par :

```js
    function vueCeSoir(zone) {
        if (d.compteur && d.compteur.renseignes) zone.append(compteurDiners());
        const ps = ranges(repas(d.aujourd_hui, 'diner'));
        const principal = ps.filter(function (x) { return x.genre === 'plat'; })[0] || ps[0];
        if (principal) {
            const bloc = el('div', 'plat-soir');
            bloc.append(el('span', 'titre', 'Ce soir'), el('span', 'nom', principal.nom));
            const ul = el('ul', 'plats-soir');
            ps.forEach(function (x) {
                const li = el('li');
                li.append(el('span', '', NOMS_GENRE[x.genre] + ' · ' + x.nom + ' · ' + duree(x.minutes)),
                          bouton('Voir la recette', '', function () { ouvrirFiche(x.id); }));
                ul.append(li);
            });
            bloc.append(ul);
            const cout = ps.reduce(function (t, x) { return t + (x.cout || 0); }, 0);
            if (cout) bloc.append(el('span', 'cout', '≈ ' + euros(cout) + ' le repas · en livraison ≈ ' + euros(d.livraison)));
            const b = el('div', 'boutons');
            b.append(bouton('Changer', 'discret', function () { vue = 'semaine'; afficher(); }));
            bloc.append(b);
            zone.append(bloc);
        } else {
            const e = el('div', 'encart');
            e.append(el('h2', '', 'Rien de prévu ce soir'),
                     el('p', 'aide', 'Avant d\\'ouvrir Deliveroo : voilà ce que le placard permet en 20 minutes.'));
            zone.append(e);
        }
```

et, plus bas dans la même fonction, `if (!p) li.append(bouton('Ce soir', …planifier…))` → `if (!principal) li.append(bouton('Ce soir', 'petit', function () { ajouterPlat(d.aujourd_hui, 'diner', x.id); }));`.

- [ ] **Step 4 : la vue Semaine en cartes composées**

Ajouter avant `function vueSemaine` :

```js
    // Une carte de repas : ses plats (× pour retirer), puis + plat / + entrée / + accompagnement / + dessert
    function carteRepas(iso, moment) {
        const r = repas(iso, moment);
        const c = el('div', 'repas');
        const t = el('div', 'titre-repas');
        t.append(el('span', '', MOMENTS[moment]));
        if (r.issue) t.append(el('span', 'badge', r.issue === 'fait' ? 'fait maison' : r.issue === 'commande' ? 'commandé' : r.issue));
        c.append(t);
        const ul = el('ul', 'plats-repas');
        ranges(r).forEach(function (p) {
            const li = el('li');
            const o = bouton('', 'ouvrir', function () { ouvrirFiche(p.id); });
            o.append(el('span', 'nom', p.nom), el('span', 'meta', NOMS_GENRE[p.genre] + ' · ' + duree(p.minutes)));
            const x = bouton('×', 'retirer', function () { retirerPlat(iso, moment, p.id); });
            x.setAttribute('aria-label', 'Retirer ' + p.nom);
            li.append(o, x);
            ul.append(li);
        });
        if (!ul.children.length) ul.append(el('li', 'meta', 'Libre'));
        c.append(ul);
        const a = el('div', 'ajouts');
        AJOUTS.forEach(function (g) { a.append(bouton(g[1], 'petit', function () { ouvrirChoix(iso, moment, g[0]); })); });
        c.append(a);
        return c;
    }
```

Dans `vueSemaine`, remplacer le texte d'aide et la boucle `d.semaine.forEach(…)` par :

```js
        e.append(el('h2', '', 'La semaine'), el('p', 'aide', 'Trois ou quatre dîners suffisent. Les autres restent libres.'));
        d.semaine.forEach(function (iso, i) {
            const jour = el('div', 'jour-repas');
            const q = el('span', 'quand', i === 0 ? 'Ce soir' : enClair(iso));
            if (i === 0) q.append(el('small', '', enClair(iso)));
            jour.append(q, carteRepas(iso, 'diner'));
            const midi = ['dejeuner', 'brunch'].filter(function (m) { return repas(iso, m).plats.length || repas(iso, m).issue; });
            midi.forEach(function (m) { jour.append(carteRepas(iso, m)); });
            if (!midi.length) {
                const plus = el('div', 'ajouts');
                const lien = bouton('+ déjeuner ou brunch', 'petit', function () {
                    plus.replaceChildren(
                        bouton('Déjeuner', 'petit', function () { ouvrirChoix(iso, 'dejeuner', 'plat'); }),
                        bouton('Brunch', 'petit', function () { ouvrirChoix(iso, 'brunch', 'plat'); }));
                });
                plus.append(lien);
                jour.append(plus);
            }
            e.append(jour);
        });
```

Bilan de la semaine, remplacer le tableau du `forEach` par :

```js
            [['', euros(cs.cout), cs.nb_repas + ' repas maison'],
             ['livraison', euros(cs.livraison), 'les mêmes en livraison'],
             ['', euros(cs.courses), 'courses à faire pour eux']].forEach(function (x) {
```

et la condition `if (cs && cs.diners)` → `if (cs && cs.nb_repas)`.

« Reproposer » : remplacer la ligne `const aRefaire = …` par :

```js
        const aRefaire = Object.keys(derniereProposition).filter(function (iso) {
            const r = repas(iso, 'diner'); return r.plats.length === 1 && r.plats[0] === derniereProposition[iso]; });
```

Dans `proposerSemaine`, remplacer la ligne `d.soirs = d.soirs.filter(…).concat([…]);` par :

```js
                  d.repas = d.repas.filter(function (x) { return !(x.jour === iso && x.moment === 'diner'); })
                                   .concat([{ jour: iso, moment: 'diner', plats: [r.proposes[iso]], issue: null }]);
```

et les messages : `' soir(s) proposé(s). Touche un soir pour le changer, puis envoie aux courses.'` → `' dîner(s) proposé(s). Ajoute un accompagnement ou un dessert, puis envoie aux courses.'` ; `'la semaine a déjà quatre soirs'` → `'la semaine a déjà quatre dîners'`.

- [ ] **Step 5 : la feuille de choix par genre**

Remplacer `function ouvrirChoix(iso) {` et ses premières lignes jusqu'à `const hasard = …` inclus par :

```js
    // Ajouter un plat d'un genre à un repas : la même recherche et les mêmes étiquettes, carnet d'abord
    function ouvrirChoix(iso, moment, genre) {
        ouverte = { id: null, edition: false };
        const c = document.querySelector('#panneau .contenu'); c.replaceChildren();
        const haut = el('div', 'haut');
        const quand = iso === d.aujourd_hui ? (moment === 'diner' ? 'ce soir' : 'aujourd\\'hui') : enClair(iso);
        haut.append(el('h2', '', MOMENTS[moment] + ' · ' + quand + ' · ' + NOMS_GENRE[genre].toLowerCase()), bouton('Fermer', 'petit', fermer));
        let q = '';
        const r = el('input', 'recherche'); r.type = 'search'; r.placeholder = 'Chercher un plat ou un ingrédient';
        r.setAttribute('aria-label', 'Chercher');
        const zoneEtiquettes = el('div'), listes = el('div', 'vue');
        const tous = d.plats.filter(function (p) { return p.genre === genre && !p.archive; });
        let affiches = [];
        // Au hasard : parmi les plats affichés (recherche et filtre compris), hors ceux déjà prévus cette semaine
        const hasard = bouton('Au hasard', 'plein', function () {
            const deja = platsDeLaSemaine();
            const pool = affiches.filter(function (p) { return deja.indexOf(p.id) < 0; });
            if (!pool.length) { hasard.textContent = 'Rien à tirer avec ces filtres'; return; }
            const p = pool[Math.floor(Math.random() * pool.length)];
            ajouterPlat(iso, moment, p.id); fermer();
        });
```

Dans `remplir()` de la même fonction, `planifier(iso, p.id); fermer();` → `ajouterPlat(iso, moment, p.id); fermer();`.
Supprimer la ligne `if (soir(iso).plat) c.append(bouton('Rien de prévu ce soir-là', …));` (le × de chaque plat la remplace).

- [ ] **Step 6 : le style**

Dans `STYLE_DINERS`, après les règles `div.jour …` (garder celles-ci, elles ne servent plus mais `div.jour button.choisir` peut être supprimé avec elles si `grep -n "'jour'\|choisir" voyage/diners.py` ne montre plus d'usage), ajouter :

```css
div.jour-repas { display: flex; flex-direction: column; gap: 8px; padding: 12px 0; border-top: 1px solid var(--ligne); }
div.jour-repas:first-of-type { border-top: none; }
div.jour-repas .quand { font-weight: 800; font-size: 15px; }
div.jour-repas .quand small { font-weight: 600; color: var(--doux); font-size: 12px; margin-left: 6px; }
div.repas { background: var(--blanc); border: 2px solid var(--ligne); border-radius: 18px; padding: 10px 12px;
            display: flex; flex-direction: column; gap: 6px; }
div.repas .titre-repas { font-size: 13px; font-weight: 800; color: var(--doux); text-transform: uppercase; letter-spacing: .05em; }
ul.plats-repas { list-style: none; margin: 0; padding: 0; }
ul.plats-repas li { display: flex; align-items: center; gap: 8px; min-height: 44px; }
ul.plats-repas li > button.ouvrir { flex: 1; min-width: 0; text-align: left; background: none; border: none; padding: 4px 0;
                                   font-family: inherit; color: var(--texte); display: flex; flex-direction: column; }
ul.plats-repas .nom { font-size: 16px; font-weight: 700; }
ul.plats-repas .meta, ul.plats-repas li.meta { font-size: 13px; color: var(--doux); }
button.retirer { border: none; background: var(--carte); color: var(--doux); border-radius: 999px; width: 36px; height: 36px;
                 font-size: 18px; font-weight: 800; flex: none; }
div.ajouts { display: flex; gap: 6px; flex-wrap: wrap; }
div.ajouts button.petit { padding: 6px 10px; }
ul.plats-soir { list-style: none; margin: 4px 0 0; padding: 0; display: flex; flex-direction: column; gap: 6px; }
ul.plats-soir li { display: flex; justify-content: space-between; align-items: center; gap: 8px; font-size: 15px; font-weight: 600; }
ul.plats-soir button { padding: 6px 12px !important; font-size: 13px !important; }
```

- [ ] **Step 7 : `VERSION_PAGE`**

`voyage/valise.py:1649` : `VERSION_PAGE = 36` → `VERSION_PAGE = 37`.

- [ ] **Step 8 : suite complète**

Run : `cd voyage && .venv/bin/python3 -m pytest -q` → tout vert (≈ 650).
Puis : `grep -n "soir(\|d\.soirs\|planifier\|api/soirs" voyage/diners.py voyage/casa.py` → aucune ligne.

- [ ] **Step 9 : vérification dans Chrome sur une copie de la prod**

```bash
cd voyage
createdb valise_copie 2>/dev/null || (dropdb valise_copie && createdb valise_copie)
set -a; source .env; set +a
pg_dump "$DATABASE_URL" --no-owner --no-acl | psql -q valise_copie            # lecture seule de Neon
DATABASE_URL="" .venv/bin/python3 appliquer_schema.py --base valise_copie --appliquer   # crée repas + reprise repas-v1
DATABASE_URL="" .venv/bin/python3 -c "from serveur import creer_app; creer_app('valise_copie', secret='').run(host='127.0.0.1', port=8766)"
```

Dans Chrome (largeur iPhone, 390 px), `http://127.0.0.1:8766/diners#semaine` puis `http://127.0.0.1:8766/` — cocher :
- [ ] les dîners déjà prévus en prod apparaissent (reprise OK), le compteur Deliveroo affiche le même chiffre qu'en prod ;
- [ ] « + accompagnement » ouvre la feuille filtrée sur les accompagnements, un appui ajoute, le plat apparaît sous le principal, × le retire ;
- [ ] « + déjeuner ou brunch » → Brunch → un plat : la carte Brunch apparaît ; retirer son dernier plat la fait disparaître ;
- [ ] le bilan de la semaine compte les repas (brunch compris) ;
- [ ] « Proposer ma semaine » puis « Reproposer » ;
- [ ] Ce soir : tous les plats du dîner, « Voir la recette » pour chacun, coût du repas entier ;
- [ ] Aujourd'hui : « Ce soir » liste le dîner ; « Hier soir ? » → Commandé : le bloc disparaît, le compteur monte ;
- [ ] rien ne déborde à 390 px.

Couper le serveur, puis `dropdb valise_copie` (la copie contient des données perso, ne pas la garder).

- [ ] **Step 10 : commit**

```bash
git add voyage/diners.py voyage/valise.py voyage/test_diners.py
git commit -m "feat: Casa Binomerie — Semaine en repas composés, déjeuner et brunch à la demande, Ce soir complet"
```

---

### Task 5 : migration à blanc sur Neon et passage de main

**Files:** aucun code. `~/Claude/TASKS.md`, `~/Claude/Work/perso/` STATUS si existant, note de reprise du brain.

- [ ] **Step 1 : migration à blanc sur Neon**

Run : `cd voyage && .venv/bin/python3 appliquer_schema.py`
Attendu : `À blanc : table(s) à créer : repas.` et `À blanc, repas composés : N soir(s) à reprendre en dîners.` — N doit correspondre au nombre de soirs renseignés en prod (comparer avec la copie de la Task 4 : `psql valise_copie -c "SELECT count(*) FROM soirs WHERE plat IS NOT NULL OR issue IS NOT NULL"` avant de la supprimer).

- [ ] **Step 2 : s'arrêter et demander à Julien**

Lui présenter : le résultat à blanc, les cases cochées de la vérif Chrome, le nombre de tests verts. **Attendre son accord explicite** avant : `--appliquer` sur Neon, puis push, PR, merge (dans cet ordre : migration juste avant le merge, personne ne saisit pendant ce temps).

- [ ] **Step 3 : après merge (si Julien l'a demandé)**

Attendre Render (`sw.js` → `valise-v37`), vérifier `GET api/diners` en prod : clé `repas` présente, compteur identique à avant. Mettre à jour `~/Claude/TASKS.md` (étape 1 cochée, étapes 2 et 3 ouvertes) et la note de reprise du brain (`brain remember`).

---

## Auto-revue (faite)

- **Couverture de la spec, étape 1** : table + reprise → T1 ; `valider_repas`, `enregistrer_repas` / `lire_repas` → T1-T2 ; route `api/repas` → T3 ; compteur dîners seuls, courses et coût sur tous les repas, proposer sur `repas` → T2-T3 ; Aujourd'hui → T3 ; Semaine composée, déjeuner/brunch, Ce soir complet, VERSION_PAGE → T4. Fait maison étendu à tous les plats → T1. Repas vide supprimé → T1 (base) + T4 (page). Ordre par genre / brunch → T2 (`ranger`) + T4 (`ranges`).
- **Hors étape 1, volontairement absent** : colonne `accords`, « Va bien avec », suggestions sous un plat, contenu (accompagnements, brunchs), proposer avec accord.
- **Écart assumé** : courses et coût ignorent les repas déjà renseignés (issue non nulle) — avant, `api/diners/courses` les prenait ; un repas déjà fait ou commandé n'a plus besoin de courses.
- **Noms** : `ranger` (Python) / `ranges` (JS) ; `cout_semaine` → `nb_repas`, `cout` (le JS de T4 lit ces deux clés).
