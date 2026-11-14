"""Tests de diners.py : carnet, semaine, secours, ingrédients à acheter, compteur Deliveroo (logique pure)."""
import sys
from datetime import date, timedelta
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pytest
from diners import (valider_plat, repas_prevus, secours, a_acheter, compteur, semaine, diners_en_html, disponibles,
                    SECOURS_MINUTES)
from carnet_depart import CARNET_DEPART, A_TESTER
from courses import PLACARD_DEPART, normaliser

AUJ = date(2026, 10, 28)


def plat(id_, nom, minutes=15, ingredients=(), genre="plat", statut="carnet", archive=False):
    return {"id": id_, "nom": nom, "genre": genre, "minutes": minutes, "ingredients": list(ingredients),
            "recette": "", "lien": "", "note": "", "statut": statut, "archive": archive}


def placard(*en_stock, epuises=(), bientot=()):
    return ([{"cle": normaliser(n), "nom": n, "en_stock": True, "bientot": False} for n in en_stock]
            + [{"cle": normaliser(n), "nom": n, "en_stock": True, "bientot": True} for n in bientot]
            + [{"cle": normaliser(n), "nom": n, "en_stock": False, "bientot": False} for n in epuises])


def habituel(nom, actif=False, pris=False):
    return {"nom": nom, "actif": actif, "pris": pris, "recurrent": True}


def diner(jour, *plats, issue=None, moment="diner"):
    return {"jour": jour, "moment": moment, "plats": list(plats), "issue": issue}


# --- Validation ---

def test_valider_plat_complet():
    p = valider_plat({"id": "plat-test-01", "nom": " Carbonara ", "genre": "plat", "minutes": 20,
                      "ingredients": [" Œufs ", "pecorino", "", "œufs"], "recette": "1. Cuire.",
                      "lien": "https://ricette.giallozafferano.it/x.html", "note": "", "statut": "carnet"})
    assert p["nom"] == "Carbonara" and p["ingredients"] == ["Œufs", "pecorino"]     # vides et doublons retirés
    assert p["archive"] is False and p["minutes"] == 20


@pytest.mark.parametrize("modif", [
    {"id": "court"}, {"nom": ""}, {"genre": "apero"}, {"minutes": 0}, {"minutes": 601}, {"minutes": "20"},
    {"minutes": True}, {"ingredients": "œufs"}, {"ingredients": ["x" * 61]}, {"ingredients": ["a"] * 41},
    {"lien": "javascript:alert(1)"}, {"lien": "ftp://x"}, {"statut": "poubelle"}, {"recette": "x" * 20001},
])
def test_valider_plat_refuse(modif):
    corps = {"id": "plat-test-01", "nom": "Carbonara", "genre": "plat", "minutes": 20, "ingredients": [],
             "recette": "", "lien": "", "note": "", "statut": "carnet", **modif}
    with pytest.raises(ValueError):
        valider_plat(corps)


# --- Semaine, secours, courses ---

def test_semaine_glissante():
    assert semaine(AUJ) == [AUJ + timedelta(days=i) for i in range(7)]


def test_secours_faisables_et_presque():
    plats = [plat("plat-carbonara", "Carbonara", 20, ["spaghetti", "œufs", "pecorino"]),
             plat("plat-baguezza1", "Baguezza", 15, ["demi-baguettes", "passata", "mozzarella"]),
             plat("plat-lent-0001", "Lasagne", 300, ["oeufs"]),
             plat("plat-archive01", "Vieux", 10, [], archive=True),
             plat("plat-atester01", "Shakshuka", 15, [], statut="a-tester"),
             plat("dessert-00001", "Mousse", 10, ["œufs"], genre="dessert")]
    p = placard("spaghetti", "Oeufs", "pecorino", "demi-baguettes", epuises=("passata",))
    faisables, presque = secours(plats, p)
    assert [x["nom"] for x in faisables] == ["Carbonara"]
    assert presque == [{"plat": plats[1], "manquants": ["passata", "mozzarella"]}]
    assert SECOURS_MINUTES == 20


def test_disponibles_placard_et_habituels_ranges():
    p = placard("spaghetti", bientot=("pecorino",), epuises=("guanciale",))
    courses = [habituel("Œufs"),                                   # rangé : on en a
               habituel("Lait", actif=True),                       # sur la liste : il en manque
               habituel("Beurre", actif=True, pris=True),          # dans le panier : on en a
               {"nom": "Riz", "actif": True, "pris": False, "recurrent": False}]
    assert disponibles(p, courses) == {"spaghetti", "pecorino", "oeufs", "beurre"}


def test_secours_avec_les_frais_en_habituels():
    carbo = plat("plat-carbonara", "Carbonara", 20, ["spaghetti", "œufs", "pecorino"])
    p = placard("spaghetti", "pecorino")
    assert secours([carbo], p, [habituel("œufs")])[0] == [carbo]
    assert secours([carbo], p, [habituel("œufs", actif=True)])[0] == []


