"""Casa Binomerie — Sortir : les envies du couple. Une pile à trier par personne, les Envies (ça plaît aux deux), le
tirage « ce week-end », les rappels de fin et de date prévue. Règles pures ici ; la page plus bas (sortir_en_html)."""
import re
import unicodedata
from datetime import date, timedelta
from urllib.parse import urlsplit
import json
from design import STYLE_D, STYLE_NAV_HUB, STYLE_HORS_LIGNE, TETE_POLICE, nav_hub, sombre
from pwa import SCRIPT_FILE, TETE_PWA

TYPES = [("cine", "Ciné"), ("theatre", "Théâtre"), ("concert", "Concert"), ("expo", "Expo"),
         ("resto-bar", "Resto / bar"), ("balade", "Balade"), ("atelier", "Atelier"), ("escapade", "Escapade")]
BUDGETS = [("gratuit", "Gratuit"), ("moyen", "~30 €"), ("premium", "~80 € +")]
RESERVATIONS = [("non", "Sans réservation"), ("conseillee", "Réservation conseillée"), ("obligatoire", "À réserver")]
ETATS = ("a-trier", "envie", "prevue", "faite", "ecartee")
QUI = ("julien", "laetitia")
MOTS_VIDES = {"le", "la", "les", "l", "un", "une", "des", "de", "du", "d", "au", "aux", "a", "et", "en", "chez"}
FIN_PROCHE = 15          # jours : priorité au tirage
RAPPEL = 7               # jours : encart d'Aujourd'hui


def _date(valeur, cle):
    if not valeur:
        return None
    try:
        return date.fromisoformat(str(valeur)[:10])
    except ValueError:
        raise ValueError(f"{cle} : date invalide")


def _choix(corps, cle, options, defaut=None):
    v = corps.get(cle) or defaut
    if v is not None and v not in [o[0] if isinstance(o, tuple) else o for o in options]:
        raise ValueError(f"{cle} invalide")
    return v


def valider_sortie(corps, aujourd_hui):
    """Une idée validée, prête pour la base. Ajoutée par Julien ou Laetitia : leur avis est « oui »."""
    titre = " ".join(str(corps.get("titre") or "").split())
    if not 1 <= len(titre) <= 200:
        raise ValueError("titre : 1 à 200 caractères")
    lien = str(corps.get("lien") or "").strip()
    if lien and not re.match(r"https?://", lien):
        raise ValueError("lien : http ou https")
    source = _choix(corps, "source", ("routine",) + QUI)
    if source is None:
        raise ValueError("source manquante")
    debut, fin = _date(corps.get("debut"), "debut"), _date(corps.get("fin"), "fin")
    if debut and fin and fin < debut:
        raise ValueError("fin avant le début")
    return {"titre": titre, "type": _choix(corps, "type", TYPES), "budget": _choix(corps, "budget", BUDGETS),
            "reservation": _choix(corps, "reservation", RESERVATIONS), "debut": debut, "fin": fin, "lien": lien,
            "infos": str(corps.get("infos") or "").strip()[:1000], "source": source, "etat": "a-trier",
            "avis_julien": "oui" if source == "julien" else None,
            "avis_laetitia": "oui" if source == "laetitia" else None}


def _sans_accents(texte):
    texte = texte.lower().replace("œ", "oe").replace("æ", "ae")
    return "".join(c for c in unicodedata.normalize("NFD", texte) if unicodedata.category(c) != "Mn")


def cle_titre(titre):
    """« Le Refuge des Fondus ! » -> « refuge fondus » : casse, accents, ponctuation et mots vides retirés."""
    mots = re.findall(r"[a-z0-9]+", _sans_accents(titre))
    return " ".join(m for m in mots if m not in MOTS_VIDES)


def cle_lien(lien):
    """L'adresse sans protocole, sans « www. », sans query string ni « / » final."""
    if not lien:
        return ""
    p = urlsplit(lien.strip().lower())
    return (p.netloc.removeprefix("www.") + p.path).rstrip("/")


def doublon(nouvelle, existantes):
    """L'id d'une idée déjà en base (tout état) au même titre ou au même lien, sinon None."""
    t, l = cle_titre(nouvelle["titre"]), cle_lien(nouvelle.get("lien", ""))
    for e in existantes:  # lien : pas de domaine nu (« wecandoo.fr » seul), titre : pas de clé vide
        if (t and cle_titre(e["titre"]) == t) or ("/" in l and cle_lien(e.get("lien", "")) == l):
            return e["id"]
    return None


def apres_avis(s, qui, avis):
    """L'idée après l'avis de qui : un « non » écarte une idée à trier, deux « oui » en font une Envie."""
    if qui not in QUI or avis not in ("oui", "non"):
        raise ValueError("avis invalide")
    s = {**s, f"avis_{qui}": avis}
    if avis == "non":
        if s["etat"] == "a-trier":
            s["etat"] = "ecartee"
    elif s["etat"] == "a-trier" and s["avis_julien"] == "oui" and s["avis_laetitia"] == "oui":
        s["etat"] = "envie"
    return s


