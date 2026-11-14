# Casa « Proposer ma semaine » en grille Midi / Soir — plan d'implémentation

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal :** « Proposer ma semaine » remplit exactement les repas cochés dans une grille 7 jours × Midi / Soir.

**Architecture :** une nouvelle fonction pure `diners.proposer_cases` (cases explicites, règles midi / soir) à côté
de `proposer` (gardée pour l'ancien corps d'API) ; la route `POST /api/diners/proposer` choisit selon la présence
de `cases` ; la page Dîners (vue Semaine) affiche la grille et envoie les cases.

**Tech Stack :** Python 3 / Flask, JS inline (`SCRIPT_DINERS` dans `voyage/diners.py`), pytest.

Spec : `docs/superpowers/specs/2026-11-14-casa-proposer-grille-design.md`.

## Global Constraints

- Tests : `cd voyage && .venv/bin/python3 -m pytest -q` (956 verts au départ). TDD : test rouge avant le code.
- Libellés et commentaires en français, style du code voisin. Pas d'emoji.
- Aucune migration. `VERSION_PAGE` (`voyage/valise.py`) = 57 à la Task 3, avec une ligne d'historique
  « # 57 = Proposer ma semaine : grille Midi / Soir. » au-dessus.
- `MINUTES_MIDI = 30` ; `MINUTES_SEMAINE = 45` et `RECENT = 14` inchangés.
- Ne jamais commiter `.claude/skills/chef-casa/SKILL.md`. Commits terminés par
  `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. Pas de push.

---

### Task 1 : `proposer_cases` (logique pure)

**Files :** Modify `voyage/diners.py` (après `proposer`, avant `LIVRAISON_DEUX`) ; Test `voyage/test_diners.py`
(à la suite des tests de `proposer`, réutiliser `plat`, `carte`, `diner`, `SEMAINE`, `LUN`, `Random`, `timedelta`).

**Interfaces :**
- Produit : `MINUTES_MIDI = 30` et
  `proposer_cases(plats, repas, cases, aujourd_hui, remplacer=(), hasard=None, a_finir=()) -> {(date, moment): id}`
  - `cases` : `[(date, "diner"|"dejeuner")]` cochées ; `remplacer` : `[(date, moment)]` à retirer puis reproposer
    (seulement si le repas est encore « tel que proposé » : `tel_que_propose(r["plats"], par_id)` et sans issue).
  - Une case est libre si aucun repas de ce jour et ce moment n'a de plats ni d'issue — pour `dejeuner`, un `brunch`
    posé le même jour l'occupe aussi — ou si elle est dans `remplacer` (et remplaçable). Jours < `aujourd_hui` : ignorés.
    Les cases de `remplacer` sont à remplir même si absentes de `cases`.
  - Candidats : comme `proposer` (genre plat, non archivé, `pour` nous, recette, pas `brunch-`, ni posés dans la
    semaine hors cases remplacées, ni mangés `fait` ces `RECENT` jours, ni le plat d'une case remplacée).
  - Temps : `dejeuner` ≤ `MINUTES_MIDI` tous les jours ; `diner` ≤ `MINUTES_SEMAINE` du lundi au jeudi.
  - Anti-gaspi : pour chaque `(cle, jusqu_au)` de `a_finir` trié par date, le plus rapide plat `statut` carnet qui
    l'utilise (`normaliser(i) == cle`), sur la première case libre (ordre : jour, puis `dejeuner` avant `diner`)
    ≤ `jusqu_au` dont il respecte le temps.
  - Puis les autres cases (dimanche d'abord comme `proposer`, puis par jour / moment) : un plat à tester au plus
    par semaine (compter ceux déjà posés), sans doublon.
  - Rendu trié par (jour, moment).

- [ ] **Step 1 : tests rouges** (dans `test_diners.py`) :

```python
from diners import proposer_cases, MINUTES_MIDI

MAR, SAM, DIM = LUN + timedelta(days=1), LUN + timedelta(days=5), LUN + timedelta(days=6)


def test_proposer_cases_remplit_exactement_les_cases_cochees():
    cases = [(j, "diner") for j in SEMAINE] + [(SAM, "dejeuner"), (DIM, "dejeuner")]
    p = proposer_cases(carte(n=20), [], cases, LUN, hasard=Random(1))
    assert sorted(p) == sorted(cases) and len(set(p.values())) == 9          # 9 repas, aucun doublon


def test_proposer_cases_midi_rapide_et_soir_comme_avant():
    plats = carte(n=4, a_tester=0) + [{**plat(f"plat-moyen-{i}", f"Moyen {i}", minutes=40), "recette": "1.",
                                       "pour": "nous"} for i in range(4)]
    for graine in range(15):
        p = proposer_cases(plats, [], [(LUN, "dejeuner"), (MAR, "dejeuner"), (LUN, "diner")], LUN,
                           hasard=Random(graine))
        assert all(not p[(j, "dejeuner")].startswith("plat-moyen") for j in (LUN, MAR))   # 40 min > 30 à midi
    assert MINUTES_MIDI == 30