def test_secours_sur_le_carnet_de_depart():
    # Le placard plein du 31/10 rend 7 dîners de secours possibles
    faisables, _ = secours([dict(p, statut="carnet", archive=False) for p in CARNET_DEPART],
                           placard(*PLACARD_DEPART))
    assert len(faisables) == 7


def test_a_acheter_sans_doublon_ni_stock():
    plats = [plat("plat-carbonara", "Carbonara", 20, ["spaghetti", "œufs", "pecorino", "guanciale"]),
             plat("plat-amatricia", "Amatriciana", 35, ["spaghetti", "guanciale", "Tomates pelées"])]
    courses = [{"nom": "Guanciale", "actif": True, "pris": False, "recurrent": False},   # déjà sur la liste
               {"nom": "pecorino", "actif": True, "pris": True, "recurrent": False}]    # pris : n'empêche pas
    p = placard("spaghetti", epuises=("œufs",))
    assert a_acheter(plats, p, courses) == [("œufs", "plat-carbonara"), ("pecorino", "plat-carbonara"),
                                            ("Tomates pelées", "plat-amatricia")]


# --- Compteur Deliveroo ---

def test_compteur():
    repas = [diner(AUJ - timedelta(days=d), issue="commande") for d in (1, 3, 10, 20, 41, 42)]
    repas += [diner(AUJ - timedelta(days=2), issue="fait"),
              diner(AUJ - timedelta(days=1), issue="commande", moment="dejeuner")]     # le déjeuner ne compte pas
    c = compteur(repas, AUJ)
    assert c["semaine"] == 2                     # J-1 et J-3 (7 derniers jours, aujourd'hui compris)
    assert c["moyenne"] == pytest.approx(5 / 6)  # J-42 hors des 6 semaines
    assert c["renseignes"] == 6                 # sur les 6 semaines


def test_compteur_vide():
    assert compteur([], AUJ) == {"semaine": 0, "moyenne": 0, "renseignes": 0}


# --- Carnet de départ et page ---

def test_carnet_de_depart_valide():
    for p in CARNET_DEPART + A_TESTER:
        valider_plat({**p, "statut": "carnet"})


def test_page_diners():
    html = diners_en_html()
    assert "<title>Dîners · Casa Binomerie</title>" in html and 'data-page="diners"' in html
    assert 'data-hub="cucina" class="actif"' in html and 'data-cucina="diners" class="actif"' in html and "<h1>Dîners</h1>" not in html
    assert 'data-vue="ce-soir"' in html and 'data-vue="semaine"' in html and 'data-vue="recettes"' not in html
    assert 'data-vue="carnet"' not in html and 'data-vue="a-tester"' not in html
    assert "function vueRecettes" in html and "function ordreRecettes" in html
    assert "nav.vues { display: grid; grid-template-columns: repeat(2, 1fr)" in html            # 2 onglets, sans trou
    assert "div.filtres.etiquettes { flex-wrap: nowrap; overflow-x: auto;" in html            # étiquettes sur une ligne
    assert "el('div', 'segments')" in html and "'Accomp.'" in html and "if (e[0] === 'tout') return;" in html
    assert "function vueCarnet" not in html and "function vueATester" not in html
    assert "'nouvelles'" in html and "'Nouvelles'" in html


def test_page_recettes():
    html = diners_en_html("recettes")
    assert "<title>Recettes · Casa Binomerie</title>" in html and 'data-page="recettes"' in html
    assert 'data-hub="cucina" class="actif"' in html and 'data-cucina="recettes" class="actif"' in html
    assert '<nav class="vues"' not in html                       # pas d'onglets internes
    assert "function vueRecettes" in html


def test_anciens_liens_vers_recettes_et_allers_retours():
    from diners import SCRIPT_DINERS
    assert "location.replace('recettes')" in SCRIPT_DINERS       # diners#recettes, #carnet, #a-tester
    assert "function allerA(" in SCRIPT_DINERS and "location.href = 'diners#' + v" in SCRIPT_DINERS
    assert "vue = 'ce-soir'; afficher()" not in SCRIPT_DINERS     # tout passe par allerA


