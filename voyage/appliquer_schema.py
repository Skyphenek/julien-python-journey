"""Applique schema.sql (idempotent : CREATE … IF NOT EXISTS) et montre les tables créées.

À lancer AVANT le merge d'une branche qui ajoute une table ou une colonne :
    .venv/bin/python3 appliquer_schema.py                 # à blanc : montre ce qui serait créé
    .venv/bin/python3 appliquer_schema.py --appliquer     # le fait (Neon si DATABASE_URL dans .env)
"""
import argparse
from pathlib import Path

from dotenv import load_dotenv

from carnet_depart import CARNET_DEPART, A_TESTER
from courses import PLACARD_DEPART
from db import connecter, semer_placard, semer_carnet

load_dotenv(Path(__file__).parent / ".env")


def tables(cur):
    cur.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
    return {ligne[0] for ligne in cur.fetchall()}


def appliquer(conn, pour_de_bon):
    with conn.cursor() as cur:
        avant = tables(cur)
        cur.execute((Path(__file__).parent / "schema.sql").read_text())
        nouvelles = sorted(tables(cur) - avant)
    if pour_de_bon:
        conn.commit()
        print(f"Schéma appliqué ; table(s) créée(s) : {', '.join(nouvelles) or 'aucune'}.")
        semes = semer_placard(conn, PLACARD_DEPART)        # placard vide seulement : jamais d'écrasement
        if semes:
            print(f"Placard de départ : {semes} basiques, tous en stock.")
        recettes = semer_carnet(conn, CARNET_DEPART, A_TESTER)    # carnet vide seulement
        if recettes:
            print(f"Carnet de départ : {recettes} recettes ({len(CARNET_DEPART)} au carnet, {len(A_TESTER)} à tester).")
    else:
        conn.rollback()
        print(f"À blanc : table(s) à créer : {', '.join(nouvelles) or 'aucune'}. Relance avec --appliquer.")


if __name__ == "__main__":
    arguments = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    arguments.add_argument("--base", default="valise")
    arguments.add_argument("--appliquer", action="store_true")
    options = arguments.parse_args()
    connexion = connecter(options.base)
    try:
        appliquer(connexion, options.appliquer)
    finally:
        connexion.close()
