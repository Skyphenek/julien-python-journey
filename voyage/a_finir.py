"""Casa Binomerie — À finir : ce qu'il faut manger avant que ça tourne, sans rien saisir
(spec docs/superpowers/specs/2026-11-03-casa-a-finir-design.md).

- suivis : le frais du frigo (placard de zone frigo en stock, habituels rangés de zone frigo) et sa date « à finir
  avant » : la correction s'il y en a une, sinon la date d'entrée (dernier achat, remise en stock) + la durée ;
- alertes (page Aujourd'hui) : à vérifier (date passée), et à finir d'ici A_FINIR_JOURS qu'aucun repas prévu n'utilise
  à temps, avec les plats du carnet qui l'utilisent et le premier soir libre pour en poser un.
"""
from datetime import date, timedelta

from conservation import duree
from courses import normaliser, deviner_zone

A_FINIR_JOURS = 2           # à finir d'ici après-demain (aujourd'hui compris) : on le signale
ENCORE_BON_JOURS = 2        # [Encore bon] : deux jours de plus
MAX_SUGGESTIONS = 3

# La reprise du frigo (03/11/2026) : ce qu'on sait déjà, {nom : (acheté le, à finir avant ou None = calculé)}
NOM_REPRISE = "a-finir-v1"
JOUR_REPRISE = date(2026, 11, 3)
FRIGO_CONNU = {"cuisses de poulet": (date(2026, 11, 1), None),
               "galettes de sarrasin": (date(2026, 11, 3), date(2026, 11, 9))}     # date imprimée


def suivis(placard, courses, derniers_achats, corrections):
    """Le frais du frigo daté, trié par date puis nom : [{cle, nom, origine ('placard' | 'habituel'), jusqu_au}].
    Sans date d'entrée ni correction (un habituel jamais acheté depuis le journal) : pas suivi."""
    produits = {}
    for p in placard:
        if p["en_stock"] and p["zone"] == "frigo":
            produits[p["cle"]] = ({"cle": p["cle"], "nom": p["nom"], "origine": "placard"}, p["entre_le"])
    for a in courses:
        cle = normaliser(a["nom"])
        if (a["recurrent"] and (not a["actif"] or a["pris"]) and cle not in produits
                and deviner_zone(a["nom"]) == "frigo"):
            produits[cle] = ({"cle": cle, "nom": a["nom"], "origine": "habituel"}, None)
    resultat = []
    for cle, (p, entre_le) in produits.items():
        dates = [d for d in (entre_le, derniers_achats.get(cle)) if d]
        if cle in corrections:
            jusqu_au = corrections[cle]
        elif dates:
            jusqu_au = max(dates) + timedelta(days=duree(p["nom"]))
        else:
            continue
        resultat.append({**p, "jusqu_au": jusqu_au})
    return sorted(resultat, key=lambda p: (p["jusqu_au"], p["nom"]))


def etat(jusqu_au, aujourd_hui):
    """'a-verifier' (date passée), 'a-finir' (d'ici A_FINIR_JOURS), ou None."""
    if jusqu_au < aujourd_hui:
        return "a-verifier"
    if jusqu_au <= aujourd_hui + timedelta(days=A_FINIR_JOURS):
        return "a-finir"
    return None


def utilise(plat, cle):
    return any(normaliser(i) == cle for i in plat["ingredients"])


def couverture(cle, jusqu_au, repas, par_id, aujourd_hui):
    """(couvert, trop tard) : un repas prévu (sans issue, tous moments) d'aujourd'hui à jusqu_au l'utilise ; sinon,
    le premier jour prévu après jusqu_au qui l'utilise, ou None."""
    jours = sorted(r["jour"] for r in repas if not r["issue"] and r["jour"] >= aujourd_hui
                   and any(i in par_id and utilise(par_id[i], cle) for i in r["plats"]))
    if any(j <= jusqu_au for j in jours):
        return True, None
    return False, (jours[0] if jours else None)


def suggestions(cle, cles_a_finir, plats, stock):
    """Les plats du carnet pour nous deux qui utilisent le produit : ceux qui finissent le plus de produits d'abord,
    puis ceux à qui il manque le moins, puis les plus rapides. [{plat, manquants}], MAX_SUGGESTIONS au plus."""
    resultat = []
    for p in plats:
        if (p["genre"] == "plat" and p["statut"] == "carnet" and not p["archive"]
                and p.get("pour", "nous") == "nous" and utilise(p, cle)):
            manquants = [i for i in p["ingredients"] if normaliser(i) not in stock]
            finis = sum(1 for c in cles_a_finir if utilise(p, c))
            resultat.append(((-finis, len(manquants), p["minutes"], p["nom"]), {"plat": p, "manquants": manquants}))
    return [s for _, s in sorted(resultat, key=lambda x: x[0])][:MAX_SUGGESTIONS]


def jour_libre(repas, aujourd_hui, jusqu_au):
    """Le premier soir d'aujourd'hui à jusqu_au sans dîner (ni plat ni issue), ou None."""
    pris = {r["jour"] for r in repas if r["moment"] == "diner" and (r["plats"] or r["issue"])}
    jour = aujourd_hui
    while jour <= jusqu_au:
        if jour not in pris:
            return jour
        jour += timedelta(days=1)
    return None


def alertes(produits, repas, plats, stock, aujourd_hui):
    """Ce que la page Aujourd'hui signale : les produits à vérifier (sans plats : [Fini] ou [Encore bon] d'abord), et
    les produits à finir qu'aucun repas prévu n'utilise à temps (trop_tard : le jour où il est prévu, trop tard), avec
    leurs plats suggérés et le premier soir libre. À vérifier d'abord, puis par date."""
    par_id = {p["id"]: p for p in plats}
    signales = [(p, etat(p["jusqu_au"], aujourd_hui)) for p in produits]
    signales = [(p, e) for p, e in signales if e]
    cles = [p["cle"] for p, _ in signales]
    resultat = []
    for p, e in signales:
        if e == "a-verifier":
            resultat.append({**p, "etat": e, "trop_tard": None, "suggestions": [], "jour": None})
            continue
        couvert, trop_tard = couverture(p["cle"], p["jusqu_au"], repas, par_id, aujourd_hui)
        if not couvert:
            resultat.append({**p, "etat": e, "trop_tard": trop_tard,
                             "suggestions": suggestions(p["cle"], cles, plats, stock),
                             "jour": jour_libre(repas, aujourd_hui, p["jusqu_au"])})
    return sorted(resultat, key=lambda a: (a["etat"] != "a-verifier", a["jusqu_au"], a["nom"]))


def plats_qui_utilisent(plats, cles):
    """Les ids des plats qui utilisent au moins un de ces produits (badge « à finir » de la page Dîners)."""
    return [p["id"] for p in plats if any(utilise(p, c) for c in cles)]
