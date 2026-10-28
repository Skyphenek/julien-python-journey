"""Tests du compte à rebours (accueil + tête de la page voyage) : même texte en Python et en JS."""
import json
import shutil
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pytest
from compte_a_rebours import texte_compte, compte_en_html, SCRIPT_COMPTE
from programme import etapes_du_voyage
from valise import accueil_en_html, construire, rendre_page, VERSION_PAGE

DEPART = date(2027, 1, 15)
ITINERAIRE = [{"destination": "Hanoï", "jours": 4}, {"destination": "Siem Reap", "jours": 3}]
ETAPES = etapes_du_voyage(ITINERAIRE, DEPART)
FIN = date(2027, 1, 21)

CAS = [
    (date(2026, 10, 28), "⏳ Départ dans 79 jours"),
    (date(2027, 1, 14), "⏳ Départ demain !"),
    (DEPART, "✈️ C’est le départ ! · jour 1 sur 7 · Hanoï"),
    (date(2027, 1, 19), "📍 Jour 5 sur 7 · Siem Reap"),
    (FIN, "🏁 Dernier jour · jour 7 sur 7 · Siem Reap"),
    (date(2027, 1, 22), "🧳 Rentrés depuis 1 jour"),
    (date(2027, 2, 1), "🧳 Rentrés depuis 11 jours"),
]


@pytest.mark.parametrize("aujourd_hui, attendu", CAS)
def test_texte_compte(aujourd_hui, attendu):
    assert texte_compte(DEPART, FIN, aujourd_hui, ETAPES) == attendu


def test_voyage_d_un_jour_et_sans_etapes():
    assert texte_compte(DEPART, DEPART, DEPART) == "✈️ C’est le départ ! · jour 1 sur 1"


def test_meme_texte_en_javascript(tmp_path):
    """La page recalcule avec la date du téléphone : la règle JS doit dire exactement la même chose."""
    if shutil.which("node") is None:
        pytest.skip("Node absent")
    etapes = [{"destination": e["destination"], "du": e["du"].isoformat(), "au": e["au"].isoformat()} for e in ETAPES]
    fichier = tmp_path / "compte.js"
    fichier.write_text(
        "const window = {}; const document = { querySelectorAll: () => [], addEventListener: () => {} };\n"
        "global.setInterval = () => {};\n" + SCRIPT_COMPTE
        + f"\nconst cas = {json.dumps([j.isoformat() for j, _ in CAS])};\n"
        + f"console.log(JSON.stringify(cas.map(j => window.texteCompte('{DEPART}', '{FIN}', j, {json.dumps(etapes)}))));\n")
    resultat = subprocess.run(["node", str(fichier)], capture_output=True, text=True)
    assert resultat.returncode == 0, resultat.stderr
    assert json.loads(resultat.stdout) == [attendu for _, attendu in CAS]


def test_compte_en_html_echappe_et_porte_les_dates():
    html = compte_en_html(DEPART, FIN, date(2026, 10, 28), [{"destination": "<b>", "du": DEPART, "au": FIN}])
    assert 'data-depart="2027-01-15" data-fin="2027-01-21"' in html and "<b>" not in html


def test_tete_de_la_page_voyage():
    voyage = {"depart": DEPART, "personnes": ["Julien"], "conduit": False, "lessive": None,
              "itineraire": [dict(e, mois=1, activites=[], normales=None) for e in ITINERAIRE]}
    html = rendre_page(voyage, construire(voyage), aujourd_hui=date(2027, 1, 19))
    tete = html.split("</h1>")[1].split('<nav class="rubriques">')[0]
    assert "📍 Jour 5 sur 7 · Siem Reap" in tete and "data-compte" in tete
    assert SCRIPT_COMPTE in html and VERSION_PAGE >= 21


def test_accueil_prochain_voyage_en_grand():
    voyages = [
        {"code": "2026-10-01 Rome", "libelle": "Rome", "depart": date(2026, 10, 1), "fin": date(2026, 10, 4),
         "personnes": ["Julien"], "etapes": [{"destination": "Rome", "jours": 4}]},
        {"code": "2027-01-15 Hanoï", "libelle": "Hanoï › Siem Reap", "depart": DEPART, "fin": FIN,
         "personnes": ["Julien"], "etapes": ITINERAIRE},
        {"code": "2027-06-01 Oslo", "libelle": "Oslo", "depart": date(2027, 6, 1), "fin": date(2027, 6, 5),
         "personnes": ["Julien"], "etapes": [{"destination": "Oslo", "jours": 5}]},
    ]
    html = accueil_en_html(voyages, date(2026, 10, 28))
    prochain = html.split('<div class="prochain">')[1].split("</div>")[0]
    assert "Hanoï › Siem Reap" in prochain and "Départ dans 79 jours" in prochain
    assert html.count("data-compte data-depart") == 3                     # le grand + les 2 à venir ; pas Rome (passé)
    assert SCRIPT_COMPTE in html
    assert '<div class="prochain">' not in accueil_en_html(voyages[:1], date(2026, 10, 28))
