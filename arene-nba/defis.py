"""Banque de défis de l'Arène — v1 : LES GAMMES.

But : consolider les 4 briques déjà acquises jusqu'au réflexe.
    - dicts          → agréger par clé (le GROUP BY de SQL), .get(), max(d, key=d.get)
    - comprehensions → filtrer/transformer en une ligne (le SELECT ... WHERE de SQL)
    - sorted_lambda  → trier par un critère calculé (le ORDER BY de SQL)
    - sets           → ensembles, unicité, intersection/différence

Chaque défi est un dict. Champs communs :
    id          str   identifiant unique
    brique      str   dicts | comprehensions | sorted_lambda | sets
    type        str   predire | oneliner | ecrire
    difficulte  int   1 (facile) → 3 (costaud)
    enonce      str   ce qui est demandé, affiché au joueur
    indices     list  3 indices socratiques : orientation → structure → quasi-solution
    solution    str   la solution complète, révélée UNIQUEMENT sur demande

Validation — correct-by-construction, la réponse attendue est CALCULÉE, jamais recopiée :
    predire  : champ `code` (str). Le moteur l'exécute, capture la sortie → c'est l'attendu.
    oneliner : champ `ref` (str), expression de référence. attendu = eval(ref).
               champ `contexte` (dict, optionnel) : variables ajoutées au namespace.
    ecrire   : champ `fonction` (nom à définir dans reponse.py), `ref` (callable de
               référence), `cas` (liste de tuples d'arguments testés en cachette).

Ajouter une brique neuve en phase 2 = ajouter des dicts ici avec une nouvelle valeur
`brique`. Aucune refonte du moteur nécessaire.
"""

from data_nba import JOUEURS

# --- Petits jeux de données pour les cas de test cachés des défis `ecrire` ---
_TRIO = [
    {"nom": "A", "equipe": "XXX", "poste": "G", "pts": 10.0, "reb": 5.0, "ast": 4.0},
    {"nom": "B", "equipe": "YYY", "poste": "C", "pts": 20.0, "reb": 12.0, "ast": 1.0},
    {"nom": "C", "equipe": "XXX", "poste": "F", "pts": 30.0, "reb": 8.0, "ast": 6.0},
]
_SOLO = [{"nom": "Z", "equipe": "ZZZ", "poste": "G", "pts": 42.0, "reb": 3.0, "ast": 9.0}]


# ---------------------------------------------------------------------------
# Fonctions de référence pour les défis `ecrire` (la "vérité" testée en cachette)
# ---------------------------------------------------------------------------
def _ref_top_scoreur(joueurs):
    return max(joueurs, key=lambda j: j["pts"])["nom"]

def _ref_moyenne_pts(joueurs):
    return sum(j["pts"] for j in joueurs) / len(joueurs)

def _ref_compte_par_poste(joueurs):
    compte = {}
    for j in joueurs:
        compte[j["poste"]] = compte.get(j["poste"], 0) + 1
    return compte

def _ref_total_pts_par_equipe(joueurs):
    total = {}
    for j in joueurs:
        total[j["equipe"]] = total.get(j["equipe"], 0) + j["pts"]
    return total

def _ref_noms_meneurs(joueurs):
    return [j["nom"] for j in joueurs if j["poste"] == "G"]

def _ref_pts_plus_20(joueurs):
    return [j["nom"] for j in joueurs if j["pts"] > 20]

def _ref_classement_pts(joueurs):
    return [j["nom"] for j in sorted(joueurs, key=lambda j: j["pts"], reverse=True)]

def _ref_top3_passeurs(joueurs):
    tries = sorted(joueurs, key=lambda j: j["ast"], reverse=True)
    return [j["nom"] for j in tries[:3]]

def _ref_equipes_uniques(joueurs):
    return {j["equipe"] for j in joueurs}

def _ref_double_double(joueurs):
    # au moins 10 en pts ET 10 en reb (double-double points/rebonds)
    return [j["nom"] for j in joueurs if j["pts"] >= 10 and j["reb"] >= 10]


