"""Tests des repas composés : validation, rangement (diners.py), base (db.py)."""
import sys
from datetime import date, timedelta
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pytest
from casa import aujourd_hui_paris
from carnet_depart import CARNET_DEPART, A_TESTER
from courses import PLACARD_DEPART
from db import connecter, semer_carnet, semer_placard, lire_plats, enregistrer_repas, lire_repas
from diners import valider_repas, ranger

AUJ = date(2026, 10, 28)

J = aujourd_hui_paris()


@pytest.fixture
def conn():
    c = connecter("valise_test")
    with c.cursor() as cur:
        cur.execute("TRUNCATE repas, plats, courses, placard, reprises")
    c.commit()
    semer_placard(c, PLACARD_DEPART)
    semer_carnet(c, CARNET_DEPART, A_TESTER)
    yield c
    c.close()


def statut(conn, id_):
    return next(p for p in lire_plats(conn) if p["id"] == id_)["statut"]


# --- Base ---

def test_enregistrer_et_lire_un_repas(conn):
    enregistrer_repas(conn, {"jour": J, "moment": "diner", "plats": ["plat-carbonara", "tester-pesto"], "issue": None})
    enregistrer_repas(conn, {"jour": J, "moment": "brunch", "plats": ["tester-shakshuka"], "issue": None})
    assert lire_repas(conn, J, J) == [
        {"jour": J, "moment": "brunch", "plats": ["tester-shakshuka"], "issue": None},
        {"jour": J, "moment": "diner", "plats": ["plat-carbonara", "tester-pesto"], "issue": None}]
    enregistrer_repas(conn, {"jour": J, "moment": "diner", "plats": ["plat-carbonara"], "issue": "commande"})
    assert lire_repas(conn, J, J)[1] == {"jour": J, "moment": "diner", "plats": ["plat-carbonara"], "issue": "commande"}


def test_un_repas_vide_est_supprime(conn):
    enregistrer_repas(conn, {"jour": J, "moment": "dejeuner", "plats": ["plat-carbonara"], "issue": None})
    enregistrer_repas(conn, {"jour": J, "moment": "dejeuner", "plats": [], "issue": None})
    assert lire_repas(conn, J, J) == []
    enregistrer_repas(conn, {"jour": J, "moment": "diner", "plats": [], "issue": "dehors"})     # une issue suffit
    assert lire_repas(conn, J, J) == [{"jour": J, "moment": "diner", "plats": [], "issue": "dehors"}]


def test_fait_maison_fait_entrer_au_carnet_tous_les_plats_a_tester(conn):
    r = {"jour": J, "moment": "diner", "plats": ["tester-pesto", "tester-shakshuka", "plat-carbonara"], "issue": None}
    enregistrer_repas(conn, r)
    assert statut(conn, "tester-pesto") == "a-tester"
    enregistrer_repas(conn, {**r, "issue": "fait"})
    assert statut(conn, "tester-pesto") == statut(conn, "tester-shakshuka") == "carnet"


def test_plus_de_table_soirs():
    """La reprise repas-v1 faite (01/11/2026), la table soirs n'existe plus : appliquer_schema la supprime."""
    from appliquer_schema import tables
    from pathlib import Path
    schema = (Path(__file__).parent / "schema.sql").read_text()
    assert "CREATE TABLE IF NOT EXISTS soirs" not in schema and "DROP TABLE IF EXISTS soirs" in schema
    c = connecter("valise_test")
    try:
        with c.cursor() as cur:
            assert "soirs" not in tables(cur)
    finally:
        c.close()


def test_valider_repas():
    assert valider_repas({"jour": "2026-10-30", "moment": "brunch", "plats": ["plat-carbonara", "tester-pesto"]}, AUJ) == {
        "jour": date(2026, 10, 30), "moment": "brunch", "plats": ["plat-carbonara", "tester-pesto"], "issue": None}
    assert valider_repas({"jour": "2026-10-27", "moment": "diner", "issue": "commande"}, AUJ)["plats"] == []


@pytest.mark.parametrize("corps", [
    None, {"moment": "diner"}, {"jour": "2026-12-31", "moment": "diner"}, {"jour": "2026-10-28", "moment": "gouter"},
    {"jour": "2026-10-28", "moment": "diner", "plats": "plat-carbonara"},
    {"jour": "2026-10-28", "moment": "diner", "plats": ["plat-carbonara", "plat-carbonara"]},
    {"jour": "2026-10-28", "moment": "diner", "plats": [f"plat-numero-{i}" for i in range(9)]},
    {"jour": "2026-10-28", "moment": "diner", "plats": ["x"]},
    {"jour": "2026-10-28", "moment": "diner", "issue": "livre"},
    {"jour": "2026-10-28", "moment": ["diner"]},
    {"jour": "2026-10-28", "moment": "diner", "issue": {"a": 1}}])
def test_valider_repas_refuse(corps):
    with pytest.raises(ValueError):
        valider_repas(corps, AUJ)


def test_ranger_dans_l_ordre_du_service():
    dessert, plat, entree, accomp = ({"id": g, "genre": g} for g in ("dessert", "plat", "entree", "accompagnement"))
    assert [p["genre"] for p in ranger([dessert, plat, entree, accomp], "diner")] == [
        "entree", "plat", "accompagnement", "dessert"]
    assert [p["genre"] for p in ranger([dessert, plat, entree], "brunch")] == ["dessert", "plat", "entree"]
