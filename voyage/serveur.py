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
from datetime import date
from pathlib import Path
from urllib.parse import quote

import psycopg2

from dotenv import load_dotenv
from flask import Blueprint, Flask, abort, jsonify, request, Response, send_from_directory

from db import (emprunter, ajouter_depense, lire_depenses, supprimer_depense, obtenir_etat,
                enregistrer_reservation, lire_reservations, supprimer_reservation,
                enregistrer_a_voir, lire_a_voir, supprimer_a_voir, enregistrer_proche, enregistrer_souvenir,
                lire_souvenirs, supprimer_souvenir, enregistrer_coche, lister_voyages, lire_voyage, archiver_voyage,
                VERDICTS, enregistrer_retour, supprimer_retour, lire_retours)
from valise import (solde_depenses, actualiser_meteo, fenetres_du_voyage, page_du_voyage, accueil_en_html,
                    lieux_depuis_reponse, normales_ou_url, normales_depuis_historique,
                    formulaire_en_html, creer_voyage, VERSION_PAGE)
from api_climat import url_geocodage
from pwa import manifeste, script_service_worker, TAILLES_ICONE
from programme import valider_reservation
from a_voir import valider_a_voir, suggestions_depuis_wikitext
from souvenirs import valider_proche, valider_souvenir
from vocabulaire import LANGUES

load_dotenv(Path(__file__).parent / ".env")   # en local : lit voyage/.env s'il existe


def creer_app(nom_base="valise", secret=None):
    if secret is None:
        secret = os.environ.get("ACCES_SECRET", "")
    app = Flask(__name__)
    app.config["NOM_BASE"] = nom_base
    routes = Blueprint("valise", __name__)        # le groupe de routes, monté sous le préfixe secret

    @routes.get("/")
    def accueil():
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
            if lire_voyage(conn, r["voyage"]) is None:
                return jsonify({"erreur": "voyage inconnu"}), 404
            enregistrer_reservation(conn, r)
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
