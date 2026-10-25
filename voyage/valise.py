"""Générateur de checklist de valise — adapté au type de destination, à la durée
et à la personne (Julien / Laetitia).

Application Python des concepts Exercism : dicts, listes, boucles, conditions.
On sépare les DONNÉES (les 3 tables ci-dessous, remplies une fois) de la LOGIQUE
(la fonction faire_valise). Démarrage minimal : on enrichit au fil des voyages.
"""
import json

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

# 4. GÉO — Table 1 : chaque ville pointe vers sa zone climatique (mapping léger).
VILLE_VERS_ZONE = {
    # Europe du Nord / îles britanniques
    "Londres": "europe_nord", "Édimbourg": "europe_nord", "Dublin": "europe_nord",
    "Amsterdam": "europe_nord", "Bruxelles": "europe_nord", "Berlin": "europe_nord",
    "Copenhague": "europe_nord", "Stockholm": "europe_nord",
    # Europe de l'Ouest continentale
    "Paris": "europe_ouest", "Lyon": "europe_ouest", 
    "Milan": "europe_ouest",
    # Côte atlantique (France / Espagne / Portugal)
    "Cap Ferret": "cote_atlantique", "Biarritz": "cote_atlantique", "Bordeaux": "cote_atlantique",
    "La Rochelle": "cote_atlantique", "Nantes": "cote_atlantique", "Saint-Sébastien": "cote_atlantique",
    "Porto": "cote_atlantique",
    # Méditerranée (Italie / Espagne / sud France / Grèce / Portugal sud)
    "Rome": "mediterranee", "Florence": "mediterranee", "Venise": "mediterranee",
    "Naples": "mediterranee", "Palerme": "mediterranee", "Marseille": "mediterranee",
    "Nice": "mediterranee", "Barcelone": "mediterranee", "Madrid": "mediterranee",
    "Séville": "mediterranee", "Valence": "mediterranee", "Athènes": "mediterranee",
    "Lisbonne": "mediterranee", "Split": "mediterranee", "Dubrovnik": "mediterranee",
    "Cyclades": "mediterranee",
    # Montagne / Alpes
    "Annecy": "montagne_alpes", "Chamonix": "montagne_alpes", "Genève": "montagne_alpes", "Grenoble": "montagne_alpes",
    "Innsbruck": "montagne_alpes", "Méribel": "montagne_alpes", "Zermatt": "montagne_alpes",
    # Afrique du Nord / désertique chaud
    "Marrakech": "afrique_nord", "Agadir": "afrique_nord", "Essaouira": "afrique_nord",
    "Tunis": "afrique_nord", "Dubaï": "afrique_nord",
    # Asie du Sud-Est
    "Hanoï": "asie_sud_est", "Ho Chi Minh": "asie_sud_est", "Siem Reap": "asie_sud_est",
    "Bangkok": "asie_sud_est", "Singapour": "asie_sud_est",
    # Asie de l'Est tempérée (4 saisons)
    "Tokyo": "asie_est_tempere", "Kyoto": "asie_est_tempere", "Osaka": "asie_est_tempere",
    "Pékin": "asie_est_tempere", "Shanghai": "asie_est_tempere", "Xi'an": "asie_est_tempere",
    "Chengdu": "asie_est_tempere", "Séoul": "asie_est_tempere", "Busan": "asie_est_tempere",
    # Amériques
    "New York": "usa_est", "Boston": "usa_est",
    "San Francisco": "usa_ouest", "Los Angeles": "usa_ouest",
    "Miami": "tropical", "Cancún": "tropical", "Bali": "tropical",
}

