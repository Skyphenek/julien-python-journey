"""Portions : les quantités qu'on peut multiplier dans le texte d'une recette (fiche « À table / À garder »).

Python repère et marque (segments) ; le JavaScript de la fiche (SCRIPT_PORTIONS) multiplie et arrondit.
"""
import re

NOMBRE = r"\d+\s+\d+/\d+|\d+/\d+|\d+(?:[.,]\d+)?"                 # « 1 1/2 », « 1/2 », « 1,2 », « 320 »
QUANTITE = re.compile(rf"(?<![\w:/.,])({NOMBRE})(?:\s?([–-])\s?({NOMBRE}))?(?![\w:/]|[.,]\d)")
METRIQUE = re.compile(r"\s?(kg|g|ml|cl|l)(?![\wÀ-ÿ’'])")
PAS_UNE_QUANTITE = re.compile(r"\s?(?:min\b|h\b|°|%)")
BASE = re.compile(r"^Pour (\d+)(?=$|[\s,(—])(.*)$")
SUITE_ADMISE = re.compile(r"^(?:$|\s*[,(—]|\s+(?:portions?|personnes?)\b)")
DEUX_REPAS = re.compile(r"deux (?:repas|dîners)")
PLUS_PARTS = re.compile(r"plus (\d+) parts?")
SECTIONS_METRIQUES = ("Variante", "Erreurs", "Avec")              # là, seuls les g/kg/ml/cl/l bougent


def base_parts(pour):
    """« Pour … » -> {"table", "garder"} de départ des compteurs, ou None : portion floue, pas de compteurs."""
    m = BASE.match(pour or "")
    if not m or not SUITE_ADMISE.match(m.group(2)):
        return None
    n, suite = int(m.group(1)), m.group(2)
    if not 1 <= n <= 12:
        return None
    if DEUX_REPAS.search(suite) and n % 2 == 0:
        return {"table": n // 2, "garder": n // 2}
    plus = PLUS_PARTS.search(suite)
    if plus:
        return {"table": n, "garder": int(plus.group(1))}
    return {"table": n, "garder": 0}


def _valeur(nombre):
    """« 1 1/2 » -> 1.5, « 1,2 » -> 1.2 ; None si illisible (1/0)."""
    n = re.sub(r"\s+", " ", nombre.strip()).replace(",", ".")
    try:
        if "/" in n:
            entier, _, fraction = n.rpartition(" ")
            haut, bas = fraction.split("/")
            return (float(entier) if entier else 0.0) + int(haut) / int(bas)
        return float(n)
    except (ValueError, ZeroDivisionError):
        return None


def segmenter(texte, premier=False):
    """Texte -> segments {"t"} ou {"t", "q", "u"} (+ "q2", "sep" pour une plage) ; les "t" bout à bout redonnent
    le texte. premier : le 1er nombre est la quantité de la ligne, quelle que soit son unité (sauf min, h, °, %) ;
    les autres nombres ne comptent que suivis de g, kg, ml, cl, l."""
    segments, i, vu = [], 0, False
    for m in QUANTITE.finditer(texte):
        apres = texte[m.end():]
        unite = METRIQUE.match(apres)
        if premier and not vu:
            vu = True
            garde = not PAS_UNE_QUANTITE.match(apres)
        else:
            garde = unite is not None
        q = _valeur(m.group(1))
        q2 = _valeur(m.group(3)) if m.group(3) else None
        if not garde or q is None or (m.group(3) and q2 is None):
            continue
        if m.start() > i:
            segments.append({"t": texte[i:m.start()]})
        s = {"t": m.group(0), "q": q, "u": unite.group(1) if unite else ""}
        if m.group(3):
            s.update({"q2": q2, "sep": texte[m.end(1):m.start(3)]})
        segments.append(s)
        i = m.end()
    if i < len(texte):
        segments.append({"t": texte[i:]})
    return segments


SCRIPT_PORTIONS = r"""
    // --- Portions (portions.py) : multiplier les quantités repérées en Python, arrondir pour la cuisine ---
    function arrondiPortion(q, u) {
        if (u === 'g' || u === 'ml') { const pas = q < 100 ? 5 : 10; return Math.max(Math.round(q / pas) * pas, pas); }
        if (u === 'kg' || u === 'l') return Math.max(Math.round(q * 10) / 10, 0.1);
        if (u === 'cl') return Math.max(Math.round(q), 1);
        return Math.max(Math.round(q * 2) / 2, 0.5);                 // à la pièce, à la cuillère : à la demie
    }
    function ecrirePortion(n, u) {
        if (u !== '') return String(n).replace('.', ',');
        const entier = Math.floor(n), demi = n - entier >= 0.5;
        if (!entier) return '1/2';
        return demi ? entier + ' 1/2' : String(entier);
    }
    function texteAjuste(segments, facteur) {
        return segments.map(function (s) {
            if (s.q === undefined || facteur === 1) return s.t;
            let t = ecrirePortion(arrondiPortion(s.q * facteur, s.u), s.u);
            if (s.q2 !== undefined) t += s.sep + ecrirePortion(arrondiPortion(s.q2 * facteur, s.u), s.u);
            return t;
        }).join('');
    }
"""
