"""Tests du vocabulaire de destination (rubrique Sur place) et de l'ordre des blocs Sur place."""
import json
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pytest
from valise import construire, rendre_page, VERSION_PAGE
from vocabulaire import (PHRASES, LANGUES, LANGUE_PAR_PAYS, langues_du_voyage, bloc_vocabulaire,
                         SCRIPT_VOCABULAIRE, cles_audio, fichier_audio, texte_a_dire)
from serveur import creer_app

CLES = [cle for _, phrases in PHRASES for cle, _ in phrases]


def test_chaque_langue_est_complete():
    for code, langue in LANGUES.items():
        assert set(langue["phrases"]) == set(CLES), code
        assert len(langue["nombres"]) == 12, code                  # 1 à 10, 100, 1000
        for ecrit, prononciation in [*langue["phrases"].values(), *langue["nombres"]]:
            assert ecrit.strip() and prononciation.strip(), code
        assert langue["nom"] and langue["voix"] and langue["neurale"].startswith(langue["voix"].split("-")[0]), code


def test_chaque_pays_pointe_vers_une_langue_connue():
    assert set(LANGUE_PAR_PAYS.values()) <= set(LANGUES)
    assert LANGUE_PAR_PAYS["VN"] == "vi" and LANGUE_PAR_PAYS["KH"] == "km" and LANGUE_PAR_PAYS["BR"] == "pt-BR"
    assert "FR" not in LANGUE_PAR_PAYS and "SN" not in LANGUE_PAR_PAYS        # francophones : rien


def test_portugais_du_bresil_reprend_le_portugal_sauf_differences():
    pt, br = LANGUES["pt"]["phrases"], LANGUES["pt-BR"]["phrases"]
    assert br["merci"] == pt["merci"]
    assert br["toilettes"] != pt["toilettes"]
    assert LANGUES["pt-BR"]["voix"] == "pt-BR"


def test_langues_du_voyage_dans_l_ordre_sans_doublon():
    itineraire = [{"code_pays": "VN"}, {"code_pays": "KH"}, {"code_pays": "VN"}, {"code_pays": "FR"}, {}]
    assert langues_du_voyage(itineraire) == ["vi", "km"]
    assert langues_du_voyage([{"code_pays": "MX"}, {"code_pays": "ES"}]) == ["es"]


def test_bloc_vocabulaire():
    html = bloc_vocabulaire(["vi", "km"])
    assert html.count('<details class="langue"') == 2
    assert '<details class="langue" open>' in html                 # la 1re langue ouverte
    assert 'data-voix="vi-VN"' in html and 'lang="vi"' in html
    assert 'data-audio="audio/vi/bonjour.mp3"' in html and 'data-audio="audio/km/nombre-12.mp3"' in html
    assert ' hidden aria-label' not in html                          # 🔊 toujours là : le son est fourni
    assert "Xin chào" in html and "sin tchao" in html
    assert "ជំរាបសួរ" in html
    assert bloc_vocabulaire([]) == ""


def test_texte_echappe():
    assert "<script" not in bloc_vocabulaire(list(LANGUES)).replace('<script', '')   # aucune balise injectée


def test_chaque_phrase_a_son_mp3_a_jour():
    """Les MP3 correspondent au texte et à la voix actuels (sinon : relancer generer_audios.py)."""
    statique = Path(__file__).parent / "static"
    index = json.loads((statique / "audio" / "textes.json").read_text())
    for code, langue in LANGUES.items():
        for cle, ecrit in cles_audio(code):
            chemin = fichier_audio(code, cle)
            assert index.get(chemin) == [langue["neurale"], texte_a_dire(ecrit, code)], chemin
            assert (statique / chemin).stat().st_size > 1000, chemin


def test_texte_a_dire_sans_barre_oblique():
    assert texte_a_dire("Obrigado / Obrigada") == "Obrigado, Obrigada"
    assert texte_a_dire("สวัสดีครับ / ค่ะ", "th") == "สวัสดีค่ะ"
    assert texte_a_dire("เท่าไหร่?", "th") == "เท่าไหร่"


def test_route_audio():
    client = creer_app("valise_test", secret="s3cret").test_client()
    r = client.get("/v/s3cret/audio/vi/bonjour.mp3")
    assert r.status_code == 200 and r.mimetype == "audio/mpeg"
    r.close()
    assert client.get("/v/s3cret/audio/xx/bonjour.mp3").status_code == 404
    assert client.get("/v/s3cret/audio/vi/inconnu.mp3").status_code == 404
    assert client.get("/v/s3cret/audio/vi/..%2Fth%2Fbonjour.mp3").status_code == 404
    assert client.get("/audio/vi/bonjour.mp3").status_code == 404               # sans le code : rien


def test_script_vocabulaire():
    for morceau in ("createObjectURL", "new Audio", "speechSynthesis", "grand-texte", "textContent"):
        assert morceau in SCRIPT_VOCABULAIRE
    assert "innerHTML" not in SCRIPT_VOCABULAIRE


def test_script_vocabulaire_syntaxiquement_valide(tmp_path):
    if shutil.which("node") is None:
        pytest.skip("Node absent")
    fichier = tmp_path / "vocabulaire.js"
    fichier.write_text(SCRIPT_VOCABULAIRE)
    resultat = subprocess.run(["node", "--check", str(fichier)], capture_output=True, text=True)
    assert resultat.returncode == 0, resultat.stderr


# --- Page : Sur place réorganisée ---

def page_vietnam():
    voyage = {"depart": date(2027, 1, 10), "personnes": ["Julien", "Laetitia"], "conduit": False, "lessive": None,
              "itineraire": [{"destination": "Hanoï", "jours": 5, "code_pays": "VN", "latitude": 21.03,
                              "longitude": 105.85, "mois": 1, "activites": [], "normales": None},
                             {"destination": "Siem Reap", "jours": 4, "code_pays": "KH", "latitude": 13.36,
                              "longitude": 103.86, "mois": 1, "activites": [], "normales": None}]}
    return rendre_page(voyage, construire(voyage))


def test_sur_place_dans_l_ordre_decalage_devises_depenses_urgences_vocabulaire():
    html = page_vietnam()
    sur_place = html.split('<div class="rubrique" data-rubrique="sur-place"')[1].split('<div class="rubrique"')[0]
    positions = [sur_place.index(f'class="info {bloc}"')
                 for bloc in ("decalage", "devises", "depenses", "urgences", "vocabulaire")]
    assert positions == sorted(positions)
    assert "Bientôt : visites à faire." in sur_place
    assert SCRIPT_VOCABULAIRE in html
    assert VERSION_PAGE >= 18