# 4avant. GÉO — Table 1ter : chaque VILLE pointe vers son PAYS.
#         Sert au statut UE et à l'adaptateur : sans elle, toute ville tombe en
#         "inconnu" -> passeport par défaut + adaptateur "à vérifier" (bug Cyclades).
#         La zone climatique reste pilotée par VILLE_VERS_ZONE (indépendant).
VILLE_VERS_PAYS = {
    "Londres": "Royaume-Uni", "Édimbourg": "Royaume-Uni", "Dublin": "Irlande",
    "Amsterdam": "Pays-Bas", "Bruxelles": "Belgique", "Berlin": "Allemagne",
    "Copenhague": "Danemark", "Stockholm": "Suède",
    "Paris": "France", "Lyon": "France", "Milan": "Italie",
    "Cap Ferret": "France", "Biarritz": "France", "Bordeaux": "France",
    "La Rochelle": "France", "Nantes": "France", "Saint-Sébastien": "Espagne",
    "Porto": "Portugal",
    "Rome": "Italie", "Florence": "Italie", "Venise": "Italie", "Naples": "Italie",
    "Palerme": "Italie", "Marseille": "France", "Nice": "France",
    "Barcelone": "Espagne", "Madrid": "Espagne", "Séville": "Espagne",
    "Valence": "Espagne", "Athènes": "Grèce", "Lisbonne": "Portugal",
    "Split": "Croatie", "Dubrovnik": "Croatie", "Cyclades": "Grèce",
    "Annecy": "France", "Chamonix": "France", "Genève": "Suisse",
    "Grenoble": "France", "Innsbruck": "Autriche", "Méribel": "France",
    "Zermatt": "Suisse",
    "Marrakech": "Maroc", "Agadir": "Maroc", "Essaouira": "Maroc",
    "Tunis": "Tunisie", "Dubaï": "Émirats Arabes Unis",
    "Hanoï": "Vietnam", "Ho Chi Minh": "Vietnam", "Siem Reap": "Cambodge",
    "Bangkok": "Thaïlande", "Singapour": "Singapour",
    "Tokyo": "Japon", "Kyoto": "Japon", "Osaka": "Japon",
    "Pékin": "Chine", "Shanghai": "Chine", "Xi'an": "Chine", "Chengdu": "Chine",
    "Séoul": "Corée du Sud", "Busan": "Corée du Sud",
    "New York": "États-Unis", "Boston": "États-Unis",
    "San Francisco": "États-Unis", "Los Angeles": "États-Unis",
    "Miami": "États-Unis", "Cancún": "Mexique", "Bali": "Indonésie",
}

# 4bis. GÉO — Table 1bis : chaque PAYS (ou État US) pointe vers sa zone climatique.
#       Même mécanisme que VILLE_VERS_ZONE : une entrée -> une zone de ZONES.
#       Pays au climat trop hétérogène pour une seule zone (USA, Indonésie, Brésil,
#       Australie, Chine, Inde) volontairement absents -> saisir par ville.
PAYS_VERS_ZONE = {
    # Europe du Nord / îles britanniques
    "Royaume-Uni": "europe_nord", "Irlande": "europe_nord",
    "Pays-Bas": "europe_nord", "Belgique": "europe_nord",
    "Allemagne": "europe_nord", "Danemark": "europe_nord",
    "Suède": "europe_nord", "Norvège": "europe_nord", "Islande": "europe_nord",
    # Europe de l'Ouest continentale
    "France": "europe_ouest", "Luxembourg": "europe_ouest",
    # Montagne / Alpes
    "Suisse": "montagne_alpes", "Autriche": "montagne_alpes", "Slovénie": "montagne_alpes",
    # Méditerranée
    "Italie": "mediterranee", "Espagne": "mediterranee", "Grèce": "mediterranee",
    "Portugal": "mediterranee", "Croatie": "mediterranee", "Malte": "mediterranee",
    "Chypre": "mediterranee",
    # Afrique du Nord / Moyen-Orient désertique
    "Maroc": "afrique_nord", "Tunisie": "afrique_nord", "Égypte": "afrique_nord",
    "Émirats Arabes Unis": "afrique_nord", "Jordanie": "afrique_nord",
    # Asie du Sud-Est
    "Thaïlande": "asie_sud_est", "Vietnam": "asie_sud_est", "Cambodge": "asie_sud_est",
    "Laos": "asie_sud_est", "Myanmar": "asie_sud_est", "Malaisie": "asie_sud_est",
    "Singapour": "asie_sud_est", "Philippines": "asie_sud_est",
    "Sri Lanka": "asie_sud_est",
    # Asie de l'Est tempérée (4 saisons)
    "Japon": "asie_est_tempere", "Chine": "asie_est_tempere",
    "Corée du Sud": "asie_est_tempere", "Taïwan": "asie_est_tempere",
    # Tropical (Amériques / îles)
    "Mexique": "tropical", "Cuba": "tropical", "République Dominicaine": "tropical",
    "Costa Rica": "tropical",
    # États-Unis (pays exclu, mais États touristiques au climat homogène inclus)
    "Californie": "usa_ouest", "Floride": "tropical", "Hawaï": "tropical",
    "Nevada": "usa_ouest", "Arizona": "usa_ouest", "Louisiane": "usa_est",
}

