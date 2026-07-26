# Python — cheatsheet complète débutant

Fiche unique de référence pour tout ce qui tient dans les 3 premiers mois. Ordre = celui dans lequel tu vas croiser les concepts. Chaque section = *ce que c'est* + *code minimal* + *piège classique*.

**Ancrage** : tu es SQL expert, donc chaque fois que possible je te donne l'équivalent SQL entre parenthèses.

---

## 1. Les bases absolues

### Lancer un script
```bash
python3 mon_script.py
```

### Afficher
```python
print("Hello")           # affiche "Hello"
print("age:", 42)        # affiche "age: 42" (espace auto)
```

### Commentaires
```python
# commentaire sur une ligne

"""
commentaire sur
plusieurs lignes (techniquement une string ignorée)
"""
```

### Demander une saisie à l'utilisateur
```python
nom = input("Ton nom ? ")     # attend une réponse au clavier
print(f"Salut {nom}")
```

---

## 2. Variables

```python
x = 5              # entier
prix = 9.99        # décimal (float)
nom = "Julien"     # chaîne (string)
actif = True       # booléen (majuscule !)
rien = None        # "vide" (équivalent NULL SQL)
```

**Règles de nommage** :
- `snake_case` (pas de camelCase)
- pas d'espace, pas d'accent, pas de chiffre en premier
- descriptif : `nb_transactions` > `n`

**Piège** : `=` = assignation. `==` = comparaison. Ne pas confondre.

---

## 3. Types de données — les 5 essentiels

| Type | Exemple | À quoi ça sert |
|---|---|---|
| `int` | `42` | nombre entier |
| `float` | `9.99` | nombre à virgule |
| `str` | `"hello"` | texte |
| `bool` | `True` / `False` | oui / non |
| `list` | `[1, 2, 3]` | collection ordonnée |
| `dict` | `{"nom": "Julien"}` | fiche clé → valeur |

### Vérifier un type
```python
type(42)           # <class 'int'>
isinstance(42, int) # True
```

### Convertir un type
```python
int("42")          # 42
float("9.99")      # 9.99
str(42)            # "42"
list("abc")        # ['a', 'b', 'c']
```

**Piège** : `int("9.99")` → **ValueError**. Il faut passer par `int(float("9.99"))` = `9`.

---

## 4. Nombres et opérateurs

```python
a + b        # addition
a - b        # soustraction
a * b        # multiplication
a / b        # division (renvoie toujours un float : 10/2 = 5.0)
a // b       # division ENTIÈRE (10 // 3 = 3)
a % b        # reste (modulo — 10 % 3 = 1)
a ** b       # puissance (2 ** 3 = 8)
```

**Raccourcis** :
```python
x += 1       # x = x + 1
x -= 1       # x = x - 1
x *= 2       # x = x * 2
```

**Piège JS→Python** : `x++` **n'existe pas** en Python. Utilise `x += 1`.

---

## 5. Strings — le kit de survie

### Créer
```python
s = "hello"
s = 'hello'       # simple ou double quote, pareil
s = """hello      # triple quote = multiligne
sur plusieurs
lignes"""
```

### Concaténer
```python
"a" + "b"                  # "ab"
"a" * 3                    # "aaa"
"a" + str(42)              # "a42" (le nombre DOIT être converti)
```

### f-string (**LA méthode moderne**)
```python
nom = "Julien"
age = 43
print(f"Salut {nom}, tu as {age} ans")
print(f"Prix : {prix:.2f}€")     # 2 décimales
print(f"Total : {montant:,}€")   # séparateur de milliers
```

### Méthodes utiles
```python
s = "  Hello World  "
s.strip()          # "Hello World" (enlève espaces début/fin)
s.lower()          # "  hello world  "
s.upper()          # "  HELLO WORLD  "
s.replace("l", "L") # "  HeLLo WorLd  "
s.split(" ")       # liste : ['', '', 'Hello', 'World', '', '']
"-".join(["a", "b", "c"])  # "a-b-c"
len(s)             # 15
"Hello" in s       # True
s.startswith("  H") # True
s.endswith("d  ")  # True
```

### Accéder à un caractère
```python
s = "Python"
s[0]         # "P" (indexe à partir de 0)
s[-1]        # "n" (le dernier)
s[0:3]       # "Pyt" (du 0 au 2 inclus, 3 exclu)
s[:3]        # "Pyt"
s[3:]        # "hon"
```

---

## 6. Booléens et comparaisons

