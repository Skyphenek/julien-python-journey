"""Moteur de l'Arène : évaluation, indices, persistance, sélection par les gammes.

Ce module ne fait AUCUN affichage — il calcule et renvoie des résultats.
arene.py s'occupe de l'interface. Cette séparation permet de tester le moteur seul.
"""

import io
import json
import os
import contextlib
import importlib
import datetime

from data_nba import JOUEURS
import defis as banque

# --- Emplacements de fichiers (relatifs à ce dossier) ---
_ICI = os.path.dirname(os.path.abspath(__file__))
FICHIER_PROGRESSION = os.path.join(_ICI, "progression.json")
FICHIER_REPONSE = os.path.join(_ICI, "reponse.py")

# Combien de points de base par difficulté, et combien un indice coûte.
POINTS_BASE = {1: 100, 2: 150, 3: 200}
MALUS_INDICE = 40  # retiré des points de la manche par indice consulté


# ===========================================================================
# 1. COMPARAISON NORMALISÉE  (floats arrondis, ordre optionnel)
# ===========================================================================
def _normalise(valeur, arrondi=2):
    """Rend une valeur comparable : arrondit les floats, récursif sur les conteneurs."""
    if isinstance(valeur, float):
        return round(valeur, arrondi)
    if isinstance(valeur, list):
        return [_normalise(v, arrondi) for v in valeur]
    if isinstance(valeur, tuple):
        return tuple(_normalise(v, arrondi) for v in valeur)
    if isinstance(valeur, set):
        return frozenset(_normalise(v, arrondi) for v in valeur)
    if isinstance(valeur, dict):
        return {k: _normalise(v, arrondi) for k, v in valeur.items()}
    return valeur


def valeurs_egales(a, b):
    """Égalité tolérante aux floats et à la représentation."""
    return _normalise(a) == _normalise(b)


# ===========================================================================
# 2. NAMESPACE d'exécution du code de Julien
# ===========================================================================
def _namespace(defi):
    """Construit l'espace de noms disponible pour eval/exec d'un défi.

    JOUEURS et joueurs pointent vers le dataset ; le `contexte` du défi (variables
    d'appoint comme pts_par_equipe) est ajouté. Les builtins sont injectés
    automatiquement par Python puisqu'on ne fixe pas __builtins__.
    """
    ns = {"JOUEURS": JOUEURS, "joueurs": JOUEURS}
    ns.update(defi.get("contexte", {}))
    return ns


# ===========================================================================
# 3. ÉVALUATION DES 3 TYPES DE MANCHES
# ===========================================================================
# Chaque évaluateur renvoie un dict : {"correct": bool, "attendu": str, "detail": str}
# `detail` est un message court (ex : le message d'erreur) — jamais un crash.

def evaluer_predire(defi, reponse_utilisateur):
    """L'attendu est la sortie RÉELLE du code exécuté (correct-by-construction)."""
    ns = _namespace(defi)
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            exec(defi["code"], ns)
    except Exception as e:  # ne devrait pas arriver (code interne), mais on protège
        return {"correct": False, "attendu": "?", "detail": f"Erreur interne : {e}"}
    attendu = buf.getvalue().strip()
    donnee = (reponse_utilisateur or "").strip()
    correct = _texte_normalise(donnee) == _texte_normalise(attendu)
    return {"correct": correct, "attendu": attendu, "detail": ""}


def evaluer_oneliner(defi, reponse_utilisateur):
    """Évalue l'expression tapée par Julien et la compare à la référence."""
    if not (reponse_utilisateur or "").strip():
        return {"correct": False, "attendu": defi["ref"], "detail": "Réponse vide."}
    ns = _namespace(defi)
    try:
        attendu = eval(defi["ref"], _namespace(defi))
    except Exception as e:
        return {"correct": False, "attendu": defi["ref"], "detail": f"Réf. cassée : {e}"}
    try:
        obtenu = eval(reponse_utilisateur, ns)
    except Exception as e:
        return {"correct": False, "attendu": _repr(attendu),
                "detail": f"Ton expression lève une erreur : {type(e).__name__} — {e}"}
    correct = valeurs_egales(obtenu, attendu)
    detail = "" if correct else f"Ton résultat : {_repr(obtenu)}"
    return {"correct": correct, "attendu": _repr(attendu), "detail": detail}


