"""Les recettes air fryer (01/11/2026) : dix plats « à tester », pensés contre le Deliveroo.

Le croustillant du fast-food (tenders, wings, frites) sans friteuse, et des légumes rôtis croustillants,
la forme sous laquelle Laetitia a le plus de chances de les aimer. Rédigées par Claude pour leur
Ninja Air Fryer Pro (panier carré ; modes MAX CRISP, AIR FRY, ROAST, BAKE, REHEAT, DEHYDRATE ; AIR FRY
jusqu'à 210 °C, MAX CRISP à 240 °C fixe) d'après les temps de référence : vérifier à la première fournée
et corriger dans l'app.
Mêmes conventions que carnet_depart.py : noms d'ingrédients du placard, sel, poivre et huile sous-entendus.
Ajoutées une seule fois (table reprises) : une recette retirée ou corrigée dans l'app ne revient pas.
"""

NOM_REPRISE = "air-fryer"

_PANIER = "Toujours avec la grille au fond du panier ; une seule couche, sans tasser : l'air doit circuler."
_HUILE = "huile au pinceau ou en flacon pompe (pas de spray aérosol : il abîme le revêtement du Ninja)"


def _af(id_, nom, genre, minutes, ingredients, recette, note=""):
    return {"id": "af-" + id_, "nom": nom + " (air fryer)", "genre": genre, "minutes": minutes,
            "ingredients": ingredients, "recette": recette, "lien": "", "note": note}


