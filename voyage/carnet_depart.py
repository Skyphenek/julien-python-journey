"""Le carnet de départ de Casa Binomerie (28/10/2026).

- Les plats de Julien et Laetitia (19) et ceux qu'ils savent déjà faire (« on sait faire » au
  Match des Recettes, 9). Les recettes italiennes viennent de leur base Mamma (recettes_mamma.json,
  extraite de leur base Notion publiée, sources Giallo Zafferano), reprises telles quelles ; les
  autres sont rédigées par Claude, à corriger par eux dans l'app.
- A_TESTER : leurs 20 matchs au jeu, la liste « à tester ensemble » (recettes : base Mamma ou recettes_a_tester.py).

Les ingrédients
reprennent les noms du placard (courses.PLACARD_DEPART) : c'est ce qui permet le secours
(plat ≤ 20 min dont tout est au placard) et l'ajout aux courses. Sel, poivre et huile : sous-entendus.
Injecté en base à la livraison 3 (Dîners).
"""

import json
from pathlib import Path

from recettes_a_tester import RECETTES_A_TESTER

_MAMMA = json.loads((Path(__file__).parent / "recettes_mamma.json").read_text())


def _mamma(id_, nom, minutes, ingredients, note=""):
    """Une recette de leur base Mamma, texte d'origine, lien vers la source."""
    r = _MAMMA[id_]
    return {"id": id_, "nom": nom, "genre": "plat", "minutes": minutes, "ingredients": ingredients,
            "recette": r["recette"], "lien": r["source"], "note": note}


