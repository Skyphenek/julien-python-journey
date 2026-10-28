"""Tests de « 🎁 Souvenirs » : carnet de proches réutilisé, souvenirs du voyage, achat qui devient
une dépense partagée, idées par pays et règles de douane."""
import shutil
import subprocess
import sys
from datetime import date
from decimal import Decimal
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pytest
from db import (connecter, enregistrer_voyage, remplacer_voyage, lire_depenses, supprimer_depense,
                enregistrer_proche, enregistrer_souvenir, lire_souvenirs, supprimer_souvenir)
from serveur import creer_app
from valise import construire, rendre_page, VERSION_PAGE
from souvenirs import (valider_proche, valider_souvenir, idees_du_voyage, bloc_souvenirs, IDEES,
                       SCRIPT_SOUVENIRS)
from pwa import SCRIPT_PRECHARGEMENT

CODE = "2027-01-15 Hanoï"
AVANT = "2025-04-01 Tokyo"
PERSONNES = ["Julien", "Laetitia"]
ITINERAIRE = [{"destination": "Hanoï", "jours": 3}]
MAMAN = {"id": "proche-maman-1", "nom": "Maman", "budget": "30", "archive": False}


def souvenir(**champs):
    base = {"id": "souv-0000-0001", "voyage": CODE, "proche": "proche-maman-1", "idee": "Foulard en soie",
            "note": "Hội An", "achete": False}
    return {**base, **champs}


def achete(**champs):
    return souvenir(**{"achete": True, "prix": "500000", "devise": "VND", "prix_eur": "18.20",
                       "paye_par": "Julien", "achete_le": "2027-01-16", **champs})


# --- Idées par pays ---

def test_idees_du_voyage_dans_l_ordre_sans_doublon():
    idees = idees_du_voyage(["VN", "KH", "VN", "FR", None])
    assert [p["pays"] for p in idees] == ["Vietnam", "Cambodge"]
    assert any("Kampot" in i[0] for i in idees[1]["idees"])


def test_chaque_idee_est_complete():
    for code, (pays, idees) in IDEES.items():
        assert pays and idees, code
        for idee, note, alerte in idees:
            assert idee and (not alerte or alerte.startswith("⚠️")), (code, idee)


def test_bloc_souvenirs():
    html = bloc_souvenirs(PERSONNES, ["VND"], idees_du_voyage(["VN"]), douane=True)
    assert 'data-personnes="Julien|Laetitia"' in html and '"devises": ["EUR", "VND"]' in html
    assert 'data-idee="Laque"' in html and "430 €" in html
    assert 'data-idee="Vin de serpent"' not in html and "Vin de serpent" in html   # à éviter : sans ➕
    sans = bloc_souvenirs(["Julien"], [], [], douane=False)
    assert "430 €" not in sans and "idees-pays" not in sans


# --- Validation ---

def test_proche_valide():
    assert valider_proche(MAMAN)["budget"] == Decimal("30.00")
    assert valider_proche({**MAMAN, "budget": None})["budget"] is None


@pytest.mark.parametrize("champs", [{"id": "x"}, {"nom": " "}, {"nom": "x" * 81}, {"budget": -1},
                                    {"budget": "abc"}, {"budget": True}, {"archive": "non"}])
def test_proche_invalide(champs):
    with pytest.raises(ValueError):
        valider_proche({**MAMAN, **champs})


def test_souvenir_valide():
    s = valider_souvenir(souvenir())
    assert s["prix"] is None and s["paye_par"] is None
    a = valider_souvenir(achete())
    assert a["prix"] == Decimal("500000.00") and a["achete_le"] == date(2027, 1, 16)
    assert valider_souvenir(souvenir(proche=""))["proche"] == ""                     # pour nous


@pytest.mark.parametrize("corps", [
    souvenir(idee=""), souvenir(idee="x" * 201), souvenir(proche="<b>"), souvenir(achete="oui"),
    souvenir(voyage=""), achete(prix="0"), achete(devise="vnd"), achete(prix_eur=None), achete(paye_par=""),
    achete(achete_le="16/01/2027"),
])
def test_souvenir_invalide(corps):
    with pytest.raises(ValueError):
        valider_souvenir(corps)


