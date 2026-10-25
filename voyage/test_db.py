"""Tests de db.py — accès Postgres à l'état de la checklist."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pytest
from db import (connecter, obtenir_etat, enregistrer_coche,
                lire_normales, enregistrer_normales)
from valise import normales_avec_cache


@pytest.fixture
def conn():
    connexion = connecter("valise_test")
    with connexion.cursor() as cur:
        cur.execute("TRUNCATE etat_case, normales_climat")
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
