"""Tests des prix d'un panier parisien (prix_paris.py)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from catalogue import CATALOGUE
from courses import courses_en_html
from prix_paris import PRIX


def test_chaque_article_du_catalogue_a_unite_et_prix():
    assert set(PRIX) == {nom for nom, _, _ in CATALOGUE}
    for nom, (unite, prix) in PRIX.items():
        assert unite and 0.3 <= prix <= 40, nom


def test_unites_types():
    assert PRIX["filets de poulet"][0].startswith("barquette de 2")
    assert PRIX["œufs"] == ("boîte de 12", 4.2)
    assert PRIX["pack d'eau"] == ("pack de 6 × 1,5 L", 3.5)


def test_page():
    html = courses_en_html()
    assert '<script type="application/json" id="prix">' in html and 'id="budget"' in html
    assert '"filets de poulet": ["barquette de 2 (300 g)", 5.5]' in html


# --- Coût d'un repas (Dîners) ---
from prix_paris import cout_repas, prix_de


def test_prix_de_par_la_cle_du_catalogue():
    assert prix_de("Tomate cerise") == PRIX["tomates cerises"] and prix_de("truc inconnu") is None


def test_cout_repas_plausible():
    carbonara = cout_repas(["spaghetti", "guanciale ou pancetta", "œufs", "pecorino"])
    assert 4 <= carbonara <= 9                                  # la part utilisée, pas les paquets entiers
    assert cout_repas(["pavés de saumon", "riz basmati"]) > cout_repas(["spaghetti", "œufs"])
    assert cout_repas([]) == 0 and cout_repas(["truc inconnu"]) == 0
    veau = ["veau", "carottes", "crème fraîche"]
    assert cout_repas(veau, "Pour 4\n- 1,2 kg de veau") == round(cout_repas(veau) / 2, 2)   # ramené à deux
