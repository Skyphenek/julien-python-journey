"""Design « D — Vif et coloré » (choisi par Julien et Laetitia le 28/10/2026, maquettes :
https://claude.ai/artifact/J68ukfvsdgJh4WPhkgv7PP).

Une couche posée PAR-DESSUS les styles existants (chargée en dernier) : elle redéfinit les
couleurs et la mise en page sans toucher aux classes dont dépendent les scripts.

- Une couleur par rubrique (Valise bleu, Avant violet, Programme orange, Sur place vert,
  Souvenirs rose) : body[data-rubrique] la propage (--rubrique), l'en-tête prend sa teinte.
- Téléphone : barre d'onglets en bas. Ordinateur (≥ 900 px) : barre latérale à gauche,
  contenu large, Sur place et Programme sur deux colonnes.
"""

POLICE = "https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,400..800&display=swap"
TETE_POLICE = (f'<link rel="preconnect" href="https://fonts.googleapis.com">'
               f'<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
               f'<link rel="stylesheet" href="{POLICE.replace("&", "&amp;")}">')

_TRAIT = ('<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" '
          'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{}</svg>')
ICONES_RUBRIQUE = {
    "valise": _TRAIT.format('<rect x="3" y="7" width="18" height="13" rx="2"/>'
                            '<path d="M8 7V5a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>'),
    "avant": _TRAIT.format('<rect x="5" y="3" width="14" height="18" rx="2"/><path d="m9 12 2 2 4-4"/>'),
    "programme": _TRAIT.format('<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 3v4M16 3v4"/>'),
    "sur-place": _TRAIT.format('<path d="M12 21s-7-6.2-7-11a7 7 0 0 1 14 0c0 4.8-7 11-7 11z"/>'
                               '<circle cx="12" cy="10" r="2.5"/>'),
    "souvenirs": _TRAIT.format('<rect x="3" y="8" width="18" height="13" rx="1"/>'
                               '<path d="M3 12h18M12 8v13M12 8c-2-3-6-3-6 0h6zM12 8c2-3 6-3 6 0h-6z"/>'),
}

# Le hub Casa Binomerie : une entrée par module livré (clé, libellé, adresse relative), dans l'ordre.
# Dîners, Courses et Colis s'ajoutent ici à leur livraison : jamais de lien vers une page absente.
HUB = [
    ("aujourdhui", "Aujourd'hui", "./"),
    ("vadrouille", "En Vadrouille", "vadrouille"),
]
ICONES_HUB = {
    "aujourdhui": _TRAIT.format('<path d="M3 11 12 4l9 7"/><path d="M5 10v10h14V10"/><path d="M10 20v-5h4v5"/>'),
    "vadrouille": ICONES_RUBRIQUE["valise"],
}


def nav_hub(actif):
    """La navigation du hub (en bas sur téléphone, à gauche sur ordinateur), l'entrée actif en surbrillance."""
    liens = "".join(
        f'<a href="{adresse}" data-hub="{cle}"'
        + (' class="actif" aria-current="page">' if cle == actif else ">")
        + f'<span class="icone-hub">{ICONES_HUB[cle]}</span><span>{libelle}</span></a>'
        for cle, libelle, adresse in HUB)
    return f'<nav class="hub">{liens}</nav>'