AIR_FRYER = [
    _af("tenders", "Tenders de poulet panko", "plat", 25,
        ["filets de poulet", "farine", "œufs", "chapelure panko", "paprika fumé", "parmesan", "mayonnaise",
         "sauce piquante"],
        """Pour 2
- 400 g de filets de poulet, coupés en lanières de 2 cm
- 3 c. à s. de farine, 1 œuf battu
- 80 g de chapelure panko, 2 c. à s. de parmesan râpé, 1 c. à c. de paprika fumé, sel
- """ + _HUILE + """
- sauce : 3 c. à s. de mayonnaise + 1 c. à c. de sauce piquante

1. Saler les lanières. Les passer dans la farine, puis l'œuf, puis le panko mélangé au parmesan et au paprika. Bien presser pour que la panure tienne.
2. AIR FRY, 200 °C, 3 min à vide pour préchauffer.
3. Huiler légèrement le panier et les tenders (c'est l'huile qui fait dorer le panko). """ + _PANIER + """
4. AIR FRY, 200 °C, 10 à 12 min, en les retournant à mi-cuisson. Ils sont cuits à cœur quand la chair est blanche et le jus clair.
5. Servir avec la sauce mayo piquante, et des frites air fryer.""",
        "Le remplaçant direct du poulet frit commandé."),

    _af("cuisses", "Cuisses de poulet paprika-citron", "plat", 40,
        ["cuisses de poulet", "paprika fumé", "ail", "citrons", "thym", "miel"],
        """Pour 2
- 2 cuisses de poulet entières (ou 4 hauts de cuisse), avec la peau
- 1 c. à s. d'huile, 1 c. à c. de paprika fumé, 1 gousse d'ail râpée, 1/2 c. à c. de thym, sel
- 1 citron (zeste et jus), 1 c. à c. de miel

1. Sécher la peau au papier absorbant : une peau sèche est une peau croustillante.
2. Mélanger huile, paprika, ail, thym, zeste, sel. En frotter les cuisses, dessus et dessous.
3. ROAST, 190 °C, peau dessous, 12 min. Retourner peau dessus, encore 12 à 15 min : la peau est dorée et le jus clair quand on pique près de l'os.
4. Repos 5 min. Mélanger jus de citron et miel, en arroser les cuisses au moment de servir.""",
        "Avec des pommes de terre grenaille coupées en deux, cuites dessous les 15 dernières minutes."),

    _af("wings", "Ailes de poulet croustillantes", "plat", 35,
        ["ailes de poulet", "levure chimique", "paprika fumé", "ail", "sauce soja", "miel", "sauce piquante"],
        """Pour 2
- 1 kg d'ailes de poulet (manchons et pilons séparés)
- 1 c. à s. de levure chimique, 1 c. à c. de paprika fumé, 1/2 c. à c. d'ail en poudre (ou 1 gousse râpée), sel
- laque : 2 c. à s. de sauce soja, 2 c. à s. de miel, 1 c. à s. de sauce piquante

1. Sécher les ailes au papier absorbant. Les rouler dans levure chimique, paprika, ail et sel : la levure fait cloquer la peau comme une friture.
2. """ + _PANIER + """
3. AIR FRY, 180 °C, 12 min, puis secouer et monter à 210 °C pour 10 à 12 min. 1 kg tient dans le panier carré en le secouant bien ; s'il déborde, deux fournées.
4. Pendant ce temps, chauffer la laque 1 min dans une petite casserole.
5. Rouler les ailes dans la laque à la sortie, 2 min de plus en AIR FRY à 210 °C pour la caraméliser.""",
        "La levure chimique, pas la levure boulangère : c'est elle qui rend la peau croustillante."),

    _af("saumon", "Saumon laqué soja-miel", "plat", 15,
        ["pavés de saumon", "sauce soja", "miel", "ail", "huile de sésame", "riz basmati"],
        """Pour 2
- 2 pavés de saumon avec la peau
- laque : 2 c. à s. de sauce soja, 1 c. à s. de miel, 1 gousse d'ail râpée, quelques gouttes d'huile de sésame
- riz pour 2 (lancé avant le saumon)

1. Lancer le riz.
2. Mélanger la laque, en badigeonner le saumon, côté chair.
3. Saumon peau dessous dans le panier (sur une feuille de papier cuisson percée, ça évite que ça colle).
4. AIR FRY, 200 °C, 8 à 10 min selon l'épaisseur : le cœur doit rester nacré.
5. Badigeonner du reste de laque à mi-cuisson. Servir sur le riz.""",
        "Un dîner en 15 minutes, presque entièrement au placard."),

    _af("gnocchi", "Gnocchi croustillants tomates-mozza", "plat", 20,
        ["gnocchi", "tomates cerises", "mozzarella", "parmesan", "ail", "basilic"],
        """Pour 2
- 500 g de gnocchi frais du commerce (sans les cuire avant)
- 250 g de tomates cerises, 1 gousse d'ail écrasée
- 1 boule de mozzarella, 2 c. à s. de parmesan râpé, quelques feuilles de basilic
- 1 c. à s. d'huile d'olive, sel

1. Mélanger gnocchi, tomates, ail, huile et sel dans un saladier.
2. AIR FRY, 200 °C, 12 à 14 min, en secouant le panier deux fois : les gnocchi dorent, les tomates éclatent.
3. Verser dans un plat, mozzarella déchirée et parmesan dessus, et encore 2 min dans le panier pour la faire filer.
4. Basilic, huile d'olive de finition.""",
        "Les gnocchi deviennent croustillants dehors et fondants dedans : rien à voir avec la version bouillie."),

    _af("croque", "Croque-monsieur", "plat", 12,
        ["pain de mie", "jambon", "comté", "beurre", "crème fraîche"],
        """Pour 2
- 4 tranches de pain de mie, beurre mou
- 2 tranches de jambon, 80 g de comté râpé
- 2 c. à s. de crème fraîche, poivre, une pincée de muscade

1. Beurrer les tranches côté extérieur.
2. Mélanger crème, la moitié du comté, poivre, muscade.
3. Monter : pain, crème au comté, jambon, comté, pain. Un peu de comté sur le dessus.
4. AIR FRY, 180 °C, 8 à 10 min, en retournant à mi-cuisson (une pique en bois pour tenir la tranche du dessus, sinon elle s'envole).""",
        "Dîner de secours : tout se garde au placard et au frigo."),

    _af("frites", "Frites maison", "accompagnement", 40,
        ["pommes de terre", "fécule de maïs", "fleur de sel"],
        """Pour 2
- 600 g de pommes de terre à frites (bintje ou agata)
- 1 c. à s. d'huile, 1 c. à c. de fécule de maïs, fleur de sel

1. Couper en bâtonnets de 1 cm. Les rincer puis les laisser 20 min dans l'eau froide : on retire l'amidon qui les ramollit.
2. Égoutter et sécher très soigneusement dans un torchon. C'est l'étape qui compte.
3. Mélanger avec l'huile et la fécule.
4. AIR FRY, 180 °C, 15 min en secouant à mi-cuisson, puis 210 °C, 6 à 8 min jusqu'à ce qu'elles soient dorées.
5. Fleur de sel à la sortie, pas avant.""",
        "Pressé : frites surgelées, MAX CRISP 15 à 18 min sans huile, en secouant deux fois."),

    _af("patate-douce", "Frites de patate douce", "accompagnement", 25,
        ["patates douces", "fécule de maïs", "paprika fumé", "fleur de sel"],
        """Pour 2
- 2 patates douces moyennes, épluchées, en bâtonnets fins (8 mm)
- 1 c. à s. d'huile, 1 c. à s. de fécule de maïs, 1/2 c. à c. de paprika fumé

1. Sécher les bâtonnets, les rouler dans l'huile, puis dans la fécule et le paprika : la patate douce ne croustille pas sans cette fécule.
2. """ + _PANIER + """
3. AIR FRY, 200 °C, 15 à 18 min, en secouant deux fois. Elles se raffermissent en refroidissant 2 min.
4. Fleur de sel. Avec la mayo piquante des tenders.""",
        "Un oui de Julien aux Légumes Démasqués."),

    _af("brocoli", "Brocoli croustillant au parmesan", "accompagnement", 12,
        ["brocoli", "parmesan", "ail", "citrons"],
        """Pour 2
- 1 brocoli en petits bouquets, la tige pelée et coupée en bâtonnets
- 1 c. à s. d'huile d'olive, 1 gousse d'ail râpée, sel
- 2 c. à s. de parmesan râpé, 1/2 citron

1. Bouquets bien secs, mélangés à l'huile, l'ail et le sel.
2. AIR FRY, 190 °C, 7 min, secouer.
3. Parmesan par-dessus, encore 2 à 3 min : les pointes noircissent légèrement et croustillent, c'est le but.
4. Un filet de citron à la sortie.""",
        "À faire goûter à Laetitia : grillé, il n'a plus le goût de brocoli vapeur."),

    _af("crumble", "Crumble aux pommes express", "dessert", 25,
        ["pommes", "farine", "beurre", "cassonade", "cannelle"],
        """Pour 2
- 2 pommes, en dés, 1 c. à s. de cassonade, 1 pincée de cannelle
- pâte : 40 g de farine, 30 g de beurre froid, 30 g de cassonade

1. Pommes, cassonade et cannelle dans 2 ramequins, posés sur la grille du panier.
2. Sabler du bout des doigts farine, beurre et cassonade, jusqu'à obtenir des miettes. Les répartir sur les pommes.
3. BAKE, 170 °C, 15 min : le dessus est doré, les pommes bouillonnent sur les bords.
4. Avec une cuillère de crème fraîche ou de yaourt grec.""",
        "Le dessert lancé pendant qu'on dîne."),
]
