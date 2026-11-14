# Casa — Cucina : onglet Recettes, refonte Courses

Date : 14/11/2026, validé par Julien en session. Deux livraisons (§2 puis §3), une PR chacune, démo sur une
copie de prod (Mac + iPhone) avant chaque push.

## 1. Raviolis « Faisable tout de suite » après [Fini] : pas de bug, livraison abandonnée

Julien tape [Fini] sur les raviolis frais (Aujourd'hui > À finir), puis Dîners > Ce soir propose les plats raviolis
et tortellini en **Faisable tout de suite**. L'achat datait de plus de 3 jours : la piste des achats récents
(`serveur.articles_et_achats_recents`) est écartée. Cause retenue avec Julien le 14/11 : un tap dans Courses > Placard
sur l'article épuisé l'a remis **en stock** (le cycle de `basculerPlacard`, `courses.py:410`).
Pas de correctif à part : la refonte Courses (§3) supprime ce cycle (1 tap = « il en manque », jamais un retour en stock).

## 2. Cucina : le nouveau nom, et Recettes au même niveau

- **Popote devient Cucina** (Laetitia trouvait « Popote » cheap). Le libellé change dans la barre du hub et dans
  l'`aria-label` de la barre d'onglets. Les clés internes (`popote`, `POPOTE`, `onglets_popote`, `data-popote`)
  deviennent `cucina`. L'icône (couverts) et la couleur (`--diners`) ne changent pas.
- Barre d'onglets en haut des pages : **Dîners · Recettes · Courses · Cave**.
- **Option A, retenue** : une route `/recettes` sert la page de `diners.py` ouverte sur la vue Recettes.
  - Dans cette page, les onglets internes et l'accès à Ce soir et Semaine sont masqués.
  - `/diners` n'a plus que **Ce soir · Semaine** en onglets internes.
  - Un lien ancien `diners#recettes` (ou `#carnet`, `#a-tester`) redirige côté page vers `recettes`.
  - Le code n'est pas découpé. Si un sous-hub Cucina voit le jour, Recettes sortira alors dans son propre module.
- Dans la barre du hub, Cucina est active sur `diners`, `recettes`, `courses` et `cave`. Un appui ouvre toujours
  Dîners.
- Largeur : 4 onglets à 24 px en gras débordent sur iPhone. La taille passe à environ 19 px. Si ça ne suffit pas à
  390 px de large avec le bouton du thème, la barre défile horizontalement. À vérifier en démo sur l'iPhone.
- `VERSION_PAGE` +1.

## 3. Refonte Courses

### Problème

- On tape au fil de l'eau quand un article finit, mais on ne le retrouve pas dans le Placard (trop de puces, zones
  pas claires).
- La différence entre Placard, Habituels et liste n'est pas claire : il existe trois chemins pour dire « il en
  manque ».
- Les onglets par magasin (Supermarché / Italien / Asiatique) obligent à passer d'un onglet à l'autre.
- Le repli « Réassort placard » coupe la liste en deux sans bénéfice perçu.

### La liste (haut de page)

- Le champ « Ajouter » reste tel quel (plusieurs articles séparés par des virgules).
- **Une seule liste, rangée par rayon** dans l'ordre de `RAYONS`. Le rayon « Épiceries spécialisées » garde sa
  place dans cet ordre.
- Un article à acheter ailleurs porte une pastille **Italien** ou **Asie**, calculée par la règle actuelle
  (`magasin()` : rayon `specialise`, puis la liste `italien` du catalogue).
- Supprimés : `nav#magasins`, la clé `localStorage` `courses:magasin`, le repli « Réassort placard »,
  `estReassort`, le titre « Cette semaine ».
- Budget : un seul total, « ≈ X € à prendre » (+ panier, + sans prix). La ligne « total des courses » disparaît.
- Restent tels quels : « Dans le panier » (repli), « Courses finies · ranger N articles », l'édition d'un article.
  Dans l'édition, le bouton « Habituel / Plus habituel » devient **« Toujours en avoir » / « Plus besoin d'en
  avoir »**.

### « À la maison » (sous la liste, remplace Placard et Habituels)

- Contenu : les éléments du placard en stock, plus les habituels rangés (`recurrent` et pas `actif`). Un même nom
  normalisé n'apparaît qu'une fois.
- Ce qui est sur la liste à prendre n'apparaît pas dans « À la maison ».
- **Groupés par rayon** (`deviner_rayon` du nom, ou le rayon de l'habituel), dans l'ordre de `RAYONS`. C'est le même
  classement que la liste.
- Un champ **chercher** en tête filtre les puces au fil de la frappe : comparaison normalisée, début de n'importe
  quel mot. Les rayons vides sont masqués. Sans résultat : « Rien à la maison qui s'appelle ainsi. Ajoute-le à la
  liste. »
- **1 tap sur une puce = il en manque** :
  - un élément du placard passe en `en_stock = false` et part sur la liste (`ajouter(nom, 'placard')`, le chemin
    « épuisé » actuel) ;
  - un habituel passe en `actif = true`.
  - Dans les deux cas, la puce quitte « À la maison » et l'article apparaît dans son rayon sur la liste.
- Plus d'état « bientôt fini » à l'écran. Les lignes `bientot = true` restent en base et comptent comme en stock
  (c'est déjà le cas dans `disponibles`). Elles s'affichent comme les autres.
- Le retour se fait comme aujourd'hui : un article coché puis « Courses finies » revient en stock au placard, ou
  dans les habituels rangés.
- Le bouton **Modifier** remplace « Ranger le placard ». En mode Modifier, un tap ouvre l'édition de la puce :
  - un **habituel** : Changer de rayon (le rayon de la ligne `courses`), Retirer (supprime la ligne), Fermer ;
  - un élément du **placard** : Retirer (supprime la ligne `placard`), Fermer. Pas de changement de rayon : le
    placard ne stocke qu'une zone, son rayon est deviné du nom (`deviner_rayon`, ajouté par `GET /api/courses`).
    Changer le rayon demanderait une colonne, donc une migration : hors périmètre (14/11, en écrivant le plan).
- Le formulaire « ajouter au placard » disparaît. On fait entrer un article par la liste, avec « Toujours en
  avoir », et les ingrédients de recettes achetés entrent tout seuls (`db.enregistrer_article`, inchangé).
- Le résumé du repli : « À la maison · N articles ».

### Inchangé

- Aucune migration. Les tables `placard`, `courses` et `achats` ne changent pas. Seul ajout d'API : `GET /api/courses`
  rend chaque élément du placard avec son `rayon` deviné (lecture seule, pas stocké).
- Le stock lu par Dîners (Ce soir, Proposer ma semaine) et par Aujourd'hui (À finir, À acheter pour aujourd'hui) ne
  change pas.
- Le fonctionnement hors ligne (file d'envois, copie `localStorage`) et les prix ne changent pas.

### Tests

- `test_courses.py` / `test_courses_db.py` : plus d'onglets magasin ni de Réassort dans le HTML ; présence
  d'« À la maison », du champ chercher et du bouton Modifier ; pastilles calculées par la règle `magasin`.
- La logique JS pure (fusion placard + habituels, groupement par rayon, filtre de recherche) est extraite en
  fonctions testées sous node, comme les règles de page de Sortir (PR #80).
- `VERSION_PAGE` +1.

## Hors périmètre

- Le sous-hub Cucina (sa propre barre ou page d'accueil).
- Le découpage de `diners.py` en un module `recettes.py`.
- La zone congélateur et les portions datées (idée Congélateur, STATUS).