STYLE_NAV_HUB = """
nav.hub { position: fixed; left: 0; right: 0; bottom: 0; z-index: 20; display: flex; justify-content: center;
          gap: 4px; padding: 8px 8px calc(8px + env(safe-area-inset-bottom)); background: var(--fond);
          border-top: 1px solid var(--ligne); }
nav.hub a { flex: 0 1 120px; display: flex; flex-direction: column; align-items: center; gap: 3px;
            font-size: 12px; font-weight: 600; color: var(--doux); text-decoration: none; }
nav.hub a .icone-hub { display: flex; padding: 6px 14px; border-radius: 16px; color: var(--c); }
nav.hub a.actif { color: var(--texte); font-weight: 800; }
nav.hub a.actif .icone-hub { background: var(--c-doux); }
nav.hub a[data-hub="aujourdhui"] { --c: var(--texte); --c-doux: var(--carte); }
nav.hub a[data-hub="vadrouille"] { --c: var(--valise); --c-doux: var(--valise-doux); }
body.hub-page { display: block; max-width: 720px; margin: 0 auto; padding: 28px 20px 110px; }   /* place pour la barre */
@media (min-width: 900px) {
    nav.hub { top: 0; right: auto; width: 232px; flex-direction: column; justify-content: flex-start;
              padding: 28px 14px; border-top: none; border-right: 1px solid var(--ligne); }
    nav.hub a { flex: 0 0 auto; flex-direction: row; gap: 10px; font-size: 16px; padding: 6px;
                border-radius: 18px; min-height: 48px; }
    nav.hub a.actif { background: var(--c-doux); }
    body.hub-page { margin-left: max(252px, calc(50% - 360px)); padding-bottom: 40px; }   /* à droite de la barre */
}
"""

