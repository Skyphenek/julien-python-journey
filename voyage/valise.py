"""Générateur de checklist de valise — adapté au type de destination, à la durée
et à la personne (Julien / Laetitia).

Application Python des concepts Exercism : dicts, listes, boucles, conditions.
On sépare les DONNÉES (les 3 tables ci-dessous, remplies une fois) de la LOGIQUE
(la fonction faire_valise). Démarrage minimal : on enrichit au fil des voyages.
"""
import json
import os
import re
import unicodedata
from datetime import date, timedelta
from pathlib import Path

import psycopg2
import requests

from api_climat import (lieux, normales_12_mois, fenetre_prevision, normales_depuis_previsions,
                        url_prevision, url_archive, extraire_lieux, normales_par_mois)
from db import (connecter, lire_normales, enregistrer_normales, publier_page,
                enregistrer_voyage, enregistrer_valise_objets, lire_voyage, lire_page,
                lire_valise_objets,
                lire_historique, lire_regles, ajouter_regle)
from dotenv import load_dotenv

# Feuille de style de la checklist HTML (mobile-first). Fournie clé en main :
# c'est de la présentation, pas de la logique. Injectée telle quelle dans le <head>.
HTML_STYLE = """
:root {
    color-scheme: light dark;
    --fond: #f4f4f5; --carte: #ffffff; --texte: #18181b; --doux: #71717a; --ligne: #e4e4e7;
    --accent: #4f46e5; --accent-doux: #eef2ff; --ok: #16a34a;
}
@media (prefers-color-scheme: dark) {
    :root {
        --fond: #18181b; --carte: #27272a; --texte: #f4f4f5; --doux: #a1a1aa; --ligne: #3f3f46;
        --accent: #818cf8; --accent-doux: #312e81; --ok: #22c55e;
    }
}
* { box-sizing: border-box; }
body {
    font-family: -apple-system, system-ui, sans-serif;
    max-width: 640px; margin: 0 auto; padding: 1rem 1rem 3rem;
    line-height: 1.45; background: var(--fond); color: var(--texte);
}
h1 { font-size: 1.25rem; margin: 0 0 .6rem; line-height: 1.3; }
a.retour { display: inline-block; margin: 0 0 .5rem; font-size: .85rem; color: var(--accent); text-decoration: none; }
h1 .duree { color: var(--doux); font-weight: 500; }

/* En-tête compact : climat et adaptateur en puces */
div.puces { display: flex; flex-wrap: wrap; gap: .4rem; margin: 0 0 .5rem; }
span.puce {
    max-width: 100%; overflow-wrap: anywhere;      /* une puce ne doit jamais élargir la page */
    font-size: .8rem; padding: .3rem .7rem; border-radius: 999px;
    background: var(--carte); border: 1px solid var(--ligne); color: var(--doux);
}

/* Barre collante : progression + onglets restent visibles en faisant défiler */
div.collant { position: sticky; top: 0; z-index: 5; background: var(--fond); padding: .6rem 0 .7rem; }
div.barres { display: grid; grid-template-columns: repeat(auto-fit, minmax(90px, 1fr)); gap: .75rem; }
div.progress-head {
    display: flex; justify-content: space-between; font-size: .8rem;
    color: var(--doux); margin-bottom: .3rem; font-weight: 600;
}
div.progress-track { height: 6px; border-radius: 999px; background: var(--ligne); overflow: hidden; }
div.progress-fill { height: 100%; width: 0; background: var(--ok); border-radius: 999px; transition: width .3s ease; }
div.barre[data-owner=""] div.progress-fill { background: var(--accent); }   /* le total se distingue */
nav.tabs { display: flex; gap: .4rem; margin-top: .6rem; }
nav.tabs button {
    flex: 1; padding: .55rem .4rem; border: none; border-radius: 10px;
    background: var(--ligne); color: var(--doux); font-size: .9rem; font-weight: 600; cursor: pointer;
}
nav.tabs button.actif { background: var(--accent); color: #fff; }
nav.tabs .tab-count { font-size: .72rem; opacity: .75; }

/* Rayons repliables (élément <details> natif : replier ne demande aucun JavaScript) */
details.rayon {
    background: var(--carte); border-radius: 14px; margin-bottom: .6rem;
    box-shadow: 0 1px 2px rgba(0,0,0,.06); overflow: hidden;
}
details.rayon > summary {
    list-style: none; display: flex; align-items: center; gap: .6rem;
    padding: .75rem 1rem; min-height: 52px; cursor: pointer; font-weight: 600;
}
details.rayon > summary::-webkit-details-marker { display: none; }
summary .icone { font-size: 1.2rem; }
summary .nom { flex: 1; }
summary .compte { font-size: .8rem; color: var(--doux); font-variant-numeric: tabular-nums; }
summary::after { content: "▾"; color: var(--doux); }
details:not([open]) > summary::after { content: "▸"; }
details.fini > summary .compte { color: var(--ok); }
details.fini > summary .compte::before { content: "✓ "; }
details.fini > summary .nom { color: var(--doux); }

/* Objets : les rangés glissent en bas de leur rayon (CSS "order", sans toucher au HTML) */
ul { list-style: none; margin: 0; padding: 0 .5rem .5rem; display: flex; flex-direction: column; }
li:has(input:checked) { order: 1; }
li label {
    display: flex; align-items: center; gap: .75rem;
    padding: .5rem .5rem; min-height: 46px; border-radius: 10px; cursor: pointer;
}
li label:active { background: var(--accent-doux); }
li input {
    appearance: none; -webkit-appearance: none; margin: 0; flex-shrink: 0;
    width: 24px; height: 24px; border: 2px solid var(--ligne); border-radius: 50%;
    display: grid; place-content: center; transition: background .15s, border-color .15s;
}
li input::after { content: "✓"; color: #fff; font-size: .8rem; font-weight: 700; transform: scale(0); transition: transform .15s; }
li input:checked { background: var(--ok); border-color: var(--ok); }
li input:checked::after { transform: scale(1); }
li .nom { flex: 1; }
li .qte {
    font-size: .8rem; font-weight: 600; padding: .15rem .55rem; border-radius: 999px;
    background: var(--accent-doux); color: var(--accent); font-variant-numeric: tabular-nums;
}
label:has(input:checked) .nom { color: var(--doux); text-decoration: line-through; }
label:has(input:checked) .qte { background: var(--ligne); color: var(--doux); }

div.controls { display: flex; flex-wrap: wrap; gap: .5rem; justify-content: flex-end; margin: 1rem 0 0; }
button.ctrl-btn {
    padding: .4rem .85rem; border: 1px solid var(--ligne); border-radius: 999px;
    background: transparent; color: var(--doux); font-size: .82rem; font-weight: 600; cursor: pointer;
}
/* ---- Mode Bilan de fin de voyage ---- */
body:not(.mode-bilan) .bilan, body:not(.mode-bilan) div.manques, body:not(.mode-bilan) #bilan-compte { display: none; }
body.mode-bilan li label { pointer-events: none; }             /* un tap ne décoche rien par accident */
body.mode-bilan li label input { display: none; }
body.mode-bilan li:has(input:checked) { order: 0; }
body.mode-bilan label:has(input:checked) .nom { text-decoration: none; color: var(--texte); }
body.mode-bilan label:has(input:checked) .qte { background: var(--accent-doux); color: var(--accent); }
#bilan-compte { font-size: .8rem; color: var(--doux); margin: .5rem 0 0; font-weight: 600; }
.bilan { display: flex; flex-wrap: wrap; align-items: center; gap: .35rem; padding: 0 .5rem .6rem; }
.bilan button {
    font-size: .78rem; font-weight: 600; padding: .35rem .65rem; border-radius: 999px; cursor: pointer;
    border: 1px solid var(--ligne); background: transparent; color: var(--doux);
}
li[data-verdict="utile"] .bilan button[data-verdict="utile"] { background: var(--ok); border-color: var(--ok); color: #fff; }
li[data-verdict="trop"] .bilan button[data-verdict="trop"] { background: #d97706; border-color: #d97706; color: #fff; }
li[data-verdict="pas_servi"] .bilan button[data-verdict="pas_servi"] { background: #dc2626; border-color: #dc2626; color: #fff; }
.bilan .utilise { display: none; align-items: center; gap: .3rem; font-size: .8rem; color: var(--doux); }
li[data-verdict="trop"][data-qte-multi] .bilan .utilise { display: inline-flex; }
.bilan .utilise input {
    width: 3.5rem; padding: .25rem .35rem; font-size: 1rem;     /* 16 px : évite le zoom auto d'iOS */
    border: 1px solid var(--ligne); border-radius: 8px; background: var(--fond); color: var(--texte);
}
div.manques { background: var(--carte); border-radius: 14px; padding: .8rem 1rem; margin-bottom: .6rem; }
div.manques h3 { font-size: .95rem; margin: 0 0 .5rem; }
.puces-manque { display: flex; flex-wrap: wrap; gap: .4rem; margin-bottom: .5rem; }
.puces-manque button { border: none; background: none; color: var(--doux); cursor: pointer; font-size: 1rem; padding: 0 0 0 .25rem; }
form.ajout-manque { display: flex; gap: .5rem; }
form.ajout-manque input {
    flex: 1; min-width: 0; padding: .5rem .7rem; font-size: 1rem;
    border: 1px solid var(--ligne); border-radius: 10px; background: var(--fond); color: var(--texte);
}
form.ajout-manque button {
    padding: .5rem .9rem; border: none; border-radius: 10px; background: var(--accent); color: #fff;
    font-weight: 600; cursor: pointer;
}
"""

