"""Tests du carnet 🗓️ Programme : vols, hôtels, transports, activités, restos réservés."""
import sys
from datetime import date
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pytest
from db import (connecter, enregistrer_voyage, enregistrer_infos_etape, remplacer_voyage,
                enregistrer_reservation, lire_reservations, supprimer_reservation)
from serveur import creer_app
from valise import construire, rendre_page, RUBRIQUES, VERSION_PAGE
from programme import TYPES_RESERVATION, valider_reservation, hotels_depuis_infos, SCRIPT_PROGRAMME
from pwa import SCRIPT_PRECHARGEMENT

CODE = "2027-01-15 Hanoï"
ITINERAIRE = [{"destination": "Hanoï", "jours": 3}, {"destination": "Ha Long", "jours": 2},
              {"destination": "Hanoï", "jours": 2}]


def resa(**champs):
    base = {"id": "a1b2c3d4-0001", "voyage": CODE, "type": "vol", "titre": "AF 198",
            "jour": "2027-01-15", "heure": "10:40", "lieu": "CDG → HAN", "reference": "XYZ123"}
    return {**base, **champs}


# --- Validation (le téléphone envoie, le serveur vérifie) ---

def test_types_dans_l_ordre():
    assert list(TYPES_RESERVATION) == ["vol", "hotel", "transport", "activite", "resto", "autre"]


def test_reservation_valide_completee():
    r = valider_reservation(resa())
    assert r["jour"] == date(2027, 1, 15) and r["jour_fin"] is None
    assert r["heure_fin"] == "" and r["notes"] == "" and r["lien"] == ""


@pytest.mark.parametrize("champs", [
    {"type": "croisiere"},
    {"titre": "  "},
    {"titre": "x" * 201},
    {"jour": "15/01/2027"},
    {"heure": "25:00"},
    {"heure": "9h"},
    {"id": "court"},
    {"id": "a b c d e f g h"},
    {"jour_fin": "2027-01-14"},                               # fin avant le début
    {"lien": "javascript:alert(1)"},                          # seulement http(s)
    {"notes": "x" * 2001},
    {"telephone": 12},
    {"type": "hotel", "jour_fin": None},                       # un hôtel a une date de départ
    {"type": "hotel", "jour_fin": "2027-01-15"},               # … après l'arrivée
])
def test_reservation_invalide(champs):
    with pytest.raises(ValueError):
        valider_reservation(resa(**champs))


def test_hotel_et_lien_valides():
    r = valider_reservation(resa(type="hotel", titre="Hanoi Pearl", jour_fin="2027-01-18",
                                 lien="https://booking.com/x", lieu="6 Bảo Khánh, Hoàn Kiếm"))
    assert r["jour_fin"] == date(2027, 1, 18) and r["lien"] == "https://booking.com/x"


# --- Reprise des anciennes fiches d'étapes en réservations « Hôtel » ---

def test_hotels_depuis_infos_d_etapes():
    infos = [{"destination": "Hanoï", "rang": 2, "hebergement": "Hôtel B", "adresse": "1 rue X",
              "reservation": "AB12", "arrivee": "vers 15h", "notes": "code porte 1234"},
             {"destination": "Ha Long", "rang": 1, "hebergement": "", "adresse": "", "reservation": "",
              "arrivee": "", "notes": ""}]                         # fiche vide : rien à reprendre
    hotels = hotels_depuis_infos(CODE, ITINERAIRE, date(2027, 1, 15), infos)
    assert len(hotels) == 1
    h = hotels[0]
    assert (h["type"], h["titre"], h["lieu"], h["reference"]) == ("hotel", "Hôtel B", "1 rue X", "AB12")
    assert (h["jour"], h["jour_fin"]) == (date(2027, 1, 20), date(2027, 1, 22))   # 2 nuits, départ le lendemain
    assert "vers 15h" in h["notes"] and "code porte 1234" in h["notes"]
    assert hotels_depuis_infos(CODE, ITINERAIRE, date(2027, 1, 15), infos)[0]["id"] == h["id"]   # rejouable


def test_hotel_sans_nom_prend_la_destination():
    infos = [{"destination": "Ha Long", "rang": 1, "hebergement": "", "adresse": "Baie", "reservation": "",
              "arrivee": "", "notes": ""}]
    assert hotels_depuis_infos(CODE, ITINERAIRE, date(2027, 1, 15), infos)[0]["titre"] == "Hébergement Ha Long"


# --- Base ---

@pytest.fixture
def conn():
    c = connecter("valise_test")
    with c.cursor() as cur:
        cur.execute("TRUNCATE voyages, infos_etape, depenses, reservations CASCADE")
    c.commit()
    enregistrer_voyage(c, CODE, "Hanoï", date(2027, 1, 15), ["Julien", "Laetitia"], ITINERAIRE, {})
    yield c
    c.close()


