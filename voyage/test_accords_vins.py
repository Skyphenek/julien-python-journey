"""Tests des accords mets-vins (accords_vins.py) : profils des plats, choix du vin du soir."""
import sys
from datetime import date
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from accords_vins import PROFILS, PAR_INGREDIENT, SEUIL_BELLE, profils_du_plat, profils_du_repas, suggerer
from catalogue import chercher
from carnet_depart import CARNET_DEPART

MARDI = date(2026, 11, 3)
SAMEDI = date(2026, 11, 7)
DIMANCHE = date(2026, 11, 8)


def plat(id_):
    return next(p for p in CARNET_DEPART if p["id"] == id_)


def vin(id_, accords, quantite=1, debut=2026, fin=2028, prix_haut=15, nom=None):
    return {"id": id_, "nom": nom or id_, "quantite": quantite, "debut": debut, "fin": fin,
            "prix_haut": prix_haut, "accords": list(accords)}


def test_profils_et_table():
    assert PROFILS == ["boeuf", "agneau", "gibier", "volaille", "porc", "charcuterie", "poisson", "fruits-de-mer",
                       "fromage", "epice", "tomate", "legumes", "apero", "dessert"]
    assert set(PAR_INGREDIENT) <= set(PROFILS)
    assert [n for noms in PAR_INGREDIENT.values() for n in noms if not chercher(n)] == []   # noms du catalogue
    assert SEUIL_BELLE == 30


def test_profils_de_plats_reels():
    assert profils_du_plat(plat("plat-boeuf-bourguignon"))[0] == "boeuf"
    assert "charcuterie" in profils_du_plat(plat("plat-boeuf-bourguignon"))
    assert profils_du_plat(plat("plat-poulet-roti")) == ["volaille"]
    assert profils_du_plat(plat("plat-carbonara")) == ["charcuterie", "fromage"]
    assert profils_du_plat(plat("plat-cacio-e-pepe")) == ["fromage"]
    assert profils_du_plat(plat("plat-taco-monday")) == ["boeuf", "fromage", "epice"]
    assert profils_du_plat(plat("plat-lasagne-bolognese"))[0] == "boeuf"


def test_plat_sans_viande_ni_poisson_ni_fromage():
    sans = {"id": "x", "genre": "plat", "ingredients": ["courgettes", "aubergines", "huile d'olive"]}
    assert profils_du_plat(sans) == ["legumes"]
    rien = {"id": "y", "genre": "plat", "ingredients": ["spaghetti", "huile d'olive"]}
    assert profils_du_plat(rien) == []


def test_genres():
    assert profils_du_plat(plat("dessert-brownie")) == ["dessert"]
    assert profils_du_plat(plat("acc-puree-robuchon")) == []          # un accompagnement ne compte pas


def test_profils_du_repas():
    principal, secondaires = profils_du_repas([plat("acc-gratin-dauphinois"), plat("plat-boeuf-bourguignon"),
                                               plat("dessert-tiramisu")])
    assert principal == "boeuf"
    assert secondaires == ["charcuterie", "dessert"]          # ordre de priorité, sans le principal
    assert profils_du_repas([plat("acc-puree-robuchon")]) == (None, [])
    assert profils_du_repas([]) == (None, [])


def test_suggestion_ordre_et_plafond():
    cave = [vin("a", ["volaille"], fin=2030), vin("b", ["boeuf"], fin=2029, prix_haut=20),
            vin("c", ["boeuf", "charcuterie"], fin=2030), vin("d", ["boeuf"], fin=2029, prix_haut=12),
            vin("e", ["boeuf"], fin=2027)]
    ids = [b["id"] for b in suggerer(cave, "boeuf", ["charcuterie"], MARDI)]
    assert ids == ["c", "e", "d"]                     # 3 points ; puis fin la plus proche ; puis le moins cher


def test_suggestion_ecarte():
    cave = [vin("vide", ["boeuf"], quantite=0), vin("garde", ["boeuf"], debut=2027),
            vin("hors", ["poisson"]), vin("belle", ["boeuf"], prix_haut=SEUIL_BELLE + 1),
            vin("trente", ["boeuf"], prix_haut=SEUIL_BELLE)]
    assert [b["id"] for b in suggerer(cave, "boeuf", [], MARDI)] == ["trente"]
    assert [b["id"] for b in suggerer(cave, "boeuf", [], DIMANCHE)] == ["trente"]
    assert [b["id"] for b in suggerer(cave, "boeuf", [], SAMEDI)] == ["trente", "belle"]


def test_suggestion_belle_bouteille():
    cave = [vin("petite", ["boeuf"]), vin("belle", ["boeuf"], prix_haut=55), vin("autre", ["poisson"], prix_haut=90),
            vin("sans-prix", ["boeuf"], prix_haut=None)]
    assert [b["id"] for b in suggerer(cave, "boeuf", [], MARDI, belle=True)] == ["belle"]


def test_suggestion_prix_inconnu_en_dernier_et_rien_qui_colle():
    cave = [vin("sans-prix", ["boeuf"], prix_haut=None), vin("prix", ["boeuf"], prix_haut=25)]
    assert [b["id"] for b in suggerer(cave, "boeuf", [], MARDI)] == ["prix", "sans-prix"]
    assert suggerer(cave, "poisson", [], MARDI) == []
    assert suggerer(cave, None, [], MARDI) == []
