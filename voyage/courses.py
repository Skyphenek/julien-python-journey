"""Casa Binomerie — Courses : la liste partagée (par rayon) et le placard des basiques.

- Un article est « actif » tant qu'il est dans la liste ; coché, il est « pris » (barré) jusqu'à
  « Vider les pris » : supprimé, sauf s'il est récurrent — il passe alors dans les Habituels
  (actif = false), d'où il revient d'un tap.
- Le placard : ce qui dure, rangé par zone de la cuisine (ZONES). En stock -> bientôt fini -> épuisé ;
  bientôt fini ou épuisé -> part dans les courses ; pris en magasin -> de nouveau en stock
  (db.enregistrer_article). Le frais à rotation hebdomadaire est un habituel des courses, pas un
  élément du placard. Les noms se comparent normalisés (casse, accents).
"""
import json
import re
import unicodedata

from design import STYLE_D, STYLE_NAV_HUB, TETE_POLICE, nav_hub
from pwa import TETE_PWA, SCRIPT_FILE

_ID = re.compile(r"[A-Za-z0-9-]{8,64}")

# Dans l'ordre d'un parcours de supermarché
RAYONS = [
    ("fruits-legumes", "Fruits et légumes"),
    ("frais", "Frais"),
    ("boucherie", "Boucherie"),
    ("boulangerie", "Boulangerie"),
    ("epicerie", "Épicerie"),
    ("surgeles", "Surgelés"),
    ("boissons", "Boissons"),
    ("specialise", "Épiceries spécialisées"),
    ("hygiene-maison", "Hygiène et maison"),
    ("autre", "Autre"),
]

# Début de mot -> rayon ; le mot le plus long qui correspond gagne (« tomates pelées » > « tomate »)
MOTS_RAYON = {
    "fruits-legumes": ["tomate", "pomme", "pommes de terre", "citron", "oignon", "ail", "echalote", "carotte",
                       "courgette", "salade", "concombre", "avocat", "banane", "orange", "poivron", "champignon",
                       "herbes", "persil", "basilic", "menthe", "aneth", "gingembre", "poireau", "fraise", "raisin"],
    "frais": ["lait", "creme", "oeuf", "beurre", "yaourt", "fromage", "pecorino", "parmesan", "mozzarella",
              "comte", "emmental", "cheddar", "feta", "ricotta", "mascarpone", "jambon", "lardon", "guanciale",
              "pancetta", "bacon", "chorizo", "saucisson"],
    "boucherie": ["steak", "boeuf", "veau", "poulet", "porc", "agneau", "viande", "hache", "roti", "cote",
                  "entrecote", "saucisse", "dinde", "piece du boucher"],
    "boulangerie": ["pain", "baguette", "brioche", "croissant"],
    "epicerie": ["pates", "spaghetti", "rigatoni", "penne", "lasagne", "riz", "farine", "sucre", "sel", "poivre",
                 "huile", "vinaigre", "moutarde", "bouillon", "tomates pelees", "passata", "coulis", "concentre",
                 "thon", "mais", "pois chiches", "lentilles", "haricots", "conserve", "tortilla", "epices",
                 "cumin", "paprika", "chocolat", "cafe", "the", "boudoirs", "biscuit", "cereales", "confiture",
                 "miel", "levure", "chapelure", "mayonnaise", "ketchup", "sauce"],
    "surgeles": ["surgel", "glace", "frites"],
    "boissons": ["eau", "eau volvic", "eau gazeuse", "eau petillante", "eau minerale", "volvic", "evian", "badoit",
                 "perrier", "vin", "biere", "jus", "soda", "coca", "sirop", "champagne", "cidre"],
    "hygiene-maison": ["papier", "essuie", "sopalin", "liquide vaisselle", "vaisselle", "lessive", "eponge",
                       "sac poubelle", "sacs poubelle", "dentifrice", "shampoing", "savon", "gel douche",
                       "deodorant", "coton", "mouchoir", "litiere", "croquettes", "pâtée"],
}
_MOTS = sorted(((mot, rayon) for rayon, mots in MOTS_RAYON.items() for mot in mots), key=lambda m: -len(m[0]))

