"""Générateur de checklist de valise — adapté au type de destination, à la durée
et à la personne (Julien / Laetitia).

Application Python des concepts Exercism : dicts, listes, boucles, conditions.
On sépare les DONNÉES (les 3 tables ci-dessous, remplies une fois) de la LOGIQUE
(la fonction faire_valise). Démarrage minimal : on enrichit au fil des voyages.
"""

# 1a. BASE COMMUN : 1 pour le groupe entier (un seul suffit à plusieurs).
BASE_COMMUN = {
    "trousse toilette": 1,
    "déodorant": 1,
    "trousse pharmacie": 1,
    "sac de jour": 1,
    "adaptateur de prise": 1,
}

# 1b. BASE PERSO : matos non-vêtement, chacun le sien -> ×nb, tiroir "Essentiels".
BASE_PERSO = {
    "chargeur": 1,
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
                 "robe légère": "par_3_jours", "sandales": 1},
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
                 "robes": "par_3_jours", "démaquillant": 1, "bijoux": 1},
}

# 3bis. Code de saisie -> liste des personnes concernées (pilote la question du prénom).
CHOIX_PERSONNE = {
    "j": ["Julien"],
    "l": ["Laetitia"],
    "2": ["Julien", "Laetitia"],
}

# 3ter. THÈMES d'affichage : à quel rayon appartient chaque objet.
#       Tout objet non listé ici tombera dans "Divers".
THEMES = {
    "Vêtements": {
        # habits
        "ceinture", "chaussettes", "pantalons", "pyjama", "sweat", "shorts",
        "débardeurs", "robe légère", "manteau", "pull", "sous-couche thermique",
        "collants", "maillot", "coupe-vent", "polaire", "chaussettes de rando",
        "tenue habillée", "imperméable", "caleçons", "t-shirts", "culottes",
        "petits-hauts", "soutien-gorge", "robes",
        # accessoires
        "chapeau", "lunettes de soleil", "gants", "bonnet", "écharpe", "bijoux",
        # chaussures
        "sandales", "chaussures de rechange", "tongs", "grosses chaussures",
        "chaussures rando", "baskets", "chaussures imperméables",
    },
    "Hygiène": {
        "trousse toilette", "déodorant", "rasoir", "maquillage", "lisseur",
        "démaquillant", "crème solaire", "biafine", "trousse pharmacie",
    },
    "Documents": {
        "passeport", "carte d'identité", "permis", "permis international",
    },
    # non listés (chargeur, adaptateur de prise, sac de jour, parapluie, gourde,
    # bâtons, futa...) -> "Divers", géré par theme_de().
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


def theme_de(objet):
    """Trouver le rayon d'un objet ; par défaut 'Divers' s'il n'est listé nulle part."""
    for theme, objets in THEMES.items():
        if objet in objets:
            return theme
    return "Divers"


def paquet_vide():
    """Un paquet neuf : un sous-dict vide par thème (l'ordre = l'ordre d'affichage)."""
    return {"Vêtements": {}, "Hygiène": {}, "Divers": {}, "Documents": {}}


def ranger(paquet, objet, quantite, jours):
    """Ranger un objet dans le bon rayon d'un paquet, quantité traduite selon la durée."""
    paquet[theme_de(objet)][objet] = quantite_reelle(quantite, jours)


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


def main():
    """Assistant interactif : pose les questions, puis construit la valise."""
    while True:
        ville = input("Ville de destination : ")
        if ville in VILLE_VERS_ZONE:
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
    hors_ue = input("Destination hors UE ? (o/n) : ") == "o"   # texte -> booléen
    conduit = input("Tu vas conduire ? (o/n) : ") == "o"

    types = types_pour(ville, mois)                     # la couche géo déduit le climat
    valise = faire_valise(types, jours, personnes, hors_ue, conduit)

    print(f"\nValise pour {ville} ({jours} jours) — types : {types}")
    for proprietaire, themes in valise.items():
        print(f"\n=== {proprietaire} ===")
        for theme, objets in themes.items():
            if not objets:            # thème vide -> on ne l'affiche pas
                continue
            print(f"  {theme} :")
            for objet, quantite in sorted(objets.items()):
                print(f"    {objet} ×{quantite}")


if __name__ == "__main__":
    main()
