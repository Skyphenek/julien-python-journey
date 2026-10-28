"""« 💡 À voir » (rubrique 🗓️ Programme) : la liste d'envies de chaque étape, remplie à deux,
avec des suggestions tirées de Wikivoyage, et un bouton 📅 qui place un lieu dans le Programme.

Suggestions : le téléphone télécharge la page Wikivoyage de l'étape (Render se fait refuser par
les API publiques), le serveur en extrait les lieux « Voir » et « Faire » (suggestions_depuis_wikitext).
"""
import json
import re
from datetime import date
from urllib.parse import quote

LONGUEURS = {"destination": 200, "nom": 200, "adresse": 300, "note": 1000, "lien": 500}
GENRES = {"voir": "voir", "see": "voir", "faire": "faire", "do": "faire"}   # modèle Wikivoyage -> genre
_ID = re.compile(r"[A-Za-z0-9-]{8,64}")


# --- Validation : tout ce qui vient du téléphone est vérifié ----------------------------------

def _texte(corps, cle):
    valeur = corps.get(cle) or ""
    if not isinstance(valeur, str):
        raise ValueError(f"{cle} invalide")
    valeur = valeur.strip()
    if len(valeur) > LONGUEURS[cle]:
        raise ValueError(f"{cle} trop long")
    return valeur


def valider_a_voir(corps):
    """JSON envoyé par la page -> envie propre (prevu en date) ; ValueError sinon."""
    if not isinstance(corps, dict):
        raise ValueError("envie invalide")
    ident, voyage, rang = corps.get("id"), corps.get("voyage"), corps.get("rang")
    if not isinstance(ident, str) or not _ID.fullmatch(ident):
        raise ValueError("id invalide")
    if not isinstance(voyage, str) or not voyage:
        raise ValueError("voyage invalide")
    if type(rang) is not int or not 1 <= rang <= 50:
        raise ValueError("étape invalide")
    e = {"id": ident, "voyage": voyage, "rang": rang, **{c: _texte(corps, c) for c in LONGUEURS}}
    if not e["destination"] or not e["nom"]:
        raise ValueError("nom ou étape manquant")
    if corps.get("genre") not in ("voir", "faire"):
        raise ValueError("genre inconnu")
    e["genre"] = corps["genre"]
    if not isinstance(corps.get("fait"), bool):
        raise ValueError("fait invalide")
    e["fait"] = corps["fait"]
    prevu = corps.get("prevu")
    try:
        e["prevu"] = date.fromisoformat(prevu) if prevu else None
    except (TypeError, ValueError):
        raise ValueError("date prévue invalide") from None
    if e["lien"] and not re.match(r"https?://", e["lien"], re.IGNORECASE):
        raise ValueError("lien : http(s) seulement")
    return e


# --- Suggestions : lire les lieux d'une page Wikivoyage (texte wiki brut) ---------------------

def _modeles(texte):
    """Le contenu de chaque modèle {{…}} de premier niveau (les modèles imbriqués restent dedans)."""
    i = 0
    while (debut := texte.find("{{", i)) >= 0:
        profondeur, j = 0, debut
        while j < len(texte):
            if texte.startswith("{{", j):
                profondeur, j = profondeur + 1, j + 2
            elif texte.startswith("}}", j):
                profondeur, j = profondeur - 1, j + 2
                if profondeur == 0:
                    break
            else:
                j += 1
        if profondeur != 0:                              # jamais fermé : on s'arrête là
            return
        yield texte[debut + 2:j - 2]
        i = j


def _scinder(corps):
    """« voir | nom=X | description=[[a|b]] » -> morceaux séparés par les | de premier niveau."""
    morceaux, courant, profondeur, k = [], [], 0, 0
    while k < len(corps):
        double = corps[k:k + 2]
        if double in ("{{", "[["):
            profondeur += 1
            courant.append(double)
            k += 2
        elif double in ("}}", "]]"):
            profondeur -= 1
            courant.append(double)
            k += 2
        else:
            if corps[k] == "|" and profondeur == 0:
                morceaux.append("".join(courant))
                courant = []
            else:
                courant.append(corps[k])
            k += 1
    morceaux.append("".join(courant))
    return morceaux


