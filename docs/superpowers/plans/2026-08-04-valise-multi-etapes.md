# Valise multi-étapes — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **Contexte coaching :** ce plan sert de projet d'apprentissage Python pour Julien. En mode coaching, Julien tape le code, guidé par questions socratiques ; le plan fournit la cible et les tests. Chaque task = un checkpoint de validation.

**Goal:** Passer `valise.py` d'une destination unique à un itinéraire multi-étapes produisant une seule checklist, avec des quantités dimensionnées climat par climat.

**Architecture:** On ajoute une couche d'agrégation d'itinéraire (fonctions pures) entre la saisie et `faire_valise`, et on remplace la règle d'accumulation de `faire_valise` (« dernière source gagne ») par « max des sources positives + suppression par 0 ». Données/logique restent séparées ; les tables de données ne bougent pas sauf un réglage `pantalons`.

**Tech Stack:** Python 3 (stdlib uniquement), pytest pour les tests.

## Global Constraints

- Python 3, `python3` uniquement. Aucune dépendance hors stdlib (sauf `pytest` en dev).
- Fichiers concernés : `voyage/valise.py` (modif), `voyage/test_valise.py` (création).
- Un itinéraire est une **liste de dicts** : `{"destination": str, "jours": int, "mois": int}`.
- Tables de données inchangées, sauf §6 : `VETEMENTS_BASE["pantalons"]` passe à `"par_semaine"` et la clé morte `PAR_TYPE_PERSO["chaud"]["pantalons"]` est retirée.
- Règle d'accumulation : base dimensionnée sur `total` ; climat dimensionné sur `jours_par_type[type]` ; collision = **max** ; un `0` climatique retire l'objet **sauf** si une source climatique positive le réclame.
- Lancement des tests : `cd voyage && python3 -m pytest test_valise.py -v`.
- Commits fréquents, un par task minimum.

## File Structure

- `voyage/valise.py` — tout le programme (données + logique + HTML + CLI). On suit le style existant (fichier unique, procédural, tables en tête). On y ajoute 4 fonctions d'agrégation, on remplace `faire_valise`/`ranger`, on adapte `valise_en_html` et `main`.
- `voyage/test_valise.py` — nouveau. Tests des fonctions pures et de la règle d'accumulation. Importe depuis `valise` (même dossier).

---

### Task 1: Fonctions d'agrégation d'itinéraire

**Files:**
- Create: `voyage/test_valise.py`
- Modify: `voyage/valise.py` (ajouter `total_jours` et `jours_par_type` après `types_pour`, ~ligne 498)

**Interfaces:**
- Consumes: `types_pour(destination, mois)` (existant).
- Produces:
  - `total_jours(itineraire: list[dict]) -> int`
  - `jours_par_type(itineraire: list[dict]) -> dict[str, int]`

- [ ] **Step 1: Écrire le fichier de test avec les 3 premiers tests**

Créer `voyage/test_valise.py` :

```python
"""Tests de valise.py — fonctions pures et règle d'accumulation."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))   # importer valise depuis ce dossier

from valise import total_jours, jours_par_type


def test_total_jours():
    itin = [{"destination": "Hanoï", "jours": 7, "mois": 1},
            {"destination": "Siem Reap", "jours": 4, "mois": 1},
            {"destination": "Phu Quoc", "jours": 7, "mois": 1}]
    assert total_jours(itin) == 18


def test_jours_par_type_additionne_les_etapes():
    # janvier, zone asie_sud_est -> ["chaud", "plage"] pour les deux villes
    itin = [{"destination": "Hanoï", "jours": 7, "mois": 1},
            {"destination": "Siem Reap", "jours": 4, "mois": 1}]
    jpt = jours_par_type(itin)
    assert jpt["chaud"] == 11
    assert jpt["plage"] == 11


def test_jours_par_type_type_sur_une_seule_etape():
    # étape d'été asie_sud_est -> ["chaud", "plage", "pluie"] ; pluie sur cette étape seule
    itin = [{"destination": "Hanoï", "jours": 5, "mois": 1},
            {"destination": "Hanoï", "jours": 3, "mois": 7}]
    jpt = jours_par_type(itin)
    assert jpt["chaud"] == 8
    assert jpt["pluie"] == 3
```

