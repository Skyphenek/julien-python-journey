"""« 🎁 Souvenirs » : quoi rapporter, et pour qui.

- Un carnet de proches (table proches) gardé d'un voyage à l'autre, avec un budget et ce qu'on
  leur a déjà rapporté (évite le 2e foulard en soie).
- Les souvenirs du voyage (table souvenirs) : une idée pour un proche (ou « pour nous »), cochée
  « acheté » avec son prix ; l'achat devient une dépense partagée (db.enregistrer_souvenir).
- Des idées par pays, écrites à la main, avec ce qui ne passe pas la douane.
"""
import json
import re
from datetime import date
from decimal import Decimal, InvalidOperation
from html import escape as echapper

_ID = re.compile(r"[A-Za-z0-9-]{8,64}")

# Idées par pays : (idée, où / conseil, alerte douane ou "")
IDEES = {
    "VN": ("Vietnam", [
        ("Café vietnamien + filtre phin", "Robusta des Hauts Plateaux ; marchés et torréfacteurs locaux plutôt que les boutiques d'aéroport.", ""),
        ("Laque", "Boîtes, plateaux, tableaux : ateliers de Hanoï et de Hô Chi Minh-Ville.", ""),
        ("Soie ou vêtement sur mesure", "Tailleurs de Hội An : 24 à 48 h, prévoir un essayage.", ""),
        ("Thé vert de Thái Nguyên", "Le thé de référence du nord, léger à transporter.", ""),
        ("Poivre de Phú Quốc", "Sous vide, sur l'île ou dans les marchés.", ""),
        ("Vin de serpent", "", "⚠️ Interdit à l'entrée dans l'UE (espèces protégées, CITES)."),
    ]),
    "KH": ("Cambodge", [
        ("Poivre de Kampot", "Indication géographique protégée ; rouge, noir ou blanc, chez les producteurs ou à Phnom Penh.", ""),
        ("Krama", "L'écharpe à carreaux en coton ou en soie, sur tous les marchés.", ""),
        ("Artisanat d'Artisans d'Angkor", "Soie, sculptures, laque : ateliers de Siem Reap, prix fixes.", ""),
        ("Sucre de palme de Kampong Speu", "Indication géographique protégée.", ""),
        ("Statues ou objets anciens", "", "⚠️ Antiquités khmères : exportation interdite."),
    ]),
    "TH": ("Thaïlande", [
        ("Soie thaïe", "Coussins, foulards ; boutiques Jim Thompson ou marchés de Chiang Mai.", ""),
        ("Céladon", "Céramique vert pâle, ateliers de Chiang Mai.", ""),
        ("Pâtes de curry et épices", "Sous vide au marché ou en supermarché.", ""),
        ("Coussin triangle", "Encombrant mais souvent vendu démonté.", ""),
        ("Statue de Bouddha", "", "⚠️ Exportation des images du Bouddha soumise à autorisation."),
    ]),
    "LA": ("Laos", [
        ("Textiles tissés main", "Marché de nuit de Luang Prabang, coopératives de tisserandes.", ""),
        ("Café des Bolovens", "Arabica et robusta du plateau du sud.", ""),
        ("Lao-Lao", "L'alcool de riz local, dans la limite d'alcool autorisée.", ""),
    ]),
    "JP": ("Japon", [
        ("Couteau de cuisine", "Kappabashi à Tokyo, Sakai près d'Osaka ; en soute uniquement.", ""),
        ("Thé (matcha, sencha)", "Uji près de Kyoto pour le matcha.", ""),
        ("Furoshiki", "Tissu d'emballage, léger et plat.", ""),
        ("Papeterie", "Itoya, Loft, Tokyu Hands.", ""),
        ("Kit Kat aux parfums locaux", "Matcha, sakura, saké… en supermarché.", ""),
        ("Bœuf wagyu, charcuterie", "", "⚠️ Viande : interdite à l'entrée dans l'UE."),
    ]),
    "ID": ("Indonésie", [
        ("Batik", "Yogyakarta et Solo à Java ; vérifier « tulis » (fait main) contre imprimé.", ""),
        ("Vanille", "Gousses sous vide.", ""),
        ("Café de Java ou de Sumatra", "", ""),
        ("Kopi luwak", "", "⚠️ Souvent issu de civettes en cage : à éviter."),
    ]),
    "MA": ("Maroc", [
        ("Huile d'argan", "En coopérative de femmes plutôt qu'en souk.", ""),
        ("Babouches", "Souks de Marrakech et de Fès, se négocie.", ""),
        ("Céramique", "Safi et Fès ; bien emballer en bagage cabine.", ""),
        ("Épices (ras el hanout, safran)", "Le safran de Taliouine est le plus réputé.", ""),
        ("Théière et verres à thé", "", ""),
    ]),
    "TR": ("Turquie", [
        ("Loukoums", "Chez un confiseur (Hafız Mustafa, Koska) plutôt qu'en vrac.", ""),
        ("Café turc + cezve", "", ""),
        ("Fouta (peştemal)", "Serviette de hammam en coton, légère.", ""),
        ("Céramique d'Iznik (reproduction)", "", ""),
        ("Antiquités", "", "⚠️ Exportation interdite sans certificat des musées."),
    ]),
    "MX": ("Mexique", [
        ("Vanille de Papantla", "", ""),
        ("Mezcal", "Oaxaca ; dans la limite d'alcool autorisée.", ""),
        ("Textiles d'Oaxaca et du Chiapas", "", ""),
        ("Alebrijes", "Figurines peintes d'Oaxaca.", ""),
        ("Chocolat d'Oaxaca", "", ""),
    ]),
    "IT": ("Italie", [
        ("Huile d'olive", "Chez un producteur, en bidon métal pour la soute.", ""),
        ("Pâtes artisanales", "", ""),
        ("Limoncello", "Côte amalfitaine.", ""),
        ("Cuir", "Florence ; vérifier « vera pelle ».", ""),
    ]),
    "ES": ("Espagne", [
        ("Jambon ibérique", "Sous vide, tranché.", ""),
        ("Turrón", "", ""),
        ("Safran de La Mancha", "", ""),
        ("Espadrilles", "", ""),
    ]),
    "PT": ("Portugal", [
        ("Conserves de poisson", "Boîtes illustrées, à Lisbonne et Porto.", ""),
        ("Azulejos", "Carreaux anciens : seulement chez des antiquaires sérieux (vols fréquents).", ""),
        ("Vin de Porto", "", ""),
        ("Objets en liège", "", ""),
    ]),
    "GR": ("Grèce", [
        ("Huile d'olive", "", ""),
        ("Miel de thym", "", ""),
        ("Mastiha de Chios", "Résine, liqueur ou chewing-gum.", ""),
        ("Savon à l'huile d'olive", "", ""),
    ]),
}

