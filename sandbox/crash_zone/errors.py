# 💥 CRASH ZONE — Reproduire des erreurs pour les comprendre
# Décommente un bloc à la fois, lis l'erreur, comprends pourquoi

# --- ERREUR 1 : = vs == ---
# x = 5
# if x = 5:    # SyntaxError
#     print("ok")

# --- ERREUR 2 : String + Number ---
# total = "10" + 5    # TypeError

# --- ERREUR 3 : Indentation ---
# for i in range(3):
# print(i)    # IndentationError

# --- ERREUR 4 : KeyError dict ---
# d = {"Cooltra": 12.50}
# print(d["Monoprix"])    # KeyError

# --- ERREUR 5 : Float precision ---
# print(0.1 + 0.2)    # pas 0.3 !
# print(0.1 + 0.2 == 0.3)    # False !

# --- ERREUR 6 : Accumulateur dans la boucle ---
# montants = [10, 20, 30]
# for m in montants:
#     total = 0        # reset à chaque tour !
#     total += m
# print(total)    # affiche 30, pas 60

# --- ERREUR 7 : CSV sans cast ---
# valeurs = ["12.50", "34.20"]
# total = 0
# for v in valeurs:
#     total += v    # TypeError : can only concatenate str to str

# --- ERREUR 8 : Division par zéro ---
# nb = 0
# print(100 / nb)    # ZeroDivisionError
