"""Tests de valise.py — fonctions pures et règle d'accumulation."""
import sys
from datetime import date
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))   # permet d'importer valise depuis ce dossier

from valise import (total_jours, jours_par_type,
                    statut_ue_itineraire, prises_itineraire,
                    quantite_reelle, faire_valise,
                    valise_en_html, paquet_vide, ligne_climat,
                    types_climat, libelle_lieu,
                    lire_mois, lire_activites, est_oui, un_par_pays, lire_lessive, objets_sans_rayon,
                    construire, rendre_page, completer_coordonnees, appliquer_previsions, types_pour,
                    fenetres_meteo, valise_depuis_photo, accueil_en_html, lieux_depuis_reponse,
                    SCRIPT_RECHERCHE, voyage_depuis_formulaire, formulaire_en_html, CHOIX_ACTIVITE,
                    statut_ue, adaptateur_pour, normales_avec_cache,
                    THEMES, ICONES_RAYON, puce_climat, HTML_SCRIPT,
                    lire_date, mois_des_etapes, code_voyage,
                    cle_objet, etiquettes_climat, propositions, appliquer, appliquer_regles, theme_de,
                    avant_de_partir)

def test_total_jours():
    itin = [{"destination": "Hanoï", "jours": 7, "mois": 1},
            {"destination": "Siem Reap", "jours": 4, "mois": 1},
            {"destination": "Phu Quoc", "jours": 7, "mois": 1}]
    assert total_jours(itin) == 18


# Normales factices (même format que api_climat.normales) : pas de réseau dans les tests
# Valeurs réelles mesurées (Open-Meteo, 2016-2025)
LONDRES_JANV = {"tmin": 1.6, "tmax": 7.7, "jours_pluie": 12, "jours_forte_pluie": 4.3}
HANOI_JANV = {"tmin": 14.3, "tmax": 21.1, "jours_pluie": 10, "jours_forte_pluie": 3.4}
SIEM_REAP_JANV = {"tmin": 21.5, "tmax": 31.1, "jours_pluie": 2, "jours_forte_pluie": 0.5}
PHU_QUOC_JANV = {"tmin": 24.0, "tmax": 30.0, "jours_pluie": 10, "jours_forte_pluie": 2.6}
PHU_QUOC_AOUT = {"tmin": 25.0, "tmax": 29.5, "jours_pluie": 30, "jours_forte_pluie": 23.8}


def test_types_climat_froid_et_pluie():
    assert types_climat(LONDRES_JANV) == ["froid", "pluie"]


def test_types_climat_chaud():
    assert types_climat(SIEM_REAP_JANV) == ["chaud"]


def test_types_climat_frais_si_soirees_fraiches():
    # Hanoï en janvier : 21 °C max (ni chaud ni froid) mais 14 °C min -> "frais" (un pull)
    assert types_climat(HANOI_JANV) == ["frais"]       # bruine : pas assez de vraie pluie


def test_types_climat_froid_n_est_pas_aussi_frais():
    # Londres est déjà "froid" (manteau, pulls) : pas de "frais" en doublon
    assert "frais" not in types_climat(LONDRES_JANV)


def test_types_climat_chaud_et_soirees_fraiches():
    # Désert : 30 °C le jour, 10 °C la nuit -> chaud ET frais
    assert types_climat({"tmin": 10, "tmax": 30, "jours_pluie": 0, "jours_forte_pluie": 0}) == ["chaud", "frais"]


def test_pluie_saison_seche_vs_mousson():
    # Phu Quoc : 10 jours "humides" en janvier mais peu de vraie pluie -> pas d'imperméable
    assert "pluie" not in types_climat(PHU_QUOC_JANV)
    assert "averses" in types_climat(PHU_QUOC_AOUT)   # chaud + pluie = averses (voir plus bas)


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
    assert jpt["frais"] == 7       # climat de Hanoï seulement
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
    assert ligne_climat("Londres", 1, LONDRES_JANV) == "Londres · janvier : 2–8 °C · 🌧️ 12 j de pluie/mois, dont 4 forts"


def test_ligne_climat_sans_donnees():
    # Ville introuvable ou API en panne -> on le dit, sans planter
    assert ligne_climat("Atlantide", 7, None) == "Atlantide · juillet : climat indisponible"


def test_valise_en_html_affiche_le_climat():
    climats = [("Hanoï", 1, HANOI_JANV)]
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



def test_normales_avec_cache_sans_base():
    # Postgres éteint (conn = None) : on interroge l'API directement, sans planter
    fausse_api = lambda latitude, longitude: {1: HANOI_JANV}
    assert normales_avec_cache(None, 21.03, 105.85, 1, chercher=fausse_api) == HANOI_JANV



# --- Affichage : rayons repliables ---

def test_chaque_rayon_a_une_icone():
    # Garde-fou : un rayon ajouté dans THEMES sans icône se verrait tout de suite
    assert set(THEMES) <= set(ICONES_RAYON)


def test_valise_en_html_rayon_repliable_avec_icone_et_compteur():
    paquet = paquet_vide()
    paquet["Vêtements"]["shorts"] = 3
    html = valise_en_html({"Julien": paquet}, "Hanoï", 7, set())
    assert '<details class="rayon" open>' in html            # repliable, ouvert au départ
    assert "👕" in html
    assert '<span class="compte"></span>' in html             # rempli par le JavaScript


def test_valise_en_html_quantite_en_pastille():
    paquet = paquet_vide()
    paquet["Vêtements"]["shorts"] = 3
    html = valise_en_html({"Julien": paquet}, "Hanoï", 7, set())
    assert '<span class="nom">shorts</span><span class="qte">×3</span>' in html


def test_valise_en_html_rayon_vide_absent():
    html = valise_en_html({"Julien": paquet_vide()}, "Hanoï", 7, set())
    assert '<details class="rayon"' not in html



def test_puce_climat_courte():
    assert puce_climat("Hanoï", HANOI_JANV) == "Hanoï 14–21° · 🌧️ 3 j forts"
    assert puce_climat("Atlantide", None) == "Atlantide ?"


