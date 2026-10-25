"""S4 — Chaîne complète : géocodage puis météo, via Open-Meteo (gratuit, sans clé).

Isolé de valise.py : on valide le concept ici avant de l'intégrer.
"""
import requests

# Étape 1 : géocodage (ville -> pays, coordonnées)
url_geo = "https://geocoding-api.open-meteo.com/v1/search?name=Hanoi&count=1&language=fr"
reponse_geo = requests.get(url_geo)
ville = reponse_geo.json()["results"][0]
print(ville["country"], ville["latitude"], ville["longitude"])

# Étape 2 : météo actuelle à ces coordonnées
url_meteo = (
    f"https://api.open-meteo.com/v1/forecast"
    f"?latitude={ville['latitude']}&longitude={ville['longitude']}"
    f"&current=temperature_2m,precipitation"
)
reponse_meteo = requests.get(url_meteo)
meteo = reponse_meteo.json()["current"]
print(meteo["temperature_2m"], "°C —", meteo["precipitation"], "mm de pluie")
