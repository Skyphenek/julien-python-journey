"""Carnet 🗓️ Programme : tout ce qui est réservé pour le voyage (vols, hôtels, transports,
activités, restos…), affiché jour par jour, saisi à deux, lisible hors ligne.

Le serveur valide et stocke (table reservations) ; la page affiche et saisit (SCRIPT_PROGRAMME).
"""
import hashlib
import json
import re
from datetime import date, timedelta

TYPES_RESERVATION = {"vol": "✈️ Vol", "hotel": "🏨 Hôtel", "transport": "🚆 Transport",
                     "activite": "🎟️ Activité", "resto": "🍽️ Resto", "autre": "📌 Autre"}
LONGUEURS = {"titre": 200, "lieu": 300, "reference": 200, "telephone": 50, "lien": 500, "notes": 2000}
_HEURE = re.compile(r"(?:[01]\d|2[0-3]):[0-5]\d")
_ID = re.compile(r"[A-Za-z0-9-]{8,64}")         # choisi par le téléphone (crypto.randomUUID)


def etapes_du_voyage(itineraire, depart):
    """[{"destination", "rang", "du", "au"}] : rang = 1re, 2e… visite de la même ville."""
    etapes, vues, debut = [], {}, depart
    for etape in itineraire:
        vues[etape["destination"]] = vues.get(etape["destination"], 0) + 1
        fin = debut + timedelta(days=etape["jours"] - 1)
        etapes.append({"destination": etape["destination"], "rang": vues[etape["destination"]],
                       "du": debut, "au": fin})
        debut = fin + timedelta(days=1)
    return etapes


# --- Validation : tout ce qui vient du téléphone est vérifié ----------------------------------

def _texte(corps, cle):
    valeur = corps.get(cle) or ""
    if not isinstance(valeur, str):
        raise ValueError(f"{cle} invalide")
    valeur = valeur.strip()
    if len(valeur) > LONGUEURS.get(cle, 5):
        raise ValueError(f"{cle} trop long")
    return valeur


def _jour(valeur, cle):
    if not isinstance(valeur, str):
        raise ValueError(f"{cle} invalide")
    try:
        return date.fromisoformat(valeur)
    except ValueError:
        raise ValueError(f"{cle} invalide") from None


def valider_reservation(corps):
    """JSON envoyé par la page -> réservation propre (dates en date) ; ValueError sinon."""
    if not isinstance(corps, dict):
        raise ValueError("réservation invalide")
    ident, voyage, genre = corps.get("id"), corps.get("voyage"), corps.get("type")
    if not isinstance(ident, str) or not _ID.fullmatch(ident):
        raise ValueError("id invalide")
    if not isinstance(voyage, str) or not voyage:
        raise ValueError("voyage invalide")
    if genre not in TYPES_RESERVATION:
        raise ValueError("type inconnu")
    r = {"id": ident, "voyage": voyage, "type": genre, **{c: _texte(corps, c) for c in LONGUEURS}}
    if not r["titre"]:
        raise ValueError("titre manquant")
    r["jour"] = _jour(corps.get("jour"), "jour")
    r["jour_fin"] = _jour(corps["jour_fin"], "jour_fin") if corps.get("jour_fin") else None
    for cle in ("heure", "heure_fin"):
        r[cle] = _texte(corps, cle)
        if r[cle] and not _HEURE.fullmatch(r[cle]):
            raise ValueError(f"{cle} invalide (HH:MM)")
    if genre == "hotel" and (r["jour_fin"] is None or r["jour_fin"] <= r["jour"]):
        raise ValueError("hôtel : date de départ après l'arrivée")
    if r["jour_fin"] is not None and r["jour_fin"] < r["jour"]:
        raise ValueError("fin avant le début")
    if r["lien"] and not re.match(r"https?://", r["lien"], re.IGNORECASE):
        raise ValueError("lien : http(s) seulement")
    return r


# --- Reprise des anciennes fiches d'étapes (infos_etape) en réservations « Hôtel » -------------

