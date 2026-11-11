"""Casa Binomerie — Cave : les vins à boire, tenus en un tap (spec : docs/superpowers/specs/2026-11-03-casa-cave-design.md).

Une ligne par référence (nom, millésime, couleur…) avec sa quantité et sa fenêtre à boire. Les vins de cuisine
restent au placard (Courses). Le vin du soir : accords_vins.py.
"""
import json

from accords_vins import PROFILS
from design import STYLE_D, STYLE_NAV_HUB, STYLE_ANNEXE, STYLE_HORS_LIGNE, TETE_POLICE, nav_hub, onglets_popote
from pwa import SCRIPT_FILE, TETE_PWA

# Les profils d'accord (accords_vins.PROFILS) tels qu'affichés
NOMS_PROFILS = {"boeuf": "Bœuf", "agneau": "Agneau", "gibier": "Gibier", "volaille": "Volaille", "porc": "Porc",
                "charcuterie": "Charcuterie", "poisson": "Poisson", "fruits-de-mer": "Fruits de mer",
                "fromage": "Fromage", "epice": "Épicé", "tomate": "Tomate", "legumes": "Légumes", "apero": "Apéro",
                "dessert": "Dessert"}
# Suggestions à la saisie de la région ; une bouteille étrangère prend aussi son pays (France par défaut)
REGIONS = ["Alsace", "Beaujolais", "Bordeaux", "Bourgogne", "Champagne", "Corse", "Jura", "Languedoc", "Loire",
           "Lorraine", "Provence", "Rhône Nord", "Rhône Sud", "Roussillon", "Savoie", "Sud-Ouest"]
COULEURS = [("rouge", "Rouge"), ("blanc", "Blanc"), ("rose", "Rosé"), ("bulles", "Effervescent"), ("doux", "Doux")]
# Fenêtre à boire par défaut, en années après le millésime (début, fin)
_FENETRE = {"rouge": (2, 6), "blanc": (0, 2), "rose": (0, 2), "bulles": (0, 5), "doux": (0, 5)}
ACCORDS_PAR_COULEUR = {"rouge": ["boeuf", "charcuterie"], "blanc": ["poisson", "fromage"],
                       "rose": ["legumes", "apero"], "bulles": ["apero"], "doux": ["dessert", "fromage"]}
MAX_TEXTE = 200


def par_defaut(couleur, millesime, annee):
    """(début, fin, accords) d'un vin ajouté sans fenêtre ni accords. Sans millésime : de cette année à +2.
    Le début n'est jamais avant cette année, la fin jamais avant le début."""
    if millesime is None:
        debut, fin = annee, annee + 2
    else:
        avant, apres = _FENETRE[couleur]
        debut, fin = max(millesime + avant, annee), millesime + apres
    return debut, max(fin, debut), list(ACCORDS_PAR_COULEUR[couleur])


def statut(b, annee):
    """« garder » (fenêtre pas encore ouverte), « vite » (elle se ferme cette année ou est passée), sinon « prete »."""
    if b["debut"] > annee:
        return "garder"
    return "vite" if b["fin"] <= annee else "prete"


def _entier(corps, cle, mini, maxi, defaut=None):
    """Entier de la plage [mini, maxi]. Un null (ou une clé absente) prend la valeur par défaut."""
    v = corps.get(cle)
    if v is None:
        v = defaut
    if v is None:
        return None
    if isinstance(v, bool) or not isinstance(v, int) or not mini <= v <= maxi:
        raise ValueError(f"{cle} invalide")
    return v


def _texte(corps, cle, obligatoire=False):
    v = corps.get(cle) or ""
    if not isinstance(v, str) or len(v) > MAX_TEXTE:
        raise ValueError(f"{cle} invalide")
    v = v.strip()
    if obligatoire and not v:
        raise ValueError(f"{cle} manquant")
    return v


