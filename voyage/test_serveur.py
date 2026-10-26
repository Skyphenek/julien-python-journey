"""Tests de serveur.py — API Flask au-dessus de db.py."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pytest
from serveur import creer_app
from db import connecter, publier_page


@pytest.fixture
def client():
    conn = connecter("valise_test")
    with conn.cursor() as cur:
        cur.execute("TRUNCATE etat_case, page_valise, voyages, valise_objets, retours")
    conn.commit()
    conn.close()
    app = creer_app("valise_test", secret="")        # secret vide : routes à la racine
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


def test_coche_cle_mal_formee(client):
    reponse = client.post("/api/coche", json={"cle": "pantalon", "coche": True})
    assert reponse.status_code == 400


def test_coche_objet_contenant_un_slash(client):
    reponse = client.post(
        "/api/coche",
        json={"cle": "Hanoï/Julien/Divers/livre / liseuse", "coche": True},
    )
    assert reponse.status_code == 200
    reponse = client.get("/api/etat/Hanoï")
    assert reponse.get_json() == {"Hanoï/Julien/Divers/livre / liseuse": True}



# --- Mise en ligne : code secret dans l'adresse, page servie depuis la base ---

@pytest.fixture
def client_secret():
    return creer_app("valise_test", secret="s3cr3t").test_client()


def test_sans_le_secret_rien_n_existe(client_secret):
    assert client_secret.get("/").status_code == 404
    assert client_secret.get("/api/etat/Hanoï").status_code == 404


def test_avec_le_secret_l_api_repond(client_secret):
    assert client_secret.get("/v/s3cr3t/api/etat/Hanoï").status_code == 200


def test_page_servie_depuis_la_base(client):
    conn = connecter("valise_test")
    publier_page(conn, "<html>valise en base</html>")
    conn.close()
    reponse = client.get("/")
    assert reponse.status_code == 200
    assert "valise en base" in reponse.get_data(as_text=True)



# --- Bilan : API des retours ---

from datetime import date
from db import enregistrer_voyage

VOYAGE = "2027-04-30 Florence › Palerme"


@pytest.fixture
def client_voyage(client):
    conn = connecter("valise_test")
    enregistrer_voyage(conn, VOYAGE, "Florence › Palerme", date(2027, 4, 30), ["Julien"], [], {})
    conn.close()
    return client


def _retour(client, **champs):
    corps = {"voyage": VOYAGE, "proprietaire": "Julien", "objet": "t-shirts"} | champs
    return client.post("/api/retour", json=corps)


def test_retour_enregistre_et_relu(client_voyage):
    assert _retour(client_voyage, verdict="trop", quantite_utilisee=8).status_code == 200
    reponse = client_voyage.get(f"/api/retours/{VOYAGE}")
    assert reponse.get_json() == [{"proprietaire": "Julien", "objet": "t-shirts",
                                   "verdict": "trop", "quantite_utilisee": 8}]


def test_verdict_vide_supprime(client_voyage):
    _retour(client_voyage, verdict="utile")
    assert _retour(client_voyage, verdict=None).status_code == 200
    assert client_voyage.get(f"/api/retours/{VOYAGE}").get_json() == []


def test_verdict_inconnu_refuse(client_voyage):
    assert _retour(client_voyage, verdict="génial").status_code == 400


def test_quantite_negative_refusee(client_voyage):
    assert _retour(client_voyage, verdict="trop", quantite_utilisee=-2).status_code == 400


def test_objet_vide_refuse(client_voyage):
    assert _retour(client_voyage, objet="   ", verdict="manque").status_code == 400


def test_voyage_inconnu_refuse(client_voyage):
    reponse = client_voyage.post("/api/retour", json={"voyage": "1999 Atlantide", "proprietaire": "Julien",
                                                      "objet": "pull", "verdict": "utile"})
    assert reponse.status_code == 400


# --- Bouton météo : POST /api/meteo/<voyage> régénère la valise avec les prévisions ---
from datetime import date, timedelta
import valise
from db import enregistrer_voyage, lire_voyage, lire_page, lire_valise_objets, ajouter_regle


@pytest.fixture
def client_meteo(client, monkeypatch):
    """Un voyage qui part dans 3 jours ; prévision factice chaude et orageuse (aucun réseau)."""
    depart = date.today() + timedelta(days=3)
    itin = [{"destination": "Hanoï", "jours": 7, "mois": depart.month, "activites": ["ville"],
             "normales": {"tmin": 14.0, "tmax": 21.0, "jours_pluie": 10, "jours_forte_pluie": 1.0},
             "code_pays": "VN", "latitude": 21.03, "longitude": 105.85}]
    code = valise.code_voyage(depart, "Hanoï")
    conn = connecter("valise_test")
    with conn.cursor() as cur:
        cur.execute("TRUNCATE regles_perso")
    conn.commit()
    enregistrer_voyage(conn, code, "Hanoï", depart, ["Julien"], itin, {"ville": 7},
                       conduit=False, lessive=None)
    ajouter_regle(conn, "Julien", "oreiller gonflable", "Divers")
    conn.close()
    prevu = {"tmin": 24.0, "tmax": 32.0, "jours_pluie": 10, "jours_forte_pluie": 5.0,
             "prevu_le": date.today().isoformat()}
    monkeypatch.setattr(valise, "previsions", lambda *a: prevu)
    return client, code


def test_meteo_voyage_inconnu(client):
    assert client.post("/api/meteo/2027-01-01 Nulle Part").status_code == 404


def test_meteo_regenere_page_voyage_et_photo(client_meteo):
    client, code = client_meteo
    reponse = client.post("/api/meteo/" + code)
    assert reponse.status_code == 200
    assert reponse.get_json() == {"ok": True, "etapes_prevues": 1, "erreurs": []}
    conn = connecter("valise_test")
    try:
        assert lire_voyage(conn, code)["itineraire"][0]["prevision"]["tmax"] == 32.0
        page = lire_page(conn)
        assert "prévu le" in page
        photo = lire_valise_objets(conn, code)
        assert ("Julien", "Vêtements", "imperméable") in photo          # averses prévues -> K-way
        assert ("Julien", "Divers", "oreiller gonflable") in photo      # règles "toujours" appliquées
    finally:
        conn.close()


def test_meteo_echec_api_remonte_la_raison(client_meteo, monkeypatch):
    # un refus d'Open-Meteo ne doit plus ressembler à un succès
    import requests
    client, code = client_meteo
    refus = requests.Response()
    refus.status_code, refus.reason = 429, "Too Many Requests"
    def refuse(*a):
        raise requests.HTTPError(response=refus)
    monkeypatch.setattr(valise, "previsions", refuse)
    corps = client.post("/api/meteo/" + code).get_json()
    assert corps["etapes_prevues"] == 0
    assert corps["erreurs"] == ["Hanoï : 429 Too Many Requests"]