def test_fiche_et_actions_de_la_page():
    html = diners_en_html()
    assert "function icone" in html and "function points" in html and "aria-label" in html
    assert '<template id="reperes">' in html and "setAttribute('role', 'img')" in html
    for signe in ("✦", "⚡", "⏳"):
        assert signe not in html, signe
    for signe in ("'Ⓙ'", "'Ⓛ'", "'●'", "'○'"):
        assert signe in html, signe
    for cle in ("nouvelle", "eclair", "sablier"):
        assert f'data-icone="{cle}"' in html
    assert "faite souvent" in html and "'faisable ce soir'" in html and "'finit un produit'" in html
    assert "el('span', 'badge', 'secours')" not in html and "badge julien" not in html
    assert "On l\\'a déjà faite" in html and "'Archiver'" in html and "'Désarchiver'" in html
    assert "au carnet" not in html and "Retirer du carnet" not in html
    assert "'recette à écrire'" in html
    assert "function envoyerOuGarder" in html and "wakeLock" in html
    assert "api/diners/proposer" in html and "Proposer ma semaine" in html and "Reproposer" in html   # A
    assert "function ouvrirChoix" in html and "function barreEtiquettes" in html                       # B
    for e in ("rapide", "nous", "julien", "air-fryer", "poisson", "legumes"):
        assert f"'{e}'" in html
    assert "pour: pour.value" in html                                                                   # D
    assert '<script type="application/json" id="prix">' in html and "function compteurDiners" in html     # C
    assert "Déjà sur la liste" in html and "À acheter" in html and "manquants aux courses" in html      # E
    assert "Au hasard parmi" in html and "'laetitia'" in html and "Laetitia seule" in html
    assert "api/repas" in html and "api/soirs" not in html and "d.soirs" not in html                  # repas composés
    for f in ("function ajouterPlat", "function retirerPlat", "function ranges", "function carteRepas"):
        assert f in html
    for marqueur in ("function uneFiche", "function bandeauCourses", "function ingredientsFiche",     # fiche magazine
                     "function tempoFiche", "function etapesFiche", "function phraseFiche",
                     "div.une-fiche", "details.courses-fiche", "ol.etapes-fiche", "div.tempo-fiche"):
        assert marqueur in html, marqueur
    assert "innerHTML" not in html.split("function phraseFiche")[1].split("function ouvrirAccords")[0]
    assert "+ déjeuner ou brunch" in html and "+ accompagnement" in html and "'brunch'" in html
    assert "'au menu'" in html and "déjà 8 plats" in html                                              # feuille de choix
    assert "function accordsDe" in html and "function ouvrirAccords" in html                          # accords
    assert "Va bien avec" in html and "Modifier les accords" in html and "'Avec :'" in html
    assert "if (absents.length && !accompagne && r.plats.length < 8)" in html     # déjà un accompagnement : rien
    assert "['brunch', 'Brunch']" in html and "brunch-" in html and "'+ ajouter'" in html            # brunch
    assert "r.menus" in html and "plats.join(' ') === derniereProposition[cle]" in html            # étape 3


def test_version_page_repas():
    from valise import VERSION_PAGE
    assert VERSION_PAGE >= 37


def test_version_page_accords():
    from valise import VERSION_PAGE
    assert VERSION_PAGE >= 38


def test_version_page_proposer():
    from valise import VERSION_PAGE
    assert VERSION_PAGE >= 39


def test_version_page_avec_masque():
    from valise import VERSION_PAGE
    assert VERSION_PAGE >= 40


# --- Pour qui (nous deux ou Julien) ---

def test_valider_plat_pour():
    corps = {"id": "plat-test-01", "nom": "Sardines", "genre": "plat", "minutes": 20}
    assert valider_plat(corps)["pour"] == "nous"
    assert valider_plat({**corps, "pour": "julien"})["pour"] == "julien"
    with pytest.raises(ValueError):
        valider_plat({**corps, "pour": "eux"})


# --- Proposer ma semaine ---
from random import Random
from diners import proposer

LUN = date(2026, 11, 2)                       # un lundi : la semaine va du lundi au dimanche
SEMAINE = semaine(LUN)


def carte(n=12, a_tester=3):
    """Un carnet de n plats rapides et quelques plats à tester, tous avec recette."""
    plats = [{**plat(f"plat-carnet-{i:02d}", f"Carnet {i}", minutes=30), "recette": "1.", "pour": "nous"} for i in range(n)]
    plats += [{**plat(f"plat-tester-{i:02d}", f"Tester {i}", minutes=40, statut="a-tester"), "recette": "1.", "pour": "nous"}
              for i in range(a_tester)]
    return plats


def test_proposer_quatre_soirs_varies():
    plats = carte() + [{**plat("plat-julien-01", "Sardines", minutes=20), "recette": "1.", "pour": "julien"},
                       {**plat("plat-archive-1", "Vieux", minutes=20, archive=True), "recette": "1.", "pour": "nous"},
                       {**plat("plat-sans-rec", "À écrire", minutes=20), "recette": "", "pour": "nous"},
                       {**plat("plat-dessert-1", "Mousse", genre="dessert"), "recette": "1.", "pour": "nous"}]
    p = proposer(plats, [], SEMAINE, LUN, hasard=Random(1))
    assert len(p) == 4 and len(set(p.values())) == 4
    assert not {j.weekday() for j in p} & {4, 5}                      # ni vendredi ni samedi : souvent dehors
    trois = proposer(plats, [diner(LUN + timedelta(days=6), "plat-carnet-00")], SEMAINE, LUN,
                     hasard=Random(1))
    assert [j.weekday() for j in trois] == [0, 2, 3]                     # répartis : lundi, mercredi, jeudi
    assert not set(p.values()) & {"plat-julien-01", "plat-archive-1", "plat-sans-rec", "plat-dessert-1"}
    assert sum(v.startswith("plat-tester") for v in p.values()) == 1    # un plat à tester par semaine