- [ ] **Step 2: Lancer les tests, vérifier qu'ils échouent**

Run: `cd voyage && python3 -m pytest test_valise.py -v`
Expected: FAIL — `ImportError: cannot import name 'total_jours'`.

- [ ] **Step 3: Implémenter les deux fonctions**

Dans `voyage/valise.py`, juste après `types_pour` (~ligne 498), ajouter :

```python
def total_jours(itineraire):
    """Somme des jours de toutes les étapes de l'itinéraire."""
    return sum(etape["jours"] for etape in itineraire)


def jours_par_type(itineraire):
    """Cumuler, par type de destination, les jours des étapes qui le réclament.

    Pour chaque étape, types_pour() donne ses types climatiques ; on additionne
    les jours de l'étape à chacun de ces types. Un type présent sur plusieurs
    étapes accumule leurs jours.
    """
    jours = {}
    for etape in itineraire:
        for type_dest in types_pour(etape["destination"], etape["mois"]):
            jours[type_dest] = jours.get(type_dest, 0) + etape["jours"]
    return jours
```

- [ ] **Step 4: Lancer les tests, vérifier qu'ils passent**

Run: `cd voyage && python3 -m pytest test_valise.py -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add voyage/test_valise.py voyage/valise.py
git commit -m "feat(valise): agrégation d'itinéraire (total_jours, jours_par_type)"
```

---

### Task 2: Statut UE et prises multi-étapes

**Files:**
- Modify: `voyage/valise.py` (ajouter après `adaptateur_pour`, ~ligne 485)
- Modify: `voyage/test_valise.py` (ajouter tests + imports)

**Interfaces:**
- Consumes: `statut_ue(destination)` et `adaptateur_pour(destination)` (existants).
- Produces:
  - `statut_ue_itineraire(itineraire) -> tuple[bool, bool]` — `(hors_ue, inconnu_rencontre)`.
  - `prises_itineraire(itineraire) -> set[str]` — adaptateurs distincts, `"aucun"` exclu.

- [ ] **Step 1: Ajouter les tests**

Dans `voyage/test_valise.py`, compléter la ligne d'import :

```python
from valise import (total_jours, jours_par_type,
                    statut_ue_itineraire, prises_itineraire)
```

et ajouter à la fin du fichier :

```python
def test_statut_ue_hors_ue_si_une_etape_hors_ue():
    itin = [{"destination": "France", "jours": 3, "mois": 6},
            {"destination": "Thaïlande", "jours": 5, "mois": 1}]
    hors_ue, inconnu = statut_ue_itineraire(itin)
    assert hors_ue is True
    assert inconnu is False


def test_statut_ue_ue_si_toutes_ue():
    itin = [{"destination": "France", "jours": 3, "mois": 6},
            {"destination": "Italie", "jours": 5, "mois": 6}]
    hors_ue, inconnu = statut_ue_itineraire(itin)
    assert hors_ue is False
    assert inconnu is False


def test_statut_ue_inconnu_declenche_le_flag():
    itin = [{"destination": "Tokyo", "jours": 3, "mois": 6}]   # ville -> statut inconnu
    hors_ue, inconnu = statut_ue_itineraire(itin)
    assert hors_ue is True
    assert inconnu is True


def test_prises_itineraire_dedup_et_sans_aucun():
    itin = [{"destination": "France", "jours": 3, "mois": 6},     # aucun
            {"destination": "Vietnam", "jours": 5, "mois": 1},    # universel
            {"destination": "Cambodge", "jours": 4, "mois": 1}]   # universel
    assert prises_itineraire(itin) == {"universel"}
```

- [ ] **Step 2: Lancer, vérifier l'échec**

Run: `cd voyage && python3 -m pytest test_valise.py -v`
Expected: FAIL — `ImportError: cannot import name 'statut_ue_itineraire'`.

- [ ] **Step 3: Implémenter**

