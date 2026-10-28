"""PWA : l'appli s'installe sur l'écran d'accueil et reste lisible sans réseau.

Tout vit sous /v/<secret>/ : le manifeste et le service worker utilisent des adresses
relatives, le secret n'apparaît jamais dans leur contenu.
"""

COULEUR = "#4f46e5"            # l'accent de la page (--accent)
TAILLES_ICONE = (180, 192, 512)


def manifeste():
    """Ce que le téléphone lit pour installer l'appli (nom, icône, plein écran)."""
    return {
        "name": "Nos valises",
        "short_name": "Valises",
        "start_url": "./",
        "scope": "./",
        "display": "standalone",
        "background_color": "#f4f4f5",
        "theme_color": COULEUR,
        "lang": "fr",
        "icons": [{"src": f"icone-{t}.png", "sizes": f"{t}x{t}", "type": "image/png", "purpose": "any"}
                  for t in (192, 512)],
    }


# Injectée dans le <head> des trois pages (voyage, accueil, formulaire)
TETE_PWA = f"""<link rel="manifest" href="manifest.webmanifest">
<link rel="apple-touch-icon" href="icone-180.png">
<meta name="theme-color" content="{COULEUR}">
<meta name="apple-mobile-web-app-title" content="Valises">
<script>if ('serviceWorker' in navigator) navigator.serviceWorker.register('sw.js').catch(function () {{}});</script>"""


# Service worker : uniquement les LECTURES (GET) de l'appli.
# - réseau d'abord, et la réponse est gardée en cache ;
# - réseau coupé, ou serveur en erreur (5xx) : la dernière copie gardée ;
# - ouverture d'une page, ou lecture marquée X-Valise-Vite : si le serveur ne répond pas
#   en 3 s (Render se réveille), la copie gardée tout de suite.
# Les envois (POST, DELETE) ne passent jamais par le cache : la page s'en charge (file d'attente).
_SW = """
const CACHE = 'valise-v__VERSION__';
const DELAI = 3000;
const PORTEE = new URL(self.registration.scope).pathname;

self.addEventListener('install', function (ev) {
    self.skipWaiting();
    ev.waitUntil(caches.open(CACHE).then(function (c) { return c.add('./'); }).catch(function () {}));
});

self.addEventListener('activate', function (ev) {
    ev.waitUntil(caches.keys().then(function (cles) {
        return Promise.all(cles.filter(function (k) { return k.indexOf('valise-') === 0 && k !== CACHE; })
                               .map(function (k) { return caches.delete(k); }));
    }).then(function () { return self.clients.claim(); }));
});

function garder(cle, reponse) {
    if (reponse.ok) {
        const copie = reponse.clone();
        caches.open(CACHE).then(function (c) { return c.put(cle, copie); });
    }
    return reponse;
}

function reseauPuisCache(req, delai) {
    const cle = req.url;
    const reseau = fetch(req).then(function (r) { return garder(cle, r); });
    return new Promise(function (resolve, reject) {
        let fini = false;
        function finir(r) { if (!fini) { fini = true; resolve(r); } }
        function copieSinon(secours) {
            return caches.match(cle).then(function (copie) {
                if (copie) finir(copie);
                else if (secours) finir(secours);
                else if (!fini) { fini = true; reject(new TypeError('hors ligne')); }
            });
        }
        const minuteur = delai ? setTimeout(function () {
            caches.match(cle).then(function (copie) { if (copie) finir(copie); });
        }, delai) : null;
        reseau.then(function (r) {
            clearTimeout(minuteur);
            if (r.status >= 500) copieSinon(r); else finir(r);
        }, function () {
            clearTimeout(minuteur);
            copieSinon(null);
        });
    });
}

self.addEventListener('fetch', function (ev) {
    const req = ev.request;
    if (req.method !== 'GET') return;
    const url = new URL(req.url);
    if (url.origin !== self.location.origin || url.pathname.indexOf(PORTEE) !== 0) return;
    if (url.pathname.slice(-6) === '/sw.js') return;
    const vite = req.mode === 'navigate' || req.headers.get('X-Valise-Vite') === '1';
    ev.respondWith(reseauPuisCache(req, vite ? DELAI : 0));
});

// Préchargement demandé par l'accueil : les voyages à venir, pour les ouvrir sans réseau
self.addEventListener('message', function (ev) {
    if (!ev.data || !Array.isArray(ev.data.precharger)) return;
    ev.waitUntil(caches.open(CACHE).then(function (c) {
        return Promise.all(ev.data.precharger.map(function (u) {
            return fetch(u).then(function (r) { if (r.ok) return c.put(u, r); }).catch(function () {});
        }));
    }));
});
"""


def script_service_worker(version):
    """Le worker change (et le cache avec) à chaque nouvelle version de page."""
    return _SW.replace("__VERSION__", str(version))


# Accueil : demande au worker de garder chaque voyage à venir (page + état + programme + à voir + dépenses + souvenirs)
SCRIPT_PRECHARGEMENT = """
if ('serviceWorker' in navigator && navigator.onLine) {
    navigator.serviceWorker.ready.then(function (reg) {
        const adresses = [];
        document.querySelectorAll('a.voyage[data-a-venir]').forEach(function (a) {
            const code = encodeURIComponent(a.dataset.code);
            adresses.push(a.href);
            ['api/etat/', 'api/reservations/', 'api/a-voir/', 'api/depenses/', 'api/souvenirs/'].forEach(function (api) {
                adresses.push(new URL(api + code, location.href).href);
            });
        });
        if (adresses.length && reg.active) reg.active.postMessage({ precharger: adresses });
    });
}
"""