def test_proposer_complete_ce_qui_est_prevu():
    plats = carte()
    soirs = [diner(LUN + timedelta(days=1), "plat-carnet-00"), diner(LUN, issue="dehors")]
    p = proposer(plats, soirs, SEMAINE, LUN, hasard=Random(2))
    assert len(p) == 3 and LUN not in p and LUN + timedelta(days=1) not in p
    assert "plat-carnet-00" not in p.values()


def test_proposer_rapide_en_semaine():
    plats = carte(n=6) + [{**plat(f"plat-long-{i:04d}", f"Long {i}", minutes=120), "recette": "1.", "pour": "nous"}
                          for i in range(6)]
    for graine in range(20):
        for jour, id_ in proposer(plats, [], SEMAINE, LUN, hasard=Random(graine)).items():
            if id_.startswith("plat-long"):
                assert jour.weekday() == 6                               # le dimanche seulement


def test_proposer_sans_ce_qu_on_a_mange_recemment():
    plats = carte(n=5, a_tester=0)
    soirs = [diner(LUN - timedelta(days=3), "plat-carnet-00", issue="fait")]
    for graine in range(10):
        assert "plat-carnet-00" not in proposer(plats, soirs, SEMAINE, LUN, hasard=Random(graine)).values()


def test_proposer_remplacer_un_soir():
    plats = carte()
    p = proposer(plats, [], SEMAINE, LUN, hasard=Random(3))
    jour, avant = sorted(p.items())[0]
    soirs = [diner(j, v) for j, v in p.items()]
    q = proposer(plats, soirs, SEMAINE, LUN, remplacer=[jour], hasard=Random(4))
    assert list(q) == [jour] and q[jour] != avant and q[jour] not in p.values()


def test_proposer_remplacer_ignore_un_diner_compose_ou_deja_vecu():
    plats = carte()
    mar = LUN + timedelta(days=1)
    soirs = [diner(LUN, "plat-carnet-00", "plat-carnet-01"), diner(mar, "plat-carnet-02", issue="fait")]
    q = proposer(plats, soirs, SEMAINE, LUN, remplacer=[LUN, mar], hasard=Random(7))
    assert LUN not in q and mar not in q                           # composé / déjà vécu : intouchables


def test_proposer_rien_si_deja_quatre():
    soirs = [diner(LUN + timedelta(days=i), f"plat-carnet-{i:02d}") for i in range(4)]
    assert proposer(carte(), soirs, SEMAINE, LUN, hasard=Random(5)) == {}


def test_proposer_ignore_dejeuner_et_brunch():
    repas = [diner(LUN + timedelta(days=i), f"plat-carnet-{i:02d}", moment="brunch") for i in range(4)]
    p = proposer(carte(), repas, SEMAINE, LUN, hasard=Random(6))
    assert len(p) == 4                                              # un brunch ne remplit pas le soir


def test_proposer_un_diner_compose_compte_comme_prevu():
    repas = [diner(LUN + timedelta(days=i), f"plat-carnet-{i:02d}", f"plat-carnet-{i + 6:02d}") for i in range(4)]
    assert proposer(carte(), repas, SEMAINE, LUN, hasard=Random(7)) == {}


# --- proposer_cases : les cases cochées, midi et soir ---
from diners import proposer_cases, MINUTES_MIDI

MAR, SAM, DIM = LUN + timedelta(days=1), LUN + timedelta(days=5), LUN + timedelta(days=6)


def test_proposer_cases_remplit_exactement_les_cases_cochees():
    cases = [(j, "diner") for j in SEMAINE] + [(SAM, "dejeuner"), (DIM, "dejeuner")]
    p = proposer_cases(carte(n=20), [], cases, LUN, hasard=Random(1))
    assert sorted(p) == sorted(cases) and len(set(p.values())) == 9          # 9 repas, aucun doublon


