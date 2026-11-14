# Casa Cucina (onglet Recettes) + refonte Courses — plan d'implémentation

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal :** Popote devient Cucina avec quatre onglets (Dîners · Recettes · Courses · Cave), puis la page Courses passe à
une liste unique par rayon et à un « À la maison » qui remplace Placard, Habituels et Réassort.

**Architecture :** deux livraisons, une PR chacune. (A) `design.py` porte la barre et les onglets ; `/recettes` sert la
page de `diners.py` ouverte sur la vue Recettes (`data-page` sur `<body>`). (B) `courses.py` : règles pures dans un
nouveau `SCRIPT_REGLES_COURSES` testé sous node, page réécrite autour ; `GET /api/courses` ajoute le rayon deviné de
chaque élément du placard. Aucune migration.

**Tech Stack :** Python 3 / Flask, pages HTML + JS inline, Postgres (Neon en prod, `valise_test` en test), pytest, node
pour les règles JS.

Spec : `docs/superpowers/specs/2026-11-14-casa-cucina-courses-design.md`.

## Global Constraints

- Tests : `cd voyage && .venv/bin/python3 -m pytest -q` (930 verts au départ). TDD : test rouge avant le code.
- Libellés et commentaires en français, style du code voisin (commentaires courts en fin de ligne).
- Pas d'emoji dans l'interface (icônes SVG au trait seulement).
- `VERSION_PAGE` (`voyage/valise.py:1648`, 53 aujourd'hui) +1 à chaque livraison : 54 pour A, 55 pour B.
- Aucune migration de base, aucune écriture en prod pendant le dev.
- Avant tout push / PR / merge : démo locale sur une copie de la prod, testée par Julien sur Mac et iPhone (wifi).
  Push, PR et merge seulement quand Julien le demande. `gh` : `env -u GITHUB_TOKEN gh ...`.
- Commits terminés par `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- Le fichier `.claude/skills/chef-casa/SKILL.md` a une modification non commitée de Julien : ne jamais l'ajouter.

---

# Livraison A — Cucina (branche `feat/casa-cucina`, déjà créée depuis `origin/main`, spec commitée)

### Task 1 : Popote devient Cucina, quatre onglets

**Files :**
- Modify : `voyage/design.py:51-60` (HUB, POPOTE), `:67` (ICONES_HUB), `:110-132` (nav_hub, onglets_popote), `:148`, `:161-168` (CSS)
- Modify : `voyage/diners.py:15,1240`, `voyage/courses.py:15,659`, `voyage/cave.py:9` + son appel `onglets_popote("cave")`
- Test : `voyage/test_casa.py:20-40`, `test_courses.py:114`, `test_courses_db.py:164`, `test_cave.py:108`,
  `test_diners.py:136`, `test_diners_db.py:112`, `test_sortir.py:130`

**Interfaces :**
- Produit : `design.CUCINA = ("diners", "recettes", "courses", "cave")`, `design.onglets_cucina(actif) -> str`
  (`<nav class="cucina" aria-label="Cucina">` + un `<a href="{cle}" data-cucina="{cle}">` par onglet),
  `nav_hub(actif)` met `data-hub="cucina"` actif pour toute clé de `CUCINA`.

- [ ] **Step 1 : tests rouges.** Dans `test_casa.py`, remplacer les deux tests Popote par :

```python
def test_barre_du_bas_a_quatre_entrees():
    from design import nav_hub
    nav = nav_hub("aujourdhui")
    assert [x.split('"')[0] for x in nav.split('data-hub="')[1:]] == ["aujourdhui", "cucina", "sortir", "budget", "vadrouille"]
    assert '<a href="diners" data-hub="cucina"' in nav and "<span>Cucina</span>" in nav and "Popote" not in nav
    for page in ("diners", "recettes", "courses", "cave"):
        assert 'data-hub="cucina" class="actif" aria-current="page"' in nav_hub(page)


def test_onglets_cucina():
    from design import onglets_cucina
    html = onglets_cucina("courses")
    assert html.startswith('<nav class="cucina" aria-label="Cucina">')
    assert [x.split('"')[0] for x in html.split('data-cucina="')[1:]] == ["diners", "recettes", "courses", "cave"]
    assert '<a href="recettes" data-cucina="recettes">Recettes</a>' in html
    assert '<a href="courses" data-cucina="courses" class="actif" aria-current="page">Courses</a>' in html
```

et dans `test_le_hub_commence_par_aujourd_hui_et_finit_par_la_vadrouille`, `"popote"` → `"cucina"`.
Dans les six autres fichiers de test listés, remplacer `data-hub="popote"` par `data-hub="cucina"`,
`data-popote=` par `data-cucina=`, et dans `test_sortir.py:130` `'class="popote"'` par `'class="cucina"'`.

- [ ] **Step 2 :** `.venv/bin/python3 -m pytest -q test_casa.py test_courses.py test_cave.py test_diners.py test_sortir.py`
  → FAIL (`ImportError: onglets_cucina`, `popote` dans les pages).

- [ ] **Step 3 : implémentation dans `design.py`.**

```python
HUB = [
    ("aujourdhui", "Aujourd'hui", "./"),
    ("cucina", "Cucina", "diners"),                     # Dîners · Recettes · Courses · Cave, onglets en haut des pages
    ("sortir", "Sortir", "sortir"),
    ("budget", "Budget", "budget"),
    ("vadrouille", "Vadrouille", "vadrouille"),          # court : tient dans la barre du bas sur iPhone
]
CUCINA = ("diners", "recettes", "courses", "cave")
```

Dans `ICONES_HUB`, la clé `"popote"` devient `"cucina"` (même SVG). Dans `nav_hub` :
`actif = "cucina" if actif in CUCINA else actif`. Remplacer `onglets_popote` par :

```python
def onglets_cucina(actif):
    """Les onglets de Cucina en haut de Dîners, Recettes, Courses et Cave (à la place du titre) ; la page active soulignée."""
    liens = "".join(
        f'<a href="{cle}" data-cucina="{cle}"'
        + (' class="actif" aria-current="page">' if cle == actif else ">")
        + f"{libelle}</a>"
        for cle, libelle in (("diners", "Dîners"), ("recettes", "Recettes"), ("courses", "Courses"), ("cave", "Cave")))
    return f'<nav class="cucina" aria-label="Cucina">{liens}</nav>'
```

CSS (`design.py:148` et `:161-168`) : `data-hub="popote"` → `data-hub="cucina"`, `nav.popote` → `nav.cucina`,
`data-popote` → `data-cucina`, et taille réduite pour quatre onglets sur iPhone :

```css
nav.cucina { display: flex; gap: 16px; margin: 0 0 18px; overflow-x: auto; scrollbar-width: none; }
nav.cucina::-webkit-scrollbar { display: none; }
nav.cucina a { flex: none; font-size: 19px; font-weight: 800; color: var(--doux); text-decoration: none; padding: 2px 0 6px;
               border-bottom: 3px solid transparent; }
nav.cucina a.actif { color: var(--texte); border-bottom-color: var(--c); }
nav.cucina a[data-cucina="diners"], nav.cucina a[data-cucina="recettes"] { --c: var(--diners); }
nav.cucina a[data-cucina="courses"] { --c: var(--courses); }
nav.cucina a[data-cucina="cave"] { --c: var(--cave); }
@media (max-width: 899px) { body.hub-page h1, body.hub-page nav.cucina { padding-right: 52px; } }
```

Dans `diners.py`, `courses.py`, `cave.py` : import et appels `onglets_popote(...)` → `onglets_cucina(...)`.
Vérifier qu'il ne reste rien : `grep -rni popote voyage --include='*.py'` → seulement des commentaires historiques
éventuels, à réécrire aussi.

- [ ] **Step 4 :** suite complète `.venv/bin/python3 -m pytest -q` → tout vert.
- [ ] **Step 5 : commit** `feat(casa): Popote devient Cucina, barre à quatre onglets` (fichiers `voyage/design.py`,
  `diners.py`, `courses.py`, `cave.py`, tests touchés).

### Task 2 : la page `/recettes`

**Files :**
- Modify : `voyage/diners.py:356-360` (CSS `nav.vues`), `:520` (`let vue`), `:711`, `:1097`, `:1194-1207` (vues, liens),
  `:1220-1257` (`diners_en_html`)
- Modify : `voyage/serveur.py:145-147` (route), `voyage/valise.py:1648` (`VERSION_PAGE = 54`)
- Test : `voyage/test_diners.py:133-140`, `voyage/test_diners_db.py` (route)

**Interfaces :**
- Consomme : `design.onglets_cucina(actif)` (Task 1).
- Produit : `diners.diners_en_html(page="diners")`, `page` ∈ `{"diners", "recettes"}` ; route `GET /recettes`.

- [ ] **Step 1 : tests rouges.** Dans `test_diners.py`, remplacer `test_page_diners` par :

```python
def test_page_diners():
    html = diners_en_html()
    assert "<title>Dîners · Casa Binomerie</title>" in html and 'data-page="diners"' in html
    assert 'data-hub="cucina" class="actif"' in html and 'data-cucina="diners" class="actif"' in html and "<h1>Dîners</h1>" not in html
    assert 'data-vue="ce-soir"' in html and 'data-vue="semaine"' in html and 'data-vue="recettes"' not in html
    assert 'data-vue="carnet"' not in html and 'data-vue="a-tester"' not in html
    assert "function vueRecettes" in html and "function ordreRecettes" in html


def test_page_recettes():
    html = diners_en_html("recettes")
    assert "<title>Recettes · Casa Binomerie</title>" in html and 'data-page="recettes"' in html
    assert 'data-hub="cucina" class="actif"' in html and 'data-cucina="recettes" class="actif"' in html
    assert '<nav class="vues"' not in html                       # pas d'onglets internes
    assert "function vueRecettes" in html


def test_anciens_liens_vers_recettes_et_allers_retours():
    from diners import SCRIPT_DINERS
    assert "location.replace('recettes')" in SCRIPT_DINERS       # diners#recettes, #carnet, #a-tester
    assert "function allerA(" in SCRIPT_DINERS and "location.href = 'diners#' + v" in SCRIPT_DINERS
    assert "vue = 'ce-soir'; afficher()" not in SCRIPT_DINERS     # tout passe par allerA
```

Dans `test_diners_db.py`, à côté du test de la page Dîners :

```python
def test_route_recettes(client):
    html = client.get("/recettes").get_data(as_text=True)
    assert 'data-page="recettes"' in html and 'data-cucina="recettes" class="actif"' in html
```

(utiliser la fixture `client` du fichier ; si son nom diffère, reprendre celle du test de `/diners` à la ligne ~110).

- [ ] **Step 2 :** `.venv/bin/python3 -m pytest -q test_diners.py test_diners_db.py` → FAIL.

- [ ] **Step 3 : implémentation.**

`diners_en_html` :

```python
def diners_en_html(page="diners"):
    """La page Dîners (Ce soir · Semaine) ou Recettes (page="recettes") : une coquille, remplie par le script depuis
    api/diners (copie gardée hors ligne). Même script ; la page choisit la vue de départ."""
    ...
    titre = "Recettes" if page == "recettes" else "Dîners"
    vues = ("" if page == "recettes" else
            '<nav class="vues">' + "".join(f'<button type="button" data-vue="{v}">{t}</button>'
                                           for v, t in [("ce-soir", "Ce soir"), ("semaine", "Semaine")]) + "</nav>")
```

et dans le gabarit : `<title>{titre} · Casa Binomerie</title>`,
`<body class="accueil hub-page diners" data-page="{page}">`, `{onglets_cucina(page)}`, `{vues}` à la place de
`<nav class="vues">{vues}</nav>`, `{nav_hub(page)}`.

CSS `diners.py:356` : `grid-template-columns: repeat(3, 1fr)` → `repeat(2, 1fr)`.

Script (`diners.py:520`) :

```js
    const PAGE = document.body.dataset.page || 'diners';
    let vue = PAGE === 'recettes' ? 'recettes' : 'ce-soir', filtre = 'tout', recherche = '';
```

Ajouter près de `afficher()` :

```js
    // Ce soir et Semaine vivent sur la page Dîners, Recettes sur la sienne
    function allerA(v) {
        if ((PAGE === 'recettes') !== (v === 'recettes')) { location.href = v === 'recettes' ? 'recettes' : 'diners#' + v; return; }
        vue = v; afficher();
    }
```

Remplacer `:711` `function () { vue = 'semaine'; afficher(); }` par `function () { allerA('semaine'); }` et `:1097`
`... fermer(); vue = 'ce-soir'; afficher(); }` par `... fermer(); allerA('ce-soir'); }`.

Remplacer le bloc des liens (`:1203-1207`) par :

```js
    const VUES = PAGE === 'recettes' ? ['recettes'] : ['ce-soir', 'semaine'];
    const VERS_RECETTES = ['recettes', 'carnet', 'a-tester'];                    // liens et favoris d'avant la page Recettes
    function vueDuLien() { const h = location.hash.slice(1); return VUES.indexOf(h) >= 0 ? h : null; }
    if (PAGE === 'diners' && VERS_RECETTES.indexOf(location.hash.slice(1)) >= 0) location.replace('recettes');
    if (vueDuLien()) vue = vueDuLien();
    window.addEventListener('hashchange', function () { if (vueDuLien()) { vue = vueDuLien(); afficher(); } });
