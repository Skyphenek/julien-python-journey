"""Tests du squelette du hub : la page d'un voyage est découpée en rubriques."""
import sys
from datetime import date
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from valise import valise_en_html, paquet_vide, avant_de_partir, HTML_SCRIPT, VERSION_PAGE, RUBRIQUES

VN = [{"destination": "Hanoï", "jours": 7, "code_pays": "VN"}]


def page(taches=None):
    paquet = paquet_vide()
    paquet["Hygiène"]["trousse toilette"] = 1
    return valise_en_html({"Partagé": paquet, "Julien": paquet_vide()}, "Hanoï", 7, set(),
                          code="2027-01-10 Hanoï", depart=date(2027, 1, 10), taches=taches)


def rubrique(html, nom):
    return html.split(f'<div class="rubrique" data-rubrique="{nom}"')[1].split('<div class="rubrique"')[0]


def test_rubriques_dans_l_ordre():
    assert [r[0] for r in RUBRIQUES] == ["valise", "avant", "programme", "sur-place", "souvenirs"]
    nav = page().split('<nav class="rubriques">')[1].split("</nav>")[0]
    positions = [nav.index(f'data-rubrique="{r}"') for r, _ in RUBRIQUES]
    assert positions == sorted(positions)
    assert '<button data-rubrique="valise" class="actif">' in nav


def test_page_arrive_ouverte_sur_la_valise():
    html = page()
    assert '<div class="rubrique" data-rubrique="valise">' in html
    for r in ("avant", "sur-place", "souvenirs"):
        assert f'<div class="rubrique" data-rubrique="{r}" hidden>' in html


def test_la_valise_garde_ses_onglets_et_sa_progression():
    valise = rubrique(page(), "valise")
    assert '<nav class="tabs">' in valise and 'class="barres"' in valise
    assert '<section data-owner="Partagé">' in valise


def test_formalites_dans_la_rubrique_avant():
    html = page(avant_de_partir(VN, date(2027, 1, 10), date(2026, 10, 27)))
    assert "Avant de partir/visa-VN" in rubrique(html, "avant")
    assert "Avant de partir/visa-VN" not in rubrique(html, "valise")
    assert 'data-owner="Avant de partir"' not in html.split('<nav class="tabs">')[1].split("</nav>")[0]


def test_rubrique_avant_sans_formalites_pour_l_europe():
    assert "Avant de partir/visa" not in rubrique(page([]), "avant")


def test_rubriques_a_venir():
    html = page()
    assert "Rien à afficher" in rubrique(html, "sur-place")          # voyage sans pays connu : rien sur place
    assert "Rien à afficher" in rubrique(html, "souvenirs")         # sans voyageurs : pas de souvenirs


def test_script_des_rubriques():
    assert "function ouvrirRubrique" in HTML_SCRIPT
    assert "location.hash" in HTML_SCRIPT                      # lien direct : ?v=…#avant
    assert "ouvrirRubrique('valise')" in HTML_SCRIPT           # le mode bilan ramène à la valise
    assert "section[data-owner]:not(.avant)" in HTML_SCRIPT


def test_version_page():
    assert VERSION_PAGE >= 7


def test_javascript_de_la_page_syntaxiquement_valide(tmp_path):
    """Une apostrophe mal échappée casse tout le script de la page : Node le voit, pas Python."""
    import shutil, subprocess
    import pytest
    if shutil.which("node") is None:
        pytest.skip("Node absent")
    fichier = tmp_path / "page.js"
    fichier.write_text('const VOYAGE="x", DEPART="2027-01-10", FIN="2027-01-20", METEO_DU=null;\n' + HTML_SCRIPT)
    resultat = subprocess.run(["node", "--check", str(fichier)], capture_output=True, text=True)
    assert resultat.returncode == 0, resultat.stderr