def test_proposer_cases_midi_rapide_et_soir_comme_avant():
    plats = carte(n=4, a_tester=0) + [{**plat(f"plat-moyen-{i}", f"Moyen {i}", minutes=40), "recette": "1.",
                                       "pour": "nous"} for i in range(4)]
    for graine in range(15):
        p = proposer_cases(plats, [], [(LUN, "dejeuner"), (MAR, "dejeuner"), (LUN, "diner")], LUN,
                           hasard=Random(graine))
        assert all(not p[(j, "dejeuner")].startswith("plat-moyen") for j in (LUN, MAR))   # 40 min > 30 à midi
    assert MINUTES_MIDI == 30


def test_proposer_cases_ne_touche_pas_ce_qui_est_pose():
    repas = [diner(LUN, "plat-carnet-00"), diner(MAR, issue="dehors"),
             diner(SAM, "plat-carnet-01", moment="brunch")]
    p = proposer_cases(carte(), repas, [(LUN, "diner"), (MAR, "diner"), (SAM, "dejeuner"), (DIM, "diner")], LUN,
                       hasard=Random(2))
    assert list(p) == [(DIM, "diner")] and p[(DIM, "diner")] not in {"plat-carnet-00", "plat-carnet-01"}


def test_proposer_cases_jours_passes_ignores():
    assert proposer_cases(carte(), [], [(LUN, "diner")], MAR, hasard=Random(3)) == {}


def test_proposer_cases_remplacer_un_dejeuner():
    plats = carte()
    p = proposer_cases(plats, [], [(SAM, "dejeuner")], LUN, hasard=Random(4))
    avant = p[(SAM, "dejeuner")]
    q = proposer_cases(plats, [diner(SAM, avant, moment="dejeuner")], [], LUN,
                       remplacer=[(SAM, "dejeuner")], hasard=Random(5))
    assert list(q) == [(SAM, "dejeuner")] and q[(SAM, "dejeuner")] != avant


def test_proposer_cases_un_seul_plat_a_tester():
    cases = [(j, m) for j in SEMAINE for m in ("dejeuner", "diner")]
    p = proposer_cases(carte(n=20, a_tester=5), [], cases, LUN, hasard=Random(6))
    assert sum(v.startswith("plat-tester") for v in p.values()) <= 1


def test_proposer_cases_anti_gaspi_a_midi():
    plats = carte(n=6, a_tester=0) + [{**plat("plat-epinards", "Épinards", minutes=20, ingredients=["épinards frais"]),
                                       "recette": "1.", "pour": "nous"}]
    p = proposer_cases(plats, [], [(LUN, "dejeuner"), (LUN, "diner"), (MAR, "diner")], LUN,
                       a_finir=[("epinards frais", MAR)], hasard=Random(7))
    assert p[(LUN, "dejeuner")] == "plat-epinards"


# fenêtre glissante : aujourd'hui + 6 jours, pas la semaine du calendrier
JEU = date(2026, 11, 5)
LUN_PROCHAIN, LUN_DERNIER = JEU + timedelta(days=4), JEU - timedelta(days=3)


def test_proposer_cases_plat_pose_lundi_prochain_jamais_propose_jeudi():
    for graine in range(20):
        p = proposer_cases(carte(n=3, a_tester=0), [diner(LUN_PROCHAIN, "plat-carnet-00")], [(JEU, "diner")], JEU,
                           hasard=Random(graine))
        assert p[(JEU, "diner")] != "plat-carnet-00"


def test_proposer_cases_plat_du_lundi_dernier_ne_bloque_pas_jeudi():
    repas = [diner(LUN_DERNIER, "plat-carnet-00"), diner(JEU + timedelta(days=1), "plat-carnet-01"),
             diner(JEU + timedelta(days=2), "plat-carnet-02")]
    for graine in range(10):
        p = proposer_cases(carte(n=3, a_tester=0), repas, [(JEU, "diner")], JEU, hasard=Random(graine))
        assert p == {(JEU, "diner"): "plat-carnet-00"}


def test_proposer_cases_un_seul_a_tester_sur_la_fenetre_glissante():
    cases = [(JEU + timedelta(days=i), m) for i in range(7) for m in ("dejeuner", "diner")]
    cases = [c for c in cases if c != (LUN_PROCHAIN, "diner")]
    repas = [diner(LUN_PROCHAIN, "plat-tester-00")]
    for graine in range(10):
        p = proposer_cases(carte(n=20, a_tester=5), repas, cases, JEU, hasard=Random(graine))
        assert not any(v.startswith("plat-tester") for v in p.values())


# --- Proposer avec un accompagnement (étape 3) ---
from diners import accompagner


def avec_accords(plats, accords):
    """Le carnet `plats`, ses accords ({id de plat: [ids]}) et les accompagnements qu'ils citent."""
    accs = sorted({a for ids in accords.values() for a in ids})
    return ([{**p, "accords": accords.get(p["id"], [])} for p in plats]
            + [{**plat(a, a, genre="accompagnement"), "recette": "1.", "pour": "nous"} for a in accs])


