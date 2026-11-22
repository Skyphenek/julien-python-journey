"""Tests des Propositions en base et par l'API (app et routine)."""
import sys
from datetime import date
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pytest
from db import (changer_etat_proposition, connecter, creer_proposition, enregistrer_reservation, enregistrer_voyage,
                lire_passages, lire_propositions, marquer_passage, remplacer_voyage)
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
