"""Tests des retours de cuisson en base (db.py) et de leurs routes (serveur.py)."""
import sys
from datetime import timedelta
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pytest
from carnet_depart import CARNET_DEPART, A_TESTER
from db import connecter, semer_carnet, enregistrer_avis, lire_avis
from avis import valider_avis
from serveur import creer_app, aujourd_hui_paris

J = aujourd_hui_paris()
HIER = (J - timedelta(days=1)).isoformat()


@pytest.fixture
def conn():
    c = connecter("valise_test")
    with c.cursor() as cur:
        cur.execute("TRUNCATE avis, repas, plats, courses, placard")
    c.commit()
    semer_carnet(c, CARNET_DEPART, A_TESTER)
    yield c
    c.close()


@pytest.fixture
def client(conn):
    return creer_app("valise_test", secret="").test_client()


def test_enregistrer_remplace_le_meme_avis(conn):
    corps = {"plat": "plat-carbonara", "jour": HIER, "moment": "diner", "qui": "julien", "note": 3, "raisons": ["trop-sale"]}
    enregistrer_avis(conn, valider_avis(corps, J))
    enregistrer_avis(conn, valider_avis({**corps, "note": 5, "raisons": ["a-refaire"]}, J))
    assert [(a["note"], a["raisons"]) for a in lire_avis(conn)] == [(5, ["a-refaire"])]


def test_api_avis(client):
    corps = {"plat": "plat-carbonara", "jour": HIER, "moment": "diner", "qui": "laetitia", "note": 4,
             "raisons": ["la-sauce"], "mot": "parfait avec plus de poivre"}
    assert client.post("/api/avis", json=corps).status_code == 200
    assert client.post("/api/avis", json={**corps, "plat": "plat-inconnu-01"}).status_code == 400
    assert client.post("/api/avis", json={**corps, "note": 9}).status_code == 400
    d = client.get("/api/avis").get_json()
    assert d["avis"] == [{**corps, "jour": HIER}]
    assert d["resume"]["plat-carbonara"]["laetitia"] == 4
    assert ["la-sauce", "la sauce"] in d["raisons"]["plus"]


def test_aujourd_hui_demande_l_avis_de_chacun(client):
    client.post("/api/repas", json={"jour": HIER, "moment": "diner", "plats": ["plat-carbonara"], "issue": "fait"})
    html = client.get("/").get_data(as_text=True)
    assert 'class="bloc-avis"' in html and "plat-carbonara" in html
    client.post("/api/avis", json={"plat": "plat-carbonara", "jour": HIER, "moment": "diner", "qui": "julien", "note": None})
    client.post("/api/avis", json={"plat": "plat-carbonara", "jour": HIER, "moment": "diner", "qui": "laetitia", "note": 5})
    assert 'class="bloc-avis"' not in client.get("/").get_data(as_text=True)     # tout le monde a répondu


def test_les_diners_portent_le_resume_des_avis(client):
    client.post("/api/avis", json={"plat": "plat-carbonara", "jour": HIER, "moment": "libre", "qui": "julien", "note": 5})
    carbo = next(p for p in client.get("/api/diners").get_json()["plats"] if p["id"] == "plat-carbonara")
    assert carbo["avis"]["moyenne"] == 5 and carbo["avis"]["julien"] == 5