def _nettoyer(texte):
    """Texte wiki -> texte simple : sans références, modèles, liens ni gras."""
    texte = re.sub(r"<ref[^>]*/>", "", texte)
    texte = re.sub(r"<ref.*?</ref>", "", texte, flags=re.S)
    texte = re.sub(r"<[^>]+>", "", texte)
    while (sans := re.sub(r"\{\{[^{}]*\}\}", "", texte)) != texte:
        texte = sans
    texte = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r"\1", texte)
    texte = re.sub(r"\[https?://\S+\s+([^\]]*)\]", r"\1", texte)
    texte = re.sub(r"\[https?://\S+\]", "", texte)
    texte = texte.replace("'''", "").replace("''", "")
    texte = " ".join(texte.split())
    return re.sub(r"^[:,;.\-–]\s*", "", texte)


def suggestions_depuis_wikitext(texte, titre, langue):
    """Les lieux « Voir » et « Faire » d'une page Wikivoyage : [{nom, adresse, note, lien, genre}]."""
    page = f"https://{langue}.wikivoyage.org/wiki/{quote(titre.replace(' ', '_'))}"
    lieux, vus = [], set()
    for modele in _modeles(texte):
        morceaux = _scinder(modele)
        genre = GENRES.get(morceaux[0].strip().lower())
        if genre is None:
            continue
        champs = {}
        for morceau in morceaux[1:]:
            cle, egal, valeur = morceau.partition("=")
            if egal:
                champs[cle.strip().lower()] = valeur.strip()
        nom = _nettoyer(champs.get("nom") or champs.get("name") or "")[:LONGUEURS["nom"]]
        if not nom or nom.casefold() in vus:
            continue
        vus.add(nom.casefold())
        url = champs.get("url", "")
        lieux.append({"nom": nom,
                      "adresse": _nettoyer(champs.get("adresse") or champs.get("address") or "")[:LONGUEURS["adresse"]],
                      "note": _nettoyer(champs.get("description") or champs.get("content") or "")[:LONGUEURS["note"]],
                      "lien": url if re.match(r"https?://\S+$", url) else page,
                      "genre": genre})
    return lieux


# --- Page : le bloc (rempli par le script) ----------------------------------------------------

def bloc_a_voir(etapes):
    """Le bloc ; les étapes (JSON : nom, rang, dates, coordonnées) servent aux listes et suggestions."""
    if not etapes:
        return ""
    donnees = json.dumps([{"destination": e["destination"], "rang": e["rang"], "du": e["du"].isoformat(),
                           "au": e["au"].isoformat(), "lat": e.get("latitude"), "lon": e.get("longitude")}
                          for e in etapes], ensure_ascii=False).replace("</", "<\\/")
    return (f'<div class="info a-voir"><h3>💡 À voir</h3>'
            f'<script type="application/json" class="etapes-a-voir">{donnees}</script>'
            '<p class="conseil">Vos envies pour chaque étape. 💡 propose les lieux du guide Wikivoyage ; '
            '📅 les place dans le Programme.</p>'
            '<div class="panneau"></div><div class="etapes-zone"></div></div>')


