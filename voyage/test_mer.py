"""Tests des recettes de Poissons Démasqués (recettes_mer.py)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pytest
from carnet_depart import CARNET_DEPART, A_TESTER
from catalogue import chercher
from courses import PLACARD_DEPART, normaliser
from db import connecter, semer_placard, semer_carnet, lire_plats, ajouter_recettes
from diners import GENRES
from recettes_air_fryer import AIR_FRYER
from recettes_legumes import LEGUMES
from recettes_mer import NOM_REPRISE, MER, MER_JULIEN, JAMAIS_LAETITIA


@pytest.fixture
def conn():
    c = connecter("valise_test")
    with c.cursor() as cur:
        cur.execute("TRUNCATE soirs, plats, courses, placard, reprises")
    c.commit()
    semer_placard(c, PLACARD_DEPART)
    semer_carnet(c, CARNET_DEPART, A_TESTER)
    yield c
    c.close()


def test_donnees():
    ids = [p["id"] for p in MER + MER_JULIEN]
    assert len(MER) == 13 and len(ids) == len(set(ids))
    assert not set(ids) & {p["id"] for p in CARNET_DEPART + A_TESTER + AIR_FRYER + LEGUMES}
    for p in MER + MER_JULIEN:
        assert p["genre"] in dict(GENRES) and p["recette"].startswith("Pour ")
        assert [i for i in p["ingredients"] if not chercher(i)] == [], p["id"]   # tout est au catalogue
    assert all(p["nom"].endswith("(Julien)") and p["note"].startswith("Pour Julien") for p in MER_JULIEN)


def test_rien_de_ses_jamais_dans_les_plats_du_couple():
    for p in MER:
        for i in p["ingredients"]:
            assert not any(j in normaliser(i) for j in JAMAIS_LAETITIA), (p["id"], i)


def test_ajout(conn):
    assert ajouter_recettes(conn, NOM_REPRISE, MER + MER_JULIEN) == len(MER) + len(MER_JULIEN)
    conn.commit()
    plats = {p["id"]: p for p in lire_plats(conn)}
    assert plats["mer-paella"]["statut"] == "a-tester" and plats["mer-brandade"]["nom"].endswith("(Julien)")
    assert ajouter_recettes(conn, NOM_REPRISE, MER + MER_JULIEN) is None
