# Casa journal des repas + « Hier soir ? » — plan d'implémentation

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal :** voir les repas des semaines passées (onglet Passé de Dîners, avec correction des « non noté ») et dire ce
qu'on a mangé depuis « Hier soir ? ».

**Architecture :** une fonction pure `diners.journal` + une route `GET /api/diners/passe` ; la vue `passe` dans
`SCRIPT_DINERS` ; le bloc `bloc_hier` / `SCRIPT_HIER` de `voyage/casa.py` reçoit la liste des plats et un second
temps pour « Fait maison ».

Spec : `docs/superpowers/specs/2026-11-14-casa-journal-design.md`.

## Global Constraints

- Tests : `cd voyage && .venv/bin/python3 -m pytest -q` (973 verts au départ). TDD.
- Français, style voisin, pas d'emoji ; aucune migration ; `VERSION_PAGE = 59` (Task 3) avec la ligne
  « # 59 = Dîners : onglet Passé ; Hier soir ? dit ce qu'on a mangé. ».
- `node --check` des scripts de page touchés avant chaque commit.
- Ne jamais commiter `.claude/skills/chef-casa/SKILL.md`. Commits terminés par
  `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. Pas de push.

---

### Task 1 : `journal` et `GET /api/diners/passe`

**Files :** `voyage/diners.py` (fonction pure, près de `compteur`), `voyage/serveur.py` (route, près de
`/api/diners`), tests `voyage/test_diners.py` et `voyage/test_diners_db.py`.

**Interfaces :**
- `SEMAINES_JOURNAL = 8`
- `journal(repas, plats, aujourd_hui, avant=None, n=SEMAINES_JOURNAL) -> {"semaines": [...], "suite": date | None}`
  - `avant` : un lundi (exclu) ; None = le lundi qui suit la semaine en cours. Rend les `n` semaines calendaires
    précédant `avant`, de la plus récente à la plus ancienne, en s'arrêtant à la semaine du plus ancien repas
    (aucune semaine plus ancienne que lui). `suite` = le lundi de la plus ancienne semaine rendue s'il existe un
    repas plus ancien, sinon None.
  - Une semaine : `{"lundi": date, "bilan": {"fait": n, "commande": n, "dehors": n, "autre": n, "non_note": n},
    "cout_maison": float, "jours": [{"jour": date, "soir": ligne, "midi": ligne | None}]}` — jours du lundi au
    dimanche, sans les jours ≥ `aujourd_hui` ; `midi` = le déjeuner, sinon le brunch, sinon None.
  - `ligne` : `{"plats": [{"id", "nom"}], "issue": str | None, "non_note": bool}` ; plats dans l'ordre de
    `ranger(…, moment)` ; ids inconnus ignorés ; `non_note` = plats non vides et issue None. Soir sans repas :
    `{"plats": [], "issue": None, "non_note": False}`.
  - Bilan : compte les lignes soir et midi des jours rendus (issue, ou `non_note`). `cout_maison` : somme de
    `prix_paris.cout_repas(p["ingredients"], p["recette"])` des plats des lignes `fait`, arrondie à 2 décimales.
- Route `GET /api/diners/passe` (`?avant=` ISO, doit être un lundi sinon 400) : lit les repas de
  `date(2000,1,1)` à hier (`lire_repas`), les plats (`lire_plats`), rend `journal(...)` sérialisé (dates ISO).

- [ ] **Step 1 : tests rouges** (`test_diners.py`, avec `plat`, `diner`, `LUN = date(2026, 11, 2)`) :

```python
from diners import journal, SEMAINES_JOURNAL


