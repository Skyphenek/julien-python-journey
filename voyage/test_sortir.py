"""Tests de sortir.py : validation, anti-doublon, avis, tirage du week-end, rappels (logique pure)."""
import sys
from datetime import date, timedelta
from pathlib import Path
from random import Random
sys.path.insert(0, str(Path(__file__).parent))

import pytest
from sortir import valider_sortie, cle_titre, cle_lien, doublon, apres_avis, tirer_weekend, rappels

J = date(2026, 11, 13)          # un vendredi


def s(id_, titre="Idée", etat="envie", type_="balade", budget="gratuit", fin=None, le=None, **k):
    return {"id": id_, "titre": titre, "etat": etat, "type": type_, "budget": budget, "debut": None, "fin": fin,
            "le": le, "lien": "", "avis_julien": "oui", "avis_laetitia": "oui", **k}


def test_valider_minimal_et_source():
    v = valider_sortie({"titre": "  Refuge des Fondus ", "source": "julien"}, J)
    assert v["titre"] == "Refuge des Fondus" and v["etat"] == "a-trier"
    assert v["avis_julien"] == "oui" and v["avis_laetitia"] is None          # ajout à la main = son « ça me tente »
    assert valider_sortie({"titre": "X", "source": "routine"}, J)["avis_julien"] is None


@pytest.mark.parametrize("modif", [{"titre": ""}, {"titre": "x" * 201}, {"type": "piscine"}, {"budget": "cher"},
                                   {"reservation": "peut-etre"}, {"lien": "ftp://x"}, {"source": "chat"},
                                   {"fin": "2026-13-01"}, {"debut": "2026-12-10", "fin": "2026-12-01"}])
def test_valider_refuse(modif):
    with pytest.raises(ValueError):
        valider_sortie({"titre": "X", "source": "routine", **modif}, J)


def test_cles_de_doublon():
    assert cle_titre("Le Refuge des Fondus !") == cle_titre("refuge  des fondus")
    assert cle_lien("https://www.x.fr/expo/?utm=1") == cle_lien("http://www.x.fr/expo")
    existantes = [s("a", "Atelier cosmétiques en duo chez Aroma-Zone", etat="ecartee", lien="https://aroma-zone.com/atelier")]
    assert doublon({"titre": "atelier cosmetiques en duo chez aroma zone", "lien": ""}, existantes) == "a"
    assert doublon({"titre": "Autre", "lien": "https://aroma-zone.com/atelier/"}, existantes) == "a"
    assert doublon({"titre": "Autre", "lien": ""}, existantes) is None


def test_avis():
    x = s("a", etat="a-trier", avis_julien="oui", avis_laetitia=None)
    assert apres_avis(x, "laetitia", "oui")["etat"] == "envie"
    assert apres_avis(x, "laetitia", "non")["etat"] == "ecartee"
    assert apres_avis(s("b", etat="a-trier", avis_julien=None, avis_laetitia=None), "julien", "oui")["etat"] == "a-trier"
    with pytest.raises(ValueError):
        apres_avis(x, "gaia", "oui")


def test_tirage_priorite_fin_proche_une_premium_types_varies():
    envies = [s("fin", type_="expo", fin=J + timedelta(days=10)), s("p1", type_="concert", budget="premium"),
              s("p2", type_="theatre", budget="premium"), s("b1", type_="balade"), s("b2", type_="balade"),
              s("faite", etat="faite")]
    for graine in range(30):
        t = tirer_weekend(envies, J, Random(graine))
        ids = [x["id"] for x in t]
        assert 2 <= len(t) <= 3 and ids[0] == "fin" and "faite" not in ids
        assert sum(x["budget"] == "premium" for x in t) <= 1
        assert len({x["type"] for x in t}) == len(t)


def test_tirage_ignore_fin_passee_et_rend_ce_qu_il_peut():
    assert tirer_weekend([s("vieux", fin=J - timedelta(days=1))], J, Random(1)) == []
    assert [x["id"] for x in tirer_weekend([s("seul")], J, Random(1))] == ["seul"]


def test_rappels():
    sorties = [s("fin", fin=J + timedelta(days=5)), s("loin", fin=J + timedelta(days=20)),
               s("prevue", etat="prevue", le=J + timedelta(days=1)), s("passee", etat="prevue", le=J - timedelta(days=2))]
    r = rappels(sorties, J)
    assert [x["id"] for x in r["finissent"]] == ["fin"] and [x["id"] for x in r["prevues"]] == ["prevue"]
    assert r["weekend"] is True and rappels(sorties, J - timedelta(days=4))["weekend"] is False
