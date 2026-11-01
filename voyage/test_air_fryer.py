"""Tests des recettes air fryer (recettes_air_fryer.py, db.ajouter_recettes)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pytest
from carnet_depart import CARNET_DEPART, A_TESTER
from courses import PLACARD_DEPART, normaliser
from db import (connecter, semer_placard, semer_carnet, lire_plats, enregistrer_plat, ajouter_recettes,
                actualiser_recettes)
from diners import GENRES
from placard_v2 import PLACARD, HABITUELS
from recettes_air_fryer import NOM_REPRISE, NOM_REPRISE_6L, AIR_FRYER


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
    ids = [p["id"] for p in AIR_FRYER]
    assert len(ids) == len(set(ids)) and not set(ids) & {p["id"] for p in CARNET_DEPART + A_TESTER}
    assert {p["genre"] for p in AIR_FRYER} <= set(dict(GENRES))
    for p in AIR_FRYER:
        assert p["nom"].endswith("(air fryer)") and p["recette"].startswith("Pour ") and "°C" in p["recette"]
        assert p["ingredients"] and all("(" not in i for i in p["ingredients"])
        assert '"' not in p["recette"] and "_" not in p["recette"]        # pas de code resté dans le texte
    # Les basiques s'écrivent comme au placard : c'est la clé qui relie recettes, placard et courses
    au_placard = {normaliser(n) for n, _, _ in PLACARD} | {normaliser(n) for n, _ in HABITUELS}
    utilises = {normaliser(i) for p in AIR_FRYER for i in p["ingredients"]}
    basiques = {"chapelure panko", "paprika fumé", "sauce soja", "miel", "parmesan", "levure chimique",
                "fécule de maïs", "pommes de terre", "comté"}
    assert {normaliser(n) for n in basiques} <= utilises & au_placard


def test_ajout_a_tester(conn):
    assert ajouter_recettes(conn, NOM_REPRISE, AIR_FRYER) == len(AIR_FRYER)
    conn.commit()
    plats = {p["id"]: p for p in lire_plats(conn)}
    assert len(plats) == len(CARNET_DEPART) + len(A_TESTER) + len(AIR_FRYER)
    for p in AIR_FRYER:
        assert plats[p["id"]]["statut"] == "a-tester" and not plats[p["id"]]["archive"]


def test_ajout_une_seule_fois(conn):
    ajouter_recettes(conn, NOM_REPRISE, AIR_FRYER)
    conn.commit()
    premier = AIR_FRYER[0]
    corrige = {**next(p for p in lire_plats(conn) if p["id"] == premier["id"]), "recette": "La nôtre."}
    enregistrer_plat(conn, corrige)                      # corrigée dans l'app
    with conn.cursor() as cur:
        cur.execute("DELETE FROM plats WHERE id = %s", (AIR_FRYER[1]["id"],))   # retirée dans l'app
    conn.commit()
    assert ajouter_recettes(conn, NOM_REPRISE, AIR_FRYER) is None
    plats = {p["id"]: p for p in lire_plats(conn)}
    assert plats[premier["id"]]["recette"] == "La nôtre." and AIR_FRYER[1]["id"] not in plats


def test_a_blanc_ne_laisse_rien(conn):
    ajouter_recettes(conn, NOM_REPRISE, AIR_FRYER)
    conn.rollback()
    assert len(lire_plats(conn)) == len(CARNET_DEPART) + len(A_TESTER)
    assert ajouter_recettes(conn, NOM_REPRISE, AIR_FRYER) == len(AIR_FRYER)


def test_actualiser_ne_touche_pas_aux_corrigees(conn):
    # Neon au 01/11 : lot ajouté avec les anciens textes ; l'une corrigée dans l'app depuis
    anciens = [{**p, "recette": p["recette"] + " (ancien)"} for p in AIR_FRYER]
    ajouter_recettes(conn, NOM_REPRISE, anciens)
    conn.commit()
    corrigee = next(p for p in lire_plats(conn) if p["id"] == AIR_FRYER[0]["id"])
    enregistrer_plat(conn, {**corrigee, "recette": "La nôtre."})
    assert actualiser_recettes(conn, NOM_REPRISE_6L, NOM_REPRISE, AIR_FRYER) == len(AIR_FRYER) - 1
    conn.commit()
    plats = {p["id"]: p for p in lire_plats(conn)}
    assert plats[AIR_FRYER[0]["id"]]["recette"] == "La nôtre."
    assert plats[AIR_FRYER[1]["id"]]["recette"] == AIR_FRYER[1]["recette"]
    assert actualiser_recettes(conn, NOM_REPRISE_6L, NOM_REPRISE, AIR_FRYER) is None
