# Casa Dîners — onglet Recettes unique — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remplacer les onglets Carnet et À tester de la page Dîners par un seul onglet Recettes, avec badges « Nouvelle » et « N× ».

**Architecture:** Le serveur ajoute à chaque plat de `api/diners` son nombre de repas « fait maison » (`faits`, une requête dans `db.py`). Le script de la page (`diners.py`, chaîne `SCRIPT_DINERS`) remplace `vueCarnet`/`vueATester` par `vueRecettes`, trie avec une fonction `ordreRecettes` partagée avec la feuille de choix d'un repas. Le champ `statut` reste en base comme repère connue / nouvelle.

**Tech Stack:** Python 3, Flask, psycopg2, Postgres (`valise_test` pour les tests), JS vanilla inline, pytest.

## Global Constraints

- Spec : `docs/superpowers/specs/2026-11-11-casa-recettes-fusion-design.md`.
- Aucune migration, aucune colonne nouvelle ; `statut` garde ses valeurs `carnet` / `a-tester`.
- Onglets : `ce-soir` « Ce soir », `semaine` « Semaine », `recettes` « Recettes ».
- Ordre : faites (compte décroissant) → connues sans repas (A → Z) → nouvelles avec recette (A → Z) → nouvelles sans recette (A → Z).
- Libellés : « Nouvelle », « N× », « Nouvelles » (étiquette), « On l'a déjà faite », « Archiver », « Désarchiver », « recette à écrire ».
- Pas de `innerHTML`. Commandes lancées depuis `voyage/` avec `.venv/bin/python -m pytest`.
- Branche `feat/casa-recettes` ; pas de push / PR / merge sans OK de Julien après la démo locale.

---

### Task 1: Compte des repas faits dans `api/diners`

**Files:**
- Modify: `voyage/db.py` (après `lire_repas`, ~ligne 862)
- Modify: `voyage/serveur.py:27` (import) et `:139-169` (`lire_les_diners`)
- Test: `voyage/test_diners_db.py`

**Interfaces:**
- Produces: `db.compter_faits(conn) -> dict[str, int]` ({id de plat: nombre de repas `issue = 'fait'` qui le contiennent}, ids absents = 0) ; chaque plat de `GET /api/diners` porte `"faits": int`.

- [ ] **Step 1: Branche**

```bash
cd ~/Claude/Work/perso/python/julien-python-journey && git checkout -b feat/casa-recettes
```

- [ ] **Step 2: Tests qui échouent** — ajouter à la fin de `voyage/test_diners_db.py` :

```python
def test_compter_faits(conn):
    from db import compter_faits
    enregistrer_repas(conn, {"jour": J - timedelta(days=2), "moment": "diner", "plats": ["plat-carbonara"], "issue": "fait"})
    enregistrer_repas(conn, {"jour": J - timedelta(days=1), "moment": "diner", "plats": ["plat-carbonara"], "issue": "fait"})
    enregistrer_repas(conn, {"jour": J, "moment": "diner", "plats": ["plat-carbonara"], "issue": None})      # pas fait
    assert compter_faits(conn) == {"plat-carbonara": 2}


def test_api_diners_faits(client, conn):
    enregistrer_repas(conn, {"jour": J - timedelta(days=1), "moment": "diner", "plats": ["plat-carbonara"], "issue": "fait"})
    plats = {p["id"]: p for p in client.get("/api/diners").get_json()["plats"]}
    assert plats["plat-carbonara"]["faits"] == 1
    assert all(p["faits"] == 0 for i, p in plats.items() if i != "plat-carbonara")
```

- [ ] **Step 3: Vérifier l'échec**

Run: `.venv/bin/python -m pytest test_diners_db.py -k "faits" -v`
Expected: FAIL (`ImportError: cannot import name 'compter_faits'`, puis `KeyError: 'faits'`).

- [ ] **Step 4: Implémentation** — dans `voyage/db.py`, juste après `lire_repas` :

