# Casa Binomerie — Budget de la maison Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Un onglet « Budget » (et une ligne sur Aujourd'hui) qui montre, semaine par semaine, le coût estimé des courses et des repas commandés ou au resto, avec un graphique d'évolution.

**Architecture:** Un journal `achats` (qui sert aussi à ne plus redemander ce qu'on vient d'acheter, 3 jours) alimenté par `db.enregistrer_article` quand un article est coché (prix estimé de `prix_paris.prix_de`). Un module pur `budget.py` calcule les semaines (courses, commandes × 35 €, restos × 60 €, repas maison) et rend la page Budget (HTML + graphique SVG côté serveur). La route `/budget`, la 5ᵉ entrée de la barre du bas et une ligne sur Aujourd'hui l'exposent.

**Tech Stack:** Python 3, Flask, psycopg2, Postgres (local `valise_test` pour les tests, Neon en prod), pytest.

Spec : `docs/superpowers/specs/2026-11-02-casa-budget-design.md`.

## Global Constraints

- Tout se passe dans `voyage/`. Tests : `cd voyage && .venv/bin/python3 -m pytest -q` (base locale `valise_test`, jamais Neon). Suite actuelle : 698 tests verts.
- TDD : test qui échoue d'abord, puis le code.
- Chiffres estimés, zéro saisie. Forfaits pour deux : **35 € la livraison** (`diners.LIVRAISON_DEUX`), **60 € le resto** (`budget.FORFAIT_RESTO`).
- Semaine du lundi au dimanche, heure de Paris. 12 semaines affichées, la plus récente en premier.
- Pas de double comptage : total = courses + commandes et restos ; le coût des repas maison est affiché à part.
- Un article hors du prix de référence compte 0 € et est signalé.
- Barre du bas : Aujourd'hui, Dîners, Courses, Budget, Vadrouille.
- `VERSION_PAGE` (dans `valise.py`) passe de 41 à 42.
- Migration Neon : à blanc d'abord ; `--appliquer` seulement avec l'accord explicite de Julien, après qu'il a testé la démo, avant le merge. Push, PR et merge seulement à sa demande (`env -u GITHUB_TOKEN gh …`). Ne jamais lancer `appliquer_schema.py` sans `--base valise_test` (sauf la Task 4, par le contrôleur).
- Branche : `feat/casa-budget` (déjà créée depuis `main`, la spec y est commitée).

## Fichiers

- Modifier `voyage/schema.sql` : table `achats`.
- Modifier `voyage/db.py` : `enregistrer_article` (journal), nouvelle `lire_achats`.
- Créer `voyage/budget.py` : calcul des semaines, page Budget.
- Modifier `voyage/serveur.py` : route `/budget`, ligne budget sur Aujourd'hui.
- Modifier `voyage/casa.py` : `bloc_budget`, paramètre `semaine_budget` de `aujourdhui_en_html`.
- Modifier `voyage/design.py` : 5ᵉ entrée `budget` de la barre du bas.
- Modifier `voyage/valise.py` : `VERSION_PAGE = 42`.
- Tests : `voyage/test_courses_db.py`, nouveau `voyage/test_budget.py`, `voyage/test_casa.py`.

---

### Task 1: Le journal des achats

**Files:**
- Modify: `voyage/schema.sql` (à la fin du fichier)
- Modify: `voyage/db.py:582-608` (`enregistrer_article`), nouvelle `lire_achats` juste après `lire_courses`
- Test: `voyage/test_courses_db.py`

**Interfaces:**
- Produces: table `achats (id, article, nom, prix NUMERIC NULL, jour DATE, cree_le)`. `db.lire_achats(conn, debut, fin) -> [{"jour": date, "nom": str, "prix": float | None}]`, triés par jour puis id.

- [ ] **Step 1: Écrire les tests qui échouent**

Dans `voyage/test_courses_db.py` :

1. Dans la fixture `conn`, remplacer `cur.execute("TRUNCATE courses, placard")` par `cur.execute("TRUNCATE courses, placard, achats")`.
2. Ajouter `lire_achats` à l'import `from db import (…)`.
3. Ajouter, avant `def test_supprimer_et_compter(conn):` :

```python
# --- Le journal des achats (budget) ---

def test_cocher_note_l_achat_avec_son_prix_estime(conn):
    from casa import aujourd_hui_paris
    from prix_paris import prix_de
    jour = aujourd_hui_paris()
    enregistrer_article(conn, article("lait-0001", "lait", rayon="frais"))
    assert lire_achats(conn, jour, jour) == []                                   # sur la liste : pas encore acheté
    enregistrer_article(conn, article("lait-0001", "lait", rayon="frais", pris=True))
    enregistrer_article(conn, article("lait-0001", "lait", rayon="frais", pris=True))   # recoché : une seule fois
    enregistrer_article(conn, article("truc-0001", "bidule introuvable", pris=True))
    assert lire_achats(conn, jour, jour) == [{"jour": jour, "nom": "lait", "prix": prix_de("lait")[1]},
                                             {"jour": jour, "nom": "bidule introuvable", "prix": None}]


def test_decocher_le_meme_jour_efface_l_achat(conn):
    from casa import aujourd_hui_paris
    jour = aujourd_hui_paris()
    enregistrer_article(conn, article("pain-0001", "pain", pris=True))
    enregistrer_article(conn, article("pain-0001", "pain"))                      # coché par erreur
    assert lire_achats(conn, jour, jour) == []


def test_vider_les_pris_garde_le_journal(conn):
    from casa import aujourd_hui_paris
    jour = aujourd_hui_paris()
    enregistrer_article(conn, article("pain-0001", "pain", pris=True))
    enregistrer_article(conn, article("lait-0001", "lait", pris=True, recurrent=True))
    vider_pris(conn)
    assert [a["nom"] for a in lire_achats(conn, jour, jour)] == ["pain", "lait"]
```

