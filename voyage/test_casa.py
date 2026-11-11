"""Tests du hub Casa Binomerie : la navigation et la page Aujourd'hui."""
import sys
import pytest
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


def test_barre_du_bas_a_quatre_entrees():
    from design import nav_hub
    nav = nav_hub("aujourdhui")
    assert [x.split('"')[0] for x in nav.split('data-hub="')[1:]] == ["aujourdhui", "popote", "sortir", "budget", "vadrouille"]
    assert '<a href="diners" data-hub="popote"' in nav
    for page in ("diners", "courses", "cave"):
        assert 'data-hub="popote" class="actif" aria-current="page"' in nav_hub(page)


def test_onglets_popote():
    from design import onglets_popote
    html = onglets_popote("courses")
    assert html.startswith('<nav class="popote" aria-label="Popote">')
    assert '<a href="diners" data-popote="diners">Dîners</a>' in html
    assert '<a href="courses" data-popote="courses" class="actif" aria-current="page">Courses</a>' in html
    assert '<a href="cave" data-popote="cave">Cave</a>' in html


def test_le_hub_commence_par_aujourd_hui_et_finit_par_la_vadrouille():
    assert [cle for cle, _, _ in HUB] == ["aujourdhui", "popote", "sortir", "budget", "vadrouille"]   # les modules s'ajoutent à leur livraison
    assert HUB[0][2] == "./" and HUB[-1][2] == "vadrouille"
    assert HUB[-1][1] == "Vadrouille"           # « En Vadrouille » débordait de la barre du bas sur iPhone


def test_nav_marque_l_entree_active():
    nav = nav_hub("vadrouille")
    assert '<nav class="hub">' in nav and nav.startswith('<button type="button" class="theme"')
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
    html = aujourdhui_en_html([], AUJOURD_HUI, plats_du_soir=[{"nom": "Carbonara", "minutes": 20, "genre": "plat"}])
    assert "<strong>Carbonara</strong><span>20 min" in html


def test_ce_soir_compose():
    plats = [{"nom": "Salade de chèvre", "minutes": 10, "genre": "entree"},
             {"nom": "Carbonara", "minutes": 20, "genre": "plat"},
             {"nom": "Tiramisu", "minutes": 30, "genre": "dessert"}]
    html = aujourdhui_en_html([], AUJOURD_HUI, plats_du_soir=plats)
    assert "<strong>Carbonara</strong>" in html and "avec Salade de chèvre, Tiramisu" in html


def test_hier_soir_tant_que_pas_renseigne():
    hier = {"jour": AUJOURD_HUI - timedelta(days=1), "moment": "diner", "plats": ["plat-carbonara"], "issue": None}
    html = aujourdhui_en_html([], AUJOURD_HUI, diner_hier=hier)
    assert "Hier soir ?" in html and 'data-issue="commande"' in html and "api/repas" in html
    assert ("&quot;jour&quot;: &quot;2026-10-27&quot;, &quot;moment&quot;: &quot;diner&quot;, "
            "&quot;plats&quot;: [&quot;plat-carbonara&quot;]") in html
    assert "Hier soir ?" not in aujourdhui_en_html([], AUJOURD_HUI, diner_hier={**hier, "issue": "fait"})


def test_compteur_deliveroo():
    html = aujourdhui_en_html([], AUJOURD_HUI, compte={"semaine": 2, "moyenne": 1.5, "renseignes": 9})
    assert '<div class="bloc-compteur trop">' in html and "2 commandes ces 7 jours" in html and "Moyenne 1,5" in html
    assert '<div class="bloc-compteur ok">' in aujourdhui_en_html([], AUJOURD_HUI, compte={"semaine": 1, "moyenne": 1, "renseignes": 3})
    assert "bloc-compteur" not in aujourdhui_en_html([], AUJOURD_HUI, compte={"semaine": 0, "moyenne": 0, "renseignes": 0}).split("<body")[1]


def test_bloc_a_acheter_aujourd_hui():
    # Seulement ce qu'il faut acheter pour les repas du jour (02/11/2026), plus le compte de toute la liste
    html = aujourdhui_en_html([], AUJOURD_HUI, a_acheter=["steaks hachés", "pains burger", "Tomates & co"])
    assert ('<a class="bloc-courses" href="courses"><strong>À acheter pour aujourd\'hui</strong>'
            '<span>steaks hachés · pains burger · Tomates &amp; co</span></a>') in html
    assert 'class="bloc-courses"' not in aujourdhui_en_html([], AUJOURD_HUI).split("<body")[1]   # rien à acheter : rien


def test_ligne_budget_sur_aujourd_hui():
    semaine = {"total": 81.6, "livraison": 35, "courses": 46.6}
    html = aujourdhui_en_html([], AUJOURD_HUI, semaine_budget=semaine)
    assert ('<a class="bloc-budget" href="budget"><strong>Cette semaine : 82 €</strong>'
            '<span>dont livraison et resto 35 €</span></a>') in html
    vide = aujourdhui_en_html([], AUJOURD_HUI, semaine_budget={"total": 0, "livraison": 0, "courses": 0})
    assert 'class="bloc-budget"' not in vide.split("<body")[1]


# --- À finir ---
from casa import bloc_a_finir


def alerte(nom, jusqu_au, etat="a-finir", trop_tard=None, suggestions=(), jour=None):
    from courses import normaliser
    return {"cle": normaliser(nom), "nom": nom, "origine": "placard", "jusqu_au": jusqu_au, "etat": etat,
            "trop_tard": trop_tard, "suggestions": list(suggestions), "jour": jour}


def test_bloc_a_finir_vide():
    assert bloc_a_finir([], AUJOURD_HUI) == ""


