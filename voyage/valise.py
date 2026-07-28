"""Générateur de checklist de valise — adapté au type de destination, à la durée
et à la personne (Julien / Laetitia).

Application Python des concepts Exercism : dicts, listes, boucles, conditions.
On sépare les DONNÉES (les 3 tables ci-dessous, remplies une fois) de la LOGIQUE
(la fonction faire_valise). Démarrage minimal : on enrichit au fil des voyages.
"""
# Feuille de style de la checklist HTML (mobile-first). Fournie clé en main :
# c'est de la présentation, pas de la logique. Injectée telle quelle dans le <head>.
HTML_STYLE = """
:root { color-scheme: light dark; }
* { box-sizing: border-box; }
body {
    font-family: -apple-system, system-ui, sans-serif;
    max-width: 640px; margin: 0 auto; padding: 1rem;
    line-height: 1.5; background: #f7f7f8; color: #18181b;
}
h1 { font-size: 1.5rem; margin: 0 0 1.25rem; }
section {
    background: #fff; border-radius: 12px; padding: .75rem 1.25rem;
    margin-bottom: 1rem; box-shadow: 0 1px 3px rgba(0,0,0,.08);
}
section h2 { font-size: 1.2rem; margin: .5rem 0; }
section h3 {
    font-size: .75rem; text-transform: uppercase; letter-spacing: .05em;
    color: #71717a; margin: 1rem 0 .25rem;
}
ul { list-style: none; margin: 0; padding: 0; }
li label {
    display: flex; align-items: center; gap: .6rem;
    padding: .55rem .1rem; cursor: pointer; min-height: 44px;
}
li input { width: 22px; height: 22px; flex-shrink: 0; }
label:has(input:checked) { color: #a1a1aa; text-decoration: line-through; }
p.prise {
    background: #eef2ff; color: #3730a3; font-size: .95rem;
    padding: .55rem .9rem; border-radius: 10px; margin: 0 0 1.5rem;
}
@media (prefers-color-scheme: dark) {
    body { background: #18181b; color: #f4f4f5; }
    section { background: #27272a; box-shadow: none; }
    section h3 { color: #a1a1aa; }
    p.prise { background: #312e81; color: #e0e7ff; }
}
"""

# 1a. BASE COMMUN : 1 pour le groupe entier (un seul suffit à plusieurs).
BASE_COMMUN = {
    "trousse toilette": 1,
    "déodorant": 1,
    "trousse pharmacie": 1,
    "sac de jour": 1,
}

# 1b. BASE PERSO : matos non-vêtement, chacun le sien -> ×nb, tiroir "Essentiels".
BASE_PERSO = {
    "chargeur": 1,
    "livre / liseuse": 1,
    "montre": 1,
    "adaptateur de prise": 1,   # chacun le sien (1 par personne) — moins relou à partager
}

# 1c. VÊTEMENTS DE BASE : la garde-robe de tout voyage, chacun la sienne -> ×nb,
#     rangés dans le tiroir "Affaires perso".
VETEMENTS_BASE = {
    "ceinture": 1,
    "chaussures de rechange": 1,
    "chaussettes": "par_jour",
    "pantalons": "par_3_jours",
    "pyjama": "par_semaine",
    "sweat": "par_semaine",
    "chemises": "par_3_jours",
}

# 2a. PAR TYPE — COMMUN : 1 pour le groupe (seuls les types concernés figurent ici).
PAR_TYPE_COMMUN = {
    "chaud": {"crème solaire": 1, "biafine": 1},
    "plage": {"crème solaire": 1, "biafine": 1},
    "pluie": {"parapluie": 1},
}

