# ============================================================
# CONCEPT : Dictionnaire — pattern GROUP BY
# SESSION : S2
# ============================================================


# ----------------------------------------------------------------
# NIVEAU 1 — Trous à remplir
# ----------------------------------------------------------------
"""
transactions = [
    ("Cooltra", 12.50), ("Monoprix", 34.20), ("Cooltra", 8.90),
    ("Amazon", 156.00), ("Monoprix", 15.60), ("Cooltra", 6.80),
]

total_par_commercant = ???    # dict vide

for desc, montant in transactions:
    if desc not in ???:
        ???[desc] = ???       # initialise la clé à 0
    ???[desc] += ???          # accumule

for commercant, total in ???.items():
    print(f"{commercant} : {total:.2f} €")
"""


# ----------------------------------------------------------------
# NIVEAU 2 — Partir de zéro
# ----------------------------------------------------------------
"""
import csv

# Avec revolut.csv, construis 2 dicts en une seule lecture :
#   total_par_commercant  : {desc: total_€}
#   nb_par_commercant     : {desc: nb_transactions}

# Puis affiche pour chaque commerçant (trié par total décroissant) :
# "Cooltra          | 156.02 €  |  23 fois  |  moy: 6.78 €"
#
# Bonus : affiche une ligne de séparation entre chaque commerçant
# et mets en majuscule le commerçant le plus dépensier
"""


# ----------------------------------------------------------------
# NIVEAU 3 — Piège volontaire
# ----------------------------------------------------------------
"""
# Ce code est censé compter les transactions par type.
# Il tourne mais le résultat est incomplet. Pourquoi ?

import csv

nb_par_type = {}

with open('revolut.csv', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for ligne in reader:
        type_t = ligne['Type']
        nb_par_type[type_t] = nb_par_type[type_t] + 1

for t, nb in nb_par_type.items():
    print(f"{t} : {nb}")
"""

# SOLUTION NIVEAU 3 :
"""
# Bug : accès à nb_par_type[type_t] avant que la clé existe → KeyError
# Fix : initialiser la clé si absente
with open('revolut.csv', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for ligne in reader:
        type_t = ligne['Type']
        if type_t not in nb_par_type:
            nb_par_type[type_t] = 0       # ← initialisation manquante
        nb_par_type[type_t] += 1
"""
