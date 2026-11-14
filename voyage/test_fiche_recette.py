"""Tests de fiche_recette.py : découpage du texte d'une recette en fiche (logique pure)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from fiche_recette import decouper, decouper_phrase

EX = Path(__file__).parent / "exemples_fiches"


def lire(id_):
    return (EX / f"{id_}.txt").read_text(encoding="utf-8")


def test_carbonara_lignes():
    f = decouper(lire("plat-carbonara"))
    assert f["structuree"] is True
    assert f["pour"] == "Pour 2"
    assert (f["ingredients"][0]["nom"], f["ingredients"][0]["quantite"]) == ("Spaghetti", "320 g")
    assert (f["ingredients"][2]["nom"], f["ingredients"][2]["quantite"]) == ("Jaunes d’œufs", "4 (env. 70 g de jaunes)")
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
    assert (f["ingredients"][3]["nom"], f["ingredients"][3]["quantite"]) == ("Beurre", "60 g (dont 30 g froid, en dés, pour la mantecatura)")
    libre = [s for s in f["sections"] if s["titre"].startswith("Secret de mamma")]
    assert len(libre) == 1 and libre[0]["lignes"] == []


def test_polpette_sous_liste_et_tiret_long():
    f = decouper(lire("tester-polpette"))
    assert f["pour"] == "Pour 4 (deux repas à deux)"
    assert (f["ingredients"][0]["nom"], f["ingredients"][0]["quantite"]) == ("Bœuf haché", "350 g")
    sauce = [s for s in f["sections"] if s["titre"] == "Sauce"][0]
    assert sauce["lignes"][0] == "Passata (coulis de tomate) — 700 g"
    assert f["tempo"]["titre"] == "Tempo (≈ 1 h 10)" and len(f["etapes"]) == 9


def test_hot_dog_sans_tempo():
    f = decouper(lire("af-hot-dog"))
    assert f["tempo"] is None and len(f["etapes"]) == 3
    assert (f["ingredients"][0]["nom"], f["ingredients"][0]["quantite"]) == ("4 saucisses de Strasbourg, 4 pains à hot dog, moutarde, ketchup", "")


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


def test_action_coupee_au_premier_point_de_phrase():
    d = decouper_phrase("Râpe le pecorino le plus fin possible — en gros copeaux, il fait des grumeaux au lieu de fondre.")
    assert d["action"] == "Râpe le pecorino le plus fin possible"
    assert d["morceaux"] == [{"genre": "pourquoi", "texte": "— en gros copeaux, il fait des grumeaux au lieu de fondre."}]


def test_abreviations_ne_coupent_pas():
    d = decouper_phrase("Ajoute l’eau 1 c. à s. à la fois. Puis mélange.")
    assert d["action"] == "Ajoute l’eau 1 c. à s. à la fois."
    assert d["morceaux"] == [{"genre": "texte", "texte": " Puis mélange."}]


def test_action_avec_deux_points():
    d = decouper_phrase("Bouillon : mets-le dans une casserole à côté.")
    assert d["action"] == "Bouillon :"
    assert d["morceaux"][0] == {"genre": "texte", "texte": " mets-le dans une casserole à côté."}


def test_secrets_retires_du_texte():
    d = decouper_phrase("Puis les oignons (secret de grand-mère : une bonne pincée d’oignons crispy dessus) en tout dernier.")
    assert d["secrets"] == [{"qui": "grand-mere", "texte": "une bonne pincée d’oignons crispy dessus"}]
    assert "secret" not in d["action"] + "".join(m["texte"] for m in d["morceaux"])
    assert "oignons en tout dernier" in d["action"] + "".join(m["texte"] for m in d["morceaux"])


def test_secret_de_mamma_avec_guillemets():
    d = decouper_phrase("Mélange (secret de mamma : remue fort, la sauce doit « enrober » la pasta).")
    assert d["secrets"] == [{"qui": "mamma", "texte": "remue fort, la sauce doit « enrober » la pasta"}]


def test_pourquoi_au_milieu():
    d = decouper_phrase("Pose les boulettes, espacées de 2 cm — serrées, elles bouillent au lieu de dorer. N’y touche pas.")
    genres = [m["genre"] for m in d["morceaux"]]
    assert genres == ["pourquoi", "texte"]
    assert d["morceaux"][0]["texte"] == "— serrées, elles bouillent au lieu de dorer."


def test_phrase_sans_coupure():
    assert decouper_phrase("Four à 220 °C, grill.") == {"action": "Four à 220 °C, grill.", "morceaux": [], "secrets": []}


def test_carbonara_etapes_decoupees():
    f = decouper(lire("plat-carbonara"))
    e7 = f["etapes"][6]
    assert e7["n"] == 7 and e7["action"].startswith("Au minuteur")
    assert e7["secrets"][0]["qui"] == "grand-mere"
    e8 = f["etapes"][7]
    assert e8["action"] == "Mantecatura."
    assert e8["si"][0]["action"].startswith("Encore liquide après 1 min")
    assert "texte" not in e8


def test_version_page_montee():
    from valise import VERSION_PAGE
    assert VERSION_PAGE >= 46


def test_phrase_indentee_rattachee_a_son_etape():
    f = decouper(lire("plat-cote-de-boeuf"))
    assert len(f["etapes"]) == 8
    assert not any(s["titre"].startswith("Contrôle") for s in f["sections"])
    e6 = f["etapes"][5]
    assert len(e6["si"]) == 3 and e6["si"][2]["action"].startswith("Contrôle")
    burger = decouper(lire("plat-bacon-cheese-burger"))
    assert not any(s["titre"].startswith("Bleu et saignant") for s in burger["sections"])
    assert burger["etapes"][3]["si"][-1]["action"].startswith("Bleu et saignant")


def test_tempo_ligne_veille():
    f = decouper(lire("plat-cote-de-boeuf"))
    l = f["tempo"]["lignes"][0]
    assert (l["heure"], l["texte"], l["etapes"]) == ("Veille", "Côte salée, au frigo à découvert (1).", [1])


def joint(segments):
    return "".join(s["t"] for s in segments)


def chiffres(segments):
    return [(s["q"], s["u"]) for s in segments if "q" in s]


def test_base_des_compteurs():
    assert decouper(lire("plat-carbonara"))["base"] == {"table": 2, "garder": 0}
    assert decouper(lire("tester-polpette"))["base"] == {"table": 2, "garder": 2}
    assert decouper(lire("tester-nems"))["base"] is None                    # « Pour 20 nems »
    assert decouper("")["base"] is None


def test_segments_des_ingredients_et_sections():
    f = decouper(lire("plat-carbonara"))
    assert chiffres(f["ingredients"][0]["quantite_s"]) == [(320.0, "g")]
    assert chiffres(f["ingredients"][2]["quantite_s"]) == [(4.0, ""), (70.0, "g")]
    sauce = [s for s in decouper(lire("tester-polpette"))["sections"] if s["titre"] == "Sauce"][0]
    assert chiffres(sauce["lignes_s"][0]) == [(700.0, "g")]


def test_variantes_seuls_poids_et_volumes():
    f = decouper("Pour 2\n- Riz : 160 g\n\nVariantes :\n- 2 œufs en plus\n- 30 g de comté\n\nSauce :\n"
                 "- Oignon — 1 petit\n\n1. Cuis le riz : 10 min dans 50 cl d'eau.")   # « : » coupe l'action
    variantes = [s for s in f["sections"] if s["titre"] == "Variantes"][0]
    assert chiffres(variantes["lignes_s"][0]) == [] and chiffres(variantes["lignes_s"][1]) == [(30.0, "g")]
    sauce = [s for s in f["sections"] if s["titre"] == "Sauce"][0]
    assert chiffres(sauce["lignes_s"][0]) == [(1.0, "")]
    etape = f["etapes"][0]
    assert chiffres(etape["action_s"]) == [] and joint(etape["action_s"]) == etape["action"]
    tout = [s for m in etape["morceaux"] for s in m["s"]]
    assert chiffres(tout) == [(50.0, "cl")]


def _verifie_bout_a_bout(f):
    for x in f["ingredients"]:
        assert joint(x["nom_s"]) == x["nom"] and joint(x["quantite_s"]) == x["quantite"]
    for s in f["sections"]:
        assert [joint(l) for l in s["lignes_s"]] == s["lignes"]
    for l in (f["tempo"] or {"lignes": []})["lignes"]:
        assert joint(l["s"]) == l["texte"]
    for e in f["etapes"]:
        for p in [e, *e["si"]]:
            assert joint(p["action_s"]) == p["action"]
            assert all(joint(m["s"]) == m["texte"] for m in p["morceaux"])
            assert all(joint(s["s"]) == s["texte"] for s in p["secrets"])


def test_segments_bout_a_bout_sur_tous_les_exemples():
    for fichier in sorted(EX.glob("*.txt")):
        f = decouper(fichier.read_text(encoding="utf-8"))
        assert f["structuree"], fichier.name
        _verifie_bout_a_bout(f)