```

`serveur.py` après la route `/diners` :

```python
    @routes.get("/recettes")
    def page_recettes():
        return Response(diners_en_html("recettes"), mimetype="text/html")
```

`valise.py:1648` : `VERSION_PAGE = 54`.

- [ ] **Step 4 :** `grep -n "vue = '" voyage/diners.py` → seulement la déclaration et `allerA`. Suite complète verte.
- [ ] **Step 5 : commit** `feat(casa): Recettes au niveau de Dîners, Courses et Cave (page /recettes, version 54)`.

### Task 3 : démo livraison A (gate Julien)

- [ ] Copie de prod dans `valise_test` (procédure habituelle des démos Casa, lecture seule de Neon ; si l'accès Neon
  n'est pas disponible dans la session, demander à Julien de le fournir, ne pas le chercher dans les fichiers).
- [ ] Serveur local : `DATABASE_URL="" .venv/bin/python3 -c "from serveur import creer_app; creer_app('valise_test', secret='').run(host='0.0.0.0', port=8766)"`.
- [ ] Vérifier dans Chrome à 390 px : les 4 onglets tiennent (ou défilent) sans passer sous le bouton du thème ;
  Recettes : fiche → « Ce soir » ramène sur `diners#ce-soir` ; `diners#recettes` ouvre `recettes`.