def ecrire_stub(defi):
    """(Ré)écrit reponse.py avec un squelette de la fonction attendue."""
    contenu = (
        '"""Écris ta réponse ici, puis sauvegarde (Cmd+S) et reviens taper Entrée dans l\'Arène."""\n\n'
        f"# {defi['enonce'].splitlines()[0]}\n"
        f"def {defi['fonction']}(joueurs):\n"
        "    # ton code\n"
        "    pass\n"
    )
    with open(FICHIER_REPONSE, "w", encoding="utf-8") as f:
        f.write(contenu)


def evaluer_ecrire(defi):
    """Recharge reponse.py, récupère la fonction, la teste sur les cas cachés.

    Toute erreur (import, fonction absente, exception, mauvais résultat) est
    transformée en message — le jeu ne crashe jamais.
    """
    try:
        if "reponse" in globals().get("_modules_charges", {}):
            module = importlib.reload(globals()["_modules_charges"]["reponse"])
        else:
            module = importlib.import_module("reponse")
        module = importlib.reload(module)
        globals().setdefault("_modules_charges", {})["reponse"] = module
    except Exception as e:
        return {"correct": False, "attendu": defi["fonction"],
                "detail": f"reponse.py ne s'importe pas : {type(e).__name__} — {e}"}

    fonction = getattr(module, defi["fonction"], None)
    if fonction is None:
        return {"correct": False, "attendu": defi["fonction"],
                "detail": f"Je ne trouve pas de fonction '{defi['fonction']}' dans reponse.py."}
    if not callable(fonction):
        return {"correct": False, "attendu": defi["fonction"],
                "detail": f"'{defi['fonction']}' existe mais n'est pas une fonction."}

    for i, args in enumerate(defi["cas"], start=1):
        try:
            obtenu = fonction(*args)
        except Exception as e:
            return {"correct": False, "attendu": defi["fonction"],
                    "detail": f"Ta fonction lève une erreur sur le cas {i} : {type(e).__name__} — {e}"}
        attendu = defi["ref"](*args)
        if not valeurs_egales(obtenu, attendu):
            return {"correct": False, "attendu": _repr(attendu),
                    "detail": (f"Cas {i} : ta fonction renvoie {_repr(obtenu)} "
                               f"au lieu de {_repr(attendu)}.")}
    return {"correct": True, "attendu": "", "detail": "Tous les cas passent."}


def evaluer(defi, reponse_utilisateur=None):
    """Aiguille vers le bon évaluateur selon le type de manche."""
    if defi["type"] == "predire":
        return evaluer_predire(defi, reponse_utilisateur)
    if defi["type"] == "oneliner":
        return evaluer_oneliner(defi, reponse_utilisateur)
    if defi["type"] == "ecrire":
        return evaluer_ecrire(defi)
    return {"correct": False, "attendu": "?", "detail": f"Type inconnu : {defi['type']}"}


# --- petits utilitaires d'affichage des valeurs ---
def _repr(valeur):
    """repr lisible, avec floats arrondis pour ne pas afficher 9.000000001."""
    return repr(_normalise(valeur))


def _texte_normalise(txt):
    """Normalise une sortie texte pour la comparaison en retirant TOUS les espaces.

    Python affiche toujours `[0, 2, 4, 6]` avec une espace après chaque virgule ; un
    débutant qui tape `[0,2,4,6]` a la BONNE réponse et ne doit pas être buzzé pour ça.
    Les défis 'predire' de la v1 affichent des valeurs (listes, dicts, sets, nombres),
    jamais des phrases où l'espacement porterait du sens — donc ignorer les espaces est sûr.
    """
    return "".join(txt.split())


