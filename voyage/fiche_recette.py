"""Découpe le texte d'une recette (format chef-casa, ou plus ancien) en fiche structurée pour l'affichage.

Le texte reste la seule source en base : on le relit à chaque affichage, on ne stocke rien.
"""
import re

ETAPE = re.compile(r"^(\d+)[.)]\s+(.*)$")
SOUS_PUCE = re.compile(r"^\s+-\s+(.*)$")
LIGNE_TEMPO = re.compile(r"^-\s+(\d+:\d\d|Veille|La veille)\s+(.*)$")   # « Veille » : marinade, salage
RENVOI = re.compile(r"\((\d+)\)")
COUPE_INGREDIENT = re.compile(r"\s+(?::|—)\s+")
SECRET = re.compile(r"\s*\(secret de (grand-mère|mamma)\s*:\s*((?:[^()]|\([^()]*\))*)\)", re.IGNORECASE)
FIN_DE_PHRASE = re.compile(r"\.\s(?=[A-ZÀ-ÖØ-Ý«])")       # « c. à s. » n'est pas une fin de phrase
POURQUOI = re.compile(r"\s—\s")


def _coupe_action(texte):
    """Indice de fin de l'action : 1er point de phrase (inclus), « : » (inclus) ou « — » (exclu)."""
    candidats = []
    m = FIN_DE_PHRASE.search(texte)
    if m:
        candidats.append(m.start() + 1)
    i = texte.find(" : ")
    if i > 0:
        candidats.append(i + 2)
    m = POURQUOI.search(texte)
    if m:
        candidats.append(m.start())
    return min(candidats) if candidats else len(texte)


def _morceaux(reste):
    """Le reste de l'étape en morceaux texte / pourquoi (« — … » jusqu'à la fin de phrase ou « ; »)."""
    morceaux, i = [], 0
    while i < len(reste):
        m = POURQUOI.search(reste, i)
        if not m:
            morceaux.append({"genre": "texte", "texte": reste[i:]})
            break
        if m.start() > i:
            morceaux.append({"genre": "texte", "texte": reste[i:m.start()]})
        debut = m.start() + 1                             # garde le « — » dans le pourquoi
        fin_phrase = FIN_DE_PHRASE.search(reste, debut)
        point_virgule = reste.find(";", debut)
        fins = [x for x in (fin_phrase.start() + 1 if fin_phrase else -1, point_virgule) if x != -1]
        fin = min(fins) if fins else len(reste)
        morceaux.append({"genre": "pourquoi", "texte": reste[debut:fin]})
        i = fin
    return [m for m in morceaux if m["texte"].strip()]


def decouper_phrase(texte):
    """Une étape (ou une sous-puce) -> action en gras, morceaux texte/pourquoi, secrets en encadré."""
    secrets = [{"qui": "mamma" if s.group(1).lower() == "mamma" else "grand-mere", "texte": s.group(2).strip()}
               for s in SECRET.finditer(texte)]
    propre = SECRET.sub("", texte).strip()
    coupe = _coupe_action(propre)
    return {"action": propre[:coupe].rstrip(), "morceaux": _morceaux(propre[coupe:]), "secrets": secrets}


def _vide():
    return {"structuree": False, "pour": "", "ingredients": [], "sections": [], "tempo": None,
            "etapes": [], "difference": []}


def _ingredient(ligne):
    morceaux = COUPE_INGREDIENT.split(ligne, maxsplit=1)
    if len(morceaux) == 2:
        return {"nom": morceaux[0].strip(), "quantite": morceaux[1].strip()}
    return {"nom": ligne.strip(), "quantite": ""}


def _lire_lignes(texte):
    f = _vide()
    zone, etape, section = "ingredients", None, None
    for brute in texte.split("\n"):
        ligne = brute.rstrip()
        if not ligne.strip():
            continue
        if not f["pour"] and zone == "ingredients" and not f["ingredients"] and ligne.startswith("Pour "):
            f["pour"] = ligne.strip()
            continue
        if ligne.startswith("Tempo"):
            zone, f["tempo"] = "tempo", {"titre": ligne.strip(), "lignes": []}
            continue
        if ligne.startswith("Ce qui fait la différence"):
            zone = "difference"
            continue
        m = ETAPE.match(ligne)
        if m:
            zone, etape = "etapes", {"n": int(m.group(1)), "texte": m.group(2).strip(), "si": []}
            f["etapes"].append(etape)
            continue
        if zone == "etapes" and SOUS_PUCE.match(ligne):
            etape["si"].append(SOUS_PUCE.match(ligne).group(1).strip())
            continue
        if zone == "etapes" and ligne[:1].isspace():         # phrase indentée après les sous-puces : même étape
            etape["si"].append(ligne.strip())
            continue
        if zone == "tempo":
            t = LIGNE_TEMPO.match(ligne)
            if t:
                f["tempo"]["lignes"].append({"heure": t.group(1), "texte": t.group(2).strip(),
                                             "etapes": [int(n) for n in RENVOI.findall(t.group(2))]})
                continue
        if zone == "difference" and ligne.startswith("- "):
            f["difference"].append(ligne[2:].strip())
            continue
        if ligne.startswith("- "):
            if section is not None and zone == "sections":
                section["lignes"].append(ligne[2:].strip())
            else:
                f["ingredients"].append(_ingredient(ligne[2:]))
            continue
        # toute autre ligne : un titre de section (ou un paragraphe libre)
        titre = ligne.strip()
        titre = titre[:-1].rstrip() if titre.endswith(":") else titre
        section = {"titre": titre, "lignes": []}
        f["sections"].append(section)
        zone = "sections"
    f["structuree"] = bool(f["etapes"])
    return f


def decouper(texte):
    """Texte brut d'une recette -> fiche (dict). Ne lève jamais : en cas de souci, fiche non structurée."""
    if not texte or not str(texte).strip():
        return _vide()
    try:
        f = _lire_lignes(str(texte))
        f["etapes"] = [{"n": e["n"], **decouper_phrase(e["texte"]), "si": [decouper_phrase(s) for s in e["si"]]}
                       for e in f["etapes"]]
        return f
    except Exception:                                    # le texte vient aussi de « Modifier » : tout peut arriver
        return _vide()
