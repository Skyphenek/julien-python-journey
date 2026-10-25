---
titre: Python 05 — Appels API (requests, JSON, clés secrètes)
date: 2026-08-05
parcours: python
source: ~/Claude/Work/perso/python/julien-python-journey/voyage/api_meteo.py
---

> **Ce que cette session débloque** : interroger une API web depuis Python (`requests`), lire une réponse JSON imbriquée sans deviner sa forme, et stocker une clé API sans jamais la faire fuiter.

Contexte : objectif S4 du programme — sortir `valise.py` du mapping pays→climat codé en dur. Session isolée du code existant : 3 scripts à part (`api_pays.py`, `api_geo.py`, `api_meteo.py`), rien touché dans `valise.py` pour l'instant.

---

## 1. `requests.get()` — le modèle mental

**Analogie** : `requests.get(url)` = tu envoies une lettre à une adresse (l'URL) et tu attends la réponse du facteur. La réponse arrive avec un **code sur l'enveloppe** (le statut HTTP — `200` = tout va bien) et un **contenu à l'intérieur** (le JSON, à décoder avec `.json()`).

```python
import requests

reponse = requests.get("https://geocoding-api.open-meteo.com/v1/search?name=Hanoi")
print(reponse.status_code)   # 200 = ça a marché
data = reponse.json()        # décode le contenu JSON en objets Python (dict/liste)
```

**Piège découvert en vrai** : un `status_code` à `200` ne garantit pas que la donnée est bonne. Une API peut répondre `200` avec un corps du genre `{"success": false, "errors": [...]}`. Le code sur l'enveloppe dit juste « le facteur a livré », pas « le contenu te plaira ».

---

## 2. `.json()` ne rend jamais la même forme deux fois

**La règle qui compte** : ne JAMAIS supposer la forme d'une réponse API sans la vérifier — même deux endpoints de recherche du même style peuvent différer.

Trois formes rencontrées dans la même session :

```python
# REST Countries (dépréciée) : une LISTE nue de dicts
[{"name": {...}, "capital": ["Hanoi"], ...}]

# Open-Meteo géocodage : un DICT, la liste planquée derrière une clé
{"results": [{"name": "Hanoï", "country": "Viêt Nam", ...}]}

# Open-Meteo météo : un DICT de DICTS, pas de liste du tout
{"current": {"temperature_2m": 25.6, "precipitation": 0.4}}
```

**Où ça revient** : avant d'écrire `data["quelque_chose"][0]`, toujours regarder un exemple réel de la réponse (`print(data)` ou doc de l'API) plutôt que de calquer le chemin de la dernière API utilisée.

---

## 3. Piège récurrent — `dict["clé"]` ne rend QUE la valeur

Erreur commise deux fois en session : répondre `"temperature_2m": 25.6` au lieu de `25.6` pour `etape_1["temperature_2m"]`.

**Analogie (fiche cartonnée)** : tu soulèves l'onglet `"temperature_2m"`, tu ne ramènes pas l'étiquette de l'onglet avec toi — juste ce qu'il y a écrit dessous.

```python
d = {"temperature_2m": 25.6}
d["temperature_2m"]   # -> 25.6           (juste la valeur)
                       # PAS "temperature_2m": 25.6
```

---

## 4. Décomposer un chemin imbriqué avant de le compacter

Un chemin du type `data["results"][0]["country"]` mélange deux mécaniques différentes (dict → clé, liste → index). Tant que ce n'est pas fluide, on le déroule en variables séparées :

```python
etape_a = data["results"]        # dict + clé "results"  -> une liste
etape_b = etape_a[0]             # liste + index 0        -> le premier dict
etape_c = etape_b["country"]     # dict + clé "country"   -> la valeur finale
```

**La règle qui compte** : `[0]` fait toujours la même chose — « donne-moi ce qu'il y a à la première place » — peu importe que cette place contienne une string, un nombre ou un dict entier. Le symbole `[ ]` change de sens selon ce qui est à sa gauche (dict → cherche par clé ; liste → cherche par position), pas selon ce qu'il contient.

