"""Normales climatiques d'une ville pour un mois donné, via Open-Meteo (gratuit, sans clé).

Principe : on récupère 10 ans de météo jour par jour (API historique), puis on fait
l'équivalent SQL de :
    SELECT AVG(tmax), AVG(tmin), COUNT(pluie >= 1 mm) / nb_annees
    FROM meteo_10_ans WHERE MONTH(date) = mois
"""
import requests

URL_GEO = "https://geocoding-api.open-meteo.com/v1/search"
URL_ARCHIVE = "https://archive-api.open-meteo.com/v1/archive"
DEBUT, FIN, NB_ANNEES = "2016-01-01", "2025-12-31", 10
SEUIL_PLUIE_MM = 1.0     # en dessous, une bruine ne compte pas comme "jour de pluie"


def calculer_normales(daily, mois, nb_annees=NB_ANNEES):
    """Fonction pure : à partir du bloc "daily" d'Open-Meteo, calculer les normales du mois."""
    tmax, tmin, jours_pluie = [], [], 0
    for i, jour in enumerate(daily["time"]):            # jour = "2024-01-10"
        if int(jour[5:7]) != mois:                       # WHERE MONTH(date) = mois
            continue
        if daily["temperature_2m_max"][i] is None:       # mesure manquante -> on saute
            continue
        tmax.append(daily["temperature_2m_max"][i])
        tmin.append(daily["temperature_2m_min"][i])
        if daily["precipitation_sum"][i] >= SEUIL_PLUIE_MM:
            jours_pluie += 1                              # COUNT ... WHERE pluie >= 1
    return {
        "tmax": round(sum(tmax) / len(tmax), 1),          # AVG(tmax)
        "tmin": round(sum(tmin) / len(tmin), 1),          # AVG(tmin)
        "jours_pluie": round(jours_pluie / nb_annees),    # par mois, en moyenne annuelle
    }


def coordonnees(ville):
    """Géocodage : "Londres" -> (latitude, longitude). None si la ville est introuvable."""
    reponse = requests.get(URL_GEO, params={"name": ville, "count": 1, "language": "fr"})
    resultats = reponse.json().get("results")         # clé absente si aucun résultat
    if not resultats:
        return None
    return resultats[0]["latitude"], resultats[0]["longitude"]


def meteo_10_ans(latitude, longitude):
    """Le FROM : 10 ans de météo jour par jour aux coordonnées données."""
    reponse = requests.get(URL_ARCHIVE, params={
        "latitude": latitude, "longitude": longitude,
        "start_date": DEBUT, "end_date": FIN,
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
        "timezone": "auto",
    })
    reponse.raise_for_status()                        # lève une erreur si l'API répond 4xx/5xx
    return reponse.json()["daily"]


def normales(ville, mois):
    """Point d'entrée : normales climatiques d'une ville pour un mois (1-12)."""
    coords = coordonnees(ville)
    if coords is None:
        return None
    return calculer_normales(meteo_10_ans(*coords), mois)


if __name__ == "__main__":
    for ville, mois in [("Londres", 1), ("Hanoï", 1), ("Siem Reap", 1), ("Lima", 7)]:
        print(ville, mois, normales(ville, mois))
