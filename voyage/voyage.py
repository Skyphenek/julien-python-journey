"""Assistant de voyage — itinéraire, budget et valise (Vietnam + Cambodge, janv. 2027).

Application Python des concepts Exercism (listes, dicts, boucles, dates).
Données de démo à ajuster avec le vrai plan.
"""

from datetime import date, timedelta

# Date de départ du voyage.
DEPART = date(2027, 1, 10)

# Itinéraire : liste d'étapes (ville, nombre de nuits). Ordre = ordre du voyage.
ETAPES = [
    ("Hanoï", 3),
    ("Baie d'Halong", 2),
    ("Hoi An", 3),
    ("Siem Reap (Angkor)", 3),
    ("Phnom Penh", 2),
    ("Kampot", 3),
    ("Ho Chi Minh", 2),
]


def planifier_itineraire(depart, etapes):
    """Afficher la date d'arrivée à chaque étape à partir de la date de départ.

    Pour chaque étape, on affiche la date puis on avance du nombre de nuits.
    """
    # TODO (Julien) : parcourir les étapes en avançant une date "jour" étape après étape
    pass


def main():
    """Lance l'assistant sur les données de démo."""
    planifier_itineraire(DEPART, ETAPES)


if __name__ == "__main__":
    main()
