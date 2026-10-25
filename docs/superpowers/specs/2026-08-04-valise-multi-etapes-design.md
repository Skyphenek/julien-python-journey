# Valise multi-étapes — design

Date : 2026-08-04
Fichier concerné : `voyage/valise.py` (+ nouveau `voyage/test_valise.py`)

## Problème

Aujourd'hui `valise.py` prend **une** destination + **un** nombre de jours + **un**
mois. Un vrai voyage (Vietnam + Cambodge, 18 jours, plusieurs villes et climats)
ne rentre pas dans ce modèle : on veut saisir un **itinéraire** de plusieurs
étapes et produire **une seule** checklist qui couvre l'ensemble, avec des
quantités réalistes climat par climat.

## Décisions cadrées (brainstorming)

1. **Durée** : jours saisis **par étape**, la somme pilote les objets de base.
2. **Quantités par climat** : chaque objet est dimensionné sur les jours **du
   climat qui le réclame** (pas sur le total).
3. **Collision** (un objet réclamé par plusieurs sources) : **max des sources
   positives** ; un **0 explicite retire** l'objet, sauf si un autre climat le
   réclame positivement.
4. **Tests** : vrai fichier `pytest` sur les fonctions pures.

## Architecture

Le découpage DONNÉES / LOGIQUE existant ne bouge pas. Les tables de données
(BASE_*, PAR_TYPE_*, ZONES, PAYS_*, THEMES…) restent inchangées, sauf un
ajustement de donnée (§6). On ajoute une **couche d'agrégation d'itinéraire**
entre la saisie et `faire_valise`, et on modifie la règle d'accumulation de
`faire_valise`.

Flux :

```
main() saisit un itinéraire : [ {destination, jours, mois}, ... ]
   │
   ├── jours_par_type(itineraire)  -> {type: jours cumulés}
   ├── total_jours(itineraire)     -> int
   ├── statut_ue_itineraire(...)   -> hors_ue global
   └── prises_itineraire(...)      -> set d'adaptateurs distincts
   │
faire_valise(jours_par_type, total, personnes, hors_ue, conduit)
   │
valise_en_html(valise, libelle_voyage, total, prises)
```

## Composants

### 1. Saisie de l'itinéraire — `main`

Boucle de saisie remplaçant les 3 questions ville/jours/mois :

```
Étape 1 — destination (ou "fin" pour terminer) : Hanoï
        — jours : 7
        — mois (1-12) : 1
Étape 2 — destination : Siem Reap  / jours : 4 / mois : 1
Étape 3 — destination : Phu Quoc   / jours : 7 / mois : 1
Étape 4 — destination : fin
```

- Chaque champ validé comme aujourd'hui : destination ∈ `VILLE_VERS_ZONE ∪
  PAYS_VERS_ZONE`, jours entier ≥ 1, mois entier 1-12.
- `"fin"` termine la saisie. **Au moins une étape** obligatoire (si l'utilisateur
  tape "fin" à l'étape 1, on redemande).
- Les questions "qui fait sa valise ?" et "tu vas conduire ?" restent posées
  **une seule fois**, après l'itinéraire.
- Un itinéraire est une **liste de dicts** : `{"destination", "jours", "mois"}`.

### 2. Couche d'agrégation (fonctions pures, testables)

- `total_jours(itineraire)` → somme des `jours` de toutes les étapes.
- `jours_par_type(itineraire)` → `{type: jours cumulés}`. Pour chaque étape,
  `types_pour(destination, mois)` donne ses types ; on **additionne** les jours de
  l'étape à chacun de ces types.
  - Ex. en janvier, les 3 villes sont en zone `asie_sud_est` → toutes `chaud` +
    `plage` : Hanoï 7j, Siem Reap 4j, Phu Quoc 7j → `{"chaud": 18, "plage": 18}`.
  - Un type présent sur une seule étape n'agrège que les jours de cette étape
    (ex. `pluie` limité à une étape d'été → seulement ses jours).
  - *(Les types réels dépendent des tables ZONES ; l'exemple illustre le
    mécanisme d'addition.)*
- `statut_ue_itineraire(itineraire)` → `hors_ue` (bool). Si **au moins une** étape
  est hors UE OU inconnue → `True` (passeport, choix prudent). Sinon `False`
  (CNI). Renvoie aussi un indicateur "inconnu rencontré" pour le warning.
- `prises_itineraire(itineraire)` → **set** des adaptateurs distincts via
  `adaptateur_pour`, en retirant `"aucun"`. Vietnam+Cambodge → `{"universel"}`.
  UK+Japon → `{"UK", "US (110V)"}`.

### 3. `faire_valise` — nouvelle règle d'accumulation

Signature : `faire_valise(jours_par_type, total, personnes, hors_ue, conduit)`
(remplace `(types, jours, ...)`).

La logique thème/rayon (`theme_de`, `paquet_vide`, structure par propriétaire)
**ne change pas**. Ce qui change : `ranger` (assignation "dernière source
gagne") est remplacé par `poser`, qui applique **max + suppression** :

```
poser(rayon, objet, marqueur, jours) :
    q = quantite_reelle(marqueur, jours)
    si marqueur est le 0 explicite (suppression) :
        marquer l'objet comme "supprimé par un climat"
    sinon :
        rayon[objet] = max(rayon.get(objet, 0), q)   # accumulation par max
