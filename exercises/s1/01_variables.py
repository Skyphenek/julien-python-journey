# ============================================================
# CONCEPT : Variables et types
# SESSION : S1
# ============================================================
# NIVEAUX :
#   [1] Trous à remplir   → décommenter le bloc NIVEAU 1
#   [2] Partir de zéro    → décommenter le bloc NIVEAU 2
#   [3] Piège volontaire  → décommenter le bloc NIVEAU 3
#
# UNE FOIS TERMINÉ : mets à jour ton tracker
#   → ouvre progress.html dans ton navigateur
# ============================================================


# ----------------------------------------------------------------
# NIVEAU 1 — Trous à remplir
# ----------------------------------------------------------------
# Décommente ce bloc et remplace les ???

"""
nom      = ???        # ton prénom (str)
age      = ???        # ton âge (int)
solde    = ???        # un solde bancaire ex: 1342.50 (float)
actif    = ???        # True ou False (bool)

# Affiche le type de chaque variable
print(type(???))
print(type(???))
print(type(???))
print(type(???))

# Convertis le string "-12.50" en float positif
montant_str = "-12.50"
montant = ???(???( montant_str ))
print(f"Montant : {montant:.2f} €")
"""


# ----------------------------------------------------------------
# NIVEAU 2 — Partir de zéro
# ----------------------------------------------------------------
# Décommente ce bloc et écris le code toi-même

"""
# Tu as ces données brutes (comme si elles venaient d'un CSV) :
desc_str    = "Cooltra"
montant_str = "-12.50"
nb_str      = "168"
actif_str   = "True"

# Objectif :
# 1. Convertis chaque valeur dans le bon type Python
# 2. Affiche le type de chacune avec type()
# 3. Calcule : montant_positif = valeur absolue du montant
# 4. Affiche : "Cooltra : 12.50 € (168 fois)"
"""


# ----------------------------------------------------------------
# NIVEAU 3 — Piège volontaire
# ----------------------------------------------------------------
# Ce code a 3 bugs. Trouve-les et corrige-les SANS regarder la solution.

"""
nom = "Julien
age = 43.0
total = "12.50" + "34.20"

print(f"Je m'appelle {nom}, j'ai {age} ans")
print(f"Total : {total:.2f} €")
"""

# SOLUTION NIVEAU 3 (à ne lire qu'après avoir cherché) :
"""
# Bug 1 : string non fermée → nom = "Julien"
# Bug 2 : age devrait être int → age = 43
# Bug 3 : on additionne des strings → total = float("12.50") + float("34.20")
nom = "Julien"
age = 43
total = float("12.50") + float("34.20")
print(f"Je m'appelle {nom}, j'ai {age} ans")
print(f"Total : {total:.2f} €")
"""