CARNET_DEPART = [
    # --- Pâtes et plats italiens : leur base Mamma ------------------------------------------------
    _mamma("plat-carbonara", "Spaghetti alla carbonara", 20,
           ["spaghetti", "guanciale ou pancetta", "œufs", "pecorino"],
           "Temps compté à 20 min (la base Mamma dit 25) : c'est le dîner de secours numéro un."),
    _mamma("plat-amatriciana", "Spaghetti all'amatriciana", 35,
           ["spaghetti", "guanciale ou pancetta", "tomates pelées", "pecorino", "vin blanc"]),
    _mamma("plat-lasagne-bolognese", "Lasagne alla bolognese", 300,
           ["feuilles de lasagne", "parmesan", "bœuf haché", "porc haché", "guanciale ou pancetta", "carottes",
            "céleri", "oignons", "passata", "vin blanc", "bouillon", "lait", "beurre", "farine"],
           "Le ragù se fait la veille ; les lasagnes se congèlent très bien."),
    _mamma("plat-cacio-e-pepe", "Spaghetti cacio e pepe", 20, ["spaghetti", "pecorino", "poivre en grains"]),
    _mamma("plat-gricia", "Mezze maniche alla gricia", 25, ["rigatoni", "guanciale ou pancetta", "pecorino"]),
    _mamma("plat-risotto-milanese", "Risotto alla milanese", 45,
           ["riz carnaroli", "bouillon", "beurre", "oignons", "vin blanc", "safran", "parmesan"]),
    _mamma("plat-saltimbocca", "Saltimbocca alla romana", 25,
           ["escalopes de veau", "jambon cru", "sauge", "farine", "beurre", "vin blanc"]),

    # --- Plats ---------------------------------------------------------------------------------
    {
        "id": "plat-blanquette-veau", "nom": "Blanquette de veau", "genre": "plat", "minutes": 150,
        "ingredients": ["veau", "carottes", "oignons", "champignons de Paris", "beurre", "farine", "crème fraîche",
                        "œufs", "citrons", "riz"],
        "recette": """Pour 4
- 1,2 kg de veau, mélange d'épaule et de tendron (le tendron donne le moelleux), en gros cubes
- 2 carottes, 1 oignon piqué de 2 clous de girofle, 1 bouquet garni (thym, laurier, queues de persil)
- 250 g de petits champignons de Paris, 1/2 citron
- 40 g de beurre, 40 g de farine
- 20 cl de crème fraîche épaisse, 1 jaune d'œuf
- riz pour 4

1. Viande dans une cocotte, couvrir d'eau froide, porter à ébullition, écumer soigneusement (c'est ce qui garde la sauce blanche).
2. Ajouter carottes en tronçons, oignon, bouquet garni, sel. Laisser frémir — jamais bouillir — 1 h 30 à 2 h, jusqu'à ce que la viande se coupe à la cuillère.
3. Champignons : les étuver 10 min avec une noix de beurre, un filet de citron et une pincée de sel.
4. Filtrer et garder 60 cl de bouillon. Roux blanc avec 40 g de beurre et 40 g de farine, 2 min sans colorer ; verser le bouillon en fouettant, 10 min à petit feu.
5. Hors du feu : mélanger jaune et crème, les incorporer à la sauce. Rectifier avec le jus de citron, sel, poivre blanc. Ne plus faire bouillir.
6. Remettre la viande, les carottes et les champignons dans la sauce, réchauffer doucement.
7. Riz cuit avec une louche du bouillon de cuisson.""",
        "lien": "",
        "note": "",
    },
    {
        "id": "plat-baguezza", "nom": "Baguezza", "genre": "plat", "minutes": 15,
        "ingredients": ["demi-baguettes", "passata", "mozzarella râpée", "jambon"],
        "recette": """Pour 2
- 2 demi-baguettes, ouvertes dans la longueur (4 tartines)
- 15 cl de passata, 1 filet d'huile d'olive, origan, sel
- 125 g de mozzarella râpée (ou une boule de mozzarella bien essorée, déchirée)
- 2 tranches de jambon

1. Four à 220 °C, grill + chaleur tournante.
2. Assaisonner la passata : sel, huile d'olive, origan. Ne pas la cuire.
3. Tartiner les baguettes jusqu'aux bords (sinon ils brûlent), jambon, fromage.
4. 8 à 10 min sur la grille haute : le fromage gratine, le dessous reste croustillant. Baguettes congelées : 3 min de plus, sans décongeler.

Variantes : comté et jambon ; beaufort, bacon et oignon (la savoyarde) ; mozzarella fraîche et basilic à la sortie du four.""",
        "lien": "",
        "note": "",
    },
    {
        "id": "plat-oeuf-cocotte", "nom": "Œufs cocotte", "genre": "plat", "minutes": 15,
        "ingredients": ["œufs", "crème fraîche", "beurre", "demi-baguettes"],
        "recette": """Pour 2
- 4 œufs, 4 c. à s. de crème fraîche épaisse, beurre
- en option : jambon en dés, comté râpé, ciboulette
- 1 demi-baguette pour les mouillettes

1. Four à 180 °C. Mettre de l'eau à chauffer.
2. Beurrer 4 ramequins. Au fond : 1/2 c. à s. de crème (et l'option choisie), casser un œuf, saler le blanc, pas le jaune. Encore 1/2 c. à s. de crème autour du jaune.
3. Ramequins dans un plat, eau chaude jusqu'à mi-hauteur. Four 10 à 12 min : le blanc est pris, le jaune tremble encore quand on secoue.
4. Poivre, ciboulette, mouillettes grillées.""",
        "lien": "",
        "note": "",
    },
    {
        "id": "plat-oeuf-coque", "nom": "Œufs à la coque", "genre": "plat", "minutes": 10,
        "ingredients": ["œufs", "demi-baguettes", "beurre"],
        "recette": """Pour 2
- 4 œufs à température ambiante (sinon ils fêlent)
- 1 demi-baguette, beurre, fleur de sel

1. Eau à petits frémissements, pas à gros bouillons.
2. Descendre les œufs à la cuillère, lancer le minuteur : 3 min pour un jaune coulant et un blanc juste pris (3 min 30 pour de gros œufs).
3. Pendant ce temps : mouillettes grillées, beurrées, une pincée de fleur de sel.
4. Sortir, décalotter tout de suite (sinon ça continue à cuire).""",
        "lien": "",
        "note": "",
    },
    {
        "id": "plat-oeufs-brouilles", "nom": "Œufs brouillés au bacon", "genre": "plat", "minutes": 15,
        "ingredients": ["œufs", "beurre", "crème fraîche", "bacon", "herbes surgelées"],
        "recette": """Pour 2
- 5 œufs, 30 g de beurre bien froid, 1 c. à s. de crème fraîche
- 6 tranches de bacon
- ciboulette, poivre

1. Bacon dans une poêle froide, feu moyen, jusqu'à ce qu'il soit croustillant. Égoutter sur du papier.
2. Battre légèrement les œufs à la fourchette (sans mousse), saler.
3. Casserole à fond épais, feu doux, la moitié du beurre. Verser les œufs, remuer sans arrêt à la spatule en raclant le fond.
4. Retirer la casserole du feu 10 s dès que ça prend trop vite, puis remettre. Compter 5 à 6 min : de petits grumeaux crémeux.
5. Encore un peu baveux : hors du feu, le reste du beurre froid et la crème — ça arrête la cuisson. Poivre, ciboulette, bacon émietté dessus.""",
        "lien": "",
        "note": "",
    },
    {
        "id": "plat-salad-bar", "nom": "Salad bar", "genre": "plat", "minutes": 20,
        "ingredients": ["salade", "tomates", "concombre", "thon", "maïs", "pois chiches", "œufs", "vinaigre",
                        "moutarde"],
        "recette": """Pour 2 — chacun compose son assiette
- 1 salade (sucrine ou romaine), 2 tomates, 1/2 concombre
- 1 boîte de thon, 1 petite boîte de maïs, 1 boîte de pois chiches rincés
- 2 œufs
- vinaigrette : 1 c. à c. de moutarde, 1 c. à s. de vinaigre, 3 c. à s. d'huile, sel, poivre

1. Œufs dans l'eau bouillante : 6 min 30 pour mollets, 9 min 30 pour durs ; puis eau glacée.
2. Laver et essorer la salade (bien sèche, sinon la vinaigrette glisse). Couper les légumes.
3. Égoutter thon, maïs, pois chiches. Tout disposer dans des bols au milieu de la table.
4. Vinaigrette : moutarde et vinaigre avec le sel, puis l'huile en fouettant.

Bonus : des croûtons de demi-baguette dorés à la poêle, des copeaux de comté.""",
        "lien": "",
        "note": "",
    },
    {
        "id": "plat-taco-monday", "nom": "Taco Monday", "genre": "plat", "minutes": 25,
        "ingredients": ["tortillas", "steaks hachés", "épices tacos", "oignons", "tomates", "salade", "avocat",
                        "cheddar râpé", "yaourt grec", "citrons"],
        "recette": """Pour 2
- 300 g de bœuf haché frais (ou 2-3 steaks hachés du congélateur, décongelés)
- 1 oignon, 2 c. à c. d'épices tacos (ou cumin, paprika fumé, origan, ail en poudre, piment)
- 6 petites tortillas
- garnitures : 2 tomates, salade ciselée, 1 avocat, cheddar râpé, yaourt grec, citron vert

1. Pico de gallo : tomates en petits dés, un peu d'oignon ciselé, sel, jus de citron. Avocat écrasé avec sel et citron.
2. Poêle très chaude, un filet d'huile, la viande étalée : la laisser colorer 2 min sans toucher, puis émietter.
3. Le reste de l'oignon émincé, 2 min. Épices et 5 cl d'eau, laisser réduire jusqu'à ce que ça nappe.
4. Tortillas chauffées 20 s par face dans une poêle sèche, gardées au chaud dans un torchon.
5. Tout au milieu de la table, chacun garnit.""",
        "lien": "",
        "note": "",
    },
    {
        "id": "plat-bacon-cheese-burger", "nom": "Bacon cheese burger", "genre": "plat", "minutes": 25,
        "ingredients": ["pains burger", "steaks hachés", "bacon", "cheddar en tranches", "oignons", "salade",
                        "tomates"],
        "recette": """Pour 2
- 2 pains burger briochés, beurre
- 2 steaks hachés de 150 g (frais à 15-20 % de matière grasse, l'idéal ; sinon congelés, décongelés)
- 4 tranches de bacon, 2 à 4 tranches de cheddar
- 1/2 oignon rouge en rondelles fines, salade, 1 tomate
- sauce : 2 c. à s. de mayonnaise, 1 de ketchup, 1 c. à c. de moutarde, 1 cornichon haché

1. Bacon croustillant à la poêle, réserver. Garder un peu de gras dans la poêle.
2. Pains ouverts, face coupée beurrée, dorée 1 min dans la poêle.
3. Saler les steaks juste avant de cuire. Poêle très chaude, 2 à 3 min sans toucher, retourner.
4. Cheddar sur les steaks, couvercle 1 min pour le faire fondre.
5. Montage : sauce, salade, steak au cheddar, bacon, tomate, oignon, sauce sur le chapeau.

Variante smash : boule de 120 g écrasée fort à la spatule dans la poêle fumante, 2 min, retourner, fromage.""",
        "lien": "",
        "note": "",
    },
    {
        "id": "plat-piece-du-boucher", "nom": "Pièce du boucher, sauce échalote", "genre": "plat", "minutes": 15,
        "ingredients": ["pièce du boucher", "beurre", "échalotes", "vinaigre"],
        "recette": """Pour 2
- 2 pièces de 200 g (onglet, bavette ou entrecôte), sorties du frigo 30 min avant
- 30 g de beurre, 2 échalotes ciselées, 1 c. à s. de vinaigre de vin rouge
- fleur de sel, poivre

1. Poêle en fonte ou inox très chaude, un filet d'huile. Viande séchée au papier.
2. 2 à 3 min par face pour saignant (selon l'épaisseur). Dans la dernière minute : 20 g de beurre, arroser la viande à la cuillère.
3. Reposer la viande 5 min sur une assiette chaude, couverte.
4. Dans la même poêle, feu moyen : échalotes 2 min, déglacer au vinaigre, 2 c. à s. d'eau, le jus de repos de la viande, le reste du beurre.
5. Trancher contre le fil, fleur de sel, poivre, sauce par-dessus.

Avec : purée façon Robuchon ou pommes de terre sautées.""",
        "lien": "",
        "note": "Passage chez le boucher à prévoir.",
    },
    {
        "id": "plat-roti-de-boeuf", "nom": "Rôti de bœuf", "genre": "plat", "minutes": 50,
        "ingredients": ["rôti de bœuf", "beurre", "ail"],
        "recette": """Pour 3-4
- 1 rôti de bœuf de 800 g à 1 kg, sorti du frigo 1 h avant
- 30 g de beurre, 4 gousses d'ail en chemise, thym

1. Four à 220 °C.
2. Cocotte ou poêle allant au four, un filet d'huile, très chaud : saisir le rôti sur toutes les faces, 5 min au total.
3. Beurre, ail, thym autour. Au four : environ 20 min pour 800 g, saignant (cœur à 50-52 °C au thermomètre ; 55 °C à point). Arroser une fois.
4. Repos 10 min sous papier aluminium, dans le four éteint porte ouverte : la viande se détend et ne perd pas son jus.
5. Saler à la découpe. Déglacer la cocotte avec 5 cl d'eau pour le jus, écraser l'ail confit dedans.

Avec : pommes de terre sautées ou purée façon Robuchon.""",
        "lien": "",
        "note": "Passage chez le boucher à prévoir. Un thermomètre de cuisson change la vie.",
    },
    {
        "id": "plat-puree-jambon", "nom": "Purée jambon rapide", "genre": "plat", "minutes": 20,
        "ingredients": ["pommes de terre", "lait", "beurre", "jambon"],
        "recette": """Pour 2
- 600 g de pommes de terre (Bintje ou BF15, à chair farineuse)
- 15 à 20 cl de lait, 40 g de beurre, muscade
- 2 à 3 tranches de jambon, en lanières
- en option : 50 g de comté râpé

1. Éplucher, couper en petits cubes de 2 cm (c'est ce qui la rend rapide). Départ eau froide salée, 12 à 15 min après ébullition : la pointe du couteau entre sans résistance.
2. Pendant ce temps, chauffer le lait.
3. Égoutter, remettre 1 min sur le feu pour sécher. Écraser au presse-purée ou à la fourchette — jamais au mixeur (la purée devient élastique).
4. Le beurre d'abord, puis le lait chaud petit à petit jusqu'à la texture voulue. Sel, muscade.
5. Le jambon (et le comté) mélangé ou posé dessus.""",
        "lien": "",
        "note": "",
    },
    # --- Accompagnements ------------------------------------------------------------------------
    {
        "id": "acc-puree-robuchon", "nom": "Purée façon Robuchon", "genre": "accompagnement", "minutes": 45,
        "ingredients": ["pommes de terre", "beurre", "lait"],
        "recette": """Pour 4
- 1 kg de pommes de terre ratte, de même taille
- 250 g de beurre très froid, en dés (oui, autant)
- 20 à 25 cl de lait entier
- gros sel

1. Pommes de terre lavées, avec la peau, départ eau froide salée (10 g par litre). Cuire 25 min environ à frémissement : le couteau entre sans forcer.
2. Éplucher encore chaudes, passer au moulin à légumes grille fine (ou au presse-purée).
3. Remettre dans la casserole, feu moyen, et dessécher 4 à 5 min en remuant à la spatule : la purée doit se détacher des bords.
4. Feu doux. Incorporer le beurre froid petit à petit, en remuant vigoureusement : c'est ce mouvement qui la rend lisse et brillante.
5. Lait bouillant en filet, sans cesser de remuer, jusqu'à la consistance voulue. Sel.
6. Pour le service façon restaurant : la passer au tamis fin.""",
        "lien": "",
        "note": "",
    },
    {
        "id": "acc-pommes-sautees", "nom": "Pommes de terre sautées", "genre": "accompagnement", "minutes": 30,
        "ingredients": ["pommes de terre", "beurre", "ail", "herbes surgelées"],
        "recette": """Pour 2
- 600 g de pommes de terre à chair ferme (Charlotte, Amandine)
- 2 c. à s. d'huile + 20 g de beurre (ou de la graisse de canard)
- 2 gousses d'ail hachées, persil

1. Éplucher, couper en rondelles de 5 mm ou en cubes. Précuire 6 min dans l'eau salée bouillante, égoutter et laisser sécher à l'air 5 min (le secret du croustillant).
2. Grande poêle, huile chaude : une seule couche de pommes de terre. Ne pas toucher pendant 5 min.
3. Retourner, ajouter le beurre, continuer 10 à 12 min en sautant de temps en temps, jusqu'à ce qu'elles soient dorées partout.
4. Dans la dernière minute : ail et persil (ail ajouté plus tôt, il brûle). Sel.""",
        "lien": "",
        "note": "",
    },
    # --- Entrée --------------------------------------------------------------------------------
    {
        "id": "entree-tzatziki", "nom": "Tzatziki", "genre": "entree", "minutes": 10,
        "ingredients": ["yaourt grec", "concombre", "ail", "citrons", "herbes surgelées", "huile d'olive"],
        "recette": """Pour 4 à l'apéro
- 300 g de yaourt grec (le vrai, à 10 % de matière grasse)
- 1/2 concombre, 1 petite gousse d'ail
- 1 c. à s. d'huile d'olive, jus d'1/2 citron
- aneth ou menthe, sel

1. Râper le concombre avec la peau, le saler, le laisser 10 min dans une passoire, puis le presser fort dans les mains : sans cette étape, le tzatziki devient de la soupe.
2. Mélanger yaourt, concombre, ail râpé, huile, citron, herbes. Sel.
3. 30 min au frais si possible, filet d'huile d'olive au service.

Avec : pain pita ou demi-baguette grillée, crudités.""",
        "lien": "",
        "note": "",
    },
    # --- Desserts ------------------------------------------------------------------------------
    {
        "id": "dessert-brownie", "nom": "Brownie", "genre": "dessert", "minutes": 40,
        "ingredients": ["chocolat noir", "beurre", "sucre", "œufs", "farine"],
        "recette": """Moule de 20 × 20 cm, 9 parts
- 200 g de chocolat noir à 60-70 %
- 150 g de beurre
- 150 g de sucre (moitié blanc, moitié cassonade si possible)
- 3 œufs, 60 g de farine, 1 pincée de sel
- en option : 100 g de noix de pécan concassées

1. Four à 180 °C. Moule chemisé de papier cuisson.
2. Fondre chocolat et beurre au bain-marie ou au micro-ondes par 30 s. Laisser tiédir.
3. Ajouter le sucre, puis les œufs un par un en mélangeant bien entre chaque. Farine et sel, mélanger juste ce qu'il faut. Les noix.
4. 20 à 22 min : le dessus craquelle, le centre tremble encore et la lame ressort humide. C'est voulu : il finit de prendre en refroidissant.
5. Laisser refroidir complètement (idéalement 1 h au frais) avant de couper.""",
        "lien": "",
        "note": "",
    },
    {
        "id": "dessert-tiramisu", "nom": "Tiramisu", "genre": "dessert", "minutes": 30,
        "ingredients": ["mascarpone", "cacao", "œufs", "sucre", "boudoirs", "café"],
        "recette": """Pour 6 — à faire la veille (6 h de frigo minimum)
- 3 œufs très frais
- 250 g de mascarpone, 70 g de sucre
- 200 g de boudoirs (savoiardi)
- 30 cl de café fort (espresso), refroidi ; en option 2 c. à s. de marsala ou d'amaretto
- cacao amer en poudre

1. Séparer blancs et jaunes. Fouetter jaunes et sucre jusqu'à ce que le mélange blanchisse et double de volume.
2. Ajouter le mascarpone, fouetter juste pour lisser.
3. Monter les blancs en neige ferme avec une pincée de sel, les incorporer à la spatule en soulevant, en trois fois, sans casser la mousse.
4. Tremper chaque boudoir 1 seconde dans le café (pas plus, sinon il s'effondre). Une couche de boudoirs, la moitié de la crème, une couche de boudoirs, le reste de la crème.
5. Filmer, au frigo au moins 6 h, idéalement une nuit.
6. Cacao tamisé au moment de servir, pas avant (il détrempe).""",
        "lien": "",
        "note": "",
    },
    # --- « On sait faire » au Match des Recettes : les classiques bistro ----------------------------
    {
        "id": "plat-boeuf-bourguignon", "nom": "Bœuf bourguignon", "genre": "plat", "minutes": 210,
        "ingredients": ["paleron ou joue de bœuf", "vin rouge", "guanciale ou pancetta", "champignons de Paris",
                        "oignons", "carottes", "ail", "farine", "beurre", "bouillon"],
        "recette": """Pour 6 — meilleur réchauffé le lendemain
- 1,5 kg de paleron ou de joue de bœuf, en cubes de 5 cm
- 75 cl de vin rouge de Bourgogne (un pinot noir correct, pas un vin de cuisine)
- 150 g de lardons de poitrine, 250 g de champignons de Paris, 12 petits oignons grelots
- 2 carottes, 1 oignon, 2 gousses d'ail, 1 bouquet garni
- 2 c. à s. de farine, 40 g de beurre, 25 cl de bouillon de bœuf

1. La veille (facultatif mais ça change tout) : faire mariner la viande avec le vin, l'oignon et les carottes en rondelles, l'ail et le bouquet garni. Égoutter et sécher la viande au papier avant de la saisir, garder la marinade.
2. Cocotte en fonte, feu vif, un filet d'huile : saisir la viande en plusieurs fois, sans entasser, jusqu'à une croûte brune sur toutes les faces. Réserver.
3. Faire revenir les légumes de la marinade 5 min, remettre la viande, saupoudrer de farine, remuer 2 min (la farine doit roussir légèrement).
4. Verser le vin de la marinade porté à ébullition et le bouillon : la viande doit être juste couverte. Bouquet garni, sel, poivre.
5. Couvrir, 2 h 30 à 3 h à frémissement (ou au four à 150 °C) : la viande se défait à la fourchette.
6. Garniture, 20 min avant la fin : lardons dorés à la poêle, puis les oignons grelots glacés dans le gras avec une noix de beurre et une pincée de sucre, puis les champignons sautés. Tout ajouter dans la cocotte.
7. Si la sauce est trop liquide, réduire à découvert : elle doit napper la cuillère.

Erreurs fréquentes
- Saisir la viande mouillée ou entassée : elle bout au lieu de colorer, et la sauce n'a pas de fond.
- Faire bouillir : à gros bouillons, la viande se resserre et reste sèche, même après 3 h.

Avec : pommes de terre vapeur, tagliatelles fraîches ou purée.""",
        "lien": "", "note": "",
    },
    {
        "id": "plat-croque-monsieur", "nom": "Croque-monsieur", "genre": "plat", "minutes": 20,
        "ingredients": ["pain de mie", "jambon", "comté", "beurre", "lait", "farine"],
        "recette": """Pour 2 (4 croques)
- 8 tranches de pain de mie de bonne qualité (ou de pain de campagne)
- 4 tranches de jambon blanc
- 150 g de comté râpé
- béchamel express : 20 g de beurre, 20 g de farine, 20 cl de lait, muscade, sel, poivre
- beurre mou

1. Four à 220 °C, grill.
2. Béchamel : beurre fondu, farine, 1 min en remuant ; lait froid d'un coup, fouetter jusqu'à épaississement, 2 min. Sel, poivre, muscade. Hors du feu, la moitié du comté.
3. Beurrer les tranches côté extérieur. Côté intérieur : une fine couche de béchamel, jambon plié, une pincée de comté, refermer.
4. Sur le dessus : le reste de béchamel et de comté.
5. Plaque, four 8 à 10 min : le dessous dore au contact de la plaque, le dessus gratine en croûte.

Variante madame : un œuf au plat posé dessus à la sortie du four.

Erreurs fréquentes
- Une béchamel trop liquide : elle détrempe le pain. Elle doit tenir sur la cuillère.
- Le croque à la poêle avec la béchamel dessus : elle brûle. La béchamel dessus, c'est au four.""",
        "lien": "", "note": "",
    },
    {
        "id": "acc-gratin-dauphinois", "nom": "Gratin dauphinois", "genre": "accompagnement", "minutes": 90,
        "ingredients": ["pommes de terre", "crème fraîche", "lait", "ail", "beurre"],
        "recette": """Pour 4
- 1 kg de pommes de terre à chair farineuse (Bintje, Agria)
- 40 cl de lait entier, 30 cl de crème liquide entière
- 1 gousse d'ail, beurre, muscade, sel, poivre

1. Four à 160 °C. Frotter le plat à l'ail coupé en deux, puis le beurrer.
2. Éplucher les pommes de terre, les trancher en rondelles de 3 mm (à la mandoline), sans les laver : l'amidon fait la liaison.
3. Dans une grande casserole, lait, crème, ail écrasé, sel, poivre, muscade. Ajouter les rondelles et cuire 10 min à frémissement en remuant délicatement : la crème épaissit.
4. Verser dans le plat, égaliser. Four 1 h à 1 h 15 : le dessus est doré, la lame d'un couteau entre sans résistance.
5. Repos 10 min avant de servir.

Erreurs fréquentes
- Ajouter du fromage : c'est alors un gratin savoyard. Le dauphinois n'en a pas.
- Laver les tranches : sans leur amidon, la crème ne lie pas et le gratin rend du liquide.

Avec : rôti de bœuf, pièce du boucher, poulet rôti.""",
        "lien": "", "note": "",
    },
    {
        "id": "plat-poulet-roti", "nom": "Poulet rôti du dimanche", "genre": "plat", "minutes": 100,
        "ingredients": ["poulet fermier", "beurre", "citrons", "ail", "pommes de terre"],
        "recette": """Pour 4
- 1 poulet fermier de 1,6 à 1,8 kg (label rouge), sorti du frigo 1 h avant
- 60 g de beurre mou, 1 citron, 1 tête d'ail, thym
- 800 g de pommes grenaille, fleur de sel

1. Idéalement la veille : saler le poulet dedans et dehors et le laisser au frigo à découvert. La peau sèche, elle sera croustillante.
2. Four à 220 °C. Glisser une partie du beurre sous la peau des blancs, enduire le reste dessus. Dans le ventre : le citron coupé en deux, 3 gousses d'ail, le thym.
3. Plat : les grenailles coupées en deux, le reste de l'ail en chemise, un filet d'huile, sel. Le poulet posé sur une cuisse.
4. 20 min sur une cuisse, 20 min sur l'autre, puis 30 à 40 min sur le dos. Arroser avec le jus toutes les 15 min.
5. C'est cuit quand le jus qui coule de la cuisse piquée est clair (72-75 °C au cœur de la cuisse).
6. Repos 15 min, poulet tête en bas sur une planche (le jus redescend dans les blancs). Déglacer le plat avec 10 cl d'eau, gratter les sucs : c'est le jus.

Erreurs fréquentes
- Le découper à la sortie du four : le jus part sur la planche et les blancs sont secs.
- Le cuire sur le dos tout du long : les blancs sont cuits bien avant les cuisses.""",
        "lien": "", "note": "",
    },
    {
        "id": "plat-quiche-lorraine", "nom": "Quiche lorraine", "genre": "plat", "minutes": 75,
        "ingredients": ["farine", "beurre", "œufs", "crème fraîche", "lait", "guanciale ou pancetta"],
        "recette": """Moule de 24 cm, pour 4 à 6
Pâte brisée
- 200 g de farine, 100 g de beurre froid en dés, 1 jaune d'œuf, 4 c. à s. d'eau froide, 1 pincée de sel
Appareil
- 200 g de lardons fumés
- 3 œufs + 1 jaune, 20 cl de crème fraîche épaisse, 20 cl de lait entier, muscade, poivre

1. Pâte : sabler farine, sel et beurre du bout des doigts, ajouter jaune et eau, rassembler sans pétrir. 30 min au frais.
2. Four à 200 °C. Étaler, foncer le moule, piquer, 15 min au frais.
3. Cuire à blanc 15 min (papier cuisson et légumes secs dessus), puis 5 min sans, pour sécher le fond.
4. Lardons blanchis 1 min à l'eau bouillante, puis dorés à la poêle sans matière grasse.
5. Fouetter œufs, jaune, crème, lait, muscade, poivre ; peu de sel (les lardons salent).
6. Lardons sur le fond, appareil par-dessus. Four à 180 °C, 30 à 35 min : le centre tremble encore légèrement.
7. 10 min de repos avant de couper.

Erreurs fréquentes
- Ajouter du gruyère : la lorraine d'origine n'a pas de fromage (c'est voulu, la crème suffit).
- Sauter la cuisson à blanc : le fond reste détrempé.""",
        "lien": "", "note": "",
    },
]


