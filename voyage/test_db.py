"""Tests de db.py — accès Postgres à l'état de la checklist."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pytest
from db import connecter, obtenir_etat, enregistrer_coche


@pytest.fixture
def conn():
    connexion = connecter("valise_test")
    with connexion.cursor() as cur:
        cur.execute("TRUNCATE etat_case")
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
