"""Tests du décalage horaire (rubrique Sur place)."""
import sys
from datetime import date
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from valise import (fuseau_de, decalages, texte_decalage, conseil_decalage, construire, rendre_page,
                    HTML_SCRIPT, VERSION_PAGE)


def etape(nom, lat, lon, jours=7):
    return {"destination": nom, "latitude": lat, "longitude": lon, "jours": jours}


VIETNAM = [etape("Hanoï", 21.03, 105.85), etape("Siem Reap", 13.36, 103.86, 4), etape("Phu Quoc", 10.22, 103.96)]


def test_fuseau_depuis_les_coordonnees_hors_ligne():
    assert fuseau_de(etape("Tokyo", 35.68, 139.69)) == "Asia/Tokyo"
    assert fuseau_de({"destination": "X", "jours": 3}) is None


def test_etapes_au_meme_decalage_regroupees():
    d = decalages(VIETNAM, date(2027, 1, 10))
    assert len(d) == 1
    assert d[0]["destinations"] == ["Hanoï", "Siem Reap", "Phu Quoc"] and d[0]["heures"] == 6


def test_heure_d_ete_prise_en_compte():
    # New York en juillet : Paris UTC+2, New York UTC-4 -> -6 h (et non -5 h comme en hiver)
    assert decalages([etape("New York", 40.71, -74.01)], date(2027, 7, 1))[0]["heures"] == -6
    assert decalages([etape("New York", 40.71, -74.01)], date(2027, 1, 10))[0]["heures"] == -6
    assert decalages([etape("New York", 40.71, -74.01)], date(2027, 3, 20))[0]["heures"] == -5   # décalage US/UE


def test_textes():
    assert texte_decalage(6) == "+6 h"
    assert texte_decalage(-6) == "−6 h"
    assert texte_decalage(4.5) == "+4 h 30"
    assert texte_decalage(5.75) == "+5 h 45"
    assert texte_decalage(0) == "même heure qu'à Paris"


def test_conseil_selon_la_direction():
    assert "plus tôt" in conseil_decalage(6)
    assert "plus tard" in conseil_decalage(-6)
    assert conseil_decalage(1) is None and conseil_decalage(-2) is None


def test_page_sur_place_avec_horloges():
    voyage = {"depart": date(2027, 1, 10), "personnes": ["Julien"], "conduit": False, "lessive": None,
              "itineraire": [dict(e, mois=1, code_pays="VN", activites=[], normales=None) for e in VIETNAM]}
    html = rendre_page(voyage, construire(voyage))
    sur_place = html.split('<div class="rubrique" data-rubrique="sur-place"')[1].split('<div class="rubrique"')[0]
    assert "+6 h" in sur_place and "Hanoï, Siem Reap, Phu Quoc" in sur_place
    assert 'data-fuseau="Asia/Bangkok"' in sur_place and "plus tôt" in sur_place
    assert "Intl.DateTimeFormat" in HTML_SCRIPT and VERSION_PAGE >= 8


def test_page_sans_coordonnees_garde_le_texte_a_venir():
    voyage = {"depart": date(2027, 1, 10), "personnes": ["Julien"], "conduit": False, "lessive": None,
              "itineraire": [{"destination": "X", "jours": 3, "mois": 1, "activites": [], "normales": None}]}
    html = rendre_page(voyage, construire(voyage))
    assert "Bientôt" in html.split('data-rubrique="sur-place"')[2]
