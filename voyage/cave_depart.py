"""La cave de départ : l'inventaire du 25/10/2026 (artifact « Cave de Julien »), repris une seule fois (cave-v1).

Les vins à boire seulement : le Chardonnay Castel et l'Aude, vins de cuisine, restent au placard (Courses).
Les accords rédigés de l'artifact sont traduits en profils (accords_vins.PROFILS), dans l'ordre de priorité.
"""
NOM_REPRISE = "cave-v1"


def _vin(id_, nom, producteur, appellation, region, couleur, millesime, debut, fin, prix_bas, prix_haut, accords,
         note="", quantite=1):
    return {"id": id_, "nom": nom, "producteur": producteur, "appellation": appellation, "region": region,
            "couleur": couleur, "millesime": millesime, "quantite": quantite, "debut": debut, "fin": fin,
            "prix_bas": prix_bas, "prix_haut": prix_haut, "accords": accords, "note": note}


CAVE_DEPART = [
    _vin("vin-clos-des-fees", "Le Clos des Fées", "Hervé Bizeul", "Côtes du Roussillon Villages", "Roussillon",
         "rouge", 2020, 2027, 2035, 45, 60, ["agneau", "gibier"], "« À garder !!! » — offert par B"),
    _vin("vin-sociando-mallet", "Château Sociando-Mallet", "Jean Gautreau", "Haut-Médoc", "Bordeaux",
         "rouge", 2011, 2026, 2030, 40, 55, ["boeuf"], "Offert par Yann. Millésime moyen : ne pas trop attendre"),
    _vin("vin-nuits-longecourts", "Nuits-Saint-Georges « Les Longecourts »", "Maison Nicolas Morin",
         "Nuits-Saint-Georges", "Bourgogne", "rouge", 2018, 2026, 2030, 40, 50, ["boeuf", "volaille", "fromage"]),
    _vin("vin-connetable-talbot", "Connétable Talbot", "Château Talbot (second vin)", "Saint-Julien", "Bordeaux",
         "rouge", 2016, 2027, 2034, 30, 40, ["boeuf", "agneau"], "Offert par L. Grand millésime, encore jeune"),
    _vin("vin-lucile-avril", "Lucile Avril", "Domaine Durieu", "Châteauneuf-du-Pape", "Rhône Sud",
         "rouge", 2020, 2027, 2032, 30, 40, ["agneau", "gibier"], "Offert (annoté 11/25)"),
    _vin("vin-esprit-de-granit", "Esprit de Granit — Sélection parcellaire", "Héritiers Gambert / Cave de Tain",
         "Saint-Joseph", "Rhône Nord", "rouge", 2019, 2026, 2028, 25, 30, ["boeuf", "volaille", "charcuterie"]),
    _vin("vin-temps-des-epices", "Le Temps des Épices", "Jeff Carrel", "Vin de France", "Languedoc",
         "rouge", 2019, 2026, 2026, 15, 25, ["epice"], "Mis en bouteille en juin 2024. Cote la moins fiable"),
    _vin("vin-peyrouquet", "Château Peyrouquet", "Propriétaire-récoltant", "Saint-Émilion", "Bordeaux",
         "rouge", 2023, 2026, 2027, 10, 15, ["boeuf", "tomate"], "Vin du quotidien"),
    _vin("vin-billecart-rose", "Billecart-Salmon Brut Rosé", "Billecart-Salmon", "Champagne", "Champagne",
         "bulles", None, 2026, 2028, 75, 90, ["poisson", "apero", "dessert"], "Bouteille la plus chère de la cave"),
    _vin("vin-meyer-fonne-pinot", "Pinot Noir Réserve", "Meyer-Fonné", "Alsace", "Alsace",
         "rouge", 2022, 2026, 2029, 18, 25, ["volaille", "poisson"]),
    _vin("vin-mourguettes", "Mourguettes", "Isabelle Guichard", "Côtes du Rhône (Uchaux)", "Rhône Sud",
         "rouge", None, 2026, 2028, 15, 20, ["agneau", "legumes"], "Vigneronne artisanale"),
    _vin("vin-maddalena", "Maddalena — Müller-Thurgau", "Molozay / Château de Vaux", "Moselle (bio)", "Lorraine",
         "blanc", 2024, 2026, 2027, 12, 15, ["poisson", "fromage"], "Appellation rare", quantite=2),
    _vin("vin-plan-cuve", "Plan Cuvé", "Non identifié", "Vin nature", "",
         "rouge", None, 2026, 2026, 12, 18, ["charcuterie", "apero"], "Producteur à vérifier"),
    _vin("vin-saint-amour", "Saint-Amour", "Négoce", "Saint-Amour (cru du Beaujolais)", "Beaujolais",
         "rouge", 2022, 2026, 2027, 10, 14, ["porc", "charcuterie"], "Servir légèrement frais"),
    _vin("vin-plan-de-dieu", "Plan de Dieu « Les Aumôniers »", "Les Aumôniers", "Côtes du Rhône Villages Plan de Dieu",
         "Rhône Sud", "rouge", 2023, 2026, 2028, 8, 12, ["boeuf", "tomate"]),
    _vin("vin-cheverny-nobles", "Cuvée des Nobles", "Vignerons de Mont-près-Chambord", "Cheverny", "Loire",
         "blanc", None, 2026, 2026, 8, 10, ["fruits-de-mer", "fromage"]),
    _vin("vin-muscat-beaumes", "Muscat de Beaumes-de-Venise", "Domaine de Durban", "Muscat de Beaumes-de-Venise (VDN)",
         "Rhône Sud", "doux", 2021, 2026, 2028, 15, 20, ["dessert"], "Servir à 8–10 °C"),
    _vin("vin-jurancon-bapteme", "Cuvée du Baptême", "Cave de Jurançon", "Jurançon (moelleux)", "Sud-Ouest",
         "doux", 2023, 2026, 2030, 12, 15, ["fromage", "dessert"]),
    _vin("vin-partages-rose", "Partages", "Domaine Galévan", "Côtes du Rhône rosé", "Rhône Sud",
         "rose", None, 2026, 2026, 10, 13, ["tomate", "legumes"], "Rosé : à boire cet hiver"),
]