def test_accompagner_un_accord_du_plat():
    plats = avec_accords(carte(), {"plat-carnet-00": ["acc-puree-0", "acc-salade-0"]})
    mer = LUN + timedelta(days=2)
    m = accompagner({LUN: "plat-carnet-00", mer: "plat-carnet-01"}, plats, [], SEMAINE, hasard=Random(1))
    assert m[LUN][0] == "plat-carnet-00" and len(m[LUN]) == 2 and m[LUN][1] in ("acc-puree-0", "acc-salade-0")
    assert m[mer] == ["plat-carnet-01"]                                   # sans accord : le plat seul


def test_accompagner_pas_deux_fois_dans_la_semaine():
    plats = avec_accords(carte(), {"plat-carnet-00": ["acc-puree-0", "acc-salade-0"],
                                   "plat-carnet-01": ["acc-puree-0", "acc-salade-0"]})
    mer, sam = LUN + timedelta(days=2), LUN + timedelta(days=5)
    deja = [diner(sam, "plat-carnet-05", "acc-salade-0")]                 # la salade est déjà au menu samedi
    for graine in range(10):
        m = accompagner({LUN: "plat-carnet-00", mer: "plat-carnet-01"}, plats, deja, SEMAINE, hasard=Random(graine))
        assert m == {LUN: ["plat-carnet-00", "acc-puree-0"], mer: ["plat-carnet-01"]}


def test_accompagner_ni_archive_ni_pour_un_seul_ni_inconnu():
    plats = avec_accords(carte(), {"plat-carnet-00": ["acc-vieux-0", "acc-coleslaw", "acc-absent"]})
    plats = [{**p, "archive": True} if p["id"] == "acc-vieux-0"
             else {**p, "pour": "laetitia"} if p["id"] == "acc-coleslaw" else p
             for p in plats if p["id"] != "acc-absent"]
    assert accompagner({LUN: "plat-carnet-00"}, plats, [], SEMAINE, hasard=Random(1)) == {LUN: ["plat-carnet-00"]}


def test_accompagner_reproposer_libere_l_ancien_accompagnement():
    plats = avec_accords(carte(), {"plat-carnet-01": ["acc-puree-0"]})
    ancien = [diner(LUN, "plat-carnet-00", "acc-puree-0")]                # le dîner qu'on repropose
    m = accompagner({LUN: "plat-carnet-01"}, plats, ancien, SEMAINE, hasard=Random(1))
    assert m == {LUN: ["plat-carnet-01", "acc-puree-0"]}


def test_accompagner_garde_l_accompagnement_d_un_soir_qu_on_ne_repropose_pas():
    plats = avec_accords(carte(), {"plat-carnet-00": ["acc-puree-0"], "plat-carnet-01": ["acc-puree-0"]})
    mar = LUN + timedelta(days=1)
    compose = [diner(mar, "plat-carnet-01", "acc-puree-0")]               # composé à la main : Reproposer le laisse
    for graine in range(10):
        m = accompagner({LUN: "plat-carnet-00"}, plats, compose, SEMAINE, hasard=Random(graine))
        assert m == {LUN: ["plat-carnet-00"]}


def test_accompagner_pas_le_soir_ce_qui_est_au_brunch_du_jour():
    plats = avec_accords(carte(), {"plat-carnet-00": ["acc-salade-0"]})
    dim = LUN + timedelta(days=6)
    brunch = [diner(dim, "plat-carnet-05", "acc-salade-0", moment="brunch")]
    assert accompagner({dim: "plat-carnet-00"}, plats, brunch, SEMAINE, hasard=Random(1)) == {dim: ["plat-carnet-00"]}


def test_accompagner_rapide_en_semaine_et_avec_recette():
    plats = avec_accords(carte(), {"plat-carnet-00": ["acc-gratin-0", "acc-vide-00"]})
    plats = [{**p, "minutes": 90} if p["id"] == "acc-gratin-0" else {**p, "recette": ""} if p["id"] == "acc-vide-00" else p
             for p in plats]
    dim = LUN + timedelta(days=6)
    assert accompagner({LUN: "plat-carnet-00"}, plats, [], SEMAINE, hasard=Random(1)) == {LUN: ["plat-carnet-00"]}
    assert accompagner({dim: "plat-carnet-00"}, plats, [], SEMAINE, hasard=Random(1)) == {dim: ["plat-carnet-00", "acc-gratin-0"]}

def test_proposer_remplace_un_diner_tel_que_propose():
    plats = avec_accords(carte(), {"plat-carnet-00": ["acc-puree-0"]})
    mar = LUN + timedelta(days=1)
    soirs = [diner(LUN, "plat-carnet-00", "acc-puree-0"),                 # un plat et son accord : tel que proposé
             diner(mar, "plat-carnet-01", "acc-puree-0")]                 # un accompagnement choisi à la main
    q = proposer(plats, soirs, SEMAINE, LUN, remplacer=[LUN, mar], hasard=Random(8))
    assert LUN in q and mar not in q


