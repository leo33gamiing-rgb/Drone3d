"""Compose des jump scares terrifiants en superposant de vrais enregistrements :
instruments d'orchestre réels (VSCO 2 Community Edition, CC0) et vrais cris (collection CC0).
C'est la méthode des films d'horreur : coup d'orchestre, cordes stridentes, cri, réverbération.

Lancement : python3 composer_jumpscares.py /chemin/cc0-public-domain-sounds /chemin/VSCO-2-CE
"""
import os
import sys

import numpy as np

from dsp import (SR, Piste, couper_silence, exporter, inverser, n_ech, niveau_rms, normaliser, reverb, saturer,
                 stereo, vitesse)
from importer_cc0 import lire

RACINE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
SONS = os.path.join(RACINE, 'sons')
CC0 = VSCO = ''

# Vrais cris (collection CC0)
CRI_FEMME = 'warfork-cc0/sounds/players/female/death.ogg'
CRI_FEMME_LONG = 'warfork-cc0/sounds/players/female/falldeath.ogg'
DOULEUR_FEMME = 'warfork-cc0/sounds/players/female/pain100.ogg'
CRI_HOMME = 'warfork-cc0/sounds/players/male/death.ogg'
CRI_HOMME_LONG = 'warfork-cc0/sounds/players/male/falldeath.ogg'
HURLEMENTS = ['80-CC0-creature-SFX/scream_01.ogg', '80-CC0-creature-SFX/scream_02.ogg']
AGONIES = ['80-CC0-creature-sfx-2/die_02.ogg', '80-CC0-creature-sfx-2/die_03.ogg', '80-CC0-creature-sfx-2/die_04.ogg',
           '80-CC0-creature-sfx-2/human_03.ogg', '80-CC0-creature-sfx-2/human_07.ogg']
RUGISSEMENTS = ['80-CC0-creature-sfx-2/roar_04.ogg', '80-CC0-creature-sfx-2/roar_05.ogg']

# Vrais instruments (VSCO 2 CE)
PIANO = ['Keys/Upright Piano/Player_dyn3_rr1_000.wav', 'Keys/Upright Piano/Player_dyn3_rr1_002.wav',
         'Keys/Upright Piano/Player_dyn3_rr1_004.wav']  # la0, do#1, fa1 (les plus graves)
ORGUE = ['Keys/Organ/Loud/Rode_Pedal_01.wav', 'Keys/Organ/Loud/Rode_Pedal_04.wav', 'Keys/Organ/Loud/Rode_Man3Open_01.wav',
         'Keys/Organ/Loud/Rode_Man3Open_04.wav', 'Keys/Organ/Loud/Rode_Man3Open_07.wav']
VIOLON_AIGU = ['Strings/Solo Violin/Arco Vib/LLVln_ArcoVib_G6_f.wav', 'Strings/Solo Violin/Arco Vib/LLVln_ArcoVib_A6_f.wav',
               'Strings/Solo Violin/Arco Vib/LLVln_ArcoVib_C7_f.wav']
SPICCATO = 'Strings/Violin Section/Spic/VlnEns_Spic_D5_v2_rr1.wav'
TREMOLO = ['Strings/Violin Section/Trem/VlnEns_Trem_D5_v2.wav', 'Strings/Violin Section/Trem/VlnEns_Trem_B4_v2.wav',
           'Strings/Violin Section/Trem/VlnEns_Trem_G4_v2.wav']
CONTREBASSE = 'Strings/Solo Contrabass/Pizz/BKCtbss_Pizz_E0_v3_rr1.wav'
CUIVRES = ['Brass/Tuba/stac/Tuba3_stac_A#0_v2_rr1_Sum.wav', 'Brass/Tenor Trombone/stac/tenortbn_stac_A#1_v4_rr1.wav',
           'Brass/F Horn/stac/MOHorn_stac_A#1_v3_rr1.wav']