```python
def compter_faits(conn):
    """{id de plat : nombre de repas « fait maison » qui le contiennent} — tout l'historique, pas la fenêtre."""
    with conn.cursor() as cur:
        cur.execute("""SELECT id, count(*) FROM repas, jsonb_array_elements_text(plats) AS id
                       WHERE issue = 'fait' GROUP BY id""")
        return dict(cur.fetchall())
```

(`repas.plats` est `JSONB` — `schema.sql:266`.)

Dans `voyage/serveur.py`, ajouter `compter_faits` à l'import `from db import (...)` ligne 27, puis dans `lire_les_diners` :

```python
            plats = lire_plats(conn)
            faits = compter_faits(conn)
```

et remplacer la ligne `"plats": [...]` par :

```python
            "plats": [{**p, "cout": cout_repas(p["ingredients"], p["recette"]), "fiche": decouper(p["recette"]),
                       "faits": faits.get(p["id"], 0)} for p in plats],
```

- [ ] **Step 5: Vérifier le succès**

Run: `.venv/bin/python -m pytest test_diners_db.py -v`
Expected: tout PASS.

- [ ] **Step 6: Commit**

```bash
git add voyage/db.py voyage/serveur.py voyage/test_diners_db.py
git commit -m "feat(casa): nombre de repas faits par plat dans api/diners"
```

---

### Task 2: Onglet Recettes, badges, ordre, feuille de choix

**Files:**
- Modify: `voyage/diners.py` (SCRIPT_DINERS : `ETIQUETTES` l.509, `aEtiquette` l.567, `lignePlat` l.636, `vueCarnet`/`vueATester` l.823-876, `ouvrirChoix` l.878-925, fiche l.1097, édition l.1171, `afficher`/`VUES` l.1186-1199 ; `diners_en_html` l.1218-1219, texte « Chargement du carnet… »)
- Modify: `voyage/valise.py:1649` (`VERSION_PAGE = 48`)
- Test: `voyage/test_diners.py` (`test_page_diners`, nouveau `test_version_page_recettes`)

**Interfaces:**
- Consumes: `p.faits` (Task 1).
- Produces: fonctions JS `ordreRecettes(a, b)` et `vueRecettes(zone)` ; vue `'recettes'`.

- [ ] **Step 1: Tests qui échouent** — dans `voyage/test_diners.py`, `test_page_diners`, remplacer la boucle des vues :

```python
    for vue in ("ce-soir", "semaine", "recettes"):
        assert f'data-vue="{vue}"' in html
    assert 'data-vue="carnet"' not in html and 'data-vue="a-tester"' not in html
    assert "function vueRecettes" in html and "function ordreRecettes" in html
    assert "function vueCarnet" not in html and "function vueATester" not in html
    assert "'nouvelles'" in html and "'Nouvelles'" in html and "'Nouvelle'" in html and "'×'" in html
    assert "On l\\\\'a déjà faite" in html and "'Archiver'" in html and "'Désarchiver'" in html
    assert "au carnet" not in html and "Retirer du carnet" not in html
    assert "'recette à écrire'" in html
    assert "carnet: 'recettes', 'a-tester': 'recettes'" in html                       # anciens liens
```

et ajouter :

```python
def test_version_page_recettes():
    from valise import VERSION_PAGE
    assert VERSION_PAGE >= 48
```

- [ ] **Step 2: Vérifier l'échec**

Run: `.venv/bin/python -m pytest test_diners.py -k "page_diners or version_page_recettes" -v`
Expected: FAIL sur `data-vue="recettes"` et `VERSION_PAGE >= 48`.

- [ ] **Step 3: Étiquette Nouvelles** — `ETIQUETTES` (l.509) devient :

```js
    const ETIQUETTES = [['tout', 'Tout'], ['nouvelles', 'Nouvelles'], ['rapide', 'Rapide'], ['nous', 'Nous deux'], ['julien', 'Julien'],
                        ['laetitia', 'Laetitia'], ['air-fryer', 'Air fryer'], ['poisson', 'Poisson'], ['legumes', 'Légumes'], ['brunch', 'Brunch']];
```