### Comparaisons
```python
a == b       # égal
a != b       # différent
a < b        # strictement inférieur
a <= b       # inférieur ou égal
a > b
a >= b
```

### Opérateurs logiques
```python
a and b      # ET (JS : &&)
a or b       # OU (JS : ||)
not a        # NON (JS : !)
```

### Chaîne de comparaisons (spécificité Python !)
```python
if 18 <= age <= 65:      # marche en Python (bug en JS)
    ...
```

### Truthy / Falsy
Ce qui vaut `False` implicitement en Python :
- `False`
- `None`
- `0` / `0.0`
- `""` (string vide)
- `[]` (liste vide)
- `{}` (dict vide)

Tout le reste = `True`. Donc :
```python
if ma_liste:          # true si non vide
    ...
if nom:               # true si nom non vide
    ...
```

**Piège** : ne pas écrire `if x == True:`. Écris `if x:`.

---

## 7. Conditionnels

```python
if age >= 18:
    print("majeur")
elif age >= 13:
    print("ado")
else:
    print("enfant")
```

**Règles** :
- `:` obligatoire à la fin de chaque `if`/`elif`/`else`
- Indentation obligatoire (4 espaces standard)
- `elif` (pas `else if`)

### Ternaire (condition en une ligne)
```python
statut = "majeur" if age >= 18 else "mineur"
```

---

## 8. Boucles

### `for` sur une plage
```python
for i in range(5):        # 0, 1, 2, 3, 4
    print(i)

for i in range(1, 6):     # 1, 2, 3, 4, 5
    print(i)

for i in range(0, 10, 2): # 0, 2, 4, 6, 8 (pas de 2)
    print(i)
```

### `for` sur une liste
```python
for t in transactions:
    print(t)
```

### `for` avec index ET valeur
```python
for i, t in enumerate(transactions):
    print(f"{i}: {t}")
```

### `while`
```python
while solde > 0:
    solde -= 10
```

### Contrôle de flux
```python
break        # sort de la boucle
continue     # passe à l'itération suivante
```

**Piège** : oublier le `:` en fin de ligne = SyntaxError.

---

## 9. Listes — l'outil "file"

### Créer
```python
l = []
l = [1, 2, 3]
l = ["a", "b", "c"]
l = [1, "hello", True]    # types mixtes autorisés
```

### Accès (comme les strings)
```python
l[0]         # premier
l[-1]        # dernier
l[1:3]       # tranche
```

### Modifier
```python
l.append(4)              # ajoute à la fin
l.insert(0, "x")         # insère à l'index 0
l.pop()                  # retire ET renvoie le dernier
l.pop(0)                 # retire ET renvoie l'index 0
l.remove("b")            # retire la 1re occurrence de "b"
l[0] = "z"               # remplace
```

### Info
```python
len(l)                   # nombre d'éléments
"b" in l                 # True/False
l.count("b")             # nombre de "b"
l.index("b")             # position de "b"
```

### Trier
```python
sorted(l)                # nouvelle liste triée (l inchangée)
l.sort()                 # trie l EN PLACE
sorted(l, reverse=True)  # décroissant
sorted(l, key=lambda x: x["montant"])  # tri par clé
```

### Réduction
```python
sum(l)       # somme
min(l)       # minimum
max(l)       # maximum
```

### List comprehension (LA feature Python)
```python
# Transformer
carres = [x ** 2 for x in range(5)]       # [0, 1, 4, 9, 16]

# Filtrer
positifs = [x for x in l if x > 0]

# Les deux
carres_pairs = [x ** 2 for x in range(10) if x % 2 == 0]
```

**SQL bridge** :
```sql
SELECT montant * 1.2 FROM transactions WHERE type = 'CB'
```
```python
[t["montant"] * 1.2 for t in transactions if t["type"] == "CB"]
```

---

## 10. Dictionnaires — l'outil "fiche"

### Créer
```python
d = {}
d = {"nom": "Julien", "age": 43}
```

### Accès
```python
d["nom"]                 # "Julien" (KeyError si clé absente)
d.get("nom")             # "Julien"
d.get("email", "vide")   # "vide" (défaut si clé absente)
```

### Modifier
```python
d["email"] = "j@qonto.eu"   # ajoute ou modifie
del d["age"]                # supprime
d.pop("nom")                # retire ET renvoie
```

### Info
```python
"nom" in d               # True (test la CLÉ)
len(d)                   # nb de paires
d.keys()                 # toutes les clés
d.values()               # toutes les valeurs
d.items()                # paires (clé, valeur)
```

