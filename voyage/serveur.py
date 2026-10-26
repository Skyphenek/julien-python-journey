"""Serveur Flask : sert la checklist HTML et expose l'état en API Postgres.

Même code en local (Mac) et en ligne (Render) ; seules les variables d'environnement changent :
- DATABASE_URL  : base en ligne (sinon base locale "valise")
- ACCES_SECRET  : code secret ; toutes les routes passent sous /v/<secret>/ (sinon à la racine)
- PORT          : imposé par l'hébergeur (sinon 8000)
"""
import os
from datetime import date
from pathlib import Path

import psycopg2

from dotenv import load_dotenv
from flask import Blueprint, Flask, jsonify, request, Response

from db import (connecter, obtenir_etat, enregistrer_coche, lister_voyages,
                VERDICTS, enregistrer_retour, supprimer_retour, lire_retours)
from valise import (actualiser_meteo, fenetres_du_voyage, page_du_voyage, accueil_en_html,
                    lieux_depuis_reponse, normales_ou_url, normales_depuis_historique)
from api_climat import url_geocodage

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
        code = request.args.get("v")
        conn = connecter(app.config["NOM_BASE"])
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
        conn = connecter(app.config["NOM_BASE"])
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
        conn = connecter(app.config["NOM_BASE"])
        try:
            enregistrer_coche(conn, voyage, proprietaire, theme, objet, bool(corps["coche"]))
        finally:
            conn.close()
        return jsonify({"ok": True})

    @routes.get("/api/retours/<voyage>")
    def retours(voyage):
        conn = connecter(app.config["NOM_BASE"])
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
        conn = connecter(app.config["NOM_BASE"])
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
        conn = connecter(app.config["NOM_BASE"])
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
        conn = connecter(app.config["NOM_BASE"])
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
        conn = connecter(app.config["NOM_BASE"])
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
        conn = connecter(app.config["NOM_BASE"])
        try:
            n = normales_depuis_historique(conn, *lieu, corps.get("daily"))
        finally:
            conn.close()
        if n is None:
            return jsonify({"erreur": "historique illisible"}), 400
        return jsonify({"normales": n})

    # Avec un secret, tout vit sous /v/<secret>/ : sans le code, chaque adresse renvoie 404
    app.register_blueprint(routes, url_prefix=f"/v/{secret}" if secret else None)
    return app


app = creer_app()                                 # point d'entrée pour gunicorn (Render) : "serveur:app"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))      # pas 5000 : pris par le récepteur AirPlay de macOS
    app.run(host="0.0.0.0", port=port)
