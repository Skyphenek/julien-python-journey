"""Tests des dîners en base (db.py) et de leurs routes (serveur.py)."""
import sys
from datetime import timedelta
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pytest
from casa import aujourd_hui_paris
from carnet_depart import CARNET_DEPART, A_TESTER
from courses import PLACARD_DEPART
from db import (connecter, semer_carnet, semer_placard, lire_plats, enregistrer_repas, lire_repas,
                completer_recettes, enregistrer_plat)
from serveur import creer_app

J = aujourd_hui_paris()


@pytest.fixture
def conn():
    c = connecter("valise_test")
    with c.cursor() as cur:
        cur.execute("TRUNCATE repas, plats, courses, placard, reprises, achats")
    c.commit()
    semer_placard(c, PLACARD_DEPART)
    semer_carnet(c, CARNET_DEPART, A_TESTER)
    yield c
    c.close()


@pytest.fixture
def client(conn):
    return creer_app("valise_test", secret="").test_client()


def test_semer_carnet_une_seule_fois(conn):
    assert len(lire_plats(conn)) == len(CARNET_DEPART) + len(A_TESTER)
    assert semer_carnet(conn, CARNET_DEPART, A_TESTER) == 0
    carbo = next(p for p in lire_plats(conn) if p["id"] == "plat-carbonara")
    assert carbo["ingredients"] == ["spaghetti", "guanciale ou pancetta", "œufs", "pecorino"]
    assert carbo["lien"].startswith("https://ricette.giallozafferano.it/")


def test_completer_recettes_ne_remplit_que_les_vides(conn):
    # Carnet semé avant les recettes à tester (cas de Neon le 28/10) : deux matchs sans recette
    for id_, recette in (("tester-shakshuka", ""), ("tester-chili", "La nôtre, corrigée dans l'app.")):
        p = next(x for x in lire_plats(conn) if x["id"] == id_)
        enregistrer_plat(conn, {**p, "ingredients": [], "recette": recette})
    assert completer_recettes(conn, A_TESTER) == 1
    plats = {p["id"]: p for p in lire_plats(conn)}
    assert plats["tester-shakshuka"]["recette"].startswith("Pour 2") and "œufs" in plats["tester-shakshuka"]["ingredients"]
    assert plats["tester-chili"]["recette"] == "La nôtre, corrigée dans l'app."
    assert completer_recettes(conn, A_TESTER) == 0


def test_api_diners(client):
    d = client.get("/api/diners").get_json()
    assert d["aujourd_hui"] == J.isoformat() and len(d["semaine"]) == 7
    assert len(d["secours"]["faisables"]) == 7 and "plat-carbonara" in d["secours"]["faisables"]
    assert d["compteur"] == {"semaine": 0, "moyenne": 0, "renseignes": 0}
    carbo = next(p for p in d["plats"] if p["id"] == "plat-carbonara")
    assert carbo["fiche"]["structuree"] is True and carbo["fiche"]["etapes"]
    assert all("fiche" in p for p in d["plats"])


def test_planifier_et_courses_de_la_semaine(client):
    corps = {"jour": J.isoformat(), "moment": "diner", "plats": ["plat-amatriciana"]}
    assert client.post("/api/repas", json=corps).status_code == 200
    assert client.post("/api/repas", json={**corps, "plats": ["plat-inconnu-01"]}).status_code == 400
    assert client.post("/api/repas", json={**corps, "moment": "gouter"}).status_code == 400
    # le repas posé a déjà mis ce qui manque sur la liste (le reste est au placard) : le bouton n'a plus rien à ajouter
    assert [(a["nom"], a["source"]) for a in client.get("/api/courses").get_json()["articles"]] == [
        ("vin blanc", "repas:plat-amatriciana")]
    assert client.post("/api/diners/courses").get_json()["ajoutes"] == []     # pas de doublon


