"""Tests du rayon « Avant de partir » : tâches datées déduites des pays de l'itinéraire."""
import sys
from datetime import date, timedelta
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from valise import avant_de_partir, ajouter_mois
from formalites import FORMALITES

AUJOURD_HUI = date(2026, 10, 27)
DEPART = date(2027, 1, 10)
VIETNAM_CAMBODGE = [{"destination": "Hanoï", "jours": 7, "code_pays": "VN"},
                    {"destination": "Siem Reap", "jours": 4, "code_pays": "KH"},
                    {"destination": "Phu Quoc", "jours": 7, "code_pays": "VN"}]


def par_id(taches):
    return {t["id"]: t for t in taches}


def test_europe_seule_aucune_tache():
    itin = [{"destination": "Rome", "jours": 5, "code_pays": "IT"},
            {"destination": "Oslo", "jours": 3, "code_pays": "NO"}]
    assert avant_de_partir(itin, DEPART, AUJOURD_HUI) == []


def test_ajouter_mois_fin_de_mois():
    assert ajouter_mois(date(2027, 1, 27), 6) == date(2027, 7, 27)
    assert ajouter_mois(date(2027, 8, 31), 6) == date(2028, 2, 29)     # février bissextile
    assert ajouter_mois(date(2026, 8, 31), 6) == date(2027, 2, 28)


def test_vietnam_cambodge_taches_attendues():
    t = par_id(avant_de_partir(VIETNAM_CAMBODGE, DEPART, AUJOURD_HUI))
    assert {"passeport", "vaccins", "assurance", "visa-VN", "visa-KH",
            "e-arrival-KH", "usd-KH"} <= set(t)


def test_passeport_valide_six_mois_apres_le_retour():
    t = par_id(avant_de_partir(VIETNAM_CAMBODGE, DEPART, AUJOURD_HUI))
    # retour le 27/01/2027 (18 jours) -> passeport valide au moins jusqu'au 27/07/2027
    assert "27/07/2027" in t["passeport"]["texte"]
    assert t["passeport"]["quand"] == DEPART - timedelta(days=60)


def test_vaccins_deux_mois_avant_avec_lien_sante():
    t = par_id(avant_de_partir(VIETNAM_CAMBODGE, DEPART, AUJOURD_HUI))["vaccins"]
    assert t["quand"] == DEPART - timedelta(days=60)
    assert "Vietnam" in t["texte"] and "Cambodge" in t["texte"]
    assert t["lien"] == FORMALITES["VN"]["sante"]


def test_vietnam_sans_visa_sous_le_seuil_compte_tous_les_jours_sur_place():
    t = par_id(avant_de_partir(VIETNAM_CAMBODGE, DEPART, AUJOURD_HUI))["visa-VN"]
    assert "pas de visa" in t["texte"]
    assert "14 j" in t["texte"]                 # Hanoï 7 + Phu Quoc 7


def test_vietnam_au_dela_du_seuil_e_visa():
    itin = [{"destination": "Hanoï", "jours": 50, "code_pays": "VN"}]
    t = par_id(avant_de_partir(itin, DEPART, AUJOURD_HUI))["visa-VN"]
    assert "e-visa" in t["texte"]
    assert t["lien"] == FORMALITES["VN"]["visa_lien"]
    assert t["quand"] == DEPART - timedelta(days=30)


def test_cambodge_visa_toujours_requis():
    t = par_id(avant_de_partir(VIETNAM_CAMBODGE, DEPART, AUJOURD_HUI))["visa-KH"]
    assert "evisa.gov.kh" in t["lien"]
    assert t["quand"] == DEPART - timedelta(days=30)


def test_assurance_obligatoire_signalee():
    t = par_id(avant_de_partir(VIETNAM_CAMBODGE, DEPART, AUJOURD_HUI))["assurance"]
    assert "obligatoire au Cambodge" in t["texte"]


def test_pays_hors_table_renvoie_vers_france_diplomatie():
    itin = [{"destination": "Kyoto", "jours": 10, "code_pays": "JP"}]
    t = par_id(avant_de_partir(itin, DEPART, AUJOURD_HUI))
    assert "Kyoto" in t["formalites-JP"]["texte"]
    assert "diplomatie.gouv.fr" in t["formalites-JP"]["lien"]
    assert "passeport" in t and "vaccins" in t


