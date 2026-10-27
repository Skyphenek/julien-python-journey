"""Tests de la checklist « fermer la maison » (rubrique Avant)."""
import sys
from datetime import date, timedelta
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from valise import fermer_la_maison, construire, rendre_page, VERSION_PAGE


def ids(taches):
    return {t["id"] for t in taches}


def test_court_sejour_gaia_reste_seule_avec_ses_provisions():
    t = fermer_la_maison(3, date(2027, 7, 1))
    assert {"gaia-provisions", "fenetres", "poubelles", "appareils"} <= ids(t)
    assert not {"gaia-garde", "gaia-fiche", "gardienne", "eau", "chauffage", "frigo"} & ids(t)
    provisions = next(x for x in t if x["id"] == "gaia-provisions")
    assert "5 jours" in provisions["texte"] and "eau" in provisions["texte"]   # 3 jours + 2 de marge


def test_garde_de_gaia_des_le_quatrieme_jour_avec_les_plantes():
    t = {x["id"]: x for x in fermer_la_maison(4, date(2027, 7, 1))}
    assert "gaia-garde" in t and "gaia-fiche" in t and "plantes" in t["gaia-garde"]["texte"]
    assert "gardienne" in t


def test_long_sejour_d_hiver():
    depart = date(2027, 1, 10)
    t = {x["id"]: x for x in fermer_la_maison(18, depart)}
    assert {"gardienne", "eau", "chauffage", "frigo", "gaia-garde"} <= set(t)
    assert not {"tranquillite", "courrier", "plantes", "voisin"} & set(t)    # gardienne dans l'immeuble
    assert t["gaia-garde"]["quand"] == depart - timedelta(days=14)
    assert t["fenetres"]["quand"] == depart
    assert "du 10/01 au 27/01" in t["gardienne"]["texte"] and "courrier" in t["gardienne"]["texte"]


def test_triee_par_echeance():
    t = fermer_la_maison(18, date(2027, 1, 10))
    assert [x["quand"] for x in t] == sorted(x["quand"] for x in t)


def avant(itin, depart=date(2027, 1, 10)):
    voyage = {"depart": depart, "personnes": ["Julien"], "conduit": False, "lessive": None,
              "itineraire": [dict(e, mois=depart.month, activites=[], normales=None) for e in itin]}
    html = rendre_page(voyage, construire(voyage), aujourd_hui=date(2026, 10, 27))
    return html.split('<div class="rubrique" data-rubrique="avant"')[1].split('<div class="rubrique"')[0]


def test_rubrique_avant_contient_la_maison_meme_en_europe():
    a = avant([{"destination": "Rome", "jours": 4, "code_pays": "IT"}])
    assert "Fermer la maison" in a and "Partagé/Fermer la maison/fenetres" in a
    assert "Avant de partir/visa" not in a and "Rien à préparer" not in a
    assert VERSION_PAGE >= 12


def test_formalites_et_maison_ensemble():
    a = avant([{"destination": "Hanoï", "jours": 7, "code_pays": "VN"}])
    assert a.index("Avant de partir/visa-VN") < a.index("Fermer la maison/fenetres")
