# Design — Casa Binomerie (hub maison v1) : Aujourd'hui, Dîners, Courses, Colis

> « Casa Binomerie » : nom de code (2026-10-28), peut-être définitif.

## Contexte et objectif

L'app « En Vadrouille » (voyage/) sert à Julien et Laetitia pour préparer et vivre leurs voyages.
On l'élargit en **hub du foyer** : En Vadrouille devient une section parmi d'autres.

Ce qu'ils s'envoient le plus par message : ce qu'on mange le soir même, les courses, des trucs
admin, des heures de livraison avec les codes. Ce qu'ils ratent : les courses — résultat,
**Deliveroo ~3 fois par semaine** (mesure de départ, 2026-10-28).

**Objectif** : que la question « on mange quoi ce soir ? » ait une réponse avant 19h30, avec les
ingrédients à la maison. **Critère de succès** : ≤ 1 commande Deliveroo par semaine en moyenne
sur les 6 semaines qui suivent la mise en prod (mesuré par l'app elle-même, voir « Soirs »).

**Hors scope v1** : admin / échéances (v1.1), Gaïa, appart (contrats, garanties), lecture
automatique des mails de livraison (Gmail, v2), import automatique d'une recette depuis un lien
(v2, voir plus bas), photos, quantités et unités dans les courses, notifications push, répartition des tâches ménagères.

## Architecture

Même repo, même serveur Flask, même base Neon, même design D (maquette retenue), même PWA.
Pas de nouvelle app.

```
/                     → Aujourd'hui (nouvel accueil du hub)
/diners               → carnet de plats + semaine + secours
/courses              → liste partagée
/colis                → livraisons attendues
/vadrouille           → l'actuel accueil des voyages (liste)
```

**Compatibilité En Vadrouille** (garantie par des tests) :
- `/` et `/vadrouille` acceptent tous les deux `?v=<code>`, `?nouvelle`, `?modifier=<code>` et
  servent exactement les mêmes pages qu'aujourd'hui. Seul `/` **sans paramètre** change.
- Toutes les adresses de l'app sont relatives (`api/…`, `?v=…`, `sw.js`) : elles se résolvent
  pareil depuis `/` et `/vadrouille`. Les seuls liens à changer sont les retours « ← Tous les
  voyages » et la redirection après suppression d'un voyage (`./` → `vadrouille`).
- Le préchargement hors ligne des voyages à venir reste déclenché par la liste des voyages.
- Les 462 tests existants restent verts sans modification de leurs attentes, sauf celle qui
  lisait la liste des voyages sur `/` (elle la lit sur `/vadrouille`).

- Toutes les routes restent sous `/v/<ACCES_SECRET>/`. C'est la seule protection : les codes de
  colis et de casier y vivront, donc le secret doit rester long et hors du repo (déjà le cas).
- Compatibilité : `/?v=<code>` continue d'ouvrir un voyage (liens déjà enregistrés sur les
  téléphones) ; seul `/` sans paramètre change de rôle.
- Navigation du hub : barre du bas (mobile) / barre latérale (web, option 2 retenue) :
  Aujourd'hui · Dîners · Courses · Colis · En Vadrouille. Une entrée n'apparaît qu'une fois son
  module livré (pas de lien mort). La page d'un voyage garde sa propre navigation par rubriques
  (Valise, Avant…) et un lien retour vers En Vadrouille.
- PWA : le nom installé devient « Casa Binomerie » (court : « Binomerie »). Sur iPhone, une app
  déjà installée garde l'ancien nom jusqu'à réinstallation depuis Safari.
- Nouveaux modules Python, logique pure testable sans base, sur le modèle de `souvenirs.py` /
  `a_voir.py` (validation + rendu HTML + style + script) :
  - `diners.py` — carnet, semaine, secours
  - `courses.py` — liste, rayons, récurrents
  - `colis.py` — livraisons
  - `aujourdhui.py` — assemble l'écran d'accueil à partir des trois autres
- Les écritures se font comme ailleurs : id choisi par le téléphone, `POST` d'upsert, `DELETE`
  ciblé, champ `maj_le`.

## Modèle de données

