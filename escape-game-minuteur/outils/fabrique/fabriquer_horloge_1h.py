"""Bande sonore d'une heure à télécharger : une horloge mécanique qui tourne, avec ses petits
mécanismes, et une tension qui monte jusqu'au gong final. Uniquement de vrais enregistrements CC0
(bois, cliquets, ressorts, gong, grosse caisse, violons), sauf la nappe sombre de l'app en fond.

  0 min   tic-tac lourd + petits mécanismes entre chaque tic + cliquets et ressorts réguliers
 15 min   le gong sonne un coup, 30 min deux coups, 45 min trois coups
 20 min   le tic-tac commence à accélérer (60 → 72 puis 100 battements par minute)
 45 min   un cœur se met à battre, de plus en plus vite
 50 min   des violons en trémolo montent
 60 min   tout s'arrête sur un grand coup de gong

Lancement : python3 fabriquer_horloge_1h.py /chemin/cc0-public-domain-sounds /chemin/VSCO-2-CE sortie.mp3
"""
import os
import sys

import numpy as np
import soundfile as sf
from scipy import signal

from dsp import SR, couper_silence, n_ech, normaliser, passe_bas, passe_haut, reponse_modale, reponse_salle, vitesse
from importer_cc0 import lire

RACINE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
DUREE = 60 * 60.0
FIN = DUREE + 25  # le dernier gong résonne
alea = np.random.default_rng(2026)

P = 'VSCO 1 Percussion'
MECA = 'bb - Smol Mechanisms (May 2021)'


def charger(chemin, debut=0.0, duree=None):
    x = lire(chemin)
    x = couper_silence(x, -45)
    i = np.nonzero(np.abs(x).max(axis=0) > np.abs(x).max() * 0.02)[0][0]
    x = x[:, max(0, i - 30) + n_ech(debut):]
    if duree:
        x = x[:, :n_ech(duree)]
        f = min(n_ech(0.05), x.shape[1])
        x[:, -f:] *= np.linspace(1, 0, f)
    return normaliser(x).astype(np.float32)


def transposer(x, demi_tons):
    return vitesse(x, 2 ** (demi_tons / 12)).astype(np.float32) if demi_tons else x


def placer(dest, son, t, gain=1.0, pan=0.0):
    angle = (pan + 1) * np.pi / 4
    i = n_ech(t)
    if i >= dest.shape[1]:
        return
    j = min(dest.shape[1], i + son.shape[1])
    gauche, droite = son[0, :j - i], son[1, :j - i]
    dest[0, i:j] += gain * np.sqrt(2) * np.cos(angle) * gauche
    dest[1, i:j] += gain * np.sqrt(2) * np.sin(angle) * droite


def limiteur(x, seuil=0.75, relache=0.3):
    """Baisse le volume en douceur juste avant les crêtes trop fortes (sans déformer le son)."""
    bloc = n_ech(0.01)
    enveloppe = np.abs(x).max(axis=0)
    nb = int(np.ceil(enveloppe.size / bloc))
    pics = np.pad(enveloppe, (0, nb * bloc - enveloppe.size)).reshape(nb, bloc).max(axis=1)
    cible = np.minimum(1, seuil / np.maximum(pics, 1e-9))
    gain, courant, retour = np.empty(nb), 1.0, np.exp(-0.01 / relache)
    for i, valeur in enumerate(cible):  # chute immédiate, remontée lente
        courant = valeur if valeur < courant else retour * courant + (1 - retour) * valeur
        gain[i] = courant
    gain = np.minimum(gain, np.concatenate([gain[1:], [1.0]]))  # anticipe d'un bloc
    return x * np.interp(np.arange(enveloppe.size), np.arange(nb) * bloc, gain).astype(np.float32)


def intervalle(t):
    """Durée entre deux tics : 1 s, puis accélération à partir de 20 min, plus forte à la fin."""
    minute = t / 60
    if minute < 20:
        return 1.0
    if minute < 50:
        return 1.0 - 0.17 * (minute - 20) / 30
    return 0.83 - 0.23 * min(1, (minute - 50) / 10)