- [ ] **Step 2: Lancer les tests, vérifier qu'ils échouent**

Run: `cd voyage && .venv/bin/python3 -m pytest test_courses_db.py -q`
Expected: FAIL (`cannot import name 'lire_achats'`, ou `relation "achats" does not exist`).

- [ ] **Step 3: La table**

À la fin de `voyage/schema.sql` :

```sql
-- Le journal des achats (02/11/2026) : chaque article coché dans Courses, son prix estimé (prix_paris), le jour à
-- Paris. Décoché le même jour : la ligne part. Vider les pris n'y touche pas. Sert au budget de la maison.
CREATE TABLE IF NOT EXISTS achats (
    id          SERIAL        PRIMARY KEY,
    article     TEXT          NOT NULL,
    nom         TEXT          NOT NULL,
    prix        NUMERIC(8,2),
    jour        DATE          NOT NULL,
    cree_le     TIMESTAMPTZ   NOT NULL DEFAULT now()
);
```

Appliquer à la base de test : `cd voyage && .venv/bin/python3 appliquer_schema.py --base valise_test --appliquer`

- [ ] **Step 4: Le journal dans `enregistrer_article` (`db.py`)**

Remplacer :

```python
            if meme:
                a = {**a, "id": meme[0], "nom": meme[1], "rayon": meme[2], "recurrent": meme[3] or a["recurrent"],
                     "source": meme[4], "actif": True}
        cur.execute(
```

par :

```python
            if meme:
                a = {**a, "id": meme[0], "nom": meme[1], "rayon": meme[2], "recurrent": meme[3] or a["recurrent"],
                     "source": meme[4], "actif": True}
        cur.execute("SELECT pris FROM courses WHERE id = %s", (a["id"],))
        avant = cur.fetchone()
        etait_pris = bool(avant and avant[0])
        cur.execute(
```

et remplacer la fin de la fonction :

```python
        if a["pris"]:
            cur.execute("""UPDATE placard SET en_stock = true, bientot = false, maj_le = now()
                           WHERE cle = %s AND (NOT en_stock OR bientot)""", (normaliser(a["nom"]),))
            if a["source"].startswith("plat:") and a["rayon"] in RAYONS_DURABLES:
                cur.execute("""INSERT INTO placard (cle, nom, zone) VALUES (%s, %s, %s) ON CONFLICT (cle) DO NOTHING""",
                            (normaliser(a["nom"]), a["nom"], deviner_zone(a["nom"], a["rayon"])))
    conn.commit()
```

par :

```python
        if a["pris"]:
            cur.execute("""UPDATE placard SET en_stock = true, bientot = false, maj_le = now()
                           WHERE cle = %s AND (NOT en_stock OR bientot)""", (normaliser(a["nom"]),))
            if a["source"].startswith("plat:") and a["rayon"] in RAYONS_DURABLES:
                cur.execute("""INSERT INTO placard (cle, nom, zone) VALUES (%s, %s, %s) ON CONFLICT (cle) DO NOTHING""",
                            (normaliser(a["nom"]), a["nom"], deviner_zone(a["nom"], a["rayon"])))
        # Le journal des achats (budget) : coché, une ligne au prix estimé ; décoché le même jour, elle part
        if a["pris"] and not etait_pris:
            from prix_paris import prix_de
            prix = prix_de(a["nom"])
            cur.execute("""INSERT INTO achats (article, nom, prix, jour)
                           VALUES (%s, %s, %s, (now() AT TIME ZONE 'Europe/Paris')::date)""",
                        (a["id"], a["nom"], prix[1] if prix else None))
        elif etait_pris and not a["pris"]:
            cur.execute("""DELETE FROM achats WHERE article = %s
                           AND jour = (now() AT TIME ZONE 'Europe/Paris')::date""", (a["id"],))
    conn.commit()
```

Et compléter la docstring de `enregistrer_article` par une phrase à la fin : `Coché : noté au journal des achats (prix estimé) ; décoché le même jour : retiré du journal.`

- [ ] **Step 5: `lire_achats` (`db.py`)**

Juste après la fonction `lire_courses` :

```python
def lire_achats(conn, debut, fin):
    """Le journal des achats entre deux jours (compris) : [{jour, nom, prix (None hors catalogue)}]."""
    with conn.cursor() as cur:
        cur.execute("SELECT jour, nom, prix FROM achats WHERE jour BETWEEN %s AND %s ORDER BY jour, id", (debut, fin))
        return [{"jour": jour, "nom": nom, "prix": float(prix) if prix is not None else None}
                for jour, nom, prix in cur.fetchall()]
```

- [ ] **Step 6: Lancer les tests**

Run: `cd voyage && .venv/bin/python3 -m pytest test_courses_db.py -q`
Expected: PASS.
Run: `cd voyage && .venv/bin/python3 -m pytest -q`
Expected: tout passe (698 + 3).

- [ ] **Step 7: Commit**

```bash
git add voyage/schema.sql voyage/db.py voyage/test_courses_db.py
git commit -m "feat: Casa Binomerie — journal des achats : chaque article coché, son prix estimé, le jour"
```

---

### Task 2: Ce qu'on vient d'acheter compte comme « à la maison » (3 jours)

