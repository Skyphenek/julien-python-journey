import csv

total_depenses = 0
nombre_transactions = 0
plus_grosse_depense = 0
nombre_transactions_cooltra = 0
total_depenses_cooltra = 0
premier_cooltra = ""
dernier_cooltra = ""  


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

            if description == "Cooltra" :
                total_depenses_cooltra = total_depenses_cooltra + montant_positif
                nombre_transactions_cooltra = nombre_transactions_cooltra + 1

                if premier_cooltra == "":
                    premier_cooltra = ligne [2]

                dernier_cooltra = ligne [2]

moyenne = total_depenses_cooltra / nombre_transactions_cooltra

print("--- ANALYSE REVOLUT ---")
print("Nombre de paiements par carte :", nombre_transactions)
print("Total dépensé :", round(total_depenses,2), "€")
print("Dépenses Cooltra :", round(total_depenses_cooltra,2), "€")
print("nombre de déplacements Cooltra :", nombre_transactions_cooltra)
print("moyenne :", round(total_depenses_cooltra / nombre_transactions_cooltra,2) )
print("premier cooltra :", premier_cooltra)
print("dernier cooltra :", dernier_cooltra)