Dans `voyage/valise.py`, après `adaptateur_pour` (~ligne 485) :

```python
def statut_ue_itineraire(itineraire):
    """Statut UE global de l'itinéraire.

    hors_ue = True si AU MOINS une étape est hors UE ou inconnue (choix prudent :
    passeport). inconnu_rencontre = True si une étape a un statut inconnu (déclenche
    un warning). Renvoie (hors_ue, inconnu_rencontre).
    """
    hors_ue = False
    inconnu = False
    for etape in itineraire:
        statut = statut_ue(etape["destination"])
        if statut == "hors_ue":
            hors_ue = True
        elif statut == "inconnu":
            hors_ue = True
            inconnu = True
    return hors_ue, inconnu


def prises_itineraire(itineraire):
    """Set des adaptateurs distincts à emporter sur tout l'itinéraire ('aucun' exclu)."""
    prises = set()
    for etape in itineraire:
        prise = adaptateur_pour(etape["destination"])
        if prise != "aucun":
            prises.add(prise)
    return prises
```

- [ ] **Step 4: Lancer, vérifier le succès**

Run: `cd voyage && python3 -m pytest test_valise.py -v`
Expected: PASS (7 tests).

- [ ] **Step 5: Commit**

```bash
git add voyage/valise.py voyage/test_valise.py
git commit -m "feat(valise): statut UE et prises agrégés sur l'itinéraire"
```

---

### Task 3: Cœur — `faire_valise` en max + suppression

C'est la task centrale. On règle d'abord la donnée `pantalons` (§6 de la spec), puis on remplace `ranger` par un remplissage en deux temps (accumulation base + climat, puis finalisation max/suppression).

**Files:**
- Modify: `voyage/valise.py` :
  - `VETEMENTS_BASE["pantalons"]` (~ligne 191) → `"par_semaine"`.
  - `PAR_TYPE_PERSO["chaud"]` (~ligne 207-212) : retirer la clé `"pantalons": "par_semaine"`.
  - Remplacer `ranger` (~ligne 550) par `_remplir`.
  - Remplacer `faire_valise` (~ligne 564).
- Modify: `voyage/test_valise.py` (ajouter tests + imports).

**Interfaces:**
- Consumes: `quantite_reelle`, `theme_de`, `paquet_vide`, tables de données, `JAMAIS`, `CONDUCTEURS` (existants) ; `jours_par_type`/`total_jours` (Task 1).
- Produces:
  - `faire_valise(jours_par_type, total, personnes, hors_ue, conduit) -> dict` — même structure de sortie qu'avant : `{proprietaire: {theme: {objet: quantité}}}`.
  - `_remplir(paquet, base_tables, type_tables, jours_types, total) -> None` — remplit un paquet en place.

- [ ] **Step 1: Ajouter les tests de la règle d'accumulation**

Dans `voyage/test_valise.py`, compléter l'import :

```python
from valise import (total_jours, jours_par_type,
                    statut_ue_itineraire, prises_itineraire,
                    quantite_reelle, faire_valise)
```

et ajouter :

