"""Tests de a_finir.py : le frais suivi et daté, son état, les repas prévus, les plats suggérés (logique pure)."""
import sys
from datetime import date, timedelta
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from a_finir import (suivis, etat, utilise, couverture, suggestions, jour_libre, alertes, plats_qui_utilisent,
                     A_FINIR_JOURS)
from conservation import duree
from courses import normaliser

AUJ = date(2026, 11, 3)                       # un mardi
J = lambda n: AUJ + timedelta(days=n)


def element(nom, entre_le=AUJ, en_stock=True, zone="frigo"):
    return {"cle": normaliser(nom), "nom": nom, "en_stock": en_stock, "zone": zone, "entre_le": entre_le}


def habituel(nom, actif=False, pris=False):
    return {"nom": nom, "recurrent": True, "actif": actif, "pris": pris}


def plat(id_, nom, ingredients, minutes=20, statut="carnet", archive=False, pour="nous", genre="plat"):
    return {"id": id_, "nom": nom, "ingredients": list(ingredients), "minutes": minutes, "statut": statut,
            "archive": archive, "pour": pour, "genre": genre}


def repas(jour, *plats, issue=None, moment="diner"):
    return {"jour": jour, "moment": moment, "plats": list(plats), "issue": issue}


# --- suivis ---

def test_suivis_placard_du_frigo_seulement():
    p = suivis([element("steaks hachés", J(-1)), element("petits pois", zone="congelateur"),
                element("comté", en_stock=False)], [], {}, {})
    assert [(x["cle"], x["origine"], x["jusqu_au"]) for x in p] == [("steaks haches", "placard", J(-1) + timedelta(days=1))]


def test_suivis_date_d_entree_la_plus_recente():
    p = suivis([element("jambon", J(-5))], [], {"jambon": J(-1)}, {})
    assert p[0]["jusqu_au"] == J(-1) + timedelta(days=duree("jambon"))


def test_suivis_habituels_ranges_du_frigo():
    courses = [habituel("mozzarella"), habituel("yaourt grec", actif=True, pris=True), habituel("lait", actif=True),
               habituel("citrons"), {"nom": "jambon", "recurrent": False, "actif": True, "pris": True}]
    p = suivis([], courses, {"mozzarella": J(-2), "yaourt grec": AUJ, "lait": AUJ, "citrons": AUJ, "jambon": AUJ}, {})
    assert {x["cle"]: x["origine"] for x in p} == {"mozzarella": "habituel", "yaourt grec": "habituel"}


def test_suivis_sans_date_non_suivi_sauf_correction():
    assert suivis([], [habituel("beurre")], {}, {}) == []
    assert suivis([], [habituel("beurre")], {}, {"beurre": J(5)})[0]["jusqu_au"] == J(5)


def test_suivis_la_correction_l_emporte_et_tri_par_date():
    p = suivis([element("comté", J(-30)), element("salade", J(-1))], [], {}, {"comte": J(9)})
    assert [(x["cle"], x["jusqu_au"]) for x in p] == [("salade", J(-1) + timedelta(days=4)), ("comte", J(9))]


def test_suivis_un_produit_du_placard_et_habituel_compte_une_fois():
    p = suivis([element("jambon", J(-1))], [habituel("jambon")], {}, {})
    assert len(p) == 1 and p[0]["origine"] == "placard"


# --- état ---

def test_etat():
    assert etat(J(-1), AUJ) == "a-verifier"
    assert etat(AUJ, AUJ) == "a-finir" and etat(J(A_FINIR_JOURS), AUJ) == "a-finir"
    assert etat(J(A_FINIR_JOURS + 1), AUJ) is None


# --- couverture par les repas prévus ---

POULET = plat("plat-poulet-01", "Poulet rôti", ["cuisses de poulet", "thym"])
SALADE = plat("plat-salade-01", "Salade César", ["salade", "cuisses de poulet", "parmesan"], minutes=15)
PAR_ID = {p["id"]: p for p in (POULET, SALADE)}