# --- Barres de progression par personne ---

def _valise_de(*personnes):
    return faire_valise({"ville": 5}, 5, list(personnes), hors_ue=False, conduit=False)


def test_deux_voyageurs_trois_barres():
    html = valise_en_html(_valise_de("Julien", "Laetitia"), "Rome", 5, set())
    assert html.count('<div class="barre"') == 3
    assert '<div class="barre" data-owner="Julien">' in html
    assert '<div class="barre" data-owner="Laetitia">' in html
    assert '<div class="barre" data-owner=""><div class="progress-head"><span>Total</span>' in html


def test_un_voyageur_une_seule_barre():
    html = valise_en_html(_valise_de("Laetitia"), "Rome", 5, set())
    assert html.count('<div class="barre"') == 1
    assert '<div class="barre" data-owner=""><div class="progress-head"><span>Rangé</span>' in html



def test_appels_api_relatifs():
    # En ligne, la page vit sous /v/<secret>/ : "api/..." (relatif) suit, "/api/..." (absolu) casserait
    assert "fetch('/api/" not in HTML_SCRIPT
    assert "url: '/api/" not in HTML_SCRIPT                      # envois via la file d'attente
    assert "url: 'api/coche'" in HTML_SCRIPT



# --- Identité d'un voyage : date de départ, mois calculés, code stable ---

def test_lire_date_formats_courants():
    attendu = date(2027, 1, 10)
    for saisie in ["10/01/2027", "10/1/2027", "10/01/27", " 10-01-2027 ", "2027-01-10",
                   "10 janvier 2027", "10 janv 2027", "10 Janv. 2027"]:
        assert lire_date(saisie) == attendu, saisie


def test_lire_date_refuse_l_invalide():
    for saisie in ["", "31/02/2027", "demain", "10/13/2027", "10 ju 2027"]:
        assert lire_date(saisie) is None, saisie


def test_mois_des_etapes_jour_du_milieu():
    # Départ 10 janvier : Tokyo 7 j (milieu 13/01), Kyoto 4 j (milieu 18/01),
    # Bangkok 20 j du 21/01 au 09/02 (milieu 30/01 -> janvier), Bali 10 j (milieu 14/02)
    assert mois_des_etapes(date(2027, 1, 10), [7, 4, 20, 10]) == [1, 1, 1, 2]


def test_mois_des_etapes_passage_d_annee():
    assert mois_des_etapes(date(2026, 12, 28), [3, 10]) == [12, 1]


def test_code_voyage_stable():
    # Même date + même itinéraire -> même code : régénérer la valise garde les cases cochées
    assert code_voyage(date(2027, 1, 10), "Tokyo › Bangkok") == "2027-01-10 Tokyo › Bangkok"


def test_valise_en_html_cles_avec_le_code_du_voyage():
    paquet = paquet_vide()
    paquet["Vêtements"]["shorts"] = 3
    html = valise_en_html({"Julien": paquet}, "Tokyo › Bangkok", 18, set(),
                          code="2027-01-10 Tokyo › Bangkok", depart=date(2027, 1, 10))
    assert 'const VOYAGE = "2027-01-10 Tokyo › Bangkok";' in html
    assert 'data-key="2027-01-10 Tokyo › Bangkok/Julien/Vêtements/shorts"' in html
    assert "départ le 10 janvier 2027" in html



# --- Mode Bilan dans la page ---

def test_page_bouton_mode_bilan():
    html = valise_en_html(_valise_de("Julien"), "Rome", 5, set())
    assert 'id="mode-bilan"' in html
    assert 'id="bilan-compte"' in html


def test_chaque_objet_a_ses_boutons_de_bilan():
    html = valise_en_html(_valise_de("Julien", "Laetitia"), "Rome", 5, set())
    assert html.count('<div class="bilan">') == html.count("data-key=")
    for verdict in ["utile", "trop", "pas_servi"]:
        assert f'data-verdict="{verdict}"' in html


def test_objet_porte_proprietaire_et_quantite():
    paquet = paquet_vide()
    paquet["Vêtements"]["shorts"] = 3
    paquet["Vêtements"]["pull"] = 1
    html = valise_en_html({"Julien": paquet}, "Rome", 5, set())
    assert '<li data-owner="Julien" data-objet="shorts" data-qte="3" data-qte-multi>' in html
    assert '<li data-owner="Julien" data-objet="pull" data-qte="1">' in html    # 1 exemplaire : pas de "utilisé x/1"


def test_bloc_ce_qui_a_manque_par_onglet():
    html = valise_en_html(_valise_de("Julien", "Laetitia"), "Rome", 5, set())
    assert '<div class="manques" data-owner="Julien"><h3>Ce qui a manqué à Julien</h3>' in html
    assert '<div class="manques" data-owner="Laetitia"><h3>Ce qui a manqué à Laetitia</h3>' in html
    assert '<div class="manques" data-owner="Partagé"><h3>Ce qui nous a manqué</h3>' in html


# --- Adaptateur : seulement si une étape en a besoin (révélé par le 1er bilan : Italie) ---

def test_pas_d_adaptateur_si_prises_identiques():
    valise = faire_valise({"ville": 9}, 9, ["Julien"], hors_ue=False, conduit=False, adaptateur=False)
    assert "adaptateur de prise" not in valise["Julien"]["Tech"]


def test_adaptateur_par_defaut_et_si_besoin():
    valise = faire_valise({"ville": 9}, 9, ["Julien", "Laetitia"], hors_ue=True, conduit=False, adaptateur=True)
    assert valise["Julien"]["Tech"]["adaptateur de prise"] == 1
    assert valise["Laetitia"]["Tech"]["adaptateur de prise"] == 1



# --- Session 3 : la valise apprend des bilans ---

def _historique(jours_types, objets, retours, code="2027-04-30 Florence › Palerme", libelle="Florence › Palerme",
                depart=date(2027, 4, 30)):
    return {"code": code, "libelle": libelle, "depart": depart, "jours_types": jours_types,
            "objets": objets, "retours": retours}


