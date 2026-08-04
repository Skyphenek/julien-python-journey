"""Tests de valise.py — fonctions pures et règle d'accumulation."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))   # permet d'importer valise depuis ce dossier

from valise import (total_jours, jours_par_type,
                    statut_ue_itineraire, prises_itineraire)

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

def test_statut_ue_hors_ue_si_une_etape_hors_ue():
    itin = [{"destination": "France", "jours": 3, "mois": 6},
            {"destination": "Thaïlande", "jours": 5, "mois": 1}]
    hors_ue, inconnu = statut_ue_itineraire(itin)
    assert hors_ue is True
    assert inconnu is False


def test_statut_ue_ue_si_toutes_ue():
    itin = [{"destination": "France", "jours": 3, "mois": 6},
            {"destination": "Italie", "jours": 5, "mois": 6}]
    hors_ue, inconnu = statut_ue_itineraire(itin)
    assert hors_ue is False
    assert inconnu is False


def test_statut_ue_inconnu_declenche_le_flag():
    itin = [{"destination": "Tokyo", "jours": 3, "mois": 6}]   # ville -> statut inconnu
    hors_ue, inconnu = statut_ue_itineraire(itin)
    assert hors_ue is True
    assert inconnu is True


def test_prises_itineraire_dedup_et_sans_aucun():
    itin = [{"destination": "France", "jours": 3, "mois": 6},     # aucun
            {"destination": "Vietnam", "jours": 5, "mois": 1},    # universel
            {"destination": "Cambodge", "jours": 4, "mois": 1}]   # universel
    assert prises_itineraire(itin) == {"universel"}