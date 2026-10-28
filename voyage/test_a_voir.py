"""Tests de « 💡 À voir » (rubrique Programme) : la liste d'envies par étape, les suggestions
tirées de Wikivoyage, et le passage d'un lieu dans le Programme."""
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pytest
from db import connecter, enregistrer_voyage, remplacer_voyage, enregistrer_a_voir, lire_a_voir, supprimer_a_voir
from serveur import creer_app
from valise import construire, rendre_page, VERSION_PAGE
from a_voir import valider_a_voir, suggestions_depuis_wikitext, SCRIPT_A_VOIR
from programme import SCRIPT_PROGRAMME
from pwa import SCRIPT_PRECHARGEMENT

CODE = "2027-01-15 Hanoï"
ITINERAIRE = [{"destination": "Hanoï", "jours": 3}, {"destination": "Ha Long", "jours": 2}]

WIKITEXTE_FR = """
== Voir ==
* {{voir | nom=Đông Xuân | alt= | url= | adresse= | lat=21.038 | long=105.849
| description=un des plus grands marchés de la ville, situé dans la [[vieille ville]] avec ses '''stands'''.}}
* {{Voir | nom=La Maison Centrale | adresse=1 Hoa Lo, Hoan Kiem | url=http://hoalo.vn
| description=: prison française de Hanoi.<ref>source</ref> {{Prix|30 000 ₫}}}}
* {{voir | nom=Đông Xuân | description=doublon}}
== Faire ==
* {{faire | nom=Théâtre de marionnettes sur l'eau | adresse=57b Dinh Tien Hoang | description=[[Spectacle|spectacle]] traditionnel}}
* {{dormir | nom=Un hôtel | description=pas un lieu à voir}}
* {{voir | nom= | description=sans nom : ignoré}}
"""
WIKITEXTE_EN = "{{see | name=Temple of Literature | address=58 Quoc Tu Giam | content=Confucian temple, 1070.}}"


def envie(**champs):
    base = {"id": "e1f2a3b4-0001", "voyage": CODE, "destination": "Hanoï", "rang": 1, "nom": "Văn Miếu",
            "adresse": "58 Quốc Tử Giám", "note": "Temple de la Littérature", "lien": "", "genre": "voir",
            "fait": False, "prevu": None}
    return {**base, **champs}


# --- Suggestions Wikivoyage (le téléphone télécharge, le serveur lit) ---

def test_suggestions_voir_et_faire_nettoyees():
    s = suggestions_depuis_wikitext(WIKITEXTE_FR, "Hanoi", "fr")
    assert [x["nom"] for x in s] == ["Đông Xuân", "La Maison Centrale", "Théâtre de marionnettes sur l'eau"]
    assert [x["genre"] for x in s] == ["voir", "voir", "faire"]
    marche, prison, marionnettes = s
    assert marche["note"] == "un des plus grands marchés de la ville, situé dans la vieille ville avec ses stands."
    assert marche["lien"] == "https://fr.wikivoyage.org/wiki/Hanoi"           # pas d'url : la page du guide
    assert prison["note"] == "prison française de Hanoi."                      # sans ref, ni modèle, ni « : »
    assert prison["lien"] == "http://hoalo.vn" and prison["adresse"] == "1 Hoa Lo, Hoan Kiem"
    assert marionnettes["note"] == "spectacle traditionnel"


def test_suggestions_en_anglais():
    s = suggestions_depuis_wikitext(WIKITEXTE_EN, "Hanoi", "en")
    assert s == [{"nom": "Temple of Literature", "adresse": "58 Quoc Tu Giam", "note": "Confucian temple, 1070.",
                  "lien": "https://en.wikivoyage.org/wiki/Hanoi", "genre": "voir"}]


def test_suggestions_texte_farfelu():
    assert suggestions_depuis_wikitext("{{voir | nom=x", "P", "fr") == []      # modèle jamais fermé
    assert suggestions_depuis_wikitext("", "P", "fr") == []


# --- Validation ---

def test_envie_valide():
    e = valider_a_voir(envie(prevu="2027-01-16"))
    assert e["prevu"] == date(2027, 1, 16) and e["fait"] is False


@pytest.mark.parametrize("champs", [
    {"id": "court"}, {"nom": " "}, {"nom": "x" * 201}, {"rang": 0}, {"rang": "1"}, {"genre": "dormir"},
    {"fait": "oui"}, {"lien": "javascript:x"}, {"note": "x" * 1001}, {"prevu": "16/01/2027"}, {"destination": ""},
])
def test_envie_invalide(champs):
    with pytest.raises(ValueError):
        valider_a_voir(envie(**champs))


# --- Base et API ---

@pytest.fixture
def conn():
    c = connecter("valise_test")
    with c.cursor() as cur:
        cur.execute("TRUNCATE voyages, a_voir, reservations CASCADE")
    c.commit()
    enregistrer_voyage(c, CODE, "Hanoï", date(2027, 1, 15), ["Julien", "Laetitia"], ITINERAIRE, {})
    yield c
    c.close()


