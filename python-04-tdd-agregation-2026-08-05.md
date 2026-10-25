---
titre: Python 04 — TDD, pytest, et patterns d'agrégation
date: 2026-08-05
parcours: python
source: ~/Claude/Work/perso/python/julien-python-journey/voyage/valise.py
---

> **Ce que cette session débloque** : écrire des tests qui *prouvent* le comportement avant de coder (TDD), et reconnaître les patterns d'agrégation quand on transforme une liste en résumé (somme, drapeau, ensemble, accumulation).

Contexte : projet `valise.py`. On l'a fait passer d'une destination unique à un **itinéraire multi-étapes** (plusieurs villes / climats sur un même voyage), avec des quantités dimensionnées climat par climat. Le tout construit en TDD, test par test.

---

## 1. Le cycle TDD : rouge → vert

**Analogie** : tu écris d'abord la *facture de recette* (ce que le plat doit contenir), tu vérifies que la cuisine est vide (rouge), puis tu cuisines jusqu'à ce que la facture soit satisfaite (vert).

Les 4 temps, à chaque fonction :
1. écrire un **test** qui décrit le comportement attendu,
2. le lancer → il **échoue** (rouge : la fonction n'existe pas / est fausse),
3. écrire la fonction,
4. relancer → **vert**.

**La règle qui compte** : le test vient AVANT le code. Ça force à définir le comportement au lieu de coder au feeling puis "tester si ça marche".

**Où ça revient** : toute logique métier un peu subtile (règles AML, calcul de score) — le test devient la spec exécutable.

---

## 2. pytest — le minimum

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))   # pour importer un module du même dossier

from valise import total_jours


def test_total_jours():
    itin = [{"destination": "Hanoï", "jours": 7, "mois": 1}]
    assert total_jours(itin) == 7