def _r(objet, verdict, q=None, qui="Julien"):
    return {"proprietaire": qui, "objet": objet, "verdict": verdict, "quantite_utilisee": q}


def _valise(**objets_julien):
    paquet = paquet_vide()
    for objet, q in objets_julien.items():
        objet = objet.replace("_", "-")                  # t_shirts (nom d'argument Python) -> t-shirts
        paquet[theme_de(objet)][objet] = q
    return {"Partagé": paquet_vide(), "Julien": paquet}


def test_cle_objet_ignore_casse_accents_pluriels():
    assert cle_objet("Bouchons d'oreilles") == cle_objet("bouchon d'oreille")
    assert cle_objet("  Crème  solaire ") == cle_objet("creme solaire")
    assert cle_objet("t-shirts") == cle_objet("T-shirt")


def test_etiquettes_climat_ignore_les_activites():
    assert etiquettes_climat({"chaud": 4, "ville": 9, "plage": 4}) == {"chaud"}


def test_oubli_propose_a_la_personne_concernee():
    h = [_historique({"ville": 9}, {}, [_r("Mots fléchés et critérium", "manque")])]
    props = propositions(_valise(t_shirts=9), {"ville": 9}, h, regles={})
    assert props == [{"type": "ajout", "personne": "Julien", "objet": "Mots fléchés et critérium",
                      "theme": "Divers", "actuelle": 0, "proposee": 1, "source": "Florence › Palerme"}]


def test_oubli_deja_dans_la_valise_pas_repropose():
    h = [_historique({"ville": 9}, {}, [_r("Pull", "manque")])]
    assert propositions(_valise(pull=1), {"ville": 9}, h, regles={}) == []


def test_oubli_deja_en_regle_toujours_pas_repropose():
    h = [_historique({"ville": 9}, {}, [_r("mots fléchés", "manque")])]
    regles = {"Julien": [{"objet": "Mots fléchés", "theme": "Divers", "quantite": 1}]}
    assert propositions(_valise(), {"ville": 9}, h, regles=regles) == []


def test_oubli_d_une_personne_absente_du_voyage_ignore():
    h = [_historique({"ville": 9}, {}, [_r("lisseur", "manque", qui="Laetitia")])]
    assert propositions(_valise(), {"ville": 9}, h, regles={}) == []


def test_en_trop_meme_climat_reduit_au_prorata():
    # Florence : 9 t-shirts proposés, 2 utilisés (22 %) -> aujourd'hui 18 prévus -> 4
    h = [_historique({"chaud": 4, "ville": 9}, {("Julien", "Vêtements", "t-shirts"): 9},
                     [_r("t-shirts", "trop", 2)])]
    props = propositions(_valise(t_shirts=18), {"chaud": 10, "plage": 18}, h, regles={})
    assert props == [{"type": "quantite", "personne": "Julien", "objet": "t-shirts", "theme": "Vêtements",
                      "actuelle": 18, "proposee": 4, "source": "Florence › Palerme", "utilise": "2/9"}]


def test_en_trop_climat_different_ignore():
    h = [_historique({"chaud": 4, "ville": 9}, {("Julien", "Vêtements", "t-shirts"): 9},
                     [_r("t-shirts", "trop", 2)])]
    assert propositions(_valise(t_shirts=18), {"froid": 18}, h, regles={}) == []


def test_pas_servi_meme_climat_propose_retrait():
    h = [_historique({"ville": 9}, {("Julien", "Chaussures", "baskets"): 1}, [_r("baskets", "pas_servi")])]
    props = propositions(_valise(baskets=1), {"ville": 5}, h, regles={})
    assert props[0]["type"] == "retrait" and props[0]["proposee"] == 0


def test_en_trop_objet_unique_sans_quantite_propose_retrait():
    h = [_historique({"ville": 9}, {("Julien", "Divers", "livre / liseuse"): 1}, [_r("livre / liseuse", "trop")])]
    assert propositions(_valise(**{"livre / liseuse": 1}), {"ville": 5}, h, regles={})[0]["type"] == "retrait"


def test_le_voyage_le_plus_recent_l_emporte():
    ancien = _historique({"ville": 9}, {("Julien", "Vêtements", "t-shirts"): 10}, [_r("t-shirts", "trop", 5)],
                         code="2025-01-01 Rome", libelle="Rome", depart=date(2025, 1, 1))
    recent = _historique({"ville": 9}, {("Julien", "Vêtements", "t-shirts"): 10}, [_r("t-shirts", "utile")])
    # historique trié du plus récent au plus ancien : "utile" à Florence -> on ne touche à rien
    assert propositions(_valise(t_shirts=10), {"ville": 9}, [recent, ancien], regles={}) == []


def test_appliquer_une_proposition():
    v = _valise(t_shirts=18, baskets=1)
    appliquer(v, {"type": "quantite", "personne": "Julien", "theme": "Vêtements", "objet": "t-shirts", "proposee": 4})
    appliquer(v, {"type": "retrait", "personne": "Julien", "theme": "Chaussures", "objet": "baskets", "proposee": 0})
    appliquer(v, {"type": "ajout", "personne": "Julien", "theme": "Divers", "objet": "Mots fléchés", "proposee": 1})
    assert v["Julien"]["Vêtements"]["t-shirts"] == 4
    assert "baskets" not in v["Julien"]["Chaussures"]
    assert v["Julien"]["Divers"]["Mots fléchés"] == 1


def test_appliquer_regles_toujours():
    v = _valise()
    ajouts = appliquer_regles(v, {"Julien": [{"objet": "Mots fléchés", "theme": "Divers", "quantite": 1}],
                                  "Laetitia": [{"objet": "lisseur", "theme": "Hygiène", "quantite": 1}]})
    assert v["Julien"]["Divers"]["Mots fléchés"] == 1
    assert ajouts == [("Julien", "Mots fléchés")]           # Laetitia ne voyage pas : rien pour elle


# --- Lessive en route : plafonne les rayons Vêtements et Sous-vêtements ---