STYLE_A_VOIR = """
div.a-voir details.etape-a-voir { border-top: 1px solid var(--ligne); padding: .4rem 0; }
div.a-voir details.etape-a-voir > summary { font-weight: 600; cursor: pointer; }
div.a-voir details.etape-a-voir .dates { font-weight: 400; font-size: .8rem; color: var(--doux); }
div.a-voir ul { list-style: none; margin: 0; padding: 0; }
div.a-voir li.envie { display: flex; gap: .5rem; align-items: flex-start; border-top: 1px solid var(--ligne); padding: .5rem 0; }
div.a-voir li.envie:first-child { border-top: none; }
div.a-voir li.envie .fait-btn { border: none; background: none; font-size: 1.2rem; cursor: pointer; padding: 0; }
div.a-voir li.envie .corps { flex: 1; min-width: 0; }
div.a-voir li.envie p { margin: .1rem 0; font-size: .9rem; overflow-wrap: anywhere; }
div.a-voir li.envie p.nom-envie { font-size: 1rem; font-weight: 600; }
div.a-voir li.envie.faite p.nom-envie { text-decoration: line-through; color: var(--doux); }
div.a-voir li.envie .note-envie { color: var(--doux); display: -webkit-box; -webkit-line-clamp: 3; line-clamp: 3;
    -webkit-box-orient: vertical; overflow: hidden; cursor: pointer; }
div.a-voir li.envie .note-envie.ouverte { display: block; -webkit-line-clamp: unset; line-clamp: unset; }
div.a-voir .actions { display: flex; flex-wrap: wrap; gap: .4rem; margin-top: .3rem; }
div.a-voir .actions button { font-size: .8rem; }
div.a-voir .vide-envies { color: var(--doux); font-size: .9rem; }
div.a-voir .panneau:empty { display: none; }
div.a-voir .panneau { background: var(--fond); border-radius: 12px; padding: .8rem; margin: .5rem 0; }
div.a-voir .panneau h4 { margin: 0 0 .4rem; }
div.a-voir .panneau label { display: block; font-size: .8rem; color: var(--doux); margin: .35rem 0; }
div.a-voir .panneau input, div.a-voir .panneau select, div.a-voir .panneau textarea {
    display: block; width: 100%; box-sizing: border-box; font-size: 1rem; padding: .4rem; margin-top: .15rem;
    border: 1px solid var(--ligne); border-radius: 8px; background: var(--carte); color: var(--texte); }
div.a-voir .panneau li.suggestion { display: flex; gap: .5rem; align-items: flex-start; border-top: 1px solid var(--ligne); padding: .45rem 0; }
div.a-voir .panneau li.suggestion .corps { flex: 1; min-width: 0; }
div.a-voir .panneau li.suggestion p { margin: .1rem 0; font-size: .85rem; overflow-wrap: anywhere; }
div.a-voir .panneau .source { font-size: .75rem; color: var(--doux); }
div.a-voir .panneau .message-envie { color: #dc2626; font-size: .85rem; }
"""