# --- Base : l'achat tient sa dépense à jour ---

@pytest.fixture
def conn():
    c = connecter("valise_test")
    with c.cursor() as cur:
        cur.execute("TRUNCATE voyages, depenses, souvenirs, proches CASCADE")
    c.commit()
    enregistrer_voyage(c, CODE, "Hanoï", date(2027, 1, 15), PERSONNES, ITINERAIRE, {})
    enregistrer_proche(c, valider_proche(MAMAN))
    yield c
    c.close()


def test_achat_cree_modifie_puis_retire_la_depense(conn):
    enregistrer_souvenir(conn, valider_souvenir(souvenir()), PERSONNES)
    assert lire_depenses(conn, CODE) == []
    enregistrer_souvenir(conn, valider_souvenir(achete()), PERSONNES)
    d, = lire_depenses(conn, CODE)
    assert d["libelle"] == "🎁 Foulard en soie (Maman)" and d["montant_eur"] == Decimal("18.20")
    assert d["pour"] == PERSONNES and d["paye_par"] == "Julien" and d["devise"] == "VND"
    enregistrer_souvenir(conn, valider_souvenir(achete(prix_eur="20.00")), PERSONNES)   # rejoué / corrigé
    d2, = lire_depenses(conn, CODE)
    assert d2["id"] == d["id"] and d2["montant_eur"] == Decimal("20.00")
    enregistrer_souvenir(conn, valider_souvenir(souvenir()), PERSONNES)                 # plus acheté
    assert lire_depenses(conn, CODE) == []


def test_depense_retiree_a_la_main_pas_recreee(conn):
    enregistrer_souvenir(conn, valider_souvenir(achete()), PERSONNES)
    supprimer_depense(conn, CODE, lire_depenses(conn, CODE)[0]["id"])
    enregistrer_souvenir(conn, valider_souvenir(achete(note="autre note")), PERSONNES)
    assert lire_depenses(conn, CODE) == []


def test_souvenir_supprime_avec_sa_depense(conn):
    enregistrer_souvenir(conn, valider_souvenir(achete()), PERSONNES)
    supprimer_souvenir(conn, CODE, "souv-0000-0001")
    assert lire_souvenirs(conn, CODE)["souvenirs"] == [] and lire_depenses(conn, CODE) == []


def test_id_d_un_autre_voyage_refuse(conn):
    enregistrer_voyage(conn, AVANT, "Tokyo", date(2025, 4, 1), PERSONNES, ITINERAIRE, {})
    enregistrer_souvenir(conn, valider_souvenir(souvenir()), PERSONNES)
    with pytest.raises(ValueError):
        enregistrer_souvenir(conn, valider_souvenir(achete(voyage=AVANT)), PERSONNES)
    assert lire_depenses(conn, AVANT) == []


def test_historique_des_autres_voyages(conn):
    enregistrer_voyage(conn, AVANT, "Tokyo", date(2025, 4, 1), PERSONNES, ITINERAIRE, {})
    enregistrer_souvenir(conn, valider_souvenir(achete(id="souv-tokyo-01", voyage=AVANT, idee="Furoshiki",
                                                       devise="JPY")), PERSONNES)
    enregistrer_souvenir(conn, valider_souvenir(souvenir(id="souv-tokyo-02", voyage=AVANT, idee="Pas acheté")), PERSONNES)
    lu = lire_souvenirs(conn, CODE)
    assert lu["historique"] == {"proche-maman-1": [{"idee": "Furoshiki", "voyage": "Tokyo"}]}
    assert lu["proches"][0]["nom"] == "Maman" and lu["souvenirs"] == []
    assert lire_souvenirs(conn, AVANT)["historique"] == {}                              # pas son propre voyage


