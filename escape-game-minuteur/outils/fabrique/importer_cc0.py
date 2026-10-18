"""Ajoute à l'application de vrais enregistrements libres de droit (CC0, domaine public).

Source : la collection https://github.com/lavenderdotpet/cc0-public-domain-sounds (licence CC0 1.0),
qui regroupe les packs CC0 de Warfork (Team Forbidden), rubberduck (OpenGameArt), Benjamin Burnes
et Kenney. Les sons sont seulement recadrés, mis au même volume et convertis en OGG.

Lancement : python3 importer_cc0.py /chemin/vers/cc0-public-domain-sounds
"""
import os
import subprocess
import sys

import numpy as np
import soundfile as sf
from scipy import signal

from dsp import SR, boucler, couper_silence, exporter, normaliser, stereo

DOSSIER = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'sons')
DEPOT = 'https://github.com/lavenderdotpet/cc0-public-domain-sounds'

WARFORK = 'Warfork, Team Forbidden'
RUBBERDUCK = 'rubberduck (OpenGameArt)'
BURNES = 'Benjamin Burnes (abstractionmusic.com)'
KENNEY = 'Kenney (kenney.nl)'
MISSLAV = 'MissLav'

# (fichier source dans la collection, fichier de destination, nom affiché, catégorie, auteur, traitement)
SONS = [
    # ----- Screamers -----
    ('warfork-cc0/sounds/players/female/death.ogg', 'cri-femme-mort.ogg', 'Cri de femme (mort)', 'screamer', WARFORK, 'fort'),
    ('warfork-cc0/sounds/players/female/falldeath.ogg', 'cri-femme-chute.ogg', 'Cri de femme (long)', 'screamer', WARFORK, 'fort'),
    ('warfork-cc0/sounds/players/female/pain100.ogg', 'cri-femme-douleur.ogg', 'Cri de douleur (femme)', 'screamer', WARFORK, 'fort'),
    ('warfork-cc0/sounds/players/male/death.ogg', 'cri-homme-mort.ogg', "Cri d'homme (mort)", 'screamer', WARFORK, 'fort'),
    ('warfork-cc0/sounds/players/male/falldeath.ogg', 'cri-homme-chute.ogg', "Cri d'homme (long)", 'screamer', WARFORK, 'fort'),
    ('80-CC0-creature-SFX/scream_01.ogg', 'hurlement-creature-1.ogg', 'Hurlement de créature 1', 'screamer', RUBBERDUCK, 'fort'),
    ('80-CC0-creature-SFX/scream_02.ogg', 'hurlement-creature-2.ogg', 'Hurlement de créature 2', 'screamer', RUBBERDUCK, 'fort'),
    ('80-CC0-creature-sfx-2/die_02.ogg', 'agonie-1.ogg', "Cri d'agonie 1", 'screamer', RUBBERDUCK, 'fort'),
    ('80-CC0-creature-sfx-2/die_03.ogg', 'agonie-2.ogg', "Cri d'agonie 2", 'screamer', RUBBERDUCK, 'fort'),
    ('80-CC0-creature-sfx-2/die_04.ogg', 'agonie-3.ogg', "Cri d'agonie 3", 'screamer', RUBBERDUCK, 'fort'),
    ('80-CC0-creature-sfx-2/human_03.ogg', 'rale-humain-1.ogg', 'Râle humain 1', 'screamer', RUBBERDUCK, 'fort'),
    ('80-CC0-creature-sfx-2/human_07.ogg', 'rale-humain-2.ogg', 'Râle humain 2', 'screamer', RUBBERDUCK, 'fort'),
    ('80-CC0-creature-sfx-2/roar_04.ogg', 'rugissement-1.ogg', 'Rugissement 1', 'screamer', RUBBERDUCK, 'fort'),
    ('80-CC0-creature-sfx-2/roar_05.ogg', 'rugissement-2.ogg', 'Rugissement 2', 'screamer', RUBBERDUCK, 'fort'),
    ('80-CC0-creature-SFX/howl.ogg', 'hurlement.ogg', 'Hurlement', 'screamer', RUBBERDUCK, 'fort'),
    ('80-CC0-creature-SFX/monster_04.ogg', 'monstre-1.ogg', 'Monstre 1', 'screamer', RUBBERDUCK, 'fort'),
    ('80-CC0-creature-SFX/monster_07.ogg', 'monstre-2.ogg', 'Monstre 2', 'screamer', RUBBERDUCK, 'fort'),
    ('80-CC0-creature-sfx-2/monster_12.ogg', 'monstre-3.ogg', 'Monstre 3', 'screamer', RUBBERDUCK, 'fort'),
    ('BB_2HTC Samples Vol 4/Weird/2022-08-10 I Should Be Sleeping - Growly.wav', 'grognement-monstrueux.ogg',
     'Grognement monstrueux', 'screamer', BURNES, 'fort'),
    ('BB_Retail Therapy Sample Pack/Monster Noise 2.wav', 'bete-1.ogg', 'Bête 1', 'screamer', BURNES, 'fort'),
    ('BB_Retail Therapy Sample Pack/Monster Noise 8.wav', 'bete-2.ogg', 'Bête 2', 'screamer', BURNES, 'fort'),
    ('Micro Pack - Kitchen Knives/Unpleasant Scraping 1.wav', 'raclement-strident.ogg', 'Raclement strident', 'screamer', BURNES, 'fort'),
    ('75-cc0-breaking-falling-hit-sfx/bfh1_glass_breaking_01.ogg', 'verre-brise.ogg', 'Verre brisé', 'screamer', RUBBERDUCK, 'fort'),
    ('bb - Novice Cello (Nov 2021)/C2 - Sforzando 1.wav', 'violoncelle-brutal.ogg', 'Coup de violoncelle', 'screamer', BURNES, 'fort'),
    # ----- Portes -----
    ('kenney_rpgaudio/Audio/creak1.ogg', 'grincement-1.ogg', 'Grincement 1', 'porte', KENNEY, 'moyen'),
    ('kenney_rpgaudio/Audio/creak2.ogg', 'grincement-2.ogg', 'Grincement 2', 'porte', KENNEY, 'moyen'),
    ('kenney_rpgaudio/Audio/creak3.ogg', 'grincement-3.ogg', 'Grincement 3', 'porte', KENNEY, 'moyen'),
    ('kenney_rpgaudio/Audio/doorOpen_1.ogg', 'porte-ouverture.ogg', "Porte qu'on ouvre", 'porte', KENNEY, 'moyen'),
    ('kenney_rpgaudio/Audio/doorClose_4.ogg', 'porte-fermeture.ogg', "Porte qu'on ferme", 'porte', KENNEY, 'moyen'),
    # ----- Bruitages -----
    ('warfork-cc0/sounds/players/female/gasp.ogg', 'souffle-coupe-femme.ogg', 'Souffle coupé (femme)', 'bruitage', WARFORK, 'moyen'),
    ('80-CC0-creature-sfx-2/breath_02.ogg', 'souffle-rauque.ogg', 'Souffle rauque', 'bruitage', RUBBERDUCK, 'moyen'),
    ('Micro Pack - Kitchen Knives/Big Knife - Unsheath 1.wav', 'couteau-degaine.ogg', "Couteau qu'on dégaine", 'bruitage', BURNES, 'moyen'),
    ('Micro Pack - Kitchen Knives/Big Knife - Scrape 3.wav', 'lame-qui-racle.ogg', 'Lame qui racle', 'bruitage', BURNES, 'moyen'),
    ('Micro Pack - Kitchen Knives/Unpleasant Scraping 3.wav', 'raclement-long.ogg', 'Raclement long', 'bruitage', BURNES, 'moyen'),
    ('MissLavs Sounds/chairwheel.ogg', 'chaise-roulettes.ogg', 'Chaise à roulettes', 'bruitage', MISSLAV, 'moyen'),
    ('40-cc0-water-splash-slime-sfx/splash_07.ogg', 'eclaboussure-1.ogg', "Éclaboussure d'eau 1", 'bruitage', RUBBERDUCK, 'moyen'),
    ('40-cc0-water-splash-slime-sfx/splash_03.ogg', 'eclaboussure-2.ogg', "Éclaboussure d'eau 2", 'bruitage', RUBBERDUCK, 'moyen'),
    ('40-cc0-water-splash-slime-sfx/loop_bubbles_1.ogg', 'bulles.ogg', 'Bulles', 'bruitage', RUBBERDUCK, 'moyen'),
    ('75-cc0-breaking-falling-hit-sfx/bfh1_glass_breaking_03.ogg', 'verre-brise-2.ogg', 'Verre brisé 2', 'bruitage', RUBBERDUCK, 'moyen'),
    ('75-cc0-breaking-falling-hit-sfx/bfh1_breaking_01.ogg', 'objet-brise.ogg', 'Objet qui se brise', 'bruitage', RUBBERDUCK, 'moyen'),
    ('bb - Fans and Drones (Jul 2021)/Sink and Faucet.wav', 'robinet.ogg', 'Robinet qui coule', 'bruitage', BURNES, 'robinet'),
    # ----- Ambiance -----
    ('bb - Fans and Drones (Jul 2021)/Sink and Faucet.wav', 'robinet-boucle.ogg', 'Robinet qui coule', 'ambiance', BURNES, 'boucle'),
]


