# Challenge 04 — Dictionnaires (pattern GROUP BY)
# Objectif : agréger des données sans pandas

transactions = [
    ("Cooltra", 12.50), ("Monoprix", 34.20), ("Cooltra", 8.90),
    ("Amazon", 156.00), ("Monoprix", 15.60), ("Cooltra", 6.80),
    ("Franprix", 22.00), ("Amazon", 43.20), ("Uber Eats", 28.90),
    ("Cooltra", 11.20), ("Uber Eats", 34.50), ("Monoprix", 67.80),
]

# LEVEL 1 — Total par commerçant
total_par_commercant = ???

# LEVEL 2 — Nombre de transactions par commerçant
nb_par_commercant = ???

# LEVEL 3 — Moyenne par commerçant (total / nb)
# Affiche : "Cooltra : moy 9.85 € sur 4 transactions"

# LEVEL 4 — Quel commerçant a le plus grand nombre de transactions ?

# LEVEL 5 — Top 3 par total dépensé (avec sorted + lambda)

# --- SOLUTION ---
"""
total_par_commercant = {}
nb_par_commercant = {}

for desc, montant in transactions:
    if desc not in total_par_commercant:
        total_par_commercant[desc] = 0
        nb_par_commercant[desc] = 0
    total_par_commercant[desc] += montant
    nb_par_commercant[desc] += 1

for desc in total_par_commercant:
    total = total_par_commercant[desc]
    nb = nb_par_commercant[desc]
    print(f"{desc} : moy {total/nb:.2f} € sur {nb} transactions")

max_desc = max(nb_par_commercant, key=lambda x: nb_par_commercant[x])
print(f"Plus de transactions : {max_desc} ({nb_par_commercant[max_desc]})")

top3 = sorted(total_par_commercant.items(), key=lambda x: x[1], reverse=True)[:3]
for desc, total in top3:
    print(f"{desc} : {total:.2f} €")
"""
