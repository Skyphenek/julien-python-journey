"""Tests de db.py — accès Postgres à l'état de la checklist."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pytest
from db import (connecter, obtenir_etat, enregistrer_coche,
                lire_normales, enregistrer_normales, publier_page, lire_page,
                enregistrer_voyage, lire_voyage, enregistrer_valise_objets, lire_valise_objets,
                enregistrer_retour, supprimer_retour, lire_retours,
                archiver_voyage, lire_historique, ajouter_regle, lire_regles, lister_voyages,
                enregistrer_passeport, lire_passeports, remplacer_voyage)
from valise import normales_avec_cache


@pytest.fixture
def conn():
    connexion = connecter("valise_test")
    with connexion.cursor() as cur:
        cur.execute("TRUNCATE etat_case, normales_climat, page_valise, voyages, valise_objets, retours, regles_perso, passeports")
    connexion.commit()
    yield connexion
    connexion.close()


def test_obtenir_etat_base_vide(conn):
    assert obtenir_etat(conn, "Hanoï") == {}


def test_enregistrer_coche_puis_lecture(conn):
    enregistrer_coche(conn, "Hanoï", "Julien", "Vêtements", "pantalons", True)
    assert obtenir_etat(conn, "Hanoï") == {"Hanoï/Julien/Vêtements/pantalons": True}


def test_enregistrer_coche_upsert_une_seule_ligne(conn):
    enregistrer_coche(conn, "Hanoï", "Julien", "Vêtements", "pantalons", True)
    enregistrer_coche(conn, "Hanoï", "Julien", "Vêtements", "pantalons", False)
    assert obtenir_etat(conn, "Hanoï") == {"Hanoï/Julien/Vêtements/pantalons": False}
    with conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM etat_case")
        assert cur.fetchone()[0] == 1


def test_obtenir_etat_filtre_par_voyage(conn):
    enregistrer_coche(conn, "Hanoï", "Julien", "Vêtements", "pantalons", True)
    enregistrer_coche(conn, "Paris", "Julien", "Vêtements", "manteau", True)
    assert obtenir_etat(conn, "Hanoï") == {"Hanoï/Julien/Vêtements/pantalons": True}



# --- Cache des normales climatiques ---

HANOI_JANV = {"tmin": 14.3, "tmax": 21.1, "jours_pluie": 10, "jours_forte_pluie": 3.4}
HANOI_JUIL = {"tmin": 26.8, "tmax": 33.0, "jours_pluie": 18, "jours_forte_pluie": 11.2}


def test_normales_absentes_du_cache(conn):
    assert lire_normales(conn, 21.03, 105.85, 1) is None


def test_enregistrer_puis_lire_normales(conn):
    enregistrer_normales(conn, 21.03, 105.85, {1: HANOI_JANV, 7: HANOI_JUIL})
    assert lire_normales(conn, 21.03, 105.85, 1) == HANOI_JANV
    assert lire_normales(conn, 21.03, 105.85, 7) == HANOI_JUIL


def test_cache_par_coordonnees_arrondies(conn):
    # Deux géocodages de "Hanoï" à quelques mètres près -> même ligne de cache
    enregistrer_normales(conn, 21.0285, 105.8542, {1: HANOI_JANV})
    assert lire_normales(conn, 21.03, 105.85, 1) == HANOI_JANV


def test_enregistrer_deux_fois_ne_duplique_pas(conn):
    enregistrer_normales(conn, 21.03, 105.85, {1: HANOI_JANV})
    enregistrer_normales(conn, 21.03, 105.85, {1: HANOI_JANV})
    with conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM normales_climat")
        assert cur.fetchone()[0] == 1


def test_normales_avec_cache_n_appelle_l_api_qu_une_fois(conn):
    appels = []
    def fausse_api(latitude, longitude):          # remplace l'API : compte les appels
        appels.append((latitude, longitude))
        return {1: HANOI_JANV, 7: HANOI_JUIL}

    assert normales_avec_cache(conn, 21.03, 105.85, 1, chercher=fausse_api) == HANOI_JANV
    assert normales_avec_cache(conn, 21.03, 105.85, 7, chercher=fausse_api) == HANOI_JUIL  # autre mois
    assert normales_avec_cache(conn, 21.03, 105.85, 1, chercher=fausse_api) == HANOI_JANV
    assert len(appels) == 1                       # 1 appel a rempli les 12 mois



# --- Page publiée en base (pour le serveur en ligne) ---

def test_lire_page_vide(conn):
    assert lire_page(conn) is None


def test_publier_remplace_la_page_precedente(conn):
    publier_page(conn, "<html>Tokyo</html>")
    publier_page(conn, "<html>Bangkok</html>")
    assert lire_page(conn) == "<html>Bangkok</html>"


def test_les_tests_ignorent_la_base_en_ligne(monkeypatch):
    # Garde-fou : même si DATABASE_URL pointe vers le cloud, "valise_test" reste locale
    monkeypatch.setenv("DATABASE_URL", "postgresql://pirate@exemple.invalid/prod")
    connexion = connecter("valise_test")
    assert connexion.info.dbname == "valise_test"
    connexion.close()



# --- Mémoire des voyages : identité + photo de la valise ---

from datetime import date

CODE = "2027-01-10 Tokyo › Bangkok"
ITINERAIRE = [{"destination": "Tokyo", "jours": 7, "mois": 1, "activites": ["ville"],
               "code_pays": "JP", "normales": {"tmin": 2.0, "tmax": 10.0, "jours_pluie": 5, "jours_forte_pluie": 1.5}}]


def test_enregistrer_puis_lire_voyage(conn):
    enregistrer_voyage(conn, CODE, "Tokyo › Bangkok", date(2027, 1, 10), ["Julien", "Laetitia"],
                       ITINERAIRE, {"froid": 7, "ville": 7})
    v = lire_voyage(conn, CODE)
    assert v["libelle"] == "Tokyo › Bangkok"
    assert v["depart"] == date(2027, 1, 10)
    assert v["personnes"] == ["Julien", "Laetitia"]
    assert v["itineraire"] == ITINERAIRE              # JSON aller-retour sans perte
    assert v["jours_types"] == {"froid": 7, "ville": 7}


def test_reenregistrer_un_voyage_le_met_a_jour(conn):
    enregistrer_voyage(conn, CODE, "Tokyo › Bangkok", date(2027, 1, 10), ["Julien"], ITINERAIRE, {})
    enregistrer_voyage(conn, CODE, "Tokyo › Bangkok", date(2027, 1, 10), ["Julien", "Laetitia"], ITINERAIRE, {})
    assert lire_voyage(conn, CODE)["personnes"] == ["Julien", "Laetitia"]
    with conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM voyages")
        assert cur.fetchone()[0] == 1


def test_photo_de_la_valise_remplacee_a_chaque_publication(conn):
    enregistrer_voyage(conn, CODE, "Tokyo › Bangkok", date(2027, 1, 10), ["Julien"], ITINERAIRE, {})
    enregistrer_valise_objets(conn, CODE, {"Julien": {"Vêtements": {"shorts": 3, "pull": 1}}})
    enregistrer_valise_objets(conn, CODE, {"Julien": {"Vêtements": {"shorts": 2}}})   # régénérée
    assert lire_valise_objets(conn, CODE) == {("Julien", "Vêtements", "shorts"): 2}



# --- Bilan de fin de voyage : les retours ---

import psycopg2


def _voyage(conn):
    enregistrer_voyage(conn, CODE, "Tokyo › Bangkok", date(2027, 1, 10), ["Julien"], ITINERAIRE, {})


def test_retour_enregistre_puis_lu(conn):
    _voyage(conn)
    enregistrer_retour(conn, CODE, "Julien", "t-shirts", "trop", quantite_utilisee=8)
    enregistrer_retour(conn, CODE, "Julien", "bouchons d'oreilles", "manque")
    assert lire_retours(conn, CODE) == [
        {"proprietaire": "Julien", "objet": "bouchons d'oreilles", "verdict": "manque", "quantite_utilisee": None},
        {"proprietaire": "Julien", "objet": "t-shirts", "verdict": "trop", "quantite_utilisee": 8},
    ]


def test_changer_d_avis_met_a_jour(conn):
    _voyage(conn)
    enregistrer_retour(conn, CODE, "Julien", "pull", "pas_servi")
    enregistrer_retour(conn, CODE, "Julien", "pull", "utile")
    assert [r["verdict"] for r in lire_retours(conn, CODE)] == ["utile"]


def test_supprimer_un_retour(conn):
    _voyage(conn)
    enregistrer_retour(conn, CODE, "Julien", "pull", "utile")
    supprimer_retour(conn, CODE, "Julien", "pull")
    assert lire_retours(conn, CODE) == []


def test_retour_sur_voyage_inconnu_refuse(conn):
    with pytest.raises(psycopg2.errors.ForeignKeyViolation):
        enregistrer_retour(conn, "1999-01-01 Atlantide", "Julien", "pull", "utile")
    conn.rollback()



# --- Session 3 : historique et règles "toujours" ---

def test_historique_du_plus_recent_au_plus_ancien_sans_archive_ni_courant(conn):
    for code, d in [("2025-01-01 Rome", date(2025, 1, 1)), ("2026-06-01 Lisbonne", date(2026, 6, 1)),
                    ("2026-09-01 Essai", date(2026, 9, 1)), ("2027-01-10 Tokyo", date(2027, 1, 10))]:
        enregistrer_voyage(conn, code, code[11:], d, ["Julien"], [], {"ville": 5})
    enregistrer_valise_objets(conn, "2026-06-01 Lisbonne", {"Julien": {"Vêtements": {"t-shirts": 6}}})
    enregistrer_retour(conn, "2026-06-01 Lisbonne", "Julien", "t-shirts", "trop", 3)
    archiver_voyage(conn, "2026-09-01 Essai")
    h = lire_historique(conn, exclure="2027-01-10 Tokyo")          # le voyage en cours n'est pas son propre passé
    assert [v["code"] for v in h] == ["2026-06-01 Lisbonne", "2025-01-01 Rome"]
    assert h[0]["objets"] == {("Julien", "Vêtements", "t-shirts"): 6}
    assert h[0]["retours"] == [{"proprietaire": "Julien", "objet": "t-shirts", "verdict": "trop", "quantite_utilisee": 3}]
    assert h[0]["jours_types"] == {"ville": 5}


def test_regles_toujours(conn):
    ajouter_regle(conn, "Julien", "Mots fléchés", "Divers", 1)
    ajouter_regle(conn, "Julien", "Mots fléchés", "Divers", 1)      # pas de doublon
    assert lire_regles(conn) == {"Julien": [{"objet": "Mots fléchés", "theme": "Divers", "quantite": 1}]}


# --- Étape 2 (météo J-7) : le voyage stocke tout ce qu'il faut pour être régénéré ---

def test_voyage_stocke_conduite_et_lessive(conn):
    enregistrer_voyage(conn, CODE, "Tokyo › Bangkok", date(2027, 1, 10), ["Julien"],
                       ITINERAIRE, {"ville": 7}, conduit=True, lessive=7)
    v = lire_voyage(conn, CODE)
    assert v["conduit"] is True
    assert v["lessive"] == 7


def test_voyage_ancien_format_valeurs_par_defaut(conn):
    # les voyages enregistrés avant l'étape 2 : pas de conduite, pas de lessive
    enregistrer_voyage(conn, CODE, "Tokyo › Bangkok", date(2027, 1, 10), ["Julien"], ITINERAIRE, {})
    v = lire_voyage(conn, CODE)
    assert v["conduit"] is False
    assert v["lessive"] is None


def test_voyage_relu_se_reconstruit(conn):
    # ce qui sort de la base suffit à construire() : c'est tout l'enjeu du bouton météo
    from valise import construire
    from valise import code_voyage
    code = code_voyage(date(2027, 1, 10), "Tokyo")          # ITINERAIRE n'a qu'une étape : Tokyo
    enregistrer_voyage(conn, code, "Tokyo", date(2027, 1, 10), ["Julien"],
                       ITINERAIRE, {"froid": 7, "ville": 7}, conduit=True, lessive=None)
    c = construire(lire_voyage(conn, code))
    assert c["code"] == code                                  # même voyage -> cases cochées gardées
    assert c["valise"]["Julien"]["Documents"]["permis"] == 1


# --- Une page par voyage (création en ligne, étape 1) ---

def test_une_page_par_voyage(conn):
    publier_page(conn, "<html>Rome</html>", cle="2026-12-30 Rome")
    publier_page(conn, "<html>Oslo</html>", cle="2026-11-01 Oslo")
    assert lire_page(conn, "2026-12-30 Rome") == "<html>Rome</html>"
    assert lire_page(conn, "2026-11-01 Oslo") == "<html>Oslo</html>"
    assert lire_page(conn, "2027-01-01 Inconnu") is None


def test_lister_voyages_a_venir_et_passes_sans_les_archives(conn):
    itin = lambda j: [{"destination": "X", "jours": j}]
    enregistrer_voyage(conn, "2027-05-01 Lisbonne", "Lisbonne", date(2027, 5, 1), ["Laetitia"], itin(4), {})
    enregistrer_voyage(conn, "2026-11-01 Oslo", "Oslo", date(2026, 11, 1), ["Julien", "Laetitia"], itin(5), {})
    enregistrer_voyage(conn, "2027-04-30 Essai", "Essai", date(2027, 4, 30), ["Julien"], itin(2), {})
    archiver_voyage(conn, "2027-04-30 Essai")
    v = lister_voyages(conn)
    assert [x["code"] for x in v] == ["2026-11-01 Oslo", "2027-05-01 Lisbonne"]     # par date, sans archive
    assert v[0] == {"code": "2026-11-01 Oslo", "libelle": "Oslo", "depart": date(2026, 11, 1),
                    "fin": date(2026, 11, 5), "personnes": ["Julien", "Laetitia"]}


def test_passeports_enregistres_puis_mis_a_jour(conn):
    from datetime import date
    assert lire_passeports(conn) == {}
    enregistrer_passeport(conn, "Julien", date(2027, 12, 17))
    enregistrer_passeport(conn, "Laetitia", date(2029, 6, 20))
    enregistrer_passeport(conn, "Julien", date(2037, 12, 1))          # renouvelé : on remplace
    assert lire_passeports(conn) == {"Julien": date(2037, 12, 1), "Laetitia": date(2029, 6, 20)}



def test_remplacer_voyage_deplace_cases_et_bilan_puis_archive(conn):
    from datetime import date
    for code in ("2027-01-10 Hanoï", "2027-01-12 Hanoï"):
        enregistrer_voyage(conn, code, "Hanoï", date(2027, 1, 10), ["Julien"], [{"jours": 5}], {})
    enregistrer_coche(conn, "2027-01-10 Hanoï", "Julien", "Vêtements", "pull", True)
    enregistrer_retour(conn, "2027-01-10 Hanoï", "Julien", "pull", "utile")
    remplacer_voyage(conn, "2027-01-10 Hanoï", "2027-01-12 Hanoï")
    assert obtenir_etat(conn, "2027-01-12 Hanoï") == {"2027-01-12 Hanoï/Julien/Vêtements/pull": True}
    assert obtenir_etat(conn, "2027-01-10 Hanoï") == {}
    assert [r["objet"] for r in lire_retours(conn, "2027-01-12 Hanoï")] == ["pull"]
    assert [v["code"] for v in lister_voyages(conn)] == ["2027-01-12 Hanoï"]      # l'ancien est archivé