Dans `aEtiquette`, après `if (e === 'tout') return true;` :

```js
        if (e === 'nouvelles') return p.statut === 'a-tester';
```

L'objet `etiquette` (l.506) : `const etiquette = { recettes: 'tout', choix: 'nous' };`

- [ ] **Step 4: Ordre et badges** — juste avant `function lignePlat`, ajouter :

```js
    // Recettes : les plus faites, puis les connues (A → Z), puis les nouvelles, recette écrite d'abord
    function rangRecette(p) { return p.statut === 'a-tester' ? (p.recette ? 2 : 3) : (p.faits ? 0 : 1); }
    function ordreRecettes(a, b) {
        return rangRecette(a) - rangRecette(b) || (b.faits || 0) - (a.faits || 0) || a.nom.localeCompare(b.nom, 'fr');
    }
```

Dans `lignePlat`, après la ligne du badge `secours` :

```js
        if (p.statut === 'a-tester') nom.append(el('span', 'badge', 'Nouvelle'));
        else if (p.faits) nom.append(el('span', 'badge', p.faits + '×'));
```

Le test cherche la chaîne `'×'` : garder exactement `p.faits + '×'`.

- [ ] **Step 5: `vueRecettes`** — remplacer `vueCarnet` et `vueATester` (l.823-876) par :

```js
    function vueRecettes(zone) {
        const r = el('input', 'recherche'); r.type = 'search'; r.placeholder = 'Chercher un plat ou un ingrédient';
        r.value = recherche; r.setAttribute('aria-label', 'Chercher');
        const f = el('div', 'filtres');
        [['tout', 'Tout']].concat(GENRES).forEach(function (g) {
            f.append(bouton(g[1], filtre === g[0] ? 'actif' : '', function () { filtre = g[0]; afficher(); }));
        });
        const ul = el('ul', 'plats');
        const toutes = d.plats.filter(function (p) { return !p.archive; });
        const zoneEtiquettes = el('div');
        function remplir() {
            ul.replaceChildren();
            const q = normaliser(recherche);
            const parGenre = toutes.filter(function (p) { return (filtre === 'tout' || p.genre === filtre) && correspond(p, q); });
            zoneEtiquettes.replaceChildren(barreEtiquettes('recettes', parGenre, remplir));
            parGenre.filter(function (p) { return aEtiquette(p, etiquette.recettes); })
                .sort(ordreRecettes)
                .forEach(function (p) { ul.append(lignePlat(p, p.statut === 'a-tester' && !p.recette ? 'recette à écrire' : undefined)); });
            if (!ul.children.length) ul.append(el('li', 'meta', 'Aucune recette ne correspond.'));
        }
        r.addEventListener('input', function () { recherche = r.value; remplir(); });
        remplir();
        const e = el('div', 'encart'); e.append(ul);
        zone.append(r, f, zoneEtiquettes, bouton('+ Nouvelle recette', 'plein', function () { ouvrirEdition(null); }), e);
    }
```

- [ ] **Step 6: Feuille de choix d'un repas** — dans `ouvrirChoix`, remplacer le bloc `[['carnet', 'Carnet'], ['a-tester', 'À tester']].forEach(function (g) { ... });` (de la ligne `[['carnet'…` jusqu'à sa fermeture `});`) par une seule liste :

```js
            const ul = el('ul', 'plats');
            affiches.slice().sort(ordreRecettes).forEach(function (p) {
                const li = lignePlat(p);
                li.querySelector('button.ouvrir').replaceWith(li.querySelector('button.ouvrir').cloneNode(true));
                if (plein || dansRepas.indexOf(p.id) >= 0) {
                    li.querySelector('button.ouvrir').disabled = true;
                    if (dansRepas.indexOf(p.id) >= 0) li.querySelector('.nom').append(el('span', 'badge', 'au menu'));
                } else {
                    li.querySelector('button.ouvrir').addEventListener('click', function () { ajouterPlat(iso, moment, p.id); fermer(); });
                }
                ul.append(li);
            });
            if (ul.children.length) listes.append(ul);
```