```

Dimensionnement des sources :
- **base** (`BASE_COMMUN`, `BASE_PERSO`, `VETEMENTS_BASE`) → `jours = total`.
- **par climat** (`PAR_TYPE_COMMUN[t]`, `PAR_TYPE_PERSO[t]`) → `jours =
  jours_par_type[t]`, uniquement pour les types présents (clés de
  `jours_par_type`).
- **documents** (passeport/CNI/permis) → `jours = total`, quantité fixe 1.

Règle de **suppression finale** (le 0) : un objet marqué "supprimé par un climat"
est retiré du rayon **sauf** si une source positive (base ou autre climat) lui a
donné une quantité > 0. Implémentation : après avoir posé toutes les sources, on
retire les objets dont **toute** contribution valait 0. En pratique le seul cas
data est `chemises` (base `par_3_jours`, `chaud` = 0) : présence de chaud →
chemises retirées ; remplacées par `chemises légères` (que chaud pose
positivement).

L'ordre de traitement conserve : base → climats → filtre `JAMAIS` → documents,
identique à aujourd'hui.

### 4. Géo multi-pays

- **UE** : `statut_ue_itineraire` (cf. §2). Le warning "statut UE inconnu" est levé
  si une étape est inconnue.
- **Prises** : `prises_itineraire` renvoie un set. `main` l'affiche joint (ex.
  "universel" ou "UK, US (110V)"), transmis à `valise_en_html`.

### 5. HTML — `valise_en_html`

Signature : `valise_en_html(valise, libelle_voyage, total, prises)`.

- `libelle_voyage` = destinations jointes par " › " (ex. "Hanoï › Siem Reap ›
  Phu Quoc"), construit dans `main`.
- `<h1>Valise — {libelle_voyage} · {total} jours</h1>`.
- Ligne prise : liste des adaptateurs (join sur ", ") ; si set vide → "aucun".
- **Persistance** : le préfixe des `data-key` (aujourd'hui la ville) devient le
  `libelle_voyage`. Les coches survivent au regen tant que l'itinéraire ne change
  pas. La logique de rendu (sections, thèmes, checkboxes) est inchangée.

### 6. Ajustement de donnée

La règle "max" rend l'ancienne réduction `PAR_TYPE_PERSO["chaud"]["pantalons"] =
"par_semaine"` sans effet (max avec la base l'emporte). Deux conséquences à
acter :
- Retirer la clé `"pantalons": "par_semaine"` de `PAR_TYPE_PERSO["chaud"]` (morte).
- Passer `VETEMENTS_BASE["pantalons"]` de `"par_3_jours"` à `"par_semaine"` pour
  garder un nombre de pantalons raisonnable sur un long voyage (18j → ~2 au lieu
  de 6). **À confirmer / ajuster par Julien** — pur réglage de donnée.

## Tests — `voyage/test_valise.py` (pytest)

Cibler les fonctions pures et la nouvelle règle :

- `total_jours` : somme correcte sur itinéraire multi-étapes.
- `jours_par_type` : addition des jours par type sur plusieurs étapes ; un type
  présent sur une seule étape n'agrège que ses jours.
- `quantite_reelle` : cas déjà existants (par_jour, par_semaine plancher, tuple).
- Règle **max** dans `faire_valise` : un objet réclamé par deux climats prend le
  max ; un objet base + climat prend le max.
- **Suppression 0** : `chemises` absent quand `chaud` présent ; présent si `chaud`
  absent.
- `statut_ue_itineraire` : hors_ue si une étape hors UE ; hors_ue si une étape
  inconnue ; UE si toutes UE.
- `prises_itineraire` : dédup + retrait de "aucun".

Lancement : `python3 -m pytest voyage/test_valise.py`.

## Hors périmètre (YAGNI)

- Activités spécifiques (snorkeling, temples) — axe séparé, plus tard.
- Plafond "lessive tous les N jours" — axe séparé.
- Météo temps réel via API — dépend de la S4 du programme (APIs).
- Refactor en classes — le style procédural/données actuel reste adapté.
