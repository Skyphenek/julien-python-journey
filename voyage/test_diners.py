"""Tests de diners.py : carnet, semaine, secours, ingrédients à acheter, compteur Deliveroo (logique pure)."""
import sys
from datetime import date, timedelta
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pytest
from diners import (valider_plat, valider_soir, secours, a_acheter, compteur, semaine, diners_en_html, disponibles,
                    SECOURS_MINUTES)
from carnet_depart import CARNET_DEPART, A_TESTER
from courses import PLACARD_DEPART, normaliser

AUJ = date(2026, 10, 28)


def plat(id_, nom, minutes=15, ingredients=(), genre="plat", statut="carnet", archive=False):
    return {"id": id_, "nom": nom, "genre": genre, "minutes": minutes, "ingredients": list(ingredients),
            "recette": "", "lien": "", "note": "", "statut": statut, "archive": archive}


def placard(*en_stock, epuises=(), bientot=()):
    return ([{"cle": normaliser(n), "nom": n, "en_stock": True, "bientot": False} for n in en_stock]
            + [{"cle": normaliser(n), "nom": n, "en_stock": True, "bientot": True} for n in bientot]
            + [{"cle": normaliser(n), "nom": n, "en_stock": False, "bientot": False} for n in epuises])


def habituel(nom, actif=False, pris=False):
    return {"nom": nom, "actif": actif, "pris": pris, "recurrent": True}


# --- Validation ---

def test_valider_plat_complet():
    p = valider_plat({"id": "plat-test-01", "nom": " Carbonara ", "genre": "plat", "minutes": 20,
                      "ingredients": [" Œufs ", "pecorino", "", "œufs"], "recette": "1. Cuire.",
                      "lien": "https://ricette.giallozafferano.it/x.html", "note": "", "statut": "carnet"})
    assert p["nom"] == "Carbonara" and p["ingredients"] == ["Œufs", "pecorino"]     # vides et doublons retirés
    assert p["archive"] is False and p["minutes"] == 20


@pytest.mark.parametrize("modif", [
    {"id": "court"}, {"nom": ""}, {"genre": "apero"}, {"minutes": 0}, {"minutes": 601}, {"minutes": "20"},
    {"minutes": True}, {"ingredients": "œufs"}, {"ingredients": ["x" * 61]}, {"ingredients": ["a"] * 41},
    {"lien": "javascript:alert(1)"}, {"lien": "ftp://x"}, {"statut": "poubelle"}, {"recette": "x" * 20001},
])
def test_valider_plat_refuse(modif):
    corps = {"id": "plat-test-01", "nom": "Carbonara", "genre": "plat", "minutes": 20, "ingredients": [],
             "recette": "", "lien": "", "note": "", "statut": "carnet", **modif}
    with pytest.raises(ValueError):
        valider_plat(corps)


def test_valider_soir():
    assert valider_soir({"jour": "2026-10-27", "issue": "commande"}, AUJ) == {
        "jour": date(2026, 10, 27), "plat": None, "issue": "commande"}
    assert valider_soir({"jour": "2026-10-30", "plat": "plat-carbonara"}, AUJ)["plat"] == "plat-carbonara"
    for corps in ({"jour": "hier"}, {"jour": "2026-10-28", "issue": "deliveroo"}, {"jour": "2025-01-01"},
                  {"jour": "2027-01-01"}, {"jour": "2026-10-28", "plat": "x"}, None):
        with pytest.raises(ValueError):
            valider_soir(corps, AUJ)


# --- Semaine, secours, courses ---

def test_semaine_glissante():
    assert semaine(AUJ) == [AUJ + timedelta(days=i) for i in range(7)]


