# Challenge 02 — Boucles for + accumulateur
# Objectif : maîtriser le pattern SUM à la main

montants = [12.50, 34.20, 8.90, 156.00, 23.10, 67.80, 9.40]

# LEVEL 1 — Calcule le total avec une boucle
total = ???

# LEVEL 2 — Calcule la moyenne
moyenne = ???

# LEVEL 3 — Trouve le montant maximum (sans max())
max_montant = ???

# LEVEL 4 — Compte combien de montants dépassent 20 €
nb_superieurs = ???

# LEVEL 5 — Affiche chaque montant avec son rang
# attendu :
# 1. 12.50 €
# 2. 34.20 €
# ...

# --- SOLUTION ---
"""
total = 0
for m in montants:
    total += m
print(f"Total : {total:.2f} €")

moyenne = total / len(montants)
print(f"Moyenne : {moyenne:.2f} €")

max_montant = 0
for m in montants:
    if m > max_montant:
        max_montant = m
print(f"Max : {max_montant:.2f} €")

nb_superieurs = 0
for m in montants:
    if m > 20:
        nb_superieurs += 1
print(f"Supérieurs à 20€ : {nb_superieurs}")

for i, m in enumerate(montants, 1):
    print(f"{i}. {m:.2f} €")
"""
