"""Enregistre le récit de la policière : voix de synthèse neuronale (Kokoro, voix féminine française
« ff_siwis »), vrais cris et respirations (CC0) et bruitages, dans l'acoustique d'une salle de bain.

Modèle (licence Apache 2.0) : fichiers kokoro-v1.0.onnx et voices-v1.0.bin de
https://github.com/thewh1teagle/kokoro-onnx/releases/tag/model-files-v1.0
Lancement : python3 enregistrer_recit.py /dossier/du/modele   (paquets : kokoro-onnx soundfile scipy)
"""
import os
import sys

import numpy as np
import soundfile as sf
from scipy import signal

from dsp import SR, Piste, couper_silence, n_ech, normaliser, passe_bas, reverb, saturer, stereo, temps, vitesse
from importer_cc0 import lire

RACINE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
SONS = os.path.join(RACINE, 'sons')

# Façons de dire : vitesse de parole, volume, tremblement de la voix, hauteur, voix étouffée.
STYLES = {
    'voix': dict(vitesse=0.9, gain=0.75, tremble=0.1),
    'faible': dict(vitesse=0.82, gain=0.5, tremble=0.2, etouffe=True),
    'tremble': dict(vitesse=0.86, gain=0.68, tremble=0.55),
    'supplie': dict(vitesse=0.85, gain=0.8, tremble=0.6, hauteur=1.03),
    'souffle': dict(vitesse=0.8, gain=0.4, tremble=0.3, etouffe=True),
    'ferme': dict(vitesse=0.95, gain=0.85, tremble=0.0),
    'cri': dict(vitesse=1.15, gain=1.0, tremble=0.2, hauteur=1.06, crie=True),
}

SOUFFLE = 'reels/bruitages/souffle-coupe-femme.ogg'
DOULEUR = 'reels/screamers/cri-femme-douleur.ogg'

