"""Casa Binomerie — Budget de la maison : combien ont coûté les courses et les repas, semaine par semaine.

Chiffres estimés, zéro saisie (spec 2026-11-02-casa-budget-design.md) :
- courses : le journal des achats (db.lire_achats), au prix d'un panier parisien (prix_paris) ;
- commandes et restos : les repas marqués « Commandé » (35 € pour deux) ou « Dehors » (60 € pour deux) ;
- repas maison : affichés pour comparer (coût moyen de leurs recettes), jamais ajoutés au total.
Semaine du lundi au dimanche.
"""
import math
from datetime import timedelta
from html import escape as echapper

from diners import LIVRAISON_DEUX
from prix_paris import cout_repas
from design import STYLE_D, STYLE_NAV_HUB, TETE_POLICE, nav_hub
from pwa import TETE_PWA
from valise import HTML_STYLE

FORFAIT_RESTO = 60          # un resto pour deux à Paris : l'ordre de grandeur
SEMAINES = 12


def lundi(jour):
    return jour - timedelta(days=jour.weekday())


def euros(x):
    """Arrondi à l'euro, le demi vers le haut (round() de Python arrondit 36,5 à 36)."""
    return f"{math.floor(x + 0.5)} €"


def semaines_budget(achats, repas, plats, aujourd_hui, n=SEMAINES):
    """Les n dernières semaines, la semaine en cours en premier (voir la docstring du module)."""
    premier_achat = min((a["jour"] for a in achats), default=None)
    semaines = []
    for k in range(n):
        debut = lundi(aujourd_hui) - timedelta(weeks=k)
        fin = debut + timedelta(days=6)
        achetes = [a for a in achats if debut <= a["jour"] <= fin]
        vecus = [r for r in repas if debut <= r["jour"] <= fin]
        commandes = sum(1 for r in vecus if r["issue"] == "commande")
        restos = sum(1 for r in vecus if r["issue"] == "dehors")
        maison = [r for r in vecus if r["issue"] == "fait"]
        couts = [sum(cout_repas(plats[i]["ingredients"], plats[i]["recette"]) for i in r["plats"] if i in plats)
                 for r in maison if any(i in plats for i in r["plats"])]
        courses = round(sum(a["prix"] or 0 for a in achetes), 2)
        livraison = commandes * LIVRAISON_DEUX + restos * FORFAIT_RESTO
        semaines.append({
            "lundi": debut, "courses": courses, "courses_suivies": premier_achat is not None and fin >= premier_achat,
            "sans_prix": sum(1 for a in achetes if a["prix"] is None),
            "commandes": commandes, "restos": restos, "livraison": livraison, "total": round(courses + livraison, 2),
            "maison": len(maison), "cout_maison": round(sum(couts) / len(couts), 2) if couts else None,
            "economie": round(len(couts) * LIVRAISON_DEUX - sum(couts), 2)})
    return semaines


def moyenne_precedentes(semaines, k=4):
    """Le total moyen des k semaines avant la semaine en cours, celles sans aucun chiffre ignorées ; None sinon."""
    precedentes = [s for s in semaines[1:1 + k] if s["total"] or s["maison"]]
    return round(sum(s["total"] for s in precedentes) / len(precedentes), 2) if precedentes else None


# --- Page ---------------------------------------------------------------------------------------

STYLE_BUDGET = """
div.chiffres { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 8px; margin: 0 0 16px; }
div.chiffres div { background: var(--carte); border-radius: 18px; padding: 12px; display: flex; flex-direction: column; gap: 2px; }
div.chiffres strong { font-size: 22px; font-weight: 800; }
div.chiffres span { font-size: 12px; color: var(--doux); font-weight: 600; }
p.note-budget { color: var(--doux); font-size: 13px; margin: 0 0 12px; }
svg.graphique { width: 100%; height: auto; display: block; margin: 0 0 8px; }
svg.graphique .barre-courses { fill: var(--courses); }
svg.graphique .barre-livraison { fill: var(--diners); }
svg.graphique text { fill: var(--doux); font-size: 9px; font-family: inherit; }
p.legende { font-size: 13px; color: var(--doux); margin: 0 0 16px; display: flex; gap: 14px; }
p.legende span::before { content: ""; display: inline-block; width: 10px; height: 10px; border-radius: 3px; margin-right: 5px; }
p.legende .l-courses::before { background: var(--courses); }
p.legende .l-livraison::before { background: var(--diners); }
div.tableau { overflow-x: auto; }
table.budget { width: 100%; border-collapse: collapse; font-size: 14px; }
table.budget th { text-align: left; font-size: 12px; color: var(--doux); font-weight: 700; padding: 6px 4px; }
table.budget td { padding: 10px 4px; border-top: 1px solid var(--ligne); white-space: nowrap; }
table.budget td.total { font-weight: 800; }
table.budget td small { color: var(--doux); font-size: 12px; display: block; }
"""

