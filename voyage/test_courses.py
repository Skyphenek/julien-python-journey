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
    assert 'data-hub="cucina" class="actif"' in html and 'data-cucina="courses" class="actif"' in html and "<h1>Courses</h1>" not in html
    assert '<form id="ajout-course"' in html and 'id="vider-pris"' in html
    assert "SCRIPT_FILE" not in html and "function envoyerOuGarder" in html     # la file hors ligne commune
    assert '"frais"' in html                                                   # les rayons pour le script
    # À la maison remplace Placard et Habituels
    assert 'id="zone-maison"' in html and "À la maison" in html and 'id="chercher-maison"' in html
    assert 'id="modifier-maison"' in html and "api/placard/" in html
    for parti in ('id="zone-placard"', 'id="zone-habituels"', '<form id="ajout-placard"', 'id="ranger"',
                  'id="zones"', 'id="zones-catalogue"', "bientôt fini"):
        assert parti not in html
    from courses import SCRIPT_COURSES
    assert "function basculerPlacard" not in SCRIPT_COURSES and "aLaMaison(placard, articles)" in SCRIPT_COURSES
    assert "correspond(m.nom, recherche)" in SCRIPT_COURSES


def test_page_courses_liste_unique():
    html = courses_en_html()
    from courses import SCRIPT_COURSES
    assert 'id="magasins"' not in html and "courses:magasin" not in html             # plus d'onglets par magasin
    assert "Réassort" not in html and "estReassort" not in html and "Cette semaine" not in html
    assert "Dans le panier" in html and "Courses finies" in html and 'class="progression"' in html
    assert "pastille(a, ITALIEN)" in SCRIPT_COURSES and "span.pastille" in html
    assert "Toujours en avoir" in SCRIPT_COURSES and "Plus besoin d'en avoir" in SCRIPT_COURSES
    assert "'Plus habituel'" not in SCRIPT_COURSES
    assert '<script type="application/json" id="italien">' in html and '"pecorino"' in html


def test_un_envoi_a_la_fois():
    # « lait, œufs, pain » d'un coup : des envois en parallèle épuisaient les 4 connexions du serveur
    from courses import SCRIPT_COURSES
    assert SCRIPT_COURSES.count("envoyerOuGarder(") == 1 and "chaine.then" in SCRIPT_COURSES


def _node_relecture(code):
    """Exécute SCRIPT_RELECTURE puis code (qui fait console.log) ; rend la sortie JSON."""
    import json, shutil, subprocess
    if not shutil.which("node"):
        pytest.skip("node absent")
    from courses import SCRIPT_RELECTURE
    sortie = subprocess.run(["node", "-e", SCRIPT_RELECTURE + "\n" + code], capture_output=True, text=True, check=True).stdout
    return json.loads(sortie)


def test_js_relecture_n_ecrase_pas_les_coches_en_vol():
    # Trois coches d'affilée : une relecture partie avant la fin des envois rendait l'ancien état (décoché)
    r = _node_relecture("""
        const s = suiviEnvois(), vus = [];
        s.debut(); s.debut(); s.debut();                 // lait, œufs, pain envoyés l'un après l'autre
        vus.push(s.peutLire());                          // pendant les envois : on ne relit pas
        s.fin();
        vus.push(s.peutLire());
        s.fin(); s.fin();
        vus.push(s.peutLire());                          // tout est arrivé : on relit
        const j = s.jeton();
        vus.push(s.fraiche(j));                          // rien n'a bougé pendant la lecture
        s.debut();                                       // une coche pendant la lecture
        vus.push(s.fraiche(j));
        s.fin();
        vus.push(s.fraiche(j));                          // lue avant cette coche : toujours périmée
        vus.push(s.fraiche(s.jeton()));
        console.log(JSON.stringify(vus));""")
    assert r == [False, False, True, True, False, False, True]


def test_page_courses_relit_seulement_quand_tout_est_envoye():
    html = courses_en_html()
    assert html.index("function suiviEnvois") < html.index("const CLE_COPIE")
    from courses import SCRIPT_COURSES
    assert "suivi.peutLire()" in SCRIPT_COURSES and "suivi.fraiche(jeton)" in SCRIPT_COURSES


def _node_regles(code):
    """Exécute SCRIPT_REGLES_COURSES puis code (qui fait console.log) ; rend la sortie JSON."""
    import json, shutil, subprocess
    if not shutil.which("node"):
        pytest.skip("node absent")
    from courses import SCRIPT_REGLES_COURSES
    sortie = subprocess.run(["node", "-e", SCRIPT_REGLES_COURSES + "\n" + code], capture_output=True, text=True, check=True).stdout
    return json.loads(sortie)


