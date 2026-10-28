"""Casa Binomerie : le hub de la maison, dont En Vadrouille est une section.

La page Aujourd'hui : chaque module y remonte une ligne — ce soir, hier soir, les courses, le prochain
voyage, le compteur Deliveroo (spec : docs/superpowers/specs/2026-10-28-hub-maison-design.md).
"""
import json
from datetime import datetime
from html import escape as echapper
from urllib.parse import quote
from zoneinfo import ZoneInfo

from compte_a_rebours import compte_en_html, STYLE_COMPTE, SCRIPT_COMPTE
from design import STYLE_D, STYLE_NAV_HUB, TETE_POLICE, nav_hub
from programme import etapes_du_voyage
from pwa import TETE_PWA
from valise import HTML_STYLE, MOIS

NOM = "Casa Binomerie"
HORIZON_VADROUILLE = 60        # jours : au-delà, le prochain voyage ne s'affiche pas sur Aujourd'hui
JOURS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]


def aujourd_hui_paris():
    """La date à Paris : le serveur (Render) est en UTC, « ce soir » ne doit pas basculer à 1 h du matin."""
    return datetime.now(ZoneInfo("Europe/Paris")).date()


def jour_en_clair(d):
    return f"{JOURS[d.weekday()]} {d.day} {MOIS[d.month - 1]}"


def prochain_voyage(voyages, aujourd_hui):
    """Le voyage en cours, ou le plus proche qui part dans moins de HORIZON_VADROUILLE jours ; sinon None."""
    candidats = [v for v in voyages
                 if v["fin"] >= aujourd_hui and (v["depart"] - aujourd_hui).days < HORIZON_VADROUILLE]
    return min(candidats, key=lambda v: v["depart"], default=None)


def bloc_vadrouille(v, aujourd_hui):
    etapes = etapes_du_voyage([e for e in v.get("etapes", []) if e.get("jours")], v["depart"])
    return (f'<div class="bloc-vadrouille"><a href="vadrouille?v={quote(v["code"])}">'
            f'<span class="titre">En Vadrouille · {echapper(v["libelle"])}</span>'
            f'{compte_en_html(v["depart"], v["fin"], aujourd_hui, etapes, balise="span")}</a></div>')


STYLE_CASA = """
p.date-du-jour { font-size: 17px; font-weight: 700; color: var(--doux); margin: -8px 0 18px; }
p.date-du-jour::first-letter { text-transform: uppercase; }
div.bloc-vadrouille { background: var(--valise); border-radius: 32px; padding: 22px; margin: 16px 0; }
div.bloc-vadrouille a { color: #ffffff; text-decoration: none; display: block; }
div.bloc-vadrouille .titre { display: block; color: #e3e8ff; font-size: 15px; }
div.bloc-vadrouille .compte { display: block; color: #ffffff; font-size: 30px; font-weight: 800;
                              letter-spacing: -0.02em; }
a.bloc-courses { display: flex; justify-content: space-between; align-items: center; gap: 12px;
                background: var(--courses-doux); color: var(--texte); text-decoration: none;
                border-radius: 24px; padding: 18px 20px; margin: 16px 0; }
a.bloc-courses strong { font-size: 19px; font-weight: 800; color: var(--courses); }
a.bloc-courses span { font-weight: 700; }
a.bloc-ce-soir { display: flex; flex-direction: column; gap: 2px; background: #c2410c; color: #ffffff;
                text-decoration: none; border-radius: 28px; padding: 20px 22px; margin: 16px 0; }
a.bloc-ce-soir.vide { background: var(--diners-doux); color: var(--texte); }
a.bloc-ce-soir .titre { font-size: 14px; font-weight: 700; opacity: .85; }
a.bloc-ce-soir strong { font-size: 28px; font-weight: 800; line-height: 1.05; letter-spacing: -0.02em; }
a.bloc-ce-soir.vide strong { color: var(--diners); }
div.bloc-hier { background: var(--carte); border-radius: 24px; padding: 18px 20px; margin: 16px 0; display: flex;
                flex-direction: column; gap: 10px; }
div.bloc-hier strong { font-size: 19px; font-weight: 800; }
div.bloc-hier .choix { display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; }
div.bloc-hier button { min-height: 48px; border-radius: 16px; border: 2px solid var(--ligne); background: var(--blanc);
                       color: var(--texte); font-family: inherit; font-weight: 700; font-size: 15px; }
div.bloc-hier button[data-issue="commande"] { border-color: var(--diners); color: var(--diners); }
div.bloc-hier .message { margin: 0; color: var(--diners); font-weight: 700; font-size: 14px; }
div.bloc-compteur { display: flex; flex-direction: column; gap: 2px; border-radius: 24px; padding: 16px 20px; margin: 16px 0;
                    background: var(--carte); }
div.bloc-compteur .titre { font-size: 13px; font-weight: 800; letter-spacing: .06em; text-transform: uppercase; color: var(--doux); }
div.bloc-compteur strong { font-size: 20px; font-weight: 800; }
div.bloc-compteur.ok strong { color: var(--courses); }
div.bloc-compteur.trop strong { color: var(--diners); }
div.bloc-compteur span:last-child { color: var(--doux); font-size: 14px; }
p.attente { background: var(--carte); border-radius: 24px; padding: 18px; color: var(--doux); }
"""