### Parcourir
```python
for cle, valeur in d.items():
    print(f"{cle} = {valeur}")
```

### Dict comprehension
```python
prix_ttc = {nom: prix * 1.2 for nom, prix in prix_ht.items()}
```

---

## 11. Le combo AML : liste de dicts

```python
transactions = [
    {"id": 1, "montant": 50, "type": "CB"},
    {"id": 2, "montant": 200, "type": "virement"},
    {"id": 3, "montant": 30, "type": "CB"},
]

# Somme des montants CB
total_cb = sum(t["montant"] for t in transactions if t["type"] == "CB")

# Trier par montant décroissant
tri = sorted(transactions, key=lambda t: t["montant"], reverse=True)

# Compter par type
from collections import Counter
compteur = Counter(t["type"] for t in transactions)
# Counter({'CB': 2, 'virement': 1})
```

**SQL bridge** :
```sql
SELECT type, COUNT(*), SUM(montant)
FROM transactions
GROUP BY type
```
```python
from collections import defaultdict
groupes = defaultdict(list)
for t in transactions:
    groupes[t["type"]].append(t["montant"])

for type_, montants in groupes.items():
    print(f"{type_}: {len(montants)} lignes, total {sum(montants)}")
```

---

## 12. Tuples et sets (à connaître, moins utilisés)

### Tuple = liste immuable
```python
point = (10, 20)
x, y = point           # déballage (unpacking)
```

Utilisation typique : renvoyer plusieurs valeurs d'une fonction.

### Set = ensemble unique
```python
s = {1, 2, 3, 3}       # {1, 2, 3} — doublons supprimés
s.add(4)
s.remove(1)
"a" in s               # test très rapide (O(1))
```

**Cas d'usage** : dédoublonner une liste :
```python
sans_doublons = list(set(ma_liste))
```

---

## 13. Fonctions

### Définition simple
```python
def bonjour():
    print("Salut")

bonjour()               # appel
```

### Avec paramètres et retour
```python
def frais(montant, taux=0.02):     # taux a une valeur par défaut
    return montant * taux

frais(100)              # 2.0 (utilise 0.02)
frais(100, 0.05)        # 5.0
frais(montant=100, taux=0.03)  # arguments nommés
```

### Renvoyer plusieurs valeurs
```python
def min_max(l):
    return min(l), max(l)

petit, grand = min_max([3, 1, 4, 1, 5])
```

### Docstring
```python
def frais(montant):
    """Calcule les frais à 2%."""
    return montant * 0.02
```

### Lambda (fonction courte anonyme)
```python
carre = lambda x: x ** 2
carre(5)                # 25

# Usage typique : dans sorted / filter / map
sorted(transactions, key=lambda t: t["montant"])
```

**Piège classique** : oublier `return`. La fonction s'exécute mais renvoie `None`.

---

## 14. Imports et modules

### Utiliser un module de la lib standard
```python
import math
math.sqrt(16)           # 4.0
math.pi                 # 3.14159...

from math import sqrt, pi
sqrt(16)                # 4.0 (plus besoin de math.)

import math as m        # alias
m.sqrt(16)
```

### Modules essentiels

| Module | À quoi ça sert |
|---|---|
| `math` | maths (sqrt, log, pi) |
| `random` | tirages aléatoires |
| `datetime` | dates et heures |
| `csv` | lire/écrire des CSV |
| `json` | lire/écrire du JSON |
| `os` | interagir avec le système de fichiers |
| `re` | expressions régulières |
| `collections` | `Counter`, `defaultdict` |
| `pathlib` | chemins de fichiers |

### Installer un package externe
```bash
pip install pandas
```
Puis dans le script :
```python
import pandas as pd
```

---

## 15. Fichiers

### Lire un fichier texte
```python
with open("data.txt") as f:
    contenu = f.read()          # tout d'un coup

with open("data.txt") as f:
    for ligne in f:             # ligne par ligne (mieux pour gros fichiers)
        print(ligne.strip())
```

### Écrire un fichier
```python
with open("out.txt", "w") as f:    # "w" = write (écrase)
    f.write("Hello\n")

with open("out.txt", "a") as f:    # "a" = append
    f.write("suite\n")
```

### Lire un CSV
```python
import csv
with open("data.csv") as f:
    reader = csv.DictReader(f)
    for ligne in reader:
        print(ligne["nom"], ligne["montant"])
```

### Lire un JSON
```python
import json
with open("data.json") as f:
    data = json.load(f)         # data = dict/list Python
```

**Pourquoi `with`** : ferme le fichier automatiquement même si erreur.

