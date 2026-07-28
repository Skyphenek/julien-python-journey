# Design — sortie HTML cochable pour valise.py

## Problème

`voyage/valise.py` imprime la checklist dans le terminal. Inutilisable pour
faire réellement son sac : rien à cocher, pas consultable sur le téléphone
pendant qu'on remplit la valise. Objectif : que `valise.py` génère, en plus,
un fichier `valise.html` — une page cochable qu'on ouvre sur son mobile et où
on barre chaque objet au fur et à mesure.

## Partage du travail (validé)

- **Julien écrit** le pont Python → HTML : la fonction qui construit la chaîne
  HTML à partir de la structure `valise` (mêmes boucles imbriquées que le
  `print` actuel), et l'écriture dans un fichier. C'est l'apprentissage
  (f-strings, écriture fichier, réutilisation des boucles).
- **Claude fournit** le CSS/ergonomie (mobile-first, checkboxes, responsive) —
  zone d'augmentation IA, pas d'apprentissage brut de CSS ici.

## Décisions validées

- **Interactivité** : checkboxes HTML natives (`<input type="checkbox">`). Un
  objet coché se barre + se grise. **Zéro JS** dans la version de base.
- **Hiérarchie visuelle** : par **personne** (Partagé / Julien / Laetitia) puis
  par **thème** (Vêtements / Hygiène / Divers / Documents). Reprend exactement
  la structure de données existante — aucun remaniement.
- **Support** : **mobile d'abord**. Une seule colonne, gros touch targets,
  responsive. Pas de feuille print dédiée dans la v1.
- **Fichier auto-suffisant** : le CSS est inline (`<style>` dans le `<head>`),
  un seul fichier `.html` portable (AirDrop / envoi sur le tél sans dépendance).
  `<meta charset="utf-8">` obligatoire (accents dans les noms d'objets).

## Architecture

Le moteur Python (`faire_valise`, tables géo, `zone_de`) reste **inchangé**.
On ajoute une **couche de rendu** au-dessus, qui consomme la structure `valise`
déjà produite (`{propriétaire: {thème: {objet: quantité}}}`).

### Constante `HTML_STYLE` (fournie par Claude)

Un bloc `<style>` mobile-first stocké en constante string en haut du fichier.
Injecté tel quel dans le `<head>`. Julien n'a pas à l'écrire ni le comprendre
ligne à ligne — c'est la partie augmentée.

### Fonction `valise_en_html(valise, ville, jours, types)` (écrite par Julien)

Construit et renvoie une **chaîne HTML complète** :
- squelette : `<!doctype html>`, `<head>` avec charset + `HTML_STYLE`, `<body>`
- un en-tête : destination, nb de jours, types de destination
- pour chaque `propriétaire` → une carte `<section>` avec son nom en titre
- dans chaque carte, pour chaque `thème` non vide → un sous-titre + une `<ul>`
- pour chaque `objet, quantité` → un `<li>` avec `<label><input type="checkbox"> objet ×quantité</label>`

Réutilise **la même triple boucle** que le `print` de `main` (lignes 313-320
actuelles), en produisant des balises au lieu de texte. Skip des thèmes vides
identique à aujourd'hui (`if not objets: continue`).

### Écriture fichier dans `main` (écrite par Julien)

Après `faire_valise`, `main` :
1. appelle `valise_en_html(...)` pour obtenir la chaîne
2. l'écrit dans `voyage/valise.html` (`open(..., "w", encoding="utf-8")`)
3. imprime une confirmation : `Checklist écrite dans valise.html`

Le fichier est **écrasé à chaque run** (une seule valise courante à la fois —
suffisant pour l'usage perso). L'affichage terminal actuel peut rester en
complément (debug), ou être remplacé par la confirmation — au choix à
l'implémentation, sans impact sur le reste.

## Découpage en briques (coaching)

1. **Squelette** : `valise_en_html` renvoie une page HTML minimale (doctype +
   head avec `HTML_STYLE` + body vide) ; `main` l'écrit dans le fichier. But :
   voir la page s'ouvrir dans le navigateur, valider le pont fichier.
2. **Remplissage** : les boucles imbriquées qui génèrent cartes / sous-titres /
   `<li>` cochables. Réutilise la boucle du `print`.
3. **Câblage `main`** : confirmation + (option) retrait du dump terminal.

## Tests / validation manuelle

- lancer avec un cas 2 personnes (ex. Thaïlande, 10 jours, les deux) → un
  `valise.html` s'ouvre dans le navigateur, 3 cartes (Partagé/Julien/Laetitia)
- cocher un objet sur mobile → il se barre et se grise
- thème vide non affiché (ex. pas de Documents si ni passeport ni CNI... —
  ici il y en a toujours un, vérifier sur un thème réellement vide)
- accents corrects (é, è) → charset OK

## Hors scope (v1)

- **Persistance des coches** (survivre à un reload) : nécessite un peu de JS +
  `localStorage`. Polish optionnel, ajoutable ensuite si l'usage le demande.
- **Compteur de progression** ("12/34 cochés") : nécessite du JS. Plus tard.
- **Feuille print A4** : non demandé en v1 (mobile d'abord).
- **Multi-valises / historique** : le fichier est écrasé à chaque run.
