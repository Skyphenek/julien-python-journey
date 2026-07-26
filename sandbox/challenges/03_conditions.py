# Challenge 03 — Conditions if/elif/else
# Objectif : filtrer et classifier des transactions

transactions = [
    {"type": "Paiement par carte", "montant": -12.50, "desc": "Cooltra"},
    {"type": "Virement reçu",      "montant": 2500.00, "desc": "Salaire"},
    {"type": "Paiement par carte", "montant": -34.20,  "desc": "Monoprix"},
    {"type": "Paiement par carte", "montant": -156.00, "desc": "Amazon"},
    {"type": "Remboursement",      "montant": 12.50,   "desc": "Cooltra"},
    {"type": "Paiement par carte", "montant": -8.90,   "desc": "Cooltra"},
]

# LEVEL 1 — Total des dépenses carte uniquement
total_carte = ???

# LEVEL 2 — Total Cooltra uniquement
total_cooltra = ???

# LEVEL 3 — Classifier chaque transaction
# "grande dépense" si > 50€, "petite dépense" si <= 50€, "crédit" si positif
for t in transactions:
    categorie = ???
    print(f"{t['desc']} → {categorie}")

# LEVEL 4 — Alerte si une transaction dépasse 100€
# Affiche "⚠️ Dépense importante : Amazon 156.00€"

# --- SOLUTION ---
"""
total_carte = 0
total_cooltra = 0
for t in transactions:
    montant = abs(t['montant'])
    if t['type'] == "Paiement par carte":
        total_carte += montant
        if t['desc'] == "Cooltra":
            total_cooltra += montant

for t in transactions:
    if t['montant'] > 0:
        categorie = "crédit"
    elif abs(t['montant']) > 50:
        categorie = "grande dépense"
    else:
        categorie = "petite dépense"
    print(f"{t['desc']} → {categorie}")

for t in transactions:
    if t['type'] == "Paiement par carte" and abs(t['montant']) > 100:
        print(f"⚠️ Dépense importante : {t['desc']} {abs(t['montant']):.2f}€")
"""
