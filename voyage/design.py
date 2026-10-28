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
"""
