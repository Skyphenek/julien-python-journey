"""Casa Binomerie — Dîners : le carnet de recettes, la semaine, le secours et le compteur Deliveroo.

- plats : les recettes ; `statut` 'carnet' = connue, 'a-tester' = nouvelle (badge), passe à 'carnet' quand un
  repas où on l'a prévue est marqué « fait maison » (db.enregistrer_repas).
- repas : un dîner par jour, un déjeuner ou un brunch à la demande — plusieurs plats, et ce qui s'est vraiment
  passé (fait, commandé, dehors, autre). Le dîner est la mesure du succès : ≤ 1 commande par semaine
  (départ : 3, le 28/10/2026).
- Secours : les plats ≤ SECOURS_MINUTES dont tout est au placard ; « presque » : il en manque 1 ou 2.
Les noms d'ingrédients se comparent normalisés, comme les courses (courses.normaliser).
"""
import re
from datetime import date, timedelta

from courses import normaliser, STYLE_COURSES
from design import STYLE_D, STYLE_NAV_HUB, TETE_POLICE, nav_hub, onglets_cucina, ICONES_REPERE
from pwa import TETE_PWA, SCRIPT_FILE

_ID = re.compile(r"[A-Za-z0-9-]{8,64}")

GENRES = [("plat", "Plats"), ("accompagnement", "Accompagnements"), ("entree", "Entrées"), ("dessert", "Desserts")]
STATUTS = ("carnet", "a-tester")
POUR = [("nous", "Nous deux"), ("julien", "Julien"), ("laetitia", "Laetitia")]
ISSUES = [("fait", "Fait maison"), ("commande", "Commandé"), ("dehors", "Dehors"), ("autre", "Autre")]
MOMENTS = [("diner", "Dîner"), ("dejeuner", "Déjeuner"), ("brunch", "Brunch")]
ORDRE_GENRES = ("entree", "plat", "accompagnement", "dessert")
MAX_PLATS = 8
MAX_ACCORDS = 6
SECOURS_MINUTES = 20
FENETRE_PASSE = 42           # jours de repas lus : les 6 semaines du compteur
FENETRE_FUTUR = 30           # jusqu'où on peut planifier


# --- Validation : tout ce qui vient du téléphone est vérifié ----------------------------------

def _texte(corps, cle, maximum):
    valeur = corps.get(cle) or ""
    if not isinstance(valeur, str):
        raise ValueError(f"{cle} invalide")
    valeur = valeur.strip()
    if len(valeur) > maximum:
        raise ValueError(f"{cle} trop long")
    return valeur


def valider_plat(corps):
    """Une recette du carnet (ou à tester). Ingrédients : noms seuls, sans vides ni doublons."""
    if not isinstance(corps, dict):
        raise ValueError("recette invalide")
    identifiant = corps.get("id")
    if not isinstance(identifiant, str) or not _ID.fullmatch(identifiant):
        raise ValueError("id invalide")
    p = {"id": identifiant, "nom": _texte(corps, "nom", 80)}
    if not p["nom"]:
        raise ValueError("nom manquant")
    if corps.get("genre") not in dict(GENRES):
        raise ValueError("genre invalide")
    p["genre"] = corps["genre"]
    minutes = corps.get("minutes")
    if isinstance(minutes, bool) or not isinstance(minutes, int) or not 1 <= minutes <= 600:
        raise ValueError("minutes invalides (1 à 600)")
    p["minutes"] = minutes
    ingredients = corps.get("ingredients", [])
    if not isinstance(ingredients, list) or len(ingredients) > 40:
        raise ValueError("ingrédients invalides")
    vus, liste = set(), []
    for i in ingredients:
        if not isinstance(i, str) or len(i.strip()) > 60:
            raise ValueError("ingrédient invalide")
        if i.strip() and normaliser(i) not in vus:
            vus.add(normaliser(i))
            liste.append(i.strip())
    p["ingredients"] = liste
    p["recette"] = _texte(corps, "recette", 20000)
    p["lien"] = _texte(corps, "lien", 500)
    if p["lien"] and not re.match(r"https?://", p["lien"]):
        raise ValueError("lien invalide (http ou https)")
    p["note"] = _texte(corps, "note", 500)
    if corps.get("statut", "carnet") not in STATUTS:
        raise ValueError("statut invalide")
    p["statut"] = corps.get("statut", "carnet")
    if corps.get("pour", "nous") not in dict(POUR):
        raise ValueError("pour invalide")
    p["pour"] = corps.get("pour", "nous")
    archive = corps.get("archive", False)
    if not isinstance(archive, bool):
        raise ValueError("archive invalide")
    p["archive"] = archive
    accords = corps.get("accords")            # absent (page d'avant les accords) : None, ceux en base restent
    if accords is not None:
        if (not isinstance(accords, list) or len(accords) > MAX_ACCORDS
                or not all(isinstance(i, str) and _ID.fullmatch(i) for i in accords)):
            raise ValueError("accords invalides")
        if len(set(accords)) != len(accords) or identifiant in accords:
            raise ValueError("accord en double")
        if p["genre"] != "plat":
            accords = []
    p["accords"] = accords
    return p


def nettoyer_accords(accords, par_id):
    """Les accords qui tiennent : des accompagnements connus et non archivés, dans l'ordre donné."""
    return [i for i in accords
            if i in par_id and par_id[i]["genre"] == "accompagnement" and not par_id[i]["archive"]]


def valider_repas(corps, aujourd_hui):
    """Un repas : {jour, moment, plats (0 à 8 ids sans doublon), issue (ou None)} ; de -60 à +30 jours."""
    if not isinstance(corps, dict):
        raise ValueError("repas invalide")
    try:
        jour = date.fromisoformat(corps.get("jour"))
    except (TypeError, ValueError):
        raise ValueError("jour invalide") from None
    if not -60 <= (jour - aujourd_hui).days <= FENETRE_FUTUR:
        raise ValueError("jour hors limites")
    if not isinstance(corps.get("moment"), str) or corps["moment"] not in dict(MOMENTS):
        raise ValueError("moment invalide")
    plats = corps.get("plats") or []
    if (not isinstance(plats, list) or len(plats) > MAX_PLATS
            or not all(isinstance(i, str) and _ID.fullmatch(i) for i in plats)):
        raise ValueError("plats invalides")
    if len(set(plats)) != len(plats):
        raise ValueError("plat en double")
    issue = corps.get("issue") or None
    if issue is not None and (not isinstance(issue, str) or issue not in dict(ISSUES)):
        raise ValueError("issue invalide")
    return {"jour": jour, "moment": corps["moment"], "plats": plats, "issue": issue}


def ranger(plats, moment):
    """Les plats d'un repas dans l'ordre du service ; au brunch, dans l'ordre d'ajout."""
    if moment == "brunch":
        return list(plats)
    return sorted(plats, key=lambda p: ORDRE_GENRES.index(p["genre"]))


# --- Logique ----------------------------------------------------------------------------------

def semaine(aujourd_hui):
    """Les 7 soirs à planifier : aujourd'hui et les 6 suivants."""
    return [aujourd_hui + timedelta(days=i) for i in range(7)]


FRAIS_JOURS = 3             # acheté il y a moins de 3 jours (aujourd'hui compris) : on l'a encore


def avec_achats_recents(courses, noms):
    """Les articles de la liste, plus ce qu'on vient d'acheter (journal des achats, FRAIS_JOURS) : compté comme un
    habituel rangé, donc disponible, même si le panier a été vidé."""
    return list(courses) + [{"nom": n, "recurrent": True, "actif": False, "pris": False} for n in noms]


def disponibles(placard, courses=()):
    """Les clés de ce qu'on a : le placard en stock (bientôt fini compris) et le frais habituel rangé
    ou déjà dans le panier (un habituel sur la liste à prendre, c'est qu'il en manque). Tout ce qui est sur la liste
    à prendre manque, même si le placard le croit en stock (un frais acheté, puis à racheter)."""
    manque = {normaliser(a["nom"]) for a in courses if a["actif"] and not a["pris"]}
    return ({p["cle"] for p in placard if p["en_stock"]} - manque
            | {normaliser(a["nom"]) for a in courses if a["recurrent"] and (not a["actif"] or a["pris"])})


def secours(plats, placard, courses=(), a_finir=()):
    """(faisables, presque) : plats du carnet ≤ SECOURS_MINUTES, tout disponible / 1-2 manquants. `a_finir` : les
    clés des produits à finir (a_finir.py) ; les plats qui en utilisent passent en tête."""
    stock = disponibles(placard, courses)
    faisables, presque = [], []
    candidats = sorted((p for p in plats if p["genre"] == "plat" and p["statut"] == "carnet" and not p["archive"]
                        and p["minutes"] <= SECOURS_MINUTES and p["ingredients"]),
                       key=lambda p: (not any(normaliser(i) in a_finir for i in p["ingredients"]), p["minutes"], p["nom"]))
    for p in candidats:
        manquants = [i for i in p["ingredients"] if normaliser(i) not in stock]
        if not manquants:
            faisables.append(p)
        elif len(manquants) <= 2:
            presque.append({"plat": p, "manquants": manquants})
    return faisables, presque


def a_acheter(plats_prevus, placard, courses):
    """[(ingrédient, id du plat)] à ajouter aux courses : ni au placard, ni déjà sur la liste."""
    deja = disponibles(placard, courses) | {normaliser(a["nom"]) for a in courses if a["actif"] and not a["pris"]}
    resultat = []
    for p in plats_prevus:
        for i in p["ingredients"]:
            if normaliser(i) not in deja:
                deja.add(normaliser(i))
                resultat.append((i, p["id"]))
    return resultat


def a_acheter_aujourd_hui(plats_du_jour, placard, courses):
    """Les ingrédients des repas du jour qu'on n'a pas (ni au placard, ni en habituel rangé), sur la liste ou
    non : ce qu'il faut acheter avant de cuisiner (page Aujourd'hui)."""
    stock, vus, noms = disponibles(placard, courses), set(), []
    for p in plats_du_jour:
        for i in p["ingredients"]:
            if normaliser(i) not in stock and normaliser(i) not in vus:
                vus.add(normaliser(i))
                noms.append(i)
    return noms


def repas_prevus(repas, par_id, jours):
    """Les repas encore à venir des `jours` (sans issue) : pour chacun, ses plats connus ; les vides sont omis."""
    prevus = []
    for r in repas:
        if r["jour"] in jours and not r["issue"]:
            plats = [par_id[i] for i in r["plats"] if i in par_id]
            if plats:
                prevus.append(plats)
    return prevus


CIBLE_SOIRS = 4             # soirs prévus par semaine : les autres restent libres
MINUTES_SEMAINE = 45        # du lundi au jeudi, on cuisine vite
RECENT = 14                 # un plat mangé il y a moins de 14 jours ne revient pas


def tel_que_propose(plats_du_diner, par_id):
    """Un dîner tel que Proposer le pose : vide, un plat, ou un plat et un de ses accords. « Reproposer » peut le
    changer ; un dîner composé à la main, jamais."""
    if len(plats_du_diner) <= 1:
        return True
    principal = par_id.get(plats_du_diner[0])
    return len(plats_du_diner) == 2 and principal is not None and plats_du_diner[1] in (principal.get("accords") or [])


def accompagner(choix, plats, repas, jours, hasard=None):
    """{jour: [plat] ou [plat, accompagnement]} : à chaque plat proposé (`choix`, voir proposer), un de ses accords
    au hasard — accompagnement non archivé, pour nous deux, ni déjà au menu de la semaine (tous moments, hors les
    jours qu'on propose de nouveau : seul leur dîner est libéré), ni déjà donné à un autre jour ; avec recette, et
    rapide (≤ 45 min) du lundi au jeudi comme le plat. Sans accord possible : le plat seul."""
    from random import Random
    hasard = hasard or Random()
    par_id = {p["id"]: p for p in plats}
    pris = {i for r in repas
            if r["jour"] in jours and not (r["jour"] in choix and r["moment"] == "diner") for i in r["plats"]}
    menus = {}
    for j, id_plat in sorted(choix.items()):
        possibles = [a for a in par_id[id_plat].get("accords") or []
                     if a in par_id and par_id[a]["genre"] == "accompagnement" and not par_id[a]["archive"]
                     and par_id[a].get("pour", "nous") == "nous" and a not in pris
                     and par_id[a]["recette"] and (j.weekday() >= 4 or par_id[a]["minutes"] <= MINUTES_SEMAINE)]
        if possibles:
            a = hasard.choice(possibles)
            pris.add(a)
            menus[j] = [id_plat, a]
        else:
            menus[j] = [id_plat]
    return menus