def test_api_repas_compose_et_brunch(client):
    jour = J.isoformat()
    client.post("/api/repas", json={"jour": jour, "moment": "diner", "plats": ["plat-carbonara", "tester-pesto"]})
    client.post("/api/repas", json={"jour": jour, "moment": "brunch", "plats": ["tester-shakshuka"]})
    d = client.get("/api/diners").get_json()
    assert {(r["moment"], tuple(r["plats"])) for r in d["repas"] if r["jour"] == jour} == {
        ("diner", ("plat-carbonara", "tester-pesto")), ("brunch", ("tester-shakshuka",))}
    assert d["cout_semaine"]["nb_repas"] == 2
    client.post("/api/repas", json={"jour": jour, "moment": "brunch", "plats": []})          # retirer le brunch
    assert [r["moment"] for r in client.get("/api/diners").get_json()["repas"]] == ["diner"]


def test_hier_soir_et_compteur_sur_aujourd_hui(client):
    hier = (J - timedelta(days=1)).isoformat()
    assert "Hier soir ?" in client.get("/").get_data(as_text=True)
    assert client.post("/api/repas", json={"jour": hier, "moment": "diner", "issue": "commande"}).status_code == 200
    html = client.get("/").get_data(as_text=True)
    assert "Hier soir ?" not in html and "1 commande ces 7 jours" in html


def test_ce_soir_compose_sur_aujourd_hui(client):
    client.post("/api/repas", json={"jour": J.isoformat(), "moment": "diner", "plats": ["plat-carbonara"]})
    html = client.get("/").get_data(as_text=True)
    assert "<strong>Spaghetti alla carbonara</strong>" in html


def test_api_plats(client):
    corps = {"id": "plat-maison-01", "nom": "Gratin de crozets", "genre": "plat", "minutes": 45,
             "ingredients": ["crozets", "beaufort"], "recette": "", "lien": "", "note": "", "statut": "carnet"}
    assert client.post("/api/plats", json=corps).status_code == 200
    assert client.post("/api/plats", json={**corps, "minutes": 0}).status_code == 400
    assert any(p["nom"] == "Gratin de crozets" for p in client.get("/api/diners").get_json()["plats"])


def test_page_diners(client):
    html = client.get("/diners").get_data(as_text=True)
    assert "<h1>Dîners</h1>" not in html and 'data-cucina="diners" class="actif"' in html


def test_route_recettes(client):
    html = client.get("/recettes").get_data(as_text=True)
    assert 'data-page="recettes"' in html and 'data-cucina="recettes" class="actif"' in html


def test_pour_julien_sort_du_nom(conn):
    from db import separer_pour_julien
    p = next(x for x in lire_plats(conn) if x["id"] == "tester-moules")
    enregistrer_plat(conn, {**p, "nom": "Moules marinières frites (Julien)"})       # comme en prod au 01/11
    assert separer_pour_julien(conn) == 1
    conn.commit()
    moules = next(x for x in lire_plats(conn) if x["id"] == "tester-moules")
    assert moules["nom"] == "Moules marinières frites" and moules["pour"] == "julien"
    assert separer_pour_julien(conn) is None                                       # une seule fois


def test_api_proposer(client):
    r = client.post("/api/diners/proposer", json={})
    assert r.status_code == 200
    proposes, menus = r.get_json()["proposes"], r.get_json()["menus"]
    assert 1 <= len(proposes) <= 4 and set(menus) == set(proposes)
    diners = {r["jour"]: r["plats"] for r in client.get("/api/diners").get_json()["repas"] if r["moment"] == "diner"}
    assert all(diners[j] == menus[j] and menus[j][0] == id_ for j, id_ in proposes.items())
    assert client.post("/api/diners/proposer", json={"remplacer": ["pas-une-date"]}).status_code == 400


def test_api_proposer_avec_un_accompagnement(client, conn):
    for p in lire_plats(conn):
        if p["genre"] == "plat":
            enregistrer_plat(conn, {**p, "accords": ["acc-puree-robuchon", "acc-pommes-sautees"]})
    menus = client.post("/api/diners/proposer", json={}).get_json()["menus"]
    accs = [ids[1] for ids in menus.values() if len(ids) == 2]
    assert accs and len(set(accs)) == len(accs) <= 2
    assert set(accs) <= {"acc-puree-robuchon", "acc-pommes-sautees"}