# 4ter. GÉO — UE : pays membres. Appartenance -> UE ; absence d'un pays connu -> hors UE.
#       (Accepte aussi des villes si on veut en couvrir plus tard.)
PAYS_UE = {
    "France", "Belgique", "Pays-Bas", "Allemagne", "Danemark", "Suède",
    "Irlande", "Luxembourg", "Autriche", "Slovénie", "Italie", "Espagne",
    "Grèce", "Portugal", "Croatie", "Malte", "Chypre",
}

# 4ter-bis. GÉO — CARTE D'IDENTITÉ SUFFIT : UE + Schengen/EEE hors UE (Suisse,
#           Norvège, Islande) où la carte d'identité remplace le passeport et où
#           le permis français suffit (pas de permis international).
SANS_PASSEPORT = PAYS_UE | {"Suisse", "Norvège", "Islande"}

# 4quater. GÉO — PRISE : quel adaptateur emporter DEPUIS LA FRANCE pour ce pays.
#          Valeurs usuelles (à revérifier ponctuellement). Le garde-fou
#          pays_sans_prise() signale tout pays de PAYS_VERS_ZONE non couvert ici.
PAYS_VERS_PRISE = {
    # Europe continentale + Maghreb (mêmes prises type C/E/F qu'en France)
    "France": "aucun", "Belgique": "aucun", "Pays-Bas": "aucun",
    "Allemagne": "aucun", "Danemark": "aucun", "Suède": "aucun",
    "Norvège": "aucun", "Islande": "aucun", "Luxembourg": "aucun",
    "Suisse": "aucun", "Autriche": "aucun", "Slovénie": "aucun",
    "Italie": "aucun", "Espagne": "aucun", "Grèce": "aucun",
    "Portugal": "aucun", "Croatie": "aucun",
    "Maroc": "aucun", "Tunisie": "aucun", "Égypte": "aucun",
    # Prises britanniques (type G)
    "Royaume-Uni": "UK", "Irlande": "UK", "Malte": "UK", "Chypre": "UK",
    "Émirats Arabes Unis": "UK", "Malaisie": "UK", "Singapour": "UK",
    # Prises américaines (type A/B, 110V)
    "Mexique": "US (110V)", "République Dominicaine": "US (110V)",
    "Costa Rica": "US (110V)", "Japon": "US (110V)",
    "États-Unis": "US (110V)",
    "Californie": "US (110V)", "Floride": "US (110V)", "Hawaï": "US (110V)",
    "Nevada": "US (110V)", "Arizona": "US (110V)", "Louisiane": "US (110V)",
    # Prises mélangées -> adaptateur universel
    "Jordanie": "universel", "Thaïlande": "universel", "Vietnam": "universel",
    "Cambodge": "universel", "Laos": "universel", "Myanmar": "universel",
    "Philippines": "universel / US", "Cuba": "universel / US",
    "Sri Lanka": "universel / UK",
    # Asie de l'Est tempérée (Corée : prises type C/F comme en France)
    "Chine": "universel", "Corée du Sud": "aucun", "Taïwan": "US (110V)",
}


