"""Le carnet de départ de Casa Binomerie : les 19 recettes de Julien et Laetitia (liste du 28/10/2026).

Recettes pré-rédigées par Claude, à corriger par eux dans l'app. Pâtes : à l'italienne, sans
compromis (pas de crème dans la carbonara, pas d'oignon dans l'amatriciana). Les ingrédients
reprennent les noms du placard (courses.PLACARD_DEPART) : c'est ce qui permet le secours
(plat ≤ 20 min dont tout est au placard) et l'ajout aux courses. Sel, poivre et huile : sous-entendus.
Injecté en base à la livraison 3 (Dîners).
"""

CARNET_DEPART = [
    # --- Plats ---------------------------------------------------------------------------------
    {
        "id": "plat-carbonara", "nom": "Spaghetti alla carbonara", "genre": "plat", "minutes": 15,
        "ingredients": ["spaghetti", "guanciale ou pancetta", "œufs", "pecorino"],
        "recette": """Pour 2
- 200 g de spaghetti (ou rigatoni)
- 120 g de guanciale (à défaut, pancetta), en bâtonnets épais
- 3 jaunes d'œufs + 1 œuf entier
- 50 g de Pecorino Romano DOP râpé fin
- poivre noir concassé au moulin, généreusement

1. Mettre l'eau à bouillir, salée moins que d'habitude (le guanciale et le pecorino le sont déjà).
2. Guanciale dans une grande poêle froide, sans matière grasse. Feu moyen, 8 à 10 min : il dore et rend son gras. Couper le feu.
3. Dans un bol, battre jaunes, œuf entier, pecorino et beaucoup de poivre jusqu'à une crème épaisse.
4. Cuire les pâtes 1 min de moins que le paquet. Garder une louche d'eau de cuisson avant d'égoutter.
5. Pâtes dans la poêle du guanciale, hors du feu. Mélanger 30 s pour les enrober de gras, laisser tiédir encore 30 s.
6. Verser la crème d'œufs et 2 c. à s. d'eau de cuisson, mélanger vivement : la sauce devient crémeuse et nappante. Trop épaisse : un peu d'eau ; trop liquide : 10 s sur feu très doux sans cesser de remuer.
7. Servir tout de suite, pecorino et poivre par-dessus.

Secret de mamma : la poêle hors du feu. C'est l'eau de cuisson et le mouvement qui font la crème.

Erreurs fréquentes
- Mettre de la crème (ou de l'ail, de l'oignon) : ce n'est plus une carbonara.
- Verser les œufs sur le feu : ils brouillent au lieu de napper.""",
        "note": "",
    },
    {
        "id": "plat-amatriciana", "nom": "Spaghetti all'amatriciana", "genre": "plat", "minutes": 25,
        "ingredients": ["spaghetti", "guanciale ou pancetta", "tomates pelées", "pecorino"],
        "recette": """Pour 2
- 200 g de spaghetti (ou bucatini, la version d'Amatrice)
- 120 g de guanciale en lardons épais
- 400 g de tomates pelées (San Marzano si possible), écrasées à la main
- 40 g de Pecorino Romano DOP râpé
- 1 trait de vin blanc sec (facultatif), 1 pointe de piment (facultatif)

1. Guanciale dans une sauteuse froide, feu moyen, 8 min jusqu'à ce qu'il soit doré et translucide. Retirer la moitié des morceaux les plus croustillants et réserver.
2. Déglacer au vin blanc, laisser évaporer. Ajouter le piment.
3. Ajouter les tomates, saler à peine. Mijoter 12 à 15 min à petit feu : la sauce épaissit et le gras remonte en surface.
4. Cuire les pâtes 1 min de moins que le paquet, les finir 1 min dans la sauce avec une demi-louche d'eau de cuisson.
5. Hors du feu, ajouter la moitié du pecorino et mélanger. Servir avec le guanciale réservé et le reste du pecorino.

Secret de mamma : finir les pâtes dans la sauce avec l'eau de cuisson, le pecorino hors du feu seulement.

Erreurs fréquentes
- Ajouter oignon ou ail : la recette d'Amatrice tient en guanciale, tomate, pecorino.
- Remplacer le guanciale par des lardons fumés : le goût fumé écrase tout.""",
        "note": "",
    },
    {
        "id": "plat-lasagne-bolognese", "nom": "Lasagne alla bolognese", "genre": "plat", "minutes": 180,
        "ingredients": ["farine", "œufs", "bœuf haché", "guanciale ou pancetta", "carottes", "céleri", "oignons",
                        "passata", "lait", "beurre", "parmesan"],
        "recette": """Pour 6 (ça se congèle très bien)

Le ragù (à lancer en premier)
- 400 g de bœuf haché (paleron), 150 g de pancetta hachée au couteau
- 1 carotte, 1 branche de céleri, 1/2 oignon, hachés très fin
- 15 cl de vin blanc sec, 200 g de passata, 25 cl de lait entier, un peu d'eau ou de bouillon
1. Faire suer le hachis de légumes 10 min à feu doux dans 30 g de beurre et un filet d'huile, sans coloration.
2. Ajouter la pancetta, puis le bœuf : feu vif, émietter, laisser grésiller jusqu'à ce que toute l'eau soit partie et que la viande colore.
3. Vin blanc, laisser évaporer. Passata, puis le lait.
4. Mijoter à couvert, à frémissement à peine visible, au moins 2 h. Mouiller d'un peu d'eau si ça attache. Saler en fin.

Les pâtes, à la bolognaise
- 300 g de farine (type 00 si possible), 3 œufs
5. Fontaine, œufs au centre, pétrir 10 min jusqu'à une pâte lisse et souple. Filmer, 30 min de repos.
6. Abaisser très fin (au rouleau ou au laminoir, avant-dernier cran), détailler à la taille du plat. Plonger 20 s dans l'eau bouillante salée, puis dans l'eau froide, égoutter sur un torchon.
Dépannage : feuilles de lasagne sèches, à blanchir de la même façon.

La béchamel
- 50 g de beurre, 50 g de farine, 75 cl de lait, muscade
7. Roux beurre-farine 2 min, lait froid d'un coup, fouetter jusqu'à ébullition, 5 min à feu doux. Sel, muscade.

Montage et cuisson
8. Plat beurré : une fine couche de béchamel, puis feuilles, ragù, béchamel, Parmigiano Reggiano DOP râpé. 5 à 6 étages ; finir par béchamel, parmesan et quelques noisettes de beurre.
9. Four à 180 °C, 30 à 35 min, jusqu'à ce que le dessus gratine. Laisser reposer 15 min avant de couper.

Secret de mamma : le lait dans le ragù, il adoucit l'acidité de la tomate et attendrit la viande.

Erreurs fréquentes
- Écourter le ragù : en dessous de 2 h de mijotage doux, c'est une sauce à la viande, pas un ragù.
- Noyer de tomate : à Bologne, le ragù est une sauce de viande à peine rosée.""",
        "note": "Se prépare la veille : encore meilleure réchauffée.",
    },
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
        "note": "",
    },
]
