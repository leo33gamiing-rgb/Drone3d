"""Fabrique les sons fournis avec l'application (dossier `sons/`) et leur catalogue.

Tous les sons sont créés par l'ordinateur (synthèse), sans enregistrement extérieur.
Lancement : python3 fabriquer_sons.py   (paquets : numpy scipy soundfile espeakng-loader)
"""
import os
import sys

import numpy as np
from scipy import signal

from dsp import (SR, Piste, alea, boucler, bruit, bruit_brun, bruit_rose, couper_silence, echo, enveloppe,
                 exporter, filtre_variable, filtre_voyelle, fondus, frapper, inverser, lisse, n_ech, niveau_rms,
                 normaliser, passe_bande, passe_bas, passe_haut, ralenti_progressif, reponse_modale, reverb, saturer,
                 source_glottale, stereo, temps, vitesse, voix)
import parole as tts

DOSSIER = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'sons')
CATALOGUE = []
SONS = []  # (catégorie, fichier, nom, fonction, réglage du volume)


def son(categorie, fichier, nom, niveau='moyen'):
    def enregistrer(fonction):
        SONS.append((categorie, fichier, nom, fonction, niveau))
        return fonction
    return enregistrer


def impact(duree=1.2, grave=45):
    t = temps(duree)
    f = grave + 90 * np.exp(-t / 0.05)
    boom = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.35)
    craque = passe_bande(bruit(duree), 800, 5000) * np.exp(-t / 0.03)
    return normaliser(boom + 0.5 * normaliser(craque))


def cri(duree=2.2, f0_base=820, voyelle='a', echelle=1.15, rugosite=0.5):
    t = temps(duree)
    f0 = enveloppe([(0, f0_base * 0.55), (0.12, f0_base), (duree * 0.7, f0_base * 1.08), (duree, f0_base * 0.8)], duree)
    f0 *= 1 + 0.03 * np.sin(2 * np.pi * 6.5 * t) + 0.015 * lisse(len(t), 12, duree)
    v = voix(f0, voyelle, echelle, ouverture=0.45, jitter=0.03, souffle=0.4, rugosite=rugosite)
    env = enveloppe([(0, 0), (0.03, 1), (duree - 0.4, 0.9), (duree, 0)], duree)
    return saturer(v * env, 2.5)


def rugissement(duree=2.6, grave=1.0):
    t = temps(duree)
    f0 = enveloppe([(0, 70), (0.2, 110), (duree * 0.7, 95), (duree, 60)], duree) * grave
    src = source_glottale(f0, 0.7, jitter=0.08, souffle=0.6) + 0.6 * source_glottale(f0 / 2, 0.7, jitter=0.1, souffle=0)
    src *= 1 + 0.8 * np.sin(2 * np.pi * 28 * t + 3 * lisse(len(t), 5, duree))
    x = normaliser(filtre_voyelle(src, 'a', 0.85)) + 0.35 * normaliser(filtre_voyelle(bruit(duree), 'o', 0.9))
    env = enveloppe([(0, 0), (0.08, 1), (duree - 0.5, 0.8), (duree, 0)], duree)
    return saturer(normaliser(x) * env, 4)


def cordes(frequences, duree, tremolo=0.0, desaccord=0.006):
    t = temps(duree)
    x = np.zeros(len(t))
    for f in frequences:
        for d in np.linspace(-desaccord, desaccord, 4):
            x += signal.sawtooth(2 * np.pi * f * (1 + d) * t + alea.uniform(0, 6.28))
    x += 0.4 * normaliser(passe_bande(bruit(duree), min(frequences), min(frequences) * 4)) * len(frequences)
    if tremolo:
        x *= 1 + 0.4 * np.sin(2 * np.pi * tremolo * t)
    return normaliser(passe_bas(x, 7000))


def rire(syllabes=6, cadence=5.0, f0=(220, 150), voyelle='a', echelle=1.0, souffle=0.5, irregularite=0.15,
         derniere_longue=0.0, vibrato=0.0, rugosite=0.0, jitter=0.02, part_voisee=1.0):
    """Un rire : une suite de « ha » (souffle puis voix) dont la hauteur descend."""
    debuts, t = [], 0.05
    for k in range(syllabes):
        debuts.append(t)
        t += (1 / cadence) * (1 + irregularite * alea.uniform(-1, 1)) * (1 + 0.04 * k)
    duree = t + 0.4 + derniere_longue
    n = n_ech(duree)
    f0c = np.full(n, float(f0[1]))
    voise, souf = np.zeros(n), np.zeros(n)
    hauteurs = np.linspace(f0[0], f0[1], syllabes)
    for k, debut in enumerate(debuts):
        longueur = 0.75 / cadence + (derniere_longue if k == syllabes - 1 else 0)
        h = min(0.06, longueur * 0.35)
        i0, i1, i2 = n_ech(debut), n_ech(debut + h), min(n, n_ech(debut + longueur))
        amp = 1.0 - 0.45 * k / max(1, syllabes - 1)
        souf[i0:i1] = np.linspace(0.2, 1, i1 - i0) * amp
        seg = i2 - i1
        voise[i1:i2] = amp * np.minimum(1, np.linspace(0, 6, seg)) * np.linspace(1, 0.15, seg) ** 0.7
        souf[i1:i2] = amp * 0.35 * np.linspace(1, 0.2, seg)
        f0c[i0:i2] = hauteurs[k] * np.linspace(1.08, 0.9, i2 - i0)
    tt = temps(duree)
    if vibrato:
        f0c *= 1 + vibrato * np.sin(2 * np.pi * 6 * tt)
    voise, souf = passe_bas(voise, 40), passe_bas(souf, 40)
    src = source_glottale(f0c, 0.55, jitter, souffle=0.02) * voise * part_voisee
    if rugosite:
        src *= 1 + rugosite * lisse(n, 70, duree)
    aspiration = normaliser(passe_haut(bruit(duree), 300)) * souf * souffle * 0.6
    return normaliser(filtre_voyelle(src + aspiration, voyelle, echelle))


