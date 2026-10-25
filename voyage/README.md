# Valise — générateur de checklist de voyage

Programme Python qui construit une checklist de valise adaptée à un **itinéraire**
(une ou plusieurs étapes), à la durée et aux personnes (Julien / Laetitia). Il
déduit le climat de chaque destination, dimensionne les quantités et produit une
page HTML cochable (persistance des coches dans le navigateur).

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

Exemple de saisie (Vietnam + Cambodge, 18 jours en janvier) :

```
Étape 1 — destination (ou 'fin' pour terminer) : hanoi
        📍 1. Hanoï — Hanoï, Viêt Nam
        📍 2. Hanoi — Hautes-Terres méridionales, Papouasie-Nouvelle-Guinée
        — lequel ? (Entrée = 1) :
        — jours : 7
        — mois (1-12 ou janvier, févr…) : janv
        — activités ? (v)ille (p)lage (m)ontagne, combinables : v
        🌡️ Hanoï · janvier : 14–21 °C · 🌧️ 10 j de pluie/mois
Étape 2 — destination : siem reap   / jours : 4 / mois : Entrée (= janvier) / activités : v
Étape 3 — destination : phu quoc    / jours : 7 / mois : Entrée (= janvier) / activités : p v
Étape 4 — destination : fin
Qui fait sa valise ? (j / l / 2) : 2
Tu vas conduire ? (o/n) : n
```

## Lancer les tests

```bash
.venv/bin/python3 -m pytest test_valise.py -v
```

Les tests couvrent les fonctions pures (agrégation d'itinéraire, statut UE, prises)
et la règle d'accumulation des quantités (max entre climats, suppression par 0).

`test_db.py` et `test_serveur.py` nécessitent en plus Postgres actif et la base
`valise_test` créée (voir `schema.sql` et la section "Lancer le programme") :

```bash
.venv/bin/python3 -m pytest test_db.py test_serveur.py -v
```

## Structure

| Fichier | Rôle |
|---------|------|
| `valise.py` | Programme complet : données (tables), logique, génération HTML, CLI |
| `test_valise.py` | Tests pytest des fonctions pures et de la règle d'accumulation |
| `valise.html` | Sortie générée (checklist cochable) — régénérée à chaque lancement |
| `db.py` | Accès Postgres à l'état de la checklist (coché / pas coché) |
| `test_db.py` | Tests pytest de `db.py` (contre une vraie base Postgres de test) |
| `serveur.py` | Serveur Flask : sert la page et expose l'API de lecture/écriture de l'état |
| `test_serveur.py` | Tests pytest de `serveur.py` (via `app.test_client()`) |
| `schema.sql` | Schéma Postgres (tables `etat_case` et `normales_climat`, le cache climat) |

## Idée d'architecture

Les **données** (tables `BASE_*`, `PAR_TYPE_*`, `PAYS_*`, `THEMES`…) sont
séparées de la **logique** (fonctions). On enrichit les tables au fil des voyages
sans toucher au code. Les types d'une étape viennent de deux sources :
- **climat** (`chaud` / `froid` / `pluie`) : déduit des normales réelles sur 10 ans
  (`api_climat.py`, Open-Meteo, gratuit sans clé) via les seuils `SEUIL_*` ;
- **activités** (`ville` / `plage` / `montagne`) : saisies par étape.
Les normales sont mises en **cache** dans Postgres (`normales_climat`) : un appel API
remplit les 12 mois d'un lieu, les lancements suivants relisent la base. Postgres éteint
-> appel direct à l'API, sans cache (rien ne plante).
Toute ville trouvée par le géocodage Open-Meteo est acceptée, sans souci de majuscules
ni d'accents ; en cas d'homonymes
(Bali Inde / Indonésie), le programme liste les lieux et on choisit. Le pays du lieu
choisi (code ISO : `VN`, `GB`…) pilote les papiers (`SANS_PASSEPORT`) et l'adaptateur
(`PAYS_VERS_PRISE`).
