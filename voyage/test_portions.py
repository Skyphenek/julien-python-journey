"""Tests de portions.py : quantités multipliables d'une recette (logique pure + JS sous node)."""
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

from portions import base_parts, segmenter


def bout_a_bout(segments):
    return "".join(s["t"] for s in segments)


def quantites(segments):
    return [(s["q"], s["u"]) for s in segments if "q" in s]


@pytest.mark.parametrize("pour, attendu", [
    ("Pour 2", {"table": 2, "garder": 0}),
    ("Pour 8", {"table": 8, "garder": 0}),
    ("Pour 4 (deux repas à deux)", {"table": 2, "garder": 2}),
    ("Pour 4 (deux repas à deux) — meilleur réchauffé le lendemain", {"table": 2, "garder": 2}),
    ("Pour 4 (deux dîners, ou un dîner à quatre)", {"table": 2, "garder": 2}),
    ("Pour 2, plus 2 parts à congeler", {"table": 2, "garder": 2}),
    ("Pour 4 portions (se congèle)", {"table": 4, "garder": 0}),
    ("Pour 6 — à faire la veille (6 heures de frigo)", {"table": 6, "garder": 0}),
    ("Pour 2 (8 rouleaux)", {"table": 2, "garder": 0}),
])
def test_base_parts_lisible(pour, attendu):
    assert base_parts(pour) == attendu


@pytest.mark.parametrize("pour", ["", "Pour 2 à 4", "Pour 1 ou 2", "Pour 1 gros appétit ou 2", "Pour 4 en apéro",
                                  "Pour 4 à l'apéro", "Pour 8 tranches (moule à cake de 25 cm)", "Pour 20 nems",
                                  "Pour 14", "Une recette sans portion"])
def test_base_parts_floue(pour):
    assert base_parts(pour) is None


def test_premier_nombre_avec_unite_metrique():
    s = segmenter("320 g de penne", premier=True)
    assert s[0] == {"t": "320", "q": 320.0, "u": "g"}
    assert bout_a_bout(s) == "320 g de penne"


def test_formats_de_quantite():
    assert quantites(segmenter("1,2 kg de veau", premier=True)) == [(1.2, "kg")]
    assert quantites(segmenter("1/2 citron", premier=True)) == [(0.5, "")]
    assert quantites(segmenter("1 1/2 c. à s. de farine", premier=True)) == [(1.5, "")]
    assert quantites(segmenter("12 petits oignons grelots", premier=True)) == [(12.0, "")]
    assert quantites(segmenter("3 cm de gingembre", premier=True)) == [(3.0, "")]


def test_plage():
    s = segmenter("2–3 c. à s. d'eau", premier=True)
    assert s[0] == {"t": "2–3", "q": 2.0, "u": "", "q2": 3.0, "sep": "–"}
    assert bout_a_bout(s) == "2–3 c. à s. d'eau"


def test_premier_nombre_qui_n_est_pas_une_quantite():
    assert quantites(segmenter("5 min à 180 °C", premier=True)) == []
    assert quantites(segmenter("50 % de cacao", premier=True)) == []


def test_dans_une_etape_seuls_poids_et_volumes():
    texte = "Fais réduire 80 cl de bouillon à feu vif 10 min, jusqu'à environ 60 cl, puis 2 œufs et les 40 g de beurre."
    s = segmenter(texte)
    assert quantites(s) == [(80.0, "cl"), (60.0, "cl"), (40.0, "g")]
    assert bout_a_bout(s) == texte


def test_heures_renvois_et_mots_ne_bougent_pas():
    for texte in ("0:12  Viande rincée, eau froide (2).", "Parmigiano Reggiano AOP (24 mois)", "en cubes de 5 cm",
                  "1 l’eau", "B12"):
        s = segmenter(texte)
        assert quantites(s) == [] and bout_a_bout(s) == texte


def test_seconds_nombres_d_une_ligne_d_ingredient():
    s = segmenter("60 g (dont 30 g froid, en dés)", premier=True)
    assert quantites(s) == [(60.0, "g"), (30.0, "g")]
    s = segmenter("4 c. à s. d'huile d'olive (dont 1 crue pour finir)", premier=True)
    assert quantites(s) == [(4.0, "")]


def test_fraction_impossible_reste_du_texte():
    s = segmenter("1/0 citron", premier=True)
    assert quantites(s) == [] and bout_a_bout(s) == "1/0 citron"


VERIFS_JS = r"""
const echecs = [];
function ok(obtenu, attendu) { if (obtenu !== attendu) echecs.push(JSON.stringify(obtenu) + ' au lieu de ' + JSON.stringify(attendu)); }
const penne = [{t: '320', q: 320, u: 'g'}, {t: ' g de penne'}];
ok(texteAjuste(penne, 1), '320 g de penne');
ok(texteAjuste(penne, 3), '960 g de penne');
ok(texteAjuste([{t: '43', q: 43, u: 'g'}, {t: ' g'}], 3), '130 g');
ok(texteAjuste([{t: '32', q: 32, u: 'g'}, {t: ' g'}], 3), '95 g');
ok(texteAjuste([{t: '1', q: 1, u: 'g'}, {t: ' g'}], 0.5), '5 g');
ok(texteAjuste([{t: '1,2', q: 1.2, u: 'kg'}, {t: ' kg'}], 3), '3,6 kg');
ok(texteAjuste([{t: '80', q: 80, u: 'cl'}, {t: ' cl'}], 1.5), '120 cl');
ok(texteAjuste([{t: '1/2', q: 0.5, u: ''}, {t: ' citron'}], 3), '1 1/2 citron');
ok(texteAjuste([{t: '1/4', q: 0.25, u: ''}, {t: ' de chou'}], 0.5), '1/2 de chou');
ok(texteAjuste([{t: '12', q: 12, u: ''}, {t: ' oignons'}], 3), '36 oignons');
ok(texteAjuste([{t: '2–3', q: 2, u: '', q2: 3, sep: '–'}, {t: ' c. à s.'}], 2), '4–6 c. à s.');
ok(texteAjuste([{t: 'Sel'}], 3), 'Sel');
if (echecs.length) { console.error(echecs.join('\n')); process.exit(1); }
"""


def test_script_portions_sous_node(tmp_path):
    from portions import SCRIPT_PORTIONS
    node = shutil.which("node")
    if node is None:
        pytest.skip("node absent")
    fichier = tmp_path / "portions.js"
    fichier.write_text(SCRIPT_PORTIONS + VERIFS_JS, encoding="utf-8")
    r = subprocess.run([node, str(fichier)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
