# Concepts Python — session 2026-07-12

Première session Python post-Jiki. Traduit les briques Jiki (fonction/retour/boucle/accumulateur) en syntaxe Python, débloque paramètre ↔ argument, ajoute listes + dictionnaires.

**Format** : chaque concept = une analogie concrète + code minimal + où ça revient. Rédigé pour être relu vite en début de session suivante.

---

## 1. Syntaxe Python des briques déjà connues (traduction depuis Jiki)

| Jiki (JS-like)              | Python                        |
|-----------------------------|-------------------------------|
| `let x = 0`                 | `x = 0` (pas de `let`)        |
| `repeat(5){ ... }`          | `for i in range(5): ...`      |
| bloc entre `{ }`            | bloc **indenté** après `:`    |
| appel `pan()`               | pareil : `pan()`              |
| retour implicite            | `return` explicite obligatoire |

**Règle Python** : le `:` ouvre un bloc, l'indentation (4 espaces) le délimite. Pas d'accolades.

---

## 2. `for ... in` : parcourir une liste

```python
for t in transactions:
    total = total + frais_transaction(t)
```

- `for` et `in` = mots-clés fixes
- `t` = nom **choisi par moi**, existe seulement le temps de la boucle
- À chaque tour, `t` contient l'élément courant
- Équivalent Python du `repeat` de Jiki, en mieux : donne l'élément à chaque tour au lieu de tourner à vide

---

## 3. LE déblocage central : paramètre vs argument

**Le piège** : ne pas voir le lien entre le nom dans `def fonction(montant)` et la variable de boucle `t`.

### Deux mondes séparés

```python
def frais_transaction(montant):   # monde INTÉRIEUR
    ...

for t in transactions:            # monde EXTÉRIEUR
    frais_transaction(t)
```

- `montant` **n'existe qu'à l'intérieur** de la fonction. C'est une **étiquette d'emprunt**.
- `t` vit **à l'extérieur**, dans la boucle.
- L'appel `frais_transaction(t)` = *"je prends la valeur de `t`, je la range dans l'étiquette `montant` le temps du calcul."*

### Analogie machine à laver

- La pile de linge dans la buanderie = `transactions` (liste dehors)
- Le vêtement que je prends en main = `t` (variable de boucle)
- La machine dit *"j'appelle ça `linge`"* = `montant` (paramètre dedans)

Le vêtement fait le **pont** entre les deux mondes. Sans lui, la machine tourne à vide.

### Les noms sont arbitraires

```python
def frais_transaction(bidule):
    return bidule * 0.02

for machin in transactions:
    frais_transaction(machin)
```

Marche pareil. **Ce qui compte : la position, pas le nom.** Ce qui est entre les `()` de l'appel remplit l'étiquette entre les `()` de la définition.

---

## 4. `return` = le tuyau de sortie

- Sans `return`, la machine tourne mais ne crache rien (retourne `None` implicitement)
- Dès qu'un `return` est atteint, la fonction s'arrête
- Attraper le retour : dans une variable OU direct dans un calcul

```python
resultat = double(5)           # attrapé dans une boîte
total = total + double(5)      # attrapé direct dans un calcul
```

**Défensif** : quand plusieurs branches `if/elif`, prévoir un `else` de fallback pour éviter que la fonction retourne `None` silencieusement.

---

## 5. `==` vs `=`

- `=` : *"mets ça dans la boîte"* (assignation)
- `==` : *"est-ce que c'est égal ?"* (comparaison, renvoie `True` ou `False`)

`if x = 5:` plante. `if x == 5:` marche.

---

## 6. `+=` et compagnie

Raccourci pour incrémenter :

```python
total = total + x     # forme longue
total += x            # forme courte, strictement équivalent
```

Existe aussi en `-=`, `*=`, `/=`.

---

## 7. `elif` : plus de deux branches

```python
if type_compte == "pro":
    return 2
elif type_compte == "perso":
    return montant * 0.01
else:
    return 0        # fallback : couvrir les cas non prévus
```

`elif` = contraction de `else if`. Si tu n'as que deux branches, un simple `else` suffit (et est plus safe).

---

## 8. Déballage de tuples dans la boucle