# Script JS de la page (persistance des coches). Dans une constante à part car le JS
# est plein d'accolades : il ne doit PAS traverser la f-string qui construit la page.
HTML_SCRIPT = """
// Références aux éléments de la page (tout en haut : dispo avant tout appel)
let sauvegarde = {};                                    // rempli après la réponse du serveur
const sections = document.querySelectorAll('section[data-owner]');
const onglets = document.querySelectorAll('nav.tabs button');
const btnMasque = document.getElementById('toggle-masque');
const btnReset = document.getElementById('reset');
let ownerActif = null;                                  // la personne actuellement affichée
let masquer = false;                                    // masquer les objets déjà rangés ?

// Une barre par personne (+ le total) : data-owner="" = toutes les cases de la page
function majProgression() {
    document.querySelectorAll('div.barre').forEach(function (barre) {
        const owner = barre.dataset.owner;
        const selecteur = owner ? 'section[data-owner="' + owner + '"] input[type=checkbox]'
                                : 'section[data-owner] input[type=checkbox]';
        const boxes = document.querySelectorAll(selecteur);
        let faites = 0;
        boxes.forEach(function (b) { if (b.checked) faites++; });
        barre.querySelector('.barre-compte').textContent = faites + ' / ' + boxes.length;
        barre.querySelector('.progress-fill').style.width = boxes.length ? (faites / boxes.length * 100) + '%' : '0%';
    });
}

// Compteur affiché sur chaque onglet (cochées / total de la personne)
function majOnglets() {
    onglets.forEach(function (b) {
        const boxes = document.querySelectorAll('section[data-owner="' + b.dataset.owner + '"] input[type=checkbox]');
        let faites = 0;
        boxes.forEach(function (x) { if (x.checked) faites++; });
        const span = b.querySelector('.tab-count');
        if (span) span.textContent = faites + '/' + boxes.length;
    });
}

// Masquer / réafficher les objets déjà cochés (+ les rayons devenus vides)
function appliquerMasque() {
    document.querySelectorAll('li').forEach(function (li) {
        const box = li.querySelector('input[type=checkbox]');
        if (box) li.style.display = (masquer && box.checked) ? 'none' : '';
    });
    document.querySelectorAll('details.rayon').forEach(function (d) {
        const visible = Array.from(d.querySelectorAll('li')).some(function (li) { return li.style.display !== 'none'; });
        d.style.display = visible ? '' : 'none';     // rayon entièrement rangé + masque -> rayon caché
    });
}

// Compteur de chaque rayon (3/8) + marque "fini" quand tout est rangé
function majRayons() {
    document.querySelectorAll('details.rayon').forEach(function (d) {
        const boxes = d.querySelectorAll('input[type=checkbox]');
        let faites = 0;
        boxes.forEach(function (b) { if (b.checked) faites++; });
        d.querySelector('.compte').textContent = faites + '/' + boxes.length;
        d.classList.toggle('fini', faites === boxes.length);
    });
}

// Onglets : n'afficher qu'une personne à la fois
function activer(nom) {
    ownerActif = nom;
    sections.forEach(function (s) { s.style.display = (s.dataset.owner === nom) ? '' : 'none'; });
    onglets.forEach(function (b) { b.classList.toggle('actif', b.dataset.owner === nom); });
    appliquerMasque();
}

// Sauvegarde d'une seule case sur le serveur (jamais tout l'état -> pas d'écrasement croisé)
const derniereModif = {};                              // clé -> instant du dernier clic sur CET appareil
function sauverCoche(cle, coche) {
    derniereModif[cle] = Date.now();
    fetch('api/coche', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cle: cle, coche: coche })
    });
}

// Rafraîchissement automatique : relire l'état du serveur pour voir les cases cochées
// sur l'AUTRE téléphone. On ignore une case cliquée ici il y a moins de 5 s : sa
// sauvegarde peut ne pas être encore arrivée, on ne veut pas la "décocher" à l'écran.
function rafraichir() {
    if (document.hidden) return;                       // onglet en arrière-plan : on ne fait rien
    fetch('api/etat/' + encodeURIComponent(VOYAGE))
        .then(function (r) { return r.json(); })
        .then(function (data) {
            let change = false;
            document.querySelectorAll('input[type=checkbox]').forEach(function (box) {
                const cle = box.dataset.key;
                if (Date.now() - (derniereModif[cle] || 0) < 5000) return;
                const coche = !!data[cle];
                if (box.checked !== coche) { box.checked = coche; change = true; }
            });
            sauvegarde = data;
            if (change) { majProgression(); majOnglets(); majRayons(); appliquerMasque(); }
        })
        .catch(function () {});                        // serveur injoignable un instant : on réessaiera
}

// ---- Mode Bilan de fin de voyage ----------------------------------------------------
// retours : "proprietaire/objet" -> {verdict, quantite_utilisee} ; manques : proprietaire -> [objets]
let retours = {};
let manques = {};
let dernierRetourLocal = 0;                            // dernier clic de bilan sur CET appareil
const btnBilan = document.getElementById('mode-bilan');
const compteBilan = document.getElementById('bilan-compte');

function cleRetour(owner, objet) { return owner + '/' + objet; }

function envoyerRetour(owner, objet, verdict, quantite) {
    dernierRetourLocal = Date.now();
    fetch('api/retour', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ voyage: VOYAGE, proprietaire: owner, objet: objet,
                               verdict: verdict, quantite_utilisee: quantite })
    });
}

function chargerRetours(liste) {
    retours = {};
    manques = {};
    liste.forEach(function (r) {
        if (r.verdict === 'manque') {
            (manques[r.proprietaire] = manques[r.proprietaire] || []).push(r.objet);
        } else {
            retours[cleRetour(r.proprietaire, r.objet)] = r;
        }
    });
    afficherRetours();
}

function afficherRetours() {
    let evalues = 0;
    const objets = document.querySelectorAll('li[data-objet]');
    objets.forEach(function (li) {
        const r = retours[cleRetour(li.dataset.owner, li.dataset.objet)];
        if (r) { li.dataset.verdict = r.verdict; evalues++; } else { delete li.dataset.verdict; }
        const champ = li.querySelector('.utilise input');
        if (champ && document.activeElement !== champ) {   // ne pas écraser une saisie en cours
            champ.value = (r && r.quantite_utilisee !== null && r.quantite_utilisee !== undefined) ? r.quantite_utilisee : '';
        }
    });
    compteBilan.textContent = 'Bilan : ' + evalues + ' / ' + objets.length + ' objets évalués';
    document.querySelectorAll('div.manques').forEach(function (bloc) {
        const zone = bloc.querySelector('.puces-manque');
        zone.textContent = '';
        (manques[bloc.dataset.owner] || []).forEach(function (objet) {
            const puce = document.createElement('span');
            puce.className = 'puce';
            puce.textContent = objet;                    // textContent : le texte tapé n'est jamais interprété comme du HTML
            const retirer = document.createElement('button');
            retirer.type = 'button';
            retirer.textContent = '×';
            retirer.setAttribute('aria-label', 'Retirer ' + objet);
            retirer.addEventListener('click', function () {
                manques[bloc.dataset.owner] = manques[bloc.dataset.owner].filter(function (o) { return o !== objet; });
                envoyerRetour(bloc.dataset.owner, objet, null, null);
                afficherRetours();
            });
            puce.appendChild(retirer);
            zone.appendChild(puce);
        });
    });
}

// Relire les retours du serveur. Une réponse est ignorée si un clic a eu lieu ici après le
// départ de la requête (elle ne le connaît pas encore) ou il y a moins de 5 s (sauvegarde en route).
function lireRetoursServeur() {
    const depart = Date.now();
    fetch('api/retours/' + encodeURIComponent(VOYAGE))
        .then(function (r) { return r.json(); })
        .then(function (liste) {
            if (dernierRetourLocal >= depart || Date.now() - dernierRetourLocal < 5000) return;
            chargerRetours(liste);
        })
        .catch(function () {});
}

function rafraichirRetours() {
    if (document.hidden || !document.body.classList.contains('mode-bilan')) return;
    lireRetoursServeur();
}

function activerBilan(actif) {
    document.body.classList.toggle('mode-bilan', actif);
    btnBilan.textContent = actif ? '✓ Terminer le bilan' : '📝 Bilan de fin de voyage';
    if (actif) {
        masquer = false;                                  // en bilan, on veut voir tous les objets
        btnMasque.textContent = 'Masquer les rangés';
        document.querySelectorAll('details.rayon').forEach(function (d) { d.open = true; });
        appliquerMasque();
        rafraichirRetours();
    }
    try { localStorage.setItem('valise-bilan:' + VOYAGE, actif ? '1' : ''); } catch (e) {}
}

function initialiserBilan() {
    btnBilan.addEventListener('click', function () {
        activerBilan(!document.body.classList.contains('mode-bilan'));
    });
    document.querySelectorAll('.bilan button[data-verdict]').forEach(function (b) {
        b.addEventListener('click', function () {
            const li = b.closest('li');
            const cle = cleRetour(li.dataset.owner, li.dataset.objet);
            if (retours[cle] && retours[cle].verdict === b.dataset.verdict) {   // re-toucher = annuler
                delete retours[cle];
                envoyerRetour(li.dataset.owner, li.dataset.objet, null, null);
            } else {
                retours[cle] = { verdict: b.dataset.verdict, quantite_utilisee: null };
                envoyerRetour(li.dataset.owner, li.dataset.objet, b.dataset.verdict, null);
            }
            afficherRetours();
            const champ = li.querySelector('.utilise input');
            if (champ && b.dataset.verdict === 'trop' && li.hasAttribute('data-qte-multi')) champ.focus();
        });
    });
    document.querySelectorAll('.utilise input').forEach(function (champ) {
        champ.addEventListener('change', function () {
            const li = champ.closest('li');
            const cle = cleRetour(li.dataset.owner, li.dataset.objet);
            const n = parseInt(champ.value, 10);
            if (!retours[cle] || isNaN(n) || n < 0) return;
            retours[cle].quantite_utilisee = n;
            envoyerRetour(li.dataset.owner, li.dataset.objet, 'trop', n);
        });
    });
    document.querySelectorAll('form.ajout-manque').forEach(function (form) {
        form.addEventListener('submit', function (e) {
            e.preventDefault();                           // pas de rechargement de page
            const owner = form.closest('div.manques').dataset.owner;
            const champ = form.querySelector('input');
            const objet = champ.value.trim();
            if (!objet) return;
            const liste = manques[owner] = manques[owner] || [];
            if (liste.indexOf(objet) === -1) {
                liste.push(objet);
                envoyerRetour(owner, objet, 'manque', null);
            }
            champ.value = '';
            afficherRetours();
        });
    });
    lireRetoursServeur();                                 // chargement initial
    let memorise = '';
    try { memorise = localStorage.getItem('valise-bilan:' + VOYAGE) || ''; } catch (e) {}
    if (memorise) activerBilan(true);                     // on reprend le bilan là où on l'a laissé
    setInterval(rafraichirRetours, 4000);
    document.addEventListener('visibilitychange', rafraichirRetours);
}

// Tout ce qui dépend de `sauvegarde` : à lancer seulement une fois l'état reçu du serveur
function initialiser() {
    document.querySelectorAll('input[type=checkbox]').forEach(function (box) {
        if (sauvegarde[box.dataset.key]) box.checked = true;
        box.addEventListener('change', function () {
            sauvegarde[box.dataset.key] = box.checked;
            sauverCoche(box.dataset.key, box.checked);
            majProgression();
            majOnglets();
            majRayons();
            const rayon = box.closest('details.rayon');
            if (rayon && rayon.classList.contains('fini')) rayon.open = false;   // rayon fini -> on le replie
            appliquerMasque();
        });
    });

    onglets.forEach(function (b) { b.addEventListener('click', function () { activer(b.dataset.owner); }); });
    btnMasque.addEventListener('click', function () {
        masquer = !masquer;
        btnMasque.textContent = masquer ? 'Afficher tout' : 'Masquer les rangés';
        appliquerMasque();
    });
    btnReset.addEventListener('click', function () {
        document.querySelectorAll('input[type=checkbox]').forEach(function (box) {
            box.checked = false;                 // on décoche visuellement
            delete sauvegarde[box.dataset.key];  // et on efface de la mémoire locale
            sauverCoche(box.dataset.key, false);  // et on sauve le décochage sur le serveur
        });
        document.querySelectorAll('details.rayon').forEach(function (d) { d.open = true; });
        majProgression();
        majOnglets();
        majRayons();
        appliquerMasque();
    });

    majRayons();
    document.querySelectorAll('details.rayon.fini').forEach(function (d) { d.open = false; });  // déjà rangés au chargement
    if (onglets.length) activer(onglets[0].dataset.owner);
    majOnglets();
    majProgression();

    initialiserBilan();
    setInterval(rafraichir, 4000);                     // toutes les 4 s
    document.addEventListener('visibilitychange', rafraichir);   // et dès qu'on revient sur la page
}

// Bouton météo : visible de J-10 (portée des prévisions) jusqu'à la fin du voyage
(function () {
    const btn = document.getElementById('meteo');
    if (!btn || typeof DEPART === 'undefined') return;
    const aujourdhui = new Date(new Date().toDateString());           // minuit local
    const ouverture = new Date(DEPART + 'T00:00:00');
    ouverture.setDate(ouverture.getDate() - 10);                      // en jours : insensible au changement d'heure
    const fermeture = new Date(FIN + 'T00:00:00');
    if (aujourdhui < ouverture || aujourdhui > fermeture) return;
    btn.hidden = false;
    btn.addEventListener('click', function () {
        btn.disabled = true;
        btn.textContent = '⏳ Prévisions en cours…';
        const base = 'api/meteo/' + encodeURIComponent(VOYAGE);
        // 1. le serveur dit quoi demander ; 2. le téléphone appelle Open-Meteo (Render prend des 429) ;
        // 3. le serveur régénère la valise avec ce qu'on lui envoie
        fetch(base + '/fenetres')
            .then(function (r) { if (!r.ok) throw new Error('erreur ' + r.status); return r.json(); })
            .then(function (res) {
                return Promise.all(res.fenetres.map(function (f) {
                    return fetch(f.url)
                        .then(function (r) {
                            if (!r.ok) return { erreur: r.status + ' ' + (r.statusText || 'refus Open-Meteo') };
                            return r.json().then(function (j) { return j.daily; });
                        })
                        .catch(function () { return { erreur: 'Open-Meteo injoignable' }; });
                })).then(function (resultats) {
                    const previsions = {};
                    res.fenetres.forEach(function (f, i) { previsions[f.etape] = resultats[i]; });
                    return fetch(base, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ previsions: previsions }),
                    });
                });
            })
            .then(function (r) { if (!r.ok) throw new Error('erreur ' + r.status); return r.json(); })
            .then(function (res) {
                if (res.etapes_prevues > 0) {                         // succès : on le dit, puis on recharge
                    btn.textContent = '✅ ' + res.etapes_prevues + ' étape(s) actualisée(s) avec les prévisions'
                        + (res.erreurs.length ? ' · ⚠️ ' + res.erreurs.join(' · ') : '');
                    setTimeout(function () { location.reload(); }, res.erreurs.length ? 4000 : 1500);
                } else if (res.erreurs.length) {
                    btn.disabled = false;
                    btn.textContent = '⚠️ Météo indisponible : ' + res.erreurs.join(' · ');
                } else {
                    btn.textContent = 'ℹ️ Aucune étape à moins de 10 jours : normales de saison gardées';
                }
            })
            .catch(function (e) {
                btn.disabled = false;
                btn.textContent = '⚠️ Échec (' + e.message + '), réessaie';
            });
    });
})();

// Démarrage : on va chercher l'état de CE voyage sur le serveur, puis on initialise
fetch('api/etat/' + encodeURIComponent(VOYAGE))
    .then(function (r) { return r.json(); })
    .then(function (data) {
        sauvegarde = data;
        initialiser();
    })
    .catch(function () {
        // Serveur éteint, Postgres down, ou téléphone hors du wifi du Mac
        document.body.insertAdjacentHTML('afterbegin',
            '<p style="background:#fee2e2;color:#991b1b;padding:.75rem 1rem;' +
            'border-radius:10px;margin-bottom:1rem;">Pas connecté au serveur — ' +
            'vérifie que le Mac est allumé et sur le même wifi.</p>');
    });
"""

