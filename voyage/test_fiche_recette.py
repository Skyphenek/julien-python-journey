"""Tests de fiche_recette.py : découpage du texte d'une recette en fiche (logique pure)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from fiche_recette import decouper

EX = Path(__file__).parent / "exemples_fiches"


def lire(id_):
    return (EX / f"{id_}.txt").read_text(encoding="utf-8")


def test_carbonara_lignes():
    f = decouper(lire("plat-carbonara"))
    assert f["structuree"] is True
    assert f["pour"] == "Pour 2"
    assert f["ingredients"][0] == {"nom": "Spaghetti", "quantite": "320 g"}
    assert f["ingredients"][2] == {"nom": "Jaunes d’œufs", "quantite": "4 (env. 70 g de jaunes)"}
    assert len(f["ingredients"]) == 6
    assert f["sections"][0]["titre"] == "Variantes (acceptables)" and len(f["sections"][0]["lignes"]) == 2
    assert f["tempo"]["titre"].startswith("Tempo (≈ 27 min")
    assert f["tempo"]["lignes"][0]["heure"] == "0:00"
    assert f["tempo"]["lignes"][1]["etapes"] == [1, 2, 3]
    assert [e["n"] for e in f["etapes"]] == list(range(1, 10))
    assert len(f["etapes"][7]["si"]) == 2                     # étape 8 : les deux rattrapages
    assert len(f["difference"]) == 3 and f["difference"][0].startswith("Pâtes finies")


def test_risotto_etapes_en_parenthese_et_secret_libre():
    f = decouper(lire("plat-risotto-milanese"))
    assert len(f["etapes"]) == 10
    assert f["ingredients"][3] == {"nom": "Beurre", "quantite": "60 g (dont 30 g froid, en dés, pour la mantecatura)"}
    libre = [s for s in f["sections"] if s["titre"].startswith("Secret de mamma")]
    assert len(libre) == 1 and libre[0]["lignes"] == []


def test_polpette_sous_liste_et_tiret_long():
    f = decouper(lire("tester-polpette"))
    assert f["pour"] == "Pour 4 (deux repas à deux)"
    assert f["ingredients"][0] == {"nom": "Bœuf haché", "quantite": "350 g"}
    sauce = [s for s in f["sections"] if s["titre"] == "Sauce"][0]
    assert sauce["lignes"][0] == "Passata (coulis de tomate) — 700 g"
    assert f["tempo"]["titre"] == "Tempo (≈ 1 h 10)" and len(f["etapes"]) == 9


def test_hot_dog_sans_tempo():
    f = decouper(lire("af-hot-dog"))
    assert f["tempo"] is None and len(f["etapes"]) == 3
    assert f["ingredients"][0] == {"nom": "4 saucisses de Strasbourg, 4 pains à hot dog, moutarde, ketchup", "quantite": ""}


def test_ancien_format_erreurs_frequentes_et_variante_libre():
    f = decouper(lire("plat-croque-monsieur"))
    assert f["structuree"] is True and len(f["etapes"]) == 5
    titres = [s["titre"] for s in f["sections"]]
    assert "Erreurs fréquentes" in titres
    assert any(t.startswith("Variante madame") for t in titres)
    erreurs = [s for s in f["sections"] if s["titre"] == "Erreurs fréquentes"][0]
    assert len(erreurs["lignes"]) == 2
    assert all(e["si"] == [] for e in f["etapes"])            # les « - » des erreurs ne sont pas des sous-puces
    assert f["difference"] == []


def test_nems_ancien_format():
    f = decouper(lire("tester-nems"))
    assert f["pour"] == "Pour 20 nems" and len(f["etapes"]) == 5 and f["tempo"] is None


def test_textes_non_structures():
    for t in ("", "   ", "Recette à écrire.", "Un texte libre\nsans étape numérotée."):
        f = decouper(t)
        assert f["structuree"] is False and f["etapes"] == []
    assert decouper(None)["structuree"] is False