def tirer_weekend(sorties, jour, hasard):
    """2 à 3 Envies : celles qui finissent dans FIN_PROCHE jours d'abord, puis au hasard ; une Premium au plus,
    jamais deux du même type. Une Envie déjà finie est ignorée."""
    envies = [s for s in sorties if s["etat"] == "envie" and not (s.get("fin") and s["fin"] < jour)]
    proches = sorted((s for s in envies if s.get("fin") and s["fin"] <= jour + timedelta(days=FIN_PROCHE)),
                     key=lambda s: s["fin"])
    reste = [s for s in envies if s not in proches]
    hasard.shuffle(reste)
    choix = []
    for s in proches + reste:
        if len(choix) == 3:
            break
        if s["type"] is not None and s["type"] in {c["type"] for c in choix}:
            continue
        if s["budget"] == "premium" and any(c["budget"] == "premium" for c in choix):
            continue
        choix.append(s)
    return choix


def rappels(sorties, jour):
    """Pour Aujourd'hui : les Envies qui finissent dans RAPPEL jours, les sorties prévues dans RAPPEL jours, et si
    c'est le moment du tirage (vendredi, samedi)."""
    limite = jour + timedelta(days=RAPPEL)
    finissent = sorted((s for s in sorties if s["etat"] == "envie" and s.get("fin") and jour <= s["fin"] <= limite),
                       key=lambda s: s["fin"])
    prevues = sorted((s for s in sorties if s["etat"] == "prevue" and s.get("le") and jour <= s["le"] <= limite),
                     key=lambda s: s["le"])
    return {"finissent": finissent, "prevues": prevues, "weekend": jour.weekday() in (4, 5)}


# --- La page ------------------------------------------------------------------------------------