```python
def test_quantite_reelle_marqueurs():
    assert quantite_reelle("par_jour", 5) == 5
    assert quantite_reelle("par_semaine", 3) == 1        # plancher à 1
    assert quantite_reelle("par_3_jours", 10) == 3
    assert quantite_reelle((3, "par_semaine"), 14) == 6  # 3 x (14//7)
    assert quantite_reelle(2, 10) == 2


def test_faire_valise_max_entre_deux_climats():
    # shorts réclamés par chaud (18j -> 6) et plage (7j -> 2) : on garde le max
    jpt = {"chaud": 18, "plage": 7}
    valise = faire_valise(jpt, 18, ["Julien"], hors_ue=True, conduit=False)
    assert valise["Julien"]["Vêtements"]["shorts"] == 6


def test_faire_valise_suppression_chemises_si_chaud():
    # chaud met "chemises": 0 -> retire la base ; "chemises légères" les remplace
    jpt = {"chaud": 10, "ville": 10}
    valise = faire_valise(jpt, 10, ["Julien"], hors_ue=False, conduit=False)
    vetements = valise["Julien"]["Vêtements"]
    assert "chemises" not in vetements
    assert "chemises légères" in vetements


def test_faire_valise_chemises_conservees_sans_chaud():
    jpt = {"ville": 10}
    valise = faire_valise(jpt, 10, ["Julien"], hors_ue=False, conduit=False)
    assert "chemises" in valise["Julien"]["Vêtements"]


def test_faire_valise_pantalons_par_semaine():
    # après le réglage §6 : base par_semaine -> 18//7 = 2
    jpt = {"chaud": 18, "plage": 18}
    valise = faire_valise(jpt, 18, ["Julien"], hors_ue=True, conduit=False)
    assert valise["Julien"]["Vêtements"]["pantalons"] == 2


def test_faire_valise_documents_selon_ue():
    jpt = {"ville": 5}
    hors = faire_valise(jpt, 5, ["Julien"], hors_ue=True, conduit=False)
    dans = faire_valise(jpt, 5, ["Julien"], hors_ue=False, conduit=False)
    assert "passeport" in hors["Julien"]["Documents"]
    assert "carte d'identité" in dans["Julien"]["Documents"]
```

- [ ] **Step 2: Lancer, vérifier l'échec**

Run: `cd voyage && python3 -m pytest test_valise.py -v`
Expected: FAIL — les tests `faire_valise` échouent (ancienne signature `(types, jours, ...)`), `test_faire_valise_max_entre_deux_climats` lève `TypeError` ou renvoie un mauvais résultat.

- [ ] **Step 3: Régler la donnée pantalons (§6)**

Dans `VETEMENTS_BASE` (~ligne 191), changer :

```python
    "pantalons": "par_semaine",
```

Dans `PAR_TYPE_PERSO["chaud"]` (~ligne 207-212), **retirer** la ligne `"pantalons": "par_semaine",` (elle devient sans effet avec la règle max). Le bloc devient :

```python
    "chaud":    {"chapeau": 1, "lunettes de soleil": "par_semaine",
                 "shorts": "par_3_jours", "débardeurs": "par_jour",
                 "robe légère": "par_3_jours", "sandales": 1,
                 "chemises légères": "par_3_jours",
                 "chemises": 0},                 # 0 = retire les chemises normales quand il fait chaud
```

- [ ] **Step 4: Remplacer `ranger` par `_remplir`**

Supprimer la fonction `ranger` (~ligne 550-561) et la remplacer par :

```python
def _remplir(paquet, base_tables, type_tables, jours_types, total):
    """Remplir un paquet selon la règle max + suppression.

    - base_tables : liste de tables {objet: marqueur} dimensionnées sur `total`.
    - type_tables : {type: {objet: marqueur}} dimensionnées sur jours_types[type],
      pour les seuls types présents (clés de jours_types). Un marqueur 0 = suppression.

    Règle : pour chaque objet, quantité = max des contributions positives (base sur
    total, climat sur ses jours). Un 0 climatique retire l'objet SAUF si une source
    climatique positive le réclame (le 0 supprime la base, pas un autre climat).
    """
    base_q = {}          # objet -> quantité issue des tables de base (sur total)
    climat_q = {}        # objet -> max des quantités climatiques positives
    climat_zero = set()  # objets qu'un climat veut retirer (marqueur 0)

    for table in base_tables:
        for objet, marqueur in table.items():
            q = quantite_reelle(marqueur, total)
            if q > 0:
                base_q[objet] = max(base_q.get(objet, 0), q)

    for type_dest, jours in jours_types.items():
        for objet, marqueur in type_tables.get(type_dest, {}).items():
            if marqueur == 0:
                climat_zero.add(objet)
                continue
            q = quantite_reelle(marqueur, jours)
            if q > 0:
                climat_q[objet] = max(climat_q.get(objet, 0), q)

    for objet in set(base_q) | set(climat_q) | climat_zero:
        cq = climat_q.get(objet, 0)
        if objet in climat_zero and cq == 0:
            continue                       # supprimé : un climat retire, aucun positif climatique
        quantite = max(base_q.get(objet, 0), cq)
        if quantite > 0:
            paquet[theme_de(objet)][objet] = quantite
```