# 1a. BASE COMMUN : 1 pour le groupe entier (un seul suffit à plusieurs).
BASE_COMMUN = {
    "trousse toilette": 1,
    "déodorant": 1,
    "trousse pharmacie": 1,
    "sac de jour": 1,
}

# 1b. BASE PERSO : matos non-vêtement, chacun le sien -> ×nb, tiroir "Essentiels".
BASE_PERSO = {
    "chargeur": 1,
    "livre / liseuse": 1,
    "montre": 1,
    "adaptateur de prise": 1,   # chacun le sien (1 par personne) — moins relou à partager
}

# 1c. VÊTEMENTS DE BASE : la garde-robe de tout voyage, chacun la sienne -> ×nb,
#     rangés dans le tiroir "Affaires perso".
VETEMENTS_BASE = {
    "ceinture": 1,
    "chaussures de rechange": 1,
    "chaussettes": "par_jour",
    "pantalons": "par_semaine",
    "pyjama": "par_semaine",
    "sweat": "par_semaine",
    "chemises": "par_3_jours",
}

# 2a. PAR TYPE — COMMUN : 1 pour le groupe (seuls les types concernés figurent ici).
PAR_TYPE_COMMUN = {
    "chaud": {"crème solaire": "par_semaine", "biafine": 1},   # 1 tube / semaine de soleil
    "plage": {"crème solaire": "par_semaine", "biafine": 1},
    "pluie": {"parapluie": 1},
    "averses": {"parapluie": 1},                 # un parapluie pour le groupe
    "snorkeling": {"pochette étanche": 1},
    "nature":     {"répulsif moustiques": 1, "lampe frontale": 1},
    "nuit":       {"cadenas": 1},                # bagages en train / bus de nuit
    "road trip":  {"support téléphone voiture": 1, "chargeur voiture USB": 1, "glacière souple": 1},
}

# 2b. PAR TYPE — PERSO : chacun le sien (tout ce qui se porte).
PAR_TYPE_PERSO = {
    "chaud":    {"chapeau": 1, "lunettes de soleil": "2_au_dela_d_une_semaine",
                 "shorts": "par_3_jours", "sandales": 1,
                 "chemises légères": "par_3_jours",
                 "chemises": 0},                 # 0 = retire les chemises normales quand il fait chaud
                                                 # hauts/robes : gérés par personne (voir PAR_PERSONNE) pour éviter les doublons
    "frais":    {"pull": 1},                     # soirées fraîches (min < 15 °C) sans être "froid"
    "froid":    {"manteau": 1, "pull": "par_3_jours", "gants": 1, "bonnet": 1,
                 "écharpe": 1, "sous-couche thermique": "par_3_jours",
                 "grosses chaussures": 1, "collants": "par_3_jours"},
    "plage":    {"maillot de bain": "maillot", "tongs": 1, "futa": 1,
                 "shorts": "par_3_jours", "sandales": 1, "lunettes de soleil": "2_au_dela_d_une_semaine"},
    "montagne": {"chaussures rando": 1, "gourde": 1, "coupe-vent": 1, "polaire": 1,
                 "chaussettes de rando": "par_3_jours", "bâtons": 1},
    "ville":    {"tenue habillée": 1, "baskets": 1},
    "pluie":    {"imperméable": 1, "chaussures imperméables": 1},
    "averses":  {"imperméable": 1},              # orages d'été : K-way, pieds mouillés tolérés
    # activités enrichies : noms d'objets absents de CHAUD_PERSO (qui réécrit après coup)
    "culte":      {"tenue couverte": 1, "étole": 1},          # épaules et genoux couverts
    "snorkeling": {"top anti-UV": 1, "chaussures d'eau": 1},  # corail, galets, oursins
    "scooter":    {"buff anti-poussière": 1, "gants légers": 1},
    "nature":     {"manches longues légères": 1},             # moustiques au crépuscule
    "nuit":       {"bouchons d'oreilles": 1, "masque de sommeil": 1, "couche légère": 1},
}

# 3. PAR PERSONNE : les affaires perso.
PAR_PERSONNE = {
    "Julien":   {"rasoir": 1, "caleçons": "par_jour", "t-shirts": "par_jour"},
    "Laetitia": {"maquillage": 1, "lisseur": 1, "culottes": "par_jour",
                 "hauts": "par_jour", "soutien-gorge": "par_semaine",
                 "robes": "par_3_jours", "démaquillant": 1, "bijoux": 1,
                 "boucles d'oreille": (3, "par_semaine")},   # 3 paires / semaine
}

# 3quater. JAMAIS : ce qu'une personne ne prend jamais, même si une table par-type
#          l'ajoute (ex. items genrés présents dans les tables partagées PAR_TYPE_PERSO
#          comme "collants" -> pas pour Julien).
JAMAIS = {
    "Julien": {"collants", "sandales", "étole"},
}

# 3ter. RÉGLAGES EN PAYS CHAUD, PAR PERSONNE : dès qu'un climat "chaud" est présent,
#       on écrase la garde-robe de base par personne (le SEUL endroit qui peut RÉDUIRE :
#       _remplir prend le max base/climat, donc ne sait qu'augmenter). Valeur 0 = retrait.
#       Absent de la table -> comportement par défaut (valeurs de base). Post-traité
#       dans faire_valise. Sert aux chaussures ouvertes ET aux tenues du soir de Laetitia :
#       1 tenue / 3 j (par_3_jours), soit robe SOIT chemise + bas ; préférence chemise.
#       Pour 15 j : 2 robes + 3 chemises = 5 tenues ; bas = 3 short habillé + 2 pantalons.
CHAUD_PERSO = {
    "Julien":   {"chaussettes": (3, "par_semaine"),    # 3 paires / semaine (chaussures fermées légères)
                 "sweat": 1},                           # soirées fraîches : la règle "frais" ajoute un pull
    "Laetitia": {
        "chaussettes": 0,                  # aucune : que des chaussures ouvertes
        "sweat": 1,                        # soirées fraîches : la règle "frais" ajoute un pull
        "hauts": "par_2_jours",            # jour : moins de hauts (le soir = tenues)
        "chemises légères": 0,             # jour couvert par les hauts -> on retire
        "tenue habillée": 0,               # remplacée par le modèle de tenues du soir
        "robes": "par_semaine",            # tenue-robe (~1/3 des soirs)
        "chemise habillée": "par_4_jours", # tenue-chemise (préférée, ~2/3 des soirs)
        "short habillé": "par_4_jours",    # bas de tenue, distinct du short de plage
    },
}

# 3quinquies. CONDUCTEURS : qui a le permis. Seuls eux emportent un permis
#             (même hors UE) — et uniquement si le voyage implique de conduire.
CONDUCTEURS = {"Julien"}

# 3bis. Code de saisie -> liste des personnes concernées (pilote la question du prénom).
CHOIX_PERSONNE = {
    "j": ["Julien"],
    "l": ["Laetitia"],
    "2": ["Julien", "Laetitia"],
}

# Activités d'une étape : saisies par lettre, combinables ("vp" = ville + plage).
# Le climat (chaud/froid/pluie) n'est PAS ici : il vient des données réelles.
CHOIX_ACTIVITE = {"v": "ville", "p": "plage", "m": "montagne",     # m = montagne ou rando
                  "t": "culte", "s": "snorkeling", "k": "scooter", "j": "nature",
                  "n": "nuit", "r": "road trip"}
ACTIVITES_CONDUITE = {"scooter", "road trip"}      # impliquent le permis pour les conducteurs

# 3ter. THÈMES d'affichage : à quel rayon appartient chaque objet.
#       7 rayons explicites, Divers compris. Tout objet ABSENT de ces 7 sets est
#       un OUBLI : theme_de() le mettra dans Divers par sécurité, mais le garde-fou
#       objets_sans_rayon() le signalera au lancement (au lieu de le cacher).
THEMES = {
    "Vêtements": {
        "pantalons", "pyjama", "sweat", "shorts", "hauts", "short habillé",
        "robes", "manteau", "pull", "maillot de bain", "coupe-vent", "polaire",
        "tenue habillée", "imperméable", "t-shirts",
        "chemises", "chemises légères", "chemise habillée",
        "tenue couverte", "top anti-UV", "manches longues légères", "couche légère",
    },
    "Sous-vêtements": {
        "caleçons", "culottes", "soutien-gorge", "chaussettes",
        "chaussettes de rando", "collants", "sous-couche thermique",
    },
    "Chaussures": {
        "chaussures de rechange", "sandales", "tongs", "grosses chaussures",
        "chaussures rando", "baskets", "chaussures imperméables", "chaussures d'eau",
    },
    "Accessoires": {
        "ceinture", "chapeau", "lunettes de soleil", "gants", "bonnet",
        "écharpe", "bijoux", "boucles d'oreille", "montre", "futa",
        "étole", "buff anti-poussière", "gants légers",
    },
    "Hygiène": {
        "trousse toilette", "déodorant", "rasoir", "maquillage", "lisseur",
        "démaquillant", "crème solaire", "biafine", "trousse pharmacie",
        "répulsif moustiques",
    },
    "Tech": {
        "chargeur", "adaptateur de prise",
        "lampe frontale", "support téléphone voiture", "chargeur voiture USB",
    },
    "Documents": {
        "passeport", "carte d'identité", "permis", "permis international",
    },
    "Divers": {
        "sac de jour", "livre / liseuse", "parapluie", "gourde", "bâtons",
        "pochette étanche", "bouchons d'oreilles", "masque de sommeil", "cadenas",
        "glacière souple",
    },
}

# Icône affichée devant chaque rayon dans la checklist (un rayon sans icône -> test rouge).
ICONES_RAYON = {
    "Vêtements": "👕", "Sous-vêtements": "🩲", "Chaussures": "👟", "Accessoires": "🕶️",
    "Hygiène": "🧴", "Tech": "🔌", "Documents": "🪪", "Divers": "🎒",
}

# 4. GÉO — Les pays sont identifiés par leur CODE ISO ("VN", "GB"…), tel que
#    renvoyé par le géocodage (api_climat.lieux). Pourquoi pas le nom ? L'API écrit
#    "Viêt Nam" là où on écrirait "Vietnam" : un code ne varie pas (jointure sur l'ID,
#    pas sur le libellé). Plus besoin de table ville -> pays : le géocodage la remplace.

# 4a. UE : les 27 pays membres. Appartenance -> UE ; absence d'un pays connu -> hors UE.
PAYS_UE = {
    "AT", "BE", "BG", "HR", "CY", "CZ", "DK",  # Autriche, Belgique, Bulgarie, Croatie, Chypre, Tchéquie, Danemark
    "EE", "FI", "FR", "DE", "GR", "HU", "IE",  # Estonie, Finlande, France, Allemagne, Grèce, Hongrie, Irlande
    "IT", "LV", "LT", "LU", "MT", "NL", "PL",  # Italie, Lettonie, Lituanie, Luxembourg, Malte, Pays-Bas, Pologne
    "PT", "RO", "SK", "SI", "ES", "SE",        # Portugal, Roumanie, Slovaquie, Slovénie, Espagne, Suède
}

# 4b. CARTE D'IDENTITÉ SUFFIT (et permis français valable) : UE + Schengen/EEE hors UE,
#     micro-États, et territoires français d'outre-mer. Tout le reste -> passeport (prudent).
SANS_PASSEPORT = PAYS_UE | {
    "CH", "NO", "IS", "LI",                    # Suisse, Norvège, Islande, Liechtenstein
    "MC", "AD", "SM", "VA",                    # Monaco, Andorre, Saint-Marin, Vatican
    "RE", "GP", "MQ", "GF", "YT",              # Réunion, Guadeloupe, Martinique, Guyane, Mayotte
    "PF", "NC", "PM", "BL", "MF", "WF",        # Polynésie, Nouvelle-Calédonie, St-Pierre, St-Barth, St-Martin, Wallis
}

