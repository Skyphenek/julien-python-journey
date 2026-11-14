"""Casa Binomerie — les retours de cuisson (14/11/2026) : une note de 1 à 5 par personne et par plat mangé, des
raisons en un appui, un mot facultatif. Chacun note sur son téléphone (« casa-qui », comme Sortir).

- a_noter : sur Aujourd'hui, les plats faits maison des JOURS_A_NOTER derniers jours que cette personne n'a pas notés ;
- resume : par plat, la moyenne, la dernière note de chacun et les raisons les plus citées (fiche, Coups de cœur) ;
- le skill chef-casa lit tout par GET /api/avis : une recette « passée au chef » tient-elle ses ≥ 4/5 ?
"""
import re
from collections import Counter
from datetime import date, timedelta

JOURS_A_NOTER = 3           # aujourd'hui et les 3 jours d'avant
QUI = ("julien", "laetitia")
MOMENTS_AVIS = ("diner", "dejeuner", "brunch", "libre")       # « libre » : noté depuis la fiche, hors d'un repas
GENRES_A_NOTER = ("plat", "dessert", "entree")                 # un accompagnement se note avec son plat
# Ce qui coince (une note de 1 à 3, ou une réserve à 4)
RAISONS_MOINS = [("trop-sale", "trop salé"), ("fade", "fade"), ("trop-epice", "trop épicé"), ("trop-gras", "trop gras"),
                 ("trop-cuit", "trop cuit"), ("pas-assez-cuit", "pas assez cuit"), ("sec", "sec"),
                 ("pas-assez", "pas assez copieux"), ("trop-long", "trop long"), ("complique", "trop compliqué")]
# Ce qui a plu (4 ou 5)
RAISONS_PLUS = [("a-refaire", "à refaire tel quel"), ("la-sauce", "la sauce"), ("la-cuisson", "la cuisson"),
                ("rapide", "rapide à faire"), ("copieux", "copieux")]
_ID = re.compile(r"[A-Za-z0-9-]{8,64}")


def valider_avis(corps, aujourd_hui):
    """Un avis : {plat, jour (≤ aujourd'hui, 60 jours au plus), moment, qui, note (1-5, ou None = pas d'avis),
    raisons (connues, sans doublon), mot (300 caractères)}."""
    if not isinstance(corps, dict):
        raise ValueError("avis invalide")
    if not isinstance(corps.get("plat"), str) or not _ID.fullmatch(corps["plat"]):
        raise ValueError("plat invalide")
    try:
        jour = date.fromisoformat(corps.get("jour"))
    except (TypeError, ValueError):
        raise ValueError("jour invalide") from None
    if not 0 <= (aujourd_hui - jour).days <= 60:
        raise ValueError("jour hors limites")
    if corps.get("moment") not in MOMENTS_AVIS:
        raise ValueError("moment invalide")
    if corps.get("qui") not in QUI:
        raise ValueError("qui invalide")
    note = corps.get("note")
    if note is not None and (isinstance(note, bool) or not isinstance(note, int) or not 1 <= note <= 5):
        raise ValueError("note invalide (1 à 5)")
    raisons = corps.get("raisons") or []
    connues = dict(RAISONS_MOINS) | dict(RAISONS_PLUS)
    if not isinstance(raisons, list) or not all(r in connues for r in raisons) or len(set(raisons)) != len(raisons):
        raise ValueError("raisons invalides")
    mot = corps.get("mot") or ""
    if not isinstance(mot, str) or len(mot) > 300:
        raise ValueError("mot invalide")
    return {"plat": corps["plat"], "jour": jour, "moment": corps["moment"], "qui": corps["qui"], "note": note,
            "raisons": raisons if note is not None else [], "mot": mot.strip() if note is not None else ""}