def test_js_a_la_maison():
    import json
    placard = [{"cle": "parmesan", "nom": "parmesan", "en_stock": True, "bientot": False, "rayon": "frais"},
               {"cle": "riz basmati", "nom": "riz basmati", "en_stock": True, "bientot": True, "rayon": "epicerie"},
               {"cle": "thon", "nom": "thon", "en_stock": False, "bientot": False, "rayon": "epicerie"},
               {"cle": "oeufs", "nom": "œufs", "en_stock": True, "bientot": False, "rayon": "frais"},
               {"cle": "farine", "nom": "farine", "en_stock": True, "bientot": False, "rayon": "epicerie"}]
    articles = [{"id": "a1", "nom": "Œufs", "rayon": "frais", "recurrent": True, "actif": False, "pris": False},
                {"id": "a2", "nom": "lait", "rayon": "frais", "recurrent": True, "actif": False, "pris": False},
                {"id": "a3", "nom": "beurre", "rayon": "frais", "recurrent": True, "actif": True, "pris": False},
                {"id": "a4", "nom": "farine", "rayon": "epicerie", "recurrent": False, "actif": True, "pris": False},
                {"id": "a5", "nom": "citrons", "rayon": "fruits-legumes", "recurrent": True, "actif": True, "pris": True}]
    r = _node_regles(f"console.log(JSON.stringify(aLaMaison({json.dumps(placard)}, {json.dumps(articles)})"
                     ".map(function (m) {{ return [m.nom, m.rayon, !!m.placard, m.article ? m.article.id : null]; }})));")
    # thon épuisé, farine sur la liste, beurre sur la liste, citrons dans le panier : absents ; œufs une seule fois
    assert r == [["lait", "frais", False, "a2"], ["œufs", "frais", True, "a1"],
                 ["parmesan", "frais", True, None], ["riz basmati", "epicerie", True, None]]


def test_js_a_la_maison_sans_le_panier():
    import json
    placard = [{"cle": "citron", "nom": "citron", "en_stock": True, "bientot": False, "rayon": "fruits-legumes"},
               {"cle": "sel", "nom": "sel", "en_stock": True, "bientot": False, "rayon": "epicerie"}]
    articles = [{"id": "c1", "nom": "citron", "rayon": "fruits-legumes", "recurrent": False, "actif": True, "pris": True}]
    r = _node_regles(f"console.log(JSON.stringify(aLaMaison({json.dumps(placard)}, {json.dumps(articles)}).map(function (m) {{ return m.nom; }})));")
    assert r == ["sel"]                                       # coché dans le panier : pas de retour dans À la maison


def test_js_plus_a_la_maison():
    import json
    placard = [{"cle": "lardons", "nom": "lardons", "en_stock": False, "rayon": "frais"},
               {"cle": "tomates pelees", "nom": "tomates pelées", "en_stock": False, "rayon": "epicerie"},
               {"cle": "thon", "nom": "thon", "en_stock": False, "rayon": "epicerie"},
               {"cle": "pain", "nom": "pain", "en_stock": False, "rayon": "frais"},
               {"cle": "riz", "nom": "riz", "en_stock": True, "rayon": "epicerie"}]
    articles = [{"id": "a1", "nom": "Thon", "actif": True, "pris": False},
                {"id": "a2", "nom": "pain", "actif": True, "pris": True},
                {"id": "a3", "nom": "lardons", "actif": False, "pris": False}]
    r = _node_regles(f"console.log(JSON.stringify(plusALaMaison({json.dumps(placard)}, {json.dumps(articles)}).map(function (p) {{ return p.nom; }})));")
    assert r == ["lardons", "tomates pelées"]                 # thon sur la liste, pain au panier, riz en stock : absents


def test_page_courses_plus_a_la_maison():
    from courses import SCRIPT_COURSES, STYLE_COURSES
    assert "plusALaMaison(placard, articles)" in SCRIPT_COURSES and "Plus à la maison" in SCRIPT_COURSES
    assert "Un appui : il repart sur la liste." in SCRIPT_COURSES and "ajouter(p.nom, 'placard')" in SCRIPT_COURSES
    assert "button.epuise" in STYLE_COURSES


def test_page_courses_maison_ouverte_jamais_coincee():
    from courses import SCRIPT_COURSES
    assert "maisonOuverte && !" in SCRIPT_COURSES and "maisonOuverte = null;" in SCRIPT_COURSES
    assert "zone-maison').addEventListener('toggle'" in SCRIPT_COURSES


def test_js_correspond():
    r = _node_regles("console.log(JSON.stringify([correspond('parmesan', 'parm'), correspond(\"huile d'olive\", 'olive'),"
                     " correspond('Crème fraîche', 'creme'), correspond('parmesan', 'mesan'), correspond('thon', ''),"
                     " correspond('Œufs', 'oeu')]));")
    assert r == [True, True, True, False, True, True]


def test_js_pastille():
    r = _node_regles("const it = new Set(['pecorino'].map(cleCatalogue));"
                     "console.log(JSON.stringify([pastille({nom: 'pecorino', rayon: 'specialise'}, it),"
                     " pastille({nom: 'sauce soja', rayon: 'specialise'}, it), pastille({nom: 'lait', rayon: 'frais'}, it)]));")
    assert r == ["Italien", "Asie", None]


def test_js_normaliser_regles():
    assert _node_regles("console.log(JSON.stringify([normaliser('Crème  Fraîche'), cleCatalogue('tomates cerises')]));") \
        == ["creme fraiche", "tomate cerise"]