Quand la liste contient des couples (ou triplets), tu peux "déballer" directement :

```python
operations = [(100, "pro"), (50, "perso")]

for montant, type_compte in operations:
    # à chaque tour, montant et type_compte sont remplis
    ...
```

Python range les deux valeurs du tuple dans deux boîtes distinctes en une ligne.

---

## 9. Squelette réutilisable "fonction règle + boucle accumulateur"

Pattern qui revient partout (AML, stats, reporting) :

```python
def regle(x):
    if condition:
        return valeur_A
    else:
        return valeur_B

liste = [...]

total = 0
for element in liste:
    total = total + regle(element)

print(total)
```

- `regle` isole la logique métier (testable, réutilisable)
- `total = 0` **avant** la boucle (accumulateur qui survit — concept Jiki #7)
- `regle(element)` dans la boucle → recalculé à chaque tour (concept Jiki #6)

---

## 10. Bugs typiques (rencontrés en session)

**Bug A — confondre "retourner une valeur" et "additionner à l'entrée"**
```python
return montant + 1.5   # ❌ pour 50 €, crache 51.5
return 1.5             # ✅ frais fixes indépendants du montant
```

**Bug B — appeler la fonction sans argument**
```python
frais_transaction()    # ❌ la machine ne sait pas quoi presser
frais_transaction(t)   # ✅ passer la valeur du tour courant
```

**Bug C — mélanger nom de boucle et nom de variable dans le corps**
```python
for m in montants:
    total += fonction(montant, seuil)   # ❌ "montant" n'existe pas, tu as choisi "m"
```
Cohérence : soit `m` partout, soit `montant` partout.

**Bug D — piège du scope (concept Jiki #6/#7)**
```python
for m in montants:
    seuil = 150             # ❌ reset à chaque tour, incrément perdu
    seuil = seuil + 50
```
Une valeur qui doit **survivre d'un tour à l'autre** = déclarée **hors** de la boucle.

**Bug E — ordre "utiliser puis avancer" (concept Jiki #8)**
```python
for m in montants:
    seuil = seuil + 50            # ❌ tu avances AVANT d'utiliser
    total += suspecte(m, seuil)   # → tu rates le 1er tour
```
Pattern correct : d'abord utiliser la valeur courante, puis avancer pour le tour suivant.

**Bug F — double comptage**
Si ta fonction compte déjà (retourne 1 ou 0), pas besoin d'un `if` supplémentaire pour ajouter encore 1.

---

## 11. Listes — l'outil "file d'attente"

### Analogie

Une file d'attente à la boulangerie : les gens sont dans un ordre précis.

```python
file = ["Marie", "Paul", "Sofia"]
```

- Marie est la première (position 0)
- Paul le deuxième (position 1)
- Sofia la troisième (position 2)

### Compter

```python
len(file)     # 3
```

### Pointer une place précise

**Piège** : Python compte à partir de **0**, pas de 1. Comme le compteur kilométrique d'une voiture neuve.

```python
file[0]      # "Marie"
file[1]      # "Paul"
file[2]      # "Sofia"
file[-1]     # "Sofia" (raccourci pour le dernier)
```

Les crochets `[ ]` avec un **nombre** = *"donne-moi ce qui est à cette place"*.

### Ajouter à la fin

```python
file.append("Lucas")
# file vaut maintenant ["Marie", "Paul", "Sofia", "Lucas"]
```

`.append` = "ajouter à la fin". Le point veut dire *"applique une action sur cet objet précis"*.

### Remplacer à une place

```python
file[0] = "Emma"
# file vaut ["Emma", "Paul", "Sofia"]
```

Même syntaxe que pour lire, mais avec `=` derrière = tu remplaces.

### Parcourir

```python
for personne in file:
    print(personne)
```

À chaque tour, `personne` contient un élément de la file, dans l'ordre.

---

## 12. Dictionnaires — l'outil "fiche cartonnée"

### Analogie

Une fiche patient : des **étiquettes à gauche** (Nom, Âge, Ville) et **des valeurs à droite** (Julien, 43, Paris).

Tu ne dis pas *"donne-moi la place 0"*. Tu dis *"donne-moi ce qu'il y a en face de l'étiquette Nom"*.

### Écrire une fiche

```python
patient = {
    "nom": "Julien",
    "age": 43,
    "ville": "Paris",
}
```

- Accolades `{ }` (pas des crochets)
- Chaque ligne = **une étiquette** + `:` + **une valeur**
- Les étiquettes s'appellent des **clés** (*keys*)
- Les valeurs à droite s'appellent des **valeurs** (*values*)
- Virgule à la fin de chaque ligne (même la dernière, par hygiène)

### Lire une valeur

```python
patient["nom"]     # "Julien"
patient["age"]     # 43
```

Crochets avec un **mot** (entre guillemets) = *"donne-moi ce qui est en face de cette étiquette"*.

### Différence clé avec les listes

- Liste : `file[0]` → on désigne par un **nombre**
- Dico : `patient["nom"]` → on désigne par un **mot**

### Modifier / ajouter

```python
patient["age"] = 44         # modifie l'étiquette existante
patient["metier"] = "Data"  # crée une nouvelle étiquette
```

Même syntaxe. Python regarde si l'étiquette existe :
- Existe → il remplace la valeur
- N'existe pas → il crée l'étiquette

### Vérifier la présence d'une clé

```python
"metier" in patient    # True ou False
```

---

## 13. LE combo AML : liste de dictionnaires (classeur de fiches)

### Analogie

Un **classeur** (la liste) contient **plusieurs fiches** (les dictionnaires).

```python
patients = [
    {"nom": "Julien", "age": 43},
    {"nom": "Marie", "age": 37},
    {"nom": "Paul", "age": 52},
]
```

- Le `[` ouvre le classeur
- Chaque `{ ... }` = une fiche dans le classeur
- Les virgules entre les fiches = "puis la suivante"
- Le `]` ferme le classeur

**Forme réelle des données AML** : résultat d'une requête SQL, export d'API, etc. arrive presque toujours sous cette forme.

### Deux niveaux d'accès

```python
patients[0]              # la fiche entière : {"nom": "Julien", "age": 43}
patients[0]["nom"]       # "Julien"
patients[1]["age"]       # 37
```

Deux syntaxes différentes qui s'enchaînent :
1. Crochets avec un **nombre** → dans une liste
2. Crochets avec un **mot** → dans un dictionnaire

### Parcourir toutes les fiches

```python
for fiche in patients:
    print(fiche["nom"])
```

À chaque tour, `fiche` contient **une fiche complète** (un dictionnaire entier), pas une valeur. Ensuite `fiche["nom"]` va chercher la valeur.

### Pattern AML classique : somme conditionnelle

```python
transactions = [
    {"id": "TX001", "montant": 500, "pays": "FR"},
    {"id": "TX002", "montant": 15000, "pays": "DE"},
    {"id": "TX003", "montant": 8000, "pays": "RU"},
]

total_ru = 0
for tx in transactions:
    if tx["pays"] == "RU":
        total_ru += tx["montant"]

print(total_ru)
```

Squelette qu'on retrouve partout : filtrer sur une clé, sommer une autre clé.

---

## 14. Méthodo pédagogique qui marche pour moi

Notes pour les prochaines sessions (à Claude et à moi) :

- **Une brique à la fois.** Ne pas balancer 3 concepts en même temps sous prétexte que "ça va ensemble".
- **Analogie concrète d'abord** (file d'attente, fiche cartonnée, machine à laver), code après.
- **Micro-question de validation** après chaque brique. Prédire ce que fait le code avant de l'exécuter. Pas passer au concept suivant tant que la brique précédente n'est pas validée.
- **Ne pas utiliser un mot-clé Python sans l'avoir explicitement introduit avant.** `return`, `for...in`, `.append`, `==`, `+=`, etc. — chaque terme mérite son propre paragraphe la première fois.
- **Répétition espacée sur les mêmes briques** avant d'ajouter du neuf : 2-3 exos courts avec contextes différents (AML, cashback, remise, score) une fois qu'un concept est passé.
- **Toujours dérouler mentalement le code à la main** (tour par tour, valeur des variables) avant de le lancer. C'est ce qui grave le pattern.