# 2b. PAR TYPE — PERSO : chacun le sien (tout ce qui se porte).
PAR_TYPE_PERSO = {
    "chaud":    {"chapeau": 1, "lunettes de soleil": "par_semaine",
                 "shorts": "par_3_jours", "débardeurs": "par_jour",
                 "robe légère": "par_3_jours", "sandales": 1,
                 "chemises légères": "par_3_jours",
                 "pantalons": "par_semaine",     # ÉCRASE le pantalon de base : ~÷3 quand il fait chaud
                 "chemises": 0},                 # 0 = retire les chemises normales quand il fait chaud
    "froid":    {"manteau": 1, "pull": "par_3_jours", "gants": 1, "bonnet": 1,
                 "écharpe": 1, "sous-couche thermique": "par_3_jours",
                 "grosses chaussures": 1, "collants": "par_3_jours"},
    "plage":    {"maillot": "par_3_jours", "tongs": 1, "futa": 1,
                 "shorts": "par_3_jours", "sandales": 1, "lunettes de soleil": 1},
    "montagne": {"chaussures rando": 1, "gourde": 1, "coupe-vent": 1, "polaire": 1,
                 "chaussettes de rando": "par_3_jours", "bâtons": 1},
    "ville":    {"tenue habillée": 1, "baskets": 1},
    "pluie":    {"imperméable": 1, "chaussures imperméables": 1},
}

# 3. PAR PERSONNE : les affaires perso.
PAR_PERSONNE = {
    "Julien":   {"rasoir": 1, "caleçons": "par_jour", "t-shirts": "par_jour"},
    "Laetitia": {"maquillage": 1, "lisseur": 1, "culottes": "par_jour",
                 "petits-hauts": "par_jour", "soutien-gorge": "par_semaine",
                 "robes": "par_3_jours", "démaquillant": 1, "bijoux": 1,
                 "boucles d'oreille": (3, "par_semaine")},   # 3 paires / semaine
}

# 3quater. JAMAIS : ce qu'une personne ne prend jamais, même si une table par-type
#          l'ajoute (ex. items genrés présents dans les tables partagées PAR_TYPE_PERSO
#          comme "robe légère" ou "collants" -> pas pour Julien).
JAMAIS = {
    "Julien": {"robe légère", "collants", "débardeurs"},
}

# 3bis. Code de saisie -> liste des personnes concernées (pilote la question du prénom).
CHOIX_PERSONNE = {
    "j": ["Julien"],
    "l": ["Laetitia"],
    "2": ["Julien", "Laetitia"],
}

# 3ter. THÈMES d'affichage : à quel rayon appartient chaque objet.
#       7 rayons explicites, Divers compris. Tout objet ABSENT de ces 7 sets est
#       un OUBLI : theme_de() le mettra dans Divers par sécurité, mais le garde-fou
#       objets_sans_rayon() le signalera au lancement (au lieu de le cacher).
THEMES = {
    "Vêtements": {
        "pantalons", "pyjama", "sweat", "shorts", "débardeurs", "robe légère",
        "robes", "manteau", "pull", "maillot", "coupe-vent", "polaire",
        "tenue habillée", "imperméable", "t-shirts", "petits-hauts",
        "chemises", "chemises légères",
    },
    "Sous-vêtements": {
        "caleçons", "culottes", "soutien-gorge", "chaussettes",
        "chaussettes de rando", "collants", "sous-couche thermique",
    },
    "Chaussures": {
        "chaussures de rechange", "sandales", "tongs", "grosses chaussures",
        "chaussures rando", "baskets", "chaussures imperméables",
    },
    "Accessoires": {
        "ceinture", "chapeau", "lunettes de soleil", "gants", "bonnet",
        "écharpe", "bijoux", "boucles d'oreille", "montre", "futa",
    },
    "Hygiène": {
        "trousse toilette", "déodorant", "rasoir", "maquillage", "lisseur",
        "démaquillant", "crème solaire", "biafine", "trousse pharmacie",
    },
    "Tech": {
        "chargeur", "adaptateur de prise",
    },
    "Documents": {
        "passeport", "carte d'identité", "permis", "permis international",
    },
    "Divers": {
        "sac de jour", "livre / liseuse", "parapluie", "gourde", "bâtons",
    },
}

