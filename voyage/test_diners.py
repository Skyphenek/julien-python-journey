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
    assert "<title>Dîners · Casa Binomerie</title>" in html
    assert 'data-hub="diners" class="actif"' in html
    for vue in ("ce-soir", "semaine", "carnet", "a-tester"):
        assert f'data-vue="{vue}"' in html
    assert "function envoyerOuGarder" in html and "wakeLock" in html
    assert "api/diners/proposer" in html and "Proposer ma semaine" in html and "Reproposer" in html   # A
    assert "function ouvrirChoix" in html and "function barreEtiquettes" in html                       # B
    for e in ("rapide", "nous", "julien", "air-fryer", "poisson", "legumes"):
        assert f"'{e}'" in html
    assert "badge julien" in html and "pour: pour.value" in html                                        # D
    assert '<script type="application/json" id="prix">' in html and "function compteurDiners" in html     # C
    assert "Déjà sur la liste" in html and "À acheter" in html and "manquants aux courses" in html      # E
    assert "Au hasard parmi" in html and "'laetitia'" in html and "Laetitia seule" in html
    assert "api/repas" in html and "api/soirs" not in html and "d.soirs" not in html                  # repas composés
    for f in ("function ajouterPlat", "function retirerPlat", "function ranges", "function carteRepas"):
        assert f in html
    assert "+ déjeuner ou brunch" in html and "+ accompagnement" in html and "'brunch'" in html
    assert "'au menu'" in html and "déjà 8 plats" in html                                              # feuille de choix
    assert "function accordsDe" in html and "function ouvrirAccords" in html                          # accords
    assert "Va bien avec" in html and "Modifier les accords" in html and "'Avec :'" in html
    assert "if (absents.length && !accompagne && r.plats.length < 8)" in html     # déjà un accompagnement : rien
    assert "['brunch', 'Brunch']" in html and "brunch-" in html and "'+ ajouter'" in html            # brunch
    assert "r.menus" in html and "plats.join(' ') === derniereProposition[iso]" in html             # étape 3


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
