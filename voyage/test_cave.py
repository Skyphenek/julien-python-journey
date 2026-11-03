"""Tests de la Cave (cave.py, cave_depart.py) : validation, statut, valeurs par défaut, reprise de départ."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pytest
from cave import COULEURS, valider_bouteille, statut, par_defaut
from cave_depart import NOM_REPRISE, CAVE_DEPART

A = 2026


def corps(**champs):
    return {"id": "vin-test", "nom": "Saint-Joseph", "couleur": "rouge", "millesime": 2019, "quantite": 1} | champs


def test_couleurs():
    assert [c for c, _ in COULEURS] == ["rouge", "blanc", "rose", "bulles", "doux"]


def test_valider_complete_les_defauts():
    b = valider_bouteille(corps(), A)
    assert b["debut"] == 2026 and b["fin"] == 2026 and b["accords"] == ["boeuf", "charcuterie"]   # 2019+2..+6 -> 2021–2025, ramené à 2026
    assert b["producteur"] == "" and b["note"] == "" and b["prix_bas"] is None and b["prix_haut"] is None


def test_valider_garde_ce_qui_est_donne():
    b = valider_bouteille(corps(debut=2026, fin=2028, accords=["volaille"], prix_bas=25, prix_haut=30,
                                producteur="Cave de Tain", note="offert"), A)
    assert (b["debut"], b["fin"], b["accords"], b["prix_bas"], b["prix_haut"]) == (2026, 2028, ["volaille"], 25, 30)
    assert b["producteur"] == "Cave de Tain" and b["note"] == "offert"


@pytest.mark.parametrize("mauvais", [
    {"id": ""}, {"nom": "  "}, {"couleur": "vert"}, {"millesime": 1800}, {"millesime": 2027}, {"millesime": "2019"},
    {"quantite": -1}, {"quantite": True}, {"quantite": 1000}, {"debut": 2029, "fin": 2027},
    {"accords": ["pizza"]}, {"accords": "boeuf"}, {"prix_bas": 40, "prix_haut": 30}, {"prix_haut": -1},
    {"couleur": []},
])
def test_valider_refuse(mauvais):
    with pytest.raises(ValueError):
        valider_bouteille(corps(**mauvais), A)


def test_valider_null_vaut_absent():
    """Un null explicite dans le JSON se comporte comme une clé absente."""
    b = valider_bouteille(corps(quantite=None), A)
    assert b["quantite"] == 1


def test_valider_null_sur_fenetre_prend_le_defaut():
    b = valider_bouteille(corps(debut=None, fin=None), A)
    assert (b["debut"], b["fin"]) == (2026, 2026)                  # rouge 2019 : fenêtre par défaut, ramenée à 2026


def test_valider_null_sur_accords_prend_le_defaut():
    assert valider_bouteille(corps(accords=None), A)["accords"] == ["boeuf", "charcuterie"]


def test_valider_null_reste_none_pour_millesime_et_prix():
    b = valider_bouteille(corps(millesime=None, prix_bas=None, prix_haut=None), A)
    assert b["millesime"] is None and b["prix_bas"] is None and b["prix_haut"] is None


def test_valider_refuse_un_corps_absent():
    with pytest.raises(ValueError):
        valider_bouteille(None, A)


def test_statut_aux_bornes():
    assert statut({"debut": 2027, "fin": 2035}, A) == "garder"
    assert statut({"debut": 2026, "fin": 2026}, A) == "vite"
    assert statut({"debut": 2020, "fin": 2025}, A) == "vite"
    assert statut({"debut": 2026, "fin": 2027}, A) == "prete"


def test_par_defaut():
    assert par_defaut("rouge", 2023, A) == (2026, 2029, ["boeuf", "charcuterie"])
    assert par_defaut("blanc", 2025, A) == (2026, 2027, ["poisson", "fromage"])
    assert par_defaut("rose", 2026, A) == (2026, 2028, ["legumes", "apero"])
    assert par_defaut("bulles", 2024, A) == (2026, 2029, ["apero"])
    assert par_defaut("doux", 2023, A) == (2026, 2028, ["dessert", "fromage"])
    assert par_defaut("rouge", None, A) == (2026, 2028, ["boeuf", "charcuterie"])
    assert par_defaut("rouge", 2015, A) == (2026, 2026, ["boeuf", "charcuterie"])   # fin jamais avant début


def test_reprise_de_depart():
    assert NOM_REPRISE == "cave-v1"
    assert len(CAVE_DEPART) == 19 and sum(b["quantite"] for b in CAVE_DEPART) == 20
    assert len({b["id"] for b in CAVE_DEPART}) == 19
    for b in CAVE_DEPART:
        assert valider_bouteille(b, A) == b                          # déjà complètes et valides
    noms = " ".join(b["nom"] for b in CAVE_DEPART)
    assert "Chardonnay" not in noms and "Aude" not in noms         # vins de cuisine : au placard
    belles = sorted(b["nom"] for b in CAVE_DEPART if b["prix_haut"] > 30)
    assert belles == ["Billecart-Salmon Brut Rosé", "Château Sociando-Mallet", "Connétable Talbot", "Le Clos des Fées",
                      "Lucile Avril", "Nuits-Saint-Georges « Les Longecourts »"]
