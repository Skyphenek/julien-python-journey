"""Premier script API — S4. Interroge REST Countries pour un pays donné.

Isolé de valise.py : on valide le concept ici avant de l'intégrer.
"""
import requests

url = "https://restcountries.com/v3.1/name/vietnam"
reponse = requests.get(url)
print(reponse.status_code)

pays = reponse.json()[0]
print(pays["capital"][0])
