# JS (Jiki) ↔ Python — la fiche anti-confusion

Tu manipules deux syntaxes en parallèle (Jiki en JS-like + coaching Python). Cette fiche liste **uniquement les points où le cerveau se prend les pieds dans le tapis** quand on switche.

Règle mentale de base : **la logique est la même**, seule l'orthographe change. Les vrais pièges sont dans le tableau ci-dessous.

---

## 1. Tableau de traduction — les 20 briques du quotidien

| Concept | JS / Jiki | Python | Piège quand tu switches |
|---|---|---|---|
| Déclarer une variable | `let x = 5` | `x = 5` | Écrire `let x = 5` en Python = SyntaxError |
| Bloc de code | `{ ... }` | `:` + indentation | Oublier le `:` en Python, oublier les `{}` en JS |
| Fin de ligne | `;` (facultatif) | rien | Un `;` traînant en Python = pas d'erreur mais moche |
| Commentaire | `// ...` | `# ...` | `//` en Python = division entière, pas un commentaire ! |
| Booléens | `true` / `false` | `True` / `False` | Majuscule obligatoire en Python |
| Rien / vide | `null` / `undefined` | `None` | `null` en Python = NameError |
| ET logique | `&&` | `and` | `&&` en Python = SyntaxError |
| OU logique | `\|\|` | `or` | idem |
| NON logique | `!x` | `not x` | `!x` en Python = SyntaxError |
| Égalité | `===` (strict) / `==` | `==` | `===` en Python = SyntaxError |
| Différent | `!==` / `!=` | `!=` | `!==` en Python = SyntaxError |
| Boucle "N fois" | `repeat(5) { ... }` | `for i in range(5):` | `repeat` n'existe pas en Python |
| Boucle sur liste | `for (let x of arr)` | `for x in arr:` | Python : pas de parenthèses, pas de `let`/`of` |
| Condition sinon-si | `else if` | `elif` | `else if` en Python = SyntaxError |
| Fonction | `function pan() { ... }` | `def pan(): ...` | Confusion `function` vs `def` |
| Return | implicite possible | `return` obligatoire pour renvoyer | Oublier `return` en Python = fonction renvoie `None` |
| Afficher | `console.log(x)` | `print(x)` | — |
| Concaténer strings | `"a" + "b"` | `"a" + "b"` | Identique. **Mais** voir ligne suivante |
| String + nombre | `"age " + 30` = `"age 30"` | `"age " + 30` = **TypeError** | Python refuse le mélange, JS convertit tout seul |
| Template string | `` `Hello ${nom}` `` | `f"Hello {nom}"` | Confondre les deux syntaxes |

---

## 2. Les 5 pièges qui vont te mordre

### Piège 1 — `&&` / `||` vs `and` / `or`

C'est le plus fréquent quand on switche.

```js
// JS / Jiki
if (age >= 18 && guest === true) { ... }
```

```python
# Python
if age >= 18 and guest:
    ...
```

**Réflexe** : dès que tu tapes `&&` ou `||`, demande-toi dans quelle plateforme tu es.

---

### Piège 2 — booléens en majuscule ou minuscule

```js
let ok = true    // JS
```

```python
ok = True        # Python — MAJUSCULE obligatoire
```

**Symptôme si tu te trompes** : Python te dit `NameError: name 'true' is not defined`. Il pense que `true` est une variable qu'il ne trouve pas.

---

### Piège 3 — la chaîne de comparaisons

**Le seul cas où Python fait un truc que JS n'autorise PAS.**

```python
# Python — MARCHE
if 58 <= shot <= 62:
    ...
```

```js
// JS — NE MARCHE PAS comme tu crois
if (58 <= shot <= 62) { ... }  // Bug silencieux : évalue faux
// Il faut écrire :
if (shot >= 58 && shot <= 62) { ... }
```

**Réflexe** : en Python la double comparaison est OK, en JS elle est traître. Si tu prends l'habitude Python, ça va te niquer en JS. Si tu prends l'habitude JS, tu perds du temps en Python.

Ma reco : **écris toujours à la manière JS** (`x >= min and x <= max` en Python aussi). C'est plus verbeux mais tu ne te fais jamais avoir.

---

