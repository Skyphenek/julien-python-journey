"""Tests d'avis.py : les retours de cuisson (logique pure, sans base)."""
import sys
from datetime import date, timedelta
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pytest
from avis import RAISONS_MOINS, RAISONS_PLUS, JOURS_A_NOTER, valider_avis, a_noter, resume

J = date(2026, 11, 14)


def plat(id_, genre="plat", nom=None):
    return {"id": id_, "nom": nom or id_, "genre": genre}


def repas(jour, moment, *plats, issue="fait"):
    return {"jour": jour, "moment": moment, "plats": list(plats), "issue": issue}


def avis(plat_, jour, moment, qui, note, raisons=(), mot=""):
    return {"plat": plat_, "jour": jour, "moment": moment, "qui": qui, "note": note, "raisons": list(raisons), "mot": mot}


def test_raisons():
    assert {c for c, _ in RAISONS_MOINS} >= {"trop-sale", "fade", "trop-cuit", "sec", "trop-long"}
    assert {c for c, _ in RAISONS_PLUS} >= {"a-refaire", "la-sauce", "rapide"}
    assert not {c for c, _ in RAISONS_MOINS} & {c for c, _ in RAISONS_PLUS}
    assert JOURS_A_NOTER == 3


def test_valider_avis():
    a = valider_avis({"plat": "plat-carbonara", "jour": "2026-11-13", "moment": "diner", "qui": "laetitia",
                      "note": 4, "raisons": ["la-sauce", "trop-sale"], "mot": "  un peu salé  "}, J)
    assert a == {"plat": "plat-carbonara", "jour": date(2026, 11, 13), "moment": "diner", "qui": "laetitia",
                 "note": 4, "raisons": ["la-sauce", "trop-sale"], "mot": "un peu salé"}
    sans = valider_avis({"plat": "plat-carbonara", "jour": "2026-11-13", "moment": "diner", "qui": "julien",
                         "note": None}, J)
    assert sans["note"] is None and sans["raisons"] == []          # « Pas d'avis » : enregistré, sans note


@pytest.mark.parametrize("changement", [
    {"qui": "paul"}, {"note": 6}, {"note": 0}, {"note": True}, {"raisons": ["inconnue"]}, {"raisons": "trop-sale"},
    {"moment": "gouter"}, {"jour": "hier"}, {"mot": "x" * 301}, {"plat": "x"}, {"jour": "2026-12-01"},
])
def test_valider_avis_refuse(changement):
    corps = {"plat": "plat-carbonara", "jour": "2026-11-13", "moment": "diner", "qui": "julien", "note": 3,
             **changement}
    with pytest.raises(ValueError):
        valider_avis(corps, J)


def test_a_noter_les_plats_faits_des_3_derniers_jours_pas_encore_notes_par_moi():
    plats = [plat("plat-a"), plat("acc-b", "accompagnement"), plat("dessert-c", "dessert"), plat("plat-d")]
    les_repas = [repas(J - timedelta(days=1), "diner", "plat-a", "acc-b", "dessert-c"),
                 repas(J - timedelta(days=2), "dejeuner", "plat-d", issue="commande"),     # pas fait maison
                 repas(J - timedelta(days=5), "diner", "plat-d"),                          # trop vieux
                 repas(J, "diner", "plat-d", issue=None)]                                  # pas encore mangé
    deja = [avis("dessert-c", J - timedelta(days=1), "diner", "julien", 5)]
    hier = (J - timedelta(days=1)).isoformat()
    assert a_noter(les_repas, plats, deja, "julien", J) == [
        {"plat": "plat-a", "nom": "plat-a", "jour": hier, "moment": "diner"}]
    assert [x["plat"] for x in a_noter(les_repas, plats, deja, "laetitia", J)] == ["plat-a", "dessert-c"]


def test_resume_par_plat():
    tous = [avis("plat-a", J, "diner", "julien", 4, ["la-sauce", "trop-sale"]),
            avis("plat-a", J, "diner", "laetitia", 5, ["la-sauce"]),
            avis("plat-a", J - timedelta(days=7), "diner", "julien", 2, ["trop-sale", "sec"]),
            avis("plat-b", J, "diner", "julien", None)]                     # pas d'avis : ne compte pas
    r = resume(tous)
    assert r["plat-a"] == {"moyenne": 3.7, "nb": 3, "julien": 4, "laetitia": 5,
                           "raisons": ["la-sauce", "trop-sale", "sec"]}
    assert "plat-b" not in r
