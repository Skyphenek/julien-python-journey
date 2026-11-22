"""Tests des Propositions : créneaux libres, passages, validation, règles de la page."""
import json
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pytest
from propositions import creneaux, jours_du_voyage

J = lambda n: date(2026, 12, n)
MARRAKECH = {"depart": J(10), "itineraire": [{"destination": "Marrakech", "jours": 4}]}


def resa(genre, titre, jour, heure="", jour_fin=None, heure_fin="", lieu=""):
    return {"type": genre, "titre": titre, "jour": jour, "heure": heure, "jour_fin": jour_fin,
            "heure_fin": heure_fin, "lieu": lieu}


RESAS = [resa("vol", "AF1276", J(10), "12:40", None, "15:05"),
         resa("hotel", "Dar Baraka", J(10), "14:00", J(11), "12:00", "Bab Doukkala"),
         resa("resto", "Terrasse des épices", J(10), "19:30"),
         resa("activite", "Désert d'Agafay", J(11)),
         resa("hotel", "Agafay palm", J(11), "15:00", J(13), "11:00"),
         resa("activite", "Tombeaux saadiens", J(13)),
         resa("hotel", "Bab Akoul", J(13), "12:00", J(14), "12:00"),
         resa("vol", "AF1077", J(14), "13:05", None, "17:25")]


def vus(voyage, reservations):
    return [(c["id"], c["debut"], c["fin"], c["ancre"]) for c in creneaux(voyage, reservations)]


def test_creneaux_de_marrakech():
    assert vus(MARRAKECH, RESAS) == [
        ("2026-12-10-apres-midi", "16:35", "19:30", "Dar Baraka"),
        ("2026-12-11-matin", "09:00", "12:00", "Dar Baraka"),
        ("2026-12-11-apres-midi", "15:00", "18:00", "Agafay palm"),
        ("2026-12-11-soir", "18:00", "22:30", "Agafay palm"),
        ("2026-12-12-matin", "09:00", "13:00", "Agafay palm"),
        ("2026-12-12-apres-midi", "13:00", "18:00", "Agafay palm"),
        ("2026-12-12-soir", "18:00", "22:30", "Agafay palm"),
        ("2026-12-13-matin", "09:00", "11:00", "Agafay palm"),
        ("2026-12-13-apres-midi", "12:00", "18:00", "Bab Akoul"),
        ("2026-12-13-soir", "18:00", "22:30", "Bab Akoul")]


def test_creneau_porte_adresse_et_etape():
    c = creneaux(MARRAKECH, RESAS)[0]
    assert (c["jour"], c["periode"], c["adresse"], c["destination"], c["rang"]) == (
        J(10), "après-midi", "Bab Doukkala", "Marrakech", 1)


def test_jours_prolonges_par_le_retour():
    assert jours_du_voyage(MARRAKECH, RESAS) == [J(n) for n in range(10, 15)]
    assert jours_du_voyage(MARRAKECH, []) == [J(n) for n in range(10, 14)]


def test_vol_de_nuit_escale_et_changement_d_etape():
    d = lambda n: date(2027, 1, n)
    voyage = {"depart": d(15), "itineraire": [{"destination": "Hanoï", "jours": 3}, {"destination": "Ha Long", "jours": 2}]}
    resas = [resa("vol", "A", d(15), "21:00", d(16), "05:00"), resa("vol", "B", d(16), "07:00", None, "16:00"),
             resa("hotel", "H1", d(16), "", d(18)), resa("transport", "bus", d(18), "08:00", None, "11:00"),
             resa("hotel", "H2", d(18), "14:00", d(19)), resa("vol", "C", d(19), "20:00", d(20), "06:00")]
    v = vus(voyage, resas)
    assert v[0] == ("2027-01-16-apres-midi", "17:30", "22:30", "H1")     # rien pendant l'escale ; 30 min isolées rattachées
    assert ("2027-01-18-apres-midi", "14:00", "18:00", "H2") in v and not any(x[0] == "2027-01-18-matin" for x in v)
    assert v[-1] == ("2027-01-19-apres-midi", "13:00", "17:00", "H2")     # 3 h avant le vol


def test_activite_avec_heure_coupe_la_journee():
    v = vus(MARRAKECH, RESAS + [resa("activite", "Cours de cuisine", J(12), "10:30", None, "12:00")])
    assert [x[1:3] for x in v if x[0].startswith("2026-12-12")] == [("09:00", "10:30"), ("12:00", "18:00"), ("18:00", "22:30")]


def test_deux_creneaux_de_la_meme_periode():
    v = vus(MARRAKECH, RESAS + [resa("activite", "Thé", J(12), "15:00", None, "16:00")])
    assert [x[0] for x in v if "2026-12-12-apres" in x[0]] == ["2026-12-12-apres-midi", "2026-12-12-apres-midi-2"]


def test_vol_interieur_sans_heure_prend_la_journee():
    v = vus(MARRAKECH, RESAS + [resa("transport", "bus", J(12))])
    assert not any(x[0].startswith("2026-12-12") for x in v)


def test_sans_reservation_ni_itineraire():
    assert vus(MARRAKECH, [])[0] == ("2026-12-10-apres-midi", "15:00", "18:00", "Marrakech")
    assert creneaux({"depart": J(10), "itineraire": []}, []) == []
