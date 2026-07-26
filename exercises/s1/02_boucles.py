# ============================================================
# CONCEPT : Boucle for + accumulateur
# SESSION : S1
# ============================================================


# ----------------------------------------------------------------
# NIVEAU 1 — Trous à remplir
# ----------------------------------------------------------------
"""
montants = [12.50, 34.20, 8.90, 156.00, 23.10]

total = ???          # initialise l'accumulateur

for m in ???:        # boucle sur la liste
    total = total + ???

print(f"Total : {total:.2f} €")
print(f"Moyenne : {??? / ???:.2f} €")
"""


# ----------------------------------------------------------------
# NIVEAU 2 — Partir de zéro
# ----------------------------------------------------------------
"""
# Tu as cette liste de montants Revolut (déjà positifs) :
montants = [12.50, 34.20, 8.90, 156.00, 23.10, 67.80, 9.40, 234.50, 18.20, 45.00]

# Objectif — calcule et affiche :
# 1. Le total
# 2. La moyenne
# 3. Le montant maximum (sans utiliser max())
# 4. Le nombre de montants supérieurs à 50 €
# 5. Ce que représente Cooltra si on imagine que les 3 premiers sont Cooltra
#    → "Cooltra : X € soit Y% du total"
"""


# ----------------------------------------------------------------
# NIVEAU 3 — Piège volontaire
# ----------------------------------------------------------------
"""
# Ce code est censé calculer le total des montants > 20€.
# Il tourne sans erreur mais donne un mauvais résultat. Pourquoi ?

montants = [12.50, 34.20, 8.90, 156.00, 23.10]

for m in montants:
    total = 0
    if m > 20:
        total = total + m

print(f"Total > 20€ : {total:.2f} €")
# Résultat attendu : 213.30 €
# Résultat obtenu : ???

# Corrige le code pour obtenir 213.30 €
"""

# SOLUTION NIVEAU 3 :
"""
# Bug : total = 0 est DANS la boucle → reset à chaque tour
# Fix : sortir l'initialisation avant la boucle
montants = [12.50, 34.20, 8.90, 156.00, 23.10]
total = 0               # ← ici, avant la boucle
for m in montants:
    if m > 20:
        total = total + m
print(f"Total > 20€ : {total:.2f} €")   # 213.30 €
"""
