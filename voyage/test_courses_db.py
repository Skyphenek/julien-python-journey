"""Tests des courses en base (db.py) et de leurs routes (serveur.py)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pytest
from db import (connecter, enregistrer_article, lire_courses, supprimer_article, vider_pris, enregistrer_placard,
                semer_placard, compter_a_prendre, retirer_du_placard)


def basique(nom, en_stock=True, bientot=False, zone="placard-sec"):
    from courses import normaliser
    return {"cle": normaliser(nom), "nom": nom, "en_stock": en_stock, "bientot": bientot, "zone": zone}
from serveur import creer_app


def article(id_, nom, **reste):
    return {"id": id_, "nom": nom, "rayon": "autre", "pris": False, "recurrent": False, "actif": True,
            "source": "", **reste}


@pytest.fixture
def conn():
    c = connecter("valise_test")
    with c.cursor() as cur:
        cur.execute("TRUNCATE courses, placard")
    c.commit()
    yield c
    c.close()


@pytest.fixture
def client(conn):
    return creer_app("valise_test", secret="").test_client()


def test_enregistrer_et_lire(conn):
    enregistrer_article(conn, article("lait-0001", "Lait", rayon="frais"))
    enregistrer_article(conn, article("lait-0001", "Lait demi-écrémé", rayon="frais"))     # même id : mise à jour
    assert [a["nom"] for a in lire_courses(conn)["articles"]] == ["Lait demi-écrémé"]


def test_pris_remet_le_basique_en_stock(conn):
    enregistrer_placard(conn, basique("Crème fraîche", en_stock=False, zone="frigo"))
    enregistrer_placard(conn, basique("Cumin", bientot=True, zone="epices"))
    enregistrer_article(conn, article("creme-001", "creme  fraiche", pris=True))
    enregistrer_article(conn, article("cumin-001", "cumin", pris=True))
    assert lire_courses(conn)["placard"] == [basique("Crème fraîche", zone="frigo"), basique("Cumin", zone="epices")]


def test_zone_et_bientot_fini(conn):
    enregistrer_placard(conn, basique("Huile d'olive", bientot=True, zone="epices"))
    enregistrer_placard(conn, basique("Huile d'olive", bientot=True, zone="cave"))       # déplacée
    assert lire_courses(conn)["placard"] == [basique("Huile d'olive", bientot=True, zone="cave")]
    retirer_du_placard(conn, "huile d'olive")
    assert lire_courses(conn)["placard"] == []


def test_achat_pour_une_recette_entre_au_placard(conn):
    # Durable acheté pour un plat : il entre au placard ; frais, non ; acheté hors recette, non plus
    enregistrer_article(conn, article("garam-001", "Garam masala", rayon="epicerie", source="plat:tester-chana", pris=True))
    enregistrer_article(conn, article("pois-0001", "Pois chiches", rayon="epicerie", source="plat:tester-chana"))
    enregistrer_article(conn, article("coriandre", "Coriandre", rayon="fruits-legumes", source="plat:tester-chana", pris=True))
    enregistrer_article(conn, article("nouilles-1", "Nouilles udon", rayon="epicerie", pris=True))
    assert lire_courses(conn)["placard"] == [basique("Garam masala", zone="epices")]


def test_vider_pris_garde_les_habituels(conn):
    enregistrer_article(conn, article("pain-0001", "pain", pris=True))
    enregistrer_article(conn, article("lait-0001", "lait", pris=True, recurrent=True))
    enregistrer_article(conn, article("oeuf-0001", "œufs"))
    vider_pris(conn)
    restants = {a["nom"]: a for a in lire_courses(conn)["articles"]}
    assert set(restants) == {"lait", "œufs"}
    assert restants["lait"]["actif"] is False and restants["lait"]["pris"] is False      # rangé dans les habituels
    assert restants["œufs"]["actif"] is True


def test_supprimer_et_compter(conn):
    enregistrer_article(conn, article("pain-0001", "pain"))
    enregistrer_article(conn, article("lait-0001", "lait", pris=True))
    enregistrer_article(conn, article("riz-00001", "riz", actif=False, recurrent=True))
    assert compter_a_prendre(conn) == 1
    supprimer_article(conn, "pain-0001")
    assert compter_a_prendre(conn) == 0


def test_semer_placard_seulement_s_il_est_vide(conn):
    assert semer_placard(conn, ["Œufs", "spaghetti"]) == 2
    enregistrer_placard(conn, basique("Œufs", en_stock=False))
    assert semer_placard(conn, ["Œufs", "spaghetti", "riz"]) == 0                       # déjà semé : rien
    assert {p["cle"]: p["en_stock"] for p in lire_courses(conn)["placard"]} == {"oeufs": False, "spaghetti": True}


# --- Routes ---

def test_page_courses(client):
    html = client.get("/courses").get_data(as_text=True)
    assert "<h1>Courses</h1>" in html


def test_api_courses(client):
    r = client.post("/api/courses", json={"id": "spag-0001", "nom": "spaghetti"})
    assert r.status_code == 200 and r.get_json()["article"]["rayon"] == "epicerie"     # rayon deviné
    assert [a["nom"] for a in client.get("/api/courses").get_json()["articles"]] == ["spaghetti"]
    assert client.post("/api/courses", json={"id": "x", "nom": "spaghetti"}).status_code == 400
    assert client.delete("/api/courses/spag-0001").status_code == 200
    assert client.get("/api/courses").get_json()["articles"] == []


def test_api_vider_et_placard(client):
    client.post("/api/courses", json={"id": "pain-0001", "nom": "pain", "pris": True})
    assert client.post("/api/courses/vider").status_code == 200
    assert client.get("/api/courses").get_json()["articles"] == []
    r = client.post("/api/placard", json={"nom": "Pâtes", "en_stock": False})
    assert r.status_code == 200
    assert client.get("/api/courses").get_json()["placard"] == [basique("Pâtes", en_stock=False)]
    assert client.post("/api/placard", json={"nom": "", "en_stock": True}).status_code == 400
    assert client.delete("/api/placard/" + "pates").status_code == 200
    assert client.get("/api/courses").get_json()["placard"] == []


def test_aujourd_hui_compte_les_courses(client):
    client.post("/api/courses", json={"id": "pain-0001", "nom": "pain"})
    client.post("/api/courses", json={"id": "lait-0001", "nom": "lait"})
    html = client.get("/").get_data(as_text=True)
    assert '<a class="bloc-courses" href="courses">' in html and "2 articles à prendre" in html