# 5. GÉO — Table 2 : chaque zone définit ses types de destination par saison.
ZONES = {
    "europe_nord": {
        "hiver": ["froid", "pluie", "ville"], "printemps": ["froid", "pluie", "ville"],
        "été": ["ville"],                     "automne": ["froid", "pluie", "ville"],
    },
    "europe_ouest": {
        "hiver": ["froid", "ville"], "printemps": ["ville"],
        "été": ["chaud", "ville"],   "automne": ["froid", "ville"],
    },
    "cote_atlantique": {
        "hiver": ["froid", "pluie", "ville"],   "printemps": ["ville"],
        "été": ["chaud", "plage", "ville"],     "automne": ["pluie", "ville"],
    },
    "mediterranee": {
        "hiver": ["ville"],                  "printemps": ["ville"],
        "été": ["chaud", "plage", "ville"],  "automne": ["ville"],
    },
    "montagne_alpes": {
        "hiver": ["froid", "montagne"],     "printemps": ["froid", "montagne"],
        "été": ["montagne", "ville"],       "automne": ["froid", "montagne"],
    },
    "afrique_nord": {
        "hiver": ["ville"],          "printemps": ["chaud", "ville"],
        "été": ["chaud", "ville"],   "automne": ["chaud", "ville"],
    },
    "asie_sud_est": {
        "hiver": ["chaud", "plage"],          "printemps": ["chaud", "plage"],
        "été": ["chaud", "plage", "pluie"],   "automne": ["chaud", "plage", "pluie"],
    },
    "asie_est_tempere": {   # Japon, Chine, Corée, Taïwan : 4 saisons marquées, mousson estivale
        "hiver": ["froid", "ville"],          "printemps": ["ville"],
        "été": ["chaud", "ville", "pluie"],   "automne": ["ville"],
    },
    "usa_est": {
        "hiver": ["froid", "ville"], "printemps": ["ville"],
        "été": ["chaud", "ville"],   "automne": ["froid", "ville"],
    },
    "usa_ouest": {
        "hiver": ["ville"],                 "printemps": ["ville"],
        "été": ["chaud", "ville"],          "automne": ["ville"],
    },
    "tropical": {
        "hiver": ["chaud", "plage"],          "printemps": ["chaud", "plage"],
        "été": ["chaud", "plage", "pluie"],   "automne": ["chaud", "plage"],
    },
}


def saison_du_mois(mois):
    """Traduire un numéro de mois (1-12) en saison."""
    if mois in [12, 1, 2]:
        return "hiver"
    if mois in [3, 4, 5]:
        return "printemps"
    if mois in [6, 7, 8]:
        return "été"
    return "automne"

def zone_de(destination):
    """Trouver la zone climatique d'une ville ou d'un pays."""
    if destination in VILLE_VERS_ZONE:
        return VILLE_VERS_ZONE[destination]
    if destination in PAYS_VERS_ZONE:
        return PAYS_VERS_ZONE[destination]
    return None


def pays_de(destination):
    """Résoudre une destination en pays : une ville -> son pays, un pays -> lui-même."""
    return VILLE_VERS_PAYS.get(destination, destination)


def statut_ue(destination):
    """Statut documents : 'ue' (carte d'identité suffit — UE + Schengen), 'hors_ue'
    (passeport + permis international), ou 'inconnu' (pays non modélisé)."""
    pays = pays_de(destination)
    if pays in SANS_PASSEPORT:
        return "ue"
    if pays in PAYS_VERS_ZONE or pays in PAYS_VERS_PRISE:   # pays connu hors zone CI
        return "hors_ue"
    return "inconnu"                     # pays non modélisé -> défaut prudent (passeport)


def adaptateur_pour(destination):
    """Libellé de l'adaptateur à emporter depuis la France, ou 'à vérifier'."""
    pays = pays_de(destination)
    if pays in PAYS_VERS_PRISE:
        return PAYS_VERS_PRISE[pays]
    return "à vérifier"

def statut_ue_itineraire(itineraire):
    hors_ue = False
    inconnu = False
    for etape in itineraire:
        statut = statut_ue(etape["destination"])
        if statut == "hors_ue":
            hors_ue = True
        elif statut == "inconnu":
            hors_ue = True
            inconnu = True
    return hors_ue, inconnu      # <-- deux valeurs = un tuple

def prises_itineraire(itineraire):
    prises = set()               # ensemble vide ; les doublons se dédupliquent tout seuls
    for etape in itineraire:
        prise = adaptateur_pour(etape["destination"])
        if prise != "aucun":                  # on ignore les "aucun"
            prises.add(prise)
    return prises