GROSSE_CAISSE = ['VSCO 1 Percussion/drums/bass/bdrum3_fff_1.wav', 'VSCO 1 Percussion/drums/bass/bdrum_fff_1.wav']
TIMBALE = 'Percussion/Timpani/Timpani2_Hit_v4_rr1_Sum.wav'
ROULEMENT = 'Percussion/Timpani/Rolls/Timpani1_Roll_v5_rr1_Sum.wav'
GONGS = ['Miscellania Raw/Misc 1/cymb_gong.wav', 'Miscellania Raw/Misc 1/cymb_gong2.wav']
CHAINES = 'Miscellania Raw/Misc 1/chain_grind.wav'
METAL = 'Miscellania Raw/Misc 1/metal_hit1.wav'
VERRE = 'Miscellania Raw/Misc 1/glass_break2.wav'


def cc0(chemin):
    return normaliser(couper_silence(lire(os.path.join(CC0, chemin)), -50))


def vsco(chemin, demarre=True):
    x = lire(os.path.join(VSCO, chemin))
    if demarre:  # commence à l'attaque de la note
        debut = np.nonzero(np.abs(x).max(axis=0) > np.abs(x).max() * 0.02)[0][0]
        x = x[:, max(0, debut - 50):]
    return normaliser(x)


def transposer(x, demi_tons):
    return vitesse(x, 2 ** (demi_tons / 12)) if demi_tons else x


def couper(x, duree, fin=0.3):
    x = stereo(x)[:, :n_ech(duree)].copy()
    f = min(n_ech(fin), x.shape[1])
    x[:, -f:] *= np.linspace(1, 0, f)
    return x


def crescendo(x, duree):
    x = couper(x, duree, 0.02)
    x *= np.linspace(0.03, 1, x.shape[1]) ** 2
    return x


def coup_grave(p, t, gain=1.0):
    """Grosse caisse fortissimo + timbale : l'impact du jump scare."""
    p.ajouter(couper(vsco(GROSSE_CAISSE[0]), 3), t, gain)
    p.ajouter(couper(vsco(TIMBALE), 4, 2), t, gain * 0.7)


JUMPSCARES = []


def jumpscare(fichier, nom):
    def enregistrer(fonction):
        JUMPSCARES.append((fichier, nom, fonction))
        return fonction
    return enregistrer


@jumpscare('piano-et-cri.ogg', 'Piano fracassé et cri de femme')
def _():
    p = Piste()
    for note in PIANO:
        for decalage in (0, 1):  # grappe de notes voisines : dissonance maximale
            p.ajouter(couper(transposer(vsco(note), decalage), 4, 1.5), 0, 0.45)
    coup_grave(p, 0)
    p.ajouter(couper(vsco(GONGS[0], False), 4, 2), 0, 0.5)
    p.ajouter(cc0(CRI_FEMME), 0.03, 1.0)
    p.ajouter(transposer(cc0(CRI_FEMME_LONG), -2), 0.06, 0.6, 0.3)
    return reverb(p.x, 2.2, 0.25)


@jumpscare('violons-psychose.ogg', 'Violons de Psychose (vrais violons)')
def _():
    p = Piste()
    for k in range(12):
        t = k * 0.19
        violon = couper(vsco(VIOLON_AIGU[k % 3]), 0.17, 0.03)
        p.ajouter(violon, t, 1.0, pan=-0.4 if k % 2 else 0.4)
        p.ajouter(couper(transposer(vsco(SPICCATO), 12 + (k % 2)), 0.17, 0.03), t, 0.5)
    p.ajouter(couper(vsco(GROSSE_CAISSE[1]), 2), 0, 0.8)
    return reverb(p.x, 1.8, 0.3)


@jumpscare('tremolo-puis-cri.ogg', 'Trémolo qui monte… puis cri')
def _():
    p = Piste()
    montee = 2.6
    for note, decalage in [(TREMOLO[0], 0), (TREMOLO[0], 1), (TREMOLO[1], 0), (TREMOLO[2], 1)]:
        p.ajouter(crescendo(transposer(vsco(note), decalage), montee), 0, 0.5, pan=np.random.uniform(-0.6, 0.6))
    p.ajouter(crescendo(vsco(ROULEMENT), montee), 0, 0.8)
    coup_grave(p, montee)
    p.ajouter(cc0(CRI_FEMME_LONG), montee + 0.02, 1.0)
    p.ajouter(vsco(VERRE, False), montee, 0.6)
    return reverb(p.x, 2.5, 0.25)