- [ ] Julien teste sur iPhone (IP du Mac, port 8766). Sur son go : push, PR, merge, attendre Render (`sw.js` valise-v54),
  vérifier `/recettes` en prod.

---

# Livraison B — Courses « À la maison » (branche `feat/casa-courses-maison` depuis `origin/main` après merge de A)

### Task 4 : le placard rendu avec son rayon

**Files :**
- Modify : `voyage/serveur.py:47` (import), `:266-272` (`lire_les_courses`)
- Test : `voyage/test_courses_db.py:176-186`

**Interfaces :**
- Produit : `GET /api/courses` → `{"articles": [...], "placard": [{cle, nom, en_stock, bientot, zone, rayon}]}` ;
  `rayon = courses.deviner_rayon(nom)`, non stocké.

- [ ] **Step 1 : test rouge.** Dans `test_api_vider_et_placard`, remplacer l'assertion du placard par :

```python
    assert client.get("/api/courses").get_json()["placard"] == [{**basique("Pâtes", en_stock=False), "rayon": "epicerie"}]
```

et ajouter :

```python
def test_api_courses_rayon_du_placard(client):
    client.post("/api/placard", json={"nom": "parmesan", "en_stock": True, "zone": "frigo"})
    client.post("/api/placard", json={"nom": "sauce soja", "en_stock": True})
    rayons = {p["nom"]: p["rayon"] for p in client.get("/api/courses").get_json()["placard"]}
    assert rayons == {"parmesan": "frais", "sauce soja": "specialise"}
```