DOUANE = ("🛃 Retour dans l'UE : franchise de 430 € d'achats par voyageur (avion ou bateau), au-delà il faut "
          "déclarer. Alcool : 1 L d'alcool fort ou 2 L à 22° max, plus 4 L de vin et 16 L de bière. Tabac : "
          "200 cigarettes. Interdits : viande et produits laitiers, ivoire, corail, écailles et autres espèces "
          "protégées, contrefaçons.")


def idees_du_voyage(codes_pays):
    """[{"pays", "idees": [(idée, note, alerte)]}], un par pays connu, dans l'ordre du voyage."""
    vus, resultat = set(), []
    for code in codes_pays:
        if code in IDEES and code not in vus:
            vus.add(code)
            nom, idees = IDEES[code]
            resultat.append({"pays": nom, "idees": idees})
    return resultat


# --- Validation : tout ce qui vient du téléphone est vérifié ----------------------------------

def _texte(corps, cle, maximum):
    valeur = corps.get(cle) or ""
    if not isinstance(valeur, str):
        raise ValueError(f"{cle} invalide")
    valeur = valeur.strip()
    if len(valeur) > maximum:
        raise ValueError(f"{cle} trop long")
    return valeur


def _identifiant(valeur, quoi):
    if not isinstance(valeur, str) or not _ID.fullmatch(valeur):
        raise ValueError(f"{quoi} invalide")
    return valeur