- [ ] **Step 5: Remplacer `faire_valise`**

Remplacer la fonction `faire_valise` (~ligne 564-612) par :

```python
def faire_valise(jours_types, total, personnes, hors_ue, conduit):
    """Construire la checklist {proprietaire: {theme: {objet: quantité}}}.

    - jours_types : {type de destination: jours cumulés} (couche d'agrégation).
    - total       : durée totale du voyage (dimensionne les objets de base).
    - personnes   : liste de personnes qui font leur valise.
    - hors_ue     : True -> passeport, False -> carte d'identité.
    - conduit     : True -> permis (+ permis international si hors_ue).
    """
    valise = {"Partagé": paquet_vide()}
    for personne in personnes:
        valise[personne] = paquet_vide()

    # Partagé : 1 pour le groupe (base commune + types communs présents)
    _remplir(valise["Partagé"],
             base_tables=[BASE_COMMUN],
             type_tables=PAR_TYPE_COMMUN,
             jours_types=jours_types, total=total)

    # Perso : le paquet de chaque personne
    for personne in personnes:
        paquet = valise[personne]
        _remplir(paquet,
                 base_tables=[BASE_PERSO, VETEMENTS_BASE, PAR_PERSONNE[personne]],
                 type_tables=PAR_TYPE_PERSO,
                 jours_types=jours_types, total=total)
        # filtre final : ce que cette personne ne prend jamais (items genrés, etc.)
        for objet in JAMAIS.get(personne, set()):
            paquet[theme_de(objet)].pop(objet, None)
        # documents personnels (chacun les siens)
        if hors_ue:
            paquet[theme_de("passeport")]["passeport"] = 1
        else:
            paquet[theme_de("carte d'identité")]["carte d'identité"] = 1
        if conduit and personne in CONDUCTEURS:
            paquet[theme_de("permis")]["permis"] = 1
            if hors_ue:
                paquet[theme_de("permis international")]["permis international"] = 1

    return valise
```

- [ ] **Step 6: Lancer, vérifier le succès**

Run: `cd voyage && python3 -m pytest test_valise.py -v`
Expected: PASS (13 tests).

- [ ] **Step 7: Commit**

```bash
git add voyage/valise.py voyage/test_valise.py
git commit -m "feat(valise): dimensionnement par climat (max + suppression), réglage pantalons"
```

---

### Task 4: HTML multi-étapes

**Files:**
- Modify: `voyage/valise.py` — `valise_en_html` (~ligne 614).

**Interfaces:**
- Consumes: `valise` (Task 3), `libelle_voyage: str`, `total: int`, `prises: set[str]`.
- Produces: `valise_en_html(valise, libelle_voyage, total, prises) -> str`.

- [ ] **Step 1: Réécrire `valise_en_html`**

Remplacer la signature et le corps de `valise_en_html` (~ligne 614-650). Changements : signature, `data-key` préfixé par `libelle_voyage`, titre/en-tête, ligne prises jointe.

```python
def valise_en_html(valise, libelle_voyage, total, prises):
    """Construire la page HTML de la checklist pour l'itinéraire complet."""
    adaptateurs = ", ".join(sorted(prises)) if prises else "aucun"
    onglets = '<nav class="tabs">'          # un bouton par propriétaire (Partagé/Julien/...)
    for proprietaire in valise:
        onglets += f'<button data-owner="{proprietaire}">{proprietaire} <span class="tab-count"></span></button>'
    onglets += '</nav>'
    corps = ""
    for proprietaire, themes in valise.items():
        corps = corps + f'<section data-owner="{proprietaire}"><h2>{proprietaire}</h2>'
        for theme, objets in themes.items():
            if not objets:
                continue
            corps = corps + f"<h3>{theme}</h3><ul>"
            for objet, quantite in sorted(objets.items()):
                corps = corps + f'<li><label><input type="checkbox" data-key="{libelle_voyage}/{proprietaire}/{theme}/{objet}"> {objet} ×{quantite}</label></li>'
            corps = corps + "</ul>"
        corps = corps + "</section>"
    page = f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Valise — {libelle_voyage}</title>
<style>{HTML_STYLE}</style>
</head>
<body>
<h1>Valise — {libelle_voyage} · {total} jours</h1>
<p class="prise">🔌 Adaptateur(s) à emporter : <strong>{adaptateurs}</strong></p>
<div class="progress"><div class="progress-head"><span>Rangé</span><span id="compte">0 / 0</span></div><div class="progress-track"><div id="progress-fill"></div></div></div>
<div class="controls"><button id="toggle-masque" class="ctrl-btn">Masquer les rangés</button><button id="reset" class="ctrl-btn">Réinitialiser</button></div>
{onglets}
{corps}
<script>{HTML_SCRIPT}</script>
</body>
</html>"""
    return page
```

