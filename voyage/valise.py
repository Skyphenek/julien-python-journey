"""Générateur de checklist de valise — adapté au type de destination, à la durée
et à la personne (Julien / Laetitia).

Application Python des concepts Exercism : dicts, listes, boucles, conditions.
On sépare les DONNÉES (les 3 tables ci-dessous, remplies une fois) de la LOGIQUE
(la fonction faire_valise). Démarrage minimal : on enrichit au fil des voyages.
"""

# 1. BASE : affaires de tout voyage. Valeur = quantité fixe, ou "par_jour".
BASE = {
    "chargeur": 1,
    "trousse toilette": 1,
    "déodorant": 1,
    "ceinture": 1,
    "chaussures de rechange": 1,
    "trousse pharmacie": 1,
    "sac de jour": 1,
    "adaptateur de prise": 1,
    "chaussettes": "par_jour",
    "pantalons": "par_3_jours",
    "pyjama": "par_semaine",
    "sweat": "par_semaine",
}

# 2. PAR TYPE de destination : chaque type -> sa liste d'affaires.
PAR_TYPE = {
    "chaud":    {"chapeau": 1, "lunettes de soleil": "par_semaine", "crème solaire": 1,
                 "biafine": 1, "shorts": "par_3_jours", "débardeurs": "par_jour",
                 "robe légère": "par_3_jours", "sandales": 1},
    "froid":    {"manteau": 1, "pull": "par_3_jours", "gants": 1, "bonnet": 1,
                 "écharpe": 1, "sous-couche thermique": "par_3_jours",
                 "grosses chaussures": 1, "collants": "par_3_jours"},
    "plage":    {"maillot": "par_3_jours", "crème solaire": 1, "tongs": 1, "futa": 1,
                 "biafine": 1, "shorts": "par_3_jours", "sandales": 1,
                 "lunettes de soleil": 1},
    "montagne": {"chaussures rando": 1, "gourde": 1, "coupe-vent": 1, "polaire": 1,
                 "chaussettes de rando": "par_3_jours", "bâtons": 1},
    "ville":    {"tenue habillée": 1, "baskets": 1},
    "pluie":    {"parapluie": 1, "imperméable": 1, "chaussures imperméables": 1},
}

# 3. PAR PERSONNE : les affaires perso.
PAR_PERSONNE = {
    "Julien":   {"rasoir": 1, "caleçons": "par_jour", "t-shirts": "par_jour"},
    "Laetitia": {"maquillage": 1, "lisseur": 1, "culottes": "par_jour",
                 "petits-hauts": "par_jour", "soutien-gorge": "par_semaine",
                 "robes": "par_3_jours", "démaquillant": 1, "bijoux": 1},
}

