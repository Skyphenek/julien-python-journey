# Concepts programmation — session Jiki du 2026-07-11

> Fiche mémoire des concepts croisés pendant les exercices Jiki (or, arc-en-ciel, coucher de soleil, splodges, stock market, golf, jardin, gratte-ciel, space invaders). Écrite pour être relue vite. Chaque concept = analogie simple + code minimal + pourquoi ça compte.

---

## 1. Une fonction = une machine

Une fonction est une petite machine avec un nom.
- Les **parenthèses `()`** = "lance la machine maintenant".
- Ce qu'il y a dedans = ce qu'on **donne** à la machine (les **arguments** / **inputs**).
- Ce qui sort par le tuyau = ce que la machine **retourne**.

```js
pan()                  // je lance la machine, elle produit un nombre
sell(numberOfNuggets)  // je lance la machine en lui donnant un nombre
```

**Analogie enfant** : une machine à jus. Tu mets un fruit (input), elle te sort du jus (retour). Sans fruit, elle ne fait rien.

---

## 2. Attraper le retour d'une fonction

Quand une machine te rend quelque chose, si tu ne l'attrapes pas, **ça tombe par terre et c'est perdu**.

```js
pan()             // le résultat est jeté
let found = pan() // le résultat est mis dans la boîte "found"
```

**Attraper = utiliser quelque part.** Deux façons :
1. Le mettre dans une variable (boîte) pour plus tard
2. L'utiliser **directement** dans un calcul ou dans une autre fonction

```js
// avec boîte intermédiaire
let found = pan()
total = total + found

// sans boîte — équivalent
total = total + pan()
```

**Règle générale** : partout où on attend un nombre, on peut mettre `pan()` si `pan()` retourne un nombre.

```js
sell(pan())              // vendre directement le résultat
let x = pan() + pan()    // additionner deux appels
if (pan() > 5) { ... }   // tester le résultat
```

C'est ce qu'on appelle une **expression** : un morceau de code qui "vaut" une valeur. `3`, `pan()`, `pan() + 2` sont toutes des expressions interchangeables tant qu'elles produisent le bon type.

---

## 3. Une variable = une boîte étiquetée

```js
let numberOfNuggets = 0
```

Traduction : *"crée une nouvelle boîte, colle l'étiquette `numberOfNuggets`, mets `0` dedans."*

- `let` = "crée une nouvelle boîte"
- Le nom = l'étiquette
- `=` = "mets dedans"

---

## 4. Réassigner une variable (l'accumulateur)

```js
numberOfNuggets = numberOfNuggets + pan()
```

**Lecture ordre d'exécution** :
1. L'ordi lance `pan()` → obtient (par ex) `2`
2. Il regarde ce qu'il y a dans la boîte `numberOfNuggets` → (par ex) `3`
3. Il calcule `3 + 2 = 5`
4. Il **remplace** le contenu de la boîte par `5`

C'est le **pattern accumulateur** : une boîte qui grossit tour après tour.

```
total = 0
pour chaque truc:
    total = total + valeur_du_truc
utiliser(total)
```

**Où tu vas revoir ça** : cumul de transactions AML, comptage d'alertes, scores de risque cumulés. Partout.

---

## 5. Une boucle `repeat`

```js
repeat(5){
  // fais ça 5 fois
}
```

Utile pour ne pas copier-coller la même action 5 fois.

**Le nombre de tours peut être une variable ou un appel de fonction** :

```js
repeat(shotLength){ ... }        // nombre de tours = valeur d'une variable
repeat(getShotLength()){ ... }   // nombre de tours = retour d'une fonction
```

Comme pour les arguments, `repeat` accepte n'importe quelle expression qui produit un nombre.

---

## 6. LE piège central : ce qui vit hors de la boucle est figé

**Réflexe à installer** : à chaque ligne du code, se demander *"cette ligne est appelée combien de fois ?"*

- Ligne **hors** de `repeat(N){}` → appelée **1 fois**
- Ligne **dans** `repeat(N){}` → appelée **N fois**

Si tu veux N valeurs différentes, il faut N appels → la ligne doit être **dans** la boucle.

### Exemples du piège rencontrés 3 fois d'affilée

