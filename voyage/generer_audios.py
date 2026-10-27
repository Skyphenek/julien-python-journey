"""Génère les MP3 du vocabulaire (static/audio/<langue>/<clé>.mp3) avec les voix neuronales
de Microsoft via edge-tts. À relancer après avoir ajouté ou corrigé une phrase dans vocabulaire.py.

Outil de développement (pas sur le serveur) :
    python3 -m venv /tmp/tts && /tmp/tts/bin/pip install edge-tts
    /tmp/tts/bin/python3 generer_audios.py            # ne refait que ce qui a changé
    /tmp/tts/bin/python3 generer_audios.py --tout     # refait tout

static/audio/textes.json garde, pour chaque fichier, la voix et le texte qui l'ont produit :
un test vérifie que les MP3 correspondent toujours à vocabulaire.py.
"""
import argparse
import asyncio
import json
from pathlib import Path

import edge_tts

from vocabulaire import LANGUES, cles_audio, fichier_audio, texte_a_dire

DOSSIER = Path(__file__).parent / "static"
INDEX = DOSSIER / "audio" / "textes.json"
DEBIT = "-15%"                                   # un peu plus lent que la normale : pour apprendre


def a_produire():
    """{chemin relatif: [voix, texte]} pour toutes les phrases de toutes les langues."""
    return {fichier_audio(code, cle): [langue["neurale"], texte_a_dire(ecrit, code)]
            for code, langue in LANGUES.items() for cle, ecrit in cles_audio(code)}


async def generer(tout):
    attendu = a_produire()
    deja = json.loads(INDEX.read_text()) if INDEX.exists() and not tout else {}
    a_faire = {chemin: v for chemin, v in attendu.items()
               if deja.get(chemin) != v or not (DOSSIER / chemin).exists()}
    print(f"{len(a_faire)} fichier(s) à générer sur {len(attendu)}")
    fait = {chemin: v for chemin, v in deja.items() if chemin in attendu and chemin not in a_faire}
    echecs = []
    try:
        for i, (chemin, (voix, texte)) in enumerate(sorted(a_faire.items()), start=1):
            cible = DOSSIER / chemin
            cible.parent.mkdir(parents=True, exist_ok=True)
            for essai in range(3):                              # le service refuse parfois un instant
                try:
                    await edge_tts.Communicate(texte, voix, rate=DEBIT).save(str(cible))
                    fait[chemin] = [voix, texte]
                    break
                except edge_tts.exceptions.NoAudioReceived:
                    await asyncio.sleep(5 * (essai + 1))
            else:
                echecs.append(f"{chemin} : {texte}")
            if i % 50 == 0:
                print(f"  {i}/{len(a_faire)}")
    finally:                                                    # interrompu : la relance reprendra ici
        INDEX.parent.mkdir(parents=True, exist_ok=True)
        INDEX.write_text(json.dumps(fait, ensure_ascii=False, indent=1, sort_keys=True))
    if echecs:
        print(f"{len(echecs)} refusé(s) par le service :", *echecs, sep="\n  ")
    for orphelin in set(deja) - set(attendu):                  # phrase retirée : son fichier aussi
        (DOSSIER / orphelin).unlink(missing_ok=True)

if __name__ == "__main__":
    arguments = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    arguments.add_argument("--tout", action="store_true")
    asyncio.run(generer(arguments.parse_args().tout))