def valider_bouteille(corps, annee):
    """Une bouteille venue du téléphone, vérifiée et complétée (fenêtre et accords par défaut s'ils manquent)."""
    if not isinstance(corps, dict):
        raise ValueError("bouteille invalide")
    identifiant = _texte(corps, "id", obligatoire=True)
    if len(identifiant) > 64:
        raise ValueError("id invalide")
    couleur = corps.get("couleur")
    if not isinstance(couleur, str) or couleur not in dict(COULEURS):
        raise ValueError("couleur invalide")
    millesime = _entier(corps, "millesime", 1900, annee)
    debut, fin, accords = par_defaut(couleur, millesime, annee)
    debut = _entier(corps, "debut", 1900, 2200, debut)
    fin = _entier(corps, "fin", 1900, 2200, fin)
    if debut > fin:
        raise ValueError("fenêtre invalide")
    if corps.get("accords") is not None:
        accords = corps["accords"]
    if not isinstance(accords, list) or any(a not in PROFILS for a in accords):
        raise ValueError("accords invalides")
    prix_bas = _entier(corps, "prix_bas", 0, 10000)
    prix_haut = _entier(corps, "prix_haut", 0, 10000)
    if prix_bas is not None and prix_haut is not None and prix_bas > prix_haut:
        raise ValueError("prix invalides")
    return {"id": identifiant, "nom": _texte(corps, "nom", obligatoire=True), "producteur": _texte(corps, "producteur"),
            "appellation": _texte(corps, "appellation"), "region": _texte(corps, "region"), "couleur": couleur,
            "millesime": millesime, "quantite": _entier(corps, "quantite", 0, 999, 1), "debut": debut, "fin": fin,
            "prix_bas": prix_bas, "prix_haut": prix_haut, "accords": [p for p in PROFILS if p in accords],
            "note": _texte(corps, "note"), "pays": _texte(corps, "pays") or "France"}


STYLE_CAVE = """
body.cave [hidden] { display: none; }
body.cave button, body.cave select, body.cave input { min-height: 40px; font-family: inherit; font-size: 14px; }
body.cave input, body.cave select { background: var(--blanc); color: var(--texte); border: 2px solid var(--ligne);
                                    border-radius: 14px; padding: 0 12px; min-width: 0; }
body.cave button { border-radius: 14px; border: 2px solid var(--ligne); background: var(--blanc); color: var(--texte);
                   font-weight: 700; padding: 0 14px; }
body.cave button#ajouter { background: var(--cave); border-color: var(--cave); color: var(--blanc); }
form#ajout-vin button[type="submit"] { background: var(--cave); border-color: var(--cave); color: var(--blanc); }
article.vin .ligne > button:not(.nom) { flex: none; border-color: var(--cave); color: var(--cave); }
body.cave h1 { margin-bottom: 4px; }
p.resume { color: var(--doux); margin: 0 0 14px; }
p.message { color: var(--doux); margin: 0 0 14px; }
p.message:empty { display: none; }
#ajouter { margin: 0 0 14px; }
form#ajout-vin[hidden] { display: none; }
form#ajout-vin { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; background: var(--carte);
                 border-radius: 20px; padding: 14px; margin: 0 0 14px; }
form#ajout-vin input[name="nom"] { grid-column: 1 / -1; }
form#ajout-vin .actions { grid-column: 1 / -1; display: flex; gap: 8px; }
section.groupe-cave h2 { font-size: 15px; font-weight: 800; color: var(--doux); margin: 18px 0 8px; }
article.vin { background: var(--carte); border-radius: 20px; padding: 12px 14px 12px 18px; margin: 0 0 8px;
              position: relative; }
article.vin::before { content: ""; position: absolute; left: 0; top: 12px; bottom: 12px; width: 5px;
                      border-radius: 0 4px 4px 0; background: var(--c); }
article.vin .ligne { display: flex; justify-content: space-between; align-items: center; gap: 10px; }
article.vin button.nom { all: unset; cursor: pointer; font-weight: 700; min-width: 0; flex: 1; min-height: 40px;
                         display: flex; flex-direction: column; justify-content: center; }
article.vin .meta { display: block; color: var(--doux); font-size: 13px; font-weight: 400; }
article.vin .edition { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 10px; align-items: center; }
article.vin .edition input[type="number"] { width: 5.5em; }
article.vin .edition label.champ { display: flex; flex-direction: column; gap: 4px; font-size: 12px; font-weight: 700;
                                   color: var(--doux); }
article.vin .edition input[name="note"] { flex: 1 1 100%; }
article.vin .puces-accords { display: flex; flex-wrap: wrap; gap: 6px; flex: 1 1 100%; }
article.vin .puces-accords button[aria-pressed="true"] { background: var(--cave); border-color: var(--cave); color: var(--blanc); }
article.vin button.nom:focus-visible { outline: 2px solid var(--cave); outline-offset: 2px; border-radius: 6px; }
article.vin[data-couleur="rouge"] { --c: #9b2c4f; }
article.vin[data-couleur="blanc"] { --c: #c9a227; }
article.vin[data-couleur="rose"] { --c: #e58aa3; }
article.vin[data-couleur="bulles"] { --c: #a08c5b; }
article.vin[data-couleur="doux"] { --c: #d39a2a; }
"""

