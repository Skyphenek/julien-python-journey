"""Formalités par pays (visa, santé, à faire avant le départ) — table tenue à la main.

Une ligne par pays où l'on va vraiment : chaque fiche garde sa source officielle et sa date
de vérification. Au-delà de 6 mois, la page affiche « à revérifier » (les règles changent).
Pays absent de la table -> une tâche « vérifier sur France Diplomatie » (jamais de silence).

Sources : France Diplomatie, Conseils aux voyageurs (pages Entrée / séjour et Santé).
"""
from datetime import date

DIPLOMATIE = "https://www.diplomatie.gouv.fr/fr/conseils-aux-voyageurs/conseils-par-pays-destination/"

FORMALITES = {
    "VN": {
        "pays": "Vietnam",
        "verifie_le": date(2026, 10, 27),     # pages mises à jour le 15/09/2026
        "entree": "https://www.diplomatie.gouv.fr/fr/information-par-pays/vietnam/conseils-aux-voyageurs-entree-sejour",
        "sante": "https://www.diplomatie.gouv.fr/fr/information-par-pays/vietnam/conseils-aux-voyageurs-sante",
        "sans_visa_jusqua": 45,               # jours, entrée et sortie incluses (depuis le 15/08/2023)
        "visa": "e-visa (90 jours max) sur le portail officiel evisa.gov.vn, méfiance faux sites",
        "visa_lien": "https://evisa.gov.vn/",
        "assurance_obligatoire": False,
        "taches": [],
    },
    "KH": {
        "pays": "Cambodge",
        "verifie_le": date(2026, 10, 27),     # pages mises à jour le 21/09/2026
        "entree": "https://www.diplomatie.gouv.fr/fr/information-par-pays/cambodge/conseils-aux-voyageurs-entree-sejour",
        "sante": "https://www.diplomatie.gouv.fr/fr/information-par-pays/cambodge/conseils-aux-voyageurs-sante",
        "sans_visa_jusqua": None,             # visa toujours requis
        "visa": "e-visa sur evisa.gov.kh, ou visa à l'arrivée à l'aéroport (environ 40 USD)",
        "visa_lien": "https://www.evisa.gov.kh/",
        "assurance_obligatoire": True,        # hospitalisation + rapatriement
        "taches": [
            # (jours avant le départ, id, texte)
            (3, "e-arrival", "Remplir Cambodia e-arrival avant l'embarquement (QR code demandé à l'immigration)"),
            (7, "usd", "Prévoir des dollars US en espèces (visa, carte pas toujours acceptée)"),
        ],
    },
}
