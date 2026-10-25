"""Tests de valise.py — fonctions pures et règle d'accumulation."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))   # permet d'importer valise depuis ce dossier

from valise import (total_jours, jours_par_type,
                    statut_ue_itineraire, prises_itineraire,
                    quantite_reelle, faire_valise,
                    valise_en_html, paquet_vide, ligne_climat,
                    types_climat)

def test_total_jours():
    itin = [{"destination": "Hanoï", "jours": 7, "mois": 1},
            {"destination": "Siem Reap", "jours": 4, "mois": 1},
            {"destination": "Phu Quoc", "jours": 7, "mois": 1}]
    assert total_jours(itin) == 18


# Normales factices (même format que api_climat.normales) : pas de réseau dans les tests
LONDRES_JANV = {"tmin": 1.6, "tmax": 7.7, "jours_pluie": 12}
HANOI_JANV = {"tmin": 14.3, "tmax": 21.1, "jours_pluie": 10}
SIEM_REAP_JANV = {"tmin": 21.5, "tmax": 31.1, "jours_pluie": 2}


def test_types_climat_froid_et_pluie():
    assert types_climat(LONDRES_JANV) == ["froid", "pluie"]


def test_types_climat_chaud():
    assert types_climat(SIEM_REAP_JANV) == ["chaud"]


def test_types_climat_doux_ni_chaud_ni_froid():
    # Hanoï en janvier : 21 °C max -> ni chaud ni froid (les anciennes zones disaient "chaud")
    assert types_climat(HANOI_JANV) == ["pluie"]


def test_types_climat_inconnu():
    assert types_climat(None) == []


def test_jours_par_type_additionne_les_etapes():
    itin = [{"destination": "Hanoï", "jours": 7, "mois": 1,
             "activites": ["ville"], "normales": HANOI_JANV},
            {"destination": "Siem Reap", "jours": 4, "mois": 1,
             "activites": ["ville"], "normales": SIEM_REAP_JANV}]
    jpt = jours_par_type(itin)
    assert jpt["ville"] == 11      # activité présente sur les deux étapes
    assert jpt["pluie"] == 7       # climat de Hanoï seulement
    assert jpt["chaud"] == 4       # climat de Siem Reap seulement


def test_jours_par_type_plusieurs_activites():
    itin = [{"destination": "Phu Quoc", "jours": 7, "mois": 1,
             "activites": ["plage", "ville"], "normales": SIEM_REAP_JANV}]
    jpt = jours_par_type(itin)
    assert jpt == {"chaud": 7, "plage": 7, "ville": 7}


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
    itin = [{"destination": "Lima", "jours": 3, "mois": 6}]   # ville non modélisée -> statut inconnu
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
    # maillot de bain n'existe que dans "plage" ; plage=7j sur 18 total -> 7//3=2, pas 18//3=6
    jpt = {"chaud": 18, "plage": 7}
    valise = faire_valise(jpt, 18, ["Julien"], hors_ue=True, conduit=False)
    assert valise["Julien"]["Vêtements"]["maillot de bain"] == 2


def test_valise_en_html_injecte_la_variable_voyage():
    html = valise_en_html({"Partagé": paquet_vide()}, "Hanoï › Siem Reap", 11, {"universel"})
    assert 'const VOYAGE = "Hanoï › Siem Reap";' in html

def test_ligne_climat_formate_les_normales():
    n = {"tmin": 1.6, "tmax": 7.7, "jours_pluie": 12}
    assert ligne_climat("Londres", 1, n) == "Londres · janvier : 2–8 °C · 🌧️ 12 j de pluie/mois"


def test_ligne_climat_sans_donnees():
    # Ville introuvable ou API en panne -> on le dit, sans planter
    assert ligne_climat("Atlantide", 7, None) == "Atlantide · juillet : climat indisponible"


def test_valise_en_html_affiche_le_climat():
    climats = [("Hanoï", 1, {"tmin": 14.3, "tmax": 21.1, "jours_pluie": 10})]
    html = valise_en_html({"Partagé": paquet_vide()}, "Hanoï", 7, set(), climats)
    assert "Hanoï · janvier : 14–21 °C" in html
