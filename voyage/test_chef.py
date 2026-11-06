"""Tests du chef de la Casa (chef.py) : file de passage, lecture, écriture sauvegardée, ligne de commande."""
import json
import sys
from datetime import date
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pytest
from db import connecter, enregistrer_plat, enregistrer_repas
from chef import MARQUEUR, RecetteModifiee, file_de_passage, lire, ecrire, main


def plat(id_, **champs):
    return {"id": id_, "nom": id_.title(), "genre": "plat", "minutes": 20, "ingredients": [], "recette": "Pour 2",
            "lien": "", "note": "", "statut": "carnet", "archive": False, "pour": "nous", "accords": []} | champs


@pytest.fixture
def conn():
    c = connecter("valise_test")
    with c.cursor() as cur:
        cur.execute("TRUNCATE repas, plats")
    c.commit()
    yield c
    c.rollback()
    with c.cursor() as cur:                          # ne pas laisser de lignes aux modules suivants
        cur.execute("TRUNCATE repas, plats")
    c.commit()
    c.close()


def faire(conn, jour, *ids):
    enregistrer_repas(conn, {"jour": date(2026, 10, jour), "moment": "diner", "plats": list(ids), "issue": "fait"})


def test_file_les_plus_cuisines_d_abord(conn):
    for id_ in ("a", "b", "c"):
        enregistrer_plat(conn, plat(id_))
    faire(conn, 1, "b")
    faire(conn, 2, "b", "c")
    enregistrer_repas(conn, {"jour": date(2026, 10, 3), "moment": "diner", "plats": ["c"], "issue": "commande"})
    assert [(p["id"], p["faits"]) for p in file_de_passage(conn)] == [("b", 2), ("c", 1), ("a", 0)]


def test_file_carnet_avant_a_tester_puis_genre_puis_nom(conn):
    enregistrer_plat(conn, plat("z-tester", statut="a-tester"))
    enregistrer_plat(conn, plat("y-dessert", genre="dessert"))
    enregistrer_plat(conn, plat("x-plat"))
    enregistrer_plat(conn, plat("w-acc", genre="accompagnement"))
    assert [p["id"] for p in file_de_passage(conn)] == ["x-plat", "w-acc", "y-dessert", "z-tester"]


def test_file_exclut_archives_et_deja_passes(conn):
    enregistrer_plat(conn, plat("vieux", archive=True))
    enregistrer_plat(conn, plat("passe", recette=f"1. Saisir.\n\n{MARQUEUR}\n- Beurre froid."))
    enregistrer_plat(conn, plat("reste"))
    assert [p["id"] for p in file_de_passage(conn)] == ["reste"]


def test_file_limitee_a_n(conn):
    for i in range(7):
        enregistrer_plat(conn, plat(f"p{i}"))
    assert len(file_de_passage(conn)) == 5
    assert len(file_de_passage(conn, n=2)) == 2


def test_lire(conn):
    enregistrer_plat(conn, plat("saltimbocca", recette="Pour 4\n1. Saisir."))
    r = lire(conn, "saltimbocca")
    assert {k: r[k] for k in ("id", "nom", "genre", "pour", "recette")} == {
        "id": "saltimbocca", "nom": "Saltimbocca", "genre": "plat", "pour": "nous", "recette": "Pour 4\n1. Saisir."}
    assert r["maj_le"] is not None
    assert lire(conn, "inconnu") is None


NEUVE = f"Pour 4\n1. Saisir, sans toucher, jusqu'aux bords dorés.\n\n{MARQUEUR}\n- Beurre froid hors du feu."


def test_ecrire_sauvegarde_puis_remplace(conn, tmp_path):
    enregistrer_plat(conn, plat("saltimbocca", recette="Pour 4\n1. Saisir.", note="La mamma"))
    avant = lire(conn, "saltimbocca")
    chemin = ecrire(conn, "saltimbocca", NEUVE, avant["maj_le"], tmp_path / "sauv")
    assert chemin.parent == tmp_path / "sauv" and chemin.name.endswith("-saltimbocca.json")
    sauve = json.loads(chemin.read_text())
    assert sauve["recette"] == "Pour 4\n1. Saisir." and sauve["note"] == "La mamma"
    apres = lire(conn, "saltimbocca")
    assert apres["recette"] == NEUVE and apres["maj_le"] > avant["maj_le"]


