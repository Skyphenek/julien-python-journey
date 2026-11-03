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
a.bloc-courses { display: flex; flex-direction: column; gap: 4px;
                background: var(--courses-doux); color: var(--texte); text-decoration: none;
                border-radius: 24px; padding: 18px 20px; margin: 16px 0; }
a.bloc-courses strong { font-size: 19px; font-weight: 800; color: var(--courses); }
a.bloc-courses span { font-weight: 700; }
a.bloc-budget { display: flex; flex-direction: column; gap: 2px; background: var(--carte); color: var(--texte);
                text-decoration: none; border-radius: 24px; padding: 16px 20px; margin: 16px 0; }
a.bloc-budget strong { font-size: 19px; font-weight: 800; }
a.bloc-budget span { color: var(--doux); font-size: 14px; }
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
div.bloc-a-finir { background: var(--carte); border-radius: 24px; padding: 18px 20px; margin: 16px 0; }
div.bloc-a-finir .titre { font-size: 13px; font-weight: 800; letter-spacing: .06em; text-transform: uppercase;
                          color: var(--diners); }
div.bloc-a-finir ul { list-style: none; margin: 8px 0 0; padding: 0; }
div.bloc-a-finir > ul > li { padding: 12px 0; border-top: 1px solid var(--ligne); }
div.bloc-a-finir .produit { display: flex; flex-direction: column; gap: 2px; }
div.bloc-a-finir .produit strong { font-size: 17px; font-weight: 800; }
div.bloc-a-finir .produit span, div.bloc-a-finir p.pris, div.bloc-a-finir small { color: var(--doux); font-size: 14px; }
div.bloc-a-finir .actions { display: flex; gap: 8px; margin: 8px 0 0; }
div.bloc-a-finir button { min-height: 40px; border-radius: 14px; border: 2px solid var(--ligne); background: var(--blanc);
                          color: var(--texte); font-family: inherit; font-weight: 700; font-size: 14px; padding: 0 12px; }
div.bloc-a-finir ul.plats li { display: flex; align-items: center; justify-content: space-between; gap: 8px; padding: 6px 0; }
div.bloc-a-finir ul.plats li span { display: flex; flex-direction: column; min-width: 0; }
div.bloc-a-finir ul.plats button { border-color: var(--diners); color: var(--diners); flex: none; }
div.bloc-a-finir p.pris { margin: 6px 0 0; }
div.bloc-a-finir .message { margin: 8px 0 0; color: var(--diners); font-weight: 700; font-size: 14px; }
div.bloc-vin { background: var(--carte); border-radius: 24px; padding: 14px 16px; margin: 0 0 12px; }
div.bloc-vin .titre { display: block; font-size: 13px; font-weight: 800; color: var(--doux); }
div.bloc-vin ul { list-style: none; margin: 4px 0 8px; padding: 0; }
div.bloc-vin li span { display: block; color: var(--doux); font-size: 13px; }
div.bloc-vin .choix { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }
div.bloc-vin [hidden], div.bloc-vin button.lien[hidden] { display: none; }
div.bloc-vin p.message { margin: 6px 0 0; color: var(--diners); font-weight: 700; font-size: 14px; }
div.bloc-vin p.message:empty { display: none; }
div.bloc-vin ul:not(:has(li:not([hidden]))) { display: none; }
div.bloc-vin button { min-height: 40px; border-radius: 14px; border: 2px solid var(--ligne); background: var(--blanc);
                      color: var(--texte); font-family: inherit; font-weight: 700; font-size: 14px; padding: 0 14px; }
div.bloc-vin button[data-action="ouverte"] { border-color: var(--cave); color: var(--cave); }
div.bloc-vin button.lien { all: unset; box-sizing: border-box; display: inline-flex; align-items: center; min-height: 40px;
                           padding: 0 6px; cursor: pointer; text-decoration: underline; color: var(--doux); font-size: 13px; }
