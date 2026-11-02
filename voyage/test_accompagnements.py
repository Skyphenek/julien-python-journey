"""Tests des accompagnements, des brunchs et des accords de départ (recettes_accompagnements.py)."""
import re
import sys
from datetime import date
from pathlib import Path
from random import Random
sys.path.insert(0, str(Path(__file__).parent))

import pytest
from carnet_depart import CARNET_DEPART, A_TESTER
from catalogue import chercher
from courses import PLACARD_DEPART, normaliser
from db import connecter, semer_placard, semer_carnet, lire_plats, ajouter_recettes, enregistrer_plat, poser_accords
from diners import valider_plat, proposer, semaine
from recettes_air_fryer import AIR_FRYER
from recettes_legumes import LEGUMES, RETIRES
from recettes_mer import MER, MER_JULIEN, JAMAIS_LAETITIA
from recettes_laetitia import LAETITIA
from recettes_accompagnements import (NOM_REPRISE, NOM_REPRISE_ACCORDS, ACCOMPAGNEMENTS, BRUNCHS, ACCORDS,
                                      JAMAIS_LEGUMES_LAETITIA)

LOTS = AIR_FRYER + LEGUMES + MER + MER_JULIEN + LAETITIA
AUTRES = CARNET_DEPART + A_TESTER + LOTS
TOUS = {p["id"]: p for p in AUTRES + ACCOMPAGNEMENTS + BRUNCHS}
JAMAIS = JAMAIS_LAETITIA + JAMAIS_LEGUMES_LAETITIA


@pytest.fixture
def conn():
    c = connecter("valise_test")
    with c.cursor() as cur:
        cur.execute("TRUNCATE repas, soirs, plats, courses, placard, reprises")
    c.commit()
    semer_placard(c, PLACARD_DEPART)
    semer_carnet(c, CARNET_DEPART, A_TESTER)
    ajouter_recettes(c, "lots-du-test", LOTS)          # la base de prod a aussi ces lots
    c.commit()
    yield c
    c.close()


def a_un_jamais(p):
    return [i for i in p["ingredients"] if any(re.search(r"\b" + re.escape(j), normaliser(i)) for j in JAMAIS)]


def test_donnees():
    nouveaux = ACCOMPAGNEMENTS + BRUNCHS
    ids = [p["id"] for p in nouveaux]
    assert len(ACCOMPAGNEMENTS) == 15 and len(BRUNCHS) == 6 and len(set(ids)) == len(ids)
    assert not set(ids) & {p["id"] for p in AUTRES}
    assert all(p["genre"] == "accompagnement" and p["id"].startswith("acc-") for p in ACCOMPAGNEMENTS)
    assert all(p["id"].startswith("brunch-") for p in BRUNCHS)
    for p in nouveaux:
        assert valider_plat({**p, "statut": "a-tester"})["pour"] == "nous"
        assert p["recette"].startswith("Pour "), p["id"]
        assert [i for i in p["ingredients"] if not chercher(i)] == [], p["id"]


def test_rien_de_ses_jamais():
    for p in ACCOMPAGNEMENTS + BRUNCHS:
        assert not a_un_jamais(p), p["id"]
    assert a_un_jamais({"ingredients": ["moules"]}) and not a_un_jamais({"ingredients": ["semoule"]})


def test_accords_de_depart():
    assert len(ACCORDS) >= 25
    for id_, accords in ACCORDS.items():
        assert TOUS[id_]["genre"] == "plat", id_
        assert 2 <= len(accords) <= 4 and len(set(accords)) == len(accords), id_
        for a in accords:
            acc = TOUS[a]
            assert acc["genre"] == "accompagnement" and acc.get("pour", "nous") == "nous", (id_, a)
            assert a not in RETIRES and not a_un_jamais(acc), (id_, a)


def test_ajout_et_accords_une_seule_fois(conn):
    assert ajouter_recettes(conn, NOM_REPRISE, ACCOMPAGNEMENTS + BRUNCHS) == 21
    assert poser_accords(conn, NOM_REPRISE_ACCORDS, ACCORDS) == len(ACCORDS)
    conn.commit()
    plats = {p["id"]: p for p in lire_plats(conn)}
    assert plats["plat-piece-du-boucher"]["accords"] == ACCORDS["plat-piece-du-boucher"]
    assert plats["acc-riz-pilaf"]["statut"] == "a-tester" and plats["brunch-crepes"]["genre"] == "dessert"
    assert poser_accords(conn, NOM_REPRISE_ACCORDS, ACCORDS) is None


def test_accords_regles_dans_l_app_et_archives(conn):
    ajouter_recettes(conn, NOM_REPRISE, ACCOMPAGNEMENTS)
    conn.commit()
    plats = {p["id"]: p for p in lire_plats(conn)}
    enregistrer_plat(conn, {**plats["plat-roti-de-boeuf"], "accords": ["acc-puree-robuchon"]})   # réglé dans l'app
    enregistrer_plat(conn, {**plats["acc-salade-verte"], "archive": True})                     # retiré dans l'app
    poser_accords(conn, NOM_REPRISE_ACCORDS, ACCORDS)
    conn.commit()
    plats = {p["id"]: p for p in lire_plats(conn)}
    assert plats["plat-roti-de-boeuf"]["accords"] == ["acc-puree-robuchon"]
    assert plats["plat-piece-du-boucher"]["accords"] == [a for a in ACCORDS["plat-piece-du-boucher"]
                                                         if a != "acc-salade-verte"]


def test_pas_de_brunch_propose_au_diner():
    lundi = date(2026, 11, 2)
    plats = [{**p, "statut": "carnet", "archive": False} for p in BRUNCHS if p["genre"] == "plat"]
    assert len(plats) == 3
    assert proposer(plats, [], semaine(lundi), lundi, hasard=Random(1)) == {}