# Script du bloc. Isolé dans une fonction ; utilise la file d'attente hors ligne du script
# principal (envoyerOuGarder, lireFile). Pas de case à cocher : le script de la valise compte
# toutes les checkbox de la page. Tout le texte passe par textContent.
SCRIPT_A_VOIR = """
(function () {
    const bloc = document.querySelector('div.a-voir');
    if (!bloc) return;
    const ETAPES = JSON.parse(bloc.querySelector('.etapes-a-voir').textContent);
    const panneau = bloc.querySelector('.panneau');
    const CLE_COPIE = 'a-voir:' + VOYAGE;
    const SEMAINE = ['dim.', 'lun.', 'mar.', 'mer.', 'jeu.', 'ven.', 'sam.'];
    let envies = [];
    let enEdition = false;                                  // panneau ouvert : pas de rafraîchissement

    function iso(d) {
        return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0');
    }
    function decaler(jour, n) { const d = new Date(jour + 'T12:00:00'); d.setDate(d.getDate() + n); return iso(d); }
    function enClair(jour) { return SEMAINE[new Date(jour + 'T12:00:00').getDay()] + ' ' + jour.slice(8) + '/' + jour.slice(5, 7); }
    function para(texte, classe) { const p = document.createElement('p'); p.textContent = texte; if (classe) p.className = classe; return p; }
    function lien(texte, href) {
        const a = document.createElement('a'); a.textContent = texte; a.href = href; a.target = '_blank'; a.rel = 'noopener'; return a;
    }
    function bouton(texte, action) {
        const b = document.createElement('button'); b.type = 'button'; b.className = 'ctrl-btn'; b.textContent = texte;
        b.addEventListener('click', action); return b;
    }
    function nouvelId() {
        if (window.crypto && crypto.randomUUID) return crypto.randomUUID();
        return Date.now().toString(36) + '-' + Math.random().toString(36).slice(2, 10);
    }
    function deLEtape(etape) {
        return envies.filter(function (e) { return e.destination === etape.destination && e.rang === etape.rang; })
            .sort(function (a, b) { return (a.fait - b.fait) || a.nom.localeCompare(b.nom); });
    }

    // Ce qui attend dans la file (hors ligne) passe par-dessus la liste lue
    function avecAttente(liste) {
        const parId = {};
        liste.forEach(function (e) { parId[e.id] = e; });
        const prefixe = 'api/a-voir/' + encodeURIComponent(VOYAGE) + '/';
        lireFile().forEach(function (f) {
            if (!f.cle || f.cle.indexOf('envie:') !== 0) return;
            if (f.methode === 'POST' && f.corps.voyage === VOYAGE) parId[f.corps.id] = f.corps;
            else if (f.methode === 'DELETE' && f.url.indexOf(prefixe) === 0) delete parId[f.cle.slice(6)];
        });
        return Object.keys(parId).map(function (k) { return parId[k]; });
    }
    function garder() { try { localStorage.setItem(CLE_COPIE, JSON.stringify(envies)); } catch (e) {} }
    function charger() {
        if (enEdition) return;
        fetch('api/a-voir/' + encodeURIComponent(VOYAGE), { headers: { 'X-Valise-Vite': '1' } })
            .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
            .then(function (liste) { envies = avecAttente(liste); garder(); afficher(); })
            .catch(function () {                                    // hors ligne : la dernière copie connue
                try { envies = avecAttente(JSON.parse(localStorage.getItem(CLE_COPIE) || '[]')); } catch (e) {}
                afficher();
            });
    }
    function enregistrer(modifiee) {
        const envie = Object.assign({}, modifiee, { voyage: VOYAGE });   // la liste lue n'a pas le voyage
        envies = envies.filter(function (x) { return x.id !== envie.id; }).concat([envie]);
        garder(); afficher();
        const envoi = envoyerOuGarder({ url: 'api/a-voir', methode: 'POST', corps: envie, cle: 'envie:' + envie.id });
        envoi.catch(charger);                                          // refusé : on réaffiche ce qu'a le serveur
        return envoi;
    }
    function supprimer(envie) {
        envies = envies.filter(function (x) { return x.id !== envie.id; });
        garder(); afficher();
        envoyerOuGarder({ url: 'api/a-voir/' + encodeURIComponent(VOYAGE) + '/' + encodeURIComponent(envie.id),
                          methode: 'DELETE', cle: 'envie:' + envie.id }).catch(charger);
    }

    function fiche(envie, etape) {
        const li = document.createElement('li'), corps = document.createElement('div');
        li.className = 'envie' + (envie.fait ? ' faite' : '');
        const fait = bouton(envie.fait ? '✅' : '⬜', function () { enregistrer(Object.assign({}, envie, { fait: !envie.fait })); });
        fait.className = 'fait-btn'; fait.title = envie.fait ? 'Pas encore fait' : 'Fait !';
        corps.className = 'corps';
        corps.append(para((envie.genre === 'faire' ? '🎯 ' : '') + envie.nom, 'nom-envie'));
        if (envie.note) {                                       // longue note du guide : 3 lignes, un tap déplie
            const note = para(envie.note, 'note-envie');
            note.addEventListener('click', function () { note.classList.toggle('ouverte'); });
            corps.append(note);
        }
        const ou = para('📍 ' + (envie.adresse || 'Sur la carte') + ' ');
        ou.append(lien('↗ Maps', 'https://www.google.com/maps/search/?api=1&query='
                       + encodeURIComponent(envie.adresse ? envie.adresse + ', ' + etape.destination : envie.nom + ', ' + etape.destination)));
        corps.append(ou);
        if (envie.lien && /^https?:\\/\\//i.test(envie.lien)) { const p = para('🔗 '); p.append(lien('En savoir plus', envie.lien)); corps.append(p); }
        if (envie.prevu) corps.append(para('📅 Prévu ' + enClair(envie.prevu)));
        const actions = document.createElement('div'); actions.className = 'actions';
        const suppr = bouton('🗑️', function () {
            if (!suppr.dataset.confirmer) { suppr.dataset.confirmer = '1'; suppr.textContent = 'Supprimer ?'; return; }
            supprimer(envie);
        });
        actions.append(bouton('📅 Planifier', function () { planifier(envie, etape); }),
                       bouton('✏️', function () { editer(envie, etape); }), suppr);
        corps.append(actions);
        li.append(fait, corps);
        return li;
    }

    function afficher() {
        const zone = bloc.querySelector('.etapes-zone'), auj = iso(new Date());
        zone.replaceChildren();
        ETAPES.forEach(function (etape) {
            const details = document.createElement('details'), resume = document.createElement('summary');
            const siennes = deLEtape(etape);
            details.className = 'etape-a-voir';
            details.open = etape.au >= auj;                            // étape passée : repliée
            resume.textContent = etape.destination + ' ';
            const dates = document.createElement('span'); dates.className = 'dates';
            dates.textContent = enClair(etape.du) + ' → ' + enClair(etape.au)
                + (siennes.length ? ' · ' + siennes.filter(function (e) { return e.fait; }).length + '/' + siennes.length : '');
            resume.append(dates);
            details.append(resume);
            const ul = document.createElement('ul');
            siennes.forEach(function (e) { ul.append(fiche(e, etape)); });
            details.append(siennes.length ? ul : para('Rien pour l\\u2019instant.', 'vide-envies'));
            const actions = document.createElement('div'); actions.className = 'actions';
            actions.append(bouton('➕ Ajouter', function () { editer(null, etape); }),
                           bouton('💡 Suggestions', function () { suggerer(etape); }));
            details.append(actions);
            zone.append(details);
        });
    }

    // --- Panneau : saisie, suggestions, planification (au-dessus des listes) ---
    function ouvrirPanneau(titre) {
        enEdition = true;
        const h = document.createElement('h4'); h.textContent = titre;
        panneau.replaceChildren(h);
        panneau.scrollIntoView({ block: 'start', behavior: 'smooth' });
        return panneau;
    }
    function fermerPanneau() { enEdition = false; panneau.replaceChildren(); afficher(); }
    function champ(form, nom, libelle, valeur, type) {
        const label = document.createElement('label'), c = document.createElement(type === 'textarea' ? 'textarea' : 'input');
        if (type && type !== 'textarea') c.type = type;
        c.name = nom; c.value = valeur || ''; c.maxLength = nom === 'note' ? 1000 : nom === 'lien' ? 500 : 300;
        label.append(libelle, c); form.append(label);
        return c;
    }

    function editer(envie, etape) {
        const p = ouvrirPanneau((envie ? '✏️ ' + envie.nom : '➕ À voir à ' + etape.destination));
        const form = document.createElement('form');
        const nom = champ(form, 'nom', 'Nom du lieu', envie && envie.nom);
        const adresse = champ(form, 'adresse', 'Adresse (facultatif)', envie && envie.adresse);
        const note = champ(form, 'note', 'Note (horaires, prix, conseil…)', envie && envie.note, 'textarea');
        const lienSaisi = champ(form, 'lien', 'Lien (https://…)', envie && envie.lien, 'url');
        const message = para('', 'message-envie');
        const actions = document.createElement('div'); actions.className = 'actions';
        const ok = document.createElement('button'); ok.type = 'submit'; ok.className = 'ctrl-btn'; ok.textContent = 'Enregistrer';
        actions.append(ok, bouton('Annuler', fermerPanneau));
        form.append(message, actions);
        form.addEventListener('submit', function (ev) {
            ev.preventDefault();
            if (!nom.value.trim()) { message.textContent = '⚠️ Il faut un nom.'; return; }
            if (lienSaisi.value.trim() && !/^https?:\\/\\//i.test(lienSaisi.value.trim())) { message.textContent = '⚠️ Le lien doit commencer par https://'; return; }
            const corps = Object.assign({ id: nouvelId(), voyage: VOYAGE, destination: etape.destination, rang: etape.rang,
                                          genre: 'voir', fait: false, prevu: null }, envie || {},
                                        { nom: nom.value.trim(), adresse: adresse.value.trim(), note: note.value.trim(), lien: lienSaisi.value.trim() });
            enEdition = false;
            panneau.replaceChildren();
            enregistrer(corps).catch(function () { charger(); });
        });
        p.append(form);
        nom.focus();
    }

    function planifier(envie, etape) {
        const p = ouvrirPanneau('📅 ' + envie.nom + ' dans le Programme');
        const form = document.createElement('form');
        const label = document.createElement('label'), jour = document.createElement('select');
        const premier = typeof DEPART !== 'undefined' ? DEPART : etape.du, dernier = typeof FIN !== 'undefined' ? FIN : etape.au;
        for (let j = premier; j <= dernier; j = decaler(j, 1)) {
            const o = document.createElement('option'); o.value = j; o.textContent = enClair(j) + (j >= etape.du && j <= etape.au ? ' · ' + etape.destination : '');
            jour.append(o);
        }
        jour.value = envie.prevu || (iso(new Date()) >= etape.du && iso(new Date()) <= etape.au ? iso(new Date()) : etape.du);
        label.append('Le', jour); form.append(label);
        const heure = champ(form, 'heure', 'Heure (facultatif)', '', 'time');
        const actions = document.createElement('div'); actions.className = 'actions';
        const ok = document.createElement('button'); ok.type = 'submit'; ok.className = 'ctrl-btn'; ok.textContent = 'Ajouter au Programme';
        actions.append(ok, bouton('Annuler', fermerPanneau));
        const message = para('', 'message-envie');
        form.append(message, actions);
        form.addEventListener('submit', function (ev) {
            ev.preventDefault();
            const resa = { id: nouvelId(), voyage: VOYAGE, type: 'activite', titre: envie.nom.slice(0, 200), jour: jour.value,
                           heure: heure.value, jour_fin: null, heure_fin: '',
                           lieu: (envie.adresse || envie.nom + ', ' + etape.destination).slice(0, 300),
                           reference: '', telephone: '', lien: envie.lien, notes: envie.note };
            ok.disabled = true;
            envoyerOuGarder({ url: 'api/reservations', methode: 'POST', corps: resa, cle: 'resa:' + resa.id })
                .then(function () {
                    document.dispatchEvent(new Event('programme-a-recharger'));
                    enEdition = false;
                    panneau.replaceChildren();
                    return enregistrer(Object.assign({}, envie, { prevu: jour.value }));
                })
                .catch(function () { ok.disabled = false; message.textContent = '⚠️ Refusé par le serveur.'; });
        });
        p.append(form);
    }

    // --- Suggestions : pages Wikivoyage téléchargées par le téléphone, lues par le serveur ---
    function wikivoyage(langue, parametres) {
        return fetch('https://' + langue + '.wikivoyage.org/w/api.php?format=json&origin=*&' + parametres)
            .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); });
    }
    function lirePage(langue, titre) {
        return wikivoyage(langue, 'action=parse&prop=wikitext&redirects=1&page=' + encodeURIComponent(titre))
            .then(function (j) { return j.error ? null : { langue: langue, titre: j.parse.title, texte: j.parse.wikitext['*'] }; });
    }
    // La page de l'étape : celle à son nom, sinon la 1re de la recherche (Hạ Long -> Baie de Ha Long),
    // sinon la plus proche de ses coordonnées
    function pageDe(langue, etape) {
        return lirePage(langue, etape.destination).then(function (page) {
            if (page) return page;
            return wikivoyage(langue, 'action=query&list=search&srlimit=1&srsearch=' + encodeURIComponent(etape.destination))
                .then(function (j) { const p = j.query && j.query.search[0]; return p ? lirePage(langue, p.title) : null; });
        }).then(function (page) {
            if (page || etape.lat == null) return page;
            return wikivoyage(langue, 'action=query&list=geosearch&gsradius=15000&gslimit=1&gscoord=' + etape.lat + '%7C' + etape.lon)
                .then(function (j) { const p = j.query && j.query.geosearch[0]; return p ? lirePage(langue, p.title) : null; });
        }).catch(function () { return null; });
    }
    function lire(pages) {
        return fetch('api/a-voir/suggestions', { method: 'POST', headers: { 'Content-Type': 'application/json' },
                                                 body: JSON.stringify({ pages: pages }) })
            .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
            .then(function (r) { return r.suggestions; });
    }
    function chercher(etape) {
        return pageDe('fr', etape).then(function (fr) {
            const pages = fr ? [fr] : [];
            return lire(pages).then(function (s) {
                if (s.length >= 15) return { suggestions: s, pages: pages };
                return pageDe('en', etape).then(function (en) {                      // page française maigre
                    if (en) pages.push(en);
                    return lire(pages).then(function (s2) { return { suggestions: s2, pages: pages }; });
                });
            });
        });
    }
    function suggerer(etape) {
        const p = ouvrirPanneau('💡 Suggestions pour ' + etape.destination);
        const attente = para('⏳ Recherche dans Wikivoyage…');
        p.append(attente, bouton('Fermer', fermerPanneau));
        chercher(etape).then(function (res) {
            attente.remove();
            const deja = deLEtape(etape).map(function (e) { return e.nom.toLowerCase(); });
            const nouvelles = res.suggestions.filter(function (s) { return deja.indexOf(s.nom.toLowerCase()) === -1; });
            if (!nouvelles.length) { p.insertBefore(para(res.pages.length ? 'Rien de plus dans le guide pour cette étape.' : 'Pas de page Wikivoyage pour cette étape.'), p.lastChild); return; }
            const ul = document.createElement('ul');
            nouvelles.forEach(function (s) {
                const li = document.createElement('li'), corps = document.createElement('div');
                li.className = 'suggestion'; corps.className = 'corps';
                corps.append(para((s.genre === 'faire' ? '🎯 ' : '') + s.nom, 'nom-envie'));
                if (s.note) corps.append(para(s.note.length > 180 ? s.note.slice(0, 180) + '…' : s.note));
                const ajouter = bouton('➕', function () {
                    ajouter.disabled = true; ajouter.textContent = '✓';
                    enregistrer(Object.assign({ id: nouvelId(), voyage: VOYAGE, destination: etape.destination, rang: etape.rang,
                                                fait: false, prevu: null }, s)).catch(function () {});
                });
                ajouter.title = 'Ajouter à la liste';
                li.append(corps, ajouter);
                ul.append(li);
            });
            p.insertBefore(ul, p.lastChild);
            const source = para('Source : ', 'source');
            res.pages.forEach(function (page, i) {
                if (i) source.append(', ');
                source.append(lien('Wikivoyage (' + page.langue + ') « ' + page.titre + ' »',
                                   'https://' + page.langue + '.wikivoyage.org/wiki/' + encodeURIComponent(page.titre.replace(/ /g, '_'))));
            });
            source.append(' · licence CC BY-SA');
            p.insertBefore(source, p.lastChild);
        }).catch(function () {
            attente.textContent = '⚠️ Suggestions indisponibles (réseau ?) : réessaie plus tard.';
        });
    }

    charger();
    document.addEventListener('visibilitychange', function () { if (!document.hidden) charger(); });
    document.addEventListener('file-videe', charger);
})();
"""
