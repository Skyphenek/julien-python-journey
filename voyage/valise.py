"""Générateur de checklist de valise — adapté au type de destination, à la durée
et à la personne (Julien / Laetitia).

Application Python des concepts Exercism : dicts, listes, boucles, conditions.
On sépare les DONNÉES (les 3 tables ci-dessous, remplies une fois) de la LOGIQUE
(la fonction faire_valise). Démarrage minimal : on enrichit au fil des voyages.
"""
import json
import unicodedata

import psycopg2
import requests

from api_climat import lieux, normales_12_mois
from db import connecter, lire_normales, enregistrer_normales

# Feuille de style de la checklist HTML (mobile-first). Fournie clé en main :
# c'est de la présentation, pas de la logique. Injectée telle quelle dans le <head>.
HTML_STYLE = """
:root { color-scheme: light dark; }
* { box-sizing: border-box; }
body {
    font-family: -apple-system, system-ui, sans-serif;
    max-width: 640px; margin: 0 auto; padding: 1rem;
    line-height: 1.5; background: #f7f7f8; color: #18181b;
}
h1 { font-size: 1.5rem; margin: 0 0 1.25rem; }
section {
    background: #fff; border-radius: 12px; padding: .75rem 1.25rem;
    margin-bottom: 1rem; box-shadow: 0 1px 3px rgba(0,0,0,.08);
}
section h2 { font-size: 1.2rem; margin: .5rem 0; }
section h3 {
    font-size: .75rem; text-transform: uppercase; letter-spacing: .05em;
    color: #71717a; margin: 1rem 0 .25rem;
}
ul { list-style: none; margin: 0; padding: 0; }
li label {
    display: flex; align-items: center; gap: .6rem;
    padding: .55rem .1rem; cursor: pointer; min-height: 44px;
}
li input { width: 22px; height: 22px; flex-shrink: 0; }
label:has(input:checked) { color: #a1a1aa; text-decoration: line-through; }

p.prise {
    background: #eef2ff; color: #3730a3; font-size: .95rem;
    padding: .55rem .9rem; border-radius: 10px; margin: 0 0 1.5rem;
}
ul.climat {
    list-style: none; background: #fffbeb; color: #92400e; font-size: .95rem;
    padding: .55rem .9rem; border-radius: 10px; margin: -1rem 0 1.5rem;
}
nav.tabs {
    display: flex; gap: .4rem; position: sticky; top: 0; z-index: 5;
    background: #f7f7f8; padding: .6rem 0; margin-bottom: .5rem;
}
nav.tabs button {
    flex: 1; padding: .6rem .4rem; border: none; border-radius: 10px;
    background: #e4e4e7; color: #52525b; font-size: .95rem; font-weight: 600;
    cursor: pointer;
}
nav.tabs button.actif { background: #4f46e5; color: #fff; }
nav.tabs .tab-count { font-size: .72rem; font-weight: 600; opacity: .7; }
div.progress { margin: 0 0 1.25rem; }
div.progress-head {
    display: flex; justify-content: space-between; font-size: .85rem;
    color: #71717a; margin-bottom: .35rem; font-weight: 600;
}
div.progress-track { height: 8px; border-radius: 999px; background: #e4e4e7; overflow: hidden; }
#progress-fill { height: 100%; width: 0; background: #4f46e5; border-radius: 999px; transition: width .3s ease; }
div.controls { display: flex; gap: .5rem; justify-content: flex-end; margin: 0 0 1rem; }
button.ctrl-btn {
    padding: .4rem .85rem;
    border: 1px solid #d4d4d8; border-radius: 999px; background: transparent;
    color: #52525b; font-size: .82rem; font-weight: 600; cursor: pointer;
}
@media (prefers-color-scheme: dark) {
    body { background: #18181b; color: #f4f4f5; }
    section { background: #27272a; box-shadow: none; }
    section h3 { color: #a1a1aa; }
    p.prise { background: #312e81; color: #e0e7ff; }
    ul.climat { background: #422006; color: #fde68a; }
    nav.tabs { background: #18181b; }
    nav.tabs button { background: #27272a; color: #a1a1aa; }
    nav.tabs button.actif { background: #6366f1; color: #fff; }
    div.progress-track { background: #27272a; }
    #progress-fill { background: #6366f1; }
    button.ctrl-btn { border-color: #3f3f46; color: #a1a1aa; }
}
"""

