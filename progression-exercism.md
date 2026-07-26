# Progression Exercism — Track Python

> Suivi des exercices Exercism. Collection annotée : `~/Downloads/Exercism/python/NN-nom/`
> Cours interactif : `cours-python-complet-2026-07-22.html` (un chapitre par exo)

## 🏁 Concept exercises — TERMINÉS (17/17) le 26/07/2026

Le parcours "concepts" complet du track Python est bouclé. Chaque exo : énoncé
traduit FR + solution codée par Julien + fichier annoté + chapitre HTML. Tous à
tests verts et Pylint 10/10.

| # | Exercice | Concept clé |
|---|----------|-------------|
| 01 | guidos-gorgeous-lasagna | fonctions, `def`/`return`, constantes |
| 02 | ghost-gobble-arcade-game | booléens `and`/`or`/`not` |
| 03 | currency-exchange | nombres, `/` vs `//` vs `%` |
| 04 | black-jack | conditions, comparaisons |
| 05 | little-sisters-vocab | strings : index, slicing, `join`/`split` |
| 06 | little-sisters-essay | méthodes de string (`.title`, `.strip`…) |
| 07 | card-games | listes |
| 08 | chaitanas-colossal-coaster | méthodes de liste |
| 09 | meltdown-mitigation | conditions, comparaisons chaînées |
| 10 | making-the-grade | boucles, `range`, `enumerate` |
| 11 | tisbury-treasure-hunt | tuples |
| 12 | inventory-management | dictionnaires |
| 13 | mecha-munch-management | dict avancé (`.items()`, tri, `fromkeys`) |
| 14 | locomotive-engineer | `*args` / `**kwargs`, unpacking |
| 15 | cater-waiter | sets (`&` `|` `-` `.issubset`) |
| 16 | ellens-alien-game | classes / POO (`self`, `__init__`, attribut de classe) |
| 17 | plane-tickets | générateurs (`yield`, `next()`) |

## Applications construites (hors Exercism)

Depuis le 26/07/2026, application des concepts sur des projets réels (Julien code,
tout tourne + Pylint 10/10) :

| Projet | Fichier | Concepts appliqués |
|--------|---------|--------------------|
| Monitoring AML | `aml-python/monitoring.py` | dict = `GROUP BY`+`SUM`, boucle+`.items()` = `HAVING`, `main()` |
| Assistant valise | `voyage/valise.py` | dicts/listes, boucle imbriquée, fonction helper, DRY, refactoring, abstraction en couches (ville→zone→climat→types), `input()`, `max()`/`min()`, 57 destinations |

## Notions de dev "pro" acquises le 26/07/2026

- **`main()`** + `if __name__ == "__main__"` : garder l'espace global propre (évite W0621).
- **Fonction helper + DRY** ("Don't Repeat Yourself") : une règle = un seul endroit
  (`quantite_reelle` réutilisée dans 3 boucles).
- **Refactoring** : changer une structure (liste → dict) sans casser le reste.
- **Structure de données ↔ code qui la lit** : si les données passent de liste à dict,
  la boucle doit passer de `for x in ...` à `for k, v in ....items()`. (Vécu 2×.)
- **Abstraction en couches** : une couche géo (ville+mois → climat) au-dessus des types.
- **Lookup dimensionnel** (= jointures SQL) : `ville → zone → climat[saison]`.
- **`input()`** : rendre un script interactif ; `int(input())` pour un nombre,
  `input(...) == "o"` pour un booléen.
- **Exécuter un script soi-même** : `python3 chemin/fichier.py` dans le terminal.

## Environnement

- Éditeur : **VS Code** (pas Cursor). La commande `code` du PATH ouvre Cursor →
  utiliser `open -a "Visual Studio Code" <chemin>`.

## Prochaine étape

- Practice exercises Exercism : réservoir de problèmes sans cours, si besoin de drills.
- Pistes valise : croiser personne × climat ; brancher de vraies températures (quand
  lecture de CSV/API acquise, semaines 3-4) ; gérer proprement une ville inconnue.
- Piste AML : détection de structuring, agrégation par type, lecture d'un vrai export.

## Règles de style apprises (config stricte Exercism)

- Pas de noms d'une seule lettre (`i` → `seat_index`) — C0104.
- Guillemets cohérents dans un fichier — W1405 (sortir une sous-expression en
  variable plutôt qu'imbriquer `'...'` dans une f-string `"..."`).
- Docstring par fonction/méthode ; `pass` volontaire → `# pylint: disable=unnecessary-pass`.
