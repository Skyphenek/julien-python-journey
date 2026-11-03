# Casa Binomerie — Cave : stock de vins et vin du soir

Date : 03/11/2026 · Statut : validé en brainstorming (Julien), à relire

## Problème

La cave de Julien (22 bouteilles, inventaire du 25/10/2026) vit dans un artifact à part
(https://claude.ai/artifact/FtxxiBUcCzgKz6Cjf4E1iD) : « Bue » n'est gardé que dans un navigateur, Laetitia ne le
voit pas, rien ne relie les vins aux dîners prévus. Objectif : une cave partagée, tenue en un tap, qui propose
quoi ouvrir avec le dîner du soir.

## Décisions

1. **Onglet « Cave » dans la barre du hub** (6 onglets). Regrouper les onglets de la maison dans un seul, comme
   Vadrouille, est une piste pour plus tard, hors périmètre.
2. **Règle des belles bouteilles : par le prix.** Prix estimé haut > 30 € → jamais proposée du dimanche au jeudi ;
   proposée vendredi et samedi soir, ou sur demande (« Une belle bouteille ? »). Pas d'étiquette manuelle.
3. **La Cave ne contient que les vins à boire.** Les vins de cuisine restent au placard (« vin blanc », « vin rouge »,
   zone Cave de Courses). Le Chardonnay Castel et l'Aude ne sont pas repris.
4. **Accords déterministes, sans IA** : profils d'accord fixes, déduits des ingrédients des plats.
5. **Une bouteille sort par [Ouverte] (suggestion du soir) ou [Bue] (onglet Cave).** Pas de question « bouteille
   ouverte ? » sur Hier soir.

## Données

Table `cave`, une ligne par référence :

| colonne | type | sens |
|---|---|---|
| `id` | TEXT PK | identifiant (comme les plats) |
| `nom` | TEXT NOT NULL | « Le Clos des Fées » |
| `producteur` | TEXT | « Hervé Bizeul » |
| `appellation` | TEXT | « Côtes du Roussillon Villages » |
| `region` | TEXT | « Roussillon » |
| `couleur` | TEXT NOT NULL | `rouge`, `blanc`, `rose`, `bulles`, `doux` |
| `millesime` | INT NULL | 2020 ; NULL = sans millésime |
| `quantite` | INT NOT NULL ≥ 0 | bouteilles en cave |
| `debut`, `fin` | INT NOT NULL | fenêtre à boire (années), `debut ≤ fin` |
| `prix_bas`, `prix_haut` | INT NULL | prix caviste estimé (€) ; NULL = inconnu |
| `accords` | JSONB | liste de profils (voir plus bas) |
| `note` | TEXT | « Offert par Yann » |
| `maj_le` | TIMESTAMPTZ | dernière modification |

Une référence à 0 reste en base (repli « Bues » de l'onglet, pour la racheter ou s'en souvenir).

**Statut** (année de Paris `A`) : `debut > A` → **à garder** ; sinon `fin ≤ A` → **à boire vite** ; sinon
**prête**. Comme l'artifact.

**Valeurs par défaut à l'ajout** (millésime `M`, ou l'année en cours sans millésime) :
rouge `M+2 … M+6` ; blanc et rosé `M … M+2` ; bulles et doux `M … M+5` ; sans millésime : `A … A+2`.
Le début n'est jamais avant l'année en cours. Accords par défaut selon la couleur :
rouge → `boeuf, charcuterie` ; blanc → `poisson, fromage` ; rosé → `legumes, apero` ; bulles → `apero` ;
doux → `dessert, fromage`.

### Reprise de départ (une fois, table `reprises`, nom `cave-v1`)

Les 19 références à boire de l'artifact (`voyage/cave_depart.py`), quantités, fenêtres, prix et notes repris
tels quels, accords convertis en profils :