# Le placard se range comme la cuisine : on en fait l'inventaire une zone à la fois
ZONES = [
    ("frigo", "Frigo"),
    ("placard-sec", "Placard sec"),
    ("epices", "Épices et condiments"),
    ("congelateur", "Congélateur"),
    ("cave", "Cave"),
]
# Début de mot -> zone Épices et condiments (huiles, vinaigres et sauces compris)
MOTS_EPICES = ["epice", "cumin", "paprika", "piment", "curry", "curcuma", "garam masala", "ras el", "cannelle",
               "muscade", "girofle", "cinq-epices", "badiane", "anis", "chipotle", "graines", "sumac", "vanille",
               "laurier", "thym", "origan", "romarin", "herbes de provence", "sel", "gros sel", "fleur de sel",
               "poivre", "moutarde", "vinaigre", "huile", "sauce", "nuoc", "mirin", "miso", "harissa", "tahini",
               "ketchup", "mayonnaise", "worcestershire", "capres", "cornichons", "miel", "sirop", "pate de curry",
               "tabasco", "sriracha", "sambal"]
_RAYON_ZONE = {"surgeles": "congelateur", "boissons": "cave", "frais": "frigo", "boucherie": "frigo"}

# Le placard de départ (plein de courses du 31/10/2026) : ce qui rend 5 dîners possibles sans courses
PLACARD_DEPART = [
    # placard
    "spaghetti", "rigatoni", "tomates pelées", "passata", "huile d'olive", "vinaigre", "moutarde", "sel",
    "poivre en grains", "bouillon", "ail", "oignons", "échalotes", "pommes de terre", "tortillas",
    "épices tacos", "farine", "sucre", "chocolat noir", "café", "boudoirs", "thon", "maïs", "pois chiches",
    # frigo
    "œufs", "beurre", "pecorino", "parmesan", "guanciale ou pancetta", "jambon", "crème fraîche", "lait",
    "yaourt grec", "citrons", "comté", "beaufort", "mozzarella",
    # congélateur
    "demi-baguettes", "pains burger", "steaks hachés", "bacon", "mozzarella râpée", "petits pois surgelés",
    "épinards surgelés", "herbes surgelées",
]


