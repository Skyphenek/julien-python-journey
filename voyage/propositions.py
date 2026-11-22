"""Vadrouille — Propositions : des idées cherchées par une routine, rangées dans les créneaux libres du Programme.
Règles pures ici (créneaux, passages, validation) ; la base dans db.py, l'accès de la routine dans routine.py."""
import re
from datetime import date, datetime, time, timedelta

from programme import etapes_du_voyage

DEBUT_JOUR, FIN_JOUR = time(9), time(22, 30)
COUPURES = (time(13), time(18))
MINIMUM = timedelta(minutes=90)
ARRIVEE_HOTEL, DEPART_HOTEL = "15:00", "11:00"          # heures d'hôtel non saisies
AVANT = {"vol": timedelta(hours=3), "transport": timedelta(hours=1)}
APRES = {"vol": timedelta(minutes=90), "transport": timedelta(minutes=30)}
TRAJETS = ("vol", "transport")


# --- Créneaux libres --------------------------------------------------------------------------

def _instant(jour, heure):
    return datetime.combine(jour, time.fromisoformat(heure))


def jours_du_voyage(voyage, reservations):
    """Du départ à la fin de l'itinéraire, prolongé par la dernière réservation (retour le lendemain, par exemple)."""
    total = sum(e["jours"] for e in voyage["itineraire"])
    dernier = max([voyage["depart"] + timedelta(days=max(total, 1) - 1)]
                  + [r["jour_fin"] or r["jour"] for r in reservations])
    return [voyage["depart"] + timedelta(days=n) for n in range((dernier - voyage["depart"]).days + 1)]


def _hotels(reservations):
    return sorted((r for r in reservations if r["type"] == "hotel" and r["jour_fin"]),
                  key=lambda r: (r["jour"], r["heure"] or ARRIVEE_HOTEL))


def _trajet(r):
    """(début, fin) pris par un vol ou un transport, marges comprises ; heure absente : la journée."""
    jour_fin = r["jour_fin"] or r["jour"]
    debut = _instant(r["jour"], r["heure"]) - AVANT[r["type"]] if r["heure"] else datetime.combine(r["jour"], time.min)
    fin = (_instant(jour_fin, r["heure_fin"]) + APRES[r["type"]] if r["heure"] and r["heure_fin"]
           else datetime.combine(jour_fin, time.max))
    return debut, fin


def _bornes(jours, reservations):
    """(début, fin) du séjour : de l'arrivée sur place à 3 h avant le vol du retour."""
    hotels, trajets = _hotels(reservations), [r for r in reservations if r["type"] in TRAJETS]
    premier, dernier = jours[0], jours[-1]
    if hotels:
        premier, dernier = hotels[0]["jour"], max(h["jour_fin"] for h in hotels)
    arrivees = [r for r in trajets if (r["jour_fin"] or r["jour"]) == premier and r["jour"] <= premier]
    arrivees = [r for r in arrivees if r["type"] == "vol"] or arrivees[:1]
    if arrivees and all(r["heure"] and r["heure_fin"] for r in arrivees):
        debut = max(_trajet(r)[1] for r in arrivees)
    else:
        debut = _instant(premier, (hotels[0]["heure"] if hotels else "") or ARRIVEE_HOTEL)
    departs = [r for r in trajets if r["jour"] >= dernier and r not in arrivees]
    vols = [r for r in departs if r["type"] == "vol"]
    retour = vols[0] if vols else departs[-1] if departs else None
    fin = _trajet(retour)[0] if retour else datetime.combine(dernier, time.max)
    return debut, fin, arrivees + ([retour] if retour else [])


def _pris(jours, reservations):
    """Les intervalles pris pendant le séjour."""
    debut, fin, bornes = _bornes(jours, reservations)
    pris = [(datetime.combine(jours[0], time.min), debut), (fin, datetime.combine(jours[-1], time.max))]
    for r in reservations:
        if r["type"] in TRAJETS and r not in bornes:
            pris.append(_trajet(r))
        elif r["type"] not in TRAJETS and r["type"] != "hotel" and r["heure"]:
            d = _instant(r["jour"], r["heure"])
            f = _instant(r["jour_fin"] or r["jour"], r["heure_fin"]) if r["heure_fin"] else d + timedelta(hours=2)
            pris.append((d, f if f > d else d + timedelta(hours=2)))
    hotels = _hotels(reservations)
    for avant, apres in zip(hotels, hotels[1:]):
        if avant["jour_fin"] == apres["jour"]:
            pris.append((_instant(apres["jour"], avant["heure_fin"] or DEPART_HOTEL),
                         _instant(apres["jour"], apres["heure"] or ARRIVEE_HOTEL)))
    return [(d, f) for d, f in pris if d < f]


def _libres(jour, pris):
    """Les morceaux libres du jour, coupés à 13 h et 18 h ; un morceau de moins de 1 h 30 rejoint son voisin ou tombe."""
    bords = [(datetime.combine(jour, DEBUT_JOUR), datetime.combine(jour, FIN_JOUR))]
    for d, f in pris:
        bords = [m for a, b in bords for m in ((a, min(b, d)), (max(a, f), b)) if m[0] < m[1]]
    resultat = []
    for a, b in sorted(bords):
        coupes = [a] + [c for c in (datetime.combine(jour, h) for h in COUPURES) if a < c < b] + [b]
        morceaux = list(zip(coupes, coupes[1:]))
        i = 0
        while i < len(morceaux):
            d, f = morceaux[i]
            if f - d >= MINIMUM or len(morceaux) == 1:
                i += 1
            elif i + 1 < len(morceaux):
                morceaux[i:i + 2] = [(d, morceaux[i + 1][1])]
            else:
                morceaux[i - 1:i + 1] = [(morceaux[i - 1][0], f)]
        resultat += [m for m in morceaux if m[1] - m[0] >= MINIMUM]
    return resultat


