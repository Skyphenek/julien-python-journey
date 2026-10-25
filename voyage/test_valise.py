"""Tests de valise.py — fonctions pures et règle d'accumulation."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))   # permet d'importer valise depuis ce dossier

from valise import (total_jours, jours_par_type,
                    statut_ue_itineraire, prises_itineraire,
                    quantite_reelle, faire_valise,
                    valise_en_html, paquet_vide, ligne_climat,
                    types_climat, libelle_lieu,
                    lire_mois, lire_activites, est_oui, un_par_pays,
                    statut_ue, adaptateur_pour)

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


def test_types_climat_frais_si_soirees_fraiches():
    # Hanoï en janvier : 21 °C max (ni chaud ni froid) mais 14 °C min -> "frais" (un pull)
    assert types_climat(HANOI_JANV) == ["frais", "pluie"]


def test_types_climat_froid_n_est_pas_aussi_frais():
    # Londres est déjà "froid" (manteau, pulls) : pas de "frais" en doublon
    assert "frais" not in types_climat(LONDRES_JANV)


def test_types_climat_chaud_et_soirees_fraiches():
    # Désert : 30 °C le jour, 10 °C la nuit -> chaud ET frais
    assert types_climat({"tmin": 10, "tmax": 30, "jours_pluie": 0}) == ["chaud", "frais"]


def test_frais_ajoute_un_pull():
    valise = faire_valise({"frais": 7, "ville": 7}, 7, ["Julien"], hors_ue=True, conduit=False)
    assert valise["Julien"]["Vêtements"]["pull"] == 1


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
    itin = [{"destination": "Paris", "code_pays": "FR"},
            {"destination": "Bangkok", "code_pays": "TH"}]
    hors_ue, inconnu = statut_ue_itineraire(itin)
    assert hors_ue is True
    assert inconnu is False


def test_statut_ue_ue_si_toutes_ue():
    itin = [{"destination": "Paris", "code_pays": "FR"},
            {"destination": "Genève", "code_pays": "CH"}]    # Schengen hors UE : carte d'identité OK
    hors_ue, inconnu = statut_ue_itineraire(itin)
    assert hors_ue is False
    assert inconnu is False


def test_statut_ue_inconnu_declenche_le_flag():
    itin = [{"destination": "Almaty", "code_pays": "KZ"}]    # pays non modélisé -> statut inconnu
    hors_ue, inconnu = statut_ue_itineraire(itin)
    assert hors_ue is True
    assert inconnu is True


def test_statut_ue_sans_pays_hors_ligne():
    itin = [{"destination": "Phu Quoc", "code_pays": None}]  # pas de réseau -> pays inconnu
    assert statut_ue_itineraire(itin) == (True, True)


def test_prises_itineraire_dedup_et_sans_aucun():
    itin = [{"destination": "Paris", "code_pays": "FR"},       # aucun
            {"destination": "Phu Quoc", "code_pays": "VN"},    # universel
            {"destination": "Siem Reap", "code_pays": "KH"}]   # universel
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


def test_libelle_lieu_distingue_les_homonymes():
    lieu = {"nom": "Bali", "region": "Bali", "pays": "Indonésie"}
    assert libelle_lieu(lieu) == "Bali — Bali, Indonésie"


def test_libelle_lieu_sans_region():
    # Singapour : l'API ne renvoie pas de région (admin1 = None)
    assert libelle_lieu({"nom": "Singapour", "region": None, "pays": "Singapour"}) == "Singapour — Singapour"



# --- Saisie tolérante : l'utilisateur tape comme il veut ---

def test_lire_mois_chiffre_ou_lettres():
    assert lire_mois("1") == 1
    assert lire_mois(" 12 ") == 12
    assert lire_mois("janvier") == 1
    assert lire_mois("Janv") == 1
    assert lire_mois("fevrier") == 2       # sans accent
    assert lire_mois("AOÛT") == 8


def test_lire_mois_refuse_l_ambigu_et_l_invalide():
    assert lire_mois("ju") is None         # juin ? juillet ?
    assert lire_mois("13") is None
    assert lire_mois("bonjour") is None


def test_lire_mois_entree_reprend_le_precedent():
    assert lire_mois("", precedent=1) == 1
    assert lire_mois("") is None           # première étape : pas de précédent


def test_lire_activites_formats_libres():
    assert lire_activites("pv") == ["plage", "ville"]
    assert lire_activites("V P") == ["plage", "ville"]
    assert lire_activites("v,p") == ["plage", "ville"]
    assert lire_activites("x") is None
    assert lire_activites("") is None


def test_est_oui():
    for r in ["o", "O", "oui", " Oui ", "y", "yes"]:
        assert est_oui(r) is True
    for r in ["n", "non", "", "peut-être"]:
        assert est_oui(r) is False


def test_un_par_pays_garde_le_premier_de_chaque_pays():
    candidats = [{"nom": "Hanoï", "code_pays": "VN"}, {"nom": "Hanoi", "code_pays": "VN"},
                 {"nom": "Hanoi", "code_pays": "PG"}, {"nom": "Bạch Mai", "code_pays": "VN"}]
    assert un_par_pays(candidats) == [{"nom": "Hanoï", "code_pays": "VN"},
                                      {"nom": "Hanoi", "code_pays": "PG"}]


# --- Couverture pays élargie ---

def test_dom_tom_carte_d_identite():
    assert statut_ue("RE") == "ue"         # La Réunion
    assert statut_ue("PF") == "ue"         # Polynésie française


def test_ue_complete():
    assert statut_ue("PL") == "ue"
    assert statut_ue("FI") == "ue"


def test_nouveaux_pays_hors_ue():
    assert statut_ue("ID") == "hors_ue"                 # Bali
    assert adaptateur_pour("ID") == "aucun"
    assert adaptateur_pour("AU") == "type I (Australie)"
    assert adaptateur_pour("PE") == "universel"