@jumpscare('braam-orchestre.ogg', "Coup d'orchestre (cuivres, timbales, gong)")
def _():
    p = Piste()
    for cuivre in CUIVRES:
        for decalage in (0, 1, -12):
            p.ajouter(transposer(vsco(cuivre), decalage), 0, 0.5)
    p.ajouter(couper(transposer(vsco(CONTREBASSE), -2), 4, 1.5), 0, 0.8)
    coup_grave(p, 0)
    p.ajouter(couper(vsco(GONGS[1], False), 5, 2.5), 0, 0.7)
    return reverb(saturer(normaliser(p.x), 1.5), 3.5, 0.4)


@jumpscare('demon.ogg', 'Démon (rugissement très grave)')
def _():
    p = Piste()
    p.ajouter(transposer(cc0(RUGISSEMENTS[1]), -7), 0, 1.0)
    p.ajouter(transposer(cc0(RUGISSEMENTS[0]), -5), 0.05, 0.7, 0.3)
    p.ajouter(transposer(cc0(CRI_HOMME_LONG), -5), 0.1, 0.6, -0.3)
    p.ajouter(couper(vsco(PIANO[0]), 3, 1.2), 0, 0.5)
    coup_grave(p, 0, 0.9)
    return reverb(saturer(normaliser(p.x), 1.6), 2.5, 0.3)


@jumpscare('choeur-des-damnes.ogg', 'Chœur des damnés (dix cris)')
def _():
    rng = np.random.default_rng(13)
    p = Piste()
    for chemin in [CRI_FEMME, CRI_FEMME_LONG, CRI_HOMME, CRI_HOMME_LONG] + HURLEMENTS + AGONIES[:4]:
        p.ajouter(transposer(cc0(chemin), int(rng.integers(-3, 3))), rng.uniform(0, 0.35), rng.uniform(0.5, 0.9),
                  pan=rng.uniform(-0.9, 0.9))
    p.ajouter(couper(vsco(GONGS[0], False), 4, 2), 0, 0.4)
    return reverb(p.x, 3.0, 0.45)


@jumpscare('cri-demoniaque.ogg', 'Cri démoniaque (voix dédoublée)')
def _():
    cri = cc0(CRI_FEMME_LONG)
    p = Piste()
    p.ajouter(cri, 0, 0.8)
    p.ajouter(transposer(cri, -12), 0, 0.9)
    p.ajouter(transposer(cri, -7), 0.02, 0.5, 0.4)
    p.ajouter(couper(vsco(GROSSE_CAISSE[0]), 2), 0, 0.7)
    return reverb(p.x, 2.0, 0.3)


@jumpscare('orgue-maudit.ogg', 'Orgue maudit et cri')
def _():
    p = Piste()
    for i, note in enumerate(ORGUE):
        p.ajouter(couper(transposer(vsco(note), i % 2), 3.5, 1.2), 0, 0.4)
    p.ajouter(couper(vsco(GROSSE_CAISSE[0]), 2.5), 0, 0.8)
    p.ajouter(cc0(CRI_FEMME), 0.9, 1.0)
    p.ajouter(transposer(cc0(CRI_FEMME), -12), 0.9, 0.5)
    return reverb(p.x, 3.0, 0.35)


@jumpscare('gong-inverse-hurlement.ogg', 'Souffle de gong inversé puis hurlement')
def _():
    gong = couper(vsco(GONGS[1], False), 5, 0.5)
    p = Piste()
    p.ajouter(inverser(gong)[:, -n_ech(1.6):], 0, 0.9)
    coup_grave(p, 1.6)
    p.ajouter(couper(vsco(GONGS[1], False), 4, 2), 1.6, 0.7)
    p.ajouter(cc0(HURLEMENTS[0]), 1.62, 1.0)
    p.ajouter(transposer(cc0(HURLEMENTS[1]), -3), 1.65, 0.7)
    return reverb(p.x, 2.5, 0.3)


