"""Les poissons et fruits de mer de Poissons Démasqués (01/11/2026), à tester.

Ce que le jeu a montré pour Laetitia : oui aux crevettes, aux gambas et au saumon fumé ; ça dépend pour le
saumon, le thon, les calamars et la morue ; jamais pour le reste, poisson blanc compris (même pané : non au
fish & chips et aux tenders). Ce qui passe : les crustacés, le saumon cru ou fumé, le thon émietté, la friture
légère, les sauces coco et asiatiques.
- MER : les 13 matchs (oui de Julien et de Laetitia) ; le poke, aussi matché, est déjà au carnet à tester.
- MER_JULIEN : des recettes de poisson pour Julien, que Laetitia a refusées (pour = 'julien').
Rédigées par Claude d'après les versions de référence, à corriger par eux dans l'app.
Mêmes conventions que carnet_depart.py : noms d'ingrédients du catalogue, sel, poivre et huile sous-entendus.
Ajoutées une seule fois (table reprises).
"""

NOM_REPRISE = "poissons-demasques"
POUR_JULIEN = ["tester-moules"]          # les moules frites du Match des Recettes : non de Laetitia au jeu

# Ses « jamais » : aucun n'entre dans une recette du couple
JAMAIS_LAETITIA = ("poisson blanc", "cabillaud", "lieu", "colin", "dorade", "bar", "sole", "truite", "sardine",
                   "maquereau", "anchois", "crabe", "huitre", "moule", "poulpe", "saint-jacques")


def _mer(id_, nom, genre, minutes, ingredients, recette, note=""):
    return {"id": "mer-" + id_, "nom": nom, "genre": genre, "minutes": minutes, "ingredients": ingredients,
            "recette": recette, "lien": "", "note": note}


def _julien(id_, nom, genre, minutes, ingredients, recette, note=""):
    return {**_mer(id_, nom, genre, minutes, ingredients, recette,
                   ("Pour Julien : Laetitia a dit non au jeu. " + note).strip()), "pour": "julien"}