```sql
-- Le carnet : les plats qu'on sait faire, et leur recette. ingredients = liste de noms (texte
-- libre), reliés aux courses par le nom. recette : la marche à suivre (texte libre, quantités
-- comprises). lien : la recette d'origine (site, Instagram…). rapide : prêt en 20 min ou moins.
CREATE TABLE IF NOT EXISTS plats (
    id          TEXT        PRIMARY KEY,
    nom         TEXT        NOT NULL,
    minutes     SMALLINT    NOT NULL CHECK (minutes BETWEEN 1 AND 600),
    genre       TEXT        NOT NULL DEFAULT 'plat'
                            CHECK (genre IN ('plat', 'accompagnement', 'entree', 'dessert')),
    ingredients JSONB       NOT NULL DEFAULT '[]',
    recette     TEXT        NOT NULL DEFAULT '',
    lien        TEXT        NOT NULL DEFAULT '',
    note        TEXT        NOT NULL DEFAULT '',
    archive     BOOLEAN     NOT NULL DEFAULT false,
    maj_le      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Les soirs : ce qui est prévu, et ce qui s'est vraiment passé. C'est aussi la mesure du succès.
-- issue : NULL tant que le soir n'est pas passé / pas renseigné.
CREATE TABLE IF NOT EXISTS soirs (
    jour        DATE        PRIMARY KEY,
    plat        TEXT        REFERENCES plats(id) ON DELETE SET NULL,
    issue       TEXT        CHECK (issue IN ('fait', 'commande', 'dehors', 'autre')),
    maj_le      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- La liste de courses. rayon : une valeur de RAYONS (courses.py). recurrent : revient en un tap
-- depuis « Habituels ». source = 'plat:<id>' quand l'article vient du planning, '' sinon.
CREATE TABLE IF NOT EXISTS courses (
    id          TEXT        PRIMARY KEY,
    nom         TEXT        NOT NULL,
    rayon       TEXT        NOT NULL DEFAULT 'autre',
    pris        BOOLEAN     NOT NULL DEFAULT false,
    recurrent   BOOLEAN     NOT NULL DEFAULT false,
    source      TEXT        NOT NULL DEFAULT '',
    maj_le      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Le placard : ce qu'on a toujours (pâtes, œufs, riz…). en_stock passe à false quand on le
-- signale épuisé (il part alors dans les courses), et à true quand il est coché « pris ».
CREATE TABLE IF NOT EXISTS placard (
    nom         TEXT        PRIMARY KEY,
    en_stock    BOOLEAN     NOT NULL DEFAULT true,
    maj_le      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Les colis attendus. code : code de retrait / casier / digicode à donner au livreur.
CREATE TABLE IF NOT EXISTS colis (
    id          TEXT        PRIMARY KEY,
    quoi        TEXT        NOT NULL,
    transporteur TEXT       NOT NULL DEFAULT '',
    jour        DATE,
    creneau     TEXT        NOT NULL DEFAULT '',
    code        TEXT        NOT NULL DEFAULT '',
    lieu        TEXT        NOT NULL DEFAULT '',
    qui         TEXT        NOT NULL DEFAULT '',
    recu        BOOLEAN     NOT NULL DEFAULT false,
    maj_le      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS colis_attente ON colis (recu, jour);
```

Migration : ajouts uniquement (`CREATE TABLE IF NOT EXISTS`), via `appliquer_schema.py`, sur Neon
après accord de Julien. Aucune table existante modifiée.

## Comportements

### Dîners

- **Carnet = livre de recettes** : un seul endroit pour les recettes au lieu de les chercher à
  droite à gauche. Ajouter / modifier / archiver un plat (nom, minutes, ingrédients, recette,
  lien d'origine, note). Recherche par nom ou ingrédient (« courgette » → tous les plats qui en
  ont). Fiche plat lisible en cuisine : ingrédients puis étapes, gros texte, l'écran ne se met
  pas en veille (Wake Lock, si le navigateur le permet). Rempli par Julien et Laetitia (liste de
  ~15 plats à fournir) ; l'app ne propose pas de plats elle-même.
- **Genres** : plat, accompagnement (purée, pommes sautées), entrée (tzatziki, salade), dessert
  (brownie, tiramisu). Le carnet les range par genre ; le planning et le secours ne proposent
  que les plats.
- **Semaine** : 7 jours glissants à partir d'aujourd'hui. Sur chaque soir, choisir un plat du
  carnet (ou rien). Objectif d'usage : 3-4 soirs planifiés le dimanche en 2 minutes.
- **« Ajouter aux courses »** (bouton sur la semaine) : pour chaque plat planifié, chaque
  ingrédient qui n'est **ni** au placard en stock **ni** déjà dans la liste non prise est ajouté
  aux courses avec `source = 'plat:<id>'`. Idempotent : deux appuis ne créent pas de doublon.
  Comparaison de noms : minuscules, espaces et accents normalisés (« Crème fraîche » = « creme
  fraiche »).
- **Secours** (« Rien de prévu ce soir ») : les plats non archivés de ≤ 20 min dont tous les
  ingrédients sont au placard en stock **ou** dans des courses déjà prises dans les 7 derniers
  jours. Triés par minutes croissantes. Si aucun : on affiche les plats rapides avec, pour chacun,
  les 1-2 ingrédients manquants (« il manque : crème »).
- **Soir passé** : le lendemain, l'écran Aujourd'hui demande « Hier soir ? » avec 4 boutons :
  fait maison · commandé · dehors · autre. Une seule réponse, modifiable.

### Courses

- Liste partagée groupée par rayon (`RAYONS` : fruits-légumes, frais, épicerie, surgelés,
  boissons, hygiène-maison, autre). Rayon deviné à l'ajout depuis un petit dictionnaire de mots
  (`lait` → frais), modifiable d'un tap.
- Cocher = pris (barré, en bas du rayon). « Vider les pris » supprime les articles pris non
  récurrents ; les récurrents repassent dans « Habituels ».