- [ ] **Step 2 :** `.venv/bin/python3 -m pytest -q test_courses_db.py` → FAIL (pas de clé `rayon`).
- [ ] **Step 3 :** `serveur.py:47` : ajouter `deviner_rayon` à l'import de `courses`. `lire_les_courses` :

```python
    @routes.get("/api/courses")
    def lire_les_courses():
        """La liste et le placard ; chaque élément du placard avec son rayon deviné (« À la maison » se range par rayon)."""
        conn = emprunter(app.config["NOM_BASE"])
        try:
            lu = lire_courses(conn)
        finally:
            conn.close()
        return jsonify({**lu, "placard": [{**p, "rayon": deviner_rayon(p["nom"])} for p in lu["placard"]]})
```

- [ ] **Step 4 :** suite complète verte.
- [ ] **Step 5 : commit** `feat(courses): le placard rendu avec son rayon deviné`.

### Task 5 : les règles de la page (JS pur, testé sous node)

**Files :**
- Modify : `voyage/courses.py` (nouvelle constante `SCRIPT_REGLES_COURSES` juste après `SCRIPT_RELECTURE` ;
  `normaliser` et `cleCatalogue` y déménagent depuis `SCRIPT_COURSES:292-299`) ; `courses_en_html` l'insère
  (`<script>{SCRIPT_REGLES_COURSES}</script>`) avant `SCRIPT_COURSES`
- Test : `voyage/test_courses.py` (après les tests de relecture)

**Interfaces :**
- Produit (fonctions globales JS) :
  - `normaliser(nom) -> string`, `cleCatalogue(nom) -> string` (inchangées) ;
  - `pastille(article, italien: Set) -> 'Italien' | 'Asie' | null` ;
  - `aLaMaison(placard, articles) -> [{cle, nom, rayon, placard: objet|null, article: objet|null}]`, trié par nom ;
  - `correspond(nom, recherche) -> bool`.

- [ ] **Step 1 : tests rouges.**

```python
def _node_regles(code):
    """Exécute SCRIPT_REGLES_COURSES puis code (qui fait console.log) ; rend la sortie JSON."""
    import json, shutil, subprocess
    if not shutil.which("node"):
        pytest.skip("node absent")
    from courses import SCRIPT_REGLES_COURSES
    sortie = subprocess.run(["node", "-e", SCRIPT_REGLES_COURSES + "\n" + code], capture_output=True, text=True, check=True).stdout
    return json.loads(sortie)


def test_js_a_la_maison():
    import json
    placard = [{"cle": "parmesan", "nom": "parmesan", "en_stock": True, "bientot": False, "rayon": "frais"},
               {"cle": "riz basmati", "nom": "riz basmati", "en_stock": True, "bientot": True, "rayon": "epicerie"},
               {"cle": "thon", "nom": "thon", "en_stock": False, "bientot": False, "rayon": "epicerie"},
               {"cle": "oeufs", "nom": "œufs", "en_stock": True, "bientot": False, "rayon": "frais"},
               {"cle": "farine", "nom": "farine", "en_stock": True, "bientot": False, "rayon": "epicerie"}]
    articles = [{"id": "a1", "nom": "Œufs", "rayon": "frais", "recurrent": True, "actif": False, "pris": False},
                {"id": "a2", "nom": "lait", "rayon": "frais", "recurrent": True, "actif": False, "pris": False},
                {"id": "a3", "nom": "beurre", "rayon": "frais", "recurrent": True, "actif": True, "pris": False},
                {"id": "a4", "nom": "farine", "rayon": "epicerie", "recurrent": False, "actif": True, "pris": False},
                {"id": "a5", "nom": "citrons", "rayon": "fruits-legumes", "recurrent": True, "actif": True, "pris": True}]
    r = _node_regles(f"console.log(JSON.stringify(aLaMaison({json.dumps(placard)}, {json.dumps(articles)})"
                     ".map(function (m) {{ return [m.nom, m.rayon, !!m.placard, m.article ? m.article.id : null]; }})));")
    # thon épuisé, farine sur la liste, beurre sur la liste, citrons dans le panier : absents ; œufs une seule fois
    assert r == [["lait", "frais", False, "a2"], ["œufs", "frais", True, "a1"],
                 ["parmesan", "frais", True, None], ["riz basmati", "epicerie", True, None]]


def test_js_correspond():
    r = _node_regles("console.log(JSON.stringify([correspond('parmesan', 'parm'), correspond(\"huile d'olive\", 'olive'),"
                     " correspond('Crème fraîche', 'creme'), correspond('parmesan', 'mesan'), correspond('thon', ''),"
                     " correspond('Œufs', 'oeu')]));")
    assert r == [True, True, True, False, True, True]


def test_js_pastille():
    r = _node_regles("const it = new Set(['pecorino'].map(cleCatalogue));"
                     "console.log(JSON.stringify([pastille({nom: 'pecorino', rayon: 'specialise'}, it),"
                     " pastille({nom: 'sauce soja', rayon: 'specialise'}, it), pastille({nom: 'lait', rayon: 'frais'}, it)]));")
    assert r == ["Italien", "Asie", None]
```