def test_journal_semaines_et_bilan():
    plats = [plat("plat-a", "Carbonara"), plat("plat-b", "Burger"), plat("acc-c", "Purée", genre="accompagnement")]
    jeu = LUN + timedelta(days=3)
    repas = [diner(LUN, "plat-a", "acc-c", issue="fait"), diner(LUN + timedelta(days=1), issue="commande"),
             diner(LUN + timedelta(days=2), "plat-b"), diner(jeu, "plat-b", moment="dejeuner", issue="fait"),
             diner(LUN - timedelta(days=7), "plat-a", issue="dehors")]
    j = journal(repas, plats, LUN + timedelta(days=5))                     # samedi : la semaine s'arrête à vendredi
    s = j["semaines"]
    assert [x["lundi"] for x in s] == [LUN, LUN - timedelta(days=7)] and j["suite"] is None
    assert [d["jour"] for d in s[0]["jours"]] == [LUN + timedelta(days=i) for i in range(5)]
    assert s[0]["bilan"] == {"fait": 2, "commande": 1, "dehors": 0, "autre": 0, "non_note": 1}
    lundi = s[0]["jours"][0]["soir"]
    assert [p["nom"] for p in lundi["plats"]] == ["Carbonara", "Purée"] and lundi["issue"] == "fait"
    assert s[0]["jours"][2]["soir"]["non_note"] and s[0]["jours"][3]["midi"]["issue"] == "fait"
    assert s[0]["jours"][4]["soir"] == {"plats": [], "issue": None, "non_note": False}


def test_journal_pagination():
    repas = [diner(LUN - timedelta(days=7 * k), issue="fait") for k in range(10)]
    j = journal(repas, [], LUN + timedelta(days=1), n=4)
    assert len(j["semaines"]) == 4 and j["suite"] == LUN - timedelta(days=21)
    k = journal(repas, [], LUN + timedelta(days=1), avant=j["suite"], n=8)
    assert [x["lundi"] for x in k["semaines"]][0] == LUN - timedelta(days=28) and k["suite"] is None
    assert SEMAINES_JOURNAL == 8
```

  et dans `test_diners_db.py` (fixture `client`, `J`) :

```python
def test_api_passe(client):
    hier = (J - timedelta(days=1)).isoformat()
    client.post("/api/repas", json={"jour": hier, "moment": "diner", "plats": ["plat-carbonara"], "issue": "fait"})
    r = client.get("/api/diners/passe")
    assert r.status_code == 200
    jours = [d for s in r.get_json()["semaines"] for d in s["jours"]]
    assert any(d["jour"] == hier and d["soir"]["issue"] == "fait" for d in jours)
    assert client.get("/api/diners/passe?avant=pas-une-date").status_code == 400
```

  (Si `plat-carbonara` n'existe pas dans la base de test semée, prendre un id de plat présent — regarder les autres
  tests du fichier.)
- [ ] **Step 2 :** FAIL. **Step 3 :** implémenter. **Step 4 :** suite verte.
- [ ] **Step 5 : commit** `feat(diners): journal des semaines passées et GET /api/diners/passe`.

### Task 2 : l'onglet « Passé »

**Files :** `voyage/diners.py` (`SCRIPT_DINERS` : vues, `diners_en_html` : onglets internes ; `STYLE_DINERS`),
`voyage/test_diners.py`.

**Interfaces :** consomme `GET api/diners/passe` (Task 1). La vue `passe` s'ajoute à `VUES` de la page Dîners
(`['ce-soir', 'semaine', 'passe']`), avec le bouton d'onglet « Passé » ; la grille des onglets passe à 3 colonnes
(`nav.vues` : `repeat(3, 1fr)`).
- Données chargées à la première ouverture de l'onglet et gardées en mémoire du module (pas dans `d`, qui est
  remplacé par `charger()`) ; « Semaines plus anciennes » charge `?avant=<suite>` et ajoute les cartes ; hors ligne :
  « Pas de réseau : l'historique se charge une fois connecté. ».
- Rendu selon la spec §1 (carte par semaine `div.semaine-passee`, bilan, lignes Soir / Midi, badges
  `span.issue.<issue>` et `button.issue.non-note`). Un appui sur un nom → `ouvrirFiche(id)`.
- Correction : un appui sur « non noté » affiche sous la ligne 4 boutons (Fait maison, Commandé, Dehors, Autre) si le
  jour est à ≤ 60 jours d'aujourd'hui ; le choix envoie `{jour, moment, plats: ids, issue}` par la file existante
  (`envoyer({url: 'api/repas', …})`, comme `enregistrerRepas`) puis met à jour la ligne et le bilan en mémoire.
- Texte vide : « Rien de noté pour l'instant. » si aucune semaine.

- [ ] **Step 1 : test rouge** :

```python
def test_page_diners_onglet_passe():
    from diners import SCRIPT_DINERS
    html = diners_en_html()
    assert 'data-vue="passe"' in html and ">Passé<" in html
    assert "'passe'" in SCRIPT_DINERS and "api/diners/passe" in SCRIPT_DINERS
    assert "Semaines plus anciennes" in SCRIPT_DINERS and "non noté" in SCRIPT_DINERS
    assert "repeat(3, 1fr)" in html
    assert 'data-vue="passe"' not in diners_en_html("recettes")
