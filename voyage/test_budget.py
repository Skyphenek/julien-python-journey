"""Tests du budget de la maison (budget.py) : les semaines, les forfaits, les repas maison."""
import sys
from datetime import date, timedelta
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from budget import semaines_budget, moyenne_precedentes, lundi, euros, FORFAIT_RESTO
from diners import LIVRAISON_DEUX
from prix_paris import cout_repas

MER = date(2026, 11, 4)                     # un mercredi : la semaine commence le lundi 2
LUN = date(2026, 11, 2)
CARBO = {"id": "plat-carbonara", "ingredients": ["spaghetti", "œufs", "pecorino"], "recette": "Pour 2"}
PLATS = {"plat-carbonara": CARBO}


def achat(jour, nom, prix):
    return {"jour": jour, "nom": nom, "prix": prix}


def repas(jour, issue, *plats, moment="diner"):
    return {"jour": jour, "moment": moment, "plats": list(plats), "issue": issue}


def test_lundi_et_euros():
    assert lundi(MER) == LUN and lundi(LUN) == LUN and lundi(date(2026, 11, 8)) == LUN
    assert euros(81.6) == "82 €" and euros(36.5) == "37 €" and euros(0) == "0 €" and euros(-2.4) == "-2 €"


def test_une_semaine():
    achats = [achat(LUN, "lait", 1.5), achat(MER, "pain", 1.4), achat(MER, "bidule", None),
              achat(LUN - timedelta(days=1), "hier dimanche", 9.0)]                    # semaine d'avant
    les_repas = [repas(LUN, "fait", "plat-carbonara"), repas(MER, "commande"),
                 repas(MER, "dehors", moment="dejeuner"), repas(MER + timedelta(days=1), None, "plat-carbonara")]
    s = semaines_budget(achats, les_repas, PLATS, MER)[0]
    cout = cout_repas(CARBO["ingredients"], CARBO["recette"])
    assert s["lundi"] == LUN and s["courses"] == 2.9 and s["sans_prix"] == 1 and s["courses_suivies"]
    assert (s["commandes"], s["restos"]) == (1, 1) and s["livraison"] == LIVRAISON_DEUX + FORFAIT_RESTO
    assert s["total"] == round(2.9 + LIVRAISON_DEUX + FORFAIT_RESTO, 2)
    assert s["maison"] == 1 and s["cout_maison"] == round(cout, 2)
    assert s["economie"] == round(LIVRAISON_DEUX - cout, 2)


def test_douze_semaines_la_plus_recente_en_premier():
    semaines = semaines_budget([], [], {}, MER)
    assert len(semaines) == 12 and semaines[0]["lundi"] == LUN and semaines[1]["lundi"] == LUN - timedelta(weeks=1)
    assert semaines[0]["cout_maison"] is None and semaines[0]["total"] == 0 and not semaines[0]["courses_suivies"]


def test_courses_suivies_a_partir_du_premier_achat():
    semaines = semaines_budget([achat(LUN - timedelta(days=3), "lait", 1.5)], [], {}, MER)
    assert semaines[0]["courses_suivies"] and semaines[1]["courses_suivies"] and not semaines[2]["courses_suivies"]


def test_repas_maison_sans_plat_compte_mais_sans_cout():
    s = semaines_budget([], [repas(LUN, "fait"), repas(MER, "fait", "plat-carbonara")], PLATS, MER)[0]
    cout = cout_repas(CARBO["ingredients"], CARBO["recette"])
    assert s["maison"] == 2 and s["cout_maison"] == round(cout, 2) and s["economie"] == round(LIVRAISON_DEUX - cout, 2)


def test_moyenne_des_semaines_precedentes():
    avant = LUN - timedelta(weeks=3)
    semaines = semaines_budget([achat(avant, "lait", 1.5)],                            # le suivi commence il y a 3 semaines
                               [repas(LUN - timedelta(weeks=1), "commande"),
                                repas(LUN - timedelta(weeks=2), "dehors")], {}, MER)
    assert moyenne_precedentes(semaines) == round((LIVRAISON_DEUX + FORFAIT_RESTO + 1.5) / 3, 2)   # semaines vides ignorées
    assert moyenne_precedentes(semaines_budget([], [], {}, MER)) is None