# 4. GÉO — Table 1 : chaque ville pointe vers sa zone climatique (mapping léger).
VILLE_VERS_ZONE = {
    # Europe du Nord / îles britanniques
    "Londres": "europe_nord", "Édimbourg": "europe_nord", "Dublin": "europe_nord",
    "Amsterdam": "europe_nord", "Bruxelles": "europe_nord", "Berlin": "europe_nord",
    "Copenhague": "europe_nord", "Stockholm": "europe_nord",
    # Europe de l'Ouest continentale
    "Paris": "europe_ouest", "Lyon": "europe_ouest", 
    "Milan": "europe_ouest",
    # Côte atlantique (France / Espagne / Portugal)
    "Cap Ferret": "cote_atlantique", "Biarritz": "cote_atlantique", "Bordeaux": "cote_atlantique",
    "La Rochelle": "cote_atlantique", "Nantes": "cote_atlantique", "Saint-Sébastien": "cote_atlantique",
    "Porto": "cote_atlantique",
    # Méditerranée (Italie / Espagne / sud France / Grèce / Portugal sud)
    "Rome": "mediterranee", "Florence": "mediterranee", "Venise": "mediterranee",
    "Naples": "mediterranee", "Palerme": "mediterranee", "Marseille": "mediterranee",
    "Nice": "mediterranee", "Barcelone": "mediterranee", "Madrid": "mediterranee",
    "Séville": "mediterranee", "Valence": "mediterranee", "Athènes": "mediterranee",
    "Lisbonne": "mediterranee", "Split": "mediterranee", "Dubrovnik": "mediterranee",
    "Cyclades": "mediterranee",
    # Montagne / Alpes
    "Annecy": "montagne_alpes", "Chamonix": "montagne_alpes", "Genève": "montagne_alpes", "Grenoble": "montagne_alpes",
    "Innsbruck": "montagne_alpes", "Méribel": "montagne_alpes", "Zermatt": "montagne_alpes",
    # Afrique du Nord / désertique chaud
    "Marrakech": "afrique_nord", "Agadir": "afrique_nord", "Essaouira": "afrique_nord",
    "Tunis": "afrique_nord", "Dubaï": "afrique_nord",
    # Asie du Sud-Est
    "Hanoï": "asie_sud_est", "Ho Chi Minh": "asie_sud_est", "Siem Reap": "asie_sud_est",
    "Bangkok": "asie_sud_est", "Singapour": "asie_sud_est",
    # Asie de l'Est tempérée (4 saisons)
    "Tokyo": "asie_est_tempere", "Kyoto": "asie_est_tempere", "Osaka": "asie_est_tempere",
    "Pékin": "asie_est_tempere", "Shanghai": "asie_est_tempere", "Xi'an": "asie_est_tempere",
    "Chengdu": "asie_est_tempere", "Séoul": "asie_est_tempere", "Busan": "asie_est_tempere",
    # Amériques
    "New York": "usa_est", "Boston": "usa_est",
    "San Francisco": "usa_ouest", "Los Angeles": "usa_ouest",
    "Miami": "tropical", "Cancún": "tropical", "Bali": "tropical",
}