| vin | millésime | profils |
|---|---|---|
| Le Clos des Fées | 2020 | agneau, gibier |
| Château Sociando-Mallet | 2011 | boeuf |
| Nuits-Saint-Georges « Les Longecourts » | 2018 | volaille, boeuf, fromage |
| Connétable Talbot | 2016 | agneau, boeuf |
| Lucile Avril (Châteauneuf-du-Pape) | 2020 | agneau, gibier |
| Esprit de Granit (Saint-Joseph) | 2019 | charcuterie, boeuf, volaille |
| Le Temps des Épices | 2019 | epice |
| Château Peyrouquet | 2023 | boeuf, tomate |
| Billecart-Salmon Brut Rosé | — | apero, poisson, dessert |
| Pinot Noir Réserve (Meyer-Fonné) | 2022 | volaille, poisson |
| Mourguettes | — | legumes, agneau |
| Maddalena Müller-Thurgau (×2) | 2024 | fromage, poisson |
| Plan Cuvé | — | apero, charcuterie |
| Saint-Amour | 2022 | charcuterie, porc |
| Plan de Dieu « Les Aumôniers » | 2023 | boeuf, tomate |
| Cuvée des Nobles (Cheverny) | — | fromage, fruits-de-mer |
| Muscat de Beaumes-de-Venise | 2021 | dessert |
| Cuvée du Baptême (Jurançon) | 2023 | dessert, fromage |
| Partages (rosé) | — | legumes, tomate |