```

- Le préfixe **`test_`** (fichier ET fonction) n'est pas décoratif : c'est comme ça que pytest les repère.
- **`assert x == y`** = « je déclare que c'est vrai ». Si c'est faux, pytest fait échouer le test ET te montre la vraie valeur (`assert 6 == 2`).
- Les 3 lignes `sys` / `Path` = boilerplate pour qu'un test lancé par pytest retrouve ton module dans un projet plat. Tu les remets telles quelles.
- Lancer : `python3 -m pytest test_valise.py -v` (avec `python3 -m pytest`, PAS le bouton ▶️ de VS Code — le bouton exécute le fichier comme un script normal au lieu de laisser pytest piloter).

---

## 3. Le piège : le test qui ne distingue rien

**La leçon la plus importante de la session.** Après avoir changé le moteur de calcul, **13 tests sont restés verts alors que le nouveau code n'était pas encore écrit**.

Pourquoi ? Le test choisi ne séparait pas l'ancien comportement du nouveau :

```python
# shorts voulu par chaud (18j→6) ET plage (7j→2)
assert valise["Julien"]["Vêtements"]["shorts"] == 6
# ancien moteur : dimensionné sur 18 → 6
# nouveau moteur : max(6, 2)  → 6
# MÊME réponse → le test ne teste rien
```

Le test qui **distingue** : un objet réclamé par UN SEUL climat court.

```python
# maillot n'existe QUE dans "plage" ; plage = 7j sur 18 total
assert valise["Julien"]["Vêtements"]["maillot"] == 2
# ancien moteur : 18//3 = 6  ❌
# nouveau moteur : 7//3  = 2  ✅
```

**La règle qui compte** : *un test qui reste vert quand tu changes le comportement ne teste pas ce comportement.* Toujours vérifier qu'un test **peut** échouer (le voir rouge au moins une fois).

---

## 4. Lire une erreur au lieu de deviner

Trois erreurs vécues, chacune se lit littéralement :

```
SyntaxError: closing parenthesis ']' does not match opening parenthesis '{' on line 27
```
→ « ligne 27 tu as ouvert avec `{`, tu refermes avec `]` ». Python compte les paires. (Piège AZERTY : `[` = Alt+Shift+( et `{` = Alt+( — même touche.)

```
SyntaxError: expected '('
```
→ sur une ligne `def`, il manque les `()`. Toute ligne `def nom` finit par `():`.

```
ValueError: too many values to unpack (expected 2)
```
→ voir section 5.

**La règle qui compte** : le message d'erreur pointe la ligne ET la cause. Lis-le avant de toucher au code.

---

## 5. Bug clé — itérer une liste-de-dicts

**Le bug** :

```python
# itineraire = [{"destination": "Hanoï", "jours": 7, "mois": 1}, ...]
return sum(nb for ville, nb in itineraire)     # ❌ ValueError: too many values to unpack
```

`for ville, nb in itineraire` suppose que chaque élément est une **paire** `(ville, nb)`. Mais chaque élément est un **dict entier** (3 clés). Python ne peut pas le déballer dans 2 variables.

**Le fix** — on itère les dicts, on va chercher la clé :

```python
return sum(etape["jours"] for etape in itineraire)   # ✅
```

**Rappel du modèle** (vu en python-02) : une liste-de-dicts = un classeur de fiches. On feuillette fiche par fiche (`for etape in ...`), puis on lit l'étiquette voulue (`etape["jours"]`).

---

## 6. Deux patterns d'agrégation à reconnaître

Transformer une liste en **un** résumé. Selon ce qu'on veut, l'accumulateur change.

**a) Drapeau booléen — « au moins un ? »** (= `EXISTS` SQL)

```python
hors_ue = False
for etape in itineraire:
    if statut_ue(etape["destination"]) == "hors_ue":
        hors_ue = True        # se lève une fois, ne redescend jamais
return hors_ue
```
On ne garde AUCUN détail, juste « oui/non ».

**b) Récolte dans un set — « lesquels, sans doublon ? »** (= `SELECT DISTINCT`)

```python
prises = set()                        # le set déduplique tout seul
for etape in itineraire:
    prise = adaptateur_pour(etape["destination"])
    if prise != "aucun":
        prises.add(prise)             # .add() pour un set (PAS .append(), ça c'est pour les listes)
return prises
```

**c) Somme par clé** (= `SUM ... GROUP BY`) — le pattern word_count revu :

```python
jours = {}
for etape in itineraire:
    for type_dest in types_pour(etape["destination"], etape["mois"]):
        jours[type_dest] = jours.get(type_dest, 0) + etape["jours"]
```
Comme le comptage de mots, mais on ajoute `etape["jours"]` au lieu de `+ 1`.

**La règle qui compte** : avant de coder une boucle d'agrégation, demande-toi ce que tu construis — un booléen, un ensemble, ou un dict de sommes ? Ça décide de l'accumulateur.

---

## 7. Le pattern accumuler-puis-finaliser

Quand un même élément reçoit des contributions de **plusieurs sources** et qu'on ne peut trancher qu'après les avoir toutes vues : deux temps.

```python
def _remplir(paquet, base_tables, type_tables, jours_types, total):
    base_q = {}          # panier 1 : quantités de base
    climat_q = {}        # panier 2 : max des quantités climatiques
    climat_zero = set()  # panier 3 : objets qu'un climat veut retirer

    # Temps 1 — RÉCOLTER (on ne décide rien encore)
    for table in base_tables:
        for objet, marqueur in table.items():
            q = quantite_reelle(marqueur, total)
            if q > 0:
                base_q[objet] = max(base_q.get(objet, 0), q)
    # ... idem pour les climats dans climat_q / climat_zero ...

    # Temps 2 — FINALISER (maintenant qu'on a tout vu)
    for objet in set(base_q) | set(climat_q) | climat_zero:
        cq = climat_q.get(objet, 0)
        if objet in climat_zero and cq == 0:
            continue                                  # supprimé
        quantite = max(base_q.get(objet, 0), cq)
        if quantite > 0:
            paquet[theme_de(objet)][objet] = quantite
```

**La règle qui compte** : si la décision finale dépend de sources qu'on n'a pas encore toutes vues, on **récolte d'abord dans des paniers séparés, on tranche à la fin**. Ne pas essayer de décider en cours de route.

Rappel : `set(a) | set(b)` = **union** de sets (tous les objets vus, sans doublon).

---

## Bugs typiques (récap)

| Symptôme | Cause | Fix |
|----------|-------|-----|
| `too many values to unpack (expected 2)` | `for ville, nb in liste_de_dicts` | `for etape in liste` puis `etape["clé"]` |
| `closing parenthesis ']' does not match '{'` | crochet/accolade mélangés (AZERTY) | vérifier la paire ligne indiquée |
| `expected '('` sur un `def` | `()` manquants | `def nom():` |
| 13 tests verts sans code écrit | test qui ne distingue pas | choisir un cas qui échoue sur l'ancien code |
| ligne de code coupée au collage | copier depuis le terminal enroule les longues lignes | pour les pavés, écrire direct dans le fichier |

---

## À retenir pour la suite

- **Validé** : cycle TDD, structure pytest, les 3 patterns d'agrégation, le pattern récolter-puis-finaliser.
- **À surveiller** : reconnaître *tout seul* quel pattern d'agrégation appliquer face à un nouveau problème (c'est le vrai saut).
- **Méthodo** : pour les gros pavés de code, on écrit direct dans le fichier (le copier-coller depuis le terminal tronque) ; Julien garde la main sur les petits bouts à forte valeur d'apprentissage (une condition, une ligne d'accumulation).