---

## 16. Dates

```python
from datetime import datetime, date, timedelta

now = datetime.now()             # maintenant
today = date.today()

# Créer une date précise
d = date(2026, 7, 12)

# Formater
now.strftime("%Y-%m-%d %H:%M")   # "2026-07-12 15:30"

# Parser une string
d = datetime.strptime("2026-07-12", "%Y-%m-%d")

# Calculs
demain = today + timedelta(days=1)
dans_1_mois = today + timedelta(days=30)
diff = date(2026, 12, 31) - today   # timedelta
diff.days                          # nb de jours
```

---

## 17. Gestion d'erreurs

### try / except
```python
try:
    montant = int(input("Montant ? "))
except ValueError:
    print("C'est pas un nombre")
```

### Plusieurs erreurs
```python
try:
    ...
except ValueError:
    print("mauvais format")
except KeyError:
    print("clé absente")
except Exception as e:              # attrape-tout (dernier recours)
    print(f"erreur : {e}")
```

### finally
```python
try:
    f = open("data.txt")
    ...
finally:
    f.close()               # exécuté même si erreur
```

**Règle** : ne JAMAIS mettre un `except:` seul ou `except Exception:` sans réfléchir. Tu masques des bugs.

---

## 18. Fonctions built-in à connaître

| Fonction | Rôle |
|---|---|
| `print(x)` | afficher |
| `input(msg)` | saisie clavier |
| `len(x)` | taille |
| `type(x)` | type |
| `range(a, b)` | plage |
| `int(x)`, `float(x)`, `str(x)`, `list(x)` | conversions |
| `sum(l)`, `min(l)`, `max(l)` | agrégats |
| `sorted(l)` | tri |
| `enumerate(l)` | index + valeur |
| `zip(l1, l2)` | fusionne 2 listes en paires |
| `map(fn, l)` | applique une fonction |
| `filter(fn, l)` | filtre |
| `abs(x)` | valeur absolue |
| `round(x, 2)` | arrondi |
| `any(l)` | True si au moins un truthy |
| `all(l)` | True si tous truthy |

### `zip` — souvent oublié, très utile
```python
noms = ["Julien", "Laetitia"]
ages = [43, 37]
for n, a in zip(noms, ages):
    print(f"{n} a {a} ans")
```

---

## 19. Conventions et style (PEP 8)

