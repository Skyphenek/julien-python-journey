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
    assert {"passeport", "vaccins", "assurance", "ariane", "visa-KH", "e-arrival-KH", "usd-KH"} <= set(t)
    assert "visa-VN" not in t                    # 14 j au Vietnam : sous l'exemption, rien à faire


def test_passeport_valide_six_mois_apres_le_retour():
    t = par_id(avant_de_partir(VIETNAM_CAMBODGE, DEPART, AUJOURD_HUI))
    # retour le 27/01/2027 (18 jours) -> passeport valide au moins jusqu'au 27/07/2027
    assert "27/07/2027" in t["passeport"]["texte"]
    assert t["passeport"]["quand"] == DEPART - timedelta(days=60)


def test_vaccins_deux_mois_avant_avec_lien_sante():
    t = par_id(avant_de_partir(VIETNAM_CAMBODGE, DEPART, AUJOURD_HUI))["vaccins"]
    assert t["quand"] == DEPART - timedelta(days=60)
    assert "Vietnam" in t["texte"] and "Cambodge" in t["texte"]
    assert t["lien"] == FORMALITES["VN"]["page_sante"]


def test_vietnam_sans_visa_sous_le_seuil_compte_tous_les_jours_sur_place():
    assert "visa-VN" not in par_id(avant_de_partir(VIETNAM_CAMBODGE, DEPART, AUJOURD_HUI))    # 7 + 7 = 14 j
    itin = [dict(e, jours=23) for e in VIETNAM_CAMBODGE]                                    # 23 + 23 = 46 j > 45
    assert "visa-VN" in par_id(avant_de_partir(itin, DEPART, AUJOURD_HUI))


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
    itin = [{"destination": "Pékin", "jours": 10, "code_pays": "CN"}]
    t = par_id(avant_de_partir(itin, DEPART, AUJOURD_HUI))
    assert "Pékin" in t["formalites-CN"]["texte"] and "santé" in t["formalites-CN"]["texte"]
    assert "diplomatie.gouv.fr" in t["formalites-CN"]["lien"]
    assert "passeport" in t and "vaccins" not in t      # la tâche « vérifier » couvre la santé


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


def test_chaque_pays_de_la_table_est_complet():
    from valise import statut_ue
    for code, f in FORMALITES.items():
        assert f["entree"].startswith("https://") and f["page_sante"].startswith("https://"), code
        assert isinstance(f["verifie_le"], date), code
        assert f["passeport_mois"] in (0, 3, 5, 6), code
        assert f["sante"] in (None, "centre", "medecin"), code
        assert f["sans_visa_jusqua"] or f["visa"], code          # sans exemption, il faut dire quoi demander
        assert statut_ue(code) != "ue", code                     # UE / Schengen : pas de fiche
        for jours, id_, texte, lien in f["taches"]:
            assert lien is None or lien.startswith("https://"), (code, id_)


def test_au_moins_vingt_pays():
    assert len(FORMALITES) >= 20


# --- Étape 2 : affichage dans la page ----------------------------------------------------
from valise import valise_en_html, paquet_vide, rendre_page, construire, HTML_SCRIPT, HTML_STYLE


def page_vn_kh():
    taches = avant_de_partir(VIETNAM_CAMBODGE, DEPART, AUJOURD_HUI)
    paquet = paquet_vide()
    paquet["Hygiène"]["trousse toilette"] = 1
    return valise_en_html({"Partagé": paquet, "Julien": paquet_vide()}, "Hanoï › Siem Reap › Phu Quoc",
                          18, set(), code="2027-01-10 X", depart=DEPART, taches=taches)


def test_formalites_separees_de_la_valise():
    html = page_vn_kh()
    nav = html.split('<nav class="tabs">')[1].split("</nav>")[0]
    assert nav.find('<button data-owner="Partagé"') == 0          # Partagé en premier : l'onglet ouvert
    assert '<section data-owner="Avant de partir" class="avant">' in html
    partage = html.split('<section data-owner="Partagé">')[1].split("</section>")[0]
    assert "visa-KH" not in partage


