"""Tests des Propositions en base et par l'API (app et routine)."""
import sys
from datetime import date
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pytest

import routine
from a_voir import valider_a_voir
from db import (archiver_voyage, changer_etat_proposition, connecter, creer_proposition, enregistrer_a_voir,
                enregistrer_reservation, enregistrer_voyage, lire_passages, lire_propositions, marquer_passage,
                remplacer_voyage)
from serveur import creer_app

CODE = "2026-12-10 Marrakech"
J = lambda n: date(2026, 12, n)
ITINERAIRE = [{"destination": "Marrakech", "jours": 5, "latitude": 31.63, "longitude": -8.0}]
P = {"titre": "Dar el Bacha", "pourquoi": "Avant Agafay.", "adresse": "", "trajet": "", "duree": "", "prix": "",
     "horaires": "", "a_confirmer": "horaires", "lien": "", "source": "", "genre": "voir", "reservation": "non",
     "creneau": "2026-12-11-matin", "jour": J(11), "periode": "matin", "debut": "09:00", "fin": "12:00",
     "ancre": "Dar Baraka", "destination": "Marrakech", "rang": 1, "verifie_le": None}


def resa(ident, genre, titre, jour, heure="", jour_fin=None, heure_fin=""):
    return {"id": ident, "voyage": CODE, "type": genre, "titre": titre, "jour": jour, "heure": heure,
            "jour_fin": jour_fin, "heure_fin": heure_fin, "lieu": "Bab Doukkala", "reference": "REF-SECRETE",
            "telephone": "0600000000", "lien": "https://booking.example/jeton", "notes": "73 euros"}


@pytest.fixture
def conn():
    c = connecter("valise_test")
    with c.cursor() as cur:
        cur.execute("TRUNCATE voyages, a_voir, reservations, propositions, propositions_passages CASCADE")
    c.commit()
    enregistrer_voyage(c, CODE, "Marrakech", J(10), ["Julien", "Laetitia"], ITINERAIRE, {})
    enregistrer_reservation(c, resa("resa-hotel-1", "hotel", "Dar Baraka", J(10), "14:00", J(11), "12:00"))
    enregistrer_reservation(c, resa("resa-hotel-2", "hotel", "Agafay palm", J(11), "15:00", J(14), "11:00"))
    yield c
    c.rollback()
    with c.cursor() as cur:
        cur.execute("TRUNCATE voyages, a_voir, reservations, propositions, propositions_passages CASCADE")
    c.commit()
    c.close()


def test_creer_lire_changer(conn):
    ident = creer_proposition(conn, CODE, "J-7", P)
    (p,) = lire_propositions(conn, CODE)
    assert ident.startswith("prop-") and p["id"] == ident and p["etat"] == "proposee" and p["jour"] == J(11)
    assert changer_etat_proposition(conn, ident, "ecartee") and changer_etat_proposition(conn, ident, "ecartee")
    assert lire_propositions(conn, CODE)[0]["etat"] == "ecartee"
    assert not changer_etat_proposition(conn, "prop-inconnue", "gardee")


def test_passages(conn):
    marquer_passage(conn, CODE, "J-7")
    marquer_passage(conn, CODE, "J-7")
    assert lire_passages(conn, CODE) == {"J-7"}


def test_suivent_un_voyage_modifie(conn):
    creer_proposition(conn, CODE, "J-7", P)
    marquer_passage(conn, CODE, "J-7")
    nouveau = "2026-12-10 Marrakech › Fès"
    enregistrer_voyage(conn, nouveau, "Marrakech › Fès", J(10), ["Julien"], ITINERAIRE, {})
    marquer_passage(conn, nouveau, "J-7")                                  # déjà là : pas d'erreur de clé
    remplacer_voyage(conn, CODE, nouveau)
    assert len(lire_propositions(conn, nouveau)) == 1 and lire_passages(conn, nouveau) == {"J-7"}
    assert lire_propositions(conn, CODE) == []


@pytest.fixture
def client(conn):
    return creer_app("valise_test", secret="", jeton="").test_client()


def test_api_propositions(client, conn):
    ident = creer_proposition(conn, CODE, "J-7", P)
    d = client.get(f"/api/propositions/{CODE}").get_json()
    assert d["creneaux"][0]["id"] == "2026-12-10-apres-midi" and d["propositions"][0]["jour"] == "2026-12-11"
    assert client.get("/api/propositions/inconnu").status_code == 404
    assert client.post(f"/api/propositions/{ident}/etat", json={"etat": "bizarre"}).status_code == 400
    assert client.post(f"/api/propositions/{ident}/etat", json=["gardee"]).status_code == 400
    assert client.post("/api/propositions/prop-inconnue/etat", json={"etat": "gardee"}).status_code == 404
    for _ in range(2):                                                      # rejoué hors ligne : sans effet
        assert client.post(f"/api/propositions/{ident}/etat", json={"etat": "gardee"}).status_code == 200
    assert client.get(f"/api/propositions/{CODE}").get_json()["propositions"] == []


def test_api_masque_apres_changement_d_hotel(client, conn):
    creer_proposition(conn, CODE, "J-7", P)
    enregistrer_reservation(conn, resa("resa-hotel-1", "hotel", "Riad Neuf", J(10), "14:00", J(11), "12:00"))
    assert client.get(f"/api/propositions/{CODE}").get_json()["propositions"] == []