# 4. GÉO — Table 1 : chaque ville pointe vers sa zone climatique (mapping léger).
VILLE_VERS_ZONE = {
    # Europe du Nord / îles britanniques
    "Londres": "europe_nord", "Édimbourg": "europe_nord", "Dublin": "europe_nord",
    "Amsterdam": "europe_nord", "Bruxelles": "europe_nord", "Berlin": "europe_nord",
    "Copenhague": "europe_nord", "Stockholm": "europe_nord",
    # Europe de l'Ouest continentale
    "Paris": "europe_ouest", "Lyon": "europe_ouest", "Nantes": "europe_ouest",
    "Genève": "europe_ouest", "Milan": "europe_ouest",
    # Côte atlantique (France / Espagne / Portugal)
    "Cap Ferret": "cote_atlantique", "Biarritz": "cote_atlantique", "Bordeaux": "cote_atlantique",
    "La Rochelle": "cote_atlantique", "Saint-Sébastien": "cote_atlantique",
    "Porto": "cote_atlantique",
    # Méditerranée (Italie / Espagne / sud France / Grèce / Portugal sud)
    "Rome": "mediterranee", "Florence": "mediterranee", "Venise": "mediterranee",
    "Naples": "mediterranee", "Palerme": "mediterranee", "Marseille": "mediterranee",
    "Nice": "mediterranee", "Barcelone": "mediterranee", "Madrid": "mediterranee",
    "Séville": "mediterranee", "Valence": "mediterranee", "Athènes": "mediterranee",
    "Lisbonne": "mediterranee", "Split": "mediterranee", "Dubrovnik": "mediterranee",
    "Cyclades": "mediterranee",
    # Montagne / Alpes
    "Annecy": "montagne_alpes", "Chamonix": "montagne_alpes", "Grenoble": "montagne_alpes",
    "Innsbruck": "montagne_alpes", "Zermatt": "montagne_alpes",
    # Afrique du Nord / désertique chaud
    "Marrakech": "afrique_nord", "Agadir": "afrique_nord", "Essaouira": "afrique_nord",
    "Tunis": "afrique_nord", "Dubaï": "afrique_nord",
    # Asie du Sud-Est
    "Hanoï": "asie_sud_est", "Ho Chi Minh": "asie_sud_est", "Siem Reap": "asie_sud_est",
    "Bangkok": "asie_sud_est", "Singapour": "asie_sud_est", "Tokyo": "asie_sud_est",
    # Amériques
    "New York": "usa_est", "Boston": "usa_est",
    "San Francisco": "usa_ouest", "Los Angeles": "usa_ouest",
    "Miami": "tropical", "Cancún": "tropical", "Bali": "tropical",
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


def types_pour(ville, mois):
    """Déduire les types de destination depuis la ville et le mois.

    Double lookup (façon jointure SQL) : ville -> zone -> climat[saison].
    """
    zone = VILLE_VERS_ZONE[ville]
    saison = saison_du_mois(mois)
    return ZONES[zone][saison]


def quantite_reelle(marqueur, jours):
    """Traduire un marqueur de quantité en nombre réel selon la durée du voyage."""
    if marqueur == "par_jour":
        return jours
    if marqueur == "par_semaine":
        return max(1, jours // 7)   # jamais moins de 1 (plancher)
    if marqueur == "par_3_jours":
        return max(1, jours // 3)
    return marqueur          # déjà un nombre (ex: 1) -> tel quel


def faire_valise(types, jours, personne, hors_ue, conduit):
    """Construire la checklist {objet: quantité} selon la destination et la personne.

    - types    : liste de types de destination, ex. ["chaud", "plage"]
    - jours    : durée du voyage (module les quantités "par_jour")
    - personne : "Julien" ou "Laetitia"
    - hors_ue  : True -> passeport, False -> CNI
    - conduit  : True -> permis (+ permis international si hors_ue)
    """
    valise = {}
    # 1. BASE : le traducteur gère la quantité (fixe ou modulée par la durée).
    for objet, quantite in BASE.items():
        valise[objet] = quantite_reelle(quantite, jours)

    # 2. PAR TYPE : idem, mais PAR_TYPE porte maintenant des quantités (dict par type).
    for type_dest in types:
        for objet, quantite in PAR_TYPE[type_dest].items():
            valise[objet] = quantite_reelle(quantite, jours)

    # 3. PERSONNE : affaires perso (dict avec quantités, comme PAR_TYPE).
    for objet, quantite in PAR_PERSONNE[personne].items():
        valise[objet] = quantite_reelle(quantite, jours)

    # 4. DOCUMENTS : pièce d'identité selon la zone, permis si on conduit.
    if hors_ue:
        valise["passeport"] = 1
    else:
        valise["carte d'identité"] = 1
    if conduit:
        valise["permis"] = 1
        if hors_ue:
            valise["permis international"] = 1

    return valise


def main():
    """Assistant interactif : pose les questions, puis construit la valise."""
    ville = input("Ville de destination : ")            # texte
    mois = int(input("Mois du départ (1-12) : "))       # texte -> nombre
    jours = int(input("Nombre de jours : "))
    personne = input("Qui fait sa valise ? (Julien / Laetitia) : ")
    hors_ue = input("Destination hors UE ? (o/n) : ") == "o"   # texte -> booléen
    conduit = input("Tu vas conduire ? (o/n) : ") == "o"

    types = types_pour(ville, mois)                     # la couche géo déduit le climat
    valise = faire_valise(types, jours, personne, hors_ue, conduit)

    print(f"\nValise pour {ville} ({jours} jours) — types : {types}")
    for objet, quantite in valise.items():
        print(f"  {objet} ×{quantite}")


if __name__ == "__main__":
    main()
