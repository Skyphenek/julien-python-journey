#!/usr/bin/env python3
"""L'Arène NBA — travaille tes gammes Python en t'amusant.

Lance :  python3 arene.py

But de la v1 : consolider les 4 briques que tu maîtrises déjà (dicts, comprehensions,
sorted+lambda, sets) par la répétition et les variations, sur des vraies stats NBA.

Trois types de manches :
  🔮 PRÉDIRE   → je montre du code, tu tapes ce qu'il affiche.
  ⚡ ONE-LINER → tu tapes UNE expression Python (inline).
  ✍️  FONCTION → tu écris la fonction dans reponse.py (sous VS Code), Entrée pour tester.

À tout moment au prompt :  i = indice · sol = solution (après 3 indices) · p = passer · q = quitter
"""

import moteur
import defis as banque

# --- Couleurs ANSI (dégradent proprement si le terminal ne les gère pas) ---
V, R, J, B, C, GRAS, OFF = (
    "\033[92m", "\033[91m", "\033[93m", "\033[94m", "\033[96m", "\033[1m", "\033[0m"
)

ICONE_TYPE = {"predire": "🔮 PRÉDIRE", "oneliner": "⚡ ONE-LINER", "ecrire": "✍️  FONCTION"}


def c(txt, couleur):
    return f"{couleur}{txt}{OFF}"


def barre(car="─", n=54):
    print(car * n)