def test_onglet_avant_exclu_de_la_progression_et_pas_ouvert_par_defaut():
    assert "section[data-owner]:not(.avant)" in HTML_SCRIPT
    assert "data-avant" in HTML_SCRIPT


def test_tache_cochable_avec_cle_stable_et_echeance():
    html = page_vn_kh()
    assert 'data-key="2027-01-10 X/Partagé/Avant de partir/visa-KH"' in html
    assert 'data-quand="2026-12-11"' in html
    assert '<span class="avant-le">avant le </span>11/12' in html


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


def test_mode_bilan_masque_l_onglet_avant_de_partir():
    assert 'body.mode-bilan [data-owner="Avant de partir"]' in HTML_STYLE



# --- Étape 3 : dates d'expiration des passeports ---------------------------------------
DEUX = ["Julien", "Laetitia"]


def tache_passeport(passeports, personnes=DEUX):
    taches = avant_de_partir(VIETNAM_CAMBODGE, DEPART, AUJOURD_HUI, passeports=passeports, personnes=personnes)
    return par_id(taches)["passeport"]


def test_passeports_ok_affiche_les_dates():
    t = tache_passeport({"Julien": date(2027, 12, 17), "Laetitia": date(2029, 6, 20)})
    assert t["texte"].startswith("Passeports OK")
    assert "Julien jusqu'au 17/12/2027" in t["texte"] and "Laetitia jusqu'au 20/06/2029" in t["texte"]
    assert "27/07/2027" in t["texte"]                       # le minimum exigé reste affiché


def test_passeport_trop_court_a_renouveler():
    t = tache_passeport({"Julien": date(2027, 5, 1), "Laetitia": date(2029, 6, 20)})
    assert t["texte"].startswith("Passeport à renouveler")
    assert "Julien" in t["texte"] and "01/05/2027" in t["texte"] and "renouveler" in t["texte"]
    assert "Laetitia" not in t["texte"]                     # seule l'alerte compte


def test_passeport_inconnu_pour_une_personne():
    t = tache_passeport({"Julien": date(2027, 12, 17)})
    assert "Laetitia" in t["texte"] and "date inconnue" in t["texte"]
    assert not t["texte"].startswith("Passeports OK")


def test_passeport_d_un_absent_ignore():
    t = tache_passeport({"Julien": date(2027, 12, 17), "Laetitia": date(2020, 1, 1)}, personnes=["Julien"])
    assert t["texte"].startswith("Passeports OK") and "Laetitia" not in t["texte"]


def test_sans_passeports_texte_generique():
    t = par_id(avant_de_partir(VIETNAM_CAMBODGE, DEPART, AUJOURD_HUI))["passeport"]
    assert t["texte"].startswith("Passeports valides au moins jusqu'au 27/07/2027")



# --- Règles par pays (États-Unis, Maroc, Royaume-Uni…) ----------------------------------
NEW_YORK = [{"destination": "New York", "jours": 7, "code_pays": "US"}]
ETE = date(2027, 7, 1)


def test_new_york_pas_de_vaccins_mais_esta():
    t = par_id(avant_de_partir(NEW_YORK, ETE, AUJOURD_HUI))
    assert "vaccins" not in t
    assert t["esta-US"]["lien"] == "https://esta.cbp.dhs.gov/"
    assert "visa-US" not in t                    # sous l'exemption : seul l'ESTA est à faire


def test_new_york_passeport_valide_pendant_le_sejour_suffit():
    # retour le 07/07/2027 ; le passeport de Julien expire le 17/12/2027 -> OK (règle 6 mois = faux ❌)
    t = par_id(avant_de_partir(NEW_YORK, ETE, AUJOURD_HUI, passeports={"Julien": date(2027, 12, 17)},
                               personnes=["Julien"]))["passeport"]
    assert t["texte"].startswith("Passeports OK") and "07/07/2027" in t["texte"]


