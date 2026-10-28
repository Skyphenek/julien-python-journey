"""« ⏳ Compte à rebours » : où en est un voyage aujourd'hui (départ dans N jours, jour k sur T et
l'étape du jour, rentrés depuis N jours), sur l'accueil et en tête de la page du voyage.

Le serveur écrit le texte du jour ; le script le recalcule avec la date du téléphone, car les
pages sont gardées hors ligne (une page ouverte trois jours plus tard doit dire vrai).
La règle existe donc deux fois, texte_compte (Python) et texteCompte (JS) : un test vérifie
qu'elles disent la même chose.
"""
import json
from html import escape as echapper


def _pluriel(n, mot):
    return f"{n} {mot}{'s' if n > 1 else ''}"


def texte_compte(depart, fin, aujourd_hui, etapes=()):
    """Le texte du jour. etapes : [{"destination", "du", "au"}] (dates), pour nommer l'étape du jour."""
    avant = (depart - aujourd_hui).days
    if avant > 1:
        return f"Départ dans {avant} jours"
    if avant == 1:
        return "Départ demain !"
    if aujourd_hui <= fin:
        jour, total = (aujourd_hui - depart).days + 1, (fin - depart).days + 1
        ou = next((e["destination"] for e in etapes if e["du"] <= aujourd_hui <= e["au"]), None)
        if jour == 1:
            texte = f"C’est le départ ! · jour 1 sur {total}"
        elif jour == total:
            texte = f"Dernier jour · jour {jour} sur {total}"
        else:
            texte = f"Jour {jour} sur {total}"
        return texte + (f" · {ou}" if ou else "")
    return f"Rentrés depuis {_pluriel((aujourd_hui - fin).days, 'jour')}"


def attributs_compte(depart, fin, etapes=()):
    """Les attributs data-… lus par le script (dates ISO, étapes en JSON)."""
    donnees = json.dumps([{"destination": e["destination"], "du": e["du"].isoformat(), "au": e["au"].isoformat()}
                          for e in etapes], ensure_ascii=False)
    return (f'data-compte data-depart="{depart.isoformat()}" data-fin="{fin.isoformat()}" '
            f'data-etapes="{echapper(donnees)}"')


def compte_en_html(depart, fin, aujourd_hui, etapes=(), balise="p", classe="compte"):
    """L'élément du compte à rebours, écrit pour aujourd'hui et tenu à jour par le script."""
    return (f'<{balise} class="{classe}" {attributs_compte(depart, fin, etapes)}>'
            f'{echapper(texte_compte(depart, fin, aujourd_hui, etapes), quote=False)}</{balise}>')


STYLE_COMPTE = """
p.compte { margin: .1rem 0 .7rem; font-weight: 600; color: var(--accent); }
a.voyage span.compte { display: block; color: var(--accent); font-weight: 600; }
div.prochain { background: var(--carte); border-radius: 14px; padding: .8rem 1rem; margin: .4rem 0 .8rem;
               box-shadow: 0 1px 3px rgba(0,0,0,.08); }
div.prochain a { color: var(--texte); text-decoration: none; display: block; }
div.prochain .titre { font-size: .85rem; color: var(--doux); }
div.prochain .compte { display: block; font-size: 1.4rem; font-weight: 700; color: var(--accent); margin-top: .1rem; }
"""

# Même règle que texte_compte, avec la date du téléphone. Recalcul au retour sur la page
# (visibilitychange) et toutes les heures : une page restée ouverte passe minuit.
SCRIPT_COMPTE = """
(function () {
    function jour(iso) { return new Date(iso + 'T12:00:00'); }
    function ecart(a, b) { return Math.round((jour(b) - jour(a)) / 86400000); }
    function auj() {
        const d = new Date();
        return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0');
    }
    function texteCompte(depart, fin, aujourdhui, etapes) {
        const avant = ecart(aujourdhui, depart);
        if (avant > 1) return 'Départ dans ' + avant + ' jours';
        if (avant === 1) return 'Départ demain !';
        if (aujourdhui <= fin) {
            const n = ecart(depart, aujourdhui) + 1, total = ecart(depart, fin) + 1;
            const etape = (etapes || []).find(function (e) { return e.du <= aujourdhui && aujourdhui <= e.au; });
            let texte = n === 1 ? 'C\\u2019est le départ ! · jour 1 sur ' + total
                      : n === total ? 'Dernier jour · jour ' + n + ' sur ' + total
                      : 'Jour ' + n + ' sur ' + total;
            return texte + (etape ? ' · ' + etape.destination : '');
        }
        const depuis = ecart(fin, aujourdhui);
        return 'Rentrés depuis ' + depuis + ' jour' + (depuis > 1 ? 's' : '');
    }
    window.texteCompte = texteCompte;
    function majComptes() {
        const a = auj();
        document.querySelectorAll('[data-compte]').forEach(function (el) {
            let etapes = [];
            try { etapes = JSON.parse(el.dataset.etapes || '[]'); } catch (e) {}
            el.textContent = texteCompte(el.dataset.depart, el.dataset.fin, a, etapes);
        });
    }
    majComptes();
    document.addEventListener('visibilitychange', function () { if (!document.hidden) majComptes(); });
    setInterval(majComptes, 3600000);
})();
"""
