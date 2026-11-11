# Casa — barre Popote — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Barre du bas à 4 entrées (Aujourd'hui · Popote · Budget · Vadrouille) et onglets Dîners · Courses · Cave en haut des trois pages de Popote.

**Architecture:** `design.HUB` passe à 4 entrées ; `nav_hub(actif)` traduit les pages `diners` / `courses` / `cave` en entrée active `popote`. Une nouvelle fonction `design.onglets_popote(actif)` rend la barre d'onglets, insérée à la place du `<h1>` dans `diners.py`, `courses.py`, `cave.py`. Pas de changement de route.

**Tech Stack:** Python 3, Flask (HTML en chaînes f-string), CSS inline, pytest.

## Global Constraints

- Spec : `docs/superpowers/specs/2026-11-11-casa-barre-popote-design.md`.
- Barre du bas : **Aujourd'hui · Popote · Budget · Vadrouille** ; Popote → `diners`, icône et couleur de Dîners (couverts, `--diners`).
- Pages `diners`, `courses`, `cave` : Popote active ; onglets **Dîners · Courses · Cave** (liens `diners`, `courses`, `cave`), page active soulignée de sa couleur (`--diners`, `--courses`, `--cave`) avec `aria-current="page"` ; plus de `<h1>` de titre sur ces trois pages.
- Adresses et routes inchangées. Pas d'emoji. Pas de `innerHTML`.
- Commandes depuis `voyage/` : `.venv/bin/python -m pytest`. Branche `feat/casa-popote`. Pas de push / PR sans OK de Julien après la démo.

---

### Task 1: Barre Popote et onglets

**Files:**
- Modify: `voyage/design.py` (`HUB` l.53-60, `ICONES_HUB` l.61+, `nav_hub` l.108-119, `STYLE_NAV_HUB` : règles `nav.hub a[data-hub=…]` l.133-138 et règle `@media (max-width: 899px)` l.148)
- Modify: `voyage/diners.py:1240`, `voyage/courses.py:641`, `voyage/cave.py:335` (le `<h1>`) et leurs imports `from design import …`
- Test: `voyage/test_casa.py`, `voyage/test_diners.py:136`, `voyage/test_courses.py:114`, `voyage/test_cave.py:108`

**Interfaces:**
- Produces: `design.onglets_popote(actif: str) -> str` (`actif` ∈ `"diners"`, `"courses"`, `"cave"`) ; `design.POPOTE = ("diners", "courses", "cave")`.

- [ ] **Step 1: Branche**

```bash
cd ~/Claude/Work/perso/python/julien-python-journey && git checkout main && git pull && git checkout -b feat/casa-popote
```

- [ ] **Step 2: Tests qui échouent** — ajouter à `voyage/test_casa.py` :

```python
def test_barre_du_bas_a_quatre_entrees():
    from design import nav_hub
    nav = nav_hub("aujourdhui")
    assert [x.split('"')[0] for x in nav.split('data-hub="')[1:]] == ["aujourdhui", "popote", "budget", "vadrouille"]
    assert '<a href="diners" data-hub="popote"' in nav
    for page in ("diners", "courses", "cave"):
        assert 'data-hub="popote" class="actif" aria-current="page"' in nav_hub(page)


def test_onglets_popote():
    from design import onglets_popote
    html = onglets_popote("courses")
    assert html.startswith('<nav class="popote" aria-label="Popote">')
    assert '<a href="diners" data-popote="diners">Dîners</a>' in html
    assert '<a href="courses" data-popote="courses" class="actif" aria-current="page">Courses</a>' in html
    assert '<a href="cave" data-popote="cave">Cave</a>' in html
```

Dans les tests de page, remplacer :
- `voyage/test_diners.py:136` : `'data-hub="diners" class="actif"'` → `'data-hub="popote" class="actif"' in html and 'data-popote="diners" class="actif"' in html and "<h1>Dîners</h1>" not in html`
- `voyage/test_courses.py:114` : `'data-hub="courses" class="actif"'` → `'data-hub="popote" class="actif"' in html and 'data-popote="courses" class="actif"' in html and "<h1>Courses</h1>" not in html`
- `voyage/test_cave.py:108` : `"<h1>Cave</h1>" in html and 'data-hub="cave" class="actif"' in html` → `"<h1>Cave</h1>" not in html and 'data-hub="popote" class="actif"' in html and 'data-popote="cave" class="actif"' in html`

