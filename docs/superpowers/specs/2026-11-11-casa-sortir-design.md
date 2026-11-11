# Casa — sous-hub Sortir (les envies du couple)

Date : 11/11/2026 — validé par Julien en session. Second chantier « vrai hub », après la barre Popote
(`2026-11-11-casa-barre-popote-design.md`).

## Problème

Une routine Claude remplit depuis le 15/10/2026 la base Notion « Idées couple 💑 » (≈ 5 idées tous les 3-4 jours,
~40 lignes). Aucune n'a jamais changé de statut ni reçu de note : la génération marche, le tri et la décision non.
Doublons (Aroma-Zone ×2, Philharmonie ×2, illuminations ×3…), un tiers en Premium, cadeaux mêlés aux sorties.

## Décisions

- Le cœur de Sortir : **une pile à trier, des Envies (ça plaît aux deux), un tirage « ce week-end », un rappel des
  dates de fin**, un retour après la sortie qui nourrit la routine.
- **La Casa devient la seule source des sorties** ; la routine y écrit par l'API. Notion ne garde que les **cadeaux**
  (pour Julien seul : la Casa est partagée, Laetitia verrait ses cadeaux).
- **« Qui es-tu ? »** une fois par appareil (Julien / Laetitia), gardé dans `localStorage` (`casa-qui`), modifiable.
  Une étiquette, pas une sécurité.
- Une idée ajoutée à la main = « ça me tente » de son auteur, elle part dans la pile de l'autre.

## Règles

États : `a-trier` → `envie` | `ecartee` ; `envie` → `prevue` | `faite` | `ecartee` ; `prevue` → `faite` | `envie`.

- `a-trier` : au moins un avis manquant. Chacun ne voit dans sa pile que ce qu'il n'a pas jugé.
- Deux « ça me tente » → `envie`. Un « bof » → `ecartee` (gardée en base : la routine ne la repropose pas).
- `prevue` : une date choisie (`le`). Date passée → affichée dans Faites avec « Alors, c'était comment ? ».
- `faite` : pouce (`haut` / `bas`) + une ligne de retour, facultatifs.
- Envie « Plus envie » → `ecartee`.

Champs d'une idée : `titre` (obligatoire, 1-200 car.) ; `type` ∈ ciné, théâtre, concert, expo, resto-bar, balade,
atelier, escapade ; `budget` ∈ gratuit, moyen (~30 €), premium (~80 € +) ; `reservation` ∈ non, conseillee,
obligatoire ; `debut`, `fin` (dates, facultatives) ; `lien` (http/https) ; `infos` (texte) ; `source` ∈ routine,
julien, laetitia ; `avis_julien`, `avis_laetitia` ∈ null, oui, non ; `etat` ; `le` (date prévue) ; `pouce`, `retour` ;
`cree_le`, `maj_le`.

Anti-doublon (serveur) : refus si une idée existante (tout état) a le même titre normalisé (casse, accents,
ponctuation, mots vides retirés) ou le même lien (sans query string ni « / » final). Réponse 409 avec l'id existant.

Tirage « Ce week-end ? » : 2 à 3 Envies ; d'abord celles qui finissent dans ≤ 15 jours ; puis budgets mêlés, au plus
une Premium ; pas deux du même type. « Retirer » relance (hasard injectable pour les tests).

## Écrans

Barre du bas : **Aujourd'hui · Popote · Sortir · Budget · Vadrouille**. Sortir : icône billet (trait `_TRAIT`), couleur
`--sortir` (violet, valeurs claire et sombre via `sombre()`).

Page `sortir`, onglets **À trier · Envies · Faites** (compteur sur À trier) :
- **À trier** : une carte à la fois (titre, type, budget, réservation, « jusqu'au … », infos, lien) ; deux gros boutons
  **Bof** / **Ça me tente** ; pile vide : « Rien à trier. »
- **Envies** : finissent bientôt en tête, puis récentes d'abord ; bouton **Ce week-end ?** ; actions par Envie :
  **On y va** (date → prévue), **Fait**, **Plus envie** ; **+ Ajouter une idée** (titre seul obligatoire).
- **Faites** : historique (pouce, retour) ; prévues passées en tête avec « Alors, c'était comment ? ».

**Aujourd'hui** : un encart Sortir seulement s'il y a quelque chose — Envie qui finit dans ≤ 7 jours, sortie prévue
dans ≤ 7 jours, et le vendredi et le samedi « Ce week-end ? » (lien vers le tirage).

Pas d'emoji, pas d'`innerHTML`, `localStorage` dans un `try`, marche hors ligne comme le reste (copie + file d'envoi).

## API

- `GET api/sorties` : toutes les idées (la page trie).
- `POST api/sorties` : créer (page ou routine) ; 409 si doublon.
- `POST api/sorties/<id>/avis` `{qui, avis}` ; `POST api/sorties/<id>` (état, `le`, pouce, retour).
- Derrière le même secret que le reste de l'app.

## Reprise et routine

- Reprise unique (`reprises`, clé `sorties-v1`) : les sorties de Notion (pas les cadeaux), dédoublonnées, en `a-trier`
  pour les deux, `source = routine`.
- Routine : consignes mises à jour — écrire dans `api/sorties` ; sorties seulement (cadeaux toujours dans Notion) ;
  au plus 1 Premium par envoi ; lire `GET api/sorties` avant (écartées, faites et retours) pour viser juste. Sa
  configuration actuelle est relevée au moment du plan.

## Tests

Règles (états, envie, écartée, tirage avec hasard fixé, anti-doublon), base (`valise_test`), routes API, page (marqueurs
comme les autres pages), encart d'Aujourd'hui. Démo sur copie de prod (Mac + iPhone, les deux identités) avant
push / PR.

## Hors périmètre

Météo dans le tirage, ajout depuis la feuille de partage iOS, cadeaux, sous-hubs Invités et Maison.