def test_secours_faisables_et_presque():
    plats = [plat("plat-carbonara", "Carbonara", 20, ["spaghetti", "œufs", "pecorino"]),
             plat("plat-baguezza1", "Baguezza", 15, ["demi-baguettes", "passata", "mozzarella"]),
             plat("plat-lent-0001", "Lasagne", 300, ["oeufs"]),
             plat("plat-archive01", "Vieux", 10, [], archive=True),
             plat("plat-atester01", "Shakshuka", 15, [], statut="a-tester"),
             plat("dessert-00001", "Mousse", 10, ["œufs"], genre="dessert")]
    p = placard("spaghetti", "Oeufs", "pecorino", "demi-baguettes", epuises=("passata",))
    faisables, presque = secours(plats, p)
    assert [x["nom"] for x in faisables] == ["Carbonara"]
    assert presque == [{"plat": plats[1], "manquants": ["passata", "mozzarella"]}]
    assert SECOURS_MINUTES == 20


def test_disponibles_placard_et_habituels_ranges():
    p = placard("spaghetti", bientot=("pecorino",), epuises=("guanciale",))
    courses = [habituel("Œufs"),                                   # rangé : on en a
               habituel("Lait", actif=True),                       # sur la liste : il en manque
               habituel("Beurre", actif=True, pris=True),          # dans le panier : on en a
               {"nom": "Riz", "actif": True, "pris": False, "recurrent": False}]
    assert disponibles(p, courses) == {"spaghetti", "pecorino", "oeufs", "beurre"}


def test_secours_avec_les_frais_en_habituels():
    carbo = plat("plat-carbonara", "Carbonara", 20, ["spaghetti", "œufs", "pecorino"])
    p = placard("spaghetti", "pecorino")
    assert secours([carbo], p, [habituel("œufs")])[0] == [carbo]
    assert secours([carbo], p, [habituel("œufs", actif=True)])[0] == []


def test_secours_sur_le_carnet_de_depart():
    # Le placard plein du 31/10 rend 7 dîners de secours possibles
    faisables, _ = secours([dict(p, statut="carnet", archive=False) for p in CARNET_DEPART],
                           placard(*PLACARD_DEPART))
    assert len(faisables) == 7


def test_a_acheter_sans_doublon_ni_stock():
    plats = [plat("plat-carbonara", "Carbonara", 20, ["spaghetti", "œufs", "pecorino", "guanciale"]),
             plat("plat-amatricia", "Amatriciana", 35, ["spaghetti", "guanciale", "Tomates pelées"])]
    courses = [{"nom": "Guanciale", "actif": True, "pris": False, "recurrent": False},   # déjà sur la liste
               {"nom": "pecorino", "actif": True, "pris": True, "recurrent": False}]    # pris : n'empêche pas
    p = placard("spaghetti", epuises=("œufs",))
    assert a_acheter(plats, p, courses) == [("œufs", "plat-carbonara"), ("pecorino", "plat-carbonara"),
                                            ("Tomates pelées", "plat-amatricia")]


# --- Compteur Deliveroo ---

def test_compteur():
    soirs = [{"jour": AUJ - timedelta(days=d), "plat": None, "issue": "commande"} for d in (1, 3, 10, 20, 41, 42)]
    soirs += [{"jour": AUJ - timedelta(days=2), "plat": None, "issue": "fait"}]
    c = compteur(soirs, AUJ)
    assert c["semaine"] == 2                     # J-1 et J-3 (7 derniers jours, aujourd'hui compris)
    assert c["moyenne"] == pytest.approx(5 / 6)  # J-42 hors des 6 semaines
    assert c["renseignes"] == 6                 # sur les 6 semaines


def test_compteur_vide():
    assert compteur([], AUJ) == {"semaine": 0, "moyenne": 0, "renseignes": 0}


# --- Carnet de départ et page ---

def test_carnet_de_depart_valide():
    for p in CARNET_DEPART + A_TESTER:
        valider_plat({**p, "statut": "carnet"})


def test_page_diners():
    html = diners_en_html()
    assert "<title>Dîners · Casa Binomerie</title>" in html
    assert 'data-hub="diners" class="actif"' in html
    for vue in ("ce-soir", "semaine", "carnet", "a-tester"):
        assert f'data-vue="{vue}"' in html
    assert "function envoyerOuGarder" in html and "wakeLock" in html
