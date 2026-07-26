# Référence Python — fonctions, boucles & pièges (session 2026-07-21)

Fiche de référence exhaustive construite pendant les exercices Exercism **making-the-grade** (loops), **card-games** (blackjack), **currency-exchange**, **ghost-gobble** (Pac-Man), **meltdown-mitigation** (nuclear), **card-tricks** (strings/prefixes).

**Comment lire cette fiche** : chaque entrée = à quoi ça sert + syntaxe + exemple + le piège qui m'a fait tomber. Rédigée pour être relue vite avant un exercice.

---

## SOMMAIRE

1. [Fonctions vs méthodes](#1-fonctions-vs-méthodes--la-distinction-qui-revient-tout-le-temps)
2. [Les fonctions built-in](#2-les-fonctions-built-in)
3. [Les méthodes de string](#3-les-méthodes-de-string)
4. [Les méthodes de liste](#4-les-méthodes-de-liste)
5. [La boucle `for`](#5-la-boucle-for)
6. [`range()`](#6-range)
7. [`range(len())` et `enumerate()`](#7-rangelen-et-enumerate)
8. [Les f-strings](#8-les-f-strings)
9. [Conditions `if / elif / else`](#9-conditions-if--elif--else)
10. [Opérateurs logiques `and / or / not`](#10-opérateurs-logiques-and--or--not)
11. [Le placement du `return`](#11-le-placement-du-return--le-piège-le-plus-fréquent)
12. [Listes de listes](#12-listes-de-listes-imbrication)
13. [Le squelette universel des exos sur listes](#13-le-squelette-universel-des-exos-sur-listes)
14. [Catalogue des erreurs rencontrées](#14-catalogue-des-erreurs-rencontrées)
15. [Les avis Pylint](#15-les-avis-pylint-style-pas-bug)

---

## 1. Fonctions vs méthodes — LA distinction qui revient tout le temps

C'est la source n°1 de mes erreurs. Deux familles d'outils, deux syntaxes.

| | **Fonction** | **Méthode** |
|---|---|---|
| Forme | `nom(objet)` | `objet.nom()` |
| Position | le nom **devant**, l'objet **dedans** | l'objet **devant**, un point, le nom |
| Exemples | `round(x)`, `int(x)`, `len(liste)` | `"txt".title()`, `liste.append(x)` |

```python
round(90.5)        # fonction : nom devant, objet dans les parenthèses
"hello".title()    # méthode : objet devant, collée après un point
```

**Piège vécu** : `title.title` (sans parenthèses) → renvoie l'objet-méthode lui-même, pas le résultat. Toujours les `()`.
**Piège vécu** : `90.5.round()` → n'existe pas, `round` est une fonction, pas une méthode.

---

## 2. Les fonctions built-in

Toutes en `nom(argument)`.

### `round()` — arrondir au plus proche
```python
round(90.5)   # 90 ou 91 (arrondi "bancaire" : .5 va vers le pair le plus proche)
round(77.8)   # 78
```

### `int()` — convertir/tronquer en entier
```python
int(15.9)     # 15  (TRONQUE, ne pas confondre avec round : n'arrondit pas, coupe la partie décimale)
int("42")     # 42  (convertit une string en entier)
```

### `float()` — convertir en décimal
```python
float("3.14") # 3.14
float(5)      # 5.0
```

### `len()` — taille d'une liste ou d'une string
```python
len([10, 20, 30])   # 3
len("abc")          # 3
```

**Conseil senior** : `int()` tronque, `round()` arrondit. `int(15.9)` = 15, `round(15.9)` = 16. Ne jamais utiliser `int()` en croyant arrondir.

---

## 3. Les méthodes de string

Toutes en `"texte".nom()`.

### `.title()` — première lettre de chaque mot en majuscule
```python
"the great gatsby".title()   # 'The Great Gatsby'
```

### `.strip()` — enlève les espaces (ou autres) aux deux bouts
```python
"  bonjour  ".strip()        # 'bonjour'
"black.".strip('.,!?;:')     # 'black'  (enlève la ponctuation aux extrémités)
```

### `.split()` — découpe une phrase en liste de mots
```python
"It got dark".split()        # ['It', 'got', 'dark']  (coupe à chaque espace)
```

### `.replace()` — remplace un bout de texte par un autre
```python
"j'aime le thé".replace("thé", "café")   # "j'aime le café"
```

### `.endswith()` / `.startswith()` — teste le début/la fin (renvoie un bool)
```python
"phrase.".endswith('.')      # True
"heaviness".endswith('ness') # True
```

**Conseil senior** : les méthodes de string ne modifient jamais l'original (les strings sont immuables) — elles renvoient une **nouvelle** string. Il faut donc `return`/réassigner le résultat, jamais juste l'appeler dans le vide.

---

## 4. Les méthodes de liste

### `.append(x)` — ajoute UN élément à la fin
```python
resultat = []
resultat.append(41)          # resultat vaut maintenant [41]
resultat.append(56)          # [41, 56]
```

**Piège vécu** : `.append()` prend **exactement un argument**. `resultat.append(nom, 100)` → `TypeError`. Pour ajouter une paire, on ajoute une liste : `resultat.append([nom, 100])`.

### `.join()` — colle une liste de strings en une seule string (c'est une méthode de string, pas de liste !)
```python
" :: ".join(['en', 'enclose', 'enjoy'])   # 'en :: enclose :: enjoy'
```
Le séparateur est **devant** (`" :: "`), la liste **dedans**. Ne marche qu'avec des strings.

---

## 5. La boucle `for`

Visite chaque élément d'une liste, un par un.

```python
notes = [90.5, 40.2, 77.8]
for note in notes:
    print(note)     # affiche 90.5 puis 40.2 puis 77.8
```

- `for` et `in` = mots-clés fixes
- `note` = nom **que je choisis**, existe seulement pendant la boucle. Pas besoin de le définir avant : le `for` fait l'affectation tout seul à chaque tour.
- Le `:` en fin de ligne est **obligatoire**, le bloc est indenté dessous.

**Piège vécu** : nommer la variable de boucle comme la liste résultat. `resultat = []` puis `for resultat in ...` → écrase la liste. Toujours un nom **singulier** pour la boucle (`note`), **pluriel** pour la liste (`notes`).

---

## 6. `range()`

Génère une séquence de nombres sans les écrire à la main.

```python
range(fin)                # de 0 à fin-1
range(debut, fin)         # de debut à fin-1
range(debut, fin, pas)    # de debut à fin-1, en avançant de "pas"
```

**Règle d'or** : la borne de fin n'est **jamais incluse** (on s'arrête AVANT).

```python
for x in range(4):          # 0, 1, 2, 3         (4 valeurs, pile ce qu'il faut pour boucler N fois)
for x in range(2, 10, 3):   # 2, 5, 8            (s'arrête avant 10)
```

**Conseil senior — le piège de la borne mobile** : pour générer un nombre FIXE de valeurs (ex : 4 tranches de notes), n'utilise PAS `range(debut, borne, pas)` en espérant tomber pile — les arrondis du `pas` peuvent générer une valeur en trop. Utilise `range(4)` (nombre de tours garanti) et calcule chaque valeur à l'intérieur :

```python
# FRAGILE — peut générer 5 valeurs au lieu de 4 selon l'arrondi du pas :
for note in range(41, highest+1, (highest-40)//4):

# ROBUSTE — exactement 4 valeurs, toujours :
pas = (highest - 40) // 4
for tranche in range(4):
    seuil = 41 + tranche * pas    # formule "point de départ + i × pas"
```

**Formule à retenir** : `valeur_de_départ + position * pas`. À la position 0 → départ. Position 1 → départ + pas. Position 2 → départ + 2×pas. Etc.

---

## 7. `range(len())` et `enumerate()`

### `range(len(liste))` — boucler par INDICE (position)
Utile pour lire **deux listes en parallèle** avec le même numéro de position.

```python
for position in range(len(noms)):
    nom = noms[position]
    note = notes[position]        # même indice → même ligne dans les deux listes
```
`noms[position]` : les crochets acceptent une variable comme indice, pas seulement un nombre fixe.

### `enumerate()` — la version propre de `range(len())`
Donne **la position ET l'élément** en même temps, en une paire.

```python
for position, nom in enumerate(noms):
    note = notes[position]        # position toujours dispo pour l'autre liste
```

**Conseil senior** : dès que tu écris `for i in range(len(x)):` et que tu fais `x[i]` juste après, remplace par `enumerate()` — c'est l'idiome Python (Pylint le réclame, cf. C0200). `enumerate` te donne l'élément directement, plus besoin de `x[i]`.

---

## 8. Les f-strings

Insérer des variables dans du texte sans coller des bouts avec `+`.

```python
prenom = "Julien"
age = 43
f"Je m'appelle {prenom} et j'ai {age} ans."   # "Je m'appelle Julien et j'ai 43 ans."
```

- Un `f` **juste avant** les guillemets.
- Les variables entre **accolades** `{}` à l'intérieur du texte.

```python
f"{rang}. {nom}: {note}"    # "1. Betty: 90"
```

**Conseil senior** : les f-strings remplacent avantageusement `str(rang) + ". " + nom + ": " + str(note)`. Plus lisible, pas besoin de convertir les nombres en string manuellement.

---

## 9. Conditions `if / elif / else`

```python
if note <= 40:
    return 'échec'
elif note < 60:
    return 'moyen'
else:
    return 'bien'
```

- `:` obligatoire en fin de chaque ligne `if`/`elif`/`else`.
- `elif` = "sinon si", testé seulement si les conditions précédentes sont fausses.
- Comparateurs : `==` (égal), `!=` (différent), `<`, `<=`, `>`, `>=`.

**Piège vécu** : confondre `<` (strict) et `<=` (inclusif). "less than 800" = `< 800`, "at or below 40" = `<= 40`. Lire le libellé précisément.
**Piège vécu** : `if condition` sans `:` → `SyntaxError`, le fichier ne se charge même pas.

---

## 10. Opérateurs logiques `and / or / not`

```python
a and b     # vrai seulement si a ET b sont vrais
a or b      # vrai si au moins un des deux est vrai
not a       # inverse : True devient False
```

**Piège vécu (Pac-Man)** : `score` = touche une pellet **OU** un dot → `or`, pas `and`. Utiliser `and` exigeait les deux à la fois → faux.

**Piège vécu (`higher_card`)** : `return card_one and card_two` ne renvoie PAS un tuple. `and` entre deux valeurs "vraies" renvoie juste la **seconde**. Pour un vrai tuple : `return card_one, card_two`.

**Astuce senior** : un booléen vaut 1 ou 0 dans un calcul. `10 * (card == 'A')` ajoute 10 si vrai, 0 si faux — pratique pour éviter un `if`.

---

## 11. Le placement du `return` — le piège le plus fréquent

`return` **arrête immédiatement** toute la fonction, où qu'on soit.

### Cas A : compter/accumuler sur TOUTE la liste → `return` APRÈS la boucle
```python
def count_failed(notes):
    compteur = 0
    for note in notes:
        if note <= 40:
            compteur += 1
    return compteur          # aligné avec 'for', hors de la boucle
```
Si le `return` était dans la boucle (aligné avec le `if`), il sortirait dès le 1er élément → compte faux.

### Cas B : trouver le PREMIER élément → `return` DANS le `if`
```python
def perfect_score(eleves):
    for eleve in eleves:
        if eleve[1] == 100:
            return [eleve[0], 100]   # trouvé → on sort tout de suite
    return []                        # rien trouvé → liste vide, après la boucle
```

**La règle** : "sur tous les éléments" → return après la boucle. "le premier qui..." → return dans le if. C'est l'indentation qui décide.

**Piège vécu (Pylint R1710)** : si certains chemins renvoient une valeur et d'autres rien (fin de fonction sans `return`), Python renvoie `None` en douce. Toujours un `return` explicite sur **tous** les chemins.

---

## 12. Listes de listes (imbrication)

Une liste peut contenir d'autres listes.

```python
eleves = [['Charles', 90], ['Tony', 80], ['Alex', 100]]
eleves[0]        # ['Charles', 90]   (le premier sous-liste entière)
eleves[0][0]     # 'Charles'         (dans la sous-liste, 1er élément)
eleves[0][1]     # 90                (dans la sous-liste, 2e élément)
```

En boucle :
```python
for eleve in eleves:
    nom = eleve[0]
    note = eleve[1]
```

**Piège vécu (`perfect_score`)** : `resultat.append([nom, 100])` puis `return resultat` → renvoie `[['Alex', 100]]` (couche d'emballage en trop). Le docstring voulait `['Alex', 100]` directement → `return [nom, 100]` sans passer par `.append()`.

---

## 13. Le squelette universel des exos sur listes

90 % des exos de boucles suivent ce moule :

```python
def ma_fonction(liste_entree):
    resultat = []                    # 1. accumulateur vide (ou compteur = 0)
    for element in liste_entree:     # 2. boucle sur l'entrée
        if condition:                # 3. filtre (optionnel)
            resultat.append(...)     # 4. transforme + ajoute (ou compteur += 1)
    return resultat                  # 5. return APRÈS la boucle
```

- **Construire une liste** → `resultat = []` + `.append()`
- **Compter** → `compteur = 0` + `compteur += 1`
- **Filtrer** → un `if` dans la boucle
- **Transformer** → appliquer une opération avant d'`append`

---

## 14. Catalogue des erreurs rencontrées

Toutes celles qui ont fait planter ou échouer un test aujourd'hui.

| Erreur | Symptôme | Cause | Fix |
|---|---|---|---|
| Espaces dans un nom de variable | `SyntaxError` | `generated power = ...` | underscores : `generated_power` |
| `:` manquant après `if`/`for` | `SyntaxError` | `if x > 0` | `if x > 0:` |
| Corps de fonction vide | `IndentationError` | rien sous le `def` | mettre du code ou `pass` |
| Faute de frappe mot-clé | `retun` → `NameError` | typo | `return` |
| Faute de frappe nom variable | `resulat` → `NameError` | typo | vérifier l'orthographe |
| Appeler une méthode sans `()` | renvoie l'objet-méthode | `title.title` | `title.title()` |
| Comparer strings au lieu de valeurs | `'10' < '9'` → True (faux !) | comparaison alphabétique | convertir en `int` d'abord |
| Concaténer au lieu d'additionner | `'5' + '6'` = `'56'` | `+` sur strings colle | `int('5') + int('6')` |
| Mélanger types dans `in` | `9 in ('9','10')` → False | int vs str | aligner : `9 in (9, 10)` |
| `return` mal indenté | boucle sort trop tôt | dans le `if` au lieu d'après | désindenter au niveau du `for` |
| `range` borne mobile | 1 valeur en trop | arrondi du pas | `range(N)` + calcul interne |
| Couche de liste en trop | `[['x',100]]` | `.append` d'une liste dans une liste | `return [x, 100]` direct |
| Écraser le paramètre | `TypeError` plus loin | `highest = []` sur le param | nom différent pour le résultat |

---

## 15. Les avis Pylint (style, pas bug)

Pylint ne casse pas le code, il signale des entorses aux conventions. Ceux vus aujourd'hui :

### R6201 `use-set-for-membership`
Test d'appartenance `in` sur un **tuple** → préférer un **set** (`{}`), plus rapide.
```python
if card in ('J','Q','K'):    # ce que Pylint pointe
if card in {'J','Q','K'}:    # ce qu'il préfère (accolades)
```

### R1710 `inconsistent-return-statements`
Certains chemins renvoient une valeur, d'autres non (→ `None` implicite). Ajouter un `return` explicite partout.

### C0104 `disallowed-name`
Nom trop peu descriptif interdit (`i`, `l`, `foo`...). Renommer en parlant : `i` → `tranche`, `position`.

### C0200 `consider-using-enumerate`
`for i in range(len(x))` suivi de `x[i]` → utiliser `enumerate(x)`.

**Conseil senior** : les avis Pylint sont des réflexes de lisibilité à prendre tôt. Le code marche sans, mais un nom clair et l'idiome standard (`enumerate`, set pour l'appartenance) te feront gagner du temps quand tu reliras ton code dans 3 mois.

---

*Fiche créée le 2026-07-21 — exercices Exercism : making-the-grade, blackjack, currency-exchange, ghost-gobble, meltdown-mitigation, card-tricks.*
