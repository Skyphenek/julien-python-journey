"""Accompagnements, brunchs et accords de départ (02/11/2026) : la spec repas composés, étape 2.

- 15 accompagnements pour nous deux : féculents, et des légumes que Laetitia accepte (champignons, haricots verts,
  tomate sans condition ; croustillant, cru, rôti). Aucun de ses « jamais ».
- 6 brunchs (ids « brunch- » : l'étiquette Brunch de la page Dîners). Jamais proposés pour un dîner.
- ACCORDS : 2 à 4 accompagnements par plat principal « nu » (viande, poisson, tarte, croque) ; rien pour les plats
  complets (pâtes, risottos, currys avec leur riz). Un plat qui a déjà son féculent reçoit des légumes.
Rédigées par Claude d'après les versions de référence, à corriger dans l'app.
Mêmes conventions que carnet_depart.py : noms d'ingrédients du catalogue, sel, poivre et huile sous-entendus.
Ajoutées une seule fois (table reprises), statut à tester ; accords posés une seule fois, sur les plats sans accords.
"""

NOM_REPRISE = "accompagnements-brunch-v1"
NOM_REPRISE_ACCORDS = "accords-v1"

# Ses « jamais » côté légumes (jeu Légumes Démasqués, 01/11/2026), comparés normalisés (sans accents)
JAMAIS_LEGUMES_LAETITIA = ("brocoli", "chou-fleur", "epinard", "aubergine", "betterave", "celeri")


def _acc(id_, nom, minutes, ingredients, recette, note=""):
    return {"id": "acc-" + id_, "nom": nom, "genre": "accompagnement", "minutes": minutes,
            "ingredients": ingredients, "recette": recette, "lien": "", "note": note}


def _brunch(id_, nom, genre, minutes, ingredients, recette, note=""):
    return {"id": "brunch-" + id_, "nom": nom, "genre": genre, "minutes": minutes, "ingredients": ingredients,
            "recette": recette, "lien": "", "note": note}


