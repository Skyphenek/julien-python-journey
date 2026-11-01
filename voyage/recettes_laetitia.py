"""Rien que pour Laetitia (01/11/2026) : ce qu'elle a voté oui et Julien non, ou « bof » (il goûte).

- Match des Recettes : goi cuon, croziflette, hachis parmentier, vitello tonnato (Julien : non).
- Légumes Démasqués : velouté potimarron, panais rôtis, coleslaw, carottes râpées (Julien : bof) ;
  endives, noix et comté (Julien : non). Les carottes rôties, déjà au carnet à tester, restent pour nous deux.
Ses « jamais » restent dehors (anchois du vitello tonnato remplacés par des câpres).
Rédigées par Claude d'après les versions de référence, à corriger dans l'app.
Mêmes conventions que carnet_depart.py : noms d'ingrédients du catalogue, sel, poivre et huile sous-entendus.
Ajoutées une seule fois (table reprises), pour = 'laetitia', statut à tester.
"""

NOM_REPRISE = "pour-laetitia"


def _laet(id_, nom, genre, minutes, ingredients, recette, note=""):
    return {"id": "laet-" + id_, "nom": nom, "genre": genre, "minutes": minutes, "ingredients": ingredients,
            "recette": recette, "lien": "", "note": note, "pour": "laetitia"}