def hotels_depuis_infos(code, itineraire, depart, infos):
    """Une fiche remplie -> un hôtel du premier au dernier soir de l'étape (départ le lendemain).

    id tiré du voyage et de l'étape : la reprise peut être rejouée sans doublon.
    """
    etapes = {(e["destination"], e["rang"]): e for e in etapes_du_voyage(itineraire, depart)}
    hotels = []
    for info in infos:
        etape = etapes.get((info["destination"], info["rang"]))
        if etape is None or not any(info.get(c) for c in ("hebergement", "adresse", "reservation",
                                                             "arrivee", "notes")):
            continue                                   # étape retirée depuis, ou fiche vide
        notes = [f"Arrivée : {info['arrivee']}"] if info.get("arrivee") else []
        notes += [info["notes"]] if info.get("notes") else []
        empreinte = hashlib.sha1(f"{code}|{info['destination']}|{info['rang']}".encode()).hexdigest()[:16]
        hotels.append({"id": f"etape-{empreinte}", "voyage": code, "type": "hotel",
                       "titre": (info.get("hebergement") or f"Hébergement {info['destination']}")[:200],
                       "jour": etape["du"], "heure": "", "jour_fin": etape["au"] + timedelta(days=1),
                       "heure_fin": "", "lieu": info.get("adresse") or "", "reference": info.get("reservation") or "",
                       "telephone": "", "lien": "", "notes": "\n".join(notes)})
    return hotels


# --- Page : le bloc (rempli par le script) ----------------------------------------------------

def bloc_programme(etapes):
    """Le carnet ; les étapes (JSON) servent à titrer chaque jour (« ven. 15/01 · Hanoï »)."""
    donnees = json.dumps([{"destination": e["destination"], "du": e["du"].isoformat(), "au": e["au"].isoformat()}
                          for e in etapes], ensure_ascii=False).replace("</", "<\\/")
    return (f'<div class="programme"><script type="application/json" class="etapes-programme">{donnees}</script>'
            '<button type="button" class="ctrl-btn ajouter-resa">➕ Ajouter</button>'
            '<div class="form-zone"></div><div class="jours"></div></div>')


STYLE_PROGRAMME = """
div.programme .ajouter-resa { margin-bottom: .75rem; }
div.programme details.jour { background: var(--carte); border-radius: 12px; margin-bottom: .6rem; padding: .5rem .8rem; }
div.programme details.jour > summary { font-weight: 600; cursor: pointer; padding: .2rem 0; list-style: none;
    display: flex; align-items: center; gap: .3rem; }
div.programme details.jour > summary::-webkit-details-marker { display: none; }
div.programme details.jour > summary::after { margin-left: auto; }
div.programme details.jour.passe > summary { color: var(--doux); }
div.programme details.jour.aujourdhui { outline: 2px solid var(--accent); }
div.programme .badge-jour { font-size: .7rem; background: var(--accent); color: #fff; border-radius: 6px; padding: .05rem .4rem; margin-left: .3rem; }
div.programme ul { list-style: none; margin: 0; padding: 0; }
div.programme li.resa { border-top: 1px solid var(--ligne); padding: .5rem 0; }
div.programme li.resa:first-child { border-top: none; }
div.programme li.resa p { margin: .15rem 0; font-size: .9rem; overflow-wrap: anywhere; }
div.programme li.resa p.titre-resa { font-size: 1rem; }
div.programme li.resa.compacte p { color: var(--doux); }
div.programme li.resa .actions { display: flex; gap: .4rem; margin-top: .3rem; }
div.programme li.resa .actions button { font-size: .8rem; }
div.programme .vide-programme { color: var(--doux); }
div.programme form.form-resa { background: var(--carte); border-radius: 12px; padding: .8rem; margin-bottom: .8rem; }
div.programme form.form-resa label { display: block; font-size: .8rem; color: var(--doux); margin: .35rem 0; }
div.programme form.form-resa label[hidden] { display: none; }
div.programme form.form-resa input, div.programme form.form-resa select, div.programme form.form-resa textarea {
    display: block; width: 100%; box-sizing: border-box; font-size: 1rem; padding: .4rem; margin-top: .15rem;
    border: 1px solid var(--ligne); border-radius: 8px; background: var(--fond); color: var(--texte); }
div.programme form.form-resa .actions { display: flex; gap: .4rem; margin-top: .6rem; }
div.programme form.form-resa .message-resa { color: #dc2626; font-size: .85rem; }
"""

