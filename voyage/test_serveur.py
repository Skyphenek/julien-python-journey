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


def test_page_du_voyage_servie_depuis_la_base(client):
    from datetime import date as d
    from db import enregistrer_voyage as ev
    conn = connecter("valise_test")
    ev(conn, "2026-12-30 Rome", "Rome", d(2026, 12, 30), ["Julien"], [{"destination": "Rome", "jours": 3}], {})
    publier_page(conn, "<html>valise en base</html>", cle="2026-12-30 Rome")
    conn.close()
    reponse = client.get("/?v=2026-12-30 Rome")
    assert reponse.status_code == 200
    assert "valise en base" in reponse.get_data(as_text=True)


def test_accueil_liste_les_voyages(client):
    from datetime import date as d
    from db import enregistrer_voyage as ev
    conn = connecter("valise_test")
    ev(conn, "2026-12-30 Rome", "Rome", d(2026, 12, 30), ["Julien"], [{"destination": "Rome", "jours": 3}], {})
    conn.close()
    html = client.get("/").get_data(as_text=True)
    assert "Rome" in html and "?v=2026-12-30%20Rome" in html


def test_voyage_inconnu_404(client):
    assert client.get("/?v=2027-01-01 Nulle Part").status_code == 404



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
    """Un voyage qui part dans 3 jours (une étape, Hanoï, 7 jours)."""
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
    return client, code


def test_meteo_voyage_inconnu(client):
    assert client.post("/api/meteo/2027-01-01 Nulle Part", json={"previsions": {}}).status_code == 404

def test_fenetres_du_voyage(client_meteo):
    client, code = client_meteo
    corps = client.get("/api/meteo/" + code + "/fenetres").get_json()
    assert [f["destination"] for f in corps["fenetres"]] == ["Hanoï"]
    assert corps["fenetres"][0]["url"].startswith("https://api.open-meteo.com/")


def test_fenetres_voyage_inconnu(client):
    assert client.get("/api/meteo/2027-01-01 Nulle Part/fenetres").status_code == 404


def test_meteo_applique_les_previsions_du_navigateur(client_meteo):
    client, code = client_meteo
    jours = [(date.today() + timedelta(days=3 + i)).isoformat() for i in range(7)]
    daily = {"time": jours, "temperature_2m_max": [32.0] * 7, "temperature_2m_min": [24.0] * 7,
             "precipitation_sum": [0, 12.0, 0, 0, 0, 0, 0]}
    reponse = client.post("/api/meteo/" + code, json={"previsions": {"0": daily}})
    assert reponse.get_json() == {"ok": True, "etapes_prevues": 1, "erreurs": []}
    conn = connecter("valise_test")
    try:
        assert lire_voyage(conn, code)["itineraire"][0]["prevision"]["tmax"] == 32.0
        assert "prévu le" in lire_page(conn, code)
        photo = lire_valise_objets(conn, code)
        assert ("Julien", "Vêtements", "imperméable") in photo          # averses prévues -> K-way
        assert ("Julien", "Divers", "oreiller gonflable") in photo      # règles "toujours" appliquées
    finally:
        conn.close()


def test_meteo_erreur_du_navigateur_remontee(client_meteo):
    client, code = client_meteo
    corps = client.post("/api/meteo/" + code,
                        json={"previsions": {"0": {"erreur": "429 Too Many Requests"}}}).get_json()
    assert corps["etapes_prevues"] == 0
    assert corps["erreurs"] == ["Hanoï : 429 Too Many Requests"]


def test_meteo_corps_invalide(client_meteo):
    client, code = client_meteo
    assert client.post("/api/meteo/" + code, json={"previsions": "nope"}).status_code == 400


def test_meteo_ancienne_page_republiee_avec_le_nouveau_bouton(client_meteo):
    # une page publiée avant le passage au navigateur envoie un POST vide : on la republie
    client, code = client_meteo
    corps = client.post("/api/meteo/" + code).get_json()
    assert corps["etapes_prevues"] == 0
    assert corps["erreurs"] == ["page mise à jour : recharge-la puis réessaie"]
    conn = connecter("valise_test")
    try:
        assert "/fenetres" in lire_page(conn, code)           # le nouveau bouton est en ligne
    finally:
        conn.close()


def test_page_reconstruite_depuis_la_photo_si_absente(client_meteo):
    # voyage enregistré, photo en base, mais aucune page à son nom (ex. page publiée en "courante")
    from db import enregistrer_valise_objets
    client, code = client_meteo
    conn = connecter("valise_test")
    enregistrer_valise_objets(conn, code, {"Partagé": {"Divers": {"parapluie": 1}},
                                           "Julien": {"Vêtements": {"t-shirts": 4}}})
    conn.close()
    html = client.get("/?v=" + code).get_data(as_text=True)
    assert "t-shirts" in html and "parapluie" in html               # fidèle à la photo, pas recalculée
    assert "×4" in html
    conn = connecter("valise_test")
    try:
        assert lire_page(conn, code) is not None                    # désormais stockée
    finally:
        conn.close()


# --- Création en ligne, étape 2 : recherche de destination et normales via le téléphone ---