SCRIPT_CAVE = """
(function () {
    const COULEURS = JSON.parse(document.getElementById('couleurs').textContent);
    const PROFILS = JSON.parse(document.getElementById('profils').textContent);
    const NOMS_PROFILS = JSON.parse(document.getElementById('noms-profils').textContent);
    const NOM_COULEUR = {}; COULEURS.forEach(function (c) { NOM_COULEUR[c[0]] = c[1]; });
    const CLE_COPIE = 'cave-copie';
    let bouteilles = [], annee = new Date().getFullYear(), ouvert = null;

    function el(balise, classe, texte) {
        const e = document.createElement(balise);
        if (classe) e.className = classe;
        if (texte !== undefined) e.textContent = texte;
        return e;
    }
    function bouton(texte, action) {
        const b = el('button', '', texte); b.type = 'button'; b.addEventListener('click', action); return b;
    }
    function statut(b) { return b.debut > annee ? 'garder' : (b.fin <= annee ? 'vite' : 'prete'); }
    function garder() { try { localStorage.setItem(CLE_COPIE, JSON.stringify({ bouteilles: bouteilles, annee: annee })); } catch (e) {} }
    function appliquer(lu) { bouteilles = lu.bouteilles; annee = lu.annee; garder(); afficher(); }
    function charger() {
        if (ouvert || lireFile().length) {                       // une édition en cours, ou des envois en attente
            if (!bouteilles.length) { try { appliquer(JSON.parse(localStorage.getItem(CLE_COPIE))); } catch (e) {} }
            return;
        }
        fetch('api/cave').then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
            .then(appliquer)
            .catch(function () { try { appliquer(JSON.parse(localStorage.getItem(CLE_COPIE))); } catch (e) {} });
    }
    function message(texte) { document.getElementById('message-cave').textContent = texte; }
    let chaine = Promise.resolve();
    function envoyer(envoi) {
        const p = chaine.then(function () { return envoyerOuGarder(envoi); });
        chaine = p.catch(function () {});
        return p.then(function (etat) {
            if (etat === 'ok') { message(''); charger(); }
            return etat;
        }, function () {                                         // écriture refusée (4xx) : on dit pourquoi et on relit le serveur
            message('Pas enregistré : vérifie les valeurs.');
            ouvert = null; charger();
        });
    }

    function enregistrer(b) {
        bouteilles = bouteilles.filter(function (x) { return x.id !== b.id; }).concat([b]);
        garder(); afficher();
        envoyer({ url: 'api/cave', methode: 'POST', corps: b, cle: 'vin:' + b.id });
    }
    function bue(b) {
        b.quantite = Math.max(b.quantite - 1, 0);
        garder(); afficher();
        envoyer({ url: 'api/cave/' + encodeURIComponent(b.id) + '/bue', methode: 'POST' });   // sans clé : chaque tap compte
    }
    function retirer(b) {
        bouteilles = bouteilles.filter(function (x) { return x.id !== b.id; });
        ouvert = null; garder(); afficher();
        envoyer({ url: 'api/cave/' + encodeURIComponent(b.id), methode: 'DELETE', cle: 'vin:' + b.id });
    }

    function fiche(b) {
        const a = el('article', 'vin'); a.dataset.couleur = b.couleur;
        const ligne = el('div', 'ligne');
        const nom = el('button', 'nom', b.nom); nom.type = 'button';
        const lieu = [b.region, b.pays && b.pays !== 'France' ? b.pays : ''].filter(Boolean).join(', ');
        nom.append(el('span', 'meta', [lieu, b.millesime || 'sans millésime', NOM_COULEUR[b.couleur],
                                       b.debut === b.fin ? '' + b.fin : b.debut + '–' + b.fin,
                                       '×\u00a0' + b.quantite].filter(Boolean).join(' · ')));
        nom.addEventListener('click', function () { ouvert = ouvert === b.id ? null : b.id; afficher(); });
        ligne.append(nom);
        if (b.quantite > 0) ligne.append(bouton('Bue', function () { bue(b); }));
        else ligne.append(bouton('Remettre', function () { enregistrer(Object.assign({}, b, { quantite: 1 })); }));
        a.append(ligne);
        if (ouvert === b.id) a.append(edition(b));
        return a;
    }
    function entierOu(champ, defaut) { const v = parseInt(champ.value, 10); return isNaN(v) ? defaut : v; }
    function nombre(nom, valeur, mini) {
        const i = el('input'); i.type = 'number'; i.name = nom; i.value = valeur; i.min = mini; return i;
    }
    function etiquette(libelle, champ) {                        // un libellé visible au-dessus du champ
        const l = el('label', 'champ'); l.append(el('span', '', libelle), champ); return l;
    }
    function retrait(b) {                                       // deux taps, sans boîte de dialogue : le 2e confirme, 4 s pour le faire
        const r = bouton('Retirer', function () {
            if (r.dataset.confirme) { retirer(b); return; }
            r.dataset.confirme = '1'; r.textContent = 'Confirmer le retrait';
            setTimeout(function () { delete r.dataset.confirme; r.textContent = 'Retirer'; }, 4000);
        });
        return r;
    }
    function edition(b) {
        const e = el('div', 'edition');
        const quantite = nombre('quantité', b.quantite, 0), debut = nombre('début', b.debut, 1900), fin = nombre('fin', b.fin, 1900);
        const accords = b.accords.slice();
        const puces = el('div', 'puces-accords');
        PROFILS.forEach(function (p) {
            const x = bouton(NOMS_PROFILS[p] || p, function () {
                const i = accords.indexOf(p);
                if (i < 0) accords.push(p); else accords.splice(i, 1);
                x.setAttribute('aria-pressed', i < 0);
            });
            x.setAttribute('aria-pressed', accords.indexOf(p) >= 0);
            puces.append(x);
        });
        const note = el('input'); note.name = 'note'; note.value = b.note; note.placeholder = 'Note'; note.setAttribute('aria-label', 'Note');
        const region = el('input'); region.name = 'region'; region.value = b.region || ''; region.placeholder = 'Région';
        region.setAttribute('aria-label', 'Région'); region.setAttribute('list', 'regions');
        const pays = el('input'); pays.name = 'pays'; pays.value = b.pays || 'France'; pays.placeholder = 'Pays';
        pays.setAttribute('aria-label', 'Pays');
        e.append(etiquette('Bouteilles', quantite), etiquette('À boire dès', debut), etiquette("Jusqu'en", fin),
                 etiquette('Région', region), etiquette('Pays', pays), puces, note,
            bouton('Enregistrer', function () {
                ouvert = null;
                enregistrer(Object.assign({}, b, { quantite: Math.max(entierOu(quantite, b.quantite), 0),
                    debut: entierOu(debut, b.debut), fin: entierOu(fin, b.fin),
                    accords: PROFILS.filter(function (p) { return accords.indexOf(p) >= 0; }), note: note.value.trim(),
                    region: region.value.trim(), pays: pays.value.trim() || 'France' }));
            }),
            retrait(b),
            bouton('Fermer', function () { ouvert = null; afficher(); }));
        return e;
    }

    function afficher() {
        const zone = document.getElementById('cave');
        zone.replaceChildren();
        const enCave = bouteilles.filter(function (b) { return b.quantite > 0; });
        [['vite', 'À boire vite'], ['prete', 'Prêtes'], ['garder', 'À garder']].forEach(function (g) {
            const du = enCave.filter(function (b) { return statut(b) === g[0]; })
                .sort(function (x, y) { return (x.fin - y.fin) || x.nom.localeCompare(y.nom, 'fr'); });
            if (!du.length) return;
            const s = el('section', 'groupe-cave'); s.append(el('h2', '', g[1]));
            du.forEach(function (b) { s.append(fiche(b)); });
            zone.append(s);
        });
        const bues = bouteilles.filter(function (b) { return b.quantite === 0; })
            .sort(function (x, y) { return x.nom.localeCompare(y.nom, 'fr'); });
        const liste = document.getElementById('bues'); liste.replaceChildren();
        bues.forEach(function (b) { liste.append(fiche(b)); });
        document.getElementById('nb-bues').textContent = bues.length;
        const n = enCave.reduce(function (t, b) { return t + b.quantite; }, 0);
        const bas = enCave.reduce(function (t, b) { return t + (b.prix_bas || 0) * b.quantite; }, 0);
        const haut = enCave.reduce(function (t, b) { return t + (b.prix_haut || 0) * b.quantite; }, 0);
        const vite = enCave.filter(function (b) { return statut(b) === 'vite'; }).reduce(function (t, b) { return t + b.quantite; }, 0);
        document.getElementById('resume').textContent = n + ' bouteille' + (n > 1 ? 's' : '') + ' · ' + bas + '–' + haut
            + ' € · ' + vite + ' à boire d\\'ici fin ' + annee;
    }

    const formulaire = document.getElementById('ajout-vin');
    document.getElementById('ajouter').addEventListener('click', function () { formulaire.hidden = !formulaire.hidden; });
    formulaire.querySelector('[data-action="annuler"]').addEventListener('click', function () { formulaire.hidden = true; });
    formulaire.addEventListener('submit', function (ev) {
        ev.preventDefault();
        const f = new FormData(formulaire);
        const entier = function (cle) { const v = parseInt(f.get(cle), 10); return isNaN(v) ? null : v; };
        const prix = entier('prix');
        const corps = { id: 'vin-' + Date.now().toString(36), nom: (f.get('nom') || '').trim(), couleur: f.get('couleur'),
                        millesime: entier('millesime'), quantite: entier('quantite') || 1, prix_bas: prix, prix_haut: prix,
                        region: (f.get('region') || '').trim(), pays: (f.get('pays') || '').trim() || 'France' };
        if (!corps.nom) return;
        // Fenêtre et accords par défaut : posés par le serveur (cave.par_defaut), relus à la réponse
        bouteilles = bouteilles.concat([Object.assign({ debut: annee, fin: annee + 2, accords: [], note: '' }, corps)]);
        garder(); afficher();
        envoyer({ url: 'api/cave', methode: 'POST', corps: corps, cle: 'vin:' + corps.id });
        formulaire.reset(); formulaire.hidden = true;
    });
    document.addEventListener('file-videe', charger);
    document.addEventListener('visibilitychange', function () { if (!document.hidden) charger(); });
    charger();
})();
"""