JETON = "j" * 32
ENTETE = {"Authorization": f"Bearer {JETON}"}
FICHE = {"voyage": CODE, "palier": "J-7", "creneau": "2026-12-11-matin", "titre": "Dar el Bacha",
         "pourquoi": "Avant Agafay.", "genre": "voir", "reservation": "non", "source": "https://fnm.ma/bacha",
         "lien": "https://fnm.ma/bacha", "horaires": "10 h à 18 h"}


@pytest.fixture
def robot(conn, monkeypatch):
    monkeypatch.setattr(routine, "aujourd_hui_paris", lambda: J(3))
    return creer_app("valise_test", secret="s" * 20, jeton=JETON).test_client()


def deposer(robot, **champs):
    return robot.post("/routine/propositions", json={**FICHE, **champs}, headers=ENTETE)


def test_jeton_absent_court_ou_faux(conn, robot):
    for jeton in ("", "court"):
        app = creer_app("valise_test", secret="", jeton=jeton).test_client()
        assert app.get("/routine/travail", headers=ENTETE).status_code == 404
    assert robot.get("/routine/travail").status_code == 401
    assert robot.get("/routine/travail", headers={"Authorization": "Bearer " + "x" * 32}).status_code == 401
    assert robot.get("/routine/travail", headers={"Authorization": "Bearer é"}).status_code == 401
    assert robot.get(f"/api/propositions/{CODE}", headers=ENTETE).status_code == 404      # le jeton n'ouvre rien d'autre


def test_travail_liste_blanche(robot, conn):
    enregistrer_reservation(conn, resa("resa-resto-1", "resto", "Terrasse", J(10), "19:30"))
    r = robot.get("/routine/travail", headers=ENTETE)
    t = r.get_json()["a_faire"]
    assert set(t) == {"voyage", "palier", "reste", "creneaux", "deja_prevu", "ne_pas_reproposer"}
    assert (t["voyage"], t["palier"], t["reste"]) == (CODE, "J-7", 12)
    assert set(t["creneaux"][0]) == {"id", "jour", "periode", "debut", "fin", "ancre", "adresse", "destination",
                                     "latitude", "longitude", "places"}
    assert all(set(x) == {"type", "titre", "lieu", "jour", "heure"} for x in t["deja_prevu"])
    assert all(set(x) == {"titre", "lien"} for x in t["ne_pas_reproposer"])
    for secret in ("REF-SECRETE", "0600000000", "booking.example", "73 euros", "Laetitia"):
        assert secret not in r.get_data(as_text=True)


def test_rien_a_faire(robot, conn, monkeypatch):
    monkeypatch.setattr(routine, "aujourd_hui_paris", lambda: date(2026, 11, 1))
    assert robot.get("/routine/travail", headers=ENTETE).get_json() == {"a_faire": None}
    monkeypatch.setattr(routine, "aujourd_hui_paris", lambda: J(3))
    archiver_voyage(conn, CODE)
    assert robot.get("/routine/travail", headers=ENTETE).get_json() == {"a_faire": None}


def test_depot(robot, conn):
    assert deposer(robot).status_code == 201
    (p,) = lire_propositions(conn, CODE)
    assert (p["ancre"], p["jour"], p["debut"], p["rang"], p["verifie_le"], p["passage"]) == (
        "Dar Baraka", J(11), "09:00", 1, J(3), "J-7")
    assert deposer(robot, titre="").status_code == 400
    assert deposer(robot, titre="Autre", source="", lien="").status_code == 400          # horaires sans source
    assert deposer(robot, titre="Autre", lien="", palier="J-2").status_code == 409       # pas le passage dû
    assert deposer(robot, titre="Autre", lien="", creneau="2026-12-30-soir").status_code == 409
    assert deposer(robot, titre="Autre", lien="", voyage="inconnu").status_code == 409
    assert robot.post("/routine/propositions", json=[1], headers=ENTETE).status_code == 400


def test_doublons(robot, conn):
    deposer(robot)
    changer_etat_proposition(conn, lire_propositions(conn, CODE)[0]["id"], "ecartee")
    assert deposer(robot, titre="DAR EL BACHA !", lien="", creneau="2026-12-12-soir").status_code == 409
    assert deposer(robot, titre="Autre nom", creneau="2026-12-12-soir").status_code == 409    # même lien
    enregistrer_a_voir(conn, valider_a_voir({"id": "envie-0001", "voyage": CODE, "destination": "Marrakech", "rang": 1,
                                             "nom": "Tombeaux saadiens", "genre": "voir", "fait": False}))
    assert deposer(robot, titre="Les tombeaux saadiens", lien="").status_code == 409
    assert deposer(robot, titre="Agafay palm", lien="").status_code == 409                    # une réservation


def test_plafonds(robot, conn):
    assert [deposer(robot, titre=f"Idée {n}", lien="").status_code for n in range(3)] == [201, 201, 409]
    for n in range(10):
        creer_proposition(conn, CODE, "J-7", {**P, "titre": f"Vieille {n}", "creneau": "2026-12-30-soir"})
    assert deposer(robot, titre="De trop", lien="", creneau="2026-12-12-soir").status_code == 409   # 12 par passage
    assert robot.get("/routine/travail", headers=ENTETE).get_json() == {"a_faire": None}


def test_fini(robot, conn):
    assert robot.post("/routine/fini", json={"voyage": CODE, "palier": "J-2"}, headers=ENTETE).status_code == 409
    assert robot.post("/routine/fini", json={"voyage": CODE, "palier": "J-7"}, headers=ENTETE).status_code == 200
    assert lire_passages(conn, CODE) == {"J-7"}
    assert robot.get("/routine/travail", headers=ENTETE).get_json() == {"a_faire": None}