def fabriquer(cc0, vsco, sortie):
    v = lambda chemin, *a, **k: charger(os.path.join(vsco, P, chemin), *a, **k)
    c = lambda chemin, *a, **k: charger(os.path.join(cc0, chemin), *a, **k)

    # --- Le tic-tac : vrais claquements de bois + résonance d'une caisse d'horloge ---
    caisse = reponse_modale([(180, 0.06, 1), (260, 0.05, 0.8), (420, 0.04, 0.6), (650, 0.03, 0.4)], 0.35)

    def coup(base, demi_tons):
        x = transposer(base, demi_tons)
        corps = np.array([signal.fftconvolve(canal, caisse)[:x.shape[1]] for canal in x])
        sourd = transposer(v('varWood/wood_click_ff_2.wav', duree=0.3), -7)
        n = max(x.shape[1], sourd.shape[1])
        total = np.zeros((2, n), np.float32)
        total[:, :x.shape[1]] += x + 0.6 * normaliser(corps)
        total[:, :sourd.shape[1]] += 0.5 * sourd
        return normaliser(total)

    tics = [coup(v('varWood/wood_click_f.wav', duree=0.3), d) for d in (-3, -2.6, -3.4)]
    tacs = [coup(v('varWood/wood_click_f2.wav', duree=0.3), d) for d in (-5, -4.6, -5.4)]

    # --- Les petits mécanismes : échappement, dents d'engrenage ---
    petits = ([transposer(v(f'varWood/wood_click_pp_{k}.wav', duree=0.12), 5) for k in (1, 2, 3)]
              + [transposer(c(f'{MECA}/Click Button {k}.wav', duree=0.15), 7) for k in (1, 3, 4)]
              + [transposer(v('varWood/claves_mp.wav', duree=0.1), 12)])
    petits = [passe_haut(x, 900).astype(np.float32) for x in petits]

    # --- Cliquets, remontoir, ressorts (toutes les quelques secondes) ---
    rouages = ([c(f'{MECA}/Ratchet Muted {k}.wav') for k in (2, 3, 4, 5)]
               + [c(f'{MECA}/Ratchet Harsh 1.wav', duree=1.2)]
               + [transposer(c(f'{MECA}/Cable Coiler {k}.wav'), -3) for k in (1, 2, 3, 4, 5)]
               + [c(f'{MECA}/Spring Loaded Blade {k}.wav') for k in (1, 3)]
               + [c('100-CC0-wood-metal-SFX/metal_spring_01.ogg'), c('100-CC0-wood-metal-SFX/metal_spring_02.ogg')]
               + [v('varWood/ratchet1.wav', 0.0, 1.5), v('varWood/ratchet2.wav', 2.0, 1.5)])

    n = n_ech(FIN)
    meca = np.zeros((2, n), np.float32)  # horloge et mécanismes (passeront dans la réverbération)
    mix = np.zeros((2, n), np.float32)

    # Tic-tac et échappement
    t, k = 0.5, 0
    while t < DUREE:
        d = intervalle(t)
        son = (tics if k % 2 == 0 else tacs)[alea.integers(3)]
        placer(meca, son, t + alea.normal(0, 0.003), 0.55 * alea.uniform(0.93, 1.0), -0.15 if k % 2 == 0 else 0.15)
        for fraction in (0.25, 0.5, 0.75):
            if alea.random() < 0.85:
                placer(meca, petits[alea.integers(len(petits))], t + d * fraction + alea.normal(0, 0.008),
                       alea.uniform(0.07, 0.15), alea.uniform(-0.35, 0.35))
        t += d
        k += 1

    # Cliquets et ressorts, de plus en plus fréquents
    t = 4.0
    while t < DUREE - 2:
        son = rouages[alea.integers(len(rouages))]
        placer(meca, transposer(son, int(alea.integers(-3, 2))), t, alea.uniform(0.12, 0.25), alea.uniform(-0.75, 0.75))
        t += alea.uniform(6, 13) * (1 - 0.45 * t / DUREE)

    # Grincement continu des rouages, très bas
    grincement = transposer(c(f'{MECA}/Ratchet Harsh 2.wav'), -12)
    grincement = passe_bas(grincement, 1500).astype(np.float32)
    pas = grincement.shape[1] - n_ech(1.0)
    for i in range(0, n, pas):
        morceau = grincement.copy()
        fondu = n_ech(1.0)
        morceau[:, :fondu] *= np.linspace(0, 1, fondu)
        morceau[:, -fondu:] *= np.linspace(1, 0, fondu)
        placer(meca, morceau, i / SR, 0.035)

    # Réverbération de la pièce, par blocs d'une minute
    salle = reponse_salle(0.9, sombre=0.3).astype(np.float32)
    mix += 0.82 * meca
    bloc = n_ech(60)
    for i in range(0, n, bloc):
        for canal in range(2):
            humide = signal.fftconvolve(meca[canal, i:i + bloc], salle[canal])
            fin = min(n, i + humide.shape[0])
            mix[canal, i:fin] += 0.18 * humide[:fin - i]
    del meca

    # Nappe sombre qui grossit lentement
    nappe = passe_bas(lire(os.path.join(RACINE, 'sons/ambiances/nappe-sombre.ogg')), 700).astype(np.float32)
    nappe = np.tile(nappe, (1, int(np.ceil(n / nappe.shape[1]))))[:, :n]
    nappe *= np.linspace(0.07, 0.10, n, dtype=np.float32)
    nappe[:, n_ech(DUREE):] = 0
    mix += nappe
    del nappe

    # Gong des quarts d'heure : 1, 2 puis 3 coups
    gong = v('varMetal/Gong/gong_hit_mf.wav')
    for quart, coups in ((15, 1), (30, 2), (45, 3)):
        for j in range(coups):
            placer(mix, gong, quart * 60 + 4 * j, 0.45)

    # Cœur qui bat de plus en plus vite à partir de 45 min (vraie grosse caisse étouffée)
    coeur = passe_bas(v('drums/bass/bdrum_muted_pp_1.wav', duree=0.5), 300).astype(np.float32)
    t = 45 * 60.0
    while t < DUREE:
        avance = (t - 45 * 60) / (15 * 60)
        force = 0.2 * min(1, avance * 5) + 0.08 * avance
        placer(mix, coeur, t, force)
        placer(mix, coeur, t + 0.27, force * 0.65)
        t += 60 / (55 + 50 * avance)

    # Violons en trémolo à partir de 50 min (vrais violons, accord dissonant)
    tremolo = [charger(os.path.join(vsco, f'Strings/Violin Section/Trem/VlnEns_Trem_{note}_v2.wav'), 1.0, 5.0)
               for note in ('D5', 'B4', 'G4')]
    tremolo.append(transposer(tremolo[0], 1))
    debut = 50 * 60.0
    for i, t in enumerate(np.arange(debut, DUREE, 4.0)):
        progression = (t - debut) / (DUREE - debut)
        for x in tremolo:
            morceau = x.copy()
            f = n_ech(1.0)
            morceau[:, :f] *= np.linspace(0, 1, f)
            morceau[:, -f:] *= np.linspace(1, 0, f)
            reste = n_ech(DUREE) - n_ech(t)
            placer(mix, morceau[:, :max(0, reste)], t, 0.022 * progression ** 1.5, alea.uniform(-0.5, 0.5))

    # Fin : grand gong et grosse caisse
    placer(mix, v('varMetal/Gong/gong_hit_fff.wav'), DUREE, 0.8)
    placer(mix, v('drums/bass/bdrum3_fff_1.wav'), DUREE, 0.7)

    # Finition : le tic-tac du début vers -22 dB (bien audible), crêtes limitées vers -2,5 dB (marge pour le MP3), fondus
    reference = mix[:, n_ech(60):n_ech(600)]
    mix *= 10 ** (-22 / 20) / np.sqrt(np.mean(reference ** 2))
    mix = limiteur(mix)
    mix[:, :n_ech(2)] *= np.linspace(0, 1, n_ech(2), dtype=np.float32)
    mix[:, -n_ech(3):] *= np.linspace(1, 0, n_ech(3), dtype=np.float32)

    with sf.SoundFile(sortie, 'w', SR, 2, format='MP3', subtype='MPEG_LAYER_III', compression_level=0.55) as f:
        for i in range(0, n, 16384):
            f.write(np.clip(mix[:, i:i + 16384].T, -1, 1))
    return mix


if __name__ == '__main__':
    mix = fabriquer(sys.argv[1], sys.argv[2], sys.argv[3])
    minutes = [20 * np.log10(np.sqrt(np.mean(mix[:, i:i + n_ech(60)] ** 2)) + 1e-9) for i in range(0, mix.shape[1], n_ech(300))]
    print('niveau (dB) toutes les 5 min :', [round(m, 1) for m in minutes])