div.bloc-vin button.lien:focus-visible { outline: 2px solid var(--diners); outline-offset: 2px; border-radius: 6px; }
"""


def bloc_courses(a_acheter):
    """Ce qu'il faut acheter pour les repas du jour (diners.a_acheter_aujourd_hui) ; rien à acheter : rien."""
    if not a_acheter:
        return ""
    return (f'<a class="bloc-courses" href="courses"><strong>À acheter pour aujourd\'hui</strong>'
            f'<span>{echapper(" · ".join(a_acheter))}</span></a>')


def bloc_budget(semaine):
    """« Cette semaine : 82 € · dont livraison et resto 35 € » (budget.semaines_budget) ; rien tant que c'est 0 €."""
    from budget import euros
    if not semaine or not semaine["total"]:
        return ""
    return (f'<a class="bloc-budget" href="budget"><strong>Cette semaine : {euros(semaine["total"])}</strong>'
            f'<span>dont livraison et resto {euros(semaine["livraison"])}</span></a>')


def bloc_ce_soir(plats):
    """Le dîner de ce soir : le plat principal en grand, les autres plats à la suite."""
    if plats:
        principal = next((p for p in plats if p.get("genre") == "plat"), plats[0])
        autres = [p["nom"] for p in plats if p is not principal]
        avec = f'avec {echapper(", ".join(autres))} · ' if autres else ""
        return (f'<a class="bloc-ce-soir" href="diners#ce-soir"><span class="titre">Ce soir</span>'
                f'<strong>{echapper(principal["nom"])}</strong><span>{principal["minutes"]} min · {avec}voir la recette</span></a>')
    return ('<a class="bloc-ce-soir vide" href="diners#ce-soir"><span class="titre">Ce soir</span>'
            '<strong>Rien de prévu</strong><span>Voir ce que le placard permet en 20 minutes</span></a>')


def _vin_en_li(v, classe=""):
    millesime = f' {v["millesime"]}' if v.get("millesime") else ""
    attributs = f' class="{classe}"' if classe else ""
    lieu = ", ".join(x for x in (v.get("region"), v.get("pays") if v.get("pays") not in (None, "", "France") else "")
                     if x)
    lieu = f"{echapper(lieu)} · " if lieu else ""
    return (f'<li data-id="{echapper(v["id"])}"{attributs} hidden><strong>{echapper(v["nom"])}{millesime}</strong>'
            f'<span>{lieu}à boire avant {v["fin"]}</span></li>')


def bloc_vin(vins, belle):
    """Le vin du soir (accords_vins.suggerer) : la première suggestion visible, [Autre] pour les suivantes,
    « Une belle bouteille ? » pour la belle (belle bouteille d'un soir de semaine). Rien si ni l'une ni l'autre."""
    vins = list(vins)
    if not vins and not belle:
        return ""
    lis = [_vin_en_li(v) for v in vins] + ([_vin_en_li(belle, "belle")] if belle else [])
    if vins:
        lis[0] = lis[0].replace(" hidden>", ">", 1)
    boutons = ('<button type="button" data-action="ouverte"' + ("" if vins else " hidden") + '>Ouverte</button>'
               + ('<button type="button" data-action="autre">Autre</button>' if len(vins) > 1 else ""))
    lien = '<button type="button" class="lien" data-action="belle">Une belle bouteille ?</button>' if belle else ""
    return (f'<div class="bloc-vin"><span class="titre">À ouvrir</span><ul>{"".join(lis)}</ul>'
            f'<div class="choix">{boutons}{lien}</div><p class="message" aria-live="polite"></p></div>')


