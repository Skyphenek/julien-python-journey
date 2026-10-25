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
Étape 1 — destination (ou 'fin' pour terminer) : Hanoï
        — jours : 7
        — mois (1-12) : 1
Étape 2 — destination : Siem Reap   / jours : 4 / mois : 1
Étape 3 — destination : Phu Quoc    / jours : 7 / mois : 1
Étape 4 — destination : fin
Qui fait sa valise ? (j / l / 2) : 2
Tu vas conduire ? (o/n) : n
```

## Lancer les tests

```bash
python3 -m pytest test_valise.py -v
```

Les tests couvrent les fonctions pures (agrégation d'itinéraire, statut UE, prises)
et la règle d'accumulation des quantités (max entre climats, suppression par 0).

Prérequis : `pytest` (`python3 -m pip install pytest` si absent).

## Structure

| Fichier | Rôle |
|---------|------|
| `valise.py` | Programme complet : données (tables), logique, génération HTML, CLI |
| `test_valise.py` | Tests pytest des fonctions pures et de la règle d'accumulation |
| `valise.html` | Sortie générée (checklist cochable) — régénérée à chaque lancement |

## Idée d'architecture

Les **données** (tables `BASE_*`, `PAR_TYPE_*`, `ZONES`, `PAYS_*`, `THEMES`…) sont
séparées de la **logique** (fonctions). On enrichit les tables au fil des voyages
sans toucher au code. Le climat est déduit en deux temps : destination → zone
climatique → types de destination selon la saison.