def test_api_reproposer_ne_reprend_pas_l_accompagnement_d_un_soir_garde(client, conn):
    for p in lire_plats(conn):
        if p["genre"] == "plat":
            enregistrer_plat(conn, {**p, "accords": ["acc-puree-robuchon"]})
    garde = (J + timedelta(days=1)).isoformat()
    client.post("/api/repas", json={"jour": garde, "moment": "diner",
                                    "plats": ["plat-carbonara", "acc-puree-robuchon", "dessert-tiramisu"], "issue": None})
    menus = client.post("/api/diners/proposer", json={"remplacer": [garde]}).get_json()["menus"]
    assert garde not in menus
    assert all("acc-puree-robuchon" not in ids for ids in menus.values())


def test_api_diners_couts(client):
    d = client.get("/api/diners").get_json()
    carbo = next(p for p in d["plats"] if p["id"] == "plat-carbonara")
    assert carbo["cout"] > 0 and d["livraison"] > 0
    assert {"nb_repas", "cout", "courses", "livraison", "a_acheter"} <= set(d["cout_semaine"])
    assert isinstance(d["liste"], list)


def test_aujourd_hui_ce_qu_il_faut_acheter_pour_les_repas_du_jour(client):
    jour = J.isoformat()
    client.post("/api/repas", json={"jour": jour, "moment": "diner", "plats": ["plat-piece-du-boucher"], "issue": None})
    client.post("/api/repas", json={"jour": jour, "moment": "dejeuner", "plats": ["plat-bacon-cheese-burger"],
                                    "issue": "fait"})                                    # déjà mangé : rien à acheter
    bloc = client.get("/").get_data(as_text=True).split('<a class="bloc-courses"')[1].split("</a>")[0]
    assert "pièce du boucher" in bloc and "pains burger" not in bloc


def test_aujourd_hui_oublie_pas_ce_qu_on_vient_d_acheter(client):
    client.post("/api/repas", json={"jour": J.isoformat(), "moment": "diner", "plats": ["plat-piece-du-boucher"],
                                    "issue": None})
    client.post("/api/courses", json={"id": "boucher-01", "nom": "pièce du boucher", "pris": True})
    client.post("/api/courses/vider")                                     # le panier est vidé
    html = client.get("/").get_data(as_text=True)
    bloc = html.split('<a class="bloc-courses"')[1].split("</a>")[0] if '<a class="bloc-courses"' in html else ""
    assert "pièce du boucher" not in bloc
    assert "piece du boucher" in client.get("/api/diners").get_json()["stock"]   # clé normalisée


def test_aujourd_hui_racheter_ce_qu_on_vient_d_acheter_le_remet_sur_la_liste(client):
    client.post("/api/repas", json={"jour": J.isoformat(), "moment": "diner", "plats": ["plat-piece-du-boucher"],
                                    "issue": None})
    client.post("/api/courses", json={"id": "boucher-01", "nom": "pièce du boucher", "pris": True})
    client.post("/api/courses/vider")
    client.post("/api/courses", json={"id": "boucher-02", "nom": "pièce du boucher"})     # il en faut encore
    bloc = client.get("/").get_data(as_text=True).split('<a class="bloc-courses"')[1].split("</a>")[0]
    assert "pièce du boucher" in bloc
    assert "piece du boucher" in client.get("/api/diners").get_json()["liste"]


def test_page_budget(client):
    client.post("/api/courses", json={"id": "lait-0001", "nom": "lait", "pris": True})
    client.post("/api/repas", json={"jour": J.isoformat(), "moment": "diner", "plats": [], "issue": "commande"})
    html = client.get("/budget").get_data(as_text=True)
    assert "<h1>Budget</h1>" in html and 'data-hub="budget" class="actif"' in html
    assert '<a class="bloc-budget" href="budget">' in client.get("/").get_data(as_text=True)