# 4bis. GÉO — Table 1bis : chaque PAYS (ou État US) pointe vers sa zone climatique.
#       Même mécanisme que VILLE_VERS_ZONE : une entrée -> une zone de ZONES.
#       Pays au climat trop hétérogène pour une seule zone (USA, Indonésie, Brésil,
#       Australie, Chine, Inde) volontairement absents -> saisir par ville.
PAYS_VERS_ZONE = {
    # Europe du Nord / îles britanniques
    "Royaume-Uni": "europe_nord", "Irlande": "europe_nord",
    "Pays-Bas": "europe_nord", "Belgique": "europe_nord",
    "Allemagne": "europe_nord", "Danemark": "europe_nord",
    "Suède": "europe_nord", "Norvège": "europe_nord", "Islande": "europe_nord",
    # Europe de l'Ouest continentale
    "France": "europe_ouest", "Luxembourg": "europe_ouest",
    # Montagne / Alpes
    "Suisse": "montagne_alpes", "Autriche": "montagne_alpes", "Slovénie": "montagne_alpes",
    # Méditerranée
    "Italie": "mediterranee", "Espagne": "mediterranee", "Grèce": "mediterranee",
    "Portugal": "mediterranee", "Croatie": "mediterranee", "Malte": "mediterranee",
    "Chypre": "mediterranee",
    # Afrique du Nord / Moyen-Orient désertique
    "Maroc": "afrique_nord", "Tunisie": "afrique_nord", "Égypte": "afrique_nord",
    "Émirats Arabes Unis": "afrique_nord", "Jordanie": "afrique_nord",
    # Asie du Sud-Est
    "Thaïlande": "asie_sud_est", "Vietnam": "asie_sud_est", "Cambodge": "asie_sud_est",
    "Laos": "asie_sud_est", "Myanmar": "asie_sud_est", "Malaisie": "asie_sud_est",
    "Singapour": "asie_sud_est", "Philippines": "asie_sud_est",
    "Sri Lanka": "asie_sud_est",
    # Asie de l'Est tempérée (4 saisons)
    "Japon": "asie_est_tempere", "Chine": "asie_est_tempere",
    "Corée du Sud": "asie_est_tempere", "Taïwan": "asie_est_tempere",
    # Tropical (Amériques / îles)
    "Mexique": "tropical", "Cuba": "tropical", "République Dominicaine": "tropical",
    "Costa Rica": "tropical",
    # États-Unis (pays exclu, mais États touristiques au climat homogène inclus)
    "Californie": "usa_ouest", "Floride": "tropical", "Hawaï": "tropical",
    "Nevada": "usa_ouest", "Arizona": "usa_ouest", "Louisiane": "usa_est",
}

# 4ter. GÉO — UE : pays membres. Appartenance -> UE ; absence d'un pays connu -> hors UE.
#       (Accepte aussi des villes si on veut en couvrir plus tard.)
PAYS_UE = {
    "France", "Belgique", "Pays-Bas", "Allemagne", "Danemark", "Suède",
    "Irlande", "Luxembourg", "Autriche", "Slovénie", "Italie", "Espagne",
    "Grèce", "Portugal", "Croatie", "Malte", "Chypre",
}

# 4quater. GÉO — PRISE : quel adaptateur emporter DEPUIS LA FRANCE pour ce pays.
#          Valeurs usuelles (à revérifier ponctuellement). Le garde-fou
#          pays_sans_prise() signale tout pays de PAYS_VERS_ZONE non couvert ici.
PAYS_VERS_PRISE = {
    # Europe continentale + Maghreb (mêmes prises type C/E/F qu'en France)
    "France": "aucun", "Belgique": "aucun", "Pays-Bas": "aucun",
    "Allemagne": "aucun", "Danemark": "aucun", "Suède": "aucun",
    "Norvège": "aucun", "Islande": "aucun", "Luxembourg": "aucun",
    "Suisse": "aucun", "Autriche": "aucun", "Slovénie": "aucun",
    "Italie": "aucun", "Espagne": "aucun", "Grèce": "aucun",
    "Portugal": "aucun", "Croatie": "aucun",
    "Maroc": "aucun", "Tunisie": "aucun", "Égypte": "aucun",
    # Prises britanniques (type G)
    "Royaume-Uni": "UK", "Irlande": "UK", "Malte": "UK", "Chypre": "UK",
    "Émirats Arabes Unis": "UK", "Malaisie": "UK", "Singapour": "UK",
    # Prises américaines (type A/B, 110V)
    "Mexique": "US (110V)", "République Dominicaine": "US (110V)",
    "Costa Rica": "US (110V)", "Japon": "US (110V)",
    "Californie": "US (110V)", "Floride": "US (110V)", "Hawaï": "US (110V)",
    "Nevada": "US (110V)", "Arizona": "US (110V)", "Louisiane": "US (110V)",
    # Prises mélangées -> adaptateur universel
    "Jordanie": "universel", "Thaïlande": "universel", "Vietnam": "universel",
    "Cambodge": "universel", "Laos": "universel", "Myanmar": "universel",
    "Philippines": "universel / US", "Cuba": "universel / US",
    "Sri Lanka": "universel / UK",
    # Asie de l'Est tempérée (Corée : prises type C/F comme en France)
    "Chine": "universel", "Corée du Sud": "aucun", "Taïwan": "US (110V)",
}