def a_noter(repas, plats, avis, qui, aujourd_hui):
    """Les plats faits maison d'aujourd'hui et des JOURS_A_NOTER jours d'avant (plats, desserts, entrées) que `qui`
    n'a pas notés (un « pas d'avis » compte comme noté), du plus récent au plus ancien : [{plat, nom, jour, moment}]."""
    par_id = {p["id"]: p for p in plats}
    notes = {(a["plat"], a["jour"], a["moment"]) for a in avis if a["qui"] == qui}
    debut = aujourd_hui - timedelta(days=JOURS_A_NOTER)
    resultat = []
    for r in sorted(repas, key=lambda r: (r["jour"], r["moment"] != "diner"), reverse=True):
        if r["issue"] != "fait" or not debut <= r["jour"] <= aujourd_hui:
            continue
        for i in r["plats"]:
            p = par_id.get(i)
            if p and p["genre"] in GENRES_A_NOTER and (i, r["jour"], r["moment"]) not in notes:
                resultat.append({"plat": i, "nom": p["nom"], "jour": r["jour"].isoformat(), "moment": r["moment"]})
    return resultat


def resume(avis):
    """{plat: {moyenne (1 décimale), nb, julien, laetitia (leur dernière note ou None), raisons (les plus citées,
    3 au plus)}} — les « pas d'avis » ne comptent pas."""
    par_plat = {}
    for a in sorted((a for a in avis if a["note"] is not None), key=lambda a: a["jour"]):
        r = par_plat.setdefault(a["plat"], {"notes": [], "julien": None, "laetitia": None, "raisons": Counter()})
        r["notes"].append(a["note"])
        r[a["qui"]] = a["note"]
        r["raisons"].update(a["raisons"])
    return {i: {"moyenne": round(sum(r["notes"]) / len(r["notes"]), 1), "nb": len(r["notes"]),
                "julien": r["julien"], "laetitia": r["laetitia"],
                "raisons": [c for c, _ in sorted(r["raisons"].items(), key=lambda x: (-x[1], x[0]))[:3]]}
            for i, r in par_plat.items()}


# Le formulaire d'avis, commun à Aujourd'hui et à la fiche recette (Dîners) : une note, des raisons, un mot.
# formulaireAvis(cible, o) — o : {nom, raisons: {moins, plus}, envoyer(corps) -> Promise, fini()} ; corps =
# {note, raisons, mot} (note null = « Pas d'avis »).
SCRIPT_FORM_AVIS = r"""
// L'étoile au trait (la classe « pleine » la remplit), commune au formulaire et aux notes affichées
const ETOILE_AVIS = '<svg viewBox="0 0 24 24" width="1em" height="1em" aria-hidden="true"><path d="M12 2.8l2.8 5.9 6.4.8-4.7 4.4 1.2 6.4L12 17.2l-5.7 3.1 1.2-6.4-4.7-4.4 6.4-.8z" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/></svg>';
function formulaireAvis(cible, o) {
    function el(b, c, t) { const e = document.createElement(b); if (c) e.className = c; if (t !== undefined) e.textContent = t; return e; }
    function bouton(t, c, f) { const b = el('button', c, t); b.type = 'button'; b.addEventListener('click', f); return b; }
    let note = null; const choisies = [];
    const f = el('div', 'form-avis');
    f.append(el('strong', 'titre-avis', o.nom + ' : ton avis ?'));
    const etoiles = el('div', 'etoiles');
    const zone = el('div', 'raisons-avis'), msg = el('p', 'message');
    const mot = el('input', 'mot-avis'); mot.type = 'text'; mot.maxLength = 300; mot.placeholder = 'Un mot ? (facultatif)';
    mot.setAttribute('aria-label', 'Un mot (facultatif)');
    const envoyer = bouton('Envoyer', 'plein', function () { partir({ note: note, raisons: choisies.slice(), mot: mot.value.trim() }); });
    envoyer.disabled = true;
    const passer = bouton("Pas d'avis", 'petit', function () { partir({ note: null, raisons: [], mot: '' }); });
    function partir(corps) {
        envoyer.disabled = true; passer.disabled = true; msg.textContent = '';
        o.envoyer(corps).then(function () { o.fini(corps.note); },
            function () { msg.textContent = 'Pas envoyé : réessaie une fois connecté.'; envoyer.disabled = note === null; passer.disabled = false; });
    }
    function puces(titre, liste) {
        const g = el('div', 'groupe-raisons'); g.append(el('span', 'aide', titre));
        liste.forEach(function (r) {
            const b = bouton(r[1], choisies.indexOf(r[0]) >= 0 ? 'puce actif' : 'puce', function () {
                const i = choisies.indexOf(r[0]);
                if (i >= 0) choisies.splice(i, 1); else choisies.push(r[0]);
                b.classList.toggle('actif', i < 0); b.setAttribute('aria-pressed', String(i < 0));
            });
            b.setAttribute('aria-pressed', String(choisies.indexOf(r[0]) >= 0));
            g.append(b);
        });
        return g;
    }
    function raisons() {
        zone.replaceChildren();
        if (note === null) return;
        if (note >= 4) zone.append(puces("Qu'est-ce qui a plu ?", o.raisons.plus), puces('Une réserve ?', o.raisons.moins));
        else zone.append(puces("Qu'est-ce qui coince ?", o.raisons.moins));
    }
    [1, 2, 3, 4, 5].forEach(function (n) {
        const b = bouton('', 'etoile', function () {
            note = n; envoyer.disabled = false;
            etoiles.querySelectorAll('button').forEach(function (x, i) { x.classList.toggle('pleine', i < n); });
            raisons();
        });
        b.innerHTML = ETOILE_AVIS;
        b.setAttribute('aria-label', n + ' sur 5');
        etoiles.append(b);
    });
    const actions = el('div', 'actions-avis'); actions.append(envoyer, passer);
    f.append(etoiles, zone, mot, actions, msg);
    cible.append(f);
}
"""