(Ordre vérifié sous node : `localeCompare(..., 'fr')` range « œufs » comme « oeufs », entre lait et parmesan.)

- [ ] **Step 2 :** `.venv/bin/python3 -m pytest -q test_courses.py -k js_` → FAIL (`ImportError SCRIPT_REGLES_COURSES`).
- [ ] **Step 3 : implémentation** dans `courses.py`, après `SCRIPT_RELECTURE` :

```python
# Les règles de la page Courses, sans DOM : exécutées telles quelles par les tests (node)
SCRIPT_REGLES_COURSES = r"""
function normaliser(nom) {
    return nom.trim().toLowerCase().replace(/œ/g, 'oe').replace(/æ/g, 'ae')
        .normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/\s+/g, ' ');
}
// Même clé que catalogue.cle_catalogue : « tomate cerise » = « tomates cerises »
function cleCatalogue(nom) {
    return normaliser(nom).split(' ').map(function (m) { return m.length > 3 && /[sx]$/.test(m) ? m.slice(0, -1) : m; }).join(' ');
}
// Où l'acheter, en pastille : les épiceries spécialisées se partagent entre l'italienne et l'asiatique
function pastille(a, italien) {
    if (a.rayon !== 'specialise') return null;
    return italien.has(cleCatalogue(a.nom)) ? 'Italien' : 'Asie';
}
// À la maison : le placard en stock (bientôt fini compris) et les habituels rangés, un seul par nom,
// sans ce qui est sur la liste à prendre
function aLaMaison(placard, articles) {
    const surLaListe = new Set(articles.filter(function (a) { return a.actif && !a.pris; })
        .map(function (a) { return normaliser(a.nom); }));
    const vus = {};
    placard.forEach(function (p) {
        if (p.en_stock && !surLaListe.has(p.cle))
            vus[p.cle] = { cle: p.cle, nom: p.nom, rayon: p.rayon || 'autre', placard: p, article: null };
    });
    articles.forEach(function (a) {
        const cle = normaliser(a.nom);
        if (!a.recurrent || a.actif || surLaListe.has(cle)) return;
        if (vus[cle]) vus[cle].article = a;
        else vus[cle] = { cle: cle, nom: a.nom, rayon: a.rayon || 'autre', placard: null, article: a };
    });
    return Object.keys(vus).map(function (k) { return vus[k]; })
        .sort(function (x, y) { return x.nom.localeCompare(y.nom, 'fr'); });
}
// La recherche : le début d'un des mots du nom (« parm » -> parmesan, « olive » -> huile d'olive)
function correspond(nom, recherche) {
    const mots = function (s) { return normaliser(s).replace(/['’-]/g, ' '); };
    const r = mots(recherche).trim();
    return !r || (' ' + mots(nom)).indexOf(' ' + r) >= 0;
}
"""
```

Dans `SCRIPT_COURSES`, supprimer les définitions de `normaliser` et `cleCatalogue` (`:292-299`, elles viennent
désormais du script de règles). Dans `courses_en_html`, ajouter `<script>{SCRIPT_REGLES_COURSES}</script>` juste
avant `<script>{SCRIPT_COURSES}</script>`.