def test_proposer_cases_ne_touche_pas_ce_qui_est_pose():
    repas = [diner(LUN, "plat-carnet-00"), diner(MAR, issue="dehors"),
             diner(SAM, "plat-carnet-01", moment="brunch")]
    p = proposer_cases(carte(), repas, [(LUN, "diner"), (MAR, "diner"), (SAM, "dejeuner"), (DIM, "diner")], LUN,
                       hasard=Random(2))
    assert list(p) == [(DIM, "diner")] and p[(DIM, "diner")] not in {"plat-carnet-00", "plat-carnet-01"}


def test_proposer_cases_jours_passes_ignores():
    assert proposer_cases(carte(), [], [(LUN, "diner")], MAR, hasard=Random(3)) == {}


def test_proposer_cases_remplacer_un_dejeuner():
    plats = carte()
    p = proposer_cases(plats, [], [(SAM, "dejeuner")], LUN, hasard=Random(4))
    avant = p[(SAM, "dejeuner")]
    q = proposer_cases(plats, [diner(SAM, avant, moment="dejeuner")], [], LUN,
                       remplacer=[(SAM, "dejeuner")], hasard=Random(5))
    assert list(q) == [(SAM, "dejeuner")] and q[(SAM, "dejeuner")] != avant


def test_proposer_cases_un_seul_plat_a_tester():
    cases = [(j, m) for j in SEMAINE for m in ("dejeuner", "diner")]
    p = proposer_cases(carte(n=20, a_tester=5), [], cases, LUN, hasard=Random(6))
    assert sum(v.startswith("plat-tester") for v in p.values()) <= 1


def test_proposer_cases_anti_gaspi_a_midi():
    plats = carte(n=6, a_tester=0) + [{**plat("plat-epinards", "Épinards", minutes=20, ingredients=["épinards frais"]),
                                       "recette": "1.", "pour": "nous"}]
    p = proposer_cases(plats, [], [(LUN, "dejeuner"), (LUN, "diner"), (MAR, "diner")], LUN,
                       a_finir=[("epinards frais", MAR)], hasard=Random(7))
    assert p[(LUN, "dejeuner")] == "plat-epinards"
```

(Si le helper `diner(...)` du fichier ne prend pas `moment=`, regarder sa signature et l'utiliser comme les tests
existants `test_proposer_ignore_dejeuner_et_brunch`.)

- [ ] **Step 2 :** `.venv/bin/python3 -m pytest -q test_diners.py -k proposer_cases` → FAIL (ImportError).
- [ ] **Step 3 :** implémenter `MINUTES_MIDI` et `proposer_cases` selon l'interface ci-dessus. Réutiliser
  `tel_que_propose`, `normaliser`, `RECENT`, `MINUTES_SEMAINE` ; ne pas modifier `proposer`. Docstring en français
  dans le style de `proposer`.
- [ ] **Step 4 :** suite complète verte.
- [ ] **Step 5 : commit** `feat(diners): proposer_cases, les repas cochés midi et soir`.

### Task 2 : l'API accepte des cases

**Files :** Modify `voyage/serveur.py` (route `proposer_la_semaine`, import) ; Test `voyage/test_diners_db.py`.

**Interfaces :**
- Consomme : `proposer_cases` (Task 1), `accompagner(choix, plats, repas, jours, hasard=None)` (existant :
  `choix` = `{jour: id}` des **dîners** seulement).
- Produit : `POST /api/diners/proposer` avec `cases` (liste de `{"jour": iso, "moment": "diner"|"dejeuner"}`) et
  `remplacer` (liste de mêmes objets) → enregistre chaque repas proposé (`enregistrer_repas`, `issue` None ;
  dîner = `accompagner(...)[jour]`, déjeuner = `[id]`) et rend `{"menus": {"<iso>|<moment>": [ids]}}`.
  Sans clé `cases` : comportement actuel inchangé. Corps invalide (jour non ISO, moment hors des deux) → 400.

- [ ] **Step 1 : tests rouges** (dans `test_diners_db.py`, fixture `client` du fichier, `J` = aujourd'hui des tests) :

```python
def test_api_proposer_cases_midi_et_soir(client):
    demain = (J + timedelta(days=1)).isoformat()
    cases = [{"jour": demain, "moment": "dejeuner"}, {"jour": demain, "moment": "diner"}]
    r = client.post("/api/diners/proposer", json={"cases": cases})
    assert r.status_code == 200
    menus = r.get_json()["menus"]
    assert set(menus) <= {f"{demain}|dejeuner", f"{demain}|diner"} and menus
    poses = {(x["jour"], x["moment"]): x["plats"] for x in client.get("/api/diners").get_json()["repas"]}
    assert all(poses[tuple(k.split("|"))] == ids for k, ids in menus.items())
    assert all(len(ids) == 1 for k, ids in menus.items() if k.endswith("|dejeuner"))   # midi : sans accompagnement


