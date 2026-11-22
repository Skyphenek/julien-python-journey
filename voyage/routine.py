"""L'accès de la routine « Vadrouille propositions » : lire les créneaux à remplir, déposer des fiches, dire « fini ».

Un jeton à part (ROUTINE_TOKEN), jamais le secret de la Casa : la routine lit des sites inconnus avec un réseau ouvert,
elle ne doit rien pouvoir lire ni écrire d'autre. Les champs rendus sont une liste blanche."""
import hmac

from flask import Blueprint, jsonify, request

from casa import aujourd_hui_paris
from db import (creer_proposition, emprunter, lire_a_voir, lire_passages, lire_propositions, lire_reservations,
                lister_voyages, marquer_passage)
from propositions import PAR_PASSAGE, a_chercher, creneaux, jours_du_voyage, passage_du, valider_proposition
from sortir import doublon

JETON_MINIMUM = 32
CHAMPS_CRENEAU = ("id", "periode", "debut", "fin", "ancre", "adresse", "destination", "places")
CHAMPS_PREVU = ("type", "titre", "lieu", "heure")


def _contexte(conn, v, jour):
    """Le passage dû de ce voyage et ce qu'il faut pour le faire, ou None."""
    if not v["etapes"]:
        return None
    reservations = lire_reservations(conn, v["code"])
    voyage = {"depart": v["depart"], "itineraire": v["etapes"]}
    palier = passage_du(jours_du_voyage(voyage, reservations), lire_passages(conn, v["code"]), jour)
    if palier is None:
        return None
    propositions = lire_propositions(conn, v["code"])
    return {"palier": palier, "reservations": reservations, "propositions": propositions,
            "envies": lire_a_voir(conn, v["code"]),
            "reste": PAR_PASSAGE - sum(p["passage"] == palier for p in propositions),
            "creneaux": a_chercher(creneaux(voyage, reservations), propositions, palier, jour)}


def _deja_vus(c):
    """Tout ce qui ne doit pas être proposé (à nouveau) ; le lien d'une réservation reste privé."""
    return ([{"id": p["id"], "titre": p["titre"], "lien": p["lien"]} for p in c["propositions"]]
            + [{"id": e["id"], "titre": e["nom"], "lien": e["lien"]} for e in c["envies"]]
            + [{"id": r["id"], "titre": r["titre"], "lien": ""} for r in c["reservations"]])


def routes_routine(app, jeton):
    routes = Blueprint("routine", __name__, url_prefix="/routine")

    @routes.before_request
    def verifier():
        recu = request.headers.get("Authorization", "")
        if not hmac.compare_digest(recu.encode(), f"Bearer {jeton}".encode()):
            return jsonify({"erreur": "jeton invalide"}), 401

    def voyage_demande(conn, corps, jour):
        """Le contexte du voyage si le corps vise son passage dû, sinon None."""
        v = next((v for v in lister_voyages(conn) if v["code"] == corps.get("voyage")), None)
        c = _contexte(conn, v, jour) if v else None
        return c if c and c["palier"] == corps.get("palier") else None

    @routes.get("/travail")
    def travail():
        jour = aujourd_hui_paris()
        conn = emprunter(app.config["NOM_BASE"])
        try:
            for v in lister_voyages(conn):                       # le départ le plus proche d'abord
                c = _contexte(conn, v, jour)
                if c is None or not c["creneaux"] or c["reste"] <= 0:
                    continue
                lieux = {e["destination"]: e for e in v["etapes"]}
                return jsonify({"a_faire": {
                    "voyage": v["code"], "palier": c["palier"], "reste": c["reste"],
                    "creneaux": [{**{k: x[k] for k in CHAMPS_CRENEAU}, "jour": x["jour"].isoformat(),
                                  "latitude": lieux[x["destination"]].get("latitude"),
                                  "longitude": lieux[x["destination"]].get("longitude")} for x in c["creneaux"]],
                    "deja_prevu": [{**{k: r[k] for k in CHAMPS_PREVU}, "jour": r["jour"].isoformat()}
                                   for r in c["reservations"]],
                    "ne_pas_reproposer": [{"titre": x["titre"], "lien": x["lien"]} for x in _deja_vus(c)]}})
        finally:
            conn.close()
        return jsonify({"a_faire": None})

    @routes.post("/propositions")
    def deposer():
        corps, jour = request.get_json(silent=True), aujourd_hui_paris()
        try:
            p = valider_proposition(corps)
        except ValueError as erreur:
            return jsonify({"erreur": str(erreur)}), 400
        conn = emprunter(app.config["NOM_BASE"])
        try:
            c = voyage_demande(conn, corps, jour)
            if c is None:
                return jsonify({"erreur": "pas le passage dû"}), 409
            if c["reste"] <= 0:
                return jsonify({"erreur": f"{PAR_PASSAGE} fiches au plus par passage"}), 409
            creneau = next((x for x in c["creneaux"] if x["id"] == corps.get("creneau")), None)
            if creneau is None:
                return jsonify({"erreur": "créneau inconnu ou plein"}), 409
            if doublon(p, _deja_vus(c)):
                return jsonify({"erreur": "déjà proposé ou déjà prévu"}), 409
            place = {k: creneau[k] for k in ("jour", "periode", "debut", "fin", "ancre", "destination", "rang")}
            identifiant = creer_proposition(conn, corps["voyage"], c["palier"], {
                **p, **place, "creneau": creneau["id"], "verifie_le": jour if p["source"] else None})
        finally:
            conn.close()
        return jsonify({"id": identifiant}), 201

    @routes.post("/fini")
    def fini():
        corps = request.get_json(silent=True)
        conn = emprunter(app.config["NOM_BASE"])
        try:
            if not isinstance(corps, dict) or voyage_demande(conn, corps, aujourd_hui_paris()) is None:
                return jsonify({"erreur": "pas le passage dû"}), 409
            marquer_passage(conn, corps["voyage"], corps["palier"])
        finally:
            conn.close()
        return jsonify({"ok": True})

    return routes