def bloc_courses(a_prendre):
    if not a_prendre:
        return ""
    return (f'<a class="bloc-courses" href="courses"><strong>Courses</strong>'
            f'<span>{a_prendre} article{"s" if a_prendre > 1 else ""} à prendre</span></a>')


def bloc_ce_soir(plat):
    if plat:
        return (f'<a class="bloc-ce-soir" href="diners#ce-soir"><span class="titre">Ce soir</span>'
                f'<strong>{echapper(plat["nom"])}</strong><span>{plat["minutes"]} min · voir la recette</span></a>')
    return ('<a class="bloc-ce-soir vide" href="diners#ce-soir"><span class="titre">Ce soir</span>'
            '<strong>Rien de prévu</strong><span>Voir ce que le placard permet en 20 minutes</span></a>')


ISSUES_HIER = [("fait", "Fait maison"), ("commande", "Commandé"), ("dehors", "Dehors"), ("autre", "Autre")]


def bloc_hier(soir_hier):
    """« Hier soir ? » tant que le soir d'hier n'est pas renseigné : c'est ce qui compte les Deliveroo."""
    if soir_hier["issue"]:
        return ""
    corps = json.dumps({"jour": soir_hier["jour"].isoformat(), "plat": soir_hier["plat"]})
    boutons = "".join(f'<button type="button" data-issue="{c}">{t}</button>' for c, t in ISSUES_HIER)
    return (f'<div class="bloc-hier" data-soir="{echapper(corps)}"><strong>Hier soir ?</strong>'
            f'<div class="choix">{boutons}</div><p class="message" aria-live="polite"></p></div>')


def bloc_compteur(c):
    if not c or not c["renseignes"]:
        return ""
    moyenne = f'{c["moyenne"]:.1f}'.replace(".", ",")
    etat = "ok" if c["semaine"] <= 1 else "trop"
    return (f'<div class="bloc-compteur {etat}"><span class="titre">Deliveroo</span>'
            f'<strong>{c["semaine"]} commande{"s" if c["semaine"] > 1 else ""} ces 7 jours</strong>'
            f'<span>Moyenne {moyenne} par semaine sur 6 semaines · objectif : 1 au plus · départ : 3</span></div>')


SCRIPT_HIER = """
(function () {
    const bloc = document.querySelector('div.bloc-hier');
    if (!bloc) return;
    const soir = JSON.parse(bloc.dataset.soir);
    bloc.querySelectorAll('button').forEach(function (b) {
        b.addEventListener('click', function () {
            bloc.querySelectorAll('button').forEach(function (x) { x.disabled = true; });
            fetch('api/soirs', { method: 'POST', headers: { 'Content-Type': 'application/json' },
                                 body: JSON.stringify(Object.assign({}, soir, { issue: b.dataset.issue })) })
                .then(function (r) { if (!r.ok) throw new Error(r.status); location.reload(); })
                .catch(function () {
                    bloc.querySelector('.message').textContent = 'Pas envoyé : réessaie une fois connecté.';
                    bloc.querySelectorAll('button').forEach(function (x) { x.disabled = false; });
                });
        });
    });
})();
"""


def aujourdhui_en_html(voyages, aujourd_hui, a_prendre=0, plat_du_soir=None, soir_hier=None, compte=None):
    """L'accueil du hub : ce soir, hier soir, les courses, le prochain voyage, le compteur Deliveroo."""
    v = prochain_voyage(voyages, aujourd_hui)
    blocs = (bloc_ce_soir(plat_du_soir) + (bloc_hier(soir_hier) if soir_hier else "") + bloc_courses(a_prendre)
             + (bloc_vadrouille(v, aujourd_hui) if v else "") + bloc_compteur(compte))
    return f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{NOM}</title>
{TETE_PWA}
{TETE_POLICE}
<style>{HTML_STYLE}{STYLE_COMPTE}{STYLE_D}{STYLE_NAV_HUB}{STYLE_CASA}</style>
</head>
<body class="accueil hub-page">
<h1>{NOM}</h1>
<p class="date-du-jour">{jour_en_clair(aujourd_hui)}</p>
{blocs}
{nav_hub("aujourdhui")}
<script>{SCRIPT_COMPTE}</script>
<script>{SCRIPT_HIER}</script>
</body>
</html>"""
