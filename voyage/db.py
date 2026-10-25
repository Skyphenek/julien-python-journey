"""Accès Postgres à l'état de la checklist (coché / pas coché)."""
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
