"""Le chef de la Casa : la file des recettes à améliorer, la lecture et l'écriture sans risque (06/11/2026).

La rédaction (trucs, gestes, secrets de Julien) vit dans le skill chef-casa ; ici, seulement les données.
Neon fait foi : on lit la version du jour, on sauvegarde l'ancienne, on n'écrase pas une correction faite dans l'app.
"""
import json
from datetime import datetime
from zoneinfo import ZoneInfo

MARQUEUR = "Ce qui fait la différence"     # le bloc final : sa présence veut dire « déjà passée »
_ORDRE_GENRES = ["plat", "accompagnement", "entree", "dessert"]


def file_de_passage(conn, n=5):
    """Les n prochaines recettes : les plus cuisinées d'abord, puis le carnet, puis le genre, puis le nom."""
    with conn.cursor() as cur:
        cur.execute(
            """SELECT p.id, p.nom, p.genre, p.statut,
                      (SELECT count(*) FROM repas r WHERE r.issue = 'fait' AND r.plats ? p.id) AS faits
               FROM plats p
               WHERE NOT p.archive AND position(%s IN p.recette) = 0
               ORDER BY faits DESC, p.statut = 'a-tester', array_position(%s, p.genre), p.nom
               LIMIT %s""", (MARQUEUR, _ORDRE_GENRES, n))
        return [dict(zip(("id", "nom", "genre", "statut", "faits"), ligne)) for ligne in cur.fetchall()]


def lire(conn, id_):
    """La recette du jour, avec son maj_le (à rendre à ecrire)."""
    with conn.cursor() as cur:
        cur.execute("SELECT id, nom, genre, pour, recette, maj_le FROM plats WHERE id = %s", (id_,))
        ligne = cur.fetchone()
    return dict(zip(("id", "nom", "genre", "pour", "recette", "maj_le"), ligne)) if ligne else None


class RecetteModifiee(Exception):
    """La recette a changé dans l'app depuis la lecture : relire et reproposer."""


def _chemin_libre(dossier, id_):
    base = f"{datetime.now(ZoneInfo('Europe/Paris')).date().isoformat()}-{id_}"   # date de Paris, comme casa.py
    chemin, i = dossier / f"{base}.json", 2
    while chemin.exists():                           # une sauvegarde n'est jamais écrasée
        chemin, i = dossier / f"{base}-{i}.json", i + 1
    return chemin


def ecrire(conn, id_, texte, maj_lu, dossier):
    """Sauvegarde l'ancienne version dans dossier, puis remplace la recette. Rend le chemin de la sauvegarde."""
    if MARQUEUR not in texte:
        raise ValueError(f"le bloc « {MARQUEUR} » manque")
    with conn.cursor() as cur:
        cur.execute("SELECT nom, recette, note, maj_le FROM plats WHERE id = %s FOR UPDATE", (id_,))
        ligne = cur.fetchone()
        if ligne is None:
            conn.rollback()
            raise KeyError(id_)
        nom, recette, note, maj_le = ligne
        if maj_le != maj_lu:
            conn.rollback()
            raise RecetteModifiee(f"{id_} modifiée le {maj_le.isoformat()}, lue le {maj_lu}")
        dossier.mkdir(parents=True, exist_ok=True)
        chemin = _chemin_libre(dossier, id_)
        chemin.write_text(json.dumps({"id": id_, "nom": nom, "recette": recette, "note": note,
                                      "maj_le": maj_le.isoformat()}, ensure_ascii=False, indent=1))
        cur.execute("UPDATE plats SET recette = %s, maj_le = now() WHERE id = %s", (texte, id_))
    conn.commit()
    return chemin