Retour de Julien (02/11/2026) : salade achetée, panier vidé, et elle reste dans « À acheter pour aujourd'hui ». Un
article ni au placard ni habituel est oublié dès qu'on vide les pris. Le journal des achats (Task 1) s'en souvient :
ce qui a été acheté ces 3 derniers jours (aujourd'hui compris) compte comme disponible, comme un habituel rangé.

**Files:**
- Modify: `voyage/diners.py` (constante `FRAIS_JOURS`, fonction `avec_achats_recents`, juste avant `def disponibles`)
- Modify: `voyage/serveur.py` (accueil, `GET api/diners`, `POST api/diners/courses`)
- Test: `voyage/test_diners.py`, `voyage/test_diners_db.py`

**Interfaces:**
- Consumes: `db.lire_achats(conn, debut, fin)` (Task 1).
- Produces: `diners.FRAIS_JOURS = 3` ; `diners.avec_achats_recents(courses, noms) -> list` : les articles `courses` plus, pour chaque nom acheté récemment, un article `{"nom": nom, "recurrent": True, "actif": False, "pris": False}` (lu par `disponibles` comme un habituel rangé).

- [ ] **Step 1: Écrire les tests qui échouent**

À la fin de `voyage/test_diners.py` :

```python
def test_achete_recemment_compte_comme_a_la_maison():
    from diners import a_acheter_aujourd_hui, avec_achats_recents
    burger = plat("plat-burger-01", "Burger", ingredients=["salade", "tomates"])
    courses = avec_achats_recents([], ["Salade"])                        # achetée, panier vidé
    assert a_acheter_aujourd_hui([burger], placard(), courses) == ["tomates"]
    assert "salade" in disponibles(placard(), courses)
```

À la fin de `voyage/test_diners_db.py` :

```python
def test_aujourd_hui_oublie_pas_ce_qu_on_vient_d_acheter(client):
    client.post("/api/repas", json={"jour": J.isoformat(), "moment": "diner", "plats": ["plat-piece-du-boucher"],
                                    "issue": None})
    client.post("/api/courses", json={"id": "boucher-01", "nom": "pièce du boucher", "pris": True})
    client.post("/api/courses/vider")                                     # le panier est vidé
    html = client.get("/").get_data(as_text=True)
    bloc = html.split('<a class="bloc-courses"')[1].split("</a>")[0] if '<a class="bloc-courses"' in html else ""
    assert "pièce du boucher" not in bloc
    assert "pièce du boucher" in client.get("/api/diners").get_json()["stock"]
```

Et dans la fixture `conn` de `voyage/test_diners_db.py`, ajouter `achats` au `TRUNCATE`
(`TRUNCATE repas, plats, courses, placard, reprises` → `TRUNCATE repas, plats, courses, placard, reprises, achats`).

- [ ] **Step 2: Lancer les tests, vérifier qu'ils échouent**

Run: `cd voyage && .venv/bin/python3 -m pytest test_diners.py test_diners_db.py -q`
Expected: FAIL (`cannot import name 'avec_achats_recents'` ; la pièce du boucher encore à acheter).

- [ ] **Step 3: `avec_achats_recents` (`diners.py`)**

Juste avant `def disponibles(` :

```python
FRAIS_JOURS = 3             # acheté il y a moins de 3 jours (aujourd'hui compris) : on l'a encore


def avec_achats_recents(courses, noms):
    """Les articles de la liste, plus ce qu'on vient d'acheter (journal des achats, FRAIS_JOURS) : compté comme un
    habituel rangé, donc disponible, même si le panier a été vidé."""
    return list(courses) + [{"nom": n, "recurrent": True, "actif": False, "pris": False} for n in noms]
```

- [ ] **Step 4: Les routes (`serveur.py`)**

Ajouter `avec_achats_recents, FRAIS_JOURS` à l'import `from diners import (…)`, `lire_achats` à l'import
`from db import (…)` et, juste avant `def creer_app(`, la fonction :

```python
def articles_et_achats_recents(conn, articles, jour):
    """La liste de courses, plus ce qui a été acheté ces FRAIS_JOURS derniers jours (voir avec_achats_recents)."""
    recents = lire_achats(conn, jour - timedelta(days=FRAIS_JOURS - 1), jour)
    return avec_achats_recents(articles, [a["nom"] for a in recents])
```

Puis, dans les trois routes qui regardent ce qu'on a :

1. `accueil` : remplacer `a_acheter_aujourd_hui(du_jour, lu["placard"], lu["articles"])` par
   `a_acheter_aujourd_hui(du_jour, lu["placard"], articles_et_achats_recents(conn, lu["articles"], jour))`.
2. `lire_les_diners` (`GET api/diners`) : après `lu = lire_courses(conn)` (dans le `try`, avant `finally`), ajouter
   `articles = articles_et_achats_recents(conn, lu["articles"], jour)` ; puis, après le `finally`, remplacer
   `lu["articles"]` par `articles` dans les appels à `secours(...)`, `cout_semaine(...)` et `disponibles(...)` — mais
   **pas** dans le calcul de `"liste"` (la vraie liste de courses).
3. `courses_de_la_semaine` (`POST api/diners/courses`) : remplacer
   `a_acheter(prevus, lu["placard"], lu["articles"])` par
   `a_acheter(prevus, lu["placard"], articles_et_achats_recents(conn, lu["articles"], jour))`.

- [ ] **Step 5: Lancer les tests**

Run: `cd voyage && .venv/bin/python3 -m pytest -q`
Expected: tout passe.

- [ ] **Step 6: Commit**

```bash
git add voyage/diners.py voyage/serveur.py voyage/test_diners.py voyage/test_diners_db.py
git commit -m "fix: Casa Binomerie — ce qu'on vient d'acheter (3 jours) compte comme à la maison, même panier vidé"
```

---

### Task 3: Le calcul des semaines (`budget.py`)

**Files:**
- Create: `voyage/budget.py`
- Test: `voyage/test_budget.py` (nouveau)

**Interfaces:**
- Consumes: achats au format de `db.lire_achats` (`{"jour", "nom", "prix"}`), repas au format de `db.lire_repas` (`{"jour", "moment", "plats", "issue"}`), plats `{id: plat}` (avec `ingredients`, `recette`). `prix_paris.cout_repas(ingredients, recette)`, `diners.LIVRAISON_DEUX` (35).
- Produces: `budget.FORFAIT_RESTO = 60` ; `budget.lundi(jour) -> date` ; `budget.euros(x) -> str` (« 82 € », arrondi à l'euro) ; `budget.semaines_budget(achats, repas, plats, aujourd_hui, n=12) -> list[dict]`, la semaine en cours en premier, chaque dict : `{"lundi": date, "courses": float, "courses_suivies": bool, "sans_prix": int, "commandes": int, "restos": int, "livraison": float, "total": float, "maison": int, "cout_maison": float | None, "economie": float}` ; `budget.moyenne_precedentes(semaines, k=4) -> float | None`.

- [ ] **Step 1: Écrire les tests qui échouent**

Créer `voyage/test_budget.py` :

```python
"""Tests du budget de la maison (budget.py) : les semaines, les forfaits, les repas maison."""
import sys
from datetime import date, timedelta
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from budget import semaines_budget, moyenne_precedentes, lundi, euros, FORFAIT_RESTO
from diners import LIVRAISON_DEUX
from prix_paris import cout_repas

MER = date(2026, 11, 4)                     # un mercredi : la semaine commence le lundi 2
LUN = date(2026, 11, 2)
CARBO = {"id": "plat-carbonara", "ingredients": ["spaghetti", "œufs", "pecorino"], "recette": "Pour 2"}
PLATS = {"plat-carbonara": CARBO}


def achat(jour, nom, prix):
    return {"jour": jour, "nom": nom, "prix": prix}


def repas(jour, issue, *plats, moment="diner"):
    return {"jour": jour, "moment": moment, "plats": list(plats), "issue": issue}


def test_lundi_et_euros():
    assert lundi(MER) == LUN and lundi(LUN) == LUN and lundi(date(2026, 11, 8)) == LUN
    assert euros(81.6) == "82 €" and euros(36.5) == "37 €" and euros(0) == "0 €" and euros(-2.4) == "-2 €"


def test_une_semaine():
    achats = [achat(LUN, "lait", 1.5), achat(MER, "pain", 1.4), achat(MER, "bidule", None),
              achat(LUN - timedelta(days=1), "hier dimanche", 9.0)]                    # semaine d'avant
    les_repas = [repas(LUN, "fait", "plat-carbonara"), repas(MER, "commande"),
                 repas(MER, "dehors", moment="dejeuner"), repas(MER + timedelta(days=1), None, "plat-carbonara")]
    s = semaines_budget(achats, les_repas, PLATS, MER)[0]
    cout = cout_repas(CARBO["ingredients"], CARBO["recette"])
    assert s["lundi"] == LUN and s["courses"] == 2.9 and s["sans_prix"] == 1 and s["courses_suivies"]
    assert (s["commandes"], s["restos"]) == (1, 1) and s["livraison"] == LIVRAISON_DEUX + FORFAIT_RESTO
    assert s["total"] == round(2.9 + LIVRAISON_DEUX + FORFAIT_RESTO, 2)
    assert s["maison"] == 1 and s["cout_maison"] == round(cout, 2)
    assert s["economie"] == round(LIVRAISON_DEUX - cout, 2)


def test_douze_semaines_la_plus_recente_en_premier():
    semaines = semaines_budget([], [], {}, MER)
    assert len(semaines) == 12 and semaines[0]["lundi"] == LUN and semaines[1]["lundi"] == LUN - timedelta(weeks=1)
    assert semaines[0]["cout_maison"] is None and semaines[0]["total"] == 0 and not semaines[0]["courses_suivies"]


def test_courses_suivies_a_partir_du_premier_achat():
    semaines = semaines_budget([achat(LUN - timedelta(days=3), "lait", 1.5)], [], {}, MER)
    assert semaines[0]["courses_suivies"] and semaines[1]["courses_suivies"] and not semaines[2]["courses_suivies"]


def test_repas_maison_sans_plat_compte_mais_sans_cout():
    s = semaines_budget([], [repas(LUN, "fait"), repas(MER, "fait", "plat-carbonara")], PLATS, MER)[0]
    cout = cout_repas(CARBO["ingredients"], CARBO["recette"])
    assert s["maison"] == 2 and s["cout_maison"] == round(cout, 2) and s["economie"] == round(LIVRAISON_DEUX - cout, 2)


def test_moyenne_des_semaines_precedentes():
    semaines = semaines_budget([], [repas(LUN - timedelta(weeks=1), "commande"),
                                    repas(LUN - timedelta(weeks=2), "dehors")], {}, MER)
    assert moyenne_precedentes(semaines) == round((LIVRAISON_DEUX + FORFAIT_RESTO) / 2, 2)    # semaines vides ignorées
    assert moyenne_precedentes(semaines_budget([], [], {}, MER)) is None
```

- [ ] **Step 2: Lancer les tests, vérifier qu'ils échouent**

Run: `cd voyage && .venv/bin/python3 -m pytest test_budget.py -q`
Expected: FAIL (`No module named 'budget'`).

- [ ] **Step 3: `budget.py`**

Créer `voyage/budget.py` :

```python
"""Casa Binomerie — Budget de la maison : combien ont coûté les courses et les repas, semaine par semaine.

Chiffres estimés, zéro saisie (spec 2026-11-02-casa-budget-design.md) :
- courses : le journal des achats (db.lire_achats), au prix d'un panier parisien (prix_paris) ;
- commandes et restos : les repas marqués « Commandé » (35 € pour deux) ou « Dehors » (60 € pour deux) ;
- repas maison : affichés pour comparer (coût moyen de leurs recettes), jamais ajoutés au total.
Semaine du lundi au dimanche.
"""
import math
from datetime import timedelta

from diners import LIVRAISON_DEUX
from prix_paris import cout_repas

FORFAIT_RESTO = 60          # un resto pour deux à Paris : l'ordre de grandeur
SEMAINES = 12


def lundi(jour):
    return jour - timedelta(days=jour.weekday())


def euros(x):
    """Arrondi à l'euro, le demi vers le haut (round() de Python arrondit 36,5 à 36)."""
    return f"{math.floor(x + 0.5)} €"


def semaines_budget(achats, repas, plats, aujourd_hui, n=SEMAINES):
    """Les n dernières semaines, la semaine en cours en premier (voir la docstring du module)."""
    premier_achat = min((a["jour"] for a in achats), default=None)
    semaines = []
    for k in range(n):
        debut = lundi(aujourd_hui) - timedelta(weeks=k)
        fin = debut + timedelta(days=6)
        achetes = [a for a in achats if debut <= a["jour"] <= fin]
        vecus = [r for r in repas if debut <= r["jour"] <= fin]
        commandes = sum(1 for r in vecus if r["issue"] == "commande")
        restos = sum(1 for r in vecus if r["issue"] == "dehors")
        maison = [r for r in vecus if r["issue"] == "fait"]
        couts = [sum(cout_repas(plats[i]["ingredients"], plats[i]["recette"]) for i in r["plats"] if i in plats)
                 for r in maison if any(i in plats for i in r["plats"])]
        courses = round(sum(a["prix"] or 0 for a in achetes), 2)
        livraison = commandes * LIVRAISON_DEUX + restos * FORFAIT_RESTO
        semaines.append({
            "lundi": debut, "courses": courses, "courses_suivies": premier_achat is not None and fin >= premier_achat,
            "sans_prix": sum(1 for a in achetes if a["prix"] is None),
            "commandes": commandes, "restos": restos, "livraison": livraison, "total": round(courses + livraison, 2),
            "maison": len(maison), "cout_maison": round(sum(couts) / len(couts), 2) if couts else None,
            "economie": round(len(couts) * LIVRAISON_DEUX - sum(couts), 2)})
    return semaines


def moyenne_precedentes(semaines, k=4):
    """Le total moyen des k semaines avant la semaine en cours, celles sans aucun chiffre ignorées ; None sinon."""
    precedentes = [s for s in semaines[1:1 + k] if s["total"] or s["maison"]]
    return round(sum(s["total"] for s in precedentes) / len(precedentes), 2) if precedentes else None
```

- [ ] **Step 4: Lancer les tests**

Run: `cd voyage && .venv/bin/python3 -m pytest test_budget.py -q`
Expected: PASS (6 tests).
Run: `cd voyage && .venv/bin/python3 -m pytest -q`
Expected: tout passe.

- [ ] **Step 5: Commit**

```bash
git add voyage/budget.py voyage/test_budget.py
git commit -m "feat: Casa Binomerie — budget : courses, commandes et restos, repas maison, semaine par semaine"
```

---

### Task 4: Les pages — onglet Budget, ligne sur Aujourd'hui

**Files:**
- Modify: `voyage/budget.py` (page : `STYLE_BUDGET`, `graphique_svg`, `budget_en_html`)
- Modify: `voyage/design.py` (`HUB`, `ICONES_HUB`, CSS de la barre)
- Modify: `voyage/casa.py` (`bloc_budget`, `aujourdhui_en_html`, CSS)
- Modify: `voyage/serveur.py` (route `/budget`, Aujourd'hui)
- Modify: `voyage/valise.py` (`VERSION_PAGE = 42`)
- Test: `voyage/test_budget.py`, `voyage/test_casa.py`

**Interfaces:**
- Consumes: `semaines_budget`, `moyenne_precedentes`, `euros`, `lundi` (Task 3) ; `db.lire_achats(conn, debut, fin)` (Task 1) ; `db.lire_repas`, `db.lire_plats`.
- Produces: `budget.budget_en_html(semaines, moyenne) -> str` ; `budget.graphique_svg(semaines) -> str` ; `casa.bloc_budget(semaine) -> str` ; `aujourdhui_en_html(..., semaine_budget=None)` ; route `GET /budget`.

- [ ] **Step 1: Écrire les tests qui échouent**

À la fin de `voyage/test_budget.py` :

```python
# --- Pages ---
from budget import budget_en_html, graphique_svg


def test_page_budget():
    les_repas = [repas(MER, "commande"), repas(LUN, "fait", "plat-carbonara")]
    semaines = semaines_budget([achat(LUN, "lait", 1.5), achat(LUN, "bidule", None)], les_repas, PLATS, MER)
    # 1,50 € de courses + 35 € de livraison = 36,50 € -> 37 €
    html = budget_en_html(semaines, moyenne_precedentes(semaines))
    assert "<title>Budget · Casa Binomerie</title>" in html and "<h1>Budget</h1>" in html
    assert 'data-hub="budget" class="actif"' in html
    assert "Cette semaine" in html and "37 €" in html
    assert "1 article sans prix" in html and "pas encore suivi" in html        # semaines d'avant le premier achat
    assert html.count("<tr") == 13                                              # en-tête + 12 semaines
    assert '<svg class="graphique"' in html


def test_graphique_barres_empilees():
    semaines = semaines_budget([achat(LUN, "lait", 20.0)], [repas(MER, "commande")], {}, MER)
    svg = graphique_svg(semaines)
    assert svg.count('class="barre-courses"') == 12 and svg.count('class="barre-livraison"') == 12
    assert svg.index("02/11") > svg.index("31/08")                              # la plus ancienne à gauche
```

Dans `voyage/test_casa.py` :

1. Remplacer la première assertion de `test_le_hub_commence_par_aujourd_hui_et_finit_par_la_vadrouille` par :

```python
    assert [cle for cle, _, _ in HUB] == ["aujourdhui", "diners", "courses", "budget", "vadrouille"]   # les modules s'ajoutent à leur livraison
```

2. Ajouter à la fin du fichier :

```python
def test_ligne_budget_sur_aujourd_hui():
    semaine = {"total": 81.6, "livraison": 35, "courses": 46.6}
    html = aujourdhui_en_html([], AUJOURD_HUI, semaine_budget=semaine)
    assert ('<a class="bloc-budget" href="budget"><strong>Cette semaine : 82 €</strong>'
            '<span>dont livraison et resto 35 €</span></a>') in html
    vide = aujourdhui_en_html([], AUJOURD_HUI, semaine_budget={"total": 0, "livraison": 0, "courses": 0})
    assert 'class="bloc-budget"' not in vide.split("<body")[1]
```

- [ ] **Step 2: Lancer les tests, vérifier qu'ils échouent**

Run: `cd voyage && .venv/bin/python3 -m pytest test_budget.py test_casa.py -q`
Expected: FAIL (`cannot import name 'budget_en_html'`, HUB à 4 entrées, `semaine_budget` inconnu).

- [ ] **Step 3: La barre du bas (`design.py`)**

Remplacer :

```python
    ("courses", "Courses", "courses"),
    ("vadrouille", "Vadrouille", "vadrouille"),          # court : tient dans la barre du bas sur iPhone
```

par :

```python
    ("courses", "Courses", "courses"),
    ("budget", "Budget", "budget"),
    ("vadrouille", "Vadrouille", "vadrouille"),          # court : tient dans la barre du bas sur iPhone
```

Dans `ICONES_HUB`, juste avant la ligne `"vadrouille": ICONES_RUBRIQUE["valise"],` :

```python
    "budget": _TRAIT.format('<path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/>'),
```

Dans `STYLE_NAV_HUB`, juste après la ligne `nav.hub a[data-hub="courses"] { --c: var(--courses); --c-doux: var(--courses-doux); }` :

```css
nav.hub a[data-hub="budget"] { --c: var(--courses); --c-doux: var(--courses-doux); }
```

- [ ] **Step 4: La page Budget (`budget.py`)**

Ajouter en tête de `voyage/budget.py`, sous `from datetime import timedelta` :

```python
from html import escape as echapper
```

Sous `from prix_paris import cout_repas` :

```python
from design import STYLE_D, STYLE_NAV_HUB, TETE_POLICE, nav_hub
from pwa import TETE_PWA
from valise import HTML_STYLE
```

Puis à la fin du fichier :

```python
# --- Page ---------------------------------------------------------------------------------------

STYLE_BUDGET = """
div.chiffres { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 8px; margin: 0 0 16px; }
div.chiffres div { background: var(--carte); border-radius: 18px; padding: 12px; display: flex; flex-direction: column; gap: 2px; }
div.chiffres strong { font-size: 22px; font-weight: 800; }
div.chiffres span { font-size: 12px; color: var(--doux); font-weight: 600; }
p.note-budget { color: var(--doux); font-size: 13px; margin: 0 0 12px; }
svg.graphique { width: 100%; height: auto; display: block; margin: 0 0 8px; }
svg.graphique .barre-courses { fill: var(--courses); }
svg.graphique .barre-livraison { fill: var(--diners); }
svg.graphique text { fill: var(--doux); font-size: 9px; font-family: inherit; }
p.legende { font-size: 13px; color: var(--doux); margin: 0 0 16px; display: flex; gap: 14px; }
p.legende span::before { content: ""; display: inline-block; width: 10px; height: 10px; border-radius: 3px; margin-right: 5px; }
p.legende .l-courses::before { background: var(--courses); }
p.legende .l-livraison::before { background: var(--diners); }
div.tableau { overflow-x: auto; }
table.budget { width: 100%; border-collapse: collapse; font-size: 14px; }
table.budget th { text-align: left; font-size: 12px; color: var(--doux); font-weight: 700; padding: 6px 4px; }
table.budget td { padding: 10px 4px; border-top: 1px solid var(--ligne); white-space: nowrap; }
table.budget td.total { font-weight: 800; }
table.budget td small { color: var(--doux); font-size: 12px; display: block; }
"""

HAUTEUR, LARGEUR = 140, 360


def graphique_svg(semaines):
    """Barres empilées (courses en bas, commandes et restos au-dessus), la plus ancienne semaine à gauche."""
    ordre = list(reversed(semaines))
    haut = max((s["total"] for s in ordre), default=0) or 1
    pas = LARGEUR / len(ordre)
    barres = []
    for k, s in enumerate(ordre):
        x = k * pas + pas * 0.15
        l = pas * 0.7
        h_courses = s["courses"] / haut * (HAUTEUR - 20)
        h_livraison = s["livraison"] / haut * (HAUTEUR - 20)
        bas = HAUTEUR - 14
        barres.append(
            f'<rect class="barre-courses" x="{x:.1f}" y="{bas - h_courses:.1f}" width="{l:.1f}" height="{h_courses:.1f}" rx="2"/>'
            f'<rect class="barre-livraison" x="{x:.1f}" y="{bas - h_courses - h_livraison:.1f}" width="{l:.1f}" '
            f'height="{h_livraison:.1f}" rx="2"/>'
            f'<text x="{x + l / 2:.1f}" y="{HAUTEUR - 2}" text-anchor="middle">{s["lundi"]:%d/%m}</text>')
    return (f'<svg class="graphique" viewBox="0 0 {LARGEUR} {HAUTEUR}" role="img" '
            f'aria-label="Dépenses des {len(ordre)} dernières semaines">{"".join(barres)}</svg>')


def _ligne(s):
    courses = euros(s["courses"]) if s["courses_suivies"] else '— <small>pas encore suivi</small>'
    if s["sans_prix"]:
        courses += f'<small>{s["sans_prix"]} article{"s" if s["sans_prix"] > 1 else ""} sans prix</small>'
    detail = " · ".join(x for x in (f'{s["commandes"]} livr.' if s["commandes"] else "",
                                    f'{s["restos"]} resto' if s["restos"] else "") if x)
    livraison = euros(s["livraison"]) + (f"<small>{detail}</small>" if detail else "")
    maison = (f'{s["maison"]}' + (f'<small>{euros(s["cout_maison"])} / repas</small>' if s["cout_maison"] is not None else "")
              if s["maison"] else "—")
    return (f'<tr><td>{s["lundi"]:%d/%m}</td><td>{courses}</td><td>{livraison}</td>'
            f'<td class="total">{euros(s["total"])}</td><td>{maison}</td></tr>')


def budget_en_html(semaines, moyenne):
    """La page Budget : les chiffres de la semaine, le graphique des 12 dernières, le tableau."""
    s = semaines[0]
    chiffres = (f'<div><strong>{euros(s["total"])}</strong><span>Cette semaine</span></div>'
                f'<div><strong>{euros(moyenne) if moyenne is not None else "—"}</strong><span>Moyenne des 4 précédentes</span></div>'
                f'<div><strong>{euros(s["economie"])}</strong><span>Économisés vs tout livrer</span></div>')
    lignes = "".join(_ligne(x) for x in semaines)
    return f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Budget · Casa Binomerie</title>
{TETE_PWA}
{TETE_POLICE}
<style>{HTML_STYLE}{STYLE_D}{STYLE_NAV_HUB}{STYLE_BUDGET}</style>
</head>
<body class="accueil hub-page">
<h1>Budget</h1>
<div class="chiffres">{chiffres}</div>
<p class="note-budget">Estimations : courses au prix d'un panier parisien, livraison {euros(LIVRAISON_DEUX)} et resto {euros(FORFAIT_RESTO)} pour deux.</p>
{graphique_svg(semaines)}
<p class="legende"><span class="l-courses">Courses</span><span class="l-livraison">Livraison et resto</span></p>
<div class="tableau"><table class="budget">
<tr><th>Semaine du</th><th>Courses</th><th>Livraison, resto</th><th>Total</th><th>Repas maison</th></tr>
{lignes}
</table></div>
{nav_hub("budget")}
</body>
</html>"""
```

(Le libellé du lundi s'écrit `{s["lundi"]:%d/%m}` : une date accepte un format strftime dans une f-string.)

- [ ] **Step 5: La ligne sur Aujourd'hui (`casa.py`)**

Dans `STYLE_CASA`, juste après la ligne `a.bloc-courses span { font-weight: 700; }` :

```css
a.bloc-budget { display: flex; flex-direction: column; gap: 2px; background: var(--carte); color: var(--texte);
                text-decoration: none; border-radius: 24px; padding: 16px 20px; margin: 16px 0; }
a.bloc-budget strong { font-size: 19px; font-weight: 800; }
a.bloc-budget span { color: var(--doux); font-size: 14px; }
```

Juste après la fonction `bloc_courses` :

```python
def bloc_budget(semaine):
    """« Cette semaine : 82 € · dont livraison et resto 35 € » (budget.semaines_budget) ; rien tant que c'est 0 €."""
    from budget import euros
    if not semaine or not semaine["total"]:
        return ""
    return (f'<a class="bloc-budget" href="budget"><strong>Cette semaine : {euros(semaine["total"])}</strong>'
            f'<span>dont livraison et resto {euros(semaine["livraison"])}</span></a>')
```

Remplacer la signature et le début de `aujourdhui_en_html` :

```python
def aujourdhui_en_html(voyages, aujourd_hui, a_acheter=(), plats_du_soir=(), diner_hier=None, compte=None):
    """L'accueil du hub : ce soir, hier soir, ce qu'il faut acheter aujourd'hui, le prochain voyage, le compteur
    Deliveroo."""
    v = prochain_voyage(voyages, aujourd_hui)
    blocs = (bloc_ce_soir(list(plats_du_soir)) + (bloc_hier(diner_hier) if diner_hier else "") + bloc_courses(list(a_acheter))
```

par :

```python
def aujourdhui_en_html(voyages, aujourd_hui, a_acheter=(), plats_du_soir=(), diner_hier=None, compte=None,
                       semaine_budget=None):
    """L'accueil du hub : ce soir, hier soir, ce qu'il faut acheter aujourd'hui, le budget de la semaine, le prochain
    voyage, le compteur Deliveroo."""
    v = prochain_voyage(voyages, aujourd_hui)
    blocs = (bloc_ce_soir(list(plats_du_soir)) + (bloc_hier(diner_hier) if diner_hier else "") + bloc_courses(list(a_acheter))
             + bloc_budget(semaine_budget)
```

(La ligne suivante, `+ (bloc_vadrouille(v, aujourd_hui) if v else "") + bloc_compteur(compte))`, reste telle quelle.)

- [ ] **Step 6: Les routes (`serveur.py`)**

1. (`lire_achats` est déjà importé depuis la Task 2.) Sous les imports existants depuis `casa` :

```python
from budget import semaines_budget, moyenne_precedentes, lundi, budget_en_html, SEMAINES
```

2. Dans `accueil`, remplacer :

```python
                lu = lire_courses(conn)
                html = aujourdhui_en_html(lister_voyages(conn), jour,
                                          a_acheter_aujourd_hui(du_jour, lu["placard"], lu["articles"]),
                                          ce_soir, hier, compteur(repas, jour))
```

par :

```python
                lu = lire_courses(conn)
                cette_semaine = semaines_budget(lire_achats(conn, lundi(jour), jour), repas, plats, jour, n=1)[0]
                html = aujourdhui_en_html(lister_voyages(conn), jour,
                                          a_acheter_aujourd_hui(du_jour, lu["placard"], lu["articles"]),
                                          ce_soir, hier, compteur(repas, jour), cette_semaine)
```

3. Juste avant le commentaire `# --- Casa Binomerie : dîners ---` :

```python
    @routes.get("/budget")
    def page_budget():
        """Le budget de la maison : 12 semaines de courses (journal des achats) et de repas (budget.py)."""
        jour = aujourd_hui_paris()
        debut = lundi(jour) - timedelta(weeks=SEMAINES - 1)
        conn = emprunter(app.config["NOM_BASE"])
        try:
            semaines = semaines_budget(lire_achats(conn, debut, jour), lire_repas(conn, debut, jour),
                                       {p["id"]: p for p in lire_plats(conn)}, jour)
        finally:
            conn.close()
        return Response(budget_en_html(semaines, moyenne_precedentes(semaines)), mimetype="text/html")

```

4. Test de route : à la fin de `voyage/test_diners_db.py` :

```python
def test_page_budget(client):
    client.post("/api/courses", json={"id": "lait-0001", "nom": "lait", "pris": True})
    client.post("/api/repas", json={"jour": J.isoformat(), "moment": "diner", "plats": [], "issue": "commande"})
    html = client.get("/budget").get_data(as_text=True)
    assert "<h1>Budget</h1>" in html and 'data-hub="budget" class="actif"' in html
    assert '<a class="bloc-budget" href="budget">' in client.get("/").get_data(as_text=True)
```

(la fixture `conn` de `voyage/test_diners_db.py` vide déjà `achats` depuis la Task 2).

- [ ] **Step 7: VERSION_PAGE**

Dans `voyage/valise.py`, `VERSION_PAGE = 41` devient `VERSION_PAGE = 42`.

- [ ] **Step 8: Lancer les tests**

Run: `cd voyage && .venv/bin/python3 -m pytest -q`
Expected: tout passe.

- [ ] **Step 9: Commit**

```bash
git add voyage/budget.py voyage/design.py voyage/casa.py voyage/serveur.py voyage/valise.py voyage/test_budget.py voyage/test_casa.py voyage/test_diners_db.py
git commit -m "feat: Casa Binomerie — onglet Budget (chiffres, graphique, tableau) et ligne sur Aujourd'hui, VERSION_PAGE 42"
```

---

### Task 5: Démo pour Julien, puis migration (contrôleur, pas de sous-agent)

**Files:** aucun dans le repo.

- [ ] **Step 1: Copie locale de la prod (Neon en lecture seule)**

Base `valise_copie` avec le schéma de `main`, tables `plats`, `repas`, `courses`, `placard`, `reprises` copiées depuis Neon en session `readonly` (script du scratchpad). Puis `cd voyage && .venv/bin/python3 appliquer_schema.py --base valise_copie --appliquer` (crée `achats`).

- [ ] **Step 2: Démo**

Serveur sur la copie, ouvert au wifi : `cd voyage && .venv/bin/python3 -c "from serveur import creer_app; creer_app('valise_copie', secret='').run(host='0.0.0.0', port=8001)"`. Vérifier soi-même dans Chrome (largeur iPhone, console), cocher deux articles dans Courses pour alimenter le journal. Donner à Julien les liens complets — `http://localhost:8001/budget`, `http://localhost:8001/` et les mêmes en `http://<ipconfig getifaddr en0>:8001/…` pour l'iPhone — et quoi regarder. Attendre son retour ; corriger sur la démo si besoin.

- [ ] **Step 3: Essai à blanc sur Neon, puis s'arrêter**

Run: `cd voyage && .venv/bin/python3 appliquer_schema.py`
Expected: « À blanc : table(s) à créer : achats ; à supprimer : aucune. »
Puis attendre l'accord explicite de Julien avant : `--appliquer` sur Neon, push, PR, merge. Après : arrêter la démo, supprimer `valise_copie`.
