"""Tests de courses.py : la liste partagée et le placard (logique pure, sans base)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pytest
from courses import (RAYONS, ZONES, normaliser, deviner_rayon, deviner_zone, valider_article, valider_placard,
                     PLACARD_DEPART, courses_en_html)

ID = "a1b2c3d4-0000"


def test_normaliser_ignore_casse_accents_et_espaces():
    assert normaliser("  Crème   Fraîche ") == "creme fraiche"
    assert normaliser("ŒUFS") == "oeufs"
    assert normaliser("Crème fraîche") == normaliser("creme fraiche")


def test_rayons_dans_l_ordre_du_magasin():
    assert [cle for cle, _ in RAYONS] == ["fruits-legumes", "frais", "boucherie", "boulangerie", "epicerie",
                                          "surgeles", "boissons", "specialise", "hygiene-maison", "autre"]


@pytest.mark.parametrize("nom, rayon", [
    ("Lait", "frais"), ("crème fraîche", "frais"), ("Œufs", "frais"), ("pecorino", "frais"),
    ("tomates", "fruits-legumes"), ("Pommes de terre", "fruits-legumes"), ("citrons", "fruits-legumes"),
    ("steak haché", "boucherie"), ("rôti de bœuf", "boucherie"),
    ("baguette", "boulangerie"),
    ("spaghetti", "epicerie"), ("tomates pelées", "epicerie"), ("huile d'olive", "epicerie"),
    ("petits pois surgelés", "surgeles"),
    ("eau gazeuse", "boissons"), ("vin rouge", "boissons"),
    ("papier toilette", "hygiene-maison"), ("liquide vaisselle", "hygiene-maison"),
    ("truc inconnu", "autre"),
])
def test_deviner_rayon(nom, rayon):
    assert deviner_rayon(nom) == rayon


def test_le_mot_le_plus_long_gagne():
    # « tomates pelées » est une conserve (épicerie), pas des tomates fraîches
    assert deviner_rayon("tomates pelées") == "epicerie" and deviner_rayon("tomates") == "fruits-legumes"


def test_valider_article_complet():
    a = valider_article({"id": ID, "nom": "  Lait ", "rayon": "frais", "pris": True, "recurrent": True,
                         "actif": True, "source": ""})
    assert a == {"id": ID, "nom": "Lait", "rayon": "frais", "pris": True, "recurrent": True, "actif": True,
                 "source": ""}


def test_valider_article_devine_le_rayon_et_complete():
    a = valider_article({"id": ID, "nom": "spaghetti"})
    assert a["rayon"] == "epicerie" and a["pris"] is False and a["recurrent"] is False and a["actif"] is True


@pytest.mark.parametrize("corps", [
    None, [], {"nom": "lait"}, {"id": "court", "nom": "lait"}, {"id": ID, "nom": ""}, {"id": ID, "nom": "x" * 81},
    {"id": ID, "nom": "lait", "rayon": "rayon-inconnu"}, {"id": ID, "nom": "lait", "pris": "oui"},
    {"id": ID, "nom": "lait", "source": "x" * 81},
])
def test_valider_article_refuse(corps):
    with pytest.raises(ValueError):
        valider_article(corps)


def test_valider_placard():
    assert valider_placard({"nom": " Paprika fumé ", "en_stock": False}) == {
        "cle": "paprika fume", "nom": "Paprika fumé", "en_stock": False, "bientot": False, "zone": "epices"}
    assert valider_placard({"nom": "Riz", "en_stock": True, "bientot": True, "zone": "cave"})["zone"] == "cave"
    for corps in (None, {"nom": "", "en_stock": True}, {"nom": "pâtes", "en_stock": "non"}, {"nom": "x" * 81, "en_stock": True},
                  {"nom": "riz", "en_stock": True, "zone": "grenier"}, {"nom": "riz", "en_stock": True, "bientot": "oui"}):
        with pytest.raises(ValueError):
            valider_placard(corps)


def test_zones_de_la_cuisine():
    assert [cle for cle, _ in ZONES] == ["frigo", "placard-sec", "epices", "congelateur", "cave"]


@pytest.mark.parametrize("nom, zone", [
    ("Cumin moulu", "epices"), ("Piment de Cayenne", "epices"), ("huile d'olive", "epices"), ("Vinaigre de Xérès", "epices"),
    ("sauce soja", "epices"), ("moutarde", "epices"), ("poivre en grains", "epices"), ("épices tacos", "epices"),
    ("Petits pois surgelés", "congelateur"), ("vin blanc", "cave"), ("pecorino", "frigo"), ("guanciale ou pancetta", "frigo"),
    ("spaghetti", "placard-sec"), ("tomates pelées", "placard-sec"), ("riz carnaroli", "placard-sec"), ("truc inconnu", "placard-sec"),
])
def test_deviner_zone(nom, zone):
    assert deviner_zone(nom) == zone


def test_deviner_zone_selon_le_rayon():
    assert deviner_zone("Gyoza", "surgeles") == "congelateur"
    assert deviner_zone("Kombucha", "boissons") == "cave"


@pytest.mark.parametrize("nom", ["cannelle", "Laurier", "thym", "vanille", "origan", "cassonade", "curcuma"])
def test_epices_au_rayon_epicerie(nom):
    assert deviner_rayon(nom) == "epicerie"


def test_rayon_epiceries_specialisees():
    assert "specialise" in dict(RAYONS) and RAYONS[-1][0] == "autre"


def test_placard_de_depart_sans_doublon():
    cles = [normaliser(nom) for nom in PLACARD_DEPART]
    assert len(cles) == len(set(cles)) and len(cles) >= 40
    for indispensable in ("oeufs", "spaghetti", "demi-baguettes", "guanciale ou pancetta", "pecorino"):
        assert indispensable in cles


def test_page_courses():
    html = courses_en_html()
    assert "<title>Courses · Casa Binomerie</title>" in html
    assert 'data-hub="courses" class="actif"' in html
    assert '<form id="ajout-course"' in html and 'id="vider-pris"' in html
    assert "SCRIPT_FILE" not in html and "function envoyerOuGarder" in html     # la file hors ligne commune
    assert '"frais"' in html                                                   # les rayons pour le script
    assert '"congelateur"' in html and '<form id="ajout-placard"' in html and 'id="ranger"' in html   # placard v2
    assert "bientot" in html and "api/placard/" in html


def test_un_envoi_a_la_fois():
    # « lait, œufs, pain » d'un coup : des envois en parallèle épuisaient les 4 connexions du serveur
    from courses import SCRIPT_COURSES
    assert SCRIPT_COURSES.count("envoyerOuGarder(") == 1 and "chaine.then" in SCRIPT_COURSES