def multiplicateur(combo):
    """x1, puis +1 tous les 3 succès d'affilée, plafonné à x4."""
    return min(1 + combo // 3, 4)


# ===========================================================================
# ÉCRANS
# ===========================================================================
def ecran_accueil(etat):
    print()
    print(c("   🏀  L'ARÈNE NBA  —  tes gammes Python", GRAS + J))
    barre("═")
    reussis = len(etat["defis_reussis"])
    total = len(banque.DEFIS)
    print(f"   Saison {etat['saison']}  ·  Niveau {c(etat['niveau'], GRAS)}  ·  "
          f"Score {c(etat['score_total'], GRAS + C)}  ·  Record streak {etat['record_streak']}")
    print(f"   Gammes maîtrisées : {reussis}/{total} défis validés au moins une fois")
    print("   Briques travaillées :")
    for cle in banque.BRIQUES_V1:
        print(f"     • {banque.BRIQUES[cle]}")
    barre()
    print(f"   {c('i', J)}=indice   {c('sol', J)}=solution   {c('p', J)}=passer   {c('q', J)}=quitter")
    barre()


def entete_manche(defi, session):
    print()
    combo = session["combo"]
    mult = multiplicateur(combo)
    ligne_combo = ""
    if combo >= 1:
        ligne_combo = c(f"  🔥 combo {combo}  (×{mult})", J) if mult > 1 else f"  streak {combo}"
    diff = "●" * defi["difficulte"] + "○" * (3 - defi["difficulte"])
    print(c(f"  {ICONE_TYPE[defi['type']]}", GRAS + B)
          + c(f"   [{banque.BRIQUES[defi['brique']].split(' · ')[0]}]", C)
          + c(f"   diff {diff}", OFF)
          + c(f"   score {session['points']}", OFF) + ligne_combo)
    barre()
    for ligne in defi["enonce"].splitlines():
        print("  " + ligne)
    if defi["type"] == "predire":
        print()
        print(c("  ┌─ code ─────────────────────────────────────────", OFF))
        for ligne in defi["code"].splitlines():
            print(c("  │ ", OFF) + c(ligne, C))
        print(c("  └────────────────────────────────────────────────", OFF))
    print()


# ===========================================================================
# UNE MANCHE
# ===========================================================================
def jouer_manche(defi, etat, session):
    """Gère une manche complète (tentatives, indices, solution).

    Renvoie l'un de : 'reussi', 'passe', 'sol', 'quit'.
    Met à jour session (points, combo, streak) et etat (defis_reussis, score).
    """
    nb_indices = 0
    entete_manche(defi, session)

    if defi["type"] == "ecrire":
        moteur.ecrire_stub(defi)
        print(c(f"  ✍️  Ouvre {c('reponse.py', GRAS)} dans VS Code, écris "
                f"{c(defi['fonction'] + '(joueurs)', GRAS)}, sauvegarde (Cmd+S).", B))
        print(c("     Astuce :  open -a \"Visual Studio Code\" reponse.py", OFF))
        prompt = c("  ⏎  Entrée pour tester  (i/sol/p/q) > ", GRAS)
    else:
        prompt = c("  ➜  ta réponse > ", GRAS)

    while True:
        try:
            rep = input(prompt).strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return "quit"
        low = rep.lower()

        # --- commandes ---
        if low in ("q", "quit"):
            return "quit"
        if low in ("p", "passe", "passer", "skip"):
            print(c("  ⏭  Manche passée.", J))
            return "passe"
        if low in ("i", "indice"):
            if nb_indices < len(defi["indices"]):
                print(c(f"  💡 Indice {nb_indices + 1}/3 : ", J) + defi["indices"][nb_indices])
                nb_indices += 1
            else:
                print(c("  Plus d'indices. Tape 'sol' pour voir la solution.", J))
            continue
        if low in ("sol", "solution"):
            if nb_indices < len(defi["indices"]):
                restants = len(defi["indices"]) - nb_indices
                print(c(f"  Cherche encore un peu — prends d'abord tes indices "
                        f"({restants} dispo, tape 'i').", J))
                continue
            print(c("  📖 Solution :", B))
            for ligne in defi["solution"].splitlines():
                print(c("     " + ligne, C))
            return "sol"

        # --- tentative ---
        if defi["type"] == "ecrire":
            resultat = moteur.evaluer(defi)  # teste reponse.py (rep ignoré)
        else:
            if rep == "":
                print(c("  (tape ta réponse, ou 'i' pour un indice)", OFF))
                continue
            resultat = moteur.evaluer(defi, rep)

        if resultat["correct"]:
            session["combo"] += 1
            mult = multiplicateur(session["combo"])
            gagnes = moteur.points_manche(defi, nb_indices, mult)
            session["points"] += gagnes
            etat["score_total"] += gagnes
            if defi["id"] not in etat["defis_reussis"]:
                etat["defis_reussis"].append(defi["id"])
            etat["record_streak"] = max(etat["record_streak"], session["combo"])
            bravo = "SWISH !" if nb_indices == 0 else "Panier bon !"
            extra = c(f"  ×{mult}", J) if mult > 1 else ""
            print(c(f"  🏀 {bravo}  +{gagnes} pts{OFF}", V + GRAS) + extra)
            return "reussi"
        else:
            session["combo"] = 0  # buzzer : le combo tombe
            print(c("  ⛔ BUZZER — pas encore.", R) +
                  (("  " + resultat["detail"]) if resultat["detail"] else ""))
            if defi["type"] == "ecrire":
                print(c("     Corrige reponse.py, sauvegarde, puis Entrée. (i pour un indice)", OFF))
            else:
                print(c("     Réessaie, ou tape 'i' pour un indice.", OFF))
            continue


# ===========================================================================
# BILAN
# ===========================================================================
def ecran_bilan(etat, session):
    print()
    barre("═")
    print(c("   🏀  FIN DE SESSION", GRAS + J))
    barre()
    print(f"   Manches réussies   : {c(session['reussies'], GRAS + V)}/{session['jouees']}")
    print(f"   Points de la session : {c(session['points'], GRAS + C)}")
    print(f"   Meilleur combo       : {session['meilleur_combo']}")
    print()
    print(f"   Score de saison      : {c(etat['score_total'], GRAS)}  "
          f"(niveau {etat['niveau']})")
    print(f"   Record streak saison : {etat['record_streak']}")
    reussis = len(etat["defis_reussis"])
    total = len(banque.DEFIS)
    print(f"   Gammes validées      : {reussis}/{total}")
    if reussis < total:
        print(c(f"   Il te reste {total - reussis} défis à débloquer. Reviens t'entraîner !", J))
    else:
        print(c("   Toutes les gammes validées — prêt pour la phase 2 (briques neuves) 💪", V))
    barre("═")
    print()


# ===========================================================================
# BOUCLE PRINCIPALE
# ===========================================================================
def main():
    etat = moteur.charger_etat()
    ecran_accueil(etat)
    session = {"points": 0, "combo": 0, "jouees": 0, "reussies": 0, "meilleur_combo": 0}
    vus = []

    try:
        input(c("\n   Entrée pour lancer la première manche… ", GRAS))
    except (EOFError, KeyboardInterrupt):
        print()
        return

    while True:
        defi = moteur.choisir_defi(etat, vus)
        if defi is None:
            print("Aucun défi disponible.")
            break

        issue = jouer_manche(defi, etat, session)
        vus.append(defi["id"])
        etat["derniere_brique"] = defi["brique"]

        if issue != "quit":
            session["jouees"] += 1
        if issue == "reussi":
            session["reussies"] += 1
        session["meilleur_combo"] = max(session["meilleur_combo"], session["combo"])

        moteur.sauver_etat(etat)  # on sauve après chaque manche

        if issue == "quit":
            break

    ecran_bilan(etat, session)


if __name__ == "__main__":
    main()
