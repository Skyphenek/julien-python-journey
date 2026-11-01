"""Les matchs de Légumes Démasqués (01/11/2026) : les plats « oui » de Julien ET de Laetitia, à tester.

Ce que le jeu a montré : pour Laetitia, c'est le légume qui décide, pas la cuisson. Non à brocoli,
chou-fleur, épinards, aubergine, betterave, céleri ; oui aux champignons, haricots verts, tomate. Les
légumes cachés ne passent pas (0 oui sur 3), les veloutés et le croustillant passent (3 sur 3).
Exception : le dal, où les épinards fondent dans les lentilles.
L'okonomiyaki et les frites de patate douce, aussi matchés, sont déjà dans l'app.
Rédigées par Claude d'après les versions de référence, à corriger par eux dans l'app.
Mêmes conventions que carnet_depart.py : noms d'ingrédients du placard, sel, poivre et huile sous-entendus.
Ajoutées une seule fois (table reprises), avec le retrait du brocoli air fryer (un « jamais » de Laetitia),
remplacé par les carottes rôties qu'elle a votées.
"""

NOM_REPRISE = "legumes-demasques"
RETIRES = ["af-brocoli"]


def _lg(id_, nom, genre, minutes, ingredients, recette, note=""):
    return {"id": "lg-" + id_, "nom": nom, "genre": genre, "minutes": minutes, "ingredients": ingredients,
            "recette": recette, "lien": "", "note": note}


