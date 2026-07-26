# ============================================================
# CONCEPT : APIs REST + JSON
# SESSION : S4
# ============================================================
# pip3 install requests  (si pas déjà fait)
# ============================================================


# ----------------------------------------------------------------
# NIVEAU 1 — Trous à remplir
# ----------------------------------------------------------------
"""
import requests

# API publique GitHub — pas de token nécessaire
url = 'https://api.github.com/users/Skyphenek'

response = requests.???(url, timeout=10)

print(response.???)       # doit afficher 200

data = response.???()     # parse le JSON

print(data[???])          # ton login
print(data[???])          # nombre de repos publics
print(data[???])          # date de création du compte
"""


# ----------------------------------------------------------------
# NIVEAU 2 — Partir de zéro
# ----------------------------------------------------------------
"""
import requests

# Objectif — avec l'API GitHub publique :
# 1. Récupère ton profil (https://api.github.com/users/Skyphenek)
# 2. Récupère la liste de tes repos (https://api.github.com/users/Skyphenek/repos)
# 3. Affiche pour chaque repo : nom, langue, nb de stars, date de création
# 4. Gère les erreurs : status != 200, timeout, ConnectionError
# 5. Formate l'affichage proprement :
#    "julien-python-journey | Python | 0 ⭐ | créé le 13/04/2026"
"""


# ----------------------------------------------------------------
# NIVEAU 3 — Piège volontaire
# ----------------------------------------------------------------
"""
import requests

# Ce code est censé afficher le nom et le bio du profil GitHub.
# Il tourne sur certains profils mais plante sur d'autres. Pourquoi ?

url = 'https://api.github.com/users/Skyphenek'
response = requests.get(url)
data = response.json()

print(data['name'].upper())    # peut planter
print(data['bio'].strip())     # peut planter
print(f"Repos : {data['public_repos']}")
"""

# SOLUTION NIVEAU 3 :
"""
# Bug 1 : pas de vérification du status_code → si 404, data contient un message d'erreur
# Bug 2 : name et bio peuvent être None (champs optionnels GitHub)
#   → .upper() et .strip() sur None → AttributeError

import requests

url = 'https://api.github.com/users/Skyphenek'
response = requests.get(url, timeout=10)

if response.status_code != 200:
    print(f"Erreur {response.status_code}")
else:
    data = response.json()
    name = data.get('name') or 'Non renseigné'    # .get() + fallback
    bio  = data.get('bio')  or 'Pas de bio'
    print(name.upper())
    print(bio.strip())
    print(f"Repos : {data['public_repos']}")
"""
