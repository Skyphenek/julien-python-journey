"""Tests des dépenses partagées (rubrique Sur place) : solde en centimes, base, API, page."""
import sys
from datetime import date
from decimal import Decimal
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pytest
from db import connecter, enregistrer_voyage, ajouter_depense, lire_depenses, supprimer_depense, remplacer_voyage
from valise import solde_depenses, construire, rendre_page, HTML_SCRIPT, VERSION_PAGE

DEUX = ["Julien", "Laetitia"]


def dep(montant_eur, paye_par, pour=DEUX):
    return {"montant_eur": Decimal(montant_eur), "paye_par": paye_par, "pour": pour}


def test_solde_simple_a_deux():
    s = solde_depenses([dep("100", "Julien"), dep("40", "Laetitia")], DEUX)
    assert s["total"] == Decimal("140.00")
    assert s["par_personne"]["Julien"] == {"paye": Decimal("100.00"), "part": Decimal("70.00"), "net": Decimal("30.00")}
    assert s["remboursements"] == [{"de": "Laetitia", "a": "Julien", "montant": Decimal("30.00")}]


def test_depense_pour_une_seule_personne():
    s = solde_depenses([dep("20", "Julien", ["Laetitia"])], DEUX)
    assert s["remboursements"] == [{"de": "Laetitia", "a": "Julien", "montant": Decimal("20.00")}]


def test_partage_au_centime_pres():
    s = solde_depenses([dep("10", "Julien", ["Julien", "Laetitia", "Ami"])], ["Julien", "Laetitia", "Ami"])
    parts = sorted(p["part"] for p in s["par_personne"].values())
    assert parts == [Decimal("3.33"), Decimal("3.33"), Decimal("3.34")] and sum(parts) == Decimal("10.00")


def test_comptes_a_l_equilibre():
    assert solde_depenses([dep("50", "Julien"), dep("50", "Laetitia")], DEUX)["remboursements"] == []
    assert solde_depenses([], DEUX)["total"] == Decimal("0.00")


@pytest.fixture
def conn():
    c = connecter("valise_test")
    with c.cursor() as cur:
        cur.execute("TRUNCATE voyages, depenses CASCADE")
    c.commit()
    enregistrer_voyage(c, "2026-12-16 Hanoï", "Hanoï", date(2026, 12, 16), DEUX, [{"destination": "Hanoï", "jours": 5}], {})
    yield c
    c.close()


def test_depenses_ajoutees_lues_supprimees(conn):
    i = ajouter_depense(conn, "2026-12-16 Hanoï", "Phở", Decimal("350000"), "VND", Decimal("12.13"), "Julien", DEUX,
                        date(2026, 12, 17))
    ajouter_depense(conn, "2026-12-16 Hanoï", "Taxi", Decimal("8"), "EUR", Decimal("8"), "Laetitia", ["Julien"],
                    date(2026, 12, 18))
    d = lire_depenses(conn, "2026-12-16 Hanoï")
    assert [x["libelle"] for x in d] == ["Taxi", "Phở"]                      # la plus récente d'abord
    assert d[1]["montant"] == Decimal("350000.00") and d[1]["pour"] == DEUX and d[1]["jour"] == date(2026, 12, 17)
    supprimer_depense(conn, "2026-12-16 Hanoï", i)
    assert [x["libelle"] for x in lire_depenses(conn, "2026-12-16 Hanoï")] == ["Taxi"]


def test_depenses_suivent_un_voyage_modifie(conn):
    enregistrer_voyage(conn, "2026-12-17 Hanoï", "Hanoï", date(2026, 12, 17), DEUX, [{"destination": "Hanoï", "jours": 5}], {})
    ajouter_depense(conn, "2026-12-16 Hanoï", "Phở", Decimal("5"), "EUR", Decimal("5"), "Julien", DEUX, date(2026, 12, 17))
    remplacer_voyage(conn, "2026-12-16 Hanoï", "2026-12-17 Hanoï")
    assert len(lire_depenses(conn, "2026-12-17 Hanoï")) == 1 and lire_depenses(conn, "2026-12-16 Hanoï") == []


def test_page_bloc_depenses():
    voyage = {"depart": date(2026, 12, 16), "personnes": DEUX, "conduit": False, "lessive": None,
              "itineraire": [{"destination": "Hanoï", "jours": 5, "mois": 12, "code_pays": "VN", "activites": [],
                              "normales": None}]}
    html = rendre_page(voyage, construire(voyage))
    sur_place = html.split('<div class="rubrique" data-rubrique="sur-place"')[1].split('<div class="rubrique"')[0]
    assert '<div class="info depenses"' in sur_place and 'data-personnes="Julien|Laetitia"' in sur_place
    assert '<option value="EUR">' in sur_place and '<option value="VND">' in sur_place
    assert "api/depenses" in HTML_SCRIPT and VERSION_PAGE >= 14