RECIT = [
    ('son', 'reels/screamers/cri-femme-chute.ogg', 1.0),
    ('pause', 0.1),
    ('cri', 'Arrêtez !'), ('pause', 0.25), ('cri', 'Arrêtez…'), ('pause', 0.2), ('cri', 'Je suis encore vivante !'),
    ('son', DOULEUR, 0.5), ('pause', 0.3),
    ('son', SOUFFLE, 0.7), ('pause', 0.2), ('son', 'reels/bruitages/souffle-rauque.ogg', 0.5), ('pause', 0.3),
    ('son', SOUFFLE, 0.5), ('pause', 1.5),
    ('faible', "C'est ce que je leur ai dit."), ('pause', 1.0),
    ('faible', "Comme s'ils ne le savaient pas…"), ('pause', 3.0),
    ('voix', "Ils m'avaient attachée dans une baignoire."), ('pause', 0.7),
    ('voix', 'Le bandeau me collait aux yeux.'), ('pause', 0.7),
    ('tremble', 'Je ne voyais pas leurs visages…'), ('pause', 0.4),
    ('tremble', 'je ne savais jamais lequel allait me toucher.'), ('pause', 1.2),
    ('fond', 'reels/bruitages/chaise-roulettes.ogg', 0.35),
    ('voix', "J'entendais quelqu'un déplacer une chaise."), ('pause', 0.9),
    ('voix', "Il s'est assis à côté de moi."), ('pause', 1.0),
    ('faible', 'Il allait rester là.'), ('pause', 1.6),
    ('son', 'reels/bruitages/souffle-rauque.ogg', 0.25), ('pause', 0.8),
    ('son', 'reels/bruitages/couteau-degaine.ogg', 0.5), ('pause', 0.3),
    ('tremble', 'Le premier coup de couteau…'), ('pause', 0.5), ('tremble', 'dans le ventre…'), ('pause', 0.5),
    ('voix', "je n'ai pas compris tout de suite."), ('pause', 1.0),
    ('voix', "J'ai senti mon corps se raidir."), ('pause', 0.6),
    ('voix', "J'ai essayé de me recroqueviller, mais les liens me retenaient."), ('pause', 1.0),
    ('tremble', 'Et puis la douleur est arrivée.'), ('pause', 1.4),
    ('voix', "Je lui ai demandé d'enlever sa main."), ('pause', 0.5),
    ('tremble', 'Je ne savais même pas ce que je disais…'), ('pause', 0.4),
    ('voix', 'je répétais :'), ('pause', 0.4),
    ('supplie', 'Enlevez votre main.'), ('pause', 0.6), ('supplie', "S'il vous plaît."), ('pause', 0.8),
    ('son', SOUFFLE, 0.45), ('pause', 0.6), ('son', SOUFFLE, 0.4), ('pause', 0.8),
    ('tremble', "Il m'a pris la main."), ('pause', 0.9),
    ('tremble', "Pendant qu'un autre recommençait."), ('pause', 1.0),
    ('faible', 'Il me tenait les doigts…'), ('pause', 0.5),
    ('faible', "comme quelqu'un qui aurait voulu me rassurer."), ('pause', 0.6),
    ('son', DOULEUR, 0.3), ('pause', 1.0),
    ('tremble', "Quand je criais, ils me plongeaient la tête sous l'eau."),
    ('son', 'reels/bruitages/eclaboussure-1.ogg', 0.6), ('fond', 'reels/bruitages/bulles.ogg', 0.3), ('pause', 0.5),
    ('voix', "Je ne pouvais même pas crier jusqu'au bout."), ('pause', 1.0),
    ('tremble', 'Ils me remontaient…'), ('pause', 0.4),
    ('tremble', "j'essayais de reprendre de l'air, de leur parler…"), ('pause', 0.4),
    ('voix', "et je sentais qu'ils se rapprochaient encore."), ('pause', 1.0),
    ('faible', "J'attendais le prochain coup."), ('pause', 0.8),
    ('faible', 'Je ne voyais rien.'), ('pause', 0.6), ('faible', "Je ne pouvais que l'attendre."), ('pause', 3.0),
    ('voix', 'À un moment, ils se sont arrêtés.'), ('pause', 0.8),
    ('fond', 'reels/bruitages/robinet.ogg', 0.3),
    ('voix', "J'entendais seulement le robinet."), ('pause', 0.7),
    ('voix', "Quelqu'un fouillait dans mes affaires."), ('pause', 1.0),
    ('voix', 'Puis mon téléphone a sonné.'), ('pause', 0.3),
    ('fond', 'bruitages/telephone.ogg', 0.3), ('pause', 2.0),
    ('tremble', "C'était ma mère."), ('pause', 0.6), ('tremble', 'Je reconnaissais sa sonnerie.'), ('pause', 0.8),
    ('voix', "Ils l'ont laissé sonner, juste à côté de moi."), ('pause', 1.0),
    ('voix', "J'ai dit :"), ('pause', 0.3), ('supplie', 'Décrochez…'), ('pause', 0.4),
    ('supplie', 'dites-lui de venir me chercher.'), ('pause', 1.0),
    ('faible', "Je savais qu'elle ne pouvait pas."), ('pause', 0.8),
    ('tremble', "Mais je voulais qu'elle vienne me chercher."), ('pause', 0.5),
    ('son', SOUFFLE, 0.35), ('pause', 0.5), ('son', DOULEUR, 0.2), ('pause', 1.2),
    ('souffle', "L'un d'eux s'est penché contre mon oreille."), ('pause', 0.7),
    ('souffle', 'Il a dit :'), ('pause', 0.3), ('souffle', 'On va terminer. Ne bouge plus.'), ('pause', 1.0),
    ('voix', "J'ai cru qu'il allait me détacher."), ('pause', 0.8),
    ('tremble', 'Même après tout ça…'), ('pause', 0.5), ('tremble', "pendant une seconde, je l'ai cru."), ('pause', 0.8),
    ('son', SOUFFLE, 0.6), ('pause', 1.5),
    ('voix', "Puis ils m'ont remise sous l'eau."),
    ('son', 'reels/bruitages/eclaboussure-2.ogg', 0.5), ('fond', 'reels/bruitages/bulles.ogg', 0.3), ('pause', 0.8),
    ('faible', "Cette fois, ils ne m'ont pas remontée."), ('pause', 1.2),
    ('tremble', "J'essayais encore de bouger les doigts…"), ('pause', 0.4),
    ('tremble', "pour qu'ils comprennent que j'étais toujours là."), ('pause', 1.0),
    ('faible', "Jusqu'au bout, j'ai attendu qu'on me laisse respirer."), ('pause', 4.0),
    ('ferme', "J'étais policière."), ('pause', 0.8),
    ('ferme', "J'avais découvert une organisation qui faisait disparaître des gens."), ('pause', 0.7),
    ('ferme', 'Ils organisaient leurs mises à mort…'), ('pause', 0.5), ('ferme', 'ils les filmaient.'), ('pause', 1.0),
    ('ferme', "J'avais trouvé des noms."), ('pause', 0.5), ('ferme', 'Des preuves.'), ('pause', 0.8),
    ('voix', "Ils m'ont capturée avant que je puisse les transmettre."), ('pause', 1.5),
    ('voix', "Pendant le trajet, j'avais les yeux bandés."), ('pause', 0.6),
    ('voix', "Ils m'ont sortie du véhicule, puis forcée à prendre un escalier."), ('pause', 0.8),
    ('tremble', 'Je me souviens des marches…'), ('pause', 0.4), ('tremble', 'de leurs mains sur mes bras.'), ('pause', 0.8),
    ('faible', 'Mais je ne sais plus si je montais ou si je descendais.'), ('pause', 1.5),
    ('voix', 'Il y a une chose dont je suis sûre.'), ('pause', 0.6),
    ('voix', "Je les ai entendus parler des preuves, des documents qu'ils m'avaient pris."), ('pause', 0.7),
    ('voix', "Ils les avaient laissés dans une salle d'eau."), ('pause', 0.9),
    ('tremble', 'Les indices étaient là…'), ('pause', 0.5), ('tremble', "dans une salle d'eau."), ('pause', 1.0),
    ('faible', 'Mais les escaliers…'), ('pause', 1.2),
    ('son', SOUFFLE, 0.35), ('pause', 0.8),
    ('souffle', 'Je ne me souviens plus.'), ('pause', 3.0),
]


