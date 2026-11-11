# Casa Dîners — un seul onglet Recettes (fusion Carnet / À tester)

Date : 11/11/2026 — validé par Julien en session.

## Problème

La page Dîners a 4 onglets : Ce soir, Semaine, Carnet (40 recettes), À tester (116). La distinction n'est pas utile
à Julien : 3/4 des recettes sont « à tester », il faut deux onglets pour chercher, et le statut ne bouge que si on y
pense (repas marqué « fait maison » ou bouton « On l'a fait »).

## Décision

Option A : un seul onglet **Recettes**, un repère calculé au lieu de deux listes.

- L'historique des repas seul ne suffit pas (10 repas « fait » depuis le 27/10/2026) : le statut `carnet` /
  `a-tester` reste en base comme repère **connue / nouvelle**, plus affiché comme une section.
- Le compte « fait maison » vient de `repas` (`issue = 'fait'` et `plats ? id`), comme dans `chef.file_de_passage`.

## Écran

Onglets : Ce soir · Semaine · Recettes.

Onglet Recettes, de haut en bas :
1. Recherche (inchangée).
2. Filtres de genre (inchangés).
3. Barre d'étiquettes existante + étiquette **Nouvelles** (statut `a-tester`), avec compteur, combinable avec le genre.
4. Bouton « + Nouvelle recette ».
5. Liste unique (non archivées).

Ordre de la liste (aussi pendant une recherche) :
1. faites le plus souvent (compte décroissant) ;
2. connues sans repas enregistré, A → Z ;
3. nouvelles : avec recette écrite d'abord, puis A → Z ; mention grise « recette à écrire » si pas de texte.

Badges de ligne : existants (secours, à finir, Julien, Laetitia) + **Nouvelle** (statut `a-tester`) + **N×** (compte
≥ 1). Une connue sans repas enregistré n'a pas de badge de fréquence.

Fiche :
- « On l'a fait : au carnet » → « On l'a déjà faite » (même effet : statut `carnet`).
- « Retirer du carnet » / « Remettre au carnet » → « Archiver » / « Désarchiver ».

Choix d'un plat pour un repas (Semaine) : les groupes Carnet / À tester deviennent une seule liste, même ordre.

Vue demandée `carnet` ou `a-tester` (lien, état mémorisé) → ouvre `recettes`.

## Inchangé

Ce soir, Semaine, secours (connues seulement), « Proposer ma semaine » (alternance connue / nouvelle), schéma de base,
passage automatique à `carnet` quand un repas est marqué « fait maison ».

## Données

- L'API `api/diners` fournit pour chaque plat son compte de repas faits (`faits`), calculé en une requête.
- Aucune migration, aucune colonne nouvelle.

## Tests et livraison

- `test_diners.py` / `test_diners_db.py` : onglets (3), vue `recettes`, redirection des anciennes vues, ordre de la
  liste, badges, compte `faits` dans l'API.
- Démo locale sur copie de prod (`valise_copie`, port 8001), testée par Julien sur Mac + iPhone avant tout push/PR.

## Hors périmètre

Renommer le champ `statut` en base, supprimer les étiquettes existantes, toucher au Match des Recettes.

## Ajout du 11/11/2026 — badges en icônes et thème Auto / Clair / Sombre

Validé par Julien après la première démo.

### Badges en icônes (lignes de plat : onglet Recettes et feuille de choix)

| Avant | Après | Règle | Mot pour lecteur d'écran |
|---|---|---|---|
| « Nouvelle » | ✦ (doré) | statut `a-tester` | « nouvelle » |
| « N× » | ●○○○ … ●●●● | faits 1 → 1 point, 2 → 2, 3-4 → 3, ≥ 5 → 4 ; rien si 0 | « faite N fois » |
| « secours » | ⚡ | faisable ce soir | « faisable ce soir » |
| « à finir » | ⏳ | finit un produit | « finit un produit » |
| « Julien » / « Laetitia » | Ⓙ / Ⓛ | `pour` | « pour Julien » / « pour Laetitia » |

- Légende d'une ligne en bas de la liste Recettes : « ✦ nouvelle · ●●● faite souvent · ⚡ faisable ce soir · ⏳ finit un produit · Ⓙ Ⓛ pour Julien / Laetitia ».
- Restent en texte : « au menu » (feuille de choix), « recette à écrire ».

### Thème Auto / Clair / Sombre

- Un bouton rond ◐ / ☀ / ☾ sur chaque page qui a la navigation Casa : en haut à droite sur téléphone (la barre du bas a déjà 6 entrées), en bas de la colonne de navigation sur ordinateur. Un appui : Auto → Clair → Sombre → Auto.
- Choix gardé par appareil dans `localStorage` (`casa-theme` : `clair` / `sombre` ; absent = auto) ; la page l'applique dans le `<head>` (attribut `data-theme="light"|"dark"` sur `<html>`) avant l'affichage. `localStorage` inaccessible : auto, sans erreur.
- Toutes les règles « mode sombre » (7 blocs, `design.py` et `valise.py`) passent par une fonction `sombre(css)` qui écrit chaque règle deux fois : sous `@media (prefers-color-scheme: dark)` gardée par `:root:not([data-theme="light"])`, et sous `:root[data-theme="dark"]`. `color-scheme` suit le choix.
- Limite : écran de lancement et barre d'état de l'app installée restent pilotés par iOS.