Une fois les 3 étapes validées séparément, elles s'écrivent en une ligne : `data["results"][0]["country"]`.

---

## 5. Une API peut casser, se déprécier ou devenir payante

Vécu en direct : REST Countries v3.1 (prévue au plan) est dépréciée, remplacée par une v5 qui exige une clé payante et renvoie une structure beaucoup plus imbriquée (traductions sur 30+ langues par champ).

**Décision prise en session** : ne pas s'entêter sur l'API prévue au départ. Bascule complète vers Open-Meteo (géocodage + météo), qui couvre le même besoin (pays, coordonnées, timezone) sans clé et avec une structure plus plate.

**La règle qui compte** : avant de construire sur une API externe, un test rapide (`curl` ou script minimal) vaut mieux qu'un plan basé sur une doc qui a pu changer. Le plan s'ajuste à ce qu'on observe, pas l'inverse.

---

## 6. Stocker une clé API sans la faire fuiter

Clé REST Countries obtenue mais pas utilisée cette session (gardée en réserve). Méthode mise en place :

1. **Jamais dans le chat** — même en local, l'historique Claude Code est écrit en clair sur le disque.
2. **Un fichier `.env`**, rempli par Julien directement dans son éditeur (pas collé dans la conversation) :
   ```
   RESTCOUNTRIES_API_KEY=ta_vraie_cle
   ```
3. **`.env` ajouté au `.gitignore`** — avant même que la clé y soit écrite, pour ne jamais risquer un commit accidentel.
4. **Lecture en Python via `python-dotenv`** :
   ```python
   from dotenv import load_dotenv
   import os

   load_dotenv()
   cle = os.environ["RESTCOUNTRIES_API_KEY"]
   ```

**Où ça revient** : tout projet qui touche une API payante ou un service externe (Notion, Claude API...) — même mécanique à chaque fois.

---

## 7. Environnement virtuel (venv) — pourquoi c'était nécessaire

`pip install requests` en direct a été bloqué par macOS/Homebrew (PEP 668, "externally managed environment"). Un venv = un tiroir à outils dédié à ce projet, isolé du reste du Mac.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install requests python-dotenv
```

**La règle qui compte** : à partir de maintenant, activer le venv (`source .venv/bin/activate`) avant de lancer un script du dossier `voyage/` qui utilise `requests` ou `dotenv`. Le `.venv/` est aussi allé dans le `.gitignore` — un environnement virtuel ne se commite jamais (trop lourd, recréable en une commande).

---

## Bugs typiques (récap)

| Symptôme | Cause | Fix |
|----------|-------|-----|
| `KeyError: 0` sur `reponse.json()[0]` | `.json()` a renvoyé un dict, pas une liste (API dépréciée, payload d'erreur) | vérifier la forme réelle avant d'indexer |
| Réponse `"clé": valeur"` au lieu de `valeur` | confusion entre la clé et ce qu'elle contient | `dict["clé"]` renvoie toujours SEULEMENT la valeur |
| `ModuleNotFoundError: No module named 'requests'` | pip bloqué par l'environnement système (PEP 668) | créer et activer un venv avant d'installer |
| Notif VS Code "terminal environment injection is disabled" | réglage sans rapport — `python-dotenv` lit le `.env` depuis le code, pas via le terminal | ignorer, aucune action requise |

---

## À retenir pour la suite

- **Validé** : `requests.get()` + `.json()`, décomposition d'un chemin imbriqué en étapes, `.env`/`.gitignore`/`python-dotenv` pour une clé API.
- **À surveiller** : compacter un chemin dict/liste en une ligne directement (`data["a"][0]["b"]`) sans repasser par les variables intermédiaires — pas encore automatique.
- **Pas encore fait** : brancher `api_meteo.py` dans `valise.py`. La météo *actuelle* ne sert à rien pour un voyage dans 5 mois — il faudra l'API "historique"/moyennes climatiques d'Open-Meteo (nouvelle notion : plages de dates). Session à part.