Non repris : Chardonnay Grande Réserve (Castel) et Aude (Cellier de l'Orb), vins de cuisine.

## Accords

**Profils** (liste fixe, `accords_vins.PROFILS`, dans cet ordre de priorité) : `boeuf`, `agneau`, `gibier`,
`volaille`, `porc`, `charcuterie`, `poisson`, `fruits-de-mer`, `fromage`, `epice`, `tomate`, `legumes`,
`apero`, `dessert`.

**Profil d'un plat** : chaque ingrédient (clé `catalogue.cle_catalogue`) est cherché dans une table fixe
ingrédient → profil (`accords_vins.PAR_INGREDIENT`, quelques dizaines de noms du catalogue : bœuf, steak, steaks
hachés, paleron ou joue de bœuf → `boeuf` ; cuisses de poulet, poulet, pintade → `volaille` ; saumon, cabillaud
→ `poisson` ; crevettes, moules → `fruits-de-mer` ; lardons, guanciale ou pancetta, chorizo, jambon →
`charcuterie` ; parmesan, comté, chèvre… → `fromage` ; curry, épices tacos, harissa, pâte de curry → `epice` ;
tomates pelées, passata, pâte à pizza → `tomate` ; etc.). Un accompagnement ne compte pas. Un plat sans aucun
profil viande, poisson ou fromage prend `legumes` s'il a des légumes. Le **profil principal** est le premier
profil du plat dans l'ordre de priorité ; les autres sont secondaires. Repas composé : profil principal = celui
du premier plat de genre `plat`, profils secondaires = tous les autres profils de ses plats.

**Suggestion** `suggerer(cave, principal, secondaires, jour, belle=False)` → au plus 3 bouteilles :

1. écartées : `quantite = 0` ; statut à garder ; si `belle` est faux et que le jour est dimanche à jeudi,
   `prix_haut > 30` (`SEUIL_BELLE = 30`) ;
2. points : +2 si le profil principal est dans ses accords, +1 par profil secondaire dans ses accords ;
   0 point → écartée ;
3. tri : points décroissants, puis `fin` croissante, puis `prix_haut` croissant (inconnu en dernier), puis nom.

Avec `belle=True` : seules les bouteilles à `prix_haut > 30` sont candidates, quel que soit le jour (même filtre
et même tri par ailleurs).

## Interfaces

### Onglet Cave (`/cave`)

- En-tête : bouteilles en cave, valeur estimée (somme bas–haut), nombre à boire d'ici fin d'année.
- Trois groupes dans l'ordre **À boire vite**, **Prêtes**, **À garder** ; dans un groupe, tri par `fin` puis nom.
  Repli **Bues** (références à 0) en bas.
- Fiche : nom, millésime (ou « sans millésime »), pastille de couleur, fenêtre `debut–fin`, quantité, bouton
  **[Bue]** (−1).
- Tap sur la fiche : édition (quantité ±, fenêtre, accords en puces cochables, note, [Retirer]).
- **[+ Ajouter]** : nom, couleur, millésime, quantité, prix optionnel ; fenêtre et accords par défaut (voir
  Données), corrigeables ensuite.
- Écritures par la même file hors ligne que Courses (envoi rejoué au retour du réseau).

### Aujourd'hui, bloc « Ce soir »

Sous le dîner prévu (repas du jour, moment dîner, avec plats, sans issue) :

> 🍷 À ouvrir : Saint-Joseph « Esprit de Granit » 2019 · à boire avant 2028   [Ouverte] [Autre]

- [Autre] passe à la suivante (3 au plus, puis revient à la première).
- Lien « Une belle bouteille ? » : affiche la première suggestion `belle=True` (absent s'il n'y en a pas).
- [Ouverte] : `POST api/cave/<id>/bue`, puis rechargement de la page.
- Rien n'est affiché si aucun dîner n'est prévu ou si aucune bouteille ne colle (ni la ligne, ni le lien).

### Barre du hub

`HUB` : Aujourd'hui, Dîners, Courses, **Cave**, Budget, Vadrouille. Libellés et espacement resserrés pour tenir
sur 375 px de large sans défilement horizontal.

## Architecture

- `voyage/accords_vins.py` (pur) : `PROFILS`, `PAR_INGREDIENT`, `SEUIL_BELLE`, `profils_du_plat(plat)`,
  `profils_du_repas(plats)` → `(principal, secondaires)`, `suggerer(...)`.
- `voyage/cave.py` : `COULEURS`, `valider_bouteille(corps)`, `statut(b, annee)`, `par_defaut(couleur, millesime,
  annee)`, `cave_en_html()` (page, style et JS, comme `courses.py`).
- `voyage/cave_depart.py` : `NOM_REPRISE = "cave-v1"`, `CAVE_DEPART` (19 références).
- `voyage/schema.sql` : `CREATE TABLE IF NOT EXISTS cave (...)`.
- `voyage/db.py` : `lire_cave(conn)`, `enregistrer_bouteille(conn, b)` (upsert par id),
  `boire(conn, id)` (`quantite = GREATEST(quantite - 1, 0)`, renvoie False si l'id n'existe pas),
  `retirer_bouteille(conn, id)`, `poser_cave(conn, nom_reprise, references)` (une fois).
- `voyage/serveur.py` : `GET /cave`, `GET /api/cave`, `POST /api/cave` (400 si invalide),
  `POST /api/cave/<id>/bue` (404 si inconnue), `DELETE /api/cave/<id>` (404 si inconnue) ; la route `/` calcule
  les suggestions du dîner prévu et les passe à `aujourdhui_en_html(..., vins=(), belle=None)`.
- `voyage/casa.py` : la ligne vin et son script.
- `voyage/design.py` : `HUB` et `ICONES_HUB["cave"]`.
- `voyage/appliquer_schema.py` : la reprise `cave-v1`, à blanc et pour de vrai.
- `voyage/valise.py` : `VERSION_PAGE = 45`.

## Tests (TDD, base `valise_test`)

- `test_accords_vins.py` : profils de plats réels du carnet (bourguignon → boeuf, curry → epice, poulet
  rôti → volaille, plat sans viande → legumes) ; repas composé ; suggestion : seuil 30 € en semaine et pas le
  samedi, `belle=True`, à garder et quantité 0 écartées, 0 point écartée, ordre de tri, plafond 3, liste vide.
- `test_cave.py` : validation (couleur, millésime, quantité ≥ 0, debut ≤ fin, accords connus), statut aux
  bornes, valeurs par défaut, page `/cave` (groupes, repli Bues), reprise : 19 références, aucune de cuisine.
- `test_cave_db.py` : upsert, bue jamais sous 0, id inconnu, retrait, reprise une seule fois.
- Routes : 200/400/404 ; Aujourd'hui : ligne vin présente avec dîner prévu et vin qui colle, absente sinon ;
  hub à 6 onglets.

## Livraison

Démo sur `valise_copie` (Mac et iPhone), migration Neon à blanc puis `--appliquer` avec l'accord de Julien,
puis push, PR, merge.

## Hors périmètre

Regroupement des onglets maison ; suggestion dans Dîners ; historique « bu avec quoi » ; photo d'étiquette ou
IA ; vins de cuisine dans la Cave.
