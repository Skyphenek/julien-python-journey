"""Tests du catalogue des ingrédients (catalogue.py) et du rangement d'office qu'il donne."""
import sys
from collections import Counter
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pytest
from carnet_depart import CARNET_DEPART, A_TESTER
from catalogue import CATALOGUE, cle_catalogue, chercher
from courses import RAYONS, ZONES, PLACARD_DEPART, deviner_rayon, deviner_zone, courses_en_html
from placard_v2 import PLACARD, HABITUELS
from recettes_air_fryer import AIR_FRYER
from recettes_legumes import LEGUMES


def test_sans_doublon_et_valide():
    assert len(CATALOGUE) > 900
    doublons = [c for c, n in Counter(cle_catalogue(nom) for nom, _, _ in CATALOGUE).items() if n > 1]
    assert doublons == []
    assert {r for _, r, _ in CATALOGUE} <= set(dict(RAYONS)) - {"autre"}
    assert {z for _, _, z in CATALOGUE} <= set(dict(ZONES))


def test_tout_ce_qui_existe_deja_est_au_catalogue():
    recettes = {i for p in CARNET_DEPART + A_TESTER + AIR_FRYER + LEGUMES for i in p["ingredients"]}
    placard = {n for n, _, _ in PLACARD} | {n for n, _ in HABITUELS} | set(PLACARD_DEPART)
    assert sorted(n for n in recettes | placard if not chercher(n)) == []
    # et dans la zone où ils l'ont rangé (le congélateur pour les demi-baguettes, etc.)
    assert [(n, z) for n, z, _ in PLACARD if chercher(n)[1] != z] == []


@pytest.mark.parametrize("nom, rayon, zone", [
    ("beaufort", "frais", "frigo"),                  # rangé dans « Autre » avant le catalogue
    ("Tomate cerise", "fruits-legumes", "frigo"),    # singulier, majuscule
    ("lentilles corail", "epicerie", "placard-sec"),
    ("pâte brisée", "frais", "frigo"),
    ("gochujang", "specialise", "epices"),
    ("magret de canard", "boucherie", "frigo"),
    ("tablettes lave-vaisselle", "hygiene-maison", "placard-sec"),
    ("croquettes pour chat", "hygiene-maison", "placard-sec"),
    ("demi-baguettes", "boulangerie", "congelateur"),
    ("gyoza", "surgeles", "congelateur"),
])
def test_range_d_office(nom, rayon, zone):
    assert deviner_rayon(nom) == rayon and deviner_zone(nom) == zone


def test_inconnu_passe_par_les_mots():
    assert deviner_rayon("tomates cerises bio") == "fruits-legumes"
    assert deviner_rayon("truc introuvable") == "autre"


def test_suggestions_a_la_saisie():
    page = courses_en_html()
    assert '<datalist id="catalogue">' in page and '<option value="lentilles corail">' in page
    assert page.count('list="catalogue"') == 2 and 'id="zones-catalogue"' in page


def test_epicerie_italienne():
    from catalogue import ITALIEN
    italien = {cle_catalogue(n) for n in ITALIEN}
    for nom in ("pecorino", "guanciale ou pancetta", "tomates pelées", "anchois", "farine 00"):
        assert cle_catalogue(nom) in italien, nom
    assert cle_catalogue("sauce soja") not in italien