SCRIPT_VIN = """
(function () {
    const bloc = document.querySelector('div.bloc-vin');
    if (!bloc) return;
    const lis = Array.prototype.slice.call(bloc.querySelectorAll('li'));
    const ordinaires = lis.filter(function (li) { return !li.classList.contains('belle'); });
    let i = 0;
    function montrer(li) { lis.forEach(function (x) { x.hidden = x !== li; }); }
    function visible() { return lis.find(function (x) { return !x.hidden; }); }
    const autre = bloc.querySelector('[data-action="autre"]');
    if (autre) autre.addEventListener('click', function () { i = (i + 1) % ordinaires.length; montrer(ordinaires[i]); });
    const belle = bloc.querySelector('[data-action="belle"]');
    const ouverte = bloc.querySelector('[data-action="ouverte"]');
    if (belle) belle.addEventListener('click', function () {
        montrer(bloc.querySelector('li.belle')); belle.hidden = true; ouverte.hidden = false;
    });
    ouverte.addEventListener('click', function () {
        const li = visible();
        if (!li) return;
        bloc.querySelectorAll('button').forEach(function (x) { x.disabled = true; });
        fetch('api/cave/' + encodeURIComponent(li.dataset.id) + '/bue', { method: 'POST' })
            .then(function (r) { if (!r.ok) throw new Error(r.status); location.reload(); })
            .catch(function () {
                bloc.querySelector('.message').textContent = 'Pas envoyé : réessaie une fois connecté.';
                bloc.querySelectorAll('button').forEach(function (x) { x.disabled = false; });
            });
    });
})();
"""


ISSUES_HIER = [("fait", "Fait maison"), ("commande", "Commandé"), ("dehors", "Dehors"), ("autre", "Autre")]


def bloc_hier(diner_hier):
    """« Hier soir ? » tant que le dîner d'hier n'est pas renseigné : c'est ce qui compte les Deliveroo."""
    if diner_hier["issue"]:
        return ""
    corps = json.dumps({"jour": diner_hier["jour"].isoformat(), "moment": "diner", "plats": diner_hier["plats"]})
    boutons = "".join(f'<button type="button" data-issue="{c}">{t}</button>' for c, t in ISSUES_HIER)
    return (f'<div class="bloc-hier" data-repas="{echapper(corps)}"><strong>Hier soir ?</strong>'
            f'<div class="choix">{boutons}</div><p class="message" aria-live="polite"></p></div>')


def bloc_compteur(c):
    if not c or not c["renseignes"]:
        return ""
    moyenne = f'{c["moyenne"]:.1f}'.replace(".", ",")
    etat = "ok" if c["semaine"] <= 1 else "trop"
    return (f'<div class="bloc-compteur {etat}"><span class="titre">Deliveroo</span>'
            f'<strong>{c["semaine"]} commande{"s" if c["semaine"] > 1 else ""} ces 7 jours</strong>'
            f'<span>Moyenne {moyenne} par semaine sur 6 semaines · objectif : 1 au plus · départ : 3</span></div>')


def _quand(jour, aujourd_hui):
    """« Ce soir », « Demain », ou le jour de la semaine (« Jeudi ») : le libellé d'un bouton."""
    ecart = (jour - aujourd_hui).days
    return "Ce soir" if ecart == 0 else "Demain" if ecart == 1 else JOURS[jour.weekday()].capitalize()


def _a_finir_quand(jusqu_au, aujourd_hui):
    ecart = (jusqu_au - aujourd_hui).days
    return "à finir aujourd'hui" if ecart == 0 else "à finir demain" if ecart == 1 else f"à finir d'ici {JOURS[jusqu_au.weekday()]}"


def bloc_a_finir(alertes, aujourd_hui):
    """Le frais qui va tourner (a_finir.alertes) : à vérifier ([Fini], [Encore bon]) ; à finir sans repas prévu à temps
    ([Fini], et jusqu'à 3 plats du carnet à poser au premier soir libre). Rien à signaler : rien."""
    if not alertes:
        return ""
    lignes = []
    for a in alertes:
        if a["etat"] == "a-verifier":
            etat = "à vérifier"
            boutons = ('<button type="button" data-action="fini">Fini</button>'
                       '<button type="button" data-action="encore-bon">Encore bon</button>')
        else:
            prevu = f'prévu {JOURS[a["trop_tard"].weekday()]}, trop tard' if a["trop_tard"] else "rien de prévu"
            etat = f'{_a_finir_quand(a["jusqu_au"], aujourd_hui)} · {prevu}'
            boutons = '<button type="button" data-action="fini">Fini</button>'
        plats = ""
        if a["suggestions"]:
            items = []
            for s in a["suggestions"]:
                manque = f'<small>il manque : {echapper(", ".join(s["manquants"]))}</small>' if s["manquants"] else ""
                bouton = (f'<button type="button" data-plat="{echapper(s["plat"]["id"])}" '
                          f'data-jour="{a["jour"].isoformat()}">{_quand(a["jour"], aujourd_hui)}</button>'
                          if a["jour"] else "")
                items.append(f'<li><span>{echapper(s["plat"]["nom"])}{manque}</span>{bouton}</li>')
            plats = f'<ul class="plats">{"".join(items)}</ul>'
            if not a["jour"]:
                plats += f'<p class="pris">soirs pris jusqu\'à {JOURS[a["jusqu_au"].weekday()]}</p>'
        lignes.append(f'<li data-cle="{echapper(a["cle"])}"><div class="produit"><strong>{echapper(a["nom"])}</strong>'
                      f'<span>{etat}</span></div><div class="actions">{boutons}</div>{plats}</li>')
    return (f'<div class="bloc-a-finir"><span class="titre">À finir</span><ul>{"".join(lignes)}</ul>'
            f'<p class="message" aria-live="polite"></p></div>')


