depenses = {}
nouveaux = ["Franprix", "Monoprix", "Franprix", "Cooltra", "Monoprix"]
montants = [12.5, 45.0, 8.3, 6.9, 22.1]

for i in range(len(nouveaux)) :
    marchand = nouveaux[i]
    montant = montants[i]
    if marchand not in depenses:
        depenses[marchand] = 0
    depenses[marchand] = depenses[marchand] + montant

print(depenses)