def proposer(plats, repas, jours, aujourd_hui, remplacer=(), cible=CIBLE_SOIRS, hasard=None, a_finir=()):
    """{jour: id du plat} pour compléter la semaine jusqu'à `cible` dîners prévus.

    Dîners libres seulement (ni plat ni issue), vendredi et samedi en dernier recours (souvent dehors), répartis
    dans la semaine. Plats pour nous deux, avec recette ; rapides (≤ 45 min) du lundi au jeudi ; ni déjà prévus
    (tous moments), ni mangés ces 14 derniers jours, ni brunchs ; un plat à tester s'il n'y en a pas déjà un. `remplacer` :
    des jours à tirer au sort de nouveau, avec un autre plat (s'ils sont encore tels que proposés). `a_finir` :
    [(clé, à finir avant)] des produits qu'aucun repas prévu n'utilise à temps (a_finir.alertes) — pour chacun, d'abord,
    le plus rapide des plats du carnet qui l'utilisent, au premier soir à remplir avant sa date (avec Reproposer,
    seulement sur les jours à remplacer). L'accompagnement : voir accompagner. Déjeuners et brunchs ne remplissent
    pas un soir."""
    from random import Random
    hasard = hasard or Random()
    diners = {r["jour"]: r for r in repas if r["moment"] == "diner"}
    par_id = {p["id"]: p for p in plats}
    remplacer = [j for j in remplacer if j in jours                          # ni composé à la main, ni déjà vécu
                 and not (j in diners and (diners[j]["issue"] or not tel_que_propose(diners[j]["plats"], par_id)))]
    prevus = {j: diners[j]["plats"] for j in jours if j in diners and diners[j]["plats"] and j not in remplacer}
    besoin = max(0, cible - len(prevus))
    libres = [j for j in jours if j not in prevus and j not in remplacer
              and not (j in diners and diners[j]["issue"])]

    manges = {i for r in repas if r["issue"] == "fait" and 0 <= (aujourd_hui - r["jour"]).days < RECENT
              for i in r["plats"]}
    deja = {i for r in repas if r["jour"] in jours and r["jour"] not in remplacer for i in r["plats"]}
    exclus = deja | manges | {i for j in remplacer if j in diners for i in diners[j]["plats"]}
    candidats = [p for p in plats if p["genre"] == "plat" and not p["archive"] and p.get("pour", "nous") == "nous"
                 and p["recette"] and p["id"] not in exclus and not p["id"].startswith("brunch-")]
    hasard.shuffle(candidats)
    a_tester = any(p["statut"] == "a-tester" and p["genre"] == "plat" for p in plats if p["id"] in deja)

    choix = {}
    possibles = sorted(remplacer[:besoin]) if remplacer else libres         # anti-gaspi : où poser un plat à finir
    for cle, jusqu_au in sorted(a_finir, key=lambda x: (x[1], x[0])):
        if len(choix) >= besoin:
            break
        for j in possibles:
            if j > jusqu_au or j in choix:
                continue
            p = next((p for p in sorted(candidats, key=lambda p: (p["minutes"], p["nom"]))
                      if p["statut"] == "carnet" and p["id"] not in choix.values()
                      and any(normaliser(i) == cle for i in p["ingredients"])
                      and not (j.weekday() < 4 and p["minutes"] > MINUTES_SEMAINE)), None)
            if p:
                choix[j] = p["id"]
                break

    restant = besoin - len(choix)
    a_remplir = [j for j in remplacer if j not in choix][:restant]
    reste = restant - len(a_remplir)
    preferes = [j for j in libres if j.weekday() not in (4, 5) and j not in choix]
    autres = [j for j in libres if j.weekday() in (4, 5) and j not in choix]
    if reste > 0:
        if len(preferes) > reste:                       # répartis : au milieu de chaque tranche, pas d'affilée
            a_remplir += [preferes[(2 * i + 1) * len(preferes) // (2 * reste)] for i in range(reste)]
        else:
            a_remplir += preferes + autres[:reste - len(preferes)]
    if not a_remplir and not choix:
        return {}

    for j in sorted(a_remplir, key=lambda j: j.weekday() != 6):     # le plat à tester, le dimanche s'il y en a un
        rapide = j.weekday() < 4
        ordre = sorted(candidats, key=lambda p: (p["statut"] == "a-tester") == a_tester)
        for p in ordre:
            if p["id"] in choix.values() or (rapide and p["minutes"] > MINUTES_SEMAINE):
                continue
            choix[j] = p["id"]
            a_tester = a_tester or p["statut"] == "a-tester"
            break
    return dict(sorted(choix.items()))


MINUTES_MIDI = 30           # à midi, tous les jours, on cuisine vite


def proposer_cases(plats, repas, cases, aujourd_hui, remplacer=(), hasard=None, a_finir=()):
    """{(jour, moment): id du plat} pour remplir exactement les `cases` cochées, dîners et déjeuners.

    Une case est libre si aucun repas de ce jour et de ce moment n'a de plat ni d'issue (à midi, un brunch du même
    jour l'occupe aussi) ; les jours passés sont ignorés. `remplacer` : des cases à tirer de nouveau, même absentes
    de `cases` (si le repas est encore tel que proposé, sans issue). Plats pour nous deux, avec recette ; ≤ 30 min à
    midi, ≤ 45 min le soir du lundi au jeudi ; ni déjà prévus dans les 7 jours (hors cases remplacées), ni mangés ces
    14 derniers jours, ni brunchs, sans doublon ; un plat à tester au plus sur ces 7 jours. `a_finir` : [(clé, à finir
    avant)] — pour chacun, d'abord le plus rapide des plats du carnet qui l'utilisent, sur la première case libre
    avant sa date. Le dimanche d'abord, puis par jour (déjeuner avant dîner). Sans plat possible, la case reste vide."""
    from random import Random
    hasard = hasard or Random()
    par_id = {p["id"]: p for p in plats}
    remplacer = set(remplacer)
    ordre = lambda c: (c[0], c[1] != "dejeuner")                            # par jour, déjeuner avant dîner
    fin = aujourd_hui + timedelta(days=6)                                   # la fenêtre : comme semaine()

    def repas_de(jour, moment):
        return [r for r in repas if r["jour"] == jour and (r["moment"] == moment
                or (moment == "dejeuner" and r["moment"] == "brunch"))]

    def libre(case):
        jour, moment = case
        if jour < aujourd_hui or jour > fin:                                # hors de la fenêtre de 7 jours
            return False
        occupes = [r for r in repas_de(jour, moment) if r["plats"] or r["issue"]]
        if not occupes:
            return True
        return (case in remplacer and all(r["moment"] == moment and not r["issue"]
                                          and tel_que_propose(r["plats"], par_id) for r in occupes))

    a_remplir = sorted({c for c in set(cases) | remplacer if libre(c)}, key=ordre)
    if not a_remplir:
        return {}

    manges = {i for r in repas if r["issue"] == "fait" and 0 <= (aujourd_hui - r["jour"]).days < RECENT
              for i in r["plats"]}
    liberees = {c for c in a_remplir if c in remplacer}
    posees = [r for r in repas if aujourd_hui <= r["jour"] <= fin and (r["jour"], r["moment"]) not in liberees]
    deja = {i for r in posees for i in r["plats"]}
    ecartes = {i for c in liberees for r in repas_de(*c) for i in r["plats"]}
    candidats = [p for p in plats if p["genre"] == "plat" and not p["archive"] and p.get("pour", "nous") == "nous"
                 and p["recette"] and p["id"] not in deja | manges | ecartes and not p["id"].startswith("brunch-")]
    hasard.shuffle(candidats)
    a_tester = any(i in par_id and par_id[i]["statut"] == "a-tester" and par_id[i]["genre"] == "plat" for i in deja)
    carnet = sorted(candidats, key=lambda p: (p["minutes"], p["nom"]))

    def assez_rapide(p, case):
        jour, moment = case
        if moment == "dejeuner":
            return p["minutes"] <= MINUTES_MIDI
        return jour.weekday() >= 4 or p["minutes"] <= MINUTES_SEMAINE

    choix = {}
    for cle, jusqu_au in sorted(a_finir, key=lambda x: (x[1], x[0])):       # anti-gaspi
        for case in a_remplir:
            if case[0] > jusqu_au:
                break
            if case in choix:
                continue
            p = next((p for p in carnet
                      if p["statut"] == "carnet" and p["id"] not in choix.values() and assez_rapide(p, case)
                      and any(normaliser(i) == cle for i in p["ingredients"])), None)
            if p:
                choix[case] = p["id"]
                break

    for case in sorted((c for c in a_remplir if c not in choix), key=lambda c: c[0].weekday() != 6):
        for p in sorted(candidats, key=lambda p: (p["statut"] == "a-tester") == a_tester):
            if p["id"] in choix.values() or not assez_rapide(p, case):
                continue
            if p["statut"] == "a-tester" and a_tester:
                continue
            choix[case] = p["id"]
            a_tester = a_tester or p["statut"] == "a-tester"
            break
    return dict(sorted(choix.items(), key=lambda kv: ordre(kv[0])))


LIVRAISON_DEUX = 35         # un Deliveroo pour deux, frais compris : l'ordre de grandeur à Paris


def cout_semaine(prevus, placard, courses):
    """Les repas prévus ([[plat, …], …], voir repas_prevus) : leur coût estimé (somme des prix_paris.cout_repas
    de leurs plats), les courses qui restent à faire pour eux (prix entier des produits ni au placard ni sur la
    liste) et le même nombre de repas en livraison."""
    from prix_paris import cout_repas, prix_de
    plats = [p for r in prevus for p in r]
    a_acheter_ = [nom for nom, _ in a_acheter(plats, placard, courses)]
    return {"nb_repas": len(prevus), "cout": round(sum(cout_repas(p["ingredients"], p["recette"]) for p in plats), 2),
            "a_acheter": a_acheter_,
            "courses": round(sum(prix_de(n)[1] for n in a_acheter_ if prix_de(n)), 2),
            "livraison": len(prevus) * LIVRAISON_DEUX}


def compteur(repas, aujourd_hui):
    """Commandes des 7 derniers jours, moyenne hebdomadaire sur 6 semaines, dîners renseignés (dîners seuls)."""
    recents = [r for r in repas if r["moment"] == "diner" and r["issue"]
               and 0 <= (aujourd_hui - r["jour"]).days < FENETRE_PASSE]
    commandes = [r for r in recents if r["issue"] == "commande"]
    return {"semaine": sum(1 for r in commandes if (aujourd_hui - r["jour"]).days < 7),
            "moyenne": len(commandes) / 6 if recents else 0,
            "renseignes": len(recents)}


SEMAINES_JOURNAL = 8        # semaines passées rendues par page du journal


def journal(repas, plats, aujourd_hui, avant=None, n=SEMAINES_JOURNAL):
    """Les `n` semaines calendaires qui précèdent `avant` (un lundi, exclu ; par défaut le lundi qui suit la
    semaine en cours), de la plus récente à la plus ancienne, sans dépasser la semaine du plus ancien repas.
    Chaque semaine : bilan des issues (soirs et midis), coût des repas faits maison, et ses jours passés
    (strictement avant aujourd'hui) avec le soir et le midi (déjeuner, sinon brunch). `suite` : le lundi à
    passer en `avant` pour la page suivante, None s'il n'y a pas de repas plus ancien."""
    from prix_paris import cout_repas
    par_id = {p["id"]: p for p in plats}
    par_case = {(r["jour"], r["moment"]): r for r in repas}
    if avant is None:
        avant = aujourd_hui - timedelta(days=aujourd_hui.weekday()) + timedelta(days=7)
    if not repas:
        return {"semaines": [], "suite": None}
    plus_ancien = min(r["jour"] for r in repas)
    premier = plus_ancien - timedelta(days=plus_ancien.weekday())

    def ligne(jour, moment):
        r = par_case.get((jour, moment))
        if r is None:
            return None
        trouves = [par_id[i] for i in r["plats"] if i in par_id]
        return {"plats": [{"id": p["id"], "nom": p["nom"]} for p in ranger(trouves, moment)],
                "issue": r["issue"], "non_note": bool(trouves) and r["issue"] is None}, trouves

    semaines, lundi_ = [], avant - timedelta(days=7)
    while len(semaines) < n and lundi_ >= premier:
        bilan = {"fait": 0, "commande": 0, "dehors": 0, "autre": 0, "non_note": 0}
        cout, jours = 0.0, []
        for i in range(7):
            jour = lundi_ + timedelta(days=i)
            if jour >= aujourd_hui:
                break
            lignes = {}
            for cle, moments in (("soir", ("diner",)), ("midi", ("dejeuner", "brunch"))):
                lignes[cle] = None
                for m in moments:
                    trouve = ligne(jour, m)
                    if trouve:
                        lignes[cle] = trouve
                        break
            for cle in ("soir", "midi"):
                if lignes[cle] is None:
                    continue
                l, trouves = lignes[cle]
                if l["issue"]:
                    bilan[l["issue"]] += 1
                elif l["non_note"]:
                    bilan["non_note"] += 1
                if l["issue"] == "fait":
                    cout += sum(cout_repas(p["ingredients"], p.get("recette", "")) for p in trouves)
            soir = lignes["soir"][0] if lignes["soir"] else {"plats": [], "issue": None, "non_note": False}
            jours.append({"jour": jour, "soir": soir, "midi": lignes["midi"][0] if lignes["midi"] else None})
        semaines.append({"lundi": lundi_, "bilan": bilan, "cout_maison": round(cout, 2), "jours": jours})
        lundi_ -= timedelta(days=7)
    suite = semaines[-1]["lundi"] if semaines and semaines[-1]["lundi"] > premier else None
    return {"semaines": semaines, "suite": suite}


# --- Page ---------------------------------------------------------------------------------------

STYLE_DINERS = """
body.diners { --rubrique: var(--diners); --rubrique-doux: var(--diners-doux); }
nav.vues { display: grid; grid-template-columns: repeat(2, 1fr); gap: 4px; background: var(--carte); border-radius: 18px;
           padding: 4px; margin: 0 0 18px; position: sticky; top: 0; z-index: 5; }
nav.vues button { border: none; background: none; border-radius: 14px; padding: 10px 4px; font-family: inherit; font-weight: 700;
                  font-size: 14px; color: var(--doux); }
nav.vues button.actif { background: var(--fond); color: var(--diners); box-shadow: 0 1px 3px rgba(0,0,0,.08); }
div.vue { display: flex; flex-direction: column; gap: 12px; }
div.plat-soir { background: #c2410c; color: #ffffff; border-radius: 28px; padding: 22px; display: flex; flex-direction: column; gap: 6px; }
div.plat-soir .titre { font-size: 15px; opacity: .85; }
div.plat-soir .nom { font-size: 30px; font-weight: 800; line-height: 1.05; letter-spacing: -0.02em; }
div.plat-soir .boutons { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 8px; }
div.plat-soir button { border: none; border-radius: 999px; padding: 10px 16px; font-family: inherit; font-weight: 800;
                       background: #ffffff; color: #8a2c06; font-size: 15px; }
div.plat-soir button.discret { background: rgba(255,255,255,.18); color: #ffffff; }
div.encart { background: var(--carte); border-radius: 24px; padding: 16px 18px; display: flex; flex-direction: column; gap: 8px; }
div.encart h2 { font-size: 18px; font-weight: 800; margin: 0; }
div.encart p.aide { color: var(--doux); font-size: 14px; margin: 0; }
ul.plats { list-style: none; margin: 0; padding: 0; }
ul.plats li { display: flex; align-items: center; gap: 10px; min-height: 52px; border-top: 1px solid var(--ligne); }
ul.plats li:first-child { border-top: none; }
ul.plats li > button.ouvrir { flex: 1; min-width: 0; text-align: left; background: none; border: none; padding: 10px 0;
                              font-family: inherit; color: var(--texte); display: flex; flex-direction: column; gap: 2px; }
ul.plats .nom { font-size: 17px; font-weight: 700; }
ul.plats .meta { font-size: 13px; color: var(--doux); }
ul.plats .meta .manque { color: var(--diners); font-weight: 700; }
button.petit { border: 2px solid var(--ligne); background: var(--blanc); color: var(--texte); border-radius: 999px;
               padding: 8px 12px; font-family: inherit; font-weight: 700; font-size: 13px; white-space: nowrap; }
button.plein { border: none; background: var(--diners); color: #ffffff; border-radius: 999px; padding: 12px 18px;
               font-family: inherit; font-weight: 800; font-size: 15px; }
span.badge { font-size: 11px; font-weight: 800; letter-spacing: .04em; text-transform: uppercase; color: var(--diners);
             background: var(--diners-doux); border-radius: 999px; padding: 2px 8px; margin-left: 6px; }
span.repere { margin-left: 6px; font-size: 14px; line-height: 1; white-space: nowrap; }
span.repere.nouvelle { color: var(--dore); font-size: 16px; }
span.repere.points { color: var(--diners); font-size: 10px; letter-spacing: 1px; vertical-align: 2px; }
span.repere.qui { color: var(--doux); font-size: 16px; }
p.legende-reperes { font-size: 12px; color: var(--doux); margin: 10px 4px 0; line-height: 1.5; }
input.recherche { width: 100%; font-family: inherit; font-size: 17px; padding: 12px 16px; border-radius: 999px;
                  border: 2px solid var(--ligne); background: var(--blanc); color: var(--texte); }
div.filtres { display: flex; gap: 6px; flex-wrap: wrap; }
div.filtres button { border: 2px solid var(--ligne); background: var(--blanc); color: var(--texte); border-radius: 999px;
                     padding: 6px 12px; font-family: inherit; font-weight: 700; font-size: 14px; }
div.filtres button.actif { background: var(--diners); border-color: var(--diners); color: #ffffff; }
div.plat-soir .cout { font-size: 15px; font-weight: 700; opacity: .95; }
div.compteur-diners { display: flex; justify-content: space-between; align-items: baseline; gap: 10px; flex-wrap: wrap;
                      background: var(--carte); border-radius: 18px; padding: 12px 16px; font-size: 14px; color: var(--doux); }
div.compteur-diners strong { font-size: 16px; color: var(--texte); }
div.compteur-diners.trop strong { color: var(--diners); }
div.bilan-semaine { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 8px; }
div.bilan-semaine div { background: var(--carte); border-radius: 18px; padding: 12px; display: flex; flex-direction: column; gap: 2px; }
div.bilan-semaine strong { font-size: 20px; font-weight: 800; }
div.bilan-semaine span { font-size: 12px; color: var(--doux); font-weight: 600; }
div.bilan-semaine .livraison strong { color: var(--doux); text-decoration: line-through; }
section.groupe-ing h3 { font-size: 13px; font-weight: 800; color: var(--doux); text-transform: uppercase; letter-spacing: .05em;
                        margin: 4px 0 6px; }
div.ingredients span.ok::before { content: "✓ "; color: var(--courses); font-weight: 800; }
div.ingredients span.liste { background: var(--courses-doux); color: var(--courses); }
div.ingredients span small { opacity: .75; margin-left: 4px; }
div.filtres.etiquettes button span { font-weight: 600; opacity: .7; margin-left: 4px; }
div.filtres.etiquettes { flex-wrap: nowrap; overflow-x: auto; scrollbar-width: none; margin: 0 -20px; padding: 0 20px; }
div.filtres.etiquettes::-webkit-scrollbar { display: none; }
div.filtres.etiquettes button { flex: 0 0 auto; border-width: 1.5px; background: transparent; font-weight: 600; font-size: 13px;
                                padding: 5px 11px; }
div.filtres.etiquettes button.actif { background: var(--diners); border-color: var(--diners); color: #ffffff; }
div.filtres.etiquettes button span { font-size: 11px; opacity: .6; }
div.segments { display: grid; grid-auto-flow: column; grid-auto-columns: 1fr; gap: 2px; background: var(--carte);
               border-radius: 14px; padding: 3px; }
div.segments button { border: none; background: none; border-radius: 11px; padding: 7px 2px; font-family: inherit;
                      font-weight: 700; font-size: 13px; color: var(--doux); white-space: nowrap; }
div.segments button.actif { background: var(--fond); color: var(--diners); box-shadow: 0 1px 3px rgba(0,0,0,.08); }
div.jour-repas { display: flex; flex-direction: column; gap: 8px; padding: 12px 0; border-top: 1px solid var(--ligne); }
div.jour-repas:first-of-type { border-top: none; }
div.jour-repas .quand { font-weight: 800; font-size: 15px; }
div.jour-repas .quand small { font-weight: 600; color: var(--doux); font-size: 12px; margin-left: 6px; }
div.repas { background: var(--blanc); border: 2px solid var(--ligne); border-radius: 18px; padding: 10px 12px;
            display: flex; flex-direction: column; gap: 6px; }
div.repas .titre-repas { font-size: 13px; font-weight: 800; color: var(--doux); text-transform: uppercase; letter-spacing: .05em; }
ul.plats-repas { list-style: none; margin: 0; padding: 0; }
ul.plats-repas li { display: flex; align-items: center; gap: 8px; min-height: 44px; }
ul.plats-repas li > button.ouvrir { flex: 1; min-width: 0; text-align: left; background: none; border: none; padding: 4px 0;
                                   font-family: inherit; color: var(--texte); display: flex; flex-direction: column; }
ul.plats-repas .nom { font-size: 16px; font-weight: 700; }
ul.plats-repas .meta, ul.plats-repas li.meta { font-size: 13px; color: var(--doux); }
button.retirer { border: none; background: var(--carte); color: var(--doux); border-radius: 999px; width: 44px; height: 44px;
                 font-size: 18px; font-weight: 800; flex: none; }
div.ajouts { display: flex; gap: 6px; flex-wrap: wrap; }
div.ajouts button.petit { padding: 6px 10px; }
button.petit.danger { border-color: var(--diners); color: var(--diners); font-weight: 800; }   /* Oui, vider : on voit ce qu'on confirme */
ul.plats-repas li.avec { flex-wrap: wrap; gap: 6px; min-height: 0; padding: 0 0 6px; }
ul.plats-repas li.avec button.petit { padding: 6px 10px; }
section.accords div.ingredients { margin-bottom: 8px; }
ul.plats-soir { list-style: none; margin: 4px 0 0; padding: 0; display: flex; flex-direction: column; gap: 6px; }
ul.plats-soir li { display: flex; justify-content: space-between; align-items: center; gap: 8px; font-size: 15px; font-weight: 600; }
ul.plats-soir button { padding: 6px 12px !important; font-size: 13px !important; }
div.proposer { display: flex; gap: 8px; flex-wrap: wrap; }
div.proposer button.plein { flex: 1 1 220px; }
div.grille-proposer { background: var(--carte); border: 1px solid var(--ligne); border-radius: 12px; padding: 6px; margin: 8px 0; }
div.grille-proposer .rang { display: grid; grid-template-columns: 2.2rem repeat(7, minmax(0, 1fr)); gap: 3px; margin-bottom: 3px; align-items: center; }
div.grille-proposer .rang > span { text-align: center; font-size: .75rem; color: var(--doux); line-height: 1.15; }
div.grille-proposer .rang > span.etiq { text-align: left; font-weight: 600; color: var(--texte); }
div.grille-proposer button.case { min-height: 44px; min-width: 0; padding: 0; border-radius: 8px; border: 1px solid var(--ligne);
    background: var(--fond); color: var(--doux); font-size: .7rem; }
div.grille-proposer button.case[aria-pressed="true"] { background: var(--diners); border-color: var(--diners); color: var(--fond); font-weight: 700; }
div.grille-proposer button.case:disabled { opacity: .55; }
div.grille-proposer .decompte { margin: 8px 0; font-size: .9rem; }
div.grille-proposer .actions { display: flex; gap: 8px; flex-wrap: wrap; }
div.grille-proposer .actions button.plein { flex: 1 1 140px; }
p.message { color: var(--diners); font-weight: 700; font-size: 14px; margin: 0; min-height: 1.2em; }
/* Fiche recette et formulaire : un panneau plein écran */
div.panneau { position: fixed; inset: 0; z-index: 30; background: var(--fond); overflow-y: auto;
              padding: calc(16px + env(safe-area-inset-top, 0px)) max(16px, env(safe-area-inset-right, 0px))
                       calc(40px + env(safe-area-inset-bottom, 0px)) max(16px, env(safe-area-inset-left, 0px)); }
div.panneau .contenu { max-width: 720px; margin: 0 auto; display: flex; flex-direction: column; gap: 14px; }
div.panneau .haut { display: flex; justify-content: space-between; align-items: center; gap: 10px; }
div.panneau h2 { font-size: 32px; font-weight: 800; line-height: 1.05; letter-spacing: -0.02em; margin: 0; }
div.panneau .meta { color: var(--doux); font-weight: 600; }
div.panneau .meta a { color: var(--diners); }
div.ingredients { display: flex; flex-wrap: wrap; gap: 6px; }
div.ingredients span { border-radius: 999px; padding: 5px 12px; background: var(--carte); font-size: 15px; }
div.ingredients span.manque { background: var(--diners-doux); color: var(--diners); font-weight: 700; }
pre.recette { white-space: pre-wrap; font-family: inherit; font-size: 18px; line-height: 1.55; margin: 0;
              background: var(--carte); border-radius: 24px; padding: 18px; }
div.actions { display: flex; flex-wrap: wrap; gap: 8px; }
form.edition { display: flex; flex-direction: column; gap: 12px; }
form.edition label { display: flex; flex-direction: column; gap: 6px; font-weight: 700; font-size: 14px; }
form.edition input, form.edition select, form.edition textarea { font-family: inherit; font-size: 16px; padding: 12px 14px;
       border-radius: 14px; border: 2px solid var(--ligne); background: var(--blanc); color: var(--texte); width: 100%; }
form.edition textarea { min-height: 220px; resize: vertical; }
form.edition .deux { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
/* Fiche recette « magazine » (06/11/2026) */
div.une-fiche { background: var(--diners); color: #fff; border-radius: 28px; padding: 20px 18px; }
div.une-fiche .meta { color: rgba(255,255,255,.85); }
div.une-fiche h2 { font-size: 36px; color: #fff; margin: 4px 0 0; }
div.une-fiche .haut button { background: rgba(255,255,255,.2); color: #fff; }
div.une-fiche ul { list-style: none; margin: 14px 0 0; padding: 12px 0 0; border-top: 1px solid rgba(255,255,255,.35); }
div.une-fiche li { font-size: 16px; line-height: 1.45; margin: 6px 0; }
details.courses-fiche { background: var(--carte); border-radius: 18px; padding: 12px 16px; }
details.courses-fiche summary { font-weight: 800; cursor: pointer; }
details.courses-fiche[open] summary { margin-bottom: 10px; }
h3.titre-fiche { font-size: 13px; font-weight: 800; color: var(--doux); text-transform: uppercase; letter-spacing: .08em; margin: 18px 0 8px; }
ul.ing-fiche { list-style: none; padding: 0; margin: 0; columns: 2; column-gap: 18px; }
ul.ing-fiche li { break-inside: avoid; padding: 7px 0; border-bottom: 1px dashed var(--ligne); font-size: 15px; line-height: 1.35;
                  display: flex; gap: 8px; align-items: flex-start; }
ul.ing-fiche input { width: 20px; height: 20px; margin: 1px 0 0; accent-color: var(--courses); flex: none; }
ul.ing-fiche b { display: block; font-size: 16px; }
ul.ing-fiche li.coche { color: var(--doux); text-decoration: line-through; }
p.para-fiche { font-size: 16px; line-height: 1.5; margin: 6px 0; }
div.tempo-fiche { display: flex; gap: 8px; overflow-x: auto; padding-bottom: 6px; scroll-snap-type: x mandatory; }
div.tempo-fiche button { flex: none; width: 72%; max-width: 260px; text-align: left; border: none; background: var(--carte);
                         color: var(--texte); border-radius: 18px; padding: 12px 14px; scroll-snap-align: start;
                         font-family: inherit; font-size: 15px; line-height: 1.4; }
div.tempo-fiche b { display: block; font-family: 'DM Mono', ui-monospace, monospace; font-size: 22px; color: var(--diners); }
ol.etapes-fiche { list-style: none; padding: 0; margin: 0; }
ol.etapes-fiche > li { position: relative; padding: 16px 0 16px 54px; border-top: 1px solid var(--ligne); font-size: 17.5px;
                       line-height: 1.55; scroll-margin-top: 16px; transition: background .4s; border-radius: 12px; }
ol.etapes-fiche > li.vise { background: var(--diners-doux); }
ol.etapes-fiche span.num { position: absolute; left: 0; top: 10px; font-size: 42px; font-weight: 800; color: var(--diners);
                           line-height: 1; letter-spacing: -0.04em; }
ol.etapes-fiche strong { font-weight: 800; }
ol.etapes-fiche em { color: var(--doux); }
ol.etapes-fiche div.secret { margin-top: 10px; padding-left: 12px; border-left: 4px solid var(--or, #b7791f); font-size: 16px; }
ol.etapes-fiche div.secret b { color: var(--or, #b7791f); }
ol.etapes-fiche div.secret.mamma { border-color: var(--courses); }
ol.etapes-fiche div.secret.mamma b { color: var(--courses); }
ol.etapes-fiche ul { padding-left: 18px; margin: 8px 0 0; }
ol.etapes-fiche ul li { font-size: 16px; margin-top: 6px; }
"""

SCRIPT_DINERS = """
(function () {
    const GENRES = JSON.parse(document.getElementById('genres').textContent);
    const NOMS_GENRE = { plat: 'Plat', accompagnement: 'Accompagnement', entree: 'Entrée', dessert: 'Dessert' };
    const JOURS = ['dim.', 'lun.', 'mar.', 'mer.', 'jeu.', 'ven.', 'sam.'];
    const MOMENTS = { diner: 'Dîner', dejeuner: 'Déjeuner', brunch: 'Brunch' };
    const ORDRE_GENRES = ['entree', 'plat', 'accompagnement', 'dessert'];
    const AJOUTS = [['plat', '+ plat'], ['entree', '+ entrée'], ['accompagnement', '+ accompagnement'], ['dessert', '+ dessert']];
    const CLE_COPIE = 'diners:copie';
    let d = null;                                         // ce que renvoie api/diners
    const PAGE = document.body.dataset.page || 'diners';
    let vue = PAGE === 'recettes' ? 'recettes' : 'ce-soir', filtre = 'tout', recherche = '';
    const etiquette = { recettes: 'tout', choix: 'nous' };   // un filtre par liste ; un soir : à deux
    let derniereProposition = {};                         // {'<iso>|<moment>': 'plat accompagnement'} : ce que « Reproposer » peut changer
    let proposeEnCours = false;                           // une demande à Proposer est partie : on n'en lance pas une seconde
    let viderDemande = false;                             // « Vider la semaine » touché une fois : on attend la confirmation
    let messageSemaine = '';
    // La grille « Proposer ma semaine » : ouverte ou non, repas cochés (« <0-6>|<moment> », 0 = lundi) ; hors du rendu pour survivre à afficher()
    const CLE_GRILLE = 'diners:grille';
    const GRILLE_DEFAUT = ['0|diner', '1|diner', '2|diner', '3|diner'];
    let grilleOuverte = false, grille = null;
    const ETIQUETTES = [['tout', 'Tout'], ['nouvelles', 'Nouvelles'], ['rapide', 'Rapide'], ['nous', 'Nous deux'], ['julien', 'Julien'], ['laetitia', 'Laetitia'],
                        ['air-fryer', 'Air fryer'], ['poisson', 'Poisson'], ['legumes', 'Légumes'], ['brunch', 'Brunch']];
    // Brunch : les recettes « brunch- » et celles du carnet qui s'y prêtent
    const BRUNCH = ['plat-oeufs-brouilles', 'plat-oeuf-coque', 'plat-oeuf-cocotte', 'tester-pancakes', 'tester-shakshuka', 'mer-bagel-saumon'];
    const MER = ['saumon', 'thon', 'crevette', 'gambas', 'cabillaud', 'dorade', 'sole', 'sardine', 'moule', 'calamar',
                 'poulpe', 'saint-jacques', 'langoustine', 'morue', 'crabe', 'maquereau', 'lieu', 'colin'];
    let ouverte = null, verrou = null;                    // fiche ouverte, wake lock

    function el(balise, classe, texte) {
        const e = document.createElement(balise);
        if (classe) e.className = classe;
        if (texte !== undefined) e.textContent = texte;
        return e;
    }
    function bouton(texte, classe, action) { const b = el('button', classe, texte); b.type = 'button'; b.addEventListener('click', action); return b; }
    function nouvelId(prefixe) {
        const h = (window.crypto && crypto.randomUUID) ? crypto.randomUUID().slice(0, 13)
                                                         : Date.now().toString(36) + Math.random().toString(36).slice(2, 7);
        return prefixe + '-' + h;
    }
    function normaliser(nom) {
        return nom.trim().toLowerCase().replace(/œ/g, 'oe').replace(/æ/g, 'ae')
            .normalize('NFD').replace(/[\\u0300-\\u036f]/g, '').replace(/\\s+/g, ' ');
    }
    function duree(m) { if (m < 60) return m + ' min'; const h = Math.floor(m / 60), r = m % 60; return h + ' h' + (r ? ' ' + String(r).padStart(2, '0') : ''); }
    function enClair(iso) { const j = new Date(iso + 'T12:00:00'); return JOURS[j.getDay()] + ' ' + j.getDate(); }
    function plat(id) { return d.plats.find(function (p) { return p.id === id; }); }
    function repas(iso, moment) {
        return d.repas.find(function (r) { return r.jour === iso && r.moment === moment; })
            || { jour: iso, moment: moment, plats: [], issue: null };
    }
    // Les plats d\\'un repas, dans l'ordre du service (au brunch : l'ordre d'ajout)
    function ranges(r) {
        const ps = r.plats.map(plat).filter(Boolean);
        if (r.moment === 'brunch') return ps;
        return ps.sort(function (a, b) { return ORDRE_GENRES.indexOf(a.genre) - ORDRE_GENRES.indexOf(b.genre); });
    }
    function platsDeLaSemaine() {
        return d.repas.filter(function (r) { return d.semaine.indexOf(r.jour) >= 0; })
                      .reduce(function (t, r) { return t.concat(r.plats); }, []);
    }
    // Les accords d'un plat qui tiennent encore : des accompagnements non archivés
    function accordsDe(p) {
        if (p.genre !== 'plat') return [];
        return (p.accords || []).map(plat).filter(function (a) { return a && !a.archive && a.genre === 'accompagnement'; });
    }
    function enStock(nom) { return d.stock.indexOf(normaliser(nom)) >= 0; }
    function surLaListe(nom) { return (d.liste || []).indexOf(normaliser(nom)) >= 0; }
    // Prix d'un panier parisien (prix_paris.py), par la même clé que le catalogue
    function cleCatalogue(nom) {
        return normaliser(nom).split(' ').map(function (m) { return m.length > 3 && /[sx]$/.test(m) ? m.slice(0, -1) : m; }).join(' ');
    }
    const PRIX = {};
    Object.entries(JSON.parse(document.getElementById('prix').textContent)).forEach(function (e) { PRIX[cleCatalogue(e[0])] = e[1]; });
    function prixDe(nom) { return PRIX[cleCatalogue(nom)] || null; }
    function euros(x) {
        return x.toLocaleString('fr-FR', { style: 'currency', currency: 'EUR', minimumFractionDigits: 0, maximumFractionDigits: 0 });
    }
    function aEtiquette(p, e) {
        if (e === 'tout') return true;
        if (e === 'nouvelles') return p.statut === 'a-tester';
        if (e === 'rapide') return p.minutes <= 20;
        if (e === 'nous' || e === 'julien' || e === 'laetitia') return (p.pour || 'nous') === e;
        if (e === 'air-fryer') return /air fryer/i.test(p.nom);
        if (e === 'poisson') return p.ingredients.some(function (i) {
            const n = normaliser(i); return n.indexOf('sauce') !== 0 && MER.some(function (m) { return n.indexOf(m) >= 0; }); });
        if (e === 'legumes') return p.id.indexOf('lg-') === 0 || (p.id.indexOf('af-') === 0 && p.genre === 'accompagnement');
        if (e === 'brunch') return p.id.indexOf('brunch-') === 0 || BRUNCH.indexOf(p.id) >= 0;
        return true;
    }
    function correspond(p, q) {
        return !q || normaliser(p.nom).indexOf(q) >= 0 || p.ingredients.some(function (i) { return normaliser(i).indexOf(q) >= 0; });
    }
    // Les étiquettes d'une liste, avec leur nombre ; celles qui ne trouvent rien sont masquées
    function barreEtiquettes(contexte, liste, rafraichir) {
        const f = el('div', 'filtres etiquettes');
        ETIQUETTES.forEach(function (e) {
            if (e[0] === 'tout') return;                       // pas de pastille « Tout » : un 2e appui sur l'active la retire
            const n = liste.filter(function (p) { return aEtiquette(p, e[0]); }).length;
            if (!n && etiquette[contexte] !== e[0]) return;
            const b = bouton(e[1], etiquette[contexte] === e[0] ? 'actif' : '', function () {
                etiquette[contexte] = etiquette[contexte] === e[0] ? 'tout' : e[0]; rafraichir(); });
            b.setAttribute('aria-pressed', String(etiquette[contexte] === e[0]));
            b.append(el('span', '', String(n)));
            f.append(b);
        });
        return f;
    }

    // --- Données : lecture, copie hors ligne, envois ---
    let chaine = Promise.resolve(), minuteur = null;
    function envoyer(envoi) { const p = chaine.then(function () { return envoyerOuGarder(envoi); }); chaine = p.catch(function () {}); return p; }
    function relire() { clearTimeout(minuteur); minuteur = setTimeout(charger, 400); }
    function garder() { try { localStorage.setItem(CLE_COPIE, JSON.stringify(d)); } catch (e) {} }
    function charger() {
        if (ouverte && ouverte.edition) return;
        fetch('api/diners', { headers: { 'X-Valise-Vite': '1' } })
            .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
            .then(function (lu) { d = lu; garder(); afficher(); })
            .catch(function () { try { d = d || JSON.parse(localStorage.getItem(CLE_COPIE)); } catch (e) {} if (d && !d.repas) d = null; if (d) afficher(); });
    }
    function enregistrerRepas(r) {
        const vide = !r.plats.length && !r.issue;
        d.repas = d.repas.filter(function (x) { return !(x.jour === r.jour && x.moment === r.moment); }).concat(vide ? [] : [r]);
        garder(); afficher();
        return envoyer({ url: 'api/repas', methode: 'POST', corps: r, cle: 'repas:' + r.jour + ':' + r.moment }).then(relire, relire);
    }
    // Les repas prévus des 7 jours sans issue (fait, commandé, dehors : gardés, ce sont des faits)
    function aViderDansLaSemaine() {
        return d.repas.filter(function (r) { return d.semaine.indexOf(r.jour) >= 0 && !r.issue && r.plats.length; });
    }
    function viderSemaine() {
        const aVider = aViderDansLaSemaine();
        viderDemande = false; derniereProposition = {};
        messageSemaine = aVider.length + ' repas retiré(s) : la semaine est libre.';
        aVider.forEach(function (r) { enregistrerRepas(Object.assign({}, r, { plats: [] })); });
        afficher();
    }
    function ajouterPlat(iso, moment, id) {
        const r = repas(iso, moment);
        if (r.plats.indexOf(id) >= 0 || r.plats.length >= 8) return;
        return enregistrerRepas(Object.assign({}, r, { plats: r.plats.concat([id]) }));
    }
    function retirerPlat(iso, moment, id) {
        const r = repas(iso, moment);
        enregistrerRepas(Object.assign({}, r, { plats: r.plats.filter(function (x) { return x !== id; }) }));
    }
    function enregistrerPlat(p) {
        d.plats = d.plats.filter(function (x) { return x.id !== p.id; }).concat([p]);
        garder(); afficher();
        return envoyer({ url: 'api/plats', methode: 'POST', corps: p, cle: 'plat:' + p.id }).then(relire, function (e) { relire(); throw e; });
    }
    function ajouterAuxCourses(noms, source) {
        noms.forEach(function (nom) {
            const id = nouvelId('art');
            envoyer({ url: 'api/courses', methode: 'POST', cle: 'article:' + id,
                      corps: { id: id, nom: nom, pris: false, recurrent: false, actif: true, source: source } });
        });
    }

    // --- Vues ---
    // Recettes : les plus faites, puis les connues (A → Z), puis les nouvelles, recette écrite d'abord
    function rangRecette(p) { return p.statut === 'a-tester' ? (p.recette ? 2 : 3) : (p.faits ? 0 : 1); }
    function ordreRecettes(a, b) {
        return rangRecette(a) - rangRecette(b) || (b.faits || 0) - (a.faits || 0) || a.nom.localeCompare(b.nom, 'fr');
    }
    // Les repères d'une recette en icônes ; le mot reste pour le lecteur d'écran et au survol
    // `signe` : une clé du <template id="reperes"> (icône SVG), sinon du texte
    const CLES_REPERES = ['nouvelle', 'eclair', 'sablier'];
    function clone(cle) { return document.getElementById('reperes').content.querySelector('[data-icone="' + cle + '"]').cloneNode(true); }
    function icone(signe, mot, classe) {
        const s = el('span', 'repere' + (classe ? ' ' + classe : ''));
        if (CLES_REPERES.indexOf(signe) >= 0) s.append(clone(signe)); else s.append(signe);
        s.setAttribute('role', 'img'); s.setAttribute('aria-label', mot); s.title = mot;
        return s;
    }
    function points(n) { const k = n >= 5 ? 4 : n >= 3 ? 3 : n; return '●'.repeat(k) + '○'.repeat(4 - k); }
    function lignePlat(p, extra) {
        const li = el('li');
        const o = bouton('', 'ouvrir', function () { ouvrirFiche(p.id); });
        const nom = el('span', 'nom', p.nom);
        if (p.statut === 'a-tester') nom.append(icone('nouvelle', 'nouvelle', 'nouvelle'));
        else if (p.faits) nom.append(icone(points(p.faits), 'faite ' + p.faits + ' fois', 'points'));
        if (d.secours.faisables.indexOf(p.id) >= 0) nom.append(icone('eclair', 'faisable ce soir'));
        if ((d.a_finir || []).indexOf(p.id) >= 0) nom.append(icone('sablier', 'finit un produit'));
        if (p.pour === 'julien') nom.append(icone('Ⓙ', 'pour Julien', 'qui'));
        if (p.pour === 'laetitia') nom.append(icone('Ⓛ', 'pour Laetitia', 'qui'));
        const meta = el('span', 'meta', NOMS_GENRE[p.genre] + ' · ' + duree(p.minutes) + (p.cout ? ' · ≈ ' + euros(p.cout) : ''));
        if (extra) { meta.append(' · '); meta.append(extra); }
        o.append(nom, meta);
        li.append(o);
        return li;
    }
    function compteurDiners() {
        const c = d.compteur;
        const b = el('div', 'compteur-diners' + (c.semaine > 1 ? ' trop' : ''));
        b.append(el('strong', '', 'Deliveroo : ' + c.semaine + ' ces 7 jours'),
                 el('span', '', 'objectif : 1 au plus · moyenne ' + c.moyenne.toFixed(1).replace('.', ',') + ' par semaine'));
        return b;
    }
    function vueCeSoir(zone) {
        if (d.compteur && d.compteur.renseignes) zone.append(compteurDiners());
        const ps = ranges(repas(d.aujourd_hui, 'diner'));
        const principal = ps.filter(function (x) { return x.genre === 'plat'; })[0] || ps[0];
        if (principal) {
            const bloc = el('div', 'plat-soir');
            bloc.append(el('span', 'titre', 'Ce soir'), el('span', 'nom', principal.nom));
            const ul = el('ul', 'plats-soir');
            ps.forEach(function (x) {
                const li = el('li');
                li.append(el('span', '', NOMS_GENRE[x.genre] + ' · ' + x.nom + ' · ' + duree(x.minutes)),
                          bouton('Voir la recette', '', function () { ouvrirFiche(x.id); }));
                ul.append(li);
            });
            bloc.append(ul);
            const cout = ps.reduce(function (t, x) { return t + (x.cout || 0); }, 0);
            if (cout) bloc.append(el('span', 'cout', '≈ ' + euros(cout) + ' le repas · en livraison ≈ ' + euros(d.livraison)));
            const b = el('div', 'boutons');
            b.append(bouton('Changer', 'discret', function () { allerA('semaine'); }));
            bloc.append(b);
            zone.append(bloc);
        } else {
            const e = el('div', 'encart');
            e.append(el('h2', '', 'Rien de prévu ce soir'),
                     el('p', 'aide', 'Avant d\\'ouvrir Deliveroo : voilà ce que le placard permet en 20 minutes.'));
            zone.append(e);
        }
        const f = el('div', 'encart');
        f.append(el('h2', '', 'Faisable tout de suite'));
        const ul = el('ul', 'plats');
        d.secours.faisables.map(plat).filter(Boolean).forEach(function (x) {
            const li = lignePlat(x);
            if (!principal) li.append(bouton('Ce soir', 'petit', function () { ajouterPlat(d.aujourd_hui, 'diner', x.id); }));
            ul.append(li);
        });
        if (!ul.children.length) ul.append(el('li', 'meta', 'Rien de faisable avec le placard actuel.'));
        f.append(ul);
        zone.append(f);
        if (d.secours.presque.length) {
            const q = el('div', 'encart');
            q.append(el('h2', '', 'Presque'), el('p', 'aide', 'Il manque un ou deux ingrédients.'));
            const ul2 = el('ul', 'plats');
            d.secours.presque.forEach(function (x) {
                const pp = plat(x.plat); if (!pp) return;
                const li = lignePlat(pp, el('span', 'manque', 'il manque : ' + x.manquants.join(', ')));
                li.append(bouton('Aux courses', 'petit', function (ev) {
                    ajouterAuxCourses(x.manquants, 'plat:' + pp.id); ev.target.textContent = 'Ajouté'; ev.target.disabled = true;
                }));
                ul2.append(li);
            });
            q.append(ul2);
            zone.append(q);
        }
    }
    // « Proposer ma semaine » : le serveur propose un menu pour chaque case cochée (diners.proposer_cases) ;
    // « Reproposer » ne change que les repas qu'il a proposés et qu'on n'a pas modifiés depuis (cases vide)
    function proposerSemaine(msg, cases, remplacer) {
        if (proposeEnCours) return;
        proposeEnCours = true;
        messageSemaine = 'Je cherche…'; msg.textContent = messageSemaine;
        afficher();                                       // grise Proposer et Reproposer pendant la demande
        chaine.then(function () {
            return fetch('api/diners/proposer', { method: 'POST', headers: { 'Content-Type': 'application/json' },
                                                  body: JSON.stringify({ cases: cases, remplacer: remplacer || [] }) });
        }).then(function (r) { if (!r.ok) { const e = new Error(r.status); e.code = r.status; throw e; } return r.json(); })
          .then(function (r) {
              proposeEnCours = false;
              const cles = Object.keys(r.menus || {}), poses = {};
              cles.forEach(function (cle) {
                  const jour = cle.split('|')[0], moment = cle.split('|')[1], plats = r.menus[cle];
                  d.repas = d.repas.filter(function (x) { return !(x.jour === jour && x.moment === moment); })
                                   .concat([{ jour: jour, moment: moment, plats: plats, issue: null }]);
                  poses[cle] = plats.join(' ');
              });
              derniereProposition = Object.assign({}, derniereProposition, poses);
              grilleOuverte = false;
              garder();
              messageSemaine = cles.length ? cles.length + ' repas proposé(s), avec un accompagnement quand le plat en a. Change-les ou ajoute un dessert, puis envoie aux courses.'
                                           : 'Rien à proposer : aucun plat ne convient pour ces repas.';
              afficher(); relire();
          }, function (e) {
              proposeEnCours = false;
              // un code : le serveur a répondu mais refusé ; sinon la requête n'a pas abouti
              messageSemaine = e && e.code ? 'Le serveur a refusé (code ' + e.code + ').' : 'Pas de réseau : réessaie une fois connecté.';
              afficher();
          });
    }
    function lireGrille() {
        if (grille) return grille;
        try {
            const v = JSON.parse(localStorage.getItem(CLE_GRILLE));
            if (Array.isArray(v)) grille = v.filter(function (x) { return typeof x === 'string'; });
        } catch (e) {}
        if (!grille) grille = GRILLE_DEFAUT.slice();
        return grille;
    }
    function ecrireGrille() { try { localStorage.setItem(CLE_GRILLE, JSON.stringify(grille)); } catch (e) {} }
    function jourDeSemaine(iso) { return (new Date(iso + 'T12:00:00').getDay() + 6) % 7; }   // 0 = lundi
    // Un repas est pris s'il a des plats ou une issue (le midi : aussi un brunch) ; un jour passé ne se remplit plus
    const MIDI_PASSE_A = 15;                              // après 15 h, le déjeuner du jour est passé : pas à proposer
    function caseOccupee(iso, moment) {
        if (iso < d.aujourd_hui) return true;
        if (iso === d.aujourd_hui && moment === 'dejeuner' && new Date().getHours() >= MIDI_PASSE_A) return true;
        const moments = moment === 'dejeuner' ? ['dejeuner', 'brunch'] : [moment];
        return moments.some(function (m) { return repas(iso, m).plats.length || repas(iso, m).issue; });
    }
    function casesCochees() {
        const choix = lireGrille(), res = [];
        d.semaine.forEach(function (iso) {
            ['dejeuner', 'diner'].forEach(function (moment) {
                if (choix.indexOf(jourDeSemaine(iso) + '|' + moment) >= 0 && !caseOccupee(iso, moment)) res.push({ jour: iso, moment: moment });
            });
        });
        return res;
    }
    function grilleProposer(msg) {
        const g = el('div', 'grille-proposer');
        const choix = lireGrille();
        const tete = el('div', 'rang');
        tete.append(el('span'));
        d.semaine.forEach(function (iso) {
            const s = el('span', '', enClair(iso).charAt(0).toUpperCase() + ' ' + iso.slice(8).replace(/^0/, ''));
            s.setAttribute('aria-label', enClair(iso));
            tete.append(s);
        });
        g.append(tete);
        [['dejeuner', 'Midi'], ['diner', 'Soir']].forEach(function (m) {
            const rang = el('div', 'rang');
            rang.append(el('span', 'etiq', m[1]));
            d.semaine.forEach(function (iso) {
                const cle = jourDeSemaine(iso) + '|' + m[0];
                const pris = caseOccupee(iso, m[0]), coche = !pris && choix.indexOf(cle) >= 0;
                const b = el('button', 'case', pris ? 'pris' : coche ? 'x' : '');
                b.type = 'button'; b.disabled = pris;
                b.setAttribute('aria-pressed', coche ? 'true' : 'false');
                b.setAttribute('aria-label', m[1] + ' ' + enClair(iso) + (pris ? ' (pris)' : ''));
                b.addEventListener('click', function () {
                    const k = choix.indexOf(cle);
                    if (k >= 0) choix.splice(k, 1); else choix.push(cle);
                    ecrireGrille(); afficher();
                });
                rang.append(b);
            });
            g.append(rang);
        });
        const cases = casesCochees();
        g.append(el('p', 'decompte', cases.length + ' repas à proposer'));
        const act = el('div', 'actions');
        const ok = bouton('Proposer', 'plein', function () { proposerSemaine(msg, casesCochees(), []); });
        ok.disabled = !cases.length || proposeEnCours;
        act.append(ok, bouton('Annuler', 'petit', function () { grilleOuverte = false; afficher(); }));
        g.append(act);
        return g;
    }
    // Une carte de repas : ses plats (× pour retirer), puis + plat / + entrée / + accompagnement / + dessert
    function carteRepas(iso, moment) {
        const r = repas(iso, moment);
        const c = el('div', 'repas');
        const t = el('div', 'titre-repas');
        t.append(el('span', '', MOMENTS[moment]));
        if (r.issue) t.append(el('span', 'badge', r.issue === 'fait' ? 'fait maison' : r.issue === 'commande' ? 'commandé' : r.issue));
        c.append(t);
        const ul = el('ul', 'plats-repas');
        const accompagne = ranges(r).some(function (x) { return x.genre === 'accompagnement'; });
        ranges(r).forEach(function (p) {
            const li = el('li');
            const o = bouton('', 'ouvrir', function () { ouvrirFiche(p.id); });
            o.append(el('span', 'nom', p.nom), el('span', 'meta', NOMS_GENRE[p.genre] + ' · ' + duree(p.minutes)));
            const x = bouton('×', 'retirer', function () { retirerPlat(iso, moment, p.id); });
            x.setAttribute('aria-label', 'Retirer ' + p.nom);
            li.append(o, x);
            ul.append(li);
            // Ses accords, tant que le repas n'a pas d'accompagnement : un appui en ajoute un
            const absents = accordsDe(p).filter(function (acc) { return r.plats.indexOf(acc.id) < 0; });
            if (absents.length && !accompagne && r.plats.length < 8) {
                const avec = el('li', 'avec');
                avec.append(el('span', 'meta', 'Avec :'));
                absents.forEach(function (acc) {
                    avec.append(bouton(acc.nom, 'petit', function () { ajouterPlat(iso, moment, acc.id); }));
                });
                ul.append(avec);
            }
        });
        if (!ul.children.length) ul.append(el('li', 'meta', 'Libre'));
        c.append(ul);
        const a = el('div', 'ajouts');
        // Au brunch, un seul bouton : tous les genres, étiquette Brunch
        (moment === 'brunch' ? [[null, '+ ajouter']] : AJOUTS).forEach(function (g) {
            a.append(bouton(g[1], 'petit', function () { ouvrirChoix(iso, moment, g[0]); }));
        });
        c.append(a);
        return c;
    }
    function vueSemaine(zone) {
        const e = el('div', 'encart');
        e.append(el('h2', '', 'La semaine'), el('p', 'aide', 'Coche les repas à remplir : l\\'app propose un plat pour chacun.'));
        d.semaine.forEach(function (iso, i) {
            const jour = el('div', 'jour-repas');
            const q = el('span', 'quand', i === 0 ? 'Ce soir' : enClair(iso));
            if (i === 0) q.append(el('small', '', enClair(iso)));
            jour.append(q, carteRepas(iso, 'diner'));
            const midi = ['dejeuner', 'brunch'].filter(function (m) { return repas(iso, m).plats.length || repas(iso, m).issue; });
            midi.forEach(function (m) { jour.append(carteRepas(iso, m)); });
            if (!midi.length) {
                const plus = el('div', 'ajouts');
                const lien = bouton('+ déjeuner ou brunch', 'petit', function () {
                    plus.replaceChildren(
                        bouton('Déjeuner', 'petit', function () { ouvrirChoix(iso, 'dejeuner', 'plat'); }),
                        bouton('Brunch', 'petit', function () { ouvrirChoix(iso, 'brunch', null); }));
                });
                plus.append(lien);
                jour.append(plus);
            }
            e.append(jour);
        });
        const msgP = el('p', 'message', messageSemaine); msgP.id = 'message-semaine';
        const cs = d.cout_semaine;
        if (cs && cs.nb_repas) {
            const bilan = el('div', 'bilan-semaine');
            [['', euros(cs.cout), cs.nb_repas + ' repas maison'],
             ['livraison', euros(cs.livraison), 'les mêmes en livraison'],
             ['', euros(cs.courses), 'courses à faire pour eux']].forEach(function (x) {
                const c = el('div', x[0]); c.append(el('strong', '', x[1]), el('span', '', x[2])); bilan.append(c);
            });
            e.append(bilan);
        }
        const prop = el('div', 'proposer');
        prop.append(bouton('Proposer ma semaine', 'plein', function () { grilleOuverte = !grilleOuverte; afficher(); }));
        const aRefaire = Object.keys(derniereProposition).filter(function (cle) {
            return cle.split('|')[0] >= d.aujourd_hui && repas(cle.split('|')[0], cle.split('|')[1]).plats.join(' ') === derniereProposition[cle]; })
            .map(function (cle) { return { jour: cle.split('|')[0], moment: cle.split('|')[1] }; });
        if (aRefaire.length) {
            const re = bouton('Reproposer', 'petit', function () { proposerSemaine(msgP, [], aRefaire); });
            if (proposeEnCours) re.disabled = true;
            prop.append(re);
        }
        const nbAVider = aViderDansLaSemaine().length;
        if (nbAVider && !viderDemande) {
            prop.append(bouton('Vider la semaine', 'petit', function () { viderDemande = true; afficher(); }));
        } else if (nbAVider) {
            prop.append(bouton('Oui, vider ' + nbAVider + ' repas', 'petit danger', viderSemaine),
                        bouton('Annuler', 'petit', function () { viderDemande = false; afficher(); }));
        }
        zone.append(prop);
        if (grilleOuverte) zone.append(grilleProposer(msgP));
        zone.append(msgP, e);
        const msg = el('p', 'message');
        zone.append(bouton('Ajouter les ingrédients de la semaine aux courses', 'plein', function () {
            msg.textContent = 'Envoi…';
            chaine.then(function () { return fetch('api/diners/courses', { method: 'POST' }); })   // après les choix en cours
                .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
                .then(function (r) {
                    msg.textContent = r.ajoutes.length ? r.ajoutes.length + ' ajouté(s) : ' + r.ajoutes.join(', ')
                                                       : 'Rien à ajouter : tout est au placard ou déjà sur la liste.';
                }, function () { msg.textContent = 'Pas de réseau : réessaie une fois connecté.'; });
        }), msg);
    }
    function vueRecettes(zone) {
        const r = el('input', 'recherche'); r.type = 'search'; r.placeholder = 'Chercher un plat ou un ingrédient';
        r.value = recherche; r.setAttribute('aria-label', 'Chercher');
        const f = el('div', 'segments');                       // le genre : une barre segmentée, comme les onglets
        [['tout', 'Tout']].concat(GENRES).forEach(function (g) {
            const b = bouton(g[0] === 'accompagnement' ? 'Accomp.' : g[1], filtre === g[0] ? 'actif' : '', function () { filtre = g[0]; afficher(); });
            b.setAttribute('aria-pressed', String(filtre === g[0]));
            f.append(b);
        });
        const ul = el('ul', 'plats');
        const toutes = d.plats.filter(function (p) { return !p.archive; });
        const zoneEtiquettes = el('div');
        function remplir() {
            ul.replaceChildren();
            const q = normaliser(recherche);
            const parGenre = toutes.filter(function (p) { return (filtre === 'tout' || p.genre === filtre) && correspond(p, q); });
            zoneEtiquettes.replaceChildren(barreEtiquettes('recettes', parGenre, remplir));
            parGenre.filter(function (p) { return aEtiquette(p, etiquette.recettes); })
                .sort(ordreRecettes)
                .forEach(function (p) { ul.append(lignePlat(p, p.statut === 'a-tester' && !p.recette ? 'recette à écrire' : undefined)); });
            if (!ul.children.length) ul.append(el('li', 'meta', 'Aucune recette ne correspond.'));
        }
        r.addEventListener('input', function () { recherche = r.value; remplir(); });
        remplir();
        const e = el('div', 'encart');
        const legende = el('p', 'legende-reperes');
        legende.append(clone('nouvelle'), ' nouvelle · ●●● faite souvent · ', clone('eclair'), ' faisable ce soir · ',
                       clone('sablier'), ' finit un produit · Ⓙ Ⓛ pour Julien / Laetitia');
        e.append(ul, legende);
        zone.append(r, f, zoneEtiquettes, bouton('+ Nouvelle recette', 'plein', function () { ouvrirEdition(null); }), e);
    }

    // Ajouter un plat d'un genre à un repas : la même recherche et les mêmes étiquettes, dans l'ordre des Recettes
    function ouvrirChoix(iso, moment, genre) {
        ouverte = { id: null, edition: false };
        const c = document.querySelector('#panneau .contenu'); c.replaceChildren();
        const haut = el('div', 'haut');
        const quand = iso === d.aujourd_hui ? (moment === 'diner' ? 'ce soir' : 'aujourd\\'hui') : enClair(iso);
        haut.append(el('h2', '', MOMENTS[moment] + ' · ' + quand + (genre ? ' · ' + NOMS_GENRE[genre].toLowerCase() : '')),
                    bouton('Fermer', 'petit', fermer));
        if (moment === 'brunch') etiquette.choix = 'brunch';                 // au brunch, d'abord les recettes de brunch
        else if (etiquette.choix === 'brunch') etiquette.choix = 'nous';
        let q = '';
        const r = el('input', 'recherche'); r.type = 'search'; r.placeholder = 'Chercher un plat ou un ingrédient';
        r.setAttribute('aria-label', 'Chercher');
        const zoneEtiquettes = el('div'), listes = el('div', 'vue');
        const tous = d.plats.filter(function (p) { return (!genre || p.genre === genre) && !p.archive; });
        let affiches = [];
        const dansRepas = repas(iso, moment).plats, plein = dansRepas.length >= 8;
        // Au hasard : parmi les plats affichés (recherche et filtre compris), hors ceux déjà prévus cette semaine
        const hasard = bouton('Au hasard', 'plein', function () {
            const deja = platsDeLaSemaine().concat(dansRepas);
            const pool = affiches.filter(function (p) { return deja.indexOf(p.id) < 0; });
            if (!pool.length) { hasard.textContent = 'Rien à tirer avec ces filtres'; return; }
            const p = pool[Math.floor(Math.random() * pool.length)];
            ajouterPlat(iso, moment, p.id); fermer();
        });
        hasard.disabled = plein;
        function remplir() {
            const trouves = tous.filter(function (p) { return correspond(p, normaliser(q)); });
            affiches = trouves.filter(function (p) { return aEtiquette(p, etiquette.choix); });
            hasard.textContent = 'Au hasard parmi ' + affiches.length;
            zoneEtiquettes.replaceChildren(barreEtiquettes('choix', trouves, remplir));
            listes.replaceChildren();
            const ul = el('ul', 'plats');
            affiches.slice().sort(ordreRecettes).forEach(function (p) {
                const li = lignePlat(p);
                li.querySelector('button.ouvrir').replaceWith(li.querySelector('button.ouvrir').cloneNode(true));
                if (plein || dansRepas.indexOf(p.id) >= 0) {
                    li.querySelector('button.ouvrir').disabled = true;
                    if (dansRepas.indexOf(p.id) >= 0) li.querySelector('.nom').append(el('span', 'badge', 'au menu'));
                } else {
                    li.querySelector('button.ouvrir').addEventListener('click', function () { ajouterPlat(iso, moment, p.id); fermer(); });
                }
                ul.append(li);
            });
            if (ul.children.length) listes.append(ul);
            if (!listes.children.length) listes.append(el('p', 'aide', 'Aucune recette ne correspond.'));
        }
        r.addEventListener('input', function () { q = r.value; remplir(); });
        remplir();
        c.append(haut);
        if (plein) c.append(el('p', 'aide', 'Ce repas a déjà 8 plats : retires-en un avant d\\'en ajouter.'));
        c.append(hasard, r, zoneEtiquettes);
        c.append(listes);
        document.getElementById('panneau').hidden = false;
        document.getElementById('panneau').scrollTop = 0;
    }

    // --- Fiche et édition ---
    function verrouiller() {
        if (!('wakeLock' in navigator)) return;
        navigator.wakeLock.request('screen').then(function (v) { verrou = v; }).catch(function () {});
    }
    function fermer() {
        ouverte = null;
        if (verrou) { verrou.release().catch(function () {}); verrou = null; }
        document.getElementById('panneau').hidden = true;
        afficher();
    }
    // --- Fiche « magazine » : affiche p.fiche (découpée en Python, fiche_recette.py) ---
    function phraseFiche(x, parent) {
        if (x.action) parent.append(el('strong', '', x.action));
        x.morceaux.forEach(function (m) { parent.append(m.genre === 'pourquoi' ? el('em', '', ' ' + m.texte) : document.createTextNode(m.texte)); });
        x.secrets.forEach(function (s) {
            const b = el('div', 'secret' + (s.qui === 'mamma' ? ' mamma' : ''));
            b.append(el('b', '', s.qui === 'mamma' ? 'Secret de mamma' : 'Secret de grand-mère'), document.createTextNode(' · ' + s.texte));
            parent.append(b);
        });
    }
    function uneFiche(p) {
        const f = p.fiche, une = el('div', 'une-fiche'), haut = el('div', 'haut');
        haut.append(el('span', 'meta', NOMS_GENRE[p.genre] + ' · ' + duree(p.minutes) + (f.pour ? ' · ' + f.pour : '')), bouton('Fermer', 'petit', fermer));
        une.append(haut, el('h2', '', p.nom));
        if (f.difference.length) {
            const ul = el('ul');
            f.difference.forEach(function (x) { ul.append(el('li', '', '« ' + x + ' »')); });
            une.append(ul);
        }
        return une;
    }
    function groupesIngredients(p) {
        return [['ok', 'Au placard', p.ingredients.filter(enStock)],
                ['liste', 'Déjà sur la liste', p.ingredients.filter(function (i) { return !enStock(i) && surLaListe(i); })],
                ['manque', 'À acheter', p.ingredients.filter(function (i) { return !enStock(i) && !surLaListe(i); })]];
    }
    function pastilles(groupes, parent) {
        groupes.forEach(function (g) {
            if (!g[2].length) return;
            const sec = el('section', 'groupe-ing'), ing = el('div', 'ingredients');
            g[2].forEach(function (i) {
                const t = el('span', g[0], i), pr = prixDe(i);
                if (g[0] === 'manque' && pr) t.append(el('small', '', euros(pr[1])));
                ing.append(t);
            });
            sec.append(el('h3', '', g[1] + ' · ' + g[2].length), ing);
            parent.append(sec);
        });
    }
    function bandeauCourses(p, groupes) {
        const manque = groupes[2][2], det = el('details', 'courses-fiche');
        const total = manque.reduce(function (t, i) { const pr = prixDe(i); return t + (pr ? pr[1] : 0); }, 0);
        det.append(el('summary', '', manque.length ? manque.length + ' à acheter' + (total ? ' · ≈ ' + euros(total) : '') : 'Tout est au placard'));
        pastilles(groupes, det);
        if (p.cout) det.append(el('p', 'meta', '≈ ' + euros(p.cout) + ' le repas pour deux · en livraison ≈ ' + euros(d.livraison)));
        return det;
    }
    function ingredientsFiche(f) {
        const frag = document.createDocumentFragment();
        function liste(lignes) {
            const ul = el('ul', 'ing-fiche');
            lignes.forEach(function (x) {
                const li = el('li'), c = el('input'), t = el('span');
                c.type = 'checkbox';
                c.addEventListener('change', function () { li.classList.toggle('coche', c.checked); });
                t.append(el('b', '', x.nom));
                if (x.quantite) t.append(document.createTextNode(x.quantite));
                li.append(c, t); ul.append(li);
            });
            return ul;
        }
        if (f.ingredients.length) frag.append(el('h3', 'titre-fiche', 'Ingrédients'), liste(f.ingredients));
        f.sections.forEach(function (s) {
            if (!s.lignes.length) { frag.append(el('p', 'para-fiche', s.titre)); return; }
            frag.append(el('h3', 'titre-fiche', s.titre),
                        liste(s.lignes.map(function (l) { return { nom: l, quantite: '' }; })));
        });
        return frag;
    }
    function tempoFiche(f) {
        const frag = document.createDocumentFragment();
        if (!f.tempo || !f.tempo.lignes.length) return frag;
        const bande = el('div', 'tempo-fiche');
        f.tempo.lignes.forEach(function (l) {
            const b = el('button');
            b.type = 'button';
            b.append(el('b', '', l.heure), document.createTextNode(l.texte));
            if (l.etapes.length) b.addEventListener('click', function () {
                const cible = document.getElementById('etape-' + l.etapes[0]);
                if (!cible) return;
                cible.scrollIntoView({ behavior: 'smooth', block: 'start' });
                cible.classList.add('vise');
                setTimeout(function () { cible.classList.remove('vise'); }, 2000);
            });
            bande.append(b);
        });
        frag.append(el('h3', 'titre-fiche', f.tempo.titre), bande);
        return frag;
    }
    function etapesFiche(f) {
        const ol = el('ol', 'etapes-fiche');
        f.etapes.forEach(function (e) {
            const li = el('li');
            li.id = 'etape-' + e.n;
            li.append(el('span', 'num', String(e.n)));
            phraseFiche(e, li);
            if (e.si.length) {
                const ul = el('ul');
                e.si.forEach(function (s) { const x = el('li'); phraseFiche(s, x); ul.append(x); });
                li.append(ul);
            }
            ol.append(li);
        });
        const frag = document.createDocumentFragment();
        frag.append(el('h3', 'titre-fiche', 'Étapes'), ol);
        return frag;
    }
    function lienOrigine(p, c) {
        if (!p.lien) return;
        const m = el('p', 'meta'), a = el('a', '', 'Recette d\\'origine');
        a.href = p.lien; a.target = '_blank'; a.rel = 'noopener'; m.append(a); c.append(m);
    }
    function ouvrirFiche(id) {
        const p = plat(id); if (!p) return;
        ouverte = { id: id, edition: false };
        const c = document.querySelector('#panneau .contenu'); c.replaceChildren();
        const groupes = groupesIngredients(p);
        if (p.fiche && p.fiche.structuree) {
            c.append(uneFiche(p), bandeauCourses(p, groupes), ingredientsFiche(p.fiche), tempoFiche(p.fiche), etapesFiche(p.fiche));
            lienOrigine(p, c);
        } else {
            const haut = el('div', 'haut');
            haut.append(el('span', 'meta', NOMS_GENRE[p.genre] + ' · ' + duree(p.minutes)), bouton('Fermer', 'petit', fermer));
            c.append(haut, el('h2', '', p.nom));
            lienOrigine(p, c);
            pastilles(groupes, c);
            if (p.cout) c.append(el('p', 'meta', '≈ ' + euros(p.cout) + ' le repas pour deux (part utilisée de chaque produit) · en livraison ≈ ' + euros(d.livraison)));
            c.append(el('pre', 'recette', p.recette || 'Recette à écrire : demande à Claude, ou écris la tienne avec « Modifier ».'));
        }
        if (p.note) c.append(el('p', 'meta', p.note));
        if (p.genre === 'plat') {
            const va = el('section', 'groupe-ing accords'), liste = el('div', 'ingredients');
            accordsDe(p).forEach(function (a) { liste.append(bouton(a.nom, 'petit', function () { ouvrirFiche(a.id); })); });
            if (!liste.children.length) liste.append(el('span', '', 'Aucun accompagnement choisi.'));
            va.append(el('h3', '', 'Va bien avec'), liste, bouton('Modifier les accords', 'petit', function () { ouvrirAccords(p.id); }));
            c.append(va);
        }
        const act = el('div', 'actions');
        act.append(bouton('Ce soir', 'plein', function () {
            const envoi = ajouterPlat(d.aujourd_hui, 'diner', p.id);
            fermer();
            // sur Recettes, allerA quitte la page : attendre que l'envoi soit parti ou mis en file hors ligne
            const aller = function () { allerA('ce-soir'); };
            if (PAGE === 'recettes' && envoi) envoi.then(aller, aller); else aller();
        }),
                   bouton('Modifier', 'petit', function () { ouvrirEdition(p.id); }));
        const manquants = p.ingredients.filter(function (i) { return !enStock(i) && !surLaListe(i); });
        const total = manquants.reduce(function (t, i) { const pr = prixDe(i); return t + (pr ? pr[1] : 0); }, 0);
        if (manquants.length) act.append(bouton('Ajouter les ' + manquants.length + ' manquants aux courses' + (total ? ' (≈ ' + euros(total) + ')' : ''), 'petit', function (ev) {
            ajouterAuxCourses(manquants, 'plat:' + p.id);
            d.liste = (d.liste || []).concat(manquants.map(normaliser)); garder();
            ev.target.textContent = 'Ajouté aux courses'; ev.target.disabled = true; }));
        if (p.statut === 'a-tester') act.append(bouton('On l\\'a déjà faite', 'petit', function () {
            enregistrerPlat(Object.assign({}, p, { statut: 'carnet' })); fermer(); }));
        c.append(act);
        document.getElementById('panneau').hidden = false;
        document.getElementById('panneau').scrollTop = 0;
        verrouiller();                                     // l'écran reste allumé pendant qu'on cuisine
    }
    // Les accords d'un plat : les accompagnements (carnet et à tester), 6 au plus ; un appui coche ou décoche
    function ouvrirAccords(id) {
        const p = plat(id); if (!p) return;
        ouverte = { id: id, edition: true };                // pas de rechargement pendant le choix
        let choisis = accordsDe(p).map(function (a) { return a.id; });
        const c = document.querySelector('#panneau .contenu'); c.replaceChildren();
        const haut = el('div', 'haut');
        haut.append(el('h2', '', 'Avec : ' + p.nom), bouton('Annuler', 'petit', function () { ouvrirFiche(id); }));
        const aide = el('p', 'aide'), ul = el('ul', 'plats'), msg = el('p', 'message');
        const accs = d.plats.filter(function (a) { return a.genre === 'accompagnement' && !a.archive; })
                            .sort(function (a, b) { return a.nom.localeCompare(b.nom, 'fr'); });
        function remplir() {
            aide.textContent = choisis.length + ' choisi(s), 6 au plus.';
            ul.replaceChildren();
            accs.forEach(function (a) {
                const pris = choisis.indexOf(a.id) >= 0;
                function basculer() {
                    if (!pris && choisis.length >= 6) return;
                    choisis = pris ? choisis.filter(function (x) { return x !== a.id; }) : choisis.concat([a.id]);
                    remplir();
                }
                const li = lignePlat(a);
                const o = li.querySelector('button.ouvrir'), o2 = o.cloneNode(true);
                o.replaceWith(o2); o2.addEventListener('click', basculer);
                const b = bouton(pris ? 'Retirer' : 'Ajouter', pris ? 'plein' : 'petit', basculer);
                b.disabled = !pris && choisis.length >= 6;
                b.setAttribute('aria-pressed', String(pris));
                li.append(b);
                ul.append(li);
            });
        }
        remplir();
        const ok = bouton('Enregistrer', 'plein', function () {
            enregistrerPlat(Object.assign({}, p, { accords: choisis })).then(function () { ouvrirFiche(id); },
                function (e) { msg.textContent = 'Refusé par le serveur (' + e.message + ').'; });
        });
        const e = el('div', 'encart'); e.append(ul);
        c.append(haut, aide, ok, msg, e);
        document.getElementById('panneau').hidden = false;
        document.getElementById('panneau').scrollTop = 0;
    }
    function ouvrirEdition(id) {
        const p = id ? plat(id) : { id: nouvelId('plat'), nom: '', genre: 'plat', minutes: 30, ingredients: [], recette: '',
                                    lien: '', note: '', statut: 'carnet', archive: false, pour: 'nous' };
        ouverte = { id: p.id, edition: true };
        const c = document.querySelector('#panneau .contenu'); c.replaceChildren();
        const haut = el('div', 'haut');
        haut.append(el('h2', '', id ? 'Modifier' : 'Nouvelle recette'), bouton('Annuler', 'petit', function () { id ? ouvrirFiche(id) : fermer(); }));
        const f = el('form', 'edition');
        function champ(etiquette, nom, element) { const l = el('label', '', etiquette); element.name = nom; element.id = 'edit-' + nom; l.append(element); return l; }
        const nom = el('input'); nom.value = p.nom; nom.required = true; nom.maxLength = 80;
        const genre = el('select'); GENRES.forEach(function (g) { genre.append(new Option(NOMS_GENRE[g[0]], g[0])); }); genre.value = p.genre;
        const minutes = el('input'); minutes.type = 'number'; minutes.min = 1; minutes.max = 600; minutes.value = p.minutes;
        const ing = el('textarea'); ing.value = p.ingredients.join(', '); ing.style.minHeight = '80px';
        ing.placeholder = 'spaghetti, œufs, pecorino (les noms du placard)';
        const rec = el('textarea'); rec.value = p.recette;
        const lien = el('input'); lien.type = 'url'; lien.value = p.lien; lien.placeholder = 'https://…';
        const note = el('input'); note.value = p.note; note.maxLength = 500;
        const pour = el('select'); [['nous', 'Nous deux'], ['julien', 'Julien seul'], ['laetitia', 'Laetitia seule']].forEach(function (x) { pour.append(new Option(x[1], x[0])); });
        pour.value = p.pour || 'nous';
        const deux = el('div', 'deux'); deux.append(champ('Genre', 'genre', genre), champ('Temps (min)', 'minutes', minutes));
        const msg = el('p', 'message');
        f.append(champ('Nom', 'nom', nom), deux, champ('Pour qui', 'pour', pour), champ('Ingrédients, séparés par des virgules', 'ingredients', ing),
                 champ('Recette', 'recette', rec), champ('Lien', 'lien', lien), champ('Note', 'note', note), msg);
        const act = el('div', 'actions');
        const ok = el('button', 'plein', 'Enregistrer'); ok.type = 'submit';
        act.append(ok);
        if (id) act.append(bouton(p.archive ? 'Désarchiver' : 'Archiver', 'petit', function () {
            enregistrerPlat(Object.assign({}, p, { archive: !p.archive })); fermer(); }));
        f.append(act);
        f.addEventListener('submit', function (ev) {
            ev.preventDefault();
            const n = Object.assign({}, p, { nom: nom.value.trim(), genre: genre.value, minutes: parseInt(minutes.value, 10) || 0,
                ingredients: ing.value.split(',').map(function (x) { return x.trim(); }).filter(Boolean),
                recette: rec.value, lien: lien.value.trim(), note: note.value.trim(), pour: pour.value });
            enregistrerPlat(n).then(function () { ouvrirFiche(n.id); },
                                    function (e) { msg.textContent = 'Refusé par le serveur (' + e.message + ') : vérifie le temps (1 à 600) et le lien.'; });
        });
        c.append(haut, f);
        document.getElementById('panneau').hidden = false;
    }

    function afficher() {
        if (!d) return;
        document.querySelectorAll('nav.vues button').forEach(function (b) { b.classList.toggle('actif', b.dataset.vue === vue); });
        const zone = document.getElementById('vue'); zone.replaceChildren();
        ({ 'ce-soir': vueCeSoir, 'semaine': vueSemaine, 'recettes': vueRecettes })[vue](zone);
    }
    // Ce soir et Semaine vivent sur la page Dîners, Recettes sur la sienne
    function allerA(v) {
        if ((PAGE === 'recettes') !== (v === 'recettes')) {
            if (v === 'recettes') location.href = 'recettes'; else location.href = 'diners#' + v;
            return;
        }
        vue = v; afficher();
    }
    document.querySelectorAll('nav.vues button').forEach(function (b) {
        b.addEventListener('click', function () { vue = b.dataset.vue; afficher(); try { history.replaceState(null, '', '#' + vue); } catch (e) {} });
    });
    const VUES = PAGE === 'recettes' ? ['recettes'] : ['ce-soir', 'semaine'];
    const VERS_RECETTES = ['recettes', 'carnet', 'a-tester'];                    // liens et favoris d'avant la page Recettes
    function vueDuLien() { const h = location.hash.slice(1); return VUES.indexOf(h) >= 0 ? h : null; }
    if (PAGE === 'diners' && VERS_RECETTES.indexOf(location.hash.slice(1)) >= 0) { location.replace('recettes'); return; }
    if (vueDuLien()) vue = vueDuLien();
    window.addEventListener('hashchange', function () { if (vueDuLien()) { vue = vueDuLien(); afficher(); } });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && ouverte) fermer(); });
    document.addEventListener('visibilitychange', function () {
        if (document.hidden) return;
        if (ouverte && !ouverte.edition) verrouiller();    // le verrou tombe quand l'onglet passe en arrière-plan
        charger();
    });
    document.addEventListener('file-videe', charger);
    charger();
})();
"""


def diners_en_html(page="diners"):
    """La page Dîners (Ce soir · Semaine) ou Recettes (page="recettes") : une coquille, remplie par le script depuis
    api/diners (copie gardée hors ligne). Même script ; la page choisit la vue de départ."""
    import json
    from prix_paris import PRIX
    genres = json.dumps(GENRES, ensure_ascii=False)
    prix = json.dumps(PRIX, ensure_ascii=False)
    reperes = "".join(svg.replace("<svg ", f'<svg data-icone="{cle}" ', 1) for cle, svg in ICONES_REPERE.items())
    titre = "Recettes" if page == "recettes" else "Dîners"
    vues = ("" if page == "recettes" else
            '<nav class="vues">' + "".join(f'<button type="button" data-vue="{v}">{t}</button>'
                                           for v, t in [("ce-soir", "Ce soir"), ("semaine", "Semaine")]) + "</nav>")
    return f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{titre} · Casa Binomerie</title>
{TETE_PWA}
{TETE_POLICE}
<style>{STYLE_D}{STYLE_NAV_HUB}{STYLE_COURSES}{STYLE_DINERS}</style>
</head>
<body class="accueil hub-page diners" data-page="{page}">
{onglets_cucina(page)}
<div id="hors-ligne" hidden></div>
{vues}
<div id="vue" class="vue"><p class="vide-courses">Chargement des recettes…</p></div>
<div class="panneau" id="panneau" hidden><div class="contenu"></div></div>
{nav_hub(page)}
<template id="reperes">{reperes}</template>
<script type="application/json" id="genres">{genres}</script>
<script type="application/json" id="prix">{prix}</script>
<script>{SCRIPT_FILE}
window.addEventListener('online', function () {{ majHorsLigne(); viderFile(); }});
window.addEventListener('offline', majHorsLigne);
majHorsLigne();
viderFile();
</script>
<script>{SCRIPT_DINERS}</script>
</body>
</html>"""
