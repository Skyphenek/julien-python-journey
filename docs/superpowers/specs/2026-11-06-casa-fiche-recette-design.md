# Casa — fiche recette lisible (design)

Date : 06/11/2026 · Statut : validé par Julien (style C « Magazine », choisi à l'unanimité avec Laetitia)

## Problème

La fiche d'un plat (Dîners, `ouvrirFiche` dans `voyage/diners.py`) affiche la recette en un seul bloc
`pre.recette` : texte brut, sans hiérarchie. Sur iPhone comme sur le web, c'est « pas très lisible, ni sympa à
lire ». Depuis le skill chef-casa, les recettes sont longues (tempo, étapes détaillées, secrets, bloc final) :
le mur de texte empire.

Démos comparées le 06/11/2026 (A fiche claire, B mode cuisine, C magazine, texte brut) sur carbonara, polpette,
hot dog : C retenue, avec trois emprunts (cocher les ingrédients, tempo qui renvoie aux étapes, mode cuisine).

## Livraisons

1. **Livraison 1 (cette spec)** : fiche C, pastilles repliées sous la une, ingrédients à cocher, tempo → étape.
2. **Livraison 2 (spec à part, plus tard)** : bouton « Mode cuisine » (pas-à-pas gros texte), réutilise la même
   structure.

## Approche retenue : découpage serveur, en Python

Le texte reste la source unique en base (`plats.recette`), édité par `chef.py` et par « Modifier ». Un module pur
le découpe en structure à chaque lecture ; la page ne fait qu'afficher. Écartés : découpage en JavaScript (non
testé, alors que c'est la partie fragile) ; structure stockée en base (migration, `chef.py` à réécrire, « Modifier »
désynchronisé).

## 1. `voyage/fiche_recette.py`

`decouper(texte: str) -> dict`, fonction pure, sans accès base.

```python
{
  "structuree": bool,          # vrai si au moins une étape numérotée
  "pour": str,                 # « Pour 2 », « Pour 4 (deux repas à deux) », « Pour 20 nems » ; "" si absent
  "ingredients": [{"nom": str, "quantite": str}],   # lignes « - » avant toute section
  "sections": [{"titre": str, "lignes": [str]}],    # « Variantes (acceptables) », « Sauce », « Erreurs fréquentes »…
  "tempo": {"titre": str, "lignes": [{"heure": "0:07", "texte": str, "etapes": [int]}]} | None,
  "etapes": [{
      "n": int,
      "action": str,           # début de l'étape jusqu'au 1er « . », « : » ou « — » (exclu pour « — »)
      "morceaux": [{"genre": "texte" | "pourquoi", "texte": str}],   # le reste ; « — … » jusqu'au « . » ou « ; »
      "secrets": [{"qui": "grand-mere" | "mamma", "texte": str}],    # « (secret de … : …) » retirés du texte
      "si": [ <même forme : action, morceaux, secrets> ]              # sous-puces indentées « - »
  }],
  "difference": [str],         # lignes du bloc « Ce qui fait la différence »
}
```

Règles de lecture (ligne par ligne, lignes vides ignorées) :

- 1re ligne commençant par « Pour » → `pour`.
- `^Tempo` → ouvre le tempo (titre = la ligne) ; lignes `- H:MM  texte` ; `etapes` = nombres entre parenthèses.
- `^Ce qui fait la différence` → ouvre le bloc final ; lignes `- …`.
- `^\d+[.)]\s` → nouvelle étape (formats « 1. » et « 1) »).
- Ligne indentée `- …` après une étape → sous-puce `si` de cette étape.
- Ligne `- …` hors étape → ingrédient (ou ligne de la section en cours).
- Toute autre ligne hors étape → titre de section (« : » final retiré) ; une ligne de texte libre après les étapes
  (« Secret de mamma : … » du risotto) → section sans liste, `titre` = la ligne entière, `lignes` = [].
