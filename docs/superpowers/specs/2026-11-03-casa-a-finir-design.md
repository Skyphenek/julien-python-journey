# Casa Binomerie — À finir : l'anti-gaspi sans saisie

Décisions du 03/11/2026 (Julien) : **aucune date à saisir** — une durée de conservation par défaut par produit frais,
ajoutée à sa date d'entrée ; un produit dépassé reste en stock **« à vérifier »** (option B) ; le frigo actuel est
**daté par Claude** avec ce qu'on sait, le reste part du 03/11, validé sur la démo (option B) ; sur Aujourd'hui, seuls
les produits **qu'aucun repas prévu n'utilise à temps**, y compris « prévu trop tard » (option C). Approche 1 :
durées dans le code, dates calculées, seules les corrections sont stockées.

## Le problème

Julien et Laetitia oublient ce qui est au frigo et le jettent, ou ouvrent Deliveroo alors que le poulet acheté
dimanche doit être mangé. L'app connaît le stock et les dates d'achat (journal `achats`, depuis le 02/11) mais pas
quand un produit frais doit être fini. « Faisable tout de suite » (Dîners) ne regarde pas ce qui périme.

## Ce qui change pour eux

- **Rien à saisir.** Chaque produit du frigo a une date « à finir avant », estimée.
- **Aujourd'hui** : un bloc « À finir », au-dessus de « À acheter pour aujourd'hui », absent quand il est vide :
  - les produits **à vérifier** (date dépassée), avec [Fini] et [Encore bon] ;
  - chaque produit affiché a [Fini] (mangé, jeté) ;
  - les produits à finir **d'ici 2 jours** (aujourd'hui compris : date ≤ aujourd'hui + 2) qu'aucun repas prévu n'utilise
    à temps : « rien de prévu », ou « prévu vendredi, trop tard » ;
  - sous chaque produit, jusqu'à 3 plats du carnet qui l'utilisent, avec un bouton qui l'ajoute au premier dîner libre
    avant la date ([Ce soir], [Demain], [Mercredi]…) ; s'il n'y en a pas : « soirs pris jusqu'à jeudi », pas de bouton.
- **Dîners, « Faisable tout de suite »** : les plats qui utilisent un produit à finir passent en tête, badge « à finir ».
- **Proposer ma semaine** : un plat qui utilise un produit à finir sans repas prévu est placé d'abord sur un soir libre
  avant la date.

## Les dates

### Produits suivis

Le frais du frigo : les éléments du placard en stock de zone `frigo`, et les habituels des courses rangés (recurrent,
pas sur la liste, ou pris) dont la zone (`courses.deviner_zone`) est `frigo`. Congélateur, placard sec, épices et cave
ne sont pas suivis.

Décision du 03/11 (option A, après la revue) : un frais non habituel coché dans Courses (zone frigo, ex. des cuisses
de poulet pour une recette) **entre au placard du frigo** ce jour-là, en stock — sinon il disparaissait au « vider
les pris » sans jamais être suivi. La viande et le poisson (rayon boucherie) du placard du frigo **sortent seuls du
stock** quand un repas qui les utilise est marqué « Fait maison » (cuisinés en entier) ; les autres produits non.

### Date d'entrée

La plus récente de :
- le dernier achat de ce produit dans le journal `achats` (nom normalisé) ;
- pour un élément du placard, la date (heure de Paris) de son `maj_le`.

Sans aucune des deux (habituel jamais acheté depuis le 02/11, sans correction) : le produit n'est pas suivi.

### Durée (`voyage/conservation.py`)

`duree(nom)` en jours : l'exception du produit si elle existe (nom normalisé), sinon le défaut de son rayon
(`catalogue`), sinon 7.

| Rayon | Défaut |
|---|---|
| boucherie (viande, volaille) | 2 |
| frais (crèmerie, fromages, charcuterie, traiteur) | 7 |
| fruits-legumes | 5 |
| epicerie (sauces entamées) | 30 |
| specialise | 14 |

Exceptions : la durée d'un produit **fermé** (décision du 03/11 : une seule durée, pas d'état « entamé » ; un
produit entamé se corrige avec [Fini] ou [Encore bon]) — valeurs réalistes pour un frigo domestique :