def _montant(valeur, quoi, minimum, maximum):
    """« 12.50 » ou 12.5 -> Decimal, borné ; ValueError sinon (jamais de float en base)."""
    if isinstance(valeur, bool) or not isinstance(valeur, (str, int, float)):
        raise ValueError(f"{quoi} invalide")
    try:
        m = Decimal(str(valeur)).quantize(Decimal("0.01"))
    except InvalidOperation:
        raise ValueError(f"{quoi} invalide") from None
    if not (minimum <= m < maximum):
        raise ValueError(f"{quoi} hors limites")
    return m


def valider_proche(corps):
    """Un proche du carnet : {id, nom, budget (Decimal ou None), archive}."""
    if not isinstance(corps, dict):
        raise ValueError("proche invalide")
    p = {"id": _identifiant(corps.get("id"), "id"), "nom": _texte(corps, "nom", 80)}
    if not p["nom"]:
        raise ValueError("nom manquant")
    budget = corps.get("budget")
    p["budget"] = None if budget in (None, "") else _montant(budget, "budget", 0, 100_000)
    if not isinstance(corps.get("archive", False), bool):
        raise ValueError("archive invalide")
    p["archive"] = corps.get("archive", False)
    return p


def valider_souvenir(corps):
    """Un souvenir du voyage. Acheté : prix, devise, prix en euros, payeur et jour obligatoires."""
    if not isinstance(corps, dict):
        raise ValueError("souvenir invalide")
    voyage = corps.get("voyage")
    if not isinstance(voyage, str) or not voyage:
        raise ValueError("voyage invalide")
    proche = corps.get("proche") or ""
    s = {"id": _identifiant(corps.get("id"), "id"), "voyage": voyage,
         "proche": proche and _identifiant(proche, "proche"),
         "idee": _texte(corps, "idee", 200), "note": _texte(corps, "note", 500)}
    if not s["idee"]:
        raise ValueError("idée manquante")
    if not isinstance(corps.get("achete"), bool):
        raise ValueError("achete invalide")
    s["achete"] = corps["achete"]
    if not s["achete"]:
        return {**s, "prix": None, "devise": None, "prix_eur": None, "paye_par": None, "achete_le": None}
    s["prix"] = _montant(corps.get("prix"), "prix", Decimal("0.01"), 10**12)
    s["prix_eur"] = _montant(corps.get("prix_eur"), "prix en euros", 0, 10**9)
    if not isinstance(corps.get("devise"), str) or not re.fullmatch(r"[A-Z]{3}", corps["devise"]):
        raise ValueError("devise invalide")
    s["devise"] = corps["devise"]
    if not isinstance(corps.get("paye_par"), str) or not corps["paye_par"]:
        raise ValueError("payeur invalide")
    s["paye_par"] = corps["paye_par"]
    try:
        s["achete_le"] = date.fromisoformat(corps.get("achete_le"))
    except (TypeError, ValueError):
        raise ValueError("date d'achat invalide") from None
    return s


# --- Page : le bloc (rempli par le script) ----------------------------------------------------

