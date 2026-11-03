"""Tests d'À finir en base (db.py) : lecture du frais, corrections, [Fini], reprise du frigo."""
import sys
from datetime import date, timedelta
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pytest
from db import (connecter, enregistrer_article, enregistrer_placard, lire_courses, lire_frais, finir,
                corriger_a_finir, dater_frigo, enregistrer_repas)
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
    enregistrer_article(conn, article("jamb-0001", "jambon", recurrent=True, pris=True))   # habituel : pas au stock
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


def test_fini_borne_au_frigo_et_remet_aussi_l_habituel(conn):
    enregistrer_placard(conn, element("lait UHT", zone="placard-sec"))
    enregistrer_article(conn, article("lait-0001", "lait uht", recurrent=True, actif=False))
    assert finir(conn, "lait uht")                                     # l'habituel revient, le placard sec reste
    lu = lire_courses(conn)
    assert lu["placard"][0]["en_stock"] and lu["articles"][0]["actif"]
    enregistrer_placard(conn, element("yaourts"))
    enregistrer_article(conn, article("yaou-0001", "yaourts", recurrent=True, actif=False))
    assert finir(conn, "yaourts")                                      # les deux sont finis
    lu = lire_courses(conn)
    assert not next(p for p in lu["placard"] if p["cle"] == "yaourts")["en_stock"]
    assert next(a for a in lu["articles"] if a["nom"] == "yaourts")["actif"]


def test_dater_frigo_force_la_zone_frigo(conn):
    enregistrer_placard(conn, element("cuisses de poulet", zone="placard-sec"))
    dater_frigo(conn, "a-finir-test", JOUR, {"cuisses de poulet": (JOUR, None)})
    conn.commit()
    assert lire_courses(conn)["placard"][0]["zone"] == "frigo"


def test_frais_coche_entre_au_stock_du_frigo(conn):
    enregistrer_article(conn, article("cuis-0001", "cuisses de poulet", rayon="boucherie", pris=True))
    enregistrer_article(conn, article("spag-0001", "spaghetti", rayon="epicerie", pris=True))
    p = {x["cle"]: x for x in lire_frais(conn)["placard"]}
    assert p["cuisses de poulet"]["en_stock"] and p["cuisses de poulet"]["entre_le"] == aujourd_hui(conn)
    assert "spaghetti" not in p
    assert "spaghetti" not in {x["cle"] for x in lire_courses(conn)["placard"] if x["zone"] == "frigo"}


def test_diner_fait_sort_la_viande_pas_le_fromage(conn):
    with conn.cursor() as cur:
        cur.execute("TRUNCATE plats, repas")
        cur.execute("""INSERT INTO plats (id, nom, genre, minutes, ingredients, recette, statut)
                       VALUES ('plat-poulet-01', 'Poulet', 'plat', 30, %s, '1.', 'carnet')""",
                    ('["cuisses de poulet", "parmesan"]',))
    conn.commit()
    enregistrer_placard(conn, element("cuisses de poulet"))
    enregistrer_placard(conn, element("parmesan"))
    corriger_a_finir(conn, "cuisses de poulet", JOUR)
    enregistrer_repas(conn, {"jour": JOUR, "moment": "diner", "plats": ["plat-poulet-01"], "issue": "fait"})
    p = {x["cle"]: x for x in lire_courses(conn)["placard"]}
    assert not p["cuisses de poulet"]["en_stock"] and p["parmesan"]["en_stock"]
    assert "cuisses de poulet" not in lire_frais(conn)["corrections"]


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


def test_si_libre_ne_declasse_pas_un_diner(client, conn):
    from casa import aujourd_hui_paris
    J = aujourd_hui_paris()
    for id_ in ("plat-riz-01", "plat-pates-01"):
        client.post("/api/plats", json={"id": id_, "nom": id_, "genre": "plat", "minutes": 20,
                                        "ingredients": ["riz"], "recette": "1.", "statut": "carnet"})
    jour = (J + timedelta(days=1)).isoformat()
    corps = {"jour": jour, "moment": "diner", "plats": ["plat-riz-01"], "issue": None, "si_libre": True}
    assert client.post("/api/repas", json=corps).status_code == 200               # soir libre
    r = client.post("/api/repas", json={**corps, "plats": ["plat-pates-01"]})            # pris par des plats
    assert r.status_code == 409 and r.get_json() == {"erreur": "soir déjà pris"}
    assert client.get("/api/diners").get_json()["repas"][0]["plats"] == ["plat-riz-01"]
    jour2 = (J + timedelta(days=2)).isoformat()
    client.post("/api/repas", json={"jour": jour2, "moment": "diner", "plats": [], "issue": "commande"})
    assert client.post("/api/repas", json={**corps, "jour": jour2}).status_code == 409   # issue seule
    passe = (J - timedelta(days=1)).isoformat()
    assert client.post("/api/repas", json={**corps, "jour": passe}).status_code == 409   # jour passé
    sans = {k: v for k, v in corps.items() if k != "si_libre"}
    assert client.post("/api/repas", json={**sans, "plats": ["plat-pates-01"]}).status_code == 200   # écrase, comme avant


def test_proposer_utilise_les_produits_a_finir(client, conn):
    from casa import aujourd_hui_paris
    J = aujourd_hui_paris()
    enregistrer_placard(conn, element("cuisses de poulet"))
    with conn.cursor() as cur:
        cur.execute("UPDATE placard SET maj_le = now() - interval '1 day' WHERE cle = 'cuisses de poulet'")
    conn.commit()
    client.post("/api/plats", json={"id": "plat-poulet-01", "nom": "Poulet rôti", "genre": "plat", "minutes": 30,
                                    "ingredients": ["cuisses de poulet", "riz"], "recette": "1.",
                                    "statut": "carnet"})
    proposes = client.post("/api/diners/proposer", json={}).get_json()["proposes"]
    jours = [j for j, id_ in proposes.items() if id_ == "plat-poulet-01"]
    assert jours and date.fromisoformat(jours[0]) <= J + timedelta(days=1)
