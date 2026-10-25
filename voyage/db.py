"""Accès Postgres : état de la checklist (coché / pas coché) et cache des normales climatiques."""
import psycopg2


def connecter(nom_base="valise"):
    """Ouvre une connexion à la base Postgres locale (auth système, pas de mot de passe)."""
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