LEGUMES = [
    _lg("veloute-poireau", "Velouté poireaux-pommes de terre", "plat", 35,
        ["poireaux", "pommes de terre", "oignons", "beurre", "bouillon", "crème fraîche", "demi-baguettes", "comté"],
        """Pour 2, plus 2 parts à congeler
- 3 poireaux (le blanc et le vert tendre), 3 pommes de terre moyennes, 1 oignon
- 30 g de beurre, 1 L de bouillon de volaille, 2 c. à s. de crème fraîche
- tartines : 1 demi-baguette, 60 g de comté râpé

1. Fendre les poireaux, les rincer sous l'eau (la terre se cache entre les feuilles), les émincer. Émincer l'oignon.
2. Les faire fondre 10 min au beurre à feu doux, avec une pincée de sel, sans colorer.
3. Pommes de terre en dés, bouillon : 20 min à frémissement.
4. Mixer très lisse, ajouter la crème, rectifier sel et poivre.
5. Tartines de comté 5 min sous le gril du four (ou 4 min en AIR FRY à 190 °C), à tremper dans la soupe.""",
        "Se congèle très bien, sans la crème : l'ajouter au réchauffage."),

    _lg("veloute-carotte", "Velouté carotte-coco-gingembre", "plat", 30,
        ["carottes", "oignons", "gingembre", "pâte de curry", "lait de coco", "bouillon", "citrons verts", "coriandre"],
        """Pour 2, plus 2 parts à congeler
- 800 g de carottes, 1 oignon, 3 cm de gingembre frais
- 1 c. à c. de pâte de curry rouge (ou 1 c. à c. de curry en poudre)
- 40 cl de lait de coco, 60 cl de bouillon de légumes
- 1 citron vert, quelques feuilles de coriandre

1. Faire revenir l'oignon émincé 5 min dans un filet d'huile. Ajouter gingembre râpé et pâte de curry, 1 min.
2. Carottes en rondelles, bouillon : 20 min à frémissement, jusqu'à ce qu'elles s'écrasent.
3. Ajouter le lait de coco (en garder 2 c. à s.), mixer très lisse.
4. Jus de citron vert, sel. Servir avec un trait de lait de coco et la coriandre.""",
        "Doux et parfumé : le gingembre et le coco font oublier la carotte bouillie."),

    _lg("quiche-poireaux", "Quiche poireaux-lardons", "plat", 60,
        ["pâte brisée", "poireaux", "lardons", "beurre", "œufs", "crème fraîche", "lait", "comté", "noix de muscade"],
        """Pour 4 (deux dîners, ou un dîner et deux déjeuners)
- 1 pâte brisée
- 3 poireaux, 200 g de lardons, 20 g de beurre
- 3 œufs, 20 cl de crème fraîche, 10 cl de lait, 80 g de comté râpé, muscade

1. Four à 200 °C. Foncer le moule avec la pâte, piquer le fond, 10 min à blanc (la pâte ne sera pas détrempée).
2. Poireaux émincés fondus 15 min au beurre à feu doux, couvercle. Lardons dorés à sec, égouttés.
3. Battre œufs, crème, lait, muscade, poivre (peu de sel : les lardons le sont).
4. Poireaux et lardons sur la pâte, comté, puis l'appareil.
5. 30 min à 180 °C : la quiche est dorée et ne tremble plus au centre. Avec une salade.""",
        "Se réchauffe 5 min en AIR FRY à 160 °C : la pâte redevient croustillante."),

    _lg("baguezza-champi", "Baguezza champignons-jambon", "plat", 20,
        ["demi-baguettes", "champignons de Paris", "ail", "crème fraîche", "jambon", "mozzarella râpée", "persil"],
        """Pour 2
- 2 demi-baguettes, ouvertes dans la longueur
- 250 g de champignons de Paris émincés, 1 gousse d'ail
- 3 c. à s. de crème fraîche, 2 tranches de jambon, 125 g de mozzarella râpée, persil

1. Champignons à la poêle très chaude avec un filet d'huile, sans remuer les 3 premières minutes : ils doivent dorer, pas rendre leur eau. Ail haché à la fin, sel.
2. Hors du feu, la crème : une poêlée crémeuse, pas liquide.
3. Tartiner les baguettes de champignons, jambon déchiré, mozzarella.
4. 8 à 10 min à 220 °C au four, ou 6 à 7 min en AIR FRY à 190 °C. Persil à la sortie.""",
        "La cousine de la baguezza du carnet, côté champignons, le légume préféré de Laetitia."),

    _lg("risotto-champi", "Risotto aux champignons", "plat", 35,
        ["riz carnaroli", "champignons de Paris", "échalotes", "ail", "vin blanc", "bouillon", "beurre", "parmesan",
         "persil"],
        """Pour 2
- 160 g de riz carnaroli
- 300 g de champignons (Paris, ou un mélange avec des pleurotes), 1 gousse d'ail
- 1 échalote, 10 cl de vin blanc sec, 80 cl de bouillon de volaille chaud
- 30 g de beurre froid, 40 g de parmesan râpé, persil

1. Champignons poêlés à feu vif avec l'ail, bien dorés. Réserver.
2. Échalote ciselée fondue dans un filet d'huile, puis le riz : 2 min en remuant, il devient nacré.
3. Vin blanc, laisser évaporer. Puis le bouillon louche par louche, en remuant souvent : 16 à 18 min.
4. Ajouter les champignons pour les 2 dernières minutes.
5. Hors du feu : beurre froid et parmesan, remuer vivement 1 min (la mantecatura, c'est elle qui rend crémeux). Couvrir 1 min, persil.""",
        "Mêmes gestes que le risotto alla milanese du carnet."),

    _lg("wok-teriyaki", "Wok de poulet teriyaki", "plat", 25,
        ["filets de poulet", "poivrons rouges", "carottes", "haricots verts", "nouilles", "sauce soja", "mirin", "miel",
         "gingembre", "ail", "fécule de maïs", "sésame"],
        """Pour 2
- 300 g de filets de poulet en lanières
- 1 poivron rouge, 1 carotte, 150 g de haricots verts
- 200 g de nouilles (udon ou nouilles aux œufs)
- sauce teriyaki : 4 c. à s. de sauce soja, 2 c. à s. de mirin, 1 c. à s. de miel, 1 c. à c. de gingembre râpé, 1 gousse d'ail, 1 c. à c. de fécule de maïs délayée dans 3 c. à s. d'eau
- graines de sésame

1. Cuire les nouilles, égoutter, un filet d'huile pour qu'elles ne collent pas.
2. Haricots verts 4 min dans l'eau bouillante salée : ils restent croquants.
3. Wok fumant, huile neutre : le poulet 4 min, réserver. Puis carotte en bâtonnets et poivron en lanières, 3 min à feu vif, les haricots 1 min.
4. Remettre le poulet, verser la sauce : 1 min, elle épaissit et laque.
5. Ajouter les nouilles, mélanger, sésame.""",
        "Les légumes restent croquants et brillants : c'est la cuisson qui les rend acceptables."),

    _lg("haricots-lardons", "Haricots verts ail et lardons", "accompagnement", 20,
        ["haricots verts", "lardons", "ail", "échalotes", "beurre", "persil"],
        """Pour 2
- 300 g de haricots verts frais (ou extra-fins surgelés)
- 100 g de lardons, 1 échalote, 1 gousse d'ail, 1 noix de beurre, persil

1. Équeuter les haricots. 6 min dans une grande eau bouillante bien salée, puis dans l'eau glacée : ils gardent leur vert et leur croquant.
2. Lardons dorés à sec dans une poêle. Ajouter l'échalote ciselée, 2 min.
3. Haricots égouttés, beurre, ail haché : 3 min à feu vif en remuant.
4. Persil, poivre. À côté d'un steak, d'une côte de porc ou d'un poulet rôti.""",
        "Un des deux légumes que Laetitia aime sans condition."),

    _lg("petits-pois-francaise", "Petits pois à la française", "accompagnement", 25,
        ["petits pois surgelés", "lardons", "oignons nouveaux", "salade", "beurre", "bouillon", "sucre"],
        """Pour 2
- 400 g de petits pois surgelés (extra-fins)
- 80 g de lardons, 4 oignons nouveaux (ou 1 oignon blanc)
- 1 cœur de sucrine émincé, 30 g de beurre, 10 cl de bouillon, 1 pincée de sucre

1. Lardons et oignons nouveaux en tronçons fondus au beurre 5 min, sans colorer.
2. Petits pois encore surgelés, bouillon, sucre, sel : couvercle, 10 min à feu doux.
3. Ajouter la sucrine, encore 3 min : elle fond juste.
4. Une noix de beurre pour finir. Avec un poulet rôti ou un rôti de porc.""",
        "Le sucre et les lardons rendent le petit pois doux et fondant."),

    _lg("tempura", "Tempura de légumes", "accompagnement", 30,
        ["courgettes", "champignons de Paris", "patates douces", "haricots verts", "farine", "fécule de maïs",
         "eau gazeuse", "sauce soja", "citrons"],
        """Pour 2
- 1 courgette en bâtonnets, 8 champignons de Paris coupés en deux, 1 petite patate douce en rondelles fines, une poignée de haricots verts
- pâte : 100 g de farine, 50 g de fécule de maïs, 20 cl d'eau gazeuse glacée, 1 jaune d'œuf (facultatif)
- huile de friture
- sauce : 3 c. à s. de sauce soja, 1 c. à s. de jus de citron, 1 c. à s. d'eau

1. Huile à 175 °C dans une sauteuse (une goutte de pâte remonte aussitôt en grésillant).
2. Pâte au dernier moment, à peine mélangée avec des baguettes : il doit rester des grumeaux. L'eau doit être glacée, c'est ce qui rend la pâte légère.
3. Légumes bien secs, passés dans un peu de farine, puis dans la pâte. Frire par petites quantités 2 à 3 min.
4. Égoutter sur une grille, sel. Servir tout de suite avec la sauce.""",
        "Sans brocoli : c'est un « jamais » de Laetitia, la courgette et la patate douce le remplacent."),

    _lg("tomates-mozza", "Tomates-mozzarella", "entree", 10,
        ["tomates", "mozzarella", "basilic", "huile d'olive de finition", "fleur de sel"],
        """Pour 2
- 3 belles tomates de saison (cœur de bœuf, ou un mélange de couleurs ; l'hiver, des tomates cerises en grappe)
- 1 boule de mozzarella di bufala, sortie du frigo 30 min avant
- basilic frais, huile d'olive de finition, fleur de sel, poivre

1. Tomates en tranches épaisses, fleur de sel dessus 5 min avant : elles rendent leur goût.
2. Mozzarella déchirée à la main plutôt que tranchée.
3. Basilic, un vrai filet d'huile d'olive, poivre au moulin.""",
        "Hors saison, préférer les tomates cerises : une tomate fade gâche le plat."),

    _lg("dal-epinards", "Dal de lentilles corail aux épinards", "plat", 30,
        ["lentilles corail", "oignons", "ail", "gingembre", "cumin", "curcuma", "garam masala", "tomates pelées",
         "lait de coco", "épinards surgelés", "riz basmati", "citrons"],
        """Pour 2, plus 2 parts à congeler
- 250 g de lentilles corail, rincées
- 1 oignon, 2 gousses d'ail, 2 cm de gingembre
- 1 c. à c. de cumin, 1 c. à c. de curcuma, 1 c. à c. de garam masala
- 200 g de tomates pelées, 20 cl de lait de coco, 70 cl d'eau
- 150 g d'épinards surgelés en galets, riz basmati, 1/2 citron

1. Oignon fondu dans un filet d'huile, puis ail, gingembre et épices : 1 min, ça doit sentir fort.
2. Lentilles, tomates écrasées, lait de coco, eau, sel : 20 min à frémissement en remuant de temps en temps. Elles se défont, c'est le but.
3. Épinards encore surgelés pour les 5 dernières minutes : ils fondent dans le dal.
4. Jus de citron, rectifier le sel. Avec le riz basmati.""",
        "Le seul plat aux épinards que Laetitia a voté oui : ils disparaissent dans les lentilles."),
]