# --- Coût de la semaine ---
from diners import cout_semaine, LIVRAISON_DEUX
from prix_paris import prix_de


def test_cout_semaine():
    carbo = plat("plat-carbonara", "Carbonara", ingredients=["spaghetti", "œufs", "pecorino"])
    saumon = plat("plat-saumon-01", "Saumon", ingredients=["pavés de saumon", "riz basmati"])
    tiramisu = plat("dessert-tira-01", "Tiramisu", genre="dessert", ingredients=["mascarpone", "œufs"])
    c = cout_semaine([[carbo, tiramisu], [saumon]], placard("spaghetti", "riz basmati"), [habituel("œufs", actif=True)])
    assert c["nb_repas"] == 2 and c["livraison"] == 2 * LIVRAISON_DEUX
    assert 0 < c["cout"] < c["livraison"]
    assert c["a_acheter"] == ["pecorino", "mascarpone", "pavés de saumon"]     # les œufs sont déjà sur la liste
    assert c["courses"] == round(sum(prix_de(n)[1] for n in c["a_acheter"] if prix_de(n)), 2)


def test_repas_prevus():
    par_id = {i: plat(i, i) for i in ("plat-aaaa-01", "plat-bbbb-01", "plat-cccc-01")}
    repas = [diner(LUN, "plat-aaaa-01", "plat-bbbb-01"),
             diner(LUN + timedelta(days=1), "plat-cccc-01", moment="dejeuner"),
             diner(LUN + timedelta(days=2), "plat-aaaa-01", issue="commande"),     # déjà passé : pas aux courses
             diner(LUN + timedelta(days=3), "plat-inconnu-01"),                     # plat disparu : repas ignoré
             diner(LUN + timedelta(days=9), "plat-aaaa-01")]                        # hors semaine
    assert [[p["id"] for p in r] for r in repas_prevus(repas, par_id, SEMAINE)] == [
        ["plat-aaaa-01", "plat-bbbb-01"], ["plat-cccc-01"]]


# --- À acheter pour les repas du jour (page Aujourd'hui) ---

def test_a_acheter_aujourd_hui():
    from diners import a_acheter_aujourd_hui
    burger = plat("plat-burger-01", "Burger", ingredients=["steaks hachés", "pains burger", "Tomates", "oignons"])
    puree = plat("acc-puree-001", "Purée", genre="accompagnement", ingredients=["pommes de terre", "tomates", "lait"])
    courses = [{"nom": "oignons", "actif": True, "pris": False, "recurrent": False},       # sur la liste : à acheter
               {"nom": "lait", "actif": False, "pris": False, "recurrent": True}]         # habituel rangé : on en a
    assert a_acheter_aujourd_hui([burger, puree], placard("pains burger"), courses) == [
        "steaks hachés", "Tomates", "oignons", "pommes de terre"]


def test_achete_recemment_compte_comme_a_la_maison():
    from diners import a_acheter_aujourd_hui, avec_achats_recents
    burger = plat("plat-burger-01", "Burger", ingredients=["salade", "tomates"])
    courses = avec_achats_recents([], ["Salade"])                        # achetée, panier vidé
    assert a_acheter_aujourd_hui([burger], placard(), courses) == ["tomates"]
    assert "salade" in disponibles(placard(), courses)


# --- À finir : d'abord ce qui va tourner ---

def test_secours_met_en_tete_ce_qui_finit_un_produit():
    plats = [plat("plat-omelette", "Omelette", minutes=10, ingredients=["œufs"]),
             plat("plat-salade-1", "Salade jambon", minutes=15, ingredients=["salade", "jambon"])]
    stock = placard("œufs", "salade", "jambon")
    assert [p["id"] for p in secours(plats, stock)[0]] == ["plat-omelette", "plat-salade-1"]
    assert [p["id"] for p in secours(plats, stock, a_finir={"jambon"})[0]] == ["plat-salade-1", "plat-omelette"]


def test_proposer_place_d_abord_un_plat_qui_finit_un_produit():
    plats = carte() + [{**plat("plat-poulet-01", "Poulet rôti", minutes=40, ingredients=["cuisses de poulet"]),
                        "recette": "1.", "pour": "nous"},
                       {**plat("plat-poulet-02", "Poulet lent", minutes=90, ingredients=["cuisses de poulet"]),
                        "recette": "1.", "pour": "nous"}]
    mar = LUN + timedelta(days=1)
    for graine in range(10):
        p = proposer(plats, [diner(LUN, "plat-carnet-00")], SEMAINE, LUN, hasard=Random(graine),
                     a_finir=[("cuisses de poulet", mar)])
        assert p[mar] == "plat-poulet-01" and len(p) == 3           # lundi déjà pris : mardi, ≤ 45 min