ACCOMPAGNEMENTS = [
    _acc("riz-pilaf", "Riz pilaf", 25, ["riz", "oignons", "beurre", "bouillon"],
         """Pour 2
- 150 g de riz long (basmati ou thaï), 1/2 oignon, 1 noix de beurre
- 25 cl de bouillon chaud (une fois et demie le volume du riz)

1. Oignon ciselé fondu 3 min dans le beurre, sans coloration.
2. Riz versé à sec, remué 2 min : les grains deviennent nacrés.
3. Bouillon chaud, couvercle, feu doux 15 min sans soulever.
4. Hors du feu 5 min à couvert, puis égrainer à la fourchette.""",
         "Avec des gambas, un saumon, un chili ou un poisson."),

    _acc("semoule", "Semoule au beurre", 10, ["couscous", "beurre", "bouillon"],
         """Pour 2
- 150 g de semoule moyenne, 15 cl de bouillon, 1 noix de beurre

1. Semoule dans un saladier, bouillon bouillant juste à hauteur, couvrir d'une assiette.
2. 5 min de repos, puis le beurre, et égrainer à la fourchette.
3. Poivre, un filet d'huile d'olive.""",
         "Avec des cuisses de poulet au paprika ou un poulet rôti."),

    _acc("pommes-grenaille", "Pommes grenaille ail-romarin (air fryer)", 30,
         ["pommes de terre grenaille", "ail", "romarin"],
         """Pour 2
- 500 g de pommes de terre grenaille, 3 gousses d'ail en chemise, 2 brins de romarin (ou 1 c. à c. séché)
- 1 c. à s. d'huile

1. Grenailles lavées, coupées en deux, séchées dans un torchon.
2. Huile, sel, romarin, ail en chemise : bien mélanger dans un saladier.
3. Air fryer 200 °C, 20 à 22 min, en secouant le panier à mi-cuisson.
4. Prêtes quand la pointe d'un couteau entre sans résister.""",
         "Croustillant : le registre où Laetitia dit oui."),

    _acc("ecrasee", "Écrasé de pommes de terre à l'huile d'olive", 25, ["pommes de terre", "ciboulette"],
         """Pour 2
- 500 g de pommes de terre à chair ferme, 3 c. à s. d'huile d'olive, ciboulette, fleur de sel

1. Pommes de terre épluchées, en gros morceaux, dans l'eau froide salée ; 18 min après l'ébullition.
2. Égoutter, écraser grossièrement à la fourchette : des morceaux doivent rester.
3. Huile d'olive, ciboulette ciselée, fleur de sel, poivre.""",
         "Pas une purée lisse : des morceaux, rien de mixé."),

    _acc("coquillettes", "Coquillettes au beurre et parmesan", 12, ["coquillettes", "beurre", "parmesan"],
         """Pour 2
- 160 g de coquillettes, 1 belle noix de beurre, 30 g de parmesan râpé

1. Coquillettes dans une grande eau bouillante salée, 1 min de moins que le temps du paquet.
2. Garder une louche d'eau de cuisson, égoutter.
3. Hors du feu, dans la casserole : beurre, parmesan, un peu d'eau de cuisson ; remuer jusqu'à ce que ce soit nappé.""",
         "Avec un bœuf bourguignon ou un osso buco : la sauce a besoin de pâtes."),

    _acc("polenta", "Polenta crémeuse au parmesan", 15, ["polenta", "lait", "beurre", "parmesan"],
         """Pour 2
- 100 g de polenta précuite, 25 cl de lait et 25 cl d'eau, 1 noix de beurre, 30 g de parmesan

1. Lait, eau et une pincée de sel à ébullition.
2. Polenta en pluie en fouettant, puis 5 min à feu doux en remuant à la cuillère en bois.
3. Hors du feu : beurre et parmesan. Elle doit couler comme une purée épaisse ; trop ferme, un trait de lait.""",
         "Avec un saltimbocca, un osso buco ou des polpette."),

    _acc("champignons-persillade", "Champignons poêlés en persillade", 15,
         ["champignons de Paris", "ail", "persil", "beurre"],
         """Pour 2
- 300 g de champignons de Paris, 1 gousse d'ail, persil, 1 noix de beurre

1. Champignons essuyés (pas lavés), en quartiers.
2. Poêle très chaude avec un filet d'huile, champignons en une couche : 3 min sans remuer, ils dorent au lieu de rendre leur eau.
3. Beurre, ail et persil hachés, 1 min. Sel à la fin.""",
         "Champignons : un des légumes que Laetitia aime sans condition."),

    _acc("haricots-amandes", "Haricots verts aux amandes", 15, ["haricots verts", "amandes effilées", "beurre"],
         """Pour 2
- 300 g de haricots verts (frais, ou extra-fins surgelés), 20 g d'amandes effilées, 1 noix de beurre

1. Haricots 6 min dans une grande eau bouillante salée, puis dans l'eau glacée : ils restent verts et croquants.
2. Amandes dorées à sec dans la poêle, 2 min, en surveillant.
3. Beurre, haricots égouttés, 3 min à feu vif. Sel, poivre.""",
         "Haricots verts : l'autre légume que Laetitia aime sans condition."),

    _acc("tomates-provencale", "Tomates à la provençale", 30, ["tomates", "ail", "persil", "chapelure"],
         """Pour 2
- 4 tomates, 1 gousse d'ail, persil, 2 c. à s. de chapelure, huile d'olive

1. Four à 200 °C (ou air fryer 180 °C). Tomates coupées en deux, côté coupé vers le haut, salées.
2. Ail et persil hachés, mélangés à la chapelure et un filet d'huile : en dôme sur chaque moitié.
3. 25 min au four (15 min en air fryer) : le dessus gratine, la tomate confit.""",
         "Tomate : un oui de Laetitia."),

    _acc("salade-verte", "Salade verte, vinaigrette moutarde", 5, ["salade", "moutarde", "vinaigre", "échalotes"],
         """Pour 2
- 1 laitue ou 1/2 batavia, 1 c. à c. de moutarde, 1 c. à s. de vinaigre, 3 c. à s. d'huile, 1/2 échalote

1. Salade lavée et bien essorée : une salade mouillée noie la vinaigrette.
2. Dans le saladier : moutarde, vinaigre, sel, puis l'huile en fouettant, l'échalote ciselée.
3. Mélanger au moment de servir, pas avant.""",
         "Cru : Laetitia dit oui 4 fois sur 5."),

    _acc("frites-courgette", "Frites de courgette au parmesan (air fryer)", 20,
         ["courgettes", "farine", "œufs", "chapelure", "parmesan"],
         """Pour 2
- 2 courgettes, 2 c. à s. de farine, 1 œuf, 50 g de chapelure (panko si possible), 30 g de parmesan râpé

1. Courgettes en bâtonnets de 1 cm, épongées dans un torchon.
2. Farine, œuf battu, puis chapelure mélangée au parmesan.
3. Un peu d'huile en spray, air fryer 200 °C, 10 à 12 min en une couche, retournées à mi-cuisson.""",
         "Croustillant : 3 oui sur 3 chez Laetitia, même quand le légume est un « ça dépend »."),

    _acc("rostis", "Röstis de pommes de terre", 25, ["pommes de terre", "oignons", "œufs"],
         """Pour 2
- 400 g de pommes de terre, 1/2 oignon, 1 œuf

1. Pommes de terre et oignon râpés gros, pressés fort dans un torchon pour sortir l'eau.
2. Œuf, sel, poivre, mélanger.
3. Poêle chaude bien huilée : 4 petits tas aplatis, 5 min par face à feu moyen, jusqu'à ce qu'ils soient dorés.
4. Égoutter sur du papier absorbant.""",
         "Avec un steak, des ailes de poulet, ou des œufs au brunch."),

    _acc("pommes-four", "Pommes de terre au four, crème ciboulette (air fryer)", 45,
         ["pommes de terre", "crème fraîche", "ciboulette"],
         """Pour 2
- 2 grosses pommes de terre (type bintje), 4 c. à s. de crème fraîche, ciboulette

1. Pommes de terre lavées, piquées à la fourchette, frottées d'huile et de gros sel.
2. Air fryer 200 °C, 40 à 45 min, retournées à mi-cuisson : peau croustillante, cœur fondant.
3. Fendre en croix, presser les côtés, crème mélangée à la ciboulette ciselée dans l'ouverture.""",
         "Avec un rôti de bœuf ou une pièce du boucher."),

    _acc("carottes-vichy", "Carottes Vichy", 25, ["carottes", "beurre", "sucre", "persil"],
         """Pour 2
- 4 carottes, 1 noix de beurre, 1 c. à c. de sucre, persil

1. Carottes en rondelles fines.
2. Dans une casserole : carottes, beurre, sucre, sel, eau juste à hauteur.
3. Feu moyen sans couvercle, 20 min : l'eau s'évapore, les carottes finissent glacées et brillantes. Persil.""",
         "Carotte : Laetitia l'aime rôtie, râpée, en velouté ; glacée, à confirmer."),

    _acc("pain-ail", "Pain à l'ail", 10, ["baguettes", "beurre", "ail", "persil"],
         """Pour 2
- 1 baguette, 60 g de beurre mou, 2 gousses d'ail, persil

1. Beurre écrasé avec l'ail haché, le persil et une pincée de sel.
2. Baguette entaillée tous les 2 cm sans couper le dessous, du beurre glissé dans chaque fente.
3. Air fryer 180 °C, 5 à 6 min (ou four 200 °C, 10 min).""",
         "Avec un velouté, des lasagnes ou des polpette."),
]