def test_reservation_enregistree_modifiee_supprimee(conn):
    enregistrer_reservation(conn, valider_reservation(resa()))
    enregistrer_reservation(conn, valider_reservation(resa(heure="11:05")))          # même id : mise à jour
    enregistrer_reservation(conn, valider_reservation(resa(id="a1b2c3d4-0002", type="resto", titre="Bún chả",
                                                           jour="2027-01-15", heure="")))
    liste = lire_reservations(conn, CODE)
    assert [(r["titre"], r["heure"]) for r in liste] == [("AF 198", "11:05"), ("Bún chả", "")]   # heure vide en dernier
    supprimer_reservation(conn, CODE, "a1b2c3d4-0001")
    supprimer_reservation(conn, CODE, "a1b2c3d4-0001")                                   # deux fois : sans erreur
    assert [r["titre"] for r in lire_reservations(conn, CODE)] == ["Bún chả"]


def test_reservation_d_un_autre_voyage_pas_ecrasee(conn):
    enregistrer_voyage(conn, "2027-05-01 Rome", "Rome", date(2027, 5, 1), ["Julien"], [], {})
    enregistrer_reservation(conn, valider_reservation(resa()))
    enregistrer_reservation(conn, valider_reservation(resa(voyage="2027-05-01 Rome", titre="Pirate")))
    assert lire_reservations(conn, CODE)[0]["titre"] == "AF 198"
    assert lire_reservations(conn, "2027-05-01 Rome") == []


def test_reservations_suivent_un_voyage_modifie(conn):
    enregistrer_voyage(conn, "2027-01-16 Hanoï", "Hanoï", date(2027, 1, 16), ["Julien"], ITINERAIRE, {})
    enregistrer_reservation(conn, valider_reservation(resa()))
    remplacer_voyage(conn, CODE, "2027-01-16 Hanoï")
    assert lire_reservations(conn, "2027-01-16 Hanoï")[0]["titre"] == "AF 198"


# --- API ---

@pytest.fixture
def client(conn):
    return creer_app("valise_test", secret="").test_client()


def test_api_reservations(client):
    assert client.post("/api/reservations", json=resa()).status_code == 200
    liste = client.get(f"/api/reservations/{CODE}").get_json()
    assert liste[0]["jour"] == "2027-01-15" and liste[0]["jour_fin"] is None
    assert client.post("/api/reservations", json=resa(heure="9h")).status_code == 400
    assert client.post("/api/reservations", json=resa(voyage="inconnu")).status_code == 404
    assert client.delete(f"/api/reservations/{CODE}/a1b2c3d4-0001").status_code == 200
    assert client.get(f"/api/reservations/{CODE}").get_json() == []


# --- Page ---

def page():
    voyage = {"depart": date(2027, 1, 15), "personnes": ["Julien"], "conduit": False, "lessive": None,
              "itineraire": [dict(e, mois=1, activites=[], normales=None) for e in ITINERAIRE]}
    return rendre_page(voyage, construire(voyage))


def rubrique(html, nom):
    return html.split(f'<div class="rubrique" data-rubrique="{nom}"')[1].split('<div class="rubrique"')[0]


def test_rubrique_programme_entre_avant_et_sur_place():
    assert [n for n, _ in RUBRIQUES] == ["valise", "avant", "programme", "sur-place", "souvenirs"]
    html = page()
    prog = rubrique(html, "programme")
    assert '<div class="programme"' in prog and "+ Ajouter" in prog
    assert '"destination": "Ha Long"' in prog                       # les étapes, pour titrer les jours
    assert '<div class="info etapes">' not in html                   # l'ancien bloc a disparu
    assert SCRIPT_PROGRAMME in html
    assert VERSION_PAGE >= 17


def test_script_programme():
    for morceau in ("api/reservations/", "envoyerOuGarder", "'resa:'", "textContent", "google.com/maps/search",
                    "tel:", "file-videe", "X-Valise-Vite"):
        assert morceau in SCRIPT_PROGRAMME
    assert "innerHTML" not in SCRIPT_PROGRAMME                         # texte saisi : jamais en HTML


def test_script_programme_syntaxiquement_valide(tmp_path):
    import shutil, subprocess
    if shutil.which("node") is None:
        pytest.skip("Node absent")
    fichier = tmp_path / "programme.js"
    fichier.write_text('const VOYAGE="x", DEPART="2027-01-15", FIN="2027-01-21";\n' + SCRIPT_PROGRAMME)
    resultat = subprocess.run(["node", "--check", str(fichier)], capture_output=True, text=True)
    assert resultat.returncode == 0, resultat.stderr


def test_accueil_precharge_le_programme():
    assert "'api/reservations/'" in SCRIPT_PRECHARGEMENT
