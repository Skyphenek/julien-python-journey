"""Serveur Flask : sert la checklist HTML et expose l'état en API Postgres.

Même code en local (Mac) et en ligne (Render) ; seules les variables d'environnement changent :
- DATABASE_URL  : base en ligne (sinon base locale "valise")
- ACCES_SECRET  : code secret ; toutes les routes passent sous /v/<secret>/ (sinon à la racine)
- PORT          : imposé par l'hébergeur (sinon 8000)
"""
import json
import os
import re
from decimal import Decimal, InvalidOperation
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import quote

import psycopg2

from dotenv import load_dotenv
from flask import Blueprint, Flask, abort, jsonify, request, Response, send_from_directory

from db import (emprunter, ajouter_depense, lire_depenses, supprimer_depense, obtenir_etat,
                enregistrer_reservation, lire_reservations, supprimer_reservation,
                enregistrer_a_voir, lire_a_voir, supprimer_a_voir, enregistrer_proche, enregistrer_souvenir,
                lire_souvenirs, supprimer_souvenir, enregistrer_coche, lister_voyages, lire_voyage, archiver_voyage,
                VERDICTS, enregistrer_retour, supprimer_retour, lire_retours,
                enregistrer_article, lire_courses, supprimer_article, vider_pris, lire_achats,
                enregistrer_placard, retirer_du_placard, enregistrer_plat, lire_plats, plat_existe, enregistrer_repas, lire_repas, compter_faits,
                lire_frais, finir, corriger_a_finir,
                lire_cave, enregistrer_bouteille, boire, retirer_bouteille,
                lire_sorties, creer_sortie, donner_avis, maj_sortie)
from sortir import valider_sortie, tirer_weekend, rappels
import random
from valise import (solde_depenses, actualiser_meteo, fenetres_du_voyage, page_du_voyage, accueil_en_html,
                    lieux_depuis_reponse, normales_ou_url, normales_depuis_historique,
                    formulaire_en_html, creer_voyage, VERSION_PAGE)
from api_climat import url_geocodage
from pwa import manifeste, script_service_worker, TAILLES_ICONE
from programme import valider_reservation
from a_voir import valider_a_voir, suggestions_depuis_wikitext
from souvenirs import valider_proche, valider_souvenir
from vocabulaire import LANGUES
from casa import aujourdhui_en_html, aujourd_hui_paris
from accords_vins import profils_du_repas, suggerer
from budget import semaines_budget, moyenne_precedentes, lundi, budget_en_html, SEMAINES
from cave import valider_bouteille, cave_en_html
from sortir import sortir_en_html
from courses import valider_article, valider_placard, courses_en_html, normaliser, deviner_rayon
from prix_paris import cout_repas
from fiche_recette import decouper
from diners import (avec_achats_recents, FRAIS_JOURS, disponibles, a_acheter_aujourd_hui, valider_plat, valider_repas, secours, a_acheter, compteur, semaine, diners_en_html,
                    proposer, proposer_cases, accompagner, cout_semaine, repas_prevus, ranger, nettoyer_accords, LIVRAISON_DEUX, FENETRE_PASSE, FENETRE_FUTUR)
from a_finir import suivis, alertes, plats_qui_utilisent, ENCORE_BON_JOURS
from uuid import uuid4

load_dotenv(Path(__file__).parent / ".env")   # en local : lit voyage/.env s'il existe


def articles_et_achats_recents(conn, articles, jour, achats=None):
    """La liste de courses, plus ce qui a été acheté ces FRAIS_JOURS derniers jours (voir avec_achats_recents).
    `achats` : le journal déjà lu (au moins sur ces FRAIS_JOURS jours), sinon on le lit.
    Un acheté qui est revenu sur la liste à prendre (actif, pas pris) n'est pas à la maison : il n'est pas ajouté."""
    debut = jour - timedelta(days=FRAIS_JOURS - 1)
    if achats is None:
        achats = lire_achats(conn, debut, jour)
    a_reprendre = {normaliser(a["nom"]) for a in articles if a["actif"] and not a["pris"]}
    noms = [a["nom"] for a in achats if a["jour"] >= debut and normaliser(a["nom"]) not in a_reprendre]
    return avec_achats_recents(articles, noms)


def alertes_du_frigo(conn, jour, plats, lu, articles):
    """(produits suivis, alertes du jour) — a_finir.py : le frais daté, et ce qu'aucun repas prévu (d'aujourd'hui à
    FENETRE_FUTUR) n'utilise à temps. `lu` : lire_courses ; `articles` : articles_et_achats_recents."""
    frais = lire_frais(conn)
    produits = suivis(frais["placard"], lu["articles"], frais["derniers_achats"], frais["corrections"])
    a_venir = lire_repas(conn, jour, jour + timedelta(days=FENETRE_FUTUR))
    return produits, alertes(produits, a_venir, plats, disponibles(lu["placard"], articles), jour)


