"""Casa Binomerie — Dîners : le carnet de recettes, la semaine, le secours et le compteur Deliveroo.

- plats : le carnet (statut 'carnet') et les envies du Match des Recettes ('a-tester'). Un plat à
  tester passe au carnet quand un soir où on l'a prévu est marqué « fait maison » (db.enregistrer_soir).
- soirs : un par jour — le plat prévu et ce qui s'est vraiment passé (fait, commandé, dehors, autre).
  C'est aussi la mesure du succès : ≤ 1 commande par semaine (départ : 3, le 28/10/2026).
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
ISSUES = [("fait", "Fait maison"), ("commande", "Commandé"), ("dehors", "Dehors"), ("autre", "Autre")]
SECOURS_MINUTES = 20
FENETRE_PASSE = 42           # jours de soirs lus : les 6 semaines du compteur
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
    archive = corps.get("archive", False)
    if not isinstance(archive, bool):
        raise ValueError("archive invalide")
    p["archive"] = archive
    return p


def valider_soir(corps, aujourd_hui):
    """Un soir : {jour, plat (id ou None), issue (ou None)} ; de -60 à +30 jours."""
    if not isinstance(corps, dict):
        raise ValueError("soir invalide")
    try:
        jour = date.fromisoformat(corps.get("jour"))
    except (TypeError, ValueError):
        raise ValueError("jour invalide") from None
    if not -60 <= (jour - aujourd_hui).days <= FENETRE_FUTUR:
        raise ValueError("jour hors limites")
    plat = corps.get("plat") or None
    if plat is not None and (not isinstance(plat, str) or not _ID.fullmatch(plat)):
        raise ValueError("plat invalide")
    issue = corps.get("issue") or None
    if issue is not None and issue not in dict(ISSUES):
        raise ValueError("issue invalide")
    return {"jour": jour, "plat": plat, "issue": issue}


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


def compteur(soirs, aujourd_hui):
    """Commandes des 7 derniers jours, moyenne hebdomadaire sur 6 semaines, soirs renseignés."""
    recents = [s for s in soirs if s["issue"] and 0 <= (aujourd_hui - s["jour"]).days < FENETRE_PASSE]
    commandes = [s for s in recents if s["issue"] == "commande"]
    return {"semaine": sum(1 for s in commandes if (aujourd_hui - s["jour"]).days < 7),
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
div.jour { display: grid; grid-template-columns: 92px 1fr; align-items: center; gap: 10px; min-height: 52px;
           border-top: 1px solid var(--ligne); }
div.jour:first-of-type { border-top: none; }
div.jour .quand { font-weight: 800; font-size: 15px; }
div.jour .quand small { display: block; font-weight: 600; color: var(--doux); font-size: 12px; }
div.jour select { width: 100%; min-width: 0; font-family: inherit; font-size: 16px; padding: 10px 12px; border-radius: 14px;
                  border: 2px solid var(--ligne); background: var(--blanc); color: var(--texte); }
input.recherche { width: 100%; font-family: inherit; font-size: 17px; padding: 12px 16px; border-radius: 999px;
                  border: 2px solid var(--ligne); background: var(--blanc); color: var(--texte); }
div.filtres { display: flex; gap: 6px; flex-wrap: wrap; }
div.filtres button { border: 2px solid var(--ligne); background: var(--blanc); color: var(--texte); border-radius: 999px;
                     padding: 6px 12px; font-family: inherit; font-weight: 700; font-size: 14px; }
div.filtres button.actif { background: var(--diners); border-color: var(--diners); color: #ffffff; }
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
    const CLE_COPIE = 'diners:copie';
    let d = null;                                         // ce que renvoie api/diners
    let vue = 'ce-soir', filtre = 'tout', recherche = '';
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
    function soir(iso) { return d.soirs.find(function (s) { return s.jour === iso; }) || { jour: iso, plat: null, issue: null }; }
    function enStock(nom) { return d.stock.indexOf(normaliser(nom)) >= 0; }

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
    function planifier(iso, idPlat) {
        const s = Object.assign({}, soir(iso), { plat: idPlat || null });
        d.soirs = d.soirs.filter(function (x) { return x.jour !== iso; }).concat([s]);
        garder(); afficher();
        envoyer({ url: 'api/soirs', methode: 'POST', corps: s, cle: 'soir:' + iso }).then(relire, relire);
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
        const meta = el('span', 'meta', NOMS_GENRE[p.genre] + ' · ' + duree(p.minutes));
        if (extra) { meta.append(' · '); meta.append(extra); }
        o.append(nom, meta);
        li.append(o);
        return li;
    }
    function vueCeSoir(zone) {
        const s = soir(d.aujourd_hui), p = s.plat && plat(s.plat);
        if (p) {
            const bloc = el('div', 'plat-soir');
            bloc.append(el('span', 'titre', 'Ce soir'), el('span', 'nom', p.nom), el('span', 'titre', duree(p.minutes)));
            const b = el('div', 'boutons');
            b.append(bouton('Voir la recette', '', function () { ouvrirFiche(p.id); }),
                     bouton('Changer', 'discret', function () { vue = 'semaine'; afficher(); }));
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
            if (!p) li.append(bouton('Ce soir', 'petit', function () { planifier(d.aujourd_hui, x.id); }));
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
    function vueSemaine(zone) {
        const e = el('div', 'encart');
        e.append(el('h2', '', 'La semaine'), el('p', 'aide', 'Trois ou quatre soirs suffisent. Les autres restent libres.'));
        const choix = d.plats.filter(function (p) { return p.genre === 'plat' && !p.archive; })
                             .sort(function (a, b) { return a.nom.localeCompare(b.nom, 'fr'); });
        d.semaine.forEach(function (iso, i) {
            const ligne = el('div', 'jour');
            const q = el('span', 'quand', i === 0 ? 'Ce soir' : enClair(iso));
            if (i === 0) q.append(el('small', '', enClair(iso)));
            const sel = el('select'); sel.setAttribute('aria-label', 'Dîner du ' + enClair(iso));
            sel.append(new Option('—', ''));
            [['carnet', 'Carnet'], ['a-tester', 'À tester']].forEach(function (g) {
                const og = document.createElement('optgroup'); og.label = g[1];
                choix.filter(function (p) { return p.statut === g[0]; }).forEach(function (p) { og.append(new Option(p.nom + ' · ' + duree(p.minutes), p.id)); });
                sel.append(og);
            });
            sel.value = soir(iso).plat || '';
            sel.addEventListener('change', function () { planifier(iso, sel.value); });
            ligne.append(q, sel);
            e.append(ligne);
        });
        zone.append(e);
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
        function remplir() {
            ul.replaceChildren();
            const q = normaliser(recherche);
            d.plats.filter(function (p) {
                return p.statut === 'carnet' && !p.archive && (filtre === 'tout' || p.genre === filtre)
                    && (!q || normaliser(p.nom).indexOf(q) >= 0 || p.ingredients.some(function (i) { return normaliser(i).indexOf(q) >= 0; }));
            }).sort(function (a, b) { return a.nom.localeCompare(b.nom, 'fr'); })
              .forEach(function (p) { ul.append(lignePlat(p)); });
            if (!ul.children.length) ul.append(el('li', 'meta', 'Aucune recette ne correspond.'));
        }
        r.addEventListener('input', function () { recherche = r.value; remplir(); });
        remplir();
        const e = el('div', 'encart'); e.append(ul);
        zone.append(r, f, bouton('+ Nouvelle recette', 'plein', function () { ouvrirEdition(null); }), e);
    }
    function vueATester(zone) {
        const e = el('div', 'encart');
        e.append(el('h2', '', 'À tester ensemble'),
                 el('p', 'aide', 'Vos matchs au Match des Recettes. Prévoyez-en un dans la semaine : une fois fait maison, il rejoint le carnet.'));
        const ul = el('ul', 'plats');
        d.plats.filter(function (p) { return p.statut === 'a-tester' && !p.archive; })
            .sort(function (a, b) { return (b.recette ? 1 : 0) - (a.recette ? 1 : 0) || a.nom.localeCompare(b.nom, 'fr'); })
            .forEach(function (p) { ul.append(lignePlat(p, p.recette ? 'recette prête' : 'recette à écrire')); });
        e.append(ul);
        zone.append(e);
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
        if (p.ingredients.length) {
            const ing = el('div', 'ingredients');
            p.ingredients.forEach(function (i) { ing.append(el('span', enStock(i) ? '' : 'manque', i)); });
            c.append(ing);
        }
        c.append(el('pre', 'recette', p.recette || 'Recette à écrire : demande à Claude, ou écris la tienne avec « Modifier ».'));
        if (p.note) c.append(el('p', 'meta', p.note));
        const act = el('div', 'actions');
        act.append(bouton('Ce soir', 'plein', function () { planifier(d.aujourd_hui, p.id); fermer(); vue = 'ce-soir'; afficher(); }),
                   bouton('Modifier', 'petit', function () { ouvrirEdition(p.id); }));
        const manquants = p.ingredients.filter(function (i) { return !enStock(i); });
        if (manquants.length) act.append(bouton('Manquants aux courses (' + manquants.length + ')', 'petit', function (ev) {
            ajouterAuxCourses(manquants, 'plat:' + p.id); ev.target.textContent = 'Ajouté aux courses'; ev.target.disabled = true; }));
        if (p.statut === 'a-tester') act.append(bouton('On l\\'a fait : au carnet', 'petit', function () {
            enregistrerPlat(Object.assign({}, p, { statut: 'carnet' })); fermer(); }));
        c.append(act);
        document.getElementById('panneau').hidden = false;
        document.getElementById('panneau').scrollTop = 0;
        verrouiller();                                     // l'écran reste allumé pendant qu'on cuisine
    }
    function ouvrirEdition(id) {
        const p = id ? plat(id) : { id: nouvelId('plat'), nom: '', genre: 'plat', minutes: 30, ingredients: [], recette: '',
                                    lien: '', note: '', statut: 'carnet', archive: false };
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
        const deux = el('div', 'deux'); deux.append(champ('Genre', 'genre', genre), champ('Temps (min)', 'minutes', minutes));
        const msg = el('p', 'message');
        f.append(champ('Nom', 'nom', nom), deux, champ('Ingrédients, séparés par des virgules', 'ingredients', ing),
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
                recette: rec.value, lien: lien.value.trim(), note: note.value.trim() });
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
    genres = json.dumps(GENRES, ensure_ascii=False)
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
<script>{SCRIPT_FILE}
window.addEventListener('online', function () {{ majHorsLigne(); viderFile(); }});
window.addEventListener('offline', majHorsLigne);
majHorsLigne();
viderFile();
</script>
<script>{SCRIPT_DINERS}</script>
</body>
</html>"""