def test_faire_valise_sans_lessive_inchange():
    # non-régression : sans le paramètre, 18 jours -> 18 caleçons
    jpt = {"chaud": 18}
    valise = faire_valise(jpt, 18, ["Julien"], hors_ue=True, conduit=False)
    assert valise["Julien"]["Sous-vêtements"]["caleçons"] == 18


def test_faire_valise_lessive_plafonne_sous_vetements():
    # lessive tous les 7 jours : on part avec 7 caleçons, pas 18
    jpt = {"chaud": 18}
    valise = faire_valise(jpt, 18, ["Julien"], hors_ue=True, conduit=False,
                          lessive_tous_les=7)
    assert valise["Julien"]["Sous-vêtements"]["caleçons"] == 7


def test_faire_valise_lessive_plafonne_vetements_climat():
    # shorts (chaud, par_3_jours) : 18//3 = 6 sans lessive -> 7//3 = 2 avec
    jpt = {"chaud": 18}
    valise = faire_valise(jpt, 18, ["Julien"], hors_ue=True, conduit=False,
                          lessive_tous_les=7)
    assert valise["Julien"]["Vêtements"]["shorts"] == 2


def test_faire_valise_lessive_ne_touche_pas_le_reste():
    # documents, tech, hygiène... restent ceux du voyage complet
    jpt = {"chaud": 18}
    sans = faire_valise(jpt, 18, ["Julien"], hors_ue=True, conduit=False)
    avec = faire_valise(jpt, 18, ["Julien"], hors_ue=True, conduit=False,
                        lessive_tous_les=7)
    for rayon in ["Chaussures", "Accessoires", "Hygiène", "Tech", "Documents", "Divers"]:
        assert avec["Julien"][rayon] == sans["Julien"][rayon]
    assert avec["Partagé"] == sans["Partagé"]


def test_lire_lessive():
    assert lire_lessive("") is None          # Entrée = pas de lessive
    assert lire_lessive("n") is None
    assert lire_lessive(" non ") is None
    assert lire_lessive("5") == 5
    assert lire_lessive(" 7 ") == 7
    assert lire_lessive("0") is None         # 0 jour n'a pas de sens -> pas de lessive
    assert lire_lessive("abc") is None       # saisie invalide -> on ne plafonne pas


def test_faire_valise_lessive_plancher_de_deux():
    # lessive tous les 5 jours : shorts 5//3 = 1 -> plancher 2 (un sur soi, un au lavage)
    jpt = {"chaud": 18, "plage": 7}
    valise = faire_valise(jpt, 18, ["Julien"], hors_ue=True, conduit=False,
                          lessive_tous_les=5)
    assert valise["Julien"]["Vêtements"]["shorts"] == 2
    assert valise["Julien"]["Vêtements"]["maillot de bain"] == 2


def test_faire_valise_lessive_plancher_jamais_au_dessus_du_voyage_complet():
    # tenue habillée : 1 sans lessive -> reste 1 (le plancher ne rajoute rien)
    jpt = {"chaud": 18, "ville": 18}
    valise = faire_valise(jpt, 18, ["Julien"], hors_ue=True, conduit=False,
                          lessive_tous_les=5)
    assert valise["Julien"]["Vêtements"]["tenue habillée"] == 1


# --- Retours sur la valise test Berlin › Sotchi (2026-10-26) ---

def test_lunettes_de_soleil_une_puis_deux_au_dela_d_une_semaine():
    courte = faire_valise({"chaud": 7}, 7, ["Julien"], hors_ue=True, conduit=False)
    longue = faire_valise({"chaud": 20}, 20, ["Julien"], hors_ue=True, conduit=False)
    tres_longue = faire_valise({"chaud": 30}, 30, ["Julien"], hors_ue=True, conduit=False)
    plage = faire_valise({"plage": 10}, 10, ["Julien"], hors_ue=True, conduit=False)
    assert courte["Julien"]["Accessoires"]["lunettes de soleil"] == 1
    assert longue["Julien"]["Accessoires"]["lunettes de soleil"] == 2
    assert tres_longue["Julien"]["Accessoires"]["lunettes de soleil"] == 2   # plafond : 2, pas 4
    assert plage["Julien"]["Accessoires"]["lunettes de soleil"] == 2


def test_chaussettes_si_chaussures_fermees_meme_en_pays_chaud():
    # Laetitia : pays chaud = chaussures ouvertes, sauf si la ville ajoute des baskets
    ville = faire_valise({"chaud": 14, "ville": 14}, 14, ["Laetitia"], hors_ue=True, conduit=False)
    plage = faire_valise({"chaud": 14, "plage": 14}, 14, ["Laetitia"], hors_ue=True, conduit=False)
    assert ville["Laetitia"]["Sous-vêtements"]["chaussettes"] == 6      # 3 paires / semaine
    assert "chaussettes" not in plage["Laetitia"]["Sous-vêtements"]


def test_pas_de_chaussures_de_rechange_si_autre_paire_fermee():
    ville = faire_valise({"ville": 10}, 10, ["Julien"], hors_ue=True, conduit=False)
    plage = faire_valise({"plage": 10}, 10, ["Julien"], hors_ue=True, conduit=False)
    assert "chaussures de rechange" not in ville["Julien"]["Chaussures"]   # les baskets suffisent
    assert "chaussures de rechange" in plage["Julien"]["Chaussures"]


def test_types_climat_averses_si_chaud_et_pluie():
    orage_ete = {"tmin": 15, "tmax": 26, "jours_pluie": 12, "jours_forte_pluie": 6}   # Prague en août
    pluie_froide = {"tmin": 2, "tmax": 8, "jours_pluie": 15, "jours_forte_pluie": 6}
    assert types_climat(orage_ete) == ["chaud", "averses"]
    assert "pluie" in types_climat(pluie_froide)


