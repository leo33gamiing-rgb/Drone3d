"""Énigme sonore en boucle : un message en morse joué au violon (vrai enregistrement, CC0),
sur un fond sonore angoissant continu, avec une longue pause avant chaque reprise.

Points et traits : la note la plus grave du violon (sol, 196 Hz) jouée à l'archet ;
seule la durée change (court = point, long = trait), comme du vrai morse.
Fond : ventilation réelle ralentie (grondement) + nappe sombre de l'app, sans aucun rythme.
Sources (CC0) : violon solo de VSCO 2 Community Edition (Versilian Studios,
https://github.com/sgossner/VSCO-2-CE) ; ventilation de Benjamin Burnes via
https://github.com/lavenderdotpet/cc0-public-domain-sounds.

Lancement : python3 fabriquer_morse.py /chemin/cc0-public-domain-sounds /chemin/VSCO-2-CE [MESSAGE]
"""
import os
import sys

import numpy as np

from dsp import (SR, Piste, boucler, exporter, n_ech, normaliser, passe_bas, passe_haut, reverb, stereo,
                 vitesse)
from enregistrer_recit import ecrire
from importer_cc0 import lire

RACINE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
SONS = os.path.join(RACINE, 'sons')

MORSE = {
    'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.', 'F': '..-.', 'G': '--.', 'H': '....', 'I': '..',
    'J': '.---', 'K': '-.-', 'L': '.-..', 'M': '--', 'N': '-.', 'O': '---', 'P': '.--.', 'Q': '--.-', 'R': '.-.',
    'S': '...', 'T': '-', 'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-', 'Y': '-.--', 'Z': '--..',
    '0': '-----', '1': '.----', '2': '..---', '3': '...--', '4': '....-', '5': '.....', '6': '-....',
    '7': '--...', '8': '---..', '9': '----.',
}

# Rythme (secondes) : un trait dure trois fois un point, pauses nettes pour pouvoir décoder.
POINT = 0.3
TRAIT = 0.9
ENTRE_SIGNES = 0.3
ENTRE_LETTRES = 1.5
AVANT_REPRISE = 6.0

VIOLON = 'Strings/Solo Violin/Arco Vib/LLVln_ArcoVib_G3_f.wav'
VENTILATION = 'bb - Fans and Drones (Jul 2021)/Air Vent.wav'


def tenir(x, duree, attaque=0.02, relache=0.08):
    """Coupe un son à `duree` secondes avec une attaque et une fin douces."""
    x = stereo(x)[:, :n_ech(duree)].copy()
    a, r = n_ech(attaque), n_ech(relache)
    x[:, :a] *= np.linspace(0, 1, a)
    x[:, -r:] *= np.linspace(1, 0, r)
    return x


def note_stable(chemin):
    """Passage le plus régulier de la note tenue à l'archet, au volume aplani : un seul bloc de son."""
    corde = lire(chemin)
    fenetre = n_ech(0.05)
    enveloppe = np.sqrt(np.convolve(corde.mean(axis=0) ** 2, np.ones(fenetre) / fenetre, 'same')) + 1e-6
    n = n_ech(TRAIT + 0.2)
    debuts = range(n_ech(1), corde.shape[1] - n, n_ech(0.05))
    debut = min(debuts, key=lambda i: np.std(enveloppe[i:i + n]) / np.mean(enveloppe[i:i + n]))
    morceau = corde[:, debut:debut + n]
    aplani = np.clip(np.mean(enveloppe[debut:debut + n]) / enveloppe[debut:debut + n], 0.5, 2.0)
    return normaliser(morceau * aplani)


def signes(vsco):
    note = note_stable(os.path.join(vsco, VIOLON))
    # Coup d'archet court (point) ou long (trait), avec une attaque franche.
    return (normaliser(tenir(note, POINT, attaque=0.015, relache=0.07)),
            normaliser(tenir(note, TRAIT, attaque=0.015, relache=0.1)))


def fond(collection, duree):
    souffle = lire(os.path.join(collection, VENTILATION))
    grondement = passe_bas(passe_haut(vitesse(souffle, 0.6), 35), 1200, 4)[:, :n_ech(duree + 3)]  # sans clics
    nappe = lire(os.path.join(SONS, 'ambiances/nappe-sombre.ogg'))
    nappe = np.tile(nappe, (1, 2))[:, :n_ech(duree + 3)]
    x = normaliser(grondement) * 0.7 + normaliser(passe_bas(nappe, 900)) * 0.5
    return boucler(x, 3)


def cycle(message, collection, vsco):
    point, trait = signes(vsco)
    evenements, t = [], 0.0
    for i, lettre in enumerate(message):
        for j, signe in enumerate(MORSE[lettre]):
            evenements.append((t, signe))
            t += (POINT if signe == '.' else TRAIT) + (ENTRE_SIGNES if j < len(MORSE[lettre]) - 1 else 0)
        if i < len(message) - 1:
            t += ENTRE_LETTRES
    duree = round(t + AVANT_REPRISE, 1)
    morse = Piste(duree, boucle=True)
    for debut, signe in evenements:
        morse.ajouter(point if signe == '.' else trait, debut + 0.5)
    morse = reverb(morse.x, 0.9, 0.12, boucle=True)  # écho léger : les sons restent nets
    total = Piste(duree, boucle=True)
    total.ajouter(normaliser(morse, 0.9), 0)
    total.ajouter(fond(collection, duree), 0, 0.11)
    return total.x, duree


def fabriquer(collection, vsco, message='ABEFU'):
    message = message.upper().replace(' ', '')
    x, duree = cycle(message, collection, vsco)
    nom = f'morse-{message.lower()}'
    os.makedirs(os.path.join(SONS, 'enigmes'), exist_ok=True)
    exporter(x, os.path.join(SONS, 'enigmes', f'{nom}.ogg'), qualite=0.6)
    repetitions = int(np.ceil(300 / duree))  # ~5 minutes pour la version à télécharger
    ecrire(np.tile(x, (1, repetitions)), os.path.join(RACINE, 'recits', f'{nom}.mp3'), 'MP3', 'MPEG_LAYER_III')
    lettres = ' '.join(message)
    with open(os.path.join(SONS, 'catalogue-enigmes.js'), 'w', encoding='utf-8') as f:
        f.write("'use strict';\n// Énigmes sonores fabriquées par outils/fabrique/fabriquer_morse.py.\n"
                f"const CATALOGUE_ENIGMES = [\n  {{ cat: 'enigme', fichier: 'sons/enigmes/{nom}.ogg', "
                f"nom: 'Code morse au violon : {lettres}' }},\n];\n")
    with open(os.path.join(SONS, 'enigmes', 'CREDITS.txt'), 'w', encoding='utf-8') as f:
        f.write('Sons réels CC0 (domaine public) :\n'
                f'  Violon : VSCO 2 Community Edition, Versilian Studios (https://github.com/sgossner/VSCO-2-CE)\n    {VIOLON}\n'
                '  Fond : Benjamin Burnes (abstractionmusic.com), via https://github.com/lavenderdotpet/cc0-public-domain-sounds\n'
                f'    {VENTILATION}\n')
    print(f'{message} : cycle de {duree} s, version téléchargeable de {repetitions} cycles')


if __name__ == '__main__':
    fabriquer(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else 'ABEFU')
