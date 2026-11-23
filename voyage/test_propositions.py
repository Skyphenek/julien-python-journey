"""Tests des Propositions : créneaux libres, passages, validation, règles de la page."""
import json
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pytest
from a_voir import SCRIPT_A_VOIR
from programme import SCRIPT_PROGRAMME
from propositions import (SCRIPT_PROPOSITIONS, SCRIPT_REGLES_PROPOSITIONS, STYLE_PROPOSITIONS, a_chercher, creneaux,
                          jours_du_voyage, passage_du, valider_proposition, visibles)
from pwa import SCRIPT_PRECHARGEMENT
from valise import VERSION_PAGE, construire, rendre_page

J = lambda n: date(2026, 12, n)
MARRAKECH = {"depart": J(10), "itineraire": [{"destination": "Marrakech", "jours": 4}]}


def resa(genre, titre, jour, heure="", jour_fin=None, heure_fin="", lieu=""):
    return {"type": genre, "titre": titre, "jour": jour, "heure": heure, "jour_fin": jour_fin,
            "heure_fin": heure_fin, "lieu": lieu}


RESAS = [resa("vol", "AF1276", J(10), "12:40", None, "15:05"),
         resa("hotel", "Dar Baraka", J(10), "14:00", J(11), "12:00", "Bab Doukkala"),
         resa("resto", "Terrasse des épices", J(10), "19:30"),
         resa("activite", "Désert d'Agafay", J(11)),
         resa("hotel", "Agafay palm", J(11), "15:00", J(13), "11:00"),
         resa("activite", "Tombeaux saadiens", J(13)),
         resa("hotel", "Bab Akoul", J(13), "12:00", J(14), "12:00"),
         resa("vol", "AF1077", J(14), "13:05", None, "17:25")]


def vus(voyage, reservations):
    return [(c["id"], c["debut"], c["fin"], c["ancre"]) for c in creneaux(voyage, reservations)]


def test_creneaux_de_marrakech():
    assert vus(MARRAKECH, RESAS) == [
        ("2026-12-10-apres-midi", "16:35", "19:30", "Dar Baraka"),
        ("2026-12-11-matin", "09:00", "12:00", "Dar Baraka"),
        ("2026-12-11-apres-midi", "15:00", "18:00", "Agafay palm"),
        ("2026-12-11-soir", "18:00", "22:30", "Agafay palm"),
        ("2026-12-12-matin", "09:00", "13:00", "Agafay palm"),
        ("2026-12-12-apres-midi", "13:00", "18:00", "Agafay palm"),
        ("2026-12-12-soir", "18:00", "22:30", "Agafay palm"),
        ("2026-12-13-matin", "09:00", "11:00", "Agafay palm"),
        ("2026-12-13-apres-midi", "12:00", "18:00", "Bab Akoul"),
        ("2026-12-13-soir", "18:00", "22:30", "Bab Akoul")]


def test_creneau_porte_adresse_et_etape():
    c = creneaux(MARRAKECH, RESAS)[0]
    assert (c["jour"], c["periode"], c["adresse"], c["destination"], c["rang"]) == (
        J(10), "après-midi", "Bab Doukkala", "Marrakech", 1)


def test_jours_prolonges_par_le_retour():
    assert jours_du_voyage(MARRAKECH, RESAS) == [J(n) for n in range(10, 15)]
    assert jours_du_voyage(MARRAKECH, []) == [J(n) for n in range(10, 14)]


def test_vol_de_nuit_escale_et_changement_d_etape():
    d = lambda n: date(2027, 1, n)
    voyage = {"depart": d(15), "itineraire": [{"destination": "Hanoï", "jours": 3}, {"destination": "Ha Long", "jours": 2}]}
    resas = [resa("vol", "A", d(15), "21:00", d(16), "05:00"), resa("vol", "B", d(16), "07:00", None, "16:00"),
             resa("hotel", "H1", d(16), "", d(18)), resa("transport", "bus", d(18), "08:00", None, "11:00"),
             resa("hotel", "H2", d(18), "14:00", d(19)), resa("vol", "C", d(19), "20:00", d(20), "06:00")]
    v = vus(voyage, resas)
    assert v[0] == ("2027-01-16-apres-midi", "17:30", "22:30", "H1")     # rien pendant l'escale ; 30 min isolées rattachées
    assert ("2027-01-18-apres-midi", "14:00", "18:00", "H2") in v and not any(x[0] == "2027-01-18-matin" for x in v)
    assert v[-1] == ("2027-01-19-apres-midi", "13:00", "17:00", "H2")     # 3 h avant le vol


