"""Tests des dîners en base (db.py) et de leurs routes (serveur.py)."""
import sys
from datetime import timedelta
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pytest
from casa import aujourd_hui_paris
from carnet_depart import CARNET_DEPART, A_TESTER
from courses import PLACARD_DEPART
from db import (connecter, semer_carnet, semer_placard, lire_plats, enregistrer_repas, lire_repas,
                completer_recettes, enregistrer_plat)
from serveur import creer_app

J = aujourd_hui_paris()


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


def test_api_diners(client):
    d = client.get("/api/diners").get_json()
    assert d["aujourd_hui"] == J.isoformat() and len(d["semaine"]) == 7
    assert len(d["secours"]["faisables"]) == 7 and "plat-carbonara" in d["secours"]["faisables"]
    assert d["compteur"] == {"semaine": 0, "moyenne": 0, "renseignes": 0}


def test_planifier_et_courses_de_la_semaine(client):
    corps = {"jour": J.isoformat(), "moment": "diner", "plats": ["plat-amatriciana"]}
    assert client.post("/api/repas", json=corps).status_code == 200
    assert client.post("/api/repas", json={**corps, "plats": ["plat-inconnu-01"]}).status_code == 400
    assert client.post("/api/repas", json={**corps, "moment": "gouter"}).status_code == 400
    r = client.post("/api/diners/courses").get_json()
    assert r["ajoutes"] == ["vin blanc"]                              # le reste est au placard
    assert client.post("/api/diners/courses").get_json()["ajoutes"] == []     # deux fois : pas de doublon
    assert [a["nom"] for a in client.get("/api/courses").get_json()["articles"]] == ["vin blanc"]


def test_api_repas_compose_et_brunch(client):
    jour = J.isoformat()
    client.post("/api/repas", json={"jour": jour, "moment": "diner", "plats": ["plat-carbonara", "tester-pesto"]})
    client.post("/api/repas", json={"jour": jour, "moment": "brunch", "plats": ["tester-shakshuka"]})
    d = client.get("/api/diners").get_json()
    assert {(r["moment"], tuple(r["plats"])) for r in d["repas"] if r["jour"] == jour} == {
        ("diner", ("plat-carbonara", "tester-pesto")), ("brunch", ("tester-shakshuka",))}
    assert d["cout_semaine"]["nb_repas"] == 2
    client.post("/api/repas", json={"jour": jour, "moment": "brunch", "plats": []})          # retirer le brunch
    assert [r["moment"] for r in client.get("/api/diners").get_json()["repas"]] == ["diner"]


def test_hier_soir_et_compteur_sur_aujourd_hui(client):
    hier = (J - timedelta(days=1)).isoformat()
    assert "Hier soir ?" in client.get("/").get_data(as_text=True)
    assert client.post("/api/repas", json={"jour": hier, "moment": "diner", "issue": "commande"}).status_code == 200
    html = client.get("/").get_data(as_text=True)
    assert "Hier soir ?" not in html and "1 commande ces 7 jours" in html


def test_ce_soir_compose_sur_aujourd_hui(client):
    client.post("/api/repas", json={"jour": J.isoformat(), "moment": "diner", "plats": ["plat-carbonara"]})
    html = client.get("/").get_data(as_text=True)
    assert "<strong>Spaghetti alla carbonara</strong>" in html


def test_api_plats(client):
    corps = {"id": "plat-maison-01", "nom": "Gratin de crozets", "genre": "plat", "minutes": 45,
             "ingredients": ["crozets", "beaufort"], "recette": "", "lien": "", "note": "", "statut": "carnet"}
    assert client.post("/api/plats", json=corps).status_code == 200
    assert client.post("/api/plats", json={**corps, "minutes": 0}).status_code == 400
    assert any(p["nom"] == "Gratin de crozets" for p in client.get("/api/diners").get_json()["plats"])


def test_page_diners(client):
    assert "<h1>Dîners</h1>" in client.get("/diners").get_data(as_text=True)


def test_pour_julien_sort_du_nom(conn):
    from db import separer_pour_julien
    p = next(x for x in lire_plats(conn) if x["id"] == "tester-moules")
    enregistrer_plat(conn, {**p, "nom": "Moules marinières frites (Julien)"})       # comme en prod au 01/11
    assert separer_pour_julien(conn) == 1
    conn.commit()
    moules = next(x for x in lire_plats(conn) if x["id"] == "tester-moules")
    assert moules["nom"] == "Moules marinières frites" and moules["pour"] == "julien"
    assert separer_pour_julien(conn) is None                                       # une seule fois


def test_api_proposer(client):
    r = client.post("/api/diners/proposer", json={})
    assert r.status_code == 200
    proposes, menus = r.get_json()["proposes"], r.get_json()["menus"]
    assert 1 <= len(proposes) <= 4 and set(menus) == set(proposes)
    diners = {r["jour"]: r["plats"] for r in client.get("/api/diners").get_json()["repas"] if r["moment"] == "diner"}
    assert all(diners[j] == menus[j] and menus[j][0] == id_ for j, id_ in proposes.items())
    assert client.post("/api/diners/proposer", json={"remplacer": ["pas-une-date"]}).status_code == 400


def test_api_proposer_avec_un_accompagnement(client, conn):
    for p in lire_plats(conn):
        if p["genre"] == "plat":
            enregistrer_plat(conn, {**p, "accords": ["acc-puree-robuchon", "acc-pommes-sautees"]})
    menus = client.post("/api/diners/proposer", json={}).get_json()["menus"]
    accs = [ids[1] for ids in menus.values() if len(ids) == 2]
    assert accs and len(set(accs)) == len(accs) <= 2
    assert set(accs) <= {"acc-puree-robuchon", "acc-pommes-sautees"}


def test_api_reproposer_ne_reprend_pas_l_accompagnement_d_un_soir_garde(client, conn):
    for p in lire_plats(conn):
        if p["genre"] == "plat":
            enregistrer_plat(conn, {**p, "accords": ["acc-puree-robuchon"]})
    garde = (J + timedelta(days=1)).isoformat()
    client.post("/api/repas", json={"jour": garde, "moment": "diner",
                                    "plats": ["plat-carbonara", "acc-puree-robuchon", "dessert-tiramisu"], "issue": None})
    menus = client.post("/api/diners/proposer", json={"remplacer": [garde]}).get_json()["menus"]
    assert garde not in menus
    assert all("acc-puree-robuchon" not in ids for ids in menus.values())


def test_api_diners_couts(client):
    d = client.get("/api/diners").get_json()
    carbo = next(p for p in d["plats"] if p["id"] == "plat-carbonara")
    assert carbo["cout"] > 0 and d["livraison"] > 0
    assert {"nb_repas", "cout", "courses", "livraison", "a_acheter"} <= set(d["cout_semaine"])
    assert isinstance(d["liste"], list)
