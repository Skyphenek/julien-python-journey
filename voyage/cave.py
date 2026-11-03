"""Casa Binomerie — Cave : les vins à boire, tenus en un tap (spec : docs/superpowers/specs/2026-11-03-casa-cave-design.md).

Une ligne par référence (nom, millésime, couleur…) avec sa quantité et sa fenêtre à boire. Les vins de cuisine
restent au placard (Courses). Le vin du soir : accords_vins.py.
"""
from accords_vins import PROFILS

COULEURS = [("rouge", "Rouge"), ("blanc", "Blanc"), ("rose", "Rosé"), ("bulles", "Effervescent"), ("doux", "Doux")]
# Fenêtre à boire par défaut, en années après le millésime (début, fin)
_FENETRE = {"rouge": (2, 6), "blanc": (0, 2), "rose": (0, 2), "bulles": (0, 5), "doux": (0, 5)}
ACCORDS_PAR_COULEUR = {"rouge": ["boeuf", "charcuterie"], "blanc": ["poisson", "fromage"],
                       "rose": ["legumes", "apero"], "bulles": ["apero"], "doux": ["dessert", "fromage"]}
MAX_TEXTE = 200


def par_defaut(couleur, millesime, annee):
    """(début, fin, accords) d'un vin ajouté sans fenêtre ni accords. Sans millésime : de cette année à +2.
    Le début n'est jamais avant cette année, la fin jamais avant le début."""
    if millesime is None:
        debut, fin = annee, annee + 2
    else:
        avant, apres = _FENETRE[couleur]
        debut, fin = max(millesime + avant, annee), millesime + apres
    return debut, max(fin, debut), list(ACCORDS_PAR_COULEUR[couleur])


def statut(b, annee):
    """« garder » (fenêtre pas encore ouverte), « vite » (elle se ferme cette année ou est passée), sinon « prete »."""
    if b["debut"] > annee:
        return "garder"
    return "vite" if b["fin"] <= annee else "prete"


def _entier(corps, cle, mini, maxi, defaut=None):
    """Entier de la plage [mini, maxi]. Un null (ou une clé absente) prend la valeur par défaut."""
    v = corps.get(cle)
    if v is None:
        v = defaut
    if v is None:
        return None
    if isinstance(v, bool) or not isinstance(v, int) or not mini <= v <= maxi:
        raise ValueError(f"{cle} invalide")
    return v


def _texte(corps, cle, obligatoire=False):
    v = corps.get(cle) or ""
    if not isinstance(v, str) or len(v) > MAX_TEXTE:
        raise ValueError(f"{cle} invalide")
    v = v.strip()
    if obligatoire and not v:
        raise ValueError(f"{cle} manquant")
    return v


def valider_bouteille(corps, annee):
    """Une bouteille venue du téléphone, vérifiée et complétée (fenêtre et accords par défaut s'ils manquent)."""
    if not isinstance(corps, dict):
        raise ValueError("bouteille invalide")
    identifiant = _texte(corps, "id", obligatoire=True)
    if len(identifiant) > 64:
        raise ValueError("id invalide")
    couleur = corps.get("couleur")
    if not isinstance(couleur, str) or couleur not in dict(COULEURS):
        raise ValueError("couleur invalide")
    millesime = _entier(corps, "millesime", 1900, annee)
    debut, fin, accords = par_defaut(couleur, millesime, annee)
    debut = _entier(corps, "debut", 1900, 2200, debut)
    fin = _entier(corps, "fin", 1900, 2200, fin)
    if debut > fin:
        raise ValueError("fenêtre invalide")
    if corps.get("accords") is not None:
        accords = corps["accords"]
    if not isinstance(accords, list) or any(a not in PROFILS for a in accords):
        raise ValueError("accords invalides")
    prix_bas = _entier(corps, "prix_bas", 0, 10000)
    prix_haut = _entier(corps, "prix_haut", 0, 10000)
    if prix_bas is not None and prix_haut is not None and prix_bas > prix_haut:
        raise ValueError("prix invalides")
    return {"id": identifiant, "nom": _texte(corps, "nom", obligatoire=True), "producteur": _texte(corps, "producteur"),
            "appellation": _texte(corps, "appellation"), "region": _texte(corps, "region"), "couleur": couleur,
            "millesime": millesime, "quantite": _entier(corps, "quantite", 0, 999, 1), "debut": debut, "fin": fin,
            "prix_bas": prix_bas, "prix_haut": prix_haut, "accords": [p for p in PROFILS if p in accords],
            "note": _texte(corps, "note")}
