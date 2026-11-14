# Casa — Journal des repas passés et « Hier soir ? » qui dit ce qu'on a mangé

Date : 14/11/2026, validé par Julien en session. Une livraison, une PR, démo sur copie de prod avant le push.

## Problème

1. Rien ne montre ce qu'on a mangé les semaines passées : la table `repas` garde tout (depuis le 27/10/2026), mais
   l'app n'affiche que la semaine à venir.
2. « Hier soir ? » (page Aujourd'hui) enregistre seulement l'issue (fait maison, commandé, dehors, autre) avec les
   plats prévus : si rien n'était prévu, ou si on a mangé autre chose, le repas « fait maison » reste sans plat ou
   faux. Et les repas passés jamais renseignés (« non noté ») ne se corrigent nulle part.

## 1. Onglet « Passé » dans Dîners

- Onglets internes de `/diners` : **Ce soir · Semaine · Passé** (`#passe`).
- Une carte par **semaine calendaire** (lundi → dimanche), de la plus récente à la plus ancienne ; la semaine en
  cours s'arrête à hier. 8 semaines par chargement, puis un bouton « Semaines plus anciennes » (s'il en reste).
- En tête de carte : « Semaine du 9 nov. » et le **bilan** : nombres de repas `maison` (issue fait), `commandé`,
  `dehors`, `autre`, `non noté` (plats prévus, pas d'issue) — seuls les nombres non nuls — et le coût estimé des
  repas faits maison (somme de `prix_paris.cout_repas` de leurs plats).
- Puis les 7 jours (hors jours futurs) : une ligne **Soir** (dîner) toujours, une ligne **Midi** seulement si un
  déjeuner ou un brunch existe. Chaque ligne : les noms des plats (plat principal d'abord) ou « — », et un badge :
  maison / commandé / dehors / autre / non noté (rien pour « — »).
- Un appui sur un nom de plat ouvre sa fiche (le panneau existant).
- **Corriger un « non noté »** : un appui sur le badge « non noté » ouvre sur la ligne les choix
  **Fait maison · Commandé · Dehors · Autre** ; le choix enregistre le repas (mêmes plats, cette issue) par
  `POST api/repas`, la carte se met à jour. Possible jusqu'à 60 jours en arrière (`valider_repas`) ; au-delà, pas
  de choix.
- API : `GET /api/diners/passe?avant=<iso d'un lundi>` → `{"semaines": [...], "suite": "<iso du lundi suivant à
  demander>" | null}`. Sans `avant` : à partir de la semaine en cours. Lecture seule.

## 2. « Hier soir ? » : Fait maison → ce qu'on a mangé

- Commandé, Dehors, Autre : inchangés (un appui enregistre, la page se recharge).
- **Fait maison**, si le dîner d'hier avait des plats prévus : le bloc demande « C'était bien : Carbonara + Purée ? »
  avec **Oui** (enregistre `fait` avec ces plats) et **Autre chose** (passe au choix du plat).
- **Fait maison** sans plat prévu, ou après « Autre chose » : un champ « Qu'avez-vous mangé ? » avec les recettes
  en suggestions (noms des plats non archivés, `<datalist>`) ; **Valider** enregistre `fait` avec le plat choisi
  (reconnu par son nom exact) ; **Je ne sais plus** enregistre `fait` sans plat. Un nom inconnu : message « Choisis
  une recette de la liste » (pas d'enregistrement).
- Le reste du bloc (disparaît une fois renseigné, rechargement) ne change pas.

## Inchangé

Table `repas` (aucune migration), compteur Deliveroo (il lit les issues : les corrections le rendent plus juste),
Semaine, Proposer, Ce soir.

`VERSION_PAGE` +1 (59).

## Hors périmètre

Changer les plats d'un repas passé depuis le journal ; journal des déjeuners en « Hier midi ? » ; statistiques
par recette.