- [ ] **Step 2: Vérifier la génération isolément**

Run (depuis `voyage/`) :

```bash
python3 -c "import valise; jpt={'chaud':18,'plage':7}; v=valise.faire_valise(jpt,18,['Julien','Laetitia'],True,False); html=valise.valise_en_html(v,'Hanoï › Phu Quoc',18,{'universel'}); open('valise.html','w',encoding='utf-8').write(html); print('OK', len(html), 'octets')"
```

Expected: `OK <n> octets`, sans exception. Ouvrir `voyage/valise.html` : titre « Valise — Hanoï › Phu Quoc · 18 jours », ligne prise « universel », onglets Partagé/Julien/Laetitia, cases cochables.

- [ ] **Step 3: Commit**

```bash
git add voyage/valise.py
git commit -m "feat(valise): page HTML pour itinéraire (libellé voyage, prises multiples)"
```

---

### Task 5: Saisie de l'itinéraire dans `main`

**Files:**
- Modify: `voyage/valise.py` — `main` (~ligne 652).

**Interfaces:**
- Consumes: toutes les fonctions ci-dessus + `objets_sans_rayon`, `pays_sans_prise`, `CHOIX_PERSONNE`, `VILLE_VERS_ZONE`, `PAYS_VERS_ZONE`.
- Produces: expérience CLI multi-étapes ; écrit `valise.html`.

- [ ] **Step 1: Réécrire `main`**

Remplacer la fonction `main` (~ligne 652-695) par :

```python
def main():
    """Assistant interactif : saisit un itinéraire, puis construit la valise."""
    manquants = objets_sans_rayon()
    if manquants:
        print(f"⚠️  Objets sans rayon (à classer dans THEMES) : {manquants}")
    sans_prise = pays_sans_prise()
    if sans_prise:
        print(f"⚠️  Pays sans prise renseignée (à compléter dans PAYS_VERS_PRISE) : {sans_prise}")

    # --- Saisie de l'itinéraire, étape par étape ---
    itineraire = []
    numero = 1
    while True:
        destination = input(f"Étape {numero} — destination (ou 'fin' pour terminer) : ")
        if destination == "fin":
            if itineraire:
                break
            print("Ajoute au moins une étape avant de terminer.")
            continue
        if destination not in VILLE_VERS_ZONE and destination not in PAYS_VERS_ZONE:
            print(f"Destination '{destination}' inconnue, vérifie l'orthographe.")
            continue
        while True:
            reponse = input("        — jours : ")
            if reponse.isdigit() and int(reponse) >= 1:
                jours = int(reponse)
                break
            print("        Nombre de jours invalide : entre un nombre positif.")
        while True:
            reponse = input("        — mois (1-12) : ")
            if reponse.isdigit() and 1 <= int(reponse) <= 12:
                mois = int(reponse)
                break
            print("        Mois invalide : entre un nombre entre 1 et 12.")
        itineraire.append({"destination": destination, "jours": jours, "mois": mois})
        numero += 1

    # --- Questions posées une seule fois ---
    while True:
        choix = input("Qui fait sa valise ? (j = Julien / l = Laetitia / 2 = les deux) : ")
        if choix in CHOIX_PERSONNE:
            break
        print("Choix invalide : tape j, l ou 2.")
    personnes = CHOIX_PERSONNE[choix]

    hors_ue, inconnu = statut_ue_itineraire(itineraire)
    if inconnu:
        print("⚠️  Statut UE inconnu pour une étape : passeport par défaut, à vérifier.")
    conduit = input("Tu vas conduire ? (o/n) : ") == "o"

    # --- Construction ---
    jours_types = jours_par_type(itineraire)
    total = total_jours(itineraire)
    prises = prises_itineraire(itineraire)
    valise = faire_valise(jours_types, total, personnes, hors_ue, conduit)

    libelle_voyage = " › ".join(etape["destination"] for etape in itineraire)
    html = valise_en_html(valise, libelle_voyage, total, prises)
    with open("valise.html", "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Checklist écrite dans valise.html ({total} jours, {len(itineraire)} étape(s))")
```

