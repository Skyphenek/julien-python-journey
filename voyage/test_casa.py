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
    assert [cle for cle, _, _ in HUB] == ["aujourdhui", "diners", "courses", "vadrouille"]   # les modules s'ajoutent à leur livraison
    assert HUB[0][2] == "./" and HUB[-1][2] == "vadrouille"
    assert HUB[-1][1] == "Vadrouille"           # « En Vadrouille » débordait de la barre du bas sur iPhone


def test_nav_marque_l_entree_active():
    nav = nav_hub("vadrouille")
    assert nav.startswith('<nav class="hub">')
    assert '<a href="vadrouille" data-hub="vadrouille" class="actif" aria-current="page">' in nav
    assert '<a href="./" data-hub="aujourdhui">' in nav


def test_nav_sans_lien_mort():
    nav = nav_hub("aujourdhui")
    for cle in ("colis",):
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


def test_ce_soir():
    vide = aujourdhui_en_html([], AUJOURD_HUI)
    assert '<a class="bloc-ce-soir vide" href="diners#ce-soir">' in vide and "Rien de prévu" in vide
    html = aujourdhui_en_html([], AUJOURD_HUI, plat_du_soir={"nom": "Carbonara", "minutes": 20})
    assert "<strong>Carbonara</strong><span>20 min" in html


def test_hier_soir_tant_que_pas_renseigne():
    hier = {"jour": AUJOURD_HUI - timedelta(days=1), "plat": "plat-carbonara", "issue": None}
    html = aujourdhui_en_html([], AUJOURD_HUI, soir_hier=hier)
    assert "Hier soir ?" in html and 'data-issue="commande"' in html
    assert "&quot;jour&quot;: &quot;2026-10-27&quot;, &quot;plat&quot;: &quot;plat-carbonara&quot;" in html
    assert "Hier soir ?" not in aujourdhui_en_html([], AUJOURD_HUI, soir_hier={**hier, "issue": "fait"})


def test_compteur_deliveroo():
    html = aujourdhui_en_html([], AUJOURD_HUI, compte={"semaine": 2, "moyenne": 1.5, "renseignes": 9})
    assert '<div class="bloc-compteur trop">' in html and "2 commandes ces 7 jours" in html and "Moyenne 1,5" in html
    assert '<div class="bloc-compteur ok">' in aujourdhui_en_html([], AUJOURD_HUI, compte={"semaine": 1, "moyenne": 1, "renseignes": 3})
    assert "bloc-compteur" not in aujourdhui_en_html([], AUJOURD_HUI, compte={"semaine": 0, "moyenne": 0, "renseignes": 0}).split("<body")[1]


def test_bloc_courses():
    html = aujourdhui_en_html([], AUJOURD_HUI, a_prendre=3)
    assert '<a class="bloc-courses" href="courses"><strong>Courses</strong><span>3 articles à prendre</span></a>' in html
    assert "1 article à prendre" in aujourdhui_en_html([], AUJOURD_HUI, a_prendre=1)
    assert 'class="bloc-courses"' not in aujourdhui_en_html([], AUJOURD_HUI).split("<body")[1]   # liste vide : rien
