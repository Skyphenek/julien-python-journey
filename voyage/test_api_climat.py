"""Tests de api_climat.py — calcul des normales sur des données factices (sans réseau)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))   # permet d'importer api_climat depuis ce dossier

from api_climat import calculer_normales, extraire_lieux, normales_par_mois

# Mini "table" au format renvoyé par Open-Meteo : 4 jours, sur 2 années différentes.
# Deux jours en janvier, un en février, un en janvier de l'année suivante.
DAILY = {
    "time":               ["2024-01-10", "2024-01-11", "2024-02-01", "2025-01-05"],
    "temperature_2m_max": [8.0,          6.0,          20.0,         7.0],
    "temperature_2m_min": [2.0,          0.0,          10.0,         1.0],
    "precipitation_sum":  [3.0,          0.2,          5.0,          1.0],
}


def test_moyennes_du_mois_seulement():
    # Janvier = 3 jours : max (8+6+7)/3 = 7.0 ; min (2+0+1)/3 = 1.0. Février ignoré.
    n = calculer_normales(DAILY, 1, nb_annees=2)
    assert n["tmax"] == 7.0
    assert n["tmin"] == 1.0


def test_jours_de_pluie_par_mois():
    # Janvier : 3.0 et 1.0 comptent (>= 1 mm), 0.2 non -> 2 jours sur 2 ans = 1 par an
    n = calculer_normales(DAILY, 1, nb_annees=2)
    assert n["jours_pluie"] == 1


def test_jours_de_forte_pluie():
    # Seuls les jours >= 5 mm comptent comme "forte pluie" : 8.0 et 5.0 oui, 3.0 non -> 2 sur 2 ans = 1.0
    daily = {
        "time":               ["2024-01-10", "2024-01-11", "2025-01-12"],
        "temperature_2m_max": [8.0,          6.0,          7.0],
        "temperature_2m_min": [2.0,          0.0,          1.0],
        "precipitation_sum":  [8.0,          5.0,          3.0],
    }
    n = calculer_normales(daily, 1, nb_annees=2)
    assert n["jours_pluie"] == 2            # (3 jours >= 1 mm) / 2 ans = 1.5 -> arrondi à 2
    assert n["jours_forte_pluie"] == 1.0


def test_ignore_les_jours_sans_mesure():
    # Open-Meteo renvoie None quand une mesure manque : il ne faut pas planter
    daily = {
        "time":               ["2024-01-10", "2024-01-11"],
        "temperature_2m_max": [8.0,          None],
        "temperature_2m_min": [2.0,          None],
        "precipitation_sum":  [3.0,          None],
    }
    n = calculer_normales(daily, 1, nb_annees=1)
    assert n["tmax"] == 8.0
    assert n["jours_pluie"] == 1


def test_extraire_lieux_garde_l_essentiel():
    # Même format que la réponse du géocodage : deux homonymes "Bali"
    reponse = {"results": [
        {"name": "Bali", "admin1": "Bengale-Occidental", "country": "Inde",
         "country_code": "IN", "latitude": 22.6, "longitude": 88.3, "population": 5000},
        {"name": "Bali", "admin1": "Bali", "country": "Indonésie",
         "country_code": "ID", "latitude": -8.5, "longitude": 115.1},
    ]}
    lieux = extraire_lieux(reponse)
    assert len(lieux) == 2
    assert lieux[1] == {"nom": "Bali", "region": "Bali", "pays": "Indonésie",
                        "code_pays": "ID", "latitude": -8.5, "longitude": 115.1}


def test_extraire_lieux_aucun_resultat():
    assert extraire_lieux({}) == []          # l'API omet "results" quand rien ne correspond



def test_normales_par_mois_calcule_tous_les_mois_presents():
    par_mois = normales_par_mois(DAILY, nb_annees=2)
    assert set(par_mois) == {1, 2}                    # seuls janvier et février sont dans les données
    assert par_mois[1]["tmax"] == 7.0
    assert par_mois[2]["tmax"] == 20.0


# --- Prévisions (météo J-7) : même format que les normales, pour réutiliser les seuils ---
from datetime import date
from api_climat import fenetre_prevision, normales_depuis_previsions, previsions

AUJOURD_HUI = date(2027, 1, 3)       # portée Open-Meteo : 16 jours -> jusqu'au 18 janvier


def test_fenetre_etape_entierement_couverte():
    assert fenetre_prevision(date(2027, 1, 10), 7, AUJOURD_HUI) == (date(2027, 1, 10), date(2027, 1, 16))


def test_fenetre_etape_a_moitie_couverte_tronquee():
    # 10 -> 19 janvier : 9 jours sur 10 dans la portée (10 -> 18)
    assert fenetre_prevision(date(2027, 1, 10), 10, AUJOURD_HUI) == (date(2027, 1, 10), date(2027, 1, 18))


def test_fenetre_moins_de_la_moitie_couverte():
    # 15 -> 24 janvier : 4 jours sur 10 seulement -> on garde les normales
    assert fenetre_prevision(date(2027, 1, 15), 10, AUJOURD_HUI) is None


def test_fenetre_hors_portee():
    assert fenetre_prevision(date(2027, 2, 1), 5, AUJOURD_HUI) is None


def test_fenetre_etape_deja_commencee():
    # 1 -> 6 janvier, on est le 3 : 4 jours restants sur 6 -> prévision du 3 au 6
    assert fenetre_prevision(date(2027, 1, 1), 6, AUJOURD_HUI) == (date(2027, 1, 3), date(2027, 1, 6))


PREVU = {
    "time":               ["2027-01-10", "2027-01-11", "2027-01-12", "2027-01-13", "2027-01-14", "2027-01-15"],
    "temperature_2m_max": [30.0,         31.0,         29.0,         30.0,         32.0,         28.0],
    "temperature_2m_min": [22.0,         23.0,         21.0,         22.0,         24.0,         20.0],
    "precipitation_sum":  [0.0,          12.0,         0.5,          2.0,          0.0,          0.0],
}


def test_normales_depuis_previsions_meme_format():
    n = normales_depuis_previsions(PREVU)
    assert n["tmax"] == 30.0                        # moyenne des 6 jours
    assert n["tmin"] == 22.0
    # 2 jours >= 1 mm sur 6 -> 10 par mois ; 1 jour >= 5 mm sur 6 -> 5.0 par mois
    assert n["jours_pluie"] == 10
    assert n["jours_forte_pluie"] == 5.0


def test_une_grosse_averse_declenche_le_kway():
    # c'est le seuil validé : 1 jour fort sur une semaine ~ 4/mois -> étiquette pluie/averses
    from valise import types_climat
    assert "averses" in types_climat(normales_depuis_previsions(PREVU))


def test_previsions_appelle_la_bonne_fenetre_et_date_la_source():
    appels = []
    def faux_api(latitude, longitude, debut, fin):
        appels.append((latitude, longitude, debut, fin))
        return PREVU
    n = previsions(10.2, 104.0, date(2027, 1, 10), 6, AUJOURD_HUI, chercher=faux_api)
    assert appels == [(10.2, 104.0, date(2027, 1, 10), date(2027, 1, 15))]
    assert n["tmax"] == 30.0
    assert n["prevu_le"] == "2027-01-03"            # pour afficher "prévision du 03/01"


def test_previsions_hors_portee_sans_appel():
    def interdit(*a):
        raise AssertionError("pas d'appel réseau hors portée")
    assert previsions(10.2, 104.0, date(2027, 3, 1), 6, AUJOURD_HUI, chercher=interdit) is None


def test_previsions_jours_manquants_ignores():
    # l'API peut renvoyer null en bout de portée : ces jours ne comptent pas
    trou = {k: v[:3] + [None] for k, v in PREVU.items() if k != "time"}
    trou["time"] = PREVU["time"][:4]
    n = normales_depuis_previsions(trou)
    assert n["tmax"] == 30.0                        # (30 + 31 + 29) / 3
