"""Tests de sortir.py : validation, anti-doublon, avis, tirage du week-end, rappels (logique pure)."""
import sys
from datetime import date, timedelta
from pathlib import Path
from random import Random
sys.path.insert(0, str(Path(__file__).parent))

import pytest
from sortir import valider_sortie, cle_titre, cle_lien, doublon, apres_avis, tirer_weekend, rappels

J = date(2026, 11, 13)          # un vendredi


def s(id_, titre="Idée", etat="envie", type_="balade", budget="gratuit", fin=None, le=None, **k):
    return {"id": id_, "titre": titre, "etat": etat, "type": type_, "budget": budget, "debut": None, "fin": fin,
            "le": le, "lien": "", "avis_julien": "oui", "avis_laetitia": "oui", **k}


def test_valider_minimal_et_source():
    v = valider_sortie({"titre": "  Refuge des Fondus ", "source": "julien"}, J)
    assert v["titre"] == "Refuge des Fondus" and v["etat"] == "a-trier"
    assert v["avis_julien"] == "oui" and v["avis_laetitia"] is None          # ajout à la main = son « ça me tente »
    assert valider_sortie({"titre": "X", "source": "routine"}, J)["avis_julien"] is None


@pytest.mark.parametrize("modif", [{"titre": ""}, {"titre": "x" * 201}, {"type": "piscine"}, {"budget": "cher"},
                                   {"reservation": "peut-etre"}, {"lien": "ftp://x"}, {"source": "chat"},
                                   {"fin": "2026-13-01"}, {"debut": "2026-12-10", "fin": "2026-12-01"}])
def test_valider_refuse(modif):
    with pytest.raises(ValueError):
        valider_sortie({"titre": "X", "source": "routine", **modif}, J)


def test_cles_de_doublon():
    assert cle_titre("Le Refuge des Fondus !") == cle_titre("refuge  des fondus")
    assert cle_lien("https://www.x.fr/expo/?utm=1") == cle_lien("http://www.x.fr/expo")
    existantes = [s("a", "Atelier cosmétiques en duo chez Aroma-Zone", etat="ecartee", lien="https://aroma-zone.com/atelier")]
    assert doublon({"titre": "atelier cosmetiques en duo chez aroma zone", "lien": ""}, existantes) == "a"
    assert doublon({"titre": "Autre", "lien": "https://aroma-zone.com/atelier/"}, existantes) == "a"
    assert doublon({"titre": "Autre", "lien": ""}, existantes) is None


def test_doublon_domaine_nu_et_titres_vides():
    nus = [s("w", "Atelier poterie", lien="https://wecandoo.fr/")]
    assert doublon({"titre": "Escape game", "lien": "https://wecandoo.fr/"}, nus) is None
    assert doublon({"titre": "Atelier poterie", "lien": ""}, nus) == "w"
    assert doublon({"titre": "Le la les !", "lien": ""}, [s("v", "De du")]) is None


def test_avis():
    x = s("a", etat="a-trier", avis_julien="oui", avis_laetitia=None)
    assert apres_avis(x, "laetitia", "oui")["etat"] == "envie"
    assert apres_avis(x, "laetitia", "non")["etat"] == "ecartee"
    assert apres_avis(s("b", etat="a-trier", avis_julien=None, avis_laetitia=None), "julien", "oui")["etat"] == "a-trier"
    with pytest.raises(ValueError):
        apres_avis(x, "gaia", "oui")


def test_annuler_son_avis():
    x = s("a", etat="a-trier", avis_julien="oui", avis_laetitia=None)
    assert apres_avis(apres_avis(x, "laetitia", "oui"), "laetitia", None)["etat"] == "a-trier"
    assert apres_avis(apres_avis(x, "laetitia", "non"), "laetitia", None) == {**x, "avis_laetitia": None}
    assert apres_avis(s("p", etat="prevue"), "julien", None)["etat"] == "prevue"


@pytest.mark.parametrize("etat", ["envie", "faite"])
def test_bof_tardif_n_ecarte_pas(etat):
    s_ = apres_avis(s("a", etat=etat, avis_julien="oui", avis_laetitia="oui"), "julien", "non")
    assert s_["etat"] == etat and s_["avis_julien"] == "non"


def test_tirage_priorite_fin_proche_une_premium_types_varies():
    envies = [s("fin", type_="expo", fin=J + timedelta(days=10)), s("p1", type_="concert", budget="premium"),
              s("p2", type_="theatre", budget="premium"), s("b1", type_="balade"), s("b2", type_="balade"),
              s("faite", etat="faite")]
    for graine in range(30):
        t = tirer_weekend(envies, J, Random(graine))
        ids = [x["id"] for x in t]
        assert 2 <= len(t) <= 3 and ids[0] == "fin" and "faite" not in ids
        assert sum(x["budget"] == "premium" for x in t) <= 1
        assert len({x["type"] for x in t}) == len(t)


def test_tirage_types_absents_ne_se_bloquent_pas():
    sans_type = [s(f"n{i}", type_=None) for i in range(3)]
    assert len(tirer_weekend(sans_type, J, Random(1))) == 3


def test_tirage_ignore_fin_passee_et_rend_ce_qu_il_peut():
    assert tirer_weekend([s("vieux", fin=J - timedelta(days=1))], J, Random(1)) == []
    assert [x["id"] for x in tirer_weekend([s("seul")], J, Random(1))] == ["seul"]


def test_rappels():
    sorties = [s("fin", fin=J + timedelta(days=5)), s("loin", fin=J + timedelta(days=20)),
               s("prevue", etat="prevue", le=J + timedelta(days=1)), s("passee", etat="prevue", le=J - timedelta(days=2))]
    r = rappels(sorties, J)
    assert [x["id"] for x in r["finissent"]] == ["fin"] and [x["id"] for x in r["prevues"]] == ["prevue"]
    assert r["weekend"] is True and rappels(sorties, J - timedelta(days=4))["weekend"] is False


