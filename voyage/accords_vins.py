"""Accords mets-vins de Casa Binomerie : le profil d'un plat (d'après ses ingrédients) et le vin du soir.

Déterministe, sans IA (spec : docs/superpowers/specs/2026-11-03-casa-cave-design.md). Un plat porte des profils
(bœuf, volaille, fromage…) ; un vin porte la liste des profils avec lesquels il va. Le vin du soir : celui qui colle
le mieux au profil principal du dîner, en finissant par ce qui doit être bu vite.
"""
from catalogue import cle_catalogue, chercher

# Dans l'ordre de priorité : le premier profil d'un plat est son profil principal (la protéine d'abord)
PROFILS = ["boeuf", "agneau", "gibier", "volaille", "porc", "charcuterie", "poisson", "fruits-de-mer",
           "fromage", "epice", "tomate", "legumes", "apero", "dessert"]
SEUIL_BELLE = 30            # € (prix estimé haut) : au-delà, une belle bouteille, pas pour un soir de semaine
MAX_SUGGESTIONS = 3
_WEEK_END = (4, 5)          # vendredi et samedi soir (date.weekday)

# Ingrédient (nom du catalogue) -> profil. Le veau va avec les viandes blanches (volaille).
PAR_INGREDIENT = {
    "boeuf": ["bœuf", "bœuf haché", "steak", "steaks hachés", "pièce du boucher", "entrecôte", "faux-filet",
              "bavette", "onglet", "rumsteck", "côte de bœuf", "rôti de bœuf", "paleron", "joue de bœuf",
              "paleron ou joue de bœuf", "bœuf à bourguignon", "plat de côtes", "carpaccio", "tartare"],
    "agneau": ["agneau", "gigot d'agneau", "épaule d'agneau", "côtelettes d'agneau", "souris d'agneau", "navarin",
               "merguez"],
    "gibier": ["canard", "magret de canard", "cuisses de canard confites", "lapin", "caille"],
    "volaille": ["poulet", "poulet entier", "poulet fermier", "filets de poulet", "blancs de poulet",
                 "cuisses de poulet", "hauts de cuisse de poulet", "pilons de poulet", "ailes de poulet", "dinde",
                 "escalopes de dinde", "pintade", "veau", "escalopes de veau", "blanquette de veau",
                 "osso buco de veau", "tendron de veau", "rôti de veau", "côtes de veau"],
    "porc": ["porc", "porc haché", "échine de porc", "filet mignon", "côtes de porc", "rôti de porc",
             "travers de porc", "poitrine de porc", "palette de porc", "saucisses", "chipolatas",
             "saucisses de Toulouse", "salsiccia", "boudin noir", "andouillette", "chair à saucisse"],
    "charcuterie": ["jambon", "jambon blanc", "jambon cru", "jambon de Bayonne", "jambon de Parme", "prosciutto",
                    "speck", "coppa", "lardons", "lardons fumés", "bacon", "allumettes de bacon",
                    "guanciale ou pancetta", "guanciale", "pancetta", "chorizo", "saucisson", "nduja"],
    "poisson": ["saumon", "pavés de saumon", "filets de saumon", "cabillaud", "dos de cabillaud", "lieu noir",
                "colin", "merlu", "églefin", "haddock", "bar", "dorade", "sole", "sardines fraîches", "maquereau",
                "thon frais", "truite", "lotte", "raie", "saumon fumé", "truite fumée", "thon"],
    "fruits-de-mer": ["Saint-Jacques", "crevettes", "crevettes crues", "gambas", "moules", "palourdes", "coques",
                      "huîtres", "calamars", "encornets", "poulpe", "seiche", "crabe", "langoustines",
                      "crevettes surgelées"],
    "fromage": ["parmesan", "pecorino", "pecorino romano", "parmigiano reggiano", "grana padano", "comté",
                "beaufort", "emmental", "gruyère", "cheddar", "cheddar râpé", "cheddar en tranches", "raclette",
                "tomme", "reblochon", "camembert", "brie", "munster", "maroilles", "mont d'or", "roquefort",
                "gorgonzola", "chèvre", "bûche de chèvre", "feta", "halloumi", "mozzarella", "mozzarella râpée",
                "burrata", "scamorza", "taleggio", "fromage râpé", "emmental râpé"],
    "epice": ["épices tacos", "curry", "curry en poudre", "pâte de curry", "pâte de curry rouge",
              "pâte de curry vert", "pâte de curry jaune", "harissa", "ras el hanout", "garam masala", "gochujang",
              "sriracha", "piment", "piment oiseau", "sambal oelek", "épices cajun", "chipotle"],
    "tomate": ["tomates pelées", "tomates concassées", "passata", "coulis de tomate", "sauce tomate",
               "pulpe de tomate", "pâte à pizza", "concentré de tomate", "tomates San Marzano"],
}
_PROFIL = {cle_catalogue(nom): profil for profil, noms in PAR_INGREDIENT.items() for nom in noms}
_PROTEINES = set(PROFILS[:PROFILS.index("fromage") + 1])          # viande, poisson ou fromage


