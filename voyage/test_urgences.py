"""Tests du bloc Urgences (rubrique Sur place) et de la tâche Ariane."""
import sys
from datetime import date
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from urgences import URGENCES
from formalites import FORMALITES
from valise import urgences_du_voyage, lien_tel, avant_de_partir, construire, rendre_page, VERSION_PAGE


def test_un_bloc_par_pays_de_la_table_formalites():
    assert set(URGENCES) == set(FORMALITES)
    for code, u in URGENCES.items():
        assert u["numeros"] or u["ambassade"], code
        for libelle, numero in u["numeros"]:
            assert numero.replace(" ", "").lstrip("+").isdigit(), (code, numero)


def test_numeros_cles():
    assert ("Police", "113") in URGENCES["VN"]["numeros"]
    assert ("Urgences", "000") in URGENCES["AU"]["numeros"]
    assert URGENCES["US"]["ambassade"]["telephone"] is None       # tronqué sur la page officielle : omis


def test_lien_tel():
    assert lien_tel("+84 24 3944 57 00") == "tel:+842439445700"
    assert lien_tel("113") == "tel:113"


def etape(nom, pays):
    return {"destination": nom, "jours": 5, "code_pays": pays}


def test_urgences_du_voyage():
    u = urgences_du_voyage([etape("Rome", "IT"), etape("Hanoï", "VN"), etape("Pékin", "CN"), etape("Hué", "VN")])
    assert [x["pays"] for x in u] == ["Union européenne", "Vietnam", "Pékin (CN)"]
    assert u[0]["numeros"] == [("Urgences (toute l'UE)", "112")]
    assert u[2]["numeros"] == [] and "diplomatie.gouv.fr" in u[2]["lien"]
    assert "contacts-utiles" in u[1]["lien"]


def test_ariane_seulement_pour_un_pays_a_zones_deconseillees():
    t = {x["id"]: x for x in avant_de_partir([etape("Siem Reap", "KH")], date(2027, 1, 10), date(2026, 10, 27))}
    assert "Ariane" in t["ariane"]["texte"] and "frontière thaïlandaise" in t["ariane"]["texte"]
    assert t["ariane"]["lien"].startswith("https://www.diplomatie.gouv.fr")
    assert "ariane" not in {x["id"] for x in avant_de_partir([etape("Hanoï", "VN")], date(2027, 1, 10), date(2026, 10, 27))}
    assert avant_de_partir([etape("Rome", "IT")], date(2027, 1, 10), date(2026, 10, 27)) == []


def test_page_bloc_urgences_dans_sur_place():
    voyage = {"depart": date(2027, 1, 10), "personnes": ["Julien"], "conduit": False, "lessive": None,
              "itineraire": [dict(etape("Hanoï", "VN"), mois=1, activites=[], normales=None)]}
    html = rendre_page(voyage, construire(voyage))
    sur_place = html.split('<div class="rubrique" data-rubrique="sur-place"')[1].split('<div class="rubrique"')[0]
    assert sur_place.index('class="info depenses"') < sur_place.index('class="info urgences"')
    assert 'href="tel:113"' in sur_place and "57 Tran Hung Dao" in sur_place
    assert "banque" in sur_place                                   # opposition carte : le numéro de ta banque
    assert VERSION_PAGE >= 15
