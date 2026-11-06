"""Tests du chef de la Casa (chef.py) : file de passage, lecture, écriture sauvegardée, ligne de commande."""
import sys
from datetime import date
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pytest
from db import connecter, enregistrer_plat, enregistrer_repas
from chef import MARQUEUR, file_de_passage, lire


def plat(id_, **champs):
    return {"id": id_, "nom": id_.title(), "genre": "plat", "minutes": 20, "ingredients": [], "recette": "Pour 2",
            "lien": "", "note": "", "statut": "carnet", "archive": False, "pour": "nous", "accords": []} | champs


@pytest.fixture
def conn():
    c = connecter("valise_test")
    with c.cursor() as cur:
        cur.execute("TRUNCATE repas, plats")
    c.commit()
    yield c
    c.rollback()
    with c.cursor() as cur:                          # ne pas laisser de lignes aux modules suivants
        cur.execute("TRUNCATE repas, plats")
    c.commit()
    c.close()


def faire(conn, jour, *ids):
    enregistrer_repas(conn, {"jour": date(2026, 10, jour), "moment": "diner", "plats": list(ids), "issue": "fait"})


def test_file_les_plus_cuisines_d_abord(conn):
    for id_ in ("a", "b", "c"):
        enregistrer_plat(conn, plat(id_))
    faire(conn, 1, "b")
    faire(conn, 2, "b", "c")
    enregistrer_repas(conn, {"jour": date(2026, 10, 3), "moment": "diner", "plats": ["c"], "issue": "commande"})
    assert [(p["id"], p["faits"]) for p in file_de_passage(conn)] == [("b", 2), ("c", 1), ("a", 0)]


def test_file_carnet_avant_a_tester_puis_genre_puis_nom(conn):
    enregistrer_plat(conn, plat("z-tester", statut="a-tester"))
    enregistrer_plat(conn, plat("y-dessert", genre="dessert"))
    enregistrer_plat(conn, plat("x-plat"))
    enregistrer_plat(conn, plat("w-acc", genre="accompagnement"))
    assert [p["id"] for p in file_de_passage(conn)] == ["x-plat", "w-acc", "y-dessert", "z-tester"]


def test_file_exclut_archives_et_deja_passes(conn):
    enregistrer_plat(conn, plat("vieux", archive=True))
    enregistrer_plat(conn, plat("passe", recette=f"1. Saisir.\n\n{MARQUEUR}\n- Beurre froid."))
    enregistrer_plat(conn, plat("reste"))
    assert [p["id"] for p in file_de_passage(conn)] == ["reste"]


def test_file_limitee_a_n(conn):
    for i in range(7):
        enregistrer_plat(conn, plat(f"p{i}"))
    assert len(file_de_passage(conn)) == 5
    assert len(file_de_passage(conn, n=2)) == 2


def test_lire(conn):
    enregistrer_plat(conn, plat("saltimbocca", recette="Pour 4\n1. Saisir."))
    r = lire(conn, "saltimbocca")
    assert {k: r[k] for k in ("id", "nom", "genre", "pour", "recette")} == {
        "id": "saltimbocca", "nom": "Saltimbocca", "genre": "plat", "pour": "nous", "recette": "Pour 4\n1. Saisir."}
    assert r["maj_le"] is not None
    assert lire(conn, "inconnu") is None