BRUNCHS = [
    _brunch("avocado-toast", "Avocado toast, œuf poché", "plat", 15,
            ["pain de campagne", "avocats", "œufs", "citrons", "vinaigre", "piment d'Espelette"],
            """Pour 2
- 2 grandes tranches de pain de campagne, 1 avocat bien mûr, 2 œufs très frais, 1/2 citron
- un trait de vinaigre, piment d'Espelette

1. Avocat écrasé à la fourchette avec le jus de citron et du sel.
2. Œufs pochés : eau frémissante (pas bouillante) avec le vinaigre, un tourbillon à la cuillère, l'œuf cassé au centre, 3 min. Égoutter sur du papier absorbant.
3. Pain grillé, avocat, œuf, piment d'Espelette, fleur de sel."""),

    _brunch("oeufs-benedicte", "Œufs Bénédicte", "plat", 30,
            ["muffins anglais", "œufs", "jambon", "beurre", "citrons", "vinaigre"],
            """Pour 2
- 2 muffins anglais, 4 œufs (2 pochés, 2 jaunes pour la sauce), 2 tranches de jambon
- 80 g de beurre, 1/2 citron, un trait de vinaigre

1. Hollandaise : 2 jaunes et 1 c. à s. d'eau au bain-marie, fouetter jusqu'à ce que ça mousse et épaississe ; le beurre fondu en filet sans cesser de fouetter. Citron, sel. Garder au bain-marie éteint.
2. Œufs pochés 3 min dans l'eau frémissante vinaigrée.
3. Muffins coupés et grillés, jambon, œuf, hollandaise."""),

    _brunch("omelette", "Omelette champignons et comté", "plat", 10,
            ["œufs", "champignons de Paris", "comté", "beurre"],
            """Pour 2
- 5 œufs, 150 g de champignons de Paris, 50 g de comté râpé, 1 noix de beurre

1. Champignons émincés dorés à la poêle, réservés.
2. Œufs battus avec sel et poivre, juste mélangés.
3. Beurre mousseux, œufs ; ramener les bords vers le centre pendant 1 min, puis laisser prendre en gardant le dessus baveux.
4. Champignons et comté sur une moitié, replier, glisser dans l'assiette."""),

    _brunch("pain-perdu", "Pain perdu brioché", "dessert", 15, ["brioche", "œufs", "lait", "sucre", "beurre"],
            """Pour 2
- 4 tranches épaisses de brioche (rassie, c'est mieux), 2 œufs, 15 cl de lait, 2 c. à s. de sucre, 1 noix de beurre

1. Œufs, lait et sucre battus dans une assiette creuse.
2. Brioche trempée 10 secondes par face, pas plus : elle doit rester entière.
3. Poêle beurrée à feu moyen, 2 à 3 min par face, jusqu'à ce que ce soit caramélisé.
4. Avec des fruits rouges, du sirop d'érable ou juste du sucre."""),

    _brunch("granola", "Granola maison, yaourt grec et fruits rouges", "dessert", 30,
            ["flocons d'avoine", "amandes", "miel", "yaourt grec", "fruits rouges"],
            """Pour 4 (le granola se garde 2 semaines en bocal)
- 200 g de flocons d'avoine, 60 g d'amandes concassées, 4 c. à s. de miel, 2 c. à s. d'huile neutre
- pour servir : yaourt grec, fruits rouges (surgelés, décongelés la veille)

1. Four à 160 °C. Flocons, amandes, miel, huile et une pincée de sel mélangés.
2. Étalés sur une plaque, 20 à 25 min, en remuant à mi-cuisson, jusqu'à ce que ce soit doré.
3. Refroidir sans toucher : il durcit en grappes. Servir sur le yaourt, avec les fruits.""",
            "Se prépare la veille."),

    _brunch("crepes", "Crêpes", "dessert", 30, ["farine", "œufs", "lait", "beurre", "sucre"],
            """Pour 2 (une dizaine)
- 125 g de farine, 2 œufs, 25 cl de lait, 20 g de beurre fondu, 1 c. à s. de sucre, 1 pincée de sel

1. Farine, sucre, sel ; les œufs au centre ; le lait petit à petit en fouettant : pas de grumeaux.
2. Beurre fondu ; 30 min de repos si possible.
3. Poêle chaude à peine beurrée, une petite louche, tourner la poêle ; 1 min, retourner, 30 s.
4. Sucre, confiture, pâte à tartiner ou citron."""),
]