def test_moyenne_ignore_les_semaines_non_suivies():
    """Avant le premier achat, le total ne contient que des livraisons : il fausserait la moyenne."""
    semaines = semaines_budget([achat(LUN - timedelta(weeks=1), "lait", 1.5)],
                               [repas(LUN - timedelta(weeks=3), "commande")], {}, MER)
    assert not semaines[3]["courses_suivies"] and semaines[3]["total"] == LIVRAISON_DEUX
    assert moyenne_precedentes(semaines) == 1.5                                       # seule la semaine 1 compte


# --- Pages ---
from budget import budget_en_html, graphique_svg


def test_page_budget():
    les_repas = [repas(MER, "commande"), repas(LUN, "fait", "plat-carbonara")]
    achats = [achat(LUN, "lait", 1.5), achat(LUN, "bidule", None), achat(LUN - timedelta(weeks=3), "pain", 1.4)]
    semaines = semaines_budget(achats, les_repas, PLATS, MER)
    # 1,50 € de courses + 35 € de livraison = 36,50 € -> 37 €
    html = budget_en_html(semaines, moyenne_precedentes(semaines))
    assert "<title>Budget · Casa Binomerie</title>" in html and "<h1>Budget</h1>" in html
    assert 'data-hub="budget" class="actif"' in html
    assert "Cette semaine" in html and "37 €" in html
    assert "1 article sans prix" in html and "pas encore suivi" not in html          # le suivi commence il y a 3 semaines
    assert html.count("<tr") == 5                                                     # en-tête + 4 semaines
    assert '<svg class="graphique"' in html


def test_page_budget_depuis_la_premiere_semaine_avec_des_chiffres():
    semaines = semaines_budget([achat(LUN - timedelta(weeks=1), "lait", 1.5)], [repas(MER, "commande")], {}, MER)
    html = budget_en_html(semaines, moyenne_precedentes(semaines))
    assert html.count("<tr") == 3 and html.count('class="barre-courses"') == 2        # en-tête + 2 semaines


def test_page_budget_sans_donnees_une_semaine():
    html = budget_en_html(semaines_budget([], [], {}, MER), None)
    assert html.count("<tr") == 2 and html.count('class="barre-courses"') == 1


def test_economie_nulle_ou_negative_en_tiret():
    semaines = semaines_budget([], [], {}, MER)
    assert "<strong>—</strong><span>Économisés" in budget_en_html(semaines, None)
    semaines = semaines_budget([], [repas(LUN, "fait", "plat-carbonara")], PLATS, MER)
    assert semaines[0]["economie"] > 0 and "<strong>—</strong><span>Économisés" not in budget_en_html(semaines, None)


def test_graphique_barres_empilees():
    semaines = semaines_budget([achat(LUN, "lait", 20.0)], [repas(MER, "commande")], {}, MER)
    svg = graphique_svg(semaines)
    assert svg.count('class="barre-courses"') == 12 and svg.count('class="barre-livraison"') == 12
    assert svg.index("02/11") > svg.index("31/08")                              # la plus ancienne à gauche


def test_peu_de_semaines_des_barres_fines():
    svg = graphique_svg(semaines_budget([], [repas(MER, "commande")], {}, MER, n=2))
    assert 'width="28.0"' in svg and svg.count('class="barre-livraison"') == 2


def test_repas_tout_pret_sans_cout_ne_fausse_pas_l_economie():
    plats = {**PLATS, "pret-roti-taboule": {"id": "pret-roti-taboule", "ingredients": [], "recette": "Pour 2"}}
    s = semaines_budget([], [repas(LUN, "fait", "pret-roti-taboule", moment="dejeuner")], plats, MER)[0]
    assert s["maison"] == 1 and s["cout_maison"] is None and s["economie"] == 0
