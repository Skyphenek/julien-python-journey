# Casa — barre du bas regroupée : « Popote » (Dîners · Courses · Cave)

Date : 11/11/2026 — validé par Julien en session. Premier des deux chantiers « vrai hub » ; le second est le sous-hub
Sortir (spec séparée).

## Problème

La barre du bas a 6 entrées (Aujourd'hui, Dîners, Courses, Cave, Budget, Vadrouille) : pleine sur iPhone, aucune place
pour un nouveau sous-hub.

## Décision

- Barre du bas : **Aujourd'hui · Popote · Budget · Vadrouille** (4 entrées). Sortir s'ajoutera avec sa propre livraison
  (cible : Aujourd'hui · Popote · Sortir · Budget · Vadrouille). Budget reste seul jusqu'au sous-hub Maison.
- **Popote** regroupe Dîners, Courses et Cave. Icône et couleur de Dîners (couverts, orange). Un appui ouvre **toujours
  Dîners** (`diners`).
- Sur les pages `diners`, `courses` et `cave`, l'entrée active de la barre est Popote.

## Onglets de Popote

- Une barre **Dîners · Courses · Cave** en haut des trois pages, liens vers `diners`, `courses`, `cave` (adresses
  inchangées : favoris, liens d'Aujourd'hui et app installée continuent de marcher).
- Style distinct des onglets internes de Dîners (Ce soir · Semaine · Recettes) : texte plus grand, sans fond, page
  active soulignée de sa couleur (`--diners`, `--courses`, `--cave`), `aria-current="page"` sur l'active.
- Le grand titre `h1` (Dîners / Courses / Cave) est retiré de ces trois pages : l'onglet actif le remplace.
- Sur ordinateur (≥ 900 px) : colonne de gauche à 4 entrées ; mêmes onglets en haut du contenu.

## Inchangé

Contenu des pages, Aujourd'hui (ses liens `diners#ce-soir` etc.), Budget, Vadrouille, bouton du thème, routes serveur.

## Tests

- `nav_hub` : 4 entrées dans l'ordre Aujourd'hui, Popote, Budget, Vadrouille ; Popote pointe vers `diners`.
- `nav_hub("diners")`, `("courses")`, `("cave")` : Popote active.
- Les trois pages contiennent la barre Dîners · Courses · Cave avec le bon onglet actif, et plus de `h1` de titre.
- Plus aucun `data-hub="diners"`, `"courses"` ou `"cave"` dans la barre du bas.
- Démo locale sur copie de prod (Mac + iPhone) avant push / PR.

## Hors périmètre

Sous-hub Sortir, sous-hub Maison, mémoire de la dernière sous-page ouverte (écartée : Popote ouvre toujours Dîners).
