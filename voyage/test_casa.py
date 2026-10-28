"""Tests du hub Casa Binomerie : la navigation et la page Aujourd'hui."""
import sys
from datetime import date, timedelta
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from design import nav_hub, HUB
from casa import aujourdhui_en_html, prochain_voyage, HORIZON_VADROUILLE

AUJOURD_HUI = date(2026, 10, 28)


def voyage(depart, jours=10, libelle="Hanoï"):
    return {"code": f"{depart.isoformat()} {libelle}", "libelle": libelle, "depart": depart,
            "fin": depart + timedelta(days=jours), "personnes": ["Julien", "Laetitia"],
            "etapes": [{"destination": libelle, "jours": jours}]}


def test_le_hub_commence_par_aujourd_hui_et_finit_par_la_vadrouille():
    assert [cle for cle, _, _ in HUB] == ["aujourdhui", "vadrouille"]    # les modules s'ajoutent à leur livraison
    assert HUB[0][2] == "./" and HUB[-1][2] == "vadrouille"


def test_nav_marque_l_entree_active():
    nav = nav_hub("vadrouille")
    assert nav.startswith('<nav class="hub">')
    assert '<a href="vadrouille" data-hub="vadrouille" class="actif" aria-current="page">' in nav
    assert '<a href="./" data-hub="aujourdhui">' in nav


def test_nav_sans_lien_mort():
    nav = nav_hub("aujourdhui")
    for cle in ("diners", "courses", "colis"):
        assert cle not in nav


def test_page_aujourd_hui():
    html = aujourdhui_en_html([], AUJOURD_HUI)
    assert "<title>Casa Binomerie</title>" in html
    assert "<h1>Casa Binomerie</h1>" in html
    assert "mercredi 28 octobre" in html
    assert 'data-hub="aujourdhui" class="actif"' in html
    assert 'rel="manifest"' in html                                  # reste installable


def test_prochain_voyage_dans_l_horizon():
    assert HORIZON_VADROUILLE == 60
    proche = voyage(AUJOURD_HUI + timedelta(days=59))
    assert prochain_voyage([proche], AUJOURD_HUI) == proche
    assert prochain_voyage([voyage(AUJOURD_HUI + timedelta(days=60))], AUJOURD_HUI) is None


def test_prochain_voyage_en_cours_ou_passe():
    en_cours = voyage(AUJOURD_HUI - timedelta(days=2))
    assert prochain_voyage([en_cours], AUJOURD_HUI) == en_cours
    assert prochain_voyage([voyage(AUJOURD_HUI - timedelta(days=30))], AUJOURD_HUI) is None
    assert prochain_voyage([], AUJOURD_HUI) is None


def test_prochain_voyage_le_plus_proche():
    loin, pres = voyage(AUJOURD_HUI + timedelta(days=40), libelle="Rome"), voyage(AUJOURD_HUI + timedelta(days=5))
    assert prochain_voyage([loin, pres], AUJOURD_HUI) == pres


def test_bloc_vadrouille_avec_compte_a_rebours():
    html = aujourdhui_en_html([voyage(AUJOURD_HUI + timedelta(days=5))], AUJOURD_HUI)
    bloc = html.split('<div class="bloc-vadrouille">')[1].split("</div>")[0]
    assert 'href="vadrouille?v=2026-11-02%20Hano%C3%AF"' in bloc
    assert "Hanoï" in bloc and 'class="compte"' in bloc


def test_sans_voyage_proche_pas_de_bloc_vadrouille():
    html = aujourdhui_en_html([voyage(AUJOURD_HUI + timedelta(days=90))], AUJOURD_HUI)
    assert '<div class="bloc-vadrouille">' not in html
    assert 'class="attente"' in html
