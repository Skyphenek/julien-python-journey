"""Tests des infos de chaque étape (hébergement, adresse, réservation) — rubrique Sur place."""
import sys
from datetime import date
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pytest
from db import (connecter, enregistrer_voyage, enregistrer_infos_etape, lire_infos_etapes, remplacer_voyage,
                CHAMPS_ETAPE)
from valise import etapes_du_voyage, construire, rendre_page, HTML_SCRIPT, VERSION_PAGE

ALLER_RETOUR = [{"destination": "Hanoï", "jours": 3}, {"destination": "Ha Long", "jours": 2},
                {"destination": "Hanoï", "jours": 2}]


def test_etapes_avec_dates_et_rang_des_villes_revisitees():
    assert etapes_du_voyage(ALLER_RETOUR, date(2026, 12, 16)) == [
        {"destination": "Hanoï", "rang": 1, "du": date(2026, 12, 16), "au": date(2026, 12, 18)},
        {"destination": "Ha Long", "rang": 1, "du": date(2026, 12, 19), "au": date(2026, 12, 20)},
        {"destination": "Hanoï", "rang": 2, "du": date(2026, 12, 21), "au": date(2026, 12, 22)},
    ]


def test_page_sur_place_liste_les_etapes():
    voyage = {"depart": date(2026, 12, 16), "personnes": ["Julien"], "conduit": False, "lessive": None,
              "itineraire": [dict(e, mois=12, activites=[], normales=None) for e in ALLER_RETOUR]}
    html = rendre_page(voyage, construire(voyage))
    sur_place = html.split('<div class="rubrique" data-rubrique="sur-place"')[1].split('<div class="rubrique"')[0]
    assert '<div class="info etapes">' in sur_place
    assert 'data-destination="Hanoï" data-rang="2"' in sur_place and "21/12 → 22/12" in sur_place
    assert "api/infos/" in HTML_SCRIPT and "'infos:'" in HTML_SCRIPT          # synchro + copie hors ligne
    assert "google.com/maps/search" in HTML_SCRIPT
    assert VERSION_PAGE >= 13


@pytest.fixture
def conn():
    c = connecter("valise_test")
    with c.cursor() as cur:
        cur.execute("TRUNCATE voyages, infos_etape, depenses CASCADE")
    c.commit()
    yield c
    c.close()


def test_infos_enregistrees_puis_mises_a_jour(conn):
    enregistrer_voyage(conn, "2026-12-16 Hanoï", "Hanoï", date(2026, 12, 16), ["Julien"], ALLER_RETOUR, {})
    enregistrer_infos_etape(conn, "2026-12-16 Hanoï", "Hanoï", 2, {"hebergement": "Hôtel A", "adresse": "1 rue X"})
    enregistrer_infos_etape(conn, "2026-12-16 Hanoï", "Hanoï", 2, {"hebergement": "Hôtel B", "reservation": "AB12"})
    infos = lire_infos_etapes(conn, "2026-12-16 Hanoï")
    assert infos == [{"destination": "Hanoï", "rang": 2, "hebergement": "Hôtel B", "adresse": "",
                      "reservation": "AB12", "arrivee": "", "notes": ""}]
    assert set(CHAMPS_ETAPE) == {"hebergement", "adresse", "reservation", "arrivee", "notes"}


def test_infos_suivent_un_voyage_modifie(conn):
    for code in ("2026-12-16 Hanoï", "2026-12-17 Hanoï"):
        enregistrer_voyage(conn, code, "Hanoï", date(2026, 12, 16), ["Julien"], ALLER_RETOUR, {})
    enregistrer_infos_etape(conn, "2026-12-16 Hanoï", "Hanoï", 1, {"hebergement": "Hôtel A"})
    remplacer_voyage(conn, "2026-12-16 Hanoï", "2026-12-17 Hanoï")
    assert lire_infos_etapes(conn, "2026-12-17 Hanoï")[0]["hebergement"] == "Hôtel A"
    assert lire_infos_etapes(conn, "2026-12-16 Hanoï") == []
