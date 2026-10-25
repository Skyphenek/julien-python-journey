"""Tests de valise.py — fonctions pures et règle d'accumulation."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))   # permet d'importer valise depuis ce dossier

from valise import (total_jours, jours_par_type,
                    statut_ue_itineraire, prises_itineraire,
                    quantite_reelle, faire_valise,
                    valise_en_html, paquet_vide)

def test_total_jours():
    itin = [{"destination": "Hanoï", "jours": 7, "mois": 1},
            {"destination": "Siem Reap", "jours": 4, "mois": 1},
            {"destination": "Phu Quoc", "jours": 7, "mois": 1}]
    assert total_jours(itin) == 18


def test_jours_par_type_additionne_les_etapes():
    # janvier, zone asie_sud_est -> ["chaud", "plage"] pour les deux villes
    itin = [{"destination": "Hanoï", "jours": 7, "mois": 1},
            {"destination": "Siem Reap", "jours": 4, "mois": 1}]
    jpt = jours_par_type(itin)
    assert jpt["chaud"] == 11
    assert jpt["plage"] == 11


def test_jours_par_type_type_sur_une_seule_etape():
    # étape d'été asie_sud_est -> ["chaud", "plage", "pluie"] ; pluie sur cette étape seule
    itin = [{"destination": "Hanoï", "jours": 5, "mois": 1},
            {"destination": "Hanoï", "jours": 3, "mois": 7}]
    jpt = jours_par_type(itin)
    assert jpt["chaud"] == 8
    assert jpt["pluie"] == 3

def test_statut_ue_hors_ue_si_une_etape_hors_ue():
    itin = [{"destination": "France", "jours": 3, "mois": 6},
            {"destination": "Thaïlande", "jours": 5, "mois": 1}]
    hors_ue, inconnu = statut_ue_itineraire(itin)
    assert hors_ue is True
    assert inconnu is False


def test_statut_ue_ue_si_toutes_ue():
    itin = [{"destination": "France", "jours": 3, "mois": 6},
            {"destination": "Italie", "jours": 5, "mois": 6}]
    hors_ue, inconnu = statut_ue_itineraire(itin)
    assert hors_ue is False
    assert inconnu is False


def test_statut_ue_inconnu_declenche_le_flag():
    itin = [{"destination": "Tokyo", "jours": 3, "mois": 6}]   # ville -> statut inconnu
    hors_ue, inconnu = statut_ue_itineraire(itin)
    assert hors_ue is True
    assert inconnu is True


def test_prises_itineraire_dedup_et_sans_aucun():
    itin = [{"destination": "France", "jours": 3, "mois": 6},     # aucun
            {"destination": "Vietnam", "jours": 5, "mois": 1},    # universel
            {"destination": "Cambodge", "jours": 4, "mois": 1}]   # universel
    assert prises_itineraire(itin) == {"universel"}

def test_quantite_reelle_marqueurs():
    assert quantite_reelle("par_jour", 5) == 5
    assert quantite_reelle("par_semaine", 3) == 1        # plancher à 1
    assert quantite_reelle("par_3_jours", 10) == 3
    assert quantite_reelle((3, "par_semaine"), 14) == 6  # 3 x (14//7)
    assert quantite_reelle(2, 10) == 2


def test_faire_valise_max_entre_deux_climats():
    # shorts réclamés par chaud (18j -> 6) et plage (7j -> 2) : on garde le max
    jpt = {"chaud": 18, "plage": 7}
    valise = faire_valise(jpt, 18, ["Julien"], hors_ue=True, conduit=False)
    assert valise["Julien"]["Vêtements"]["shorts"] == 6


def test_faire_valise_suppression_chemises_si_chaud():
    # chaud met "chemises": 0 -> retire la base ; "chemises légères" les remplace
    jpt = {"chaud": 10, "ville": 10}
    valise = faire_valise(jpt, 10, ["Julien"], hors_ue=False, conduit=False)
    vetements = valise["Julien"]["Vêtements"]
    assert "chemises" not in vetements
    assert "chemises légères" in vetements


def test_faire_valise_chemises_conservees_sans_chaud():
    jpt = {"ville": 10}
    valise = faire_valise(jpt, 10, ["Julien"], hors_ue=False, conduit=False)
    assert "chemises" in valise["Julien"]["Vêtements"]


def test_faire_valise_pantalons_par_semaine():
    # après le réglage §6 : base par_semaine -> 18//7 = 2
    jpt = {"chaud": 18, "plage": 18}
    valise = faire_valise(jpt, 18, ["Julien"], hors_ue=True, conduit=False)
    assert valise["Julien"]["Vêtements"]["pantalons"] == 2


def test_faire_valise_documents_selon_ue():
    jpt = {"ville": 5}
    hors = faire_valise(jpt, 5, ["Julien"], hors_ue=True, conduit=False)
    dans = faire_valise(jpt, 5, ["Julien"], hors_ue=False, conduit=False)
    assert "passeport" in hors["Julien"]["Documents"]
    assert "carte d'identité" in dans["Julien"]["Documents"]

def test_faire_valise_dimension_par_jours_du_climat():
    # maillot n'existe que dans "plage" ; plage=7j sur 18 total -> 7//3=2, pas 18//3=6
    jpt = {"chaud": 18, "plage": 7}
    valise = faire_valise(jpt, 18, ["Julien"], hors_ue=True, conduit=False)
    assert valise["Julien"]["Vêtements"]["maillot"] == 2


def test_valise_en_html_injecte_la_variable_voyage():
    html = valise_en_html({"Partagé": paquet_vide()}, "Hanoï › Siem Reap", 11, {"universel"})
    assert 'const VOYAGE = "Hanoï › Siem Reap";' in html