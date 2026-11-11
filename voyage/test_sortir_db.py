"""Tests de Sortir en base (db.py) : créer, doublon, avis, mise à jour, reprise de départ."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from datetime import date

import pytest
from db import connecter
from sortir import valider_sortie

J = date(2026, 11, 13)


@pytest.fixture
def conn():
    c = connecter("valise_test")
    with c.cursor() as cur:
        cur.execute("TRUNCATE sorties")
        cur.execute("DELETE FROM reprises WHERE nom = 'sorties-test'")
    c.commit()
    yield c
    c.rollback()
    with c.cursor() as cur:                          # ne pas laisser de lignes aux modules suivants
        cur.execute("TRUNCATE sorties")
        cur.execute("DELETE FROM reprises WHERE nom = 'sorties-test'")
    c.commit()
    c.close()


def test_creer_lire_et_doublon(conn):
    from db import creer_sortie, lire_sorties
    id1, cree = creer_sortie(conn, valider_sortie({"titre": "Refuge des Fondus", "source": "routine"}, J))
    assert cree and id1.startswith("sortie-")
    id2, cree2 = creer_sortie(conn, valider_sortie({"titre": "le refuge des fondus", "source": "julien"}, J))
    assert (id2, cree2) == (id1, False)
    (x,) = lire_sorties(conn)
    assert x["titre"] == "Refuge des Fondus" and x["etat"] == "a-trier" and x["avis_julien"] is None


def test_avis_jusqu_a_l_envie_puis_maj(conn):
    from db import creer_sortie, donner_avis, maj_sortie
    i, _ = creer_sortie(conn, valider_sortie({"titre": "Catch Impro", "source": "julien"}, J))
    assert donner_avis(conn, i, "laetitia", "oui")["etat"] == "envie"
    assert maj_sortie(conn, i, {"etat": "prevue", "le": "2026-11-21"})["le"] == date(2026, 11, 21)
    f = maj_sortie(conn, i, {"etat": "faite", "pouce": "haut", "retour": "Génial"})
    assert (f["etat"], f["pouce"], f["retour"]) == ("faite", "haut", "Génial")
    assert donner_avis(conn, "inconnue", "julien", "oui") is None
    with pytest.raises(ValueError):
        maj_sortie(conn, i, {"etat": "volee"})


def test_poser_sorties_une_seule_fois(conn):
    from db import poser_sorties, lire_sorties
    depart = [{"titre": "Balade Campagne à Paris", "source": "routine", "type": "balade", "budget": "gratuit"}]
    assert poser_sorties(conn, "sorties-test", depart) == 1
    assert poser_sorties(conn, "sorties-test", depart) is None and len(lire_sorties(conn)) == 1
