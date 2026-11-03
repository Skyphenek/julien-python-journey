"""Tests des durées de conservation (conservation.py) : exceptions, défaut du rayon, inconnu."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from conservation import duree, PAR_RAYON, DUREE_INCONNUE


def test_exceptions_par_produit():
    assert duree("steaks hachés") == 1 and duree("Steak haché") == 1 and duree("saumon") == 1
    assert duree("fraises") == 3 and duree("salade") == 4 and duree("burrata") == 5
    assert duree("jambon") == 7 and duree("lait") == 7 and duree("mozzarella") == 10
    assert duree("crème fraîche") == 14 and duree("yaourt grec") == 14
    assert duree("bacon") == 10 and duree("mozzarella râpée") == 14
    assert duree("comté") == 21 and duree("œufs") == 28 and duree("beurre demi-sel") == 28


def test_defaut_du_rayon():
    assert duree("cuisses de poulet") == PAR_RAYON["boucherie"] == 2
    assert duree("tomates") == PAR_RAYON["fruits-legumes"] == 5
    assert duree("chèvre") == PAR_RAYON["frais"] == 7
    assert duree("harissa") == PAR_RAYON["epicerie"] == 30
    assert duree("kimchi") == PAR_RAYON["specialise"] == 14


def test_inconnu():
    assert duree("truc introuvable") == DUREE_INCONNUE == 7