def test_compter_faits(conn):
    from db import compter_faits
    enregistrer_repas(conn, {"jour": J - timedelta(days=2), "moment": "diner", "plats": ["plat-carbonara"], "issue": "fait"})
    enregistrer_repas(conn, {"jour": J - timedelta(days=1), "moment": "diner", "plats": ["plat-carbonara"], "issue": "fait"})
    enregistrer_repas(conn, {"jour": J, "moment": "diner", "plats": ["plat-carbonara"], "issue": None})      # pas fait
    assert compter_faits(conn) == {"plat-carbonara": 2}


def test_api_diners_faits(client, conn):
    enregistrer_repas(conn, {"jour": J - timedelta(days=1), "moment": "diner", "plats": ["plat-carbonara"], "issue": "fait"})
    plats = {p["id"]: p for p in client.get("/api/diners").get_json()["plats"]}
    assert plats["plat-carbonara"]["faits"] == 1
    assert all(p["faits"] == 0 for i, p in plats.items() if i != "plat-carbonara")


def test_api_proposer_cases_midi_et_soir(client):
    demain = (J + timedelta(days=1)).isoformat()
    cases = [{"jour": demain, "moment": "dejeuner"}, {"jour": demain, "moment": "diner"}]
    r = client.post("/api/diners/proposer", json={"cases": cases})
    assert r.status_code == 200
    menus = r.get_json()["menus"]
    assert set(menus) <= {f"{demain}|dejeuner", f"{demain}|diner"} and menus
    poses = {(x["jour"], x["moment"]): x["plats"] for x in client.get("/api/diners").get_json()["repas"]}
    assert all(poses[tuple(k.split("|"))] == ids for k, ids in menus.items())
    assert all(len(ids) == 1 for k, ids in menus.items() if k.endswith("|dejeuner"))   # midi : sans accompagnement


def test_api_proposer_cases_invalides(client):
    assert client.post("/api/diners/proposer", json={"cases": [{"jour": "x", "moment": "diner"}]}).status_code == 400
    assert client.post("/api/diners/proposer",
                       json={"cases": [{"jour": J.isoformat(), "moment": "brunch"}]}).status_code == 400


def test_api_passe(client):
    hier = (J - timedelta(days=1)).isoformat()
    client.post("/api/repas", json={"jour": hier, "moment": "diner", "plats": ["plat-carbonara"], "issue": "fait"})
    r = client.get("/api/diners/passe")
    assert r.status_code == 200
    jours = [d for s in r.get_json()["semaines"] for d in s["jours"]]
    assert any(d["jour"] == hier and d["soir"]["issue"] == "fait" for d in jours)
    assert client.get("/api/diners/passe?avant=pas-une-date").status_code == 400


def test_api_passe_avant_un_mardi_refuse(client):
    mardi = J + timedelta(days=(1 - J.weekday()) % 7)
    assert mardi.weekday() == 1
    assert client.get(f"/api/diners/passe?avant={mardi.isoformat()}").status_code == 400


# --- Courses des repas prévus, automatiques (14/11/2026) ---

def _sans_placard(conn):
    with conn.cursor() as cur:                       # rien à la maison : tous les ingrédients manquent
        cur.execute("TRUNCATE placard, a_finir")
    conn.commit()


def _a_prendre(client):
    return {a["nom"]: a["source"] for a in client.get("/api/courses").get_json()["articles"] if a["actif"] and not a["pris"]}


def test_poser_un_repas_met_ses_ingredients_aux_courses_et_le_retirer_les_enleve(client, conn):
    _sans_placard(conn)
    demain = (J + timedelta(days=1)).isoformat()
    client.post("/api/repas", json={"jour": demain, "moment": "dejeuner", "plats": ["plat-carbonara"], "issue": None})
    poses = _a_prendre(client)
    assert poses and all(src == "repas:plat-carbonara" for src in poses.values())
    client.post("/api/courses", json={"id": "garder-0001", "nom": "pain", "source": "fiche:plat-carbonara"})   # depuis une fiche : intouchable
    client.post("/api/repas", json={"jour": demain, "moment": "dejeuner", "plats": [], "issue": None})
    assert _a_prendre(client) == {"pain": "fiche:plat-carbonara"}


