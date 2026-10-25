"""Accès Postgres : état de la checklist (coché / pas coché) et cache des normales climatiques."""
import os

import psycopg2


def connecter(nom_base="valise"):
    """Ouvre une connexion Postgres.

    - Base "valise" + variable DATABASE_URL définie -> la base en ligne (Neon).
    - Sinon -> la base locale du Mac (auth système, pas de mot de passe).
    Garde-fou : "valise_test" est TOUJOURS locale, les tests ne peuvent pas toucher au cloud.
    """
    url = os.environ.get("DATABASE_URL")
    if url and nom_base == "valise":
        return psycopg2.connect(url)
    return psycopg2.connect(dbname=nom_base)


def obtenir_etat(conn, voyage):
    """Renvoie {"voyage/proprietaire/theme/objet": True/False} pour ce voyage."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT proprietaire, theme, objet, coche FROM etat_case WHERE voyage = %s",
            (voyage,),
        )
        lignes = cur.fetchall()
    return {
        f"{voyage}/{proprietaire}/{theme}/{objet}": coche
        for proprietaire, theme, objet, coche in lignes
    }


def enregistrer_coche(conn, voyage, proprietaire, theme, objet, coche):
    """Upsert l'état d'une case (une seule clé à la fois, jamais tout l'état)."""
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO etat_case (voyage, proprietaire, theme, objet, coche, maj_le)
            VALUES (%s, %s, %s, %s, %s, now())
            ON CONFLICT (voyage, proprietaire, theme, objet)
            DO UPDATE SET coche = EXCLUDED.coche, maj_le = now()
            """,
            (voyage, proprietaire, theme, objet, coche),
        )
    conn.commit()


def lire_normales(conn, latitude, longitude, mois):
    """Normales en cache pour ce lieu et ce mois, ou None si jamais calculées."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT tmin, tmax, jours_pluie, jours_forte_pluie FROM normales_climat
            WHERE latitude = %s AND longitude = %s AND mois = %s
            """,
            (round(latitude, 2), round(longitude, 2), mois),
        )
        ligne = cur.fetchone()
    if ligne is None:
        return None
    tmin, tmax, jours_pluie, jours_forte_pluie = ligne
    return {"tmin": tmin, "tmax": tmax, "jours_pluie": jours_pluie,
            "jours_forte_pluie": jours_forte_pluie}


def enregistrer_normales(conn, latitude, longitude, normales_par_mois):
    """Upsert des normales d'un lieu, un dict {mois: normales} (en pratique les 12 mois)."""
    with conn.cursor() as cur:
        for mois, n in normales_par_mois.items():
            cur.execute(
                """
                INSERT INTO normales_climat
                    (latitude, longitude, mois, tmin, tmax, jours_pluie, jours_forte_pluie, calcule_le)
                VALUES (%s, %s, %s, %s, %s, %s, %s, now())
                ON CONFLICT (latitude, longitude, mois)
                DO UPDATE SET tmin = EXCLUDED.tmin, tmax = EXCLUDED.tmax,
                              jours_pluie = EXCLUDED.jours_pluie,
                              jours_forte_pluie = EXCLUDED.jours_forte_pluie,
                              calcule_le = now()
                """,
                (round(latitude, 2), round(longitude, 2), mois,
                 n["tmin"], n["tmax"], n["jours_pluie"], n["jours_forte_pluie"]),
            )
    conn.commit()


def publier_page(conn, html):
    """Enregistre la page de checklist courante (remplace la précédente)."""
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO page_valise (cle, html, maj_le) VALUES ('courante', %s, now())
            ON CONFLICT (cle) DO UPDATE SET html = EXCLUDED.html, maj_le = now()
            """,
            (html,),
        )
    conn.commit()


def lire_page(conn):
    """La page de checklist courante, ou None si rien n'a encore été publié."""
    with conn.cursor() as cur:
        cur.execute("SELECT html FROM page_valise WHERE cle = 'courante'")
        ligne = cur.fetchone()
    return ligne[0] if ligne else None
