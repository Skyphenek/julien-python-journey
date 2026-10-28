"""Tests de la PWA : installable (manifeste + icône), lisible hors ligne (service worker),
et rien de perdu sans réseau (file d'attente des envois sur le téléphone)."""
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pytest
from serveur import creer_app
from valise import valise_en_html, paquet_vide, accueil_en_html, formulaire_en_html, HTML_SCRIPT, VERSION_PAGE
from pwa import manifeste, script_service_worker, SCRIPT_PRECHARGEMENT


@pytest.fixture
def client():
    return creer_app("valise_test", secret="s3cret").test_client()


def page_voyage():
    return valise_en_html({"Partagé": paquet_vide()}, "Hanoï", 7, set(), code="2027-01-10 Hanoï",
                          depart=date(2027, 1, 10))


def accueil():
    voyages = [{"code": "2027-01-10 Hanoï", "libelle": "Hanoï", "depart": date(2027, 1, 10),
                "fin": date(2027, 1, 17), "personnes": ["Julien"], "etapes": []}]
    return accueil_en_html(voyages, date(2026, 10, 27))


def node_check(tmp_path, code):
    if shutil.which("node") is None:
        pytest.skip("Node absent")
    fichier = tmp_path / "script.js"
    fichier.write_text(code)
    resultat = subprocess.run(["node", "--check", str(fichier)], capture_output=True, text=True)
    assert resultat.returncode == 0, resultat.stderr


# --- Manifeste et icônes ---

def test_manifeste_relatif_au_secret():
    m = manifeste()
    assert m["start_url"] == "./" and m["scope"] == "./"      # jamais le secret en dur
    assert m["display"] == "standalone"
    assert {i["sizes"] for i in m["icons"]} == {"192x192", "512x512"}


def test_routes_pwa_sous_le_secret(client):
    r = client.get("/v/s3cret/manifest.webmanifest")
    assert r.status_code == 200 and r.mimetype == "application/manifest+json"
    assert r.get_json()["name"]
    r = client.get("/v/s3cret/sw.js")
    assert r.status_code == 200 and r.mimetype == "text/javascript"
    assert r.headers["Cache-Control"] == "no-cache"           # le téléphone voit vite un nouveau worker
    assert f"valise-v{VERSION_PAGE}" in r.get_data(as_text=True)
    for taille in (180, 192, 512):
        r = client.get(f"/v/s3cret/icone-{taille}.png")
        assert r.status_code == 200 and r.mimetype == "image/png"
    assert client.get("/sw.js").status_code == 404               # sans le code : rien


def test_icone_inconnue(client):
    assert client.get("/v/s3cret/icone-64.png").status_code == 404


def test_les_trois_pages_sont_installables():
    for html in (page_voyage(), accueil(), formulaire_en_html()):
        assert '<link rel="manifest" href="manifest.webmanifest">' in html
        assert '<link rel="apple-touch-icon" href="icone-180.png">' in html
        assert "serviceWorker.register('sw.js')" in html


# --- Service worker ---

def test_service_worker_syntaxiquement_valide(tmp_path):
    node_check(tmp_path, script_service_worker(VERSION_PAGE))


def test_service_worker_ne_touche_qu_aux_lectures():
    sw = script_service_worker(VERSION_PAGE)
    assert "req.method !== 'GET'" in sw                         # envois : jamais en cache
    assert "X-Valise-Vite" in sw                                # ouverture : cache après 3 s
    assert "caches.delete" in sw                                # anciennes versions effacées


# --- File d'attente hors ligne (page voyage) ---

def test_file_d_attente_dans_la_page():
    for morceau in ("function envoyerOuGarder", "function viderFile", "'online'", "file-videe"):
        assert morceau in HTML_SCRIPT
    assert "fetch('api/coche'" not in HTML_SCRIPT               # la case passe par la file
    assert "fetch('api/infos', {" not in HTML_SCRIPT
    assert "fetch('api/depenses', {" not in HTML_SCRIPT


def test_page_voyage_signale_les_envois_en_attente():
    assert 'id="hors-ligne"' in page_voyage()


def test_accueil_precharge_les_voyages_a_venir():
    html = accueil()
    assert 'data-code="2027-01-10 Hanoï"' in html
    assert SCRIPT_PRECHARGEMENT in html


def test_prechargement_syntaxiquement_valide(tmp_path):
    node_check(tmp_path, SCRIPT_PRECHARGEMENT)


def test_icone_en_vadrouille():
    # Source SVG gardée à côté des PNG (refaits avec Chrome sans fenêtre, voir la PR #44)
    dossier = Path(__file__).parent / "static"
    assert "#0e9aa7" in (dossier / "icone.svg").read_text()
    for taille in (180, 192, 512):
        png = (dossier / f"icone-{taille}.png").read_bytes()
        assert png[:8] == b"\x89PNG\r\n\x1a\n" and int.from_bytes(png[16:20], "big") == taille