# 4c. PRISE : quel adaptateur emporter DEPUIS LA FRANCE pour ce pays.
#     Valeurs usuelles (à revérifier avant un voyage). Pays absent -> "à vérifier".
#     On part des groupes de prises, puis on construit la table pays -> libellé.
_PRISES = {
    # Prises type C/E/F, comme en France
    "aucun": [
        "FR", "RE", "GP", "MQ", "GF", "YT", "PF", "NC", "PM", "BL", "MF", "WF",  # France + outre-mer
        "BE", "NL", "LU", "DE", "AT", "CH", "LI", "DK", "SE", "NO", "FI", "IS",  # Europe du Nord/Ouest
        "ES", "PT", "IT", "GR", "SI", "HR", "MC", "AD", "SM", "VA",              # Europe du Sud
        "PL", "CZ", "SK", "HU", "RO", "BG", "EE", "LV", "LT",                    # Europe de l'Est (UE)
        "RS", "BA", "ME", "MK", "AL", "XK", "MD", "UA", "RU",                    # Balkans, Europe de l'Est
        "TR", "GE", "AM", "AZ",                                                  # Turquie, Caucase
        "MA", "TN", "DZ", "EG", "SN", "CI", "CV", "ET", "RW", "MG",              # Afrique
        "ID", "KR", "MN", "CL", "UY", "PY",                                      # Indonésie, Corée, Mongolie, Am. du Sud
    ],
    # Prises britanniques (type G)
    "UK": [
        "GB", "IE", "MT", "CY",                                                  # Europe
        "AE", "QA", "BH", "KW", "OM",                                            # Golfe
        "MY", "SG", "HK", "BN",                                                  # Asie
        "KE", "UG", "ZM", "MW", "GH", "SC",                                      # Afrique
    ],
    # Prises américaines (type A/B, 100-127 V)
    "US (110V)": [
        "US", "CA", "MX", "PR", "BS", "JM", "DO",                                # Amérique du Nord, Caraïbes
        "GT", "HN", "SV", "NI", "CR", "PA",                                      # Amérique centrale
        "CO", "EC", "VE",                                                        # Amérique du Sud
        "JP", "TW",                                                              # Japon, Taïwan
    ],
    # Prises mélangées -> adaptateur universel
    "universel": [
        "TH", "VN", "KH", "LA", "MM", "CN", "MO",                                # Asie du Sud-Est, Chine
        "IN", "NP", "BD", "PK",                                                  # Sous-continent indien
        "JO", "IL", "LB",                                                        # Proche-Orient
        "BR", "PE", "BO", "BZ",                                                  # Amériques
    ],
    "universel / US": ["PH", "CU"],                                              # Philippines, Cuba
    "universel / UK": ["LK", "MV", "MU", "TZ", "NG", "SA"],                      # Sri Lanka, Maldives, Maurice…
    "type I (Australie)": ["AU", "NZ", "FJ", "AR"],                              # Australie, NZ, Fidji, Argentine
    "type M (Afrique du Sud)": ["ZA", "NA", "BW"],                               # Afrique du Sud, Namibie, Botswana
}
PAYS_VERS_PRISE = {pays: prise for prise, liste in _PRISES.items() for pays in liste}


# 5. CLIMAT — seuils appliqués aux normales réelles (api_climat). Façon CASE WHEN.
SEUIL_CHAUD = 25          # °C : max moyenne >= 25 -> "chaud"
SEUIL_FROID = 12          # °C : max moyenne < 12 -> "froid"
SEUIL_FRAIS = 15          # °C : min moyenne < 15 (et pas "froid") -> "frais" (un pull pour le soir)
SEUIL_JOURS_FORTE_PLUIE = 4   # jours >= 5 mm par mois >= 4 (≈ une vraie averse par semaine) -> "pluie"
                              # Pas les jours >= 1 mm : ils comptent les petites averses tropicales
                              # (Phu Quoc en janvier = 10 j, en pleine saison sèche).

MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet",
        "août", "septembre", "octobre", "novembre", "décembre"]


def ligne_climat(destination, mois, n):
    """Phrase lisible des normales d'une étape ; n = dict de api_climat.normales ou None."""
    debut = f"{destination} · {MOIS[mois - 1]} : "       # mois 1 -> index 0
    if n is None:
        return debut + "climat indisponible"
    return (debut + f"{round(n['tmin'])}–{round(n['tmax'])} °C · 🌧️ {n['jours_pluie']} j de pluie/mois, "
            f"dont {round(n['jours_forte_pluie'])} forts")


def puce_climat(destination, n):
    """Version courte pour l'en-tête de la checklist : 'Hanoï 14–21° · 🌧️ 3 j forts'."""
    if n is None:
        return f"{destination} ?"
    puce = f"{destination} {round(n['tmin'])}–{round(n['tmax'])}° · 🌧️ {round(n['jours_forte_pluie'])} j forts"
    if "prevu_le" in n:                          # prévision (J-10) plutôt que normale de saison
        puce += f" · prévu le {n['prevu_le'][8:10]}/{n['prevu_le'][5:7]}"
    return puce


def types_climat(n):
    """Étiquettes climatiques d'une étape à partir de ses normales (None -> aucune)."""
    if n is None:
        return []
    types = []
    if n["tmax"] >= SEUIL_CHAUD:
        types.append("chaud")
    elif n["tmax"] < SEUIL_FROID:
        types.append("froid")
    if n["tmin"] < SEUIL_FRAIS and "froid" not in types:    # froid couvre déjà les pulls
        types.append("frais")
    if n["jours_forte_pluie"] >= SEUIL_JOURS_FORTE_PLUIE:
        types.append("averses" if "chaud" in types else "pluie")   # chaud + pluie = orages
    return types


def statut_ue(code_pays):
    """Statut documents : 'ue' (carte d'identité suffit — UE + Schengen), 'hors_ue'
    (passeport + permis international), ou 'inconnu' (pays non modélisé ou hors ligne)."""
    if code_pays in SANS_PASSEPORT:
        return "ue"
    if code_pays in PAYS_VERS_PRISE:     # pays connu hors zone carte d'identité
        return "hors_ue"
    return "inconnu"                     # pays non modélisé -> défaut prudent (passeport)


def adaptateur_pour(code_pays):
    """Libellé de l'adaptateur à emporter depuis la France, ou 'à vérifier'."""
    return PAYS_VERS_PRISE.get(code_pays, "à vérifier")

def statut_ue_itineraire(itineraire):
    hors_ue = False
    inconnu = False
    for etape in itineraire:
        statut = statut_ue(etape.get("code_pays"))
        if statut == "hors_ue":
            hors_ue = True
        elif statut == "inconnu":
            hors_ue = True
            inconnu = True
    return hors_ue, inconnu      # <-- deux valeurs = un tuple

def prises_itineraire(itineraire):
    prises = set()               # ensemble vide ; les doublons se dédupliquent tout seuls
    for etape in itineraire:
        prise = adaptateur_pour(etape.get("code_pays"))
        if prise != "aucun":                  # on ignore les "aucun"
            prises.add(prise)
    return prises

def climat_de(etape):
    """Le climat retenu pour une étape : la prévision si on en a une, sinon les normales."""
    return etape.get("prevision") or etape.get("normales")


def types_pour(etape):
    """Types d'une étape = climat (déduit des normales) + activités (saisies par l'utilisateur)."""
    return types_climat(climat_de(etape)) + etape.get("activites", [])

def total_jours(itineraire):
    """Compter le nombre de jours d'un itinéraire (liste de tuples [(ville, nb_jours), ...])."""
    return sum(etape["jours"] for etape in itineraire)

def jours_par_type(itineraire):
    jours = {}
    for etape in itineraire:
        for type_dest in types_pour(etape):
            jours[type_dest] = jours.get(type_dest, 0) + etape["jours"]
    return jours