MER = [
    _mer("gambas-ail", "Gambas à l'ail et au persil", "plat", 15,
         ["gambas", "ail", "beurre", "persil", "citrons", "piment", "baguettes"],
         """Pour 2
- 12 gambas crues (décortiquées, la queue laissée)
- 3 gousses d'ail émincées, 30 g de beurre, 1 pincée de piment, 1/2 botte de persil, 1 citron
- une baguette pour saucer

1. Sécher les gambas au papier absorbant : sinon elles bouillent au lieu de dorer.
2. Poêle très chaude, un filet d'huile : les gambas 1 min 30 par face, sans les toucher. Elles deviennent roses et nacrées. Réserver.
3. Feu moyen : beurre, ail, piment, 1 min, sans laisser brunir l'ail.
4. Remettre les gambas, persil haché, jus de citron, sel. Servir tout de suite, avec la baguette.""",
         "Trop cuites, elles deviennent caoutchouteuses : 3 min en tout."),

    _mer("curry-crevettes", "Curry de crevettes coco", "plat", 25,
         ["crevettes crues", "lait de coco", "pâte de curry rouge", "citronnelle", "oignons", "gingembre", "sauce poisson",
          "citrons verts", "coriandre", "riz jasmin"],
         """Pour 2
- 300 g de crevettes crues décortiquées
- 40 cl de lait de coco, 1 c. à s. de pâte de curry rouge, 1 tige de citronnelle, 1 oignon, 2 cm de gingembre
- 1 c. à s. de sauce poisson, 1 citron vert, coriandre
- riz jasmin pour 2

1. Lancer le riz.
2. Oignon émincé fondu 5 min dans un filet d'huile. Ajouter gingembre râpé, citronnelle écrasée et pâte de curry : 1 min.
3. Lait de coco, sauce poisson : 10 min à frémissement, la sauce épaissit.
4. Les crevettes : 3 à 4 min, juste roses.
5. Jus de citron vert, coriandre, sur le riz.""",
         "La sauce se fait d'avance ; les crevettes au dernier moment."),

    _mer("pad-thai", "Pad thaï aux crevettes", "plat", 25,
         ["nouilles de riz", "crevettes crues", "œufs", "pousses de soja", "oignons nouveaux", "cacahuètes", "tamarin",
          "sauce poisson", "sucre de palme", "citrons verts", "ail"],
         """Pour 2
- 200 g de nouilles de riz plates, trempées 30 min dans l'eau tiède
- 200 g de crevettes crues décortiquées, 2 œufs, 1 gousse d'ail
- 100 g de pousses de soja, 3 oignons nouveaux, 40 g de cacahuètes concassées, 1 citron vert
- sauce : 3 c. à s. de pâte de tamarin, 2 c. à s. de sauce poisson, 2 c. à s. de sucre de palme (ou cassonade)

1. Chauffer la sauce 1 min pour fondre le sucre. Goûter : sucré, acide, salé à parts égales.
2. Wok fumant : ail, crevettes 2 min. Pousser sur le côté, casser les œufs, brouiller.
3. Nouilles égouttées et sauce : 2 à 3 min en remuant, jusqu'à ce qu'elles soient tendres et brillantes.
4. Pousses de soja et oignons nouveaux, 30 s.
5. Cacahuètes, quartier de citron vert, piment pour qui en veut.""",
         "Un entraînement pour le Vietnam et le Cambodge en janvier."),

    _mer("linguine-crevettes", "Linguine aux crevettes, ail et citron", "plat", 20,
         ["linguine", "crevettes crues", "ail", "piment", "citrons", "persil", "vin blanc", "beurre"],
         """Pour 2
- 200 g de linguine
- 250 g de crevettes crues décortiquées, 2 gousses d'ail, 1 pincée de piment
- 1 citron (zeste et jus), 10 cl de vin blanc, 20 g de beurre, persil

1. Cuire les linguine 2 min de moins que le paquet. Garder une louche d'eau de cuisson.
2. Grande poêle : huile d'olive, ail, piment, 1 min. Les crevettes, 2 min, retirer.
3. Vin blanc, laisser réduire de moitié. Ajouter les pâtes, la louche d'eau, le beurre : remuer 2 min, la sauce nappe.
4. Remettre les crevettes, zeste et jus de citron, persil.""",
         "Dans le jeu : « linguine vongole », version crevettes."),

    _mer("paella", "Paella", "plat", 60,
         ["riz rond", "cuisses de poulet", "chorizo", "crevettes crues", "calamars", "poivrons rouges", "oignons", "ail",
          "tomates pelées", "safran", "paprika fumé", "bouillon de volaille", "petits pois surgelés", "citrons"],
         """Pour 4 (deux dîners)
- 300 g de riz rond (bomba si possible)
- 4 hauts de cuisse de poulet en morceaux, 100 g de chorizo en rondelles
- 8 crevettes crues avec la tête, 200 g de calamars en anneaux
- 1 poivron rouge, 1 oignon, 2 gousses d'ail, 200 g de tomates pelées
- 1 dose de safran, 1 c. à c. de paprika fumé, 90 cl de bouillon de volaille chaud
- 100 g de petits pois, 1 citron

1. Sauteuse ou plat à paella : dorer poulet et chorizo 10 min, réserver.
2. Poivron et oignon 5 min, ail, tomates écrasées, paprika : 5 min, une sauce épaisse.
3. Riz, 1 min pour l'enrober. Bouillon et safran, sel : remettre poulet et chorizo, répartir. Ne plus jamais remuer.
4. 15 min à feu moyen. Ajouter calamars, crevettes et petits pois en les enfonçant à peine : 8 à 10 min.
5. Les 2 dernières minutes à feu vif : le fond accroche et croustille (le socarrat). Repos 5 min sous un torchon, quartiers de citron.""",
         "Sans moules : un « jamais » de Laetitia. Le chorizo est là pour elle."),

    _mer("calamars-frits", "Calamars frits, aïoli", "entree", 25,
         ["calamars", "farine", "fécule de maïs", "paprika fumé", "citrons", "mayonnaise", "ail"],
         """Pour 2
- 400 g de calamars en anneaux (frais ou décongelés, bien séchés)
- 4 c. à s. de farine, 2 c. à s. de fécule de maïs, 1/2 c. à c. de paprika fumé, sel
- huile de friture, 1 citron
- aïoli express : 4 c. à s. de mayonnaise, 1 petite gousse d'ail râpée, un trait de citron

1. Huile à 180 °C.
2. Mélanger farine, fécule, paprika et sel. Y rouler les anneaux, secouer l'excès.
3. Frire par petites poignées, 1 min 30 à 2 min : à peine dorés. Plus longtemps, ils durcissent.
4. Égoutter, sel, citron, aïoli à côté.""",
         "Air fryer : huilés au pinceau, AIR FRY 200 °C, 8 min en secouant ; moins croustillants qu'en friture."),

    _mer("crevettes-tempura", "Crevettes tempura", "entree", 25,
         ["crevettes crues", "farine", "fécule de maïs", "eau gazeuse", "œufs", "sauce soja", "citrons"],
         """Pour 2
- 12 crevettes crues décortiquées, la queue laissée
- pâte : 100 g de farine, 50 g de fécule de maïs, 20 cl d'eau gazeuse glacée, 1 jaune d'œuf
- sauce : 3 c. à s. de sauce soja, 1 c. à s. de jus de citron, 1 c. à s. d'eau

1. Inciser 3 fois le ventre des crevettes et les étirer : elles restent droites à la cuisson.
2. Huile à 180 °C. Pâte au dernier moment, à peine mélangée : les grumeaux font la légèreté.
3. Crevettes séchées, farinées, trempées dans la pâte : 2 min de friture, par 4.
4. Égoutter sur une grille, sel, sauce à côté.""",
         "À servir avec la tempura de légumes du carnet : même pâte, même huile."),

    _mer("accras", "Accras de morue", "entree", 40,
         ["morue salée", "farine", "levure chimique", "œufs", "ail", "ciboule", "persil", "piment", "citrons verts"],
         """Pour 4 en apéro (une vingtaine)
- 200 g de morue salée, dessalée 24 h au frigo (3 changements d'eau)
- 150 g de farine, 1 c. à c. de levure chimique, 1 œuf, 15 cl d'eau
- 2 gousses d'ail, 2 ciboules, persil, 1/2 piment
- huile de friture, citron vert

1. Pocher la morue 10 min dans l'eau frémissante, l'effeuiller finement en retirant les arêtes.
2. Mélanger farine, levure, œuf et eau : une pâte épaisse. Ajouter morue, ail, ciboule, persil et piment hachés. Repos 30 min.
3. Huile à 175 °C : des cuillerées de pâte, 3 à 4 min, en les retournant. Elles gonflent et dorent.
4. Égoutter, citron vert.""",
         "Pressé : de la morue déjà dessalée chez le poissonnier."),

    _mer("rillettes-thon", "Rillettes de thon", "entree", 10,
         ["thon", "fromage frais", "citrons", "ciboulette", "câpres", "pain de campagne"],
         """Pour 4 en apéro
- 2 boîtes de thon au naturel (280 g égoutté)
- 150 g de fromage frais (type Saint Môret), 1/2 citron, 1 c. à s. de câpres, ciboulette
- pain de campagne grillé

1. Égoutter le thon, l'émietter à la fourchette.
2. Mélanger avec le fromage frais, le jus de citron, les câpres hachées et la ciboulette. Poivre, peu de sel.
3. Au frais 30 min si possible. Sur le pain grillé.""",
         "Se garde 3 jours au frigo."),

    _mer("salade-nicoise", "Salade niçoise", "plat", 20,
         ["thon", "œufs", "tomates", "haricots verts", "pommes de terre", "olives noires", "salade", "oignons rouges",
          "moutarde", "vinaigre de vin rouge"],
         """Pour 2
- 1 boîte de thon (140 g) ou un pavé de thon frais snacké
- 2 œufs, 3 tomates, 150 g de haricots verts, 4 petites pommes de terre, une poignée d'olives noires
- 1 cœur de laitue, 1/2 oignon rouge
- vinaigrette : 1 c. à c. de moutarde, 1 c. à s. de vinaigre de vin, 3 c. à s. d'huile d'olive

1. Pommes de terre 15 min à l'eau salée ; haricots 6 min puis eau glacée ; œufs 9 min.
2. Couper tomates et pommes de terre en quartiers, oignon en fines lamelles, écaler les œufs.
3. Disposer sur la salade, thon émietté au centre, olives.
4. Vinaigrette à la toute fin.""",
         "Sans anchois : un « jamais » de Laetitia (Julien peut en ajouter dans son assiette)."),

    _mer("bagel-saumon", "Bagel saumon fumé cream cheese", "plat", 10,
         ["bagels", "saumon fumé", "fromage frais", "oignons rouges", "câpres", "aneth", "citrons"],
         """Pour 2
- 2 bagels, 4 tranches de saumon fumé
- 4 c. à s. de fromage frais, 1/4 d'oignon rouge en fines lamelles, 1 c. à c. de câpres, aneth, citron

1. Ouvrir et griller les bagels.
2. Fromage frais mélangé à l'aneth et à un trait de citron, tartiné généreusement.
3. Saumon, oignon rouge, câpres, poivre.""",
         "Le brunch du dimanche ; le saumon fumé est un « oui » franc de Laetitia."),

    _mer("makis-saumon", "Makis et sushis au saumon", "plat", 60,
         ["riz à sushi", "vinaigre de riz", "sucre", "algues nori", "pavés de saumon", "avocats", "concombre",
          "fromage frais", "sauce soja", "gingembre mariné", "wasabi"],
         """Pour 2 (une trentaine de pièces)
- 300 g de riz à sushi ; assaisonnement : 4 c. à s. de vinaigre de riz, 1 c. à s. de sucre, 1 c. à c. de sel
- 4 feuilles de nori, 250 g de saumon très frais (qualité sushi, demandé au poissonnier)
- 1 avocat, 1/2 concombre, fromage frais (pour les California)
- sauce soja, gingembre mariné, wasabi ; une natte en bambou

1. Rincer le riz jusqu'à ce que l'eau soit claire, cuire (même volume d'eau, 12 min couvert, 10 min de repos).
2. Mélanger l'assaisonnement chaud au riz à la spatule, en éventant : il devient brillant. Laisser tiédir.
3. Saumon, avocat, concombre en bâtonnets.
4. Nori sur la natte, une fine couche de riz (mains mouillées), garniture sur un bord, rouler en serrant. Couper en 6 au couteau mouillé.
5. Sushis : une boulette de riz, une tranche de saumon dessus.""",
         "À faire ensemble un samedi soir : c'est l'activité autant que le dîner."),

    _mer("langoustines-mayo", "Langoustines mayonnaise", "entree", 20,
         ["langoustines", "œufs", "moutarde", "huile neutre", "citrons", "gros sel"],
         """Pour 2
- 12 langoustines vivantes ou très fraîches
- mayonnaise maison : 1 jaune d'œuf, 1 c. à c. de moutarde, 20 cl d'huile neutre, un trait de citron
- gros sel

1. Mayonnaise : jaune et moutarde à température ambiante, l'huile en filet en fouettant, puis citron et sel.
2. Grande casserole d'eau très salée (30 g par litre) à gros bouillons. Les langoustines : 2 min dès la reprise de l'ébullition.
3. Égoutter, laisser tiédir. Décortiquer à table, tremper dans la mayo.""",
         "Laetitia a dit « jamais » aux langoustines mais « oui » à ce plat : à vérifier à table."),
]

