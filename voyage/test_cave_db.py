"""Tests de la Cave en base (db.py) : enregistrer, boire, retirer, reprise de départ."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pytest
from db import connecter, lire_cave, enregistrer_bouteille, boire, retirer_bouteille, poser_cave
from cave_depart import CAVE_DEPART


def bouteille(id_="vin-a", **champs):
    return {"id": id_, "nom": "Saint-Joseph", "producteur": "", "appellation": "", "region": "", "couleur": "rouge",
            "millesime": 2019, "quantite": 1, "debut": 2026, "fin": 2028, "prix_bas": 25, "prix_haut": 30,
            "accords": ["boeuf"], "note": ""} | champs


@pytest.fixture
def conn():
    c = connecter("valise_test")
    with c.cursor() as cur:
        cur.execute("TRUNCATE cave")
        cur.execute("DELETE FROM reprises WHERE nom = 'cave-test'")
    c.commit()
    yield c
    c.close()


def test_enregistrer_et_lire(conn):
    enregistrer_bouteille(conn, bouteille())
    enregistrer_bouteille(conn, bouteille("vin-b", nom="Bandol", quantite=2))
    assert lire_cave(conn) == [bouteille("vin-b", nom="Bandol", quantite=2), bouteille()]   # tri par nom


def test_enregistrer_met_a_jour(conn):
    enregistrer_bouteille(conn, bouteille())
    enregistrer_bouteille(conn, bouteille(quantite=3, accords=["volaille", "fromage"], note="offert"))
    assert lire_cave(conn) == [bouteille(quantite=3, accords=["volaille", "fromage"], note="offert")]


def test_boire_jamais_sous_zero(conn):
    enregistrer_bouteille(conn, bouteille(quantite=1))
    assert boire(conn, "vin-a") == 0
    assert boire(conn, "vin-a") == 0
    assert lire_cave(conn)[0]["quantite"] == 0                       # reste en base (repli « Bues »)
    assert boire(conn, "inconnu") is None


def test_retirer(conn):
    enregistrer_bouteille(conn, bouteille())
    assert retirer_bouteille(conn, "vin-a") is True
    assert retirer_bouteille(conn, "vin-a") is False
    assert lire_cave(conn) == []


def test_reprise_une_seule_fois(conn):
    assert poser_cave(conn, "cave-test", CAVE_DEPART) == 19
    conn.commit()
    assert len(lire_cave(conn)) == 19
    boire(conn, "vin-maddalena")
    assert poser_cave(conn, "cave-test", CAVE_DEPART) is None        # déjà faite : rien ne bouge
    conn.commit()
    assert next(b for b in lire_cave(conn) if b["id"] == "vin-maddalena")["quantite"] == 1


def test_reprise_n_ecrase_pas(conn):
    enregistrer_bouteille(conn, bouteille("vin-peyrouquet", nom="Château Peyrouquet", quantite=6))
    assert poser_cave(conn, "cave-test", CAVE_DEPART) == 18
    conn.commit()
    assert next(b for b in lire_cave(conn) if b["id"] == "vin-peyrouquet")["quantite"] == 6


from serveur import creer_app


@pytest.fixture
def client(conn):
    return creer_app("valise_test", secret="").test_client()


def test_routes_cave(client, conn):
    assert client.get("/cave").status_code == 200
    r = client.post("/api/cave", json={"id": "vin-x", "nom": "Saint-Amour", "couleur": "rouge", "millesime": 2022,
                                       "quantite": 2})
    assert r.status_code == 200 and r.get_json()["bouteille"]["accords"] == ["boeuf", "charcuterie"]
    lu = client.get("/api/cave").get_json()
    assert [b["id"] for b in lu["bouteilles"]] == ["vin-x"] and isinstance(lu["annee"], int)
    assert client.post("/api/cave/vin-x/bue").get_json() == {"ok": True, "quantite": 1}
    assert client.post("/api/cave/inconnu/bue").status_code == 404
    assert client.post("/api/cave", json={"id": "vin-y", "nom": "", "couleur": "rouge"}).status_code == 400
    assert client.delete("/api/cave/vin-x").status_code == 200
    assert client.delete("/api/cave/vin-x").status_code == 404


from db import enregistrer_plat, enregistrer_repas
from casa import aujourd_hui_paris


@pytest.fixture
def client_diner(client, conn):
    with conn.cursor() as cur:
        cur.execute("TRUNCATE repas, plats")
    conn.commit()
    enregistrer_plat(conn, {"id": "plat-test-boeuf", "nom": "Steak", "genre": "plat", "minutes": 15,
                            "ingredients": ["pièce du boucher", "beurre"], "recette": "", "lien": "", "note": "",
                            "statut": "carnet", "archive": False, "pour": "nous"})
    yield client
    with conn.cursor() as cur:                       # ne pas laisser de dîner prévu aux autres tests
        cur.execute("TRUNCATE repas, plats")
    conn.commit()


def test_aujourd_hui_propose_un_vin(client_diner, conn):
    enregistrer_bouteille(conn, bouteille("vin-boeuf", nom="Plan de Dieu", accords=["boeuf"], prix_haut=12))
    enregistrer_bouteille(conn, bouteille("vin-poisson", nom="Cheverny", accords=["poisson"], prix_haut=10))
    assert '<div class="bloc-vin">' not in client_diner.get("/").get_data(as_text=True)   # rien de prévu
    enregistrer_repas(conn, {"jour": aujourd_hui_paris(), "moment": "diner", "plats": ["plat-test-boeuf"], "issue": None})
    html = client_diner.get("/").get_data(as_text=True)
    assert '<div class="bloc-vin">' in html and "Plan de Dieu" in html and "Cheverny" not in html


def test_aujourd_hui_sans_vin_qui_colle(client_diner, conn):
    enregistrer_bouteille(conn, bouteille("vin-poisson", nom="Cheverny", accords=["poisson"], prix_haut=10))
    enregistrer_repas(conn, {"jour": aujourd_hui_paris(), "moment": "diner", "plats": ["plat-test-boeuf"], "issue": None})
    assert '<div class="bloc-vin">' not in client_diner.get("/").get_data(as_text=True)
