"""Tests de api_climat.py — calcul des normales sur des données factices (sans réseau)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))   # permet d'importer api_climat depuis ce dossier

from api_climat import calculer_normales

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