def bloc_souvenirs(personnes, devises, idees, douane):
    """Le bloc : carnet et souvenirs remplis par le script ; idées par pays et douane écrites ici."""
    donnees = json.dumps({"devises": ["EUR", *devises]}, ensure_ascii=False).replace("</", "<\\/")
    pays = ""
    for p in idees:
        lignes = ""
        for idee, note, alerte in p["idees"]:
            detail = " — ".join(x for x in (note, alerte) if x)
            bouton = ("" if alerte and not note else
                      f'<button type="button" class="ctrl-btn ajouter-idee" data-idee="{echapper(idee)}" '
                      f'data-note="{echapper(note)}" title="Ajouter pour quelqu\'un">➕</button>')
            lignes += (f'<li><span><strong>{echapper(idee, quote=False)}</strong>'
                       f'{" — " + echapper(detail, quote=False) if detail else ""}</span>{bouton}</li>')
        pays += f'<h4>{echapper(p["pays"], quote=False)}</h4><ul class="idees">{lignes}</ul>'
    if pays:
        pays = f'<details class="idees-pays"><summary>🛍️ Idées par pays</summary>{pays}</details>'
    regles = f'<p class="conseil">{echapper(DOUANE, quote=False)}</p>' if douane else ""
    return (f'<div class="info souvenirs" data-personnes="{echapper("|".join(personnes))}"><h3>🎁 Souvenirs</h3>'
            f'<script type="application/json" class="donnees-souvenirs">{donnees}</script>'
            '<p class="resume-souvenirs"></p>'
            '<div class="panneau"></div><div class="proches-zone"></div>'
            '<div class="actions"><button type="button" class="ctrl-btn ajouter-proche">➕ Un proche</button></div>'
            f'{pays}'
            f'{regles}'
            '<p class="conseil">Le carnet de proches est gardé pour les prochains voyages. '
            'Un souvenir acheté s\'ajoute aux 💸 Dépenses.</p></div>')


STYLE_SOUVENIRS = """
div.souvenirs .proche { border-top: 1px solid var(--ligne); padding: .5rem 0; }
div.souvenirs .proche .tete { display: flex; justify-content: space-between; gap: .5rem; align-items: baseline; }
div.souvenirs .proche .nom-proche { font-weight: 600; margin: 0; }
div.souvenirs .proche .budget { font-size: .85rem; color: var(--doux); font-variant-numeric: tabular-nums; white-space: nowrap; }
div.souvenirs .proche .budget.depasse { color: #dc2626; }
div.souvenirs .historique { font-size: .8rem; color: var(--doux); margin: .1rem 0; }
div.souvenirs ul { list-style: none; margin: 0; padding: 0; }
div.souvenirs li.souvenir { display: flex; gap: .5rem; align-items: flex-start; padding: .35rem 0; }
div.souvenirs li.souvenir .achat-btn { border: none; background: none; font-size: 1.2rem; cursor: pointer; padding: 0; }
div.souvenirs li.souvenir .corps { flex: 1; min-width: 0; }
div.souvenirs li.souvenir p { margin: .1rem 0; font-size: .9rem; overflow-wrap: anywhere; }
div.souvenirs li.souvenir p.idee { font-size: 1rem; }
div.souvenirs li.souvenir.achete p.idee { color: var(--doux); }
div.souvenirs li.souvenir .note-souvenir, div.souvenirs li.souvenir .prix { color: var(--doux); font-size: .85rem; }
div.souvenirs .actions { display: flex; flex-wrap: wrap; gap: .4rem; margin-top: .3rem; }
div.souvenirs .actions button { font-size: .8rem; }
div.souvenirs .panneau:empty { display: none; }
div.souvenirs .panneau { background: var(--fond); border-radius: 12px; padding: .8rem; margin: .5rem 0; }
div.souvenirs .panneau h4 { margin: 0 0 .4rem; }
div.souvenirs .panneau label { display: block; font-size: .8rem; color: var(--doux); margin: .35rem 0; }
div.souvenirs .panneau input, div.souvenirs .panneau select, div.souvenirs .panneau textarea {
    display: block; width: 100%; box-sizing: border-box; font-size: 1rem; padding: .4rem; margin-top: .15rem;
    border: 1px solid var(--ligne); border-radius: 8px; background: var(--carte); color: var(--texte); }
div.souvenirs .panneau .message-souvenir { color: #dc2626; font-size: .85rem; }
div.souvenirs details.idees-pays { margin-top: .6rem; }
div.souvenirs details.idees-pays > summary { font-weight: 600; cursor: pointer; }
div.souvenirs ul.idees li { display: flex; gap: .5rem; align-items: flex-start; justify-content: space-between;
    border-top: 1px solid var(--ligne); padding: .4rem 0; font-size: .9rem; }
"""