STYLE_SORTIR = """
body.sortir { --rubrique: var(--sortir); --rubrique-doux: var(--sortir-doux); }
body.sortir nav.vues { display: grid; grid-template-columns: repeat(3, 1fr); gap: 4px; background: var(--carte); border-radius: 18px;
           padding: 4px; margin: 0 0 18px; position: sticky; top: 0; z-index: 5; }
body.sortir nav.vues button { border: none; background: none; border-radius: 14px; padding: 10px 4px; min-height: 44px;
                  font-family: inherit; font-weight: 700; font-size: 14px; color: var(--doux); }
body.sortir nav.vues button.actif { background: var(--fond); color: var(--sortir); box-shadow: 0 1px 3px rgba(0,0,0,.08); }
body.sortir .message { min-height: 1.2em; color: var(--doux); margin: 0 0 8px; }
body.sortir .lien-discret { border: none; background: none; padding: 10px 0; min-height: 44px; font-family: inherit;
                            font-size: 14px; color: var(--doux); text-decoration: underline; }
body.sortir .vue { display: flex; flex-direction: column; gap: 12px; }
body.sortir .carte-sortie { background: var(--carte); border-radius: 24px; padding: 18px; display: flex; flex-direction: column; gap: 10px; }
body.sortir .carte-sortie h3 { margin: 0; font-size: 22px; line-height: 1.15; }
body.sortir .carte-sortie.prevue { border: 2px solid var(--sortir); }
body.sortir .puces { display: flex; flex-wrap: wrap; gap: 6px; }
body.sortir .puce { background: var(--sortir-doux); color: var(--sortir); border-radius: 999px; padding: 4px 10px; font-size: 13px; font-weight: 700; }
body.sortir .infos { margin: 0; color: var(--texte); }
body.sortir .carte-sortie a { color: var(--sortir); font-weight: 700; min-height: 44px; display: inline-flex; align-items: center; }
body.sortir .boutons { display: flex; flex-wrap: wrap; gap: 8px; }
body.sortir .boutons button, body.sortir form button { flex: 1 1 auto; min-height: 44px; border-radius: 999px; padding: 10px 16px;
                  font-family: inherit; font-weight: 800; font-size: 15px; border: 2px solid var(--sortir); background: transparent; color: var(--sortir); }
body.sortir .boutons button.principal, body.sortir form button[type=submit] { background: var(--sortir); color: var(--fond); }
body.sortir .boutons.gros button { min-height: 56px; font-size: 17px; }
body.sortir button[aria-pressed=true] { background: var(--sortir); color: var(--fond); }
body.sortir input, body.sortir select, body.sortir textarea { font-family: inherit; font-size: 16px; min-height: 44px; border-radius: 14px;
                  border: 1px solid var(--ligne); padding: 8px 12px; background: var(--fond); color: var(--texte); width: 100%; box-sizing: border-box; }
body.sortir form { display: flex; flex-direction: column; gap: 8px; background: var(--carte); border-radius: 24px; padding: 18px; }
body.sortir .ligne-date { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
body.sortir .ligne-date input { width: auto; flex: 1 1 140px; }
body.sortir .vide { text-align: center; color: var(--doux); padding: 28px 0; font-size: 18px; }
body.sortir h2 { font-size: 18px; margin: 4px 0 0; }
body.sortir .qui { display: flex; flex-direction: column; gap: 12px; align-items: stretch; }
body.sortir .filtres { display: flex; gap: 6px; overflow-x: auto; scrollbar-width: none; margin: 0 -16px; padding: 0 16px 2px; }
body.sortir .filtres::-webkit-scrollbar { display: none; }
body.sortir .filtres button { flex: 0 0 auto; min-height: 36px; border-radius: 999px; padding: 6px 12px; font-family: inherit;
                  font-weight: 700; font-size: 14px; border: 1px solid var(--ligne); background: transparent; color: var(--doux); }
body.sortir .filtres button[aria-pressed=true] { border-color: var(--sortir); background: var(--sortir-doux); color: var(--sortir); }
body.sortir details.attente summary { font-weight: 800; font-size: 16px; padding: 10px 0; min-height: 44px; box-sizing: border-box; cursor: pointer; color: var(--doux); }
body.sortir details.attente > div { display: flex; flex-direction: column; gap: 12px; }
body.sortir .tas, body.sortir .indice, body.sortir .boutons.gros { width: 100%; max-width: 520px; box-sizing: border-box; }
body.sortir .tas { position: relative; }
body.sortir .carte-tri { position: relative; z-index: 2; padding: 18px 18px 20px; gap: 10px; overflow: hidden; touch-action: pan-y;
                  border-top: 5px solid var(--t, var(--sortir)); box-shadow: 0 6px 20px rgba(0,0,0,.08);
                  user-select: none; -webkit-user-select: none; transition: transform .2s ease-out; }
body.sortir .carte-tri.tire { transition: none; }
body.sortir .carte-tri.derriere { position: absolute; inset: 0; z-index: 1; transform: translateY(18px) scale(.94); opacity: .5;
                  pointer-events: none; }
body.sortir .tete-tri { display: flex; justify-content: space-between; align-items: center; gap: 8px; margin: -4px 0 0; }
body.sortir .type-tri { display: inline-flex; align-items: center; gap: 6px; border-radius: 999px; padding: 4px 10px 4px 8px;
                  background: color-mix(in srgb, var(--t, var(--sortir)) 16%, transparent); color: var(--t, var(--sortir));
                  font-weight: 800; font-size: 12px; letter-spacing: .06em; text-transform: uppercase; }
body.sortir .type-tri::before { content: ""; width: 8px; height: 8px; border-radius: 50%; background: currentColor; }
body.sortir .carte-tri a.ouvrir { width: 40px; height: 40px; min-height: 40px; border-radius: 50%; justify-content: center;
                  background: var(--sortir-doux); color: var(--sortir); font-size: 18px; text-decoration: none; }
body.sortir .carte-tri h3 { font-size: 21px; line-height: 1.2; }
body.sortir .reperes { margin: -2px 0 0; color: var(--doux); font-weight: 700; font-size: 14px; }
body.sortir .carte-tri .infos { color: var(--doux); font-size: 15px; line-height: 1.45; }
body.sortir .infos.coupe { display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }
body.sortir .carte-tri .lien-discret { align-self: flex-start; padding: 0; min-height: 32px; margin-top: -4px; text-decoration: none;
                  color: var(--sortir); font-weight: 700; }
body.sortir .tampon { position: absolute; top: 16px; padding: 4px 10px; border: 3px solid currentColor; border-radius: 10px;
                  font-weight: 900; font-size: 18px; text-transform: uppercase; pointer-events: none; background: var(--carte); }
body.sortir .tampon.oui { left: 14px; color: var(--sortir); transform: rotate(-12deg); opacity: var(--oui, 0); }
body.sortir .tampon.non { right: 14px; color: var(--doux); transform: rotate(12deg); opacity: var(--non, 0); }
body.sortir .indice { display: flex; justify-content: space-between; color: var(--doux); font-size: 13px; margin: 6px 0 -4px; padding: 0 6px; }
body.sortir .t-cine { --t: #374151; } body.sortir .t-theatre { --t: #9b2c4f; } body.sortir .t-concert { --t: #6d28d9; }
body.sortir .t-expo { --t: #0b7a87; } body.sortir .t-resto-bar { --t: #c2410c; } body.sortir .t-balade { --t: #2f7d32; }
body.sortir .t-atelier { --t: #8a5a00; } body.sortir .t-escapade { --t: #1d4ed8; }
@media (prefers-reduced-motion: reduce) { body.sortir .carte-tri { transition: none; } }
""" + sombre("""body.sortir .t-cine { --t: #cbd5e1; } body.sortir .t-theatre { --t: #f08aa8; } body.sortir .t-concert { --t: #b794f6; }
body.sortir .t-expo { --t: #4cc3d1; } body.sortir .t-resto-bar { --t: #ff8f5a; } body.sortir .t-balade { --t: #7bc67e; }
body.sortir .t-atelier { --t: #f0c24b; } body.sortir .t-escapade { --t: #8fb3ff; }""") + """
"""

