"""Découpe le texte d'une recette (format chef-casa, ou plus ancien) en fiche structurée pour l'affichage.

Le texte reste la seule source en base : on le relit à chaque affichage, on ne stocke rien.
"""
import re

ETAPE = re.compile(r"^(\d+)[.)]\s+(.*)$")
SOUS_PUCE = re.compile(r"^\s+-\s+(.*)$")
LIGNE_TEMPO = re.compile(r"^-\s+(\d+:\d\d)\s+(.*)$")
RENVOI = re.compile(r"\((\d+)\)")
COUPE_INGREDIENT = re.compile(r"\s+(?::|—)\s+")


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
        return _lire_lignes(str(texte))
    except Exception:                                    # le texte vient aussi de « Modifier » : tout peut arriver
        return _vide()
