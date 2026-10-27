"""Tests de la météo automatique à J-10 : ce qui change, et ce que la page sait."""
import sys
from datetime import date
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from valise import difference_valises, construire, rendre_page, HTML_SCRIPT, VERSION_PAGE


def test_difference_ajouts_retraits_quantites():
    avant = {("Julien", "Chaussures", "chaussures imperméables"): 1, ("Julien", "Vêtements", "t-shirts"): 7,
             ("Partagé", "Divers", "sac de jour"): 1}
    apres = {"Partagé": {"Divers": {"sac de jour": 1, "parapluie": 1}},
             "Julien": {"Vêtements": {"t-shirts": 5, "imperméable": 1}, "Chaussures": {}}}
    d = difference_valises(avant, apres)
    assert d["ajouts"] == ["imperméable (Julien)", "parapluie"]
    assert d["retraits"] == ["chaussures imperméables (Julien)"]
    assert d["quantites"] == ["t-shirts (Julien) : 7 → 5"]


def test_difference_sans_photo_avant():
    assert difference_valises({}, {"Julien": {"Vêtements": {"t-shirts": 5}}}) is None


VOYAGE = {"depart": date(2027, 1, 10), "personnes": ["Julien"], "conduit": False, "lessive": None,
          "itineraire": [{"destination": "Hanoï", "jours": 7, "mois": 1, "code_pays": "VN", "activites": [],
                          "normales": None}]}


def test_page_connait_la_date_de_la_derniere_meteo():
    assert "const METEO_DU = null;" in rendre_page(VOYAGE, construire(VOYAGE))
    prevue = {**VOYAGE, "itineraire": [{**VOYAGE["itineraire"][0], "prevision": {
        "tmax": 25.0, "tmin": 18.0, "jours_pluie": 4, "jours_forte_pluie": 1.0, "prevu_le": "2027-01-03"}}]}
    assert 'const METEO_DU = "2027-01-03";' in rendre_page(prevue, construire(prevue))


def test_script_auto_une_fois_par_jour_et_bandeau():
    assert "meteo-auto:" in HTML_SCRIPT                  # une tentative par jour et par téléphone
    assert "METEO_DU" in HTML_SCRIPT and "bandeau-meteo" in HTML_SCRIPT
    assert "sessionStorage" in HTML_SCRIPT               # le bandeau survit au rechargement
    assert VERSION_PAGE >= 9


def test_page_a_le_bandeau():
    assert '<div id="bandeau-meteo" hidden></div>' in rendre_page(VOYAGE, construire(VOYAGE))
