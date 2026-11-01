"""Casa Binomerie — Dîners : le carnet de recettes, la semaine, le secours et le compteur Deliveroo.

- plats : le carnet (statut 'carnet') et les envies du Match des Recettes ('a-tester'). Un plat à
  tester passe au carnet quand un repas où on l'a prévu est marqué « fait maison » (db.enregistrer_repas).
- repas : un dîner par jour, un déjeuner ou un brunch à la demande — plusieurs plats, et ce qui s'est vraiment
  passé (fait, commandé, dehors, autre). Le dîner est la mesure du succès : ≤ 1 commande par semaine
  (départ : 3, le 28/10/2026).
- Secours : les plats ≤ SECOURS_MINUTES dont tout est au placard ; « presque » : il en manque 1 ou 2.
Les noms d'ingrédients se comparent normalisés, comme les courses (courses.normaliser).
"""
import re
from datetime import date, timedelta

from courses import normaliser, STYLE_COURSES
from design import STYLE_D, STYLE_NAV_HUB, TETE_POLICE, nav_hub
from pwa import TETE_PWA, SCRIPT_FILE

_ID = re.compile(r"[A-Za-z0-9-]{8,64}")

GENRES = [("plat", "Plats"), ("accompagnement", "Accompagnements"), ("entree", "Entrées"), ("dessert", "Desserts")]
STATUTS = ("carnet", "a-tester")
POUR = [("nous", "Nous deux"), ("julien", "Julien"), ("laetitia", "Laetitia")]
ISSUES = [("fait", "Fait maison"), ("commande", "Commandé"), ("dehors", "Dehors"), ("autre", "Autre")]
MOMENTS = [("diner", "Dîner"), ("dejeuner", "Déjeuner"), ("brunch", "Brunch")]
ORDRE_GENRES = ("entree", "plat", "accompagnement", "dessert")
MAX_PLATS = 8
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
    return p


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
    if corps.get("moment") not in dict(MOMENTS):
        raise ValueError("moment invalide")
    plats = corps.get("plats") or []
    if (not isinstance(plats, list) or len(plats) > MAX_PLATS
            or not all(isinstance(i, str) and _ID.fullmatch(i) for i in plats)):
        raise ValueError("plats invalides")
    if len(set(plats)) != len(plats):
        raise ValueError("plat en double")
    issue = corps.get("issue") or None
    if issue is not None and issue not in dict(ISSUES):
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


def disponibles(placard, courses=()):
    """Les clés de ce qu'on a : le placard en stock (bientôt fini compris) et le frais habituel rangé
    ou déjà dans le panier (un habituel sur la liste à prendre, c'est qu'il en manque)."""
    return ({p["cle"] for p in placard if p["en_stock"]}
            | {normaliser(a["nom"]) for a in courses if a["recurrent"] and (not a["actif"] or a["pris"])})


def secours(plats, placard, courses=()):
    """(faisables, presque) : plats du carnet ≤ SECOURS_MINUTES, tout disponible / 1-2 manquants."""
    stock = disponibles(placard, courses)
    faisables, presque = [], []
    candidats = sorted((p for p in plats if p["genre"] == "plat" and p["statut"] == "carnet" and not p["archive"]
                        and p["minutes"] <= SECOURS_MINUTES and p["ingredients"]),
                       key=lambda p: (p["minutes"], p["nom"]))
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


