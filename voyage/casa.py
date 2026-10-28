"""Casa Binomerie : le hub de la maison, dont En Vadrouille est une section.

Livraison 1 (squelette) : la page Aujourd'hui et la navigation. Dîners, Courses et Colis viendront
y ajouter chacun leur bloc (spec : docs/superpowers/specs/2026-10-28-hub-maison-design.md).
"""
from html import escape as echapper
from urllib.parse import quote

from compte_a_rebours import compte_en_html, STYLE_COMPTE, SCRIPT_COMPTE
from design import STYLE_D, STYLE_NAV_HUB, TETE_POLICE, nav_hub
from programme import etapes_du_voyage
from pwa import TETE_PWA
from valise import HTML_STYLE, MOIS

NOM = "Casa Binomerie"
HORIZON_VADROUILLE = 60        # jours : au-delà, le prochain voyage ne s'affiche pas sur Aujourd'hui
JOURS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]


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
p.attente { background: var(--carte); border-radius: 24px; padding: 18px; color: var(--doux); }
"""


def aujourdhui_en_html(voyages, aujourd_hui):
    """L'accueil du hub : ce qui compte aujourd'hui (pour l'instant : le prochain voyage)."""
    v = prochain_voyage(voyages, aujourd_hui)
    blocs = (bloc_vadrouille(v, aujourd_hui) if v else
             '<p class="attente">Rien de prévu pour l\'instant. Dîners, courses et colis arrivent ici bientôt.</p>')
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
</body>
</html>"""