def test_new_york_assurance_indispensable():
    t = par_id(avant_de_partir(NEW_YORK, ETE, AUJOURD_HUI))["assurance"]
    assert "soins très chers" in t["texte"]


def test_regle_passeport_la_plus_stricte_de_l_itineraire():
    itin = NEW_YORK + [{"destination": "Lima", "jours": 7, "code_pays": "PE"}]
    t = par_id(avant_de_partir(itin, ETE, AUJOURD_HUI))["passeport"]
    assert "14/01/2028" in t["texte"]                       # retour 14/07/2027 + 6 mois (Pérou)


def test_maroc_seulement_le_passeport():
    """Feedback 28/10/2026 : pas de vaccins, pas de « pas de visa », ni Ariane ni assurance au Maroc."""
    itin = [{"destination": "Marrakech", "jours": 5, "code_pays": "MA"}]
    assert set(par_id(avant_de_partir(itin, DEPART, AUJOURD_HUI))) == {"passeport"}


def test_assurance_seulement_si_elle_compte():
    japon = par_id(avant_de_partir([{"destination": "Tokyo", "jours": 10, "code_pays": "JP"}], DEPART, AUJOURD_HUI))
    assert "soins chers" in japon["assurance"]["texte"] and "carte bancaire" in japon["assurance"]["texte"]
    assert "assurance" not in par_id(avant_de_partir([{"destination": "Bangkok", "jours": 10, "code_pays": "TH"}],
                                                     DEPART, AUJOURD_HUI))


def test_centre_de_vaccination_l_emporte_et_note_affichee():
    itin = [{"destination": "Marrakech", "jours": 5, "code_pays": "MA"},
            {"destination": "Dakar", "jours": 5, "code_pays": "SN"}]
    t = par_id(avant_de_partir(itin, DEPART, AUJOURD_HUI))["vaccins"]
    assert t["quand"] == DEPART - timedelta(days=60)
    assert "centre de vaccinations" in t["texte"] and "fièvre jaune" in t["texte"]
    assert "Maroc" not in t["texte"] and "Sénégal" in t["texte"]


def test_royaume_uni_eta_et_ceam():
    itin = [{"destination": "Londres", "jours": 4, "code_pays": "GB"}]
    t = par_id(avant_de_partir(itin, DEPART, AUJOURD_HUI))
    assert "eta-GB" in t and "ceam-GB" in t and "vaccins" not in t


def test_thailande_au_dela_de_30_jours_signale_le_depassement():
    itin = [{"destination": "Bangkok", "jours": 35, "code_pays": "TH"}]
    t = par_id(avant_de_partir(itin, DEPART, AUJOURD_HUI))["visa-TH"]
    assert "dépasse" in t["texte"] and "30 j" in t["texte"]


def test_passeport_ok_jamais_en_retard():
    taches = avant_de_partir(VIETNAM_CAMBODGE, DEPART, AUJOURD_HUI, personnes=DEUX,
                             passeports={"Julien": date(2027, 12, 17), "Laetitia": date(2029, 6, 20)})
    assert par_id(taches)["passeport"]["ok"] is True
    html = valise_en_html({"Partagé": paquet_vide()}, "X", 18, set(), code="c", taches=taches)
    li = html.split("Partagé/Avant de partir/passeport")[0].rsplit("<li", 1)[1]
    assert "data-quand" not in li and 'class="tache ok"' in li


def test_page_arrive_deja_ouverte_sur_partage():
    """Pas de flash à l'ouverture : seul Partagé est visible avant même le JavaScript."""
    html = page_vn_kh()
    assert '<section data-owner="Partagé">' in html                       # visible
    assert '<section data-owner="Julien" hidden>' in html
    assert '<div class="rubrique" data-rubrique="avant" hidden>' in html
    assert '<button data-owner="Partagé" class="actif">' in html
    assert html.index('<section data-owner="Julien"') < html.index('<section data-owner="Avant de partir"')
    assert "s.hidden = " in HTML_SCRIPT                                    # les onglets basculent hidden
