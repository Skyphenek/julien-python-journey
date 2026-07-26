# ============================================================
# CONCEPT : pandas — lecture, filtres, groupby, export
# SESSION : S3
# ============================================================
# pip3 install pandas openpyxl  (si pas déjà fait)
# ============================================================


# ----------------------------------------------------------------
# NIVEAU 1 — Trous à remplir
# ----------------------------------------------------------------
"""
import pandas as ???

df = pd.???(revolut.csv', encoding='utf-8-sig')

print(df.???)           # dimensions (nb lignes, nb colonnes)
print(df.???)           # noms des colonnes
print(df.???())         # 5 premières lignes

# Filtre : paiements carte uniquement
cartes = df[df[???] == ???]

# Colonne calculée
cartes = cartes.copy()
cartes[???] = cartes['Amount'].???()   # valeur absolue

print(f"Total : {cartes[???].sum():.2f} €")
"""


# ----------------------------------------------------------------
# NIVEAU 2 — Partir de zéro
# ----------------------------------------------------------------
"""
import pandas as pd

# Avec revolut.csv, produis un rapport Excel 3 onglets :
#
# Onglet 1 "Résumé" :
#   Métrique          | Valeur
#   Total dépenses    | 13 643.13 €
#   Nb transactions   | 573
#   Moyenne/trans     | 23.81 €
#   Commerçant top    | Amazon
#
# Onglet 2 "Top 15" :
#   Description | Total € | Nb fois | Moyenne €
#   (trié par total décroissant)
#
# Onglet 3 "Détail" :
#   Toutes les lignes paiement carte, colonnes : Date, Description, Montant
#   Triées par montant décroissant
#
# Fichier : rapport_revolut.xlsx
"""


# ----------------------------------------------------------------
# NIVEAU 3 — Piège volontaire
# ----------------------------------------------------------------
"""
import pandas as pd

# Ce code est censé calculer le top 5.
# Il tourne mais le résultat est faux ou génère un warning. Pourquoi ?

df = pd.read_csv('revolut.csv', encoding='utf-8-sig')

cartes = df[df['Type'] == 'Paiement par carte']
cartes['Montant'] = cartes['Amount'].abs()   # ← warning ici

top5 = cartes.groupby('Description')['Montant'].sum()
top5 = top5.sort_values()[:5]

print(top5)
# Problème 1 : warning SettingWithCopyWarning
# Problème 2 : le tri donne les 5 MOINS dépensiers
# Corrige les deux
"""

# SOLUTION NIVEAU 3 :
"""
df = pd.read_csv('revolut.csv', encoding='utf-8-sig')

# Fix 1 : .copy() pour éviter le warning
cartes = df[df['Type'] == 'Paiement par carte'].copy()
cartes['Montant'] = cartes['Amount'].abs()

# Fix 2 : ascending=False pour ordre décroissant
top5 = (
    cartes.groupby('Description')['Montant']
    .sum()
    .sort_values(ascending=False)   # ← ascending=False
    .head(5)
)
print(top5)
"""
