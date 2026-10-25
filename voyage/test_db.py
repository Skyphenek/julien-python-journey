"""Tests de db.py — accès Postgres à l'état de la checklist."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pytest
from db import (connecter, obtenir_etat, enregistrer_coche,
                lire_normales, enregistrer_normales, publier_page, lire_page,
                enregistrer_voyage, lire_voyage, enregistrer_valise_objets, lire_valise_objets,
                enregistrer_retour, supprimer_retour, lire_retours)
from valise import normales_avec_cache


@pytest.fixture
def conn():
    connexion = connecter("valise_test")
    with connexion.cursor() as cur:
        cur.execute("TRUNCATE etat_case, normales_climat, page_valise, voyages, valise_objets, retours")
    connexion.commit()
    yield connexion
    connexion.close()


def test_obtenir_etat_base_vide(conn):
    assert obtenir_etat(conn, "Hanoï") == {}


def test_enregistrer_coche_puis_lecture(conn):
    enregistrer_coche(conn, "Hanoï", "Julien", "Vêtements", "pantalons", True)
    assert obtenir_etat(conn, "Hanoï") == {"Hanoï/Julien/Vêtements/pantalons": True}


def test_enregistrer_coche_upsert_une_seule_ligne(conn):
    enregistrer_coche(conn, "Hanoï", "Julien", "Vêtements", "pantalons", True)
    enregistrer_coche(conn, "Hanoï", "Julien", "Vêtements", "pantalons", False)
    assert obtenir_etat(conn, "Hanoï") == {"Hanoï/Julien/Vêtements/pantalons": False}
    with conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM etat_case")
        assert cur.fetchone()[0] == 1


def test_obtenir_etat_filtre_par_voyage(conn):
    enregistrer_coche(conn, "Hanoï", "Julien", "Vêtements", "pantalons", True)
    enregistrer_coche(conn, "Paris", "Julien", "Vêtements", "manteau", True)
    assert obtenir_etat(conn, "Hanoï") == {"Hanoï/Julien/Vêtements/pantalons": True}



# --- Cache des normales climatiques ---

HANOI_JANV = {"tmin": 14.3, "tmax": 21.1, "jours_pluie": 10, "jours_forte_pluie": 3.4}
HANOI_JUIL = {"tmin": 26.8, "tmax": 33.0, "jours_pluie": 18, "jours_forte_pluie": 11.2}


def test_normales_absentes_du_cache(conn):
    assert lire_normales(conn, 21.03, 105.85, 1) is None


def test_enregistrer_puis_lire_normales(conn):
    enregistrer_normales(conn, 21.03, 105.85, {1: HANOI_JANV, 7: HANOI_JUIL})
    assert lire_normales(conn, 21.03, 105.85, 1) == HANOI_JANV
    assert lire_normales(conn, 21.03, 105.85, 7) == HANOI_JUIL


def test_cache_par_coordonnees_arrondies(conn):
    # Deux géocodages de "Hanoï" à quelques mètres près -> même ligne de cache
    enregistrer_normales(conn, 21.0285, 105.8542, {1: HANOI_JANV})
    assert lire_normales(conn, 21.03, 105.85, 1) == HANOI_JANV


def test_enregistrer_deux_fois_ne_duplique_pas(conn):
    enregistrer_normales(conn, 21.03, 105.85, {1: HANOI_JANV})
    enregistrer_normales(conn, 21.03, 105.85, {1: HANOI_JANV})
    with conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM normales_climat")
        assert cur.fetchone()[0] == 1


def test_normales_avec_cache_n_appelle_l_api_qu_une_fois(conn):
    appels = []
    def fausse_api(latitude, longitude):          # remplace l'API : compte les appels
        appels.append((latitude, longitude))
        return {1: HANOI_JANV, 7: HANOI_JUIL}

    assert normales_avec_cache(conn, 21.03, 105.85, 1, chercher=fausse_api) == HANOI_JANV
    assert normales_avec_cache(conn, 21.03, 105.85, 7, chercher=fausse_api) == HANOI_JUIL  # autre mois
    assert normales_avec_cache(conn, 21.03, 105.85, 1, chercher=fausse_api) == HANOI_JANV
    assert len(appels) == 1                       # 1 appel a rempli les 12 mois



# --- Page publiée en base (pour le serveur en ligne) ---

def test_lire_page_vide(conn):
    assert lire_page(conn) is None


def test_publier_remplace_la_page_precedente(conn):
    publier_page(conn, "<html>Tokyo</html>")
    publier_page(conn, "<html>Bangkok</html>")
    assert lire_page(conn) == "<html>Bangkok</html>"


def test_les_tests_ignorent_la_base_en_ligne(monkeypatch):
    # Garde-fou : même si DATABASE_URL pointe vers le cloud, "valise_test" reste locale
    monkeypatch.setenv("DATABASE_URL", "postgresql://pirate@exemple.invalid/prod")
    connexion = connecter("valise_test")
    assert connexion.info.dbname == "valise_test"
    connexion.close()



# --- Mémoire des voyages : identité + photo de la valise ---

from datetime import date

CODE = "2027-01-10 Tokyo › Bangkok"
ITINERAIRE = [{"destination": "Tokyo", "jours": 7, "mois": 1, "activites": ["ville"],
               "code_pays": "JP", "normales": {"tmin": 2.0, "tmax": 10.0, "jours_pluie": 5, "jours_forte_pluie": 1.5}}]


def test_enregistrer_puis_lire_voyage(conn):
    enregistrer_voyage(conn, CODE, "Tokyo › Bangkok", date(2027, 1, 10), ["Julien", "Laetitia"],
                       ITINERAIRE, {"froid": 7, "ville": 7})
    v = lire_voyage(conn, CODE)
    assert v["libelle"] == "Tokyo › Bangkok"
    assert v["depart"] == date(2027, 1, 10)
    assert v["personnes"] == ["Julien", "Laetitia"]
    assert v["itineraire"] == ITINERAIRE              # JSON aller-retour sans perte
    assert v["jours_types"] == {"froid": 7, "ville": 7}


def test_reenregistrer_un_voyage_le_met_a_jour(conn):
    enregistrer_voyage(conn, CODE, "Tokyo › Bangkok", date(2027, 1, 10), ["Julien"], ITINERAIRE, {})
    enregistrer_voyage(conn, CODE, "Tokyo › Bangkok", date(2027, 1, 10), ["Julien", "Laetitia"], ITINERAIRE, {})
    assert lire_voyage(conn, CODE)["personnes"] == ["Julien", "Laetitia"]
    with conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM voyages")
        assert cur.fetchone()[0] == 1


def test_photo_de_la_valise_remplacee_a_chaque_publication(conn):
    enregistrer_voyage(conn, CODE, "Tokyo › Bangkok", date(2027, 1, 10), ["Julien"], ITINERAIRE, {})
    enregistrer_valise_objets(conn, CODE, {"Julien": {"Vêtements": {"shorts": 3, "pull": 1}}})
    enregistrer_valise_objets(conn, CODE, {"Julien": {"Vêtements": {"shorts": 2}}})   # régénérée
    assert lire_valise_objets(conn, CODE) == {("Julien", "Vêtements", "shorts"): 2}



# --- Bilan de fin de voyage : les retours ---

import psycopg2


def _voyage(conn):
    enregistrer_voyage(conn, CODE, "Tokyo › Bangkok", date(2027, 1, 10), ["Julien"], ITINERAIRE, {})


def test_retour_enregistre_puis_lu(conn):
    _voyage(conn)
    enregistrer_retour(conn, CODE, "Julien", "t-shirts", "trop", quantite_utilisee=8)
    enregistrer_retour(conn, CODE, "Julien", "bouchons d'oreilles", "manque")
    assert lire_retours(conn, CODE) == [
        {"proprietaire": "Julien", "objet": "bouchons d'oreilles", "verdict": "manque", "quantite_utilisee": None},
        {"proprietaire": "Julien", "objet": "t-shirts", "verdict": "trop", "quantite_utilisee": 8},
    ]


def test_changer_d_avis_met_a_jour(conn):
    _voyage(conn)
    enregistrer_retour(conn, CODE, "Julien", "pull", "pas_servi")
    enregistrer_retour(conn, CODE, "Julien", "pull", "utile")
    assert [r["verdict"] for r in lire_retours(conn, CODE)] == ["utile"]


def test_supprimer_un_retour(conn):
    _voyage(conn)
    enregistrer_retour(conn, CODE, "Julien", "pull", "utile")
    supprimer_retour(conn, CODE, "Julien", "pull")
    assert lire_retours(conn, CODE) == []


def test_retour_sur_voyage_inconnu_refuse(conn):
    with pytest.raises(psycopg2.errors.ForeignKeyViolation):
        enregistrer_retour(conn, "1999-01-01 Atlantide", "Julien", "pull", "utile")
    conn.rollback()
