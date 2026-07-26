# ============================================================
# CONCEPT : try / except — gestion des erreurs
# SESSION : S3
# ============================================================


# ----------------------------------------------------------------
# NIVEAU 1 — Trous à remplir
# ----------------------------------------------------------------
"""
valeurs = ["-12.50", "-34.20", "N/A", "-8.90", "", "abc", "-156.00"]

total   = 0
erreurs = 0

for v in valeurs:
    ???:
        total += abs(float(???))
    except ???:
        erreurs += 1
        print(f"Valeur ignorée : '{v}'")

print(f"Total : {total:.2f} € | Erreurs : {erreurs}")
# Attendu : Total : 211.60 € | Erreurs : 3
"""


# ----------------------------------------------------------------
# NIVEAU 2 — Partir de zéro
# ----------------------------------------------------------------
"""
import csv

# Avec revolut.csv, lis toutes les lignes en gérant les erreurs :
# - Si 'Amount' est absent ou non-convertible → ignore la ligne, compte l'erreur
# - Si 'Type' est absent → ignore la ligne, compte l'erreur
# - Si tout va bien → accumule dans total_carte (paiements carte)
#
# Affiche à la fin :
# "573 lignes traitées | 0 erreurs | Total : 13 643.13 €"
#
# Bonus : écris les lignes en erreur dans un fichier errors.txt
"""


# ----------------------------------------------------------------
# NIVEAU 3 — Piège volontaire
# ----------------------------------------------------------------
"""
# Ce code gère les erreurs mais il a un défaut grave.
# Le script tourne, mais tu ne sauras jamais si quelque chose a vraiment planté.
# Identifie le problème et corrige-le.

import csv

total = 0

try:
    with open('revolut.csv', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for ligne in reader:
            if ligne['Type'] == 'Paiement par carte':
                montant = abs(float(ligne['Amount']))
                total += montant
                moyenne = total / 0    # bug volontaire — division par zéro
except Exception:
    pass

print(f"Total : {total:.2f} €")
"""

# SOLUTION NIVEAU 3 :
"""
# Bug 1 : except Exception + pass = silence total → on avale TOUS les bugs
#   → toujours logger : except Exception as e: print(f"Erreur : {e}")
# Bug 2 : le try couvre 50 lignes → on ne sait pas où ça plante
#   → cibler le bloc minimal qui peut échouer
# Bug 3 : division par zéro silencieuse → résultat faux sans avertissement

import csv
total = 0
erreurs = 0

try:
    with open('revolut.csv', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for ligne in reader:
            try:                                        # try ciblé
                if ligne['Type'] == 'Paiement par carte':
                    total += abs(float(ligne['Amount']))
            except (ValueError, KeyError) as e:
                erreurs += 1
                print(f"Ligne ignorée : {e}")          # jamais silencieux
except FileNotFoundError:
    print("Fichier revolut.csv introuvable")

print(f"Total : {total:.2f} € | Erreurs : {erreurs}")
"""