### Piège 4 — string + nombre

```js
// JS — silencieux, ça marche mais c'est louche
"total: " + 42        // → "total: 42"
"3" + 4               // → "34" (bug typique)
```

```python
# Python — refuse net
"total: " + 42        # TypeError
"total: " + str(42)   # OK
f"total: {42}"        # OK et plus élégant
```

**Symptôme si tu te trompes en Python** : `TypeError: can only concatenate str (not "int") to str`.

**Bonne pratique universelle** : en Python utilise **f-string**, en JS utilise **template string** (backticks). Tu n'as plus jamais de `+` avec des strings :

```python
print(f"Total: {montant}€")
```
```js
console.log(`Total: ${montant}€`)
```

---

### Piège 5 — `let x = "suit" || "dress"`

Tu as déjà buté dessus côté Jiki. Rappel :

```js
let formal = "suit" || "dress"   // formal vaut "suit" (le premier truthy)
```

En Python même chose :

```python
formal = "suit" or "dress"       # formal vaut "suit"
```

Les deux langages évaluent le `||`/`or` de la même manière : ils renvoient **la première valeur truthy**, pas un booléen. Donc **le piège est identique dans les deux langues**. Retiens : `||`/`or` ne peut jamais te fabriquer un "ou l'un ou l'autre selon les cas" — il renvoie toujours le premier truthy.

---

## 3. Ce qui est identique (ne te crée pas de faux problèmes)

- **La logique de la boucle** : accumulateur, ordre "use then advance", scope. Change juste l'orthographe.
- **La logique du `if`** : branches disjointes et nécessaires. Change juste `else if` ↔ `elif`.
- **L'égalité de type simple** : `x == 5` marche pareil.
- **Les opérateurs mathématiques** : `+ - * / %` identiques (attention : `//` = division entière en Python, commentaire en JS).
- **Les fonctions** : machine avec entrées et sortie. Change juste `function` ↔ `def`.
- **Comparaisons** : `< > <= >= == !=` sauf `===`/`!==` qui n'existent qu'en JS.

---

## 4. Le réflexe universel : le "check-langue" avant de taper

Avant chaque bloc de code, redis-toi à voix basse (littéralement) :

> *"Je suis dans **Python**. Donc : indentation, `:`, `and`/`or`/`not`, `True`/`False`, `None`, `elif`, f-string."*

ou

> *"Je suis dans **JS/Jiki**. Donc : `{}`, `let`, `&&`/`||`/`!`, `true`/`false`, `null`, `else if`, backticks."*

Ça prend 2 secondes et supprime 80% des bugs de switch.

---

## 5. Cheat sheet ultra-condensée (à imprimer mentalement)

```
                JS/Jiki           Python
                -------           ------
variable        let x = 5         x = 5
bloc            { ... }           :\n  ...
booléens        true/false        True/False
rien            null              None
et              &&                and
ou              ||                or
non             !                 not
égal            === ou ==         ==
différent       !== ou !=         !=
sinon-si        else if           elif
boucle N        repeat(N){}       for _ in range(N):
boucle liste    for(x of arr)     for x in arr:
fonction        function f(){}    def f():
afficher        console.log(x)    print(x)
template        `hello ${n}`      f"hello {n}"
commentaire     //                #
```

---

## 6. Où tu vas revoir ça

- **Chaque exercice Jiki** : ta réflexe `&&` va essayer de sortir en Python le lendemain, et inversement.
- **Session AML** : tes futurs scripts Python s'inspirent de la logique conditionnelle que tu construis dans Jiki. La logique passe, la syntaxe change.
- **Quand tu bloques 30 secondes sur "pourquoi ça marche pas"** : viens ici en premier. 9 fois sur 10, c'est un item de cette fiche.

---

## Ce qui doit devenir automatique (à te dire tout haut)

- `&&` → JS. `and` → Python.
- `true` → JS. `True` → Python.
- `else if` → JS. `elif` → Python.
- `null` → JS. `None` → Python.
- `{}` → JS. `:` + indent → Python.
- String + nombre : JS pardonne, Python refuse. Utiliser f-string / backticks partout.
- Chaîne de comparaisons `a <= x <= b` : autorisée en Python, **piège en JS**.