| Jours | Produits |
|---|---|
| 1 | bœuf haché, porc haché, steak haché, steaks hachés, chair à saucisse, tartare, carpaccio, foies de volaille, tous les poissons et fruits de mer frais du rayon boucherie (saumon … langoustines, sauf morue salée) |
| 3 | fraises, framboises, myrtilles, mûres, groseilles, cassis, cerises, champignons de Paris, champignons, pleurotes, shiitakés, girolles, cèpes, pousses de soja, germes de haricot mungo |
| 4 | salade, sucrine, laitue, batavia, roquette, mâche, mesclun, jeunes pousses, épinards frais, persil, persil plat, coriandre, basilic, menthe, ciboulette, aneth, cerfeuil, estragon, basilic thaï |
| 5 | burrata, stracciatella |
| 7 | lait, lait entier, lait demi-écrémé, ricotta, jambon, jambon blanc, blanc de dinde |
| 10 | mozzarella, mozzarella di bufala, saumon fumé, truite fumée, carottes, chou blanc, chou rouge, chou vert, céleri-rave, poireaux, navets, panais, betteraves, radis noir, lardons, lardons fumés, allumettes de bacon, saucisses de Strasbourg, saucisses de Francfort, knacks, galettes de sarrasin, crêpes, pâte brisée, pâte feuilletée, pâte sablée, pâte à pizza, gnocchi, tortellini, raviolis frais, pâtes fraîches, tagliatelles fraîches, ravioles |
| 14 | crème fraîche, crème fraîche épaisse, crème liquide, crème fleurette, crème entière, mascarpone, yaourts, yaourt nature, yaourt grec, skyr, fromage blanc, faisselle, petits-suisses, crème dessert, kéfir, emmental râpé, fromage râpé, cheddar râpé, feta, halloumi, tofu, tofu fumé, chorizo, gingembre |
| 21 | parmesan, pecorino, pecorino romano, parmigiano reggiano, grana padano, comté, beaufort, emmental, gruyère, abondance, cantal, mimolette, gouda, cheddar, saucisson, saucisson sec, rosette, salami, guanciale, guanciale entier, pancetta, guanciale ou pancetta |
| 28 | œufs, beurre, beurre doux, beurre demi-sel |

### À finir avant, état

- `jusqu_au` = la correction si elle existe et vaut encore (voir plus bas), sinon date d'entrée + durée.
- **à vérifier** : `jusqu_au` < aujourd'hui ;
- **à finir** : aujourd'hui ≤ `jusqu_au` ≤ aujourd'hui + 2 (`A_FINIR_JOURS = 2`) ;
- sinon rien à signaler.

### Corrections (nouvelle table)

```sql
-- À finir (03/11/2026) : les dates corrigées à la main (« Encore bon », reprise du frigo).
CREATE TABLE IF NOT EXISTS a_finir (
    cle         TEXT        PRIMARY KEY,             -- nom normalisé du produit
    jusqu_au    DATE        NOT NULL
);
```

- Une correction l'emporte sur le calcul. Elle est supprimée quand le produit repart de zéro : coché dans Courses
  (`db.enregistrer_article`), remis en stock alors qu'il ne l'était pas (`db.enregistrer_placard`), ou [Fini].
- **Encore bon** : `jusqu_au` = aujourd'hui + 2 (`ENCORE_BON_JOURS`).
- **Fini** : l'élément du placard **du frigo** passe `en_stock = false` (et `bientot = false`) ; l'habituel du même
  nom revient sur la liste (`actif = true`, `pris = false`), comme quand il en manque — les deux s'il y a les deux.
  La correction est supprimée.

### Reprise du frigo (une fois, `reprises` : `a-finir-v1`)

Les habituels du frigo rangés sans achat au journal (donc sans date) : une correction `jusqu_au` = 03/11 + durée.
Ce qu'on sait déjà (`a_finir.FRIGO_CONNU`) entre au placard (zone frigo, en stock) avec sa correction :
- cuisses de poulet (nom des recettes) : achetées le 01/11 → `jusqu_au` = 01/11 + 2 = 03/11 ;
- galettes de sarrasin : 09/11 (date imprimée).

La liste datée est montrée sur la démo (copie prod) ; Julien la corrige avant l'écriture sur Neon.

## Couverture par les repas prévus