def proposer(plats, repas, jours, aujourd_hui, remplacer=(), cible=CIBLE_SOIRS, hasard=None):
    """{jour: id du plat} pour compléter la semaine jusqu'à `cible` dîners prévus.

    Dîners libres seulement (ni plat ni issue), vendredi et samedi en dernier recours (souvent dehors), répartis
    dans la semaine. Plats pour nous deux, avec recette ; rapides (≤ 45 min) du lundi au jeudi ; ni déjà prévus
    (tous moments), ni mangés ces 14 derniers jours ; un plat à tester s'il n'y en a pas déjà un. `remplacer` :
    des jours à tirer au sort de nouveau, avec un autre plat. Déjeuners et brunchs ne remplissent pas un soir."""
    from random import Random
    hasard = hasard or Random()
    remplacer = [j for j in remplacer if j in jours]
    diners = {r["jour"]: r for r in repas if r["moment"] == "diner"}
    prevus = {j: diners[j]["plats"] for j in jours if j in diners and diners[j]["plats"] and j not in remplacer}
    besoin = max(0, cible - len(prevus))
    libres = [j for j in jours if j not in prevus and j not in remplacer
              and not (j in diners and diners[j]["issue"])]
    preferes = [j for j in libres if j.weekday() not in (4, 5)]
    autres = [j for j in libres if j.weekday() in (4, 5)]
    a_remplir = remplacer[:besoin]
    reste = besoin - len(a_remplir)
    if reste > 0:
        if len(preferes) > reste:                       # répartis : au milieu de chaque tranche, pas d'affilée
            a_remplir += [preferes[(2 * i + 1) * len(preferes) // (2 * reste)] for i in range(reste)]
        else:
            a_remplir += preferes + autres[:reste - len(preferes)]
    if not a_remplir:
        return {}

    manges = {i for r in repas if r["issue"] == "fait" and 0 <= (aujourd_hui - r["jour"]).days < RECENT
              for i in r["plats"]}
    deja = {i for r in repas if r["jour"] in jours and r["jour"] not in remplacer for i in r["plats"]}
    exclus = deja | manges | {i for j in remplacer if j in diners for i in diners[j]["plats"]}
    candidats = [p for p in plats if p["genre"] == "plat" and not p["archive"] and p.get("pour", "nous") == "nous"
                 and p["recette"] and p["id"] not in exclus]
    hasard.shuffle(candidats)
    a_tester = any(p["statut"] == "a-tester" for p in plats if p["id"] in deja)
    choix = {}
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


# --- Page ---------------------------------------------------------------------------------------

STYLE_DINERS = """
body.diners { --rubrique: var(--diners); --rubrique-doux: var(--diners-doux); }
nav.vues { display: grid; grid-template-columns: repeat(4, 1fr); gap: 4px; background: var(--carte); border-radius: 18px;
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
span.badge.julien { color: var(--doux); background: var(--carte); border: 1px solid var(--ligne); }
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
button.retirer { border: none; background: var(--carte); color: var(--doux); border-radius: 999px; width: 36px; height: 36px;
                 font-size: 18px; font-weight: 800; flex: none; }
div.ajouts { display: flex; gap: 6px; flex-wrap: wrap; }
div.ajouts button.petit { padding: 6px 10px; }
ul.plats-soir { list-style: none; margin: 4px 0 0; padding: 0; display: flex; flex-direction: column; gap: 6px; }
ul.plats-soir li { display: flex; justify-content: space-between; align-items: center; gap: 8px; font-size: 15px; font-weight: 600; }
ul.plats-soir button { padding: 6px 12px !important; font-size: 13px !important; }
div.proposer { display: flex; gap: 8px; flex-wrap: wrap; }
div.proposer button.plein { flex: 1 1 220px; }
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
    let vue = 'ce-soir', filtre = 'tout', recherche = '';
    const etiquette = { carnet: 'tout', 'a-tester': 'tout', choix: 'nous' };   // un filtre par liste ; un soir : à deux
    let derniereProposition = {};                         // {jour: plat} : ce que « Reproposer » peut changer
    let messageSemaine = '';
    const ETIQUETTES = [['tout', 'Tout'], ['rapide', 'Rapide'], ['nous', 'Nous deux'], ['julien', 'Julien'], ['laetitia', 'Laetitia'],
                        ['air-fryer', 'Air fryer'], ['poisson', 'Poisson'], ['legumes', 'Légumes']];
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
        if (e === 'rapide') return p.minutes <= 20;
        if (e === 'nous' || e === 'julien' || e === 'laetitia') return (p.pour || 'nous') === e;
        if (e === 'air-fryer') return /air fryer/i.test(p.nom);
        if (e === 'poisson') return p.ingredients.some(function (i) {
            const n = normaliser(i); return n.indexOf('sauce') !== 0 && MER.some(function (m) { return n.indexOf(m) >= 0; }); });
        if (e === 'legumes') return p.id.indexOf('lg-') === 0 || (p.id.indexOf('af-') === 0 && p.genre === 'accompagnement');
        return true;
    }
    function correspond(p, q) {
        return !q || normaliser(p.nom).indexOf(q) >= 0 || p.ingredients.some(function (i) { return normaliser(i).indexOf(q) >= 0; });
    }
    // Les étiquettes d'une liste, avec leur nombre ; celles qui ne trouvent rien sont masquées
    function barreEtiquettes(contexte, liste, rafraichir) {
        const f = el('div', 'filtres etiquettes');
        ETIQUETTES.forEach(function (e) {
            const n = liste.filter(function (p) { return aEtiquette(p, e[0]); }).length;
            if (!n && e[0] !== 'tout' && etiquette[contexte] !== e[0]) return;
            const b = bouton(e[1], etiquette[contexte] === e[0] ? 'actif' : '', function () { etiquette[contexte] = e[0]; rafraichir(); });
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
            .catch(function () { try { d = d || JSON.parse(localStorage.getItem(CLE_COPIE)); } catch (e) {} if (d) afficher(); });
    }
    function enregistrerRepas(r) {
        const vide = !r.plats.length && !r.issue;
        d.repas = d.repas.filter(function (x) { return !(x.jour === r.jour && x.moment === r.moment); }).concat(vide ? [] : [r]);
        garder(); afficher();
        envoyer({ url: 'api/repas', methode: 'POST', corps: r, cle: 'repas:' + r.jour + ':' + r.moment }).then(relire, relire);
    }
    function ajouterPlat(iso, moment, id) {
        const r = repas(iso, moment);
        if (r.plats.indexOf(id) >= 0 || r.plats.length >= 8) return;
        enregistrerRepas(Object.assign({}, r, { plats: r.plats.concat([id]) }));
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
    function lignePlat(p, extra) {
        const li = el('li');
        const o = bouton('', 'ouvrir', function () { ouvrirFiche(p.id); });
        const nom = el('span', 'nom', p.nom);
        if (d.secours.faisables.indexOf(p.id) >= 0) nom.append(el('span', 'badge', 'secours'));
        if (p.pour === 'julien') nom.append(el('span', 'badge julien', 'Julien'));
        if (p.pour === 'laetitia') nom.append(el('span', 'badge julien', 'Laetitia'));
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
            b.append(bouton('Changer', 'discret', function () { vue = 'semaine'; afficher(); }));
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
    // « Proposer ma semaine » : le serveur complète jusqu'à 4 soirs (diners.proposer) ; « Reproposer » ne
    // change que les soirs qu'il a proposés et qu'on n'a pas modifiés depuis
    function proposerSemaine(msg, remplacer) {
        msg.textContent = 'Je cherche…';
        chaine.then(function () {
            return fetch('api/diners/proposer', { method: 'POST', headers: { 'Content-Type': 'application/json' },
                                                  body: JSON.stringify({ remplacer: remplacer || [] }) });
        }).then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
          .then(function (r) {
              const jours = Object.keys(r.proposes);
              jours.forEach(function (iso) {
                  d.repas = d.repas.filter(function (x) { return !(x.jour === iso && x.moment === 'diner'); })
                                   .concat([{ jour: iso, moment: 'diner', plats: [r.proposes[iso]], issue: null }]);
              });
              derniereProposition = remplacer && remplacer.length ? Object.assign({}, derniereProposition, r.proposes) : r.proposes;
              garder(); afficher();
              messageSemaine = jours.length ? jours.length + ' dîner(s) proposé(s). Ajoute un accompagnement ou un dessert, puis envoie aux courses.'
                                            : 'Rien à proposer : la semaine a déjà quatre dîners, ou aucun plat ne convient.';
              afficher(); relire();
          }, function () { msg.textContent = 'Pas de réseau : réessaie une fois connecté.'; });
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
        ranges(r).forEach(function (p) {
            const li = el('li');
            const o = bouton('', 'ouvrir', function () { ouvrirFiche(p.id); });
            o.append(el('span', 'nom', p.nom), el('span', 'meta', NOMS_GENRE[p.genre] + ' · ' + duree(p.minutes)));
            const x = bouton('×', 'retirer', function () { retirerPlat(iso, moment, p.id); });
            x.setAttribute('aria-label', 'Retirer ' + p.nom);
            li.append(o, x);
            ul.append(li);
        });
        if (!ul.children.length) ul.append(el('li', 'meta', 'Libre'));
        c.append(ul);
        const a = el('div', 'ajouts');
        AJOUTS.forEach(function (g) { a.append(bouton(g[1], 'petit', function () { ouvrirChoix(iso, moment, g[0]); })); });
        c.append(a);
        return c;
    }
    function vueSemaine(zone) {
        const e = el('div', 'encart');
        e.append(el('h2', '', 'La semaine'), el('p', 'aide', 'Trois ou quatre dîners suffisent. Les autres restent libres.'));
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
                        bouton('Brunch', 'petit', function () { ouvrirChoix(iso, 'brunch', 'plat'); }));
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
        prop.append(bouton('Proposer ma semaine', 'plein', function () { proposerSemaine(msgP, []); }));
        const aRefaire = Object.keys(derniereProposition).filter(function (iso) {
            const r = repas(iso, 'diner'); return r.plats.length === 1 && r.plats[0] === derniereProposition[iso]; });
        if (aRefaire.length) prop.append(bouton('Reproposer', 'petit', function () { proposerSemaine(msgP, aRefaire); }));
        zone.append(prop, msgP, e);
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
    function vueCarnet(zone) {
        const r = el('input', 'recherche'); r.type = 'search'; r.placeholder = 'Chercher un plat ou un ingrédient';
        r.value = recherche; r.setAttribute('aria-label', 'Chercher');
        const f = el('div', 'filtres');
        [['tout', 'Tout']].concat(GENRES).forEach(function (g) {
            const b = bouton(g[1], filtre === g[0] ? 'actif' : '', function () { filtre = g[0]; afficher(); });
            f.append(b);
        });
        const ul = el('ul', 'plats');
        const carnet = d.plats.filter(function (p) { return p.statut === 'carnet' && !p.archive; });
        const zoneEtiquettes = el('div');
        function remplir() {
            ul.replaceChildren();
            const q = normaliser(recherche);
            const parGenre = carnet.filter(function (p) { return (filtre === 'tout' || p.genre === filtre) && correspond(p, q); });
            zoneEtiquettes.replaceChildren(barreEtiquettes('carnet', parGenre, remplir));
            parGenre.filter(function (p) { return aEtiquette(p, etiquette.carnet); })
              .sort(function (a, b) { return a.nom.localeCompare(b.nom, 'fr'); })
              .forEach(function (p) { ul.append(lignePlat(p)); });
            if (!ul.children.length) ul.append(el('li', 'meta', 'Aucune recette ne correspond.'));
        }
        r.addEventListener('input', function () { recherche = r.value; remplir(); });
        remplir();
        const e = el('div', 'encart'); e.append(ul);
        zone.append(r, f, zoneEtiquettes, bouton('+ Nouvelle recette', 'plein', function () { ouvrirEdition(null); }), e);
    }
    function vueATester(zone) {
        const tous = d.plats.filter(function (p) { return p.statut === 'a-tester' && !p.archive; });
        const r = el('input', 'recherche'); r.type = 'search'; r.placeholder = 'Chercher un plat ou un ingrédient';
        r.value = recherche; r.setAttribute('aria-label', 'Chercher');
        const f = el('div', 'filtres');
        [['tout', 'Tout']].concat(GENRES).forEach(function (g) {
            f.append(bouton(g[1], filtre === g[0] ? 'actif' : '', function () { filtre = g[0]; afficher(); }));
        });
        const e = el('div', 'encart');
        e.append(el('h2', '', 'À tester'),
                 el('p', 'aide', 'Prévoyez-en un dans la semaine : une fois fait maison, il rejoint le carnet.'));
        const zoneEtiquettes = el('div');
        const ul = el('ul', 'plats');
        function remplir() {
            ul.replaceChildren();
            const q = normaliser(recherche);
            const parGenre = tous.filter(function (p) { return (filtre === 'tout' || p.genre === filtre) && correspond(p, q); });
            zoneEtiquettes.replaceChildren(barreEtiquettes('a-tester', parGenre, remplir));
            parGenre.filter(function (p) { return aEtiquette(p, etiquette['a-tester']); })
                .sort(function (a, b) { return (b.recette ? 1 : 0) - (a.recette ? 1 : 0) || a.nom.localeCompare(b.nom, 'fr'); })
                .forEach(function (p) { ul.append(lignePlat(p, p.recette ? undefined : 'recette à écrire')); });
            if (!ul.children.length) ul.append(el('li', 'meta', 'Aucune recette ne correspond.'));
        }
        r.addEventListener('input', function () { recherche = r.value; remplir(); });
        remplir();
        e.append(ul);
        zone.append(r, f, zoneEtiquettes, e);
    }

    // Ajouter un plat d'un genre à un repas : la même recherche et les mêmes étiquettes, carnet d'abord
    function ouvrirChoix(iso, moment, genre) {
        ouverte = { id: null, edition: false };
        const c = document.querySelector('#panneau .contenu'); c.replaceChildren();
        const haut = el('div', 'haut');
        const quand = iso === d.aujourd_hui ? (moment === 'diner' ? 'ce soir' : 'aujourd\\'hui') : enClair(iso);
        haut.append(el('h2', '', MOMENTS[moment] + ' · ' + quand + ' · ' + NOMS_GENRE[genre].toLowerCase()), bouton('Fermer', 'petit', fermer));
        let q = '';
        const r = el('input', 'recherche'); r.type = 'search'; r.placeholder = 'Chercher un plat ou un ingrédient';
        r.setAttribute('aria-label', 'Chercher');
        const zoneEtiquettes = el('div'), listes = el('div', 'vue');
        const tous = d.plats.filter(function (p) { return p.genre === genre && !p.archive; });
        let affiches = [];
        // Au hasard : parmi les plats affichés (recherche et filtre compris), hors ceux déjà prévus cette semaine
        const hasard = bouton('Au hasard', 'plein', function () {
            const deja = platsDeLaSemaine();
            const pool = affiches.filter(function (p) { return deja.indexOf(p.id) < 0; });
            if (!pool.length) { hasard.textContent = 'Rien à tirer avec ces filtres'; return; }
            const p = pool[Math.floor(Math.random() * pool.length)];
            ajouterPlat(iso, moment, p.id); fermer();
        });
        function remplir() {
            const trouves = tous.filter(function (p) { return correspond(p, normaliser(q)); });
            affiches = trouves.filter(function (p) { return aEtiquette(p, etiquette.choix); });
            hasard.textContent = 'Au hasard parmi ' + affiches.length;
            zoneEtiquettes.replaceChildren(barreEtiquettes('choix', trouves, remplir));
            listes.replaceChildren();
            [['carnet', 'Carnet'], ['a-tester', 'À tester']].forEach(function (g) {
                const ul = el('ul', 'plats');
                trouves.filter(function (p) { return p.statut === g[0] && aEtiquette(p, etiquette.choix); })
                    .sort(function (a, b) { return a.nom.localeCompare(b.nom, 'fr'); })
                    .forEach(function (p) {
                        const li = lignePlat(p);
                        li.querySelector('button.ouvrir').replaceWith(li.querySelector('button.ouvrir').cloneNode(true));
                        li.querySelector('button.ouvrir').addEventListener('click', function () { ajouterPlat(iso, moment, p.id); fermer(); });
                        ul.append(li);
                    });
                if (!ul.children.length) return;
                const e = el('div', 'encart'); e.append(el('h2', '', g[1]), ul); listes.append(e);
            });
            if (!listes.children.length) listes.append(el('p', 'aide', 'Aucune recette ne correspond.'));
        }
        r.addEventListener('input', function () { q = r.value; remplir(); });
        remplir();
        c.append(haut, hasard, r, zoneEtiquettes);
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
    function ouvrirFiche(id) {
        const p = plat(id); if (!p) return;
        ouverte = { id: id, edition: false };
        const c = document.querySelector('#panneau .contenu'); c.replaceChildren();
        const haut = el('div', 'haut');
        haut.append(el('span', 'meta', NOMS_GENRE[p.genre] + ' · ' + duree(p.minutes)), bouton('Fermer', 'petit', fermer));
        c.append(haut, el('h2', '', p.nom));
        if (p.lien) { const m = el('p', 'meta'); const a = el('a', '', 'Recette d\\'origine'); a.href = p.lien; a.target = '_blank'; a.rel = 'noopener'; m.append(a); c.append(m); }
        const groupes = [['ok', 'Au placard', p.ingredients.filter(enStock)],
                         ['liste', 'Déjà sur la liste', p.ingredients.filter(function (i) { return !enStock(i) && surLaListe(i); })],
                         ['manque', 'À acheter', p.ingredients.filter(function (i) { return !enStock(i) && !surLaListe(i); })]];
        groupes.forEach(function (g) {
            if (!g[2].length) return;
            const sec = el('section', 'groupe-ing'), ing = el('div', 'ingredients');
            g[2].forEach(function (i) {
                const t = el('span', g[0], i), pr = prixDe(i);
                if (g[0] === 'manque' && pr) t.append(el('small', '', euros(pr[1])));
                ing.append(t);
            });
            sec.append(el('h3', '', g[1] + ' · ' + g[2].length), ing);
            c.append(sec);
        });
        if (p.cout) c.append(el('p', 'meta', '≈ ' + euros(p.cout) + ' le repas pour deux (part utilisée de chaque produit) · en livraison ≈ ' + euros(d.livraison)));
        c.append(el('pre', 'recette', p.recette || 'Recette à écrire : demande à Claude, ou écris la tienne avec « Modifier ».'));
        if (p.note) c.append(el('p', 'meta', p.note));
        const act = el('div', 'actions');
        act.append(bouton('Ce soir', 'plein', function () { ajouterPlat(d.aujourd_hui, 'diner', p.id); fermer(); vue = 'ce-soir'; afficher(); }),
                   bouton('Modifier', 'petit', function () { ouvrirEdition(p.id); }));
        const manquants = p.ingredients.filter(function (i) { return !enStock(i) && !surLaListe(i); });
        const total = manquants.reduce(function (t, i) { const pr = prixDe(i); return t + (pr ? pr[1] : 0); }, 0);
        if (manquants.length) act.append(bouton('Ajouter les ' + manquants.length + ' manquants aux courses' + (total ? ' (≈ ' + euros(total) + ')' : ''), 'petit', function (ev) {
            ajouterAuxCourses(manquants, 'plat:' + p.id);
            d.liste = (d.liste || []).concat(manquants.map(normaliser)); garder();
            ev.target.textContent = 'Ajouté aux courses'; ev.target.disabled = true; }));
        if (p.statut === 'a-tester') act.append(bouton('On l\\'a fait : au carnet', 'petit', function () {
            enregistrerPlat(Object.assign({}, p, { statut: 'carnet' })); fermer(); }));
        c.append(act);
        document.getElementById('panneau').hidden = false;
        document.getElementById('panneau').scrollTop = 0;
        verrouiller();                                     // l'écran reste allumé pendant qu'on cuisine
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
        if (id) act.append(bouton(p.archive ? 'Remettre au carnet' : 'Retirer du carnet', 'petit', function () {
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
        ({ 'ce-soir': vueCeSoir, 'semaine': vueSemaine, 'carnet': vueCarnet, 'a-tester': vueATester })[vue](zone);
    }
    document.querySelectorAll('nav.vues button').forEach(function (b) {
        b.addEventListener('click', function () { vue = b.dataset.vue; afficher(); try { history.replaceState(null, '', '#' + vue); } catch (e) {} });
    });
    const VUES = ['ce-soir', 'semaine', 'carnet', 'a-tester'];
    if (VUES.indexOf(location.hash.slice(1)) >= 0) vue = location.hash.slice(1);
    window.addEventListener('hashchange', function () {
        if (VUES.indexOf(location.hash.slice(1)) >= 0) { vue = location.hash.slice(1); afficher(); }
    });
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


def diners_en_html():
    """La page Dîners : une coquille, remplie par le script depuis api/diners (copie gardée hors ligne)."""
    import json
    from prix_paris import PRIX
    genres = json.dumps(GENRES, ensure_ascii=False)
    prix = json.dumps(PRIX, ensure_ascii=False)
    vues = "".join(f'<button type="button" data-vue="{v}">{t}</button>'
                   for v, t in [("ce-soir", "Ce soir"), ("semaine", "Semaine"), ("carnet", "Carnet"), ("a-tester", "À tester")])
    return f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Dîners · Casa Binomerie</title>
{TETE_PWA}
{TETE_POLICE}
<style>{STYLE_D}{STYLE_NAV_HUB}{STYLE_COURSES}{STYLE_DINERS}</style>
</head>
<body class="accueil hub-page diners">
<h1>Dîners</h1>
<div id="hors-ligne" hidden></div>
<nav class="vues">{vues}</nav>
<div id="vue" class="vue"><p class="vide-courses">Chargement du carnet…</p></div>
<div class="panneau" id="panneau" hidden><div class="contenu"></div></div>
{nav_hub("diners")}
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
