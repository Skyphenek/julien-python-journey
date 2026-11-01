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


def test_page():
    html = courses_en_html()
    assert '<script type="application/json" id="prix">' in html and 'id="budget"' in html
    assert '"filets de poulet": ["barquette de 2 (300 g)", 5.5]' in html
