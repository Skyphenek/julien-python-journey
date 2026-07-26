# ============================================================
# CONCEPT : sorted() + lambda + slices
# SESSION : S2
# ============================================================


# ----------------------------------------------------------------
# NIVEAU 1 — Trous à remplir
# ----------------------------------------------------------------
"""
depenses = {
    "Cooltra": 156.02, "Monoprix": 234.50,
    "Franprix": 89.10, "Amazon": 312.80, "Uber Eats": 178.40,
}

# Top 3 décroissant
top3 = sorted(
    ???.items(),
    key=lambda x: ???,
    reverse=???
)[???]

for commercant, total in top3:
    print(f"{commercant} : {total:.2f} €")
"""


# ----------------------------------------------------------------
# NIVEAU 2 — Partir de zéro
# ----------------------------------------------------------------
"""
import csv

# Avec revolut.csv :
# 1. Construis le dict total_par_commercant (paiements carte uniquement)
# 2. Affiche le top 10 décroissant avec rang :
#    "1.  Amazon           312.80 €"
#    "2.  Monoprix         234.50 €"
#    ...
# 3. Affiche le flop 3 (moins dépensiers)
# 4. Calcule le % que représente le top 1 sur le total général
#    "Amazon représente 12.3% de tes dépenses totales"
"""


# ----------------------------------------------------------------
# NIVEAU 3 — Piège volontaire
# ----------------------------------------------------------------
"""
# Ce code est censé afficher le top 5 des commerçants.
# Il tourne mais le classement est faux. Trouve le bug.

depenses = {
    "Cooltra": 156.02, "Monoprix": 234.50,
    "Franprix": 89.10, "Amazon": 312.80, "Uber Eats": 178.40,
}

top5 = sorted(depenses)[:5]

for item in top5:
    print(item)

# Attendu : Amazon, Monoprix, Uber Eats, Cooltra, Franprix
# Obtenu  : ???
# Pourquoi ? Comment corriger ?
"""

# SOLUTION NIVEAU 3 :
"""
# Bug : sorted(depenses) trie sur les CLÉS (strings) par ordre alphabétique
# → retourne ['Amazon', 'Cooltra', 'Franprix', 'Monoprix', 'Uber Eats']
# Fix : trier sur les valeurs avec .items() + lambda
top5 = sorted(depenses.items(), key=lambda x: x[1], reverse=True)[:5]
for commercant, total in top5:
    print(f"{commercant} : {total:.2f} €")
"""
