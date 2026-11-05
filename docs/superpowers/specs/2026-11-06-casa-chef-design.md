# Casa Binomerie — Chef : rendre les recettes du hub « meilleures que correctes »

Date : 06/11/2026 · Statut : validé en brainstorming (Julien), à relire

## Problème

Les recettes du hub (table `plats`, 124 lignes) se suivent sans accroc mais donnent un résultat « correct, sans
plus ». Ce qui manque n'est pas une fiche à part : c'est le petit truc du chef et le geste précis de grand-mère,
écrits dans la recette elle-même. Julien les lit sur l'iPhone, en cuisine : le contenu doit être dans l'app, hors
ligne, sans appel IA à l'usage.

## Décisions

1. **Un skill Claude Code `chef-casa` qui réécrit les recettes en place** (colonne `plats.recette`). L'app affiche
   déjà ce texte tel quel (`diners.py`, `pre.recette`, `pre-wrap`) : aucun changement d'app, aucune migration.
   Écartés : fiche séparée (nouvelle colonne + affichage, consultée à part, donc pas lue) ; « Demande au chef » en
   direct dans l'app (clé API, coût, réseau, premier appel LLM d'une app déterministe).
2. **Format (b)** : les trucs sont fondus dans les étapes, raison entre tirets, plus un bloc final
   « Ce qui fait la différence » de 3 lignes au plus.
3. **Neon fait foi.** Les fichiers de départ (`carnet_depart.py`, `recettes_*.py`, `recettes_mamma.json`) ne
   servent qu'à l'amorçage (table `reprises`) : on ne les modifie pas.
4. **Une session = 5 recettes au plus**, cuisinées ensuite ; le retour de Julien après cuisson est le seul juge.

## Règles de rédaction (le cœur du skill)

1. **Les secrets de Julien d'abord.** Avant toute proposition, le skill demande : « tu as un truc à toi sur ce
   plat ? ». S'il y en a un, il entre en premier, marqué *secret de grand-mère*, et prime sur toute proposition
   de Claude qui le contredit. *Secret de grand-mère* est réservé aux trucs de Julien ; *secret de mamma* reste la
   convention des recettes Mamma.
2. **2 à 4 trucs par recette, pas plus**, parmi : assaisonnement (acide, sel au bon moment, finition), technique
   (saisie, réduction, repos, monter au beurre), ingrédient qui change tout (de préférence déjà au placard),
   texture et dressage. Un truc qui n'améliore pas nettement le résultat n'est pas proposé. Pas de débat d'école
   (« côté jambon ou côté veau d'abord ») : si la version actuelle marche, on la garde.
3. **Test du geste** : chaque verbe d'action répond à trois questions, sinon il est réécrit :
   - avec quoi (spatule en bois, plat de casserole, doigts) ;
   - dans quel sens, comment (à plat comme une épingle, du centre vers les bords) ;
   - jusqu'à quel signal, vu, entendu ou senti (le beurre mousse et chante, l'alcool ne pique plus le nez).
   Un temps en minutes seul ne suffit pas : il accompagne le signal.
4. **L'ordre des étapes suit les trucs** : si un geste en contredit un autre (eau pour aplatir / viande sèche pour
   dorer), on réordonne (aplatir, puis sécher) et on le dit dans l'étape.
5. **Ne bouge pas** : liste d'ingrédients (seule une répartition est permise, ex. « dont 30 g froid »), `minutes`,
   `ingredients` JSONB, accords, `pour`. Les « jamais » de Laetitia (brain) restent dehors.
6. **Signaler sans corriger** ce qui est hors sujet (ex. « Pour 4 » alors qu'on est deux) : une ligne dans la
   proposition, pas dans la recette.
7. **Ton** : tutoiement, phrases courtes, comme les recettes existantes. Le bloc « Erreurs fréquentes », s'il
   existe, est absorbé par les étapes et le bloc final (pas deux encadrés qui disent la même chose).

Exemple de référence : `plat-saltimbocca`, réécrit et écrit dans Neon le 06/11/2026 (ancienne version :
`~/Claude/Work/perso/casa-sauvegardes/2026-11-06-plat-saltimbocca.json`).

## Ordre de passage

Calculé, pas choisi à la main :

1. plats non archivés, sans bloc « Ce qui fait la différence » (= pas encore passés) ;
2. triés par nombre de repas `issue = 'fait'` qui les contiennent (décroissant) ;
3. puis `statut = 'carnet'` avant `'a-tester'` ;
4. puis `genre` : plats avant accompagnements, entrées, desserts ;
5. puis nom.

Julien peut toujours demander une recette précise (« fais les lasagnes ») : elle passe devant.

## Déroulé d'une session

1. Le skill affiche les 5 prochaines recettes de la file ; Julien garde, retire ou en impose une.
2. Pour chaque recette : lecture dans Neon (version du jour, `maj_le` noté) → question « ton truc à toi ? » →
   avant/après complet + liste des changements et pourquoi → OK explicite de Julien → écriture.
3. Écriture = sauvegarde JSON de l'ancienne version dans `~/Claude/Work/perso/casa-sauvegardes/`
   (`AAAA-MM-JJ-<id>.json`), puis `UPDATE` seulement si `maj_le` n'a pas bougé depuis la lecture (sinon : arrêt,
   relecture, nouvelle proposition — Julien ou Laetitia ont pu corriger dans l'app), `maj_le = now()`.
4. Après cuisson, le retour de Julien (« ça a fait la différence » / « tel geste ne sert à rien ») déclenche une
   nouvelle passe sur la recette ; un geste inutile sort.

## Composants

| pièce | rôle |
|---|---|
| `.claude/skills/chef-casa/SKILL.md` (projet) | règles de rédaction, déroulé, exemple saltimbocca |
| `voyage/chef.py` | `file_de_passage(conn, n=5)`, `lire(conn, id)`, `ecrire(conn, id, texte, maj_lu, dossier)` |
| `voyage/test_chef.py` | TDD sur `valise_test` local : ordre de passage, recette déjà passée exclue, archivée exclue, écriture refusée si `maj_le` a bougé, sauvegarde créée avant l'`UPDATE` |

Le skill appelle `chef.py` via `.venv/bin/python` avec `voyage/.env` ; il n'écrit jamais en SQL à la main.

## Hors périmètre

- Changement d'app (affichage, mise en forme du bloc, mode « en cuisine »).
- Nouvelles recettes, recalcul des portions, modification des ingrédients ou des temps.
- Appel IA depuis l'app.

## Mesure du succès

Sur les 5 premières recettes passées et cuisinées : Julien juge que 4 au moins ont « fait la différence ».
Sinon, on revoit les règles avant de continuer.