- **Habituels** : les articles marqués récurrents, ajoutables en un tap.
- Cocher un article dont le nom est au placard le remet `en_stock = true`.
- Placard : liste des basiques ; « épuisé » d'un tap → `en_stock = false` + article ajouté aux
  courses.

### Colis

- Ajout manuel : quoi, transporteur, jour, créneau (texte libre « 14h-18h »), code, lieu
  (« casier Pickup rue Ordener », « gardien »), qui le récupère.
- Liste des colis non reçus triée par jour (sans jour en dernier). Bouton « Reçu ».
- Le code est affiché en grand et copiable d'un tap.
- Les colis reçus depuis plus de 14 jours ne sont plus affichés (pas supprimés).

### Aujourd'hui (accueil du hub)

Un seul écran, de haut en bas, chaque bloc masqué s'il est vide :

1. **Ce soir** : le plat prévu (avec ses minutes) ; sinon « Rien de prévu » + bouton Secours.
2. **Hier soir ?** : la question des 4 boutons, si le soir d'hier n'est pas renseigné.
3. **Colis** : ceux attendus aujourd'hui ou en retard, avec créneau et code.
4. **Courses** : nombre d'articles à prendre + lien.
5. **En Vadrouille** : le prochain voyage et son compte à rebours (réutilise
   `compte_a_rebours.py`), seulement s'il part dans moins de 60 jours.
6. **Le compteur** : commandes des 7 derniers jours et moyenne sur 6 semaines
   (« 1 commande cette semaine · moyenne 1,5 »). C'est le critère de succès, visible par les deux.

## Erreurs et cas limites

- Validation côté serveur pour toutes les écritures (textes bornés, minutes 1-600, issue dans la
  liste, ids `[A-Za-z0-9-]{8,64}` comme `souvenirs.py`) → `400` + message.
- Plat archivé encore planifié : reste affiché sur le soir concerné, mais n'apparaît plus dans le
  choix ni dans le secours.
- Hors ligne : même comportement que les rubriques existantes (le worker sert la dernière page ;
  les écritures échouent avec un message, pas de file d'attente en v1).
- Fuseau : `date.today()` du serveur (Europe/Paris à vérifier sur Render — sinon le « ce soir »
  bascule à 1h du matin ; à forcer via `TZ` si besoin).

## Tests (TDD, comme le reste du repo)

- `test_diners.py` : validation plat / soir (recette et lien bornés, lien http(s) seulement) ;
  recherche par nom et par ingrédient ; ajout aux courses idempotent et dédupliqué ;
  normalisation des noms ; secours (tous dispo, aucun dispo → manquants, archivés exclus) ;
  compteur hebdo et moyenne 6 semaines.
- `test_courses.py` : rayon deviné ; vider les pris garde les récurrents ; lien placard.
- `test_colis.py` : validation ; tri (sans jour en dernier) ; masquage > 14 jours.
- `test_aujourdhui.py` : chaque bloc présent / masqué selon les données ; ordre des blocs.
- `test_serveur.py` : nouvelles routes sous le préfixe secret ; `/?v=<code>` ouvre toujours un
  voyage ; `/vadrouille` liste les voyages.
- Tests existants : tous verts (460 au 2026-10-28).

## Découpage en livraisons (une PR chacune)

1. **Squelette du hub** : nav 5 entrées, `/` = Aujourd'hui (vide), En Vadrouille déplacée sous
   `/vadrouille`, compat `/?v=`. Rien de cassé côté voyage.
2. **Courses + placard** (utile seul dès le jour 1).
3. **Dîners** : carnet, semaine, ajout aux courses, secours, soirs + compteur.
4. **Colis**.
5. **Aujourd'hui complet** : assemble les blocs.

## Questions ouvertes

- **Nom du hub** : « En Vadrouille » reste le nom de la section voyage ; le hub (et l'icône PWA)
  a besoin du sien. À choisir avec Laetitia avant la livraison 1 (le manifeste PWA change).
- **Carnet de départ** (liste reçue le 2026-10-28, 19 entrées) : plats — matriciana, carbonara,
  blanquette de veau, baguezza, œuf cocotte, œuf à la coque, œufs brouillés, salad bar, lasagnes
  bolognaise, rôti de bœuf, purée jambon rapide, taco Monday, bacon cheese burger, pièce du
  boucher ; accompagnements — purée façon Robuchon, pommes de terre sautées ; entrée — tzatziki ;
  desserts — brownie, tiramisu. Injecté en base à la livraison 3 avec des ingrédients et des
  temps proposés par Claude, **à valider par Julien et Laetitia** avant injection.
- **Import depuis un lien (v2)** : la plupart des sites de recettes publient la recette en
  données structurées (schema.org `Recipe`) — on pourrait préremplir ingrédients et étapes à
  partir d'une URL collée. Instagram / TikTok ne le font pas : saisie manuelle. À décider une
  fois le carnet utilisé.
- **Placard de départ** : liste des basiques à fournir avec les plats.
