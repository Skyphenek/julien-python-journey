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


# --- Sans emojis, Sur place épuré (maquette D) ---
import re
from valise import formulaire_en_html
EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-⛿⬀-⯿✀-✒✔✖-➿]")


def page_complete():
    voyage = {"depart": date(2027, 1, 15), "personnes": ["Julien", "Laetitia"], "conduit": True, "lessive": None,
              "itineraire": [{"destination": "Hanoï", "jours": 6, "mois": 1, "code_pays": "VN", "latitude": 21.03,
                              "longitude": 105.85, "activites": ["ville", "nature"], "normales": None},
                             {"destination": "Siem Reap", "jours": 4, "mois": 1, "code_pays": "KH", "latitude": 13.36,
                              "longitude": 103.86, "activites": ["culte"], "normales": None}]}
    return rendre_page(voyage, construire(voyage), aujourd_hui=date(2026, 10, 28))


def test_aucun_emoji_dans_les_pages():
    for html in (page_complete(), accueil_en_html([], date(2026, 10, 28)), formulaire_en_html()):
        assert EMOJI.findall(html) == []


def test_sur_place_tuiles_et_carte_depenses():
    sur_place = page_complete().split('<div class="rubrique" data-rubrique="sur-place"')[1].split('<div class="rubrique"')[0]
    tuiles = sur_place.split('<div class="tuiles">')[1].split('<div class="info depenses"')[0]
    assert tuiles.count('<li class="tuile" data-fuseau=') == 1 and 'Hanoï, Siem Reap' in tuiles and '+6 h / Paris' in tuiles
    assert '<li class="tuile" data-devise="VND">' in tuiles and '<div class="convertisseur" data-devise="KHR">' in tuiles
    assert '<button type="button" class="ajouter-depense" aria-expanded="false">+ Ajouter</button>' in sur_place
    assert '<form class="nouvelle-depense" hidden>' in sur_place and '<strong class="total">' in sur_place


def test_synchro_ne_touche_que_les_cases_de_la_valise():
    # Les cases « pour » des dépenses n'ont pas de data-key : la synchro ne doit pas les décocher
    assert "document.querySelectorAll('input[type=checkbox]')" not in HTML_SCRIPT
    assert HTML_SCRIPT.count("querySelectorAll('input[type=checkbox][data-key]')") == 3