- [ ] **Step 4 :** suite complète verte (la page fonctionne encore à l'identique).
- [ ] **Step 5 : commit** `feat(courses): règles de « À la maison » et des pastilles, testées sous node`.

### Task 6 : liste unique par rayon, pastilles Italien / Asie

**Files :**
- Modify : `voyage/courses.py` : CSS `:193-200,203` ; `SCRIPT_COURSES` `:284-290` (états), `:311-323` (`magasin`,
  `DURABLES`, `estReassort`), `:422-470` (`ligne`, `parRayon`), `:472-531` (`afficher`) ; HTML `:661`
- Test : `voyage/test_courses.py:111-129`

**Interfaces :**
- Consomme : `pastille`, `normaliser`, `cleCatalogue` (Task 5).
- Produit : `parRayon(liste_, conteneur)` (sections `section.rayon` seulement) ; `afficher()` appelle
  `afficherMaison()` (défini en Task 7 ; dans cette task, il continue d'appeler `afficherPlacard()`).

- [ ] **Step 1 : tests rouges.** Remplacer `test_page_courses_v2` par :

```python
def test_page_courses_liste_unique():
    html = courses_en_html()
    from courses import SCRIPT_COURSES
    assert 'id="magasins"' not in html and "courses:magasin" not in html             # plus d'onglets par magasin
    assert "Réassort" not in html and "estReassort" not in html and "Cette semaine" not in html
    assert "Dans le panier" in html and "Courses finies" in html and 'class="progression"' in html
    assert "pastille(a, ITALIEN)" in SCRIPT_COURSES and "span.pastille" in html
    assert "Toujours en avoir" in SCRIPT_COURSES and "Plus besoin d'en avoir" in SCRIPT_COURSES
    assert "'Plus habituel'" not in SCRIPT_COURSES
    assert '<script type="application/json" id="italien">' in html and '"pecorino"' in html
```

- [ ] **Step 2 :** `.venv/bin/python3 -m pytest -q test_courses.py` → FAIL.
- [ ] **Step 3 : implémentation.**
  - Supprimer : CSS `nav#magasins*` et `h2.semaine` ; `reassortOuvert` (garder `panierOuvert`), `MAGASINS`,
    `CLE_MAGASIN`, `magasinActif` et sa lecture `localStorage` ; `magasin()`, `DURABLES`, `estReassort` ;
    `<nav id="magasins" ...></nav>` du HTML.
  - CSS, ajouter :

```css
ul.articles .nom span.pastille { display: inline-block; margin-left: 8px; padding: 1px 8px; border-radius: 999px;
                                 font-size: 12px; font-weight: 700; vertical-align: 2px;
                                 background: var(--courses-doux); color: var(--courses); }
```

  - `ligne(a)` : après `const nom = el('button', 'nom', a.nom); nom.type = 'button';` ajouter
    `const ou = pastille(a, ITALIEN); if (ou) nom.append(el('span', 'pastille', ou));` (avant le `small` du prix).
    Bouton d'édition : `el('button', '', a.recurrent ? "Plus besoin d'en avoir" : 'Toujours en avoir')`.
    L'icône et son `aria-label`/`title` : `'toujours en avoir'` au lieu de `'habituel'`.
  - `parRayon` devient :

```js
    // Les articles à prendre par rayon, dans l'ordre du parcours du magasin
    function parRayon(liste_, conteneur) {
        RAYONS.forEach(function (r) {
            const du = liste_.filter(function (a) { return a.rayon === r[0]; }).sort(parNom);
            if (!du.length) return;
            const ul = el('ul', 'articles');
            du.forEach(function (a) { ligne(a).forEach(function (n) { ul.append(n); }); });
            const section = el('section', 'rayon'); section.dataset.rayon = r[0];
            section.append(el('h2', '', r[1]), ul); conteneur.append(section);
        });
    }
```

  - Début de `afficher()` jusqu'au repli du panier :

```js
    function afficher() {
        const actifs = articles.filter(function (a) { return a.actif; });
        const aPrendre = actifs.filter(function (a) { return !a.pris; });
        const panier = actifs.filter(function (a) { return a.pris; });
        resume.textContent = aPrendre.length ? aPrendre.length + ' à prendre' + (panier.length ? ' · ' + panier.length + ' dans le panier' : '')
                                             : (panier.length ? 'Tout est dans le panier' : 'Rien à prendre');
        const budget = document.getElementById('budget');
        const sansPrix = aPrendre.filter(function (a) { return !prixDe(a); }).length;
        budget.replaceChildren();
        if (actifs.length) {
            budget.append(el('strong', '', '≈ ' + euros(somme(aPrendre), true)), ' à prendre');
            if (panier.length) budget.append(' · ' + euros(somme(panier), true) + ' dans le panier');
            if (sansPrix) budget.append(' · ' + sansPrix + ' sans prix');
        }
        document.querySelector('div.progression div').style.width =
            (actifs.length ? Math.round(100 * panier.length / actifs.length) : 0) + '%';

        liste.replaceChildren();
        parRayon(aPrendre, liste);
        if (panier.length) {
            const d = repli('panier', 'Dans le panier', panier.length, panierOuvert, function (o) { panierOuvert = o; });
            const ul = el('ul', 'articles');
            panier.sort(parNom).forEach(function (a) { ligne(a).forEach(function (n) { ul.append(n); }); });
            d.append(ul);
            liste.append(d);
        }
        if (!actifs.length) liste.append(el('p', 'vide-courses', 'Rien à acheter. Ajoute un article, ou touche ce qui manque dans « À la maison ».'));
        viderPris.hidden = !panier.length;
        viderPris.textContent = 'Courses finies · ranger ' + panier.length + ' article' + (panier.length > 1 ? 's' : '');
```

    La suite de `afficher()` (habituels, `afficherPlacard()`) reste en l'état jusqu'à la Task 7.
    `details.repli h3` reste (inutilisé mais inoffensif) : le supprimer aussi.

- [ ] **Step 4 :** suite complète verte. `grep -n "magasin\|reassort\|semaine" voyage/courses.py` → plus rien côté
  page (hors `ITALIEN`).
- [ ] **Step 5 : commit** `feat(courses): une seule liste par rayon, pastilles Italien et Asie`.

### Task 7 : « À la maison » remplace Placard et Habituels

**Files :**
- Modify : `voyage/courses.py` : CSS `:231-248` ; `SCRIPT_COURSES` états `:285`, `charger` `:355`, `basculerPlacard`
  `:408-414`, `retirerPlacard` `:415-419`, `etatPlacard` `:420`, fin d'`afficher` `:534-545`, `afficherPlacard` /
  `editionPlacard` `:548-604`, handlers `:606-626` ; HTML `:671-686` et `:689-690` ; `courses_en_html` (`zones`,
  `zones_catalogue`, `options_zones`) ; docstring du module `:1-10`
- Modify : `voyage/valise.py:1648` → `VERSION_PAGE = 55`
- Test : `voyage/test_courses.py:103-109`

**Interfaces :**
- Consomme : `aLaMaison`, `correspond` (Task 5) ; `enregistrer`, `supprimer`, `ajouter`, `enregistrerPlacard`
  (existants) ; `rayon` des éléments du placard (Task 4).
- Produit : `afficherMaison()`, `manque(m)`, `editionMaison(m)`.

- [ ] **Step 1 : test rouge.** Remplacer `test_page_courses` par :

```python
def test_page_courses():
    html = courses_en_html()
    from courses import SCRIPT_COURSES
    assert "<title>Courses · Casa Binomerie</title>" in html
    assert 'data-hub="cucina" class="actif"' in html and 'data-cucina="courses" class="actif"' in html and "<h1>Courses</h1>" not in html
    assert '<form id="ajout-course"' in html and 'id="vider-pris"' in html
    assert "SCRIPT_FILE" not in html and "function envoyerOuGarder" in html     # la file hors ligne commune
    assert '"frais"' in html                                                   # les rayons pour le script
    # À la maison remplace Placard et Habituels
    assert 'id="zone-maison"' in html and "À la maison" in html and 'id="chercher-maison"' in html
    assert 'id="modifier-maison"' in html and "api/placard/" in html
    for parti in ('id="zone-placard"', 'id="zone-habituels"', '<form id="ajout-placard"', 'id="ranger"',
                  'id="zones"', 'id="zones-catalogue"', "bientôt fini"):
        assert parti not in html
    assert "function basculerPlacard" not in SCRIPT_COURSES and "aLaMaison(placard, articles)" in SCRIPT_COURSES
    assert "correspond(m.nom, recherche)" in SCRIPT_COURSES
```

- [ ] **Step 2 :** `.venv/bin/python3 -m pytest -q test_courses.py` → FAIL.
- [ ] **Step 3 : implémentation.**

HTML : remplacer les deux `<details class="annexe">` (habituels et placard) par :

```html
<details class="annexe" id="zone-maison">
<summary>À la maison · <span id="nb-maison">…</span></summary>
<p class="aide">Ce qu'on a toujours chez nous, rangé comme la liste. Il en manque ? Un appui : il part sur la liste. Acheté, il revient ici tout seul.</p>
<input type="search" id="chercher-maison" placeholder="Chercher (ex. parmesan)" aria-label="Chercher à la maison" autocomplete="off" enterkeyhint="search">
<div id="maison"></div>
<button type="button" id="modifier-maison">Modifier</button>
</details>
```

Supprimer `<script type="application/json" id="zones">` et `id="zones-catalogue"`, et dans `courses_en_html` les
variables `zones`, `zones_catalogue`, `options_zones` (garder l'import `CATALOGUE` pour les suggestions).

CSS : supprimer les règles `button.epuise`, `button.bientot` (et leurs `::after`), `section.zone-placard*`,
`form#ajout-placard*`, `button#ranger` ; ajouter :

```css
section.rayon-maison { border-top: 1px solid var(--ligne); margin-top: 12px; padding-top: 10px; }
section.rayon-maison h3 { font-size: 15px; font-weight: 800; margin: 0; }
div.puces-courses button.choisi { border-color: var(--courses); background: var(--courses-doux); font-weight: 700; }
input#chercher-maison { width: 100%; box-sizing: border-box; font-family: inherit; font-size: 16px; padding: 10px 14px;
                        margin-top: 10px; border-radius: 999px; border: 2px solid var(--ligne); background: var(--blanc);
                        color: var(--texte); }
div.edition-placard select, div.edition-placard button, button#modifier-maison { font-family: inherit; font-size: 14px;
    padding: 8px 12px; border-radius: 999px; border: 2px solid var(--ligne); background: var(--blanc); color: var(--texte); }
button#modifier-maison { margin-top: 12px; font-weight: 700; }
```

(`div.edition-placard` et `div.edition-placard strong` gardent leurs règles existantes.)

Script :
- états : `let ranger = false, placardOuvert = null;` → `let modifier = false, maisonOuverte = null, recherche = '';` ;
  supprimer `const ZONES = ...`.
- `charger` : `if (ouvert || placardOuvert || ...)` → `if (ouvert || maisonOuverte || ...)`.
- supprimer `basculerPlacard` et `etatPlacard` ; `retirerPlacard` : `placardOuvert = null;` → `maisonOuverte = null;`.
- fin d'`afficher()` : supprimer le bloc des habituels (`const habituels = ...` jusqu'à `nb-habituels`) et remplacer
  `afficherPlacard();` par `afficherMaison();`.
- remplacer `afficherPlacard`, `editionPlacard`, le handler `#ranger`, `ZONES_CATALOGUE` et les handlers
  `#ajout-placard` par :

```js
    // Un appui : il en manque. Le placard passe épuisé et l'article part sur la liste (ajouter remet aussi
    // l'habituel du même nom) ; un habituel seul revient sur la liste.
    function manque(m) {
        if (m.placard) {
            enregistrerPlacard(Object.assign({}, m.placard, { en_stock: false, bientot: false }));
            ajouter(m.nom, 'placard');
        } else enregistrer(Object.assign({}, m.article, { actif: true, pris: false }));
    }
    function afficherMaison() {
        const zone = document.getElementById('maison');
        zone.replaceChildren();
        const tous = aLaMaison(placard, articles);
        const vus = tous.filter(function (m) { return correspond(m.nom, recherche); });
        RAYONS.forEach(function (r) {
            const du = vus.filter(function (m) { return m.rayon === r[0]; });
            if (!du.length) return;
            const section = el('section', 'rayon-maison'); section.dataset.rayon = r[0];
            const puces = el('div', 'puces-courses');
            du.forEach(function (m) {
                const b = el('button', modifier && maisonOuverte === m.cle ? 'choisi' : '', m.nom); b.type = 'button';
                if (!modifier) b.setAttribute('aria-label', m.nom + ', il en manque');
                b.addEventListener('click', function () {
                    if (modifier) { maisonOuverte = maisonOuverte === m.cle ? null : m.cle; afficherMaison(); }
                    else manque(m);
                });
                puces.append(b);
            });
            section.append(el('h3', '', r[1]), puces);
            const choisi = modifier && du.find(function (m) { return m.cle === maisonOuverte; });
            if (choisi) section.append(editionMaison(choisi));
            zone.append(section);
        });
        if (!vus.length) zone.append(el('p', 'aide', tous.length ? "Rien à la maison qui s'appelle ainsi. Ajoute-le à la liste."
                                                                   : "Rien pour l'instant : sur la liste, marque un article « Toujours en avoir »."));
        document.getElementById('nb-maison').textContent = tous.length + ' article' + (tous.length > 1 ? 's' : '');
        document.getElementById('modifier-maison').textContent = modifier ? 'Terminé' : 'Modifier';
    }
    // Modifier : un habituel change de rayon ; le placard n'a qu'une zone en base, son rayon est deviné du nom
    function editionMaison(m) {
        const bloc = el('div', 'edition-placard');
        bloc.append(el('strong', '', m.nom));
        if (m.article && !m.placard) {
            const rayon = el('select'); rayon.setAttribute('aria-label', 'Rayon de ' + m.nom);
            RAYONS.forEach(function (r) { const o = el('option', '', r[1]); o.value = r[0]; o.selected = r[0] === m.article.rayon; rayon.append(o); });
            rayon.addEventListener('change', function () { maisonOuverte = null; enregistrer(Object.assign({}, m.article, { rayon: rayon.value })); });
            bloc.append(rayon);
        }
        const retirer = el('button', '', 'Retirer'); retirer.type = 'button';
        retirer.addEventListener('click', function () {
            maisonOuverte = null;
            if (m.placard) retirerPlacard(m.placard);
            if (m.article) supprimer(m.article);
        });
        const fermer = el('button', '', 'Fermer'); fermer.type = 'button';
        fermer.addEventListener('click', function () { maisonOuverte = null; afficherMaison(); });
        bloc.append(retirer, fermer);
        return bloc;
    }

    document.getElementById('modifier-maison').addEventListener('click', function () {
        modifier = !modifier; maisonOuverte = null; afficherMaison();
    });
    document.getElementById('chercher-maison').addEventListener('input', function () {
        recherche = this.value; afficherMaison();                       // le champ n'est pas redessiné : il garde le focus
    });
```

Docstring du module (`courses.py:1-10`) : remplacer la description du placard par « À la maison » (placard en stock +
habituels rangés, par rayon ; un appui = il en manque ; la zone reste en base pour À finir).
`valise.py:1648` : `VERSION_PAGE = 55`.

- [ ] **Step 4 :** suite complète verte ; `grep -n "placardOuvert\|ranger\b\|afficherPlacard\|ZONES" voyage/courses.py`
  → seulement `ZONES` côté Python (`deviner_zone`, `valider_placard`).
- [ ] **Step 5 : commit** `feat(courses): « À la maison » remplace Placard et Habituels (version 55)`.

### Task 8 : démo livraison B (gate Julien)

- [ ] Copie de prod dans `valise_test`, serveur local (comme Task 3).
- [ ] Parcours à vérifier dans Chrome (390 px) puis par Julien sur iPhone :
  1. la liste est unique, par rayon, les articles d'épicerie spécialisée portent Italien / Asie ;
  2. « À la maison » : chercher « parm » ne montre que le parmesan ; un appui l'envoie dans Frais sur la liste et le
     retire d'« À la maison » ;
  3. le cocher puis « Courses finies » : il revient dans « À la maison » ;
  4. Modifier : retirer un élément, changer le rayon d'un habituel ;
  5. hors ligne (mode avion) : un appui reste en file et passe au retour du réseau ;
  6. Dîners > Ce soir : un plat dont on vient d'envoyer l'ingrédient sur la liste n'est plus « Faisable tout de suite ».
- [ ] Sur le go de Julien : push, PR, merge, attendre Render (`sw.js` valise-v55), vérifier `/courses` en prod.
- [ ] Fin de session : `~/Claude/Work/perso/casa/STATUS.md` (Cucina, Courses v3, « bug » ravioli expliqué),
  `~/Claude/TASKS.md`.