def test_couverture():
    assert utilise(POULET, "cuisses de poulet") and not utilise(POULET, "salade")
    assert couverture("cuisses de poulet", J(1), [repas(J(1), POULET["id"])], PAR_ID, AUJ) == (True, None)
    assert couverture("cuisses de poulet", J(1), [repas(J(3), POULET["id"]), repas(J(2), SALADE["id"])],
                      PAR_ID, AUJ) == (False, J(2))
    assert couverture("cuisses de poulet", J(1), [], PAR_ID, AUJ) == (False, None)
    vecu = [repas(AUJ, POULET["id"], issue="commande"), repas(J(1), POULET["id"], moment="dejeuner")]
    assert couverture("cuisses de poulet", J(1), vecu, PAR_ID, AUJ) == (True, None)       # le déjeuner compte
    assert couverture("cuisses de poulet", J(1), vecu[:1], PAR_ID, AUJ) == (False, None)  # vécu : ne compte pas


# --- suggestions ---

def test_suggestions_filtres_tri_et_maximum():
    plats = [POULET, SALADE,
             plat("plat-poulet-02", "Poulet curry", ["cuisses de poulet", "curry", "lait de coco"], minutes=30),
             plat("plat-poulet-03", "Poulet basquaise", ["cuisses de poulet", "poivrons"], minutes=40),
             plat("plat-poulet-jul", "Poulet piquant", ["cuisses de poulet"], pour="julien"),
             plat("plat-poulet-arc", "Vieux poulet", ["cuisses de poulet"], archive=True),
             plat("plat-poulet-tst", "Poulet à tester", ["cuisses de poulet"], statut="a-tester"),
             plat("acc-poulet-001", "Accompagnement", ["cuisses de poulet"], genre="accompagnement")]
    stock = {"cuisses de poulet", "thym", "salade", "parmesan", "curry"}
    s = suggestions("cuisses de poulet", ["cuisses de poulet", "salade"], plats, stock)
    assert [x["plat"]["id"] for x in s] == ["plat-salade-01", "plat-poulet-01", "plat-poulet-02"]
    assert s[0]["manquants"] == [] and s[2]["manquants"] == ["lait de coco"]


# --- jour libre ---

def test_jour_libre():
    assert jour_libre([], AUJ, J(2)) == AUJ
    assert jour_libre([repas(AUJ, "plat-x-000001"), repas(J(1), issue="dehors")], AUJ, J(2)) == J(2)
    assert jour_libre([repas(AUJ, "plat-x-000001", moment="dejeuner")], AUJ, J(1)) == AUJ
    assert jour_libre([repas(AUJ, "plat-x-000001")], AUJ, AUJ) is None


# --- alertes ---

def test_alertes():
    produits = [{"cle": "steaks haches", "nom": "steaks hachés", "origine": "placard", "jusqu_au": J(-1)},
                {"cle": "cuisses de poulet", "nom": "cuisses de poulet", "origine": "placard", "jusqu_au": J(1)},
                {"cle": "salade", "nom": "salade", "origine": "placard", "jusqu_au": J(2)},
                {"cle": "comte", "nom": "comté", "origine": "placard", "jusqu_au": J(20)}]
    a = alertes(produits, [repas(J(4), POULET["id"]), repas(J(1), SALADE["id"]), repas(AUJ, "plat-autre-01")],
                [POULET, SALADE], {"thym", "parmesan"}, AUJ)
    # la salade est utilisée demain (Salade César) : couverte ; le poulet aussi (même repas) ; le comté : loin
    assert [(x["cle"], x["etat"]) for x in a] == [("steaks haches", "a-verifier")]
    assert a[0]["suggestions"] == [] and a[0]["jour"] is None and a[0]["trop_tard"] is None

    b = alertes(produits[:2], [repas(J(4), POULET["id"]), repas(AUJ, "plat-autre-01")], [POULET, SALADE],
                {"thym", "salade", "parmesan"}, AUJ)
    poulet = b[1]
    assert poulet["cle"] == "cuisses de poulet" and poulet["etat"] == "a-finir" and poulet["trop_tard"] == J(4)
    assert [x["plat"]["id"] for x in poulet["suggestions"]] == ["plat-salade-01", "plat-poulet-01"]
    assert poulet["jour"] == J(1)                                     # ce soir est déjà pris


def test_plats_qui_utilisent():
    assert plats_qui_utilisent([POULET, SALADE], {"salade"}) == ["plat-salade-01"]
    assert plats_qui_utilisent([POULET, SALADE], set()) == []