STYLE_D = """
:root {
    --fond: #ffffff; --carte: #f4f4f8; --texte: #14142b; --doux: #5c5c74; --ligne: #e6e6ee; --blanc: #ffffff;
    --valise: #3355ff; --valise-doux: #e8ecff;
    --avant: #7b3fe4; --avant-doux: #f1eaff;
    --programme: #d9481f; --programme-doux: #ffece5;
    --sur-place: #0f8a5c; --sur-place-doux: #e3f7ee;
    --souvenirs: #d63384; --souvenirs-doux: #fde8f2;
    --rubrique: var(--valise); --rubrique-doux: var(--valise-doux);
    --accent: var(--rubrique); --accent-doux: var(--rubrique-doux); --ok: var(--rubrique);
}
@media (prefers-color-scheme: dark) {
    :root {
        --fond: #12121c; --carte: #1e1e2c; --texte: #f2f2f7; --doux: #a3a3b8; --ligne: #2e2e40; --blanc: #26263a;
        --valise: #8097ff; --valise-doux: #1f2856;
        --avant: #b48dff; --avant-doux: #2c1f4a;
        --programme: #ff8a63; --programme-doux: #3f2218;
        --sur-place: #3cc68f; --sur-place-doux: #12382b;
        --souvenirs: #f27ab3; --souvenirs-doux: #40172b;
    }
}
body[data-rubrique="avant"] { --rubrique: var(--avant); --rubrique-doux: var(--avant-doux); }
body[data-rubrique="programme"] { --rubrique: var(--programme); --rubrique-doux: var(--programme-doux); }
body[data-rubrique="sur-place"] { --rubrique: var(--sur-place); --rubrique-doux: var(--sur-place-doux); }
body[data-rubrique="souvenirs"] { --rubrique: var(--souvenirs); --rubrique-doux: var(--souvenirs-doux); }

body { font-family: 'Bricolage Grotesque', system-ui, -apple-system, sans-serif; background: var(--fond);
       color: var(--texte); max-width: none; margin: 0; padding: 0 0 calc(96px + env(safe-area-inset-bottom)); }
h1, h2, h3, h4 { letter-spacing: -0.02em; }

/* En-tête du voyage : teinte de la rubrique ouverte */
header.entete { background: var(--rubrique-doux); border-radius: 0 0 32px 32px; padding: 16px 20px 20px;
                transition: background .25s; }
header.entete a.retour { display: inline-flex; align-items: center; min-height: 40px; padding: 0 14px; margin: 0 0 10px;
                         border-radius: 999px; background: var(--blanc); color: var(--texte); font-weight: 600; }
header.entete h1 { font-size: 30px; font-weight: 800; line-height: 1.05; margin: 0 0 6px; }
header.entete h1 .duree { display: block; font-size: 15px; font-weight: 500; color: var(--doux); letter-spacing: 0;
                          margin-top: 6px; }
header.entete p.compte { color: var(--rubrique); font-size: 17px; font-weight: 800; margin: 4px 0 10px; }
span.puce { background: var(--blanc); border: none; color: var(--texte); font-size: 13px; }
main { padding: 16px 20px 0; }
#bandeau-meteo { background: var(--carte); border-radius: 20px; }

/* Onglets des rubriques : en bas sur téléphone */
nav.rubriques { position: fixed; left: 0; right: 0; bottom: 0; z-index: 20; margin: 0; display: flex;
                justify-content: space-around; gap: 0; background: var(--fond); border-top: 1px solid var(--ligne);
                border-bottom: none; padding: 8px 4px calc(10px + env(safe-area-inset-bottom)); }
nav.rubriques button { flex: 1; display: flex; flex-direction: column; align-items: center; gap: 3px;
                       padding: 0; border: none; background: none; color: var(--doux); font: inherit;
                       font-size: 11px; font-weight: 600; min-height: 52px; }
nav.rubriques button .icone-rubrique { display: flex; padding: 6px 14px; border-radius: 16px; color: var(--c); }
nav.rubriques button.actif { color: var(--texte); font-weight: 800; }
nav.rubriques button.actif .icone-rubrique { background: var(--c-doux); }
nav.rubriques button .compte-rubrique { display: none; }
nav.rubriques button[data-rubrique="valise"] { --c: var(--valise); --c-doux: var(--valise-doux); }
nav.rubriques button[data-rubrique="avant"] { --c: var(--avant); --c-doux: var(--avant-doux); }
nav.rubriques button[data-rubrique="programme"] { --c: var(--programme); --c-doux: var(--programme-doux); }
nav.rubriques button[data-rubrique="sur-place"] { --c: var(--sur-place); --c-doux: var(--sur-place-doux); }
nav.rubriques button[data-rubrique="souvenirs"] { --c: var(--souvenirs); --c-doux: var(--souvenirs-doux); }

/* Valise */
div.collant { background: var(--fond); }
div.progress-track { height: 8px; background: var(--carte); }
div.progress-fill, div.barre[data-owner=""] div.progress-fill { background: var(--rubrique); }
nav.tabs { background: var(--carte); border-radius: 999px; padding: 4px; gap: 4px; }
nav.tabs button { border-radius: 999px; background: transparent; color: var(--texte); font: inherit; font-weight: 600;
                  min-height: 40px; }
nav.tabs button.actif { background: var(--rubrique); color: #ffffff; font-weight: 800; }
details.rayon { background: var(--carte); border-radius: 22px; box-shadow: none; }
details.rayon > summary { font-size: 18px; font-weight: 800; }
li label { min-height: 50px; border-radius: 16px; }
li input { width: 26px; height: 26px; border-color: #c9c9d6; background: var(--blanc); }
li input:checked { background: var(--rubrique); border-color: var(--rubrique); }
li .qte { background: var(--blanc); color: var(--texte); font-weight: 800; }
li label:active { background: var(--rubrique-doux); }
div.manques { background: var(--carte); border-radius: 22px; }

/* Blocs d'information (Avant, Programme, Sur place, Souvenirs) */
div.info { background: var(--carte); border-radius: 24px; padding: 18px; margin: 0 0 14px; box-shadow: none; }
div.info h3 { font-size: 21px; font-weight: 800; margin: 0 0 10px; }
div.info p.conseil { font-size: 14px; }
div.depenses .solde { font-size: 22px; font-weight: 800; }
div.urgences li a { color: var(--rubrique); }

/* Boutons et champs */
button.ctrl-btn, a.ctrl-btn { border: 2px solid var(--ligne); color: var(--texte); background: var(--blanc);
                              font-family: inherit; font-weight: 700; min-height: 40px; }
input, select, textarea { font-family: inherit; }
div.controls { padding: 0 20px 20px; justify-content: flex-start; }
form.ajout-manque button, button.principal { background: var(--rubrique); border-radius: 999px; font-family: inherit;
                                             font-weight: 800; }

/* Ordinateur : barre latérale, contenu large, deux colonnes là où c'est utile */
@media (min-width: 900px) {
    body { display: grid; grid-template-columns: 232px minmax(0, 1fr); grid-template-rows: auto 1fr;
           grid-template-areas: "nav entete" "nav main";
           align-items: start; padding: 0 0 40px; }
    nav.rubriques { grid-area: nav; position: sticky; top: 0; height: 100vh; flex-direction: column;
                    justify-content: flex-start; gap: 4px; padding: 28px 14px; border-top: none;
                    border-right: 1px solid var(--ligne); }
    nav.rubriques button { flex: 0 0 auto; flex-direction: row; justify-content: flex-start; gap: 10px; font-size: 16px;
                           padding: 6px; border-radius: 18px; min-height: 48px; }
    nav.rubriques button.actif { background: var(--c-doux); }
    nav.rubriques button .compte-rubrique { display: inline; margin-left: auto; padding-right: 8px; }
    header.entete { grid-area: entete; margin: 20px 28px 0; border-radius: 32px; padding: 24px 28px; }
    header.entete h1 { font-size: 40px; }
    main { grid-area: main; padding: 24px 28px 0; max-width: 1180px; }
    div.controls { padding: 0; }
    section[data-owner]:not([hidden]) { column-count: 2; column-gap: 16px; }
    details.rayon, div.manques { break-inside: avoid; }
    div.rubrique[data-rubrique="programme"]:not([hidden]) {
        display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px; align-items: start; }
    div.rubrique[data-rubrique="programme"] > * { margin: 0; }
    div.rubrique[data-rubrique="sur-place"]:not([hidden]) { column-count: 2; column-gap: 16px; }   /* blocs en colonnes, sans trous */
    div.rubrique[data-rubrique="sur-place"] div.info { break-inside: avoid; }
}

/* Accueil et formulaire */
body.accueil, body.formulaire { display: block; max-width: 720px; margin: 0 auto; padding: 28px 20px 40px; }
body.accueil h1 { font-size: 40px; font-weight: 800; line-height: 1; margin: 0 0 18px; }
body.formulaire h1 { font-size: 34px; font-weight: 800; }
a.nouvelle { display: flex; align-items: center; justify-content: center; min-height: 56px; border-radius: 999px;
             background: var(--texte); color: var(--fond); font-weight: 800; font-size: 17px; }
div.prochain { background: var(--valise); border-radius: 32px; padding: 22px; margin: 16px 0; box-shadow: none; }
div.prochain a { color: #ffffff; }
div.prochain .titre { color: #e3e8ff; font-size: 15px; }
div.prochain .compte { color: #ffffff; font-size: 30px; font-weight: 800; letter-spacing: -0.02em; }
a.voyage { background: var(--carte); border-radius: 24px; padding: 16px 18px; box-shadow: none; }
a.voyage strong { font-size: 19px; font-weight: 800; }
a.voyage span.compte { color: var(--valise); }
section.liste h2 { font-size: 20px; font-weight: 800; color: var(--texte); }
#carte { border-radius: 24px; }
div.bloc { background: var(--carte); border-radius: 22px; box-shadow: none; }

/* Urgences : une pastille par numéro (maquette D) */
div.urgences h4 { font-size: 16px; font-weight: 800; margin: 14px 0 8px; }
div.urgences h4 .source { color: var(--doux); font-weight: 600; }
div.pastilles-urgence { display: grid; grid-template-columns: repeat(auto-fill, minmax(96px, 1fr)); gap: 8px; }
a.pastille-urgence { display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 2px;
                     min-height: 76px; padding: 8px; border-radius: 22px; background: #ffe3e3; color: #a3150d;
                     text-decoration: none; text-align: center; line-height: 1.15; }
a.pastille-urgence strong { font-size: 24px; font-weight: 800; letter-spacing: -0.01em; }
a.pastille-urgence span { font-size: 12px; font-weight: 600; }
.appel-ambassade { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin: 8px 0 0;
                   padding: 12px 16px; border-radius: 18px; background: var(--blanc); color: var(--texte);
                   text-decoration: none; }
.appel-ambassade span { display: flex; flex-direction: column; font-size: 13px; color: var(--doux); }
.appel-ambassade strong { font-size: 15px; color: var(--texte); }
.appel-ambassade em { font-style: normal; font-weight: 800; color: var(--rubrique); white-space: nowrap; font-size: 14px; }
@media (prefers-color-scheme: dark) {
    a.pastille-urgence { background: #47191b; color: #ffb4ab; }
}

/* Avant de partir : une carte par tâche, l'échéance en pastille (maquette D) */
details.rayon.avant { background: transparent; }
details.rayon.avant > summary { padding: 4px 2px 10px; min-height: 0; font-size: 21px; }
details.rayon.avant ul { padding: 0; gap: 8px; }
li.tache label { background: var(--carte); border-radius: 20px; padding: 14px 16px; align-items: center; min-height: 64px; }
li.tache .nom { font-size: 16px; font-weight: 600; line-height: 1.3; }
li.tache .echeance { background: var(--blanc); border-radius: 10px; padding: 4px 8px; font-size: 12px; font-weight: 800; }
li.tache a.source { padding: 4px 0 4px 18px; font-weight: 700; color: var(--rubrique); }
li.retard:not(:has(input:checked)) .echeance { background: #ffe3e3; color: #a3150d; }
li.tache:has(input:checked) label { opacity: .7; }
li.tache .avant-le { display: none; }                 /* la pastille dit juste « 16/11 » */

/* Formulaire « On part où ? » : pastilles au lieu de cases et boutons radio (maquette D) */
body.formulaire h1 { font-size: 38px; line-height: 1; margin: 6px 0 18px; }
body.formulaire a.retour { display: inline-flex; align-items: center; min-height: 40px; padding: 0 14px; border-radius: 999px;
                           background: var(--carte); color: var(--texte); font-weight: 600; text-decoration: none; }
div.bloc { padding: 18px; margin-bottom: 12px; }
form input[type=text], form input[type=date], form input[type=number] { border: 2px solid var(--ligne); border-radius: 16px;
    background: var(--blanc); min-height: 48px; padding: 0 14px; font-family: inherit; font-size: 17px; }
form input:focus { outline: none; border-color: var(--valise); }
legend, form label { font-weight: 700; }
fieldset { display: flex; flex-wrap: wrap; gap: 8px; }
fieldset legend { flex-basis: 100%; margin-bottom: 8px; }
fieldset label, .activites label, div.options > label:not(#bloc-lessive) {
    position: relative; display: inline-flex; align-items: center; min-height: 44px; margin: 0; padding: 0 16px;
    border: 2px solid var(--ligne); border-radius: 999px; background: var(--blanc); font-weight: 600; cursor: pointer; }
fieldset label input, .activites label input, div.options > label:not(#bloc-lessive) input {
    position: absolute; opacity: 0; pointer-events: none; }          /* la pastille entière fait la case */
fieldset label:has(input:checked) { background: var(--texte); border-color: var(--texte); color: var(--fond); }
.activites label:has(input:checked), div.options > label:has(input:checked) {
    background: var(--valise-doux); border-color: var(--valise); color: var(--texte); }
label:has(input:focus-visible) { outline: 3px solid var(--valise); outline-offset: 2px; }
.activites { gap: 8px; margin-top: 10px; }
div.options { display: flex; flex-wrap: wrap; gap: 8px; }
div.options #bloc-lessive { flex-basis: 100%; font-weight: 600; }
div.etape.bloc { border-radius: 24px; }
div.etape.bloc:nth-child(3n+1) { background: var(--valise-doux); }
div.etape.bloc:nth-child(3n+2) { background: var(--avant-doux); }
div.etape.bloc:nth-child(3n) { background: var(--sur-place-doux); }
div.etape .numero { font-size: 20px; font-weight: 800; }
div.etape .chercher { min-height: 48px; }
button.ajouter-etape { width: 100%; min-height: 54px; border: 2px dashed #c9c9d6; border-radius: 22px; background: transparent;
                       color: var(--texte); font: inherit; font-size: 16px; font-weight: 800; cursor: pointer; }
body.formulaire button.principal { min-height: 58px; background: var(--valise); font-size: 17px; }
"""