def test_pays_inconnu_sans_code():
    itin = [{"destination": "Atlantide", "jours": 5, "code_pays": None}]
    t = par_id(avant_de_partir(itin, DEPART, AUJOURD_HUI))
    assert "formalites-Atlantide" in t


def test_infos_vieilles_de_plus_de_six_mois_a_reverifier():
    plus_tard = FORMALITES["KH"]["verifie_le"] + timedelta(days=181)
    t = par_id(avant_de_partir(VIETNAM_CAMBODGE, DEPART, plus_tard))
    assert "à revérifier" in t["visa-KH"]["texte"]
    assert "à revérifier" not in par_id(avant_de_partir(VIETNAM_CAMBODGE, DEPART, AUJOURD_HUI))["visa-KH"]["texte"]


def test_taches_triees_par_echeance():
    taches = avant_de_partir(VIETNAM_CAMBODGE, DEPART, AUJOURD_HUI)
    assert [t["quand"] for t in taches] == sorted(t["quand"] for t in taches)


def test_chaque_pays_de_la_table_a_ses_sources():
    for code, f in FORMALITES.items():
        assert f["entree"].startswith("https://") and f["sante"].startswith("https://"), code
        assert isinstance(f["verifie_le"], date), code


# --- Étape 2 : affichage dans la page ----------------------------------------------------
from valise import valise_en_html, paquet_vide, rendre_page, construire, HTML_SCRIPT, HTML_STYLE


def page_vn_kh():
    taches = avant_de_partir(VIETNAM_CAMBODGE, DEPART, AUJOURD_HUI)
    paquet = paquet_vide()
    paquet["Hygiène"]["trousse toilette"] = 1
    return valise_en_html({"Partagé": paquet, "Julien": paquet_vide()}, "Hanoï › Siem Reap › Phu Quoc",
                          18, set(), code="2027-01-10 X", depart=DEPART, taches=taches)


def test_rayon_avant_de_partir_en_tete_du_partage():
    html = page_vn_kh()
    partage = html.split('<section data-owner="Partagé">')[1].split("</section>")[0]
    assert partage.index("Avant de partir") < partage.index("trousse toilette")


def test_tache_cochable_avec_cle_stable_et_echeance():
    html = page_vn_kh()
    assert 'data-key="2027-01-10 X/Partagé/Avant de partir/visa-KH"' in html
    assert 'data-quand="2026-12-11"' in html
    assert "avant le 11/12" in html


def test_tache_avec_lien_vers_la_source():
    html = page_vn_kh()
    assert 'href="https://www.evisa.gov.kh/"' in html
    assert 'target="_blank"' in html


def test_tache_sans_boutons_de_bilan():
    html = page_vn_kh()
    rayon = html.split("Avant de partir</span>")[1].split("</details>")[0]
    assert "data-verdict" not in rayon and "data-objet" not in rayon


def test_page_sans_taches_inchangee():
    paquet = paquet_vide()
    paquet["Hygiène"]["trousse toilette"] = 1
    args = ({"Partagé": paquet}, "Rome", 5, set())
    assert valise_en_html(*args, taches=[]) == valise_en_html(*args)
    assert 'class="rayon avant"' not in valise_en_html(*args)


def test_rendre_page_calcule_les_taches():
    voyage = {"depart": DEPART, "itineraire": [dict(e, mois=1, activites=[]) for e in VIETNAM_CAMBODGE],
              "personnes": ["Julien", "Laetitia"], "conduit": False, "lessive": None}
    html = rendre_page(voyage, construire(voyage), aujourd_hui=AUJOURD_HUI)
    assert "Partagé/Avant de partir/vaccins" in html


def test_echeance_depassee_marquee_par_le_script():
    assert "retard" in HTML_SCRIPT and "retard" in HTML_STYLE


def test_mode_bilan_masque_le_rayon_avant_de_partir():
    assert "body.mode-bilan details.avant" in HTML_STYLE
