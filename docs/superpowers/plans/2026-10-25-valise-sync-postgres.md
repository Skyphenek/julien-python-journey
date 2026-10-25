# Sync multi-appareils valise.py via Postgres + Flask — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remplacer le `localStorage` du navigateur par Postgres + une API Flask, pour que Julien et Laetitia voient le même état de checklist de valise depuis leurs deux téléphones (même wifi maison).

**Architecture:** `valise.py` génère toujours la checklist HTML (logique inchangée) ; une nouvelle couche `db.py` lit/écrit l'état coché/pas-coché dans Postgres ; un nouveau `serveur.py` (Flask) expose cette couche en API et sert la page HTML ; le JS embarqué dans la page appelle cette API au lieu de `localStorage`.

**Tech Stack:** Python 3, Flask, psycopg2-binary, PostgreSQL 15 (déjà installé via `brew install postgresql@15`), pytest.

## Global Constraints

- Toutes les commandes Python passent par l'environnement virtuel existant : `voyage/.venv/bin/python3` et `voyage/.venv/bin/pip` (ne jamais utiliser le `python3` système pour ce projet).
- Noms de fonctions/variables en français, cohérent avec le reste de `valise.py` et `test_valise.py`.
- Deux bases Postgres : `valise` (dev, utilisée par `serveur.py`) et `valise_test` (utilisée uniquement par les tests pytest). Auth locale par défaut (pas de mot de passe — comportement standard de `brew install postgresql@15`).
- Tous les tests DB/API doivent `TRUNCATE etat_case` avant de s'exécuter — aucune dépendance d'ordre entre tests.
- `voyage/valise.html` reste dans `.gitignore` (déjà le cas) — fichier généré, jamais commité.

---

### Task 1: Schéma Postgres (bases dev + test)

**Files:**
- Create: `voyage/schema.sql`

**Interfaces:**
- Produces: table `etat_case(voyage, proprietaire, theme, objet, coche, maj_le)` avec clé primaire composite `(voyage, proprietaire, theme, objet)`, dans les deux bases `valise` et `valise_test`.

- [ ] **Step 1: Vérifier que Postgres tourne**

Run: `brew services list | grep postgresql`
Expected: une ligne `postgresql@15 started ...`. Si ce n'est pas le cas :
```bash
brew services start postgresql@15
```

- [ ] **Step 2: Créer le fichier de schéma**

```sql
-- voyage/schema.sql
CREATE TABLE etat_case (
    voyage       TEXT    NOT NULL,
    proprietaire TEXT    NOT NULL,
    theme        TEXT    NOT NULL,
    objet        TEXT    NOT NULL,
    coche        BOOLEAN NOT NULL DEFAULT FALSE,
    maj_le       TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (voyage, proprietaire, theme, objet)
);
```

- [ ] **Step 3: Créer les deux bases et appliquer le schéma**

```bash
createdb valise
createdb valise_test
psql valise -f voyage/schema.sql
psql valise_test -f voyage/schema.sql
```

- [ ] **Step 4: Vérifier que la table existe dans les deux bases**

Run: `psql valise -c "\d etat_case"`
Expected : affiche les 6 colonnes (`voyage`, `proprietaire`, `theme`, `objet`, `coche`, `maj_le`) et la clé primaire composite.

Run: `psql valise_test -c "\d etat_case"`
Expected : même résultat.

- [ ] **Step 5: Commit**

```bash
cd /Users/julien/Claude/Work/perso/python/julien-python-journey
git add voyage/schema.sql
git commit -m "feat: schéma Postgres pour l'état de la checklist valise"
```

---

### Task 2: Couche d'accès DB (`voyage/db.py`)

**Files:**
- Create: `voyage/db.py`
- Create: `voyage/test_db.py`

**Interfaces:**
- Consumes: table `etat_case` créée en Task 1.
- Produces:
  - `connecter(nom_base: str = "valise") -> psycopg2.connection`
  - `obtenir_etat(conn, voyage: str) -> dict[str, bool]` — clés au format `"voyage/proprietaire/theme/objet"`
  - `enregistrer_coche(conn, voyage: str, proprietaire: str, theme: str, objet: str, coche: bool) -> None`

- [ ] **Step 1: Installer psycopg2-binary dans le venv**