def profils_du_plat(plat):
    """Les profils d'un plat, dans l'ordre de priorité. Un dessert : « dessert » ; un accompagnement : aucun.
    Sans viande, poisson ni fromage, mais avec des légumes du rayon fruits et légumes : « legumes »."""
    if plat.get("genre") == "dessert":
        return ["dessert"]
    if plat.get("genre") == "accompagnement":
        return []
    trouves = {_PROFIL[cle_catalogue(i)] for i in plat["ingredients"] if cle_catalogue(i) in _PROFIL}
    if not trouves & _PROTEINES and any((chercher(i) or ("",))[0] == "fruits-legumes" for i in plat["ingredients"]):
        trouves.add("legumes")
    return [p for p in PROFILS if p in trouves]


def profils_du_repas(plats):
    """(profil principal, profils secondaires) d'un repas : le principal est le premier profil du premier plat de
    genre « plat » (sinon du premier plat qui en a) ; les secondaires, tous les autres profils de ses plats."""
    par_plat = [(p, profils_du_plat(p)) for p in plats]
    avec = [x for x in par_plat if x[1]]
    if not avec:
        return None, []
    principal = next((pr[0] for p, pr in avec if p.get("genre") == "plat"), avec[0][1][0])
    tous = {x for _, pr in avec for x in pr} - {principal}
    return principal, [p for p in PROFILS if p in tous]


def suggerer(cave, principal, secondaires, jour, belle=False):
    """Au plus MAX_SUGGESTIONS bouteilles pour ce repas. Écartées : vides, à garder (fenêtre pas ouverte), les vins doux hors dessert, et les
    belles (prix_haut > SEUIL_BELLE) du dimanche au jeudi. belle=True : seulement les belles, quel que soit le jour.
    Points : +2 pour le profil principal, +1 par profil secondaire ; 0 point -> écartée.
    Tri : points, puis fin de la fenêtre la plus proche, puis le moins cher (prix inconnu en dernier), puis nom."""
    if principal is None:
        return []
    candidats = []
    for b in cave:
        est_belle = b.get("prix_haut") is not None and b["prix_haut"] > SEUIL_BELLE
        if b["quantite"] <= 0 or b["debut"] > jour.year:
            continue
        if b.get("couleur") == "doux" and principal != "dessert":      # un moelleux : au dessert seulement
            continue
        if belle and not est_belle:
            continue
        if not belle and est_belle and jour.weekday() not in _WEEK_END:
            continue
        points = 2 * (principal in b["accords"]) + sum(1 for s in secondaires if s in b["accords"])
        if points:
            candidats.append((-points, b["fin"], b.get("prix_haut") is None, b.get("prix_haut") or 0, b["nom"], b))
    candidats.sort(key=lambda c: c[:5])
    return [c[5] for c in candidats[:MAX_SUGGESTIONS]]