def test_averses_kway_et_un_parapluie_pour_deux():
    jpt = {"chaud": 20, "averses": 6}
    valise = faire_valise(jpt, 20, ["Julien", "Laetitia"], hors_ue=True, conduit=False)
    for p in ["Julien", "Laetitia"]:
        assert "imperméable" in valise[p]["Vêtements"]
        assert "chaussures imperméables" not in valise[p]["Chaussures"]
        assert "parapluie" not in valise[p]["Divers"]
    assert valise["Partagé"]["Divers"]["parapluie"] == 1


def test_vraie_pluie_garde_les_chaussures_impermeables():
    # Londres en hiver + Bangkok : la pluie froide d'une étape garde les chaussures imperméables
    jpt = {"froid": 5, "pluie": 5, "chaud": 10}
    valise = faire_valise(jpt, 15, ["Julien"], hors_ue=True, conduit=False)
    assert "chaussures imperméables" in valise["Julien"]["Chaussures"]


def test_maillot_deux_des_quatre_jours_de_plage():
    court = faire_valise({"plage": 3}, 3, ["Julien"], hors_ue=True, conduit=False)
    quatre = faire_valise({"chaud": 10, "plage": 4}, 10, ["Julien"], hors_ue=True, conduit=False)
    assert court["Julien"]["Vêtements"]["maillot de bain"] == 1
    assert quatre["Julien"]["Vêtements"]["maillot de bain"] == 2    # un sur soi, un qui sèche


def test_un_seul_sweat_en_pays_chaud():
    jpt = {"chaud": 20, "ville": 20}
    valise = faire_valise(jpt, 20, ["Julien", "Laetitia"], hors_ue=True, conduit=False,
                          lessive_tous_les=10)
    assert valise["Julien"]["Vêtements"]["sweat"] == 1
    assert valise["Laetitia"]["Vêtements"]["sweat"] == 1


def test_creme_solaire_un_tube_par_semaine_de_soleil():
    court = faire_valise({"chaud": 6}, 6, ["Julien"], hors_ue=True, conduit=False)
    long = faire_valise({"chaud": 21, "plage": 7}, 21, ["Julien"], hors_ue=True, conduit=False)
    assert court["Partagé"]["Hygiène"]["crème solaire"] == 1
    assert long["Partagé"]["Hygiène"]["crème solaire"] == 3


def test_maillot_plafonne_a_trois():
    # 18 jours de plage : 18//3 = 6 -> plafond 3 (un sur soi, un qui sèche, un pour le style)
    valise = faire_valise({"plage": 18}, 18, ["Julien"], hors_ue=True, conduit=False)
    assert valise["Julien"]["Vêtements"]["maillot de bain"] == 3


# --- Activités enrichies (9 lettres) ---

def test_lire_activites_neuf_lettres():
    assert lire_activites("tsk") == ["culte", "scooter", "snorkeling"]
    assert lire_activites("j n r") == ["nature", "nuit", "road trip"]
    assert lire_activites("vpm") == ["montagne", "plage", "ville"]


def _une_activite(activite, personnes=("Julien", "Laetitia"), conduit=False):
    return faire_valise({activite: 5}, 5, list(personnes), hors_ue=True, conduit=conduit)


def test_activite_lieux_de_culte():
    v = _une_activite("culte")
    assert v["Julien"]["Vêtements"]["tenue couverte"] == 1
    assert v["Laetitia"]["Vêtements"]["tenue couverte"] == 1
    assert v["Laetitia"]["Accessoires"]["étole"] == 1
    assert "étole" not in v["Julien"]["Accessoires"]


def test_activite_lieux_de_culte_resiste_au_pays_chaud():
    # CHAUD_PERSO réécrit des vêtements après coup : la tenue couverte ne doit pas sauter
    v = faire_valise({"chaud": 5, "culte": 5}, 5, ["Laetitia"], hors_ue=True, conduit=False)
    assert v["Laetitia"]["Vêtements"]["tenue couverte"] == 1


def test_activite_snorkeling():
    v = _une_activite("snorkeling")
    assert v["Julien"]["Vêtements"]["top anti-UV"] == 1
    assert v["Julien"]["Chaussures"]["chaussures d'eau"] == 1
    assert v["Partagé"]["Divers"]["pochette étanche"] == 1


def test_activite_nature_moustiques():
    v = _une_activite("nature")
    assert v["Julien"]["Vêtements"]["manches longues légères"] == 1
    assert v["Partagé"]["Hygiène"]["répulsif moustiques"] == 1
    assert v["Partagé"]["Tech"]["lampe frontale"] == 1


def test_activite_transport_de_nuit():
    v = _une_activite("nuit")
    assert v["Julien"]["Divers"]["bouchons d'oreilles"] == 1
    assert v["Julien"]["Divers"]["masque de sommeil"] == 1
    assert v["Julien"]["Vêtements"]["couche légère"] == 1
    assert v["Partagé"]["Divers"]["cadenas"] == 1


def test_activite_road_trip():
    v = _une_activite("road trip")
    assert v["Partagé"]["Tech"]["support téléphone voiture"] == 1
    assert v["Partagé"]["Tech"]["chargeur voiture USB"] == 1
    assert v["Partagé"]["Divers"]["glacière souple"] == 1


def test_activite_scooter():
    v = _une_activite("scooter")
    assert v["Julien"]["Accessoires"]["buff anti-poussière"] == 1
    assert v["Julien"]["Accessoires"]["gants légers"] == 1


def test_scooter_et_road_trip_impliquent_le_permis():
    # même si on a répondu "non" à "Tu vas conduire ?" : seuls les conducteurs le prennent
    for activite in ["scooter", "road trip"]:
        v = _une_activite(activite, conduit=False)
        assert v["Julien"]["Documents"]["permis"] == 1
        assert v["Julien"]["Documents"]["permis international"] == 1
        assert "permis" not in v["Laetitia"]["Documents"]


def test_nouveaux_objets_tous_ranges():
    assert objets_sans_rayon() == set()


# --- construire() : la génération sans terminal (base du bouton météo et de la saisie en ligne) ---