def test_proposer_a_finir_respecte_reproposer_et_la_cible():
    plats = carte() + [{**plat("plat-poulet-01", "Poulet rôti", minutes=40, ingredients=["cuisses de poulet"]),
                        "recette": "1.", "pour": "nous"}]
    p = proposer(plats, [], SEMAINE, LUN, hasard=Random(3))
    jour = sorted(p)[-1]
    soirs = [diner(j, v) for j, v in p.items()]
    q = proposer(plats, soirs, SEMAINE, LUN, remplacer=[jour], hasard=Random(4),
                 a_finir=[("cuisses de poulet", LUN + timedelta(days=1))])
    assert list(q) == [jour]                                         # Reproposer ne touche qu'au jour demandé
    plein = [diner(LUN + timedelta(days=i), f"plat-carnet-{i:02d}") for i in range(4)]
    assert proposer(plats, plein, SEMAINE, LUN, a_finir=[("cuisses de poulet", LUN + timedelta(days=5))]) == {}


def test_version_page_recettes():
    from valise import VERSION_PAGE
    assert VERSION_PAGE >= 48


def test_ce_soir_depuis_recettes_attend_l_envoi_avant_de_changer_de_page():
    from diners import SCRIPT_DINERS
    # enregistrerRepas et ajouterPlat rendent la promesse d'envoi
    assert "return envoyer({ url: 'api/repas'" in SCRIPT_DINERS
    assert "return enregistrerRepas(Object.assign({}, r, { plats: r.plats.concat([id]) }))" in SCRIPT_DINERS
    # sur Recettes, allerA attend que l'envoi soit parti ou mis en file ; sur Dîners, immédiat
    assert "const envoi = ajouterPlat(d.aujourd_hui, 'diner', p.id);" in SCRIPT_DINERS
    assert "if (PAGE === 'recettes' && envoi) envoi.then(aller, aller); else aller();" in SCRIPT_DINERS


def test_redirection_vers_recettes_sort_de_l_iife():
    from diners import SCRIPT_DINERS
    assert "{ location.replace('recettes'); return; }" in SCRIPT_DINERS


def test_page_diners_grille_proposer():
    from diners import SCRIPT_DINERS
    html = diners_en_html()
    assert "div.grille-proposer" in html and "'diners:grille'" in SCRIPT_DINERS
    assert "cases:" in SCRIPT_DINERS and "remplacer:" in SCRIPT_DINERS
    assert "['0|diner', '1|diner', '2|diner', '3|diner']" in SCRIPT_DINERS
    assert "Trois ou quatre dîners suffisent" not in SCRIPT_DINERS
    assert "repas à proposer" in SCRIPT_DINERS
    from valise import VERSION_PAGE
    assert VERSION_PAGE >= 57


def test_proposer_cases_hors_fenetre_jamais_propose():
    # une case à aujourd'hui + 10 est hors de la fenêtre de 7 jours : jamais proposée
    assert proposer_cases(carte(), [], [(LUN + timedelta(days=10), "diner")], LUN, hasard=Random(4)) == {}


def test_script_proposer_semaine_garde_anti_double_envoi_et_erreurs():
    from diners import SCRIPT_DINERS
    s = SCRIPT_DINERS
    assert "let proposeEnCours = false;" in s
    assert "if (proposeEnCours) return;" in s and "proposeEnCours = true;" in s
    assert s.count("proposeEnCours = false;") >= 3                      # déclaration + les deux branches du .then final
    assert "ok.disabled = !cases.length || proposeEnCours;" in s
    assert "if (proposeEnCours) re.disabled = true;" in s
    # « Proposer » mémorise toujours en fusionnant, et Reproposer ignore les jours passés
    assert "derniereProposition = Object.assign({}, derniereProposition, poses);" in s
    assert "cle.split('|')[0] >= d.aujourd_hui" in s
    # erreur serveur distincte de la panne réseau
    assert "Le serveur a refusé (code ' + e.code + ').'" in s
    # largeur des cases à 390 px
    from diners import STYLE_DINERS
    assert "padding: 6px; margin: 8px 0;" in STYLE_DINERS and "grid-template-columns: 2.2rem repeat(7" in STYLE_DINERS


def test_page_diners_vider_la_semaine():
    from diners import SCRIPT_DINERS
    assert "function viderSemaine" in SCRIPT_DINERS and "'Vider la semaine'" in SCRIPT_DINERS
    assert "'Oui, vider '" in SCRIPT_DINERS                         # confirmation dans la page, pas de confirm()
    assert "confirm(" not in SCRIPT_DINERS
    assert "!r.issue && r.plats.length" in SCRIPT_DINERS             # fait, commandé, dehors : gardés
