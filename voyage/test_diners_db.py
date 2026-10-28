"""Tests des dîners en base (db.py) et de leurs routes (serveur.py)."""
import sys
from datetime import timedelta
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pytest
from casa import aujourd_hui_paris
from carnet_depart import CARNET_DEPART, A_TESTER
from courses import PLACARD_DEPART
from db import (connecter, semer_carnet, semer_placard, lire_plats, enregistrer_soir, lire_soirs,
                completer_recettes, enregistrer_plat)
from serveur import creer_app

J = aujourd_hui_paris()


@pytest.fixture
def conn():
    c = connecter("valise_test")
    with c.cursor() as cur:
        cur.execute("TRUNCATE soirs, plats, courses, placard")
    c.commit()
    semer_placard(c, PLACARD_DEPART)
    semer_carnet(c, CARNET_DEPART, A_TESTER)
    yield c
    c.close()


@pytest.fixture
def client(conn):
    return creer_app("valise_test", secret="").test_client()


def test_semer_carnet_une_seule_fois(conn):
    assert len(lire_plats(conn)) == len(CARNET_DEPART) + len(A_TESTER)
    assert semer_carnet(conn, CARNET_DEPART, A_TESTER) == 0
    carbo = next(p for p in lire_plats(conn) if p["id"] == "plat-carbonara")
    assert carbo["ingredients"] == ["spaghetti", "guanciale ou pancetta", "œufs", "pecorino"]
    assert carbo["lien"].startswith("https://ricette.giallozafferano.it/")


def test_completer_recettes_ne_remplit_que_les_vides(conn):
    # Carnet semé avant les recettes à tester (cas de Neon le 28/10) : deux matchs sans recette
    for id_, recette in (("tester-shakshuka", ""), ("tester-chili", "La nôtre, corrigée dans l'app.")):
        p = next(x for x in lire_plats(conn) if x["id"] == id_)
        enregistrer_plat(conn, {**p, "ingredients": [], "recette": recette})
    assert completer_recettes(conn, A_TESTER) == 1
    plats = {p["id"]: p for p in lire_plats(conn)}
    assert plats["tester-shakshuka"]["recette"].startswith("Pour 2") and "œufs" in plats["tester-shakshuka"]["ingredients"]
    assert plats["tester-chili"]["recette"] == "La nôtre, corrigée dans l'app."
    assert completer_recettes(conn, A_TESTER) == 0


def test_fait_maison_fait_entrer_au_carnet(conn):
    enregistrer_soir(conn, {"jour": J, "plat": "tester-pesto", "issue": None})
    assert next(p for p in lire_plats(conn) if p["id"] == "tester-pesto")["statut"] == "a-tester"
    enregistrer_soir(conn, {"jour": J, "plat": "tester-pesto", "issue": "fait"})
    assert next(p for p in lire_plats(conn) if p["id"] == "tester-pesto")["statut"] == "carnet"
    assert lire_soirs(conn, J, J) == [{"jour": J, "plat": "tester-pesto", "issue": "fait"}]


def test_api_diners(client):
    d = client.get("/api/diners").get_json()
    assert d["aujourd_hui"] == J.isoformat() and len(d["semaine"]) == 7
    assert len(d["secours"]["faisables"]) == 7 and "plat-carbonara" in d["secours"]["faisables"]
    assert d["compteur"] == {"semaine": 0, "moyenne": 0, "renseignes": 0}


def test_planifier_et_courses_de_la_semaine(client):
    assert client.post("/api/soirs", json={"jour": J.isoformat(), "plat": "plat-amatriciana"}).status_code == 200
    assert client.post("/api/soirs", json={"jour": J.isoformat(), "plat": "plat-inconnu-01"}).status_code == 400
    r = client.post("/api/diners/courses").get_json()
    assert r["ajoutes"] == ["vin blanc"]                              # le reste est au placard
    assert client.post("/api/diners/courses").get_json()["ajoutes"] == []     # deux fois : pas de doublon
    assert [a["nom"] for a in client.get("/api/courses").get_json()["articles"]] == ["vin blanc"]


def test_hier_soir_et_compteur_sur_aujourd_hui(client):
    hier = (J - timedelta(days=1)).isoformat()
    assert "Hier soir ?" in client.get("/").get_data(as_text=True)
    assert client.post("/api/soirs", json={"jour": hier, "issue": "commande"}).status_code == 200
    html = client.get("/").get_data(as_text=True)
    assert "Hier soir ?" not in html and "1 commande ces 7 jours" in html


def test_api_plats(client):
    corps = {"id": "plat-maison-01", "nom": "Gratin de crozets", "genre": "plat", "minutes": 45,
             "ingredients": ["crozets", "beaufort"], "recette": "", "lien": "", "note": "", "statut": "carnet"}
    assert client.post("/api/plats", json=corps).status_code == 200
    assert client.post("/api/plats", json={**corps, "minutes": 0}).status_code == 400
    assert any(p["nom"] == "Gratin de crozets" for p in client.get("/api/diners").get_json()["plats"])


def test_page_diners(client):
    assert "<h1>Dîners</h1>" in client.get("/diners").get_data(as_text=True)
