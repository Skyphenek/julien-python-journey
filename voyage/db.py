"""Accès Postgres : état de la checklist (coché / pas coché) et cache des normales climatiques."""
import os

import time

import psycopg2
from psycopg2.extras import Json
from psycopg2.pool import ThreadedConnectionPool


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


def publier_page(conn, html, cle="courante"):
    """Enregistre la page de checklist d'un voyage (cle = son code) ; remplace la précédente."""
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO page_valise (cle, html, maj_le) VALUES (%s, %s, now())
            ON CONFLICT (cle) DO UPDATE SET html = EXCLUDED.html, maj_le = now()
            """,
            (cle, html),
        )
    conn.commit()


def lire_page(conn, cle="courante"):
    """La page de checklist d'un voyage (cle = son code), ou None si rien n'a été publié."""
    with conn.cursor() as cur:
        cur.execute("SELECT html FROM page_valise WHERE cle = %s", (cle,))
        ligne = cur.fetchone()
    return ligne[0] if ligne else None


def lister_voyages(conn):
    """Les voyages non archivés, par date de départ : de quoi afficher l'accueil."""
    from datetime import timedelta
    with conn.cursor() as cur:
        cur.execute("SELECT code, libelle, depart, personnes, itineraire FROM voyages "
                    "WHERE NOT archive ORDER BY depart, code")
        lignes = cur.fetchall()
    voyages = []
    for code, libelle, depart, personnes, itineraire in lignes:
        jours = sum(e.get("jours", 0) for e in itineraire)
        etapes = [{"destination": e.get("destination"), "jours": e.get("jours", 0),
                   "code_pays": e.get("code_pays"), "latitude": e.get("latitude"),
                   "longitude": e.get("longitude")} for e in itineraire]     # pour la carte de l'accueil
        voyages.append({"code": code, "libelle": libelle, "depart": depart,
                        "fin": depart + timedelta(days=max(jours, 1) - 1), "personnes": personnes,
                        "etapes": etapes})
    return voyages


def enregistrer_voyage(conn, code, libelle, depart, personnes, itineraire, jours_types,
                       conduit=False, lessive=None, cabine=False):
    """Upsert de l'identité et du contexte d'un voyage (régénérer = mettre à jour).

    conduit / lessive / cabine : les réglages qui permettent de reconstruire le voyage sans le terminal.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO voyages (code, libelle, depart, personnes, itineraire, jours_types, conduit, lessive,
                                 cabine)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (code) DO UPDATE SET
                libelle = EXCLUDED.libelle, depart = EXCLUDED.depart, personnes = EXCLUDED.personnes,
                itineraire = EXCLUDED.itineraire, jours_types = EXCLUDED.jours_types,
                conduit = EXCLUDED.conduit, lessive = EXCLUDED.lessive, cabine = EXCLUDED.cabine,
                maj_le = now()
            """,
            (code, libelle, depart, list(personnes), Json(itineraire), Json(jours_types),
             conduit, lessive, cabine),
        )
    conn.commit()


def lire_voyage(conn, code):
    """Le voyage sous forme de dict, ou None. JSONB et TEXT[] reviennent en dict / list Python."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT libelle, depart, personnes, itineraire, jours_types, conduit, lessive, cabine "
            "FROM voyages WHERE code = %s",
            (code,),
        )
        ligne = cur.fetchone()
    if ligne is None:
        return None
    libelle, depart, personnes, itineraire, jours_types, conduit, lessive, cabine = ligne
    return {"code": code, "libelle": libelle, "depart": depart, "personnes": personnes,
            "itineraire": itineraire, "jours_types": jours_types,
            "conduit": conduit, "lessive": lessive, "cabine": cabine}       # forme acceptée telle quelle par construire()


def enregistrer_valise_objets(conn, code, valise):
    """Remplace la photo de la valise de ce voyage ({proprietaire: {theme: {objet: quantite}}})."""
    with conn.cursor() as cur:
        cur.execute("DELETE FROM valise_objets WHERE voyage = %s", (code,))
        for proprietaire, themes in valise.items():
            for theme, objets in themes.items():
                for objet, quantite in objets.items():
                    cur.execute(
                        "INSERT INTO valise_objets (voyage, proprietaire, theme, objet, quantite) "
                        "VALUES (%s, %s, %s, %s, %s)",
                        (code, proprietaire, theme, objet, quantite),
                    )
    conn.commit()                     # DELETE + INSERT dans la même transaction : tout ou rien


def lire_valise_objets(conn, code):
    """{(proprietaire, theme, objet): quantite} pour ce voyage."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT proprietaire, theme, objet, quantite FROM valise_objets WHERE voyage = %s",
            (code,),
        )
        return {(p, t, o): q for p, t, o, q in cur.fetchall()}


