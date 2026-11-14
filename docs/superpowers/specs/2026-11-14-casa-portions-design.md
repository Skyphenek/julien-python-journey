# Casa — ajuster les quantités au nombre de parts (design)

Date : 14/11/2026. Demande de Laetitia : « un dîner pour 6 », ou « un repas à 4 en gardant 2 parts pour nous ».

## But

Sur la fiche recette, choisir combien on est à table et combien de parts on garde ; les quantités de la
recette se recalculent sur-le-champ. Rien n'est enregistré.

## Hors périmètre

- Mémoriser des couverts sur un repas planifié (Semaine).
- Des quantités dans la liste de courses (elle ne porte que des noms).
- Réécrire le texte des recettes en base.

## Ce que voit Laetitia

Au-dessus des ingrédients (sous l'en-tête « Pour N » et le bandeau des courses) :

```
À table  [–] 4 [+]    À garder  [–] 2 [+]    = 6 parts (recette écrite pour 2)
```

- Valeurs de départ, tirées de la ligne « Pour » :
  - « Pour N » → à table N, à garder 0 ;
  - « Pour 4 (deux repas à deux) », « Pour 4 (deux dîners) » → à table 2, à garder 2 ;
  - « Pour 2, plus 2 parts à congeler » → à table 2, à garder 2.
- Bornes : à table de 1 à 12, à garder de 0 à 12 ; total d'au moins 1.
- Dès que le total diffère de la base, un bandeau au-dessus des étapes :
  « Quantités ajustées pour 6 parts — temps de cuisson inchangés ; prends une plus grande cocotte, saisis en
  plus de fournées. » Revenu à la base : bandeau masqué, texte d'origine.
- Rouvrir la fiche repart de la base (pas de mémoire, pas de localStorage).

## Ce qui est multiplié

Facteur = total des parts ÷ base.

- **Liste d'ingrédients** : le premier nombre de la quantité (après « : » ou « — » s'il y en a un, sinon de la
  ligne), quelle que soit son unité sauf min, h, °, % : « 320 g de penne », « Spaghetti : 320 g », « Oignon — 1,
  râpé », « 1,2 kg de veau », « 1/2 citron », « 1 1/2 c. à s. de farine », « 12 petits oignons », « 3 cm de
  gingembre ». Les plages « 2–3 c. à s. » : les deux bornes. Les autres nombres de la ligne : seulement suivis de
  g, kg, ml, cl, l (« dont 30 g froid »).
- **Sections** (« Sauce », « Gremolata », « Pour la cuisson »…) : comme les ingrédients. Sections dont le titre
  commence par « Variante », « Erreurs » ou « Avec » : seulement les poids et volumes.
- **Étapes et Tempo** : seulement les poids et volumes, un nombre suivi de g, kg, ml, cl, l
  (« 80 cl de bouillon », « les 40 g de beurre »).

## Ce qui ne bouge jamais

- Minutes, heures, °C, %, numéros d'étape, heures du Tempo (0:12), renvois (4) ; cm et mm hors première
  quantité d'un ingrédient (« en cubes de 5 cm »).
- Lignes sans chiffre (sel, poivre, persil, « selon le goût »).
- Dans les étapes, le Tempo et les sections Variante/Erreurs/Avec, les nombres sans unité de poids ou de volume
  (« 2 œufs », « 3 fournées », « 2 min »).
- Limite connue : une seconde quantité sans unité métrique sur une ligne d'ingrédient ne bouge pas
  (« 4 c. à s. d'huile (dont 1 crue) », « Beurre : 40 g, plus 2 noix »).

## Recettes sans compteurs

Pas de compteurs quand la base n'est pas un nombre unique de parts : « Pour 2 à 4 », « Pour 1 ou 2 »,
« Pour 1 gros appétit ou 2 », « Pour 4 en apéro », « Pour 8 tranches », recette sans ligne « Pour » — environ
une dizaine en prod au 14/11/2026. La fiche s'affiche comme aujourd'hui.

## Arrondis (à l'affichage)

- g et ml : à 5 près sous 100, à 10 près au-dessus ; kg et l : à 0,1 près (virgule française).
- cl : à l'unité.
- Pièces et cuillères (nombre sans unité métrique) : à la demie près, écrit « 1 1/2 », « 1/2 », « 3 ».
- Jamais 0 : un résultat qui s'arrondit à 0 affiche la plus petite valeur de l'arrondi (5 g, 1/2).

## Construction

### Python — `voyage/portions.py` + `voyage/fiche_recette.py` (testés)

- `portions.py` : `base_parts(pour)` et `segmenter(texte, premier)` — les règles de détection (unités,
  formats, exclusions) ; et `SCRIPT_PORTIONS`, le JavaScript pur d'arrondi et de réécriture, testé sous node.
- `decouper(texte)` ajoute :
  - `fiche["base"]` : `{"table": int, "garder": int}` ou `None` (pas de compteurs) ;
  - des listes de segments `{"t": "texte"}` ou `{"t": "320", "q": 320.0, "u": "g"}` (+ `q2`, `sep` pour une
    plage) : `nom_s` et `quantite_s` par ingrédient, `lignes_s` par section, `s` par ligne de Tempo,
    `action_s` par étape et sous-puce, `s` par morceau et par secret. Concaténer les `t` redonne exactement le
    texte d'origine.
- Tests (`test_fiche_recette.py`) : chaque format ci-dessus, chaque exclusion, la base de chaque libellé
  « Pour » présent en prod, et un test de non-régression qui passe toutes les recettes de la copie de prod :
  la concaténation des segments égale le texte d'origine.

### JavaScript — fiche dans `voyage/diners.py`

- Les deux compteurs, le total, le bandeau.
- `texteAjuste(segments, facteur)` (de `SCRIPT_PORTIONS`) multiplie les `q`, arrondit selon `u`, et
  reconstruit le texte ; facteur 1 → les `t` d'origine, à l'identique.
- Les cases à cocher des ingrédients gardent leur état quand on change les compteurs.

### Données et livraison

- Aucune migration, aucun changement d'API hors du champ `fiche` déjà envoyé.
- VERSION_PAGE +1 (`voyage/valise.py`).
- Démo sur la copie de prod (Mac + iPhone en wifi) avant push et PR.

## Critère de succès

Laetitia ouvre la blanquette, règle 4 à table et 2 à garder, et peut faire ses courses et cuisiner avec les
quantités affichées sans calcul de tête.