def chuchoter(texte, voix_espeak='fr+whisper', debit=120, hauteur=30, doublures=2, rt=1.8, mix=0.35, ralenti=1.0):
    s, taux = tts.parler(texte, voix_espeak, debit, hauteur)
    s = signal.resample_poly(s, SR // 50, taux // 50)
    if ralenti != 1:
        s = vitesse(s, ralenti)
    s = normaliser(passe_haut(s, 150))
    piste = Piste()
    piste.ajouter(s, 0.0, 1.0, 0.0)
    for k in range(doublures):
        double = vitesse(s, 1 + alea.uniform(-0.05, 0.05))
        piste.ajouter(double, 0.03 + 0.05 * k, 0.4, pan=0.6 if k % 2 else -0.6)
    return reverb(piste.x, rt, mix)


# ======================= SCREAMERS =======================

@son('screamer', 'screamers/cri-strident.ogg', 'Cri strident', 'fort')
def _():
    p = Piste()
    p.ajouter(impact(), 0, 0.7)
    p.ajouter(cri(2.2, 820), 0.02, 1.0, -0.2)
    p.ajouter(cri(2.2, 850), 0.04, 0.6, 0.3)
    return reverb(p.x, 1.2, 0.25)


@son('screamer', 'screamers/cri-enfant.ogg', "Cri d'enfant", 'fort')
def _():
    p = Piste()
    p.ajouter(cri(1.7, 1050, 'i', 1.35, 0.4), 0, 1.0)
    p.ajouter(cri(1.7, 1010, 'a', 1.3, 0.4), 0.02, 0.5, 0.3)
    return reverb(p.x, 1.6, 0.3)


@son('screamer', 'screamers/hurlement-demoniaque.ogg', 'Hurlement démoniaque', 'fort')
def _():
    p = Piste()
    p.ajouter(vitesse(rugissement(2.6), 0.85), 0, 1.0)
    p.ajouter(vitesse(cri(2.0, 700), 0.9), 0.15, 0.25)
    return reverb(saturer(normaliser(p.x), 1.5), 2.5, 0.35)


@son('screamer', 'screamers/violons-psychose.ogg', 'Violons stridents (Psychose)', 'fort')
def _():
    p = Piste()
    notes = [(1318, 1397), (1397, 1480), (1318, 1397), (1480, 1568)] * 2
    for k, (f1, f2) in enumerate(notes):
        d = 0.17
        coup = cordes([f1, f2], d) * enveloppe([(0, 0), (0.005, 1), (d - 0.04, 0.8), (d, 0)], d)
        p.ajouter(coup, k * 0.2, 1.0, pan=-0.3 if k % 2 else 0.3)
    return reverb(saturer(p.x, 1.5), 2.0, 0.3)


@son('screamer', 'screamers/stinger-orchestre.ogg', 'Coup d\'orchestre dissonant', 'fort')
def _():
    d = 3.2
    graves = cordes([55, 58.27, 61.74, 110], d, desaccord=0.004)
    graves = filtre_variable(graves, enveloppe([(0, 300), (0.06, 3000), (1.5, 600), (d, 200)], d), 'lowpass')
    aigus = cordes([1046.5, 1108.7, 1174.7, 1244.5], d, tremolo=12)
    env = enveloppe([(0, 0), (0.05, 1), (d, 0)], d) ** 1.5
    cymbale = passe_haut(bruit(d), 5000) * np.exp(-temps(d) / 0.5)
    p = Piste()
    p.ajouter(normaliser(graves) * env, 0, 0.9)
    p.ajouter(aigus * env, 0, 0.5)
    p.ajouter(normaliser(cymbale), 0, 0.3)
    p.ajouter(impact(1.5, 38), 0, 1.0)
    return reverb(saturer(normaliser(p.x), 1.5), 2.5, 0.35)


@son('screamer', 'screamers/crissement-metal.ogg', 'Crissement de métal', 'fort')
def _():
    d = 2.4
    n = n_ech(d)
    cadence = enveloppe([(0, 300), (0.6, 700), (1.5, 450), (d, 900)], d) * (1 + 0.2 * lisse(n, 20, d))
    phase = np.cumsum(cadence / SR)
    train = (np.diff(np.floor(phase), prepend=0) > 0).astype(float)
    modes = [(1570, 0.1, 0.6), (2130, 0.08, 1), (3170, 0.06, 0.8), (4410, 0.05, 0.7), (5960, 0.04, 0.5), (7340, 0.03, 0.4)]
    x = signal.fftconvolve(train, reponse_modale(modes))[:n]
    x = normaliser(x) * (1 + 0.6 * lisse(n, 8, d)) + 0.2 * normaliser(passe_bande(bruit(d), 3000, 8000))
    x = saturer(normaliser(x) * enveloppe([(0, 0), (0.05, 1), (d - 0.3, 0.9), (d, 0)], d), 2)
    p = Piste()
    p.ajouter(frapper([(180, 0.6, 1), (441, 0.45, 0.7), (901, 0.3, 0.5), (1733, 0.2, 0.3)], 0.003), 0, 0.8)
    p.ajouter(x, 0.05, 1.0)
    return reverb(p.x, 1.5, 0.3)


@son('screamer', 'screamers/braam.ogg', 'Braam grave (cinéma)', 'fort')
def _():
    d = 4.0
    f = 49.0
    x = cordes([f, f * 1.0595, f * 2], d, desaccord=0.003)
    x = filtre_variable(x, enveloppe([(0, 150), (0.08, 2400), (0.6, 1200), (2.5, 400), (d, 150)], d), 'lowpass')
    x = saturer(normaliser(x) * enveloppe([(0, 0), (0.05, 1), (2.8, 0.7), (d, 0)], d), 3)
    sub = np.sin(2 * np.pi * f * temps(d)) * enveloppe([(0, 0), (0.05, 1), (d, 0)], d)
    p = Piste()
    p.ajouter(x, 0, 1.0)
    p.ajouter(sub, 0, 0.5)
    return reverb(p.x, 3.0, 0.3)


@son('screamer', 'screamers/banshee.ogg', 'Plainte de banshee', 'fort')
def _():
    d = 3.2
    t = temps(d)
    base = enveloppe([(0, 500), (0.6, 1150), (1.4, 1250), (2.2, 900), (d, 600)], d) * (1 + 0.05 * np.sin(2 * np.pi * 5 * t))
    p = Piste()
    for k, ecart in enumerate([1.0, 1.012, 0.985]):
        o = voix(base * ecart, 'o', 1.2, souffle=0.5, jitter=0.02)
        a = voix(base * ecart, 'a', 1.2, souffle=0.5, jitter=0.02)
        melange = enveloppe([(0, 0), (1.2, 1), (2.4, 0.3), (d, 0)], d)
        v = (o * (1 - melange) + a * melange) * enveloppe([(0, 0), (0.4, 1), (d - 0.6, 0.8), (d, 0)], d)
        p.ajouter(v, 0.03 * k, 0.6, pan=(k - 1) * 0.6)
    return reverb(echo(p.x, 0.3, 0.35, 3), 3.5, 0.5)


@son('screamer', 'screamers/larsen-glitch.ogg', 'Larsen et parasites', 'fort')
def _():
    d = 2.0
    f = enveloppe([(0, 2400), (1.4, 3600), (d, 3900)], d)
    phase = 2 * np.pi * np.cumsum(f) / SR
    x = np.sin(phase) + 0.5 * np.sin(2 * phase) + 0.3 * np.sin(3 * phase)
    x = saturer(x * enveloppe([(0, 0.2), (1.4, 1), (d, 1)], d), 6)
    debut, fin = n_ech(1.4), len(x)
    morceau = n_ech(0.04)
    for i in range(debut, fin, morceau):
        if alea.random() < 0.5:
            x[i:i + morceau] = x[debut:debut + min(morceau, fin - i)]  # bégaiement
        else:
            x[i:i + morceau] *= alea.random() < 0.5
    x[debut:] = np.round(x[debut:] * 6) / 6  # son écrasé
    p = Piste()
    p.ajouter(x, 0, 0.8)
    p.ajouter(normaliser(bruit(0.5)) * np.exp(-temps(0.5) / 0.15), d - 0.1, 0.6)
    return p.x


@son('screamer', 'screamers/rugissement-impact.ogg', 'Rugissement et choc', 'fort')
def _():
    p = Piste()
    p.ajouter(impact(1.5, 40), 0, 1.0)
    p.ajouter(vitesse(rugissement(2.2, 1.1), 0.8), 0.05, 0.9)
    return reverb(p.x, 2.2, 0.3)


@son('screamer', 'screamers/cri-inverse.ogg', 'Souffle inversé puis cri', 'fort')
def _():
    c = cri(1.0, 900)
    souffle = inverser(reverb(c, 2.5, 1.0))[:, -n_ech(1.6):]
    p = Piste()
    p.ajouter(normaliser(souffle), 0, 0.8)
    p.ajouter(impact(), 1.55, 0.8)
    p.ajouter(c, 1.55, 1.0)
    return reverb(p.x, 1.5, 0.25)


@son('screamer', 'screamers/ames-hurlantes.ogg', 'Âmes hurlantes', 'fort')
def _():
    p = Piste()
    for k in range(6):
        p.ajouter(cri(2.4, alea.uniform(520, 1100), alea.choice(['a', 'o', 'i']), alea.uniform(1.0, 1.35)),
                  alea.uniform(0, 0.4), alea.uniform(0.4, 0.8), pan=alea.uniform(-0.9, 0.9))
    return reverb(saturer(normaliser(p.x), 1.4), 3.0, 0.45)


# ======================= INDICE =======================

def boite_a_musique(notes, tempo=0.32, ralentir=0.045, desaccord=0.015):
    p = Piste()
    instant = 0.0
    for i, note in enumerate(notes):
        if note is not None:
            f = 440 * 2 ** ((note - 69) / 12) * (1 + alea.uniform(-desaccord, desaccord))
            modes = [(f, 0.5, 1.0), (f * 2.01, 0.2, 0.35), (f * 3.98, 0.1, 0.15), (f * 6.3, 0.04, 0.06)]
            p.ajouter(frapper(modes, 0.0008, variation=0), instant, 0.8)
        instant += tempo + i * ralentir
    return p.x


@son('indice', 'indice/boite-a-musique.ogg', 'Boîte à musique faussée', 'moyen')
def _():
    return reverb(echo(boite_a_musique([76, 79, 83, 82, 76, 79, 74, 75]), 0.37, 0.35, 3), 1.8, 0.3)


@son('indice', 'indice/clochette.ogg', 'Clochette', 'moyen')
def _():
    p = Piste()
    for k in range(3):
        f = 1760
        p.ajouter(frapper([(f, 0.9, 1), (f * 2.0, 0.5, 0.5), (f * 2.76, 0.4, 0.4), (f * 5.4, 0.15, 0.2), (f * 8.93, 0.08, 0.1)],
                          0.0006), k * 0.35, 0.8 - 0.15 * k)
    return reverb(p.x, 2.0, 0.35)


@son('indice', 'indice/cloche-lointaine.ogg', "Cloche d'église lointaine", 'moyen')
def _():
    f = 196
    modes = [(f * r, d, a) for r, d, a in [(0.5, 4, 0.6), (1, 3, 0.5), (1.19, 2.5, 0.35), (1.5, 2, 0.3), (2, 1.6, 0.25),
                                            (2.52, 1.2, 0.15), (3.01, 0.9, 0.1), (4.07, 0.5, 0.06)]]
    p = Piste()
    p.ajouter(frapper(modes, 0.004), 0, 1.0)
    p.ajouter(frapper(modes, 0.004), 2.2, 0.9)
    return reverb(passe_bas(p.x, 2500), 4.0, 0.6)


@son('indice', 'indice/comptine-fredonnee.ogg', 'Comptine fredonnée', 'moyen')
def _():
    melodie = [(69, 1), (71, 1), (72, 1), (69, 1), (69, 1), (71, 1), (72, 1), (69, 1), (72, 1), (74, 1), (76, 2.2)]
    temps_noire = 0.55
    duree = sum(d for _, d in melodie) * temps_noire + 0.3
    f0 = np.zeros(n_ech(duree))
    amp = np.zeros(n_ech(duree))
    instant = 0.0
    for note, d in melodie:
        i0, i1 = n_ech(instant), n_ech(instant + d * temps_noire)
        f0[i0:i1] = 440 * 2 ** ((note - 69 - 12) / 12) * 2 * (1 + alea.uniform(-0.012, 0.012))
        amp[i0:i1] = np.minimum(1, np.linspace(0, 8, i1 - i0)) * np.linspace(1, 0.6, i1 - i0)
        instant += d * temps_noire
    f0[f0 == 0] = 330
    f0 = passe_bas(f0, 12) * (1 + 0.012 * np.sin(2 * np.pi * 5.5 * temps(duree)))
    v = voix(f0, 'm', 1.25, souffle=0.15) * passe_bas(amp, 20)
    return reverb(vitesse(v, 0.94), 2.5, 0.4)


@son('indice', 'indice/psst-par-ici.ogg', 'Chuchotement « psst… par ici »', 'moyen')
def _():
    return chuchoter('Psst... Par ici... Un indice...', 'fr+whisperf', 110, 45)


# ======================= RIRES =======================

@son('rire', 'rires/rire-demoniaque.ogg', 'Rire démoniaque')
def _():
    r = rire(7, 4.2, (130, 85), 'a', 0.9, souffle=0.6, derniere_longue=0.6, rugosite=0.4, jitter=0.04)
    return reverb(saturer(vitesse(r, 0.78), 2), 2.8, 0.4)


@son('rire', 'rires/rire-enfant.ogg', "Rire d'enfant")
def _():
    return reverb(rire(9, 7.5, (480, 380), 'i', 1.3, souffle=0.8, irregularite=0.25), 1.6, 0.35)


@son('rire', 'rires/ricanement-sorciere.ogg', 'Ricanement de sorcière')
def _():
    r = rire(8, 8.5, (700, 520), 'e', 1.2, souffle=0.5, derniere_longue=0.9, vibrato=0.04, rugosite=0.5)
    return reverb(saturer(r, 1.5), 1.4, 0.25)


@son('rire', 'rires/rire-clown.ogg', 'Rire de clown fou')
def _():
    p = Piste()
    p.ajouter(rire(6, 6, (260, 330), 'a', 1.05, irregularite=0.3), 0)
    p.ajouter(rire(5, 5, (340, 200), 'a', 1.05, derniere_longue=0.8, vibrato=0.05), 1.2)
    return reverb(saturer(normaliser(p.x), 1.3), 1.0, 0.2)


@son('rire', 'rires/rire-lointain.ogg', "Rire d'enfant lointain", 'moyen')
def _():
    r = passe_bas(rire(8, 7, (460, 370), 'i', 1.3, souffle=0.9, irregularite=0.3), 2500)
    return reverb(echo(r, 0.45, 0.4, 3), 3.5, 0.7)


@son('rire', 'rires/rire-etouffe.ogg', 'Ricanement étouffé', 'moyen')
def _():
    r = rire(5, 3.2, (125, 105), 'e', 0.95, souffle=1.6, part_voisee=0.45)
    return reverb(r, 0.5, 0.1)


@son('rire', 'rires/rire-deforme.ogg', 'Rire qui ralentit')
def _():
    r = rire(9, 5.5, (210, 150), 'a', 1.0, souffle=0.5, derniere_longue=0.5, rugosite=0.2)
    return reverb(ralenti_progressif(r, 1.0, 0.35), 2.2, 0.35)


@son('rire', 'rires/rires-multiples.ogg', "Rires d'enfants")
def _():
    p = Piste()
    for k, pan in enumerate([-0.8, -0.3, 0.3, 0.8]):
        p.ajouter(rire(alea.integers(6, 10), alea.uniform(6.5, 8.5), (alea.uniform(420, 520), alea.uniform(340, 400)),
                       alea.choice(['i', 'e', 'a']), alea.uniform(1.25, 1.4), souffle=0.8, irregularite=0.3),
                  k * 0.35 + alea.uniform(0, 0.15), alea.uniform(0.6, 1.0), pan)
    return reverb(p.x, 2.2, 0.45)


# ======================= CHUCHOTEMENTS =======================

PHRASES = [
    ('je-te-vois', 'Je te vois...', 'fr+whisper', 25),
    ('derriere-toi', 'Derrière toi...', 'fr+whisper', 25),
    ('tu-ne-sortiras-jamais', "Tu ne sortiras jamais d'ici...", 'fr+whisper', 30),
    ('trop-tard', 'Il est trop tard...', 'fr+whisper', 20),
    ('viens-jouer', 'Viens jouer avec nous...', 'fr+whisperf', 70),
    ('ne-te-retourne-pas', 'Ne te retourne pas...', 'fr+whisperf', 40),
    ('ils-arrivent', 'Ils arrivent...', 'fr+whisper', 30),
    ('tu-es-le-prochain', 'Tu es le prochain...', 'fr+whisper', 20),
    ('laissez-moi-sortir', 'Laissez-moi sortir...', 'fr+whisperf', 50),
]

for _cle, _texte, _voix, _hauteur in PHRASES:
    son('chuchotement', f'chuchotements/{_cle}.ogg', f'« {_texte} »', 'moyen')(
        lambda t=_texte, v=_voix, h=_hauteur: chuchoter(t, v, 115, h, ralenti=0.93))


@son('chuchotement', 'chuchotements/murmures-indistincts.ogg', 'Murmures indistincts', 'moyen')
def _():
    p = Piste()
    for k, (_c, texte, v, h) in enumerate(PHRASES * 2):
        s, taux = tts.parler(texte, v, 110, h)
        s = normaliser(signal.resample_poly(s, SR // 50, taux // 50))
        if k % 2:
            s = inverser(s)  # parole à l'envers : incompréhensible
        p.ajouter(s, alea.uniform(0, 6), alea.uniform(0.3, 0.7), alea.uniform(-1, 1))
    return reverb(p.x, 2.5, 0.45)


# ======================= PORTES ET COUPS =======================

PORTE_BOIS = [(92, 0.07, 1.0), (147, 0.06, 0.8), (213, 0.05, 0.7), (288, 0.045, 0.6), (395, 0.035, 0.5),
              (540, 0.03, 0.4), (760, 0.02, 0.3), (1080, 0.015, 0.2), (1600, 0.01, 0.12)]
METAL = [(180, 0.6, 1), (287, 0.5, 0.8), (441, 0.45, 0.7), (623, 0.35, 0.6), (901, 0.3, 0.5), (1247, 0.25, 0.4),
         (1733, 0.2, 0.3), (2410, 0.15, 0.2), (3300, 0.1, 0.15)]
LOQUET = [(2300, 0.02, 1), (3400, 0.015, 0.7), (5100, 0.01, 0.5)]


def grincement(duree=3.0, points=((0, 30), (0.8, 90), (1.6, 50), (2.4, 140), (3.0, 70))):
    n = n_ech(duree)
    cadence = enveloppe([(min(t, duree), v) for t, v in points], duree) * (1 + 0.15 * lisse(n, 15, duree))
    phase = np.cumsum(cadence / SR)
    train = (np.diff(np.floor(phase), prepend=0) > 0) * (0.6 + 0.4 * alea.random(n))
    modes = [(380, 0.015, 0.5), (620, 0.012, 1), (1240, 0.01, 0.7), (1830, 0.008, 0.5), (2600, 0.006, 0.4), (3900, 0.004, 0.25)]
    x = signal.fftconvolve(train, reponse_modale(modes))[:n]
    return normaliser(x) * enveloppe([(0, 0), (0.1, 1), (duree - 0.2, 0.8), (duree, 0)], duree)


@son('porte', 'portes/trois-coups-lents.ogg', 'Trois coups lents')
def _():
    p = Piste()
    for t, force in [(0, 1.0), (0.85, 0.95), (1.75, 1.1)]:
        p.ajouter(frapper(PORTE_BOIS, 0.002, force, clic=0.25), t)
    return reverb(p.x, 1.2, 0.3)


@son('porte', 'portes/coups-frenetiques.ogg', 'Coups frénétiques')
def _():
    p = Piste()
    t = 0.0
    poing = [(f * 0.85, d * 1.2, a) for f, d, a in PORTE_BOIS]
    for k in range(14):
        force = 0.6 + 0.6 * k / 13
        p.ajouter(frapper(poing, 0.006, force, clic=0.1), t)
        p.ajouter(frapper(LOQUET, 0.0005, 0.15 * force), t + 0.02)
        t += alea.uniform(0.11, 0.2)
    return reverb(p.x, 1.0, 0.25)


@son('porte', 'portes/porte-metal.ogg', 'Coups sur une porte en métal')
def _():
    p = Piste()
    for k in range(4):
        p.ajouter(frapper(METAL, 0.004, 1.0 - 0.1 * k, clic=0.2), k * 0.9)
    return reverb(p.x, 2.0, 0.35)


@son('porte', 'portes/grattements.ogg', 'Ongles qui grattent la porte')
def _():
    p = Piste()
    for k, t in enumerate([0, 1.1, 2.0]):
        d = alea.uniform(0.7, 1.0)
        n = n_ech(d)
        densite = enveloppe([(0, 150), (d / 2, 400), (d, 200)], d)
        train = (alea.random(n) < densite / SR).astype(float)
        rugueux = passe_bas(train, 300)
        g = normaliser(passe_bande(bruit(d), 2000, 6500)) * (0.3 + 0.7 * normaliser(rugueux, 1))
        g += 0.3 * normaliser(passe_bande(g, 700, 1200))
        p.ajouter(g * np.sin(np.pi * temps(d) / d) ** 0.7, t, 0.9 - 0.1 * k)
    return reverb(p.x, 0.6, 0.15)


@son('porte', 'portes/porte-qui-grince.ogg', 'Porte qui grince')
def _():
    return reverb(grincement(), 1.0, 0.25)


@son('porte', 'portes/porte-qui-claque.ogg', 'Porte qui claque')
def _():
    p = Piste()
    lourde = [(f * 0.7, d * 2, a) for f, d, a in PORTE_BOIS]
    p.ajouter(frapper(lourde, 0.008, 1.0, clic=0.4), 0)
    p.ajouter(impact(0.8, 50), 0, 0.6)
    for k in range(6):
        p.ajouter(frapper(LOQUET, 0.0005, 0.3 * (1 - k / 6)), 0.03 + k * 0.025)
    return reverb(p.x, 1.8, 0.35)


@son('porte', 'portes/poignee-secouee.ogg', 'Poignée secouée')
def _():
    p = Piste()
    t = 0.0
    for rafale in range(3):
        for k in range(alea.integers(4, 7)):
            p.ajouter(frapper(LOQUET, 0.0005, alea.uniform(0.4, 0.9)), t)
            if k % 2:
                p.ajouter(frapper([(f * 1.2, d, a) for f, d, a in PORTE_BOIS], 0.003, 0.25), t + 0.01)
            t += alea.uniform(0.06, 0.11)
        t += alea.uniform(0.3, 0.5)
    return reverb(p.x, 0.8, 0.2)


@son('porte', 'portes/coups-dans-le-mur.ogg', 'Coups sourds dans le mur', 'moyen')
def _():
    p = Piste()
    mur = [(60, 0.12, 1), (95, 0.1, 0.8), (140, 0.08, 0.6), (210, 0.06, 0.4)]
    for k in range(4):
        p.ajouter(passe_bas(frapper(mur, 0.01, 1.0 - 0.05 * k), 400), k * 1.2)
    return reverb(p.x, 1.5, 0.3)


# ======================= AUTRES BRUITAGES =======================

def pas(clarte=1.0):
    sol = [(80, 0.05, 1), (130, 0.04, 0.8), (210, 0.03, 0.6), (340, 0.02, 0.4)]
    p = Piste()
    p.ajouter(frapper(sol, 0.006, 1.0, clic=0.3), 0)
    p.ajouter(frapper(sol, 0.004, 0.5, clic=0.2), 0.08)
    return passe_bas(p.x, 600 + 5400 * clarte)


@son('bruitage', 'bruitages/pas-qui-approchent.ogg', 'Pas qui approchent')
def _():
    p = Piste()
    t = 0.0
    for k in range(10):
        proche = k / 9
        p.ajouter(pas(proche), t, 0.15 + 0.85 * proche, pan=0.5 - 0.5 * proche)
        if k in (4, 8):
            p.ajouter(grincement(0.5, ((0, 40), (0.5, 70))), t + 0.1, 0.3 * proche)
        t += alea.uniform(0.7, 0.85)
    return reverb(p.x, 1.4, 0.3)


@son('bruitage', 'bruitages/chaines-trainees.ogg', 'Chaînes traînées')
def _():
    d = 4.0
    p = Piste()
    trainee = normaliser(passe_bande(bruit(d), 1000, 5000)) * (0.5 + 0.5 * lisse(n_ech(d), 3, d))
    p.ajouter(trainee * enveloppe([(0, 0), (0.3, 1), (d - 0.4, 1), (d, 0)], d), 0, 0.25)
    t = 0.0
    while t < d - 0.2:
        modes = [(alea.uniform(2800, 7000), alea.uniform(0.02, 0.08), 1) for _ in range(3)]
        p.ajouter(frapper(modes, 0.0004, alea.uniform(0.3, 1)), t, pan=alea.uniform(-0.6, 0.6))
        t += alea.exponential(1 / 18)
    return reverb(p.x, 1.5, 0.3)


@son('bruitage', 'bruitages/respiration-rauque.ogg', 'Respiration rauque', 'moyen')
def _():
    p = Piste()
    t = 0.0
    for k in range(3):
        inspire = filtre_voyelle(normaliser(passe_bande(bruit(1.0), 800, 3000)), 'e', 1.1)
        inspire = normaliser(inspire) * enveloppe([(0, 0), (0.7, 1), (1.0, 0)], 1.0)
        d = 1.3
        expire = normaliser(filtre_voyelle(normaliser(passe_bande(bruit(d), 300, 1500)), 'a', 0.95))
        f0 = np.full(n_ech(d), 75.0) * (1 + 0.1 * lisse(n_ech(d), 4, d))
        expire += 0.25 * voix(f0, 'a', 0.9, jitter=0.1, rugosite=0.6)
        expire = expire * enveloppe([(0, 0), (0.15, 1), (d, 0)], d)
        p.ajouter(inspire, t, 0.6)
        p.ajouter(normaliser(expire), t + 1.05, 0.9)
        t += 2.6
    return reverb(p.x, 0.5, 0.1)


def battement(t0, force, piste):
    d = 0.3
    t = temps(d)
    f = 35 + 25 * np.exp(-t / 0.04)
    coup = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.08)
    coup += 0.3 * normaliser(passe_bas(bruit(d), 150)) * np.exp(-t / 0.03)
    piste.ajouter(normaliser(coup) * force, t0)


@son('bruitage', 'bruitages/battements-coeur.ogg', 'Battements de cœur qui accélèrent')
def _():
    p = Piste()
    t = 0.0
    for k in range(10):
        battement(t, 0.9, p)
        battement(t + 0.28, 0.6, p)
        t += 1.0 - k * 0.055
    return reverb(p.x, 0.6, 0.15)


@son('bruitage', 'bruitages/glas.ogg', 'Glas funèbre')
def _():
    f = 98
    modes = [(f * r, d, a) for r, d, a in [(0.5, 3.5, 0.5), (1, 2.5, 0.45), (1.19, 2, 0.3), (1.5, 1.7, 0.25),
                                            (2, 1.4, 0.2), (2.52, 1.0, 0.15), (2.66, 0.9, 0.12), (3.01, 0.7, 0.1),
                                            (4.07, 0.4, 0.06)]]
    return reverb(frapper(modes, 0.005), 3.5, 0.4)


@son('bruitage', 'bruitages/grognement.ogg', 'Grognement')
def _():
    d = 2.5
    t = temps(d)
    f0 = enveloppe([(0, 60), (0.5, 80), (d, 65)], d)
    src = source_glottale(f0, 0.7, jitter=0.1, souffle=0.5) * (1 + 0.7 * np.sin(2 * np.pi * 25 * t))
    x = filtre_voyelle(src, 'o', 0.8) * enveloppe([(0, 0), (0.3, 1), (d - 0.4, 0.8), (d, 0)], d)
    return reverb(saturer(normaliser(x), 3), 0.6, 0.12)


def goutte():
    d = 0.12
    t = temps(d)
    f = alea.uniform(700, 1100) * (1 + 0.8 * t / 0.03).clip(max=2.0)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.035)


@son('bruitage', 'bruitages/gouttes.ogg', "Gouttes d'eau dans le noir", 'moyen')
def _():
    p = Piste(7.0)
    t = 0.2
    while t < 6.5:
        p.ajouter(goutte(), t, alea.uniform(0.4, 1.0), alea.uniform(-0.7, 0.7))
        t += alea.uniform(0.4, 1.3)
    return reverb(p.x, 2.5, 0.5)


@son('bruitage', 'bruitages/radio-statique.ogg', 'Radio : « Aidez-moi… »')
def _():
    d = 6.0
    n = n_ech(d)
    statique = normaliser(passe_bande(bruit(d), 300, 4000)) * (0.6 + 0.4 * lisse(n, 6, d))
    statique += (alea.random(n) < 30 / SR) * alea.uniform(-1, 1, n) * 3  # craquements
    t = temps(d)
    sifflet = np.sin(2 * np.pi * np.cumsum(enveloppe([(0, 800), (d, 2400)], d)) / SR) * enveloppe(
        [(0, 0), (1.5, 0), (1.8, 0.4), (2.5, 0), (d, 0)], d)
    s, taux = tts.parler('Aidez-moi... Aidez-moi...', 'fr+f3', 120, 40)
    s = normaliser(passe_bande(signal.resample_poly(s, SR // 50, taux // 50), 400, 3000))
    s = saturer(s * (1 + 0.5 * np.sin(2 * np.pi * 30 * np.arange(len(s)) / SR)), 3)
    p = Piste(d)
    p.ajouter(normaliser(statique), 0, 0.5)
    p.ajouter(sifflet, 0, 0.3)
    p.ajouter(s * np.sin(np.pi * np.arange(len(s)) / len(s)), 2.8, 0.8)
    return p.x * enveloppe([(0, 0), (0.2, 1), (d - 0.3, 1), (d, 0)], d)


def bulles(duree, densite, f_bas, f_haut, amortissement=(0.01, 0.03)):
    p = Piste(duree)
    t = 0.0
    while t < duree:
        d = alea.uniform(*amortissement)
        tt = temps(d * 5)
        f = alea.uniform(f_bas, f_haut) * (1 + 2.5 * tt)  # la bulle monte en fréquence en remontant
        p.ajouter(np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt / d), t, alea.uniform(0.2, 1), alea.uniform(-0.6, 0.6))
        t += alea.exponential(1 / densite)
    return p.x[:, :n_ech(duree)]


@son('bruitage', 'bruitages/telephone.ogg', 'Téléphone qui sonne')
def _():
    cloche = [(1150, 0.25, 1), (1730, 0.2, 0.7), (2890, 0.12, 0.4), (4100, 0.08, 0.2)]
    p = Piste()
    for sonnerie in range(3):
        debut = sonnerie * 4.0
        for k in range(40):  # le marteau frappe les deux cloches 25 fois par seconde
            p.ajouter(frapper(cloche if k % 2 else [(f * 1.06, d, a) for f, d, a in cloche], 0.0005, 0.7), debut + k / 25)
    return reverb(p.x, 0.6, 0.25)


@son('bruitage', 'bruitages/robinet.ogg', 'Robinet qui coule')
def _():
    d = 8.0
    jet = normaliser(passe_bande(bruit(d), 400, 6000)) * 0.4
    x = stereo(jet) + bulles(d, 350, 600, 3000)
    return reverb(x * enveloppe([(0, 0), (0.3, 1), (d - 0.5, 1), (d, 0)], d), 0.6, 0.3)


@son('bruitage', 'bruitages/chaise-trainee.ogg', "Chaise qu'on déplace")
def _():
    p = Piste()
    p.ajouter(grincement(1.3, ((0, 45), (0.4, 110), (0.9, 70), (1.3, 120))), 0, 0.8)
    p.ajouter(normaliser(passe_bande(bruit(1.3), 200, 1500)) * enveloppe([(0, 0), (0.1, 1), (1.2, 1), (1.3, 0)], 1.3), 0, 0.3)
    p.ajouter(frapper([(f * 1.1, d, a) for f, d, a in PORTE_BOIS], 0.004, 0.9, clic=0.2), 1.45)
    return reverb(p.x, 0.6, 0.25)


@son('bruitage', 'bruitages/sous-l-eau.ogg', "Sous l'eau (bulles)")
def _():
    d = 6.0
    p = Piste(d)
    p.ajouter(normaliser(passe_bas(bruit_brun(d), 250)), 0, 0.5)
    p.ajouter(passe_bas(bulles(d, 12, 150, 500, (0.04, 0.09)), 1500), 0, 1.0)
    for k in range(6):
        battement(0.4 + k * 0.9, 0.5, p)
    return reverb(passe_bas(p.x, 1800), 1.2, 0.35)


# ======================= AMBIANCES (boucles) =======================

BOUCLE = 60.0  # durée des ambiances en secondes


def periodique(f):
    """Arrondit une fréquence pour qu'elle boucle exactement sur BOUCLE secondes."""
    return round(f * BOUCLE) / BOUCLE


@son('ambiance', 'ambiances/nappe-sombre.ogg', 'Nappe sombre', 'ambiance')
def _():
    t = temps(BOUCLE + 5)  # 5 s de préchauffage du filtre, retirées ensuite
    x = sum(signal.sawtooth(2 * np.pi * periodique(f) * t) for f in [41.2, 43.7, 61.7, 82.9])
    x = filtre_variable(x, 160 + 90 * np.sin(2 * np.pi * periodique(1 / 30) * t), 'lowpass')
    halo = (np.sin(2 * np.pi * periodique(1975) * t) + np.sin(2 * np.pi * periodique(2093) * t))
    halo *= 0.5 + 0.5 * np.sin(2 * np.pi * periodique(1 / 20) * t)
    x = (normaliser(x) + 0.04 * halo)[n_ech(5):]
    return reverb(x, 3.0, 0.3, boucle=True)


@son('ambiance', 'ambiances/vent-hurlant.ogg', 'Vent qui hurle', 'ambiance')
def _():
    d = BOUCLE + 4
    n = n_ech(d)
    x = np.zeros(n)
    for bas, haut, q in [(300, 900, 8), (700, 1600, 10), (1500, 2600, 12)]:
        centre = bas + (haut - bas) * (0.5 + 0.5 * lisse(n, 0.15, d))
        x += normaliser(filtre_variable(bruit(d), centre, 'bandpass', q))
    rafales = 0.35 + 0.65 * (0.5 + 0.5 * lisse(n, 0.1, d))
    x = normaliser(x) * rafales + 0.5 * normaliser(passe_bas(bruit_brun(d), 120))
    return boucler(stereo(x) * [[1], [0.9]], 4)


@son('ambiance', 'ambiances/cave-gouttes.ogg', 'Cave humide (gouttes)', 'ambiance')
def _():
    p = Piste(BOUCLE, boucle=True)
    fond = normaliser(passe_bas(bruit_brun(BOUCLE + 3), 200)) * 0.5 + 0.1 * normaliser(passe_bas(bruit_rose(BOUCLE + 3), 800))
    p.ajouter(boucler(fond, 3), 0)
    t = 0.0
    while t < BOUCLE:
        p.ajouter(goutte(), t, alea.uniform(0.3, 1.0), alea.uniform(-0.8, 0.8))
        t += alea.uniform(0.6, 2.2)
    p.ajouter(grincement(1.2, ((0, 25), (0.6, 45), (1.2, 30))), 37, 0.15)
    return reverb(p.x, 2.5, 0.45, boucle=True)


@son('ambiance', 'ambiances/choeur-fantome.ogg', 'Chœur fantôme', 'ambiance')
def _():
    d = BOUCLE + 4
    n = n_ech(d)
    t = temps(d)
    p = Piste()
    for k, (f, voyelle, pan) in enumerate([(146.8, 'ou', -0.7), (174.6, 'o', -0.3), (207.7, 'ou', 0.3),
                                           (293.7, 'o', 0.7), (311.1, 'ou', 0.0)]):
        f0 = f * (1 + 0.01 * np.sin(2 * np.pi * 4.5 * t + k) + 0.006 * lisse(n, 0.2, d))
        v = voix(f0, voyelle, 1.0 if f < 250 else 1.15, souffle=0.25, jitter=0.01)
        v *= 0.3 + 0.7 * (0.5 + 0.5 * lisse(n, 0.05, d))
        p.ajouter(v, 0, 0.5, pan)
    return reverb(boucler(p.x, 4), 4.0, 0.6, boucle=True)


@son('ambiance', 'ambiances/asile-abandonne.ogg', 'Asile abandonné', 'ambiance')
def _():
    t = temps(BOUCLE)
    n = len(t)
    bourdon = sum(a * np.sin(2 * np.pi * f * t) for f, a in [(50, 1), (100, 0.6), (150, 0.4), (200, 0.2), (250, 0.1)])
    bourdon *= 1 + 0.1 * np.sin(2 * np.pi * periodique(0.3) * t)
    neon = passe_bande(np.sign(np.sin(2 * np.pi * 100 * t)), 2000, 6000)
    allume = (lisse(n, 0.5, BOUCLE) > -0.2).astype(float)
    clignote = np.where(alea.random(n // 2000 + 1) < 0.3, 0.0, 1.0).repeat(2000)[:n]
    neon *= passe_bas(allume * np.where(lisse(n, 0.2, BOUCLE) > 0.5, clignote, 1.0), 200)
    p = Piste(BOUCLE, boucle=True)
    p.ajouter(normaliser(bourdon), 0, 0.5)
    p.ajouter(normaliser(neon), 0, 0.15)
    for instant in (14, 41):
        p.ajouter(passe_bas(frapper(METAL, 0.004), 900), instant, 0.4, alea.uniform(-0.8, 0.8))
    p.ajouter(passe_bas(frapper([(f * 0.7, d * 2, a) for f, d, a in PORTE_BOIS], 0.008), 600), 28, 0.5, -0.6)
    return reverb(p.x, 2.0, 0.35, boucle=True)


@son('ambiance', 'ambiances/berceuse-lointaine.ogg', 'Berceuse lointaine', 'ambiance')
def _():
    p = Piste(BOUCLE, boucle=True)
    melodie = [76, 74, 72, 74, 76, 76, 76, None, 74, 74, 74, None, 76, 79, 79, None,
               76, 74, 72, 74, 76, 76, 76, 76, 74, 74, 76, 74, 72]
    musique = boite_a_musique(melodie, 0.42, 0.0, 0.02)
    musique = ralenti_progressif(musique, 0.98, 0.94)
    p.ajouter(musique, 2.0, 1.0)
    p.ajouter(musique, 31.0, 0.8)
    return reverb(passe_bas(p.x, 3000), 3.0, 0.55, boucle=True)


@son('ambiance', 'ambiances/orage-lointain.ogg', 'Pluie et orage lointain', 'ambiance')
def _():
    d = BOUCLE + 4
    n = n_ech(d)
    pluie = normaliser(passe_bande(bruit_rose(d), 800, 8000)) * 0.6
    pluie += (alea.random(n) < 400 / SR) * alea.uniform(0, 1, n) * 0.8
    p = Piste(d)
    p.ajouter(normaliser(passe_bande(pluie, 600, 9000)), 0, 0.5)
    for instant in (12, 39):
        dt = alea.uniform(4, 6)
        tonnerre = normaliser(passe_bas(bruit_brun(dt), 150)) * enveloppe([(0, 0), (0.3, 1), (dt, 0)], dt)
        p.ajouter(tonnerre, instant, 0.9)
    return boucler(p.x, 4)


@son('ambiance', 'ambiances/coeur-lent.ogg', 'Cœur qui bat lentement', 'ambiance')
def _():
    p = Piste(BOUCLE, boucle=True)
    periode = BOUCLE / 54
    for k in range(54):
        battement(k * periode, 1.0, p)
        battement(k * periode + 0.3, 0.6, p)
    return reverb(passe_bas(p.x, 300), 0.8, 0.2, boucle=True)


# ======================= HORLOGES (boucles) =======================

def tic(clic, corps, grave=0.0, clarte=1.0):
    a, b = frapper(clic, 0.0005, 0.7), frapper(corps, 0.002, 1.0)
    x = np.zeros(max(len(a), len(b)))
    x[:len(a)] += a
    x[:len(b)] += b
    if grave:
        t = temps(0.15)
        x[:len(t)] += grave * np.sin(2 * np.pi * 60 * t) * np.exp(-t / 0.04)
    return passe_bas(normaliser(x), 2000 + 8000 * clarte)


CLIC = [(2100, 0.01, 1), (3300, 0.008, 0.7), (4700, 0.006, 0.5)]
CAISSE = [(180, 0.06, 1), (260, 0.05, 0.8), (420, 0.04, 0.6), (650, 0.03, 0.4)]


def horloge(duree, periode, sons, rt, mix):
    p = Piste(duree, boucle=True)
    for k in range(int(round(duree / periode))):
        p.ajouter(sons[k % len(sons)], k * periode)
    return reverb(p.x, rt, mix, boucle=True)


@son('horloge', 'horloges/horloge-lourde.ogg', 'Grande horloge (lourde)', 'horloge')
def _():
    lourd = [(f * 0.8, d * 1.5, a) for f, d, a in CAISSE]
    sons = [tic(CLIC, lourd, 0.8), tic([(f * 0.85, d, a) for f, d, a in CLIC], [(f * 0.9, d, a) for f, d, a in lourd], 0.8)]
    return horloge(30, 1.0, sons, 1.8, 0.35)


@son('horloge', 'horloges/pendule.ogg', 'Pendule tic-tac', 'horloge')
def _():
    sons = [tic(CLIC, CAISSE, clarte=1.0), tic([(f * 0.8, d, a) for f, d, a in CLIC], CAISSE, clarte=0.6)]
    return horloge(20, 1.0, sons, 0.7, 0.2)


@son('horloge', 'horloges/montre-gousset.ogg', 'Montre à gousset (rapide)', 'horloge')
def _():
    petit = [(3500, 0.004, 1), (5200, 0.003, 0.7), (7000, 0.002, 0.5)]
    sons = [tic(petit, [(1200, 0.006, 0.5)]), tic([(f * 0.92, d, a) for f, d, a in petit], [(1100, 0.006, 0.5)])]
    return horloge(10, 0.2, sons, 0.3, 0.1)


@son('horloge', 'horloges/horloge-fantome.ogg', 'Horloge fantôme (ralentie)', 'horloge')
def _():
    lourd = [(f * 0.8, d * 1.5, a) for f, d, a in CAISSE]
    sons = [vitesse(tic(CLIC, lourd, 1.0), 0.6), vitesse(tic(CLIC, lourd, 1.0, 0.5), 0.55)]
    x = horloge(28, 1.4, sons, 4.0, 0.55)
    t = temps(28)
    drone = np.sin(2 * np.pi * (55 + 1 / 28) * t) + np.sin(2 * np.pi * (58 + 3 / 28) * t)
    return x + 0.06 * stereo(drone)


@son('horloge', 'horloges/mecanisme.ogg', 'Mécanisme d\'horloge', 'horloge')
def _():
    p = Piste(16, boucle=True)
    son_tic = tic(CLIC, CAISSE, clarte=0.8)
    for k in range(32):
        p.ajouter(son_tic, k * 0.5)
    for k in range(8):
        for j in range(6):
            p.ajouter(frapper([(f * 1.3, d, a) for f, d, a in CLIC], 0.0004, 0.25), k * 2 + 0.25 + j * 0.03)
    t = temps(16)
    rouages = normaliser(passe_bande(bruit(16), 400, 1200)) * (0.5 + 0.5 * np.sin(2 * np.pi * t / 2) ** 2)
    p.ajouter(rouages, 0, 0.06)
    return reverb(p.x, 0.8, 0.2, boucle=True)


@son('horloge', 'horloges/tic-tac-coeur.ogg', 'Tic-tac et cœur (très lourd)', 'horloge')
def _():
    lourd = [(f * 0.8, d * 1.5, a) for f, d, a in CAISSE]
    p = Piste(30, boucle=True)
    for k in range(30):
        p.ajouter(tic(CLIC, lourd, 0.8), k)
        battement(k + 0.5, 0.9, p)
        battement(k + 0.78, 0.55, p)
    return reverb(p.x, 1.6, 0.3, boucle=True)


# ======================= FABRICATION =======================

NIVEAUX = {
    'fort': lambda x: niveau_rms(x, -13),
    'moyen': lambda x: normaliser(x, 0.84),
    'ambiance': lambda x: niveau_rms(x, -22),
    'horloge': lambda x: normaliser(x, 0.7),
}


def fabriquer(filtre=''):
    for categorie, fichier, nom, fonction, niveau in SONS:
        if filtre not in fichier:
            continue
        x = fonction()
        boucle = categorie in ('ambiance', 'horloge')
        if not boucle:
            x = fondus(couper_silence(x), 0.002, 0.08)
        x = NIVEAUX[niveau](stereo(x))
        chemin = os.path.join(DOSSIER, fichier)
        os.makedirs(os.path.dirname(chemin), exist_ok=True)
        duree = exporter(x, chemin)
        print(f'{fichier:48s} {duree:6.1f} s  crête {np.abs(x).max():.2f}')
    ecrire_catalogue()


def ecrire_catalogue():
    lignes = [
        "'use strict';",
        "// Sons fournis avec l'application (fabriqués par outils/fabrique/fabriquer_sons.py).",
        'const CATALOGUE = [',
    ]
    for categorie, fichier, nom, _f, _n in SONS:
        nom_js = nom.replace("'", "\\'")
        lignes.append(f"  {{ cat: '{categorie}', fichier: 'sons/{fichier}', nom: '{nom_js}' }},")
    lignes.append('];')
    with open(os.path.join(DOSSIER, 'catalogue.js'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(lignes) + '\n')


if __name__ == '__main__':
    fabriquer(sys.argv[1] if len(sys.argv) > 1 else '')
