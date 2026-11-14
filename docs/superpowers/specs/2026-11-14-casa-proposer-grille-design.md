# Casa — « Proposer ma semaine » : grille Midi / Soir

Date : 14/11/2026, validé par Julien en session. Une livraison, une PR, démo sur copie de prod avant le push.

## Problème

« Proposer ma semaine » ne remplit que des dîners, avec une cible fixe de 4 soirs (`CIBLE_SOIRS`) dont l'app choisit
les jours. Julien et Laetitia veulent aussi des déjeuners proposés (n'importe quel jour) et pouvoir remplir toute la
semaine s'ils le souhaitent.

## Décisions

- **Grille à cocher** : le bouton « Proposer ma semaine » ouvre une grille 7 jours (ceux de `d.semaine`) × **Midi**
  (déjeuner) / **Soir** (dîner). On coche les repas à remplir, puis **Proposer**.
  - Une case dont le repas est déjà posé (des plats ou une issue) ou dont le jour est passé : affichée remplie,
    pas cochable. Proposer ne touche jamais à ce qui est posé.
  - Le midi d'un jour qui a déjà un brunch posé compte comme posé.
  - La grille retient la dernière sélection par téléphone (`localStorage` `diners:grille`, la liste des cases
    `jour de la semaine (0-6) + moment`, pas des dates). Premier usage : Soir du lundi au jeudi cochés.
  - Sous la grille : « N repas à proposer » (cases cochées et libres) ; Proposer est inactif à 0.
  - « Annuler » referme la grille sans rien proposer.
- **Règles de choix**
  - Soir : celles d'aujourd'hui (plats `genre` plat, pour nous deux, avec recette, non archivés, pas `brunch-` ;
    ≤ 45 min du lundi au jeudi ; rien de mangé ces 14 jours ; un plat à tester au plus par semaine, le dimanche
    d'abord s'il y en a un ; un accompagnement par `accompagner` quand le plat a des accords).
  - Midi : mêmes candidats, mais **≤ 30 min tous les jours** (`MINUTES_MIDI = 30`) et **sans accompagnement**.
  - Pas de doublon dans la semaine, midi et soir confondus (ni avec ce qui est déjà posé, tous moments).
  - Anti-gaspi : pour chaque produit à finir (`a_finir`), d'abord le plus rapide des plats du carnet qui l'utilise,
    sur la première case cochée (midi avant soir le même jour) avant sa date, en respectant la règle de temps de la
    case.
  - Plus d'étalement automatique ni de cible : on remplit exactement les cases cochées libres (ou moins si aucun plat
    ne convient).
- **Reproposer** : change les repas que la dernière proposition a posés et qu'on n'a pas modifiés depuis, midi
  compris (`derniereProposition` indexée par `jour + moment`).
- **API** : `POST /api/diners/proposer` accepte `{"cases": [{"jour": iso, "moment": "diner"|"dejeuner"}],
  "remplacer": [{"jour", "moment"}]}` et rend `{"menus": {"<iso>|<moment>": [ids]}}`. L'ancien corps
  (`remplacer` = liste de dates, sans `cases`) garde l'ancien comportement (4 soirs) pour les pages en cache.
- `VERSION_PAGE` +1 (57).

## Inchangé

Ajout à la main (« + déjeuner ou brunch »), Ce soir, « Ajouter les ingrédients de la semaine aux courses » (les
déjeuners posés y entrent déjà : tous moments), coût de la semaine, table `repas` (aucune migration).

## Limite

« Léger » à midi = ≤ 30 min de préparation ; aucune donnée ne dit si un plat est copieux. Marquer des plats « midi »
est hors périmètre.

## Hors périmètre

Proposer des brunchs ; restes du dîner de la veille ; marquage « midi » des recettes.