STYLE_AVIS = """
div.form-avis { display: flex; flex-direction: column; gap: 10px; }
div.form-avis .titre-avis { font-size: 17px; font-weight: 800; }
div.form-avis .etoiles { display: flex; gap: 4px; }
div.form-avis button.etoile { width: 48px; height: 48px; font-size: 30px; line-height: 1; border: none; background: none; color: var(--doux);
                              padding: 0; font-family: inherit; cursor: pointer; }
div.form-avis button.etoile.pleine { color: var(--diners); }
button.etoile svg path, span.note-avis svg path { fill: none; }
button.etoile.pleine svg path, span.note-avis svg path { fill: currentColor; }
span.note-avis svg { vertical-align: -0.12em; }
div.form-avis .groupe-raisons { display: flex; flex-wrap: wrap; gap: 6px; align-items: center; }
div.form-avis .groupe-raisons .aide { flex-basis: 100%; font-size: 13px; color: var(--doux); font-weight: 700; }
div.form-avis button.puce { min-height: 40px; padding: 6px 12px; border-radius: 999px; border: 2px solid var(--ligne);
                            background: var(--blanc); color: var(--texte); font: inherit; font-size: 14px; font-weight: 700; }
div.form-avis button.puce.actif { border-color: var(--diners); color: var(--diners); }
div.form-avis input.mot-avis { font: inherit; font-size: 16px; min-height: 44px; padding: 0 12px; border-radius: 14px;
                               border: 2px solid var(--ligne); background: var(--blanc); color: var(--texte); }
div.form-avis .actions-avis { display: flex; gap: 8px; flex-wrap: wrap; }
div.form-avis .actions-avis button { min-height: 48px; border-radius: 999px; font: inherit; font-weight: 800; padding: 0 18px;
                                     border: 2px solid var(--ligne); background: var(--blanc); color: var(--texte); }
div.form-avis .actions-avis button.plein { flex: 1 1 160px; background: var(--diners); border-color: var(--diners); color: #ffffff; }
div.form-avis .actions-avis button:disabled { opacity: .5; }
div.form-avis p.message { color: var(--diners); font-weight: 700; margin: 0; }
"""