# Script du carnet. Dans une fonction isolée : ses noms ne touchent pas au script principal,
# dont il utilise la file d'attente hors ligne (envoyerOuGarder, lireFile). Tout le texte
# saisi passe par textContent, jamais par du HTML.
SCRIPT_PROGRAMME = """
(function () {
    const bloc = document.querySelector('div.programme');
    if (!bloc) return;
    const ETAPES = JSON.parse(bloc.querySelector('.etapes-programme').textContent);
    const TYPES = { vol: ['✈️', 'Vol'], hotel: ['🏨', 'Hôtel'], transport: ['🚆', 'Transport'],
                    activite: ['🎟️', 'Activité'], resto: ['🍽️', 'Resto'], autre: ['📌', 'Autre'] };
    // Libellé de chaque champ selon le type ; absent = champ caché
    const COMMUNS = { reference: 'Réservation (référence)', lien: 'Lien (https://…)', notes: 'Notes' };
    const LIBELLES = {
        vol: { titre: 'N° de vol (ex. AF 198)', jour: 'Départ le', heure: 'Heure de départ',
               jour_fin: 'Arrivée le (si un autre jour)', heure_fin: "Heure d'arrivée", lieu: 'Trajet (ex. CDG → HAN)' },
        hotel: { titre: "Nom de l'hôtel", jour: 'Arrivée le', heure: "Heure d'arrivée", jour_fin: 'Départ le',
                 heure_fin: 'Heure de départ', lieu: 'Adresse', telephone: 'Téléphone' },
        transport: { titre: 'Quoi (ex. train de nuit SE3, bus, bateau)', jour: 'Départ le', heure: 'Heure de départ',
                     jour_fin: 'Arrivée le (si un autre jour)', heure_fin: "Heure d'arrivée", lieu: 'Trajet (ex. Hanoï → Hué)' },
        activite: { titre: 'Activité', jour: 'Le', heure: 'Heure', lieu: 'Adresse ou rendez-vous', telephone: 'Téléphone' },
        resto: { titre: 'Restaurant', jour: 'Le', heure: 'Heure', lieu: 'Adresse', telephone: 'Téléphone' },
        autre: { titre: 'Quoi', jour: 'Le', heure: 'Heure', jour_fin: "Jusqu'au (si plusieurs jours)", lieu: 'Adresse',
                 telephone: 'Téléphone' }
    };
    const CHAMPS = ['titre', 'jour', 'heure', 'jour_fin', 'heure_fin', 'lieu', 'telephone', 'reference', 'lien', 'notes'];
    const ADRESSE = { hotel: true, activite: true, resto: true, autre: true };        // lieu = adresse : lien Maps
    const SEMAINE = ['dim.', 'lun.', 'mar.', 'mer.', 'jeu.', 'ven.', 'sam.'];
    const CLE_COPIE = 'programme:' + VOYAGE;
    let reservations = [];
    let enEdition = null;                                  // pas de rafraîchissement pendant une saisie

    function iso(d) {
        return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0');
    }
    function decaler(jour, n) { const d = new Date(jour + 'T12:00:00'); d.setDate(d.getDate() + n); return iso(d); }
    function ecart(du, au) { return Math.round((new Date(au + 'T12:00:00') - new Date(du + 'T12:00:00')) / 86400000); }
    function enClair(jour) { return SEMAINE[new Date(jour + 'T12:00:00').getDay()] + ' ' + jour.slice(8) + '/' + jour.slice(5, 7); }
    function etapeDu(jour) { const e = ETAPES.find(function (e) { return e.du <= jour && jour <= e.au; }); return e ? e.destination : ''; }
    function para(texte, classe) { const p = document.createElement('p'); p.textContent = texte; if (classe) p.className = classe; return p; }
    function lien(texte, href) {
        const a = document.createElement('a'); a.textContent = texte; a.href = href; a.target = '_blank'; a.rel = 'noopener'; return a;
    }
    function nouvelId() {
        if (window.crypto && crypto.randomUUID) return crypto.randomUUID();
        return Date.now().toString(36) + '-' + Math.random().toString(36).slice(2, 10);
    }

    // Ce qui attend dans la file (hors ligne) passe par-dessus la liste lue
    function avecAttente(liste) {
        const parId = {};
        liste.forEach(function (r) { parId[r.id] = r; });
        const prefixe = 'api/reservations/' + encodeURIComponent(VOYAGE) + '/';
        lireFile().forEach(function (e) {
            if (!e.cle || e.cle.indexOf('resa:') !== 0) return;
            if (e.methode === 'POST' && e.corps.voyage === VOYAGE) parId[e.corps.id] = e.corps;
            else if (e.methode === 'DELETE' && e.url.indexOf(prefixe) === 0) delete parId[e.cle.slice(5)];
        });
        return Object.keys(parId).map(function (k) { return parId[k]; });
    }
    function enFile() {
        const ids = {};
        lireFile().forEach(function (e) { if (e.cle && e.cle.indexOf('resa:') === 0) ids[e.cle.slice(5)] = true; });
        return ids;
    }
    function garder() { try { localStorage.setItem(CLE_COPIE, JSON.stringify(reservations)); } catch (e) {} }

    // Chaque réservation placée sur ses jours : le jour même (fiche complète), puis les nuits
    // d'hôtel et le jour de départ / d'arrivée (une ligne courte)
    function parJour() {
        const jours = {};
        function placer(jour, entree) { (jours[jour] = jours[jour] || []).push(entree); }
        reservations.forEach(function (r) {
            placer(r.jour, { r: r, role: 'debut' });
            if (!r.jour_fin || r.jour_fin <= r.jour) return;
            if (r.type === 'hotel') {
                const nuits = ecart(r.jour, r.jour_fin);
                for (let n = 2; n <= nuits; n++) placer(decaler(r.jour, n - 1), { r: r, role: 'nuit', n: n, total: nuits });
            }
            placer(r.jour_fin, { r: r, role: 'fin' });
        });
        const ordre = { fin: 0, debut: 1, nuit: 2 };
        Object.keys(jours).forEach(function (j) {
            jours[j].sort(function (a, b) {
                if (ordre[a.role] !== ordre[b.role]) return ordre[a.role] - ordre[b.role];
                const ha = a.r.heure || '99', hb = b.r.heure || '99';
                return ha < hb ? -1 : ha > hb ? 1 : 0;
            });
        });
        return jours;
    }

    function ligneLieu(r) {
        if (!r.lieu) return null;
        const p = para('📍 ' + r.lieu);
        if (ADRESSE[r.type]) p.append(' ', lien('↗ Maps', 'https://www.google.com/maps/search/?api=1&query=' + encodeURIComponent(r.lieu)));
        return p;
    }

    function fiche(entree, attente) {
        const r = entree.r, li = document.createElement('li'), emoji = TYPES[r.type][0];
        li.className = 'resa';
        if (entree.role !== 'debut') {                         // ligne courte : nuit d'hôtel, départ, arrivée
            li.classList.add('compacte');
            let texte;
            if (r.type === 'hotel' && entree.role === 'nuit') texte = emoji + ' ' + r.titre + ' · nuit ' + entree.n + '/' + entree.total;
            else if (r.type === 'hotel') texte = emoji + ' Départ' + (r.heure_fin ? ' ' + r.heure_fin : '') + ' · ' + r.titre;
            else texte = emoji + (r.type === 'autre' ? ' Fin' : ' Arrivée') + (r.heure_fin ? ' ' + r.heure_fin : '') + ' · ' + r.titre;
            li.append(para(texte));
            if (r.type === 'hotel' && entree.role === 'nuit') { const l = ligneLieu(r); if (l) li.append(l); }
            return li;
        }
        let titre = (attente ? '⏳ ' : '') + emoji + ' ' + (r.heure ? r.heure + ' · ' : '') + r.titre;
        if (r.type !== 'hotel' && r.heure_fin && !(r.jour_fin && r.jour_fin > r.jour)) titre += ' → ' + r.heure_fin;
        li.append(para(titre, 'titre-resa'));
        if (r.type === 'hotel') {
            const nuits = ecart(r.jour, r.jour_fin);
            li.append(para('🛏️ ' + nuits + (nuits > 1 ? ' nuits' : ' nuit') + ', départ ' + enClair(r.jour_fin)
                           + (r.heure_fin ? ' à ' + r.heure_fin : '')));
        } else if (r.jour_fin && r.jour_fin > r.jour) {
            li.append(para('↘ Arrivée ' + enClair(r.jour_fin) + (r.heure_fin ? ' à ' + r.heure_fin : '')));
        }
        const l = ligneLieu(r); if (l) li.append(l);
        if (r.reference) li.append(para('🎫 ' + r.reference));
        if (r.telephone) { const p = para('📞 '); p.append(lien(r.telephone, 'tel:' + r.telephone.replace(/[^0-9+]/g, ''))); li.append(p); }
        if (r.lien && /^https?:\\/\\//i.test(r.lien)) { const p = para('🔗 '); p.append(lien('Ouvrir le lien', r.lien)); li.append(p); }
        if (r.notes) r.notes.split('\\n').forEach(function (t) { if (t.trim()) li.append(para('📝 ' + t)); });
        const actions = document.createElement('div'); actions.className = 'actions';
        const modifier = document.createElement('button');
        modifier.type = 'button'; modifier.className = 'ctrl-btn'; modifier.textContent = '✏️ Modifier';
        modifier.addEventListener('click', function () { editer(r); });
        const suppr = document.createElement('button');
        suppr.type = 'button'; suppr.className = 'ctrl-btn'; suppr.textContent = '🗑️';
        suppr.addEventListener('click', function () {
            if (!suppr.dataset.confirmer) { suppr.dataset.confirmer = '1'; suppr.textContent = 'Supprimer ?'; return; }
            supprimer(r);
        });
        actions.append(modifier, suppr);
        li.append(actions);
        return li;
    }

    function afficher() {
        const zone = bloc.querySelector('.jours');
        zone.replaceChildren();
        const jours = parJour(), liste = Object.keys(jours).sort(), attente = enFile(), auj = iso(new Date());
        if (!liste.length) {
            zone.append(para('Rien de réservé pour l\\u2019instant : ajoute tes vols, hôtels, activités, restos…', 'vide-programme'));
            return;
        }
        let ouvert = null;
        liste.forEach(function (jour) {
            const details = document.createElement('details'), resume = document.createElement('summary');
            details.className = 'jour';
            const etape = etapeDu(jour);
            resume.textContent = enClair(jour) + (etape ? ' · ' + etape : '');
            if (jour === auj) {
                details.classList.add('aujourdhui');
                const badge = document.createElement('span'); badge.className = 'badge-jour'; badge.textContent = 'aujourd\\u2019hui';
                resume.append(badge);
                ouvert = details;
            }
            if (jour < auj) details.classList.add('passe'); else details.open = true;
            const ul = document.createElement('ul');
            jours[jour].forEach(function (e) { ul.append(fiche(e, attente[e.r.id])); });
            details.append(resume, ul);
            zone.append(details);
        });
        return ouvert;
    }

    function charger() {
        if (enEdition) return;
        fetch('api/reservations/' + encodeURIComponent(VOYAGE), { headers: { 'X-Valise-Vite': '1' } })
            .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
            .then(function (liste) { reservations = avecAttente(liste); garder(); afficher(); })
            .catch(function () {                                    // hors ligne : la dernière copie connue
                try { reservations = avecAttente(JSON.parse(localStorage.getItem(CLE_COPIE) || '[]')); } catch (e) {}
                afficher();
            });
    }

    function editer(r) {
        enEdition = r ? r.id : 'nouvelle';
        const zone = bloc.querySelector('.form-zone'), form = document.createElement('form');
        form.className = 'form-resa';
        const choix = document.createElement('select');
        choix.name = 'type';
        Object.keys(TYPES).forEach(function (t) {
            const o = document.createElement('option'); o.value = t; o.textContent = TYPES[t].join(' '); choix.append(o);
        });
        const etiquette = document.createElement('label'); etiquette.append('Type', choix); form.append(etiquette);
        const auj = iso(new Date());
        const valeurs = r || { type: 'vol', jour: (typeof DEPART !== 'undefined' && (auj < DEPART || auj > FIN)) ? DEPART : auj };
        choix.value = valeurs.type;
        const labels = {};
        CHAMPS.forEach(function (c) {
            const label = document.createElement('label'), texte = document.createElement('span');
            const champ = document.createElement(c === 'notes' ? 'textarea' : 'input');
            if (c === 'jour' || c === 'jour_fin') champ.type = 'date';
            else if (c === 'heure' || c === 'heure_fin') champ.type = 'time';
            else if (c === 'telephone') champ.type = 'tel';
            else if (c === 'lien') champ.type = 'url';
            champ.name = c; champ.value = valeurs[c] || '';
            champ.maxLength = c === 'notes' ? 2000 : c === 'lien' ? 500 : 200;
            label.append(texte, champ); labels[c] = { label: label, texte: texte };
            form.append(label);
        });
        function adapter() {                                       // libellés et champs selon le type
            const propres = LIBELLES[choix.value];
            CHAMPS.forEach(function (c) {
                const libelle = propres[c] || COMMUNS[c];
                labels[c].label.hidden = !libelle;
                labels[c].texte.textContent = libelle || '';
            });
        }
        choix.addEventListener('change', adapter);
        adapter();
        const message = para('', 'message-resa');
        const actions = document.createElement('div'); actions.className = 'actions';
        const ok = document.createElement('button'); ok.type = 'submit'; ok.className = 'ctrl-btn'; ok.textContent = 'Enregistrer';
        const annuler = document.createElement('button'); annuler.type = 'button'; annuler.className = 'ctrl-btn'; annuler.textContent = 'Annuler';
        annuler.addEventListener('click', fermer);
        actions.append(ok, annuler);
        form.append(message, actions);
        form.addEventListener('submit', function (ev) {
            ev.preventDefault();
            const corps = { id: r ? r.id : nouvelId(), voyage: VOYAGE, type: choix.value };
            CHAMPS.forEach(function (c) { corps[c] = labels[c].label.hidden ? '' : form.elements[c].value.trim(); });
            if (!corps.jour_fin) corps.jour_fin = null;
            if (!corps.titre || !corps.jour) { message.textContent = '⚠️ Il faut au moins un nom et une date.'; return; }
            if (corps.type === 'hotel' && (!corps.jour_fin || corps.jour_fin <= corps.jour)) {
                message.textContent = '⚠️ Hôtel : la date de départ doit être après l\\u2019arrivée.'; return;
            }
            if (corps.jour_fin && corps.jour_fin < corps.jour) { message.textContent = '⚠️ La fin est avant le début.'; return; }
            if (corps.lien && !/^https?:\\/\\//i.test(corps.lien)) { message.textContent = '⚠️ Le lien doit commencer par https://'; return; }
            ok.disabled = true; ok.textContent = '⏳';
            envoyerOuGarder({ url: 'api/reservations', methode: 'POST', corps: corps, cle: 'resa:' + corps.id })
                .then(function () {
                    reservations = reservations.filter(function (x) { return x.id !== corps.id; }).concat([corps]);
                    garder(); fermer();
                })
                .catch(function () { ok.disabled = false; ok.textContent = 'Enregistrer'; message.textContent = '⚠️ Refusé par le serveur : vérifie les champs.'; });
        });
        zone.replaceChildren(form);
        form.scrollIntoView({ block: 'start', behavior: 'smooth' });
        form.elements.titre.focus();
    }
    function fermer() {
        enEdition = null;
        bloc.querySelector('.form-zone').replaceChildren();
        afficher();
    }

    function supprimer(r) {
        reservations = reservations.filter(function (x) { return x.id !== r.id; });
        garder(); afficher();
        envoyerOuGarder({ url: 'api/reservations/' + encodeURIComponent(VOYAGE) + '/' + encodeURIComponent(r.id),
                          methode: 'DELETE', cle: 'resa:' + r.id }).catch(charger);
    }

    bloc.querySelector('.ajouter-resa').addEventListener('click', function () { editer(null); });
    // En ouvrant la rubrique : le jour en cours à l'écran
    document.querySelectorAll('nav.rubriques button[data-rubrique="programme"]').forEach(function (b) {
        b.addEventListener('click', function () {
            const auj = bloc.querySelector('details.aujourdhui');
            if (auj && !enEdition) setTimeout(function () { auj.scrollIntoView({ block: 'start', behavior: 'smooth' }); }, 50);
        });
    });
    charger();
    document.addEventListener('visibilitychange', function () { if (!document.hidden) charger(); });
    document.addEventListener('file-videe', charger);
})();
"""