Un produit est **couvert** si un repas prévu (dîner, déjeuner ou brunch, `repas` sans issue), d'aujourd'hui à
`jusqu_au` inclus, contient un plat dont un ingrédient a ce nom normalisé. Un repas prévu qui l'utilise **après**
`jusqu_au` donne « prévu <jour>, trop tard » (le premier de ces jours). Les produits « à vérifier » sont toujours
affichés, couverts ou non.

## Plats suggérés

Pour un produit : les plats `genre` plat, `statut` carnet, non archivés, pour les deux (`pour` = `nous`, qui exclut
déjà les « jamais » de Laetitia), dont un ingrédient a ce nom. Tri : nombre de produits à finir utilisés
(décroissant), nombre d'ingrédients manquants (`disponibles`, croissant), minutes, nom. Les 3 premiers, avec « il
manque : … » si besoin.

Bouton : le premier jour d'aujourd'hui à `jusqu_au` sans dîner prévu ; libellé « Ce soir », « Demain » ou le nom du
jour. Il pose le plat en dîner ce jour-là par l'API repas existante, avec `si_libre` : le serveur refuse (409, « Ce
soir-là est déjà pris : recharge la page. ») si ce soir a été pris entre-temps ou est passé — une page en cache ne
peut pas écraser un dîner ni une issue. Aucun jour libre : pas
de bouton, « soirs pris jusqu'à <jour> ». Un produit à vérifier ne propose pas de plats : [Fini] ou [Encore bon]
d'abord (après « Encore bon », il redevient à finir, avec ses plats).

## Dîners et Proposer

- `secours` : à nombre de manquants égal, les plats qui utilisent un produit à finir (à finir ou à vérifier) passent
  en tête ; l'API renvoie leurs ids, la page affiche le badge « à finir ».
- `proposer` : avant le tirage, pour chaque produit à finir non couvert (par date), un plat du carnet qui l'utilise
  (avec les filtres habituels de Proposer, ≤ 45 min du lundi au jeudi, le plus rapide) est placé sur le premier soir
  à remplir ≤ `jusqu_au`, dans la limite des soirs à remplir ; avec Reproposer, seulement sur les jours à remplacer.
  Le reste de la semaine est tiré comme aujourd'hui.

## Écrans et API

- `POST api/a-finir/<cle>` avec `{"action": "fini" | "encore-bon"}` ; erreur 400 sur une action inconnue, 404 sur un
  produit non suivi.
- Aujourd'hui (page servie par le serveur) : bloc « À finir », style des blocs existants, largeur iPhone, mode sombre.
  Les boutons font comme « Hier soir ? » : envoi, rechargement ; hors connexion, « Pas envoyé : réessaie une fois
  connecté ».
- `VERSION_PAGE` +1 (43).

## Hors périmètre

Date imprimée lue sur photo, congélateur, notifications push, réglage des durées dans l'app.

## Limites connues

- Les dates sont des estimations : un emballé à date longue peut sortir plus tard qu'annoncé (« Encore bon »).
- Durée d'un produit fermé : un produit entamé (jambon, crème) peut tourner avant l'alerte ; l'app ne sait pas
  qu'il est ouvert.
- Un achat hors liste (pas coché dans Courses ni mis en stock) n'est pas suivi.
- Les produits entrés au placard par un achat restent visibles côté Stock (épuisés une fois finis).
- Un `maj_le` du placard touché pour une autre raison (bientôt fini) décale la date d'entrée d'un élément.

## Tests

- Durées : exception, défaut du rayon, inconnu → 7.
- Dates : entrée par l'achat, par le placard, la plus récente ; correction valable / ignorée après rachat ; pas de date
  → non suivi ; congélateur non suivi ; habituel rangé suivi, habituel sur la liste non suivi.
- États : à vérifier, à finir (bornes aujourd'hui et +2), rien.
- Couverture : couvert avant la date, prévu trop tard, non prévu ; à vérifier toujours affiché.
- Suggestions : filtres (carnet, pour nous, archivé), tri, 3 max, jour du bouton, soirs pris.
- Actions : fini (placard, habituel), encore bon, 400, 404 ; correction supprimée au rachat et à la remise en stock.
- Secours et Proposer : priorité aux plats à finir, refus respecté.
- Reprise `a-finir-v1` une seule fois.
- Page : bloc présent/absent, boutons.
- Démo sur copie des données de prod (frigo daté), testée par Julien avant migration et push/PR/merge.
