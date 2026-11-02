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
    semaines = semaines_budget([], [repas(LUN - timedelta(weeks=1), "commande"),
                                    repas(LUN - timedelta(weeks=2), "dehors")], {}, MER)
    assert moyenne_precedentes(semaines) == round((LIVRAISON_DEUX + FORFAIT_RESTO) / 2, 2)    # semaines vides ignorées
    assert moyenne_precedentes(semaines_budget([], [], {}, MER)) is None