def _ancre(instant, hotels):
    """L'hôtel où l'on est à cet instant (le premier, si l'on n'y est pas encore arrivé) ; None sans hôtel ce jour-là."""
    jour = instant.date()
    presents = [h for h in hotels if h["jour"] <= jour <= h["jour_fin"]]
    arrives = [h for h in presents if _instant(h["jour"], h["heure"] or ARRIVEE_HOTEL) <= instant]
    return arrives[-1] if arrives else presents[0] if presents else None


def creneaux(voyage, reservations):
    """Les créneaux libres du voyage, dans l'ordre : id, jour, période, heures, ancre (hôtel), étape."""
    if not voyage["itineraire"]:
        return []
    jours = jours_du_voyage(voyage, reservations)
    pris, hotels = _pris(jours, reservations), _hotels(reservations)
    etapes = etapes_du_voyage(voyage["itineraire"], voyage["depart"])
    resultat, ids = [], set()
    for jour in jours:
        etape = next((e for e in etapes if e["du"] <= jour <= e["au"]), etapes[-1])
        for d, f in _libres(jour, pris):
            periode = "matin" if d.hour < 12 else "après-midi" if d.hour < 18 else "soir"
            base = f"{jour.isoformat()}-{periode.replace('è', 'e')}"
            ident, n = base, 2
            while ident in ids:
                ident, n = f"{base}-{n}", n + 1
            ids.add(ident)
            hotel = _ancre(d, hotels)
            resultat.append({"id": ident, "jour": jour, "periode": periode, "debut": f"{d:%H:%M}", "fin": f"{f:%H:%M}",
                             "ancre": hotel["titre"] if hotel else etape["destination"],
                             "adresse": hotel["lieu"] if hotel else "",
                             "destination": etape["destination"], "rang": etape["rang"]})
    return resultat


# --- Passages de la routine -------------------------------------------------------------------

PAR_CRENEAU, PAR_PASSAGE = 2, 12
ETATS = ("proposee", "gardee", "planifiee", "ecartee")


def passage_du(jours, faits, aujourd_hui):
    """Le passage à faire aujourd'hui (« J-14 », « J-7 », « J-2 », « soir-AAAA-MM-JJ ») ou None. Pas fait : encore dû le lendemain."""
    avant = (jours[0] - aujourd_hui).days
    if avant > 14 or aujourd_hui >= jours[-1]:
        return None
    palier = ("J-14" if avant > 7 else "J-7" if avant > 2 else "J-2" if avant > 0
              else f"soir-{aujourd_hui.isoformat()}")
    return None if palier in faits else palier


def visibles(propositions, creneaux):
    """Les fiches ouvertes dont le créneau existe encore, avec la même ancre."""
    ancres = {c["id"]: c["ancre"] for c in creneaux}
    return [p for p in propositions if p["etat"] == "proposee" and ancres.get(p["creneau"]) == p["ancre"]]


def a_chercher(creneaux, propositions, palier, aujourd_hui):
    """Les créneaux à remplir, avec leurs places ; le soir, ceux du lendemain seulement."""
    ouvertes = [p["creneau"] for p in visibles(propositions, creneaux)]
    demain = aujourd_hui + timedelta(days=1)
    return [{**c, "places": PAR_CRENEAU - ouvertes.count(c["id"])} for c in creneaux
            if ouvertes.count(c["id"]) < PAR_CRENEAU and (not palier.startswith("soir-") or c["jour"] == demain)]


# --- Validation : tout ce que dépose la routine est vérifié -----------------------------------

LONGUEURS = {"titre": 200, "pourquoi": 500, "adresse": 300, "trajet": 100, "duree": 60, "prix": 100, "horaires": 150,
             "a_confirmer": 300, "lien": 500, "source": 500}
RESERVATIONS = ("non", "conseillee", "obligatoire", "a-demander")


def valider_proposition(corps):
    """Une fiche de la routine -> champs propres ; ValueError sinon. Un prix ou un horaire exige une source."""
    if not isinstance(corps, dict):
        raise ValueError("proposition invalide")
    p = {}
    for champ, longueur in LONGUEURS.items():
        valeur = corps.get(champ) or ""
        if not isinstance(valeur, str):
            raise ValueError(f"{champ} invalide")
        p[champ] = " ".join(valeur.split())
        if len(p[champ]) > longueur:
            raise ValueError(f"{champ} trop long")
    if not p["titre"] or not p["pourquoi"]:
        raise ValueError("titre ou pourquoi manquant")
    for champ in ("lien", "source"):
        if p[champ] and not re.match(r"https?://", p[champ], re.IGNORECASE):
            raise ValueError(f"{champ} : http(s) seulement")
    if not p["source"] and (p["prix"] or p["horaires"]):
        raise ValueError("prix ou horaires sans source")
    if not p["source"] and not p["a_confirmer"]:
        raise ValueError("sans source : dire ce qui reste à confirmer")
    if corps.get("genre") not in ("voir", "faire"):
        raise ValueError("genre inconnu")
    if corps.get("reservation") not in RESERVATIONS:
        raise ValueError("réservation inconnue")
    return {**p, "genre": corps["genre"], "reservation": corps["reservation"]}