def test_souvenirs_suivent_un_voyage_modifie(conn):
    enregistrer_voyage(conn, "2027-01-16 Hanoï", "Hanoï", date(2027, 1, 16), PERSONNES, ITINERAIRE, {})
    enregistrer_souvenir(conn, valider_souvenir(souvenir()), PERSONNES)
    remplacer_voyage(conn, CODE, "2027-01-16 Hanoï")
    assert lire_souvenirs(conn, "2027-01-16 Hanoï")["souvenirs"][0]["idee"] == "Foulard en soie"


# --- API ---

@pytest.fixture
def client(conn):
    return creer_app("valise_test", secret="").test_client()


def test_api_souvenirs(client):
    assert client.post("/api/proches", json={**MAMAN, "nom": "Maman L."}).status_code == 200
    assert client.post("/api/proches", json={**MAMAN, "id": "x"}).status_code == 400
    assert client.post("/api/souvenirs", json=achete()).status_code == 200
    lu = client.get(f"/api/souvenirs/{CODE}").get_json()
    assert lu["proches"][0] == {"id": "proche-maman-1", "nom": "Maman L.", "budget": "30.00", "archive": False}
    s = lu["souvenirs"][0]
    assert s["prix_eur"] == "18.20" and s["achete_le"] == "2027-01-16" and "depense" not in s
    assert client.get(f"/api/depenses/{CODE}").get_json()["depenses"][0]["libelle"] == "🎁 Foulard en soie (Maman L.)"
    assert client.post("/api/souvenirs", json=achete(paye_par="Inconnu")).status_code == 400
    assert client.post("/api/souvenirs", json=souvenir(voyage="inconnu")).status_code == 404
    assert client.post("/api/souvenirs", json=souvenir(idee="")).status_code == 400
    assert client.delete(f"/api/souvenirs/{CODE}/souv-0000-0001").status_code == 200
    assert client.get(f"/api/depenses/{CODE}").get_json()["depenses"] == []


# --- Page ---

def page(personnes=("Julien",), code_pays="VN"):
    voyage = {"depart": date(2027, 1, 15), "personnes": list(personnes), "conduit": False, "lessive": None,
              "itineraire": [dict(e, mois=1, activites=[], normales=None, code_pays=code_pays, latitude=21.03,
                                  longitude=105.85) for e in ITINERAIRE]}
    return rendre_page(voyage, construire(voyage))


def test_souvenirs_dans_la_page():
    html = page()
    rub = html.split('<div class="rubrique" data-rubrique="souvenirs"')[1].split('</div>\n<div class="controls">')[0]
    assert 'class="info souvenirs"' in rub and "Vietnam" in rub and "430 €" in rub
    assert "Bientôt" not in rub
    assert SCRIPT_SOUVENIRS in html and VERSION_PAGE >= 20
    assert "430 €" not in page(code_pays="IT")                        # retour d'un pays de l'UE : pas de franchise


def test_script_souvenirs():
    for morceau in ("api/souvenirs/", "'api/proches'", "'api/souvenirs'", "envoyerOuGarder", "lireTauxGardes",
                    "chargerDepenses", "Object.assign({}, modifie, { voyage: VOYAGE })", "textContent"):
        assert morceau in SCRIPT_SOUVENIRS
    assert "innerHTML" not in SCRIPT_SOUVENIRS
    assert "type = 'checkbox'" not in SCRIPT_SOUVENIRS          # les cases de la valise comptent toutes les checkbox
    assert "'api/souvenirs/'" in SCRIPT_PRECHARGEMENT


def test_script_souvenirs_syntaxiquement_valide(tmp_path):
    if shutil.which("node") is None:
        pytest.skip("Node absent")
    fichier = tmp_path / "souvenirs.js"
    fichier.write_text('const VOYAGE="x";\n' + SCRIPT_SOUVENIRS)
    resultat = subprocess.run(["node", "--check", str(fichier)], capture_output=True, text=True)
    assert resultat.returncode == 0, resultat.stderr
