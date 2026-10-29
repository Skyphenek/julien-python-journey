"""Placard v2 (29/10/2026) : la reprise du placard rangé par zone, depuis la checklist « La cuisine de
Ste Isaure » remplie par Julien et Laetitia.

- PLACARD : chaque élément durable, sa zone, et son état d'après la checklist : « stock » (on a),
  « samedi » (vague 1, à acheter samedi), « epiceries » (vague 2, épiceries asiatique et italienne),
  None (déjà au placard, pas dans la checklist : on ne touche qu'à sa zone).
- HABITUELS : le frais à rotation hebdomadaire ; il quitte le placard pour les habituels des courses.
  True : à acheter samedi (sur la liste) ; False : rangé.
- Les noms sont ceux des recettes du carnet (« riz carnaroli », « sauce poisson »), pas ceux de la
  checklist : c'est la même clé normalisée qui relie placard, courses et ingrédients.
Les ingrédients « à la demande » (62) ne sont pas repris : ils entrent au placard quand une recette les
fait acheter (db.enregistrer_article).
"""

NOM_REPRISE = "placard-v2"

PLACARD = [
    # Frigo
    ("parmesan", "frigo", "samedi"), ("comté", "frigo", "samedi"), ("pecorino", "frigo", "epiceries"),
    ("guanciale ou pancetta", "frigo", "epiceries"), ("beaufort", "frigo", None), ("lardons", "frigo", "samedi"),
    ("chorizo", "frigo", "samedi"),                       # pour Laetitia : toujours en avoir
    ("concentré de tomate", "frigo", "samedi"), ("mayonnaise", "frigo", "samedi"),
    # Placard sec
    ("spaghetti", "placard-sec", "samedi"), ("rigatoni", "placard-sec", "samedi"),
    ("feuilles de lasagne", "placard-sec", "stock"), ("riz carnaroli", "placard-sec", "stock"),
    ("riz basmati", "placard-sec", "samedi"), ("riz jasmin", "placard-sec", "epiceries"),
    ("vermicelles de riz", "placard-sec", "epiceries"), ("tortillas", "placard-sec", "samedi"),
    ("tomates pelées", "placard-sec", "epiceries"), ("passata", "placard-sec", "samedi"),
    ("pois chiches", "placard-sec", "samedi"), ("thon", "placard-sec", "samedi"), ("maïs", "placard-sec", None),
    ("anchois", "placard-sec", "epiceries"), ("bouillon", "placard-sec", "stock"),
    ("farine", "placard-sec", "samedi"), ("fécule de maïs", "placard-sec", "samedi"),
    ("sucre", "placard-sec", "samedi"), ("cassonade", "placard-sec", "samedi"),
    ("levure chimique", "placard-sec", "samedi"), ("chocolat noir", "placard-sec", "samedi"),
    ("chapelure panko", "placard-sec", "epiceries"), ("café", "placard-sec", None), ("boudoirs", "placard-sec", None),
    ("pommes de terre", "placard-sec", "samedi"), ("ail", "placard-sec", "stock"),
    ("oignons", "placard-sec", "samedi"), ("échalotes", "placard-sec", "samedi"),
    # Épices et condiments (huiles, vinaigres et sauces compris)
    ("huile d'olive", "epices", "samedi"), ("huile d'olive de finition", "epices", "stock"),
    ("huile neutre", "epices", "stock"), ("huile de sésame", "epices", "epiceries"),
    ("vinaigre", "epices", "stock"), ("vinaigre de xérès", "epices", "stock"),
    ("vinaigre de riz", "epices", "epiceries"), ("sel", "epices", "stock"), ("gros sel", "epices", "stock"),
    ("fleur de sel", "epices", "stock"), ("poivre en grains", "epices", "stock"),
    ("piment en flocons", "epices", "stock"), ("piment de cayenne", "epices", "stock"),
    ("paprika doux", "epices", "stock"), ("paprika fumé", "epices", "samedi"), ("cumin", "epices", "stock"),
    ("curcuma", "epices", "stock"), ("cannelle", "epices", "samedi"), ("noix de muscade", "epices", "stock"),
    ("vanille", "epices", "samedi"), ("laurier", "epices", "samedi"), ("thym", "epices", "samedi"),
    ("origan", "epices", "samedi"), ("épices tacos", "epices", None), ("moutarde", "epices", "samedi"),
    ("sauce piquante", "epices", "stock"), ("miel", "epices", "samedi"), ("sauce soja", "epices", "epiceries"),
    ("sauce poisson", "epices", "epiceries"), ("sauce huître", "epices", "epiceries"),
    ("mirin", "epices", "epiceries"), ("pâte de curry", "epices", "epiceries"),
    # Congélateur
    ("petits pois surgelés", "congelateur", "samedi"), ("épinards surgelés", "congelateur", "samedi"),
    ("herbes surgelées", "congelateur", "samedi"), ("citronnelle", "congelateur", "epiceries"),
    ("demi-baguettes", "congelateur", None), ("pains burger", "congelateur", None),
    ("steaks hachés", "congelateur", None), ("bacon", "congelateur", None), ("mozzarella râpée", "congelateur", None),
    # Cave
    ("vin blanc", "cave", "stock"), ("vin rouge", "cave", "stock"),
]

HABITUELS = [
    ("œufs", True), ("beurre", True), ("beurre demi-sel", True), ("crème fraîche", True), ("lait", True),
    ("yaourt grec", True), ("citrons", True), ("mozzarella", False), ("jambon", False),
    ("eau Volvic citron", True),                          # pour Laetitia : toujours en avoir
]
