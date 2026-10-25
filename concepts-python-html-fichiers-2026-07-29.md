---
titre: Python 03 — Écrire des fichiers, générer du HTML, garde-fous par sets
date: 2026-07-29
parcours: python
source: ~/Claude/Work/perso/python/julien-python-journey/voyage/valise.py
---

> **Ce que cette session débloque** : faire sortir un programme Python ailleurs que dans le terminal (un fichier HTML qu'on ouvre dans le navigateur), et se protéger des incohérences de données avec des opérations d'ensembles.

Contexte : projet `valise.py` (générateur de checklist de voyage). On est passé d'un affichage terminal à une page web cochable, et on a blindé la classification des objets.

---

## 1. Écrire dans un fichier

**Analogie** : jusqu'ici tu *lisais* des fichiers (le CSV Revolut). Là tu en *écris* un. Même objet, sens inverse.

```python
with open("valise.html", "w", encoding="utf-8") as f:
    f.write(page)
```

- `"w"` = **w**rite (écriture). Crée le fichier, ou l'écrase s'il existe.
- `f.write(texte)` = écrit une chaîne dans le fichier.
- `encoding="utf-8"` = obligatoire dès qu'il y a des accents (é, è...).

**`with` = un `finally` gratuit** : à la sortie du bloc, le fichier se ferme tout seul, même si ça plante. Tu n'as jamais à écrire `f.close()`.

**Où ça revient** : exporter un rapport, écrire un CSV de résultats, sauver un JSON d'API.

---

## 2. Le dossier courant (cwd) — LE piège

**La règle qui compte** : `open("valise.html", ...)` crée le fichier **là où tu lances la commande**, PAS là où le script est rangé.

Deux erreurs vécues, même cause :

```
# Lancé depuis /  (racine du Mac, protégée)
OSError: [Errno 30] Read-only file system: 'test.html'

# Lancé depuis la racine du repo, script dans voyage/
can't open file '.../valise.py': [Errno 2] No such file or directory
```

**Réflexe** : avant de lancer, se placer au bon endroit.
```bash
cd voyage          # descendre dans le dossier du script
python3 valise.py  # le .html se crée ICI
pwd                # "print working directory" = où suis-je ?
ls                 # ce qu'il y a autour
```

**Où ça revient** : partout. C'est la source n°1 des "fichier introuvable / permission refusée".

---

## 3. Générer du HTML depuis Python

**Analogie** : un fichier HTML, c'est **du texte avec des balises**, et le navigateur le transforme en page. Le HTML, c'est comme le Markdown mais avec des balises qui s'ouvrent ET se ferment :

| Markdown | HTML |
|---|---|
| `# Titre` | `<h1>Titre</h1>` |
| `- un item` | `<li>un item</li>` |

Une balise s'ouvre `<h1>` et se ferme `</h1>` (avec le `/`), le contenu est au milieu.

### Construire la page = accumuler du texte dans une boucle

**Analogie** : comme un total qui grossit, mais avec du texte. Partir d'une chaîne vide, coller un bout à chaque tour.

```python
corps = ""                                   # on part de vide
for objet in objets:
    corps = corps + f"<li>{objet}</li>"      # on colle un <li> à chaque tour
page = f"<h1>Ma valise</h1><ul>{corps}</ul>" # <ul> entoure tous les <li>
```

### Injecter une variable = f-string

Le `{ville}` dans une f-string est remplacé par la variable, comme dans tes `print(f"...")`. C'est ce qui rend la page **dynamique** (son contenu suit les données).

### Deux pièges de syntaxe

**Échappement `\"`** : pour mettre un guillemet DANS une chaîne déjà délimitée par des guillemets, on le fait précéder d'un `\` :
```python
f"<input type=\"checkbox\">"   # les \" font partie du texte, ne ferment pas la chaîne
```

**Accolades `{` `}` en f-string** : elles sont réservées (pour les variables). Du CSS est plein d'accolades → on le range dans une **constante à part** et on l'injecte via `{HTML_STYLE}`. La f-string ne voit alors pas les accolades internes du CSS.

**Où ça revient** : générer n'importe quel rapport lisible (HTML, Markdown, email formaté).

---

## 4. Lookup à fallback (le pattern "COALESCE")

**Analogie SQL** : `COALESCE(a, b, défaut)` — prends le premier qui répond.

Chercher dans une table, sinon dans une autre, sinon valeur par défaut :

```python
def zone_de(destination):
    if destination in VILLE_VERS_ZONE:
        return VILLE_VERS_ZONE[destination]   # trouvé côté villes
    if destination in PAYS_VERS_ZONE:
        return PAYS_VERS_ZONE[destination]    # sinon côté pays
    return None                               # sinon rien
```

Réutilisé 3 fois dans le projet (`zone_de`, `statut_ue`, `adaptateur_pour`). Un pattern, plusieurs usages.

**Où ça revient** : enrichir une donnée depuis plusieurs sources, avec une priorité.

---

## 5. Set difference comme garde-fou

**Le problème** : une table `THEMES` classe chaque objet dans un rayon. Si un objet oublié n'y figure pas, il tombe en silence dans "Divers". Dérive invisible.

**La parade** : rassembler tous les objets, soustraire ceux déjà classés. Ce qui reste = les oublis.

```python
tous = set(BASE_COMMUN) | set(VETEMENTS_BASE)   # | = union d'ensembles
for sous_table in PAR_TYPE_PERSO.values():
    tous |= set(sous_table)                     # |= = union en place
classes = set()
for objets in THEMES.values():
    classes |= objets
return tous - classes                           # - = différence : dans tous, pas dans classes
```

- `set(dict)` = l'ensemble des **clés** du dict.
- `A | B` union, `A - B` différence (les compétences de l'exo cater-waiter).
- Si le résultat n'est pas vide → un `⚠️` au lancement. Vide = tout est classé.

**Où ça revient** : contrôle de complétude / réconciliation (colonnes attendues vs présentes, IDs d'une table vs d'une autre — très AML).

---

## 6. Deux mécanismes de données propres

**Marqueur composé `(n, base)`** — un tuple qui veut dire "n fois la base" :
```python
def quantite_reelle(marqueur, jours):
    if isinstance(marqueur, tuple):          # est-ce un tuple ?
        nombre, base = marqueur              # dépaquetage : (3, "par_semaine")
        return nombre * quantite_reelle(base, jours)
    ...
# usage : "boucles d'oreille": (3, "par_semaine")  -> 3 paires / semaine
```
`isinstance(x, tuple)` teste le type. Le dépaquetage `nombre, base = marqueur` = ton tuple unpacking.

**Retirer avec `pop`** — convention "quantité 0 = on retire l'objet" :
```python
rayon.pop(objet, None)   # retire objet s'il est là, sinon ne fait rien (grâce au None)
```
`dict.pop(clé, défaut)` : le 2e argument évite le plantage si la clé n'existe pas.

**Où ça revient** : nettoyer/normaliser un dict de données avant traitement.

---

## Bugs typiques rencontrés

| Bug | Faux | Correct |
|---|---|---|
| `in` sur une fonction | `if ville in zone_de` | `if zone_de(ville) is not None` — une fonction s'**appelle** avec `()`, `in` cherche dans un **contenant** (dict/liste/set) |
| cwd | lancer depuis `/` ou la racine du repo | `cd` dans le bon dossier d'abord |
| Dérive de classification | `chemises` oublié dans `THEMES` → planqué dans "Divers" | garde-fou set-difference qui le signale |
| Item genré partagé | `robe légère` ajoutée à tout le monde via table partagée | filtre `JAMAIS["Julien"]` qui retire après coup |

---

## À retenir pour la suite

- **Solide** : écrire un fichier, générer du HTML par accumulation, f-strings, sets (union/différence), lookup fallback. Tu as produit toi-même le pont Python→HTML.
- **Encore neuf** : le JS côté navigateur (state/render, localStorage) — vu en lecture sur une maquette Design, pas encore écrit. Prochaine étape possible : rendre la page interactive (onglets, barre de progression, persistance des coches) en JS vanilla.
- **Méthode qui a marché** : quand j'ai empilé CSS + génération + fichier d'un coup, blocage net ("aucune idée de quoi faire"). Le redémarrage brique par brique dans un bac à sable (`test.html`) a tout débloqué. → Voir [[style-apprentissage-code]] règle 1.