def test_activite_avec_heure_coupe_la_journee():
    v = vus(MARRAKECH, RESAS + [resa("activite", "Cours de cuisine", J(12), "10:30", None, "12:00")])
    assert [x[1:3] for x in v if x[0].startswith("2026-12-12")] == [("09:00", "10:30"), ("12:00", "18:00"), ("18:00", "22:30")]


def test_deux_creneaux_de_la_meme_periode():
    v = vus(MARRAKECH, RESAS + [resa("activite", "Thé", J(12), "15:00", None, "16:00")])
    assert [x[0] for x in v if "2026-12-12-apres" in x[0]] == ["2026-12-12-apres-midi", "2026-12-12-apres-midi-2"]


def test_vol_interieur_sans_heure_prend_la_journee():
    v = vus(MARRAKECH, RESAS + [resa("transport", "bus", J(12))])
    assert not any(x[0].startswith("2026-12-12") for x in v)


def test_sans_reservation_ni_itineraire():
    assert vus(MARRAKECH, [])[0] == ("2026-12-10-apres-midi", "15:00", "18:00", "Marrakech")
    assert creneaux({"depart": J(10), "itineraire": []}, []) == []


JOURS = [J(n) for n in range(10, 15)]


@pytest.mark.parametrize("jour, attendu", [
    (date(2026, 11, 9), None), (date(2026, 11, 10), "J-30"), (date(2026, 11, 25), "J-30"), (date(2026, 11, 26), "J-14"), (date(2026, 12, 2), "J-14"), (J(3), "J-7"),
    (J(7), "J-7"), (J(8), "J-2"), (J(9), "J-2"), (J(10), "soir-2026-12-10"), (J(13), "soir-2026-12-13"),
    (J(14), None), (J(20), None)])
def test_passage_du(jour, attendu):
    assert passage_du(JOURS, set(), jour) == attendu


def test_passage_rate_repris_et_fait_pas_refait():
    assert passage_du(JOURS, {"J-14"}, date(2026, 11, 27)) is None
    assert passage_du(JOURS, {"J-14"}, J(4)) == "J-7"                # J-7 raté le 3 : repris le 4
    assert passage_du(JOURS, set(), J(8)) == "J-2"                    # les paliers sautés ne reviennent pas
    assert passage_du(JOURS, {"J-30"}, date(2026, 11, 25)) is None
    assert passage_du(JOURS, {"J-30"}, date(2026, 11, 26)) == "J-14"  # un mois avant, puis 2 semaines avant


def fiche(creneau="2026-12-11-matin", ancre="Dar Baraka", etat="proposee"):
    return {"id": "prop-1", "creneau": creneau, "ancre": ancre, "etat": etat}


def test_visibles_suit_le_programme():
    c = creneaux(MARRAKECH, RESAS)
    assert visibles([fiche()], c) == [fiche()]
    assert visibles([fiche(etat="ecartee")], c) == []
    assert visibles([fiche(ancre="Autre hôtel")], c) == []             # hôtel changé
    assert visibles([fiche(creneau="2026-12-14-matin")], c) == []      # créneau disparu


def test_a_chercher_places_et_soir():
    c = creneaux(MARRAKECH, RESAS)
    places = {x["id"]: x["places"] for x in a_chercher(c, [fiche()], "J-7", J(3))}
    assert places["2026-12-11-matin"] == 3 and places["2026-12-12-soir"] == 4 and len(places) == 10
    assert "2026-12-11-matin" not in {x["id"] for x in a_chercher(c, [fiche()] * 4, "J-7", J(3))}
    assert {x["jour"] for x in a_chercher(c, [], "soir-2026-12-11", J(11))} == {J(12)}


CORPS = {"titre": " Dar el  Bacha ", "pourquoi": "Palais-musée avant Agafay.", "genre": "voir", "reservation": "non",
         "horaires": "10 h à 18 h, fermé le lundi", "source": "https://fnm.ma/x", "lien": "https://fnm.ma/x"}


def test_proposition_valide():
    p = valider_proposition(CORPS)
    assert p["titre"] == "Dar el Bacha" and p["prix"] == "" and p["genre"] == "voir"
    sans = valider_proposition({"titre": "Dromadaire", "pourquoi": "Au couchant.", "genre": "faire",
                                "reservation": "a-demander", "a_confirmer": "À demander au camp : prix, durée"})
    assert sans["source"] == ""