@jumpscare('rafale-de-cris.ogg', 'Rafale de cris, verre et métal')
def _():
    p = Piste()
    p.ajouter(couper(vsco(GROSSE_CAISSE[0]), 2), 0, 0.9)
    for t, chemin, gain in [(0.0, VERRE, 0.8), (0.0, DOULEUR_FEMME, 1.0), (0.35, CRI_HOMME, 0.9), (0.6, CRI_FEMME, 1.0),
                            (0.9, METAL, 0.7), (1.0, CRI_FEMME_LONG, 0.9), (1.3, CHAINES, 0.7)]:
        p.ajouter(vsco(chemin, False) if chemin in (VERRE, METAL, CHAINES) else cc0(chemin), t, gain,
                  pan=np.random.uniform(-0.7, 0.7))
    p.ajouter(couper(vsco(GROSSE_CAISSE[1]), 2), 1.0, 0.8)
    return reverb(p.x, 1.5, 0.25)


@jumpscare('timbales-de-l-enfer.ogg', "Timbales de l'enfer puis cri")
def _():
    p = Piste()
    p.ajouter(crescendo(vsco(ROULEMENT), 2.5), 0, 1.0)
    coup_grave(p, 2.5)
    p.ajouter(cc0(CRI_FEMME_LONG), 2.52, 1.0)
    p.ajouter(cc0(HURLEMENTS[0]), 2.55, 0.6)
    return reverb(p.x, 2.2, 0.3)


@jumpscare('contrebasse-chaines-cri.ogg', 'Contrebasse, chaînes et cri')
def _():
    p = Piste()
    p.ajouter(couper(transposer(vsco(CONTREBASSE), -2), 3.5, 1.5), 0, 1.0)
    p.ajouter(couper(vsco(GROSSE_CAISSE[1]), 2), 0, 0.8)
    p.ajouter(vsco(CHAINES, False), 0.05, 0.8)
    p.ajouter(cc0(CRI_HOMME_LONG), 0.15, 1.0)
    p.ajouter(vsco(METAL, False), 0.6, 0.5)
    return reverb(p.x, 2.0, 0.3)


def composer():
    np.random.seed(5)
    dossier = os.path.join(SONS, 'reels', 'jumpscares')
    os.makedirs(dossier, exist_ok=True)
    lignes = ["'use strict';",
              "// Jump scares composés de vrais enregistrements (outils/fabrique/composer_jumpscares.py).",
              'const CATALOGUE_JUMPSCARES = [']
    for fichier, nom, fonction in JUMPSCARES:
        x = niveau_rms(stereo(couper_silence(fonction(), -50)), -11)
        duree = exporter(x, os.path.join(dossier, fichier), qualite=0.6)
        print(f'{fichier:32s} {duree:4.1f} s  crête {np.abs(x).max():.2f}  {nom}')
        nom_js = nom.replace("'", "\\'")
        lignes.append(f"  {{ cat: 'screamer', fichier: 'sons/reels/jumpscares/{fichier}', nom: '{nom_js}' }},")
    lignes.append('];')
    with open(os.path.join(SONS, 'catalogue-jumpscares.js'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(lignes) + '\n')
    with open(os.path.join(dossier, 'CREDITS.txt'), 'w', encoding='utf-8') as f:
        f.write('Jump scares composés uniquement de vrais enregistrements libres de droit :\n'
                '- Instruments : VSCO 2 Community Edition (CC0), Versilian Studios / Sam Gossner,\n'
                '  piano et orgue : Ivy Audio / Simon Dalzell — https://github.com/sgossner/VSCO-2-CE\n'
                '- Cris : Warfork (Team Forbidden) et rubberduck (OpenGameArt), CC0,\n'
                '  via https://github.com/lavenderdotpet/cc0-public-domain-sounds\n')


if __name__ == '__main__':
    CC0, VSCO = sys.argv[1], sys.argv[2]
    composer()