def normaliser(nom):
    """« Crème  Fraîche » -> « creme fraiche » : la clé de comparaison des noms (courses, placard, plats)."""
    nom = nom.strip().lower().replace("œ", "oe").replace("æ", "ae")
    nom = "".join(c for c in unicodedata.normalize("NFD", nom) if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", nom)


def deviner_rayon(nom):
    """Le rayon d'un article d'après ses mots ; « surgelé » l'emporte toujours ; 'autre' sinon."""
    n = normaliser(nom)
    if re.search(r"(?<![a-z])surgel", n):
        return "surgeles"
    for mot, rayon in _MOTS:
        if re.search(r"(?<![a-z])" + re.escape(normaliser(mot)), n):
            return rayon
    if any(re.search(r"(?<![a-z])" + re.escape(mot), n) for mot in MOTS_EPICES + ["cassonade", "fecule"]):
        return "epicerie"                                  # épices et condiments : au rayon épicerie
    return "autre"


def deviner_zone(nom, rayon=None):
    """La zone d'un élément du placard : surgelé -> congélateur, épices et condiments par mots, puis le rayon."""
    rayon = rayon or deviner_rayon(nom)
    if rayon == "surgeles":
        return "congelateur"
    n = normaliser(nom)
    if any(re.search(r"(?<![a-z])" + re.escape(mot), n) for mot in MOTS_EPICES):
        return "epices"
    return _RAYON_ZONE.get(rayon, "placard-sec")


# --- Validation : tout ce qui vient du téléphone est vérifié ----------------------------------

def _texte(corps, cle, maximum):
    valeur = corps.get(cle) or ""
    if not isinstance(valeur, str):
        raise ValueError(f"{cle} invalide")
    valeur = valeur.strip()
    if len(valeur) > maximum:
        raise ValueError(f"{cle} trop long")
    return valeur


def _booleen(corps, cle, defaut):
    valeur = corps.get(cle, defaut)
    if not isinstance(valeur, bool):
        raise ValueError(f"{cle} invalide")
    return valeur


def valider_article(corps):
    """Un article de la liste. Sans rayon : deviné d'après le nom."""
    if not isinstance(corps, dict):
        raise ValueError("article invalide")
    identifiant = corps.get("id")
    if not isinstance(identifiant, str) or not _ID.fullmatch(identifiant):
        raise ValueError("id invalide")
    nom = _texte(corps, "nom", 80)
    if not nom:
        raise ValueError("nom manquant")
    rayon = corps.get("rayon") or deviner_rayon(nom)
    if rayon not in dict(RAYONS):
        raise ValueError("rayon invalide")
    return {"id": identifiant, "nom": nom, "rayon": rayon, "pris": _booleen(corps, "pris", False),
            "recurrent": _booleen(corps, "recurrent", False), "actif": _booleen(corps, "actif", True),
            "source": _texte(corps, "source", 80)}


def valider_placard(corps):
    """Un élément du placard : {cle (nom normalisé), nom, en_stock, bientot, zone}. Sans zone : devinée.
    En stock, bientôt fini (en_stock et bientot) ou épuisé (pas en_stock)."""
    if not isinstance(corps, dict):
        raise ValueError("basique invalide")
    nom = _texte(corps, "nom", 80)
    if not nom:
        raise ValueError("nom manquant")
    zone = corps.get("zone") or deviner_zone(nom)
    if zone not in dict(ZONES):
        raise ValueError("zone invalide")
    return {"cle": normaliser(nom), "nom": nom, "en_stock": _booleen(corps, "en_stock", None),
            "bientot": _booleen(corps, "bientot", False), "zone": zone}


# --- Page ---------------------------------------------------------------------------------------

STYLE_COURSES = """
body.courses { --rubrique: var(--courses); --rubrique-doux: var(--courses-doux); }
body.courses h1 { margin-bottom: 4px; }
p.resume { color: var(--doux); font-weight: 700; margin: 0 0 16px; }
form#ajout-course { display: flex; gap: 8px; margin: 0 0 18px; position: sticky; top: 0; z-index: 5;
                    background: var(--fond); padding: 8px 0; }
form#ajout-course input { flex: 1; min-width: 0; font-size: 17px; padding: 12px 16px; border-radius: 999px;
                          border: 2px solid var(--ligne); background: var(--blanc); color: var(--texte); }
form#ajout-course button { border: none; border-radius: 999px; padding: 0 20px; font-weight: 800; font-size: 16px;
                           background: var(--courses); color: #ffffff; font-family: inherit; }
section.rayon { background: var(--carte); border-radius: 24px; padding: 14px 16px; margin: 0 0 12px; }
section.rayon h2 { font-size: 15px; font-weight: 800; color: var(--doux); margin: 0 0 6px; }
ul.articles { list-style: none; margin: 0; padding: 0; }
ul.articles li { display: flex; align-items: center; gap: 12px; min-height: 48px; border-top: 1px solid var(--ligne); }
ul.articles li:first-child { border-top: none; }
ul.articles input[type=checkbox] { width: 26px; height: 26px; accent-color: var(--courses); flex: none; }
ul.articles .nom { flex: 1; font-size: 17px; background: none; border: none; text-align: left; padding: 10px 0;
                   color: var(--texte); font-family: inherit; }
ul.articles li.pris .nom { text-decoration: line-through; color: var(--doux); }
ul.articles .recurrent { font-size: 12px; color: var(--courses); font-weight: 700; }
div.edition { display: flex; flex-wrap: wrap; gap: 8px; padding: 0 0 12px 38px; }
div.edition select, div.edition button { font-family: inherit; font-size: 14px; padding: 8px 12px; border-radius: 999px;
                                          border: 2px solid var(--ligne); background: var(--blanc); color: var(--texte); }
button#vider-pris { width: 100%; min-height: 48px; border-radius: 999px; border: 2px solid var(--ligne);
                    background: var(--blanc); color: var(--texte); font-weight: 800; font-family: inherit;
                    font-size: 15px; margin: 4px 0 20px; }
details.annexe { background: var(--carte); border-radius: 24px; padding: 14px 16px; margin: 0 0 12px; }
details.annexe summary { font-size: 17px; font-weight: 800; cursor: pointer; }
details.annexe p.aide { color: var(--doux); font-size: 14px; margin: 8px 0; }
div.puces-courses { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 10px; }
div.puces-courses button { font-family: inherit; font-size: 15px; padding: 8px 14px; border-radius: 999px;
                           border: 2px solid var(--ligne); background: var(--blanc); color: var(--texte); }
div.puces-courses button.epuise { border-color: var(--courses); background: var(--courses-doux); font-weight: 700; }
div.puces-courses button.bientot { border-color: var(--courses); border-style: dashed; }
div.puces-courses button.bientot::after { content: " · bientôt fini"; color: var(--courses); font-size: 13px; font-weight: 700; }
div.puces-courses button.epuise::after { content: " · épuisé"; color: var(--courses); font-size: 13px; }
section.zone-placard { border-top: 1px solid var(--ligne); margin-top: 12px; padding-top: 10px; }
section.zone-placard h3 { font-size: 15px; font-weight: 800; margin: 0; display: flex; justify-content: space-between; gap: 8px; }
section.zone-placard h3 span { color: var(--courses); font-size: 13px; font-weight: 700; }
div.edition-placard { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin-top: 10px; padding: 10px 12px;
                      border-radius: 16px; background: var(--courses-doux); }
div.edition-placard strong { flex-basis: 100%; }
div.edition-placard select, div.edition-placard button, form#ajout-placard select, form#ajout-placard input,
form#ajout-placard button, button#ranger { font-family: inherit; font-size: 14px; padding: 8px 12px; border-radius: 999px;
    border: 2px solid var(--ligne); background: var(--blanc); color: var(--texte); }
form#ajout-placard { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px; }
form#ajout-placard input { flex: 1 1 160px; min-width: 0; }
form#ajout-placard[hidden] { display: none; }
button#ranger { margin-top: 12px; font-weight: 700; }
p.vide-courses { background: var(--carte); border-radius: 24px; padding: 18px; color: var(--doux); }
div#hors-ligne { background: #fff4d6; color: #6b4e00; border-radius: 16px; padding: 10px 14px; margin: 0 0 12px;
                 font-weight: 600; font-size: 14px; }
@media (prefers-color-scheme: dark) { div#hors-ligne { background: #3d3214; color: #ffe08a; } }
"""

SCRIPT_COURSES = """
(function () {
    const RAYONS = JSON.parse(document.getElementById('rayons').textContent);
    const NOMS_RAYON = {};
    RAYONS.forEach(function (r) { NOMS_RAYON[r[0]] = r[1]; });
    const CLE_COPIE = 'courses:copie';
    const liste = document.getElementById('liste');
    const resume = document.getElementById('resume');
    const viderPris = document.getElementById('vider-pris');
    let articles = [], placard = [];
    const ZONES = JSON.parse(document.getElementById('zones').textContent);
    let ouvert = null;                                   // article en cours d'édition : pas de rafraîchissement
    let ranger = false, placardOuvert = null;            // mode « Ranger le placard » : zone, retrait, ajout

    function normaliser(nom) {
        return nom.trim().toLowerCase().replace(/œ/g, 'oe').replace(/æ/g, 'ae')
            .normalize('NFD').replace(/[\\u0300-\\u036f]/g, '').replace(/\\s+/g, ' ');
    }
    function nouvelId() {
        if (window.crypto && crypto.randomUUID) return crypto.randomUUID();
        return Date.now().toString(36) + '-' + Math.random().toString(36).slice(2, 10);
    }
    function el(balise, classe, texte) {
        const e = document.createElement(balise);
        if (classe) e.className = classe;
        if (texte !== undefined) e.textContent = texte;
        return e;
    }

    // Ce qui attend dans la file (hors ligne) passe par-dessus ce qui a été lu
    function avecAttente(lu) {
        const parId = {}, parCle = {};
        lu.articles.forEach(function (a) { parId[a.id] = a; });
        lu.placard.forEach(function (p) { parCle[p.cle] = p; });
        lireFile().forEach(function (f) {
            if (f.cle && f.cle.indexOf('article:') === 0) {
                if (f.methode === 'POST') parId[f.corps.id] = f.corps; else delete parId[f.cle.slice(8)];
            } else if (f.cle && f.cle.indexOf('placard:') === 0) {
                if (f.methode === 'DELETE') delete parCle[f.cle.slice(8)];
                else parCle[f.cle.slice(8)] = Object.assign({}, parCle[f.cle.slice(8)], f.corps, { cle: f.cle.slice(8) });
            }
        });
        return { articles: Object.keys(parId).map(function (k) { return parId[k]; }),
                 placard: Object.keys(parCle).map(function (k) { return parCle[k]; }) };
    }
    function garder() { try { localStorage.setItem(CLE_COPIE, JSON.stringify({ articles: articles, placard: placard })); } catch (e) {} }
    function appliquer(lu) { const r = avecAttente(lu); articles = r.articles; placard = r.placard; garder(); afficher(); }
    function charger() {
        if (ouvert || placardOuvert) return;
        fetch('api/courses', { headers: { 'X-Valise-Vite': '1' } })
            .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
            .then(appliquer)
            .catch(function () {
                try { appliquer(JSON.parse(localStorage.getItem(CLE_COPIE) || '{"articles":[],"placard":[]}')); } catch (e) {}
            });
    }

    // Un envoi à la fois (« lait, œufs, pain » = 3 envois) et une seule relecture à la fin :
    // le serveur n'a que 4 connexions à la base.
    let chaine = Promise.resolve(), minuteurRelire = null;
    function envoyer(envoi) {
        const p = chaine.then(function () { return envoyerOuGarder(envoi); });
        chaine = p.catch(function () {});
        return p;
    }
    function relire() { clearTimeout(minuteurRelire); minuteurRelire = setTimeout(charger, 400); }

    function enregistrer(article) {
        articles = articles.filter(function (a) { return a.id !== article.id; }).concat([article]);
        if (article.pris) {                                   // pris en magasin : de nouveau au placard
            placard.forEach(function (p) { if (p.cle === normaliser(article.nom)) { p.en_stock = true; p.bientot = false; } });
        }
        garder(); afficher();
        envoyer({ url: 'api/courses', methode: 'POST', corps: article, cle: 'article:' + article.id })
            .then(function (etat) { if (etat === 'ok') relire(); })    // le rayon deviné par le serveur
            .catch(relire);                                              // refusé : on relit la vérité
    }
    function supprimer(article) {
        articles = articles.filter(function (a) { return a.id !== article.id; });
        garder(); afficher();
        envoyer({ url: 'api/courses/' + encodeURIComponent(article.id), methode: 'DELETE', cle: 'article:' + article.id });
    }
    function ajouter(nom) {
        const cle = normaliser(nom);
        if (!cle) return;
        const deja = articles.find(function (a) { return normaliser(a.nom) === cle; });
        if (deja && deja.actif && !deja.pris) return;                      // déjà sur la liste
        if (deja) { enregistrer(Object.assign({}, deja, { actif: true, pris: false })); return; }   // un habituel
        enregistrer({ id: nouvelId(), nom: nom.trim(), rayon: '', pris: false, recurrent: false, actif: true, source: '' });
    }
    function enregistrerPlacard(p) {
        placard = placard.filter(function (x) { return x.cle !== p.cle; }).concat([p]);
        garder();
        envoyer({ url: 'api/placard', methode: 'POST', cle: 'placard:' + p.cle,
                  corps: { nom: p.nom, en_stock: p.en_stock, bientot: p.bientot, zone: p.zone } })
            .then(function (etat) { if (etat === 'ok') relire(); });
    }
    // En stock -> bientôt fini -> épuisé -> en stock. Bientôt fini ou épuisé : direction les courses.
    function basculerPlacard(p) {
        const suivant = !p.en_stock ? { en_stock: true, bientot: false }
                      : p.bientot ? { en_stock: false, bientot: false } : { en_stock: true, bientot: true };
        enregistrerPlacard(Object.assign({}, p, suivant));
        if (suivant.bientot || !suivant.en_stock) ajouter(p.nom); else afficher();
    }
    function retirerPlacard(p) {
        placard = placard.filter(function (x) { return x.cle !== p.cle; });
        placardOuvert = null; garder(); afficher();
        envoyer({ url: 'api/placard/' + encodeURIComponent(p.cle), methode: 'DELETE', cle: 'placard:' + p.cle });
    }
    function etatPlacard(p) { return !p.en_stock ? 'epuise' : p.bientot ? 'bientot' : ''; }

    function ligne(a) {
        const li = el('li', a.pris ? 'pris' : '');
        const coche = el('input'); coche.type = 'checkbox'; coche.checked = a.pris;
        coche.setAttribute('aria-label', a.nom);
        coche.addEventListener('change', function () { enregistrer(Object.assign({}, a, { pris: coche.checked })); });
        const nom = el('button', 'nom', a.nom); nom.type = 'button';
        nom.addEventListener('click', function () { ouvert = ouvert === a.id ? null : a.id; afficher(); });
        li.append(coche, nom);
        if (a.recurrent) li.append(el('span', 'recurrent', 'habituel'));
        if (ouvert !== a.id) return [li];
        const edition = el('div', 'edition');
        const rayon = el('select');
        RAYONS.forEach(function (r) { const o = el('option', '', r[1]); o.value = r[0]; o.selected = r[0] === a.rayon; rayon.append(o); });
        rayon.addEventListener('change', function () { ouvert = null; enregistrer(Object.assign({}, a, { rayon: rayon.value })); });
        const recurrent = el('button', '', a.recurrent ? 'Plus habituel' : 'Habituel'); recurrent.type = 'button';
        recurrent.addEventListener('click', function () { ouvert = null; enregistrer(Object.assign({}, a, { recurrent: !a.recurrent })); });
        const retirer = el('button', '', 'Retirer'); retirer.type = 'button';
        retirer.addEventListener('click', function () { ouvert = null; supprimer(a); });
        edition.append(rayon, recurrent, retirer);
        return [li, edition];
    }

    function afficher() {
        const actifs = articles.filter(function (a) { return a.actif; });
        const aPrendre = actifs.filter(function (a) { return !a.pris; }).length;
        const pris = actifs.length - aPrendre;
        resume.textContent = aPrendre ? aPrendre + ' à prendre' + (pris ? ' · ' + pris + ' dans le panier' : '')
                                      : (pris ? 'Tout est dans le panier' : 'Liste vide');
        liste.replaceChildren();
        RAYONS.forEach(function (r) {
            const du = actifs.filter(function (a) { return a.rayon === r[0]; })
                .sort(function (x, y) { return (x.pris - y.pris) || x.nom.localeCompare(y.nom, 'fr'); });
            if (!du.length) return;
            const section = el('section', 'rayon'); section.dataset.rayon = r[0];
            section.append(el('h2', '', r[1]));
            const ul = el('ul', 'articles');
            du.forEach(function (a) { ligne(a).forEach(function (n) { ul.append(n); }); });
            section.append(ul);
            liste.append(section);
        });
        if (!actifs.length) liste.append(el('p', 'vide-courses', 'Rien à acheter. Ajoute un article, un habituel ou un basique épuisé.'));
        viderPris.hidden = !pris;
        viderPris.textContent = 'Vider les pris (' + pris + ')';

        const habituels = articles.filter(function (a) { return a.recurrent && !a.actif; })
            .sort(function (x, y) { return x.nom.localeCompare(y.nom, 'fr'); });
        const zoneH = document.getElementById('habituels');
        zoneH.replaceChildren();
        habituels.forEach(function (a) {
            const b = el('button', '', '+ ' + a.nom); b.type = 'button';
            b.addEventListener('click', function () { enregistrer(Object.assign({}, a, { actif: true, pris: false })); });
            zoneH.append(b);
        });
        document.getElementById('nb-habituels').textContent = habituels.length;

        afficherPlacard();
    }

    function afficherPlacard() {
        const zoneP = document.getElementById('placard');
        zoneP.replaceChildren();
        const rang = { epuise: 0, bientot: 1, '': 2 };
        ZONES.forEach(function (z) {
            const du = placard.filter(function (p) { return (p.zone || 'placard-sec') === z[0]; })
                .sort(function (x, y) { return (rang[etatPlacard(x)] - rang[etatPlacard(y)]) || x.nom.localeCompare(y.nom, 'fr'); });
            if (!du.length) return;
            const section = el('section', 'zone-placard'); section.dataset.zone = z[0];
            const titre = el('h3', '', z[1]);
            const manque = du.filter(function (p) { return etatPlacard(p); }).length;
            if (manque) titre.append(el('span', '', manque + ' à racheter'));
            const puces = el('div', 'puces-courses');
            du.forEach(function (p) {
                const b = el('button', etatPlacard(p), p.nom); b.type = 'button';
                b.setAttribute('aria-label', p.nom + ({ epuise: ', épuisé', bientot: ', bientôt fini', '': ', en stock' })[etatPlacard(p)]);
                b.addEventListener('click', function () {
                    if (ranger) { placardOuvert = placardOuvert === p.cle ? null : p.cle; afficher(); }
                    else basculerPlacard(p);
                });
                puces.append(b);
            });
            section.append(titre, puces);
            const choisi = ranger && du.find(function (p) { return p.cle === placardOuvert; });
            if (choisi) section.append(editionPlacard(choisi));
            zoneP.append(section);
        });
        const epuises = placard.filter(function (p) { return !p.en_stock; }).length;
        const bientot = placard.filter(function (p) { return p.en_stock && p.bientot; }).length;
        document.getElementById('nb-placard').textContent = (epuises || bientot)
            ? [epuises ? epuises + ' épuisé(s)' : '', bientot ? bientot + ' bientôt fini(s)' : ''].filter(Boolean).join(' · ')
            : 'tout en stock';
        document.getElementById('ranger').textContent = ranger ? 'Terminé' : 'Ranger le placard';
        document.getElementById('ajout-placard').hidden = !ranger;
    }
    function editionPlacard(p) {
        const bloc = el('div', 'edition-placard');
        bloc.append(el('strong', '', p.nom));
        const zone = el('select'); zone.setAttribute('aria-label', 'Zone de ' + p.nom);
        ZONES.forEach(function (z) { const o = el('option', '', z[1]); o.value = z[0]; o.selected = z[0] === p.zone; zone.append(o); });
        zone.addEventListener('change', function () { placardOuvert = null; enregistrerPlacard(Object.assign({}, p, { zone: zone.value })); afficher(); });
        const retirer = el('button', '', 'Retirer du placard'); retirer.type = 'button';
        retirer.addEventListener('click', function () { retirerPlacard(p); });
        const fermer = el('button', '', 'Fermer'); fermer.type = 'button';
        fermer.addEventListener('click', function () { placardOuvert = null; afficher(); });
        bloc.append(zone, retirer, fermer);
        return bloc;
    }

    document.getElementById('ranger').addEventListener('click', function () { ranger = !ranger; placardOuvert = null; afficher(); });
    document.getElementById('ajout-placard').addEventListener('submit', function (ev) {
        ev.preventDefault();
        const nom = this.querySelector('input').value.trim();
        if (!nom) return;
        enregistrerPlacard({ cle: normaliser(nom), nom: nom, en_stock: true, bientot: false, zone: this.querySelector('select').value });
        this.querySelector('input').value = '';
        afficher();
    });
    document.getElementById('ajout-course').addEventListener('submit', function (ev) {
        ev.preventDefault();
        const champ = this.querySelector('input');
        champ.value.split(',').forEach(ajouter);                          // « lait, œufs, pain » d'un coup
        champ.value = '';
        champ.focus();
    });
    viderPris.addEventListener('click', function () {
        articles = articles.filter(function (a) { return !(a.actif && a.pris && !a.recurrent); })
            .map(function (a) { return a.actif && a.pris ? Object.assign({}, a, { actif: false, pris: false }) : a; });
        garder(); afficher();
        envoyer({ url: 'api/courses/vider', methode: 'POST', cle: 'vider' })
            .then(function (etat) { if (etat === 'ok') relire(); });
    });
    document.addEventListener('file-videe', charger);
    document.addEventListener('visibilitychange', function () { if (!document.hidden) charger(); });
    setInterval(function () { if (!document.hidden) charger(); }, 15000);   // l'autre téléphone, en magasin
    charger();
})();
"""


def courses_en_html():
    """La page Courses : une coquille, remplie par le script depuis api/courses (copie gardée hors ligne)."""
    rayons = json.dumps(RAYONS, ensure_ascii=False)
    zones = json.dumps(ZONES, ensure_ascii=False)
    options_zones = "".join(f'<option value="{cle}"{" selected" if cle == "placard-sec" else ""}>{nom}</option>'
                            for cle, nom in ZONES)
    return f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Courses · Casa Binomerie</title>
{TETE_PWA}
{TETE_POLICE}
<style>{STYLE_D}{STYLE_NAV_HUB}{STYLE_COURSES}</style>
</head>
<body class="accueil hub-page courses">
<h1>Courses</h1>
<p class="resume" id="resume">Chargement…</p>
<div id="hors-ligne" hidden></div>
<form id="ajout-course" autocomplete="off">
<input name="nom" placeholder="Ajouter (ex. lait, œufs)" aria-label="Article à ajouter" enterkeyhint="done">
<button type="submit">Ajouter</button>
</form>
<div id="liste"></div>
<button type="button" id="vider-pris" hidden>Vider les pris</button>
<details class="annexe" id="zone-habituels">
<summary>Habituels (<span id="nb-habituels">0</span>)</summary>
<p class="aide">Les articles marqués « habituel » reviennent ici une fois achetés : un tap pour les remettre sur la liste.</p>
<div class="puces-courses" id="habituels"></div>
</details>
<details class="annexe" id="zone-placard">
<summary>Placard · <span id="nb-placard">…</span></summary>
<p class="aide">Ce qui dure, rangé comme la cuisine. Un appui : en stock, puis bientôt fini, puis épuisé. Bientôt fini ou épuisé, il part dans les courses ; acheté, il revient en stock tout seul.</p>
<div id="placard"></div>
<form id="ajout-placard" autocomplete="off" hidden>
<input name="nom" placeholder="Ajouter au placard" aria-label="Élément à ajouter au placard">
<select name="zone" aria-label="Zone">{options_zones}</select>
<button type="submit">Ajouter</button>
</form>
<button type="button" id="ranger">Ranger le placard</button>
</details>
{nav_hub("courses")}
<script type="application/json" id="rayons">{rayons}</script>
<script type="application/json" id="zones">{zones}</script>
<script>{SCRIPT_FILE}
window.addEventListener('online', function () {{ majHorsLigne(); viderFile(); }});
window.addEventListener('offline', majHorsLigne);
majHorsLigne();
viderFile();
</script>
<script>{SCRIPT_COURSES}</script>
</body>
</html>"""