def trembler(x, force):
    """Voix qui tremble : légères variations de hauteur et de volume."""
    if not force:
        return x
    n = len(x)
    t = np.arange(n) / SR
    taux = 1 + force * 0.012 * np.sin(2 * np.pi * 4.7 * t + np.random.uniform(0, 6))
    positions = np.cumsum(taux)
    positions = positions[positions < n - 1]
    y = np.interp(positions, np.arange(n), x)
    return y * (1 - force * 0.35 * (0.5 + 0.5 * np.sin(2 * np.pi * 5.3 * t[:len(y)])))


def dire(kokoro, texte, style):
    p = STYLES[style]
    s, taux = kokoro.create(texte, voice='ff_siwis', speed=p['vitesse'], lang='fr-fr')
    x = normaliser(signal.resample_poly(s, SR // 300, taux // 300))
    x = couper_silence(x, -45)[0]
    if p.get('hauteur'):
        x = vitesse(x, p['hauteur'])
    x = trembler(x, p['tremble'])
    if p.get('etouffe'):
        x = passe_bas(x, 5000)
    if p.get('crie'):
        x = saturer(normaliser(x), 1.8)
    return normaliser(x) * p['gain']


def enregistrer(dossier_modele):
    from kokoro_onnx import Kokoro
    kokoro = Kokoro(os.path.join(dossier_modele, 'kokoro-v1.0.onnx'), os.path.join(dossier_modele, 'voices-v1.0.bin'))
    np.random.seed(7)
    voix, bruitages = Piste(), Piste()
    curseur = 0.5
    for element in RECIT:
        genre = element[0]
        if genre == 'pause':
            curseur += element[1]
        elif genre in ('son', 'fond'):
            x = normaliser(lire(os.path.join(SONS, element[1]))) * element[2]
            bruitages.ajouter(x, curseur)
            if genre == 'son':
                curseur += x.shape[1] / SR
        else:
            x = dire(kokoro, element[1], genre)
            voix.ajouter(x, curseur)
            curseur += len(x) / SR
            print(f'{curseur:6.1f} s  {genre:8s} {element[1]}')
    duree = curseur + 1.0
    # Salle de bain carrelée : réverbération courte et claire.
    v = reverb(voix.x, 0.8, 0.22, sombre=0.2)
    b = reverb(bruitages.x, 0.8, 0.2, sombre=0.2)
    fond = lire(os.path.join(SONS, 'ambiances/nappe-sombre.ogg'))
    nappe = np.tile(fond, (1, int(np.ceil(duree * SR / fond.shape[1])) + 1))[:, :n_ech(duree)]
    nappe = passe_bas(nappe, 600)  # garde le grondement, retire le sifflement aigu de la nappe
    nappe *= np.minimum(1, np.minimum(temps(duree) / 4, (duree - temps(duree)) / 4))  # fondus
    total = Piste(duree)
    total.ajouter(v, 0)
    total.ajouter(b, 0)
    total.ajouter(nappe, 0, 0.12)
    x = normaliser(total.x[:, :n_ech(duree)], 0.95)
    return x


def ecrire(x, chemin, format_, sous_type):
    with sf.SoundFile(chemin, 'w', SR, 2, format=format_, subtype=sous_type) as f:
        st = np.clip(stereo(x), -1, 1).T.astype(np.float32)
        for i in range(0, len(st), 16384):
            f.write(st[i:i + 16384])


if __name__ == '__main__':
    x = enregistrer(sys.argv[1])
    os.makedirs(os.path.join(SONS, 'recits'), exist_ok=True)
    ecrire(x, os.path.join(SONS, 'recits', 'recit-policiere.ogg'), 'OGG', 'VORBIS')
    ecrire(x, os.path.join(RACINE, 'recits', 'recit-policiere.mp3'), 'MP3', 'MPEG_LAYER_III')
    with open(os.path.join(SONS, 'catalogue-recits.js'), 'w', encoding='utf-8') as f:
        f.write("'use strict';\n// Récits enregistrés par outils/fabrique/enregistrer_recit.py.\nconst CATALOGUE_RECITS = [\n"
                "  { cat: 'recit', fichier: 'sons/recits/recit-policiere.ogg', nom: 'Récit de la policière' },\n];\n")
    print(f'Durée : {x.shape[1] / SR / 60:.1f} min')
