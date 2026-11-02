# Casa Binomerie — Repas composés, étape 3 (Proposer avec accompagnement) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** « Proposer ma semaine » pose un dîner complet : le plat tiré, et un de ses accompagnements (« accords ») au hasard, pas déjà au menu de la semaine.

**Architecture:** `diners.proposer` reste inchangé dans ce qu'il renvoie (`{jour: id du plat}`) ; une nouvelle fonction pure `diners.accompagner` ajoute à chaque plat proposé un de ses accords. La route `api/diners/proposer` enregistre les dîners composés et renvoie `menus` (`{jour: [ids]}`) en plus de `proposes` (gardé pour les téléphones encore en version 38). `proposer` accepte de remplacer (« Reproposer ») un dîner tel qu'il l'a posé : un plat, ou un plat et un de ses accords. La page lit `menus`.

**Tech Stack:** Python 3, Flask, psycopg2, Postgres (local `valise_test` pour les tests), JS ES5 inline dans une chaîne Python, pytest.

Spec : `docs/superpowers/specs/2026-11-01-casa-repas-composes-design.md`, section « Livraison », étape 3 : « `proposer` ajoute au dîner un accord du plat tiré (au hasard parmi ses accords, pas déjà au menu de la semaine) ».

## Global Constraints

- Tout se passe dans `voyage/`. Tests : `cd voyage && .venv/bin/python3 -m pytest -q` (base locale `valise_test`, jamais Neon). Suite actuelle : 680 tests verts.
- TDD : test qui échoue d'abord, puis le code.
- Accompagnement proposé : un accord du plat tiré, au hasard, accompagnement non archivé, pour nous deux, pas déjà au menu de la semaine (tous moments), jamais deux fois dans la même proposition. Sans accord possible : le plat seul.
- « Reproposer » ne touche jamais un dîner composé à la main ni un dîner déjà vécu (issue renseignée).
- Pas de changement de schéma : aucune migration Neon.
- `VERSION_PAGE` (dans `valise.py`) passe de 38 à 39.
- JS : ES5 comme le reste de `SCRIPT_DINERS`, chaîne Python normale : une apostrophe dans une chaîne JS entre apostrophes s'écrit `\\'`.
- Push, PR et merge seulement à la demande de Julien (`env -u GITHUB_TOKEN gh …`).
- Branche : `feat/casa-proposer-accord` (déjà créée depuis `main`).

## Fichiers

- Modifier `voyage/diners.py` : `proposer` (garde de `remplacer`), nouvelles `tel_que_propose` et `accompagner`, JS `proposerSemaine` et « Reproposer ».
- Modifier `voyage/serveur.py` : route `POST /api/diners/proposer`.
- Modifier `voyage/valise.py` : `VERSION_PAGE = 39`.
- Tests : `voyage/test_diners.py`, `voyage/test_diners_db.py`.

---

### Task 1: `accompagner`, « Reproposer » sur un dîner proposé, et la route

**Files:**
- Modify: `voyage/diners.py` (dans `proposer`, la ligne `remplacer = [j for j in remplacer if j in jours …]` ; nouvelles fonctions juste avant `def proposer`)
- Modify: `voyage/serveur.py:155-173` (route `proposer_la_semaine`, import depuis `diners`)
- Test: `voyage/test_diners.py` (après `test_proposer_un_diner_compose_compte_comme_prevu`), `voyage/test_diners_db.py` (`test_api_proposer` et un nouveau test)

**Interfaces:**
- Consumes: plats lus par `db.lire_plats` : dicts avec `id`, `genre`, `archive`, `pour`, `accords` (liste d'ids). `proposer(plats, repas, jours, aujourd_hui, remplacer=(), cible=CIBLE_SOIRS, hasard=None) -> {date: id}` (existante).
- Produces: `diners.tel_que_propose(plats_du_diner, par_id) -> bool` ; `diners.accompagner(choix, plats, repas, jours, remplacer=(), hasard=None) -> {date: [id du plat] | [id du plat, id de l'accompagnement]}`. Réponse de `POST api/diners/proposer` : `{"proposes": {iso: id du plat}, "menus": {iso: [ids]}}`.

- [ ] **Step 1: Écrire les tests qui échouent**

Dans `voyage/test_diners.py`, juste après `test_proposer_un_diner_compose_compte_comme_prevu` :

```python
# --- Proposer avec un accompagnement (étape 3) ---
from diners import accompagner


def avec_accords(plats, accords):
    """Le carnet `plats`, ses accords ({id de plat: [ids]}) et les accompagnements qu'ils citent."""
    accs = sorted({a for ids in accords.values() for a in ids})
    return ([{**p, "accords": accords.get(p["id"], [])} for p in plats]
            + [{**plat(a, a, genre="accompagnement"), "recette": "1.", "pour": "nous"} for a in accs])


def test_accompagner_un_accord_du_plat():
    plats = avec_accords(carte(), {"plat-carnet-00": ["acc-puree-0", "acc-salade-0"]})
    mer = LUN + timedelta(days=2)
    m = accompagner({LUN: "plat-carnet-00", mer: "plat-carnet-01"}, plats, [], SEMAINE, hasard=Random(1))
    assert m[LUN][0] == "plat-carnet-00" and len(m[LUN]) == 2 and m[LUN][1] in ("acc-puree-0", "acc-salade-0")
    assert m[mer] == ["plat-carnet-01"]                                   # sans accord : le plat seul


def test_accompagner_pas_deux_fois_dans_la_semaine():
    plats = avec_accords(carte(), {"plat-carnet-00": ["acc-puree-0", "acc-salade-0"],
                                   "plat-carnet-01": ["acc-puree-0", "acc-salade-0"]})
    mer, sam = LUN + timedelta(days=2), LUN + timedelta(days=5)
    deja = [diner(sam, "plat-carnet-05", "acc-salade-0")]                 # la salade est déjà au menu samedi
    for graine in range(10):
        m = accompagner({LUN: "plat-carnet-00", mer: "plat-carnet-01"}, plats, deja, SEMAINE, hasard=Random(graine))
        assert m == {LUN: ["plat-carnet-00", "acc-puree-0"], mer: ["plat-carnet-01"]}


def test_accompagner_ni_archive_ni_pour_un_seul_ni_inconnu():
    plats = avec_accords(carte(), {"plat-carnet-00": ["acc-vieux-0", "acc-coleslaw", "acc-absent"]})
    plats = [{**p, "archive": True} if p["id"] == "acc-vieux-0"
             else {**p, "pour": "laetitia"} if p["id"] == "acc-coleslaw" else p
             for p in plats if p["id"] != "acc-absent"]
    assert accompagner({LUN: "plat-carnet-00"}, plats, [], SEMAINE, hasard=Random(1)) == {LUN: ["plat-carnet-00"]}


def test_accompagner_reproposer_libere_l_ancien_accompagnement():
    plats = avec_accords(carte(), {"plat-carnet-01": ["acc-puree-0"]})
    ancien = [diner(LUN, "plat-carnet-00", "acc-puree-0")]                # le dîner qu'on repropose
    m = accompagner({LUN: "plat-carnet-01"}, plats, ancien, SEMAINE, remplacer=[LUN], hasard=Random(1))
    assert m == {LUN: ["plat-carnet-01", "acc-puree-0"]}


def test_proposer_remplace_un_diner_tel_que_propose():
    plats = avec_accords(carte(), {"plat-carnet-00": ["acc-puree-0"]})
    mar = LUN + timedelta(days=1)
    soirs = [diner(LUN, "plat-carnet-00", "acc-puree-0"),                 # un plat et son accord : tel que proposé
             diner(mar, "plat-carnet-01", "acc-puree-0")]                 # un accompagnement choisi à la main
    q = proposer(plats, soirs, SEMAINE, LUN, remplacer=[LUN, mar], hasard=Random(8))
    assert LUN in q and mar not in q
```

Dans `voyage/test_diners_db.py`, remplacer `test_api_proposer` par :

```python
def test_api_proposer(client):
    r = client.post("/api/diners/proposer", json={})
    assert r.status_code == 200
    proposes, menus = r.get_json()["proposes"], r.get_json()["menus"]
    assert 1 <= len(proposes) <= 4 and set(menus) == set(proposes)
    diners = {r["jour"]: r["plats"] for r in client.get("/api/diners").get_json()["repas"] if r["moment"] == "diner"}
    assert all(diners[j] == menus[j] and menus[j][0] == id_ for j, id_ in proposes.items())
    assert client.post("/api/diners/proposer", json={"remplacer": ["pas-une-date"]}).status_code == 400


def test_api_proposer_avec_un_accompagnement(client, conn):
    for p in lire_plats(conn):
        if p["genre"] == "plat":
            enregistrer_plat(conn, {**p, "accords": ["acc-puree-robuchon", "acc-pommes-sautees"]})
    menus = client.post("/api/diners/proposer", json={}).get_json()["menus"]
    accs = [ids[1] for ids in menus.values() if len(ids) == 2]
    assert accs and len(set(accs)) == len(accs) <= 2
    assert set(accs) <= {"acc-puree-robuchon", "acc-pommes-sautees"}
```

- [ ] **Step 2: Lancer les tests, vérifier qu'ils échouent**

Run: `cd voyage && .venv/bin/python3 -m pytest test_diners.py test_diners_db.py -q`
Expected: FAIL (`cannot import name 'accompagner'` ; `KeyError: 'menus'`).

- [ ] **Step 3: `tel_que_propose` et `accompagner` dans `diners.py`**

Juste avant `def proposer(` :

```python
def tel_que_propose(plats_du_diner, par_id):
    """Un dîner tel que Proposer le pose : vide, un plat, ou un plat et un de ses accords. « Reproposer » peut le
    changer ; un dîner composé à la main, jamais."""
    if len(plats_du_diner) <= 1:
        return True
    principal = par_id.get(plats_du_diner[0])
    return len(plats_du_diner) == 2 and principal is not None and plats_du_diner[1] in (principal.get("accords") or [])


def accompagner(choix, plats, repas, jours, remplacer=(), hasard=None):
    """{jour: [plat] ou [plat, accompagnement]} : à chaque plat proposé (`choix`, voir proposer), un de ses accords
    au hasard — accompagnement non archivé, pour nous deux, ni déjà au menu de la semaine (tous moments, hors les
    jours remplacés), ni déjà donné à un autre jour. Sans accord possible : le plat seul."""
    from random import Random
    hasard = hasard or Random()
    par_id = {p["id"]: p for p in plats}
    pris = {i for r in repas if r["jour"] in jours and r["jour"] not in remplacer for i in r["plats"]}
    menus = {}
    for j, id_plat in sorted(choix.items()):
        possibles = [a for a in par_id[id_plat].get("accords") or []
                     if a in par_id and par_id[a]["genre"] == "accompagnement" and not par_id[a]["archive"]
                     and par_id[a].get("pour", "nous") == "nous" and a not in pris]
        if possibles:
            a = hasard.choice(possibles)
            pris.add(a)
            menus[j] = [id_plat, a]
        else:
            menus[j] = [id_plat]
    return menus
```

- [ ] **Step 4: La garde de « Reproposer » dans `proposer`**

Dans `proposer`, remplacer :

```python
    remplacer = [j for j in remplacer if j in jours
                 and not (j in diners and (len(diners[j]["plats"]) > 1 or diners[j]["issue"]))]   # ni composé, ni déjà vécu
```

par :

```python
    par_id = {p["id"]: p for p in plats}
    remplacer = [j for j in remplacer if j in jours                          # ni composé à la main, ni déjà vécu
                 and not (j in diners and (diners[j]["issue"] or not tel_que_propose(diners[j]["plats"], par_id)))]
```

Et dans la docstring de `proposer`, remplacer `` `remplacer` : des jours à tirer au sort de nouveau, avec un autre plat. `` par `` `remplacer` : des jours à tirer au sort de nouveau, avec un autre plat (s'ils sont encore tels que proposés). L'accompagnement : voir accompagner. ``

- [ ] **Step 5: La route dans `serveur.py`**

Ajouter `accompagner` à l'import `from diners import (…)`. Dans `proposer_la_semaine`, remplacer :

```python
            proposes = proposer(plats, repas, semaine(jour), jour, remplacer=remplacer)
            for j, id_plat in proposes.items():
                enregistrer_repas(conn, {"jour": j, "moment": "diner", "plats": [id_plat], "issue": None})
        finally:
            conn.close()
        return jsonify({"proposes": {j.isoformat(): id_plat for j, id_plat in proposes.items()}})
```

par :

```python
            proposes = proposer(plats, repas, semaine(jour), jour, remplacer=remplacer)
            menus = accompagner(proposes, plats, repas, semaine(jour), remplacer=remplacer)
            for j, ids in menus.items():
                enregistrer_repas(conn, {"jour": j, "moment": "diner", "plats": ids, "issue": None})
        finally:
            conn.close()
        return jsonify({"proposes": {j.isoformat(): id_plat for j, id_plat in proposes.items()},   # pages v38
                        "menus": {j.isoformat(): ids for j, ids in menus.items()}})
```

Et dans sa docstring : `"""Complète la semaine (diners.proposer, un accompagnement par diners.accompagner) et enregistre les dîners proposés ; `remplacer` : jours à retirer."""`

- [ ] **Step 6: Lancer les tests**

Run: `cd voyage && .venv/bin/python3 -m pytest test_diners.py test_diners_db.py -q`
Expected: PASS.
Run: `cd voyage && .venv/bin/python3 -m pytest -q`
Expected: tout passe (680 + 6).

- [ ] **Step 7: Commit**

```bash
git add voyage/diners.py voyage/serveur.py voyage/test_diners.py voyage/test_diners_db.py
git commit -m "feat: Casa Binomerie — Proposer pose le plat et un de ses accompagnements ; Reproposer sur un dîner tel que proposé"
```

---

### Task 2: La page lit les dîners composés proposés

**Files:**
- Modify: `voyage/diners.py` (`SCRIPT_DINERS` : déclaration de `derniereProposition`, `proposerSemaine`, `aRefaire` dans `vueSemaine`)
- Modify: `voyage/valise.py` (`VERSION_PAGE = 38` → `39`)
- Test: `voyage/test_diners.py` (`test_page_diners`, nouveau `test_version_page_proposer`)

**Interfaces:**
- Consumes: réponse `{"proposes": {iso: id}, "menus": {iso: [ids]}}` de `POST api/diners/proposer` (Task 1).

- [ ] **Step 1: Écrire les tests qui échouent**

Dans `voyage/test_diners.py`, à la fin de `test_page_diners` :

```python
    assert "r.menus" in html and "plats.join(' ') === derniereProposition[iso]" in html             # étape 3
```

et après `test_version_page_accords` :

```python
def test_version_page_proposer():
    from valise import VERSION_PAGE
    assert VERSION_PAGE >= 39
```

- [ ] **Step 2: Lancer les tests, vérifier qu'ils échouent**

Run: `cd voyage && .venv/bin/python3 -m pytest test_diners.py -q -k "page_diners or version_page"`
Expected: FAIL.

- [ ] **Step 3: Le JS**

Remplacer :

```js
    let derniereProposition = {};                         // {jour: plat} : ce que « Reproposer » peut changer
```

par :

```js
    let derniereProposition = {};                         // {jour: 'plat accompagnement'} : ce que « Reproposer » peut changer
```

Dans `proposerSemaine`, remplacer :

```js
              const jours = Object.keys(r.proposes);
              jours.forEach(function (iso) {
                  d.repas = d.repas.filter(function (x) { return !(x.jour === iso && x.moment === 'diner'); })
                                   .concat([{ jour: iso, moment: 'diner', plats: [r.proposes[iso]], issue: null }]);
              });
              derniereProposition = remplacer && remplacer.length ? Object.assign({}, derniereProposition, r.proposes) : r.proposes;
              garder(); afficher();
              messageSemaine = jours.length ? jours.length + ' dîner(s) proposé(s). Ajoute un accompagnement ou un dessert, puis envoie aux courses.'
```

par :

```js
              const jours = Object.keys(r.proposes), poses = {};
              jours.forEach(function (iso) {
                  const plats = (r.menus && r.menus[iso]) || [r.proposes[iso]];   // le plat et son accompagnement
                  d.repas = d.repas.filter(function (x) { return !(x.jour === iso && x.moment === 'diner'); })
                                   .concat([{ jour: iso, moment: 'diner', plats: plats, issue: null }]);
                  poses[iso] = plats.join(' ');
              });
              derniereProposition = remplacer && remplacer.length ? Object.assign({}, derniereProposition, poses) : poses;
              garder(); afficher();
              messageSemaine = jours.length ? jours.length + ' dîner(s) proposé(s), avec un accompagnement quand le plat en a. Change-le ou ajoute un dessert, puis envoie aux courses.'
```

Dans `vueSemaine`, remplacer :

```js
            const r = repas(iso, 'diner'); return r.plats.length === 1 && r.plats[0] === derniereProposition[iso]; });
```

par :

```js
            return repas(iso, 'diner').plats.join(' ') === derniereProposition[iso]; });
```

- [ ] **Step 4: VERSION_PAGE**

Dans `voyage/valise.py`, `VERSION_PAGE = 38` devient `VERSION_PAGE = 39`.

- [ ] **Step 5: Lancer les tests**

Run: `cd voyage && .venv/bin/python3 -m pytest -q`
Expected: tout passe.
Contrôle de syntaxe JS : `cd voyage && .venv/bin/python3 -c "from diners import SCRIPT_DINERS; open('/tmp/diners.js','w').write(SCRIPT_DINERS)" && node --check /tmp/diners.js`
Expected: aucune sortie.

- [ ] **Step 6: Commit**

```bash
git add voyage/diners.py voyage/valise.py voyage/test_diners.py
git commit -m "feat: Casa Binomerie — la Semaine affiche les dîners proposés avec leur accompagnement, VERSION_PAGE 39"
```

---

### Task 3: Vérification sur une copie de la prod (contrôleur, pas de sous-agent)

**Files:** aucun dans le repo.

- [ ] **Step 1: Copie locale de la prod (Neon en lecture seule)**

Base `valise_copie` créée avec le schéma de `main`, tables `plats`, `repas`, `soirs`, `courses`, `placard`, `reprises` copiées depuis Neon en session `readonly` (script du scratchpad). Pas de migration à appliquer (aucun changement de schéma) : `appliquer_schema.py --base valise_copie` à blanc doit n'annoncer rien à créer ni à reprendre.

- [ ] **Step 2: Vérification dans Chrome**

Serveur local sur la copie (port 8001), `http://localhost:8001/diners#semaine` :
- Vider les dîners proposables de la semaine si besoin (retirer les plats d'un ou deux soirs), puis « Proposer ma semaine » : chaque dîner proposé dont le plat a des accords arrive avec un accompagnement de ses accords ; aucun accompagnement deux fois ; le message parle de l'accompagnement.
- « Reproposer » : change plat et accompagnement des soirs non touchés ; un soir où l'on a changé l'accompagnement à la main n'est plus reproposé (le bouton ne le compte plus).
- Recharger : les dîners composés tiennent (ils viennent du serveur).
- 390 px sans débordement ; console sans erreur.
Puis arrêter le serveur et supprimer `valise_copie`.

- [ ] **Step 3: S'arrêter et demander à Julien**

Résumer (livré, tests, vérification Chrome ; pas de migration Neon), puis attendre son accord explicite avant push, PR, merge.