def lire(chemin):
    x, taux = sf.read(chemin, always_2d=True)
    x = stereo(x.T if x.shape[1] == 2 else x[:, 0])
    if taux != SR:
        x = signal.resample_poly(x, SR // 100, taux // 100, axis=-1)
    return x


def preparer(x, traitement):
    if traitement == 'boucle':
        return boucler(normaliser(x, 0.5)[:, :int(SR * 58)], 3)  # 55 s bouclables
    if traitement == 'robinet':
        x = x[:, :int(SR * 15)]
        x[:, -int(SR * 1.5):] *= np.linspace(1, 0, int(SR * 1.5))
        return normaliser(x, 0.84)
    x = couper_silence(x, -50)
    debut = np.nonzero(np.abs(x).max(axis=0) > np.abs(x).max() * 0.01)[0][0]
    x = x[:, max(0, debut - 200):]
    return normaliser(x, 0.95 if traitement == 'fort' else 0.84)


def importer(collection):
    commit = subprocess.run(['git', '-C', collection, 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip()
    lignes = [
        "'use strict';",
        "// Vrais enregistrements libres de droit (CC0), ajoutés par outils/fabrique/importer_cc0.py.",
        'const CATALOGUE_REELS = [',
    ]
    credits = [
        'SONS RÉELS LIBRES DE DROIT (CC0 1.0, domaine public)',
        '======================================================',
        f'Collection : {DEPOT} (commit {commit[:12]})',
        'Licence : CC0 1.0 Universal — usage libre, sans attribution obligatoire.',
        'Les fichiers ont seulement été recadrés, mis au même volume et convertis en OGG.',
        '',
    ]
    for source, fichier, nom, cat, auteur, traitement in SONS:
        x = preparer(lire(os.path.join(collection, source)), traitement)
        sous_dossier = 'ambiances' if cat == 'ambiance' else f'{cat}s'
        relatif = f'reels/{sous_dossier}/{fichier}'
        chemin = os.path.join(DOSSIER, relatif)
        os.makedirs(os.path.dirname(chemin), exist_ok=True)
        duree = exporter(x, chemin, qualite=0.6)
        print(f'{relatif:50s} {duree:5.1f} s  <- {source}')
        nom_js = nom.replace("'", "\\'")
        lignes.append(f"  {{ cat: '{cat}', fichier: 'sons/{relatif}', nom: '{nom_js}' }},")
        credits.append(f'sons/{relatif}\n    {auteur} — {source}')
    lignes.append('];')
    with open(os.path.join(DOSSIER, 'catalogue-reels.js'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(lignes) + '\n')
    with open(os.path.join(DOSSIER, 'CREDITS-CC0.txt'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(credits) + '\n')


if __name__ == '__main__':
    importer(sys.argv[1])