# 5. GÉO — Table 2 : chaque zone définit ses types de destination par saison.
ZONES = {
    "europe_nord": {
        "hiver": ["froid", "pluie", "ville"], "printemps": ["froid", "pluie", "ville"],
        "été": ["ville"],                     "automne": ["froid", "pluie", "ville"],
    },
    "europe_ouest": {
        "hiver": ["froid", "ville"], "printemps": ["ville"],
        "été": ["chaud", "ville"],   "automne": ["froid", "ville"],
    },
    "cote_atlantique": {
        "hiver": ["froid", "pluie", "ville"],   "printemps": ["ville"],
        "été": ["chaud", "plage", "ville"],     "automne": ["pluie", "ville"],
    },
    "mediterranee": {
        "hiver": ["ville"],                  "printemps": ["ville"],
        "été": ["chaud", "plage", "ville"],  "automne": ["ville"],
    },
    "montagne_alpes": {
        "hiver": ["froid", "montagne"],     "printemps": ["froid", "montagne"],
        "été": ["montagne", "ville"],       "automne": ["froid", "montagne"],
    },
    "afrique_nord": {
        "hiver": ["ville"],          "printemps": ["chaud", "ville"],
        "été": ["chaud", "ville"],   "automne": ["chaud", "ville"],
    },
    "asie_sud_est": {
        "hiver": ["chaud", "plage"],          "printemps": ["chaud", "plage"],
        "été": ["chaud", "plage", "pluie"],   "automne": ["chaud", "plage", "pluie"],
    },
    "asie_est_tempere": {   # Japon, Chine, Corée, Taïwan : 4 saisons marquées, mousson estivale
        "hiver": ["froid", "ville"],          "printemps": ["ville"],
        "été": ["chaud", "ville", "pluie"],   "automne": ["ville"],
    },
    "usa_est": {
        "hiver": ["froid", "ville"], "printemps": ["ville"],
        "été": ["chaud", "ville"],   "automne": ["froid", "ville"],
    },
    "usa_ouest": {
        "hiver": ["ville"],                 "printemps": ["ville"],
        "été": ["chaud", "ville"],          "automne": ["ville"],
    },
    "tropical": {
        "hiver": ["chaud", "plage"],          "printemps": ["chaud", "plage"],
        "été": ["chaud", "plage", "pluie"],   "automne": ["chaud", "plage"],
    },
}


def saison_du_mois(mois):
    """Traduire un numéro de mois (1-12) en saison."""
    if mois in [12, 1, 2]:
        return "hiver"
    if mois in [3, 4, 5]:
        return "printemps"
    if mois in [6, 7, 8]:
        return "été"
    return "automne"

def zone_de(destination):
    """Trouver la zone climatique d'une ville ou d'un pays."""
    if destination in VILLE_VERS_ZONE:
        return VILLE_VERS_ZONE[destination]
    if destination in PAYS_VERS_ZONE:
        return PAYS_VERS_ZONE[destination]
    return None


def statut_ue(destination):
    """Déduire le statut UE : 'ue', 'hors_ue', ou 'inconnu' (ville non couverte)."""
    if destination in PAYS_UE:
        return "ue"
    if destination in PAYS_VERS_ZONE:   # pays connu absent de l'UE -> hors UE
        return "hors_ue"
    return "inconnu"                     # ville ou non couvert -> défaut prudent


def adaptateur_pour(destination):
    """Libellé de l'adaptateur à emporter depuis la France, ou 'à vérifier'."""
    if destination in PAYS_VERS_PRISE:
        return PAYS_VERS_PRISE[destination]
    return "à vérifier"


def pays_sans_prise():
    """Garde-fou : pays/États qui ont une zone mais aucune prise renseignée."""
    return set(PAYS_VERS_ZONE) - set(PAYS_VERS_PRISE)

def types_pour(ville, mois):
    """Déduire les types de destination depuis la ville et le mois.

    Double lookup (façon jointure SQL) : ville -> zone -> climat[saison].
    """
    zone = zone_de(ville)
    saison = saison_du_mois(mois)
    return ZONES[zone][saison]


