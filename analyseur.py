import csv

total_depenses = 0
nombre_transactions = 0
plus_grosse_depense = 0
description_plus_grosse = ""

with open ("revolut.csv", "r", encoding="utf-8") as fichier:
    lecteur = csv.reader(fichier)
    next(lecteur)

    for ligne in lecteur:
        type_transaction = ligne[0]
        description = ligne[4]
        montant = ligne[5]

        if type_transaction == "Paiement par carte":
            montant_nombre = float(montant)
            montant_positif = abs(montant_nombre)

            total_depenses = total_depenses +montant_positif
            nombre_transactions = nombre_transactions + 1

            if montant_positif > plus_grosse_depense:
                plus_grosse_depense = montant_positif
                description_plus_grosse = description

moyenne = total_depenses / nombre_transactions

print("--- ANALYSE REVOLUT ---")
print("Nombre de paiements par carte :", nombre_transactions)
print("Total dépensé :", round(total_depenses,2), "€")
print("Dépense moyenne :", round(moyenne, 2), "€")
print("Plus grosse dépnese :", round(plus_grosse_depense,2), "€", "chez", description_plus_grosse)