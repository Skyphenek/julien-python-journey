"""Casa Binomerie — Sortir : les envies du couple. Une pile à trier par personne, les Envies (ça plaît aux deux), le
tirage « ce week-end », les rappels de fin et de date prévue. Règles pures ici ; la page plus bas (sortir_en_html)."""
import re
import unicodedata
from datetime import date, timedelta
from urllib.parse import urlsplit

TYPES = [("cine", "Ciné"), ("theatre", "Théâtre"), ("concert", "Concert"), ("expo", "Expo"),
         ("resto-bar", "Resto / bar"), ("balade", "Balade"), ("atelier", "Atelier"), ("escapade", "Escapade")]
BUDGETS = [("gratuit", "Gratuit"), ("moyen", "~30 €"), ("premium", "~80 € +")]
RESERVATIONS = [("non", "Sans réservation"), ("conseillee", "Réservation conseillée"), ("obligatoire", "À réserver")]
ETATS = ("a-trier", "envie", "prevue", "faite", "ecartee")
QUI = ("julien", "laetitia")
MOTS_VIDES = {"le", "la", "les", "l", "un", "une", "des", "de", "du", "d", "au", "aux", "a", "et", "en", "chez"}
FIN_PROCHE = 15          # jours : priorité au tirage
RAPPEL = 7               # jours : encart d'Aujourd'hui


def _date(valeur, cle):
    if not valeur:
        return None
    try:
        return date.fromisoformat(str(valeur)[:10])
    except ValueError:
        raise ValueError(f"{cle} : date invalide")


def _choix(corps, cle, options, defaut=None):
    v = corps.get(cle) or defaut
    if v is not None and v not in [o[0] if isinstance(o, tuple) else o for o in options]:
        raise ValueError(f"{cle} invalide")
    return v


def valider_sortie(corps, aujourd_hui):
    """Une idée validée, prête pour la base. Ajoutée par Julien ou Laetitia : leur avis est « oui »."""
    titre = " ".join(str(corps.get("titre") or "").split())
    if not 1 <= len(titre) <= 200:
        raise ValueError("titre : 1 à 200 caractères")
    lien = str(corps.get("lien") or "").strip()
    if lien and not re.match(r"https?://", lien):
        raise ValueError("lien : http ou https")
    source = _choix(corps, "source", ("routine",) + QUI)
    if source is None:
        raise ValueError("source manquante")
    debut, fin = _date(corps.get("debut"), "debut"), _date(corps.get("fin"), "fin")
    if debut and fin and fin < debut:
        raise ValueError("fin avant le début")
    return {"titre": titre, "type": _choix(corps, "type", TYPES), "budget": _choix(corps, "budget", BUDGETS),
            "reservation": _choix(corps, "reservation", RESERVATIONS), "debut": debut, "fin": fin, "lien": lien,
            "infos": str(corps.get("infos") or "").strip()[:1000], "source": source, "etat": "a-trier",
            "avis_julien": "oui" if source == "julien" else None,
            "avis_laetitia": "oui" if source == "laetitia" else None}


def _sans_accents(texte):
    texte = texte.lower().replace("œ", "oe").replace("æ", "ae")
    return "".join(c for c in unicodedata.normalize("NFD", texte) if unicodedata.category(c) != "Mn")


def cle_titre(titre):
    """« Le Refuge des Fondus ! » -> « refuge fondus » : casse, accents, ponctuation et mots vides retirés."""
    mots = re.findall(r"[a-z0-9]+", _sans_accents(titre))
    return " ".join(m for m in mots if m not in MOTS_VIDES)


def cle_lien(lien):
    """L'adresse sans protocole, sans « www. », sans query string ni « / » final."""
    if not lien:
        return ""
    p = urlsplit(lien.strip().lower())
    return (p.netloc.removeprefix("www.") + p.path).rstrip("/")


def doublon(nouvelle, existantes):
    """L'id d'une idée déjà en base (tout état) au même titre ou au même lien, sinon None."""
    t, l = cle_titre(nouvelle["titre"]), cle_lien(nouvelle.get("lien", ""))
    for e in existantes:
        if cle_titre(e["titre"]) == t or (l and cle_lien(e.get("lien", "")) == l):
            return e["id"]
    return None


def apres_avis(s, qui, avis):
    """L'idée après l'avis de qui : un « non » l'écarte, deux « oui » en font une Envie."""
    if qui not in QUI or avis not in ("oui", "non"):
        raise ValueError("avis invalide")
    s = {**s, f"avis_{qui}": avis}
    if avis == "non":
        s["etat"] = "ecartee"
    elif s["etat"] == "a-trier" and s["avis_julien"] == "oui" and s["avis_laetitia"] == "oui":
        s["etat"] = "envie"
    return s


def tirer_weekend(sorties, jour, hasard):
    """2 à 3 Envies : celles qui finissent dans FIN_PROCHE jours d'abord, puis au hasard ; une Premium au plus,
    jamais deux du même type. Une Envie déjà finie est ignorée."""
    envies = [s for s in sorties if s["etat"] == "envie" and not (s.get("fin") and s["fin"] < jour)]
    proches = sorted((s for s in envies if s.get("fin") and s["fin"] <= jour + timedelta(days=FIN_PROCHE)),
                     key=lambda s: s["fin"])
    reste = [s for s in envies if s not in proches]
    hasard.shuffle(reste)
    choix = []
    for s in proches + reste:
        if len(choix) == 3:
            break
        if s["type"] in {c["type"] for c in choix}:
            continue
        if s["budget"] == "premium" and any(c["budget"] == "premium" for c in choix):
            continue
        choix.append(s)
    return choix


def rappels(sorties, jour):
    """Pour Aujourd'hui : les Envies qui finissent dans RAPPEL jours, les sorties prévues dans RAPPEL jours, et si
    c'est le moment du tirage (vendredi, samedi)."""
    limite = jour + timedelta(days=RAPPEL)
    finissent = sorted((s for s in sorties if s["etat"] == "envie" and s.get("fin") and jour <= s["fin"] <= limite),
                       key=lambda s: s["fin"])
    prevues = sorted((s for s in sorties if s["etat"] == "prevue" and s.get("le") and jour <= s["le"] <= limite),
                     key=lambda s: s["le"])
    return {"finissent": finissent, "prevues": prevues, "weekend": jour.weekday() in (4, 5)}