def quantite_reelle(marqueur, jours):
    """Traduire un marqueur de quantité en nombre réel selon la durée du voyage."""
    if isinstance(marqueur, tuple):        # ex: (3, "par_semaine") = 3× la base par semaine
        nombre, base = marqueur
        return nombre * quantite_reelle(base, jours)
    if marqueur == "par_jour":
        return jours
    if marqueur == "par_semaine":
        return max(1, jours // 7)   # jamais moins de 1 (plancher)
    if marqueur == "par_3_jours":
        return max(1, jours // 3)
    return marqueur          # déjà un nombre (ex: 1) -> tel quel


def theme_de(objet):
    """Trouver le rayon d'un objet ; par défaut 'Divers' s'il n'est listé nulle part."""
    for theme, objets in THEMES.items():
        if objet in objets:
            return theme
    return "Divers"


def paquet_vide():
    """Un paquet neuf : un sous-dict vide par thème (l'ordre = l'ordre d'affichage)."""
    return {"Vêtements": {}, "Sous-vêtements": {}, "Chaussures": {},
            "Accessoires": {}, "Hygiène": {}, "Tech": {}, "Documents": {},
            "Divers": {}}


def objets_sans_rayon():
    """Garde-fou : renvoie les objets qui n'appartiennent à AUCUN rayon de THEMES.

    Rassemble tous les objets de toutes les tables de données (set = ensemble),
    puis soustrait ceux déjà classés. Ce qui reste = les oublis à ranger.
    Vide = tout est classé.
    """
    tous = set(BASE_COMMUN) | set(BASE_PERSO) | set(VETEMENTS_BASE)
    for sous_table in PAR_TYPE_COMMUN.values():
        tous |= set(sous_table)
    for sous_table in PAR_TYPE_PERSO.values():
        tous |= set(sous_table)
    for sous_table in PAR_PERSONNE.values():
        tous |= set(sous_table)
    classes = set()
    for objets in THEMES.values():
        classes |= objets
    return tous - classes


def ranger(paquet, objet, quantite, jours):
    """Ranger un objet dans le bon rayon d'un paquet, quantité traduite selon la durée.

    Convention : quantité réelle == 0 -> on RETIRE l'objet (utile quand une table
    par-type écrase un objet de base à 0, ex. chemises normales par temps chaud).
    """
    rayon = paquet[theme_de(objet)]
    quantite = quantite_reelle(quantite, jours)
    if quantite == 0:
        rayon.pop(objet, None)      # retire s'il était là, sinon ne fait rien
        return
    rayon[objet] = quantite


def faire_valise(types, jours, personnes, hors_ue, conduit):
    """Construire la checklist {objet: quantité} selon la destination et la personne.

    - types    : liste de types de destination, ex. ["chaud", "plage"]
    - jours    : durée du voyage (module les quantités "par_jour")
    - personnes : liste de personnes qui font leur valise
    - hors_ue  : True -> passeport, False -> CNI
    - conduit  : True -> permis (+ permis international si hors_ue)
    """
    # Un paquet par propriétaire : "Partagé" + un paquet par personne.
    # Chaque paquet est lui-même découpé par thème (via paquet_vide()).
    valise = {"Partagé": paquet_vide()}
    for personne in personnes:
        valise[personne] = paquet_vide()

    # === PARTAGÉ : 1 pour le groupe entier ===
    partage = valise["Partagé"]
    for objet, quantite in BASE_COMMUN.items():
        ranger(partage, objet, quantite, jours)
    for type_dest in types:      # types sans commun -> .get renvoie {} : rien à ajouter
        for objet, quantite in PAR_TYPE_COMMUN.get(type_dest, {}).items():
            ranger(partage, objet, quantite, jours)

    # === PERSO : le paquet de CHAQUE personne (×1, plus besoin de ×nb) ===
    for personne in personnes:
        paquet = valise[personne]        # raccourci : paquet POINTE vers valise[personne]
        for objet, quantite in BASE_PERSO.items():
            ranger(paquet, objet, quantite, jours)
        for objet, quantite in VETEMENTS_BASE.items():
            ranger(paquet, objet, quantite, jours)
        for type_dest in types:
            for objet, quantite in PAR_TYPE_PERSO[type_dest].items():
                ranger(paquet, objet, quantite, jours)
        for objet, quantite in PAR_PERSONNE[personne].items():
            ranger(paquet, objet, quantite, jours)
        # filtre final : ce que cette personne ne prend jamais (items genrés, etc.)
        for objet in JAMAIS.get(personne, set()):
            paquet[theme_de(objet)].pop(objet, None)
        # documents personnels (chacun les siens)
        if hors_ue:
            ranger(paquet, "passeport", 1, jours)
        else:
            ranger(paquet, "carte d'identité", 1, jours)
        if conduit:
            ranger(paquet, "permis", 1, jours)
            if hors_ue:
                ranger(paquet, "permis international", 1, jours)

    return valise

def valise_en_html(valise, ville, jours, types):
    """Construire la page HTML de la checklist."""
    adaptateur = adaptateur_pour(ville)     # info niveau destination, affichée en tête
    corps = ""
    for proprietaire, themes in valise.items():
        corps = corps + f"<section><h2>{proprietaire}</h2>"
        for theme, objets in themes.items():
            if not objets:
                continue
            corps = corps + f"<h3>{theme}</h3><ul>"
            for objet, quantite in sorted(objets.items()):
                corps = corps + f"<li><label><input type=\"checkbox\"> {objet} ×{quantite}</label></li>"
            corps = corps + "</ul>"
        corps = corps + "</section>"
    page = f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Valise — {ville}</title>
<style>{HTML_STYLE}</style>
</head>
<body>
<h1>Valise — {ville} · {jours} jours</h1>
<p class="prise">🔌 Adaptateur à emporter : <strong>{adaptateur}</strong></p>
{corps}
</body>
</html>"""
    return page

def main():
    """Assistant interactif : pose les questions, puis construit la valise."""
    manquants = objets_sans_rayon()
    if manquants:
        print(f"⚠️  Objets sans rayon (à classer dans THEMES) : {manquants}")
    sans_prise = pays_sans_prise()
    if sans_prise:
        print(f"⚠️  Pays sans prise renseignée (à compléter dans PAYS_VERS_PRISE) : {sans_prise}")
    while True:
        ville = input("Ville de destination : ")
        if ville in VILLE_VERS_ZONE or ville in PAYS_VERS_ZONE:
            break
        print(f"Ville '{ville}' inconnue, vérifie l'orthographe.")          # texte
    while True:
        reponse = input("Nombre de jours : ")
        if reponse.isdigit() and int(reponse) >= 1:      # au moins 1 jour
            jours = int(reponse)
            break                            # sortir de la boucle
        print("Nombre de jours invalide : entre un nombre positif.")
    while True:
        reponse = input("Mois du départ (1-12) : ")
        if reponse.isdigit() and 1 <= int(reponse) <= 12:
            mois = int(reponse)
            break                     # sortir de la boucle
        print("Mois invalide : entre un nombre entre 1 et 12.")    
    while True:
        choix = input("Qui fait sa valise ? (j = Julien / l = Laetitia / 2 = les deux) : ")
        if choix in CHOIX_PERSONNE:
            break
        print("Choix invalide : tape j, l ou 2.")
    personnes = CHOIX_PERSONNE[choix]
    statut = statut_ue(ville)                       # déduit du pays, plus de question
    hors_ue = statut != "ue"                        # inconnu -> passeport (défaut prudent)
    if statut == "inconnu":
        print("⚠️  Statut UE inconnu pour cette destination : passeport par défaut, à vérifier.")
    conduit = input("Tu vas conduire ? (o/n) : ") == "o"

    types = types_pour(ville, mois)                     # la couche géo déduit le climat
    valise = faire_valise(types, jours, personnes, hors_ue, conduit)

    html = valise_en_html(valise, ville, jours, types)
    with open("valise.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("Checklist écrite dans valise.html")


if __name__ == "__main__":
    main()