SCRIPT_HIER = """
(function () {
    const bloc = document.querySelector('div.bloc-hier');
    if (!bloc) return;
    const repas = JSON.parse(bloc.dataset.repas);
    bloc.querySelectorAll('button').forEach(function (b) {
        b.addEventListener('click', function () {
            bloc.querySelectorAll('button').forEach(function (x) { x.disabled = true; });
            fetch('api/repas', { method: 'POST', headers: { 'Content-Type': 'application/json' },
                                 body: JSON.stringify(Object.assign({}, repas, { issue: b.dataset.issue })) })
                .then(function (r) { if (!r.ok) throw new Error(r.status); location.reload(); })
                .catch(function () {
                    bloc.querySelector('.message').textContent = 'Pas envoyé : réessaie une fois connecté.';
                    bloc.querySelectorAll('button').forEach(function (x) { x.disabled = false; });
                });
        });
    });
})();
"""


SCRIPT_A_FINIR = """
(function () {
    const bloc = document.querySelector('div.bloc-a-finir');
    if (!bloc) return;
    function envoyer(url, corps) {
        bloc.querySelectorAll('button').forEach(function (x) { x.disabled = true; });
        fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(corps) })
            .then(function (r) { if (!r.ok) throw new Error(r.status); location.reload(); })
            .catch(function (e) {
                bloc.querySelector('.message').textContent = (e && e.message === '409')
                    ? 'Ce soir-là est déjà pris : recharge la page.' : 'Pas envoyé : réessaie une fois connecté.';
                bloc.querySelectorAll('button').forEach(function (x) { x.disabled = false; });
            });
    }
    bloc.querySelectorAll('button[data-action]').forEach(function (b) {
        b.addEventListener('click', function () {
            const cle = b.closest('li[data-cle]').dataset.cle;
            envoyer('api/a-finir/' + encodeURIComponent(cle), { action: b.dataset.action });
        });
    });
    bloc.querySelectorAll('button[data-plat]').forEach(function (b) {
        b.addEventListener('click', function () {
            envoyer('api/repas', { jour: b.dataset.jour, moment: 'diner', plats: [b.dataset.plat], issue: null, si_libre: true });
        });
    });
})();
"""


def aujourdhui_en_html(voyages, aujourd_hui, a_acheter=(), plats_du_soir=(), diner_hier=None, compte=None,
                       semaine_budget=None, a_finir=(), vins=(), belle=None):
    """L'accueil du hub : ce soir (et le vin à ouvrir), hier soir, ce qui est à finir, ce qu'il faut acheter aujourd'hui, le budget de la
    semaine, le prochain voyage, le compteur Deliveroo."""
    v = prochain_voyage(voyages, aujourd_hui)
    blocs = (bloc_ce_soir(list(plats_du_soir)) + bloc_vin(vins, belle)
             + (bloc_hier(diner_hier) if diner_hier else "")
             + bloc_a_finir(list(a_finir), aujourd_hui) + bloc_courses(list(a_acheter))
             + bloc_budget(semaine_budget)
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
<script>{SCRIPT_A_FINIR}</script>
<script>{SCRIPT_VIN}</script>
</body>
</html>"""