HAUTEUR, LARGEUR = 140, 360


def graphique_svg(semaines):
    """Barres empilées (courses en bas, commandes et restos au-dessus), la plus ancienne semaine à gauche."""
    ordre = list(reversed(semaines))
    haut = max((s["total"] for s in ordre), default=0) or 1
    pas = LARGEUR / len(ordre)
    barres = []
    for k, s in enumerate(ordre):
        x = k * pas + pas * 0.15
        l = pas * 0.7
        h_courses = s["courses"] / haut * (HAUTEUR - 20)
        h_livraison = s["livraison"] / haut * (HAUTEUR - 20)
        bas = HAUTEUR - 14
        barres.append(
            f'<rect class="barre-courses" x="{x:.1f}" y="{bas - h_courses:.1f}" width="{l:.1f}" height="{h_courses:.1f}" rx="2"/>'
            f'<rect class="barre-livraison" x="{x:.1f}" y="{bas - h_courses - h_livraison:.1f}" width="{l:.1f}" '
            f'height="{h_livraison:.1f}" rx="2"/>'
            f'<text x="{x + l / 2:.1f}" y="{HAUTEUR - 2}" text-anchor="middle">{s["lundi"]:%d/%m}</text>')
    return (f'<svg class="graphique" viewBox="0 0 {LARGEUR} {HAUTEUR}" role="img" '
            f'aria-label="Dépenses des {len(ordre)} dernières semaines">{"".join(barres)}</svg>')


def _ligne(s):
    courses = euros(s["courses"]) if s["courses_suivies"] else '— <small>pas encore suivi</small>'
    if s["sans_prix"]:
        courses += f'<small>{s["sans_prix"]} article{"s" if s["sans_prix"] > 1 else ""} sans prix</small>'
    detail = " · ".join(x for x in (f'{s["commandes"]} livr.' if s["commandes"] else "",
                                    f'{s["restos"]} resto' if s["restos"] else "") if x)
    livraison = euros(s["livraison"]) + (f"<small>{detail}</small>" if detail else "")
    maison = (f'{s["maison"]}' + (f'<small>{euros(s["cout_maison"])} / repas</small>' if s["cout_maison"] is not None else "")
              if s["maison"] else "—")
    return (f'<tr><td>{s["lundi"]:%d/%m}</td><td>{courses}</td><td>{livraison}</td>'
            f'<td class="total">{euros(s["total"])}</td><td>{maison}</td></tr>')


def budget_en_html(semaines, moyenne):
    """La page Budget : les chiffres de la semaine, le graphique des 12 dernières, le tableau."""
    s = semaines[0]
    chiffres = (f'<div><strong>{euros(s["total"])}</strong><span>Cette semaine</span></div>'
                f'<div><strong>{euros(moyenne) if moyenne is not None else "—"}</strong><span>Moyenne des 4 précédentes</span></div>'
                f'<div><strong>{euros(s["economie"])}</strong><span>Économisés vs tout livrer</span></div>')
    lignes = "".join(_ligne(x) for x in semaines)
    return f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Budget · Casa Binomerie</title>
{TETE_PWA}
{TETE_POLICE}
<style>{HTML_STYLE}{STYLE_D}{STYLE_NAV_HUB}{STYLE_BUDGET}</style>
</head>
<body class="accueil hub-page">
<h1>Budget</h1>
<div class="chiffres">{chiffres}</div>
<p class="note-budget">Estimations : courses au prix d'un panier parisien, livraison {euros(LIVRAISON_DEUX)} et resto {euros(FORFAIT_RESTO)} pour deux.</p>
{graphique_svg(semaines)}
<p class="legende"><span class="l-courses">Courses</span><span class="l-livraison">Livraison et resto</span></p>
<div class="tableau"><table class="budget">
<tr><th>Semaine du</th><th>Courses</th><th>Livraison, resto</th><th>Total</th><th>Repas maison</th></tr>
{lignes}
</table></div>
{nav_hub("budget")}
</body>
</html>"""