# Script du bloc. Isolé dans une fonction ; utilise la file d'attente hors ligne du script
# principal (envoyerOuGarder, lireFile) et ses taux gardés (lireTauxGardes). Pas de case à
# cocher : le script de la valise compte toutes les checkbox de la page. Texte via textContent.
SCRIPT_SOUVENIRS = """
(function () {
    const bloc = document.querySelector('div.souvenirs');
    if (!bloc) return;
    const DEVISES = JSON.parse(bloc.querySelector('.donnees-souvenirs').textContent).devises;
    const PERSONNES = bloc.dataset.personnes.split('|');
    const panneau = bloc.querySelector('.panneau');
    const CLE_COPIE = 'souvenirs:' + VOYAGE;
    const EUR = new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' });
    const NOMBRE = new Intl.NumberFormat('fr-FR');
    let proches = [], souvenirs = [], historique = {};
    let enEdition = false;                                  // panneau ouvert : pas de rafraîchissement

    function para(texte, classe) { const p = document.createElement('p'); p.textContent = texte; if (classe) p.className = classe; return p; }
    function bouton(texte, action) {
        const b = document.createElement('button'); b.type = 'button'; b.className = 'ctrl-btn'; b.textContent = texte;
        b.addEventListener('click', action); return b;
    }
    function deuxTemps(texte, question, action) {          // 1er tap : « Sûr ? », 2e tap : on agit
        const b = bouton(texte, function () {
            if (!b.dataset.confirmer) { b.dataset.confirmer = '1'; b.textContent = question; return; }
            action();
        });
        return b;
    }
    function nouvelId() {
        if (window.crypto && crypto.randomUUID) return crypto.randomUUID();
        return Date.now().toString(36) + '-' + Math.random().toString(36).slice(2, 10);
    }
    function aujourdhui() {
        const d = new Date();
        return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0');
    }
    function nomDe(id) {
        if (!id) return 'nous';
        const p = proches.find(function (x) { return x.id === id; });
        return p ? p.nom : '?';
    }

    // Ce qui attend dans la file (hors ligne) passe par-dessus ce qu'a lu le serveur
    function avecAttente(lu) {
        const parProche = {}, parSouvenir = {};
        (lu.proches || []).forEach(function (p) { parProche[p.id] = p; });
        (lu.souvenirs || []).forEach(function (s) { parSouvenir[s.id] = s; });
        const prefixe = 'api/souvenirs/' + encodeURIComponent(VOYAGE) + '/';
        lireFile().forEach(function (f) {
            if (!f.cle) return;
            if (f.cle.indexOf('proche:') === 0 && f.methode === 'POST') parProche[f.corps.id] = f.corps;
            else if (f.cle.indexOf('souvenir:') === 0) {
                if (f.methode === 'POST' && f.corps.voyage === VOYAGE) parSouvenir[f.corps.id] = f.corps;
                else if (f.methode === 'DELETE' && f.url.indexOf(prefixe) === 0) delete parSouvenir[f.cle.slice(9)];
            }
        });
        proches = Object.keys(parProche).map(function (k) { return parProche[k]; });
        souvenirs = Object.keys(parSouvenir).map(function (k) { return parSouvenir[k]; });
        historique = lu.historique || {};
    }
    function garder() {
        try { localStorage.setItem(CLE_COPIE, JSON.stringify({ proches: proches, souvenirs: souvenirs, historique: historique })); } catch (e) {}
    }
    function charger() {
        if (enEdition) return;
        fetch('api/souvenirs/' + encodeURIComponent(VOYAGE), { headers: { 'X-Valise-Vite': '1' } })
            .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
            .then(function (lu) { avecAttente(lu); garder(); afficher(); })
            .catch(function () {                                    // hors ligne : la dernière copie connue
                try { avecAttente(JSON.parse(localStorage.getItem(CLE_COPIE) || '{}')); } catch (e) {}
                afficher();
            });
    }
    function depensesARelire() { if (typeof chargerDepenses === 'function') chargerDepenses(); }
    function enregistrerProche(p) {
        proches = proches.filter(function (x) { return x.id !== p.id; }).concat([p]);
        garder(); afficher();
        envoyerOuGarder({ url: 'api/proches', methode: 'POST', corps: p, cle: 'proche:' + p.id }).catch(charger);
    }
    function enregistrer(modifie) {
        const s = Object.assign({}, modifie, { voyage: VOYAGE });       // la liste lue n'a pas le voyage
        souvenirs = souvenirs.filter(function (x) { return x.id !== s.id; }).concat([s]);
        garder(); afficher();
        return envoyerOuGarder({ url: 'api/souvenirs', methode: 'POST', corps: s, cle: 'souvenir:' + s.id })
            .then(depensesARelire, charger);                          // refusé : on réaffiche ce qu'a le serveur
    }
    function supprimer(s) {
        souvenirs = souvenirs.filter(function (x) { return x.id !== s.id; });
        garder(); afficher();
        envoyerOuGarder({ url: 'api/souvenirs/' + encodeURIComponent(VOYAGE) + '/' + encodeURIComponent(s.id),
                          methode: 'DELETE', cle: 'souvenir:' + s.id }).then(depensesARelire, charger);
    }

    function ligne(s) {
        const li = document.createElement('li'), corps = document.createElement('div');
        li.className = 'souvenir' + (s.achete ? ' achete' : '');
        const achat = s.achete
            ? deuxTemps('✅', 'Pas acheté ?', function () {
                enregistrer(Object.assign({}, s, { achete: false, prix: null, devise: null, prix_eur: null, paye_par: null, achete_le: null }));
            })
            : bouton('🛍️', function () { acheter(s); });
        achat.className = 'achat-btn'; achat.title = s.achete ? 'Annuler l\\u2019achat' : 'Acheté !';
        corps.className = 'corps';
        corps.append(para(s.idee, 'idee'));
        if (s.note) corps.append(para(s.note, 'note-souvenir'));
        if (s.achete) {
            let t = NOMBRE.format(Number(s.prix)) + ' ' + s.devise;
            if (s.devise !== 'EUR') t += ' ≈ ' + EUR.format(Number(s.prix_eur));
            if (PERSONNES.length > 1) t += ' · payé par ' + s.paye_par;
            corps.append(para(t, 'prix'));
        }
        const actions = document.createElement('div'); actions.className = 'actions';
        actions.append(bouton('✏️', function () { editer(s, s.proche); }),
                       deuxTemps('🗑️', 'Supprimer ?', function () { supprimer(s); }));
        corps.append(actions);
        li.append(achat, corps);
        return li;
    }

    function carte(p) {
        const div = document.createElement('div'), tete = document.createElement('div');
        div.className = 'proche'; tete.className = 'tete';
        const siens = souvenirs.filter(function (s) { return (s.proche || '') === p.id; })
            .sort(function (a, b) { return (a.achete - b.achete) || a.idee.localeCompare(b.idee); });
        const depense = siens.reduce(function (t, s) { return t + (s.achete ? Number(s.prix_eur) : 0); }, 0);
        tete.append(para((p.id ? '🎁 ' : '🏠 ') + (p.id ? p.nom : 'Pour nous'), 'nom-proche'));
        if (p.budget || depense) {
            const budget = document.createElement('span'); budget.className = 'budget';
            budget.textContent = EUR.format(depense) + (p.budget ? ' / ' + EUR.format(Number(p.budget)) : '');
            if (p.budget && depense > Number(p.budget)) budget.classList.add('depasse');
            tete.append(budget);
        }
        div.append(tete);
        const deja = historique[p.id];
        if (deja && deja.length) {
            div.append(para('Déjà rapporté : ' + deja.slice(0, 3).map(function (h) { return h.idee + ' (' + h.voyage + ')'; }).join(' · '),
                            'historique'));
        }
        if (siens.length) {
            const ul = document.createElement('ul');
            siens.forEach(function (s) { ul.append(ligne(s)); });
            div.append(ul);
        }
        const actions = document.createElement('div'); actions.className = 'actions';
        actions.append(bouton('➕ Idée', function () { editer(null, p.id); }));
        if (p.id) actions.append(bouton('✏️', function () { editerProche(p); }));
        div.append(actions);
        return div;
    }

    function afficher() {
        const zone = bloc.querySelector('.proches-zone');
        zone.replaceChildren();
        const visibles = proches.filter(function (p) { return !p.archive || souvenirs.some(function (s) { return s.proche === p.id; }); })
            .sort(function (a, b) { return a.nom.localeCompare(b.nom); });
        visibles.concat([{ id: '', nom: 'nous' }]).forEach(function (p) { zone.append(carte(p)); });
        const budget = visibles.reduce(function (t, p) { return t + (p.budget ? Number(p.budget) : 0); }, 0);
        const achetes = souvenirs.filter(function (s) { return s.achete; });
        const depense = achetes.reduce(function (t, s) { return t + Number(s.prix_eur); }, 0);
        let resume = visibles.length ? '' : 'Ajoute tes proches : le carnet servira aussi aux prochains voyages. ';
        if (souvenirs.length) resume += achetes.length + ' / ' + souvenirs.length + ' acheté' + (achetes.length > 1 ? 's' : '')
            + ' · ' + EUR.format(depense) + (budget ? ' sur ' + EUR.format(budget) + ' de budget' : '');
        else if (budget) resume += 'Budget : ' + EUR.format(budget);
        bloc.querySelector('.resume-souvenirs').textContent = resume;
    }

    // --- Panneau : saisie (au-dessus des listes) ---
    function ouvrirPanneau(titre) {
        enEdition = true;
        const h = document.createElement('h4'); h.textContent = titre;
        panneau.replaceChildren(h);
        panneau.scrollIntoView({ block: 'start', behavior: 'smooth' });
        return panneau;
    }
    function fermerPanneau() { enEdition = false; panneau.replaceChildren(); afficher(); }
    function champ(form, libelle, valeur, type, max) {
        const label = document.createElement('label'), c = document.createElement(type === 'textarea' ? 'textarea' : 'input');
        if (type && type !== 'textarea') c.type = type;
        c.value = valeur == null ? '' : valeur;
        if (max) c.maxLength = max;
        label.append(libelle, c); form.append(label);
        return c;
    }
    function liste(form, libelle, options, valeur) {
        const label = document.createElement('label'), sel = document.createElement('select');
        options.forEach(function (o) { const opt = document.createElement('option'); opt.value = o[0]; opt.textContent = o[1]; sel.append(opt); });
        sel.value = valeur;
        label.append(libelle, sel); form.append(label);
        return { label: label, select: sel };
    }
    function pied(form, texteOk) {
        const message = para('', 'message-souvenir');
        const actions = document.createElement('div'); actions.className = 'actions';
        const ok = document.createElement('button'); ok.type = 'submit'; ok.className = 'ctrl-btn'; ok.textContent = texteOk;
        actions.append(ok, bouton('Annuler', fermerPanneau));
        form.append(message, actions);
        return message;
    }
    function fermerSansRelire() { enEdition = false; panneau.replaceChildren(); }

    function editerProche(p) {
        const f = ouvrirPanneau(p ? '✏️ ' + p.nom : '➕ Un proche');
        const form = document.createElement('form');
        const nom = champ(form, 'Nom', p && p.nom, 'text', 80);
        const budget = champ(form, 'Budget en euros (facultatif)', p && p.budget, 'number');
        budget.min = '0'; budget.step = '1'; budget.inputMode = 'decimal';
        const message = pied(form, 'Enregistrer');
        if (p) form.append(deuxTemps('Retirer du carnet', 'Retirer ' + p.nom + ' ?', function () {
            fermerSansRelire(); enregistrerProche(Object.assign({}, p, { archive: true }));
        }));
        form.addEventListener('submit', function (ev) {
            ev.preventDefault();
            if (!nom.value.trim()) { message.textContent = '⚠️ Il faut un nom.'; return; }
            fermerSansRelire();
            enregistrerProche(Object.assign({ id: nouvelId(), archive: false }, p || {},
                                            { nom: nom.value.trim(), budget: budget.value ? Number(budget.value).toFixed(2) : null }));
        });
        f.append(form);
        nom.focus();
    }

    function editer(s, proche, propose) {
        const f = ouvrirPanneau(s ? '✏️ ' + s.idee : '➕ Une idée');
        const form = document.createElement('form');
        const pourQui = liste(form, 'Pour', proches.filter(function (p) { return !p.archive; })
                              .sort(function (a, b) { return a.nom.localeCompare(b.nom); })
                              .map(function (p) { return [p.id, p.nom]; }).concat([['', 'Nous']]), proche || '');
        const idee = champ(form, 'Idée', s ? s.idee : propose && propose.idee, 'text', 200);
        const note = champ(form, 'Note (où, taille, couleur…)', s ? s.note : propose && propose.note, 'textarea', 500);
        const message = pied(form, 'Enregistrer');
        form.addEventListener('submit', function (ev) {
            ev.preventDefault();
            if (!idee.value.trim()) { message.textContent = '⚠️ Il faut une idée.'; return; }
            fermerSansRelire();
            enregistrer(Object.assign({ id: nouvelId(), achete: false, prix: null, devise: null, prix_eur: null,
                                        paye_par: null, achete_le: null }, s || {},
                                      { proche: pourQui.select.value, idee: idee.value.trim(), note: note.value.trim() }));
        });
        f.append(form);
        idee.focus();
    }

    function acheter(s) {
        const f = ouvrirPanneau('🛍️ ' + s.idee + ' pour ' + nomDe(s.proche));
        const form = document.createElement('form');
        const prix = champ(form, 'Prix payé', '', 'number');
        prix.min = '0.01'; prix.step = '0.01'; prix.inputMode = 'decimal'; prix.required = true;
        const devise = liste(form, 'Devise', DEVISES.map(function (d) { return [d, d]; }), DEVISES[DEVISES.length > 1 ? 1 : 0]);
        const payeur = liste(form, 'Payé par', PERSONNES.map(function (p) { return [p, p]; }), PERSONNES[0]);
        if (PERSONNES.length < 2) payeur.label.hidden = true;
        const message = pied(form, 'Acheté ✅');
        form.addEventListener('submit', function (ev) {
            ev.preventDefault();
            const montant = Number(prix.value), code = devise.select.value;
            if (!(montant > 0)) { message.textContent = '⚠️ Indique le prix.'; return; }
            let enEuros = montant;
            if (code !== 'EUR') {
                const taux = typeof lireTauxGardes === 'function' ? lireTauxGardes() : null, t = taux && taux.eur[code.toLowerCase()];
                if (!t) { message.textContent = '⚠️ Pas de taux pour ' + code + ' : saisis le prix en euros.'; return; }
                enEuros = montant / t;
            }
            fermerSansRelire();
            enregistrer(Object.assign({}, s, { achete: true, prix: montant.toFixed(2), devise: code, prix_eur: enEuros.toFixed(2),
                                               paye_par: payeur.select.value, achete_le: aujourdhui() }));
        });
        f.append(form);
        prix.focus();
    }

    bloc.querySelector('.ajouter-proche').addEventListener('click', function () { editerProche(null); });
    bloc.querySelectorAll('button.ajouter-idee').forEach(function (b) {
        b.addEventListener('click', function () { editer(null, '', { idee: b.dataset.idee, note: b.dataset.note }); });
    });
    charger();
    document.addEventListener('visibilitychange', function () { if (!document.hidden) charger(); });
    document.addEventListener('file-videe', charger);
})();
"""
