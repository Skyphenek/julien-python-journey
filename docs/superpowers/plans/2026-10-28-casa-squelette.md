# Plan — Casa Binomerie, livraison 1 : squelette du hub

Spec : `docs/superpowers/specs/2026-10-28-hub-maison-design.md`. Branche `feat/casa-squelette`.
Aucune table, aucune migration Neon.

## Tâches (TDD : test rouge → code → vert, puis suite complète)

1. **Navigation du hub** (`design.py`) : `nav_hub(actif)` + `STYLE_NAV_HUB`. Entrées livrées :
   Aujourd'hui (`./`) et En Vadrouille (`vadrouille`) ; `HUB` liste les entrées dans l'ordre,
   les futures (Dîners, Courses, Colis) s'y ajoutent à leur livraison. Barre en bas sur
   téléphone, latérale ≥ 900 px, couleur maison distincte des rubriques voyage.
   Tests : `test_casa.py` — ordre, entrée active, pas de lien mort.
2. **Page Aujourd'hui** (`casa.py`) : `aujourdhui_en_html(voyages, aujourd_hui)` — titre
   Casa Binomerie, date du jour en clair, bloc « En Vadrouille » (prochain voyage + compte à
   rebours) seulement s'il part dans moins de 60 jours ou est en cours, message d'attente sinon.
   Tests : `test_casa.py` — bloc présent à J-59 / en cours, absent à J-60 / voyage passé / aucun.
3. **Routes** (`serveur.py`) : `/` sans paramètre → Aujourd'hui ; `/vadrouille` → l'ancien accueil ;
   les deux acceptent `?v=`, `?nouvelle`, `?modifier=` (même fonction).
   Tests : `test_serveur.py` — `/vadrouille` liste les voyages, `/vadrouille?v=` et `/?v=` ouvrent
   le même voyage, `/` sans paramètre affiche Aujourd'hui, préfixe secret respecté.
4. **Liens retour** (`valise.py`) : « ← En Vadrouille » vers `vadrouille` (page voyage +
   formulaire) ; suppression d'un voyage → `vadrouille`. La liste des voyages reçoit la nav du hub.
5. **PWA** (`pwa.py`) : nom « Casa Binomerie », court « Binomerie ». Icône inchangée.
6. Suite complète verte ; vérification dans Chrome (téléphone + large) : Aujourd'hui, liste,
   ouverture d'un voyage, retour, création.
