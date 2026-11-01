# Casa Binomerie — Repas composés, déjeuner et brunch, accords plat + accompagnement

Décisions du 01/11/2026 (Julien) : déjeuner et brunch à la demande ; accords enregistrés ; approche A
(nouvelle table `repas`). Branche `feat/casa-repas`.

## Le problème

Un soir = un plat (table `soirs`, clé `jour`). Or un dîner a souvent une entrée, un accompagnement ou un
dessert ; un brunch pose cinq plats sur la table ; le déjeuner du week-end n'existe pas. Et un plat
principal « nu » (pièce du boucher, saumon, poulet rôti) ne dit pas avec quoi le servir.

## Ce qui change pour Julien et Laetitia

- **Un repas = plusieurs plats.** Chaque jour a son dîner ; on y ajoute une entrée, un accompagnement,
  un dessert, ou plusieurs plats.
- **Déjeuner et brunch à la demande.** Un lien « + déjeuner ou brunch » ajoute un deuxième repas à un
  jour ; il n'existe que s'il est prévu (pas 14 cases vides).
- **Accords.** Un plat principal porte 2 à 4 accompagnements qui vont avec. Quand on le prévoit, ils
  apparaissent sous lui : un appui les ajoute au repas.
- **Courses, coût, compteur.** Les ingrédients et le coût couvrent tous les plats de tous les repas de la
  semaine. Le compteur Deliveroo ne regarde que le dîner (c'est l'objectif mesuré).
- **Contenu.** ~15 accompagnements (féculents et légumes compatibles avec Laetitia), les accords des plats
  principaux, ~6 recettes de brunch.

## Données

```sql
CREATE TABLE IF NOT EXISTS repas (
    jour    DATE  NOT NULL,
    moment  TEXT  NOT NULL CHECK (moment IN ('diner', 'dejeuner', 'brunch')),
    plats   JSONB NOT NULL DEFAULT '[]',          -- ids de plats, dans l'ordre de la table
    issue   TEXT  CHECK (issue IN ('fait', 'commande', 'dehors', 'autre')),
    maj_le  TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (jour, moment)
);
ALTER TABLE plats ADD COLUMN IF NOT EXISTS accords JSONB NOT NULL DEFAULT '[]';   -- ids d'accompagnements
```

- Un repas sans plat ni issue est supprimé (retirer un déjeuner = le vider).
- Les plats d'un repas s'affichent rangés par genre : entrée, plat, accompagnement, dessert ; au brunch,
  dans l'ordre d'ajout.
- `accords` : ids de plats de genre accompagnement, non archivés ; 6 au plus.
- **Reprise `repas-v1`** (une fois, table `reprises`) : chaque ligne de `soirs` devient un dîner
  (`plats` = `[plat]` ou `[]`, même issue). `soirs` reste en lecture, plus aucune écriture ; suppression
  dans une livraison ultérieure.
- Fenêtre de bascule : entre la migration Neon et le déploiement (quelques minutes), un soir saisi avec
  l'ancienne page irait dans `soirs` et ne serait pas repris. Accepté : migration juste avant le merge,
  personne ne saisit à ce moment-là.

## Règles

- **Fait maison** sur un repas : chacun de ses plats « à tester » passe au carnet (la règle actuelle,
  étendue à tous les plats du repas).
- **Validation** : jour de −60 à +30, moment connu, plats = liste de 0 à 8 ids existants sans doublon,
  issue connue ou nulle.
- **Courses de la semaine** (`a_acheter`, `cout_semaine`) : tous les plats des repas prévus des 7 jours,
  sans doublon d'ingrédient.
- **Coût** : coût d'un repas = somme des `cout_repas` de ses plats ; bilan de la semaine sur les repas.
- **Compteur** : repas `diner` seulement.

## Écrans

- **Semaine** : pour chaque jour, une carte « Dîner » qui liste ses plats (nom, durée, × pour retirer),
  puis des boutons « + plat », « + entrée », « + accompagnement », « + dessert » qui ouvrent la feuille de
  choix (filtres, au hasard) pré-réglée sur ce genre. Sous un plat qui a des accords absents du repas :
  « Avec : purée · haricots verts » (un appui ajoute). « + déjeuner ou brunch » ajoute une carte de plus
  (choix du moment). Le bilan de la semaine et l'envoi aux courses restent en bas.
- **Ce soir** : la carte orange montre le dîner complet (tous ses plats, « Voir la recette » pour chacun),
  le coût du repas entier.
- **Aujourd'hui** (accueil du hub) : « Ce soir » liste les plats du dîner ; « Hier soir ? » écrit l'issue
  du dîner d'hier via la nouvelle route.
- **Fiche recette** : « Va bien avec » (les accords, chacun ouvrable) et « Modifier les accords » (la
  feuille de choix, genre accompagnement, sélection multiple).

## API

- `GET api/diners` : `repas` remplace `soirs` (`[{jour, moment, plats, issue}]`), plats avec `accords`.
- `POST api/repas` : `{jour, moment, plats, issue}` (validé ; repas vide supprimé). Remplace `api/soirs`.
- `POST api/diners/proposer` : inchangé côté appel ; complète les dîners (étape 3 : avec un accord).

## Livraison en 3 étapes (TDD, chacune migrée sur Neon avec accord, puis PR)

1. **Repas** : table `repas` + reprise, `valider_repas`, `db.enregistrer_repas` / `lire_repas`, route,
   compteur / courses / coût / proposer / Aujourd'hui sur `repas`, écran Semaine composé, déjeuner et
   brunch, Ce soir complet. VERSION_PAGE +1.
2. **Accords et contenu** : colonne `accords`, validation, fiche « Va bien avec » + modification, suggestions
   sous un plat prévu ; `recettes_accompagnements.py` (~15), accords des plats principaux du carnet et à
   tester, ~6 brunchs (étiquette « Brunch »), reprise `accords-v1`.
3. **Proposer avec accompagnement** : `proposer` ajoute au dîner un accord du plat tiré (au hasard parmi
   ses accords, pas déjà au menu de la semaine).

## Tests

- `test_repas.py` : validation, enregistrement et suppression d'un repas vide, reprise depuis `soirs`
  (une fois, issues gardées), fait maison qui fait passer au carnet tous les plats à tester du repas.
- `test_diners.py` : compteur sur les dîners seuls, `a_acheter` et `cout_semaine` sur plusieurs plats et
  moments, `proposer` sur `repas` (et avec accord à l'étape 3).
- `test_serveur.py` / `test_diners_db.py` : `POST api/repas`, `GET api/diners` (clé `repas`), Aujourd'hui.
- Contenu (étape 2) : accords valides (accompagnements existants), aucun « jamais » de Laetitia dans les
  accompagnements pour nous deux.
- Vérification dans Chrome sur une copie des données de prod avant chaque PR.

## Hors périmètre

- Quantités et nombre de convives (un repas reste pour deux).
- Apéro, goûter, moments libres.
- Suppression de la table `soirs` (livraison suivante, une fois `repas` éprouvée).