def test_ecrire_ne_touche_qu_a_la_recette(conn, tmp_path):
    enregistrer_plat(conn, plat("s", minutes=25, ingredients=["sauge"], accords=["acc-polenta"], pour="julien"))
    ecrire(conn, "s", NEUVE, lire(conn, "s")["maj_le"], tmp_path)
    with conn.cursor() as cur:
        cur.execute("SELECT minutes, ingredients, accords, pour, statut FROM plats WHERE id = 's'")
        assert cur.fetchone() == (25, ["sauge"], ["acc-polenta"], "julien", "carnet")


def test_ecrire_refuse_si_modifiee_entre_temps(conn, tmp_path):
    enregistrer_plat(conn, plat("s"))
    lu = lire(conn, "s")["maj_le"]
    enregistrer_plat(conn, plat("s", recette="Corrigée dans l'app"))     # Laetitia corrige sur l'iPhone
    with pytest.raises(RecetteModifiee):
        ecrire(conn, "s", NEUVE, lu, tmp_path)
    assert lire(conn, "s")["recette"] == "Corrigée dans l'app"
    assert list(tmp_path.iterdir()) == []                              # pas de sauvegarde pour rien


def test_ecrire_refuse_sans_bloc_final(conn, tmp_path):
    enregistrer_plat(conn, plat("s"))
    with pytest.raises(ValueError):
        ecrire(conn, "s", "Pour 4\n1. Saisir.", lire(conn, "s")["maj_le"], tmp_path)
    assert lire(conn, "s")["recette"] == "Pour 2"


def test_ecrire_id_inconnu(conn, tmp_path):
    with pytest.raises(KeyError):
        ecrire(conn, "inconnu", NEUVE, None, tmp_path)


def test_deux_passes_le_meme_jour_ne_s_ecrasent_pas(conn, tmp_path):
    enregistrer_plat(conn, plat("s", recette="v1"))
    premiere = ecrire(conn, "s", NEUVE, lire(conn, "s")["maj_le"], tmp_path)
    seconde = ecrire(conn, "s", NEUVE + "\n- Sel à la fin.", lire(conn, "s")["maj_le"], tmp_path)
    assert premiere != seconde and seconde.name.endswith("-s-2.json")
    assert json.loads(premiere.read_text())["recette"] == "v1"
    assert json.loads(seconde.read_text())["recette"] == NEUVE


def test_cli_file_et_lire(conn, capsys):
    enregistrer_plat(conn, plat("saltimbocca", recette="Pour 4"))
    faire(conn, 1, "saltimbocca")
    assert main(["--base", "valise_test", "file"]) == 0
    assert capsys.readouterr().out == "1\tsaltimbocca\tSaltimbocca\tcarnet\n"
    assert main(["--base", "valise_test", "lire", "saltimbocca"]) == 0
    sortie = json.loads(capsys.readouterr().out)
    assert sortie["recette"] == "Pour 4" and sortie["maj_le"] == lire(conn, "saltimbocca")["maj_le"].isoformat()


def test_cli_ecrire(conn, capsys, tmp_path):
    enregistrer_plat(conn, plat("s"))
    maj = lire(conn, "s")["maj_le"].isoformat()
    texte = tmp_path / "s.txt"
    texte.write_text(NEUVE + "\n")
    argv = ["--base", "valise_test", "ecrire", "s", str(texte), "--maj", maj, "--dossier", str(tmp_path / "sauv")]
    assert main(argv) == 0
    assert capsys.readouterr().out.strip().endswith("-s.json")
    assert lire(conn, "s")["recette"] == NEUVE                       # retour à la ligne final retiré
    assert main(argv) == 2                                           # même maj : la recette a bougé depuis


def test_cli_ecrire_id_inconnu(conn, tmp_path):
    texte = tmp_path / "x.txt"
    texte.write_text(NEUVE)
    assert main(["--base", "valise_test", "ecrire", "x", str(texte), "--maj", "2026-11-06T00:00:00+00:00",
                 "--dossier", str(tmp_path)]) == 1