def test_lieux_url_puis_interpretation(client):
    url = client.get("/api/lieux?nom=Hanoï").get_json()["url"]
    assert url.startswith("https://geocoding-api.open-meteo.com/")
    reponse = {"results": [{"name": "Hanoï", "admin1": "Hanoï", "country": "Vietnam", "country_code": "VN",
                            "latitude": 21.02, "longitude": 105.84}]}
    lieux = client.post("/api/lieux", json={"reponse": reponse}).get_json()["lieux"]
    assert lieux[0]["libelle"] == "Hanoï — Hanoï, Vietnam"
    assert client.get("/api/lieux").status_code == 400                   # nom manquant


def _historique(jours):
    """Un faux historique Open-Meteo : chaque jour 20-30 °C, un jour sur trois à 6 mm."""
    from datetime import date as d, timedelta as td
    debut = d(2021, 1, 1)
    dates = [(debut + td(days=i)).isoformat() for i in range(jours)]
    return {"time": dates, "temperature_2m_max": [30.0] * jours, "temperature_2m_min": [20.0] * jours,
            "precipitation_sum": [6.0 if i % 3 == 0 else 0.0 for i in range(jours)]}


def test_normales_absentes_du_cache_puis_envoyees_par_le_telephone(client):
    conn = connecter("valise_test")
    with conn.cursor() as cur:
        cur.execute("TRUNCATE normales_climat")
    conn.commit()
    conn.close()
    r = client.get("/api/normales?latitude=38.72&longitude=-9.14&mois=5").get_json()
    assert "normales" not in r and r["url"].startswith("https://archive-api.open-meteo.com/")
    n = client.post("/api/normales", json={"latitude": 38.72, "longitude": -9.14, "mois": 5,
                                           "daily": _historique(5 * 365)}).get_json()["normales"]
    assert (n["tmin"], n["tmax"]) == (20.0, 30.0)
    # deuxième demande : servie depuis le cache, sans téléchargement
    assert client.get("/api/normales?latitude=38.72&longitude=-9.14&mois=5").get_json()["normales"]["tmax"] == 30.0


def test_normales_requetes_invalides(client):
    assert client.get("/api/normales?latitude=abc&longitude=1&mois=5").status_code == 400
    assert client.get("/api/normales?latitude=1&longitude=1&mois=13").status_code == 400
    assert client.post("/api/normales", json={"latitude": 1, "longitude": 1, "mois": 5,
                                              "daily": {"time": "x"}}).status_code == 400


# --- Création en ligne, étape 3 : POST /api/voyages ---

CORPS_LISBONNE = {
    "depart": "2027-05-01", "personnes": "l", "conduit": False, "lessive": None,
    "etapes": [{"destination": "Lisbonne", "code_pays": "PT", "latitude": 38.72, "longitude": -9.14,
                "jours": 4, "activites": ["ville", "plage"]}],
}


@pytest.fixture
def client_creation(client):
    conn = connecter("valise_test")
    with conn.cursor() as cur:
        cur.execute("TRUNCATE normales_climat, regles_perso")
    conn.commit()
    conn.close()
    return client


def test_formulaire_servi(client):
    html = client.get("/?nouvelle").get_data(as_text=True)
    assert "api/voyages" in html


def test_creation_demande_les_normales_manquantes(client_creation):
    r = client_creation.post("/api/voyages", json=CORPS_LISBONNE)
    assert r.status_code == 409
    assert r.get_json()["manquantes"] == [{"etape": 0, "destination": "Lisbonne",
                                           "latitude": 38.72, "longitude": -9.14, "mois": 5}]


def test_creation_avec_normales_en_cache(client_creation):
    from db import enregistrer_normales, lire_valise_objets
    conn = connecter("valise_test")
    enregistrer_normales(conn, 38.72, -9.14, {5: {"tmin": 14.0, "tmax": 26.0, "jours_pluie": 3,
                                                  "jours_forte_pluie": 0.5}})
    conn.close()
    r = client_creation.post("/api/voyages", json=CORPS_LISBONNE)
    assert r.status_code == 201
    corps = r.get_json()
    assert corps["code"] == "2027-05-01 Lisbonne"
    assert corps["url"] == "?v=2027-05-01%20Lisbonne"
    conn = connecter("valise_test")
    try:
        v = lire_voyage(conn, corps["code"])
        assert v["personnes"] == ["Laetitia"]
        assert v["itineraire"][0]["normales"]["tmax"] == 26.0         # climat repris du cache
        assert ("Laetitia", "Vêtements", "maillot de bain") in lire_valise_objets(conn, corps["code"])
        assert "Lisbonne" in lire_page(conn, corps["code"])
    finally:
        conn.close()
    assert "Lisbonne" in client_creation.get("/").get_data(as_text=True)     # visible à l'accueil


def test_creation_forcee_sans_normales(client_creation):
    # Open-Meteo injoignable depuis le téléphone : la valise est créée quand même
    r = client_creation.post("/api/voyages", json={**CORPS_LISBONNE, "forcer": True})
    assert r.status_code == 201
    conn = connecter("valise_test")
    try:
        assert lire_voyage(conn, r.get_json()["code"])["itineraire"][0]["normales"] is None
    finally:
        conn.close()


def test_creation_saisie_invalide(client_creation):
    r = client_creation.post("/api/voyages", json={**CORPS_LISBONNE, "etapes": []})
    assert r.status_code == 400 and "étape" in r.get_json()["erreur"]
    assert client_creation.post("/api/voyages").status_code == 400