```js
// ❌ FAUX — couleur calculée 1 seule fois, tout sera de la même couleur
let color = hsl(hue, 50, 50)
repeat(100){
  rectangle(x, 0, 1, 100, color)
  hue = hue + 3
}
```

```js
// ✅ CORRECT — couleur recalculée à chaque tour
repeat(100){
  rectangle(x, 0, 1, 100, hsl(hue, 50, 50))
  hue = hue + 3
}
```

Même erreur avec `let skyColor = hsl(z, 70, 60)` (coucher de soleil) et `let growth = marketGrowth(year)` (stock market).

**Règle qui doit devenir réflexe** : si une valeur doit **changer à chaque tour**, elle doit être **calculée dans la boucle**, pas avant.

Inversement (règle miroir) : si une valeur **ne change pas** entre les tours, ne la recalcule pas dans la boucle. Exemple : `let spacing = 100 / (count + 1)` reste dehors.

---

## 7. Portée (scope) : où vit une variable

- Déclarée **hors** de la boucle → survit d'un tour à l'autre (utile pour accumuler)
- Déclarée **dans** la boucle avec `let` → recréée à chaque tour (utile quand chaque tour est indépendant)

```js
// accumulateur : garde la valeur d'un tour à l'autre → hors boucle
let total = 0
repeat(10){ total = total + pan() }

// tour indépendant : recréé à chaque tour → dans boucle
repeat(200){
  let radius = randomInt(2, 29)
  let x = randomInt(radius, 100 - radius)
  circle(x, y, radius, hsl(hue, 50, 50))
}
```

**Règle** : la variable doit vivre au niveau où on a besoin qu'elle survive.

---

## 8. Ordre des opérations dans une boucle

L'ordre des lignes dans un bloc change le comportement.

Pattern **"utiliser puis avancer"** (le plus courant) :
```js
repeat(20){
  // 1. utiliser les valeurs actuelles (ex : dessiner, calculer)
  // 2. faire avancer les compteurs pour le tour suivant
}
```

Si tu inverses (avancer puis utiliser), tu sautes la première valeur et tu vas trop loin à la fin. Bug d'**off-by-one** classique.

**Autre variante** : quand une valeur dépend d'une autre, il faut la calculer **après** celle dont elle dépend.
```js
radius = randomInt(2, 29)             // d'abord
x = randomInt(radius, 100 - radius)   // ensuite, car dépend de radius
```

Ce concept revient en SQL : tu ne peux pas filtrer sur une colonne calculée avant qu'elle soit calculée.

---

## 9. Paramétrer avec des variables plutôt qu'écrire "en dur"

Au lieu de :
```js
buildWall(17, 2)
buildGlass(18, 2)
buildEntrance(19, 2)
```

Faire :
```js
let center = 19
let groundFloor = 2
buildWall(center - 2, groundFloor)
buildGlass(center - 1, groundFloor)
buildEntrance(center, groundFloor)
```

**Pourquoi c'est important** : si demain le centre passe à 30, tu changes **une** ligne au lieu de 15. Et tu ne peux pas en oublier une.

C'est le principe **"one source of truth"** que tu croiseras :
- en SQL avec les CTE (`WITH threshold AS (SELECT 10000)`)
- en AML : "seuil de suspicion = 10 000 €" déclaré une fois en tête de requête

---

## 10. Intérêts composés (concept maths pour le stock market)

Si tu as V et ça grandit de X %, tu obtiens :
```
nouveau = V + (V × X / 100)
       = V × (1 + X / 100)
```

Le "composé" = l'année suivante, la croissance s'applique sur le **nouveau** solde, pas sur le solde de départ.

```js
balance = balance * (1 + growth / 100)
```

Ce pattern (boucle temporelle + fonction qui donne une valeur par période + accumulation) est le squelette de la plupart des calculs quantitatifs.

---

## 11. Répartition uniforme sur une ligne

Pour placer N éléments également espacés sur une longueur de 100 **avec des marges égales aux deux bouts** :

```
espacement = 100 / (N + 1)
positions = espacement, 2×espacement, ..., N×espacement
```

Le `+1` vient du fait qu'il faut N+1 espaces égaux (avant le 1er, entre chaque, après le dernier).

