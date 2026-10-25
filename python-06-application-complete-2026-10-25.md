---
titre: De script à application en ligne — le projet valise
date: 2026-10-25
parcours: Python (julien-python-journey, dossier voyage/)
niveau: Découverte — code écrit par Claude, expliqué étape par étape ; à pratiquer soi-même
---

# De script à application en ligne — le projet valise

**En une phrase** : `valise.py` est passé d'un script avec des tables écrites à la main à une application en ligne (Render + Neon) qui va chercher le climat réel, se synchronise entre deux téléphones et apprend des bilans de fin de voyage.

> ⚠️ Niveau honnête : tout ce qui suit a été **vu et compris**, pas encore **produit par toi**. C'est l'équivalent de « j'ai lu la requête et je comprends ce qu'elle fait » — pas encore « je l'écris de tête ». Les exercices en fin de fiche servent à passer de l'un à l'autre.

---

## 1. Les normales climatiques : un `SELECT` en Python

**Analogie (celle de la session)** : on a écrit la requête SQL d'abord, puis on l'a traduite clause par clause.

```sql
SELECT AVG(tmax), AVG(tmin), COUNT(CASE WHEN pluie >= 1 THEN 1 END) / 10
FROM meteo_10_ans
WHERE MONTH(date) = 1
```

| SQL | Python |
|-----|--------|
| `FROM` | l'API Open-Meteo `archive-api` (10 ans de données jour par jour, gratuite, sans clé) |
| `WHERE MONTH(date) = 1` | `if int(jour[5:7]) != mois: continue` |
| `AVG(tmax)` | `sum(tmax) / len(tmax)` |
| `COUNT(... WHERE pluie >= 1)` | un compteur `jours_pluie += 1` |
| `GROUP BY MONTH(date)` | `normales_par_mois()` : le même calcul pour les 12 mois d'un coup |

```python
for i, jour in enumerate(daily["time"]):      # jour = "2024-01-10"
    if int(jour[5:7]) != mois:                 # "01" -> 1 : SUBSTRING + CAST
        continue                               # = le WHERE
    tmax.append(daily["temperature_2m_max"][i])
```

**La règle qui compte** : l'API renvoie **une liste par colonne**, pas une liste de lignes. Le jour n°`i` de `time` correspond au `tmax` n°`i`. `enumerate` donne à la fois le numéro et la valeur pour lire la même « ligne » dans chaque colonne.

**Nouveaux outils** :
- `params={...}` dans `requests.get` : `requests` construit l'URL à ta place (plus lisible qu'une f-string).
- `.get("results")` au lieu de `["results"]` : pas de plantage si la clé manque.
- `raise_for_status()` : s'arrêter proprement si l'API répond une erreur (500, quota 429).
- `*coords` : « déballe » un tuple `(51.5, -0.13)` en deux arguments.

**Leçon data** : les données sont des moyennes sur des carrés de ~25 km → elles **surestiment les petites averses tropicales** (Phu Quoc en janvier = « 10 jours de pluie » en pleine saison sèche). On a changé d'indicateur : jours **≥ 5 mm** (la vraie pluie), seuil 4/mois. Toujours confronter un indicateur à des cas dont tu connais la réalité.

---

## 2. TDD et fonctions pures : tester sans Internet

**Analogie** : tester une requête SQL sur une table de 4 lignes remplie à la main avant de la lancer sur la prod.

