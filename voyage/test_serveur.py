"""Tests de serveur.py — API Flask au-dessus de db.py."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pytest
from serveur import creer_app
from db import connecter


@pytest.fixture
def client():
    conn = connecter("valise_test")
    with conn.cursor() as cur:
        cur.execute("TRUNCATE etat_case")
    conn.commit()
    conn.close()
    app = creer_app("valise_test")
    return app.test_client()


def test_etat_base_vide(client):
    reponse = client.get("/api/etat/Hanoï")
    assert reponse.status_code == 200
    assert reponse.get_json() == {}


def test_coche_puis_etat(client):
    reponse = client.post(
        "/api/coche",
        json={"cle": "Hanoï/Julien/Vêtements/pantalons", "coche": True},
    )
    assert reponse.status_code == 200
    reponse = client.get("/api/etat/Hanoï")
    assert reponse.get_json() == {"Hanoï/Julien/Vêtements/pantalons": True}


def test_coche_upsert_une_seule_ligne(client):
    client.post("/api/coche", json={"cle": "Hanoï/Julien/Vêtements/pantalons", "coche": True})
    client.post("/api/coche", json={"cle": "Hanoï/Julien/Vêtements/pantalons", "coche": False})
    conn = connecter("valise_test")
    with conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM etat_case")
        assert cur.fetchone()[0] == 1
    conn.close()


def test_coche_payload_invalide(client):
    reponse = client.post("/api/coche", json={"cle": "Hanoï/Julien/Vêtements/pantalons"})
    assert reponse.status_code == 400