SCRIPT_SORTIR = """(function () {
    const LIB = JSON.parse(document.getElementById('libelles').textContent);
    const FIN_PROCHE = JSON.parse(document.getElementById('reglages').textContent).fin_proche;
    const CLE_COPIE = 'casa-sortir-copie';
    let d = null, vue = 'a-trier', qui = null, tirageCartes = null, tirageMessage = '', dateOuverte = null, formulaireOuvert = false, filtreType = null, minuteurMessage = null, attenteOuverte = false;
    try { qui = localStorage.getItem('casa-qui'); } catch (e) {}
    if (qui !== 'julien' && qui !== 'laetitia') qui = null;

    function el(balise, classe, texte) {
        const e = document.createElement(balise);
        if (classe) e.className = classe;
        if (texte !== undefined) e.textContent = texte;
        return e;
    }
    function bouton(texte, classe, action) { const b = el('button', classe, texte); b.type = 'button'; b.addEventListener('click', action); return b; }
    function libelle(liste, cle) { const t = (LIB[liste] || []).filter(function (x) { return x[0] === cle; })[0]; return t ? t[1] : null; }
    function jjmm(iso) { return iso.slice(8, 10) + '/' + iso.slice(5, 7); }
    function aujourdhui() { return d ? d.aujourd_hui : new Date().toISOString().slice(0, 10); }
    function message(texte) { clearTimeout(minuteurMessage); document.getElementById('message-sortir').textContent = texte || ''; }
    function annonce(texte) { message(texte); minuteurMessage = setTimeout(function () { message(''); }, 2500); }
    function autre() { return qui === 'julien' ? 'Laetitia' : 'Julien'; }
    function sortie(id) { return d.sorties.filter(function (s) { return s.id === id; })[0]; }

    // --- Données : lecture, copie hors ligne, envois ---
    let chaine = Promise.resolve(), minuteur = null;
    function envoyer(envoi) { const p = chaine.then(function () { return envoyerOuGarder(envoi); }); chaine = p.catch(function () {}); return p; }
    function relire() { clearTimeout(minuteur); minuteur = setTimeout(charger, 400); }
    function refuse() { message('Refusé par le serveur, la page a été remise à jour.'); relire(); }
    function garder() { try { localStorage.setItem(CLE_COPIE, JSON.stringify(d)); } catch (e) {} }
    function charger() {
        fetch('api/sorties', { headers: { 'X-Valise-Vite': '1' } })
            .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
            .then(function (lu) { d = lu; garder(); afficher(); })
            .catch(function () {
                try { d = d || JSON.parse(localStorage.getItem(CLE_COPIE)); } catch (e) {}
                if (d && !d.sorties) d = null;
                if (d) afficher();
                else document.getElementById('vue').replaceChildren(el('p', 'vide', 'Pas de connexion et rien en copie.'));
            });
    }
    // Un changement : appliqué ici tout de suite, envoyé par la file (il part au retour du réseau sinon)
    function modifier(s, champs, cle) {
        Object.assign(s, champs); garder(); afficher();
        envoyer({ url: 'api/sorties/' + s.id, methode: 'POST', corps: champs, cle: 'sortie:' + s.id + ':' + cle }).then(relire, refuse);
    }
    function donnerAvis(s, avis) {
        s['avis_' + qui] = avis;
        if (avis === 'non') { if (s.etat === 'a-trier') s.etat = 'ecartee'; }
        else if (s.etat === 'a-trier' && s.avis_julien === 'oui' && s.avis_laetitia === 'oui') s.etat = 'envie';
        annonce(avis === 'non' ? 'Écartée.' : s.etat === 'envie' ? 'Envie ! Partants tous les deux.' : 'En attente de ' + autre() + '.');
        garder(); afficher();
        envoyer({ url: 'api/sorties/' + s.id + '/avis', methode: 'POST', corps: { qui: qui, avis: avis }, cle: 'avis:' + s.id + ':' + qui }).then(relire, refuse);
    }

    // --- Qui es-tu ? ---
    function quiSuisJe(zone) {
        if (qui) return true;
        const c = el('div', 'carte-sortie qui');
        c.append(el('h3', '', 'Qui es-tu ?'), el('p', 'infos', 'Chacun son avis : on garde ça sur ce téléphone.'));
        const b = el('div', 'boutons gros');
        [['julien', 'Julien'], ['laetitia', 'Laetitia']].forEach(function (p) {
            b.append(bouton(p[1], 'principal', function () {
                qui = p[0]; try { localStorage.setItem('casa-qui', qui); } catch (e) {} afficher(); }));
        });
        c.append(b); zone.append(c);
        return false;
    }

    // --- Cartes ---
    function carte(s) {
        const c = el('div', 'carte-sortie' + (s.etat === 'prevue' ? ' prevue' : ''));
        c.append(el('h3', '', s.titre));
        const p = el('div', 'puces');
        [libelle('types', s.type), libelle('budgets', s.budget), libelle('reservations', s.reservation)].forEach(function (t) { if (t) p.append(el('span', 'puce', t)); });
        if (s.etat === 'prevue' && s.le) p.append(el('span', 'puce', 'Prévu le ' + jjmm(s.le)));
        if (s.fin) p.append(el('span', 'puce', (s.fin < aujourdhui() ? 'Terminé le ' : 'Jusqu\\'au ') + jjmm(s.fin)));
        else if (s.debut && s.debut > aujourdhui()) p.append(el('span', 'puce', 'À partir du ' + jjmm(s.debut)));
        if (p.children.length) c.append(p);
        if (s.infos) c.append(el('p', 'infos', s.infos));
        if (s.lien) { const a = el('a', '', 'Voir'); a.href = s.lien; a.target = '_blank'; a.rel = 'noopener'; c.append(a); }
        return c;
    }
    function actionsEnvie(s) {
        const b = el('div', 'boutons');
        b.append(bouton('On y va', 'principal', function () { dateOuverte = dateOuverte === s.id ? null : s.id; afficher(); }));
        b.append(bouton('Fait', '', function () { modifier(s, { etat: 'faite', le: s.le || aujourdhui() }, 'etat'); vue = 'faites'; afficher(); }));
        b.append(bouton('Plus envie', '', function () { modifier(s, { etat: 'ecartee' }, 'etat'); }));
        return b;
    }
    function ligneDate(s) {
        const l = el('div', 'ligne-date');
        const champ = el('input'); champ.type = 'date'; champ.min = aujourdhui(); champ.value = s.le || ''; champ.setAttribute('aria-label', 'Date prévue');
        l.append(champ, bouton('Valider', 'principal', function () {
            if (!champ.value) return;
            dateOuverte = null; modifier(s, { etat: 'prevue', le: champ.value }, 'etat'); }));
        return l;
    }
    function carteEnvie(s) {
        const c = carte(s);
        if (s.etat === 'prevue') {
            c.append(bouton('Fait', 'lien-discret', function () { modifier(s, { etat: 'faite' }, 'etat'); vue = 'faites'; afficher(); }));
            c.append(bouton('Annuler', 'lien-discret', function () { modifier(s, { etat: 'envie', le: null }, 'etat'); }));
        }
        else c.append(actionsEnvie(s));
        if (dateOuverte === s.id) c.append(ligneDate(s));
        return c;
    }

    // --- Filtre par type (À trier et Envies) ---
    function filtrer(liste, zone) {
        const presents = LIB.types.filter(function (t) { return liste.some(function (s) { return s.type === t[0]; }); });
        if (filtreType && !presents.some(function (t) { return t[0] === filtreType; })) filtreType = null;
        if (presents.length > 1) {
            const f = el('div', 'filtres'); f.setAttribute('role', 'group'); f.setAttribute('aria-label', 'Type');
            [[null, 'Tous']].concat(presents).forEach(function (t) {
                const n = t[0] ? liste.filter(function (s) { return s.type === t[0]; }).length : liste.length;
                const b = bouton(t[1] + ' ' + n, '', function () { filtreType = t[0]; afficher(); });
                b.setAttribute('aria-pressed', String(filtreType === t[0]));
                f.append(b);
            });
            zone.append(f);
        }
        return filtreType ? liste.filter(function (s) { return s.type === filtreType; }) : liste;
    }

    // --- À trier : une carte à glisser (droite : ça me tente, gauche : bof), la suivante derrière ---
    function carteTri(s) {
        const c = el('div', 'carte-sortie carte-tri');
        c.classList.add('t-' + (s.type || 'aucun'));
        const tete = el('div', 'tete-tri');
        tete.append(el('span', 'type-tri', libelle('types', s.type) || 'Sortie'));
        if (s.lien) {
            const a = el('a', 'ouvrir', '\u2197'); a.href = s.lien; a.target = '_blank'; a.rel = 'noopener';
            a.setAttribute('aria-label', 'Voir le site'); tete.append(a);
        }
        c.append(tete, el('h3', '', s.titre));
        const jour = aujourdhui(), reperes = [libelle('budgets', s.budget), libelle('reservations', s.reservation)];
        if (s.fin) reperes.push((s.fin < jour ? 'terminé le ' : 'jusqu\\'au ') + jjmm(s.fin));
        else if (s.debut && s.debut > jour) reperes.push('à partir du ' + jjmm(s.debut));
        const r = reperes.filter(Boolean).join(' · ');
        if (r) c.append(el('p', 'reperes', r));
        if (s.infos) {
            const t = el('p', 'infos coupe', s.infos);
            c.append(t);
            if (s.infos.length > 140) {
                const plus = bouton('Lire la suite', 'lien-discret', function () {
                    t.classList.toggle('coupe'); plus.textContent = t.classList.contains('coupe') ? 'Lire la suite' : 'Réduire'; });
                c.append(plus);
            }
        }
        c.append(el('span', 'tampon oui', 'Ça me tente'), el('span', 'tampon non', 'Bof'));
        return c;
    }
    function partir(c, avis, fin) {
        if (c.dataset.parti) return;
        c.dataset.parti = '1';
        let calme = false;
        try { calme = matchMedia('(prefers-reduced-motion: reduce)').matches; } catch (e) {}
        if (calme) { fin(avis); return; }
        const sens = avis === 'oui' ? 1 : -1;
        c.style.setProperty(avis === 'oui' ? '--oui' : '--non', 1);
        c.style.transition = 'transform .25s ease-in, opacity .25s ease-in';
        c.style.transform = 'translateX(' + sens * (window.innerWidth + 100) + 'px) rotate(' + sens * 18 + 'deg)';
        c.style.opacity = '0';
        setTimeout(function () { fin(avis); }, 230);
    }
    function glisser(c, fin) {
        let x0 = null, y0 = 0, dx = 0, actif = false, id = null;
        function poser(x) {
            c.style.transform = x ? 'translateX(' + x + 'px) rotate(' + x / 20 + 'deg)' : '';
            c.style.setProperty('--oui', Math.max(0, Math.min(1, x / 100)));
            c.style.setProperty('--non', Math.max(0, Math.min(1, -x / 100)));
        }
        c.addEventListener('pointerdown', function (e) {
            if (e.target.closest('a, button') || c.dataset.parti) return;
            x0 = e.clientX; y0 = e.clientY; dx = 0; actif = false; id = e.pointerId;
        });
        c.addEventListener('pointermove', function (e) {
            if (x0 === null || e.pointerId !== id) return;
            const mx = e.clientX - x0, my = e.clientY - y0;
            if (!actif) {
                if (Math.abs(mx) < 8 && Math.abs(my) < 8) return;
                if (Math.abs(my) > Math.abs(mx)) { x0 = null; return; }   // geste vertical : on laisse défiler
                actif = true; c.classList.add('tire');
                try { c.setPointerCapture(id); } catch (err) {}
            }
            dx = mx; poser(dx);
        });
        function lacher() {
            if (x0 === null) return;
            x0 = null; c.classList.remove('tire');
            if (!actif) return;
            actif = false;
            if (Math.abs(dx) > Math.min(110, c.offsetWidth * 0.3)) partir(c, dx > 0 ? 'oui' : 'non', fin);
            else poser(0);
        }
        c.addEventListener('pointerup', lacher);
        c.addEventListener('pointercancel', lacher);
    }

    // --- À trier ---
    function vueATrier(zone) {
        const jour = aujourdhui();
        function passee(s) { return s.fin && s.fin < jour ? 1 : 0; }
        const pile = filtrer(d.sorties.filter(function (s) { return s.etat === 'a-trier' && !s['avis_' + qui]; }), zone)
                              .sort(function (a, b) { return passee(a) - passee(b) || String(b.cree_le || '').localeCompare(String(a.cree_le || '')); });
        if (!pile.length) { zone.append(el('p', 'vide', 'Rien à trier.')); return; }
        const s = pile[0], c = carteTri(s), tas = el('div', 'tas');
        function fin(avis) { donnerAvis(s, avis); }
        if (pile[1]) { const der = carteTri(pile[1]); der.classList.add('derriere'); der.setAttribute('aria-hidden', 'true'); tas.append(der); }
        tas.append(c); glisser(c, fin);
        const indice = el('div', 'indice');
        indice.append(el('span', '', '\u2190 Bof'), el('span', '', 'Ça me tente \u2192'));
        const b = el('div', 'boutons gros');
        b.append(bouton('Bof', '', function () { partir(c, 'non', fin); }));
        b.append(bouton('Ça me tente', 'principal', function () { partir(c, 'oui', fin); }));
        zone.append(tas, indice, b);
        if (pile.length > 1) zone.append(el('p', 'message', (pile.length - 1) + ' autre(s) derrière.'));
    }

    // --- Envies ---
    function enviesTriees() {
        const jour = aujourdhui();
        const liste = d.sorties.filter(function (s) { return s.etat === 'envie' || (s.etat === 'prevue' && !(s.le && s.le < jour)); });
        const limite = new Date(Date.parse(jour + 'T00:00:00Z') + FIN_PROCHE * 86400000).toISOString().slice(0, 10);
        function rang(s) {
            if (s.etat === 'prevue') return 0;
            if (s.fin && s.fin < jour) return 3;
            if (s.fin && s.fin <= limite) return 1;
            return 2;
        }
        return liste.sort(function (a, b) {
            if (rang(a) !== rang(b)) return rang(a) - rang(b);
            if (rang(a) === 0) return String(a.le || '9').localeCompare(String(b.le || '9'));
            if (rang(a) === 1) return a.fin.localeCompare(b.fin);
            return String(b.cree_le || '').localeCompare(String(a.cree_le || ''));
        });
    }
    function tirage() {
        tirageMessage = 'Tirage en cours…'; tirageCartes = []; afficher();
        fetch('api/sorties/weekend')
            .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
            .then(function (j) {
                tirageCartes = (j.tirage || []).map(function (t) { return t.id; });
                tirageMessage = tirageCartes.length ? '' : 'Pas assez d\\'Envies pour un tirage';
                afficher();
            })
            .catch(function () { tirageCartes = []; tirageMessage = 'Tirage impossible hors ligne.'; afficher(); });
    }
    function blocTirage(zone) {
        if (tirageCartes === null) return;
        const h = el('div', 'boutons');
        zone.append(el('h2', '', 'Ce week-end'));
        const vivantes = tirageCartes.map(sortie).filter(function (s) { return s && s.etat === 'envie'; });
        if (!vivantes.length) zone.append(el('p', 'message', tirageMessage || 'Plus rien dans le tirage.'));
        vivantes.forEach(function (s) { zone.append(carteEnvie(s)); });
        h.append(bouton('Retirer', '', tirage), bouton('Fermer le tirage', 'lien-discret', function () { tirageCartes = null; afficher(); }));
        zone.append(h);
    }
    function ajouterIdee(zone) {
        if (!formulaireOuvert) { zone.append(bouton('+ Ajouter une idée', '', function () { formulaireOuvert = true; afficher(); })); return; }
        const f = el('form'); f.autocomplete = 'off';
        const titre = el('input'); titre.placeholder = 'Titre'; titre.required = true; titre.maxLength = 200; titre.setAttribute('aria-label', 'Titre');
        function liste(nom, cle) {
            const s = el('select'); s.setAttribute('aria-label', nom);
            const o = el('option', '', nom); o.value = ''; s.append(o);
            LIB[cle].forEach(function (x) { const p = el('option', '', x[1]); p.value = x[0]; s.append(p); });
            return s;
        }
        const type = liste('Type', 'types'), budget = liste('Budget', 'budgets');
        const fin = el('input'); fin.type = 'date'; fin.setAttribute('aria-label', 'Jusqu\\'au (facultatif)'); fin.title = 'Jusqu\\'au (facultatif)';
        const lien = el('input'); lien.type = 'url'; lien.placeholder = 'Lien (facultatif)'; lien.setAttribute('aria-label', 'Lien');
        const b = el('div', 'boutons');
        const ok = el('button', '', 'Ajouter'); ok.type = 'submit';
        b.append(ok, bouton('Annuler', '', function () { formulaireOuvert = false; afficher(); }));
        f.append(titre, type, budget, el('label', 'message', 'Jusqu\\'au (facultatif)'), fin, lien, b);
        f.addEventListener('submit', function (ev) {
            ev.preventDefault();
            const nom = titre.value.trim(); if (!nom) return;
            const corps = { titre: nom, source: qui };
            if (type.value) corps.type = type.value;
            if (budget.value) corps.budget = budget.value;
            if (fin.value) corps.fin = fin.value;
            if (lien.value.trim()) corps.lien = lien.value.trim();
            ok.disabled = true;
            if (navigator.onLine) {
                fetch('api/sorties', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(corps) })
                    .then(function (r) {
                        if (r.status === 201) {
                            formulaireOuvert = false; message('Ajoutée'); relire(); afficher();   // l'API ne rend que l'id : on relit
                            return;
                        }
                        ok.disabled = false;
                        if (r.status === 409) { message('Déjà dans la liste'); return; }
                        return r.json().catch(function () { return {}; }).then(function (j) {
                            message(j && j.erreur ? j.erreur : 'Refusé par le serveur : vérifie le titre et le lien.');
                        });
                    })
                    .catch(function () { ok.disabled = false; message('Envoi impossible, réessaie.'); });
                return;
            }
            envoyer({ url: 'api/sorties', methode: 'POST', corps: corps, cle: 'idee:' + nom }).then(function (etat) {
                formulaireOuvert = false;
                message(etat === 'attente' ? 'Gardée sur le téléphone : partira au retour du réseau' : 'Ajoutée.');
                relire(); afficher();
            }, function (e) {
                ok.disabled = false;
                message(String(e.message) === '409' ? 'Déjà dans la liste' : 'Refusé par le serveur : vérifie le titre et le lien.');
            });
        });
        zone.append(f);
    }
    function vueEnvies(zone) {
        const haut = el('div', 'boutons');
        haut.append(bouton('Ce week-end ?', 'principal', tirage));
        zone.append(haut);
        blocTirage(zone);
        ajouterIdee(zone);
        const liste = filtrer(enviesTriees(), zone);
        if (!liste.length) zone.append(el('p', 'vide', 'Aucune Envie pour l\\'instant.'));
        liste.forEach(function (s) { zone.append(carteEnvie(s)); });
        enAttente(zone);
    }
    // Mes « ça me tente » que l'autre n'a pas encore jugés
    function enAttente(zone) {
        const autreCle = 'avis_' + (qui === 'julien' ? 'laetitia' : 'julien');
        const liste = d.sorties.filter(function (s) { return s.etat === 'a-trier' && s['avis_' + qui] === 'oui' && !s[autreCle]; })
                               .sort(function (a, b) { return String(b.cree_le || '').localeCompare(String(a.cree_le || '')); });
        if (!liste.length) return;
        const det = el('details', 'attente'), corps = el('div');
        det.open = attenteOuverte; det.addEventListener('toggle', function () { attenteOuverte = det.open; });
        det.append(el('summary', '', 'En attente de ' + autre() + ' (' + liste.length + ')'));
        liste.forEach(function (s) {
            const c = carte(s);
            c.append(bouton('Finalement bof', 'lien-discret', function () { donnerAvis(s, 'non'); }));
            corps.append(c);
        });
        det.append(corps); zone.append(det);
    }

    // --- Faites ---
    function pouces(s) {
        const b = el('div', 'boutons');
        [['haut', 'J\\'ai aimé'], ['bas', 'Pas terrible']].forEach(function (p) {
            const x = bouton(p[1], '', function () { modifier(s, { pouce: s.pouce === p[0] ? null : p[0] }, 'pouce'); });
            x.setAttribute('aria-pressed', String(s.pouce === p[0])); b.append(x);
        });
        return b;
    }
    function champRetour(s) {
        const l = el('div', 'ligne-date');
        const t = el('input'); t.value = s.retour || ''; t.maxLength = 500; t.placeholder = 'Un mot pour s\\'en souvenir'; t.setAttribute('aria-label', 'Retour');
        l.append(t, bouton('Noter', '', function () { modifier(s, { retour: t.value.trim() }, 'retour'); }));
        return l;
    }
    function vueFaites(zone) {
        const jour = aujourdhui();
        const passees = d.sorties.filter(function (s) { return s.etat === 'prevue' && s.le && s.le < jour; })
                                 .sort(function (a, b) { return a.le.localeCompare(b.le); });
        const faites = d.sorties.filter(function (s) { return s.etat === 'faite'; })
                                .sort(function (a, b) { return String(b.le || b.cree_le || '').localeCompare(String(a.le || a.cree_le || '')); });
        passees.forEach(function (s) {
            const c = carte(s); c.append(el('h2', '', "Alors, c'était comment ?"));
            const b = el('div', 'boutons');
            b.append(bouton('J\\'ai aimé', 'principal', function () { modifier(s, { etat: 'faite', pouce: 'haut' }, 'etat'); }));
            b.append(bouton('Pas terrible', '', function () { modifier(s, { etat: 'faite', pouce: 'bas' }, 'etat'); }));
            b.append(bouton('Pas fait', 'lien-discret', function () { modifier(s, { etat: 'envie', le: null }, 'etat'); }));
            c.append(b); zone.append(c);
        });
        faites.forEach(function (s) {
            const c = carte(s);
            const puces = c.querySelector('.puces');
            if (s.le && puces) puces.prepend(el('span', 'puce', 'Le ' + jjmm(s.le)));
            c.append(pouces(s), champRetour(s)); zone.append(c);
        });
        if (!passees.length && !faites.length) zone.append(el('p', 'vide', 'Rien de fait pour l\\'instant.'));
    }

    function afficher() {
        if (!d) return;
        const zone = document.getElementById('vue'); zone.replaceChildren();
        document.querySelectorAll('nav.vues button').forEach(function (b) { b.classList.toggle('actif', b.dataset.vue === vue); });
        const lien = document.getElementById('changer'); lien.hidden = !qui;
        if (!quiSuisJe(zone)) { document.getElementById('compte').textContent = ''; return; }
        const n = d.sorties.filter(function (s) { return s.etat === 'a-trier' && !s['avis_' + qui]; }).length;
        document.getElementById('compte').textContent = n ? ' (' + n + ')' : '';
        ({ 'a-trier': vueATrier, 'envies': vueEnvies, 'faites': vueFaites })[vue](zone);
    }
    document.querySelectorAll('nav.vues button').forEach(function (b) {
        b.addEventListener('click', function () { vue = b.dataset.vue; afficher(); try { history.replaceState(null, '', '#' + vue); } catch (e) {} });
    });
    document.getElementById('changer').addEventListener('click', function () {
        qui = null; try { localStorage.removeItem('casa-qui'); } catch (e) {} afficher();
    });
    const h = location.hash.slice(1);
    if (h === 'a-trier' || h === 'envies' || h === 'faites') vue = h;
    if (h === 'tirage') { vue = 'envies'; }
    document.addEventListener('file-videe', charger);
    document.addEventListener('visibilitychange', function () { if (!document.hidden) charger(); });
    charger();
    if (h === 'tirage') tirage();
})();"""