- [ ] **Step 2: Test manuel de bout en bout**

Run (depuis `voyage/`) :

```bash
printf "Hanoï\n7\n1\nSiem Reap\n4\n1\nPhu Quoc\n7\n1\nfin\n2\nn\n" | python3 valise.py
```

Expected : affiche `Checklist écrite dans valise.html (18 jours, 3 étape(s))`, sans warning UE (pays connus hors UE), sans exception. Ouvrir `voyage/valise.html` : titre « Hanoï › Siem Reap › Phu Quoc · 18 jours », onglets Julien/Laetitia, quantités cohérentes (t-shirts ×18, pantalons ×2, maillot présent).

- [ ] **Step 3: Test manuel du garde-fou (au moins une étape)**

Run :

```bash
printf "fin\nParis\n3\n6\nfin\nj\nn\n" | python3 valise.py
```

Expected : « Ajoute au moins une étape avant de terminer. » puis accepte Paris et écrit la checklist (Paris = UE, pas de warning passeport).

- [ ] **Step 4: Lancer toute la suite de tests (non-régression)**

Run: `cd voyage && python3 -m pytest test_valise.py -v`
Expected: PASS (13 tests).

- [ ] **Step 5: Commit**

```bash
git add voyage/valise.py
git commit -m "feat(valise): saisie d'itinéraire multi-étapes dans la CLI"
```

---

## Self-Review

**Spec coverage :**
- §1 saisie itinéraire → Task 5. ✓
- §2 agrégation (`total_jours`, `jours_par_type`, `statut_ue_itineraire`, `prises_itineraire`) → Tasks 1 & 2. ✓
- §3 `faire_valise` max + suppression → Task 3. ✓ (sémantique de suppression précisée : le 0 supprime la base, un positif climatique l'emporte — corrige l'ambiguïté de la spec §3.)
- §4 géo multi-pays (UE, prises) → Task 2 (logique) + Tasks 4/5 (affichage). ✓
- §5 HTML (libellé voyage, préfixe data-key, prises) → Task 4. ✓
- §6 réglage pantalons → Task 3, steps 3. ✓
- Tests pytest → présents dans chaque task. ✓

**Placeholder scan :** aucun TBD/TODO ; tout le code est fourni en entier. ✓

**Type consistency :** `jours_par_type` (fonction, Task 1) vs paramètre `jours_types` (dans `faire_valise`/`_remplir`, Task 3) — noms distincts volontairement pour éviter que le paramètre masque la fonction. `faire_valise(jours_types, total, personnes, hors_ue, conduit)` appelé de façon cohérente en Tasks 3/4/5. `valise_en_html(valise, libelle_voyage, total, prises)` cohérent Tasks 4/5. ✓

## Notes d'exécution

- Entre la Task 3 et la Task 5, `python3 valise.py` (mode interactif) est temporairement cassé (nouvelle signature de `faire_valise` avant réécriture de `main`) — c'est attendu, les tests unitaires restent verts. La CLI redevient fonctionnelle en fin de Task 5.
- Hors périmètre (rappel spec) : sur-attribution « plage » de la zone `asie_sud_est` (Hanoï classée plage en janvier), plafond lessive, activités, météo API. À traiter dans un axe séparé.