On sépare :
- la partie **réseau** (lente, dépend d'Internet) → pas testée automatiquement ;
- la partie **calcul** = **fonction pure** (mêmes entrées → même sortie, ne modifie rien) → testée avec de fausses données.

```python
DAILY = {"time": ["2024-01-10", "2024-01-11", "2024-02-01", "2025-01-05"],
         "temperature_2m_max": [8.0, 6.0, 20.0, 7.0], ...}

def test_moyennes_du_mois_seulement():
    n = calculer_normales(DAILY, 1, nb_annees=2)
    assert n["tmax"] == 7.0          # (8 + 6 + 7) / 3 — février ignoré
```

**Rouge → vert** : on écrit le test, on le voit échouer (preuve qu'il teste quelque chose), puis on écrit le code.

Même principe pour l'apprentissage (session 3) : `propositions(valise, historique)` calcule **sans rien modifier ni demander** → testable. Seul `main()` pose les questions.

**Injection d'une fausse fonction** : `normales_avec_cache(conn, lat, lon, mois, chercher=fausse_api)` — dans les tests, on passe une fausse API qui **compte ses appels** pour prouver que le cache marche (3 demandes → 1 seul appel).

---

## 3. Règles métier en `CASE WHEN` : les seuils

**Analogie** : un `CASE WHEN` SQL.

```python
SEUIL_CHAUD = 25          # constantes en haut du fichier : on règle sans toucher à la logique
SEUIL_FROID = 12

if n["tmax"] >= SEUIL_CHAUD:
    types.append("chaud")
elif n["tmax"] < SEUIL_FROID:     # elif : jamais chaud ET froid
    types.append("froid")
if n["tmin"] < SEUIL_FRAIS and "froid" not in types:
    types.append("frais")
```

**Ce qu'on a appris en chemin** : les anciennes tables mélangeaient deux natures de données — le **climat** (déductible des chiffres) et les **activités** (plage, ville, montagne : pas déductibles). On a séparé : climat calculé, activités saisies.

---

## 4. Saisie tolérante : faciliter la vie de l'utilisateur

```python
import unicodedata

def sans_accents(texte):
    decompose = unicodedata.normalize("NFD", texte)          # "é" -> "e" + accent
    return "".join(c for c in decompose if unicodedata.category(c) != "Mn")   # on jette l'accent
```

Ce que ça permet :
- `lire_mois("fevrier")`, `lire_mois("Janv")` → mois par **préfixe unique** (« ju » refusé : juin ou juillet ?) ;
- `lire_date("10 janv 2027")`, `"10/01/27"`, `"2027-01-10"` → découpage avec `re.split(r"[\s/-]+", texte)` ;
- `cle_objet("Bouchons d'oreilles") == cle_objet("bouchon d'oreille")` → minuscules + sans accents + sans pluriel.

**Règle** : `.strip().lower()` partout où l'utilisateur tape quelque chose.

---

## 5. Les codes pays ISO : jointure sur l'ID, pas sur le libellé

**Analogie (session)** : en SQL, on joint sur un identifiant, pas sur un nom.

L'API écrit « Viêt Nam », ta table disait « Vietnam » → la recherche échouait. Avec le code `"VN"`, plus de souci d'orthographe.

**Leçon homonymes** : « Bali » → d'abord un village en **Inde**. Le programme montre les lieux trouvés et tu choisis — puis on garde **les coordonnées du lieu choisi** (sinon une deuxième recherche retomberait sur l'Inde).

---

## 6. Postgres : upsert, JSONB, listes, clés étrangères

**Upsert** (insérer ou mettre à jour) — déjà vu pour les cases cochées, réutilisé partout :

```sql
INSERT INTO normales_climat (latitude, longitude, mois, tmin, ...)
VALUES (%s, %s, %s, %s, ...)
ON CONFLICT (latitude, longitude, mois) DO UPDATE SET tmin = EXCLUDED.tmin, ...
```

- `ON CONFLICT DO NOTHING` : pour les règles « toujours » (pas de doublon si on répond « t » deux fois).
- **Cache** : clé = coordonnées arrondies à 0,01° (~1 km) → « hanoi » et « Hanoï » tombent sur la même ligne.
- `CREATE TABLE IF NOT EXISTS` / `ADD COLUMN IF NOT EXISTS` : schéma **rejouable** sans erreur.

**Types riches** :
- `JSONB` : stocke un dict / une liste Python tel quel (les étapes d'un voyage). Envoi : `Json(itineraire)` ; lecture : revient en dict.
- `TEXT[]` : une colonne liste (`{Julien,Laetitia}`).

**Clé étrangère** :
```sql
voyage TEXT NOT NULL REFERENCES voyages(code) ON DELETE CASCADE
```
Un retour ne peut pas exister pour un voyage inconnu (la base refuse → l'API répond 400). Supprimer un voyage supprime ses retours.

**Transaction** : `DELETE` + `INSERT` puis un seul `commit()` → la photo de la valise est remplacée en entier ou pas du tout.

**Archiver plutôt que supprimer** : colonne `archive BOOLEAN` → un voyage d'essai sort de l'historique, réversible.

---

## 7. Mettre en ligne : variables d'environnement, secret, Render + Neon

**Analogie (session)** : ton Mac joue le rôle d'un mini site web visible seulement sur ton wifi ; « tant que le terminal tourne, le site existe ». Le cloud = le même site, mais sur un ordinateur qui ne dort jamais.

Même code partout, seules les **variables d'environnement** changent :

```python
url = os.environ.get("DATABASE_URL")
if url and nom_base == "valise":
    return psycopg2.connect(url)          # la base en ligne (Neon)
return psycopg2.connect(dbname=nom_base)  # la base locale — et valise_test reste TOUJOURS locale
```

- `.env` (exclu de Git par `.gitignore`) contient l'adresse et le mot de passe de la base. **Jamais dans un fichier suivi par Git** (dépôt public = mot de passe public).
- `ACCES_SECRET` : toutes les routes sous `/v/<code>/` ; sans le code → 404. Flask `Blueprint(url_prefix=...)`.
- Appels JavaScript **relatifs** (`fetch('api/etat')` et non `'/api/etat'`) pour suivre le préfixe secret.
- `requirements.txt` (bibliothèques) + `render.yaml` (recette) + `gunicorn serveur:app` (serveur de production).
- La page est stockée **en base** (`page_valise`) : générée sur le Mac, servie par le cloud, sans commit.

---

## 8. Côté page web : HTML/CSS/JS modernes

- `<details><summary>` : élément HTML qui se replie **tout seul**, sans JavaScript.
- `li:has(input:checked) { order: 1 }` : les objets cochés glissent en bas **sans toucher au HTML** (CSS pur).
- **Variables CSS** (`--fond`, `--accent`) : couleurs définies une fois, redéfinies pour le mode sombre.
- **Polling** : `setInterval(rafraichir, 4000)` relit l'état toutes les 4 s → synchro entre téléphones.
- `localStorage` : se souvenir du mode Bilan sur l'appareil.
- `textContent` (et non `innerHTML`) pour afficher un texte tapé par l'utilisateur : il n'est jamais interprété comme du code.

---

## 9. Git : branches, pull requests, fusion

- `git switch -c feat/...` : une branche par chantier.
- `git add` = préparer ta liste d'`INSERT` ; `git commit` = le `COMMIT` ; `git push -u` la première fois (relie la branche à GitHub), puis `git push`.
- `git add voyage/` : tout le dossier d'un coup — le `.gitignore` protège `.env`, `.venv/`, `valise.html`.
- Pull request → vérifier (conflits, secrets, tests) → fusion dans `main` → Render redéploie automatiquement.
- Piège rencontré : une branche partie d'une autre branche non fusionnée embarque **ses commits aussi** (35 au lieu de 7) → fusionner la première d'abord.

---

## Bugs typiques rencontrés (et leur correction)

| Bug | Symptôme | Correction |
|-----|----------|------------|
| Mauvais dossier | `can't open file '/Users/julien/valise.py'` | `cd` dans `voyage/` avant de lancer — Python cherche dans le dossier courant |
| Mauvais Python | `ModuleNotFoundError: requests` | `.venv/bin/python3` : le Python du projet a les bibliothèques |
| Port déjà pris | le téléphone tombe sur AirPlay | macOS occupe le port 5000 → serveur sur 8000 |
| Téléphone hors wifi | « rien ne se passe » | le site du Mac n'existe que sur le wifi de la maison |
| `git add` incomplet | code du cache commité sans ses tests | relire `git status` : `M` à droite = pas encore ajouté |
| Mot de passe dans `serveur.py` | secret dans un fichier suivi par Git | déplacé dans `.env`, fichier remis à l'état du commit — rien n'était parti |
| Aide de test fausse | `t_shirts` devenu « t shirts » → test rouge | le bug était dans le test, pas dans le code : toujours suspecter les deux |
| Test faux positif | `"<details" not in html` échoue | un commentaire CSS contenait le mot : chercher la vraie balise `<details class="rayon"` |
| Course entre requêtes | compteur retombé à 0 alors que la base avait 3 verdicts | une réponse partie **avant** un clic et arrivée **après** l'écrasait → ignorer les réponses plus anciennes que le dernier clic |
| Rotation CSS sans effet | flèche ▸ dans le mauvais sens | `transform` ne s'applique pas à un élément `inline` → afficher directement ▸ / ▾ |
| Indicateur trompeur | imperméable en saison sèche | jours ≥ 1 mm comptent la bruine → jours ≥ 5 mm |
| Règle au mauvais niveau | adaptateur proposé pour l'Italie | dépend du **pays**, pas du climat → règle sur les prises |

---

## À retenir pour la suite

**Ce qui est solide (vu plusieurs fois)** : l'analogie SQL ↔ Python (`WHERE` / `AVG` / `COUNT` / `GROUP BY` / `CASE WHEN`), le cycle Git add → commit → push → PR → fusion, l'upsert `ON CONFLICT`.

**Ce qui est fragile (vu une fois, pas pratiqué)** : `enumerate`, compréhensions de dict `{k: v for ...}`, `unicodedata`, `re.split`, `JSONB`, Flask `Blueprint`, `fetch` + `setInterval` en JavaScript.

**Exercices proposés (15-30 min chacun, zéro concept nouveau)** :
1. Écrire **toi-même** `lire_heure("14h30")` → `(14, 30)` en t'inspirant de `lire_date` (strip, lower, split, isdigit, `None` si invalide) + 3 tests pytest.
2. Écrire en SQL, dans `psql` sur `valise_test`, la requête « pour chaque voyage, nombre de retours par verdict » (`GROUP BY voyage, verdict`).
3. Ajouter un seuil `SEUIL_CANICULE = 35` → étiquette `"canicule"` dans `types_climat`, en TDD (test rouge d'abord).