def quantite_reelle(marqueur, jours):
    """Traduire un marqueur de quantité en nombre réel selon la durée du voyage."""
    if isinstance(marqueur, tuple):        # ex: (3, "par_semaine") = 3× la base par semaine
        nombre, base = marqueur
        return nombre * quantite_reelle(base, jours)
    if marqueur == "par_jour":
        return jours
    if marqueur == "par_semaine":
        return max(1, jours // 7)   # jamais moins de 1 (plancher)
    if marqueur == "par_4_jours":
        return max(1, jours // 4)
    if marqueur == "par_3_jours":
        return max(1, jours // 3)
    if marqueur == "par_2_jours":
        return max(1, jours // 2)
    if marqueur == "maillot":   # 1, puis 2 dès 4 jours (un qui sèche), plafond 3 (pour le style)
        return min(3, max(2, jours // 3)) if jours >= 4 else 1
    if marqueur == "2_au_dela_d_une_semaine":   # ex: lunettes de soleil, une paire de secours
        return 2 if jours > 7 else 1
    return marqueur          # déjà un nombre (ex: 1) -> tel quel


def theme_de(objet):
    """Trouver le rayon d'un objet ; par défaut 'Divers' s'il n'est listé nulle part."""
    for theme, objets in THEMES.items():
        if objet in objets:
            return theme
    return "Divers"


def paquet_vide():
    """Un paquet neuf : un sous-dict vide par thème (l'ordre = l'ordre d'affichage)."""
    return {"Vêtements": {}, "Sous-vêtements": {}, "Chaussures": {},
            "Accessoires": {}, "Hygiène": {}, "Tech": {}, "Documents": {},
            "Divers": {}}


def objets_sans_rayon():
    """Garde-fou : renvoie les objets qui n'appartiennent à AUCUN rayon de THEMES.

    Rassemble tous les objets de toutes les tables de données (set = ensemble),
    puis soustrait ceux déjà classés. Ce qui reste = les oublis à ranger.
    Vide = tout est classé.
    """
    tous = set(BASE_COMMUN) | set(BASE_PERSO) | set(VETEMENTS_BASE)
    for sous_table in PAR_TYPE_COMMUN.values():
        tous |= set(sous_table)
    for sous_table in PAR_TYPE_PERSO.values():
        tous |= set(sous_table)
    for sous_table in PAR_PERSONNE.values():
        tous |= set(sous_table)
    for sous_table in CHAUD_PERSO.values():
        tous |= set(sous_table)
    classes = set()
    for objets in THEMES.values():
        classes |= objets
    return tous - classes


def _remplir(paquet, base_tables, type_tables, jours_types, total):
    """Remplir un paquet selon la règle max + suppression.

    - base_tables : tables {objet: marqueur} dimensionnées sur `total`.
    - type_tables : {type: {objet: marqueur}} dimensionnées sur jours_types[type],
      pour les seuls types présents. Un marqueur 0 = suppression.
    """
    base_q = {}          # objet -> quantité issue des tables de base
    climat_q = {}        # objet -> max des quantités climatiques positives
    climat_zero = set()  # objets qu'un climat veut retirer (marqueur 0)

    # Temps 1a : tables de base, dimensionnées sur le total
    for table in base_tables:
        for objet, marqueur in table.items():
            q = quantite_reelle(marqueur, total)
            if q > 0:
                base_q[objet] = max(base_q.get(objet, 0), q)

    # Temps 1b : tables par climat, dimensionnées sur les jours du climat
    for type_dest, jours in jours_types.items():
        for objet, marqueur in type_tables.get(type_dest, {}).items():
            if marqueur == 0:
                climat_zero.add(objet)              # candidat au retrait
                continue
            q = quantite_reelle(marqueur, jours)
            if q > 0:
                climat_q[objet] = max(climat_q.get(objet, 0), q)

    # Temps 2 : finalisation
    for objet in set(base_q) | set(climat_q) | climat_zero:
        cq = climat_q.get(objet, 0)
        if objet in climat_zero and cq == 0:
            continue                            # supprimé : climat retire, aucun positif
        quantite = max(base_q.get(objet, 0), cq)
        if quantite > 0:
            paquet[theme_de(objet)][objet] = quantite


CHAUSSURES_FERMEES = {"baskets", "grosses chaussures", "chaussures rando", "chaussures imperméables"}
RAYONS_LAVABLES = ("Vêtements", "Sous-vêtements")   # ce qu'une lessive en route permet de réduire
SEUIL_LESSIVE = 10      # la question "lessive ?" n'est posée qu'au-delà de 10 jours
PLANCHER_LESSIVE = 2    # avec lessive, jamais moins de 2 d'un vêtement (un sur soi, un au lavage)


def faire_valise(jours_types, total, personnes, hors_ue, conduit, adaptateur=True,
                 lessive_tous_les=None):
    """Construire la checklist {proprietaire: {theme: {objet: quantité}}}.

    - jours_types : {type de destination: jours cumulés} (couche d'agrégation).
    - total       : durée totale du voyage (dimensionne les objets de base).
    - personnes   : liste de personnes qui font leur valise.
    - hors_ue     : True -> passeport, False -> carte d'identité.
    - conduit     : True -> permis (+ permis international si hors_ue).
    - adaptateur  : False -> aucune étape n'en a besoin (prises françaises partout) : on le retire.
    - lessive_tous_les : None -> pas de lessive ; N -> vêtements et sous-vêtements prévus pour N jours.
    """
    # Un paquet par propriétaire : "Partagé" + un paquet par personne.
    # Chaque paquet est lui-même découpé par thème (via paquet_vide()).
    valise = {"Partagé": paquet_vide()}
    for personne in personnes:
        valise[personne] = paquet_vide()

    # === PARTAGÉ : 1 pour le groupe (base commune + types communs présents) ===
    _remplir(valise["Partagé"],
             base_tables=[BASE_COMMUN],
             type_tables=PAR_TYPE_COMMUN,
             jours_types=jours_types, total=total)

    # === PERSO : le paquet de CHAQUE personne ===
    for personne in personnes:
        paquet = valise[personne]        # raccourci : paquet POINTE vers valise[personne]
        _remplir(paquet,
                 base_tables=[BASE_PERSO, VETEMENTS_BASE, PAR_PERSONNE[personne]],
                 type_tables=PAR_TYPE_PERSO,
                 jours_types=jours_types, total=total)
        # filtre final : ce que cette personne ne prend jamais (items genrés, etc.)
        for objet in JAMAIS.get(personne, set()):
            paquet[theme_de(objet)].pop(objet, None)
        # réglages en pays chaud : écrasent la base (chaussures ouvertes + tenues du soir)
        if "chaud" in jours_types:
            for objet, marqueur in CHAUD_PERSO.get(personne, {}).items():
                rayon = paquet[theme_de(objet)]
                q = quantite_reelle(marqueur, total)
                if q > 0:
                    rayon[objet] = q
                else:
                    rayon.pop(objet, None)
        # chaussures fermées prévues : les "de rechange" font doublon, et il faut des chaussettes
        if CHAUSSURES_FERMEES & set(paquet["Chaussures"]):
            paquet["Chaussures"].pop("chaussures de rechange", None)
            if "chaussettes" not in paquet["Sous-vêtements"]:
                paquet["Sous-vêtements"]["chaussettes"] = quantite_reelle((3, "par_semaine"), total)
        if not adaptateur:
            paquet[theme_de("adaptateur de prise")].pop("adaptateur de prise", None)
        # documents personnels (chacun les siens)
        if hors_ue:
            paquet[theme_de("passeport")]["passeport"] = 1
        else:
            paquet[theme_de("carte d'identité")]["carte d'identité"] = 1
        if (conduit or ACTIVITES_CONDUITE & set(jours_types)) and personne in CONDUCTEURS:
            paquet[theme_de("permis")]["permis"] = 1
            if hors_ue:
                paquet[theme_de("permis international")]["permis international"] = 1

    # === LESSIVE : brouillon de valise comme si le voyage durait N jours ===
    # On y prend seulement les rayons lavables ; toutes les règles (climats, CHAUD_PERSO,
    # JAMAIS) s'appliquent au brouillon comme à la vraie valise.
    if lessive_tous_les and lessive_tous_les < total:
        jours_courts = {t: min(j, lessive_tous_les) for t, j in jours_types.items()}
        brouillon = faire_valise(jours_courts, lessive_tous_les, personnes, hors_ue,
                                 conduit, adaptateur)
        for personne in personnes:
            for rayon in RAYONS_LAVABLES:
                complet = valise[personne][rayon]
                # plancher : un sur soi, un au lavage — sans dépasser le voyage complet
                valise[personne][rayon] = {
                    objet: max(q, min(complet[objet], PLANCHER_LESSIVE))
                    for objet, q in brouillon[personne][rayon].items()}

    return valise

# 9. APPRENTISSAGE — exploiter les bilans des voyages précédents (session 3).
#    Options prudentes : rien n'est appliqué sans "o" ; un oubli est reproposé à la personne
#    concernée sur tous ses voyages ; une quantité n'est ajustée que d'après un voyage au
#    MÊME climat (le plus récent qui a un avis sur cet objet).
CLIMATS = {"chaud", "froid", "frais", "pluie", "averses"}       # les étiquettes météo (pas les activités)


def cle_objet(texte):
    """Clé de rapprochement : 'Bouchons d'oreilles' == 'bouchon d'oreille' (casse, accents, pluriels)."""
    mots = sans_accents(texte.strip().lower()).split()
    return " ".join(m[:-1] if len(m) > 3 and m[-1] in "sx" else m for m in mots)


def etiquettes_climat(jours_types):
    return {t for t in jours_types if t in CLIMATS}


def _avis_le_plus_recent(historique, personne, cle, climat):
    """Premier voyage au même climat (historique trié du plus récent) qui a un avis sur cet objet."""
    for voyage in historique:
        if etiquettes_climat(voyage["jours_types"]) != climat:
            continue
        for r in voyage["retours"]:
            if r["proprietaire"] == personne and r["verdict"] != "manque" and cle_objet(r["objet"]) == cle:
                return voyage, r
    return None, None


def propositions(valise, jours_types, historique, regles):
    """Liste des ajustements à proposer. Fonction pure : ne modifie rien, ne pose aucune question."""
    props = []
    climat = etiquettes_climat(jours_types)
    for personne, paquet in valise.items():
        presents = {cle_objet(o) for objets in paquet.values() for o in objets}
        en_regle = {cle_objet(r["objet"]) for r in regles.get(personne, [])}

        # 1. Oublis : ce qui a manqué à cette personne, quel que soit le climat
        vus = set()
        for voyage in historique:
            for r in voyage["retours"]:
                cle = cle_objet(r["objet"])
                if (r["proprietaire"] != personne or r["verdict"] != "manque"
                        or cle in presents or cle in en_regle or cle in vus):
                    continue
                vus.add(cle)
                props.append({"type": "ajout", "personne": personne, "objet": r["objet"],
                              "theme": theme_de(r["objet"]), "actuelle": 0, "proposee": 1,
                              "source": voyage["libelle"]})

        # 2. Quantités et retraits : d'après le voyage au même climat le plus récent
        for theme, objets in paquet.items():
            for objet, quantite in objets.items():
                voyage, avis = _avis_le_plus_recent(historique, personne, cle_objet(objet), climat)
                if avis is None or avis["verdict"] == "utile":
                    continue
                base = {"personne": personne, "objet": objet, "theme": theme,
                        "actuelle": quantite, "source": voyage["libelle"]}
                utilise = avis["quantite_utilisee"]
                if avis["verdict"] == "pas_servi" or utilise == 0 or (utilise is None and quantite == 1):
                    raison = "pas servi" if avis["verdict"] == "pas_servi" else "en trop"
                    props.append({"type": "retrait", **base, "proposee": 0, "raison": raison})
                elif utilise is not None:
                    prevu_avant = next((q for (p, _t, o), q in voyage["objets"].items()
                                        if p == personne and cle_objet(o) == cle_objet(objet)), None)
                    if prevu_avant:
                        nouvelle = max(1, round(quantite * utilise / prevu_avant))   # au prorata de l'utilisé
                        if nouvelle < quantite:
                            props.append({"type": "quantite", **base, "proposee": nouvelle,
                                          "utilise": f"{utilise}/{prevu_avant}"})
    return props


def appliquer(valise, proposition):
    """Applique UNE proposition acceptée (quantité, retrait = 0, ou ajout)."""
    rayon = valise[proposition["personne"]].setdefault(proposition["theme"], {})
    if proposition["proposee"] == 0:
        rayon.pop(proposition["objet"], None)
    else:
        rayon[proposition["objet"]] = proposition["proposee"]


def appliquer_regles(valise, regles):
    """Ajoute les objets "toujours" des voyageurs présents ; renvoie [(personne, objet)] ajoutés."""
    ajouts = []
    for personne, liste in regles.items():
        if personne not in valise:
            continue
        presents = {cle_objet(o) for objets in valise[personne].values() for o in objets}
        for r in liste:
            if cle_objet(r["objet"]) not in presents:
                valise[personne].setdefault(r["theme"], {})[r["objet"]] = r["quantite"]
                ajouts.append((personne, r["objet"]))
    return ajouts


def valise_en_html(valise, libelle_voyage, total, prises, climats=None, code=None, depart=None):
    """Construire la page HTML de la checklist pour l'itinéraire complet.

    climats : liste optionnelle de (destination, mois, normales) — une puce par étape.
    code    : identifiant stable du voyage (date + itinéraire) ; préfixe des cases cochées.
    depart  : date de départ, affichée dans le titre.
    """
    cle_voyage = code or libelle_voyage
    quand = f" · départ le {date_en_clair(depart)}" if depart else ""
    dates_js = ""                       # pour le bouton météo (affiché de J-10 à la fin du voyage)
    if depart:
        fin = depart + timedelta(days=total - 1)
        dates_js = f' const DEPART = "{depart.isoformat()}"; const FIN = "{fin.isoformat()}";'
    adaptateurs = ", ".join(sorted(prises)) if prises else "aucun"
    puces = f'<span class="puce">🔌 Adaptateur : {adaptateurs}</span>'
    for destination, mois, n in climats or []:
        # Puce courte à l'écran, phrase complète en info-bulle (title)
        puces += f'<span class="puce" title="{ligne_climat(destination, mois, n)}">🌡️ {puce_climat(destination, n)}</span>'

    # Barres de progression : une par voyageur + le total s'ils sont plusieurs ; sinon le total seul
    voyageurs = [p for p in valise if p != "Partagé"]
    proprios_barres = voyageurs + [""] if len(voyageurs) >= 2 else [""]
    barres = ""
    for owner in proprios_barres:
        libelle = owner or ("Total" if len(voyageurs) >= 2 else "Rangé")
        barres += (f'<div class="barre" data-owner="{owner}"><div class="progress-head"><span>{libelle}</span>'
                   f'<span class="barre-compte">0 / 0</span></div>'
                   f'<div class="progress-track"><div class="progress-fill"></div></div></div>')

    onglets = '<nav class="tabs">'          # un bouton par propriétaire (Partagé/Julien/...)
    for proprietaire in valise:
        onglets += f'<button data-owner="{proprietaire}">{proprietaire} <span class="tab-count"></span></button>'
    onglets += '</nav>'

    corps = ""
    for proprietaire, themes in valise.items():
        corps += f'<section data-owner="{proprietaire}">'
        for theme, objets in themes.items():
            if not objets:
                continue
            icone = ICONES_RAYON.get(theme, "📦")
            corps += (f'<details class="rayon" open><summary><span class="icone">{icone}</span>'
                      f'<span class="nom">{theme}</span><span class="compte"></span></summary><ul>')
            for objet, quantite in sorted(objets.items()):
                cle = f"{cle_voyage}/{proprietaire}/{theme}/{objet}"
                multi = " data-qte-multi" if quantite > 1 else ""       # "utilisé x / N" n'a de sens que si N > 1
                corps += (f'<li data-owner="{proprietaire}" data-objet="{objet}" data-qte="{quantite}"{multi}>'
                          f'<label><input type="checkbox" data-key="{cle}">'
                          f'<span class="nom">{objet}</span><span class="qte">×{quantite}</span></label>'
                          f'<div class="bilan">'
                          f'<button type="button" data-verdict="utile">✅ utile</button>'
                          f'<button type="button" data-verdict="trop">➖ en trop</button>'
                          f'<button type="button" data-verdict="pas_servi">❌ pas servi</button>'
                          f'<span class="utilise">utilisé <input type="number" min="0" max="{quantite}" '
                          f'inputmode="numeric"> / {quantite}</span></div></li>')
            corps += "</ul></details>"
        titre = "Ce qui nous a manqué" if proprietaire == "Partagé" else f"Ce qui a manqué à {proprietaire}"
        corps += (f'<div class="manques" data-owner="{proprietaire}"><h3>{titre}</h3>'
                  f'<div class="puces-manque"></div>'
                  f'<form class="ajout-manque"><input type="text" placeholder="ex. bouchons d\'oreilles" '
                  f'enterkeyhint="done"><button type="submit">Ajouter</button></form></div>')
        corps += "</section>"

    page = f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Valise — {libelle_voyage}</title>
<style>{HTML_STYLE}</style>
</head>
<body>
<a class="retour" href="./">← Tous les voyages</a>
<h1>{libelle_voyage} <span class="duree">· {total} jours{quand}</span></h1>
<div class="puces">{puces}</div>
<div class="collant">
<div class="barres">{barres}</div>
{onglets}
<p id="bilan-compte"></p>
</div>
{corps}
<div class="controls"><button id="meteo" class="ctrl-btn" hidden>🌦️ Actualiser avec la météo</button><button id="mode-bilan" class="ctrl-btn">📝 Bilan de fin de voyage</button><button id="toggle-masque" class="ctrl-btn">Masquer les rangés</button><button id="reset" class="ctrl-btn">Réinitialiser</button></div>
<script>const VOYAGE = {json.dumps(cle_voyage, ensure_ascii=False)};{dates_js}</script>
<script>{HTML_SCRIPT}</script>
</body>
</html>"""
    return page

def normales_avec_cache(conn, latitude, longitude, mois, chercher=normales_12_mois):
    """Lire le cache ; sinon interroger l'API (12 mois d'un coup) et remplir le cache.

    conn = None (Postgres éteint) -> API directe, sans cache.
    chercher : la fonction qui interroge l'API (remplaçable par une fausse dans les tests).
    """
    if conn is not None:
        n = lire_normales(conn, latitude, longitude, mois)
        if n is not None:
            return n                                    # cache trouvé : pas d'appel réseau
    par_mois = chercher(latitude, longitude)
    if conn is not None:
        enregistrer_normales(conn, latitude, longitude, par_mois)
    return par_mois.get(mois)


def sans_accents(texte):
    """'Février' -> 'Fevrier' : on décompose chaque lettre accentuée et on jette l'accent."""
    decompose = unicodedata.normalize("NFD", texte)
    return "".join(c for c in decompose if unicodedata.category(c) != "Mn")


def lire_mois(reponse, precedent=None):
    """'1', 'janvier', 'Janv', 'fevrier', 'AOÛT' -> numéro du mois. Entrée = mois précédent.
    Renvoie None si invalide ou ambigu ('ju' = juin ou juillet ?)."""
    texte = sans_accents(reponse.strip().lower())
    if texte == "":
        return precedent
    if texte.isdigit():
        mois = int(texte)
        return mois if 1 <= mois <= 12 else None
    trouves = [i for i, nom in enumerate(MOIS, start=1) if sans_accents(nom).startswith(texte)]
    return trouves[0] if len(trouves) == 1 else None


def lire_date(reponse):
    """'10/01/2027', '10/1/27', '2027-01-10', '10 janv. 2027' -> date ; None si invalide.
    Le mois accepte chiffre ou nom (même logique que lire_mois)."""
    texte = sans_accents(reponse.strip().lower()).replace(".", " ")
    morceaux = [m for m in re.split(r"[\s/-]+", texte) if m]     # séparateurs : espace, / ou -
    if len(morceaux) != 3:
        return None
    if len(morceaux[0]) == 4:                                   # format ISO : année-mois-jour
        annee, mois_txt, jour = morceaux
    else:
        jour, mois_txt, annee = morceaux
    mois = lire_mois(mois_txt)
    if mois is None or not (jour.isdigit() and annee.isdigit()):
        return None
    annee = int(annee) + (2000 if len(annee) == 2 else 0)       # "27" -> 2027
    try:
        return date(annee, mois, int(jour))
    except ValueError:                                          # 31 février…
        return None


def mois_des_etapes(depart, durees):
    """Mois de chaque étape, déduit de la date de départ et des jours cumulés.
    Une étape à cheval sur deux mois prend le mois de son jour du milieu."""
    mois = []
    debut = depart
    for jours in durees:
        milieu = debut + timedelta(days=(jours - 1) // 2)
        mois.append(milieu.month)
        debut += timedelta(days=jours)
    return mois


def code_voyage(depart, libelle):
    """Identifiant stable d'un voyage : même date + même itinéraire = même voyage."""
    return f"{depart.isoformat()} {libelle}"


def date_en_clair(d):
    return f"{d.day} {MOIS[d.month - 1]} {d.year}"


def lire_activites(reponse):
    """'pv', 'V P', 'v,p' -> ['plage', 'ville'] ; None si une lettre est inconnue ou si vide."""
    lettres = {c for c in reponse.lower() if c not in " ,;"}     # on ignore espaces et virgules
    if lettres and lettres <= set(CHOIX_ACTIVITE):              # <= : "est inclus dans"
        return sorted(CHOIX_ACTIVITE[l] for l in lettres)
    return None


def est_oui(reponse):
    return reponse.strip().lower() in {"o", "oui", "y", "yes"}


def lire_lessive(reponse):
    """Nombre de jours entre deux lessives ; None = pas de lessive (Entrée, "n", 0, saisie invalide)."""
    reponse = reponse.strip()
    if reponse.isdigit() and int(reponse) > 0:
        return int(reponse)
    return None


def un_par_pays(candidats):
    """Garder le premier lieu de chaque pays : Hanoï (VN) x4 + Hanoi (PG) -> 2 lignes."""
    vus = set()
    gardes = []
    for lieu in candidats:
        if lieu["code_pays"] not in vus:
            vus.add(lieu["code_pays"])
            gardes.append(lieu)
    return gardes


def libelle_lieu(lieu):
    """'Bali — Bali, Indonésie' : de quoi distinguer deux homonymes."""
    precision = ", ".join(x for x in (lieu["region"], lieu["pays"]) if x)
    return f"{lieu['nom']} — {precision}" if precision else lieu["nom"]


def choisir_lieu(candidats):
    """Montrer les homonymes trouvés et laisser choisir (Entrée = le premier)."""
    if len(candidats) == 1:
        print(f"        📍 {libelle_lieu(candidats[0])}")
        return candidats[0]
    for i, lieu in enumerate(candidats, start=1):          # start=1 : numéroter comme un humain
        print(f"        📍 {i}. {libelle_lieu(lieu)}")
    while True:
        reponse = input("        — lequel ? (Entrée = 1) : ")
        if reponse == "":
            return candidats[0]
        if reponse.isdigit() and 1 <= int(reponse) <= len(candidats):
            return candidats[int(reponse) - 1]               # choix 1 -> index 0
        print(f"        Choix invalide : entre un nombre entre 1 et {len(candidats)}.")


def question_proposition(p):
    """Formule la question d'une proposition d'ajustement (o/n, ou o/n/t pour un ajout)."""
    qui = "vous a manqué (partagé)" if p["personne"] == "Partagé" else f"a manqué à {p['personne']}"
    if p["type"] == "ajout":
        return f"   ➕ {p['source']} : « {p['objet']} » {qui}. L'ajouter ? (o / n / t = toujours) : "
    if p["type"] == "quantite":
        return (f"   ➖ {p['objet']} ({p['personne']}) : {p['actuelle']} prévus. {p['source']}, même climat : "
                f"{p['utilise']} utilisés. J'en mets {p['proposee']} ? (o/n) : ")
    return (f"   ➖ {p['objet']} ({p['personne']}) : {p['raison']} à {p['source']} (même climat). "
            f"Le retirer ? (o/n) : ")


def completer_coordonnees(itineraire, chercher=lieux):
    """Copie de l'itinéraire où chaque étape a ses coordonnées (nécessaires aux prévisions).

    Pour les voyages enregistrés avant qu'on les stocke : re-géocodage de la destination,
    en gardant le candidat du bon pays. Introuvable ou hors ligne : l'étape reste sans
    coordonnées (elle gardera ses normales de saison).
    """
    complete = []
    for etape in itineraire:
        etape = dict(etape)                          # copie : on ne touche pas à l'original
        if "latitude" not in etape:
            try:
                candidats = chercher(etape["destination"])
            except requests.RequestException:
                candidats = []
            bons = [c for c in candidats if c["code_pays"] == etape.get("code_pays")] or candidats
            if bons:
                etape["latitude"], etape["longitude"] = bons[0]["latitude"], bons[0]["longitude"]
        complete.append(etape)
    return complete


def fenetres_meteo(voyage, aujourd_hui):
    """Ce que le navigateur doit demander à Open-Meteo : une fenêtre par étape proche.

    Le serveur n'appelle pas Open-Meteo lui-même : les adresses partagées de Render prennent
    des 429 Too Many Requests. Il fournit l'URL complète ; le téléphone fait l'appel.
    """
    fenetres = []
    debut = voyage["depart"]
    for i, etape in enumerate(voyage["itineraire"]):
        fenetre = fenetre_prevision(debut, etape["jours"], aujourd_hui) if "latitude" in etape else None
        if fenetre:
            premier, dernier = fenetre
            fenetres.append({"etape": i, "destination": etape["destination"],
                             "debut": premier.isoformat(), "fin": dernier.isoformat(),
                             "url": url_prevision(etape["latitude"], etape["longitude"], premier, dernier)})
        debut += timedelta(days=etape["jours"])
    return fenetres


def appliquer_previsions(itineraire, depart, aujourd_hui, recues, erreurs):
    """Copie de l'itinéraire où chaque étape proche reçoit la prévision envoyée par le navigateur.

    recues  : {"<index d'étape>": bloc "daily" d'Open-Meteo, ou {"erreur": "raison"}}.
    erreurs : liste fournie par l'appelant, complétée des raisons à afficher.
    Les normales restent en réserve ; une prévision périmée (étape hors portée) est retirée ;
    en cas d'erreur, on garde ce qu'on avait.
    """
    nouveau = []
    debut = depart
    for i, etape in enumerate(itineraire):
        etape = dict(etape)
        attendue = "latitude" in etape and fenetre_prevision(debut, etape["jours"], aujourd_hui)
        recu = recues.get(str(i))
        if not attendue:
            etape.pop("prevision", None)
        elif not isinstance(recu, dict):
            erreurs.append(f"{etape['destination']} : aucune prévision reçue")
        elif "erreur" in recu:
            erreurs.append(f"{etape['destination']} : {str(recu['erreur'])[:120]}")
        else:
            try:                                        # données venues du navigateur : on vérifie
                n = normales_depuis_previsions(recu)
            except (KeyError, TypeError, ValueError, IndexError, ZeroDivisionError):
                erreurs.append(f"{etape['destination']} : prévision illisible")
            else:
                n["prevu_le"] = aujourd_hui.isoformat()
                etape["prevision"] = n
        nouveau.append(etape)
        debut += timedelta(days=etape["jours"])
    return nouveau


def construire(voyage):
    """Calculer la valise d'un voyage déjà saisi. Pure : ni input(), ni base, ni réseau.

    voyage = {"depart": date, "itineraire": [étapes], "personnes": [...],
              "conduit": bool, "lessive": int | None}
    Appelée par main() (terminal) et, demain, par le serveur (bouton météo, saisie en ligne).
    """
    itineraire = voyage["itineraire"]
    jours_types = jours_par_type(itineraire)
    total = total_jours(itineraire)
    prises = prises_itineraire(itineraire)
    hors_ue, inconnu = statut_ue_itineraire(itineraire)
    # prises_itineraire ignore déjà les "aucun" : vide = prises françaises partout
    valise = faire_valise(jours_types, total, voyage["personnes"], hors_ue, voyage["conduit"],
                          adaptateur=bool(prises), lessive_tous_les=voyage.get("lessive"))
    libelle = " › ".join(etape["destination"] for etape in itineraire)
    return {"valise": valise, "jours_types": jours_types, "total": total, "prises": prises,
            "libelle": libelle, "code": code_voyage(voyage["depart"], libelle),
            "ue_inconnu": inconnu}


def rendre_page(voyage, c):
    """La page HTML d'une construction (après d'éventuels ajustements de c["valise"])."""
    climats = [(e["destination"], e["mois"], climat_de(e)) for e in voyage["itineraire"]]
    return valise_en_html(c["valise"], c["libelle"], c["total"], c["prises"], climats,
                          code=c["code"], depart=voyage["depart"])


def fenetres_du_voyage(conn, code, aujourd_hui):
    """Bouton météo, temps 1 : les fenêtres à demander, ou None si le voyage est inconnu."""
    voyage = lire_voyage(conn, code)
    if voyage is None:
        return None
    voyage["itineraire"] = completer_coordonnees(voyage["itineraire"])
    return fenetres_meteo(voyage, aujourd_hui)


def actualiser_meteo(conn, code, aujourd_hui, recues):
    """Bouton météo, temps 2 : régénère le voyage avec les prévisions reçues du navigateur.

    Re-géocode si besoin, applique les prévisions, reconstruit, remet les règles "toujours",
    puis republie voyage + photo + page. Les propositions o/n des bilans restent au terminal.
    Renvoie {"etapes_prevues": n, "erreurs": [...]}, ou None si le voyage est inconnu.
    """
    voyage = lire_voyage(conn, code)
    if voyage is None:
        return None
    itineraire = completer_coordonnees(voyage["itineraire"])
    erreurs = []
    voyage["itineraire"] = appliquer_previsions(itineraire, voyage["depart"], aujourd_hui,
                                                recues, erreurs)
    c = construire(voyage)
    appliquer_regles(c["valise"], lire_regles(conn))
    enregistrer_voyage(conn, code, c["libelle"], voyage["depart"], voyage["personnes"],
                       voyage["itineraire"], c["jours_types"],
                       conduit=voyage["conduit"], lessive=voyage["lessive"])
    enregistrer_valise_objets(conn, code, c["valise"])
    publier_page(conn, rendre_page(voyage, c), cle=code)
    return {"etapes_prevues": sum("prevision" in e for e in voyage["itineraire"]), "erreurs": erreurs}


def valise_depuis_photo(photo, personnes):
    """La photo en base {(proprietaire, theme, objet): q} remise en valise d'affichage.

    Partagé d'abord, puis les voyageurs ; rayons dans l'ordre habituel (paquet_vide).
    """
    proprietaires = ["Partagé"] + list(personnes)
    proprietaires += sorted({p for p, _t, _o in photo} - set(proprietaires))
    valise = {p: paquet_vide() for p in proprietaires}
    for (p, theme, objet), quantite in photo.items():
        valise[p].setdefault(theme, {})[objet] = quantite
    return valise


def page_du_voyage(conn, code):
    """La page d'un voyage ; si aucune n'est stockée à son nom, refaite depuis la photo en base.

    La photo (ce qui a été réellement proposé) prime sur un recalcul : les règles ont pu
    changer depuis, et le bilan se fait par rapport à la photo. None si le voyage est inconnu.
    """
    html = lire_page(conn, code)
    if html is not None:
        return html
    voyage = lire_voyage(conn, code)
    if voyage is None:
        return None
    c = construire(voyage)
    photo = lire_valise_objets(conn, code)
    if photo:
        c["valise"] = valise_depuis_photo(photo, voyage["personnes"])
    else:
        appliquer_regles(c["valise"], lire_regles(conn))
    html = rendre_page(voyage, c)
    publier_page(conn, html, cle=code)
    return html


ACCUEIL_STYLE = """
section.liste h2 { font-size: .95rem; color: var(--doux); margin: 1.2rem 0 .5rem; }
a.voyage {
 display: block; background: var(--carte); border-radius: 14px; padding: .8rem 1rem; margin-bottom: .6rem;
 color: var(--texte); text-decoration: none; box-shadow: 0 1px 2px rgba(0,0,0,.06);
}
a.voyage strong { display: block; font-size: 1rem; }
a.voyage span { font-size: .85rem; color: var(--doux); }
p.vide { color: var(--doux); }
a.nouvelle { display: inline-block; padding: .55rem 1rem; border-radius: 999px; background: var(--accent);
             color: #fff; text-decoration: none; font-weight: 600; }
"""


def accueil_en_html(voyages, aujourd_hui):
    """Page d'accueil : les voyages à venir (le plus proche d'abord), puis les passés."""
    from urllib.parse import quote
    a_venir = [v for v in voyages if v["fin"] >= aujourd_hui]
    passes = sorted((v for v in voyages if v["fin"] < aujourd_hui), key=lambda v: v["depart"], reverse=True)

    def carte(v):
        return (f'<a class="voyage" href="?v={quote(v["code"])}"><strong>{v["libelle"]}</strong>'
                f'<span>{date_en_clair(v["depart"])} → {date_en_clair(v["fin"])} · '
                f'{" · ".join(v["personnes"])}</span></a>')

    corps = ""
    for titre, liste in [("À venir", a_venir), ("Passés", passes)]:
        if liste:
            corps += f'<section class="liste"><h2>{titre}</h2>{"".join(carte(v) for v in liste)}</section>'
    if not voyages:
        corps = '<p class="vide">Aucune valise pour l\'instant.</p>'
    return f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Nos valises</title>
<style>{HTML_STYLE}{ACCUEIL_STYLE}</style>
</head>
<body>
<h1>🧳 Nos valises</h1>
<p><a class="nouvelle" href="?nouvelle">➕ Nouvelle valise</a></p>
{corps}
</body>
</html>"""


# --- Création en ligne : le téléphone télécharge, le serveur interprète (Render prend des 429) ---

def lieux_depuis_reponse(reponse_json):
    """Réponse brute du géocodage (envoyée par le téléphone) -> un lieu par pays, avec libellé.

    Mêmes règles que le terminal (extraire_lieux + un_par_pays). Réponse farfelue -> [].
    """
    try:
        candidats = un_par_pays(extraire_lieux(reponse_json))
    except (AttributeError, TypeError, KeyError):
        return []
    return [{**lieu, "libelle": libelle_lieu(lieu)} for lieu in candidats]


def normales_ou_url(conn, latitude, longitude, mois):
    """Normales en cache -> {"normales": ...} ; sinon {"url": ...} : l'historique à télécharger."""
    n = lire_normales(conn, latitude, longitude, mois)
    return {"normales": n} if n is not None else {"url": url_archive(latitude, longitude)}


def normales_depuis_historique(conn, latitude, longitude, mois, daily):
    """L'historique envoyé par le téléphone -> 12 mois mis en cache ; renvoie le mois demandé.

    None si les données sont illisibles (elles viennent du navigateur : on vérifie).
    """
    try:
        par_mois = normales_par_mois(daily)
    except (KeyError, TypeError, ValueError, IndexError, ZeroDivisionError):
        return None
    if mois not in par_mois:
        return None
    return normales_avec_cache(conn, latitude, longitude, mois, chercher=lambda _la, _lo: par_mois)


# Fonctions JavaScript du formulaire de création (étape 3) : même découpage que la météo.
SCRIPT_RECHERCHE = """
function enJson(r) { if (!r.ok) throw new Error('erreur ' + r.status); return r.json(); }
function envoyer(url, corps) {
    return fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(corps) }).then(enJson);
}
function depuisOpenMeteo(url) {
    return fetch(url).then(function (r) {
        if (!r.ok) throw new Error(r.status + ' ' + (r.statusText || 'refus Open-Meteo'));
        return r.json();
    });
}
// Destination -> [{nom, region, pays, code_pays, latitude, longitude, libelle}], un lieu par pays
function chercherLieux(nom) {
    return fetch('api/lieux?nom=' + encodeURIComponent(nom)).then(enJson)
        .then(function (r) { return depuisOpenMeteo(r.url); })
        .then(function (reponse) { return envoyer('api/lieux', { reponse: reponse }); })
        .then(function (r) { return r.lieux; });
}
// Normales d'un lieu pour un mois : cache du serveur, sinon historique téléchargé par le téléphone
function normalesDe(lieu, mois) {
    const q = 'latitude=' + lieu.latitude + '&longitude=' + lieu.longitude + '&mois=' + mois;
    return fetch('api/normales?' + q).then(enJson).then(function (r) {
        if (r.normales) return r.normales;
        return depuisOpenMeteo(r.url).then(function (j) {
            return envoyer('api/normales', { latitude: lieu.latitude, longitude: lieu.longitude,
                                             mois: mois, daily: j.daily });
        }).then(function (r) { return r.normales; });
    });
}
"""


# --- Création en ligne, étape 3 : le formulaire ---

LIBELLES_ACTIVITE = {
    "ville": "🏙️ Ville", "plage": "🏖️ Plage", "montagne": "⛰️ Montagne / rando",
    "culte": "🛕 Lieux de culte", "snorkeling": "🤿 Snorkeling", "scooter": "🛵 Scooter / moto",
    "nature": "🦟 Nature / moustiques", "nuit": "🌙 Transport de nuit", "road trip": "🚗 Road trip",
}


def voyage_depuis_formulaire(corps):
    """Le formulaire envoyé par le téléphone -> voyage accepté par construire() (normales à None).

    Mêmes règles que le terminal. Données venues du navigateur : tout est vérifié,
    ValueError avec un message lisible sinon. Les mois sont calculés ici, pas par le téléphone.
    """
    if not isinstance(corps, dict):
        raise ValueError("formulaire vide")
    try:
        depart = date.fromisoformat(str(corps.get("depart")))
    except ValueError:
        raise ValueError("date de départ invalide") from None
    personnes = CHOIX_PERSONNE.get(corps.get("personnes"))
    if personnes is None:
        raise ValueError("qui part : Julien, Laetitia ou les deux")
    lessive = corps.get("lessive")
    if lessive is not None and (type(lessive) is not int or lessive < 1):
        raise ValueError("lessive : un nombre de jours positif, ou vide")
    etapes = corps.get("etapes")
    if not isinstance(etapes, list) or not etapes:
        raise ValueError("ajoute au moins une étape")
    connues = set(CHOIX_ACTIVITE.values())
    itineraire = []
    for n, e in enumerate(etapes, start=1):
        if not isinstance(e, dict):
            raise ValueError(f"étape {n} illisible")
        destination = str(e.get("destination") or "").strip()
        lat, lon = e.get("latitude"), e.get("longitude")
        if not destination or type(lat) not in (int, float) or type(lon) not in (int, float):
            raise ValueError(f"étape {n} : choisis une destination dans la liste")
        jours = e.get("jours")
        if type(jours) is not int or not 1 <= jours <= 365:
            raise ValueError(f"étape {n} : nombre de jours invalide")
        activites = e.get("activites") or []
        if not isinstance(activites, list) or not set(activites) <= connues:
            raise ValueError(f"étape {n} : activité inconnue")
        itineraire.append({"destination": destination, "jours": jours, "activites": sorted(set(activites)),
                           "normales": None, "code_pays": e.get("code_pays") or None,
                           "latitude": float(lat), "longitude": float(lon)})
    for etape, mois in zip(itineraire, mois_des_etapes(depart, [e["jours"] for e in itineraire])):
        etape["mois"] = mois
    return {"depart": depart, "itineraire": itineraire, "personnes": personnes,
            "conduit": bool(corps.get("conduit")), "lessive": lessive}


def creer_voyage(conn, corps):
    """Formulaire -> voyage créé et publié : {"code": ...}.

    Normales lues dans le cache ; s'il en manque (et sans "forcer"), renvoie
    {"manquantes": [...]} : le téléphone les télécharge (normalesDe) puis renvoie le formulaire.
    """
    voyage = voyage_depuis_formulaire(corps)
    manquantes = []
    for i, e in enumerate(voyage["itineraire"]):
        e["normales"] = lire_normales(conn, e["latitude"], e["longitude"], e["mois"])
        if e["normales"] is None:
            manquantes.append({"etape": i, "destination": e["destination"], "latitude": e["latitude"],
                               "longitude": e["longitude"], "mois": e["mois"]})
    if manquantes and not corps.get("forcer"):
        return {"manquantes": manquantes}
    c = construire(voyage)
    appliquer_regles(c["valise"], lire_regles(conn))
    enregistrer_voyage(conn, c["code"], c["libelle"], voyage["depart"], voyage["personnes"],
                       voyage["itineraire"], c["jours_types"],
                       conduit=voyage["conduit"], lessive=voyage["lessive"])
    enregistrer_valise_objets(conn, c["code"], c["valise"])
    publier_page(conn, rendre_page(voyage, c), cle=c["code"])
    return {"code": c["code"]}


FORMULAIRE_STYLE = """
[hidden] { display: none !important; }          /* sinon "form label { display: block }" l'emporte */
div.bloc { background: var(--carte); border-radius: 14px; padding: .8rem 1rem; margin-bottom: .6rem;
           box-shadow: 0 1px 2px rgba(0,0,0,.06); }
form label { display: block; margin: .45rem 0; }
form input[type=text], form input[type=date], form input[type=number] {
 font-size: 1rem; padding: .45rem .6rem; border: 1px solid var(--ligne); border-radius: 8px;
 background: var(--fond); color: var(--texte);
}
form input[type=number] { width: 4.5rem; }
fieldset { border: none; padding: 0; margin: .45rem 0; }
legend { font-weight: 600; padding: 0; }
fieldset label { display: inline-flex; gap: .3rem; margin-right: .9rem; }
.ligne { display: flex; gap: .4rem; margin-top: .25rem; }
.ligne input { flex: 1; min-width: 0; }
.entete { display: flex; justify-content: space-between; align-items: center; }
.entete button { border: none; background: none; color: var(--doux); font-size: 1rem; cursor: pointer; }
.lieux label.lieu { font-size: .9rem; margin: .25rem 0; }
.activites { display: flex; flex-wrap: wrap; gap: .35rem; margin-top: .4rem; }
.activites label { display: inline-flex; gap: .3rem; margin: 0; padding: .3rem .6rem; font-size: .85rem;
                   border: 1px solid var(--ligne); border-radius: 999px; }
.activites label:has(input:checked) { background: var(--accent-doux); border-color: var(--accent); }
button.principal { width: 100%; padding: .85rem; border: none; border-radius: 12px; background: var(--accent);
                   color: #fff; font-size: 1rem; font-weight: 600; cursor: pointer; }
button.principal:disabled { opacity: .6; }
#message { color: var(--doux); min-height: 1.2rem; }
"""

SCRIPT_FORMULAIRE = """
const etapes = document.getElementById('etapes');
const modele = document.getElementById('modele-etape');
const message = document.getElementById('message');
let compteur = 0;

function totalJours() {
    let total = 0;
    etapes.querySelectorAll('.jours').forEach(function (j) { total += parseInt(j.value, 10) || 0; });
    return total;
}
function majLessive() { document.getElementById('bloc-lessive').hidden = totalJours() <= 10; }
function numeroter() {
    etapes.querySelectorAll('.etape').forEach(function (e, i) { e.querySelector('.numero').textContent = 'Étape ' + (i + 1); });
    majLessive();
}

// Destination : recherche via le téléphone (chercherLieux), choix parmi les homonymes
function chercher(etape) {
    const nom = etape.querySelector('.destination').value.trim();
    const zone = etape.querySelector('.lieux');
    etape.lieu = null;
    if (!nom) return;
    zone.textContent = '⏳ Recherche…';
    chercherLieux(nom).then(function (lieux) {
        zone.textContent = '';
        if (!lieux.length) { zone.textContent = "❌ Introuvable : vérifie l'orthographe"; return; }
        lieux.forEach(function (lieu, i) {
            const label = document.createElement('label');
            label.className = 'lieu';
            const radio = document.createElement('input');
            radio.type = 'radio';
            radio.name = 'lieu-' + etape.id;
            radio.addEventListener('change', function () { etape.lieu = lieu; });
            if (i === 0) { radio.checked = true; etape.lieu = lieu; }     // le premier par défaut
            label.append(radio, ' 📍 ' + lieu.libelle);
            zone.append(label);
        });
    }).catch(function (e) { zone.textContent = '⚠️ Recherche impossible (' + e.message + ')'; });
}

function ajouterEtape() {
    const etape = modele.content.firstElementChild.cloneNode(true);
    etape.id = 'etape-' + (++compteur);
    etape.querySelector('.chercher').addEventListener('click', function () { chercher(etape); });
    etape.querySelector('.destination').addEventListener('keydown', function (ev) {
        if (ev.key === 'Enter') { ev.preventDefault(); chercher(etape); }
    });
    etape.querySelector('.jours').addEventListener('input', majLessive);
    etape.querySelector('.retirer').addEventListener('click', function () {
        if (etapes.children.length > 1) { etape.remove(); numeroter(); }
    });
    etapes.append(etape);
    numeroter();
}
document.getElementById('ajouter-etape').addEventListener('click', ajouterEtape);
ajouterEtape();

function lireFormulaire() {
    const corps = {
        depart: document.getElementById('depart').value,
        personnes: document.querySelector('input[name=personnes]:checked').value,
        conduit: document.getElementById('conduit').checked,
        lessive: null,
        etapes: [],
    };
    const lessive = parseInt(document.getElementById('lessive').value, 10);
    if (totalJours() > 10 && lessive > 0) corps.lessive = lessive;
    etapes.querySelectorAll('.etape').forEach(function (e) {
        const lieu = e.lieu || {};
        corps.etapes.push({
            destination: lieu.nom || e.querySelector('.destination').value,
            code_pays: lieu.code_pays || null,
            latitude: lieu.latitude !== undefined ? lieu.latitude : null,
            longitude: lieu.longitude !== undefined ? lieu.longitude : null,
            jours: parseInt(e.querySelector('.jours').value, 10),
            activites: Array.from(e.querySelectorAll('.activites input:checked')).map(function (c) { return c.value; }),
        });
    });
    return corps;
}
function envoyerVoyage(corps) {
    return fetch('api/voyages', { method: 'POST', headers: { 'Content-Type': 'application/json' },
                                  body: JSON.stringify(corps) })
        .then(function (r) { return r.json().then(function (j) { return { statut: r.status, corps: j }; }); });
}

// Envoi : le serveur dit s'il manque des normales ; le téléphone les télécharge puis renvoie
document.getElementById('creation').addEventListener('submit', function (ev) {
    ev.preventDefault();
    const bouton = document.getElementById('creer');
    const corps = lireFormulaire();
    bouton.disabled = true;
    message.textContent = '⏳ Création de la valise…';
    envoyerVoyage(corps).then(function (res) {
        if (res.statut !== 409) return res;
        message.textContent = '⏳ Climat de saison : téléchargement (' + res.corps.manquantes.length + ' étape(s))…';
        return Promise.all(res.corps.manquantes.map(function (m) {
            return normalesDe(m, m.mois).catch(function () { return null; });   // échec : climat inconnu
        })).then(function () { corps.forcer = true; return envoyerVoyage(corps); });
    }).then(function (res) {
        if (res.statut === 201) { location.href = res.corps.url; return; }
        bouton.disabled = false;
        message.textContent = '⚠️ ' + (res.corps.erreur || 'erreur ' + res.statut);
    }).catch(function (e) {
        bouton.disabled = false;
        message.textContent = '⚠️ Échec (' + e.message + '), réessaie';
    });
});
"""


def formulaire_en_html():
    """Page de création d'une valise : les questions du terminal, en formulaire."""
    cases = "".join(f'<label><input type="checkbox" value="{activite}"{" checked" if activite == "ville" else ""}>'
                    f'{LIBELLES_ACTIVITE[activite]}</label>' for activite in CHOIX_ACTIVITE.values())
    return f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Nouvelle valise</title>
<style>{HTML_STYLE}{FORMULAIRE_STYLE}</style>
</head>
<body>
<a class="retour" href="./">← Tous les voyages</a>
<h1>➕ Nouvelle valise</h1>
<form id="creation">
<div class="bloc">
<label>Date de départ<br><input type="date" id="depart" required></label>
<fieldset><legend>Qui part ?</legend>
<label><input type="radio" name="personnes" value="j">Julien</label>
<label><input type="radio" name="personnes" value="l">Laetitia</label>
<label><input type="radio" name="personnes" value="2" checked>Les deux</label>
</fieldset>
</div>
<div id="etapes"></div>
<p><button type="button" id="ajouter-etape" class="ctrl-btn">➕ Ajouter une étape</button></p>
<div class="bloc">
<label><input type="checkbox" id="conduit"> On conduit (voiture ou scooter)</label>
<label id="bloc-lessive" hidden>Lessive en route : tous les
<input type="number" id="lessive" min="1" inputmode="numeric"> jours (vide = pas de lessive)</label>
</div>
<p id="message"></p>
<button type="submit" id="creer" class="principal">Créer la valise</button>
</form>
<template id="modele-etape">
<div class="etape bloc">
<div class="entete"><strong class="numero"></strong><button type="button" class="retirer" title="Retirer l'étape">✕</button></div>
<label>Destination<span class="ligne"><input type="text" class="destination" placeholder="ex. Lisbonne"
 enterkeyhint="search"><button type="button" class="chercher ctrl-btn">Chercher</button></span></label>
<div class="lieux"></div>
<label>Jours <input type="number" class="jours" min="1" max="365" value="3" inputmode="numeric"></label>
<div class="activites">{cases}</div>
</div>
</template>
<script>{SCRIPT_RECHERCHE}</script>
<script>{SCRIPT_FORMULAIRE}</script>
</body>
</html>"""


def ajuster_selon_bilans(valise, jours_types, code):
    """Lit l'historique en base et pose les questions ; modifie la valise selon les réponses."""
    try:
        conn = connecter()
    except psycopg2.OperationalError:
        print("ℹ️  Base indisponible : pas d'ajustement d'après les bilans.")
        return
    try:
        regles = lire_regles(conn)
        for personne, objet in appliquer_regles(valise, regles):
            print(f"   ➕ {objet} ajouté pour {personne} (règle « toujours »)")
        props = propositions(valise, jours_types, lire_historique(conn, exclure=code), regles)
        if props:
            print(f"📒 D'après vos bilans précédents ({len(props)} proposition(s)) :")
        for p in props:
            reponse = input(question_proposition(p)).strip().lower()
            if est_oui(reponse) or (reponse == "t" and p["type"] == "ajout"):
                appliquer(valise, p)
            if reponse == "t" and p["type"] == "ajout":
                ajouter_regle(conn, p["personne"], p["objet"], p["theme"], 1)
    finally:
        conn.close()


def main():
    """Assistant interactif : saisit un itinéraire, puis construit la valise."""
    load_dotenv(Path(__file__).parent / ".env")   # DATABASE_URL éventuelle -> base en ligne
    manquants = objets_sans_rayon()
    if manquants:
        print(f"⚠️  Objets sans rayon (à classer dans THEMES) : {manquants}")

    try:
        conn = connecter()                # cache des normales ; facultatif
    except psycopg2.OperationalError:
        conn = None
        print("ℹ️  Postgres indisponible : climat interrogé en direct, sans cache.")

    # --- Date de départ : identifie le voyage et donne le mois de chaque étape ---
    while True:
        depart = lire_date(input("Date de départ (ex. 10/01/2027 ou 10 janv 2027) : "))
        if depart:
            break
        print("Date invalide : jour/mois/année, par exemple 10/01/2027.")
    debut_etape = depart

    # --- Saisie de l'itinéraire, étape par étape ---
    itineraire = []
    numero = 1
    while True:
        saisie = input(f"Étape {numero} — destination (ou 'fin' pour terminer) : ").strip()
        if saisie == "":
            continue
        if saisie.lower() == "fin":
            if itineraire:
                break
            print("Ajoute au moins une étape avant de terminer.")
            continue
        try:
            candidats = un_par_pays(lieux(saisie))   # le géocodage ignore déjà majuscules et accents
        except requests.RequestException:
            candidats = None
            print("        ⚠️  Pas de réseau : destination acceptée, pays et climat inconnus.")
        if candidats == []:
            print(f"Destination '{saisie}' introuvable, vérifie l'orthographe.")
            continue
        lieu = choisir_lieu(candidats) if candidats else None
        destination = lieu["nom"] if lieu else saisie    # "londres" tapé -> "Londres" affiché
        while True:
            reponse = input("        — jours : ").strip()
            if reponse.isdigit() and int(reponse) >= 1:
                jours = int(reponse)
                break
            print("        Nombre de jours invalide : entre un nombre positif.")
        mois = mois_des_etapes(debut_etape, [jours])[0]        # plus de question : calculé
        fin_etape = debut_etape + timedelta(days=jours - 1)
        print(f"        — du {date_en_clair(debut_etape)} au {date_en_clair(fin_etape)} ({MOIS[mois - 1]})")
        debut_etape += timedelta(days=jours)
        while True:
            print("        — activités : (v)ille (p)lage (m)ontagne/rando (t)emples/lieux de culte (s)norkeling")
            print("                      (k) scooter (j)ungle/moustiques (n)uit en transport (r)oad trip")
            activites = lire_activites(input("          lettres combinables (ex : vt) : "))
            if activites:
                break
            print("        Choix invalide : tape une ou plusieurs lettres de la liste (ex : vt).")
        n = None
        if lieu:
            try:
                n = normales_avec_cache(conn, lieu["latitude"], lieu["longitude"], mois)  # lieu CHOISI
            except requests.RequestException:
                pass
        print("        🌡️", ligne_climat(destination, mois, n))
        itineraire.append({"destination": destination, "jours": jours, "mois": mois,
                           "activites": activites, "normales": n,
                           "code_pays": lieu["code_pays"] if lieu else None,
                           **({"latitude": lieu["latitude"], "longitude": lieu["longitude"]} if lieu else {})})
        numero += 1

    if conn is not None:
        conn.close()                      # le cache n'est plus utile après la saisie

    # --- Questions posées une seule fois ---
    while True:
        choix = input("Qui fait sa valise ? (j = Julien / l = Laetitia / 2 = les deux) : ").strip().lower()
        if choix in CHOIX_PERSONNE:
            break
        print("Choix invalide : tape j, l ou 2.")
    personnes = CHOIX_PERSONNE[choix]

    if statut_ue_itineraire(itineraire)[1]:
        print("⚠️  Statut UE inconnu pour une étape : passeport par défaut, à vérifier.")
    conduit = est_oui(input("Tu vas conduire ? (o/n) : "))

    lessive = None
    if total_jours(itineraire) > SEUIL_LESSIVE:      # sur un voyage court, la question n'a pas d'intérêt
        lessive = lire_lessive(input("Lessive en route ? tous les combien de jours "
                                     "(Entrée = pas de lessive) : "))

    # --- Construction (sans terminal : la même fonction servira au serveur) ---
    voyage = {"depart": depart, "itineraire": itineraire, "personnes": personnes,
              "conduit": conduit, "lessive": lessive}
    c = construire(voyage)
    valise, jours_types, total, code = c["valise"], c["jours_types"], c["total"], c["code"]
    libelle_voyage = c["libelle"]

    # --- Apprentissage : règles "toujours", puis propositions tirées des bilans précédents ---
    ajuster_selon_bilans(valise, jours_types, code)

    html = rendre_page(voyage, c)
    with open("valise.html", "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Checklist écrite dans valise.html ({total} jours, {len(itineraire)} étape(s))")
    try:                                  # publication en base : c'est elle que le serveur affiche
        conn = connecter()
        enregistrer_voyage(conn, code, libelle_voyage, depart, personnes, itineraire, jours_types,
                           conduit=conduit, lessive=lessive)
        enregistrer_valise_objets(conn, code, valise)      # la photo : référence du futur bilan
        publier_page(conn, html, cle=code)                 # une page par voyage
        conn.close()
        print(f"Voyage mémorisé : {code}")
        ou = "en ligne" if os.environ.get("DATABASE_URL") else "sur le Mac"
        print(f"Checklist publiée dans la base ({ou}).")
    except psycopg2.OperationalError:
        print("ℹ️  Base indisponible : checklist non publiée (seul valise.html est à jour).")


if __name__ == "__main__":
    main()
