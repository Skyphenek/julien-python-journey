# ============================================================
# CONCEPT : CSV DictReader + f-strings
# SESSION : S1
# ============================================================
# NOTE : ces exercices nécessitent revolut.csv dans le même dossier
# Copie-le depuis session-01 ou session-02 si besoin :
#   cp ../session-02-top-commercants/revolut.csv .
# ============================================================


# ----------------------------------------------------------------
# NIVEAU 1 — Trous à remplir
# ----------------------------------------------------------------
"""
import csv

with open('revolut.csv', encoding=???) as f:
    reader = csv.???(f)
    for ligne in reader:
        desc    = ligne[???]
        montant = ligne[???]
        print(f"{???} : {???}")
"""


# ----------------------------------------------------------------
# NIVEAU 2 — Partir de zéro
# ----------------------------------------------------------------
"""
import csv

# Objectif — en une seule lecture du CSV, calcule et affiche :
# 1. Nombre total de transactions
# 2. Total des paiements par carte (positif)
# 3. Nombre de marchands distincts (unique descriptions)
# 4. La ligne formatée la plus chère :
#    "→ Amazon : 156.00 € (Paiement par carte)"
#
# Format d'affichage final :
# ─────────────────────────────
#   Transactions   : 573
#   Total dépenses : 13 643.13 €
#   Marchands uniq : 87
#   Plus grosse dép: Amazon — 156.00 €
# ─────────────────────────────
"""


# ----------------------------------------------------------------
# NIVEAU 3 — Piège volontaire
# ----------------------------------------------------------------
"""
import csv

# Ce script tourne mais affiche des résultats incohérents.
# Trouve les 2 bugs.

total = 0
nb    = 0

with open('revolut.csv') as f:
    reader = csv.DictReader(f)
    for ligne in reader:
        if ligne['Type'] == 'paiement par carte':
            total = total + ligne['Amount']
            nb    = nb + 1

print(f"Total : {total:.2f} €")
print(f"Nb    : {nb}")
"""

# SOLUTION NIVEAU 3 :
"""
# Bug 1 : encoding manquant → caractères corrompus dans 'Type'
#   → with open('revolut.csv', encoding='utf-8-sig') as f:
# Bug 2 : case-sensitive → 'paiement par carte' ≠ 'Paiement par carte'
#   → if ligne['Type'] == 'Paiement par carte':
# Bug 3 : pas de float() → on additionne des strings
#   → total = total + abs(float(ligne['Amount']))
"""
