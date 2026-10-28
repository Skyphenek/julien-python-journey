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
from html import escape as echapper
from datetime import date, datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from urllib.parse import quote
import zoneinfo
from zoneinfo import ZoneInfo

import psycopg2
import requests

from api_climat import (lieux, normales_12_mois, fenetre_prevision, normales_depuis_previsions,
                        url_prevision, url_archive, extraire_lieux, normales_par_mois)
from db import (connecter, lire_normales, enregistrer_normales, publier_page,
                enregistrer_voyage, enregistrer_valise_objets, lire_voyage, lire_page,
                lire_valise_objets,
                lire_historique, lire_regles, ajouter_regle, lire_passeports, remplacer_voyage)
from dotenv import load_dotenv
from formalites import FORMALITES, DIPLOMATIE
from devises import DEVISE_PAR_PAYS
from urgences import URGENCES
from pwa import TETE_PWA, SCRIPT_PRECHARGEMENT, SCRIPT_FILE
from programme import etapes_du_voyage, bloc_programme, STYLE_PROGRAMME, SCRIPT_PROGRAMME
from vocabulaire import langues_du_voyage, bloc_vocabulaire, STYLE_VOCABULAIRE, SCRIPT_VOCABULAIRE
from a_voir import bloc_a_voir, STYLE_A_VOIR, SCRIPT_A_VOIR
from souvenirs import bloc_souvenirs, idees_du_voyage, STYLE_SOUVENIRS, SCRIPT_SOUVENIRS
from compte_a_rebours import compte_en_html, STYLE_COMPTE, SCRIPT_COMPTE
from design import STYLE_D, STYLE_EPURE, TETE_POLICE, ICONES_RUBRIQUE, STYLE_NAV_HUB, nav_hub

# Fuseaux horaires : toujours la base du paquet tzdata (version figée dans requirements.txt),
# jamais celle de la machine : celle de macOS ignorait encore le passage du Maroc à GMT
# (20/09/2026), celle de Render peut différer. Même résultat partout.
zoneinfo.reset_tzpath(to=[])

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

/* Hub : la page d'un voyage est découpée en rubriques (Valise, Avant, Sur place, Souvenirs) */
nav.rubriques { display: flex; gap: .2rem; margin: .3rem 0 .2rem; border-bottom: 1px solid var(--ligne); }
nav.rubriques button {
    flex: 1; padding: .55rem .2rem; border: none; border-bottom: 3px solid transparent; background: none;
    color: var(--doux); font-size: .85rem; font-weight: 600; cursor: pointer; white-space: nowrap;
}
nav.rubriques button.actif { color: var(--texte); border-bottom-color: var(--accent); }
nav.rubriques .compte-rubrique { font-size: .7rem; opacity: .75; }
div.rubrique p.vide { color: var(--doux); padding: 1rem .2rem; }
div.info { background: var(--carte); border-radius: 14px; padding: .8rem 1rem; margin: .6rem 0;
           box-shadow: 0 1px 2px rgba(0,0,0,.06); }
div.info h3 { font-size: 1rem; margin: 0 0 .5rem; }
div.info ul { list-style: none; padding: 0; margin: 0; }
div.info li { padding: .35rem 0; }
div.info .horloge { display: block; font-size: .8rem; color: var(--doux); font-variant-numeric: tabular-nums; }
div.info p.conseil { font-size: .85rem; color: var(--doux); margin: .5rem 0 0; }
div.urgences h4 { font-size: .9rem; margin: .5rem 0 .2rem; }
div.urgences h4 .source { font-weight: 400; font-size: .75rem; color: var(--accent); }
div.urgences li { font-size: .9rem; padding: .15rem 0; }
div.urgences li a { color: var(--accent); font-weight: 600; text-decoration: none; }
div.depenses form { display: flex; flex-wrap: wrap; gap: .4rem; align-items: center; margin: .4rem 0; font-size: .9rem; }
div.depenses form input[type=text], div.depenses form input[type=number], div.depenses form select {
    font-size: 1rem; padding: .35rem .5rem; border: 1px solid var(--ligne); border-radius: 8px;
    background: var(--fond); color: var(--texte); min-width: 0; }
div.depenses form input[name=libelle] { flex: 1 1 100%; }
div.depenses form input[name=montant] { width: 7rem; }
div.depenses .solde { font-weight: 600; margin: .2rem 0 .4rem; }
div.depenses .liste-depenses li { display: flex; gap: .5rem; align-items: baseline; border-top: 1px solid var(--ligne);
    font-size: .88rem; }
div.depenses .liste-depenses li span { flex: 1; overflow-wrap: anywhere; }
div.depenses .liste-depenses button { border: none; background: none; color: var(--doux); cursor: pointer; }
div.devises .taux { display: block; font-size: .8rem; color: var(--doux); font-variant-numeric: tabular-nums; }
div.devises .convertisseur { display: flex; align-items: center; gap: .3rem; margin-top: .3rem; font-size: .9rem; }
div.devises .convertisseur input { width: 7.5rem; min-width: 0; font-size: 1rem; padding: .35rem .5rem;
    border: 1px solid var(--ligne); border-radius: 8px; background: var(--fond); color: var(--texte); }
#bandeau-meteo { display: flex; gap: .5rem; align-items: flex-start; background: var(--accent-doux);
                 border-radius: 12px; padding: .6rem .8rem; margin: .4rem 0; font-size: .85rem; }
#bandeau-meteo[hidden] { display: none; }
#bandeau-meteo span { flex: 1; }
#bandeau-meteo button.fermer { border: none; background: none; color: var(--doux); cursor: pointer; font-size: 1rem; }

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
button.ctrl-btn, a.ctrl-btn {
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
/* Rayon « Avant de partir » : des tâches datées, pas des objets (pas de bilan) */
li.tache { flex-wrap: wrap; }
li.tache .echeance { font-size: .75rem; color: var(--doux); white-space: nowrap; font-variant-numeric: tabular-nums; }
li.tache a.source { font-size: .75rem; color: var(--accent); padding: 0 .5rem .5rem 2.6rem; }
li.retard:not(:has(input:checked)) .echeance { color: #dc2626; font-weight: 700; }
body.mode-bilan [data-owner="Avant de partir"] { display: none !important; }
a.ctrl-btn { display: inline-block; text-decoration: none; }
#hors-ligne { position: sticky; top: 0; z-index: 5; background: #fef3c7; color: #92400e; border-radius: 10px;
              padding: .4rem .75rem; margin-bottom: .75rem; font-size: .85rem; }
#hors-ligne[hidden] { display: none; }
"""

# Script JS de la page (persistance des coches). Dans une constante à part car le JS
# est plein d'accolades : il ne doit PAS traverser la f-string qui construit la page.
HTML_SCRIPT = """
// Références aux éléments de la page (tout en haut : dispo avant tout appel)
let sauvegarde = {};                                    // rempli après la réponse du serveur
const sections = document.querySelectorAll('section[data-owner]:not(.avant)');   // les onglets de la valise
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
                                : 'section[data-owner]:not(.avant) input[type=checkbox]';   // le total = la valise seule
        const boxes = document.querySelectorAll(selecteur);
        let faites = 0;
        boxes.forEach(function (b) { if (b.checked) faites++; });
        barre.querySelector('.barre-compte').textContent = faites + ' / ' + boxes.length;
        barre.querySelector('.progress-fill').style.width = boxes.length ? (faites / boxes.length * 100) + '%' : '0%';
    });
    if (typeof majRubriques === 'function') majRubriques();
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
    sections.forEach(function (s) { s.hidden = s.dataset.owner !== nom; });   // le serveur envoie déjà Partagé seul
    onglets.forEach(function (b) { b.classList.toggle('actif', b.dataset.owner === nom); });
    appliquerMasque();
}

""" + SCRIPT_FILE + """// La file appliquée par-dessus un état lu (serveur ou copie gardée) : ce qui attend gagne
function enAttente(url, voyage) {
    return lireFile().filter(function (e) { return e.url === url && (!voyage || (e.corps && e.corps.voyage === voyage)); });
}
function avecCochesEnAttente(etat) {
    enAttente('api/coche').forEach(function (e) {
        if (e.corps.coche) etat[e.corps.cle] = true; else delete etat[e.corps.cle];
    });
    return etat;
}
window.addEventListener('online', function () { majHorsLigne(); viderFile(); });
window.addEventListener('offline', majHorsLigne);
majHorsLigne();
viderFile();

// Sauvegarde d'une seule case sur le serveur (jamais tout l'état -> pas d'écrasement croisé)
const derniereModif = {};                              // clé -> instant du dernier clic sur CET appareil
function sauverCoche(cle, coche) {
    derniereModif[cle] = Date.now();
    envoyerOuGarder({ url: 'api/coche', methode: 'POST', corps: { cle: cle, coche: coche }, cle: 'coche:' + cle });
}

