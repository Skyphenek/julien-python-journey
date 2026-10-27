"""Tests des devises (rubrique Sur place) : devise de chaque pays, convertisseur."""
import sys
from datetime import date
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from devises import DEVISE_PAR_PAYS
from valise import devises_du_voyage, construire, rendre_page, HTML_SCRIPT, VERSION_PAGE


def test_table_des_devises():
    assert len(DEVISE_PAR_PAYS) >= 250
    assert (DEVISE_PAR_PAYS["VN"], DEVISE_PAR_PAYS["KH"], DEVISE_PAR_PAYS["MA"]) == ("VND", "KHR", "MAD")
    assert DEVISE_PAR_PAYS["FR"] == DEVISE_PAR_PAYS["HR"] == "EUR"
    assert DEVISE_PAR_PAYS["BG"] == "EUR"                       # Bulgarie à l'euro depuis le 01/01/2026


def etape(nom, pays):
    return {"destination": nom, "jours": 5, "code_pays": pays}


def test_devises_regroupees_sans_l_euro():
    itin = [etape("Hanoï", "VN"), etape("Siem Reap", "KH"), etape("Phu Quoc", "VN"), etape("Lisbonne", "PT"),
            etape("Atlantide", None)]
    assert devises_du_voyage(itin) == [
        {"devise": "VND", "destinations": ["Hanoï", "Phu Quoc"], "note": None},
        {"devise": "KHR", "destinations": ["Siem Reap"], "note": None},
        {"devise": "USD", "destinations": ["Siem Reap"], "note": "très utilisé sur place"},
    ]


def test_voyage_en_zone_euro_sans_devise():
    assert devises_du_voyage([etape("Rome", "IT"), etape("Sofia", "BG")]) == []


def page(itin):
    voyage = {"depart": date(2027, 1, 10), "personnes": ["Julien"], "conduit": False, "lessive": None,
              "itineraire": [dict(e, mois=1, activites=[], normales=None) for e in itin]}
    html = rendre_page(voyage, construire(voyage), aujourd_hui=date(2026, 10, 27))
    return html.split('<div class="rubrique" data-rubrique="sur-place"')[1].split('<div class="rubrique"')[0]


def test_page_sur_place_avec_convertisseur():
    sur_place = page([etape("Hanoï", "VN")])
    assert 'data-devise="VND"' in sur_place and "Hanoï" in sur_place
    assert 'class="montant-local"' in sur_place and 'class="montant-eur"' in sur_place
    assert "currency-api" in HTML_SCRIPT and "taux-eur" in HTML_SCRIPT       # taux du jour, gardé hors ligne
    assert VERSION_PAGE >= 11


def test_page_zone_euro_sans_bloc_devises():
    assert 'data-devise=' not in page([etape("Rome", "IT")])