def sortir_en_html():
    """La page Sortir : une coquille, remplie par le script depuis api/sorties (copie gardée hors ligne)."""
    libelles = json.dumps({"types": TYPES, "budgets": BUDGETS, "reservations": RESERVATIONS}, ensure_ascii=False)
    reglages = json.dumps({"fin_proche": FIN_PROCHE})
    return f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Sortir · Casa Binomerie</title>
{TETE_PWA}
{TETE_POLICE}
<style>{STYLE_D}{STYLE_NAV_HUB}{STYLE_HORS_LIGNE}{STYLE_SORTIR}</style>
</head>
<body class="accueil hub-page sortir">
<h1>Sortir</h1>
<button type="button" class="lien-discret" id="changer" hidden>Changer</button>
<nav class="vues" aria-label="Sortir">
<button type="button" data-vue="a-trier">À trier<span id="compte"></span></button>
<button type="button" data-vue="envies">Envies</button>
<button type="button" data-vue="faites">Faites</button>
</nav>
<p class="message" id="message-sortir" aria-live="polite"></p>
<div id="hors-ligne" hidden></div>
<div id="vue" class="vue"></div>
{nav_hub("sortir")}
<script type="application/json" id="libelles">{libelles}</script>
<script type="application/json" id="reglages">{reglages}</script>
<script>{SCRIPT_FILE}
window.addEventListener('online', function () {{ majHorsLigne(); viderFile(); }});
window.addEventListener('offline', majHorsLigne);
majHorsLigne();
viderFile();
</script>
<script>{SCRIPT_SORTIR}</script>
</body>
</html>"""