VERDICTS = {"utile", "trop", "pas_servi", "manque"}


def enregistrer_retour(conn, voyage, proprietaire, objet, verdict, quantite_utilisee=None):
    """Upsert d'un verdict de bilan (changer d'avis = remplacer)."""
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO retours (voyage, proprietaire, objet, verdict, quantite_utilisee, maj_le)
            VALUES (%s, %s, %s, %s, %s, now())
            ON CONFLICT (voyage, proprietaire, objet) DO UPDATE SET
                verdict = EXCLUDED.verdict, quantite_utilisee = EXCLUDED.quantite_utilisee, maj_le = now()
            """,
            (voyage, proprietaire, objet, verdict, quantite_utilisee),
        )
    conn.commit()


def supprimer_retour(conn, voyage, proprietaire, objet):
    with conn.cursor() as cur:
        cur.execute("DELETE FROM retours WHERE voyage = %s AND proprietaire = %s AND objet = %s",
                    (voyage, proprietaire, objet))
    conn.commit()


def lire_retours(conn, voyage):
    """Les verdicts du voyage, triés (personne, objet) : liste de dicts prête pour du JSON."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT proprietaire, objet, verdict, quantite_utilisee FROM retours "
            "WHERE voyage = %s ORDER BY proprietaire, objet",
            (voyage,),
        )
        return [{"proprietaire": p, "objet": o, "verdict": v, "quantite_utilisee": q}
                for p, o, v, q in cur.fetchall()]


def archiver_voyage(conn, code):
    """Sortir un voyage de l'historique (essai, annulé) sans rien supprimer."""
    with conn.cursor() as cur:
        cur.execute("UPDATE voyages SET archive = true WHERE code = %s", (code,))
    conn.commit()


