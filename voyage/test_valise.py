"""Tests de valise.py — fonctions pures et règle d'accumulation."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))   # permet d'importer valise depuis ce dossier

from valise import total_jours, jours_par_type


def test_total_jours():
    itin = [{"destination": "Hanoï", "jours": 7, "mois": 1},
            {"destination": "Siem Reap", "jours": 4, "mois": 1},
            {"destination": "Phu Quoc", "jours": 7, "mois": 1}]
    assert total_jours(itin) == 18


def test_jours_par_type_additionne_les_etapes():
    # janvier, zone asie_sud_est -> ["chaud", "plage"] pour les deux villes
    itin = [{"destination": "Hanoï", "jours": 7, "mois": 1},
            {"destination": "Siem Reap", "jours": 4, "mois": 1}]
    jpt = jours_par_type(itin)
    assert jpt["chaud"] == 11
    assert jpt["plage"] == 11


def test_jours_par_type_type_sur_une_seule_etape():
    # étape d'été asie_sud_est -> ["chaud", "plage", "pluie"] ; pluie sur cette étape seule
    itin = [{"destination": "Hanoï", "jours": 5, "mois": 1},
            {"destination": "Hanoï", "jours": 3, "mois": 7}]
    jpt = jours_par_type(itin)
    assert jpt["chaud"] == 8
    assert jpt["pluie"] == 3