@pytest.mark.parametrize("champs", [
    {"titre": ""}, {"titre": "x" * 201}, {"titre": 3}, {"pourquoi": ""}, {"genre": "manger"}, {"reservation": "peut-être"},
    {"source": ""}, {"prix": "60 MAD", "horaires": "", "source": ""}, {"source": "", "horaires": "", "a_confirmer": ""},
    {"lien": "javascript:alert(1)"}, {"source": "ftp://x"}, {"trajet": "x" * 101}])
def test_proposition_refusee(champs):
    with pytest.raises(ValueError):
        valider_proposition({**CORPS, **champs})


def test_proposition_pas_un_objet():
    with pytest.raises(ValueError):
        valider_proposition([CORPS])


def _node(appels):
    if not shutil.which("node"):
        pytest.skip("node absent")
    code = SCRIPT_REGLES_PROPOSITIONS + "\nconsole.log(JSON.stringify([" + ",".join(appels) + "]));"
    return json.loads(subprocess.run(["node", "-e", code], capture_output=True, text=True, check=True).stdout)


def test_position_des_lignes():
    assert _node(["positionLigne(['12:00', '15:00'], '09:00')", "positionLigne(['12:00', '15:00'], '15:00')",
                  "positionLigne(['12:00', '15:00', ''], '18:00')", "positionLigne(['', ''], '09:00')",
                  "positionLigne([], '09:00')", "positionLigne(['', '19:30'], '16:35')"]) == [0, 2, 2, 0, 0, 1]


def test_deux_idees_montrees_le_reste_en_reserve():
    ids = "[{id: 'a'}, {id: 'b'}, {id: 'c'}, {id: 'd'}]"
    vus = lambda ecartees: _node([f"montrees({ids}, {ecartees}).map(function (p) {{ return p.id; }})"])[0]
    assert vus("{}") == ["a", "b"]
    assert vus("{a: 1}") == ["a", "b", "c"]                       # écartée : sa place reste (Annuler), la suivante arrive
    assert vus("{a: 1, b: 1, c: 1}") == ["a", "b", "c", "d"]


def test_etats_en_attente_de_reseau():
    liste = "[{id: 'prop-a'}, {id: 'prop-b'}]"
    file = ("[{cle: 'prop-etat:prop-a', corps: {etat: 'gardee'}}, {cle: 'prop-etat:prop-b', corps: {etat: 'proposee'}},"
            " {cle: 'envie:prop-b', corps: {}}, {}]")
    assert _node([f"apresFile({liste}, {file}).map(function (p) {{ return p.id; }})"]) == [["prop-b"]]


def test_script_propositions():
    for morceau in ("'api/propositions/'", "'prop-etat:'", "'envie:'", "'resa:'", "envoyerOuGarder", "textContent",
                    "aria-expanded", "X-Valise-Vite", "propositions-changees", "a-voir-a-recharger",
                    "programme-a-recharger", "file-videe", "Annuler"):
        assert morceau in SCRIPT_PROPOSITIONS
    assert "innerHTML" not in SCRIPT_PROPOSITIONS and "checkbox" not in SCRIPT_PROPOSITIONS
    assert "min-height: 44px" in STYLE_PROPOSITIONS and "dashed" in STYLE_PROPOSITIONS
    assert "window.Propositions" in SCRIPT_PROGRAMME and "propositions-changees" in SCRIPT_PROGRAMME
    assert "a-voir-a-recharger" in SCRIPT_A_VOIR
    assert "'api/propositions/'" in SCRIPT_PRECHARGEMENT


def test_propositions_avant_le_programme_dans_la_page():
    voyage = {"depart": J(10), "personnes": ["Julien"], "conduit": False, "lessive": None,
              "itineraire": [{"destination": "Marrakech", "jours": 4, "mois": 12, "activites": [], "normales": None}]}
    html = rendre_page(voyage, construire(voyage))
    assert STYLE_PROPOSITIONS in html and VERSION_PAGE >= 68
    assert html.index(SCRIPT_PROPOSITIONS) < html.index(SCRIPT_PROGRAMME)


def test_scripts_syntaxiquement_valides(tmp_path):
    if not shutil.which("node"):
        pytest.skip("node absent")
    fichier = tmp_path / "p.js"
    fichier.write_text('const VOYAGE="x";\n' + SCRIPT_PROPOSITIONS + SCRIPT_PROGRAMME)
    r = subprocess.run(["node", "--check", str(fichier)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