def lire_historique(conn, exclure=None):
    """Voyages passés non archivés, du plus récent au plus ancien, avec leur photo et leurs retours.
    exclure : le voyage en cours de préparation (il n'est pas son propre passé)."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT code, libelle, depart, jours_types FROM voyages "
            "WHERE NOT archive AND code IS DISTINCT FROM %s ORDER BY depart DESC",
            (exclure,),
        )
        voyages = cur.fetchall()
    return [{"code": code, "libelle": libelle, "depart": depart, "jours_types": jours_types,
             "objets": lire_valise_objets(conn, code), "retours": lire_retours(conn, code)}
            for code, libelle, depart, jours_types in voyages]


def ajouter_regle(conn, personne, objet, theme, quantite=1):
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO regles_perso (personne, objet, theme, quantite) VALUES (%s, %s, %s, %s) "
            "ON CONFLICT (personne, objet) DO NOTHING",
            (personne, objet, theme, quantite),
        )
    conn.commit()


def lire_regles(conn):
    """{personne: [{"objet", "theme", "quantite"}]} — les ajouts "toujours"."""
    with conn.cursor() as cur:
        cur.execute("SELECT personne, objet, theme, quantite FROM regles_perso ORDER BY personne, objet")
        regles = {}
        for personne, objet, theme, quantite in cur.fetchall():
            regles.setdefault(personne, []).append({"objet": objet, "theme": theme, "quantite": quantite})
    return regles


def enregistrer_passeport(conn, personne, expire_le):
    """Date d'expiration du passeport d'une personne (un renouvellement remplace l'ancienne)."""
    with conn.cursor() as cur:
        cur.execute(
            """INSERT INTO passeports (personne, expire_le) VALUES (%s, %s)
               ON CONFLICT (personne) DO UPDATE SET expire_le = EXCLUDED.expire_le, maj_le = now()""",
            (personne, expire_le))
    conn.commit()


def lire_passeports(conn):
    """{personne: date d'expiration}."""
    with conn.cursor() as cur:
        cur.execute("SELECT personne, expire_le FROM passeports")
        return dict(cur.fetchall())


def remplacer_voyage(conn, ancien, nouveau):
    """Voyage modifié dont le code a changé (date ou étapes) : les cases cochées, le bilan et les
    infos des étapes, les dépenses, les réservations, les envies « à voir » et les souvenirs suivent le nouveau code, puis l'ancien est archivé (rien n'est supprimé)."""
    with conn.cursor() as cur:
        cur.execute("""INSERT INTO etat_case (voyage, proprietaire, theme, objet, coche, maj_le)
                       SELECT %s, proprietaire, theme, objet, coche, maj_le FROM etat_case WHERE voyage = %s
                       ON CONFLICT DO NOTHING""", (nouveau, ancien))
        cur.execute("DELETE FROM etat_case WHERE voyage = %s", (ancien,))
        cur.execute("""INSERT INTO retours (voyage, proprietaire, objet, verdict, quantite_utilisee, maj_le)
                       SELECT %s, proprietaire, objet, verdict, quantite_utilisee, maj_le FROM retours
                       WHERE voyage = %s ON CONFLICT DO NOTHING""", (nouveau, ancien))
        cur.execute("DELETE FROM retours WHERE voyage = %s", (ancien,))
        cur.execute("""INSERT INTO infos_etape (voyage, destination, rang, hebergement, adresse, reservation,
                                                arrivee, notes, maj_le)
                       SELECT %s, destination, rang, hebergement, adresse, reservation, arrivee, notes, maj_le
                       FROM infos_etape WHERE voyage = %s ON CONFLICT DO NOTHING""", (nouveau, ancien))
        cur.execute("DELETE FROM infos_etape WHERE voyage = %s", (ancien,))
        cur.execute("UPDATE depenses SET voyage = %s WHERE voyage = %s", (nouveau, ancien))
        cur.execute("UPDATE reservations SET voyage = %s WHERE voyage = %s", (nouveau, ancien))
        cur.execute("UPDATE a_voir SET voyage = %s WHERE voyage = %s", (nouveau, ancien))
        cur.execute("UPDATE souvenirs SET voyage = %s WHERE voyage = %s", (nouveau, ancien))
        cur.execute("UPDATE voyages SET archive = true WHERE code = %s", (ancien,))
    conn.commit()



# --- Pool de connexions (serveur) -------------------------------------------------------
# Ouvrir une connexion à Neon coûte 0,4 à 1,2 s (poignée de main sécurisée) ; une requête,
# quelques centièmes. Le serveur garde donc ses connexions ouvertes et les réutilise.
# Neon coupe les connexions quand la base se met en veille (5 min) : une connexion restée
# au repos est vérifiée avant usage, et remplacée si elle est morte.
REPOS_AVANT_VERIFICATION = 60      # secondes
_pools = {}
_derniere_utilisation = {}         # id(connexion) -> instant où elle a été rendue


class ConnexionEmpruntee:
    """Une connexion du pool : s'utilise comme une connexion psycopg2 ; close() la rend."""

    def __init__(self, pool, brute):
        self._pool, self.brute = pool, brute

    def __getattr__(self, nom):                    # cursor(), commit(), rollback()…
        return getattr(self.brute, nom)

    def close(self):
        _derniere_utilisation[id(self.brute)] = time.monotonic()
        self._pool.putconn(self.brute)             # le pool annule toute transaction en cours


def _pool(nom_base):
    if nom_base not in _pools:
        url = os.environ.get("DATABASE_URL")
        if url and nom_base == "valise":
            _pools[nom_base] = ThreadedConnectionPool(1, 4, url)
        else:
            _pools[nom_base] = ThreadedConnectionPool(1, 4, dbname=nom_base)
    return _pools[nom_base]


def _vivante(conn):
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
        conn.rollback()
        return True
    except psycopg2.Error:
        return False


def emprunter(nom_base="valise"):
    """Comme connecter(), mais réutilise une connexion déjà ouverte (mêmes règles de base)."""
    pool = _pool(nom_base)
    conn = pool.getconn()
    repos = time.monotonic() - _derniere_utilisation.get(id(conn), time.monotonic())
    if conn.closed or (repos >= REPOS_AVANT_VERIFICATION and not _vivante(conn)):
        pool.putconn(conn, close=True)             # morte : on la jette, le pool en ouvre une neuve
        conn = pool.getconn()
    return ConnexionEmpruntee(pool, conn)



# --- Infos de chaque étape (rubrique Sur place) ----------------------------------------------
CHAMPS_ETAPE = ("hebergement", "adresse", "reservation", "arrivee", "notes")


def enregistrer_infos_etape(conn, voyage, destination, rang, champs):
    """Remplace la fiche d'une étape (champs absents = vides)."""
    valeurs = [str(champs.get(c) or "") for c in CHAMPS_ETAPE]
    with conn.cursor() as cur:
        cur.execute(
            f"""INSERT INTO infos_etape (voyage, destination, rang, {", ".join(CHAMPS_ETAPE)})
                VALUES (%s, %s, %s, {", ".join(["%s"] * len(CHAMPS_ETAPE))})
                ON CONFLICT (voyage, destination, rang) DO UPDATE SET
                {", ".join(f"{c} = EXCLUDED.{c}" for c in CHAMPS_ETAPE)}, maj_le = now()""",
            (voyage, destination, rang, *valeurs))
    conn.commit()


def lire_infos_etapes(conn, voyage):
    """[{"destination", "rang", <champs>}] du voyage."""
    with conn.cursor() as cur:
        cur.execute(f"SELECT destination, rang, {', '.join(CHAMPS_ETAPE)} FROM infos_etape "
                    "WHERE voyage = %s ORDER BY destination, rang", (voyage,))
        return [dict(zip(("destination", "rang", *CHAMPS_ETAPE), ligne)) for ligne in cur.fetchall()]



# --- Dépenses partagées (rubrique Sur place) -------------------------------------------------
def ajouter_depense(conn, voyage, libelle, montant, devise, montant_eur, paye_par, pour, jour):
    """Enregistre une dépense ; renvoie son id."""
    with conn.cursor() as cur:
        cur.execute("""INSERT INTO depenses (voyage, libelle, montant, devise, montant_eur, paye_par, pour, jour)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id""",
                    (voyage, libelle, montant, devise, montant_eur, paye_par, list(pour), jour))
        identifiant = cur.fetchone()[0]
    conn.commit()
    return identifiant


def lire_depenses(conn, voyage):
    """Les dépenses du voyage, la plus récente d'abord."""
    with conn.cursor() as cur:
        cur.execute("""SELECT id, libelle, montant, devise, montant_eur, paye_par, pour, jour FROM depenses
                       WHERE voyage = %s ORDER BY jour DESC, id DESC""", (voyage,))
        cles = ("id", "libelle", "montant", "devise", "montant_eur", "paye_par", "pour", "jour")
        return [dict(zip(cles, ligne)) for ligne in cur.fetchall()]


# --- Carnet 🗓️ Programme : les réservations du voyage ------------------------------------------
CHAMPS_RESERVATION = ("type", "titre", "jour", "heure", "jour_fin", "heure_fin", "lieu", "reference",
                      "telephone", "lien", "notes")


def enregistrer_reservation(conn, r):
    """Crée ou met à jour (même id) une réservation déjà validée ; jamais celle d'un autre voyage."""
    with conn.cursor() as cur:
        cur.execute(
            f"""INSERT INTO reservations (id, voyage, {", ".join(CHAMPS_RESERVATION)})
                VALUES (%s, %s, {", ".join(["%s"] * len(CHAMPS_RESERVATION))})
                ON CONFLICT (id) DO UPDATE SET
                {", ".join(f"{c} = EXCLUDED.{c}" for c in CHAMPS_RESERVATION)}, maj_le = now()
                WHERE reservations.voyage = EXCLUDED.voyage""",
            (r["id"], r["voyage"], *(r[c] for c in CHAMPS_RESERVATION)))
    conn.commit()


def lire_reservations(conn, voyage):
    """Dans l'ordre du voyage : par jour, puis par heure (sans heure : en fin de journée)."""
    with conn.cursor() as cur:
        cur.execute(f"""SELECT id, {", ".join(CHAMPS_RESERVATION)} FROM reservations WHERE voyage = %s
                        ORDER BY jour, heure = '', heure, titre""", (voyage,))
        return [dict(zip(("id", *CHAMPS_RESERVATION), ligne)) for ligne in cur.fetchall()]


def supprimer_reservation(conn, voyage, identifiant):
    with conn.cursor() as cur:
        cur.execute("DELETE FROM reservations WHERE voyage = %s AND id = %s", (voyage, identifiant))
    conn.commit()


# --- « 💡 À voir » : les envies de chaque étape -------------------------------------------------
CHAMPS_A_VOIR = ("destination", "rang", "nom", "adresse", "note", "lien", "genre", "fait", "prevu")


def enregistrer_a_voir(conn, e):
    """Crée ou met à jour (même id) une envie déjà validée ; jamais celle d'un autre voyage."""
    with conn.cursor() as cur:
        cur.execute(
            f"""INSERT INTO a_voir (id, voyage, {", ".join(CHAMPS_A_VOIR)})
                VALUES (%s, %s, {", ".join(["%s"] * len(CHAMPS_A_VOIR))})
                ON CONFLICT (id) DO UPDATE SET
                {", ".join(f"{c} = EXCLUDED.{c}" for c in CHAMPS_A_VOIR)}, maj_le = now()
                WHERE a_voir.voyage = EXCLUDED.voyage""",
            (e["id"], e["voyage"], *(e[c] for c in CHAMPS_A_VOIR)))
    conn.commit()


def lire_a_voir(conn, voyage):
    """Dans l'ordre de saisie (la page les range par étape, les faites en bas)."""
    with conn.cursor() as cur:
        cur.execute(f"""SELECT id, {", ".join(CHAMPS_A_VOIR)} FROM a_voir WHERE voyage = %s
                        ORDER BY maj_le, id""", (voyage,))
        return [dict(zip(("id", *CHAMPS_A_VOIR), ligne)) for ligne in cur.fetchall()]


def supprimer_a_voir(conn, voyage, identifiant):
    with conn.cursor() as cur:
        cur.execute("DELETE FROM a_voir WHERE voyage = %s AND id = %s", (voyage, identifiant))
    conn.commit()


def supprimer_depense(conn, voyage, identifiant):
    with conn.cursor() as cur:
        cur.execute("DELETE FROM depenses WHERE voyage = %s AND id = %s", (voyage, identifiant))
    conn.commit()


# --- 🎁 Souvenirs : carnet de proches (tous voyages) et souvenirs du voyage ---------------------
CHAMPS_SOUVENIR = ("proche", "idee", "note", "achete", "prix", "devise", "prix_eur", "paye_par", "achete_le")


def enregistrer_proche(conn, p):
    """Crée ou modifie (même id) un proche du carnet."""
    with conn.cursor() as cur:
        cur.execute("""INSERT INTO proches (id, nom, budget, archive) VALUES (%s, %s, %s, %s)
                       ON CONFLICT (id) DO UPDATE SET nom = EXCLUDED.nom, budget = EXCLUDED.budget,
                                                      archive = EXCLUDED.archive, maj_le = now()""",
                    (p["id"], p["nom"], p["budget"], p["archive"]))
    conn.commit()


def enregistrer_souvenir(conn, s, personnes):
    """Crée ou modifie (même id) un souvenir, et tient sa dépense partagée à jour, d'un seul coup :
    acheté -> dépense créée (ou modifiée) ; plus acheté -> dépense retirée. Une dépense retirée à la
    main dans Dépenses n'est pas recréée tant que le souvenir reste acheté.
    ValueError si l'id appartient à un autre voyage."""
    with conn.cursor() as cur:
        cur.execute("SELECT voyage, achete, depense FROM souvenirs WHERE id = %s FOR UPDATE", (s["id"],))
        avant = cur.fetchone()
        if avant and avant[0] != s["voyage"]:
            conn.rollback()
            raise ValueError("souvenir d'un autre voyage")
        depense = avant[2] if avant else None
        if s["achete"]:
            cur.execute("SELECT nom FROM proches WHERE id = %s", (s["proche"],))
            proche = cur.fetchone()
            libelle = (f"Souvenir : {s['idee']}" + (f" ({proche[0]})" if proche else ""))[:120]
            valeurs = (libelle, s["prix"], s["devise"], s["prix_eur"], s["paye_par"], list(personnes), s["achete_le"])
            if depense is not None:
                cur.execute("""UPDATE depenses SET libelle = %s, montant = %s, devise = %s, montant_eur = %s,
                                                   paye_par = %s, pour = %s, jour = %s WHERE id = %s""",
                            (*valeurs, depense))
            elif not (avant and avant[1]):
                cur.execute("""INSERT INTO depenses (voyage, libelle, montant, devise, montant_eur, paye_par, pour, jour)
                               VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id""", (s["voyage"], *valeurs))
                depense = cur.fetchone()[0]
        elif depense is not None:
            cur.execute("DELETE FROM depenses WHERE id = %s", (depense,))
            depense = None
        cur.execute(
            f"""INSERT INTO souvenirs (id, voyage, {", ".join(CHAMPS_SOUVENIR)}, depense)
                VALUES (%s, %s, {", ".join(["%s"] * len(CHAMPS_SOUVENIR))}, %s)
                ON CONFLICT (id) DO UPDATE SET
                {", ".join(f"{c} = EXCLUDED.{c}" for c in CHAMPS_SOUVENIR)}, depense = EXCLUDED.depense, maj_le = now()""",
            (s["id"], s["voyage"], *(s[c] for c in CHAMPS_SOUVENIR), depense))
    conn.commit()


def supprimer_souvenir(conn, voyage, identifiant):
    """Retire un souvenir et sa dépense."""
    with conn.cursor() as cur:
        cur.execute("DELETE FROM souvenirs WHERE voyage = %s AND id = %s RETURNING depense", (voyage, identifiant))
        ligne = cur.fetchone()
        if ligne and ligne[0] is not None:
            cur.execute("DELETE FROM depenses WHERE id = %s", (ligne[0],))
    conn.commit()


def lire_souvenirs(conn, voyage):
    """{"proches": tout le carnet, "souvenirs": ceux du voyage, "historique": {proche: [{idee, voyage}]}}
    L'historique : ce qui a été acheté pour chaque proche lors des autres voyages, du plus récent."""
    with conn.cursor() as cur:
        cur.execute("SELECT id, nom, budget, archive FROM proches ORDER BY nom, id")
        proches = [dict(zip(("id", "nom", "budget", "archive"), ligne)) for ligne in cur.fetchall()]
        cur.execute(f"SELECT id, {', '.join(CHAMPS_SOUVENIR)} FROM souvenirs WHERE voyage = %s ORDER BY maj_le, id",
                    (voyage,))
        souvenirs = [dict(zip(("id", *CHAMPS_SOUVENIR), ligne)) for ligne in cur.fetchall()]
        cur.execute("""SELECT s.proche, s.idee, v.libelle FROM souvenirs s JOIN voyages v ON v.code = s.voyage
                       WHERE s.achete AND s.proche <> '' AND s.voyage <> %s AND NOT v.archive
                       ORDER BY v.depart DESC, s.idee""", (voyage,))
        historique = {}
        for proche, idee, libelle in cur.fetchall():
            historique.setdefault(proche, []).append({"idee": idee, "voyage": libelle})
    return {"proches": proches, "souvenirs": souvenirs, "historique": historique}



# --- Casa Binomerie : courses et placard ------------------------------------------------------

CHAMPS_ARTICLE = ("nom", "rayon", "pris", "recurrent", "actif", "source")


def enregistrer_article(conn, a):
    """Crée ou met à jour (même id) un article validé ; pris : son basique revient en stock."""
    from courses import normaliser
    with conn.cursor() as cur:
        cur.execute(
            f"""INSERT INTO courses (id, {", ".join(CHAMPS_ARTICLE)})
                VALUES (%s, {", ".join(["%s"] * len(CHAMPS_ARTICLE))})
                ON CONFLICT (id) DO UPDATE SET
                {", ".join(f"{c} = EXCLUDED.{c}" for c in CHAMPS_ARTICLE)}, maj_le = now()""",
            (a["id"], *(a[c] for c in CHAMPS_ARTICLE)))
        if a["pris"]:
            cur.execute("UPDATE placard SET en_stock = true, maj_le = now() WHERE cle = %s AND NOT en_stock",
                        (normaliser(a["nom"]),))
    conn.commit()


def lire_courses(conn):
    """{articles: [...], placard: [...]} — tout, la page trie (rayons, habituels, épuisés)."""
    with conn.cursor() as cur:
        cur.execute(f"SELECT id, {', '.join(CHAMPS_ARTICLE)} FROM courses ORDER BY maj_le, id")
        articles = [dict(zip(("id", *CHAMPS_ARTICLE), ligne)) for ligne in cur.fetchall()]
        cur.execute("SELECT cle, nom, en_stock FROM placard ORDER BY nom")
        placard = [dict(zip(("cle", "nom", "en_stock"), ligne)) for ligne in cur.fetchall()]
    return {"articles": articles, "placard": placard}


def supprimer_article(conn, identifiant):
    with conn.cursor() as cur:
        cur.execute("DELETE FROM courses WHERE id = %s", (identifiant,))
    conn.commit()


def vider_pris(conn):
    """Les pris quittent la liste : supprimés, sauf les récurrents, rangés dans les habituels."""
    with conn.cursor() as cur:
        cur.execute("DELETE FROM courses WHERE actif AND pris AND NOT recurrent")
        cur.execute("UPDATE courses SET actif = false, pris = false, maj_le = now() WHERE actif AND pris")
    conn.commit()


def compter_a_prendre(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM courses WHERE actif AND NOT pris")
        return cur.fetchone()[0]


def enregistrer_placard(conn, p):
    with conn.cursor() as cur:
        cur.execute("""INSERT INTO placard (cle, nom, en_stock) VALUES (%s, %s, %s)
                       ON CONFLICT (cle) DO UPDATE SET nom = EXCLUDED.nom, en_stock = EXCLUDED.en_stock,
                       maj_le = now()""", (p["cle"], p["nom"], p["en_stock"]))
    conn.commit()


def semer_placard(conn, noms):
    """Remplit le placard de départ (tout en stock) s'il est vide ; renvoie le nombre de basiques ajoutés.
    Jamais sur un placard déjà utilisé : un basique retiré ne revient pas."""
    from courses import normaliser
    with conn.cursor() as cur:
        cur.execute("SELECT EXISTS (SELECT 1 FROM placard)")
        if cur.fetchone()[0]:
            return 0
        for nom in noms:
            cur.execute("INSERT INTO placard (cle, nom) VALUES (%s, %s) ON CONFLICT DO NOTHING", (normaliser(nom), nom))
    conn.commit()
    return len(noms)
