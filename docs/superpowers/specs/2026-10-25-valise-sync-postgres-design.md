# Design — Sync multi-appareils de valise.py via Postgres + Flask

## Contexte et objectif

`valise.py` génère une checklist de valise en HTML. L'état coché/pas-coché de
chaque case est aujourd'hui stocké en `localStorage` du navigateur — propre à
un appareil, invisible de l'autre. Julien et Laetitia préparent leurs valises
chacun sur son téléphone, sans voir la progression de l'autre.

**Objectif double** :
- Pédagogique : apprendre à connecter Python à Postgres et à exposer cette
  donnée via une petite API web (pattern transférable au monde pro).
- Pratique : synchroniser l'état des cases entre les deux téléphones quand ils
  sont sur le même wifi (maison), sans besoin d'accès depuis l'extérieur.

**Hors scope** : accès depuis l'extérieur du réseau local, mise à jour en
temps réel sans rafraîchir (un rechargement de page suffit), authentification
(réseau domestique de confiance), migration des anciennes données
`localStorage` existantes (nouvel usage, base vide au départ), table séparée
pour les items/thèmes (ils restent calculés dynamiquement par `valise.py`).

## Architecture

```
┌─────────────┐         ┌─────────────┐         ┌──────────────┐
│ Tél. Julien │  HTTP   │   Flask     │  SQL    │  PostgreSQL  │
│ (navigateur)│ ───────▶│  serveur.py │ ───────▶│  valise DB   │
└─────────────┘         │  (Mac)      │         └──────────────┘
┌─────────────┐  HTTP   │             │
│Tél. Laetitia│ ───────▶│             │
└─────────────┘         └─────────────┘
```

- `valise.py` ne change pas de rôle : génère les items/thèmes/quantités à
  partir des tables Python existantes (logique métier pure, aucune dépendance
  à la DB).
- Nouveau fichier `voyage/serveur.py` : serveur Flask tournant sur le Mac de
  Julien, écoutant sur le réseau local (`0.0.0.0:5000`). Sert la page HTML
  générée et expose l'API de lecture/écriture de l'état des cases.
- PostgreSQL stocke uniquement l'état coché/pas-coché, pas les items eux-mêmes.
- Les deux téléphones doivent être sur le même wifi que le Mac et ouvrir
  `http://<ip-locale-du-mac>:5000`. Ouvrir le fichier `.html` directement
  (double-clic Finder) ne fonctionnera plus — les appels `fetch` échoueraient
  sous `file://`.

## Modèle de données

Une seule table, reflet direct de la clé composite déjà utilisée côté JS
(`voyage/proprietaire/theme/objet`) :

```sql
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

- Pas de table pour les items/thèmes : ils n'ont pas d'existence stable, ils
  sont recalculés à chaque génération selon climat/durée/personnes. La DB ne
  connaît que "cette clé est cochée ou pas".
- `maj_le` donne un bonus quasi gratuit : l'historique des voyages passés via
  `SELECT DISTINCT voyage FROM etat_case`, sans table dédiée.
- La clé primaire composite permet un upsert naturel
  (`INSERT ... ON CONFLICT (...) DO UPDATE`) à chaque coche, sans risque de
  doublon.

## API (Flask — `serveur.py`)

| Méthode | Route | Rôle |
|---|---|---|
| `GET` | `/` | Sert la page HTML générée par `valise.py` |
| `GET` | `/api/etat/<voyage>` | Renvoie `{ "voyage/perso/theme/objet": true/false, ... }` pour ce voyage |
| `POST` | `/api/coche` | Body `{ "cle": "voyage/perso/theme/objet", "coche": true }` → upsert d'une seule ligne |

**Pourquoi un upsert par case plutôt que remplacer l'état entier** : si on
renvoyait l'objet complet à chaque coche (comme le faisait `localStorage`), le
téléphone de Julien pourrait écraser une coche que Laetitia vient de faire
quelques secondes avant — il aurait chargé son état avant son clic à elle, et
renverrait ensuite son état complet désormais périmé. En écrivant une seule
clé à la fois, ce risque disparaît : chacun ne modifie que ce qu'il touche.

Erreurs :
- Payload invalide sur `/api/coche` → 400, pas de crash serveur.
- Postgres non démarré → 500 côté serveur ; pas de gestion spécifique côté
  client, c'est un problème de démarrage à résoudre avant la session (lancer
  `brew services start postgresql@15`).

## Changements côté client (JS dans `valise.html`)

Le JS actuel (`HTML_SCRIPT` dans `valise.py`) utilise `localStorage` à deux
endroits : lecture au démarrage, écriture à chaque coche. Seuls ces deux
points changent, le reste (onglets, progression, masquage) ne bouge pas.

Lecture au démarrage — remplace `JSON.parse(localStorage.getItem(CLE) || "{}")` :
```js
let sauvegarde = {};
fetch(`/api/etat/${VOYAGE}`)
    .then(r => r.json())
    .then(data => {
        sauvegarde = data;
        // appliquer l'état reçu aux checkboxes avant majOnglets()/majProgression()
    });
```

Écriture à chaque coche — remplace `localStorage.setItem(CLE, JSON.stringify(sauvegarde))` :
```js
fetch('/api/coche', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ cle: cleCoche, coche: box.checked })
});
```

- `VOYAGE` : variable injectée par `valise.py` dans le HTML généré (le
  libellé du voyage existe déjà, utilisé dans les `data-key`).
- L'application de l'état reçu aux checkboxes doit se faire juste après le
  `fetch` initial, avant les premiers appels à `majOnglets()` /
  `majProgression()`.

## Gestion d'erreurs / cas limites — réseau

- Serveur Flask éteint ou téléphone hors wifi : le `fetch` initial échoue →
  afficher un message simple en haut de page ("Pas connecté au serveur —
  vérifie que le Mac est allumé et sur le même wifi"). Pas de retry
  automatique, pas de mode offline : hors scope pour un usage ponctuel avant
  un voyage.
- Ancien fichier `.html` ouvert directement : à bannir une fois la migration
  faite — toujours passer par `http://<ip-mac>:5000/`.

## Tests

`test_valise.py` existant (pytest, logique pure, pas de DB) reste inchangé.
Nouveau fichier `voyage/test_serveur.py` :

- Fixture pytest connectée à une base de test dédiée (`valise_test`, créée une
  fois via `createdb valise_test`), qui vide `etat_case` (`TRUNCATE`) avant
  chaque test.
- `app.test_client()` de Flask pour appeler les routes sans vrai réseau.
- Cas couverts :
  - `GET /api/etat/<voyage>` sur base vide → `{}`.
  - `POST /api/coche` puis `GET /api/etat/<voyage>` → l'état posté est bien
    renvoyé.
  - Upsert : poster deux fois la même clé → une seule ligne en base, dernière
    valeur gagne.
- Pas de mock de `psycopg2` : tester contre une vraie base de test est plus
  simple et plus fidèle que mocker le driver.

## Dépendances nouvelles

- `flask` (serveur web)
- `psycopg2-binary` (driver Postgres)

Les deux à ajouter à l'environnement virtuel du projet (`voyage/` a déjà un
`.venv` avec `requests`/`dotenv` d'après la session API).