# Plat principal -> 2 à 4 accompagnements (ids). Un plat qui a déjà son féculent reçoit des légumes.
ACCORDS = {
    # Carnet
    "plat-piece-du-boucher": ["af-frites", "acc-pommes-sautees", "acc-haricots-amandes", "acc-salade-verte"],
    "plat-roti-de-boeuf": ["acc-gratin-dauphinois", "acc-pommes-grenaille", "acc-haricots-amandes",
                           "acc-champignons-persillade"],
    "plat-poulet-roti": ["lg-haricots-lardons", "af-carottes", "acc-salade-verte"],               # pommes de terre dedans
    "plat-blanquette-veau": ["acc-haricots-amandes", "acc-salade-verte"],                         # riz dedans
    "plat-boeuf-bourguignon": ["acc-puree-robuchon", "acc-coquillettes", "acc-ecrasee"],
    "plat-saltimbocca": ["acc-ecrasee", "acc-polenta", "acc-tomates-provencale"],
    "plat-bacon-cheese-burger": ["af-frites", "af-patate-douce", "acc-rostis"],
    "plat-quiche-lorraine": ["acc-salade-verte", "acc-tomates-provencale"],
    "plat-croque-monsieur": ["acc-salade-verte", "af-frites"],
    "plat-baguezza": ["acc-salade-verte", "acc-frites-courgette"],
    "lg-baguezza-champi": ["acc-salade-verte", "acc-frites-courgette"],
    "plat-lasagne-bolognese": ["acc-salade-verte", "acc-pain-ail"],
    # À tester
    "lg-quiche-poireaux": ["acc-salade-verte", "acc-tomates-provencale"],
    "af-croque": ["acc-salade-verte", "af-frites"],
    "af-wings": ["af-frites", "af-patate-douce", "acc-frites-courgette"],
    "af-tenders": ["af-frites", "af-patate-douce", "acc-salade-verte"],
    "af-cuisses": ["acc-pommes-grenaille", "acc-semoule", "af-carottes", "acc-frites-courgette"],
    "af-saumon": ["acc-haricots-amandes", "lg-tempura"],                                          # riz dedans
    "tester-osso-buco": ["acc-polenta", "acc-ecrasee", "acc-coquillettes"],
    "tester-polpette": ["acc-pain-ail", "acc-polenta"],
    "lg-veloute-carotte": ["acc-pain-ail", "acc-salade-verte"],
    "mer-gambas-ail": ["acc-riz-pilaf", "acc-salade-verte"],
    # Pour Julien seul (Laetitia mange l'accompagnement)
    "mer-sole-meuniere": ["acc-haricots-amandes", "acc-salade-verte"],                            # pommes de terre dedans
    "mer-dorade-four": ["acc-tomates-provencale", "acc-salade-verte"],
    "mer-cabillaud-chorizo": ["acc-haricots-amandes", "acc-tomates-provencale"],
    "mer-sardines-grillees": ["acc-pommes-grenaille", "acc-salade-verte"],
    "mer-tenders-cabillaud": ["af-frites", "af-patate-douce"],
    "mer-moules-chorizo": ["af-frites", "acc-salade-verte"],
    # Pour Laetitia seule
    "laet-vitello-tonnato": ["acc-salade-verte", "acc-pommes-grenaille"],
}