LAETITIA = [
    _laet("goi-cuon", "Goi cuon, rouleaux de printemps", "plat", 40,
          ["feuilles de riz", "crevettes", "vermicelles de riz", "laitue", "menthe", "coriandre", "carottes",
           "sauce hoisin", "cacahuètes", "sauce poisson", "citrons verts", "sucre", "ail"],
          """Pour 2 (8 rouleaux)
- 8 galettes de riz, 16 crevettes cuites décortiquées coupées en deux dans l'épaisseur
- 100 g de vermicelles de riz, 4 feuilles de laitue, 1 carotte râpée, menthe et coriandre
- sauce cacahuète : 3 c. à s. de sauce hoisin, 1 c. à s. de beurre de cacahuète ou de cacahuètes mixées, 3 c. à s. d'eau chaude
- ou nuoc-mâm : 2 c. à s. de sauce poisson, 1 c. à s. de sucre, 1 citron vert, 4 c. à s. d'eau, 1/2 gousse d'ail

1. Vermicelles 3 min dans l'eau bouillante, rincés à l'eau froide, égouttés.
2. Galette trempée 5 secondes dans l'eau tiède : elle doit rester un peu ferme, elle s'assouplit sur la planche.
3. Au tiers bas : laitue, vermicelles, carotte, herbes. Replier le bas, puis les côtés.
4. Trois demi-crevettes côté rose contre la galette, et rouler serré jusqu'au bout.
5. Sous un torchon humide jusqu'au service. Sauces à côté.""",
          "Un « oui » de Laetitia au Match des Recettes ; et une révision avant le Vietnam."),

    _laet("croziflette", "Croziflette", "plat", 45,
          ["crozets", "reblochon", "lardons", "oignons", "vin blanc", "crème fraîche"],
          """Pour 2
- 200 g de crozets (pâtes de Savoie au sarrasin)
- 1/2 reblochon, 150 g de lardons, 1 oignon, 5 cl de vin blanc, 10 cl de crème fraîche

1. Crozets 15 à 20 min dans l'eau bouillante salée (ils sont longs à cuire), égouttés.
2. Lardons dorés à sec, oignon émincé, 5 min. Vin blanc, 1 min.
3. Mélanger crozets, lardons et crème dans un plat.
4. Reblochon coupé en deux dans l'épaisseur, croûte dessus. 15 min à 200 °C : il coule et gratine.""",
          "La tartiflette en pâtes : la saison commence."),

    _laet("hachis-parmentier", "Hachis parmentier carottes-bœuf", "plat", 60,
          ["bœuf haché", "carottes", "oignons", "concentré de tomate", "thym", "bouillon de volaille", "pommes de terre",
           "lait", "beurre", "noix de muscade", "gruyère"],
          """Pour 4 (deux dîners)
- 500 g de bœuf haché, 2 carottes râpées, 1 oignon, 1 c. à s. de concentré de tomate, thym, 10 cl de bouillon
- purée : 1 kg de pommes de terre, 20 cl de lait chaud, 50 g de beurre, muscade
- 50 g de gruyère râpé

1. Purée : pommes de terre à l'eau, écrasées avec le lait et le beurre, muscade, sel.
2. Oignon fondu, puis le bœuf à feu vif, 5 min. Carottes râpées, concentré, thym, bouillon : 10 min, les carottes fondent dans la viande.
3. Viande au fond du plat, purée dessus, rayée à la fourchette, gruyère.
4. 20 min à 200 °C, 3 min de gril pour la croûte.""",
          "Un « oui » de Laetitia aux deux jeux (le parmentier et ses carottes fondues)."),

    _laet("vitello-tonnato", "Vitello tonnato", "plat", 30,
          ["rôti de veau", "thon", "mayonnaise", "câpres", "citrons", "vin blanc"],
          """Pour 2
- 300 g de rôti de veau cuit, froid (du boucher ou un reste de rôti)
- sauce : 1 boîte de thon au naturel (140 g), 3 c. à s. de mayonnaise, 1 c. à s. de câpres, 1/2 citron, 2 c. à s. de vin blanc
- câpres pour le service

1. Mixer thon, mayonnaise, câpres, jus de citron et vin blanc : une sauce lisse et nappante (un peu d'eau si trop épaisse).
2. Trancher le veau très finement, en rosace dans un plat.
3. Napper de sauce, câpres par-dessus. Au frais 1 h si possible : la viande s'imprègne.""",
          "Sans anchois (un « jamais » de Laetitia) : les câpres donnent le salé."),

    _laet("veloute-potimarron", "Velouté potimarron-châtaigne", "plat", 35,
          ["potimarron", "châtaignes", "oignons", "bouillon de volaille", "crème fraîche", "lardons", "beurre"],
          """Pour 2, plus 2 parts à congeler
- 1 potimarron (1 kg), la peau se mange : seulement épépiné et coupé en cubes
- 150 g de châtaignes cuites, 1 oignon, 80 cl de bouillon, 2 c. à s. de crème, 80 g de lardons, une noix de beurre

1. Oignon fondu au beurre, 5 min. Potimarron et châtaignes (en garder quelques-unes), bouillon : 25 min.
2. Mixer très lisse, crème, sel.
3. Lardons et châtaignes émiettées grillés à sec, par-dessus.""",
          "Julien : bof. Le velouté de Laetitia."),

    _laet("panais-rotis", "Panais rôtis au parmesan (air fryer)", "accompagnement", 25,
          ["panais", "parmesan", "huile d'olive", "thym"],
          """Pour 2
- 500 g de panais, épluchés, en bâtonnets comme des frites
- 1 c. à s. d'huile d'olive, thym, sel, 30 g de parmesan râpé

1. Mélanger panais, huile, thym et sel.
2. AIR FRY, 190 °C, 15 min en secouant à mi-cuisson.
3. Parmesan par-dessus, encore 3 à 4 min : il croustille et dore.""",
          "Comme des frites, en plus sucré."),

    _laet("coleslaw", "Coleslaw", "accompagnement", 15,
          ["chou blanc", "carottes", "mayonnaise", "moutarde", "vinaigre de cidre", "sucre"],
          """Pour 2 à 4
- 1/4 de chou blanc très finement émincé, 2 carottes râpées
- sauce : 4 c. à s. de mayonnaise, 1 c. à c. de moutarde, 1 c. à s. de vinaigre de cidre, 1 c. à c. de sucre

1. Chou émincé avec une pincée de sel, 10 min : il rend un peu d'eau, l'essorer à la main.
2. Mélanger la sauce, puis chou et carottes.
3. 30 min au frais : meilleur. Avec un burger, du poulet frit, des tenders.""",
          "Julien : bof. Pour accompagner les burgers et les tenders."),

    _laet("carottes-rapees", "Carottes râpées au citron", "entree", 10,
          ["carottes", "citrons", "huile d'olive", "sucre", "persil"],
          """Pour 2
- 4 carottes, 1 citron, 2 c. à s. d'huile d'olive, 1 pincée de sucre, persil

1. Râper les carottes fin (la grille fine change tout).
2. Jus de citron, huile, sucre, sel : mélanger.
3. 15 min au frais avant de servir, persil.""",
          "Le classique de bistrot ; Julien : bof."),

    _laet("salade-endives", "Endives, noix et comté", "entree", 10,
          ["endives", "noix", "comté", "moutarde", "vinaigre de xérès", "huile d'olive"],
          """Pour 2
- 3 endives, une poignée de cerneaux de noix, 80 g de comté en dés
- vinaigrette : 1 c. à c. de moutarde, 1 c. à s. de vinaigre de xérès, 3 c. à s. d'huile (de noix si possible)

1. Endives en tronçons, sans le cœur amer à la base.
2. Noix grillées 2 min à sec.
3. Tout mélanger avec la vinaigrette au dernier moment.""",
          "Julien : non. L'entrée d'hiver de Laetitia."),
]
