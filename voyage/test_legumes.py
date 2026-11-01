"""Tests des matchs de Légumes Démasqués (recettes_legumes.py) et du retrait du brocoli air fryer."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pytest
from carnet_depart import CARNET_DEPART, A_TESTER
from courses import PLACARD_DEPART, normaliser
from db import connecter, semer_placard, semer_carnet, lire_plats, ajouter_recettes
from diners import GENRES
from placard_v2 import PLACARD
from recettes_air_fryer import NOM_REPRISE as REPRISE_AIR_FRYER, AIR_FRYER
from recettes_legumes import NOM_REPRISE, LEGUMES, RETIRES

NON_DE_LAETITIA = ("brocoli", "chou-fleur", "epinards", "aubergine", "betterave", "celeri")


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
    ids = [p["id"] for p in LEGUMES]
    assert len(ids) == 11 == len(set(ids))
    assert not set(ids) & {p["id"] for p in CARNET_DEPART + A_TESTER + AIR_FRYER}
    assert {p["genre"] for p in LEGUMES} <= set(dict(GENRES))
    for p in LEGUMES:
        assert p["recette"].startswith("Pour ") and p["ingredients"] and all("(" not in i for i in p["ingredients"])
    # Ses « jamais » n'entrent dans aucune recette, sauf les épinards fondus du dal (voté oui)
    for p in LEGUMES + AIR_FRYER:
        for i in p["ingredients"]:
            if p["id"] != "lg-dal-epinards":
                assert not any(n in normaliser(i).replace(" ", "-") for n in NON_DE_LAETITIA), (p["id"], i)
    au_placard = {normaliser(n) for n, _, _ in PLACARD}
    assert {normaliser(n) for n in ("riz carnaroli", "épinards surgelés", "petits pois surgelés", "lardons")} <= \
        {normaliser(i) for p in LEGUMES for i in p["ingredients"]} & au_placard


def test_neon_au_01_11(conn):
    # Neon : le premier lot air fryer, avec le brocoli
    brocoli = {"id": "af-brocoli", "nom": "Brocoli croustillant au parmesan (air fryer)", "genre": "accompagnement",
               "minutes": 12, "ingredients": ["brocoli"], "recette": "Pour 2", "lien": "", "note": ""}
    ajouter_recettes(conn, REPRISE_AIR_FRYER, [p for p in AIR_FRYER if p["id"] != "af-carottes"] + [brocoli])
    conn.commit()
    carottes = [p for p in AIR_FRYER if p["id"] == "af-carottes"]
    assert ajouter_recettes(conn, NOM_REPRISE, LEGUMES + carottes, RETIRES) == 12
    conn.commit()
    plats = {p["id"]: p for p in lire_plats(conn)}
    assert plats["af-brocoli"]["archive"] and not plats["af-carottes"]["archive"]
    assert all(plats[p["id"]]["statut"] == "a-tester" for p in LEGUMES)
    assert ajouter_recettes(conn, NOM_REPRISE, LEGUMES + carottes, RETIRES) is None
