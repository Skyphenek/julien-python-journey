"""Tests des accords d'un plat : validation (diners.py), enregistrement (db.py) et route api/plats."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pytest
from carnet_depart import CARNET_DEPART, A_TESTER
from courses import PLACARD_DEPART
from db import connecter, semer_carnet, semer_placard, lire_plats, enregistrer_plat
from diners import valider_plat, nettoyer_accords, MAX_ACCORDS
from serveur import creer_app

STEAK = {"id": "plat-test-steak", "nom": "Steak", "genre": "plat", "minutes": 15}


@pytest.fixture
def conn():
    c = connecter("valise_test")
    with c.cursor() as cur:
        cur.execute("TRUNCATE repas, soirs, plats, courses, placard, reprises")
    c.commit()
    semer_placard(c, PLACARD_DEPART)
    semer_carnet(c, CARNET_DEPART, A_TESTER)
    yield c
    c.close()


@pytest.fixture
def client(conn):
    return creer_app("valise_test", secret="").test_client()


def plats(conn):
    return {p["id"]: p for p in lire_plats(conn)}


# --- Validation ---

def test_valider_plat_accords():
    assert valider_plat(STEAK)["accords"] is None                       # page d'avant les accords : rien à changer
    assert valider_plat({**STEAK, "accords": []})["accords"] == []
    assert valider_plat({**STEAK, "accords": ["acc-puree-robuchon", "af-frites"]})["accords"] == ["acc-puree-robuchon", "af-frites"]
    acc = {**STEAK, "id": "acc-test-puree", "genre": "accompagnement"}
    assert valider_plat({**acc, "accords": ["acc-puree-robuchon"]})["accords"] == []   # seul un plat porte des accords


@pytest.mark.parametrize("accords", [
    "acc-puree-robuchon",                                   # pas une liste
    ["acc-puree-robuchon", 3],                              # pas un id
    ["x"],                                                  # id trop court
    ["acc-puree-robuchon", "acc-puree-robuchon"],           # doublon
    ["plat-test-steak"],                                    # lui-même
    [f"acc-test-{i:02d}" for i in range(MAX_ACCORDS + 1)],  # 7 : trop
])
def test_valider_plat_refuse_des_accords(accords):
    with pytest.raises(ValueError):
        valider_plat({**STEAK, "accords": accords})


def test_nettoyer_accords():
    par_id = {"acc-puree": {"genre": "accompagnement", "archive": False},
              "acc-vieux": {"genre": "accompagnement", "archive": True},
              "plat-carbo": {"genre": "plat", "archive": False}}
    assert nettoyer_accords(["acc-vieux", "inconnu-01", "plat-carbo", "acc-puree"], par_id) == ["acc-puree"]


# --- Base ---

def test_enregistrer_et_lire_des_accords(conn):
    boucher = plats(conn)["plat-piece-du-boucher"]
    assert boucher["accords"] == []
    enregistrer_plat(conn, {**boucher, "accords": ["acc-pommes-sautees", "acc-puree-robuchon"]})
    assert plats(conn)["plat-piece-du-boucher"]["accords"] == ["acc-pommes-sautees", "acc-puree-robuchon"]


def test_sans_accords_ceux_en_base_restent(conn):
    boucher = plats(conn)["plat-piece-du-boucher"]
    enregistrer_plat(conn, {**boucher, "accords": ["acc-pommes-sautees"]})
    ancien = {k: v for k, v in boucher.items() if k != "accords"}                  # la page d'avant
    enregistrer_plat(conn, valider_plat({**ancien, "nom": "Pièce du boucher"}))
    relu = plats(conn)["plat-piece-du-boucher"]
    assert relu["nom"] == "Pièce du boucher" and relu["accords"] == ["acc-pommes-sautees"]


def test_nouveau_plat_sans_accords(conn):
    enregistrer_plat(conn, valider_plat(STEAK))
    assert plats(conn)["plat-test-steak"]["accords"] == []


# --- Route ---

def test_api_plats_ne_garde_que_des_accompagnements(client, conn):
    boucher = plats(conn)["plat-piece-du-boucher"]
    corps = {**boucher, "accords": ["acc-puree-robuchon", "plat-carbonara", "inconnu-01"]}
    assert client.post("/api/plats", json=corps).status_code == 200
    assert plats(conn)["plat-piece-du-boucher"]["accords"] == ["acc-puree-robuchon"]
    assert client.post("/api/plats", json={**boucher, "accords": "acc-puree-robuchon"}).status_code == 400
    lu = {p["id"]: p for p in client.get("/api/diners").get_json()["plats"]}
    assert lu["plat-piece-du-boucher"]["accords"] == ["acc-puree-robuchon"]