```

- [ ] **Step 2-4 :** FAIL, implémenter, suite verte, `node --check`.
- [ ] **Step 5 : commit** `feat(diners): onglet Passé, le journal des repas et la correction des non notés`.

### Task 3 : « Hier soir ? » → ce qu'on a mangé

**Files :** `voyage/casa.py` (`bloc_hier`, `SCRIPT_HIER`, `aujourdhui_en_html`, CSS `div.bloc-hier`),
`voyage/serveur.py` (route `/` : passer les plats), `voyage/valise.py` (`VERSION_PAGE = 59`), tests
`voyage/test_casa.py`.

**Interfaces :**
- `bloc_hier(diner_hier, plats=())` : `plats` = `[{"id", "nom"}]` des plats non archivés (tous genres), triés par
  nom ; le bloc embarque `data-prevus` (les noms des plats prévus, dans l'ordre de `ranger`) et un
  `<datalist id="plats-hier">` des noms, avec `<script type="application/json" id="plats-hier-json">` (nom → id).
  `aujourdhui_en_html(..., plats_hier=())` le transmet ; la route `/` passe la liste.
- `SCRIPT_HIER` : Commandé / Dehors / Autre inchangés. Fait maison :
  - avec plats prévus → texte « C'était bien : A + B ? », boutons **Oui** (POST fait + plats prévus) et
    **Autre chose** ;
  - sans plats prévus ou après Autre chose → champ `input[list=plats-hier]` « Qu'avez-vous mangé ? », **Valider**
    (nom exact connu → POST fait + [id] ; sinon message « Choisis une recette de la liste. ») et **Je ne sais plus**
    (POST fait + plats []).
  - Échec réseau : message existant, boutons réactivés.
- `VERSION_PAGE = 59` + ligne d'historique.

- [ ] **Step 1 : tests rouges** (`test_casa.py`) :

```python
def test_bloc_hier_fait_maison_demande_le_plat():
    from datetime import date
    from casa import bloc_hier, SCRIPT_HIER
    hier = {"jour": date(2026, 11, 13), "moment": "diner", "plats": ["plat-a"], "issue": None}
    html = bloc_hier(hier, [{"id": "plat-a", "nom": "Carbonara"}, {"id": "plat-b", "nom": "Burger"}])
    assert 'data-prevus="[&quot;Carbonara&quot;]"' in html or "data-prevus='[\"Carbonara\"]'" in html
    assert '<datalist id="plats-hier">' in html and '<option value="Burger">' in html
    assert 'id="plats-hier-json"' in html
    for texte in ("C'était bien", "Autre chose", "Qu'avez-vous mangé ?", "Je ne sais plus",
                  "Choisis une recette de la liste."):
        assert texte in SCRIPT_HIER
    assert bloc_hier({**hier, "issue": "fait"}, []) == ""
```

  (Adapter l'assertion `data-prevus` à l'échappement réellement utilisé par `echapper` — garder l'intention : les
  noms prévus sont dans l'attribut.)
- [ ] **Step 2-4 :** FAIL, implémenter, suite verte, `node --check` de `SCRIPT_HIER`.
- [ ] **Step 5 : commit** `feat(casa): Hier soir ? Fait maison dit ce qu'on a mangé (version 59)`.

### Task 4 : démo (gate Julien)

Copie de prod (URL Neon fournie par Julien, `~/Claude/Work/perso/casa/copier_prod.py`) ou copie du matin si Julien
le préfère ; serveur `valise_copie` :8001 ; Chrome : onglet Passé (semaines, bilan, fiche, correction d'un non noté),
Aujourd'hui (Hier soir ? : Oui / Autre chose / Je ne sais plus) ; puis iPhone. Arrêter le serveur après.