VOYAGE_VIETNAM = {
    "depart": date(2027, 1, 10),
    "itineraire": [
        {"destination": "Hanoï", "jours": 7, "mois": 1, "activites": ["culte", "ville"],
         "normales": HANOI_JANV, "code_pays": "VN"},
        {"destination": "Siem Reap", "jours": 4, "mois": 1, "activites": ["culte", "nature"],
         "normales": SIEM_REAP_JANV, "code_pays": "KH"},
        {"destination": "Phu Quoc", "jours": 7, "mois": 1, "activites": ["plage", "snorkeling"],
         "normales": PHU_QUOC_JANV, "code_pays": "VN"},
    ],
    "personnes": ["Julien", "Laetitia"],
    "conduit": False,
    "lessive": 7,
}


def test_construire_identique_a_la_chaine_du_terminal():
    # caractérisation : construire() reproduit exactement ce que main() enchaînait à la main
    itin = VOYAGE_VIETNAM["itineraire"]
    jpt = jours_par_type(itin)
    hors_ue, _ = statut_ue_itineraire(itin)
    attendu = faire_valise(jpt, 18, ["Julien", "Laetitia"], hors_ue, False,
                           adaptateur=bool(prises_itineraire(itin)), lessive_tous_les=7)
    c = construire(VOYAGE_VIETNAM)
    assert c["valise"] == attendu
    assert c["jours_types"] == jpt
    assert c["total"] == 18
    assert c["libelle"] == "Hanoï › Siem Reap › Phu Quoc"
    assert c["code"] == code_voyage(date(2027, 1, 10), "Hanoï › Siem Reap › Phu Quoc")
    assert c["ue_inconnu"] is False


def test_construire_sans_lessive_ni_conduite():
    voyage = {**VOYAGE_VIETNAM, "lessive": None}
    c = construire(voyage)
    assert c["valise"]["Julien"]["Sous-vêtements"]["caleçons"] == 18


def test_construire_ne_modifie_pas_le_voyage():
    import copy
    avant = copy.deepcopy(VOYAGE_VIETNAM)
    construire(VOYAGE_VIETNAM)
    assert VOYAGE_VIETNAM == avant


def test_rendre_page_transmet_chaque_element_calcule(monkeypatch):
    """rendre_page calcule et passe à valise_en_html : climats, tâches, maison, étapes, devises, personnes…
    (vérifié par espionnage plutôt que par recopie de l'appel, qui cassait à chaque nouvelle rubrique)."""
    import valise
    recu = {}
    monkeypatch.setattr(valise, "valise_en_html", lambda *a, **k: recu.update(args=a, kwargs=k) or "html")
    c = construire(VOYAGE_VIETNAM)
    assert rendre_page(VOYAGE_VIETNAM, c, aujourd_hui=date(2026, 10, 27)) == "html"
    assert recu["args"][:4] == (c["valise"], c["libelle"], c["total"], c["prises"])
    k = recu["kwargs"]
    assert k["code"] == c["code"] and k["depart"] == date(2027, 1, 10) and k["jour"] == date(2026, 10, 27)
    assert k["taches"] == avant_de_partir(VOYAGE_VIETNAM["itineraire"], date(2027, 1, 10), date(2026, 10, 27))
    assert k["maison"] == valise.fermer_la_maison(c["total"], date(2027, 1, 10))
    assert k["etapes"] == valise.etapes_du_voyage(VOYAGE_VIETNAM["itineraire"], date(2027, 1, 10))
    assert k["devises"] == valise.devises_du_voyage(VOYAGE_VIETNAM["itineraire"])
    assert k["personnes"] == list(VOYAGE_VIETNAM["personnes"])


# --- Coordonnées des étapes (prévisions météo) ---

def _faux_lieux(nom):
    return {"Hanoï": [{"nom": "Hanoi", "code_pays": "PG", "latitude": -5.0, "longitude": 145.0},
                      {"nom": "Hanoï", "code_pays": "VN", "latitude": 21.03, "longitude": 105.85}],
            "Nulle Part": []}[nom]


def test_completer_coordonnees_retrouve_le_bon_pays():
    itin = [{"destination": "Hanoï", "jours": 5, "code_pays": "VN"}]
    complete = completer_coordonnees(itin, chercher=_faux_lieux)
    assert (complete[0]["latitude"], complete[0]["longitude"]) == (21.03, 105.85)   # pas la Papouasie
    assert "latitude" not in itin[0]                                                # l'original est intact


def test_completer_coordonnees_garde_l_existant_sans_appel():
    def interdit(nom):
        raise AssertionError("aucun appel réseau si les coordonnées sont déjà là")
    itin = [{"destination": "Hanoï", "jours": 5, "code_pays": "VN", "latitude": 1.0, "longitude": 2.0}]
    assert completer_coordonnees(itin, chercher=interdit) == itin


def test_completer_coordonnees_introuvable_ou_hors_ligne():
    import requests
    def hors_ligne(nom):
        raise requests.RequestException("pas de réseau")
    itin = [{"destination": "Nulle Part", "jours": 2, "code_pays": None}]
    assert "latitude" not in completer_coordonnees(itin, chercher=_faux_lieux)[0]
    assert "latitude" not in completer_coordonnees(itin, chercher=hors_ligne)[0]


# --- Étape 4 (météo J-7) : les prévisions remplacent les normales des étapes proches ---

CHAUD_ORAGEUX = {"tmin": 24.0, "tmax": 32.0, "jours_pluie": 10, "jours_forte_pluie": 5.0,
                 "prevu_le": "2027-01-07"}
ITIN_2_ETAPES = [
    {"destination": "Hanoï", "jours": 7, "mois": 1, "activites": ["ville"], "normales": HANOI_JANV,
     "code_pays": "VN", "latitude": 21.03, "longitude": 105.85},
    {"destination": "Phu Quoc", "jours": 7, "mois": 1, "activites": ["plage"], "normales": PHU_QUOC_JANV,
     "code_pays": "VN", "latitude": 10.23, "longitude": 103.96},
]


def test_la_prevision_prime_sur_les_normales():
    etape = {**ITIN_2_ETAPES[0], "prevision": CHAUD_ORAGEUX}     # Hanoï : normales douces, prévu chaud
    assert "chaud" not in types_pour(ITIN_2_ETAPES[0])
    assert types_pour(etape) == ["chaud", "averses", "ville"]