- Ingrédient : coupé au premier « : » ou « — » entouré d'espaces → `nom` / `quantite` ; sinon `quantite` = "".
- Secrets : `(secret de grand-mère : …)` et `(secret de mamma : …)` (casse insensible) ; une seule paire de
  parenthèses imbriquées tolérée dans le texte du secret.
- Ne lève jamais d'exception : en cas d'erreur, renvoie `{"structuree": False, …}` avec les champs vides.

## 2. Serveur

`/api/diners` : chaque plat reçoit `"fiche": decouper(p["recette"])` à côté de `recette` et `cout`. Le texte
brut reste envoyé (édition). Coût : ~130 découpages de textes courts par chargement, négligeable.

## 3. Page — fiche C (`ouvrirFiche`, `voyage/diners.py`)

Si `p.fiche.structuree` est faux : affichage actuel inchangé (`pre.recette`). Sinon, dans l'ordre :

1. **Une** (fond `--diners`, texte blanc, coins 28 px) : ligne meta (genre · durée · `pour`), nom en 38 px, puis
   les lignes `difference` entre guillemets sous un filet. Bouton « Fermer » conservé en haut.
2. **Bandeau courses replié** sous la une : `<details>` dont le résumé dit « N à acheter · ≈ X € » (ou « Tout est
   au placard ») ; ouvert, il montre les pastilles actuelles (Au placard / Déjà sur la liste / À acheter, prix).
   Le coût du repas (ligne `≈ … le repas pour deux`) passe dans ce bandeau.
3. **Ingrédients** sur deux colonnes : case à cocher + nom en gras + quantité dessous. État des cases en mémoire
   tant que la fiche est ouverte (remis à zéro à la fermeture). Ingrédient coché : barré, grisé.
4. **Sections** (variantes, sous-listes « Sauce »…) : titre en petites capitales, lignes sur deux colonnes ;
   section sans lignes = paragraphe.
5. **Tempo** : titre, puis cartes qui défilent horizontalement (scroll-snap), heure en DM Mono 22 px cuivre.
   Toucher une carte qui renvoie à une étape : défilement doux jusqu'à la 1re étape citée, surlignée 2 s.
6. **Étapes** : gros numéro cuivre (44 px) à gauche ; action en gras ; morceaux « pourquoi » en italique gris ;
   secrets en encadré (bordure gauche dorée « Secret de grand-mère », verte « Secret de mamma ») ; `si` en
   sous-liste.
7. Inchangés ensuite : lien « Recette d'origine », note, « Va bien avec », actions, édition.

Construction exclusivement via `el()` / `textContent` (le texte peut venir de « Modifier ») : aucun `innerHTML`
avec du contenu de recette. Mode sombre : variables existantes de `design.py`. `VERSION_PAGE` 45 → 46.

## 4. Tests et validation

TDD, `voyage/test_fiche_recette.py`, sur textes réels figés dans le fichier de test :

- carbonara (tempo, renvois, secret de grand-mère, sous-puces « Encore liquide… », bloc final) ;
- risotto milanese (étapes « 1) », secret de mamma en paragraphe libre, ingrédient « dont 30 g froid ») ;
- polpette (sous-liste « Sauce » avec ingrédients `—`, 9 étapes, tempo « ≈ 1 h 10 ») ;
- hot dog (pas de tempo, secret de grand-mère au milieu d'une phrase) ;
- nems (ancien format, « Pour 20 nems », pas de bloc final) ;
- une recette à l'ancien bloc « Erreurs fréquentes » (devient une section) ;
- texte vide, texte libre sans étape → `structuree` faux, sans exception.

`test_serveur.py` : `/api/diners` renvoie `fiche` pour chaque plat. Le rendu JS n'a pas de test automatique :
démo locale sur une copie des données de prod, Mac + iPhone en wifi, testée par Julien avant toute PR.

## Hors périmètre

Mode cuisine (livraison 2) ; changement du format des recettes ; correction du coût faussé par « Pour 20 nems »
(signalé, traité avec la recette nems) ; fusion des pastilles avec la liste d'ingrédients du texte.