def test_envie_enregistree_modifiee_supprimee(conn):
    enregistrer_a_voir(conn, valider_a_voir(envie()))
    enregistrer_a_voir(conn, valider_a_voir(envie(fait=True)))                       # même id : mise à jour
    enregistrer_a_voir(conn, valider_a_voir(envie(id="e1f2a3b4-0002", nom="Hồ Gươm")))
    liste = lire_a_voir(conn, CODE)
    assert [(e["nom"], e["fait"]) for e in liste] == [("Văn Miếu", True), ("Hồ Gươm", False)]
    supprimer_a_voir(conn, CODE, "e1f2a3b4-0001")
    assert [e["nom"] for e in lire_a_voir(conn, CODE)] == ["Hồ Gươm"]


def test_envies_suivent_un_voyage_modifie(conn):
    enregistrer_voyage(conn, "2027-01-16 Hanoï", "Hanoï", date(2027, 1, 16), ["Julien"], ITINERAIRE, {})
    enregistrer_a_voir(conn, valider_a_voir(envie()))
    remplacer_voyage(conn, CODE, "2027-01-16 Hanoï")
    assert lire_a_voir(conn, "2027-01-16 Hanoï")[0]["nom"] == "Văn Miếu"


@pytest.fixture
def client(conn):
    return creer_app("valise_test", secret="").test_client()


def test_api_a_voir(client):
    assert client.post("/api/a-voir", json=envie(prevu="2027-01-16")).status_code == 200
    liste = client.get(f"/api/a-voir/{CODE}").get_json()
    assert liste[0]["nom"] == "Văn Miếu" and liste[0]["prevu"] == "2027-01-16"
    assert client.post("/api/a-voir", json=envie(rang=0)).status_code == 400
    assert client.post("/api/a-voir", json=envie(voyage="inconnu")).status_code == 404
    assert client.delete(f"/api/a-voir/{CODE}/e1f2a3b4-0001").status_code == 200
    assert client.get(f"/api/a-voir/{CODE}").get_json() == []


def test_api_suggestions(client):
    r = client.post("/api/a-voir/suggestions", json={"pages": [
        {"langue": "fr", "titre": "Hanoi", "texte": WIKITEXTE_FR},
        {"langue": "en", "titre": "Hanoi", "texte": WIKITEXTE_EN}]})
    noms = [s["nom"] for s in r.get_json()["suggestions"]]
    assert noms == ["Đông Xuân", "La Maison Centrale", "Théâtre de marionnettes sur l'eau", "Temple of Literature"]
    assert client.post("/api/a-voir/suggestions", json={"pages": [{"langue": "de", "titre": "x", "texte": ""}]}
                       ).status_code == 400
    assert client.post("/api/a-voir/suggestions", json={}).status_code == 400


# --- Page ---

def page():
    voyage = {"depart": date(2027, 1, 15), "personnes": ["Julien"], "conduit": False, "lessive": None,
              "itineraire": [dict(e, mois=1, activites=[], normales=None, latitude=21.03, longitude=105.85)
                             for e in ITINERAIRE]}
    return rendre_page(voyage, construire(voyage))


def test_a_voir_dans_le_programme():
    html = page()
    prog = html.split('<div class="rubrique" data-rubrique="programme"')[1].split('<div class="rubrique"')[0]
    assert prog.index('<div class="programme"') < prog.index('<div class="info a-voir"')
    assert '"destination": "Ha Long", "rang": 1, "du": "2027-01-18", "au": "2027-01-19", "lat": 21.03' in prog
    assert SCRIPT_A_VOIR in html
    sur_place = html.split('<div class="rubrique" data-rubrique="sur-place"')[1].split('<div class="rubrique"')[0]
    assert "Bientôt" not in sur_place
    assert VERSION_PAGE >= 19


def test_script_a_voir():
    for morceau in ("api/a-voir/", "api/a-voir/suggestions", "wikivoyage.org/w/api.php", "origin=*",
                    "envoyerOuGarder", "'api/reservations'", "programme-a-recharger", "textContent", "Wikivoyage"):
        assert morceau in SCRIPT_A_VOIR
    assert "innerHTML" not in SCRIPT_A_VOIR
    assert "Object.assign({}, modifiee, { voyage: VOYAGE })" in SCRIPT_A_VOIR   # la liste lue n'a pas le voyage
    assert "type = 'checkbox'" not in SCRIPT_A_VOIR          # les cases de la valise comptent toutes les checkbox
    assert "programme-a-recharger" in SCRIPT_PROGRAMME
    assert "'api/a-voir/'" in SCRIPT_PRECHARGEMENT


def test_script_a_voir_syntaxiquement_valide(tmp_path):
    if shutil.which("node") is None:
        pytest.skip("Node absent")
    fichier = tmp_path / "a_voir.js"
    fichier.write_text('const VOYAGE="x", DEPART="2027-01-15", FIN="2027-01-19";\n' + SCRIPT_A_VOIR)
    resultat = subprocess.run(["node", "--check", str(fichier)], capture_output=True, text=True)
    assert resultat.returncode == 0, resultat.stderr
