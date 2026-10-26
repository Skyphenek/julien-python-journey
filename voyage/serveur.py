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

from db import (connecter, obtenir_etat, enregistrer_coche, lire_page,
                VERDICTS, enregistrer_retour, supprimer_retour, lire_retours)
from valise import actualiser_meteo

load_dotenv(Path(__file__).parent / ".env")   # en local : lit voyage/.env s'il existe


def creer_app(nom_base="valise", secret=None):
    if secret is None:
        secret = os.environ.get("ACCES_SECRET", "")
    app = Flask(__name__)
    app.config["NOM_BASE"] = nom_base
    routes = Blueprint("valise", __name__)        # le groupe de routes, monté sous le préfixe secret

    @routes.get("/")
    def accueil():
        conn = connecter(app.config["NOM_BASE"])
        try:
            html = lire_page(conn)                # page publiée par valise.py
        finally:
            conn.close()
        if html is None:                          # rien en base : ancien fonctionnement (fichier local)
            chemin = Path(__file__).parent / "valise.html"
            if not chemin.exists():
                return "Aucune valise publiée : lance valise.py.", 404
            html = chemin.read_text(encoding="utf-8")
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

    @routes.post("/api/meteo/<voyage>")
    def meteo(voyage):
        """Bouton météo : régénère la valise de ce voyage avec les prévisions du jour."""
        conn = connecter(app.config["NOM_BASE"])
        try:
            resultat = actualiser_meteo(conn, voyage, date.today())
        finally:
            conn.close()
        if resultat is None:
            return jsonify({"erreur": f"voyage inconnu : {voyage}"}), 404
        return jsonify({"ok": True, **resultat})        # erreurs : raisons affichées par le bouton

    # Avec un secret, tout vit sous /v/<secret>/ : sans le code, chaque adresse renvoie 404
    app.register_blueprint(routes, url_prefix=f"/v/{secret}" if secret else None)
    return app


app = creer_app()                                 # point d'entrée pour gunicorn (Render) : "serveur:app"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))      # pas 5000 : pris par le récepteur AirPlay de macOS
    app.run(host="0.0.0.0", port=port)