def test_page_sortir():
    from sortir import sortir_en_html
    html = sortir_en_html()
    assert "<title>Sortir · Casa Binomerie</title>" in html and 'data-hub="sortir" class="actif"' in html
    for v in ("a-trier", "envies", "faites"):
        assert f'data-vue="{v}"' in html
    for f in ("function vueATrier", "function vueEnvies", "function vueFaites", "function tirage", "function quiSuisJe",
              "function ajouterIdee", "api/sorties", "casa-qui"):
        assert f in html, f
    marque = "afficher();   // l'API ne rend que l'id : on relit"
    assert marque in html and html.split(marque, 1)[1][:80].strip().startswith("return;")
    assert "X-Valise-Vite" not in html.split("function tirage()", 1)[1].split("function blocTirage", 1)[0]
    for mot in ("Bof", "Ça me tente", "Ce week-end ?", "On y va", "Plus envie", "+ Ajouter une idée",
                "Alors, c'était comment ?", "Rien à trier.", "Annuler", "Ajoutée",
                "Refusé par le serveur, la page a été remise à jour.", "Déjà dans la liste",
                "En attente de ", "Envie ! Partants tous les deux.", "Écartée.", "Finalement bof", "Tous"):
        assert mot in html, mot
    assert "innerHTML" not in html
    assert "function glisser" in html and "touch-action: pan-y" in html and "Lire la suite" in html
    assert "prefers-reduced-motion" in html and ".t-expo" in html and "function phrases" in html and "ul.details" in html
    assert "function filtrer" in html and "filtrer(enviesTriees(), zone)" in html and "function enAttente" in html
    assert "filtrer(pileATrier(d.sorties, qui, aujourdhui()), zone)" in html
    assert html.index("function pileATrier") < html.index("const LIB = JSON.parse")      # règles chargées avant la page
    from sortir import FIN_PROCHE
    assert f'"fin_proche": {FIN_PROCHE}' in html and "const FIN_PROCHE = JSON.parse" in html
    assert "<h1>Sortir</h1>" in html and 'class="popote"' not in html


# --- Les règles de la page, exécutées avec node (mêmes cas que les règles Python) ------------------------------

def _node(appels):
    """Exécute SCRIPT_REGLES_SORTIR puis chaque appel (expression JS) ; rend la liste des résultats."""
    import json, shutil, subprocess
    if not shutil.which("node"):
        pytest.skip("node absent")
    from sortir import SCRIPT_REGLES_SORTIR
    code = SCRIPT_REGLES_SORTIR + "\nconsole.log(JSON.stringify([" + ",".join(appels) + "]));"
    sortie = subprocess.run(["node", "-e", code], capture_output=True, text=True, check=True).stdout
    return json.loads(sortie)


def test_js_apres_avis_comme_python():
    import json
    cas = [(s("a", etat=e, avis_julien=aj, avis_laetitia=al), qui, avis)
           for e in ("a-trier", "envie", "ecartee", "prevue", "faite")
           for aj in (None, "oui", "non") for al in (None, "oui")
           for qui in ("julien", "laetitia") for avis in ("oui", "non", None)]
    js = _node([f"apresAvis({json.dumps(x)}, {json.dumps(q)}, {json.dumps(a)})" for x, q, a in cas])
    assert js == [apres_avis(x, q, a) for x, q, a in cas]


def test_js_pile_et_envies():
    import json
    jour = "2026-11-13"
    pile = [s("vieille", etat="a-trier", avis_julien=None, cree_le="2026-10-01"),
            s("recente", etat="a-trier", avis_julien=None, cree_le="2026-11-10"),
            s("finie", etat="a-trier", avis_julien=None, fin="2026-11-12", cree_le="2026-11-11"),
            s("jugee", etat="a-trier", avis_julien="oui", cree_le="2026-11-12"),
            s("envie", cree_le="2026-11-12")]
    envies = [s("loin", cree_le="2026-10-01"), s("neuve", cree_le="2026-11-10"),
              s("bientot", fin="2026-11-20"), s("tres-bientot", fin="2026-11-15"), s("passee", fin="2026-11-01"),
              s("prevue", etat="prevue", le="2026-11-21"), s("prevue-passee", etat="prevue", le="2026-11-01"),
              s("a-trier", etat="a-trier")]
    p, e = _node([f"pileATrier({json.dumps(pile)}, 'julien', '{jour}').map(function (x) {{ return x.id; }})",
                  f"enviesOrdonnees({json.dumps(envies)}, '{jour}', 15).map(function (x) {{ return x.id; }})"])
    assert p == ["recente", "vieille"]
    assert e == ["prevue", "tres-bientot", "bientot", "neuve", "loin", "passee"]


def test_js_phrases_et_glisse():
    r = _node(["phrases(\"Ouverture le 22/11 (jusqu'au 4 janvier). 180 chalets. ~25€/pers. Accès M1 Franklin-D.-Roosevelt. Fin\")",
               "phrases('Une seule phrase sans point')",
               "[sensGlisse(80, 400), sensGlisse(120, 400), sensGlisse(-120, 400), sensGlisse(100, 300), sensGlisse(-91, 300)]"])
    assert r[0] == ["Ouverture le 22/11 (jusqu'au 4 janvier)", "180 chalets", "~25€/pers", "Accès M1 Franklin-D.-Roosevelt", "Fin"]
    assert r[1] == ["Une seule phrase sans point"]
    assert r[2] == [None, "oui", "non", "oui", "non"]
