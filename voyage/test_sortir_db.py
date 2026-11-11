"""Tests de Sortir en base (db.py) : créer, doublon, avis, mise à jour, reprise de départ."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from datetime import date
from zoneinfo import ZoneInfo

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
    conn.commit()
    assert poser_sorties(conn, "sorties-test", depart) is None and len(lire_sorties(conn)) == 1


def test_poser_sorties_a_blanc_sans_commit(conn):
    from db import poser_sorties, lire_sorties
    depart = [{"titre": "Balade Campagne à Paris", "source": "routine", "type": "balade", "budget": "gratuit"}]
    assert poser_sorties(conn, "sorties-test", depart) == 1
    conn.rollback()                                  # à blanc : l'appelant annule
    assert lire_sorties(conn) == []
    assert poser_sorties(conn, "sorties-test", depart) == 1   # la reprise n'a pas été notée


def test_poser_sorties_doublons_dans_le_lot(conn):
    from db import poser_sorties, lire_sorties
    lot = [{"titre": "Catch Impro", "source": "routine"}, {"titre": "catch impro", "source": "routine"}]
    assert poser_sorties(conn, "sorties-test", lot) == 1
    assert len(lire_sorties(conn)) == 1


def test_donner_avis_garde_sur_qui():
    from db import donner_avis
    with pytest.raises(ValueError, match="avis invalide"):   # avant tout SQL : pas de conn
        donner_avis(None, "sortie-x", "tiers", "oui")


def test_une_sortie_par_id(conn):
    from db import creer_sortie, lire_sorties, _une_sortie
    i, _ = creer_sortie(conn, valider_sortie({"titre": "Catch Impro", "source": "julien"}, J))
    creer_sortie(conn, valider_sortie({"titre": "Expo Bob", "source": "laetitia"}, J))
    assert _une_sortie(conn, i) == next(s for s in lire_sorties(conn) if s["id"] == i)
    assert _une_sortie(conn, "inconnue") is None


@pytest.fixture
def client(conn):
    from serveur import creer_app
    return creer_app("valise_test", secret="").test_client()


def test_api_sorties(client):
    r = client.post("/api/sorties", json={"titre": "Refuge des Fondus", "source": "routine", "type": "resto-bar"})
    assert r.status_code == 201 and r.get_json()["id"].startswith("sortie-")
    i = r.get_json()["id"]
    r2 = client.post("/api/sorties", json={"titre": "refuge des fondus", "source": "julien"})
    assert r2.status_code == 409 and r2.get_json() == {"id": i, "doublon": True}
    assert client.post("/api/sorties", json={"titre": "", "source": "julien"}).status_code == 400
    assert client.post(f"/api/sorties/{i}/avis", json={"qui": "julien", "avis": "oui"}).get_json()["etat"] == "a-trier"
    assert client.post(f"/api/sorties/{i}/avis", json={"qui": "laetitia", "avis": "oui"}).get_json()["etat"] == "envie"
    # « Annuler » juste après le vote : avis null, l'Envie revient à trier ; un avis absent est refusé
    r3 = client.post(f"/api/sorties/{i}/avis", json={"qui": "laetitia", "avis": None}).get_json()
    assert r3["etat"] == "a-trier" and r3["avis_laetitia"] is None
    assert client.post(f"/api/sorties/{i}/avis", json={"qui": "laetitia"}).status_code == 400
    assert client.post(f"/api/sorties/{i}/avis", json={"qui": "laetitia", "avis": "oui"}).get_json()["etat"] == "envie"
    assert client.post(f"/api/sorties/{i}", json={"etat": "prevue", "le": "2026-11-21"}).get_json()["le"] == "2026-11-21"
    assert client.post("/api/sorties/inconnue/avis", json={"qui": "julien", "avis": "oui"}).status_code == 404
    assert client.post(f"/api/sorties/{i}", json={"etat": "volee"}).status_code == 400
    d = client.get("/api/sorties").get_json()
    assert [x["id"] for x in d["sorties"]] == [i] and "aujourd_hui" in d
    assert client.get("/api/sorties/weekend").status_code == 200


def test_accueil_sans_table_sorties(client, monkeypatch):
    import psycopg2.errors
    import serveur

    def sans_table(conn):
        raise psycopg2.errors.UndefinedTable("relation \"sorties\" does not exist")
    monkeypatch.setattr(serveur, "lire_sorties", sans_table)
    r = client.get("/")
    assert r.status_code == 200 and "bloc-sortir" not in r.get_data(as_text=True).split("</style>")[-1]


def test_api_sorties_corps_invalide(client):
    assert client.post("/api/sorties", data="pas du json").status_code == 400
    assert client.post("/api/sorties", json=["liste"]).status_code == 400


def test_sorties_depart_valides_sans_doublon_ni_cadeau():
    from sorties_depart import SORTIES_DEPART
    from sortir import doublon
    vues = []
    for s in SORTIES_DEPART:
        v = valider_sortie(s, J)
        assert v["titre"], s
        titre = s["titre"].lower()
        # « soin massage duo » au spa = une sortie à deux (autorisée) ; un « soin » seul serait un cadeau
        assert not any(mot in titre for mot in ("bon cadeau", "spa day")), s["titre"]
        assert "soin " not in titre or "duo" in titre, s["titre"]
        assert doublon(v, vues) is None, s["titre"]
        vues.append({"id": len(vues), **v})
    assert len(SORTIES_DEPART) == 97


def test_poser_sorties_garde_les_dates_d_origine(conn):
    from db import poser_sorties, lire_sorties
    lot = [{"titre": "Vieille idée", "source": "routine", "propose_le": "2026-03-01"},
           {"titre": "Idée récente", "source": "routine", "propose_le": "2026-10-20"},
           {"titre": "Idée du milieu", "source": "routine", "propose_le": "2026-06-15"}]
    assert poser_sorties(conn, "sorties-test", lot) == 3
    conn.commit()
    lues = lire_sorties(conn)
    assert [s["titre"] for s in lues] == ["Idée récente", "Idée du milieu", "Vieille idée"]
    assert [s["cree_le"].astimezone(ZoneInfo("Europe/Paris")).date().isoformat() for s in lues] \
        == ["2026-10-20", "2026-06-15", "2026-03-01"]
