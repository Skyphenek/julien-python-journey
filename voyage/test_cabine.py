"""Tests du mode « bagage cabine seulement » (par voyage)."""
import sys
from datetime import date
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from valise import (faire_valise, construire, rendre_page, voyage_depuis_formulaire, formulaire_initial,
                    formulaire_en_html, PLAFOND_CABINE, SAC_LIQUIDES, VERSION_PAGE)


def valise(jours, cabine, types=None, personnes=("Julien", "Laetitia")):
    return faire_valise(types or {"ville": jours}, jours, list(personnes), False, False, cabine=cabine)


def test_vetements_plafonnes_a_quatre():
    v = valise(7, cabine=True)
    assert PLAFOND_CABINE == 4
    assert v["Julien"]["Sous-vêtements"]["caleçons"] == 4
    assert v["Julien"]["Vêtements"]["t-shirts"] == 4
    assert valise(7, cabine=False)["Julien"]["Sous-vêtements"]["caleçons"] == 7


def test_court_sejour_inchange():
    assert valise(3, cabine=True)["Julien"]["Sous-vêtements"]["caleçons"] == 3


def test_pas_de_chaussures_de_rechange():
    assert "chaussures de rechange" not in valise(3, cabine=True)["Julien"]["Chaussures"]


def test_batons_interdits_en_cabine():
    types = {"montagne": 3}
    assert "bâtons" in valise(3, False, types)["Julien"]["Divers"]
    assert "bâtons" not in valise(3, True, types)["Julien"]["Divers"]


def test_sac_liquides_partage():
    assert valise(3, cabine=True)["Partagé"]["Hygiène"][SAC_LIQUIDES] == 1
    assert SAC_LIQUIDES not in valise(3, cabine=False)["Partagé"]["Hygiène"]


ROME = {"depart": date(2027, 3, 5), "personnes": ["Julien"], "conduit": False, "lessive": None,
        "itineraire": [{"destination": "Rome", "jours": 6, "mois": 3, "code_pays": "IT",
                        "activites": ["ville"], "normales": None}]}


def test_construire_lit_le_reglage_du_voyage():
    assert construire({**ROME, "cabine": True})["valise"]["Julien"]["Sous-vêtements"]["caleçons"] == 4
    assert construire(ROME)["valise"]["Julien"]["Sous-vêtements"]["caleçons"] == 6     # absent = soute


def test_page_affiche_le_mode_cabine():
    v = {**ROME, "cabine": True}
    assert "Bagage cabine" in rendre_page(v, construire(v))
    assert "Bagage cabine" not in rendre_page(ROME, construire(ROME))
    assert VERSION_PAGE >= 4


def test_formulaire_case_cabine():
    corps = {"depart": "2027-03-05", "personnes": "j", "cabine": True,
             "etapes": [{"destination": "Rome", "latitude": 41.9, "longitude": 12.5, "jours": 6}]}
    assert voyage_depuis_formulaire(corps)["cabine"] is True
    assert voyage_depuis_formulaire({**corps, "cabine": None})["cabine"] is False
    assert 'id="cabine"' in formulaire_en_html()
    initial = formulaire_initial({**ROME, "code": "2027-03-05 Rome", "cabine": True})
    assert initial["cabine"] is True
