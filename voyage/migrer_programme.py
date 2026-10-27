"""Migration du carnet 🗓️ Programme : crée la table reservations et y reprend les anciennes
fiches d'étapes (infos_etape) en réservations « Hôtel ».

À lancer AVANT le merge (sinon l'appli en ligne plante sur une table absente) :
    .venv/bin/python3 migrer_programme.py                # à blanc : montre ce qui serait fait
    .venv/bin/python3 migrer_programme.py --appliquer    # le fait (Neon si DATABASE_URL dans .env)
    .venv/bin/python3 migrer_programme.py --base valise_test --appliquer   # une base locale précise

Rejouable : une fiche déjà reprise (même id) n'est ni doublée ni écrasée. infos_etape est gardée.
"""
import argparse
from pathlib import Path

from dotenv import load_dotenv

from db import connecter, lire_voyage, lire_infos_etapes, CHAMPS_RESERVATION
from programme import hotels_depuis_infos

load_dotenv(Path(__file__).parent / ".env")


def migrer(conn, appliquer):
    with conn.cursor() as cur:
        cur.execute((Path(__file__).parent / "schema.sql").read_text())     # idempotent (IF NOT EXISTS)
        cur.execute("SELECT DISTINCT voyage FROM infos_etape ORDER BY voyage")
        codes = [ligne[0] for ligne in cur.fetchall()]
    hotels = []
    for code in codes:
        voyage = lire_voyage(conn, code)
        if voyage is not None:
            hotels += hotels_depuis_infos(code, voyage["itineraire"], voyage["depart"], lire_infos_etapes(conn, code))
    for h in hotels:
        print(f"  {h['voyage']} · 🏨 {h['titre']} · {h['jour']:%d/%m} → {h['jour_fin']:%d/%m}")
    repris = 0
    with conn.cursor() as cur:
        for h in hotels:
            cur.execute(f"""INSERT INTO reservations (id, voyage, {", ".join(CHAMPS_RESERVATION)})
                            VALUES (%s, %s, {", ".join(["%s"] * len(CHAMPS_RESERVATION))})
                            ON CONFLICT (id) DO NOTHING""",
                        (h["id"], h["voyage"], *(h[c] for c in CHAMPS_RESERVATION)))
            repris += cur.rowcount
    if appliquer:
        conn.commit()
        print(f"Table reservations prête ; {repris} fiche(s) reprise(s) sur {len(hotels)} (les autres l'étaient déjà).")
    else:
        conn.rollback()
        print(f"À blanc : {len(hotels)} fiche(s) à reprendre. Relance avec --appliquer pour le faire.")


if __name__ == "__main__":
    arguments = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    arguments.add_argument("--base", default="valise")
    arguments.add_argument("--appliquer", action="store_true")
    options = arguments.parse_args()
    connexion = connecter(options.base)
    try:
        migrer(connexion, options.appliquer)
    finally:
        connexion.close()
