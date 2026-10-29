# Plan — Casa Binomerie, Placard v2 (zones, frais en habituels)

Décision du 29/10 (Julien) : options A + C, zones par défaut. Branche `feat/casa-placard-v2`.
Point de départ : la checklist « La cuisine de Ste Isaure » (artifact 3qrB11grRnJnbFN4pSK4t2),
remplie le 29/10 : 21 ingrédients « on a », 117 « à acheter » (vague 1 samedi : 40, vague 2
épiceries : 15, à la demande : 62), 1 « pas besoin ».

## Le problème

Le placard est une liste plate de 45 basiques, en stock ou épuisés. Avec 130+ ingrédients, il
devient illisible, et il mélange deux rythmes : le frais (œufs, crème, lait) se rachète chaque
semaine, le durable (épices, huiles, conserves) quelques fois par an.

## Ce qui change pour Julien et Laetitia

- **Le placard ne garde que ce qui dure**, rangé par zone de la cuisine : Frigo (fromages durs,
  guanciale), Placard sec, Épices et condiments, Congélateur, Cave. Une zone se parcourt comme on
  ouvre un placard.
- **Trois états** au lieu de deux : En stock → Bientôt fini → Épuisé. « Bientôt fini » et « Épuisé »
  ajoutent l'article aux courses ; « Bientôt fini » compte encore comme disponible pour le mode
  secours (on peut cuisiner ce soir, mais il faut racheter).
- **Le frais devient des habituels des courses** (fonction existante : un article récurrent revient
  dans « Habituels » après le vidage). Rangé, il compte comme disponible ; sur la liste à prendre,
  non.
- **À la demande** : un ingrédient durable acheté pour une recette (source `plat:`) entre au placard
  quand on le coche « pris ». Le placard se construit au fil des recettes.
- **Nouveau rayon** « Épiceries spécialisées » (asiatique, italienne) : la vague 2 y apparaît, à part
  des courses du supermarché.

## Données

- `placard` : + `zone TEXT NOT NULL DEFAULT 'placard-sec'`, + `bientot BOOLEAN NOT NULL DEFAULT false`
  (`ALTER TABLE … ADD COLUMN IF NOT EXISTS` : additif, l'app actuelle continue de marcher pendant
  la migration). États : `en_stock and not bientot` = en stock ; `en_stock and bientot` = bientôt
  fini ; `not en_stock` = épuisé.
- Import (`placard_v2.py`) : pour chaque ingrédient retenu, un **nom court aligné sur les recettes**
  (« tomates pelées », pas « Tomates pelées (San Marzano si possible) »), une zone, et un rythme
  (`placard` ou `habituel`). « On a » → en stock ; vague 1 → épuisé (donc dans les courses de
  samedi) ; vague 2 → épuisé, rayon Épiceries spécialisées. « À la demande » : pas importé.
- Reprise des 45 basiques existants : zone attribuée ; les frais à rotation hebdomadaire (œufs,
  beurre, crème fraîche, lait, yaourt grec, mozzarella, jambon, citrons, demi-baguettes) passent en
  habituels et quittent le placard. Rien n'est supprimé sans être recréé ailleurs ; ce qu'ils ont
  modifié dans l'app (état en stock) est conservé.

## Tâches (TDD : test rouge → code → vert, puis suite complète)

1. **Zones et états** (`courses.py`) : `ZONES`, `deviner_zone(nom, rayon)` (épices et condiments par
   mots-clés, surgelés → congélateur, boissons → cave, frais durable → frigo, sinon placard sec),
   `valider_placard` accepte `zone` et `bientot`, rayon `specialise` ajouté à `RAYONS`.
   Tests : `test_courses.py`.
2. **Base** (`schema.sql`, `db.py`) : colonnes `zone`, `bientot` ; `enregistrer_placard`,
   `lire_courses` les portent ; `retirer_du_placard(conn, cle)`.
   Tests : `test_courses_db.py`.
3. **Disponibilité** (`diners.py`) : `disponibles(placard, courses)` = placard en stock (bientôt
   compris) + habituels rangés (`recurrent and not actif`) ; `secours` et `a_acheter` l'utilisent.
   Tests : `test_diners.py` — un habituel rangé rend un plat faisable, un habituel sur la liste non ;
   bientôt fini compte comme disponible.
4. **Import** (`placard_v2.py`, `db.reorganiser_placard`) : idempotent (relancé, il ne crée aucun
   doublon et ne repasse pas en épuisé ce qu'ils ont coché en stock entre-temps), sans suppression
   nette ; ajoute aux courses les épuisés importés (source `placard`). Branché dans
   `appliquer_schema.py`, qui l'annonce en à blanc avant `--appliquer`.
   Tests : `test_placard_v2.py` — noms alignés sur les ingrédients du carnet (un ingrédient de
   recette qui correspond à un élément importé a la même clé normalisée), le mode secours garde au
   moins ses 7 dîners une fois les frais passés en habituels, double import sans effet.
5. **Achat d'une recette → placard** (`db.enregistrer_article`) : un article `plat:` coché pris, de
   rayon durable (épicerie, surgelés, boissons, spécialisé), absent du placard, y entre en stock
   avec sa zone devinée. Les rayons frais (fruits-légumes, frais, boucherie, boulangerie) n'y
   entrent pas. Tests : `test_courses_db.py`.
6. **Écran** (`courses.py`) : le placard par zone (une section repliable par zone, compteur
   d'épuisés et de bientôt finis), un appui fait tourner En stock → Bientôt fini → Épuisé → En stock,
   ajout d'un élément avec choix de la zone, déplacement de zone. Hors ligne : même file d'attente.
   Tests : `test_courses.py` (HTML), `test_serveur.py` (routes).
7. **Version de page 30** (`valise.py`) : le téléphone jette l'ancienne page Courses.
8. Suite complète verte ; vérification dans Chrome sur `valise_test` (largeur téléphone et large) :
   parcours d'une zone, trois états, épuisé → courses, frais habituel → secours, achat d'une recette.

## Mise en production

Migration Neon (colonnes + import) **avant** le merge, avec l'accord de Julien ; à blanc d'abord,
qui liste les éléments créés, déplacés vers les habituels, et ajoutés aux courses.

## Hors périmètre

- Quantités (combien d'œufs) et dates de péremption.
- Liste d'équipement (ustensiles, appareils) : reste dans la checklist.