def test_bloc_a_finir():
    demain = AUJOURD_HUI + timedelta(days=1)
    salade = {"id": "plat-salade-01", "nom": "Salade César"}
    html = bloc_a_finir([alerte("steaks hachés", AUJOURD_HUI - timedelta(days=1), etat="a-verifier"),
                         alerte("cuisses de poulet", demain, trop_tard=AUJOURD_HUI + timedelta(days=2),
                                suggestions=[{"plat": salade, "manquants": ["crème"]}], jour=AUJOURD_HUI),
                         alerte("salade", AUJOURD_HUI + timedelta(days=2), suggestions=[{"plat": salade, "manquants": []}])],
                        AUJOURD_HUI)
    assert "À finir" in html and "steaks hachés" in html and "à vérifier" in html
    assert 'data-cle="steaks haches"' in html and 'data-action="encore-bon"' in html
    assert "à finir demain" in html and "prévu vendredi, trop tard" in html          # 28/10/2026 : un mercredi
    assert "Salade César" in html and "il manque : crème" in html
    assert f'data-plat="plat-salade-01" data-jour="{AUJOURD_HUI.isoformat()}">Ce soir</button>' in html
    assert "d'ici vendredi" in html and "rien de prévu" in html and "soirs pris jusqu'à vendredi" in html
    assert html.count('data-action="fini"') == 3 and html.count('data-action="encore-bon"') == 1


def test_page_aujourd_hui_avec_a_finir():
    html = aujourdhui_en_html([], AUJOURD_HUI, a_finir=[alerte("salade", AUJOURD_HUI)])
    assert '<div class="bloc-a-finir">' in html and "api/a-finir/" in html
    assert "si_libre: true" in html and "Ce soir-là est déjà pris : recharge la page." in html
    assert '<div class="bloc-a-finir">' not in aujourdhui_en_html([], AUJOURD_HUI)   # le CSS, lui, contient toujours le nom


from casa import bloc_vin


def vin(id_, nom, fin=2028, millesime=2019, region="", pays="France"):
    return {"id": id_, "nom": nom, "millesime": millesime, "fin": fin, "region": region, "pays": pays}


def test_bloc_vin_vide():
    assert bloc_vin([], None) == ""


def test_bloc_vin():
    html = bloc_vin([vin("vin-a", "Saint-Joseph"), vin("vin-b", "Saint-Amour", millesime=None)], None)
    assert html.startswith('<div class="bloc-vin">') and "À ouvrir" in html
    assert '<li data-id="vin-a">' in html and '<li data-id="vin-b" hidden>' in html
    assert "Saint-Joseph 2019" in html and "à boire avant 2028" in html
    assert 'data-action="ouverte"' in html and 'data-action="autre"' in html
    assert "belle bouteille" not in html


def test_bloc_vin_une_seule_et_une_belle():
    html = bloc_vin([vin("vin-a", "Saint-Joseph")], vin("vin-c", "Clos des Fées", fin=2035, millesime=2020))
    assert 'data-action="autre"' not in html
    assert '<li data-id="vin-c" class="belle" hidden>' in html and "Une belle bouteille ?" in html


def test_bloc_vin_seulement_une_belle():
    html = bloc_vin([], vin("vin-c", "Clos des Fées"))
    assert "Une belle bouteille ?" in html and 'data-action="ouverte"' in html


def test_bloc_vin_styles_tactiles_et_hidden():
    from casa import STYLE_CASA
    assert "div.bloc-vin [hidden], div.bloc-vin button.lien[hidden] { display: none; }" in STYLE_CASA   # .lien impose un display plus spécifique
    assert "div.bloc-vin p.message:empty { display: none; }" in STYLE_CASA
    assert "div.bloc-vin button { min-height: 40px" in STYLE_CASA
    assert "div.bloc-vin button.lien:focus-visible" in STYLE_CASA


def test_page_aujourd_hui_avec_vin():
    html = aujourdhui_en_html([], AUJOURD_HUI, vins=[vin("vin-a", "Saint-Joseph")])
    assert html.index('class="bloc-ce-soir') < html.index('<div class="bloc-vin">')
    assert "<script>" in html and "api/cave/" in html


def test_script_vin_syntaxe_js(tmp_path):
    """Le script du vin du soir est du JavaScript valide (node --check), sinon test ignoré."""
    import shutil
    import subprocess
    from casa import SCRIPT_VIN
    node = shutil.which("node")
    if node is None:
        pytest.skip("node absent")
    html = aujourdhui_en_html([], AUJOURD_HUI, vins=[vin("vin-a", "Saint-Joseph")])
    assert SCRIPT_VIN in html
    fichier = tmp_path / "vin.js"
    fichier.write_text(SCRIPT_VIN, encoding="utf-8")
    r = subprocess.run([node, "--check", str(fichier)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr


def test_six_onglets_tiennent_sur_iphone():
    from design import STYLE_NAV_HUB
    # base « auto » : un onglet au libellé long (« Aujourd'hui », 61 px) prend sa place au lieu de déborder sur le voisin
    assert "nav.hub a { flex: 1 1 auto; min-width: 0;" in STYLE_NAV_HUB


def test_bloc_vin_indique_la_region_et_le_pays_etranger():
    html = bloc_vin([vin("vin-a", "Esprit de Granit", region="Rhône Nord"),
                     vin("vin-b", "Chianti", region="Toscane", pays="Italie"), vin("vin-c", "Plan Cuvé")], None)
    assert "<span>Rhône Nord · à boire avant 2028</span>" in html
    assert "<span>Toscane, Italie · à boire avant 2028</span>" in html
    assert "<span>à boire avant 2028</span>" in html                     # sans région : rien de plus
