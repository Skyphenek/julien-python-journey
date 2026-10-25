"""Dataset NBA embarqué pour l'Arène.

Offline, déterministe : aucune connexion réseau, aucune dépendance.
Les stats sont INDICATIVES (ordre de grandeur ~saison 2023-24, arrondies) —
le but est de s'entraîner sur des données réalistes, pas de tenir un almanach.

Chaque joueur est un dict :
    nom     (str)   nom complet
    equipe  (str)   code équipe à 3 lettres (DEN, BOS, ...)
    poste   (str)   G (guard) / F (forward) / C (center)
    pts     (float) points par match
    reb     (float) rebonds par match
    ast     (float) passes décisives par match

C'est volontairement le même schéma qu'une table SQL : une "ligne" = un dict,
la liste JOUEURS = la table. Les défis de l'Arène tournent autour de ce dataset.
"""

JOUEURS = [
    {"nom": "Nikola Jokic",        "equipe": "DEN", "poste": "C", "pts": 26.4, "reb": 12.4, "ast": 9.0},
    {"nom": "Luka Doncic",         "equipe": "DAL", "poste": "G", "pts": 33.9, "reb": 9.2,  "ast": 9.8},
    {"nom": "Shai Gilgeous-Alexander","equipe": "OKC","poste": "G","pts": 30.1,"reb": 5.5,  "ast": 6.2},
    {"nom": "Giannis Antetokounmpo","equipe": "MIL", "poste": "F", "pts": 30.4, "reb": 11.5, "ast": 6.5},
    {"nom": "Jayson Tatum",        "equipe": "BOS", "poste": "F", "pts": 26.9, "reb": 8.1,  "ast": 4.9},
    {"nom": "Joel Embiid",         "equipe": "PHI", "poste": "C", "pts": 34.7, "reb": 11.0, "ast": 5.6},
    {"nom": "Kevin Durant",        "equipe": "PHX", "poste": "F", "pts": 27.1, "reb": 6.6,  "ast": 5.0},
    {"nom": "Stephen Curry",       "equipe": "GSW", "poste": "G", "pts": 26.4, "reb": 4.5,  "ast": 5.1},
    {"nom": "LeBron James",        "equipe": "LAL", "poste": "F", "pts": 25.7, "reb": 7.3,  "ast": 8.3},
    {"nom": "Anthony Davis",       "equipe": "LAL", "poste": "C", "pts": 24.7, "reb": 12.6, "ast": 3.5},
    {"nom": "Devin Booker",        "equipe": "PHX", "poste": "G", "pts": 27.1, "reb": 4.5,  "ast": 6.9},
    {"nom": "Damian Lillard",      "equipe": "MIL", "poste": "G", "pts": 24.3, "reb": 4.4,  "ast": 7.0},
    {"nom": "Jimmy Butler",        "equipe": "MIA", "poste": "F", "pts": 20.8, "reb": 5.3,  "ast": 5.0},
    {"nom": "Anthony Edwards",     "equipe": "MIN", "poste": "G", "pts": 25.9, "reb": 5.4,  "ast": 5.1},
    {"nom": "Tyrese Haliburton",   "equipe": "IND", "poste": "G", "pts": 20.1, "reb": 3.9,  "ast": 10.9},
    {"nom": "Domantas Sabonis",    "equipe": "SAC", "poste": "C", "pts": 19.4, "reb": 13.7, "ast": 8.2},
    {"nom": "Bam Adebayo",         "equipe": "MIA", "poste": "C", "pts": 19.3, "reb": 10.4, "ast": 3.9},
    {"nom": "Jalen Brunson",       "equipe": "NYK", "poste": "G", "pts": 28.7, "reb": 3.6,  "ast": 6.7},
]
