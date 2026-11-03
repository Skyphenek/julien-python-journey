"""Tests de la Cave en base (db.py) : enregistrer, boire, retirer, reprise de départ."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pytest
from db import connecter, lire_cave, enregistrer_bouteille, boire, retirer_bouteille, poser_cave
from cave_depart import CAVE_DEPART


def bouteille(id_="vin-a", **champs):
    return {"id": id_, "nom": "Saint-Joseph", "producteur": "", "appellation": "", "region": "", "couleur": "rouge",
            "millesime": 2019, "quantite": 1, "debut": 2026, "fin": 2028, "prix_bas": 25, "prix_haut": 30,
            "accords": ["boeuf"], "note": ""} | champs


@pytest.fixture
def conn():
    c = connecter("valise_test")
    with c.cursor() as cur:
        cur.execute("TRUNCATE cave")
        cur.execute("DELETE FROM reprises WHERE nom = 'cave-test'")
    c.commit()
    yield c
    c.close()


def test_enregistrer_et_lire(conn):
    enregistrer_bouteille(conn, bouteille())
    enregistrer_bouteille(conn, bouteille("vin-b", nom="Bandol", quantite=2))
    assert lire_cave(conn) == [bouteille("vin-b", nom="Bandol", quantite=2), bouteille()]   # tri par nom


def test_enregistrer_met_a_jour(conn):
    enregistrer_bouteille(conn, bouteille())
    enregistrer_bouteille(conn, bouteille(quantite=3, accords=["volaille", "fromage"], note="offert"))
    assert lire_cave(conn) == [bouteille(quantite=3, accords=["volaille", "fromage"], note="offert")]


def test_boire_jamais_sous_zero(conn):
    enregistrer_bouteille(conn, bouteille(quantite=1))
    assert boire(conn, "vin-a") == 0
    assert boire(conn, "vin-a") == 0
    assert lire_cave(conn)[0]["quantite"] == 0                       # reste en base (repli « Bues »)
    assert boire(conn, "inconnu") is None


def test_retirer(conn):
    enregistrer_bouteille(conn, bouteille())
    assert retirer_bouteille(conn, "vin-a") is True
    assert retirer_bouteille(conn, "vin-a") is False
    assert lire_cave(conn) == []


def test_reprise_une_seule_fois(conn):
    assert poser_cave(conn, "cave-test", CAVE_DEPART) == 19
    conn.commit()
    assert len(lire_cave(conn)) == 19
    boire(conn, "vin-maddalena")
    assert poser_cave(conn, "cave-test", CAVE_DEPART) is None        # déjà faite : rien ne bouge
    conn.commit()
    assert next(b for b in lire_cave(conn) if b["id"] == "vin-maddalena")["quantite"] == 1


def test_reprise_n_ecrase_pas(conn):
    enregistrer_bouteille(conn, bouteille("vin-peyrouquet", nom="Château Peyrouquet", quantite=6))
    assert poser_cave(conn, "cave-test", CAVE_DEPART) == 18
    conn.commit()
    assert next(b for b in lire_cave(conn) if b["id"] == "vin-peyrouquet")["quantite"] == 6