def cave_en_html():
    """La page Cave : une coquille, remplie par le script depuis api/cave (copie gardée hors ligne)."""
    couleurs = json.dumps(COULEURS, ensure_ascii=False)
    profils = json.dumps(PROFILS, ensure_ascii=False)
    noms_profils = json.dumps(NOMS_PROFILS, ensure_ascii=False)
    options = "".join(f'<option value="{c}">{nom}</option>' for c, nom in COULEURS)
    regions = "".join(f'<option value="{r}">' for r in REGIONS)
    return f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Cave · Casa Binomerie</title>
{TETE_PWA}
{TETE_POLICE}
<style>{STYLE_D}{STYLE_NAV_HUB}{STYLE_ANNEXE}{STYLE_HORS_LIGNE}{STYLE_CAVE}</style>
</head>
<body class="accueil hub-page cave">
{onglets_popote("cave")}
<p class="resume" id="resume">Chargement…</p>
<p class="message" id="message-cave" aria-live="polite"></p>
<div id="hors-ligne" hidden></div>
<button type="button" id="ajouter">+ Ajouter</button>
<form id="ajout-vin" autocomplete="off" hidden>
<input name="nom" placeholder="Nom du vin" aria-label="Nom du vin" required>
<select name="couleur" aria-label="Couleur">{options}</select>
<input name="millesime" type="number" min="1900" placeholder="Millésime" aria-label="Millésime">
<input name="quantite" type="number" min="1" value="1" aria-label="Quantité">
<input name="prix" type="number" min="0" placeholder="Prix (€)" aria-label="Prix estimé">
<input name="region" placeholder="Région" aria-label="Région" list="regions">
<input name="pays" placeholder="Pays (France)" aria-label="Pays">
<div class="actions"><button type="submit">Ajouter</button><button type="button" data-action="annuler">Annuler</button></div>
</form>
<div id="cave"></div>
<details class="annexe" id="zone-bues">
<summary>Bues (<span id="nb-bues">0</span>)</summary>
<div id="bues"></div>
</details>
{nav_hub("cave")}
<datalist id="regions">{regions}</datalist>
<script type="application/json" id="couleurs">{couleurs}</script>
<script type="application/json" id="noms-profils">{noms_profils}</script>
<script type="application/json" id="profils">{profils}</script>
<script>{SCRIPT_FILE}
window.addEventListener('online', function () {{ majHorsLigne(); viderFile(); }});
window.addEventListener('offline', majHorsLigne);
majHorsLigne();
viderFile();
</script>
<script>{SCRIPT_CAVE}</script>
</body>
</html>"""