(garder la forme `assert … in html` de chaque ligne d'origine ; adapter seulement les chaînes.)

- [ ] **Step 3: Vérifier l'échec** — `cd voyage && .venv/bin/python -m pytest test_casa.py test_diners.py test_courses.py test_cave.py -q` → FAIL (`cannot import name 'onglets_popote'`, entrées de barre).

- [ ] **Step 4: `HUB` et icône** — dans `voyage/design.py` :

```python
HUB = [
    ("aujourdhui", "Aujourd'hui", "./"),
    ("popote", "Popote", "diners"),                     # Dîners · Courses · Cave, onglets en haut des pages
    ("budget", "Budget", "budget"),
    ("vadrouille", "Vadrouille", "vadrouille"),          # court : tient dans la barre du bas sur iPhone
]
POPOTE = ("diners", "courses", "cave")
```

Dans `ICONES_HUB`, ajouter `"popote": <la même valeur que "diners">` (garder les clés existantes). Dans `STYLE_NAV_HUB`, remplacer les 3 lignes `nav.hub a[data-hub="diners"]`, `[data-hub="courses"]`, `[data-hub="cave"]` par :

```css
nav.hub a[data-hub="popote"] { --c: var(--diners); --c-doux: var(--diners-doux); }
```

- [ ] **Step 5: `nav_hub` et `onglets_popote`** — dans `nav_hub`, en première ligne du corps :

```python
    actif = "popote" if actif in POPOTE else actif
```

Ajouter après `nav_hub` :

```python
def onglets_popote(actif):
    """Les onglets de Popote en haut de Dîners, Courses et Cave (à la place du titre) ; la page active soulignée."""
    liens = "".join(
        f'<a href="{cle}" data-popote="{cle}"'
        + (' class="actif" aria-current="page">' if cle == actif else ">")
        + f"{libelle}</a>"
        for cle, libelle in (("diners", "Dîners"), ("courses", "Courses"), ("cave", "Cave")))
    return f'<nav class="popote" aria-label="Popote">{liens}</nav>'
```

Dans `STYLE_NAV_HUB`, ajouter (avant le bloc `@media (min-width: 900px)`) :

```css
nav.popote { display: flex; gap: 22px; margin: 0 0 18px; }
nav.popote a { font-size: 24px; font-weight: 800; color: var(--doux); text-decoration: none; padding: 2px 0 6px;
               border-bottom: 3px solid transparent; }
nav.popote a.actif { color: var(--texte); border-bottom-color: var(--c); }
nav.popote a[data-popote="diners"] { --c: var(--diners); }
nav.popote a[data-popote="courses"] { --c: var(--courses); }
nav.popote a[data-popote="cave"] { --c: var(--cave); }
```

et remplacer la règle l.148 par :

```css
@media (max-width: 899px) { body.hub-page h1, body.hub-page nav.popote { padding-right: 52px; } }
```

- [ ] **Step 6: Les trois pages** — dans `diners.py`, `courses.py`, `cave.py` : ajouter `onglets_popote` à l'import `from design import …`, et remplacer la ligne `<h1>Dîners</h1>` / `<h1>Courses</h1>` / `<h1>Cave</h1>` par `{onglets_popote("diners")}` / `{onglets_popote("courses")}` / `{onglets_popote("cave")}` (ces gabarits sont des f-strings : vérifier que la ligne est bien dans la f-string de la page).

- [ ] **Step 7: Vérifier**

Run: `.venv/bin/python -m pytest test_casa.py test_diners.py test_courses.py test_cave.py -q` → PASS, puis la suite complète `.venv/bin/python -m pytest -q` → PASS (baseline 889 + 2). Corriger tout autre test qui attendait `data-hub="diners"|"courses"|"cave"` dans la barre (`grep -rn 'data-hub="\(diners\|courses\|cave\)"' test_*.py`), en gardant son intention.

- [ ] **Step 8: Commit**

```bash
git add voyage/design.py voyage/diners.py voyage/courses.py voyage/cave.py voyage/test_casa.py voyage/test_diners.py voyage/test_courses.py voyage/test_cave.py
git commit -m "feat(casa): barre Popote (Dîners · Courses · Cave), 4 entrées en bas"
```

---

### Task 2: Démo locale

- [ ] Copie de prod → `valise_copie` (script `scratchpad/copie_seule.py`), serveur `creer_app('valise_copie', secret='').run(host='0.0.0.0', port=8001)`.
- [ ] À vérifier par Julien (Mac + iPhone) : 4 entrées en bas ; Popote ouvre Dîners ; onglets Dîners · Courses · Cave en haut, couleur de la page active, sans chevauchement avec le bouton du thème ; Dîners garde ses onglets Ce soir · Semaine · Recettes en dessous ; liens d'Aujourd'hui vers Ce soir toujours bons ; sur Mac, colonne à 4 entrées.
- [ ] Push / PR / merge seulement sur demande de Julien.