# Script JS de la page (persistance des coches). Dans une constante à part car le JS
# est plein d'accolades : il ne doit PAS traverser la f-string qui construit la page.
HTML_SCRIPT = """
// Références aux éléments de la page (tout en haut : dispo avant tout appel)
let sauvegarde = {};                                    // rempli après la réponse du serveur
const sections = document.querySelectorAll('section[data-owner]');
const onglets = document.querySelectorAll('nav.tabs button');
const compte = document.getElementById('compte');
const remplissage = document.getElementById('progress-fill');
const btnMasque = document.getElementById('toggle-masque');
const btnReset = document.getElementById('reset');
let ownerActif = null;                                  // la personne actuellement affichée
let masquer = false;                                    // masquer les objets déjà rangés ?

// Progression DE LA PERSONNE AFFICHÉE (compte ses cases à elle)
function majProgression() {
    const boxes = document.querySelectorAll('section[data-owner="' + ownerActif + '"] input[type=checkbox]');
    let faites = 0;
    boxes.forEach(function (b) { if (b.checked) faites++; });
    compte.textContent = faites + ' / ' + boxes.length;
    remplissage.style.width = boxes.length ? (faites / boxes.length * 100) + '%' : '0%';
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
    document.querySelectorAll('section[data-owner] ul').forEach(function (ul) {
        const visible = Array.from(ul.querySelectorAll('li')).some(function (li) { return li.style.display !== 'none'; });
        ul.style.display = visible ? '' : 'none';
        const h3 = ul.previousElementSibling;         // le titre du rayon, juste avant la liste
        if (h3 && h3.tagName === 'H3') h3.style.display = visible ? '' : 'none';
    });
}

// Onglets : n'afficher qu'une personne à la fois
function activer(nom) {
    ownerActif = nom;
    sections.forEach(function (s) { s.style.display = (s.dataset.owner === nom) ? '' : 'none'; });
    onglets.forEach(function (b) { b.classList.toggle('actif', b.dataset.owner === nom); });
    majProgression();      // recompter pour la personne affichée
    appliquerMasque();
}

// Sauvegarde d'une seule case sur le serveur (jamais tout l'état -> pas d'écrasement croisé)
function sauverCoche(cle, coche) {
    fetch('/api/coche', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cle: cle, coche: coche })
    });
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
        majProgression();
        appliquerMasque();
    });

    if (onglets.length) activer(onglets[0].dataset.owner);
    majOnglets();
}

// Démarrage : on va chercher l'état de CE voyage sur le serveur, puis on initialise
fetch('/api/etat/' + encodeURIComponent(VOYAGE))
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
    "chaud": {"crème solaire": 1, "biafine": 1},
    "plage": {"crème solaire": 1, "biafine": 1},
    "pluie": {"parapluie": 1},
}

# 2b. PAR TYPE — PERSO : chacun le sien (tout ce qui se porte).
PAR_TYPE_PERSO = {
    "chaud":    {"chapeau": 1, "lunettes de soleil": "par_semaine",
                 "shorts": "par_3_jours", "sandales": 1,
                 "chemises légères": "par_3_jours",
                 "chemises": 0},                 # 0 = retire les chemises normales quand il fait chaud
                                                 # hauts/robes : gérés par personne (voir PAR_PERSONNE) pour éviter les doublons
    "frais":    {"pull": 1},                     # soirées fraîches (min < 15 °C) sans être "froid"
    "froid":    {"manteau": 1, "pull": "par_3_jours", "gants": 1, "bonnet": 1,
                 "écharpe": 1, "sous-couche thermique": "par_3_jours",
                 "grosses chaussures": 1, "collants": "par_3_jours"},
    "plage":    {"maillot de bain": "par_3_jours", "tongs": 1, "futa": 1,
                 "shorts": "par_3_jours", "sandales": 1, "lunettes de soleil": 1},
    "montagne": {"chaussures rando": 1, "gourde": 1, "coupe-vent": 1, "polaire": 1,
                 "chaussettes de rando": "par_3_jours", "bâtons": 1},
    "ville":    {"tenue habillée": 1, "baskets": 1},
    "pluie":    {"imperméable": 1, "chaussures imperméables": 1},
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
    "Julien": {"collants", "sandales"},
}

# 3ter. RÉGLAGES EN PAYS CHAUD, PAR PERSONNE : dès qu'un climat "chaud" est présent,
#       on écrase la garde-robe de base par personne (le SEUL endroit qui peut RÉDUIRE :
#       _remplir prend le max base/climat, donc ne sait qu'augmenter). Valeur 0 = retrait.
#       Absent de la table -> comportement par défaut (valeurs de base). Post-traité
#       dans faire_valise. Sert aux chaussures ouvertes ET aux tenues du soir de Laetitia :
#       1 tenue / 3 j (par_3_jours), soit robe SOIT chemise + bas ; préférence chemise.
#       Pour 15 j : 2 robes + 3 chemises = 5 tenues ; bas = 3 short habillé + 2 pantalons.
CHAUD_PERSO = {
    "Julien":   {"chaussettes": (3, "par_semaine")},   # 3 paires / semaine (chaussures fermées légères)
    "Laetitia": {
        "chaussettes": 0,                  # aucune : que des chaussures ouvertes
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
CHOIX_ACTIVITE = {"v": "ville", "p": "plage", "m": "montagne"}

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
    },
    "Sous-vêtements": {
        "caleçons", "culottes", "soutien-gorge", "chaussettes",
        "chaussettes de rando", "collants", "sous-couche thermique",
    },
    "Chaussures": {
        "chaussures de rechange", "sandales", "tongs", "grosses chaussures",
        "chaussures rando", "baskets", "chaussures imperméables",
    },
    "Accessoires": {
        "ceinture", "chapeau", "lunettes de soleil", "gants", "bonnet",
        "écharpe", "bijoux", "boucles d'oreille", "montre", "futa",
    },
    "Hygiène": {
        "trousse toilette", "déodorant", "rasoir", "maquillage", "lisseur",
        "démaquillant", "crème solaire", "biafine", "trousse pharmacie",
    },
    "Tech": {
        "chargeur", "adaptateur de prise",
    },
    "Documents": {
        "passeport", "carte d'identité", "permis", "permis international",
    },
    "Divers": {
        "sac de jour", "livre / liseuse", "parapluie", "gourde", "bâtons",
    },
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
        types.append("pluie")
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

def types_pour(etape):
    """Types d'une étape = climat (déduit des normales) + activités (saisies par l'utilisateur)."""
    return types_climat(etape.get("normales")) + etape.get("activites", [])

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


def faire_valise(jours_types, total, personnes, hors_ue, conduit):
    """Construire la checklist {proprietaire: {theme: {objet: quantité}}}.

    - jours_types : {type de destination: jours cumulés} (couche d'agrégation).
    - total       : durée totale du voyage (dimensionne les objets de base).
    - personnes   : liste de personnes qui font leur valise.
    - hors_ue     : True -> passeport, False -> carte d'identité.
    - conduit     : True -> permis (+ permis international si hors_ue).
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
        # documents personnels (chacun les siens)
        if hors_ue:
            paquet[theme_de("passeport")]["passeport"] = 1
        else:
            paquet[theme_de("carte d'identité")]["carte d'identité"] = 1
        if conduit and personne in CONDUCTEURS:
            paquet[theme_de("permis")]["permis"] = 1
            if hors_ue:
                paquet[theme_de("permis international")]["permis international"] = 1

    return valise

def valise_en_html(valise, libelle_voyage, total, prises, climats=None):
    """Construire la page HTML de la checklist pour l'itinéraire complet.

    climats : liste optionnelle de (destination, mois, normales) — une ligne par étape.
    """
    adaptateurs = ", ".join(sorted(prises)) if prises else "aucun"
    bandeau_climat = ""
    if climats:
        bandeau_climat = '<ul class="climat">'
        for destination, mois, n in climats:
            bandeau_climat += f"<li>🌡️ {ligne_climat(destination, mois, n)}</li>"
        bandeau_climat += "</ul>"
    onglets = '<nav class="tabs">'          # un bouton par propriétaire (Partagé/Julien/...)
    for proprietaire in valise:
        onglets += f'<button data-owner="{proprietaire}">{proprietaire} <span class="tab-count"></span></button>'
    onglets += '</nav>'
    corps = ""
    for proprietaire, themes in valise.items():
        corps = corps + f'<section data-owner="{proprietaire}"><h2>{proprietaire}</h2>'
        for theme, objets in themes.items():
            if not objets:
                continue
            corps = corps + f"<h3>{theme}</h3><ul>"
            for objet, quantite in sorted(objets.items()):
                corps = corps + f'<li><label><input type="checkbox" data-key="{libelle_voyage}/{proprietaire}/{theme}/{objet}"> {objet} ×{quantite}</label></li>'
            corps = corps + "</ul>"
        corps = corps + "</section>"
    page = f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Valise — {libelle_voyage}</title>
<style>{HTML_STYLE}</style>
</head>
<body>
<h1>Valise — {libelle_voyage} · {total} jours</h1>
<p class="prise">🔌 Adaptateur(s) à emporter : <strong>{adaptateurs}</strong></p>
{bandeau_climat}
<div class="progress"><div class="progress-head"><span>Rangé</span><span id="compte">0 / 0</span></div><div class="progress-track"><div id="progress-fill"></div></div></div>
<div class="controls"><button id="toggle-masque" class="ctrl-btn">Masquer les rangés</button><button id="reset" class="ctrl-btn">Réinitialiser</button></div>
{onglets}
{corps}
<script>const VOYAGE = {json.dumps(libelle_voyage, ensure_ascii=False)};</script>
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


def lire_activites(reponse):
    """'pv', 'V P', 'v,p' -> ['plage', 'ville'] ; None si une lettre est inconnue ou si vide."""
    lettres = {c for c in reponse.lower() if c not in " ,;"}     # on ignore espaces et virgules
    if lettres and lettres <= set(CHOIX_ACTIVITE):              # <= : "est inclus dans"
        return sorted(CHOIX_ACTIVITE[l] for l in lettres)
    return None


def est_oui(reponse):
    return reponse.strip().lower() in {"o", "oui", "y", "yes"}


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


def main():
    """Assistant interactif : saisit un itinéraire, puis construit la valise."""
    manquants = objets_sans_rayon()
    if manquants:
        print(f"⚠️  Objets sans rayon (à classer dans THEMES) : {manquants}")

    try:
        conn = connecter()                # cache des normales ; facultatif
    except psycopg2.OperationalError:
        conn = None
        print("ℹ️  Postgres indisponible : climat interrogé en direct, sans cache.")

    # --- Saisie de l'itinéraire, étape par étape ---
    itineraire = []
    numero = 1
    mois_precedent = None             # Entrée au mois = même mois que l'étape d'avant
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
        while True:
            defaut = f" [Entrée = {MOIS[mois_precedent - 1]}]" if mois_precedent else ""
            mois = lire_mois(input(f"        — mois (1-12 ou janvier, févr…){defaut} : "), mois_precedent)
            if mois:
                break
            print("        Mois invalide : un nombre de 1 à 12 ou un nom de mois (janv, juillet…).")
        mois_precedent = mois
        while True:
            activites = lire_activites(input("        — activités ? (v)ille (p)lage (m)ontagne, combinables : "))
            if activites:
                break
            print("        Choix invalide : tape v, p, m ou une combinaison (ex : vp).")
        n = None
        if lieu:
            try:
                n = normales_avec_cache(conn, lieu["latitude"], lieu["longitude"], mois)  # lieu CHOISI
            except requests.RequestException:
                pass
        print("        🌡️", ligne_climat(destination, mois, n))
        itineraire.append({"destination": destination, "jours": jours, "mois": mois,
                           "activites": activites, "normales": n,
                           "code_pays": lieu["code_pays"] if lieu else None})
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

    hors_ue, inconnu = statut_ue_itineraire(itineraire)
    if inconnu:
        print("⚠️  Statut UE inconnu pour une étape : passeport par défaut, à vérifier.")
    conduit = est_oui(input("Tu vas conduire ? (o/n) : "))

    # --- Construction ---
    jours_types = jours_par_type(itineraire)
    total = total_jours(itineraire)
    prises = prises_itineraire(itineraire)
    valise = faire_valise(jours_types, total, personnes, hors_ue, conduit)

    climats = [(e["destination"], e["mois"], e["normales"]) for e in itineraire]
    libelle_voyage = " › ".join(etape["destination"] for etape in itineraire)
    html = valise_en_html(valise, libelle_voyage, total, prises, climats)
    with open("valise.html", "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Checklist écrite dans valise.html ({total} jours, {len(itineraire)} étape(s))")


if __name__ == "__main__":
    main()
