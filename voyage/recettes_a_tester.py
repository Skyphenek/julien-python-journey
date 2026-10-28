"""Les recettes des matchs « à tester » qui n'en avaient pas (28/10/2026).

Le bánh mì vient de leur base Mamma (texte d'origine, lien vers la source) ; le bò bún en reprend
la base (bún bò xào sả, même source) sans le twist thaï. Les autres sont rédigées par Claude
d'après les versions de référence de chaque plat, à corriger par eux dans l'app.
Mêmes conventions que carnet_depart.py : noms d'ingrédients du placard, sel, poivre et huile sous-entendus.
"""

import json
from pathlib import Path

_MAMMA = json.loads((Path(__file__).parent / "recettes_mamma.json").read_text())

RECETTES_A_TESTER = {
    "tester-focaccia": {
        "minutes": 180,
        "ingredients": ["farine", "levure boulangère", "huile d'olive", "sel", "fleur de sel", "sucre"],
        "recette": """Pour une plaque de 30 × 40 cm
- 500 g de farine T65 (ou T55), 350 g d'eau tiède, 10 g de sel, 5 g de levure boulangère sèche (ou 12 g fraîche), 1 c. à c. de sucre
- 40 g d'huile d'olive dans la pâte + 40 g pour la plaque
- Saumure : 50 g d'eau, 50 g d'huile d'olive, 1 c. à c. de sel ; fleur de sel

1. Délayer levure et sucre dans l'eau. Ajouter la farine, mélanger, puis le sel et 40 g d'huile. Pétrir 8-10 min : la pâte est collante, c'est normal.
2. Pousse 1 h 30 à couvert, jusqu'à doubler. (Mieux : une nuit au frigo, la mie gagne en goût et en alvéoles.)
3. Huiler généreusement la plaque, y verser la pâte, l'étirer du bout des doigts. Si elle se rétracte, attendre 10 min et recommencer.
4. Deuxième pousse 45 min à 1 h.
5. Four à 230 °C. Fouetter la saumure, la verser sur la pâte puis enfoncer les doigts bien droits jusqu'au fond pour former les trous : la saumure s'y loge, c'est le secret de la genovese.
6. Fleur de sel, 20 min de cuisson en bas du four, jusqu'à dorure. Un filet d'huile à la sortie.""",
        "note": "Le dessous doit frire dans l'huile : ne pas en économiser sur la plaque.",
    },
    "tester-meurette": {
        "minutes": 40,
        "ingredients": ["œufs", "vin rouge", "lardons", "échalotes", "champignons de Paris", "beurre", "farine",
                        "pain de campagne", "ail"],
        "recette": """Pour 2
- 4 œufs très frais
- 50 cl de vin rouge de Bourgogne (pinot noir), 25 cl de bouillon de volaille
- 100 g de lardons, 2 échalotes, 150 g de champignons de Paris, 1 brin de thym, 1 feuille de laurier
- 40 g de beurre, 1 c. à s. de farine (beurre manié)
- 4 tranches de pain de campagne, 1 gousse d'ail

1. Faire revenir les lardons à sec, réserver. Dans la même casserole, fondre les échalotes ciselées.
2. Verser vin et bouillon, thym, laurier. Réduire de moitié à feu vif (15-20 min).
3. Pendant ce temps : champignons en quartiers sautés au beurre ; pain grillé puis frotté d'ail.
4. Baisser à frémissement, pocher les œufs dans la sauce 3 min (casser chaque œuf dans une tasse et le glisser). Les sortir à l'écumoire.
5. Filtrer la sauce, la lier hors du feu avec le beurre manié (20 g de beurre mou + 1 c. à s. de farine écrasés ensemble) en fouettant, puis remettre 1 min sur le feu. Elle doit napper la cuillère.
6. Pain au fond de l'assiette, 2 œufs dessus, lardons et champignons, napper de sauce.""",
        "note": "",
    },
    "tester-moules": {
        "minutes": 30,
        "ingredients": ["moules", "échalotes", "ail", "vin blanc", "beurre", "persil", "crème fraîche",
                        "pommes de terre"],
        "recette": """Pour 2
- 1,5 kg de moules de bouchot
- 2 échalotes, 1 gousse d'ail, 30 g de beurre, 20 cl de vin blanc sec (muscadet), 1 bouquet de persil plat
- 2 c. à s. de crème fraîche (facultatif, version normande)
- Frites : 800 g de pommes de terre bintje, huile de friture

Frites (double cuisson, c'est elle qui fait le croustillant)
1. Pommes de terre en bâtonnets de 1 cm, rincées et bien séchées dans un torchon.
2. Première cuisson à 150 °C, 6-7 min : elles cuisent sans colorer. Égoutter, laisser reposer au moins 10 min.
3. Seconde cuisson à 180 °C juste avant de servir, 2-3 min jusqu'à dorure. Sel immédiatement.

Moules
4. Gratter et rincer les moules ; jeter celles qui restent ouvertes après une pichenette.
5. Dans un grand faitout : beurre, échalotes et ail hachés 2 min. Vin blanc, porter à ébullition.
6. Moules, couvercle, feu vif 4-5 min en secouant 2 fois. Dès qu'elles sont ouvertes, c'est fini.
7. Hors du feu : persil haché (et crème). Servir dans le faitout, frites à côté, pain pour le jus.""",
        "note": "Lancer la seconde cuisson des frites au moment où les moules vont sur le feu.",
    },
    "tester-soupe-oignon": {
        "minutes": 75,
        "ingredients": ["oignons", "beurre", "farine", "vin blanc", "bouillon", "pain de campagne", "comté"],
        "recette": """Pour 2 (bols allant au four)
- 600 g d'oignons jaunes, 40 g de beurre, 1 c. à s. de farine
- 10 cl de vin blanc sec, 80 cl de bouillon de bœuf (maison ou un bon cube), 1 feuille de laurier, 1 brin de thym
- 4 tranches de pain de campagne rassis, 120 g de comté râpé

1. Émincer finement les oignons. Les faire fondre au beurre dans une cocotte, feu moyen-doux, 40 min en remuant de temps en temps : ils doivent devenir brun acajou, pas brûlés. C'est toute la recette, ne pas raccourcir.
2. Saupoudrer de farine, remuer 1 min. Déglacer au vin blanc en grattant le fond.
3. Bouillon, thym, laurier, 20 min de frémissement. Sel, poivre.
4. Griller le pain. Remplir les bols, poser le pain dessus, couvrir généreusement de comté.
5. Sous le gril du four 5-8 min jusqu'à ce que le fromage bulle et dore.""",
        "note": "Plus de goût encore : un trait de cognac ou de porto au moment de déglacer.",
    },
    "tester-bo-bun": {
        "minutes": 40,
        "ingredients": ["vermicelles de riz", "bœuf", "citronnelle", "ail", "sauce poisson", "sucre",
                        "citrons verts", "salade", "concombre", "carottes", "pousses de soja", "menthe",
                        "coriandre", "cacahuètes", "oignons frits", "nems"],
        "recette": """Pour 2
- 150 g de vermicelles de riz (bún)
- 300 g de bœuf (rumsteck ou faux-filet) tranché très fin, 2 tiges de citronnelle, 2 gousses d'ail, 1 oignon
- Marinade : 1 c. à s. de sauce poisson, 1 c. à s. de sucre, 1 c. à s. d'huile
- Garniture : salade, 1/2 concombre et 1 carotte en julienne, 1 poignée de pousses de soja, menthe, coriandre, 40 g de cacahuètes grillées concassées, oignons frits, 4 petits nems (voir « Nems maison », ou achetés)
- Nước chấm : 3 c. à s. de sauce poisson, 2 c. à s. de sucre, 6 c. à s. d'eau, le jus d'1 citron vert, 1 gousse d'ail, 1 piment

1. Nước chấm : dissoudre le sucre dans l'eau tiède, ajouter sauce poisson, citron, ail et piment hachés. Goûter : salé, sucré, acide à parts égales.
2. Mariner le bœuf avec la citronnelle hachée très fin (partie blanche), l'ail et la marinade : 15 min minimum.
3. Vermicelles 3-5 min à l'eau bouillante, rincer à l'eau froide, bien égoutter.
4. Préparer les bols : salade, crudités, soja, herbes, puis vermicelles.
5. Wok très chaud, oignon émincé 30 s, puis le bœuf en une seule couche (en 2 fois si besoin) : 1 min 30 en tout. Une poêle pas assez chaude fait bouillir la viande.
6. Bœuf chaud et nems coupés sur les bols, cacahuètes, oignons frits. Le nước chấm s'ajoute à table, jamais à l'avance.""",
        "lien": "https://iamafoodblog.com/a-very-authentic-countryside-bun-bo-xa-ot-vietnamese-lemongrass-beef-recipe/",
        "note": "D'après la base Mamma (bún bò xào sả), sans le twist thaï.",
    },
    "tester-nems": {
        "minutes": 60,
        "ingredients": ["galettes de riz", "porc haché", "crevettes", "vermicelles de riz", "champignons noirs",
                        "carottes", "oignons", "œufs", "sauce poisson", "salade", "menthe"],
        "recette": """Pour 20 nems
- 20 galettes de riz (16 cm)
- 300 g de porc haché, 150 g de crevettes décortiquées hachées
- 30 g de vermicelles de riz et 10 g de champignons noirs séchés, réhydratés 20 min et coupés aux ciseaux
- 1 carotte râpée fin, 1 petit oignon haché, 1 œuf, 1 c. à s. de sauce poisson, poivre
- Salade, menthe, nước chấm (voir bò bún) pour servir

1. Farce : tout mélanger à la main. Elle doit être sèche : presser la carotte si elle rend de l'eau.
2. Tremper une galette 2 secondes dans l'eau tiède, la poser sur un torchon humide. Elle finit de ramollir toute seule.
3. 1 c. à s. de farce en boudin sur le bas, rabattre le bas, les côtés, rouler serré.
4. Le secret du croustillant : les mettre dans l'huile encore froide (ou à peine tiède), puis chauffer à feu moyen. 15-20 min en les retournant, sans qu'ils se touchent au début.
5. Égoutter sur du papier. Se mangent roulés dans une feuille de salade avec de la menthe, trempés dans le nước chấm.""",
        "note": "Se congèlent crus sur une plaque, puis en sac : frire directement sans décongeler.",
    },
    "tester-banh-mi": {
        "minutes": 60,
        "ingredients": ["porc", "citronnelle", "ail", "sauce poisson", "sauce huître", "miel", "cinq-épices",
                        "baguettes", "concombre", "coriandre", "mayonnaise", "carottes", "radis blanc",
                        "vinaigre de riz", "sucre"],
        "recette": _MAMMA["tester-banh-mi"]["recette"],
        "lien": _MAMMA["tester-banh-mi"]["source"],
        "note": "Base Mamma : le porc caramélise au miel (twist thaï 5-épices).",
    },
    "tester-shakshuka": {
        "minutes": 25,
        "ingredients": ["tomates pelées", "poivrons rouges", "oignons", "ail", "cumin", "paprika fumé",
                        "œufs", "feta", "coriandre", "pain"],
        "recette": """Pour 2
- 1 boîte de 400 g de tomates pelées, 1 poivron rouge, 1 oignon, 2 gousses d'ail
- 1 c. à c. de cumin, 1 c. à c. de paprika fumé, 1 pincée de piment (ou 1 c. à c. de harissa)
- 4 œufs, 60 g de feta, coriandre ou persil
- Pain pour saucer

1. Dans une poêle large avec couvercle : oignon et poivron émincés 8-10 min à feu moyen, jusqu'à ce qu'ils soient bien fondants.
2. Ail, cumin, paprika, piment : 1 min.
3. Tomates écrasées à la main, sel, 1 pincée de sucre. 10 min de mijotage : la sauce doit être épaisse, sinon les œufs se noient.
4. Creuser 4 puits, y casser les œufs, saler les blancs. Couvrir, feu doux 5-7 min : blancs pris, jaunes coulants.
5. Feta émiettée, herbes, poivre. Servir dans la poêle.""",
        "note": "Dîner de secours possible : tout est au placard sauf poivron, feta et herbes.",
    },
    "tester-chana-masala": {
        "minutes": 35,
        "ingredients": ["pois chiches", "oignons", "ail", "gingembre", "tomates pelées", "garam masala", "cumin",
                        "curcuma", "lait de coco", "citrons", "coriandre", "riz basmati"],
        "recette": """Pour 2
- 1 grande boîte de pois chiches (400 g égouttés)
- 1 gros oignon, 3 gousses d'ail, 1 morceau de gingembre (3 cm), 1 piment vert
- 1 c. à c. de graines de cumin, 1 c. à c. de garam masala, 1/2 c. à c. de curcuma, 1 c. à c. de paprika
- 200 g de tomates pelées, 10 cl de lait de coco (facultatif, plus doux)
- 1/2 citron, coriandre ; riz basmati

1. Huile chaude, graines de cumin 30 s jusqu'à ce qu'elles crépitent.
2. Oignon haché fin, 10-12 min à feu moyen : il doit être bien doré, c'est la base du goût.
3. Ail, gingembre râpé, piment : 1 min. Épices moulues : 30 s sans brûler.
4. Tomates écrasées, cuire 5 min jusqu'à ce que l'huile perle sur les bords.
5. Pois chiches + 15 cl d'eau, 10 min. Écraser une louche de pois chiches contre la paroi pour épaissir la sauce. Lait de coco si on veut.
6. Jus de citron, sel, coriandre. Avec le riz basmati.""",
        "note": "",
    },
    "tester-quesadillas": {
        "minutes": 15,
        "ingredients": ["tortillas", "comté", "chorizo", "oignons rouges", "coriandre", "crème fraîche",
                        "citrons verts"],
        "recette": """Pour 2
- 4 tortillas de blé
- 150 g de comté râpé (un comté jeune fond mieux), 80 g de chorizo en fines tranches puis en bâtonnets
- 1/2 oignon rouge très finement émincé, coriandre
- Pour tremper : crème fraîche citronnée (2 c. à s. + un filet de citron vert)

1. Faire suer le chorizo 2 min à sec dans la poêle, réserver. Garder le gras orange : il colorera les tortillas.
2. Sur une moitié de chaque tortilla : comté, chorizo, quelques lamelles d'oignon, coriandre. Plier en deux.
3. Poêle à feu moyen (pas plus, sinon l'extérieur brûle avant que le fromage fonde), 2-3 min par face en appuyant avec une spatule.
4. Couper en triangles, servir avec la crème citronnée.""",
        "note": "Version secours : comté + jambon, tout est au placard.",
    },
    "tester-chili": {
        "minutes": 120,
        "ingredients": ["bœuf haché", "haricots rouges", "tomates pelées", "oignons", "ail", "poivrons rouges",
                        "cumin", "paprika fumé", "piment", "chocolat noir", "bouillon", "riz", "crème fraîche"],
        "recette": """Pour 4 (ça se garde 3 jours et se congèle)
- 600 g de bœuf haché 15 % (ou 800 g de paleron en petits dés, encore meilleur)
- 2 oignons, 4 gousses d'ail, 1 poivron rouge
- 2 c. à c. de cumin, 1 c. à s. de paprika fumé, 1 c. à c. d'origan, piment (chipotle ou de Cayenne) à doser
- 2 c. à s. de concentré de tomate, 1 boîte de 400 g de tomates pelées, 25 cl de bouillon de bœuf
- 1 boîte de haricots rouges, 15 g de chocolat noir
- Riz, crème fraîche, oignon nouveau, citron vert

1. Faire dorer la viande en 2 fois dans une cocotte très chaude, sans remuer pendant 3 min : il faut une croûte brune, pas de la viande grise. Réserver.
2. Oignons, poivron, 8 min. Ail, épices et concentré de tomate : 2 min, ça doit sentir fort.
3. Remettre la viande, tomates écrasées, bouillon. Couvrir et mijoter 1 h 30 à feu très doux.
4. Haricots rincés et chocolat les 20 dernières minutes. Rectifier sel et piment.
5. Servir sur le riz, crème, oignon nouveau ciselé, un quartier de citron vert.""",
        "note": "Meilleur réchauffé le lendemain.",
    },
    "tester-okonomiyaki": {
        "minutes": 30,
        "ingredients": ["chou blanc", "farine", "œufs", "bacon", "oignons nouveaux", "mayonnaise",
                        "sauce okonomiyaki", "bonite séchée"],
        "recette": """Pour 2 (2 galettes)
- 1/4 de chou blanc (300 g) finement émincé
- 100 g de farine, 10 cl de bouillon dashi (ou d'eau), 2 œufs, 1 pincée de sel
- 6 tranches de bacon fines, 2 oignons nouveaux
- Garnitures : sauce okonomiyaki (ou 2 c. à s. de ketchup + 1 c. à s. de sauce Worcestershire + 1 c. à c. de sauce soja + 1 c. à c. de miel), mayonnaise (Kewpie idéalement), bonite séchée et algue aonori si on en trouve

1. Fouetter farine et dashi, ajouter les œufs. Incorporer le chou et les oignons nouveaux : il doit y avoir plus de chou que de pâte.
2. Poêle huilée à feu moyen, verser la moitié de la pâte en galette épaisse (2 cm). Poser 3 tranches de bacon dessus.
3. 5 min, retourner (à l'aide d'une assiette), 5 min côté bacon, retourner encore 2 min. L'intérieur doit être pris.
4. Napper de sauce, zébrer de mayonnaise, bonite et aonori. La bonite « danse » sur la galette chaude.""",
        "note": "Courses d'épicerie japonaise (sauce, Kewpie, bonite) : elles se gardent des mois.",
    },
    "tester-poke": {
        "minutes": 25,
        "ingredients": ["saumon", "riz à sushi", "vinaigre de riz", "sauce soja", "huile de sésame", "avocats",
                        "concombre", "edamame", "mangue", "sésame", "oignons nouveaux"],
        "recette": """Pour 2
- 250 g de saumon extra-frais (qualité sashimi, demander au poissonnier), en cubes de 2 cm
- 150 g de riz à sushi, 2 c. à s. de vinaigre de riz, 1 c. à c. de sucre, 1/2 c. à c. de sel
- Marinade : 3 c. à s. de sauce soja, 1 c. à s. d'huile de sésame, 1 c. à c. de gingembre râpé, 1 oignon nouveau
- 1 avocat, 1/2 concombre, 1 poignée d'edamame, 1/2 mangue, sésame grillé
- Mayo épicée : 2 c. à s. de mayonnaise + 1 c. à c. de sriracha

1. Rincer le riz jusqu'à ce que l'eau soit claire, cuire (1 volume pour 1,2 d'eau, 12 min puis 10 min à couvert hors du feu). Assaisonner tiède avec vinaigre, sucre, sel.
2. Mariner le saumon 10 min maximum au frais (au-delà, la soja le « cuit »).
3. Tailler avocat, concombre, mangue.
4. Riz tiède au fond du bol, garnitures en quartiers, saumon au centre, sésame, oignon nouveau, mayo épicée.""",
        "note": "Saumon cru : l'acheter le jour même.",
    },
    "tester-mousse": {
        "minutes": 20,
        "ingredients": ["chocolat noir", "œufs", "sucre", "sel"],
        "recette": """Pour 4 (à faire au moins 4 h avant)
- 200 g de chocolat noir à 64-70 %
- 6 œufs à température ambiante, 30 g de sucre, 1 pincée de sel
- 20 g de beurre (facultatif, pour une texture plus soyeuse)

1. Fondre le chocolat (et le beurre) au bain-marie, sans dépasser 45 °C. Laisser tiédir.
2. Séparer les blancs des jaunes. Incorporer les jaunes un à un au chocolat tiède : il épaissit, c'est normal.
3. Monter les blancs avec le sel ; quand ils moussent, ajouter le sucre et monter en neige souple (bec d'oiseau, pas trop ferme : sinon ils font des grumeaux).
4. Mélanger un tiers des blancs vivement au chocolat pour l'assouplir, puis incorporer le reste en soulevant délicatement à la maryse.
5. Au frais 4 h minimum, une nuit c'est mieux.""",
        "note": "Œufs crus : très frais.",
    },
    "tester-cookies": {
        "minutes": 30,
        "ingredients": ["beurre", "sucre", "cassonade", "œufs", "farine", "levure chimique", "chocolat noir",
                        "fleur de sel"],
        "recette": """Pour 12 cookies
- 170 g de beurre, 150 g de cassonade (sucre brun), 50 g de sucre blanc
- 1 œuf + 1 jaune, 1 c. à c. d'extrait de vanille
- 250 g de farine, 1/2 c. à c. de bicarbonate (ou 1 c. à c. de levure chimique), 1/2 c. à c. de sel
- 200 g de chocolat noir haché au couteau (pas de pépites : les éclats fondent en flaques)
- Fleur de sel

1. Beurre noisette : fondre le beurre et le cuire à feu moyen en remuant, jusqu'à ce qu'il mousse, brunisse et sente la noisette (5-7 min). Le verser dans un bol avec les dépôts bruns, laisser tiédir 10 min.
2. Fouetter le beurre avec les sucres, puis l'œuf, le jaune et la vanille, 1 min : le mélange blanchit.
3. Incorporer farine, bicarbonate, sel, puis le chocolat.
4. Repos de la pâte 1 h au frigo minimum (24 h, c'est encore mieux : goût caramel).
5. Four 180 °C. Boules de 60 g bien espacées, 10-11 min : les bords dorés, le centre encore mou. Fleur de sel à la sortie.
6. Laisser 10 min sur la plaque : ils finissent de cuire.""",
        "note": "",
    },
    "tester-fondant": {
        "minutes": 25,
        "ingredients": ["chocolat noir", "beurre", "œufs", "sucre", "farine"],
        "recette": """Pour 4 fondants coulants (ou 1 moule de 20 cm)
- 125 g de chocolat noir à 70 %, 100 g de beurre (+ pour les moules)
- 3 œufs, 80 g de sucre, 30 g de farine, 1 pincée de sel

1. Four 200 °C. Beurrer et fariner (ou cacaoter) 4 ramequins.
2. Fondre chocolat et beurre, lisser.
3. Fouetter œufs, sucre et sel jusqu'à ce que le mélange blanchisse et double (3 min).
4. Verser le chocolat, mélanger, puis la farine tamisée sans trop travailler.
5. Remplir les ramequins aux 3/4. Cuisson 9-10 min : le dessus est pris, le centre tremble. (Grand moule : 180 °C, 20-22 min.)
6. Attendre 1 min, démouler sur l'assiette.""",
        "note": "Se prépare à l'avance : ramequins garnis au frigo, ajouter 2 min de cuisson.",
    },
    "tester-pancakes": {
        "minutes": 25,
        "ingredients": ["farine", "levure chimique", "sucre", "œufs", "lait", "beurre", "sirop d'érable"],
        "recette": """Pour 2 (8 pancakes)
- 200 g de farine, 2 c. à c. de levure chimique, 1 c. à s. de sucre, 1 pincée de sel
- 2 œufs, 25 cl de lait (ou lait ribot pour plus de moelleux), 30 g de beurre fondu
- Sirop d'érable, beurre, fruits

1. Mélanger les ingrédients secs dans un bol, les liquides dans un autre.
2. Verser les liquides sur les secs, mélanger juste à la fourchette : il doit rester des grumeaux. Trop fouetter = pancakes plats et caoutchouteux.
3. Laisser reposer 10 min : la levure travaille, la pâte épaissit.
4. Poêle à feu moyen à peine beurrée (essuyer au papier). Une louche par pancake.
5. Retourner quand des bulles crèvent à la surface et que les bords sont mats (2 min), 1 min de l'autre côté.
6. Empiler, beurre, sirop d'érable.""",
        "note": "",
    },
}
