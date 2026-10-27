"""Tests de la carte de nos voyages et des compteurs (accueil)."""
import sys
from datetime import date
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from valise import accueil_en_html, stats_voyages, points_carte


def voyage(code, depart, jours, etapes):
    return {"code": code, "libelle": code[11:], "depart": depart, "fin": depart, "personnes": ["Julien"],
            "etapes": etapes}


def etape(nom, pays, lat=10.0, lon=20.0, jours=5):
    return {"destination": nom, "code_pays": pays, "latitude": lat, "longitude": lon, "jours": jours}


VOYAGES = [
    voyage("2026-11-01 Oslo", date(2026, 11, 1), 5, [etape("Oslo", "NO", 59.9, 10.7, 5)]),
    voyage("2027-01-10 Hanoï › Siem Reap", date(2027, 1, 10), 11,
           [etape("Hanoï", "VN", 21.0, 105.8, 7), etape("Siem Reap", "KH", 13.4, 103.9, 4)]),
    voyage("2027-05-27 New York", date(2027, 5, 27), 7, [etape("New York", "US", 40.7, -74.0, 7)]),
    voyage("2027-06-01 Essai", date(2027, 6, 1), 3, [etape("Nulle part", None, None, None, 3)]),
]


def test_stats_par_annee_la_plus_recente_d_abord():
    assert stats_voyages(VOYAGES) == [
        {"annee": 2027, "voyages": 3, "jours": 21, "pays": 3},       # VN, KH, US (sans code : ignoré)
        {"annee": 2026, "voyages": 1, "jours": 5, "pays": 1},
    ]


def test_points_de_la_carte():
    points = points_carte(VOYAGES, date(2026, 12, 1))
    assert [p["nom"] for p in points] == ["Oslo", "Hanoï", "Siem Reap", "New York"]   # sans coordonnées : absent
    assert points[0]["avenir"] is False and points[1]["avenir"] is True
    assert points[1]["code"] == "2027-01-10 Hanoï › Siem Reap"


def test_accueil_affiche_carte_et_compteurs():
    html = accueil_en_html(VOYAGES, date(2026, 12, 1))
    assert '<div id="carte"' in html and '"nom": "Hanoï"' in html
    assert "sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=" in html          # Leaflet vérifié
    assert "<strong>2027</strong> : 3 voyages · 21 jours · 3 pays" in html
    assert "<strong>2026</strong> : 1 voyage · 5 jours · 1 pays" in html
    assert html.index('id="carte"') < html.index("À venir")


def test_accueil_sans_coordonnees_pas_de_carte():
    html = accueil_en_html([voyage("2027-06-01 Essai", date(2027, 6, 1), 3, [etape("X", None, None, None)])],
                           date(2026, 12, 1))
    assert 'id="carte"' not in html and "leaflet.js" not in html
