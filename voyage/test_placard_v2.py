"""Tests de la reprise Placard v2 (placard_v2.py, db.reorganiser_placard)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pytest
from carnet_depart import CARNET_DEPART, A_TESTER
from courses import PLACARD_DEPART, ZONES, normaliser
from db import (connecter, semer_placard, semer_carnet, lire_courses, lire_plats, reorganiser_placard,
                enregistrer_article, vider_pris)
from diners import secours
from placard_v2 import PLACARD, HABITUELS


@pytest.fixture
def conn():
    c = connecter("valise_test")
    with c.cursor() as cur:
        cur.execute("TRUNCATE soirs, plats, courses, placard, reprises")
    c.commit()
    semer_placard(c, PLACARD_DEPART)
    semer_carnet(c, CARNET_DEPART, A_TESTER)
    yield c
    c.close()


def test_donnees_sans_doublon_ni_nom_de_checklist():
    cles = [normaliser(n) for n, _, _ in PLACARD] + [normaliser(n) for n, _ in HABITUELS]
    assert len(cles) == len(set(cles))
    assert all("(" not in n for n, _, _ in PLACARD)                     # noms courts, comme dans les recettes
    assert {z for _, z, _ in PLACARD} <= set(dict(ZONES))
    assert {e for _, _, e in PLACARD} <= {"stock", "samedi", "epiceries", None}
    for nom in ("chorizo", "eau volvic citron"):                         # les indispensables de Laetitia
        assert nom in cles
    ingredients = {normaliser(i) for p in CARNET_DEPART for i in p["ingredients"]}
    for vieux in PLACARD_DEPART:                                         # tout l'ancien placard a sa place
        assert normaliser(vieux) in cles, vieux
    assert {"sauce poisson", "riz carnaroli", "vermicelles de riz"} <= ingredients | {normaliser(n) for n, _, _ in PLACARD}


def test_reprise(conn):
    bilan = reorganiser_placard(conn)
    conn.commit()
    lu = lire_courses(conn)
    placard = {p["cle"]: p for p in lu["placard"]}
    articles = {normaliser(a["nom"]): a for a in lu["articles"]}
    assert placard["paprika fume"]["zone"] == "epices" and placard["paprika fume"]["en_stock"] is False
    assert placard["cumin"]["en_stock"] is True and placard["vin blanc"]["zone"] == "cave"
    assert placard["beaufort"]["en_stock"] is True and placard["beaufort"]["zone"] == "frigo"   # hors checklist
    assert "oeufs" not in placard and "lait" not in placard                                    # frais : habituels
    assert articles["oeufs"]["recurrent"] and articles["oeufs"]["actif"]                       # à acheter samedi
    assert articles["jambon"]["recurrent"] and not articles["jambon"]["actif"]                 # rangé
    assert articles["paprika fume"]["rayon"] == "epicerie" and articles["paprika fume"]["source"] == "placard"
    assert articles["sauce poisson"]["rayon"] == "specialise"                                  # vague 2
    assert articles["eau volvic citron"]["rayon"] == "boissons" and articles["eau volvic citron"]["actif"]
    assert placard["chorizo"]["zone"] == "frigo" and articles["chorizo"]["actif"]
    assert "cumin" not in articles                                                             # on l'a
    assert bilan["aux_courses"] == len([a for a in lu["articles"] if a["actif"]])


def test_reprise_une_seule_fois(conn):
    reorganiser_placard(conn)
    conn.commit()
    enregistrer_article(conn, {"id": "pris-paprika", "nom": "paprika fumé", "rayon": "epicerie", "pris": True,
                               "recurrent": False, "actif": True, "source": ""})
    avant = lire_courses(conn)
    assert reorganiser_placard(conn) is None                          # déjà faite : rien ne bouge
    conn.commit()
    assert lire_courses(conn) == avant


def test_apres_samedi_le_secours_garde_ses_diners(conn):
    reorganiser_placard(conn)
    conn.commit()
    for a in lire_courses(conn)["articles"]:                          # tout acheté, puis rangé
        if a["actif"]:
            enregistrer_article(conn, {**a, "pris": True})
    vider_pris(conn)
    lu = lire_courses(conn)
    faisables, _ = secours(lire_plats(conn), lu["placard"], lu["articles"])
    assert len(faisables) >= 7
