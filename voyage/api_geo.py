"""Premier script API — S4. Géocodage via Open-Meteo (gratuit, sans clé).

Isolé de valise.py : on valide le concept ici avant de l'intégrer.
"""
import requests

url = "https://geocoding-api.open-meteo.com/v1/search?name=Hanoi&count=1&language=fr"
reponse = requests.get(url)
print(reponse.status_code)

data = reponse.json()
ville = data["results"][0]
print(ville["country"])
print(ville["latitude"], ville["longitude"])