# Les 20 matchs du Match des Recettes (28/10/2026) : oui de Julien et de Laetitia. Recette de leur base
# Mamma quand elle existe (recettes_mamma.json), sinon à rédiger quand ils la choisissent.
# (id, nom, genre, minutes, ingrédients — vides tant que la recette n'est pas écrite)
_MATCHS = [
    ("tester-pesto", "Trofie al pesto genovese", "plat", 35,
     ["trofie", "basilic", "pignons", "ail", "parmesan", "pecorino", "huile d'olive", "pommes de terre", "haricots verts"]),
    ("tester-polpette", "Polpette al sugo", "plat", 80,
     ["bœuf haché", "salsiccia", "pain", "œufs", "parmesan", "persil", "ail", "passata", "oignons", "basilic"]),
    ("tester-osso-buco", "Osso buco et gremolata", "plat", 140,
     ["osso buco de veau", "oignons", "farine", "beurre", "vin blanc", "bouillon", "persil", "ail", "citrons"]),
    ("tester-focaccia", "Focaccia genovese", "entree", 180, []),
    ("tester-meurette", "Œufs en meurette", "plat", 40, []),
    ("tester-moules", "Moules marinières frites", "plat", 30, []),
    ("tester-soupe-oignon", "Soupe à l'oignon gratinée", "plat", 60, []),
    ("tester-bo-bun", "Bò bún", "plat", 40, []),
    ("tester-nems", "Nems maison", "entree", 60, []),
    ("tester-banh-mi", "Bánh mì au porc caramélisé", "plat", 30, []),
    ("tester-shakshuka", "Shakshuka", "plat", 25, []),
    ("tester-chana-masala", "Curry de pois chiches", "plat", 35, []),
    ("tester-quesadillas", "Quesadillas comté-chorizo", "plat", 15, []),
    ("tester-chili", "Chili con carne", "plat", 90, []),
    ("tester-okonomiyaki", "Okonomiyaki", "plat", 30, []),
    ("tester-poke", "Poke bowl au saumon", "plat", 25, []),
    ("tester-mousse", "Mousse au chocolat", "dessert", 20, []),
    ("tester-cookies", "Cookies au beurre noisette", "dessert", 30, []),
    ("tester-fondant", "Fondant au chocolat", "dessert", 25, []),
    ("tester-pancakes", "Pancakes du dimanche", "dessert", 25, []),
]
A_TESTER = [
    {"id": id_, "nom": nom, "genre": genre, "minutes": minutes, "ingredients": ingredients,
     "recette": _MAMMA[id_]["recette"], "lien": _MAMMA[id_]["source"], "note": ""}
    if ingredients else      # les 3 matchs Mamma ; les autres : recettes_a_tester.py
    {"id": id_, "nom": nom, "genre": genre, "lien": "", **RECETTES_A_TESTER[id_]}
    for id_, nom, genre, minutes, ingredients in _MATCHS
]