STYLE_EPURE = """
/* Sur place épuré (maquette D) : tuiles heure / devise, convertisseur sur une ligne, carte Dépenses sombre */
div.tuiles { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; margin: 0 0 14px; break-inside: avoid; }
div.tuiles > div.info, div.tuiles ul { display: contents; }
div.tuiles h3 { position: absolute; width: 1px; height: 1px; overflow: hidden; clip-path: inset(50%); white-space: nowrap; }
div.tuiles li.tuile { display: flex; flex-direction: column; justify-content: center; min-height: 96px; padding: 14px 16px;
                      border-radius: 22px; background: var(--rubrique-doux); list-style: none; }
div.tuiles li.tuile .lieu { font-size: 13px; color: var(--doux); overflow-wrap: anywhere; }
div.tuiles li.tuile strong { font-size: 30px; font-weight: 800; letter-spacing: -0.02em; line-height: 1.1;
                             font-variant-numeric: tabular-nums; }
div.tuiles li.tuile .ecart { font-size: 13px; font-weight: 800; color: var(--rubrique); }
div.tuiles li.tuile .ecart em { font-style: normal; font-weight: 600; color: var(--doux); }
div.tuiles .horloge { display: block; color: var(--texte); }
div.tuiles p.conseil, div.tuiles div.convertisseur { grid-column: 1 / -1; order: 1; margin: 0; }
div.tuiles p.conseil { font-size: 13px; color: var(--doux); padding: 0 4px; }
div.tuiles p.taux-date { order: 2; }
div.devises div.convertisseur { display: flex; align-items: center; gap: 10px; padding: 12px; border-radius: 22px;
                                background: var(--carte); font-size: 18px; }
div.devises div.convertisseur input { flex: 1; width: auto; min-width: 0; height: 52px; border: none; border-radius: 16px;
                                      padding: 0 14px; font: inherit; font-size: 18px; font-weight: 800;
                                      background: var(--blanc); color: var(--texte); }
div.devises div.convertisseur input.montant-eur { background: var(--rubrique); color: #ffffff; text-align: center; }
div.devises div.convertisseur input.montant-eur::placeholder { color: rgba(255, 255, 255, .8); }
div.devises div.convertisseur .egal { font-size: 20px; font-weight: 800; }

div.info.depenses { background: transparent; padding: 0; }
div.resume-depenses { background: #14142b; color: #ffffff; border-radius: 28px; padding: 20px; margin-bottom: 10px; }
div.resume-depenses .tete { display: flex; justify-content: space-between; align-items: center; }
div.resume-depenses h3 { font-size: 15px; font-weight: 600; color: #c9c9dc; margin: 0; letter-spacing: 0; }
div.resume-depenses .ajouter-depense { min-height: 40px; padding: 0 16px; border: none; border-radius: 999px;
                                       background: #ffffff; color: #14142b; font: inherit; font-size: 14px; font-weight: 800; cursor: pointer; }
div.resume-depenses .total { display: block; font-size: 40px; font-weight: 800; letter-spacing: -0.02em; margin: 6px 0 2px; }
div.depenses div.resume-depenses .solde { font-size: 15px; font-weight: 500; margin: 0; color: #ffffff; }
div.depenses form.nouvelle-depense { background: var(--carte); border-radius: 24px; padding: 14px; margin: 0 0 10px; gap: 8px; }
div.depenses form.nouvelle-depense[hidden] { display: none; }
div.depenses form input[type=text], div.depenses form input[type=number], div.depenses form select {
    min-height: 48px; border: 2px solid var(--ligne); border-radius: 16px; background: var(--blanc); padding: 0 12px;
    font: inherit; font-size: 16px; }
div.depenses form label { display: inline-flex; align-items: center; gap: 4px; }
div.depenses form button.principal { flex-basis: 100%; min-height: 50px; border: none; color: #ffffff; font-size: 16px; }
div.depenses p.message-depense:empty { display: none; }
div.depenses .liste-depenses { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 8px; }
div.depenses .liste-depenses li { display: flex; align-items: center; gap: 10px; min-height: 58px; padding: 6px 6px 6px 16px;
                                  border: none; border-radius: 18px; background: var(--carte); }
div.depenses .liste-depenses .quoi { flex: 1; display: flex; flex-direction: column; min-width: 0; }
div.depenses .liste-depenses .quoi strong { font-size: 16px; font-weight: 800; overflow-wrap: anywhere; }
div.depenses .liste-depenses .quoi small { font-size: 12px; color: var(--doux); }
div.depenses .liste-depenses .combien { font-size: 16px; font-weight: 800; white-space: nowrap; }
div.depenses .liste-depenses button.suppr { min-width: 36px; min-height: 36px; border: none; border-radius: 12px;
                                            background: transparent; color: var(--doux); font: inherit; cursor: pointer; }
div.depenses .liste-depenses button.suppr[data-confirmer] { background: #ffe3e3; color: #a3150d; font-size: 13px; font-weight: 700; }
@media (prefers-color-scheme: dark) {
    div.resume-depenses { background: #2a2a44; }
}

/* Cases rondes à la place des emojis (À voir : fait ; Souvenirs : acheté) */
div.a-voir li.envie .fait-btn, div.souvenirs li.souvenir .achat-btn {
    flex-shrink: 0; min-width: 28px; height: 28px; padding: 0 6px; border: 2px solid #c9c9d6; border-radius: 999px;
    background: var(--blanc); color: #ffffff; font: inherit; font-size: 15px; font-weight: 800; cursor: pointer; }
div.a-voir li.envie.faite .fait-btn, div.souvenirs li.souvenir.achete .achat-btn { background: var(--rubrique); border-color: var(--rubrique); }
div.souvenirs li.souvenir .achat-btn[data-confirmer] { color: var(--texte); background: var(--blanc); font-size: 12px; }

/* Programme : une pastille colorée par type de réservation */
div.programme .tete-resa { display: flex; align-items: center; gap: 10px; }
div.programme .tete-resa p { margin: 0; }
div.programme .tete-resa p.attente { font-size: 12px; color: var(--doux); }
span.icone-resa { flex-shrink: 0; width: 32px; height: 32px; border-radius: 10px; display: flex; align-items: center;
                  justify-content: center; color: #ffffff; background: var(--programme); }
span.icone-resa.type-vol { background: var(--valise); }
span.icone-resa.type-hotel { background: var(--sur-place); }
span.icone-resa.type-transport { background: var(--avant); }
span.icone-resa.type-activite { background: #e8890c; }
span.icone-resa.type-resto { background: var(--souvenirs); }

/* Vocabulaire : bouton haut-parleur */
div.vocabulaire button.ecouter { display: flex; align-items: center; justify-content: center; color: var(--rubrique); }
"""
STYLE_EPURE += """
div.tuiles li.tuile strong.taux { color: var(--texte); }
/* « pour » : pastilles au lieu de cases */
div.depenses form label:has(input[name=pour]) { position: relative; min-height: 40px; padding: 0 14px; border-radius: 999px;
    border: 2px solid var(--ligne); background: var(--blanc); font-weight: 700; cursor: pointer; }
div.depenses form label input[name=pour] { position: absolute; opacity: 0; pointer-events: none; }
div.depenses form label:has(input[name=pour]:checked) { background: var(--rubrique); border-color: var(--rubrique); color: #ffffff; }
"""
