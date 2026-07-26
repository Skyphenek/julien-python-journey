# ============================================================
# CONCEPT : Conditions if / elif / else
# SESSION : S1
# ============================================================


# ----------------------------------------------------------------
# NIVEAU 1 — Trous à remplir
# ----------------------------------------------------------------
"""
transactions = [
    {"type": "Paiement par carte", "montant": -12.50, "desc": "Cooltra"},
    {"type": "Virement reçu",      "montant": 2500.00, "desc": "Salaire"},
    {"type": "Paiement par carte", "montant": -156.00, "desc": "Amazon"},
    {"type": "Paiement par carte", "montant": -8.90,   "desc": "Cooltra"},
]

total_carte = 0

for t in transactions:
    if t[???] == ???:                      # filtre paiements carte
        montant = ???(t["montant"])        # rends positif
        total_carte = total_carte + ???

print(f"Total carte : {total_carte:.2f} €")
"""


# ----------------------------------------------------------------
# NIVEAU 2 — Partir de zéro
# ----------------------------------------------------------------
"""
transactions = [
    {"type": "Paiement par carte", "montant": -12.50,  "desc": "Cooltra"},
    {"type": "Virement reçu",      "montant": 2500.00, "desc": "Salaire"},
    {"type": "Paiement par carte", "montant": -156.00, "desc": "Amazon"},
    {"type": "Paiement par carte", "montant": -8.90,   "desc": "Cooltra"},
    {"type": "Remboursement",      "montant": 12.50,   "desc": "Cooltra"},
    {"type": "Paiement par carte", "montant": -234.50, "desc": "Monoprix"},
]

# Objectif — calcule et affiche :
# 1. Total des paiements par carte uniquement
# 2. Total Cooltra uniquement (dans les paiements carte)
# 3. Pour chaque transaction : affiche "✓ crédit" ou "✗ dépense"
# 4. Alerte si une dépense dépasse 100€ : "⚠ Grosse dépense : Amazon 156.00€"
"""


# ----------------------------------------------------------------
# NIVEAU 3 — Piège volontaire
# ----------------------------------------------------------------
"""
# Ce code est censé compter les crédits ET les débits séparément.
# Il tourne mais les chiffres sont faux. Trouve le(s) bug(s).

transactions = [
    {"type": "Paiement par carte", "montant": -12.50},
    {"type": "Virement reçu",      "montant": 500.00},
    {"type": "Paiement par carte", "montant": -34.20},
    {"type": "Virement reçu",      "montant": 1200.00},
]

total_credits = 0
total_debits  = 0

for t in transactions:
    if t["montant"] > 0:
        total_credits = total_credits + t["montant"]
    if t["montant"] < 0:
        total_debits = total_debits + t["montant"]

print(f"Crédits : {total_credits:.2f} €")    # attendu : 1700.00 €
print(f"Débits  : {total_debits:.2f} €")     # attendu : 46.70 €
# Quel est le vrai résultat ? Pourquoi ? Comment corriger ?
"""

# SOLUTION NIVEAU 3 :
"""
# Bug : total_debits accumule des négatifs → -12.50 + -34.20 = -46.70
# Le code est logiquement correct mais le résultat affiché est -46.70, pas 46.70
# Fix : abs() sur les débits
for t in transactions:
    if t["montant"] > 0:
        total_credits += t["montant"]
    if t["montant"] < 0:
        total_debits += abs(t["montant"])   # ← abs() ici
"""
