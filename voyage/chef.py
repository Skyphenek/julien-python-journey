"""Le chef de la Casa : la file des recettes à améliorer, la lecture et l'écriture sans risque (06/11/2026).

La rédaction (trucs, gestes, secrets de Julien) vit dans le skill chef-casa ; ici, seulement les données.
Neon fait foi : on lit la version du jour, on sauvegarde l'ancienne, on n'écrase pas une correction faite dans l'app.
"""

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