```bash
cd /Users/julien/Claude/Work/perso/python/julien-python-journey/voyage
.venv/bin/pip install psycopg2-binary
```

- [ ] **Step 2: Écrire les tests (ils vont échouer, `db.py` n'existe pas encore)**

```python
# voyage/test_db.py
"""Tests de db.py — accès Postgres à l'état de la checklist."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pytest
from db import connecter, obtenir_etat, enregistrer_coche


@pytest.fixture
def conn():
    connexion = connecter("valise_test")
    with connexion.cursor() as cur:
        cur.execute("TRUNCATE etat_case")
    connexion.commit()
    yield connexion
    connexion.close()


def test_obtenir_etat_base_vide(conn):
    assert obtenir_etat(conn, "Hanoï") == {}


def test_enregistrer_coche_puis_lecture(conn):
    enregistrer_coche(conn, "Hanoï", "Julien", "Vêtements", "pantalons", True)
    assert obtenir_etat(conn, "Hanoï") == {"Hanoï/Julien/Vêtements/pantalons": True}


def test_enregistrer_coche_upsert_une_seule_ligne(conn):
    enregistrer_coche(conn, "Hanoï", "Julien", "Vêtements", "pantalons", True)
    enregistrer_coche(conn, "Hanoï", "Julien", "Vêtements", "pantalons", False)
    assert obtenir_etat(conn, "Hanoï") == {"Hanoï/Julien/Vêtements/pantalons": False}
    with conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM etat_case")
        assert cur.fetchone()[0] == 1


def test_obtenir_etat_filtre_par_voyage(conn):
    enregistrer_coche(conn, "Hanoï", "Julien", "Vêtements", "pantalons", True)
    enregistrer_coche(conn, "Paris", "Julien", "Vêtements", "manteau", True)
    assert obtenir_etat(conn, "Hanoï") == {"Hanoï/Julien/Vêtements/pantalons": True}
```

- [ ] **Step 3: Lancer les tests pour vérifier qu'ils échouent**

Run: `cd voyage && .venv/bin/python3 -m pytest test_db.py -v`
Expected: `ModuleNotFoundError: No module named 'db'`

- [ ] **Step 4: Écrire `db.py`**

```python
# voyage/db.py
"""Accès Postgres à l'état de la checklist (coché / pas coché)."""
import psycopg2


def connecter(nom_base="valise"):
    """Ouvre une connexion à la base Postgres locale (auth système, pas de mot de passe)."""
    return psycopg2.connect(dbname=nom_base)


def obtenir_etat(conn, voyage):
    """Renvoie {"voyage/proprietaire/theme/objet": True/False} pour ce voyage."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT proprietaire, theme, objet, coche FROM etat_case WHERE voyage = %s",
            (voyage,),
        )
        lignes = cur.fetchall()
    return {
        f"{voyage}/{proprietaire}/{theme}/{objet}": coche
        for proprietaire, theme, objet, coche in lignes
    }


def enregistrer_coche(conn, voyage, proprietaire, theme, objet, coche):
    """Upsert l'état d'une case (une seule clé à la fois, jamais tout l'état)."""
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO etat_case (voyage, proprietaire, theme, objet, coche, maj_le)
            VALUES (%s, %s, %s, %s, %s, now())
            ON CONFLICT (voyage, proprietaire, theme, objet)
            DO UPDATE SET coche = EXCLUDED.coche, maj_le = now()
            """,
            (voyage, proprietaire, theme, objet, coche),
        )
    conn.commit()
```

- [ ] **Step 5: Lancer les tests pour vérifier qu'ils passent**

Run: `cd voyage && .venv/bin/python3 -m pytest test_db.py -v`
Expected: 4 passed

- [ ] **Step 6: Commit**

```bash
cd /Users/julien/Claude/Work/perso/python/julien-python-journey
git add voyage/db.py voyage/test_db.py
git commit -m "feat: couche d'accès Postgres pour l'état de la checklist"
```

---

### Task 3: API Flask (`voyage/serveur.py`)

**Files:**
- Create: `voyage/serveur.py`
- Create: `voyage/test_serveur.py`

**Interfaces:**
- Consumes: `connecter`, `obtenir_etat`, `enregistrer_coche` de `db.py` (Task 2).
- Produces: `creer_app(nom_base: str = "valise") -> flask.Flask` avec 3 routes :
  - `GET /` — sert `voyage/valise.html`
  - `GET /api/etat/<voyage>` — renvoie le dict de `obtenir_etat`
  - `POST /api/coche` — body `{"cle": "...", "coche": bool}`, appelle `enregistrer_coche`

- [ ] **Step 1: Installer Flask dans le venv**

```bash
cd /Users/julien/Claude/Work/perso/python/julien-python-journey/voyage
.venv/bin/pip install flask
```

- [ ] **Step 2: Écrire les tests (ils vont échouer, `serveur.py` n'existe pas encore)**

```python
# voyage/test_serveur.py
"""Tests de serveur.py — API Flask au-dessus de db.py."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pytest
from serveur import creer_app
from db import connecter


@pytest.fixture
def client():
    conn = connecter("valise_test")
    with conn.cursor() as cur:
        cur.execute("TRUNCATE etat_case")
    conn.commit()
    conn.close()
    app = creer_app("valise_test")
    return app.test_client()


def test_etat_base_vide(client):
    reponse = client.get("/api/etat/Hanoï")
    assert reponse.status_code == 200
    assert reponse.get_json() == {}


def test_coche_puis_etat(client):
    reponse = client.post(
        "/api/coche",
        json={"cle": "Hanoï/Julien/Vêtements/pantalons", "coche": True},
    )
    assert reponse.status_code == 200
    reponse = client.get("/api/etat/Hanoï")
    assert reponse.get_json() == {"Hanoï/Julien/Vêtements/pantalons": True}


def test_coche_upsert_une_seule_ligne(client):
    client.post("/api/coche", json={"cle": "Hanoï/Julien/Vêtements/pantalons", "coche": True})
    client.post("/api/coche", json={"cle": "Hanoï/Julien/Vêtements/pantalons", "coche": False})
    conn = connecter("valise_test")
    with conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM etat_case")
        assert cur.fetchone()[0] == 1
    conn.close()


def test_coche_payload_invalide(client):
    reponse = client.post("/api/coche", json={"cle": "Hanoï/Julien/Vêtements/pantalons"})
    assert reponse.status_code == 400
```

- [ ] **Step 3: Lancer les tests pour vérifier qu'ils échouent**

Run: `cd voyage && .venv/bin/python3 -m pytest test_serveur.py -v`
Expected: `ModuleNotFoundError: No module named 'serveur'`

- [ ] **Step 4: Écrire `serveur.py`**

```python
# voyage/serveur.py
"""Serveur Flask : sert la checklist HTML et expose l'état en API Postgres."""
from pathlib import Path

from flask import Flask, jsonify, request, Response

from db import connecter, obtenir_etat, enregistrer_coche


def creer_app(nom_base="valise"):
    app = Flask(__name__)
    app.config["NOM_BASE"] = nom_base

    @app.get("/")
    def accueil():
        chemin = Path(__file__).parent / "valise.html"
        return Response(chemin.read_text(encoding="utf-8"), mimetype="text/html")

    @app.get("/api/etat/<voyage>")
    def etat(voyage):
        conn = connecter(app.config["NOM_BASE"])
        try:
            return jsonify(obtenir_etat(conn, voyage))
        finally:
            conn.close()

    @app.post("/api/coche")
    def coche():
        corps = request.get_json(silent=True)
        if not corps or "cle" not in corps or "coche" not in corps:
            return jsonify({"erreur": "payload invalide"}), 400
        voyage, proprietaire, theme, objet = corps["cle"].split("/")
        conn = connecter(app.config["NOM_BASE"])
        try:
            enregistrer_coche(conn, voyage, proprietaire, theme, objet, bool(corps["coche"]))
        finally:
            conn.close()
        return jsonify({"ok": True})

    return app


if __name__ == "__main__":
    app = creer_app()
    app.run(host="0.0.0.0", port=5000)
```

- [ ] **Step 5: Lancer les tests pour vérifier qu'ils passent**

Run: `cd voyage && .venv/bin/python3 -m pytest test_serveur.py -v`
Expected: 4 passed

- [ ] **Step 6: Commit**

```bash
cd /Users/julien/Claude/Work/perso/python/julien-python-journey
git add voyage/serveur.py voyage/test_serveur.py
git commit -m "feat: API Flask pour lire/écrire l'état de la checklist"
```

---

### Task 4: Injecter la variable `VOYAGE` dans la page générée

**Files:**
- Modify: `voyage/valise.py` (ajout `import json` en tête, fonction `valise_en_html`)
- Modify: `voyage/test_valise.py` (import à compléter)

**Interfaces:**
- Consumes: rien de nouveau.
- Produces: la page HTML générée contient désormais `<script>const VOYAGE = "<libelle_voyage>";</script>` juste avant le script principal — c'est cette variable que le JS (Task 5) utilisera pour appeler l'API.

- [ ] **Step 1: Écrire le test (il va échouer, la variable n'est pas encore injectée)**

Ajouter à la fin de `voyage/test_valise.py` :

```python
def test_valise_en_html_injecte_la_variable_voyage():
    html = valise_en_html({"Partagé": paquet_vide()}, "Hanoï › Siem Reap", 11, {"universel"})
    assert 'const VOYAGE = "Hanoï › Siem Reap";' in html
```

Et compléter l'import en haut du fichier :

```python
from valise import (total_jours, jours_par_type,
                    statut_ue_itineraire, prises_itineraire,
                    quantite_reelle, faire_valise,
                    valise_en_html, paquet_vide)
```

- [ ] **Step 2: Lancer le test pour vérifier qu'il échoue**

Run: `cd voyage && .venv/bin/python3 -m pytest test_valise.py::test_valise_en_html_injecte_la_variable_voyage -v`
Expected: FAIL (`assert 'const VOYAGE = ...' in html` → la chaîne n'est pas présente)

- [ ] **Step 3: Ajouter `import json` en tête de `valise.py`**

Première ligne du fichier, avant la docstring de module n'est pas possible (la docstring doit rester en premier) — donc juste après la docstring de module (après la ligne 7 `"""`), avant la définition de `HTML_STYLE` :

```python
"""Générateur de checklist de valise — adapté au type de destination, à la durée
et à la personne (Julien / Laetitia).

Application Python des concepts Exercism : dicts, listes, boucles, conditions.
On sépare les DONNÉES (les 3 tables ci-dessous, remplies une fois) de la LOGIQUE
(la fonction faire_valise). Démarrage minimal : on enrichit au fil des voyages.
"""
import json

# Feuille de style de la checklist HTML (mobile-first). Fournie clé en main :
```

- [ ] **Step 4: Modifier `valise_en_html` pour injecter la variable**

Dans la fonction `valise_en_html`, remplacer :

```python
{onglets}
{corps}
<script>{HTML_SCRIPT}</script>
</body>
</html>"""
    return page
```

par :

```python
{onglets}
{corps}
<script>const VOYAGE = {json.dumps(libelle_voyage)};</script>
<script>{HTML_SCRIPT}</script>
</body>
</html>"""
    return page
```

- [ ] **Step 5: Lancer les tests pour vérifier qu'ils passent**

Run: `cd voyage && .venv/bin/python3 -m pytest test_valise.py -v`
Expected: tous les tests passent (celui ajouté + les existants, inchangés)

- [ ] **Step 6: Commit**

```bash
cd /Users/julien/Claude/Work/perso/python/julien-python-journey
git add voyage/valise.py voyage/test_valise.py
git commit -m "feat: injecter la variable VOYAGE dans la page générée"
```

---

### Task 5: Basculer le JS de `localStorage` vers l'API (`HTML_SCRIPT`)

**Files:**
- Modify: `voyage/valise.py` (constante `HTML_SCRIPT`)

**Interfaces:**
- Consumes: variable globale `VOYAGE` injectée par Task 4 ; routes `/api/etat/<voyage>` et `/api/coche` de Task 3.
- Produces: aucune nouvelle fonction Python — ce changement est uniquement du JavaScript intégré dans la constante `HTML_SCRIPT`. Pas de test pytest possible ici (c'est du JS exécuté dans le navigateur) : vérification manuelle à l'étape 3.

Ce changement restructure l'initialisation : avant, `sauvegarde` était lu **de façon synchrone** depuis `localStorage` avant même que le DOM soit traité. Avec `fetch`, la lecture est **asynchrone** — tout ce qui dépendait de `sauvegarde` (restaurer les cases, brancher les boutons, activer le premier onglet) doit être déplacé dans une fonction `initialiser()` appelée seulement après la réponse du serveur.

- [ ] **Step 1: Remplacer tout le contenu de `HTML_SCRIPT`**

Remplacer la constante `HTML_SCRIPT` (de `HTML_SCRIPT = """` jusqu'au `"""` fermant) par :

```python
HTML_SCRIPT = """
// Références aux éléments de la page (tout en haut : dispo avant tout appel)
let sauvegarde = {};                                    // rempli après la réponse du serveur
const sections = document.querySelectorAll('section[data-owner]');
const onglets = document.querySelectorAll('nav.tabs button');
const compte = document.getElementById('compte');
const remplissage = document.getElementById('progress-fill');
const btnMasque = document.getElementById('toggle-masque');
const btnReset = document.getElementById('reset');
let ownerActif = null;                                  // la personne actuellement affichée
let masquer = false;                                    // masquer les objets déjà rangés ?

// Progression DE LA PERSONNE AFFICHÉE (compte ses cases à elle)
function majProgression() {
    const boxes = document.querySelectorAll('section[data-owner="' + ownerActif + '"] input[type=checkbox]');
    let faites = 0;
    boxes.forEach(function (b) { if (b.checked) faites++; });
    compte.textContent = faites + ' / ' + boxes.length;
    remplissage.style.width = boxes.length ? (faites / boxes.length * 100) + '%' : '0%';
}

// Compteur affiché sur chaque onglet (cochées / total de la personne)
function majOnglets() {
    onglets.forEach(function (b) {
        const boxes = document.querySelectorAll('section[data-owner="' + b.dataset.owner + '"] input[type=checkbox]');
        let faites = 0;
        boxes.forEach(function (x) { if (x.checked) faites++; });
        const span = b.querySelector('.tab-count');
        if (span) span.textContent = faites + '/' + boxes.length;
    });
}

// Masquer / réafficher les objets déjà cochés (+ les rayons devenus vides)
function appliquerMasque() {
    document.querySelectorAll('li').forEach(function (li) {
        const box = li.querySelector('input[type=checkbox]');
        if (box) li.style.display = (masquer && box.checked) ? 'none' : '';
    });
    document.querySelectorAll('section[data-owner] ul').forEach(function (ul) {
        const visible = Array.from(ul.querySelectorAll('li')).some(function (li) { return li.style.display !== 'none'; });
        ul.style.display = visible ? '' : 'none';
        const h3 = ul.previousElementSibling;         // le titre du rayon, juste avant la liste
        if (h3 && h3.tagName === 'H3') h3.style.display = visible ? '' : 'none';
    });
}

// Onglets : n'afficher qu'une personne à la fois
function activer(nom) {
    ownerActif = nom;
    sections.forEach(function (s) { s.style.display = (s.dataset.owner === nom) ? '' : 'none'; });
    onglets.forEach(function (b) { b.classList.toggle('actif', b.dataset.owner === nom); });
    majProgression();      // recompter pour la personne affichée
    appliquerMasque();
}

// Sauvegarde d'une seule case sur le serveur (jamais tout l'état -> pas d'écrasement croisé)
function sauverCoche(cle, coche) {
    fetch('/api/coche', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cle: cle, coche: coche })
    });
}

// Tout ce qui dépend de `sauvegarde` : à lancer seulement une fois l'état reçu du serveur
function initialiser() {
    document.querySelectorAll('input[type=checkbox]').forEach(function (box) {
        if (sauvegarde[box.dataset.key]) box.checked = true;
        box.addEventListener('change', function () {
            sauvegarde[box.dataset.key] = box.checked;
            sauverCoche(box.dataset.key, box.checked);
            majProgression();
            majOnglets();
            appliquerMasque();
        });
    });

    onglets.forEach(function (b) { b.addEventListener('click', function () { activer(b.dataset.owner); }); });
    btnMasque.addEventListener('click', function () {
        masquer = !masquer;
        btnMasque.textContent = masquer ? 'Afficher tout' : 'Masquer les rangés';
        appliquerMasque();
    });
    btnReset.addEventListener('click', function () {
        document.querySelectorAll('input[type=checkbox]').forEach(function (box) {
            box.checked = false;                 // on décoche visuellement
            delete sauvegarde[box.dataset.key];  // et on efface de la mémoire locale
            sauverCoche(box.dataset.key, false);  // et on sauve le décochage sur le serveur
        });
        majProgression();
        appliquerMasque();
    });

    if (onglets.length) activer(onglets[0].dataset.owner);
    majOnglets();
}

// Démarrage : on va chercher l'état de CE voyage sur le serveur, puis on initialise
fetch('/api/etat/' + encodeURIComponent(VOYAGE))
    .then(function (r) { return r.json(); })
    .then(function (data) {
        sauvegarde = data;
        initialiser();
    })
    .catch(function () {
        // Serveur éteint, Postgres down, ou téléphone hors du wifi du Mac
        document.body.insertAdjacentHTML('afterbegin',
            '<p style="background:#fee2e2;color:#991b1b;padding:.75rem 1rem;' +
            'border-radius:10px;margin-bottom:1rem;">Pas connecté au serveur — ' +
            'vérifie que le Mac est allumé et sur le même wifi.</p>');
    });
"""
```

- [ ] **Step 2: Régénérer la page et démarrer le serveur**

```bash
cd /Users/julien/Claude/Work/perso/python/julien-python-journey/voyage
.venv/bin/python3 valise.py
# répondre aux questions interactives (ex. Hanoï / 7 jours / mois 1 / fin / 2 / n)
.venv/bin/python3 serveur.py
```

- [ ] **Step 3: Vérification manuelle dans le navigateur (pas de test automatisé possible pour du JS)**

1. Ouvrir `http://localhost:5000/` dans un premier onglet du navigateur.
2. Cocher 2-3 cases.
3. Ouvrir `http://localhost:5000/` dans un **second** onglet (ou un autre navigateur, ou le Mac avec `http://<ip-locale-du-mac>:5000/` depuis un téléphone sur le même wifi).
4. Vérifier que les cases cochées à l'étape 2 apparaissent déjà cochées dans ce second onglet.
5. Cocher une case supplémentaire dans le second onglet, recharger le premier onglet, vérifier qu'elle apparaît cochée.
6. Cliquer "Réinitialiser" dans un onglet, recharger l'autre, vérifier que tout est décoché partout.

Expected: l'état est partagé entre les deux onglets/appareils après rechargement — c'est le critère de succès de toute la feature.

- [ ] **Step 4: Commit**

```bash
cd /Users/julien/Claude/Work/perso/python/julien-python-journey
git add voyage/valise.py
git commit -m "feat: remplacer localStorage par l'API serveur pour la sync multi-appareils"
```

---

### Task 6: Mettre à jour le README

**Files:**
- Modify: `voyage/README.md`

**Interfaces:**
- Consumes: rien.
- Produces: instructions à jour pour un nouvel utilisateur du projet (toi, dans 3 mois, qui a oublié le détail).

- [ ] **Step 1: Remplacer la section "Lancer le programme"**

Dans `voyage/README.md`, remplacer :

```markdown
## Lancer le programme

Depuis le dossier `voyage/` :

```bash
python3 valise.py
```

Assistant interactif : saisis les étapes une par une (destination, jours, mois),
puis qui fait sa valise et si tu conduis. Le programme écrit `valise.html` dans le
dossier — ouvre-le dans un navigateur.
```

par :

```markdown
## Lancer le programme

Pré-requis : Postgres doit tourner (`brew services start postgresql@15`) et les
bases `valise`/`valise_test` doivent exister (voir `schema.sql`).

Depuis le dossier `voyage/` :

```bash
.venv/bin/python3 valise.py
```

Assistant interactif : saisis les étapes une par une (destination, jours, mois),
puis qui fait sa valise et si tu conduis. Le programme écrit `valise.html` dans le
dossier.

Puis lance le serveur (à garder ouvert pendant que vous préparez vos valises) :

```bash
.venv/bin/python3 serveur.py
```

Ouvre `http://localhost:5000/` sur le Mac, ou `http://<ip-locale-du-mac>:5000/`
depuis un téléphone sur le même wifi. L'état des cases est partagé entre tous
les appareils qui ouvrent cette URL — ne plus ouvrir `valise.html` directement
(ça ne syncroniserait rien).
```

- [ ] **Step 2: Commit**

```bash
cd /Users/julien/Claude/Work/perso/python/julien-python-journey
git add voyage/README.md
git commit -m "docs: mettre à jour le README pour le flux serveur Postgres/Flask"
```