def creer_app(nom_base="valise", secret=None):
    if secret is None:
        secret = os.environ.get("ACCES_SECRET", "")
    app = Flask(__name__)
    app.config["NOM_BASE"] = nom_base
    routes = Blueprint("valise", __name__)        # le groupe de routes, monté sous le préfixe secret

    @routes.get("/")
    def accueil():
        """Sans paramètre : Aujourd'hui (accueil du hub). Avec ?v=, ?nouvelle, ?modifier= : En Vadrouille,
        pour que les adresses déjà enregistrées sur les téléphones marchent toujours."""
        if not request.args:
            jour = aujourd_hui_paris()
            conn = emprunter(app.config["NOM_BASE"])
            try:
                repas = lire_repas(conn, jour - timedelta(days=FENETRE_PASSE), jour)
                plats = {p["id"]: p for p in lire_plats(conn)}
                diners = {r["jour"]: r for r in repas if r["moment"] == "diner"}
                ce_soir = ranger([plats[i] for i in diners.get(jour, {"plats": []})["plats"] if i in plats], "diner")
                veille = jour - timedelta(days=1)
                hier = diners.get(veille, {"jour": veille, "moment": "diner", "plats": [], "issue": None})
                du_jour = [plats[i] for r in repas if r["jour"] == jour and not r["issue"] for i in r["plats"] if i in plats]
                lu = lire_courses(conn)
                # Une seule lecture du journal : la semaine en cours (budget) et les derniers jours (à la maison)
                achats = lire_achats(conn, min(lundi(jour), jour - timedelta(days=FRAIS_JOURS - 1)), jour)
                cette_semaine = semaines_budget([a for a in achats if a["jour"] >= lundi(jour)], repas, plats, jour, n=1)[0]
                articles = articles_et_achats_recents(conn, lu["articles"], jour, achats)
                _, a_finir = alertes_du_frigo(conn, jour, list(plats.values()), lu, articles)
                soir = diners.get(jour)
                vins, belle = [], None
                if soir and soir["plats"] and not soir["issue"]:          # un dîner prévu, pas encore passé
                    cave = lire_cave(conn)
                    principal, secondaires = profils_du_repas(ce_soir)
                    vins = suggerer(cave, principal, secondaires, jour)
                    belles = [b for b in suggerer(cave, principal, secondaires, jour, belle=True)
                              if b["id"] not in {v["id"] for v in vins}]
                    belle = belles[0] if belles else None
                try:
                    sortir = rappels(lire_sorties(conn), jour)
                except psycopg2.errors.UndefinedTable:      # table pas encore créée (appliquer_schema pas passé)
                    conn.rollback()
                    sortir = None
                html = aujourdhui_en_html(lister_voyages(conn), jour,
                                          a_acheter_aujourd_hui(du_jour, lu["placard"], articles),
                                          ce_soir, hier, compteur(repas, jour), cette_semaine, a_finir, vins, belle,
                                          sortir=sortir)
            finally:
                conn.close()
            return Response(html, mimetype="text/html")
        return vadrouille()

    @routes.get("/budget")
    def page_budget():
        """Le budget de la maison : 12 semaines de courses (journal des achats) et de repas (budget.py)."""
        jour = aujourd_hui_paris()
        debut = lundi(jour) - timedelta(weeks=SEMAINES - 1)
        conn = emprunter(app.config["NOM_BASE"])
        try:
            semaines = semaines_budget(lire_achats(conn, debut, jour), lire_repas(conn, debut, jour),
                                       {p["id"]: p for p in lire_plats(conn)}, jour)
        finally:
            conn.close()
        return Response(budget_en_html(semaines, moyenne_precedentes(semaines)), mimetype="text/html")

    # --- Casa Binomerie : dîners ---

    @routes.get("/diners")
    def page_diners():
        return Response(diners_en_html(), mimetype="text/html")

    @routes.get("/recettes")
    def page_recettes():
        return Response(diners_en_html("recettes"), mimetype="text/html")

    @routes.get("/api/diners")
    def lire_les_diners():
        """Tout ce que la page Dîners affiche ; le secours est calculé ici (logique testée en Python)."""
        jour = aujourd_hui_paris()
        conn = emprunter(app.config["NOM_BASE"])
        try:
            plats = lire_plats(conn)
            faits = compter_faits(conn)
            repas = lire_repas(conn, jour - timedelta(days=FENETRE_PASSE), jour + timedelta(days=FENETRE_FUTUR))
            lu = lire_courses(conn)
            articles = articles_et_achats_recents(conn, lu["articles"], jour)
            _, a_finir = alertes_du_frigo(conn, jour, plats, lu, articles)
        finally:
            conn.close()
        cles_a_finir = {a["cle"] for a in a_finir}
        faisables, presque = secours(plats, lu["placard"], articles, a_finir=cles_a_finir)
        par_id = {p["id"]: p for p in plats}
        jours = semaine(jour)
        prevus = repas_prevus(repas, par_id, jours)
        return jsonify({
            "aujourd_hui": jour.isoformat(), "semaine": [j.isoformat() for j in jours],
            "plats": [{**p, "cout": cout_repas(p["ingredients"], p["recette"]), "fiche": decouper(p["recette"]),
                       "faits": faits.get(p["id"], 0)} for p in plats],
            "repas": [{**r, "jour": r["jour"].isoformat()} for r in repas],
            "liste": sorted({normaliser(a["nom"]) for a in lu["articles"] if a["actif"] and not a["pris"]}),
            "livraison": LIVRAISON_DEUX, "cout_semaine": cout_semaine(prevus, lu["placard"], articles),
            "stock": sorted(disponibles(lu["placard"], articles)),
            "secours": {"faisables": [p["id"] for p in faisables],
                        "presque": [{"plat": x["plat"]["id"], "manquants": x["manquants"]} for x in presque]},
            "a_finir": plats_qui_utilisent(plats, cles_a_finir),
            "compteur": compteur(repas, jour)})

    @routes.post("/api/plats")
    def enregistrer_une_recette():
        try:
            plat = valider_plat(request.get_json(silent=True))
        except ValueError as e:
            return jsonify({"erreur": str(e)}), 400
        conn = emprunter(app.config["NOM_BASE"])
        try:
            if plat["accords"] is not None:           # seulement des accompagnements connus et non archivés
                plat["accords"] = nettoyer_accords(plat["accords"], {p["id"]: p for p in lire_plats(conn)})
            enregistrer_plat(conn, plat)
        finally:
            conn.close()
        return jsonify({"ok": True})

    @routes.post("/api/repas")
    def enregistrer_un_repas():
        corps = request.get_json(silent=True)
        try:
            repas = valider_repas(corps, aujourd_hui_paris())
        except ValueError as e:
            return jsonify({"erreur": str(e)}), 400
        conn = emprunter(app.config["NOM_BASE"])
        try:
            if not all(plat_existe(conn, i) for i in repas["plats"]):
                return jsonify({"erreur": "plat inconnu"}), 400
            if corps.get("si_libre") is True:           # le bouton d'À finir (page peut-être en cache) n'écrase rien
                pris = lire_repas(conn, repas["jour"], repas["jour"])
                if repas["jour"] < aujourd_hui_paris() or any(
                        r["moment"] == repas["moment"] and (r["plats"] or r["issue"]) for r in pris):
                    return jsonify({"erreur": "soir déjà pris"}), 409
            enregistrer_repas(conn, repas)
        finally:
            conn.close()
        return jsonify({"ok": True})

    @routes.post("/api/diners/courses")
    def courses_de_la_semaine():
        """Les ingrédients des repas prévus cette semaine, ni au placard ni déjà sur la liste."""
        jour = aujourd_hui_paris()
        conn = emprunter(app.config["NOM_BASE"])
        try:
            plats = {p["id"]: p for p in lire_plats(conn)}
            prevus = [p for r in repas_prevus(lire_repas(conn, jour, jour + timedelta(days=6)), plats, semaine(jour))
                      for p in r]
            lu = lire_courses(conn)
            ajoutes = []
            for nom, id_plat in a_acheter(prevus, lu["placard"], articles_et_achats_recents(conn, lu["articles"], jour)):
                enregistrer_article(conn, valider_article({"id": str(uuid4()), "nom": nom, "source": f"plat:{id_plat}"}))
                ajoutes.append(nom)
        finally:
            conn.close()
        return jsonify({"ok": True, "ajoutes": ajoutes})

    @routes.post("/api/diners/proposer")
    def proposer_la_semaine():
        """Complète la semaine (diners.proposer, un accompagnement par diners.accompagner) et enregistre les dîners proposés ; `remplacer` : jours à retirer."""
        corps = request.get_json(silent=True) or {}
        if "cases" in corps:
            return proposer_des_cases(corps)
        try:
            remplacer = [date.fromisoformat(j) for j in corps.get("remplacer", [])]
        except (TypeError, ValueError):
            return jsonify({"erreur": "remplacer invalide"}), 400
        jour = aujourd_hui_paris()
        conn = emprunter(app.config["NOM_BASE"])
        try:
            plats = lire_plats(conn)
            repas = lire_repas(conn, jour - timedelta(days=FENETRE_PASSE), jour + timedelta(days=6))
            lu = lire_courses(conn)
            _, a_finir = alertes_du_frigo(conn, jour, plats, lu, articles_et_achats_recents(conn, lu["articles"], jour))
            proposes = proposer(plats, repas, semaine(jour), jour, remplacer=remplacer,
                                a_finir=[(a["cle"], a["jusqu_au"]) for a in a_finir if a["etat"] == "a-finir"])
            menus = accompagner(proposes, plats, repas, semaine(jour))
            for j, ids in menus.items():
                enregistrer_repas(conn, {"jour": j, "moment": "diner", "plats": ids, "issue": None})
        finally:
            conn.close()
        return jsonify({"proposes": {j.isoformat(): id_plat for j, id_plat in proposes.items()},   # pages v38
                        "menus": {j.isoformat(): ids for j, ids in menus.items()}})

    def lire_cases(brut):
        """Liste d'objets {jour: iso, moment: diner|dejeuner} -> [(date, moment)] ; ValueError si invalide."""
        if not isinstance(brut, list):
            raise ValueError("liste attendue")
        cases = []
        for c in brut:
            if not isinstance(c, dict) or c.get("moment") not in ("diner", "dejeuner"):
                raise ValueError("case invalide")
            cases.append((date.fromisoformat(c.get("jour")), c["moment"]))
        return cases

    def proposer_des_cases(corps):
        """Propose des cases (midi/soir) : dîner = plat + accompagnement, déjeuner = plat seul ; enregistre chaque repas."""
        try:
            cases = lire_cases(corps["cases"])
            remplacer = lire_cases(corps.get("remplacer", []))
        except (TypeError, ValueError):
            return jsonify({"erreur": "cases invalides"}), 400
        jour = aujourd_hui_paris()
        conn = emprunter(app.config["NOM_BASE"])
        try:
            plats = lire_plats(conn)
            repas = lire_repas(conn, jour - timedelta(days=FENETRE_PASSE), jour + timedelta(days=6))
            lu = lire_courses(conn)
            _, a_finir = alertes_du_frigo(conn, jour, plats, lu, articles_et_achats_recents(conn, lu["articles"], jour))
            choix = proposer_cases(plats, repas, cases, jour, remplacer=remplacer,
                                   a_finir=[(a["cle"], a["jusqu_au"]) for a in a_finir if a["etat"] == "a-finir"])
            diners = {j: i for (j, m), i in choix.items() if m == "diner"}
            accomp = accompagner(diners, plats, repas, semaine(jour))
            menus = {}
            for (j, m), i in choix.items():
                ids = accomp[j] if m == "diner" else [i]
                enregistrer_repas(conn, {"jour": j, "moment": m, "plats": ids, "issue": None})
                menus[f"{j.isoformat()}|{m}"] = ids
        finally:
            conn.close()
        return jsonify({"menus": menus})

    # --- Casa Binomerie : courses et placard ---

    @routes.get("/courses")
    def page_courses():
        return Response(courses_en_html(), mimetype="text/html")

    @routes.get("/api/courses")
    def lire_les_courses():
        """La liste et le placard ; chaque élément du placard avec son rayon deviné (« À la maison » se range par rayon)."""
        conn = emprunter(app.config["NOM_BASE"])
        try:
            lu = lire_courses(conn)
        finally:
            conn.close()
        return jsonify({**lu, "placard": [{**p, "rayon": deviner_rayon(p["nom"])} for p in lu["placard"]]})

    @routes.post("/api/courses")
    def enregistrer_un_article():
        try:
            article = valider_article(request.get_json(silent=True))
        except ValueError as e:
            return jsonify({"erreur": str(e)}), 400
        conn = emprunter(app.config["NOM_BASE"])
        try:
            enregistrer_article(conn, article)
        finally:
            conn.close()
        return jsonify({"ok": True, "article": article})

    @routes.delete("/api/courses/<identifiant>")
    def supprimer_un_article(identifiant):
        conn = emprunter(app.config["NOM_BASE"])
        try:
            supprimer_article(conn, identifiant)
        finally:
            conn.close()
        return jsonify({"ok": True})

    @routes.post("/api/courses/vider")
    def vider_les_pris():
        conn = emprunter(app.config["NOM_BASE"])
        try:
            vider_pris(conn)
        finally:
            conn.close()
        return jsonify({"ok": True})

    @routes.post("/api/placard")
    def enregistrer_un_basique():
        try:
            basique = valider_placard(request.get_json(silent=True))
        except ValueError as e:
            return jsonify({"erreur": str(e)}), 400
        conn = emprunter(app.config["NOM_BASE"])
        try:
            enregistrer_placard(conn, basique)
        finally:
            conn.close()
        return jsonify({"ok": True})

    @routes.delete("/api/placard/<path:cle>")
    def retirer_un_basique(cle):
        conn = emprunter(app.config["NOM_BASE"])
        try:
            retirer_du_placard(conn, cle)
        finally:
            conn.close()
        return jsonify({"ok": True})

    # --- Casa Binomerie : la cave ---

    @routes.get("/cave")
    def page_cave():
        return Response(cave_en_html(), mimetype="text/html")

    @routes.get("/api/cave")
    def lire_la_cave():
        conn = emprunter(app.config["NOM_BASE"])
        try:
            return jsonify({"bouteilles": lire_cave(conn), "annee": aujourd_hui_paris().year})
        finally:
            conn.close()

    @routes.post("/api/cave")
    def enregistrer_une_bouteille():
        try:
            bouteille = valider_bouteille(request.get_json(silent=True), aujourd_hui_paris().year)
        except ValueError as e:
            return jsonify({"erreur": str(e)}), 400
        conn = emprunter(app.config["NOM_BASE"])
        try:
            enregistrer_bouteille(conn, bouteille)
        finally:
            conn.close()
        return jsonify({"ok": True, "bouteille": bouteille})

    @routes.post("/api/cave/<identifiant>/bue")
    def boire_une_bouteille(identifiant):
        conn = emprunter(app.config["NOM_BASE"])
        try:
            quantite = boire(conn, identifiant)
        finally:
            conn.close()
        if quantite is None:
            return jsonify({"erreur": "bouteille inconnue"}), 404
        return jsonify({"ok": True, "quantite": quantite})

    @routes.delete("/api/cave/<identifiant>")
    def retirer_une_bouteille(identifiant):
        conn = emprunter(app.config["NOM_BASE"])
        try:
            retiree = retirer_bouteille(conn, identifiant)
        finally:
            conn.close()
        if not retiree:
            return jsonify({"erreur": "bouteille inconnue"}), 404
        return jsonify({"ok": True})

    # ---------- Sortir : idées de sorties du couple ----------
    def _iso(s):
        """Une sortie prête pour le JSON : dates en ISO."""
        return {c: (v.isoformat() if c in ("debut", "fin", "le", "cree_le") and v is not None else v)
                for c, v in s.items()}

    @routes.get("/sortir")
    def page_sortir():
        return Response(sortir_en_html(), mimetype="text/html")

    @routes.get("/api/sorties")
    def lire_les_sorties():
        conn = emprunter(app.config["NOM_BASE"])
        try:
            return jsonify({"sorties": [_iso(s) for s in lire_sorties(conn)],
                            "aujourd_hui": aujourd_hui_paris().isoformat()})
        finally:
            conn.close()

    @routes.post("/api/sorties")
    def creer_une_sortie():
        conn = emprunter(app.config["NOM_BASE"])
        try:
            try:
                corps = request.get_json(silent=True)
                sortie = valider_sortie(corps if isinstance(corps, dict) else {}, aujourd_hui_paris())
                identifiant, cree = creer_sortie(conn, sortie)
            except (ValueError, TypeError) as e:
                conn.rollback()
                return jsonify({"erreur": str(e)}), 400
        finally:
            conn.close()
        if not cree:
            return jsonify({"id": identifiant, "doublon": True}), 409
        return jsonify({"id": identifiant}), 201

    @routes.post("/api/sorties/<identifiant>/avis")
    def avis_sur_une_sortie(identifiant):
        corps = request.get_json(silent=True)
        corps = corps if isinstance(corps, dict) else {}
        conn = emprunter(app.config["NOM_BASE"])
        try:
            try:
                if "avis" not in corps:      # avis null = retirer son avis ; absent = requête incomplète
                    raise ValueError("avis manquant")
                sortie = donner_avis(conn, identifiant, corps.get("qui"), corps["avis"])
            except (ValueError, TypeError) as e:
                conn.rollback()
                return jsonify({"erreur": str(e)}), 400
        finally:
            conn.close()
        if sortie is None:
            return jsonify({"erreur": "sortie inconnue"}), 404
        return jsonify(_iso(sortie))

    @routes.post("/api/sorties/<identifiant>")
    def maj_une_sortie(identifiant):
        corps = request.get_json(silent=True)
        corps = corps if isinstance(corps, dict) else {}
        conn = emprunter(app.config["NOM_BASE"])
        try:
            try:
                sortie = maj_sortie(conn, identifiant, corps)
            except (ValueError, TypeError) as e:
                conn.rollback()
                return jsonify({"erreur": str(e)}), 400
        finally:
            conn.close()
        if sortie is None:
            return jsonify({"erreur": "sortie inconnue"}), 404
        return jsonify(_iso(sortie))

    @routes.get("/api/sorties/weekend")
    def tirage_du_weekend():
        conn = emprunter(app.config["NOM_BASE"])
        try:
            tirage = tirer_weekend(lire_sorties(conn), aujourd_hui_paris(), random.Random())
        finally:
            conn.close()
        return jsonify({"tirage": [_iso(s) for s in tirage]})

    @routes.post("/api/a-finir/<path:cle>")
    def corriger_un_produit(cle):
        """[Fini] ou [Encore bon] sur un produit du frais suivi (a_finir.py)."""
        corps = request.get_json(silent=True)
        action = corps.get("action") if isinstance(corps, dict) else None
        if action not in ("fini", "encore-bon"):
            return jsonify({"erreur": "action inconnue"}), 400
        jour = aujourd_hui_paris()
        conn = emprunter(app.config["NOM_BASE"])
        try:
            frais = lire_frais(conn)
            produits = suivis(frais["placard"], lire_courses(conn)["articles"], frais["derniers_achats"],
                              frais["corrections"])
            if cle not in {p["cle"] for p in produits}:
                return jsonify({"erreur": "produit non suivi"}), 404
            if action == "fini":
                finir(conn, cle)
            else:
                corriger_a_finir(conn, cle, jour + timedelta(days=ENCORE_BON_JOURS))
        finally:
            conn.close()
        return jsonify({"ok": True})

    @routes.get("/vadrouille")
    def vadrouille():
        """Sans paramètre : la liste des voyages. ?v=<code> : la valise de ce voyage."""
        if "nouvelle" in request.args:                # formulaire de création (sans base)
            return Response(formulaire_en_html(), mimetype="text/html")
        if "modifier" in request.args:                # le même formulaire, prérempli
            conn = emprunter(app.config["NOM_BASE"])
            try:
                voyage = lire_voyage(conn, request.args["modifier"])
            finally:
                conn.close()
            if voyage is None:
                return f"Voyage inconnu : {request.args['modifier']}", 404
            return Response(formulaire_en_html(voyage), mimetype="text/html")
        code = request.args.get("v")
        conn = emprunter(app.config["NOM_BASE"])
        try:
            if code:
                html = page_du_voyage(conn, code)   # stockée, ou refaite depuis la photo
            else:
                html = accueil_en_html(lister_voyages(conn), date.today())
        finally:
            conn.close()
        if html is None:
            return f"Voyage inconnu : {code}", 404
        return Response(html, mimetype="text/html")

    @routes.get("/api/etat/<voyage>")
    def etat(voyage):
        conn = emprunter(app.config["NOM_BASE"])
        try:
            return jsonify(obtenir_etat(conn, voyage))
        finally:
            conn.close()

    @routes.post("/api/coche")
    def coche():
        corps = request.get_json(silent=True)
        if not corps or "cle" not in corps or "coche" not in corps:
            return jsonify({"erreur": "payload invalide"}), 400
        segments = corps["cle"].split("/", 3)
        if len(segments) != 4:
            return jsonify({"erreur": "payload invalide"}), 400
        voyage, proprietaire, theme, objet = segments
        conn = emprunter(app.config["NOM_BASE"])
        try:
            enregistrer_coche(conn, voyage, proprietaire, theme, objet, bool(corps["coche"]))
        finally:
            conn.close()
        return jsonify({"ok": True})

    @routes.get("/api/retours/<voyage>")
    def retours(voyage):
        conn = emprunter(app.config["NOM_BASE"])
        try:
            return jsonify(lire_retours(conn, voyage))
        finally:
            conn.close()

    @routes.post("/api/retour")
    def retour():
        """Un verdict de bilan. verdict = null -> on efface le verdict de cet objet."""
        corps = request.get_json(silent=True) or {}
        voyage = corps.get("voyage")
        proprietaire = corps.get("proprietaire")
        objet = (corps.get("objet") or "").strip()
        verdict = corps.get("verdict")
        quantite = corps.get("quantite_utilisee")
        if not voyage or not proprietaire or not objet:
            return jsonify({"erreur": "voyage, proprietaire et objet sont obligatoires"}), 400
        if verdict is not None and verdict not in VERDICTS:
            return jsonify({"erreur": f"verdict inconnu : {verdict}"}), 400
        if quantite is not None and (not isinstance(quantite, int) or quantite < 0):
            return jsonify({"erreur": "quantite_utilisee doit être un entier positif"}), 400
        conn = emprunter(app.config["NOM_BASE"])
        try:
            if verdict is None:
                supprimer_retour(conn, voyage, proprietaire, objet)
            else:
                enregistrer_retour(conn, voyage, proprietaire, objet, verdict, quantite)
        except psycopg2.errors.ForeignKeyViolation:          # voyage absent de la table voyages
            conn.rollback()
            return jsonify({"erreur": f"voyage inconnu : {voyage}"}), 400
        finally:
            conn.close()
        return jsonify({"ok": True})

    @routes.get("/api/meteo/<voyage>/fenetres")
    def meteo_fenetres(voyage):
        """Bouton météo, temps 1 : les prévisions que le navigateur doit demander à Open-Meteo."""
        conn = emprunter(app.config["NOM_BASE"])
        try:
            fenetres = fenetres_du_voyage(conn, voyage, date.today())
        finally:
            conn.close()
        if fenetres is None:
            return jsonify({"erreur": f"voyage inconnu : {voyage}"}), 404
        return jsonify({"fenetres": fenetres})

    @routes.post("/api/meteo/<voyage>")
    def meteo(voyage):
        """Bouton météo, temps 2 : régénère la valise avec les prévisions envoyées par le navigateur."""
        corps = request.get_json(silent=True) or {}
        ancienne_page = "previsions" not in corps     # bouton d'avant le 26/10 : POST vide
        recues = corps.get("previsions", {})
        if not isinstance(recues, dict):
            return jsonify({"erreur": "previsions attendues : {index d'étape: daily}"}), 400
        conn = emprunter(app.config["NOM_BASE"])
        try:
            resultat = actualiser_meteo(conn, voyage, date.today(), recues)   # republie la page
        finally:
            conn.close()
        if resultat is None:
            return jsonify({"erreur": f"voyage inconnu : {voyage}"}), 404
        if ancienne_page:                             # la page republiée porte le nouveau bouton
            return jsonify({"ok": True, "etapes_prevues": 0,
                            "erreurs": ["page mise à jour : recharge-la puis réessaie"]})
        return jsonify({"ok": True, **resultat})        # erreurs : raisons affichées par le bouton

    @routes.post("/api/voyages")
    def creer():
        """Formulaire de création : 201 + adresse de la valise, 409 s'il manque des normales."""
        conn = emprunter(app.config["NOM_BASE"])
        try:
            resultat = creer_voyage(conn, request.get_json(silent=True))
        except ValueError as exc:
            return jsonify({"erreur": str(exc)}), 400
        finally:
            conn.close()
        if "manquantes" in resultat:
            return jsonify(resultat), 409
        return jsonify({"code": resultat["code"], "url": "?v=" + quote(resultat["code"])}), 201

    def _en_json(valeur):
        """Decimal -> texte (« 12.13 »), date -> ISO : ce que le navigateur lit sans perte."""
        if isinstance(valeur, Decimal):
            return str(valeur)
        if isinstance(valeur, date):
            return valeur.isoformat()
        if isinstance(valeur, dict):
            return {k: _en_json(v) for k, v in valeur.items()}
        if isinstance(valeur, list):
            return [_en_json(v) for v in valeur]
        return valeur

    @routes.get("/api/depenses/<voyage>")
    def depenses(voyage):
        conn = emprunter(app.config["NOM_BASE"])
        try:
            v = lire_voyage(conn, voyage)
            if v is None:
                return jsonify({"erreur": "voyage inconnu"}), 404
            liste = lire_depenses(conn, voyage)
        finally:
            conn.close()
        return jsonify(_en_json({"depenses": liste, "solde": solde_depenses(liste, v["personnes"])}))

    @routes.post("/api/depenses")
    def nouvelle_depense():
        """Une dépense saisie sur le téléphone, déjà convertie en euros. Tout est vérifié."""
        corps = request.get_json(silent=True) or {}
        conn = emprunter(app.config["NOM_BASE"])
        try:
            v = lire_voyage(conn, corps.get("voyage"))
            if v is None:
                return jsonify({"erreur": "voyage inconnu"}), 404
            try:
                libelle = corps["libelle"].strip()
                montant, montant_eur = Decimal(str(corps["montant"])), Decimal(str(corps["montant_eur"]))
                jour = date.fromisoformat(corps["jour"])
                pour = list(corps["pour"])
                valide = (0 < len(libelle) <= 120 and 0 < montant < 10**12 and 0 <= montant_eur < 10**9
                          and re.fullmatch(r"[A-Z]{3}", str(corps["devise"])) is not None
                          and corps["paye_par"] in v["personnes"] and pour and set(pour) <= set(v["personnes"]))
            except (KeyError, TypeError, ValueError, AttributeError, InvalidOperation):
                valide = False
            if not valide:
                return jsonify({"erreur": "dépense invalide"}), 400
            ajouter_depense(conn, v["code"], libelle, montant, corps["devise"], montant_eur, corps["paye_par"],
                            pour, jour)
        finally:
            conn.close()
        return jsonify({"ok": True})

    @routes.delete("/api/depenses/<voyage>/<int:identifiant>")
    def retirer_depense(voyage, identifiant):
        conn = emprunter(app.config["NOM_BASE"])
        try:
            supprimer_depense(conn, voyage, identifiant)
        finally:
            conn.close()
        return jsonify({"ok": True})

    @routes.get("/api/reservations/<voyage>")
    def reservations(voyage):
        """Le carnet 🗓️ Programme : lu par la page à l'ouverture (et gardé hors ligne)."""
        conn = emprunter(app.config["NOM_BASE"])
        try:
            return jsonify(_en_json(lire_reservations(conn, voyage)))
        finally:
            conn.close()

    @routes.post("/api/reservations")
    def enregistrer_une_reservation():
        """Crée ou modifie (même id) une réservation. Tout est vérifié (programme.valider_reservation)."""
        try:
            r = valider_reservation(request.get_json(silent=True))
        except ValueError as erreur:
            return jsonify({"erreur": str(erreur)}), 400
        conn = emprunter(app.config["NOM_BASE"])
        try:
            v = lire_voyage(conn, r["voyage"])
            if v is None:
                return jsonify({"erreur": "voyage inconnu"}), 404
            if r["prix"] is not None and r["paye_par"] not in v["personnes"]:
                return jsonify({"erreur": "payeur inconnu"}), 400
            enregistrer_reservation(conn, r, v["personnes"])
        finally:
            conn.close()
        return jsonify({"ok": True})

    @routes.delete("/api/reservations/<voyage>/<identifiant>")
    def retirer_reservation(voyage, identifiant):
        conn = emprunter(app.config["NOM_BASE"])
        try:
            supprimer_reservation(conn, voyage, identifiant)
        finally:
            conn.close()
        return jsonify({"ok": True})

    @routes.get("/api/a-voir/<voyage>")
    def envies(voyage):
        """Les envies « 💡 À voir » du voyage (gardées hors ligne par la page)."""
        conn = emprunter(app.config["NOM_BASE"])
        try:
            return jsonify(_en_json(lire_a_voir(conn, voyage)))
        finally:
            conn.close()

    @routes.post("/api/a-voir")
    def enregistrer_une_envie():
        """Crée ou modifie (même id) une envie. Tout est vérifié (a_voir.valider_a_voir)."""
        try:
            e = valider_a_voir(request.get_json(silent=True))
        except ValueError as erreur:
            return jsonify({"erreur": str(erreur)}), 400
        conn = emprunter(app.config["NOM_BASE"])
        try:
            if lire_voyage(conn, e["voyage"]) is None:
                return jsonify({"erreur": "voyage inconnu"}), 404
            enregistrer_a_voir(conn, e)
        finally:
            conn.close()
        return jsonify({"ok": True})

    @routes.delete("/api/a-voir/<voyage>/<identifiant>")
    def retirer_envie(voyage, identifiant):
        conn = emprunter(app.config["NOM_BASE"])
        try:
            supprimer_a_voir(conn, voyage, identifiant)
        finally:
            conn.close()
        return jsonify({"ok": True})

    @routes.post("/api/a-voir/suggestions")
    def suggestions_a_voir():
        """Pages Wikivoyage téléchargées par le téléphone -> les lieux « Voir » et « Faire »."""
        pages = (request.get_json(silent=True) or {}).get("pages")
        if not isinstance(pages, list) or len(pages) > 4 or not all(
                isinstance(p, dict) and p.get("langue") in ("fr", "en") and isinstance(p.get("titre"), str)
                and len(p["titre"]) <= 300 and isinstance(p.get("texte"), str) and len(p["texte"]) <= 3_000_000
                for p in pages):
            return jsonify({"erreur": "pages invalides"}), 400
        suggestions, vus = [], set()
        for p in pages:
            for s in suggestions_depuis_wikitext(p["texte"], p["titre"], p["langue"]):
                if s["nom"].casefold() not in vus:
                    vus.add(s["nom"].casefold())
                    suggestions.append(s)
        return jsonify({"suggestions": suggestions})

    @routes.get("/api/souvenirs/<voyage>")
    def souvenirs(voyage):
        """🎁 Souvenirs : le carnet de proches, les souvenirs du voyage et ce qui a déjà été rapporté."""
        conn = emprunter(app.config["NOM_BASE"])
        try:
            return jsonify(_en_json(lire_souvenirs(conn, voyage)))
        finally:
            conn.close()

    @routes.post("/api/proches")
    def enregistrer_un_proche():
        """Crée ou modifie (même id) un proche du carnet (souvenirs.valider_proche)."""
        try:
            p = valider_proche(request.get_json(silent=True))
        except ValueError as erreur:
            return jsonify({"erreur": str(erreur)}), 400
        conn = emprunter(app.config["NOM_BASE"])
        try:
            enregistrer_proche(conn, p)
        finally:
            conn.close()
        return jsonify({"ok": True})

    @routes.post("/api/souvenirs")
    def enregistrer_un_souvenir():
        """Crée ou modifie (même id) un souvenir ; acheté, il tient sa dépense partagée à jour."""
        try:
            s = valider_souvenir(request.get_json(silent=True))
        except ValueError as erreur:
            return jsonify({"erreur": str(erreur)}), 400
        conn = emprunter(app.config["NOM_BASE"])
        try:
            v = lire_voyage(conn, s["voyage"])
            if v is None:
                return jsonify({"erreur": "voyage inconnu"}), 404
            if s["achete"] and s["paye_par"] not in v["personnes"]:
                return jsonify({"erreur": "payeur inconnu"}), 400
            try:
                enregistrer_souvenir(conn, s, v["personnes"])
            except ValueError as erreur:
                return jsonify({"erreur": str(erreur)}), 400
        finally:
            conn.close()
        return jsonify({"ok": True})

    @routes.delete("/api/souvenirs/<voyage>/<identifiant>")
    def retirer_souvenir(voyage, identifiant):
        conn = emprunter(app.config["NOM_BASE"])
        try:
            supprimer_souvenir(conn, voyage, identifiant)
        finally:
            conn.close()
        return jsonify({"ok": True})

    @routes.post("/api/voyages/<code>/archiver")
    def retirer(code):
        """Bouton « Retirer » : le voyage quitte l'accueil (archivé, rien n'est supprimé)."""
        conn = emprunter(app.config["NOM_BASE"])
        try:
            if lire_voyage(conn, code) is None:
                return jsonify({"erreur": f"voyage inconnu : {code}"}), 404
            archiver_voyage(conn, code)
        finally:
            conn.close()
        return jsonify({"ok": True})

    # --- Création en ligne : le téléphone appelle Open-Meteo, le serveur interprète ---
    @routes.get("/api/lieux")
    def lieux_url():
        """L'adresse de recherche d'une destination, à appeler par le navigateur."""
        nom = (request.args.get("nom") or "").strip()
        if not nom:
            return jsonify({"erreur": "nom de destination manquant"}), 400
        return jsonify({"url": url_geocodage(nom)})

    @routes.post("/api/lieux")
    def lieux_interpretes():
        """La réponse brute du géocodage -> un lieu par pays, avec libellé."""
        corps = request.get_json(silent=True) or {}
        if not isinstance(corps.get("reponse"), dict):
            return jsonify({"erreur": "reponse attendue : le JSON du géocodage"}), 400
        return jsonify({"lieux": lieux_depuis_reponse(corps["reponse"])})

    def _lieu_et_mois(source):
        """(latitude, longitude, mois) valides, ou None."""
        try:
            lat, lon, mois = float(source["latitude"]), float(source["longitude"]), int(source["mois"])
        except (KeyError, TypeError, ValueError):
            return None
        return (lat, lon, mois) if 1 <= mois <= 12 else None

    @routes.get("/api/normales")
    def normales_cache():
        """Normales en cache, ou l'adresse de l'historique à télécharger par le navigateur."""
        lieu = _lieu_et_mois(request.args)
        if lieu is None:
            return jsonify({"erreur": "latitude, longitude et mois (1-12) attendus"}), 400
        conn = emprunter(app.config["NOM_BASE"])
        try:
            return jsonify(normales_ou_url(conn, *lieu))
        finally:
            conn.close()

    @routes.post("/api/normales")
    def normales_recues():
        """L'historique téléchargé par le navigateur -> normales calculées et mises en cache."""
        corps = request.get_json(silent=True) or {}
        lieu = _lieu_et_mois(corps)
        if lieu is None:
            return jsonify({"erreur": "latitude, longitude et mois (1-12) attendus"}), 400
        conn = emprunter(app.config["NOM_BASE"])
        try:
            n = normales_depuis_historique(conn, *lieu, corps.get("daily"))
        finally:
            conn.close()
        if n is None:
            return jsonify({"erreur": "historique illisible"}), 400
        return jsonify({"normales": n})

    # PWA : manifeste, worker et icônes à côté des pages (adresses relatives, même portée)
    @routes.get("/manifest.webmanifest")
    def manifeste_pwa():
        return Response(json.dumps(manifeste(), ensure_ascii=False), mimetype="application/manifest+json")

    @routes.get("/sw.js")
    def service_worker():
        reponse = Response(script_service_worker(VERSION_PAGE), mimetype="text/javascript")
        reponse.headers["Cache-Control"] = "no-cache"
        return reponse

    @routes.get("/icone-<int:taille>.png")
    def icone(taille):
        if taille not in TAILLES_ICONE:
            abort(404)
        return send_from_directory(Path(__file__).parent / "static", f"icone-{taille}.png", mimetype="image/png")

    @routes.get("/audio/<code>/<nom>.mp3")
    def audio(code, nom):
        """Le son d'une phrase du vocabulaire (généré par generer_audios.py)."""
        if code not in LANGUES or not re.fullmatch(r"[a-z0-9_-]{1,40}", nom):
            abort(404)
        return send_from_directory(Path(__file__).parent / "static" / "audio" / code, f"{nom}.mp3",
                                   mimetype="audio/mpeg", max_age=86400)

    # Avec un secret, tout vit sous /v/<secret>/ : sans le code, chaque adresse renvoie 404
    app.register_blueprint(routes, url_prefix=f"/v/{secret}" if secret else None)
    return app


app = creer_app()                                 # point d'entrée pour gunicorn (Render) : "serveur:app"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))      # pas 5000 : pris par le récepteur AirPlay de macOS
    app.run(host="0.0.0.0", port=port)