# ---------------------------------------------------------------------------
# LA BANQUE
# ---------------------------------------------------------------------------
DEFIS = [

    # =====================================================================
    # BRIQUE : dicts  (agréger par clé — le GROUP BY de SQL)
    # =====================================================================
    {
        "id": "dicts_predire_1",
        "brique": "dicts",
        "type": "predire",
        "difficulte": 1,
        "enonce": "Que va afficher ce code ?",
        "code": (
            "compte = {}\n"
            "for poste in ['G', 'C', 'G', 'F', 'G']:\n"
            "    compte[poste] = compte.get(poste, 0) + 1\n"
            "print(compte)"
        ),
        "indices": [
            "compte.get(poste, 0) renvoie la valeur si la clé existe, sinon 0. C'est un COUNT(*) ... GROUP BY qui se construit clé par clé.",
            "Déroule la boucle : G→1, C→1, G devient 2, F→1, G devient 3.",
            "Il reste 3 'G', 1 'C', 1 'F'. L'ordre d'apparition est conservé (G, C, F).",
        ],
        "solution": "{'G': 3, 'C': 1, 'F': 1}\n\nLe pattern .get(cle, 0) + 1 est LE réflexe pour compter par catégorie.",
    },
    {
        "id": "dicts_oneliner_1",
        "brique": "dicts",
        "type": "oneliner",
        "difficulte": 2,
        "enonce": (
            "On te donne un dict pts_par_equipe (total de points par équipe).\n"
            "Écris l'expression qui renvoie le CODE de l'équipe au plus gros total."
        ),
        "contexte": {"pts_par_equipe": {"DEN": 26.4, "LAL": 50.4, "MIL": 54.7, "PHX": 54.2}},
        "ref": "max(pts_par_equipe, key=pts_par_equipe.get)",
        "indices": [
            "max() sait comparer selon un critère : max(iterable, key=...). Sur un dict, itérer donne les CLÉS.",
            "Tu veux la clé dont la VALEUR est la plus grande. Le critère key doit renvoyer la valeur d'une clé.",
            "pts_par_equipe.get est une fonction : donne-lui une clé, elle rend la valeur. max(pts_par_equipe, key=pts_par_equipe.get).",
        ],
        "solution": "max(pts_par_equipe, key=pts_par_equipe.get)\n\nÉquivalent SQL : SELECT equipe ... ORDER BY total DESC LIMIT 1.",
    },
    {
        "id": "dicts_ecrire_1",
        "brique": "dicts",
        "type": "ecrire",
        "difficulte": 1,
        "enonce": (
            "Écris compte_par_poste(joueurs) : renvoie un dict {poste: nombre de joueurs}.\n"
            "Ex : {'G': 8, 'C': 5, 'F': 5}"
        ),
        "fonction": "compte_par_poste",
        "ref": _ref_compte_par_poste,
        "cas": [(JOUEURS,), (_TRIO,), (_SOLO,)],
        "indices": [
            "C'est un COUNT ... GROUP BY poste. Tu pars d'un dict vide et tu le remplis en parcourant les joueurs.",
            "Pour chaque joueur : compte[j['poste']] = compte.get(j['poste'], 0) + 1",
            "def compte_par_poste(joueurs):\n    compte = {}\n    for j in joueurs:\n        compte[j['poste']] = compte.get(j['poste'], 0) + 1\n    return compte",
        ],
        "solution": (
            "def compte_par_poste(joueurs):\n"
            "    compte = {}\n"
            "    for j in joueurs:\n"
            "        compte[j['poste']] = compte.get(j['poste'], 0) + 1\n"
            "    return compte"
        ),
    },
    {
        "id": "dicts_ecrire_2",
        "brique": "dicts",
        "type": "ecrire",
        "difficulte": 2,
        "enonce": (
            "Écris total_pts_par_equipe(joueurs) : renvoie un dict {equipe: somme des pts}.\n"
            "Même pattern que le comptage, mais tu additionnes les points au lieu de +1."
        ),
        "fonction": "total_pts_par_equipe",
        "ref": _ref_total_pts_par_equipe,
        "cas": [(JOUEURS,), (_TRIO,)],
        "indices": [
            "SUM(pts) ... GROUP BY equipe. Dict vide, puis on cumule.",
            "total[j['equipe']] = total.get(j['equipe'], 0) + j['pts']",
            "def total_pts_par_equipe(joueurs):\n    total = {}\n    for j in joueurs:\n        total[j['equipe']] = total.get(j['equipe'], 0) + j['pts']\n    return total",
        ],
        "solution": (
            "def total_pts_par_equipe(joueurs):\n"
            "    total = {}\n"
            "    for j in joueurs:\n"
            "        total[j['equipe']] = total.get(j['equipe'], 0) + j['pts']\n"
            "    return total"
        ),
    },
    {
        "id": "dicts_ecrire_3",
        "brique": "dicts",
        "type": "ecrire",
        "difficulte": 2,
        "enonce": (
            "Écris top_scoreur(joueurs) : renvoie le NOM du joueur qui marque le plus de points."
        ),
        "fonction": "top_scoreur",
        "ref": _ref_top_scoreur,
        "cas": [(JOUEURS,), (_TRIO,), (_SOLO,)],
        "indices": [
            "max() avec un critère key= sur la clé 'pts' te donne le joueur (le dict entier).",
            "meilleur = max(joueurs, key=lambda j: j['pts']) — puis tu renvoies son 'nom'.",
            "def top_scoreur(joueurs):\n    return max(joueurs, key=lambda j: j['pts'])['nom']",
        ],
        "solution": (
            "def top_scoreur(joueurs):\n"
            "    return max(joueurs, key=lambda j: j['pts'])['nom']"
        ),
    },
    {
        "id": "dicts_ecrire_4",
        "brique": "dicts",
        "type": "ecrire",
        "difficulte": 3,
        "enonce": (
            "Écris moyenne_pts(joueurs) : renvoie la moyenne des points (un float).\n"
            "AVG(pts) en SQL."
        ),
        "fonction": "moyenne_pts",
        "ref": _ref_moyenne_pts,
        "cas": [(JOUEURS,), (_TRIO,), (_SOLO,)],
        "indices": [
            "Moyenne = somme / nombre. sum() sur une comprehension des pts, len() pour le nombre.",
            "total = sum(j['pts'] for j in joueurs) ; return total / len(joueurs)",
            "def moyenne_pts(joueurs):\n    return sum(j['pts'] for j in joueurs) / len(joueurs)",
        ],
        "solution": (
            "def moyenne_pts(joueurs):\n"
            "    return sum(j['pts'] for j in joueurs) / len(joueurs)"
        ),
    },

    # =====================================================================
    # BRIQUE : comprehensions  (filtrer/transformer — le SELECT ... WHERE)
    # =====================================================================
    {
        "id": "comprehensions_predire_1",
        "brique": "comprehensions",
        "type": "predire",
        "difficulte": 1,
        "enonce": "Que va afficher ce code ?",
        "code": "print([x * 2 for x in range(4)])",
        "indices": [
            "range(4) produit 0, 1, 2, 3.",
            "Pour chacun, on garde x * 2.",
            "0→0, 1→2, 2→4, 3→6.",
        ],
        "solution": "[0, 2, 4, 6]\n\nUne list comprehension = transformer chaque élément d'une séquence.",
    },
    {
        "id": "comprehensions_predire_2",
        "brique": "comprehensions",
        "type": "predire",
        "difficulte": 2,
        "enonce": "Que va afficher ce code ?",
        "code": "print([n for n in range(10) if n % 3 == 0])",
        "indices": [
            "Le if à la fin FILTRE : on ne garde que les n qui passent le test.",
            "n % 3 == 0 → n est un multiple de 3.",
            "Dans 0..9, les multiples de 3 sont 0, 3, 6, 9.",
        ],
        "solution": "[0, 3, 6, 9]\n\nComprehension avec filtre = SELECT n ... WHERE n % 3 = 0.",
    },
    {
        "id": "comprehensions_oneliner_1",
        "brique": "comprehensions",
        "type": "oneliner",
        "difficulte": 1,
        "enonce": "Écris l'expression qui renvoie la LISTE des noms de tous les joueurs (clé 'nom').",
        "ref": "[j['nom'] for j in JOUEURS]",
        "indices": [
            "Tu transformes chaque joueur (un dict) en son seul nom. SELECT nom FROM joueurs.",
            "Forme : [ <ce qu'on garde> for j in JOUEURS ].",
            "[j['nom'] for j in JOUEURS]",
        ],
        "solution": "[j['nom'] for j in JOUEURS]",
    },
    {
        "id": "comprehensions_oneliner_2",
        "brique": "comprehensions",
        "type": "oneliner",
        "difficulte": 2,
        "enonce": "Écris l'expression qui renvoie la liste des noms des joueurs marquant plus de 28 points.",
        "ref": "[j['nom'] for j in JOUEURS if j['pts'] > 28]",
        "indices": [
            "Transformer (garder le nom) ET filtrer (pts > 28). Les deux dans la même comprehension.",
            "Forme : [ j['nom'] for j in JOUEURS if <condition> ].",
            "[j['nom'] for j in JOUEURS if j['pts'] > 28]",
        ],
        "solution": "[j['nom'] for j in JOUEURS if j['pts'] > 28]",
    },
    {
        "id": "comprehensions_ecrire_1",
        "brique": "comprehensions",
        "type": "ecrire",
        "difficulte": 2,
        "enonce": (
            "Écris noms_meneurs(joueurs) : renvoie la liste des noms des joueurs dont le poste est 'G'."
        ),
        "fonction": "noms_meneurs",
        "ref": _ref_noms_meneurs,
        "cas": [(JOUEURS,), (_TRIO,), (_SOLO,)],
        "indices": [
            "Une seule ligne suffit : comprehension avec filtre sur le poste.",
            "return [ j['nom'] for j in joueurs if j['poste'] == 'G' ]",
            "def noms_meneurs(joueurs):\n    return [j['nom'] for j in joueurs if j['poste'] == 'G']",
        ],
        "solution": (
            "def noms_meneurs(joueurs):\n"
            "    return [j['nom'] for j in joueurs if j['poste'] == 'G']"
        ),
    },
    {
        "id": "comprehensions_ecrire_2",
        "brique": "comprehensions",
        "type": "ecrire",
        "difficulte": 3,
        "enonce": (
            "Écris double_double(joueurs) : renvoie les noms des joueurs avec AU MOINS 10 pts ET 10 rebonds.\n"
            "(Un 'double-double' points/rebonds.)"
        ),
        "fonction": "double_double",
        "ref": _ref_double_double,
        "cas": [(JOUEURS,), (_TRIO,)],
        "indices": [
            "Filtre à double condition dans la comprehension : les deux doivent être vraies → and.",
            "if j['pts'] >= 10 and j['reb'] >= 10",
            "def double_double(joueurs):\n    return [j['nom'] for j in joueurs if j['pts'] >= 10 and j['reb'] >= 10]",
        ],
        "solution": (
            "def double_double(joueurs):\n"
            "    return [j['nom'] for j in joueurs if j['pts'] >= 10 and j['reb'] >= 10]"
        ),
    },

    # =====================================================================
    # BRIQUE : sorted_lambda  (trier par critère calculé — le ORDER BY)
    # =====================================================================
    {
        "id": "sorted_lambda_predire_1",
        "brique": "sorted_lambda",
        "type": "predire",
        "difficulte": 1,
        "enonce": "Que va afficher ce code ?",
        "code": "print(sorted([3, 1, 2], reverse=True))",
        "indices": [
            "sorted() ne modifie pas la liste, il en renvoie une nouvelle triée.",
            "reverse=True → ordre décroissant.",
            "3, 2, 1.",
        ],
        "solution": "[3, 2, 1]",
    },
    {
        "id": "sorted_lambda_predire_2",
        "brique": "sorted_lambda",
        "type": "predire",
        "difficulte": 2,
        "enonce": "Que va afficher ce code ?",
        "code": (
            "mots = ['ballon', 'jeu', 'panier']\n"
            "print(sorted(mots, key=len))"
        ),
        "indices": [
            "key=len → on trie selon la LONGUEUR de chaque mot, pas l'alphabet.",
            "len('ballon')=6, len('jeu')=3, len('panier')=6.",
            "Le plus court d'abord (jeu=3), puis 'ballon' et 'panier' (6 chacun, ordre d'origine conservé).",
        ],
        "solution": "['jeu', 'ballon', 'panier']\n\nÀ égalité de clé, sorted garde l'ordre initial (tri stable).",
    },
    {
        "id": "sorted_lambda_oneliner_0",
        "brique": "sorted_lambda",
        "type": "oneliner",
        "difficulte": 1,
        "enonce": "Écris l'expression qui renvoie la liste des points ('pts') de tous les joueurs, triés du plus PETIT au plus grand.",
        "ref": "sorted([j['pts'] for j in JOUEURS])",
        "indices": [
            "Deux temps : extraire les pts (comprehension), puis trier la liste obtenue.",
            "sorted() sur une liste de nombres trie en croissant par défaut, pas besoin de key.",
            "sorted([j['pts'] for j in JOUEURS])",
        ],
        "solution": "sorted([j['pts'] for j in JOUEURS])",
    },
    {
        "id": "sorted_lambda_oneliner_1",
        "brique": "sorted_lambda",
        "type": "oneliner",
        "difficulte": 2,
        "enonce": (
            "Écris l'expression qui renvoie la liste des JOUEURS triés par points DÉCROISSANTS.\n"
            "(La liste complète des dicts, triée — pas seulement les noms.)"
        ),
        "ref": "sorted(JOUEURS, key=lambda j: j['pts'], reverse=True)",
        "indices": [
            "ORDER BY pts DESC. sorted() avec un critère key= et reverse=True.",
            "key est une fonction qui, pour un joueur j, renvoie ce sur quoi on trie : j['pts'].",
            "sorted(JOUEURS, key=lambda j: j['pts'], reverse=True)",
        ],
        "solution": "sorted(JOUEURS, key=lambda j: j['pts'], reverse=True)",
    },
    {
        "id": "sorted_lambda_ecrire_1",
        "brique": "sorted_lambda",
        "type": "ecrire",
        "difficulte": 2,
        "enonce": (
            "Écris classement_pts(joueurs) : renvoie la liste des NOMS, du meilleur scoreur au moins bon."
        ),
        "fonction": "classement_pts",
        "ref": _ref_classement_pts,
        "cas": [(JOUEURS,), (_TRIO,), (_SOLO,)],
        "indices": [
            "Deux étapes : trier les joueurs par pts décroissants, puis en extraire les noms.",
            "tries = sorted(joueurs, key=lambda j: j['pts'], reverse=True) ; puis [j['nom'] for j in tries]",
            "def classement_pts(joueurs):\n    tries = sorted(joueurs, key=lambda j: j['pts'], reverse=True)\n    return [j['nom'] for j in tries]",
        ],
        "solution": (
            "def classement_pts(joueurs):\n"
            "    tries = sorted(joueurs, key=lambda j: j['pts'], reverse=True)\n"
            "    return [j['nom'] for j in tries]"
        ),
    },
    {
        "id": "sorted_lambda_ecrire_2",
        "brique": "sorted_lambda",
        "type": "ecrire",
        "difficulte": 3,
        "enonce": (
            "Écris top3_passeurs(joueurs) : renvoie les NOMS des 3 meilleurs passeurs (clé 'ast'), du meilleur au 3e."
        ),
        "fonction": "top3_passeurs",
        "ref": _ref_top3_passeurs,
        "cas": [(JOUEURS,), (_TRIO,)],
        "indices": [
            "Trier par 'ast' décroissant, puis ne garder que les 3 premiers avec un slice [:3].",
            "tries = sorted(joueurs, key=lambda j: j['ast'], reverse=True) ; puis [j['nom'] for j in tries[:3]]",
            "def top3_passeurs(joueurs):\n    tries = sorted(joueurs, key=lambda j: j['ast'], reverse=True)\n    return [j['nom'] for j in tries[:3]]",
        ],
        "solution": (
            "def top3_passeurs(joueurs):\n"
            "    tries = sorted(joueurs, key=lambda j: j['ast'], reverse=True)\n"
            "    return [j['nom'] for j in tries[:3]]"
        ),
    },

    # =====================================================================
    # BRIQUE : sets  (ensembles, unicité, opérations)
    # =====================================================================
    {
        "id": "sets_predire_1",
        "brique": "sets",
        "type": "predire",
        "difficulte": 1,
        "enonce": "Que va afficher ce code ?",
        "code": "print(len({1, 2, 2, 3, 3, 3}))",
        "indices": [
            "Un set ne garde jamais de doublon.",
            "{1, 2, 2, 3, 3, 3} se réduit à {1, 2, 3}.",
            "len de {1, 2, 3} = 3.",
        ],
        "solution": "3\n\nConstruire un set = DISTINCT en SQL.",
    },
    {
        "id": "sets_predire_2",
        "brique": "sets",
        "type": "predire",
        "difficulte": 2,
        "enonce": "Que va afficher ce code ?",
        "code": "print({1, 2, 3, 4} & {3, 4, 5})",
        "indices": [
            "L'opérateur & entre deux sets = INTERSECTION (les éléments communs).",
            "Quels éléments sont dans les DEUX ensembles ?",
            "3 et 4 sont communs.",
        ],
        "solution": "{3, 4}\n\n& = intersection, | = union, - = différence.",
    },
    {
        "id": "sets_oneliner_1",
        "brique": "sets",
        "type": "oneliner",
        "difficulte": 2,
        "enonce": "Écris l'expression qui renvoie l'ensemble (set) des équipes distinctes présentes dans JOUEURS.",
        "ref": "{j['equipe'] for j in JOUEURS}",
        "indices": [
            "SELECT DISTINCT equipe. Une set comprehension utilise des accolades {}.",
            "Forme : { j['equipe'] for j in JOUEURS }.",
            "{j['equipe'] for j in JOUEURS}",
        ],
        "solution": "{j['equipe'] for j in JOUEURS}\n\nLes doublons d'équipe disparaissent automatiquement.",
    },
    {
        "id": "sets_oneliner_2",
        "brique": "sets",
        "type": "oneliner",
        "difficulte": 3,
        "enonce": (
            "On te donne deux sets titulaires et blesses.\n"
            "Écris l'expression qui renvoie les titulaires qui NE sont PAS blessés."
        ),
        "contexte": {
            "titulaires": {"Jokic", "Doncic", "Curry", "Tatum"},
            "blesses": {"Curry", "Embiid"},
        },
        "ref": "titulaires - blesses",
        "indices": [
            "« présents dans A mais pas dans B » = différence d'ensembles.",
            "L'opérateur de différence entre sets est le tiret -.",
            "titulaires - blesses",
        ],
        "solution": "titulaires - blesses\n\n{'Jokic', 'Doncic', 'Tatum'} — Curry est retiré car blessé.",
    },
    {
        "id": "sets_ecrire_1",
        "brique": "sets",
        "type": "ecrire",
        "difficulte": 2,
        "enonce": (
            "Écris equipes_uniques(joueurs) : renvoie l'ENSEMBLE (set) des codes d'équipe présents."
        ),
        "fonction": "equipes_uniques",
        "ref": _ref_equipes_uniques,
        "cas": [(JOUEURS,), (_TRIO,), (_SOLO,)],
        "indices": [
            "Tu veux les équipes SANS doublon → un set.",
            "return { j['equipe'] for j in joueurs }",
            "def equipes_uniques(joueurs):\n    return {j['equipe'] for j in joueurs}",
        ],
        "solution": (
            "def equipes_uniques(joueurs):\n"
            "    return {j['equipe'] for j in joueurs}"
        ),
    },
    {
        "id": "sets_ecrire_2",
        "brique": "sets",
        "type": "ecrire",
        "difficulte": 3,
        "enonce": (
            "Écris pts_plus_20(joueurs) : renvoie la liste des noms des joueurs à plus de 20 points.\n"
            "(Révision transversale : comprehension + filtre.)"
        ),
        "fonction": "pts_plus_20",
        "ref": _ref_pts_plus_20,
        "cas": [(JOUEURS,), (_TRIO,), (_SOLO,)],
        "indices": [
            "Filtre pts > 20 dans une comprehension, on garde le nom.",
            "return [ j['nom'] for j in joueurs if j['pts'] > 20 ]",
            "def pts_plus_20(joueurs):\n    return [j['nom'] for j in joueurs if j['pts'] > 20]",
        ],
        "solution": (
            "def pts_plus_20(joueurs):\n"
            "    return [j['nom'] for j in joueurs if j['pts'] > 20]"
        ),
    },
]


# --- Métadonnées de briques : ordre + libellé (utilisés par le moteur/l'UI) ---
BRIQUES = {
    "dicts":          "Dictionnaires · agréger par clé (GROUP BY)",
    "comprehensions": "Comprehensions · filtrer & transformer (SELECT WHERE)",
    "sorted_lambda":  "sorted + lambda · trier par critère (ORDER BY)",
    "sets":           "Sets · unicité & ensembles (DISTINCT)",
}

# Briques travaillées en v1 (les gammes). Phase 2 en ajoutera d'autres.
BRIQUES_V1 = ["dicts", "comprehensions", "sorted_lambda", "sets"]
