"""Serveur Flask : sert la checklist HTML et expose l'état en API Postgres."""
from pathlib import Path

from flask import Flask, jsonify, request, Response

from db import connecter, obtenir_etat, enregistrer_coche


def creer_app(nom_base="valise"):
    app = Flask(__name__)
    app.config["NOM_BASE"] = nom_base

    @app.get("/")
    def accueil():
        chemin = Path(__file__).parent / "valise.html"
        return Response(chemin.read_text(encoding="utf-8"), mimetype="text/html")

    @app.get("/api/etat/<voyage>")
    def etat(voyage):
        conn = connecter(app.config["NOM_BASE"])
        try:
            return jsonify(obtenir_etat(conn, voyage))
        finally:
            conn.close()

    @app.post("/api/coche")
    def coche():
        corps = request.get_json(silent=True)
        if not corps or "cle" not in corps or "coche" not in corps:
            return jsonify({"erreur": "payload invalide"}), 400
        voyage, proprietaire, theme, objet = corps["cle"].split("/")
        conn = connecter(app.config["NOM_BASE"])
        try:
            enregistrer_coche(conn, voyage, proprietaire, theme, objet, bool(corps["coche"]))
        finally:
            conn.close()
        return jsonify({"ok": True})

    return app


if __name__ == "__main__":
    app = creer_app()
    app.run(host="0.0.0.0", port=5000)