def test_api_proposer_cases_invalides(client):
    assert client.post("/api/diners/proposer", json={"cases": [{"jour": "x", "moment": "diner"}]}).status_code == 400
    assert client.post("/api/diners/proposer",
                       json={"cases": [{"jour": J.isoformat(), "moment": "brunch"}]}).status_code == 400
```

- [ ] **Step 2 :** FAIL. **Step 3 :** implémenter (garder l'ancien chemin intact). **Step 4 :** suite verte.
- [ ] **Step 5 : commit** `feat(diners): l'API Proposer accepte les cases midi et soir`.

### Task 3 : la grille dans la vue Semaine

**Files :** Modify `voyage/diners.py` (`SCRIPT_DINERS` : `proposerSemaine`, `vueSemaine`, état
`derniereProposition` ; CSS `STYLE_DINERS` près de `div.proposer`) ; `voyage/valise.py` (`VERSION_PAGE = 57` + ligne
d'historique) ; Test `voyage/test_diners.py`.

**Interfaces :**
- Consomme : l'API de la Task 2 (`menus` indexé `"<iso>|<moment>"`).
- Comportement :
  - « Proposer ma semaine » ouvre/ferme un bloc `div.grille-proposer` sous le bouton : un tableau 7 colonnes
    (initiale du jour + numéro, depuis `d.semaine`) × 2 lignes « Midi » / « Soir » de cases à cocher (boutons
    `aria-pressed`, cible ≥ 40 px). Case occupée (repas avec plats ou issue ; midi occupé aussi par un brunch) ou
    jour passé (`iso < d.aujourd_hui`) : désactivée, marquée « pris ».
  - Sélection mémorisée dans `localStorage` `diners:grille` (tableau de chaînes `"<0-6>|<moment>"`, 0 = lundi, à
    partir du jour de semaine de chaque date ; try/catch). Défaut : `["0|diner","1|diner","2|diner","3|diner"]`.
  - « N repas à proposer » (cases cochées et libres) ; bouton **Proposer** (inactif à 0) et **Annuler**.
  - Proposer envoie `{cases}` ; à la réponse, pose chaque menu dans `d.repas` (jour + moment), met à jour
    `derniereProposition` indexée `"<iso>|<moment>"`, ferme la grille, message « N repas proposé(s)… » ou
    « Rien à proposer : aucun plat ne convient pour ces repas. ».
  - Reproposer : les clés de `derniereProposition` dont le repas est inchangé → `{remplacer: [{jour, moment}]}`
    (sans `cases`).
  - Les déjeuners proposés s'affichent par le chemin existant (`midi` dans `vueSemaine`).
  - Texte d'aide de l'encart : remplacer « Trois ou quatre dîners suffisent. Les autres restent libres. » par
    « Coche les repas à remplir : l'app propose un plat pour chacun. ».
- `VERSION_PAGE = 57`.

- [ ] **Step 1 : test rouge** (dans `test_diners.py`) :

```python
def test_page_diners_grille_proposer():
    from diners import SCRIPT_DINERS
    html = diners_en_html()
    assert "div.grille-proposer" in html and "'diners:grille'" in SCRIPT_DINERS
    assert "cases:" in SCRIPT_DINERS and "remplacer:" in SCRIPT_DINERS
    assert "['0|diner', '1|diner', '2|diner', '3|diner']" in SCRIPT_DINERS
    assert "Trois ou quatre dîners suffisent" not in SCRIPT_DINERS
    assert "repas à proposer" in SCRIPT_DINERS
    from valise import VERSION_PAGE
    assert VERSION_PAGE >= 57
```

- [ ] **Step 2 :** FAIL. **Step 3 :** implémenter. `node --check` sur `SCRIPT_DINERS` extrait (le script ne doit pas
  lever au chargement). **Step 4 :** suite verte.
- [ ] **Step 5 : commit** `feat(diners): Proposer ma semaine en grille Midi / Soir (version 57)`.

### Task 4 : démo (gate Julien)

Copie de prod (`~/Claude/Work/perso/casa/copier_prod.py`, URL Neon fournie par Julien), serveur local sur
`valise_copie` port 8001, vérification Chrome (grille, cases prises, proposer midi + soir, reproposer, mémoire de
la grille, 0 erreur console), puis iPhone de Julien. Push / PR / merge sur son go. Arrêter le serveur de démo
ensuite (des modifications faites sur la démo ne vont pas en prod).