MER_JULIEN = [
    _julien("brandade", "Brandade de morue gratinée", "plat", 60,
            ["morue salée", "pommes de terre", "lait", "ail", "huile d'olive", "thym", "laurier", "chapelure"],
            """Pour 2
- 300 g de morue salée, dessalée 24 h (3 changements d'eau)
- 500 g de pommes de terre, 25 cl de lait, 3 gousses d'ail, 10 cl d'huile d'olive, thym, laurier, chapelure

1. Pocher la morue 10 min dans le lait et de l'eau avec thym et laurier, sans bouillir. Effeuiller, retirer peau et arêtes.
2. Pommes de terre à l'eau, écrasées à la fourchette.
3. Écraser la morue avec l'ail, puis l'huile d'olive en filet et un peu du lait de cuisson : une pâte souple.
4. Mélanger aux pommes de terre, poivre. Dans un plat, chapelure et filet d'huile, 15 min à 200 °C."""),

    _julien("tenders-cabillaud", "Tenders de cabillaud panko (air fryer)", "plat", 25,
            ["dos de cabillaud", "farine", "œufs", "chapelure panko", "parmesan", "paprika fumé", "mayonnaise",
             "sauce piquante"],
            """Pour 2
- 2 dos de cabillaud (300 g), en bâtonnets de 2 cm
- farine, 1 œuf battu, 80 g de panko, 2 c. à s. de parmesan, 1/2 c. à c. de paprika fumé
- sauce : mayonnaise et sauce piquante

1. Sécher le poisson, saler. Farine, œuf, panko mélangé au parmesan et au paprika.
2. Huiler au pinceau. AIR FRY, 200 °C, 8 à 10 min, en retournant à mi-cuisson : le panko est doré, la chair se détache.
3. Mayo piquante à côté.""",
            "Les mêmes gestes que les tenders de poulet."),

    _julien("cabillaud-chorizo", "Cabillaud en croûte de chorizo", "plat", 30,
            ["dos de cabillaud", "chorizo", "chapelure", "beurre", "persil", "pommes de terre", "lait"],
            """Pour 2
- 2 dos de cabillaud (300 g)
- croûte : 60 g de chorizo, 40 g de chapelure, 30 g de beurre mou, persil
- purée : 500 g de pommes de terre, 10 cl de lait chaud, 30 g de beurre

1. Purée : pommes de terre à l'eau, écrasées avec le lait et le beurre.
2. Chorizo haché finement, mélangé à la chapelure, au beurre et au persil.
3. Poisson salé dans un plat, la croûte pressée dessus. 12 à 15 min à 200 °C : la croûte croustille, la chair est nacrée."""),

    _julien("dorade-four", "Dorade au four, citron et herbes", "plat", 40,
            ["dorade", "citrons", "thym", "ail", "pommes de terre", "vin blanc"],
            """Pour 2
- 1 dorade (ou un bar) de 500 g, vidée et écaillée par le poissonnier
- 1 citron, thym, 2 gousses d'ail, 400 g de pommes de terre en rondelles fines, 5 cl de vin blanc

1. Four à 200 °C. Pommes de terre huilées et salées au fond du plat, 15 min.
2. Inciser le poisson 3 fois de chaque côté, saler, garnir le ventre de citron, thym et ail.
3. Sur les pommes de terre, rondelles de citron autour, vin blanc, filet d'huile : 20 à 25 min. La chair se détache de l'arête."""),

    _julien("sole-meuniere", "Sole meunière", "plat", 20,
            ["sole", "farine", "beurre", "citrons", "persil", "pommes de terre"],
            """Pour 2
- 2 soles portion, prêtes à cuire (demander au poissonnier de retirer la peau noire)
- farine, 60 g de beurre, 1 citron, persil ; pommes de terre vapeur

1. Saler, fariner, tapoter l'excès.
2. Poêle, huile et une noix de beurre : 4 min par face à feu moyen, en arrosant. Réserver au chaud.
3. Essuyer la poêle, le reste du beurre jusqu'à noisette (il sent la noisette et mousse), jus de citron, persil.
4. Napper les soles."""),

    _julien("sardines-grillees", "Sardines grillées", "plat", 20,
            ["sardines fraîches", "gros sel", "citrons", "pain de campagne", "persil"],
            """Pour 1 ou 2
- 500 g de sardines fraîches entières, non vidées
- gros sel, citron, persil, pain de campagne grillé

1. Rincer, sécher, gros sel 15 min avant.
2. Plancha ou poêle en fonte très chaude, ou barbecue : 3 min par face. La peau doit cloquer.
3. Citron, persil, sur une tranche de pain qui boit le jus (à la portugaise).""",
            "L'odeur : hotte à fond, ou plancha sur le balcon."),

    _julien("poulpe-grille", "Poulpe grillé, pommes de terre", "plat", 90,
            ["poulpe", "pommes de terre", "paprika fumé", "huile d'olive", "gros sel", "citrons"],
            """Pour 2
- 1 poulpe de 1 kg (surgelé : la congélation l'attendrit)
- 500 g de pommes de terre grenaille, paprika fumé, huile d'olive, gros sel, citron

1. Plonger le poulpe 3 fois dans l'eau bouillante (les tentacules frisent), puis l'y laisser 45 min à 1 h à frémissement : la pointe d'un couteau entre comme dans du beurre.
2. Les pommes de terre dans la même eau les 20 dernières minutes.
3. Tentacules huilés, grillés 3 min par face à la poêle très chaude ou à la plancha.
4. Sur les pommes de terre écrasées, paprika fumé, gros sel, huile d'olive, citron (a feira, en Galice)."""),

    _julien("ceviche", "Ceviche de dorade", "entree", 20,
            ["dorade", "citrons verts", "oignons rouges", "coriandre", "piment", "avocats"],
            """Pour 2
- 250 g de filet de dorade (ou de bar) très frais, sans peau
- 4 citrons verts, 1/2 oignon rouge, coriandre, 1 petit piment, 1 avocat

1. Poisson en dés de 1,5 cm, au frais.
2. Oignon rouge en fines lamelles, rincé à l'eau froide (il perd son piquant).
3. Poisson, sel, jus de citron vert à hauteur : 10 min au frigo. Il blanchit en surface et reste tendre au cœur.
4. Oignon, piment, coriandre, avocat en dés. Tout de suite."""),

    _julien("risotto-saint-jacques", "Risotto aux Saint-Jacques", "plat", 35,
            ["riz carnaroli", "Saint-Jacques", "échalotes", "vin blanc", "bouillon de légumes", "beurre", "parmesan",
             "citrons"],
            """Pour 2
- 160 g de riz carnaroli, 1 échalote, 10 cl de vin blanc, 80 cl de bouillon chaud
- 8 noix de Saint-Jacques, 30 g de beurre froid, 40 g de parmesan, 1/2 citron (zeste)

1. Risotto : échalote, riz nacré, vin blanc, puis le bouillon louche par louche, 17 min.
2. Hors du feu : beurre, parmesan, zeste de citron. Couvrir.
3. Saint-Jacques séchées, poêle fumante, 1 min 30 par face sans les bouger : croûte dorée, cœur translucide.
4. Sur le risotto, fleur de sel."""),

    _julien("tacos-poisson", "Tacos de poisson", "plat", 30,
            ["dos de cabillaud", "tortillas", "chou rouge", "crème fraîche", "citrons verts", "coriandre", "farine",
             "paprika fumé", "sauce piquante"],
            """Pour 2 (6 tacos)
- 300 g de cabillaud en bâtonnets, farine, paprika fumé
- 6 petites tortillas de maïs, 1/4 de chou rouge très finement émincé
- crème : 4 c. à s. de crème fraîche, zeste et jus d'un citron vert ; coriandre, sauce piquante

1. Chou rouge mélangé à un peu de citron vert et de sel : il s'assouplit.
2. Poisson fariné au paprika, poêlé 2 min par face dans l'huile chaude (ou AIR FRY 200 °C 8 min).
3. Tortillas chauffées à sec dans la poêle.
4. Chou, poisson, crème citronnée, coriandre, sauce piquante."""),

    _julien("moules-chorizo", "Moules au chorizo et à la crème", "plat", 30,
            ["moules", "chorizo", "échalotes", "ail", "vin blanc", "crème fraîche", "persil", "baguettes"],
            """Pour 1 gros appétit ou 2
- 1,5 kg de moules de bouchot, grattées
- 80 g de chorizo en dés, 2 échalotes, 1 gousse d'ail, 15 cl de vin blanc, 10 cl de crème, persil

1. Grand faitout : chorizo à sec 2 min, il rend son huile rouge. Échalotes et ail, 2 min.
2. Vin blanc, puis les moules : couvercle, feu vif, 5 min en secouant. Jeter celles qui restent fermées.
3. Retirer les moules, crème dans le jus, 2 min de réduction, persil. Napper.
4. Une baguette pour saucer."""),
]