def test_puce_climat_signale_la_prevision():
    assert "prévu le 07/01" in puce_climat("Hanoï", CHAUD_ORAGEUX)
    assert "prévu" not in puce_climat("Hanoï", HANOI_JANV)


def test_rendre_page_affiche_la_prevision():
    voyage = {**VOYAGE_VIETNAM,
              "itineraire": [{**VOYAGE_VIETNAM["itineraire"][0], "prevision": CHAUD_ORAGEUX}]
                            + VOYAGE_VIETNAM["itineraire"][1:]}
    html = rendre_page(voyage, construire(voyage))
    assert "prévu le 07/01" in html


def test_page_porte_le_bouton_meteo_et_ses_dates():
    html = rendre_page(VOYAGE_VIETNAM, construire(VOYAGE_VIETNAM))
    assert 'id="meteo"' in html
    assert 'const DEPART = "2027-01-10"' in html
    assert 'const FIN = "2027-01-27"' in html                    # 18 jours : 10 -> 27 janvier

# --- Météo B : le navigateur appelle Open-Meteo, le serveur applique ce qu'il reçoit ---
# (les serveurs partagés de Render prennent des 429 Too Many Requests)

DAILY_CHAUD_ORAGEUX = {
    "time":               ["2027-01-10", "2027-01-11", "2027-01-12", "2027-01-13"],
    "temperature_2m_max": [32.0, 31.0, 33.0, 32.0],
    "temperature_2m_min": [24.0, 24.0, 25.0, 23.0],
    "precipitation_sum":  [0.0, 14.0, 0.0, 1.0],
}


def test_fenetres_meteo_etapes_proches_avec_url():
    voyage = {"depart": date(2027, 1, 10), "itineraire": ITIN_2_ETAPES}
    f = fenetres_meteo(voyage, date(2027, 1, 7))           # portée : jusqu'au 16 janvier
    assert len(f) == 1                                       # Phu Quoc (17 -> 23) hors portée
    assert f[0]["etape"] == 0 and f[0]["destination"] == "Hanoï"
    assert (f[0]["debut"], f[0]["fin"]) == ("2027-01-10", "2027-01-16")
    assert f[0]["url"].startswith("https://api.open-meteo.com/v1/forecast?")
    assert "latitude=21.03" in f[0]["url"] and "start_date=2027-01-10" in f[0]["url"]


def test_fenetres_meteo_ignore_les_etapes_sans_coordonnees():
    sans = [{k: v for k, v in ITIN_2_ETAPES[0].items() if k not in ("latitude", "longitude")}]
    assert fenetres_meteo({"depart": date(2027, 1, 10), "itineraire": sans}, date(2027, 1, 7)) == []


def test_appliquer_previsions_recues():
    erreurs = []
    itin = appliquer_previsions(ITIN_2_ETAPES, date(2027, 1, 10), date(2027, 1, 7),
                                {"0": DAILY_CHAUD_ORAGEUX}, erreurs)
    p = itin[0]["prevision"]
    assert (p["tmax"], p["tmin"], p["prevu_le"]) == (32.0, 24.0, "2027-01-07")
    assert "prevision" not in itin[1]                        # hors portée : rien attendu
    assert erreurs == []
    assert itin[0]["normales"] == HANOI_JANV                 # normales gardées en réserve
    assert "prevision" not in ITIN_2_ETAPES[0]               # original intact


def test_appliquer_previsions_erreur_du_navigateur_gardee_et_signalee():
    erreurs = []
    deja = [{**ITIN_2_ETAPES[0], "prevision": CHAUD_ORAGEUX}]
    itin = appliquer_previsions(deja, date(2027, 1, 10), date(2027, 1, 7),
                                {"0": {"erreur": "429 Too Many Requests"}}, erreurs)
    assert itin[0]["prevision"] == CHAUD_ORAGEUX              # on garde ce qu'on avait
    assert erreurs == ["Hanoï : 429 Too Many Requests"]


def test_appliquer_previsions_manquante_ou_illisible():
    erreurs = []
    appliquer_previsions(ITIN_2_ETAPES, date(2027, 1, 10), date(2027, 1, 7), {}, erreurs)
    assert erreurs == ["Hanoï : aucune prévision reçue"]
    erreurs = []
    appliquer_previsions(ITIN_2_ETAPES, date(2027, 1, 10), date(2027, 1, 7),
                         {"0": {"time": "n'importe quoi"}}, erreurs)
    assert erreurs == ["Hanoï : prévision illisible"]


def test_appliquer_previsions_retire_une_prevision_perimee():
    itin = [{**ITIN_2_ETAPES[0], "prevision": CHAUD_ORAGEUX}]
    nouveau = appliquer_previsions(itin, date(2027, 1, 10), date(2027, 1, 20), {}, [])
    assert "prevision" not in nouveau[0]                     # étape passée : plus de prévision


# --- Une page par voyage + accueil (création en ligne, étape 1) ---

def test_valise_depuis_photo_ordre_d_affichage():
    photo = {("Julien", "Documents", "passeport"): 1, ("Partagé", "Divers", "parapluie"): 1,
             ("Julien", "Vêtements", "t-shirts"): 5}
    v = valise_depuis_photo(photo, ["Julien"])
    assert list(v) == ["Partagé", "Julien"]                         # Partagé d'abord
    assert list(v["Julien"]) == list(paquet_vide())                 # rayons dans l'ordre habituel
    assert v["Julien"]["Vêtements"] == {"t-shirts": 5}
    assert v["Partagé"]["Divers"] == {"parapluie": 1}