# ===========================================================================
# 4. POINTS
# ===========================================================================
def points_manche(defi, nb_indices, multiplicateur):
    """Points gagnés pour une manche réussie, indices déduits, combo appliqué."""
    base = POINTS_BASE.get(defi["difficulte"], 100)
    apres_indices = max(base - nb_indices * MALUS_INDICE, 20)  # plancher à 20
    return int(apres_indices * multiplicateur)


# ===========================================================================
# 5. SÉLECTION PAR LES GAMMES
# ===========================================================================
def choisir_defi(etat, deja_vus_session):
    """Choisit le prochain défi selon la logique des gammes.

    - On fait tourner les 4 briques en alternance (celle la moins récemment jouée).
    - Dans une brique, on prend la plus petite difficulté encore NON réussie
      (dans la saison), pour monter progressivement.
    - Rien de neuf à faire dans une brique → on re-propose une variante déjà vue
      (répétition espacée) en évitant de répéter le tout dernier défi de la session.

    `etat` : dict de progression (contient 'defis_reussis' et 'derniere_brique').
    `deja_vus_session` : liste d'ids déjà servis dans la session courante.
    Renvoie un défi (dict) ou None si la banque est vide.
    """
    briques = banque.BRIQUES_V1
    reussis = set(etat.get("defis_reussis", []))
    derniere = etat.get("derniere_brique")

    # Ordre des briques à tenter : commencer juste après la dernière jouée (rotation).
    if derniere in briques:
        depart = (briques.index(derniere) + 1) % len(briques)
    else:
        depart = 0
    ordre = [briques[(depart + i) % len(briques)] for i in range(len(briques))]

    dernier_id = deja_vus_session[-1] if deja_vus_session else None

    # 1) priorité : un défi jamais réussi, difficulté la plus basse, en tournant les briques.
    meilleur = None
    for brique in ordre:
        candidats = [d for d in banque.DEFIS
                     if d["brique"] == brique and d["id"] not in reussis]
        if candidats:
            candidats.sort(key=lambda d: d["difficulte"])
            return candidats[0]

    # 2) tout est réussi au moins une fois → révision : une variante de la brique
    #    suivante, en évitant le tout dernier défi servi.
    for brique in ordre:
        candidats = [d for d in banque.DEFIS
                     if d["brique"] == brique and d["id"] != dernier_id]
        if candidats:
            candidats.sort(key=lambda d: d["difficulte"])
            return candidats[0]

    # 3) filet de sécurité : n'importe quel défi.
    return banque.DEFIS[0] if banque.DEFIS else None


def niveau_depuis_score(score):
    """Un 'niveau' cosmétique qui monte avec le score (1 niveau / 500 pts)."""
    return 1 + score // 500


# ===========================================================================
# 6. PERSISTANCE  (progression.json)
# ===========================================================================
def _etat_neuf():
    return {
        "saison": 1,
        "niveau": 1,
        "score_total": 0,
        "record_streak": 0,
        "briques_debloquees": list(banque.BRIQUES_V1),
        "defis_reussis": [],
        "derniere_brique": None,
        "derniere_session": None,
    }


def charger_etat():
    """Charge la progression. Fichier absent ou corrompu → nouvel état propre, sans crash."""
    if not os.path.exists(FICHIER_PROGRESSION):
        return _etat_neuf()
    try:
        with open(FICHIER_PROGRESSION, encoding="utf-8") as f:
            etat = json.load(f)
        if not isinstance(etat, dict):
            raise ValueError("format inattendu")
    except (json.JSONDecodeError, ValueError, OSError):
        return _etat_neuf()
    # Complète les clés manquantes (compat ascendante).
    base = _etat_neuf()
    base.update({k: v for k, v in etat.items() if k in base})
    return base


def sauver_etat(etat):
    """Écrit la progression sur disque (best-effort ; une erreur disque ne casse pas le jeu)."""
    etat["derniere_session"] = datetime.date.today().isoformat()
    etat["niveau"] = niveau_depuis_score(etat.get("score_total", 0))
    try:
        with open(FICHIER_PROGRESSION, "w", encoding="utf-8") as f:
            json.dump(etat, f, ensure_ascii=False, indent=2)
    except OSError:
        pass
