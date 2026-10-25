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
SEUIL_PLUIE_MM = 1.0         # en dessous, une bruine ne compte pas comme "jour de pluie"
SEUIL_FORTE_PLUIE_MM = 5.0   # "vraie" pluie, celle qui mouille : distingue mousson et averses tropicales


def calculer_normales(daily, mois, nb_annees=NB_ANNEES):
    """Fonction pure : à partir du bloc "daily" d'Open-Meteo, calculer les normales du mois."""
    tmax, tmin, jours_pluie, jours_forte_pluie = [], [], 0, 0
    for i, jour in enumerate(daily["time"]):            # jour = "2024-01-10"
        if int(jour[5:7]) != mois:                       # WHERE MONTH(date) = mois
            continue
        if daily["temperature_2m_max"][i] is None:       # mesure manquante -> on saute
            continue
        tmax.append(daily["temperature_2m_max"][i])
        tmin.append(daily["temperature_2m_min"][i])
        if daily["precipitation_sum"][i] >= SEUIL_PLUIE_MM:
            jours_pluie += 1                              # COUNT ... WHERE pluie >= 1
        if daily["precipitation_sum"][i] >= SEUIL_FORTE_PLUIE_MM:
            jours_forte_pluie += 1                        # COUNT ... WHERE pluie >= 5
    return {
        "tmax": round(sum(tmax) / len(tmax), 1),          # AVG(tmax)
        "tmin": round(sum(tmin) / len(tmin), 1),          # AVG(tmin)
        "jours_pluie": round(jours_pluie / nb_annees),    # par mois, en moyenne annuelle
        "jours_forte_pluie": round(jours_forte_pluie / nb_annees, 1),   # gardé à 0.1 près : sert au seuil
    }


def normales_par_mois(daily, nb_annees=NB_ANNEES):
    """Fonction pure : les normales de chaque mois présent dans les données -> {1: {...}, 2: {...}}.
    Équivalent SQL : le même calcul, mais avec GROUP BY MONTH(date) au lieu de WHERE."""
    mois_presents = {int(jour[5:7]) for jour in daily["time"]}
    return {mois: calculer_normales(daily, mois, nb_annees) for mois in sorted(mois_presents)}


def extraire_lieux(reponse_json):
    """Fonction pure : réponse brute du géocodage -> liste de lieux (champs utiles seulement)."""
    lieux = []
    for r in reponse_json.get("results", []):         # clé absente si aucun résultat
        lieux.append({
            "nom": r["name"], "region": r.get("admin1"), "pays": r.get("country"),
            "code_pays": r.get("country_code"),        # code ISO : "VN", "GB"… (stable, sans accents)
            "latitude": r["latitude"], "longitude": r["longitude"],
        })
    return lieux


def lieux(nom, nb=5):
    """Géocodage : les nb lieux qui portent ce nom (homonymes possibles : Bali Inde / Indonésie)."""
    reponse = requests.get(URL_GEO, params={"name": nom, "count": nb, "language": "fr"})
    reponse.raise_for_status()
    return extraire_lieux(reponse.json())


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


def normales_12_mois(latitude, longitude):
    """Un seul appel API -> les normales des 12 mois (de quoi remplir le cache d'un coup)."""
    return normales_par_mois(meteo_10_ans(latitude, longitude))


def normales(latitude, longitude, mois):
    """Normales climatiques d'un mois (1-12) aux coordonnées d'un lieu déjà choisi.

    On passe des coordonnées, pas un nom : sinon on re-géocoderait et on pourrait
    retomber sur un homonyme (Bali -> Inde).
    """
    return calculer_normales(meteo_10_ans(latitude, longitude), mois)


if __name__ == "__main__":
    for ville, mois in [("Londres", 1), ("Hanoï", 1), ("Siem Reap", 1), ("Lima", 7)]:
        lieu = lieux(ville)[0]
        print(ville, mois, lieu["pays"], normales(lieu["latitude"], lieu["longitude"], mois))
