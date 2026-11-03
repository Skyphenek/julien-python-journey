"""Tests d'À finir en base (db.py) : lecture du frais, corrections, [Fini], reprise du frigo."""
import sys
from datetime import date, timedelta
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pytest
from db import (connecter, enregistrer_article, enregistrer_placard, lire_courses, lire_frais, finir,
                corriger_a_finir, dater_frigo)
from conservation import duree

JOUR = date(2026, 11, 3)


def article(id_, nom, **reste):
    return {"id": id_, "nom": nom, "rayon": "frais", "pris": False, "recurrent": False, "actif": True,
            "source": "", **reste}


def element(nom, en_stock=True, zone="frigo"):
    from courses import normaliser
    return {"cle": normaliser(nom), "nom": nom, "en_stock": en_stock, "bientot": False, "zone": zone}


@pytest.fixture
def conn():
    c = connecter("valise_test")
    with c.cursor() as cur:
        cur.execute("TRUNCATE courses, placard, achats, a_finir")
        cur.execute("DELETE FROM reprises WHERE nom = 'a-finir-test'")
    c.commit()
    yield c
    c.close()


def aujourd_hui(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT (now() AT TIME ZONE 'Europe/Paris')::date")
        return cur.fetchone()[0]


def test_lire_frais(conn):
    enregistrer_placard(conn, element("steaks hachés"))
    enregistrer_placard(conn, element("riz", zone="placard-sec"))
    enregistrer_article(conn, article("jamb-0001", "jambon", pris=True))
    corriger_a_finir(conn, "comte", JOUR)
    f = lire_frais(conn)
    assert [(p["cle"], p["entre_le"]) for p in f["placard"]] == [("steaks haches", aujourd_hui(conn))]
    assert f["derniers_achats"] == {"jambon": aujourd_hui(conn)} and f["corrections"] == {"comte": JOUR}


def test_corriger_remplace(conn):
    corriger_a_finir(conn, "comte", JOUR)
    corriger_a_finir(conn, "comte", JOUR + timedelta(days=2))
    assert lire_frais(conn)["corrections"] == {"comte": JOUR + timedelta(days=2)}


def test_fini_sort_du_stock_ou_remet_l_habituel_sur_la_liste(conn):
    enregistrer_placard(conn, element("steaks hachés"))
    enregistrer_article(conn, article("mozz-0001", "mozzarella", recurrent=True, actif=False))
    corriger_a_finir(conn, "steaks haches", JOUR)
    assert finir(conn, "steaks haches") and finir(conn, "mozzarella")
    lu = lire_courses(conn)
    assert not lu["placard"][0]["en_stock"] and lu["articles"][0]["actif"] and not lu["articles"][0]["pris"]
    assert lire_frais(conn)["corrections"] == {}
    assert not finir(conn, "inconnu")


def test_le_rachat_et_la_remise_en_stock_effacent_la_correction(conn):
    enregistrer_placard(conn, element("lardons", en_stock=False))
    corriger_a_finir(conn, "lardons", JOUR)
    corriger_a_finir(conn, "jambon", JOUR)
    corriger_a_finir(conn, "comte", JOUR)
    enregistrer_placard(conn, element("lardons"))                       # remis en stock
    enregistrer_article(conn, article("jamb-0001", "jambon", pris=True))  # racheté
    enregistrer_placard(conn, element("comté"))                         # pas en stock avant : nouveau
    assert lire_frais(conn)["corrections"] == {}
    corriger_a_finir(conn, "comte", JOUR)
    enregistrer_placard(conn, {**element("comté"), "bientot": True})    # déjà en stock : la correction reste
    assert lire_frais(conn)["corrections"] == {"comte": JOUR}


def test_dater_frigo_une_seule_fois(conn):
    enregistrer_article(conn, article("beur-0001", "beurre", recurrent=True, actif=False))
    enregistrer_article(conn, article("lait-0001", "lait", recurrent=True, actif=True))       # sur la liste
    enregistrer_article(conn, article("jamb-0001", "jambon", recurrent=True, pris=True))      # acheté : daté
    enregistrer_article(conn, article("citr-0001", "citrons", recurrent=True, actif=False))   # pas au frigo
    connus = {"cuisses de poulet": (date(2026, 11, 1), None), "galettes de sarrasin": (JOUR, date(2026, 11, 9))}
    dates = dater_frigo(conn, "a-finir-test", JOUR, connus)
    assert dates == {"cuisses de poulet": date(2026, 11, 3), "galettes de sarrasin": date(2026, 11, 9),
                     "beurre": JOUR + timedelta(days=duree("beurre"))}
    conn.commit()
    assert lire_frais(conn)["corrections"] == dates
    assert {p["cle"] for p in lire_courses(conn)["placard"] if p["en_stock"]} == {"cuisses de poulet",
                                                                                   "galettes de sarrasin"}
    assert dater_frigo(conn, "a-finir-test", JOUR, connus) is None


# --- Routes ---
from serveur import creer_app


@pytest.fixture
def client(conn):
    with conn.cursor() as cur:
        cur.execute("TRUNCATE plats, repas")
    conn.commit()
    return creer_app("valise_test", secret="").test_client()


def test_api_a_finir(client, conn):
    enregistrer_placard(conn, element("steaks hachés"))
    assert client.post("/api/a-finir/steaks%20haches", json={"action": "encore-bon"}).status_code == 200
    assert lire_frais(conn)["corrections"] == {"steaks haches": aujourd_hui(conn) + timedelta(days=2)}
    assert client.post("/api/a-finir/steaks%20haches", json={"action": "fini"}).status_code == 200
    assert not lire_courses(conn)["placard"][0]["en_stock"]
    assert client.post("/api/a-finir/steaks%20haches", json={"action": "fini"}).status_code == 404   # plus suivi
    assert client.post("/api/a-finir/steaks%20haches", json={"action": "jeter"}).status_code == 400
    assert client.post("/api/a-finir/steaks%20haches", json=["fini"]).status_code == 400


def test_aujourd_hui_et_diners_montrent_ce_qui_est_a_finir(client, conn):
    enregistrer_placard(conn, element("steaks hachés"))           # entré aujourd'hui, 1 jour : à finir demain
    client.post("/api/plats", json={"id": "plat-burger-01", "nom": "Burger", "genre": "plat", "minutes": 15,
                                    "ingredients": ["steaks hachés", "pains burger"], "recette": "1.",
                                    "statut": "carnet"})
    html = client.get("/").get_data(as_text=True)
    assert "bloc-a-finir" in html and "steaks hachés" in html and "Burger" in html
    assert client.get("/api/diners").get_json()["a_finir"] == ["plat-burger-01"]
