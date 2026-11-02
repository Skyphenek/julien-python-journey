"""Tests des recettes rien que pour Laetitia (recettes_laetitia.py)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pytest
from carnet_depart import CARNET_DEPART, A_TESTER
from catalogue import chercher
from courses import PLACARD_DEPART, normaliser
from db import connecter, semer_placard, semer_carnet, lire_plats, ajouter_recettes
from diners import GENRES, valider_plat
from recettes_air_fryer import AIR_FRYER
from recettes_legumes import LEGUMES
from recettes_mer import MER, MER_JULIEN, JAMAIS_LAETITIA
from recettes_laetitia import NOM_REPRISE, LAETITIA


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


def test_donnees():
    ids = [p["id"] for p in LAETITIA]
    assert len(ids) == 9 == len(set(ids))
    assert not set(ids) & {p["id"] for p in CARNET_DEPART + A_TESTER + AIR_FRYER + LEGUMES + MER + MER_JULIEN}
    for p in LAETITIA:
        assert valider_plat({**p, "statut": "a-tester"})["pour"] == "laetitia"
        assert p["genre"] in dict(GENRES) and p["recette"].startswith("Pour ")
        assert [i for i in p["ingredients"] if not chercher(i)] == [], p["id"]
        assert not [i for i in p["ingredients"] if any(j in normaliser(i) for j in JAMAIS_LAETITIA)], p["id"]


def test_ajout(conn):
    assert ajouter_recettes(conn, NOM_REPRISE, LAETITIA) == len(LAETITIA)
    conn.commit()
    plats = {p["id"]: p for p in lire_plats(conn)}
    assert plats["laet-croziflette"]["pour"] == "laetitia" and plats["laet-croziflette"]["statut"] == "a-tester"