// Rafraîchissement automatique : relire l'état du serveur pour voir les cases cochées
// sur l'AUTRE téléphone. On ignore une case cliquée ici il y a moins de 5 s : sa
// sauvegarde peut ne pas être encore arrivée, on ne veut pas la "décocher" à l'écran.
function rafraichir() {
    if (document.hidden) return;                       // onglet en arrière-plan : on ne fait rien
    if (lireFile().length) viderFile();
    fetch('api/etat/' + encodeURIComponent(VOYAGE))
        .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
        .then(function (data) {
            data = avecCochesEnAttente(data);
            let change = false;
            document.querySelectorAll('input[type=checkbox][data-key]').forEach(function (box) {
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
    if (actif) ouvrirRubrique('valise');                  // le bilan porte sur la valise
    btnBilan.textContent = actif ? '✓ Terminer le bilan' : 'Bilan de fin de voyage';
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

// Rubriques du hub (Valise, Avant, Sur place, Souvenirs) : le serveur envoie Valise ouverte.
// Lien direct possible : ?v=<voyage>#avant
const rubriques = document.querySelectorAll('div.rubrique');
const boutonsRubrique = document.querySelectorAll('nav.rubriques button');
function ouvrirRubrique(nom) {
    rubriques.forEach(function (r) { r.hidden = r.dataset.rubrique !== nom; });
    boutonsRubrique.forEach(function (b) { b.classList.toggle('actif', b.dataset.rubrique === nom); });
    document.body.dataset.rubrique = nom;                  // la couleur de la rubrique (design D)
}
boutonsRubrique.forEach(function (b) {
    b.addEventListener('click', function () { ouvrirRubrique(b.dataset.rubrique); history.replaceState(null, '', '#' + b.dataset.rubrique); });
});
if (location.hash && document.querySelector('div.rubrique[data-rubrique="' + location.hash.slice(1) + '"]')) {
    ouvrirRubrique(location.hash.slice(1));
}
// Compteur de la rubrique Avant (tâches cochées / total)
function majRubriques() {
    const boxes = document.querySelectorAll('section.avant input[type=checkbox]');
    const span = document.querySelector('nav.rubriques .compte-rubrique');
    if (!span || !boxes.length) return;
    let faites = 0;
    boxes.forEach(function (b) { if (b.checked) faites++; });
    span.textContent = faites + '/' + boxes.length;
}

// Horloges de la rubrique Sur place : heure sur place et à Paris. Les décalages viennent des
// tables calculées par le serveur (data-horaire, data-paris) : la base de fuseaux du téléphone
// peut être périmée (ex. Maroc passé à GMT le 20/09/2026). Au-delà des tables : celle du téléphone.
function majHorloges() {
    const bloc = document.querySelector('div.decalage');
    if (!bloc) return;
    const maintenant = Date.now();
    const valide = maintenant < Number(bloc.dataset.jusqua);
    const heure = function (table, fuseau) {
        if (valide) {
            let minutes = null;
            JSON.parse(table).forEach(function (t) { if (t[0] <= maintenant) minutes = t[1]; });
            if (minutes !== null) {
                return new Intl.DateTimeFormat('fr-FR', { hour: '2-digit', minute: '2-digit', timeZone: 'UTC' })
                    .format(new Date(maintenant + minutes * 60000));
            }
        }
        return new Intl.DateTimeFormat('fr-FR', { hour: '2-digit', minute: '2-digit', timeZone: fuseau }).format(new Date());
    };
    document.querySelectorAll('li[data-fuseau]').forEach(function (li) {
        li.querySelector('.horloge').textContent = heure(li.dataset.horaire, li.dataset.fuseau);
        li.title = heure(bloc.dataset.paris, 'Europe/Paris') + ' à Paris';
    });
}
majHorloges();
setInterval(majHorloges, 30000);

// Dépenses partagées : saisie convertie en euros au moment même (taux gardés sur le téléphone),
// liste et solde calculés par le serveur (api/depenses). Texte saisi affiché en textContent.
const euros = new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' });
function jourLocal() {
    const d = new Date();
    return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0');
}
function afficherDepenses(res) {
    const bloc = document.querySelector('div.depenses');
    const s = res.solde, plusieurs = bloc.dataset.personnes.indexOf('|') !== -1;
    const prefixe = 'api/depenses/' + encodeURIComponent(VOYAGE) + '/';
    const retirees = lireFile().filter(function (e) { return e.methode === 'DELETE' && e.url.indexOf(prefixe) === 0; })
                               .map(function (e) { return e.url.slice(prefixe.length); });
    const ajoutees = enAttente('api/depenses', VOYAGE);
    const visibles = res.depenses.filter(function (d) { return retirees.indexOf(String(d.id)) === -1; })
        .concat(ajoutees.map(function (e) { return Object.assign({ attente: e.id }, e.corps); }));
    let texte = '';
    if (!visibles.length) texte = 'Aucune dépense pour l’instant.';
    else if (plusieurs) texte = s.remboursements.length
        ? s.remboursements.map(function (r) { return r.de + ' doit ' + euros.format(Number(r.montant)) + ' à ' + r.a; }).join(' · ')
        : 'Comptes à l’équilibre';
    if (ajoutees.length) texte += (texte ? ' · ' : '') + ajoutees.length + ' en attente de réseau (hors total)';
    bloc.querySelector('.total').textContent = euros.format(Number(s.total));
    bloc.querySelector('.solde').textContent = texte;
    const liste = bloc.querySelector('.liste-depenses');
    liste.replaceChildren();
    visibles.forEach(function (d) {
        const li = document.createElement('li'), quoi = document.createElement('span');
        const nom = document.createElement('strong'), detail = document.createElement('small'), combien = document.createElement('strong');
        quoi.className = 'quoi'; combien.className = 'combien';
        nom.textContent = d.libelle;
        let t = (d.attente ? 'en attente · ' : '') + d.jour.slice(8) + '/' + d.jour.slice(5, 7);
        if (plusieurs) {
            t += ' · ' + d.paye_par;
            if (d.pour.length < bloc.dataset.personnes.split('|').length) t += ' pour ' + d.pour.join(', ');
        }
        if (d.devise !== 'EUR') t += ' · ' + new Intl.NumberFormat('fr-FR').format(Number(d.montant)) + ' ' + d.devise;
        detail.textContent = t;
        combien.textContent = euros.format(Number(d.montant_eur));
        quoi.append(nom, detail);
        const suppr = document.createElement('button');
        suppr.type = 'button'; suppr.className = 'suppr'; suppr.textContent = '✕'; suppr.title = 'Supprimer';
        suppr.addEventListener('click', function () {
            if (!suppr.dataset.confirmer) { suppr.dataset.confirmer = '1'; suppr.textContent = 'Supprimer ?'; return; }
            if (d.attente) {                                   // jamais partie : on la retire de la file
                ecrireFile(lireFile().filter(function (e) { return e.id !== d.attente; }));
                chargerDepenses();
                return;
            }
            envoyerOuGarder({ url: prefixe + d.id, methode: 'DELETE' }).then(chargerDepenses, chargerDepenses);
        });
        li.append(quoi, combien, suppr);
        liste.append(li);
    });
}
function chargerDepenses() {
    if (!document.querySelector('div.depenses')) return;
    fetch('api/depenses/' + encodeURIComponent(VOYAGE), { headers: { 'X-Valise-Vite': '1' } })
        .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
        .then(afficherDepenses)
        .catch(function () { document.querySelector('div.depenses .solde').textContent = 'Dépenses indisponibles sans réseau.'; });
}
(function () {
    const form = document.querySelector('form.nouvelle-depense');
    if (!form) return;
    const message = document.querySelector('div.depenses .message-depense');
    const ouvrir = document.querySelector('div.depenses .ajouter-depense');
    function montrerFormulaire(oui) {                      // « + Ajouter » déplie la saisie, l'envoi la replie
        form.hidden = !oui; ouvrir.setAttribute('aria-expanded', String(oui));
        ouvrir.textContent = oui ? 'Fermer' : '+ Ajouter';
        if (oui) form.elements.libelle.focus();
    }
    ouvrir.addEventListener('click', function () { montrerFormulaire(form.hidden); });
    form.addEventListener('submit', function (ev) {
        ev.preventDefault();
        const devise = form.elements.devise.value, montant = Number(form.elements.montant.value);
        let enEuros = montant;
        if (devise !== 'EUR') {
            const taux = lireTauxGardes(), t = taux && taux.eur[devise.toLowerCase()];
            if (!t) { message.textContent = 'Pas de taux pour ' + devise + ' : saisis le montant en euros.'; return; }
            enEuros = montant / t;
        }
        const pour = Array.from(form.querySelectorAll('input[name=pour]:checked')).map(function (c) { return c.value; });
        if (!pour.length) { message.textContent = 'Coche au moins une personne.'; return; }
        const corps = { voyage: VOYAGE, libelle: form.elements.libelle.value.trim(), montant: montant.toFixed(2), devise: devise,
                        montant_eur: enEuros.toFixed(2), paye_par: form.elements.paye_par.value, pour: pour, jour: jourLocal() };
        message.textContent = '…';
        envoyerOuGarder({ url: 'api/depenses', methode: 'POST', corps: corps })
            .then(function (etat) {
                message.textContent = etat === 'attente' ? 'Gardée sur le téléphone : partira au retour du réseau' : '';
                form.elements.libelle.value = ''; form.elements.montant.value = ''; montrerFormulaire(false); chargerDepenses();
            })
            .catch(function () { message.textContent = 'Échec, réessaie (réseau ?)'; });
    });
    chargerDepenses();
    document.addEventListener('visibilitychange', function () { if (!document.hidden) chargerDepenses(); });
    document.addEventListener('file-videe', chargerDepenses);
})();

// Devises : taux du jour (euro -> devise) téléchargés par le téléphone une fois par jour,
// gardés pour le hors-ligne. Deux adresses de la même source, la seconde en secours.
const SOURCES_TAUX = ['https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/eur.json',
                      'https://latest.currency-api.pages.dev/v1/currencies/eur.json'];
function lireTauxGardes() {
    try { return JSON.parse(localStorage.getItem('taux-eur') || 'null'); } catch (e) { return null; }
}
function telechargerTaux(i) {
    if (i >= SOURCES_TAUX.length) return Promise.reject(new Error('taux injoignables'));
    return fetch(SOURCES_TAUX[i]).then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
        .catch(function () { return telechargerTaux(i + 1); });
}
function afficherTaux(taux) {
    const date = document.querySelector('div.devises .taux-date');
    if (!taux) { date.textContent = 'Pas de taux : ouvre la page une fois avec du réseau.'; return; }
    date.textContent = 'Taux moyens du ' + taux.date.slice(8) + '/' + taux.date.slice(5, 7) + ', indicatifs (hors frais de change).';
    document.querySelectorAll('div.devises li[data-devise]').forEach(function (li) {
        const code = li.dataset.devise, t = taux.eur[code.toLowerCase()];
        if (!t) { li.querySelector('.taux').textContent = '?'; return; }
        const f = new Intl.NumberFormat('fr-FR', { maximumFractionDigits: t >= 100 ? 0 : 2 });
        li.querySelector('.taux').textContent = f.format(t);
        const conv = document.querySelector('div.devises .convertisseur[data-devise="' + code + '"]');
        const local = conv.querySelector('.montant-local'), eur = conv.querySelector('.montant-eur');
        local.addEventListener('input', function () { eur.value = local.value === '' ? '' : (local.value / t).toFixed(2); });
        const decimales = t >= 100 ? 1 : 100;                    // pas de centimes de dong ou de riel
        eur.addEventListener('input', function () { local.value = eur.value === '' ? '' : Math.round(eur.value * t * decimales) / decimales; });
    });
}
(function () {
    if (!document.querySelector('div.devises')) return;
    const d = new Date();
    const jour = d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0');
    const gardes = lireTauxGardes();
    if (gardes && gardes.recu_le === jour) { afficherTaux(gardes); return; }
    telechargerTaux(0).then(function (j) {
        const taux = { recu_le: jour, date: j.date, eur: j.eur };
        try { localStorage.setItem('taux-eur', JSON.stringify(taux)); } catch (e) {}
        afficherTaux(taux);
    }).catch(function () { afficherTaux(gardes); });             // hors ligne : les derniers taux connus
})();

// Retirer le voyage : deux taps (pas de fenêtre de confirmation), puis retour à l'accueil.
// Le voyage est archivé, pas supprimé.
const btnRetirer = document.getElementById('retirer');
if (btnRetirer) btnRetirer.addEventListener('click', function () {
    if (!btnRetirer.dataset.confirmer) {
        btnRetirer.dataset.confirmer = '1';
        btnRetirer.textContent = 'Confirmer le retrait ?';
        setTimeout(function () { delete btnRetirer.dataset.confirmer; btnRetirer.textContent = 'Retirer'; }, 4000);
        return;
    }
    fetch('api/voyages/' + encodeURIComponent(VOYAGE) + '/archiver', { method: 'POST' })
        .then(function (r) { if (r.ok) location.href = 'vadrouille'; else btnRetirer.textContent = 'Échec, réessaie'; })
        .catch(function () { btnRetirer.textContent = 'Échec, réessaie'; });
});

// Échéances dépassées en rouge : calculé à l'ouverture, avec la date du téléphone
function marquerRetards() {
    const d = new Date();
    const auj = d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0');
    document.querySelectorAll('li.tache[data-quand]').forEach(function (li) {
        li.classList.toggle('retard', li.dataset.quand < auj);     // dates ISO : l'ordre alphabétique suffit
    });
}

// Tout ce qui dépend de `sauvegarde` : à lancer seulement une fois l'état reçu du serveur
function initialiser() {
    marquerRetards();
    document.querySelectorAll('input[type=checkbox][data-key]').forEach(function (box) {
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
        document.querySelectorAll('input[type=checkbox][data-key]').forEach(function (box) {
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
    // Onglet ouvert au chargement : le premier de la valise (« Avant de partir » reste à un tap)
    const premier = Array.from(onglets).find(function (b) { return !b.hasAttribute('data-avant'); }) || onglets[0];
    if (premier) activer(premier.dataset.owner);
    majOnglets();
    majProgression();

    initialiserBilan();
    setInterval(rafraichir, 4000);                     // toutes les 4 s
    document.addEventListener('visibilitychange', rafraichir);   // et dès qu'on revient sur la page
}

// Météo de J-10 à la fin du voyage : automatique à l'ouverture (une fois par jour et par
// téléphone, sauf si l'autre l'a déjà fait aujourd'hui), bouton pour la refaire à la main.
// Après le rechargement, un bandeau dit ce qui a changé dans la valise.
(function () {
    const btn = document.getElementById('meteo');
    const bandeau = document.getElementById('bandeau-meteo');
    function afficherBandeau(texte) {
        if (!bandeau) return;
        const span = document.createElement('span');
        span.textContent = texte;
        const fermer = document.createElement('button');
        fermer.type = 'button'; fermer.className = 'fermer'; fermer.textContent = '✕';
        fermer.addEventListener('click', function () { bandeau.hidden = true; });
        bandeau.replaceChildren(span, fermer);
        bandeau.hidden = false;
    }
    try {                                                              // message laissé avant le rechargement
        const message = sessionStorage.getItem('meteo-bandeau:' + VOYAGE);
        if (message) { sessionStorage.removeItem('meteo-bandeau:' + VOYAGE); afficherBandeau(message); }
    } catch (e) {}
    if (!btn || typeof DEPART === 'undefined') return;
    const d = new Date();
    const jour = d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0');
    const aujourdhui = new Date(new Date().toDateString());           // minuit local
    const ouverture = new Date(DEPART + 'T00:00:00');
    ouverture.setDate(ouverture.getDate() - 10);                      // en jours : insensible au changement d'heure
    const fermeture = new Date(FIN + 'T00:00:00');
    if (aujourdhui < ouverture || aujourdhui > fermeture) return;
    btn.hidden = false;

    function resume(res) {
        let texte = 'Prévisions du ' + jour.slice(8) + '/' + jour.slice(5, 7) + ' appliquées';
        const c = res.changements;
        if (c) {
            const parts = [];
            if (c.ajouts.length) parts.push('ajouté : ' + c.ajouts.join(', '));
            if (c.retraits.length) parts.push('retiré : ' + c.retraits.join(', '));
            if (c.quantites.length) parts.push('quantités : ' + c.quantites.join(', '));
            texte += parts.length ? ' — ' + parts.join(' ; ') : ' — valise inchangée';
        }
        return texte + (res.erreurs.length ? ' · ' + res.erreurs.join(' · ') : '');
    }

    function actualiser(auto) {
        btn.disabled = true;
        btn.textContent = 'Prévisions en cours…';
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
                if (res.etapes_prevues > 0) {                         // succès : bandeau après rechargement
                    try { sessionStorage.setItem('meteo-bandeau:' + VOYAGE, resume(res)); } catch (e) {}
                    btn.textContent = '' + res.etapes_prevues + ' étape(s) actualisée(s)';
                    setTimeout(function () { location.reload(); }, auto ? 0 : 800);
                    return;
                }
                btn.disabled = false;
                btn.textContent = 'Actualiser la météo';
                if (res.erreurs.length) afficherBandeau('Météo non actualisée : ' + res.erreurs.join(' · '));
                else if (!auto) afficherBandeau('ℹ️ Aucune étape à moins de 10 jours : normales de saison gardées');
            })
            .catch(function (e) {
                btn.disabled = false;
                btn.textContent = 'Actualiser la météo';
                afficherBandeau('Météo non actualisée (' + e.message + ') : réessaie avec le bouton');
            });
    }
    btn.addEventListener('click', function () { actualiser(false); });

    let tentee = null;
    try { tentee = localStorage.getItem('meteo-auto:' + VOYAGE); } catch (e) {}
    if (METEO_DU !== jour && tentee !== jour) {
        try { localStorage.setItem('meteo-auto:' + VOYAGE, jour); } catch (e) {}
        actualiser(true);
    }
})();

// Démarrage : on va chercher l'état de CE voyage sur le serveur, puis on initialise
fetch('api/etat/' + encodeURIComponent(VOYAGE), { headers: { 'X-Valise-Vite': '1' } })
    .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
    .then(function (data) {
        sauvegarde = avecCochesEnAttente(data);
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
        "répulsif moustiques", "sac transparent 1 L (liquides ≤ 100 ml)",
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
    return (debut + f"{round(n['tmin'])}–{round(n['tmax'])} °C · {n['jours_pluie']} j de pluie/mois, "
            f"dont {round(n['jours_forte_pluie'])} forts")


def puce_climat(destination, n):
    """Version courte pour l'en-tête de la checklist : 'Hanoï 14–21° · 3 j de forte pluie'."""
    if n is None:
        return f"{destination} ?"
    puce = f"{destination} {round(n['tmin'])}–{round(n['tmax'])}° · {round(n['jours_forte_pluie'])} j de forte pluie"
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
# Mode « bagage cabine seulement » (réglage du voyage)
PLAFOND_CABINE = 4                                     # au plus 4 de chaque vêtement / sous-vêtement
INTERDITS_CABINE = {"bâtons"}                          # refusés au contrôle de sûreté
SAC_LIQUIDES = "sac transparent 1 L (liquides ≤ 100 ml)"


def faire_valise(jours_types, total, personnes, hors_ue, conduit, adaptateur=True,
                 lessive_tous_les=None, cabine=False):
    """Construire la checklist {proprietaire: {theme: {objet: quantité}}}.

    - jours_types : {type de destination: jours cumulés} (couche d'agrégation).
    - total       : durée totale du voyage (dimensionne les objets de base).
    - personnes   : liste de personnes qui font leur valise.
    - hors_ue     : True -> passeport, False -> carte d'identité.
    - conduit     : True -> permis (+ permis international si hors_ue).
    - adaptateur  : False -> aucune étape n'en a besoin (prises françaises partout) : on le retire.
    - lessive_tous_les : None -> pas de lessive ; N -> vêtements et sous-vêtements prévus pour N jours.
    - cabine      : True -> bagage cabine seulement (plafond vêtements, liquides, interdits).
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

    # === CABINE : tout doit tenir dans un bagage cabine et passer le contrôle de sûreté ===
    if cabine:
        for proprietaire, paquet in valise.items():
            for objet in INTERDITS_CABINE:
                paquet[theme_de(objet)].pop(objet, None)
            if proprietaire == "Partagé":
                continue
            for rayon in RAYONS_LAVABLES:
                paquet[rayon] = {objet: min(q, PLAFOND_CABINE) for objet, q in paquet[rayon].items()}
            paquet["Chaussures"].pop("chaussures de rechange", None)    # une paire aux pieds suffit
        valise["Partagé"][theme_de(SAC_LIQUIDES)][SAC_LIQUIDES] = 1

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


# 10. AVANT DE PARTIR — tâches datées déduites des pays (visa, passeport, santé, assurance).
#     Rien pour un voyage en Europe (carte d'identité) ; règles par pays dans formalites.py.
PASSEPORT_PAR_DEFAUT = 6        # mois après le retour, pour un pays hors table (prudence)
ARIANE = "https://www.diplomatie.gouv.fr/fr/conseils-aux-voyageurs/"     # inscription au Fil d'Ariane
FRAICHEUR_FORMALITES = 180      # jours : au-delà, la fiche pays est signalée « à revérifier »
DELAIS = {"passeport": 60, "centre": 60, "visa": 30, "assurance": 14}   # jours avant le départ


def ajouter_mois(d, n):
    """d + n mois ; un 31 qui n'existe pas devient le dernier jour du mois (31/08 + 6 -> 28/02)."""
    mois = d.month - 1 + n
    annee, mois = d.year + mois // 12, mois % 12 + 1
    for jour in (d.day, 30, 29, 28):
        try:
            return date(annee, mois, jour)
        except ValueError:
            continue


def _tache(id_, quand, texte, lien=None, ok=False):
    """ok = déjà vérifiée par l'app (passeports valides) : jamais signalée en retard."""
    return {"id": id_, "quand": quand, "texte": texte, "lien": lien, "ok": ok}


def texte_passeports(limite, regle, passeports, personnes):
    """La tâche passeport : vérifiée si on connaît les dates d'expiration, générique sinon."""
    exige = f"{limite:%d/%m/%Y}"
    if not passeports or not personnes:
        return f"Passeports valides au moins jusqu'au {exige} ({regle})"
    trop_courts = [f"{p} (expire le {passeports[p]:%d/%m/%Y})"
                   for p in personnes if p in passeports and passeports[p] < limite]
    if trop_courts:
        return f"Passeport à renouveler : {', '.join(trop_courts)} — il faut au moins le {exige}"
    inconnus = [p for p in personnes if p not in passeports]
    connus = ", ".join(f"{p} jusqu'au {passeports[p]:%d/%m/%Y}" for p in personnes if p in passeports)
    if inconnus:
        return (f"Passeports valides au moins jusqu'au {exige} : {connus} ; "
                f"{', '.join(inconnus)} : date inconnue, à vérifier")
    return f"Passeports OK : {connus} (minimum exigé : {exige})"


def _tache_sante(fiches, avant):
    """Une seule tâche santé, seulement pour une zone tropicale (centre de vaccinations)."""
    concernees = [f for f in fiches if f["sante"] == "centre"]
    if not concernees:
        return None
    noms = ", ".join(f["pays"] for f in concernees)
    notes = "".join(f" — {f['pays']} : {f['sante_note']}" for f in concernees if f["sante_note"])
    return _tache("vaccins", avant(DELAIS["centre"]),
                  f"Consultation en centre de vaccinations internationales : vaccins, paludisme, "
                  f"dengue ({noms}){notes}", concernees[0]["page_sante"])


def _tache_visa(cle, f, jours, avant, suffixe):
    """Une démarche de visa à faire, ou None quand le séjour est sous l'exemption (rien à faire)."""
    exemption = f["sans_visa_jusqua"]
    if exemption and jours <= exemption:
        return None
    if f["visa"]:
        return _tache(f"visa-{cle}", avant(DELAIS["visa"]), f"{f['pays']} : visa — {f['visa']}{suffixe}",
                      f["visa_lien"] or f["entree"])
    return _tache(f"visa-{cle}", avant(DELAIS["visa"]),
                  f"{f['pays']} : {jours} j sur place dépasse l'exemption de {exemption} j — "
                  f"visa à demander, voir la fiche officielle{suffixe}", f["entree"])


def avant_de_partir(itineraire, depart, aujourd_hui, passeports=None, personnes=()):
    """Les tâches à faire avant le départ, triées par échéance. Fonction pure.

    Une tâche = {"id": stable (clé de la case cochée), "quand": date limite, "texte", "lien"}.
    passeports : {personne: date d'expiration} (table passeports) ; personnes : les voyageurs.
    """
    hors_ue = []                                     # [(code ou destination, étape)] dans l'ordre, sans doublon
    jours_par_pays = {}
    for etape in itineraire:
        if statut_ue(etape.get("code_pays")) == "ue":
            continue
        cle = etape.get("code_pays") or etape["destination"]
        if cle not in jours_par_pays:
            hors_ue.append((cle, etape))
        jours_par_pays[cle] = jours_par_pays.get(cle, 0) + etape["jours"]
    if not hors_ue:
        return []

    avant = lambda jours: depart - timedelta(days=jours)
    retour = depart + timedelta(days=total_jours(itineraire) - 1)
    connus = [FORMALITES[c] for c, _e in hors_ue if c in FORMALITES]

    # Passeport : la règle la plus exigeante de l'itinéraire (pays hors table -> 6 mois)
    mois = max(FORMALITES[c]["passeport_mois"] if c in FORMALITES else PASSEPORT_PAR_DEFAUT
               for c, _e in hors_ue)
    regle = f"{mois} mois après le retour" if mois else "valides pendant tout le séjour"
    texte = texte_passeports(ajouter_mois(retour, mois), regle, passeports, personnes)
    taches = [_tache("passeport", avant(DELAIS["passeport"]), texte, ok=texte.startswith("Passeports OK"))]

    sante = _tache_sante(connus, avant)
    if sante:
        taches.append(sante)
    # Fil d'Ariane et assurance : seulement là où ça compte (zones à risque, soins très chers, obligation)
    zones = [f"{f['pays']} : {f['ariane']}" for f in connus if f["ariane"]]
    if zones:
        taches.append(_tache("ariane", avant(7), "Fil d'Ariane (gratuit) si vous passez près de zones "
                                                 "déconseillées — " + " ; ".join(zones), ARIANE))
    precisions = [f["assurance"] for f in connus if f["assurance"]]
    if precisions:
        taches.append(_tache("assurance", avant(DELAIS["assurance"]),
                             "Assurance voyage : hospitalisation et rapatriement — " + " ; ".join(precisions)
                             + " (vérifie d'abord ce que couvre ta carte bancaire)"))

    for cle, etape in hors_ue:
        f = FORMALITES.get(cle)
        if f is None:
            taches.append(_tache(f"formalites-{cle}", avant(DELAIS["visa"]),
                                 f"{etape['destination']} ({cle}) : vérifier visa et santé sur France Diplomatie",
                                 DIPLOMATIE))
            continue
        a_reverifier = (aujourd_hui - f["verifie_le"]).days > FRAICHEUR_FORMALITES
        suffixe = f" — infos du {f['verifie_le']:%d/%m/%Y}, à revérifier" if a_reverifier else ""
        visa = _tache_visa(cle, f, jours_par_pays[cle], avant, suffixe)
        if visa:
            taches.append(visa)
        for jours_avant, id_, texte_pays, lien in f["taches"]:
            taches.append(_tache(f"{id_}-{cle}", avant(jours_avant), f"{f['pays']} : {texte_pays}{suffixe}",
                                 lien or f["entree"]))
    return sorted(taches, key=lambda t: t["quand"])


# Version des pages stockées en base. À INCRÉMENTER à chaque changement de la page (rendu, script,
# règles) : au prochain affichage, une page d'une autre version est refaite depuis la photo.
# 1 = avant le marqueur ; 2 = onglet Formalités (27/10/2026) ; 3 = boutons modifier / retirer ;
# 4 = puce « bagage cabine » ; 5 = onglet Formalités en dernier ; 6 = ouverte sur Partagé sans flash ;
# 7 = hub en rubriques ; 8 = décalage horaire dans Sur place ; 9 = météo automatique à J-10 ;
# 10 = horloges calculées depuis la base du serveur (pas celle du téléphone) ; 11 = devises ;
# 12 = « fermer la maison » dans Avant ; 13 = infos de chaque étape dans Sur place ;
# 14 = dépenses partagées ; 15 = urgences du pays ; 16 = PWA (hors ligne) ;
# 17 = carnet 🗓️ Programme (remplace les infos d'étapes) ; 18 = vocabulaire + Sur place réordonnée ;
# 19 = « 💡 À voir » dans le Programme ; 20 = 🎁 Souvenirs ; 21 = ⏳ compte à rebours ;
# 22 = Avant de partir : seulement ce qui compte (visa à faire, zone tropicale, Ariane, assurance) ;
# 23 = design D (une couleur par rubrique, onglets en bas, barre latérale sur ordinateur) ;
# 24 = finitions D : urgences en pastilles, tâches Avant en cartes.
# 25 = sans emojis ; Sur place épuré (tuiles heure/devise, carte Dépenses).
# 26 = l'app s'appelle « En Vadrouille » (Valise reste l'onglet bagages).
# 27 = icône « En Vadrouille » (V blanc, repère orange, fond turquoise).
# 28 = adresse de l'icône versionnée (?v=vadrouille) : sinon iOS et Safari gardent l'ancienne.
# 29 = Casa Binomerie (Aujourd'hui, Courses, Dîners) : jette les copies d'avant le hub.
VERSION_PAGE = 29

# Le hub : chaque page voyage est découpée en rubriques (la première est ouverte à l'arrivée).
RUBRIQUES = [("valise", "Valise"), ("avant", "Avant"), ("programme", "Programme"), ("sur-place", "Sur place"),
             ("souvenirs", "Souvenirs")]
A_VENIR = {"sur-place": "Rien à afficher pour ce voyage.",
           "souvenirs": "Rien à afficher pour ce voyage."}
MARQUE_VERSION = f'<meta name="valise-version" content="{VERSION_PAGE}">'


# --- Sur place : urgences du pays -----------------------------------------------------------
def lien_tel(numero):
    """« +84 24 3944 57 00 » -> « tel:+842439445700 » (un tap pour appeler)."""
    return "tel:" + "".join(c for c in numero if c.isdigit() or c == "+")


def urgences_du_voyage(itineraire):
    """[{"pays", "numeros", "ambassade", "autres", "lien"}], un par pays, dans l'ordre du voyage.

    Toute étape dans l'UE / Schengen partage une seule entrée « 112 » ; pays hors table : un
    renvoi vers France Diplomatie, sans numéro inventé.
    """
    vus, resultat = set(), []
    for etape in itineraire:
        code = etape.get("code_pays")
        if statut_ue(code) == "ue":
            cle = "UE"
            entree = {"pays": "Union européenne", "numeros": [("Urgences (toute l'UE)", "112")],
                      "ambassade": None, "autres": [], "lien": None}
        elif code in URGENCES:
            cle = code
            entree = {"pays": FORMALITES[code]["pays"], **URGENCES[code],
                      "lien": FORMALITES[code]["entree"].replace("entree-sejour", "contacts-utiles")}
        else:
            cle = code or etape["destination"]
            entree = {"pays": f"{etape['destination']} ({code or '?'})", "numeros": [], "ambassade": None,
                      "autres": [], "lien": DIPLOMATIE}
        if cle not in vus:
            vus.add(cle)
            resultat.append(entree)
    return resultat


def bloc_urgences(urgences):
    """Le bloc « Urgences » : une pastille par numéro (un tap appelle), l'ambassade en ligne
    d'appel, et le rappel de l'opposition bancaire."""
    def pastille(libelle, numero):
        return (f'<a class="pastille-urgence" href="{lien_tel(numero)}"><strong>{echapper(numero, quote=False)}</strong>'
                f'<span>{echapper(libelle, quote=False)}</span></a>')
    corps = ""
    for u in urgences:
        pastilles = "".join(pastille(l, n) for l, n in [*u["numeros"], *u["autres"]])
        a = u["ambassade"]
        ambassade = ""
        if a:
            adresse = f'<span>{echapper(a["adresse"], quote=False)}</span>'
            ambassade = (f'<a class="appel-ambassade" href="{lien_tel(a["telephone"])}">'
                         f'<span><strong>Ambassade de France ({echapper(a["ville"], quote=False)})</strong>{adresse}</span>'
                         f'<em>{a["telephone"]}</em></a>' if a["telephone"] else
                         f'<p class="appel-ambassade"><span><strong>Ambassade de France '
                         f'({echapper(a["ville"], quote=False)})</strong>{adresse}</span></p>')
        lien = f' <a class="source" href="{u["lien"]}" target="_blank" rel="noopener">contacts officiels ↗</a>' if u["lien"] else ""
        if not pastilles and not ambassade:
            ambassade = '<p class="conseil">Pas de numéros dans notre table : voir les contacts officiels.</p>'
        corps += (f'<h4>{echapper(u["pays"], quote=False)}{lien}</h4>'
                  f'{f"<div class=\"pastilles-urgence\">{pastilles}</div>" if pastilles else ""}{ambassade}')
    return (f'<div class="info urgences"><h3>Urgences</h3>{corps}'
            f'<p class="conseil">Carte perdue ou volée : appelle le numéro d\'opposition de ta banque '
            f'(dans son appli ou au dos de la carte), à noter avant de partir.</p></div>')


# --- Sur place : dépenses partagées --------------------------------------------------------
def _euros(centimes):
    return (Decimal(centimes) / 100).quantize(Decimal("0.01"))


def solde_depenses(depenses, personnes):
    """Qui a payé quoi, la part de chacun et les remboursements, calculés en centimes.

    depenses : [{"montant_eur", "paye_par", "pour"}]. Une dépense est partagée à parts égales
    entre les personnes de "pour" ; les centimes restants vont aux dernières de la liste.
    """
    paye, part = {p: 0 for p in personnes}, {p: 0 for p in personnes}
    for d in depenses:
        centimes = int((Decimal(d["montant_eur"]) * 100).to_integral_value(ROUND_HALF_UP))
        paye[d["paye_par"]] = paye.get(d["paye_par"], 0) + centimes
        base, reste = divmod(centimes, len(d["pour"]))
        for i, p in enumerate(d["pour"]):
            part[p] = part.get(p, 0) + base + (1 if i >= len(d["pour"]) - reste else 0)
    noms = list(dict.fromkeys(list(paye) + list(part)))
    net = {p: paye.get(p, 0) - part.get(p, 0) for p in noms}
    debiteurs = sorted(([p, -n] for p, n in net.items() if n < 0), key=lambda x: -x[1])
    crediteurs = sorted(([p, n] for p, n in net.items() if n > 0), key=lambda x: -x[1])
    remboursements = []
    while debiteurs and crediteurs:                      # le plus gros débiteur rembourse le plus gros créancier
        montant = min(debiteurs[0][1], crediteurs[0][1])
        remboursements.append({"de": debiteurs[0][0], "a": crediteurs[0][0], "montant": _euros(montant)})
        debiteurs[0][1] -= montant
        crediteurs[0][1] -= montant
        debiteurs = [d for d in debiteurs if d[1]]
        crediteurs = [c for c in crediteurs if c[1]]
    return {"total": _euros(sum(paye.values())),
            "par_personne": {p: {"paye": _euros(paye.get(p, 0)), "part": _euros(part.get(p, 0)),
                                 "net": _euros(net[p])} for p in noms},
            "remboursements": remboursements}


def bloc_depenses(personnes, devises):
    """Le bloc « Dépenses » : formulaire de saisie ; liste et solde remplis par le script."""
    options_devise = "".join(f'<option value="{d}">{d}</option>' for d in ["EUR", *devises])
    seul = len(personnes) == 1
    payeur = "".join(f'<option value="{echapper(p)}">{echapper(p, quote=False)}</option>' for p in personnes)
    pour = "".join(f'<label><input type="checkbox" name="pour" value="{echapper(p)}" checked> '
                   f'{echapper(p, quote=False)}</label>' for p in personnes)
    return (f'<div class="info depenses" data-personnes="{echapper("|".join(personnes))}">'
            f'<div class="resume-depenses"><div class="tete"><h3>Dépenses</h3>'
            f'<button type="button" class="ajouter-depense" aria-expanded="false">+ Ajouter</button></div>'
            f'<strong class="total"></strong><p class="solde"></p></div>'
            f'<form class="nouvelle-depense" hidden>'
            f'<input type="text" name="libelle" placeholder="ex. dîner, taxi" maxlength="120" required>'
            f'<span class="montant"><input type="number" name="montant" inputmode="decimal" min="0.01" step="0.01" '
            f'placeholder="montant" required><select name="devise">{options_devise}</select></span>'
            f'<span{" hidden" if seul else ""}>payé par <select name="paye_par">{payeur}</select> pour {pour}</span>'
            f'<button type="submit" class="principal">Ajouter la dépense</button></form>'
            f'<p class="message-depense"></p><ul class="liste-depenses"></ul></div>')


# --- Sur place : décalage horaire ---------------------------------------------------------
# Fuseau trouvé hors ligne depuis les coordonnées (timezonefinder) ; décalage calculé aux dates
# de l'étape (heure d'été de part et d'autre comprise).
REFERENCE_HORAIRE = "Europe/Paris"
SEUIL_CONSEIL_DECALAGE = 3      # heures : en dessous, pas de conseil contre le décalage
_trouveur_fuseau = None


def fuseau_de(etape):
    """Le fuseau IANA d'une étape (« Asia/Tokyo »), ou None sans coordonnées."""
    global _trouveur_fuseau
    if etape.get("latitude") is None or etape.get("longitude") is None:
        return None
    if _trouveur_fuseau is None:                      # chargé à la première demande seulement
        from timezonefinder import TimezoneFinder
        _trouveur_fuseau = TimezoneFinder()
    return _trouveur_fuseau.timezone_at(lat=etape["latitude"], lng=etape["longitude"])


def _decalage_heures(fuseau, jour):
    """Heures d'avance du fuseau sur Paris, le jour donné à midi local."""
    instant = datetime(jour.year, jour.month, jour.day, 12, tzinfo=ZoneInfo(fuseau))
    ecart = instant.utcoffset() - instant.astimezone(ZoneInfo(REFERENCE_HORAIRE)).utcoffset()
    return ecart.total_seconds() / 3600


def decalages(itineraire, depart):
    """[{"destinations", "heures", "fuseau"}] : étapes regroupées par décalage, dans l'ordre du voyage."""
    groupes, debut = {}, depart
    for etape in itineraire:
        fuseau = fuseau_de(etape)
        milieu = debut + timedelta(days=(etape["jours"] - 1) // 2)
        debut += timedelta(days=etape["jours"])
        if fuseau is None:
            continue
        heures = _decalage_heures(fuseau, milieu)
        groupe = groupes.setdefault(heures, {"destinations": [], "heures": heures, "fuseau": fuseau})
        groupe["destinations"].append(etape["destination"])
    return list(groupes.values())


def texte_decalage(heures):
    """6 -> « +6 h », -6 -> « −6 h », 4.5 -> « +4 h 30 », 0 -> « même heure qu'à Paris »."""
    if heures == 0:
        return "même heure qu'à Paris"
    signe = "+" if heures > 0 else "−"
    minutes = round(abs(heures) * 60)
    h, m = divmod(minutes, 60)
    return f"{signe}{h} h" + (f" {m:02d}" if m else "")


def conseil_decalage(heures):
    """Conseil contre le décalage horaire pour l'arrivée, ou None si le décalage est faible."""
    if heures >= SEUIL_CONSEIL_DECALAGE:
        return ("Vers l'est : couchez-vous 1 h plus tôt chaque soir les 2 ou 3 jours avant le départ, "
                "puis prenez la lumière du matin sur place.")
    if heures <= -SEUIL_CONSEIL_DECALAGE:
        return ("Vers l'ouest : couchez-vous 1 h plus tard les 2 ou 3 soirs avant le départ, "
                "et tenez jusqu'au soir local le jour de l'arrivée.")
    return None


HORIZON_HORLOGES = 400         # jours couverts par les tables horaires embarquées dans la page


def table_horaire(fuseau, depuis, jours=HORIZON_HORLOGES):
    """[[début en ms depuis 1970 (UTC), décalage en minutes], …] : l'heure légale du fuseau,
    à l'heure près, de `depuis` à `depuis + jours`. Les horloges de la page s'en servent au lieu
    de la base de fuseaux du téléphone, qui peut être périmée."""
    tz, utc = ZoneInfo(fuseau), ZoneInfo("UTC")
    instant = datetime(depuis.year, depuis.month, depuis.day, tzinfo=utc)
    table = []
    for _ in range(jours * 24):
        minutes = round(instant.astimezone(tz).utcoffset().total_seconds() / 60)
        if not table or table[-1][1] != minutes:
            table.append([int(instant.timestamp() * 1000), minutes])
        instant += timedelta(hours=1)
    return table


def bloc_decalage(groupes, jour):
    """Le bloc « Décalage horaire » de la rubrique Sur place (horloges remplies par le script)."""
    lignes = "".join(f'<li class="tuile" data-fuseau="{echapper(g["fuseau"])}" '
                     f'data-horaire="{json.dumps(table_horaire(g["fuseau"], jour))}">'
                     f'<span class="lieu">{echapper(", ".join(g["destinations"]), quote=False)}</span>'
                     f'<strong class="horloge"></strong>'
                     f'<span class="ecart">{texte_decalage(g["heures"])}{" / Paris" if g["heures"] else ""}</span></li>'
                     for g in groupes)
    conseil = conseil_decalage(groupes[0]["heures"])
    conseil = f'<p class="conseil">{conseil}</p>' if conseil else ""
    fin = int(datetime(jour.year, jour.month, jour.day, tzinfo=ZoneInfo("UTC")).timestamp() * 1000
              + HORIZON_HORLOGES * 86_400_000)
    return (f'<div class="info decalage" data-paris="{json.dumps(table_horaire(REFERENCE_HORAIRE, jour))}" '
            f'data-jusqua="{fin}"><h3>Décalage horaire</h3><ul>{lignes}</ul>{conseil}</div>')


# --- Sur place : devises -----------------------------------------------------------------
# La devise vient de la table CLDR (devises.py) ; les taux, du téléphone (currency-api, taux
# du jour, gardés pour le hors-ligne) : la page reste valable sans le serveur.
DEVISES_D_USAGE = {"KH": ("USD", "très utilisé sur place")}     # monnaie courante en plus de l'officielle


def devises_du_voyage(itineraire):
    """[{"devise", "destinations", "note"}] hors euro, dans l'ordre du voyage."""
    groupes = {}
    for etape in itineraire:
        pays = etape.get("code_pays")
        devises = [(DEVISE_PAR_PAYS.get(pays), None)]
        if pays in DEVISES_D_USAGE:
            devises.append(DEVISES_D_USAGE[pays])
        for devise, note in devises:
            if devise is None or devise == "EUR":
                continue
            groupe = groupes.setdefault(devise, {"devise": devise, "destinations": [], "note": note})
            if etape["destination"] not in groupe["destinations"]:
                groupe["destinations"].append(etape["destination"])
    return list(groupes.values())


def bloc_devises(devises):
    """Le bloc « Devises » : taux et convertisseur remplis par le script (données du téléphone)."""
    lignes = convertisseurs = ""
    for d in devises:
        note = f' <em>({echapper(d["note"], quote=False)})</em>' if d["note"] else ""
        lignes += (f'<li class="tuile" data-devise="{d["devise"]}"><span class="lieu">1 € =</span>'
                   f'<strong class="taux">…</strong>'
                   f'<span class="ecart">{d["devise"]} · {echapper(", ".join(d["destinations"]), quote=False)}{note}</span></li>')
        convertisseurs += (f'<div class="convertisseur" data-devise="{d["devise"]}">'
                           f'<input type="number" inputmode="decimal" min="0" class="montant-local" '
                           f'aria-label="Montant en {d["devise"]}" placeholder="{d["devise"]}">'
                           f'<span class="egal">=</span><input type="number" inputmode="decimal" min="0" '
                           f'class="montant-eur" aria-label="Montant en euros" placeholder="€"></div>')
    return (f'<div class="info devises"><h3>Devises</h3><ul>{lignes}</ul>{convertisseurs}'
            f'<p class="conseil taux-date"></p></div>')


# --- Avant : fermer la maison ---------------------------------------------------------------
# Générée selon la durée et la saison du voyage. Gaïa reste seule jusqu'à 3 jours ; au-delà,
# elle est gardée (la personne arrose aussi les plantes). Une gardienne dans l'immeuble : pas
# d'Opération Tranquillité Vacances ni de garde du courrier, on la prévient.
MARGE_CROQUETTES = 2                 # jours de provisions en plus de la durée du voyage
GARDE_GAIA_DES = 4                   # jours de voyage à partir desquels Gaïa est gardée
MOIS_CHAUFFAGE = {10, 11, 12, 1, 2, 3, 4}


def fermer_la_maison(total, depart):
    """Les tâches pour fermer l'appartement, triées par échéance (même format que avant_de_partir)."""
    avant = lambda jours: depart - timedelta(days=jours)
    retour = depart + timedelta(days=total - 1)
    taches = [
        _tache("gaia-provisions", avant(3), f"Gaïa : croquettes, eau, litière (gravier + sacs à litière) "
                                            f"et friandises pour "
                                            f"{total + MARGE_CROQUETTES} jours ({total} jours de voyage + "
                                            f"{MARGE_CROQUETTES} de marge)"),
        _tache("appareils", avant(0), "Débrancher box, télé et multiprises (sauf le frigo)"),
        _tache("poubelles", avant(0), "Sortir les poubelles"),
        _tache("fenetres", avant(0), "Fermer fenêtres et volets, porte à clé"),
    ]
    if total >= GARDE_GAIA_DES:
        taches += [
            _tache("gaia-garde", avant(14), "Gaïa : réserver sa garde (proche ou pet-sitter), avec "
                                            "l'arrosage des plantes ; clés et consignes"),
            _tache("gaia-fiche", avant(1), "Gaïa : fiche pour la personne qui la garde (repas, vétérinaire, "
                                            "arthrose : pas de caresses sur le dos ni les hanches, plantes)"),
            _tache("gardienne", avant(2), f"Prévenir la gardienne : absents du {depart:%d/%m} au {retour:%d/%m}, "
                                          f"courrier ; lui laisser un double des clés si besoin"),
            _tache("frigo", avant(1), "Vider le frigo des produits frais"),
        ]
    if depart.month in MOIS_CHAUFFAGE:
        taches.append(_tache("chauffage", avant(0), "Chauffage en mode absence (hors-gel)"))
    if total >= 7:
        taches.append(_tache("eau", avant(0), "Couper l'arrivée d'eau"))
    return sorted(taches, key=lambda t: t["quand"])


def rayon_taches(titre, icone, theme, taches, cle_voyage):
    """Un rayon de tâches datées : cases cochées comme les objets (même API), sans bilan."""
    rayon = (f'<details class="rayon avant" open><summary>'
             f'<span class="nom">{titre}</span><span class="compte"></span></summary><ul>')
    for t in taches:
        cle = f"{cle_voyage}/Partagé/{theme}/{t['id']}"
        lien = (f'<a class="source" href="{echapper(t["lien"])}" target="_blank" rel="noopener">source ↗</a>'
                if t["lien"] else "")
        quand = "" if t.get("ok") else f' data-quand="{t["quand"].isoformat()}"'    # vérifiée : pas de retard
        rayon += (f'<li class="tache{" ok" if t.get("ok") else ""}"{quand}>'
                  f'<label><input type="checkbox" data-key="{echapper(cle)}">'
                  f'<span class="nom">{echapper(t["texte"], quote=False)}</span>'
                  f'<span class="echeance" title="À faire avant le {t["quand"]:%d/%m}">'
                  f'<span class="avant-le">avant le </span>{t["quand"]:%d/%m}</span></label>{lien}</li>')
    return rayon + "</ul></details>"


def rayon_avant_de_partir(taches, cle_voyage):
    return rayon_taches("Avant de partir", "", "Avant de partir", taches, cle_voyage)


def valise_en_html(valise, libelle_voyage, total, prises, climats=None, code=None, depart=None,
                   taches=None, cabine=False, fuseaux=None, meteo_du=None, jour=None, devises=None,
                   maison=None, etapes=None, personnes=None, urgences=None, langues=None, a_voir=None,
                   souvenirs=None):
    """Construire la page HTML de la checklist pour l'itinéraire complet.

    climats : liste optionnelle de (destination, mois, normales) — une puce par étape.
    code    : identifiant stable du voyage (date + itinéraire) ; préfixe des cases cochées.
    depart  : date de départ, affichée dans le titre.
    taches  : tâches « Avant de partir » (avant_de_partir), dans leur propre onglet, en dernier.
    """
    cle_voyage = code or libelle_voyage
    quand = f" · départ le {date_en_clair(depart)}" if depart else ""
    a_rebours = (compte_en_html(depart, depart + timedelta(days=total - 1), jour or date.today(), etapes or [])
                 if depart else "")
    dates_js = ""                       # pour le bouton météo (affiché de J-10 à la fin du voyage)
    if depart:
        fin = depart + timedelta(days=total - 1)
        dates_js = f' const DEPART = "{depart.isoformat()}"; const FIN = "{fin.isoformat()}";'
    adaptateurs = ", ".join(sorted(prises)) if prises else "aucun"
    puces = f'<span class="puce">Adaptateur : {adaptateurs}</span>'
    if cabine:
        puces += f'<span class="puce" title="Vêtements plafonnés à {PLAFOND_CABINE}, liquides ≤ 100 ml">Bagage cabine</span>'
    for destination, mois, n in climats or []:
        # Puce courte à l'écran, phrase complète en info-bulle (title)
        puces += f'<span class="puce" title="{ligne_climat(destination, mois, n)}">{puce_climat(destination, n)}</span>'

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
    ouvert = next(iter(valise))             # Partagé : l'onglet ouvert dès l'arrivée de la page (pas de flash)
    for proprietaire in valise:
        actif = ' class="actif"' if proprietaire == ouvert else ""
        onglets += f'<button data-owner="{proprietaire}"{actif}>{proprietaire} <span class="tab-count"></span></button>'
    onglets += '</nav>'

    corps = ""
    for proprietaire, themes in valise.items():
        cache = "" if proprietaire == ouvert else " hidden"
        corps += f'<section data-owner="{proprietaire}"{cache}>'
        for theme, objets in themes.items():
            if not objets:
                continue
            corps += (f'<details class="rayon" open><summary>'
                      f'<span class="nom">{theme}</span><span class="compte"></span></summary><ul>')
            for objet, quantite in sorted(objets.items()):
                cle = f"{cle_voyage}/{proprietaire}/{theme}/{objet}"
                multi = " data-qte-multi" if quantite > 1 else ""       # "utilisé x / N" n'a de sens que si N > 1
                corps += (f'<li data-owner="{proprietaire}" data-objet="{objet}" data-qte="{quantite}"{multi}>'
                          f'<label><input type="checkbox" data-key="{cle}">'
                          f'<span class="nom">{objet}</span><span class="qte">×{quantite}</span></label>'
                          f'<div class="bilan">'
                          f'<button type="button" data-verdict="utile">utile</button>'
                          f'<button type="button" data-verdict="trop">en trop</button>'
                          f'<button type="button" data-verdict="pas_servi">pas servi</button>'
                          f'<span class="utilise">utilisé <input type="number" min="0" max="{quantite}" '
                          f'inputmode="numeric"> / {quantite}</span></div></li>')
            corps += "</ul></details>"
        titre = "Ce qui nous a manqué" if proprietaire == "Partagé" else f"Ce qui a manqué à {proprietaire}"
        corps += (f'<div class="manques" data-owner="{proprietaire}"><h3>{titre}</h3>'
                  f'<div class="puces-manque"></div>'
                  f'<form class="ajout-manque"><input type="text" placeholder="ex. bouchons d\'oreilles" '
                  f'enterkeyhint="done"><button type="submit">Ajouter</button></form></div>')
        corps += "</section>"

    # --- Les rubriques du hub ---
    contenus = {
        "valise": (f'<div class="collant">\n<div class="barres">{barres}</div>\n{onglets}\n'
                   f'<p id="bilan-compte"></p>\n</div>\n{corps}'),
        "avant": (f'<section data-owner="Avant de partir" class="avant">'
                  f'{rayon_avant_de_partir(taches, cle_voyage) if taches else ""}'
                  f'{rayon_taches("Fermer la maison", "", "Fermer la maison", maison, cle_voyage) if maison else ""}'
                  f'</section>' if taches or maison
                  else '<p class="vide">Rien à préparer pour ce voyage : la carte d\'identité suffit.</p>'),
        "programme": bloc_programme(etapes or []) + bloc_a_voir(a_voir or []),
        **{r: f'<p class="vide">{texte}</p>' for r, texte in A_VENIR.items()},
    }
    tuiles = ((bloc_decalage(fuseaux, jour or date.today()) if fuseaux else "")
              + (bloc_devises(devises) if devises else ""))
    blocs_sur_place = ((f'<div class="tuiles">{tuiles}</div>' if tuiles else "")
                       + (bloc_depenses(personnes, [d["devise"] for d in devises or []]) if personnes else "")
                       + (bloc_urgences(urgences) if urgences else "")
                       + bloc_vocabulaire(langues or []))
    if blocs_sur_place:
        contenus["sur-place"] = blocs_sur_place
    if personnes:
        contenus["souvenirs"] = bloc_souvenirs(personnes, [d["devise"] for d in devises or []],
                                               (souvenirs or {}).get("idees", []), (souvenirs or {}).get("douane", False))
    nav_rubriques = '<nav class="rubriques">'
    blocs = ""
    for i, (nom, libelle) in enumerate(RUBRIQUES):
        compte = ' <span class="compte-rubrique"></span>' if nom == "avant" and (taches or maison) else ""
        nav_rubriques += (f'<button data-rubrique="{nom}"{" class=\"actif\"" if i == 0 else ""}>'
                          f'<span class="icone-rubrique">{ICONES_RUBRIQUE[nom]}</span>{libelle}{compte}</button>')
        blocs += f'<div class="rubrique" data-rubrique="{nom}"{"" if i == 0 else " hidden"}>\n{contenus[nom]}\n</div>\n'
    nav_rubriques += '</nav>'

    page = f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
{MARQUE_VERSION}
<title>{libelle_voyage} · En Vadrouille</title>
{TETE_PWA}
{TETE_POLICE}
<style>{HTML_STYLE}{STYLE_PROGRAMME}{STYLE_A_VOIR}{STYLE_VOCABULAIRE}{STYLE_SOUVENIRS}{STYLE_COMPTE}{STYLE_D}{STYLE_EPURE}</style>
</head>
<body data-rubrique="{RUBRIQUES[0][0]}">
<header class="entete">
<a class="retour" href="vadrouille">← En Vadrouille</a>
<h1>{libelle_voyage} <span class="duree">{total} jours{quand}</span></h1>
{a_rebours}
<div class="puces">{puces}</div>
</header>
{nav_rubriques}
<main>
<div id="bandeau-meteo" hidden></div>
<div id="hors-ligne" hidden></div>
{blocs}<div class="controls"><button id="meteo" class="ctrl-btn" hidden>Actualiser la météo</button><a id="modifier" class="ctrl-btn" href="?modifier={quote(cle_voyage)}">Modifier</a><button id="retirer" class="ctrl-btn">Retirer</button><button id="mode-bilan" class="ctrl-btn">Bilan de fin de voyage</button><button id="toggle-masque" class="ctrl-btn">Masquer les rangés</button><button id="reset" class="ctrl-btn">Réinitialiser</button></div>
</main>
<script>const VOYAGE = {json.dumps(cle_voyage, ensure_ascii=False)};{dates_js} const METEO_DU = {json.dumps(meteo_du)};</script>
<script>{HTML_SCRIPT}</script>
<script>{SCRIPT_PROGRAMME}</script>
<script>{SCRIPT_VOCABULAIRE}</script>
<script>{SCRIPT_A_VOIR}</script>
<script>{SCRIPT_SOUVENIRS}</script>
<script>{SCRIPT_COMPTE}</script>
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
        return f"   + {p['source']} : « {p['objet']} » {qui}. L'ajouter ? (o / n / t = toujours) : "
    if p["type"] == "quantite":
        return (f"   {p['objet']} ({p['personne']}) : {p['actuelle']} prévus. {p['source']}, même climat : "
                f"{p['utilise']} utilisés. J'en mets {p['proposee']} ? (o/n) : ")
    return (f"   {p['objet']} ({p['personne']}) : {p['raison']} à {p['source']} (même climat). "
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
                          adaptateur=bool(prises), lessive_tous_les=voyage.get("lessive"),
                          cabine=voyage.get("cabine", False))
    libelle = " › ".join(etape["destination"] for etape in itineraire)
    return {"valise": valise, "jours_types": jours_types, "total": total, "prises": prises,
            "libelle": libelle, "code": code_voyage(voyage["depart"], libelle),
            "ue_inconnu": inconnu}


def rendre_page(voyage, c, aujourd_hui=None, passeports=None):
    """La page HTML d'une construction (après d'éventuels ajustements de c["valise"]).

    aujourd_hui : sert à signaler les fiches pays « à revérifier » (défaut : la date du jour).
    passeports  : {personne: date d'expiration}, pour vérifier la validité (sinon texte générique).
    """
    climats = [(e["destination"], e["mois"], climat_de(e)) for e in voyage["itineraire"]]
    taches = avant_de_partir(voyage["itineraire"], voyage["depart"], aujourd_hui or date.today(),
                             passeports=passeports, personnes=voyage["personnes"])
    return valise_en_html(c["valise"], c["libelle"], c["total"], c["prises"], climats,
                          code=c["code"], depart=voyage["depart"], taches=taches,
                          cabine=voyage.get("cabine", False),
                          fuseaux=decalages(voyage["itineraire"], voyage["depart"]),
                          meteo_du=max((e["prevision"].get("prevu_le") for e in voyage["itineraire"]
                                        if e.get("prevision")), default=None),
                          jour=aujourd_hui or date.today(),
                          devises=devises_du_voyage(voyage["itineraire"]),
                          maison=fermer_la_maison(c["total"], voyage["depart"]),
                          etapes=etapes_du_voyage(voyage["itineraire"], voyage["depart"]),
                          personnes=list(voyage["personnes"]),
                          urgences=urgences_du_voyage(voyage["itineraire"]),
                          langues=langues_du_voyage(voyage["itineraire"]),
                          a_voir=[dict(e, latitude=etape.get("latitude"), longitude=etape.get("longitude"))
                                  for e, etape in zip(etapes_du_voyage(voyage["itineraire"], voyage["depart"]),
                                                      voyage["itineraire"])],
                          souvenirs={"idees": idees_du_voyage([e.get("code_pays") for e in voyage["itineraire"]]),
                                     "douane": statut_ue_itineraire(voyage["itineraire"])[0]})


def fenetres_du_voyage(conn, code, aujourd_hui):
    """Bouton météo, temps 1 : les fenêtres à demander, ou None si le voyage est inconnu."""
    voyage = lire_voyage(conn, code)
    if voyage is None:
        return None
    voyage["itineraire"] = completer_coordonnees(voyage["itineraire"])
    return fenetres_meteo(voyage, aujourd_hui)


def difference_valises(avant, apres):
    """Ce que la météo a changé : photo d'avant {(proprietaire, theme, objet): q} contre la valise
    recalculée. {"ajouts", "retraits", "quantites"} (libellés triés), ou None sans photo d'avant."""
    if not avant:
        return None
    a = {(p, o): q for (p, _t, o), q in avant.items()}
    b = {(p, o): q for p, themes in apres.items() for objets in themes.values() for o, q in objets.items()}
    libelle = lambda p, o: o if p == "Partagé" else f"{o} ({p})"
    return {"ajouts": sorted(libelle(*k) for k in b.keys() - a.keys()),
            "retraits": sorted(libelle(*k) for k in a.keys() - b.keys()),
            "quantites": sorted(f"{libelle(*k)} : {a[k]} → {b[k]}" for k in a.keys() & b.keys() if a[k] != b[k])}


def actualiser_meteo(conn, code, aujourd_hui, recues):
    """Bouton météo, temps 2 : régénère le voyage avec les prévisions reçues du navigateur.

    Re-géocode si besoin, applique les prévisions, reconstruit, remet les règles "toujours",
    puis republie voyage + photo + page. Les propositions o/n des bilans restent au terminal.
    Renvoie {"etapes_prevues": n, "erreurs": [...], "changements": difference_valises(...)},
    ou None si le voyage est inconnu.
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
    avant = lire_valise_objets(conn, code)
    enregistrer_voyage(conn, code, c["libelle"], voyage["depart"], voyage["personnes"],
                       voyage["itineraire"], c["jours_types"],
                       conduit=voyage["conduit"], lessive=voyage["lessive"],
                       cabine=voyage.get("cabine", False))
    enregistrer_valise_objets(conn, code, c["valise"])
    publier_page(conn, rendre_page(voyage, c, passeports=lire_passeports(conn)), cle=code)
    return {"etapes_prevues": sum("prevision" in e for e in voyage["itineraire"]), "erreurs": erreurs,
            "changements": difference_valises(avant, c["valise"])}


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
    """La page d'un voyage ; refaite depuis la photo si elle manque ou date d'une autre version.

    None si le voyage est inconnu.
    """
    html = lire_page(conn, code)
    if html is not None and MARQUE_VERSION in html:
        return html
    return refaire_page(conn, code) or html          # voyage disparu : on sert quand même l'ancienne


def refaire_page(conn, code):
    """Refait et republie la page d'un voyage depuis sa photo en base.

    La photo (ce qui a été réellement proposé) prime sur un recalcul : les règles ont pu
    changer depuis, et le bilan se fait par rapport à la photo. Les cases cochées ne bougent
    pas (table etat_case). None si le voyage est inconnu.
    """
    voyage = lire_voyage(conn, code)
    if voyage is None:
        return None
    c = construire(voyage)
    photo = lire_valise_objets(conn, code)
    if photo:
        c["valise"] = valise_depuis_photo(photo, voyage["personnes"])
    else:
        appliquer_regles(c["valise"], lire_regles(conn))
    html = rendre_page(voyage, c, passeports=lire_passeports(conn))
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


# --- Carte de nos voyages (accueil) : Leaflet + fond OpenStreetMap, sans clé ---------------
LEAFLET = "https://unpkg.com/leaflet@1.9.4/dist/leaflet"
LEAFLET_JS_SRI = "sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo="    # empreintes vérifiées le 27/10/2026
LEAFLET_CSS_SRI = "sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY="

CARTE_STYLE = """
div.compteurs { color: var(--doux); font-size: .85rem; margin: .2rem 0 .6rem; }
div.compteurs strong { color: var(--texte); }
#carte { height: 240px; border-radius: 14px; margin-bottom: .4rem; z-index: 0; }
p.legende { font-size: .75rem; color: var(--doux); margin: 0 0 .6rem; }
p.legende .avenir { color: var(--accent); } p.legende .passe { color: #9ca3af; }
@media (prefers-color-scheme: dark) {     /* fond de carte sombre, comme le reste de l'app */
  #carte .leaflet-tile { filter: invert(1) hue-rotate(180deg) brightness(.95) contrast(.9); }
}
"""

SCRIPT_CARTE = """
(function () {
    const div = document.getElementById('carte');
    if (typeof L === 'undefined') { div.hidden = true; document.querySelector('p.legende').hidden = true; return; }  // hors ligne
    const accent = getComputedStyle(document.documentElement).getPropertyValue('--accent').trim() || '#4f46e5';
    const carte = L.map(div, { scrollWheelZoom: false });
    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                { maxZoom: 12, attribution: '© OpenStreetMap' }).addTo(carte);
    const bornes = [];
    POINTS.forEach(function (p) {
        const lien = document.createElement('a');                   // DOM, pas de HTML : noms saisis par nous
        lien.href = '?v=' + encodeURIComponent(p.code);
        lien.textContent = p.nom + ' — ' + p.voyage;
        L.circleMarker([p.lat, p.lon], { radius: 7, weight: 2, fillOpacity: .85,
                                         color: p.avenir ? accent : '#9ca3af' }).addTo(carte).bindPopup(lien);
        bornes.push([p.lat, p.lon]);
    });
    if (bornes.length === 1) carte.setView(bornes[0], 5);
    else carte.fitBounds(bornes, { padding: [24, 24], maxZoom: 6 });
})();
"""


def stats_voyages(voyages):
    """Compteurs par année de départ, la plus récente d'abord : voyages, jours, pays distincts."""
    par_annee = {}
    for v in voyages:
        a = par_annee.setdefault(v["depart"].year, {"voyages": 0, "jours": 0, "pays": set()})
        a["voyages"] += 1
        a["jours"] += sum(e.get("jours", 0) for e in v.get("etapes", []))
        a["pays"] |= {e["code_pays"] for e in v.get("etapes", []) if e.get("code_pays")}
    return [{"annee": annee, "voyages": a["voyages"], "jours": a["jours"], "pays": len(a["pays"])}
            for annee, a in sorted(par_annee.items(), reverse=True)]


def points_carte(voyages, aujourd_hui):
    """Une étape = un point (si elle a des coordonnées) ; à venir ou passé selon la fin du voyage."""
    return [{"nom": e["destination"], "lat": e["latitude"], "lon": e["longitude"],
             "voyage": v["libelle"], "code": v["code"], "avenir": v["fin"] >= aujourd_hui}
            for v in voyages for e in v.get("etapes", [])
            if e.get("latitude") is not None and e.get("longitude") is not None]


def carte_en_html(voyages, aujourd_hui):
    """Compteurs + carte (rien si aucune étape n'a de coordonnées). Renvoie (tête, corps)."""
    lignes = "<br>".join(f'<strong>{s["annee"]}</strong> : {s["voyages"]} voyage{"s" if s["voyages"] > 1 else ""}'
                         f' · {s["jours"]} jours · {s["pays"]} pays' for s in stats_voyages(voyages))
    compteurs = f'<div class="compteurs">{lignes}</div>' if lignes else ""
    points = points_carte(voyages, aujourd_hui)
    if not points:
        return "", compteurs
    tete = (f'<link rel="stylesheet" href="{LEAFLET}.css" integrity="{LEAFLET_CSS_SRI}" crossorigin="">'
            f'<script src="{LEAFLET}.js" integrity="{LEAFLET_JS_SRI}" crossorigin=""></script>')
    donnees = json.dumps(points, ensure_ascii=False).replace("</", "<\\/")
    corps = (f'{compteurs}<div id="carte" role="img" aria-label="Carte de nos voyages"></div>'
             f'<p class="legende"><span class="avenir">●</span> à venir · <span class="passe">●</span> passés</p>'
             f'<script>const POINTS = {donnees};{SCRIPT_CARTE}</script>')
    return tete, corps


def accueil_en_html(voyages, aujourd_hui):
    """Page d'accueil : les voyages à venir (le plus proche d'abord), puis les passés."""
    a_venir = [v for v in voyages if v["fin"] >= aujourd_hui]
    passes = sorted((v for v in voyages if v["fin"] < aujourd_hui), key=lambda v: v["depart"], reverse=True)

    def etapes(v):
        return etapes_du_voyage([e for e in v.get("etapes", []) if e.get("jours")], v["depart"])

    def carte(v):
        a_venir = " data-a-venir" if v["fin"] >= aujourd_hui else ""      # préchargé pour le hors-ligne
        compte = (compte_en_html(v["depart"], v["fin"], aujourd_hui, etapes(v), balise="span")
                  if a_venir else "")
        return (f'<a class="voyage" href="?v={quote(v["code"])}" data-code="{echapper(v["code"])}"{a_venir}>'
                f'<strong>{v["libelle"]}</strong>{compte}'
                f'<span>{date_en_clair(v["depart"])} → {date_en_clair(v["fin"])} · '
                f'{" · ".join(v["personnes"])}</span></a>')

    corps, prochain = "", ""
    if a_venir:                                     # le prochain voyage (ou celui en cours), en grand
        v = a_venir[0]
        prochain = (f'<div class="prochain"><a href="?v={quote(v["code"])}"><span class="titre">{v["libelle"]}</span>'
                  f'{compte_en_html(v["depart"], v["fin"], aujourd_hui, etapes(v), balise="span")}</a></div>')
    for titre, liste in [("À venir", a_venir), ("Passés", passes)]:
        if liste:
            corps += f'<section class="liste"><h2>{titre}</h2>{"".join(carte(v) for v in liste)}</section>'
    if not voyages:
        corps = '<p class="vide">Aucune valise pour l\'instant.</p>'
    tete_carte, carte = carte_en_html(voyages, aujourd_hui)
    return f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>En Vadrouille</title>
{TETE_PWA}
{TETE_POLICE}
<style>{HTML_STYLE}{ACCUEIL_STYLE}{CARTE_STYLE}{STYLE_COMPTE}{STYLE_D}{STYLE_NAV_HUB}</style>
{tete_carte}
</head>
<body class="accueil hub-page">
<h1>En Vadrouille</h1>
<p><a class="nouvelle" href="?nouvelle">+ Nouveau voyage</a></p>
{prochain}
{carte}
{corps}
{nav_hub("vadrouille")}
<script>{SCRIPT_PRECHARGEMENT}</script>
<script>{SCRIPT_COMPTE}</script>
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
    "ville": "Ville", "plage": "Plage", "montagne": "Montagne / rando",
    "culte": "Lieux de culte", "snorkeling": "Snorkeling", "scooter": "Scooter / moto",
    "nature": "Nature / moustiques", "nuit": "Transport de nuit", "road trip": "Road trip",
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
            "conduit": bool(corps.get("conduit")), "lessive": lessive, "cabine": corps.get("cabine") is True}


def creer_voyage(conn, corps):
    """Formulaire -> voyage créé et publié : {"code": ...}.

    Normales lues dans le cache ; s'il en manque (et sans "forcer"), renvoie
    {"manquantes": [...]} : le téléphone les télécharge (normalesDe) puis renvoie le formulaire.
    corps["remplace"] : code du voyage modifié ; si le code change (date, étapes), ses cases
    cochées et son bilan passent au nouveau, et l'ancien est archivé.
    """
    voyage = voyage_depuis_formulaire(corps)
    remplace = corps.get("remplace")
    if remplace is not None and (not isinstance(remplace, str) or lire_voyage(conn, remplace) is None):
        raise ValueError("voyage à modifier introuvable")
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
                       conduit=voyage["conduit"], lessive=voyage["lessive"],
                       cabine=voyage.get("cabine", False))
    enregistrer_valise_objets(conn, c["code"], c["valise"])
    publier_page(conn, rendre_page(voyage, c, passeports=lire_passeports(conn)), cle=c["code"])
    if remplace and remplace != c["code"]:
        remplacer_voyage(conn, remplace, c["code"])
    return {"code": c["code"]}


def formulaire_initial(voyage):
    """Un voyage en base -> les valeurs du formulaire de modification (lues par remplir() en JS)."""
    personnes = next(cle for cle, liste in CHOIX_PERSONNE.items() if liste == list(voyage["personnes"]))
    return {"remplace": voyage["code"], "depart": voyage["depart"].isoformat(), "personnes": personnes,
            "conduit": voyage["conduit"], "lessive": voyage["lessive"], "cabine": voyage.get("cabine", False),
            "etapes": [{"destination": e["destination"], "code_pays": e.get("code_pays"),
                        "latitude": e.get("latitude"), "longitude": e.get("longitude"),
                        "jours": e["jours"], "activites": e.get("activites", [])}
                       for e in voyage["itineraire"]]}


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
    zone.textContent = 'Recherche…';
    chercherLieux(nom).then(function (lieux) {
        zone.textContent = '';
        if (!lieux.length) { zone.textContent = "Introuvable : vérifie l'orthographe"; return; }
        lieux.forEach(function (lieu, i) {
            const label = document.createElement('label');
            label.className = 'lieu';
            const radio = document.createElement('input');
            radio.type = 'radio';
            radio.name = 'lieu-' + etape.id;
            radio.addEventListener('change', function () { etape.lieu = lieu; });
            if (i === 0) { radio.checked = true; etape.lieu = lieu; }     // le premier par défaut
            label.append(radio, ' ' + lieu.libelle);
            zone.append(label);
        });
    }).catch(function (e) { zone.textContent = 'Recherche impossible (' + e.message + ')'; });
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

// Modification : le formulaire reprend le voyage (INITIAL), lieux déjà choisis compris
function remplir(v) {
    document.getElementById('depart').value = v.depart;
    document.querySelector('input[name=personnes][value="' + v.personnes + '"]').checked = true;
    document.getElementById('conduit').checked = !!v.conduit;
    document.getElementById('cabine').checked = !!v.cabine;
    if (v.lessive) document.getElementById('lessive').value = v.lessive;
    v.etapes.forEach(function (e) {
        ajouterEtape();
        const etape = etapes.lastElementChild;
        etape.querySelector('.destination').value = e.destination;
        etape.querySelector('.jours').value = e.jours;
        etape.querySelectorAll('.activites input').forEach(function (c) { c.checked = e.activites.indexOf(c.value) !== -1; });
        if (e.latitude !== null && e.latitude !== undefined) {
            etape.lieu = { nom: e.destination, code_pays: e.code_pays, latitude: e.latitude, longitude: e.longitude };
            etape.querySelector('.lieux').textContent = '' + e.destination + ' (lieu actuel)';
        }
    });
    majLessive();
}
if (INITIAL) remplir(INITIAL); else ajouterEtape();

function lireFormulaire() {
    const corps = {
        depart: document.getElementById('depart').value,
        personnes: document.querySelector('input[name=personnes]:checked').value,
        conduit: document.getElementById('conduit').checked,
        cabine: document.getElementById('cabine').checked,
        lessive: null,
        etapes: [],
    };
    if (INITIAL) corps.remplace = INITIAL.remplace;
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
    message.textContent = INITIAL ? 'Enregistrement…' : 'Création du voyage…';
    envoyerVoyage(corps).then(function (res) {
        if (res.statut !== 409) return res;
        message.textContent = 'Climat de saison : téléchargement (' + res.corps.manquantes.length + ' étape(s))…';
        return Promise.all(res.corps.manquantes.map(function (m) {
            return normalesDe(m, m.mois).catch(function () { return null; });   // échec : climat inconnu
        })).then(function () { corps.forcer = true; return envoyerVoyage(corps); });
    }).then(function (res) {
        if (res.statut === 201) { location.href = res.corps.url; return; }
        bouton.disabled = false;
        message.textContent = '' + (res.corps.erreur || 'erreur ' + res.statut);
    }).catch(function (e) {
        bouton.disabled = false;
        message.textContent = 'Échec (' + e.message + '), réessaie';
    });
});
"""


def formulaire_en_html(voyage=None):
    """Page de création d'une valise : les questions du terminal, en formulaire.

    voyage : un voyage en base -> formulaire de modification, prérempli.
    """
    initial = formulaire_initial(voyage) if voyage else None
    titre = "Modifier le voyage" if voyage else "On part où ?"
    bouton = "Enregistrer les modifications" if voyage else "Créer la valise"
    donnees = json.dumps(initial, ensure_ascii=False).replace("</", "<\\/")
    cases = "".join(f'<label><input type="checkbox" value="{activite}"{" checked" if activite == "ville" else ""}>'
                    f'{LIBELLES_ACTIVITE[activite]}</label>' for activite in CHOIX_ACTIVITE.values())
    return f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{"Modifier le voyage" if voyage else "Nouveau voyage"} · En Vadrouille</title>
{TETE_PWA}
{TETE_POLICE}
<style>{HTML_STYLE}{FORMULAIRE_STYLE}{STYLE_D}</style>
</head>
<body class="formulaire">
<a class="retour" href="vadrouille">← En Vadrouille</a>
<h1>{titre}</h1>
<form id="creation">
<div class="bloc quand">
<label>Date de départ<br><input type="date" id="depart" required></label>
<fieldset><legend>Qui part ?</legend>
<label><input type="radio" name="personnes" value="j">Julien</label>
<label><input type="radio" name="personnes" value="l">Laetitia</label>
<label><input type="radio" name="personnes" value="2" checked>Les deux</label>
</fieldset>
</div>
<div id="etapes"></div>
<p><button type="button" id="ajouter-etape" class="ajouter-etape">+ Une étape</button></p>
<div class="bloc options">
<label><input type="checkbox" id="conduit"> On conduit (voiture ou scooter)</label>
<label><input type="checkbox" id="cabine"> Bagage cabine seulement</label>
<label id="bloc-lessive" hidden>Lessive en route : tous les
<input type="number" id="lessive" min="1" inputmode="numeric"> jours (vide = pas de lessive)</label>
</div>
<p id="message"></p>
<button type="submit" id="creer" class="principal">{bouton}</button>
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
<script>const INITIAL = {donnees};</script>
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