Lire d'abord les lignes qui suivent `if (!ul.children.length) return;` dans l'ancien bloc (titre de groupe `h3` ajouté à `listes`) : elles disparaissent avec lui ; garder tel quel tout message « aucun résultat » qui suit le bloc. Mettre à jour le commentaire au-dessus de `ouvrirChoix` : « … la même recherche et les mêmes étiquettes, dans l'ordre des Recettes ».

- [ ] **Step 7: Boutons de la fiche et de l'édition**

l.1097-1098 :

```js
        if (p.statut === 'a-tester') act.append(bouton('On l\\'a déjà faite', 'petit', function () {
            enregistrerPlat(Object.assign({}, p, { statut: 'carnet' })); fermer(); }));
```

l.1171 :

```js
        if (id) act.append(bouton(p.archive ? 'Désarchiver' : 'Archiver', 'petit', function () {
```

Le test cherche `'Archiver'` et `'Désarchiver'` entre apostrophes : c'est le cas avec ce code.

- [ ] **Step 8: Vues et anciens liens** — remplacer l.1190 et l.1195-1199 :

```js
        ({ 'ce-soir': vueCeSoir, 'semaine': vueSemaine, 'recettes': vueRecettes })[vue](zone);
```

```js
    const VUES = ['ce-soir', 'semaine', 'recettes'];
    const ANCIENNES = { carnet: 'recettes', 'a-tester': 'recettes' };           // liens et favoris d'avant la fusion
    function vueDuLien() { const h = location.hash.slice(1); return ANCIENNES[h] || (VUES.indexOf(h) >= 0 ? h : null); }
    if (vueDuLien()) vue = vueDuLien();
    window.addEventListener('hashchange', function () { if (vueDuLien()) { vue = vueDuLien(); afficher(); } });
```

