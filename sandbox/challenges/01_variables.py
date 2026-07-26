# Challenge 01 — Variables et types
# Objectif : manipuler les 4 types de base + conversions

# LEVEL 1 — Déclare ces variables avec le bon type
nom = ???           # ton prénom
age = ???           # ton âge
solde = ???         # un solde bancaire (ex: 1342.50)
actif = ???         # True ou False

# LEVEL 2 — Affiche le type de chaque variable
# attendu : <class 'str'>, <class 'int'>, <class 'float'>, <class 'bool'>

# LEVEL 3 — Convertis
montant_str = "-12.50"
# → convertis en float, rends positif, affiche avec 2 décimales

# LEVEL 4 — Piège
# Pourquoi "10" + "5" = "105" et pas 15 ?
# Teste-le, puis corrige pour obtenir 15.0

# --- SOLUTION (à ne lire qu'après avoir essayé) ---
"""
nom = "Julien"
age = 43
solde = 1342.50
actif = True

print(type(nom), type(age), type(solde), type(actif))

montant = abs(float(montant_str))
print(f"{montant:.2f} €")

# "10" + "5" = concaténation de strings
print(float("10") + float("5"))   # → 15.0
"""