def test_un_repas_hors_des_7_jours_ne_touche_pas_les_courses(client):
    loin = (J + timedelta(days=10)).isoformat()
    client.post("/api/repas", json={"jour": loin, "moment": "diner", "plats": ["plat-carbonara"], "issue": None})
    assert _a_prendre(client) == {}


def test_un_article_coche_reste_quand_on_retire_le_repas(client, conn):
    _sans_placard(conn)
    demain = (J + timedelta(days=1)).isoformat()
    client.post("/api/repas", json={"jour": demain, "moment": "diner", "plats": ["plat-carbonara"], "issue": None})
    a = next(a for a in client.get("/api/courses").get_json()["articles"] if a["source"] == "repas:plat-carbonara")
    client.post("/api/courses", json={**a, "pris": True})
    client.post("/api/repas", json={"jour": demain, "moment": "diner", "plats": [], "issue": None})
    assert any(x["id"] == a["id"] for x in client.get("/api/courses").get_json()["articles"])


def test_la_viande_perimee_repart_aux_courses(client, conn):
    _sans_placard(conn)
    client.post("/api/placard", json={"nom": "guanciale ou pancetta", "en_stock": True, "zone": "frigo"})
    with conn.cursor() as cur:                       # entré au frigo il y a un mois : passé (il se garde 21 jours)
        cur.execute("UPDATE placard SET maj_le = now() - interval '30 days'")
    conn.commit()
    demain = (J + timedelta(days=1)).isoformat()
    client.post("/api/repas", json={"jour": demain, "moment": "diner", "plats": ["plat-carbonara"], "issue": None})
    assert "guanciale ou pancetta" in _a_prendre(client)


def test_mettre_la_liste_a_jour_retire_les_ingredients_des_recettes_retirees(client, conn):
    _sans_placard(conn)
    demain = (J + timedelta(days=1)).isoformat()
    client.post("/api/repas", json={"jour": demain, "moment": "diner", "plats": ["plat-carbonara"], "issue": None})
    # ajoutés par l'ancien bouton (source « plat: ») ou une fiche (« fiche: », volontaire : jamais retiré)
    client.post("/api/courses", json={"id": "ancien-0001", "nom": "tomates pelées", "source": "plat:plat-amatriciana"})
    client.post("/api/courses", json={"id": "fiche-0001", "nom": "pain", "source": "fiche:plat-amatriciana"})
    r = client.post("/api/diners/courses").get_json()
    assert r["retires"] == ["tomates pelées"] and r["ajoutes"] == []
    noms = {a["nom"]: a["source"] for a in client.get("/api/courses").get_json()["articles"] if a["actif"]}
    assert noms["pain"] == "fiche:plat-amatriciana" and noms["guanciale ou pancetta"] == "repas:plat-carbonara"
    assert "tomates pelées" not in noms
    assert client.post("/api/diners/courses").get_json() == {"ok": True, "ajoutes": [], "retires": []}


def test_un_ingredient_du_planning_achete_entre_au_placard(client, conn):
    _sans_placard(conn)
    demain = (J + timedelta(days=1)).isoformat()
    client.post("/api/repas", json={"jour": demain, "moment": "diner", "plats": ["plat-carbonara"], "issue": None})
    spag = next(a for a in client.get("/api/courses").get_json()["articles"] if a["nom"] == "spaghetti")
    client.post("/api/courses", json={**spag, "pris": True})
    assert any(p["cle"] == "spaghetti" and p["en_stock"] for p in client.get("/api/courses").get_json()["placard"])


def test_cuisine_enregistree_et_gardee_si_absente(conn):
    from diners import valider_plat
    carbo = next(p for p in lire_plats(conn) if p["id"] == "plat-carbonara")
    assert carbo["cuisine"] == ""
    enregistrer_plat(conn, valider_plat({**carbo, "cuisine": "italie"}))
    enregistrer_plat(conn, valider_plat({k: v for k, v in carbo.items() if k != "cuisine"}))   # page en cache
    assert next(p for p in lire_plats(conn) if p["id"] == "plat-carbonara")["cuisine"] == "italie"
