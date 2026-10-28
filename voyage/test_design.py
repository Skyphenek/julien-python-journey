"""Tests du design D : une couleur par rubrique, onglets à icônes, barre latérale sur ordinateur."""
import sys
from datetime import date
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from design import STYLE_D, TETE_POLICE, ICONES_RUBRIQUE
from valise import construire, rendre_page, accueil_en_html, RUBRIQUES, HTML_SCRIPT, VERSION_PAGE


def page():
    voyage = {"depart": date(2027, 1, 15), "personnes": ["Julien"], "conduit": False, "lessive": None,
              "itineraire": [{"destination": "Hanoï", "jours": 4, "mois": 1, "activites": [], "normales": None}]}
    return rendre_page(voyage, construire(voyage))


def test_chaque_rubrique_a_son_icone_et_sa_couleur():
    assert set(ICONES_RUBRIQUE) == {nom for nom, _ in RUBRIQUES}
    for nom, _ in RUBRIQUES:
        assert f"--{nom}:" in STYLE_D and f"--{nom}-doux:" in STYLE_D
    nav = page().split('<nav class="rubriques">')[1].split("</nav>")[0]
    assert nav.count('class="icone-rubrique"') == len(RUBRIQUES) and "🧳" not in nav


def test_page_voyage_en_tete_et_contenu():
    html = page()
    assert '<body data-rubrique="valise">' in html
    assert html.index('<header class="entete">') < html.index('<nav class="rubriques">') < html.index("<main>")
    assert html.index("</main>") > html.index('<div class="controls">')
    assert STYLE_D in html and TETE_POLICE in html and VERSION_PAGE >= 23
    assert "document.body.dataset.rubrique = nom" in HTML_SCRIPT


def test_ordinateur_barre_laterale():
    assert "@media (min-width: 900px)" in STYLE_D and "grid-template-areas" in STYLE_D


def test_accueil_au_design_d():
    html = accueil_en_html([], date(2026, 10, 28))
    assert '<body class="accueil">' in html and STYLE_D in html and "🧳 Nos valises" not in html