(Vérifié : aucune autre affectation de `vue` vers `carnet` / `a-tester`, et la vue n'est pas mémorisée dans `localStorage`.)

- [ ] **Step 9: Coquille HTML** — dans `diners_en_html` :

```python
                   for v, t in [("ce-soir", "Ce soir"), ("semaine", "Semaine"), ("recettes", "Recettes")])
```

et `Chargement du carnet…` → `Chargement des recettes…`. Mettre à jour la docstring du module (l.1-4) : « plats : les recettes ; `statut` 'carnet' = connue, 'a-tester' = nouvelle (badge), passe à 'carnet' quand un repas où on l'a prévue est marqué « fait maison » ».

- [ ] **Step 10: Version de page** — `voyage/valise.py:1649` : `VERSION_PAGE = 48`.

- [ ] **Step 11: Vérifier le succès**

Run: `.venv/bin/python -m pytest test_diners.py test_diners_db.py test_serveur.py test_hub.py -q`
Expected: tout PASS. Puis la suite complète : `.venv/bin/python -m pytest -q` → PASS (corriger tout test qui cherchait `data-vue="carnet"`).

- [ ] **Step 12: Commit**

```bash
git add voyage/diners.py voyage/valise.py voyage/test_diners.py
git commit -m "feat(casa): un seul onglet Recettes (badges Nouvelle / N×), fin de Carnet et À tester"
```

---

### Task 3: Démo locale sur copie de prod

**Files:** aucun dans le repo (script du scratchpad `copie_demo.py` déjà existant, ou copie directe).

- [ ] **Step 1: Copie de prod vers `valise_copie`** — relancer la copie en lecture seule de Neon (tables plats, courses, placard, repas, reprises, achats, a_finir, cave) sans appliquer de plan.

- [ ] **Step 2: Serveur de démo**

```bash
cd voyage && .venv/bin/python -c "from serveur import creer_app; creer_app('valise_copie', secret='').run(host='0.0.0.0', port=8001)"
```

- [ ] **Step 3: Vérifs à faire faire à Julien (Mac + iPhone en wifi, `http://<ip>:8001/diners#recettes`)**
  - 3 onglets ; Recettes affiche ~155 recettes, plats les plus faits en tête avec « N× ».
  - Étiquette Nouvelles + genre Plats : seulement des nouvelles.
  - Recherche « ragù » : Tagliatelle al ragù avec badge Nouvelle.
  - `#carnet` ouvre Recettes.
  - Semaine → + plat : une seule liste, même ordre.
  - Fiche d'une nouvelle : « On l'a déjà faite » ; Modifier : « Archiver ».

- [ ] **Step 4: Arrêter le serveur après OK** ; push / PR / merge seulement sur demande explicite de Julien.

---

## Ajout du 11/11/2026 — badges en icônes, thème Auto / Clair / Sombre

Spec : section « Ajout du 11/11/2026 » de `docs/superpowers/specs/2026-11-11-casa-recettes-fusion-design.md`.
Contraintes : pas de `innerHTML` ; chaque icône garde son mot en `aria-label` et `title` ; `localStorage` toujours dans
un `try` ; `VERSION_PAGE` reste 48 (la branche n'est pas déployée).

### Task 4: Badges en icônes

**Files:**
- Modify: `voyage/diners.py` (SCRIPT_DINERS : `lignePlat` et juste avant ; `vueRecettes` ; CSS `STYLE_DINERS` près de `span.badge`)
- Test: `voyage/test_diners.py` (`test_page_diners`)

**Interfaces:**
- Consumes: `p.faits`, `p.statut`, `p.pour`, `d.secours.faisables`, `d.a_finir` (existants).
- Produces: fonctions JS `icone(signe, mot, classe)` et `points(n)`.

- [ ] **Step 1: Tests qui échouent** — dans `test_page_diners`, remplacer l'assertion `"'nouvelles'" in html and "'Nouvelles'" in html and "'Nouvelle'" in html and "'×'" in html` par :

```python
    assert "'nouvelles'" in html and "'Nouvelles'" in html
    assert "function icone" in html and "function points" in html and "aria-label" in html
    for signe in ("'✦'", "'⚡'", "'⏳'", "'Ⓙ'", "'Ⓛ'", "'●'", "'○'"):
        assert signe in html, signe
    assert "faite souvent" in html and "'faisable ce soir'" in html and "'finit un produit'" in html
    assert "el('span', 'badge', 'secours')" not in html and "badge julien" not in html
```

et retirer l'ancienne assertion `"badge julien" in html and "pour: pour.value" in html` au profit de `assert "pour: pour.value" in html`.

- [ ] **Step 2: Vérifier l'échec** — `cd voyage && .venv/bin/python -m pytest test_diners.py -k page_diners -q` → FAIL sur `function icone`.

- [ ] **Step 3: Implémentation JS** — juste avant `function lignePlat` :

```js
    // Les repères d'une recette en icônes ; le mot reste pour le lecteur d'écran et au survol
    function icone(signe, mot, classe) {
        const s = el('span', 'repere' + (classe ? ' ' + classe : ''), signe);
        s.setAttribute('aria-label', mot); s.title = mot;
        return s;
    }
    function points(n) { const k = n >= 5 ? 4 : n >= 3 ? 3 : n; return '●'.repeat(k) + '○'.repeat(4 - k); }
```

Dans `lignePlat`, remplacer les 6 lignes de badges (`secours`, `à finir`, `Nouvelle`, `p.faits + '×'`, `Julien`, `Laetitia`) par :

```js
        if (p.statut === 'a-tester') nom.append(icone('✦', 'nouvelle', 'nouvelle'));
        else if (p.faits) nom.append(icone(points(p.faits), 'faite ' + p.faits + ' fois', 'points'));
        if (d.secours.faisables.indexOf(p.id) >= 0) nom.append(icone('⚡', 'faisable ce soir'));
        if ((d.a_finir || []).indexOf(p.id) >= 0) nom.append(icone('⏳', 'finit un produit'));
        if (p.pour === 'julien') nom.append(icone('Ⓙ', 'pour Julien', 'qui'));
        if (p.pour === 'laetitia') nom.append(icone('Ⓛ', 'pour Laetitia', 'qui'));
```

Les tests cherchent `'●'` et `'○'` entre apostrophes : c'est le cas dans `points`.

Dans `vueRecettes`, remplacer `const e = el('div', 'encart'); e.append(ul);` par :

```js
        const e = el('div', 'encart');
        e.append(ul, el('p', 'legende-reperes', '✦ nouvelle · ●●● faite souvent · ⚡ faisable ce soir · ⏳ finit un produit · Ⓙ Ⓛ pour Julien / Laetitia'));
```

- [ ] **Step 4: CSS** — dans le style des Dîners, supprimer la ligne `span.badge.julien { … }` et ajouter après `span.badge { … }` :

```css
span.repere { margin-left: 6px; font-size: 14px; line-height: 1; white-space: nowrap; }
span.repere.nouvelle { color: #d4a017; font-size: 16px; }
span.repere.points { color: var(--diners); font-size: 10px; letter-spacing: 1px; vertical-align: 2px; }
span.repere.qui { color: var(--doux); font-size: 16px; }
p.legende-reperes { font-size: 12px; color: var(--doux); margin: 10px 4px 0; line-height: 1.5; }
```

`span.badge` reste (badge « au menu » de la feuille de choix).

- [ ] **Step 5: Vérifier** — `.venv/bin/python -m pytest test_diners.py -q` → PASS ; puis la suite complète `.venv/bin/python -m pytest -q` → PASS ; puis contrôle de syntaxe du JS généré :

```bash
.venv/bin/python -c "
import re; from diners import diners_en_html
open('/tmp/diners-check.js','w').write(re.findall(r'<script>(.*?)</script>', diners_en_html(), re.S)[-1])" && node --check /tmp/diners-check.js && echo JS_OK
```

- [ ] **Step 6: Commit**

```bash
git add voyage/diners.py voyage/test_diners.py
git commit -m "feat(casa): repères des recettes en icônes (✦, points, ⚡, ⏳, Ⓙ Ⓛ) avec légende"
```

---

### Task 5: Thème Auto / Clair / Sombre

**Files:**
- Modify: `voyage/design.py` (fonction `sombre`, les 5 blocs `@media (prefers-color-scheme: dark)` l.64, 102, 240, 341, 385 ; `nav_hub` ; `STYLE_NAV_HUB`)
- Modify: `voyage/valise.py` (2 blocs : `HTML_STYLE` l.54, style de carte l.2500)
- Modify: `voyage/pwa.py` (`TETE_PWA`)
- Test: `voyage/test_design.py`, `voyage/test_pwa.py`

**Interfaces:**
- Produces: `design.sombre(css: str) -> str` ; `design.SCRIPT_THEME` (str, script du bouton) ; `pwa.TETE_THEME` (str, script de tête).

- [ ] **Step 1: Tests qui échouent** — ajouter à `voyage/test_design.py` :

```python
def test_sombre_double_chaque_regle():
    from design import sombre
    css = sombre(":root { --a: 1; } div.x, p { color: red; }")
    assert css.startswith("@media (prefers-color-scheme: dark) {")
    assert ':root:not([data-theme="light"]) { --a: 1; }' in css
    assert ':root:not([data-theme="light"]) div.x, :root:not([data-theme="light"]) p { color: red; }' in css
    assert ':root[data-theme="dark"] { --a: 1; }' in css
    assert ':root[data-theme="dark"] div.x, :root[data-theme="dark"] p { color: red; }' in css


def test_plus_aucun_mode_sombre_qui_ignore_le_choix():
    import design, valise
    styles = [v for k, v in vars(design).items() if k.startswith("STYLE_") and isinstance(v, str)]
    styles += [valise.HTML_STYLE] + [v for k, v in vars(valise).items() if k.endswith("_STYLE") and isinstance(v, str)]
    for s in styles:
        assert s.count("@media (prefers-color-scheme: dark)") == s.count('@media (prefers-color-scheme: dark) { :root:not([data-theme="light"])')


def test_bouton_theme_dans_la_navigation():
    from design import nav_hub, STYLE_NAV_HUB
    html = nav_hub("diners")
    assert '<button type="button" class="theme"' in html and "casa-theme" in html
    assert "nav.hub button.theme" in STYLE_NAV_HUB
```

et à `voyage/test_pwa.py` :

```python
def test_theme_applique_dans_la_tete():
    from pwa import TETE_PWA
    assert "casa-theme" in TETE_PWA and "dataset.theme" in TETE_PWA and "try" in TETE_PWA
```

- [ ] **Step 2: Vérifier l'échec** — `cd voyage && .venv/bin/python -m pytest test_design.py test_pwa.py -q` → FAIL (`cannot import name 'sombre'`).

- [ ] **Step 3: `sombre`** — dans `voyage/design.py`, après les imports (ajouter `import re` s'il manque) :

```python
_AUTO = ':root:not([data-theme="light"])'      # l'appareil est en sombre et on n'a pas choisi Clair
_FORCE = ':root[data-theme="dark"]'             # on a choisi Sombre


def sombre(css):
    """Les règles du mode sombre, écrites deux fois : quand l'appareil est en sombre (sauf choix Clair) et quand on a
    choisi Sombre (bouton du thème). `css` : des règles simples « sélecteurs { déclarations } », sans @media imbriqué."""
    def prefixer(prefixe, selecteurs):
        return ", ".join(s.replace(":root", prefixe, 1) if s.startswith(":root") else f"{prefixe} {s}"
                         for s in (x.strip() for x in selecteurs.split(",")))
    regles = re.findall(r"([^{}]+)\{([^{}]*)\}", re.sub(r"/\*.*?\*/", "", css, flags=re.S))
    def ecrire(prefixe):
        return " ".join(f"{prefixer(prefixe, sel)} {{{corps}}}" for sel, corps in regles)
    return f"@media (prefers-color-scheme: dark) {{ {ecrire(_AUTO)} }}\n{ecrire(_FORCE)}\n"
```

Vérifier que le résultat du test `{ --a: 1; }` sort bien avec une espace avant et après : `corps` capturé vaut ` --a: 1; ` (espaces compris), donc `{{{corps}}}` donne `{ --a: 1; }`. Si le test échoue sur les espaces, normaliser `corps` en `" " + corps.strip() + " "`.

- [ ] **Step 4: Les 7 blocs** — chaque bloc `@media (prefers-color-scheme: dark) { … }` d'une chaîne de style devient une concaténation. Exemple pour `STYLE_NAV_HUB` (l.64-65) :

```python
STYLE_NAV_HUB = """
:root { --cave: #9b2c4f; ... --diners-doux: #ffede3; }
""" + sombre(""":root { --cave: #f08aa8; --cave-doux: #3d1824; --courses: #4cc3d1; --courses-doux: #10343a;
                --diners: #ff8f5a; --diners-doux: #3b1d0f; }""") + """
nav.hub { ... }
...
"""
```

Faire de même pour design.py l.102, 240, 341, 385 et valise.py l.54 (`HTML_STYLE`) et l.2500 (carte) : le contenu entre les accolades du `@media` passe tel quel dans `sombre("""…""")`. Si une de ces chaînes est une f-string, sortir le bloc de la f-string de la même façon (concaténation). `sombre` doit être défini avant le premier style qui l'utilise ; dans `valise.py`, l'importer depuis `design` (ligne d'import l.39).

- [ ] **Step 5: Bouton** — dans `design.py`, ajouter :

```python
SCRIPT_THEME = """<script>(function () {
    const b = document.querySelector('nav.hub button.theme'); if (!b) return;
    const ORDRE = ['auto', 'clair', 'sombre'], SIGNE = { auto: '◐', clair: '☀', sombre: '☾' },
          MOT = { auto: 'automatique', clair: 'clair', sombre: 'sombre' };
    let courant = 'auto';
    try { courant = localStorage.getItem('casa-theme') || 'auto'; } catch (e) {}
    function appliquer() {
        const h = document.documentElement;
        if (courant === 'auto') { delete h.dataset.theme; h.style.colorScheme = ''; }
        else { h.dataset.theme = courant === 'clair' ? 'light' : 'dark'; h.style.colorScheme = h.dataset.theme; }
        b.textContent = SIGNE[courant]; b.setAttribute('aria-label', 'Thème ' + MOT[courant] + ', appuyer pour changer');
    }
    b.addEventListener('click', function () {
        courant = ORDRE[(ORDRE.indexOf(courant) + 1) % ORDRE.length];
        try { if (courant === 'auto') localStorage.removeItem('casa-theme'); else localStorage.setItem('casa-theme', courant); } catch (e) {}
        appliquer();
    });
    appliquer();
})();</script>"""
```

et `nav_hub` renvoie :

```python
    return f'<nav class="hub">{liens}<button type="button" class="theme" aria-label="Thème">◐</button></nav>{SCRIPT_THEME}'
```

Dans `STYLE_NAV_HUB`, ajouter avant le bloc `@media (min-width: 900px)` :

```css
nav.hub button.theme { position: fixed; top: calc(10px + env(safe-area-inset-top)); right: 12px; z-index: 21;
                       width: 44px; height: 44px; border-radius: 999px; border: 1px solid var(--ligne);
                       background: var(--carte); color: var(--texte); font-size: 20px; line-height: 1; }
```

et dans ce bloc `@media (min-width: 900px)` :

```css
    nav.hub button.theme { position: static; margin-top: auto; align-self: flex-start; }
```

- [ ] **Step 6: Tête de page** — dans `voyage/pwa.py`, avant `TETE_PWA` :

```python
# Le thème choisi (bouton de la navigation), appliqué avant l'affichage : pas d'éclair de l'autre couleur
TETE_THEME = """<script>(function () { try {
    const t = localStorage.getItem('casa-theme');
    if (t === 'clair' || t === 'sombre') {
        document.documentElement.dataset.theme = t === 'clair' ? 'light' : 'dark';
        document.documentElement.style.colorScheme = document.documentElement.dataset.theme;
    }
} catch (e) {} })();</script>"""
```

et ajouter `{TETE_THEME}` en première ligne de la f-string `TETE_PWA`.

- [ ] **Step 7: Vérifier** — `.venv/bin/python -m pytest test_design.py test_pwa.py -q` → PASS ; suite complète `.venv/bin/python -m pytest -q` → PASS (corriger un test qui comparait un style ou `nav_hub` à une chaîne exacte, en gardant son intention) ; `node --check` du script de la page Dîners comme à la Task 4, plus celui de `SCRIPT_THEME` :

```bash
.venv/bin/python -c "
from design import SCRIPT_THEME; open('/tmp/theme-check.js','w').write(SCRIPT_THEME[8:-9])" && node --check /tmp/theme-check.js && echo THEME_OK
```

- [ ] **Step 8: Commit**

```bash
git add voyage/design.py voyage/valise.py voyage/pwa.py voyage/test_design.py voyage/test_pwa.py
git commit -m "feat(casa): thème Auto / Clair / Sombre au choix, gardé par appareil"
```

### Task 6: Démo — reprendre la Task 3 avec, en plus :
- les icônes et la légende ; survol d'une icône sur Mac = son mot ;
- le bouton ◐ en haut à droite sur iPhone (ne cache rien d'important), en bas de la colonne sur Mac ; Clair puis Sombre puis Auto ; rechargement = choix gardé, sans éclair ; Courses, Cave, Budget, Vadrouille suivent ;
- iPhone de Laetitia en Clair pendant que celui de Julien reste en Auto.