def test_accueil_liste_les_voyages_a_venir_puis_passes():
    voyages = [
        {"code": "2026-10-01 Rome", "libelle": "Rome", "depart": date(2026, 10, 1),
         "fin": date(2026, 10, 4), "personnes": ["Julien"]},
        {"code": "2026-11-01 Oslo", "libelle": "Oslo", "depart": date(2026, 11, 1),
         "fin": date(2026, 11, 5), "personnes": ["Julien", "Laetitia"]},
    ]
    html = accueil_en_html(voyages, date(2026, 10, 26))
    assert html.index("À venir") < html.index("Oslo") < html.index("Passés") < html.index("Rome")
    assert 'href="?v=2026-11-01%20Oslo"' in html                     # lien vers la page du voyage
    assert "Julien · Laetitia" in html


def test_accueil_vide():
    assert "Aucune valise" in accueil_en_html([], date(2026, 10, 26))


def test_page_du_voyage_a_un_lien_vers_l_accueil():
    html = rendre_page(VOYAGE_VIETNAM, construire(VOYAGE_VIETNAM))
    assert 'href="./"' in html and "Tous les voyages" in html


# --- Création en ligne, étape 2 : interpréter ce que le téléphone a téléchargé ---

GEO_HANOI = {"results": [
    {"name": "Hanoï", "admin1": "Hanoï", "country": "Vietnam", "country_code": "VN", "latitude": 21.02, "longitude": 105.84},
    {"name": "Hanoi", "admin1": None, "country": "Vietnam", "country_code": "VN", "latitude": 21.0, "longitude": 105.8},
    {"name": "Hanoi", "admin1": "Madang", "country": "Papouasie", "country_code": "PG", "latitude": -5.0, "longitude": 145.0},
]}


def test_lieux_depuis_reponse_un_par_pays_avec_libelle():
    lieux = lieux_depuis_reponse(GEO_HANOI)
    assert [l["code_pays"] for l in lieux] == ["VN", "PG"]
    assert lieux[0]["libelle"] == "Hanoï — Hanoï, Vietnam"
    assert (lieux[0]["latitude"], lieux[0]["longitude"]) == (21.02, 105.84)


def test_lieux_depuis_reponse_vide_ou_invalide():
    assert lieux_depuis_reponse({}) == []                  # destination introuvable
    assert lieux_depuis_reponse({"results": "nope"}) == []  # réponse farfelue : pas de crash


def test_script_recherche_utilise_les_routes_du_serveur():
    assert "api/lieux" in SCRIPT_RECHERCHE and "api/normales" in SCRIPT_RECHERCHE


# --- Création en ligne, étape 3 : le formulaire ---

FORMULAIRE_LISBONNE = {
    "depart": "2027-05-01", "personnes": "2", "conduit": False, "lessive": None,
    "etapes": [{"destination": "Lisbonne", "code_pays": "PT", "latitude": 38.72, "longitude": -9.14,
                "jours": 4, "activites": ["ville", "plage"]}],
}


def test_voyage_depuis_formulaire():
    v = voyage_depuis_formulaire(FORMULAIRE_LISBONNE)
    assert v["depart"] == date(2027, 5, 1)
    assert v["personnes"] == ["Julien", "Laetitia"]
    assert (v["conduit"], v["lessive"]) == (False, None)
    e = v["itineraire"][0]
    assert (e["destination"], e["jours"], e["mois"], e["code_pays"]) == ("Lisbonne", 4, 5, "PT")
    assert (e["latitude"], e["longitude"], e["activites"]) == (38.72, -9.14, ["plage", "ville"])
    assert e["normales"] is None                                   # remplies par le serveur, depuis le cache


def test_voyage_depuis_formulaire_mois_par_etape_et_lessive():
    corps = {**FORMULAIRE_LISBONNE, "personnes": "l", "lessive": 7,
             "etapes": [{**FORMULAIRE_LISBONNE["etapes"][0], "jours": 28},
                        {**FORMULAIRE_LISBONNE["etapes"][0], "destination": "Porto", "jours": 8}]}
    v = voyage_depuis_formulaire(corps)
    assert [e["mois"] for e in v["itineraire"]] == [5, 6]           # Porto : 29 mai -> 5 juin, milieu le 1er juin
    assert v["personnes"] == ["Laetitia"] and v["lessive"] == 7


import pytest


@pytest.mark.parametrize("modif, message", [
    ({"depart": "31/02/2027"}, "date"),
    ({"personnes": "x"}, "qui part"),
    ({"etapes": []}, "étape"),
    ({"lessive": 0}, "lessive"),
    ({"etapes": [{**FORMULAIRE_LISBONNE["etapes"][0], "jours": 0}]}, "jours"),
    ({"etapes": [{**FORMULAIRE_LISBONNE["etapes"][0], "activites": ["piscine"]}]}, "activité"),
    ({"etapes": [{**FORMULAIRE_LISBONNE["etapes"][0], "latitude": None}]}, "destination"),
    ({"etapes": [{**FORMULAIRE_LISBONNE["etapes"][0], "destination": " "}]}, "destination"),
])
def test_voyage_depuis_formulaire_refuse_les_saisies_invalides(modif, message):
    with pytest.raises(ValueError, match=message):
        voyage_depuis_formulaire({**FORMULAIRE_LISBONNE, **modif})


def test_formulaire_contient_les_champs_et_les_activites():
    html = formulaire_en_html()
    assert 'type="date"' in html and "api/voyages" in html and "chercherLieux" in html
    for code, activite in CHOIX_ACTIVITE.items():
        assert f'value="{activite}"' in html                          # une case par activité
    assert 'href="./"' in html                                       # retour à l'accueil


def test_accueil_propose_une_nouvelle_valise():
    assert 'href="?nouvelle"' in accueil_en_html([], date(2026, 10, 26))


def test_formulaire_hidden_l_emporte_sur_le_style_des_labels():
    # bug vu dans Chrome : la ligne lessive restait affichée pour 3 jours
    assert "[hidden] { display: none !important; }" in formulaire_en_html()



def test_page_porte_sa_version():
    from valise import MARQUE_VERSION, VERSION_PAGE
    assert VERSION_PAGE >= 3                          # 3 = boutons modifier / retirer
    assert MARQUE_VERSION in valise_en_html({"Partagé": paquet_vide()}, "Rome", 3, set())