def pays_sans_prise():
    """Garde-fou : pays/États qui ont une zone mais aucune prise renseignée."""
    return set(PAYS_VERS_ZONE) - set(PAYS_VERS_PRISE)

def types_pour(ville, mois):
    """Déduire les types de destination depuis la ville et le mois.

    Double lookup (façon jointure SQL) : ville -> zone -> climat[saison].
    """
    zone = zone_de(ville)
    saison = saison_du_mois(mois)
    return ZONES[zone][saison]

def total_jours(itineraire):
    """Compter le nombre de jours d'un itinéraire (liste de tuples [(ville, nb_jours), ...])."""
    return sum(etape["jours"] for etape in itineraire)

def jours_par_type(itineraire):
    jours = {}
    for etape in itineraire:
        for type_dest in types_pour(etape["destination"], etape["mois"]):
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

def valise_en_html(valise, libelle_voyage, total, prises):
    """Construire la page HTML de la checklist pour l'itinéraire complet."""
    adaptateurs = ", ".join(sorted(prises)) if prises else "aucun"
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
<div class="progress"><div class="progress-head"><span>Rangé</span><span id="compte">0 / 0</span></div><div class="progress-track"><div id="progress-fill"></div></div></div>
<div class="controls"><button id="toggle-masque" class="ctrl-btn">Masquer les rangés</button><button id="reset" class="ctrl-btn">Réinitialiser</button></div>
{onglets}
{corps}
<script>const VOYAGE = {json.dumps(libelle_voyage, ensure_ascii=False)};</script>
<script>{HTML_SCRIPT}</script>
</body>
</html>"""
    return page

def main():
    """Assistant interactif : saisit un itinéraire, puis construit la valise."""
    manquants = objets_sans_rayon()
    if manquants:
        print(f"⚠️  Objets sans rayon (à classer dans THEMES) : {manquants}")
    sans_prise = pays_sans_prise()
    if sans_prise:
        print(f"⚠️  Pays sans prise renseignée (à compléter dans PAYS_VERS_PRISE) : {sans_prise}")

    # --- Saisie de l'itinéraire, étape par étape ---
    itineraire = []
    numero = 1
    while True:
        destination = input(f"Étape {numero} — destination (ou 'fin' pour terminer) : ")
        if destination == "fin":
            if itineraire:
                break
            print("Ajoute au moins une étape avant de terminer.")
            continue
        if destination not in VILLE_VERS_ZONE and destination not in PAYS_VERS_ZONE:
            print(f"Destination '{destination}' inconnue, vérifie l'orthographe.")
            continue
        while True:
            reponse = input("        — jours : ")
            if reponse.isdigit() and int(reponse) >= 1:
                jours = int(reponse)
                break
            print("        Nombre de jours invalide : entre un nombre positif.")
        while True:
            reponse = input("        — mois (1-12) : ")
            if reponse.isdigit() and 1 <= int(reponse) <= 12:
                mois = int(reponse)
                break
            print("        Mois invalide : entre un nombre entre 1 et 12.")
        itineraire.append({"destination": destination, "jours": jours, "mois": mois})
        numero += 1

    # --- Questions posées une seule fois ---
    while True:
        choix = input("Qui fait sa valise ? (j = Julien / l = Laetitia / 2 = les deux) : ")
        if choix in CHOIX_PERSONNE:
            break
        print("Choix invalide : tape j, l ou 2.")
    personnes = CHOIX_PERSONNE[choix]

    hors_ue, inconnu = statut_ue_itineraire(itineraire)
    if inconnu:
        print("⚠️  Statut UE inconnu pour une étape : passeport par défaut, à vérifier.")
    conduit = input("Tu vas conduire ? (o/n) : ") == "o"

    # --- Construction ---
    jours_types = jours_par_type(itineraire)
    total = total_jours(itineraire)
    prises = prises_itineraire(itineraire)
    valise = faire_valise(jours_types, total, personnes, hors_ue, conduit)

    libelle_voyage = " › ".join(etape["destination"] for etape in itineraire)
    html = valise_en_html(valise, libelle_voyage, total, prises)
    with open("valise.html", "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Checklist écrite dans valise.html ({total} jours, {len(itineraire)} étape(s))")


if __name__ == "__main__":
    main()