**Analogie clôture** : pour 20 poteaux, il te faut 19 sections de grillage **entre** eux. N éléments → N-1 intervalles entre (ou N+1 avec marges des deux côtés). Ce type de "N vs N-1 vs N+1" est le berceau des bugs off-by-one.

---

## 12. `if` sans `else` : action optionnelle

Deux patterns différents avec `if` :

**Pattern A — deux branches obligatoires** :
```js
if (condition) {
  faireX()
} else {
  faireY()
}
```
"Soit X, soit Y, jamais les deux, jamais rien."

**Pattern B — une branche optionnelle** :
```js
if (condition) {
  actionOptionnelle()
}
actionObligatoire()
```
"Toujours l'obligatoire. En plus, l'optionnelle si la condition."

Exemple Space Invaders : `move()` obligatoire (chaque tour), `shoot()` optionnel (seulement si alien au-dessus).

**Où tu vas revoir ça** :
- AML : "toujours logger la transaction ; en plus, alerter si montant > seuil"
- Web : "toujours répondre à la requête ; en plus, envoyer un email en cas d'erreur"

---

## 13. "Loop peeling" : sortir une itération de la boucle

Quand la première (ou la dernière) itération est différente des autres, on la **sort** de la boucle.

Exemple Space Invaders : je veux vérifier 20 cases mais faire seulement 19 mouvements (sinon je sors de l'écran au 20e move).

```js
// vérifier la case de départ (1 fois, hors boucle)
if (isAlienAbove()) { shoot() }

// puis pour les 19 cases suivantes : bouger PUIS vérifier
repeat(19){
  move()
  if (isAlienAbove()) { shoot() }
}
```

**Analogie poteaux/clôture** : pour 20 poteaux alignés, il te faut 19 sections de grillage entre eux, pas 20.

**Où tu vas revoir ça** :
- Séparateurs : "afficher `a | b | c`" — N éléments, N-1 séparateurs. En SQL c'est `STRING_AGG` qui gère, en code procédural tu dois peeler.
- Fenêtres glissantes en analyse : premier/dernier point traités à part.

---

## 14. Tester les cas limites (edge cases)

Quand ton code a des seuils ou des branches conditionnelles, **teste toujours mentalement les valeurs pile sur le seuil, juste en dessous, juste au-dessus** avant de lancer.

Exemple digital clock 24h → 12h. Les 4 cas limites : `0`, `11`, `12`, `23`.

| hour24 | Branche prise | Résultat obtenu | Attendu | OK ? |
|--------|---------------|-----------------|---------|------|
| 0      | `=== 0`       | 12am            | 12am    | ✅   |
| 11     | `else`        | -1am (bug !)    | 11am    | ❌   |
| 12     | `> 11`        | 0pm (bug !)     | 12pm    | ❌   |
| 23     | `> 11`        | 11pm            | 11pm    | ✅   |

Deux bugs trouvés **sans lancer le code**, juste en faisant le tableau.

**Où tu vas revoir ça** : partout où tu écris des règles de détection AML avec des seuils (montant > 10 000, ancienneté < 30 jours, etc.). Le bug est presque toujours sur `<` vs `<=`. Teste pile sur la valeur du seuil.

**Règle** : dès qu'il y a un `if`, liste les valeurs frontières et passe-les mentalement dans chaque branche.

---

## 15. Opérateurs logiques `&&` et `||`

Pour combiner plusieurs conditions dans un `if` :

- `&&` = "ET" — les deux doivent être vraies
- `||` = "OU" — au moins une doit être vraie

```js
if (y === "rock" && a === "scissors") { ... }  // ET
if (hour === 0 || hour === 12) { ... }         // OU
```

**Parenthèses** : quand tu mélanges `&&` et `||`, mets des parenthèses pour être sûr de la priorité. `&&` est prioritaire sur `||` (comme `×` sur `+`) mais mieux vaut être explicite.

```js
if ((y === "rock" && a === "scissors") ||
    (y === "paper" && a === "rock") ||
    (y === "scissors" && a === "paper")) {
  // Yuki gagne
}
```

---

## 16. Piège des typos silencieuses sur les strings

En JS, comparer une variable à une string mal orthographiée **ne lève aucune erreur** — le test retourne juste `false` toujours.

```js
if (y === "papper") { ... }   // "papper" ≠ "paper"
                              // → toujours false, aucune alerte
```

Idem pour un appel de fonction mal orthographié : `annouceResult(...)` (sans `n`) plante avec "function is not defined" **seulement quand la ligne est exécutée**. Si la branche n'est jamais prise, tu ne verras jamais le bug.

**Parade** : mettre les strings récurrentes dans des **constantes** en haut du fichier.

```js
let PAPER = "paper"
let ROCK = "rock"
let SCISSORS = "scissors"
// puis y === PAPER partout
```

Avantage : une seule chance de te tromper (dans la constante). Et un éditeur peut t'auto-compléter le nom de la constante, pas la string.

**En SQL/AML** : même piège avec les valeurs d'énumération (`"PENDING"` vs `"pending"`, `"FR"` vs `"FRA"`). Toujours vérifier les valeurs exactes en base avant de filtrer.

---

## 17. Simplifier les conditions : sortir la structure du problème

Pierre-Feuille-Ciseaux mal écrit = 3 branches longues avec 9 conditions au total :

```js
if ((y===r && a===r) || (y===p && a===p) || (y===s && a===s)) { tie }
else if ((y===r && a===s) || (y===p && a===r) || (y===s && a===p)) { yuki }
else if ((a===r && y===s) || (a===p && y===r) || (a===s && y===p)) { ando }
```

Mieux écrit : on utilise deux propriétés du problème.
1. **Égalité** = même choix → 1 seul test `y === a`
2. **Exhaustivité** = s'il n'y a pas égalité et que Yuki ne gagne pas, Ando gagne forcément → pas besoin de retester

```js
if (y === a) { tie }
else if (yukiGagne) { yuki }
else { ando }
```

De 9 tests à 4. Moins de risque de typo, plus facile à lire.

**Le concept général** : avant d'écrire une cascade de `if`, cherche si le problème a une propriété qui te permet de simplifier (symétrie, exhaustivité, égalité). C'est la différence entre "coder ce qu'on voit" et "coder ce qu'on comprend".

**En AML** : au lieu d'énumérer 12 typologies de fraude avec 12 `if`, cherche l'attribut commun (montant, fréquence, corridor) et regroupe.

---

## 18. Comparer un booléen à `true` / `false` est redondant

Un booléen est **déjà** une valeur vraie ou fausse. Pas besoin de le comparer à `true`.

```js
if (guest === true)  { ... }  // ❌ bruyant
if (guest)           { ... }  // ✅ propre

if (guest === false) { ... }  // ❌ bruyant
if (!guest)          { ... }  // ✅ propre — le "!" veut dire "pas"
```

Le `!` inverse : `!true` = `false`, `!false` = `true`.

**Se dire mentalement** : "if (guest)" se lit "si le gars est sur la liste". "if (!guest)" se lit "si le gars n'est PAS sur la liste". Ça sonne comme une phrase normale.

**Réserve `===` aux comparaisons de vraies valeurs** (chiffres, strings) : `age >= 18`, `outfit === "suit"`.

---

## 19. Branches d'un `if/else if/else` : disjointes ET nécessaires

Une cascade propre a deux propriétés :

**Disjointes** : les conditions ne se chevauchent pas. Un cas ne peut matcher qu'une seule branche. Sinon l'ordre devient piégeux.

**Nécessaires** : chaque branche fait quelque chose de **différent**. Si deux branches font la même action, fusionne-les.

Exemple à traquer :
```js
else if (style === "beauf" && ...) { turnAway() }
else                               { turnAway() }
```
→ Les deux font `turnAway()` → la première est inutile. Le `else` final ramasse tout ce qui n'a matché nulle part.

**Règle** : le `else` final est la poubelle par défaut. Ne re-spécifie pas les conditions dedans, il attrape déjà tout le reste.

**En SQL** : même règle dans un `CASE WHEN`. Chaque `WHEN` doit ajouter une info nouvelle. Le `ELSE` final ramasse le reste sans qu'on ait à le re-décrire.

---

## 20. Variables booléennes nommées pour rendre le code lisible

Au lieu de retaper des tests longs, extrais-les dans des variables au nom parlant.

```js
// ❌ verbeux, se relit mal
if ((outfit === "ballgown" || outfit === "tuxedo") ||
    (outfit === "suit" || outfit === "dress")) { ... }

// ✅ le code se lit comme la règle métier
let isFormal = (outfit === "ballgown" || outfit === "tuxedo")
let isSmart  = (outfit === "suit"     || outfit === "dress")

if (isFormal || isSmart) { ... }
if (isFormal && age >= 18) { offerChampagne() }
```

Avantages :
1. Le `if` se lit comme la règle métier ("if formal or smart")
2. Si la définition de "formal" change, un seul endroit à modifier
3. Facile de tester une nouvelle règle : `if (isFormal && guest) { ... }`

**Nom** : préfixe `is`, `has`, `can` pour signaler que c'est un booléen (`isFormal`, `hasEntrance`, `canDrink`). Convention universelle en programmation.

**En SQL/AML** : même principe avec des colonnes calculées nommées (`is_high_risk`, `is_pep`) dans une CTE, réutilisables dans le `WHERE` et le `SELECT`.

---

## 21. Traduire les mots-clés métier en structures de code

Dans un énoncé de règle, certains mots signalent la structure à écrire :

| Mot dans la règle | Structure de code |
|-------------------|-------------------|
| "or"              | `||`              |
| "and"             | `&&`              |
| "also"            | `if` **imbriqué dans** une branche existante (pas une nouvelle branche) |
| "only if"         | `if` seul (branche unique) |
| "otherwise" / "everyone else" | `else` final |
| "regardless of"   | condition à **enlever**, pas à ajouter |

Exemple bouncer : *"Adults in formal ALSO get champagne"* → `also` signale un `if` imbriqué dans la branche `formal`, pas une branche à part.

Cette traduction directe évite d'inventer une logique qui ne colle pas à la règle.

---

## 22. Le compteur d'index `i` (que TU crées, pas un cadeau de la machine)

Point de blocage central de l'exercice "stripey fabric" : `i` **n'est pas** fourni par la plateforme ni le retour d'une fonction (comme `getShotLength()`). C'est **une boîte que tu crées toi-même**, exactement comme `x` au golf.

Rôle : **numéroter** le tour de boucle en cours (ici : la stripe n°`i`, de 1 à 20).

```js
let i = 1        // avant la boucle : on démarre à 1

repeat(20){
  // ... utiliser i (position, couleur) ...
  i = i + 1      // EN DERNIER : avancer pour le tour suivant (concept #8)
}
```

Même pattern que `x = x + 1` au golf. La différence : `x` *positionnait* la balle, `i` *numérote* pour ensuite en déduire position et couleur.

**Piège associé** (déjà rencontré, cf. #8) : `i = i + 1` doit être **en dernier** dans la boucle. Si tu l'oublies, `i` reste bloqué à 1 → les 20 tours font tous exactement la même chose.

### Déduire la position à partir de l'index : `(i - 1) * largeur`

N stripes de 5 de large, collées, la 1re au bord (position 0). `rectangle(left, ...)` veut le **bord gauche**.

```
stripe n°1 → 0 stripe avant elle → (1-1)*5 = 0
stripe n°2 → 1 stripe avant elle → (2-1)*5 = 5
stripe n°3 → 2 stripes avant elle → (3-1)*5 = 10
```

**Le `-1` corrige le décalage** : on compte *combien d'éléments sont avant moi*, pas mon propre numéro. Avec `i * 5`, la stripe 1 démarrerait à 5 → trou vide au début. Vérif de bord : stripe 20 → `(20-1)*5 = 95`, et `95 + 5 = 100` = pile le bord du canvas. ✅

**Piège #6 qui revient** : `let left = (i-1)*5` doit être **dans** la boucle (recalculé à chaque tour), sinon figé sur la valeur de `i=1`.

---

## 23. Le remainder / modulo `%` : forcer un compteur infini dans un cycle fixe

### Définition

`%` = le **reste** de la division posée à l'école. Tu ignores le quotient, tu ne gardes que le reste.

```
13 ÷ 4 = 3 reste 1   →   13 % 4 = 1
```

### Pourquoi ça "boucle"

Le reste d'une division par `k` est **toujours** entre `0` et `k-1` — jamais `k`, jamais négatif. Donc si `i` monte (1, 2, 3, 4, 5…), `i % 4` tourne en rond : `1, 2, 3, 0, 1, 2, 3, 0…`

| i | i % 4 |
|---|-------|
| 1 | 1 |
| 2 | 2 |
| 3 | 3 |
| 4 | 0 |
| 5 | 1 |
| 8 | 0 |

**Analogie** : playlist de 4 chansons en boucle. Piste n°37 ? `37 % 4 = 1` → tu tombes sur la chanson 1 du cycle, sans compter 37 fois.

### Le nombre après `%` = la taille du motif qui se répète

- Cycle de 4 couleurs → `% 4` (restes possibles : 0,1,2,3)
- Cycle de 5 → `% 5` (restes : 0,1,2,3,4)
- Cycle de 7 → `% 7`

Toute la logique (if/elif sur le reste) reste identique ; seul le diviseur change.

### Traduire un cycle en if/elif

Un cycle de N couleurs → N branches, une par valeur de reste. On lit la table ligne par ligne :

```js
let color = ""
let i = 1
repeat(20){
  let left = (i - 1) * 5

  if (i === 1 || i === 20){       // cas spéciaux EN PREMIER (premier match gagne, cf. #19)
    color = "purple"
  } else if (i % 4 === 2){
    color = "blue"
  } else if (i % 4 === 0){
    color = "green"
  } else {                        // i%4 === 1 OU 3 → les deux impairs
    color = "yellow"
  }

  rectangle(left, 0, 5, 100, color)   // UN SEUL appel, après le if
  i = i + 1
}
```

**Piège vécu** : le cycle est calé sur le **numéro de stripe directement** (stripe 1 = 1re position du cycle, même si écrasée par purple). Bien vérifier l'alignement du cycle avec un cas test que la plateforme te donne (ici "stripe 2 = blue") avant de coder — sinon tu codes correctement une table fausse.

### Où tu vas revoir ça (AML / data)

- **pair/impair** : `n % 2 == 0`
- **zebra striping** d'un rapport : une ligne sur deux en gris → `ligne % 2`
- **round-robin** : distribuer les alertes à 4 analystes → `alerte % 4` donne 0-3
- **échantillonnage QA** : contrôler 1 transaction sur 10 → `if (i % 10 == 0)`
- **jour de la semaine** depuis un jour de référence → `numero % 7`

Point commun : une valeur qui monte à l'infini (n° de ligne, d'alerte, de jour), forcée à retomber dans un petit cycle fixe.

**En Python** : `%` fonctionne pareil (`13 % 4` → `1`). À réutiliser tel quel.

---

## 24. `if` séparés vs cascade `if/else if` : actions indépendantes vs exclusives

Deux structures qui se ressemblent mais font l'opposé. Le choix dépend d'une seule question : **plusieurs actions peuvent-elles se déclencher en même temps ?**

**`if` séparés** — chaque action est indépendante, plusieurs peuvent arriver dans le même scénario :
```js
if (condA) { actionA() }
if (condB) { actionB() }   // testé même si condA était vraie
if (condC) { actionC() }
```

**Cascade `if / else if`** — actions **mutuellement exclusives**, une seule gagne (le premier match, cf. #19) :
```js
if (condA) { actionA() }
else if (condB) { actionB() }   // ignoré si condA était vraie
```

Exemple Annalyn's Infiltration : *"Perform each action you can"* → spy, signal, attack, free sont **indépendantes** (on peut espionner ET attaquer ET libérer). Donc **4 `if` séparés**, surtout pas une cascade. Une cascade aurait bloqué toutes les actions après la première qui match.

**Réflexe** : "each action you can" / "do all that apply" → `if` séparés. "do the first that matches" / "otherwise" → cascade.

---

## 25. Ne coder QUE ce qui est écrit — la condition-piège

Le vrai skill sur les règles complexes n'est pas le code, c'est **traduire une spec sans rien inventer ni oublier**. Deux erreurs symétriques, vécues sur Annalyn :

**Erreur A — inventer une condition absente.** Règle "signal si prisoner awake et archer asleep" → j'avais ajouté `&& knightIsAwake()`. Le knight n'était pas dans la règle. Toute condition que tu ne peux pas pointer dans le texte = à supprimer.

**Erreur B — coder une info qui dit "ça n'a pas d'importance".** Règle du chien : *"the knight is terrified of dogs so won't fight back"* → j'avais mis `!knightIsAwake()`. Or "won't fight back" veut dire **le knight ne bloque rien** : c'est un *"regardless of the knight"* (cf. #21) → condition à **enlever**, pas à ajouter. Une phrase qui neutralise un acteur est un piège : elle ressemble à une contrainte, c'en est l'inverse.

**Méthode** : pour chaque acteur mentionné, se demander *"cette phrase ajoute une condition, ou dit-elle que cet acteur n'a pas d'effet ?"*. Puis pour chaque condition écrite, la pointer dans le texte. Si tu ne peux pas → elle n'a rien à faire là.

**Fusionner deux règles → une condition.** Quand deux règles déclenchent la **même** action (`freePrisoner` via chien OU via Annalyn), on ne double pas le `if` — on combine les deux conditions avec `||`, chacune entre parenthèses :
```js
if ( (dogIsBehaving() && !archerIsAwake()) ||
     (prisonerIsAwake() && !knightIsAwake() && !archerIsAwake()) ) {
  freePrisoner()
}
```

**En AML** : c'est exactement écrire une règle de détection depuis une spec compliance. Ne coder que les critères listés ; une phrase du genre "peu importe le pays" = critère à retirer du `WHERE`, pas à ajouter.

---

## Récap ultra-condensé (à relire avant d'attaquer un nouvel exercice)

1. Une fonction = machine avec input(s) et parfois un retour
2. Attrape toujours le retour (boîte OU utilisation directe), sinon il est perdu
3. Variable = boîte étiquetée ; `=` remplace le contenu
4. Accumulateur : `total = total + valeur` dans une boucle
5. `repeat(N){}` répète N fois, N peut être une variable/fonction
6. **RÉFLEXE** : "cette ligne est appelée combien de fois ?" → si tu veux N valeurs différentes, la ligne doit être dans la boucle
7. Portée : garde une variable au niveau où elle doit survivre
8. Ordre dans la boucle : utiliser d'abord, faire avancer les compteurs à la fin
9. Paramétrer avec des variables (`center`, `spacing`) au lieu de valeurs en dur
10. Intérêts composés : `V = V × (1 + X/100)`
11. N éléments uniformes sur 100 avec marges : `espacement = 100 / (N+1)`
12. `if` sans `else` = action optionnelle par-dessus une obligatoire
13. Loop peeling : sortir la 1re ou dernière itération quand elle est différente
14. Tester les cas limites mentalement avant de lancer (valeur pile sur le seuil, juste en dessous, juste au-dessus)
15. `&&` (ET) et `||` (OU) — mets des parenthèses quand tu mélanges
16. Typos silencieuses sur strings → mets les valeurs récurrentes dans des constantes
17. Simplifier les cascades de `if` en cherchant symétrie / exhaustivité / égalité dans le problème
18. Pas de `=== true` ni `=== false` : `if (guest)` / `if (!guest)`
19. Branches disjointes et nécessaires ; le `else` final ramasse tout
20. Variables booléennes nommées (`isFormal`, `isSmart`) pour lisibilité
21. Traduire les mots-clés métier ("also", "regardless of", "otherwise") en structures de code
22. Compteur `i` = boîte que TU crées (`let i = 1` + `i = i + 1` en dernier) ; position = `(i-1)*largeur` (le `-1` = combien avant moi)
23. Modulo `% N` = reste de division, force un compteur infini dans un cycle de N valeurs (0 à N-1) ; N = taille du motif → cas spéciaux en premier dans le if/elif
24. `if` séparés (actions indépendantes, "do all that apply") vs cascade `if/else if` (exclusif, "the first that matches")
25. Ne coder QUE ce qui est écrit : ne pas inventer de condition absente ; une phrase qui neutralise un acteur ("won't fight back", "regardless of") = condition à ENLEVER ; deux règles → même action = fusion avec `||`

---

## Ce qui doit devenir automatique

Le vrai déclic de cette session, c'est **le point 6**. Tu es tombé 3 fois d'affilée dans le même piège (color figée dans arc-en-ciel, skyColor figée dans sunset, growth figé dans stock market). C'est **le** concept à graver.

Test mental à faire systématiquement avant de lancer :
> "Chaque ligne de mon code : elle est exécutée combien de fois, et est-ce que c'est ce que je veux ?"
