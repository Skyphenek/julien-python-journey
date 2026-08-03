# 🏀 L'Arène NBA

Un jeu de terminal pour **travailler tes gammes Python** en t'amusant, sur des vraies stats NBA.

## Lancer

```bash
cd arene-nba
python3 arene.py
```

## Le principe (v1 = les gammes)

Consolider les 4 briques que tu maîtrises déjà, jusqu'au réflexe, par la répétition et les variations :

| Brique | Ce que tu muscles | Équivalent SQL |
|---|---|---|
| **Dictionnaires** | agréger par clé (`.get`, `max(d, key=d.get)`) | `GROUP BY` |
| **Comprehensions** | filtrer & transformer en une ligne | `SELECT … WHERE` |
| **sorted + lambda** | trier par un critère calculé | `ORDER BY` |
| **Sets** | unicité, intersection / différence | `DISTINCT` |

Le jeu fait tourner les 4 briques en alternance et monte la difficulté à l'intérieur de chacune
au fur et à mesure que tu valides les défis faciles.

## Trois types de manches

- **🔮 Prédire** — je montre du code, tu tapes ce qu'il affiche.
- **⚡ One-liner** — tu tapes **une** expression Python, directement dans le terminal.
- **✍️ Fonction** — tu écris la fonction dans `reponse.py` sous VS Code, tu sauvegardes,
  puis **Entrée** dans l'Arène pour lancer les tests cachés.

## Commandes (au prompt de réponse)

| Touche | Effet |
|---|---|
| `i` | indice suivant (3 max, socratiques) |
| `sol` | solution complète (débloquée après les 3 indices) |
| `p` | passer la manche |
| `q` | quitter (le bilan s'affiche) |

## Score & saison

- Points par manche selon la difficulté ; chaque indice consommé en retire un peu.
- **Combo** : 3 réussites d'affilée → ×2, puis ×3, ×4. Un buzzer (mauvaise réponse) remet le combo à zéro.
- Ta progression (score, record de streak, défis validés) est sauvegardée dans `progression.json` :
  tu reprends où tu t'es arrêté à chaque lancement.

## Fichiers

| Fichier | Rôle |
|---|---|
| `arene.py` | boucle de jeu, affichage, score/combo — le point d'entrée |
| `data_nba.py` | dataset NBA embarqué (offline, ~18 joueurs) |
| `defis.py` | banque de défis (24 en v1) + indices + solutions |
| `moteur.py` | évaluation, indices, persistance, sélection par les gammes |
| `reponse.py` | brouillon regénéré pour les manches « fonction » (gitignored) |
| `progression.json` | ta saison sauvegardée (gitignored) |

## Phase 2 (plus tard)

Débloquer des briques neuves une à la fois (`try/except`, `itertools`, décorateurs…) après un streak.
L'architecture est déjà prévue : il suffira d'ajouter des défis dans `defis.py` avec une nouvelle
valeur `brique` — aucune refonte du moteur.