- **Indentation** : 4 espaces (pas de tab)
- **Noms de variables et fonctions** : `snake_case`
- **Noms de constantes** : `MAJUSCULES_AVEC_UNDERSCORES`
- **Espaces** : `x = 5` (autour du `=`), `f(x, y)` (pas d'espace avant `(`)
- **Ligne** : max ~80 caractères
- **Un import par ligne** :
  ```python
  import os
  import sys
  # PAS import os, sys
  ```

---

## 20. Les pièges qui vont te mordre (top 10)

1. **Indentation incohérente** → IndentationError. Utilise **4 espaces**, jamais de tab.
2. **Oublier le `:` en fin de `if`/`for`/`def`** → SyntaxError.
3. **`=` au lieu de `==`** dans un `if` → SyntaxError.
4. **Modifier une liste pendant qu'on la parcourt** :
   ```python
   for x in l:
       if x < 0:
           l.remove(x)     # bug : saute des éléments
   ```
   Fais plutôt : `l = [x for x in l if x >= 0]`
5. **Mutabilité des listes en argument par défaut** :
   ```python
   def f(x=[]):     # PIÈGE : x est partagé entre les appels
       x.append(1)
       return x
   ```
   Fais plutôt : `def f(x=None): x = x or []`
6. **`==` sur des floats** :
   ```python
   0.1 + 0.2 == 0.3    # False !
   ```
   Utilise `abs(a - b) < 0.0001` pour comparer des floats.
7. **Confondre liste et set** : `{1, 2, 3}` = set (non ordonné, non indexable). `[1, 2, 3]` = liste.
8. **Copie de liste** :
   ```python
   b = a           # b et a pointent SUR LA MÊME liste
   b = a.copy()    # b est une VRAIE copie
   ```
9. **Oublier `return`** : la fonction renvoie `None`.
10. **Confondre `is` et `==`** :
    - `==` : même valeur
    - `is` : même objet en mémoire
    - Utilise `is` UNIQUEMENT avec `None` : `if x is None:`

---

## 21. Patterns récurrents (les copier-coller utiles)

### Accumulateur (somme conditionnelle)
```python
total = 0
for t in transactions:
    if t["type"] == "CB":
        total += t["montant"]
```
ou plus court :
```python
total = sum(t["montant"] for t in transactions if t["type"] == "CB")
```

### Compter par catégorie
```python
from collections import Counter
compteur = Counter(t["type"] for t in transactions)
```

### Regrouper par catégorie
```python
from collections import defaultdict
groupes = defaultdict(list)
for t in transactions:
    groupes[t["type"]].append(t)
```

### Trouver le max selon un critère
```python
plus_gros = max(transactions, key=lambda t: t["montant"])
```

### Filtrer + transformer
```python
resultats = [t["montant"] * 1.2 for t in transactions if t["type"] == "CB"]
```

### Dédoublonner en préservant l'ordre
```python
vus = set()
uniques = []
for x in liste:
    if x not in vus:
        vus.add(x)
        uniques.append(x)
```

### Fusionner deux dicts
```python
d3 = {**d1, **d2}       # d2 écrase d1 en cas de collision
```

---

## 22. Structure d'un vrai script Python

```python
"""
analyseur.py — calcule les frais totaux d'un CSV de transactions.
Usage : python3 analyseur.py mon_fichier.csv
"""

import csv
import sys
from collections import defaultdict

TAUX_FRAIS = 0.02      # constante en majuscules

def frais(montant):
    """Frais à 2%."""
    return montant * TAUX_FRAIS

def charger(chemin):
    """Lit le CSV, renvoie liste de dicts."""
    with open(chemin) as f:
        return list(csv.DictReader(f))

def main():
    chemin = sys.argv[1]                # 1er argument CLI
    transactions = charger(chemin)
    total = sum(frais(float(t["montant"])) for t in transactions)
    print(f"Total frais : {total:.2f}€")

if __name__ == "__main__":
    main()
```

**Le `if __name__ == "__main__":`** = "n'exécute `main()` que si on lance ce fichier directement, pas si on l'importe ailleurs." Convention à respecter dès qu'un script fait plus que 20 lignes.

---

## 23. Environnements virtuels (pour projets sérieux)

```bash
python3 -m venv .venv           # crée l'env
source .venv/bin/activate       # active (à faire à chaque terminal)
pip install pandas requests     # installe
pip freeze > requirements.txt   # sauvegarde
deactivate                      # sort de l'env
```

**Pourquoi** : chaque projet a ses versions de packages, sans conflit avec d'autres projets.

---

## 24. Ce qui doit devenir automatique

- **f-string partout** — pas de concaténation avec `+`
- **List comprehension** au lieu de `for` + `append` quand c'est du transform/filter
- **`with open(...)`** au lieu de `open()` + `close()`
- **`dict.get(cle, defaut)`** au lieu de `if cle in d`
- **`snake_case`** pour tous les noms
- **`if x:`** au lieu de `if x == True:`
- **Toujours `return`** explicite si la fonction doit renvoyer quelque chose
- **Toujours indenter à 4 espaces**
- **Toujours un `main()` + `if __name__ == "__main__":`** pour un vrai script

---

## Récap ultra-condensé (à relire avant un exercice)

```
Variable          x = 5                   (pas de let)
Bloc              :  + indentation 4 espaces
Print             print(f"...")
Booléens          True / False / None
Logique           and / or / not
Comparaison       == != < <= > >=
Chaîne comp       18 <= x <= 65
Condition         if / elif / else
Boucle N          for i in range(N):
Boucle liste      for x in l:
Index + val       for i, x in enumerate(l):
Liste             l = [1, 2, 3]
Ajouter           l.append(x)
Tranche           l[1:3]
Somme             sum(l)
Trier             sorted(l, key=lambda x: ...)
Comprehension     [x * 2 for x in l if x > 0]
Dict              d = {"cle": val}
Accès sûr         d.get("cle", defaut)
Parcours dict     for k, v in d.items():
Fonction          def f(a, b=10): return ...
Fichier           with open("f") as f: ...
Import            from module import truc
Erreur            try: ... except ValueError: ...
```

---

## Où tu vas revoir tout ça

- **Chaque session Python** : cette fiche est ton point de départ.
- **Scripts AML** : sections 9 (listes), 10 (dicts), 11 (combo AML), 15 (CSV), 21 (patterns) sont **le cœur** de ce que tu vas coder.
- **Dès que tu bloques** : ctrl+F sur cette fiche AVANT d'aller sur Google.
- **En parallèle** : la fiche `js-vs-python-2026-07-12.md` te sauve si tu confonds avec Jiki.
