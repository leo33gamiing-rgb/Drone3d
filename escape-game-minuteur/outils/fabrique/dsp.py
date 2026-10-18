"""Petite boîte à outils de synthèse sonore (numpy/scipy) pour fabriquer les sons de l'app."""
from fractions import Fraction

import numpy as np
import soundfile as sf
from scipy import signal

SR = 44100
alea = np.random.default_rng(1337)


# ---------- Bases ----------

def n_ech(duree):
    return int(round(duree * SR))


def temps(duree):
    return np.arange(n_ech(duree)) / SR


def bruit(duree):
    return alea.standard_normal(n_ech(duree))


def bruit_rose(duree):
    b = [0.049922035, -0.095993537, 0.050612699, -0.004408786]
    a = [1, -2.494956002, 2.017265875, -0.522189400]
    return normaliser(signal.lfilter(b, a, bruit(duree)), 1)


def bruit_brun(duree):
    x = passe_haut(np.cumsum(bruit(duree)), 15)
    return normaliser(x, 1)


def lisse(n, vitesse_hz, duree):
    """Courbe aléatoire douce entre -1 et 1 (environ `vitesse_hz` variations par seconde)."""
    k = max(2, int(duree * vitesse_hz) + 2)
    points = alea.uniform(-1, 1, k)
    x = np.linspace(0, k - 1, n)
    i = np.floor(x).astype(int).clip(0, k - 2)
    f = x - i
    f = f * f * (3 - 2 * f)  # interpolation douce
    return points[i] * (1 - f) + points[i + 1] * f


def enveloppe(points, duree):
    tp, vp = zip(*points)
    return np.interp(temps(duree), tp, vp)


def normaliser(x, crete=0.9):
    return x * (crete / (np.abs(x).max() + 1e-12))


def saturer(x, force=2.0):
    return np.tanh(force * x) / np.tanh(force)


def stereo(x, pan=0.0):
    if x.ndim == 2:
        return x
    angle = (pan + 1) * np.pi / 4
    return np.array([x * np.cos(angle), x * np.sin(angle)]) * np.sqrt(2)


def vitesse(x, facteur):
    """Accélère (> 1, plus aigu) ou ralentit (< 1, plus grave) comme une bande magnétique."""
    fr = Fraction(facteur).limit_denominator(64)
    return signal.resample_poly(x, fr.denominator, fr.numerator, axis=-1)


def ralenti_progressif(x, debut=1.0, fin=0.35):
    """Bande qui ralentit progressivement (la hauteur descend au fil du son)."""
    n = x.shape[-1]
    taux = np.linspace(debut, fin, n)
    positions = np.cumsum(taux)
    positions = positions[positions < n - 1]
    if x.ndim == 1:
        return np.interp(positions, np.arange(n), x)
    return np.array([np.interp(positions, np.arange(n), c) for c in x])


def inverser(x):
    return x[..., ::-1].copy()


# ---------- Filtres ----------

def _sos(genre, f, ordre):
    return signal.butter(ordre, f, genre, fs=SR, output='sos')


def passe_bas(x, f, ordre=2):
    return signal.sosfilt(_sos('lowpass', f, ordre), x, axis=-1)


def passe_haut(x, f, ordre=2):
    return signal.sosfilt(_sos('highpass', f, ordre), x, axis=-1)


def passe_bande(x, f1, f2, ordre=2):
    return signal.sosfilt(_sos('bandpass', [f1, min(f2, SR / 2.2)], ordre), x, axis=-1)


def resonateur(x, f, largeur):
    """Résonateur à deux pôles (gain 1 à fréquence nulle), comme dans les synthétiseurs de voix."""
    r = np.exp(-np.pi * largeur / SR)
    c = -r * r
    b = 2 * r * np.cos(2 * np.pi * f / SR)
    return signal.lfilter([1 - b - c], [1, -b, -c], x)


def filtre_variable(x, frequences, genre='bandpass', q=5.0, bloc=256):
    """Filtre dont la fréquence suit `frequences` (une valeur par échantillon)."""
    y = np.zeros_like(x)
    zi = np.zeros(2)
    for i in range(0, len(x), bloc):
        f = float(np.clip(frequences[i], 25, SR / 2.3))
        if genre == 'bandpass':
            b, a = signal.iirpeak(f, q, fs=SR)
        else:
            b, a = signal.butter(2, f, 'low', fs=SR)
        y[i:i + bloc], zi = signal.lfilter(b, a, x[i:i + bloc], zi=zi)
    return y


# ---------- Voix (synthèse par formants) ----------

VOYELLES = {
    'a': [(800, 90), (1200, 110), (2500, 140), (3500, 200), (4500, 250)],
    'e': [(480, 70), (1850, 110), (2600, 140), (3500, 200), (4500, 250)],
    'i': [(300, 60), (2300, 110), (3000, 160), (3700, 220), (4600, 260)],
    'o': [(450, 70), (800, 90), (2800, 140), (3500, 200), (4500, 250)],
    'ou': [(320, 60), (700, 90), (2500, 140), (3400, 200), (4500, 250)],
    'm': [(260, 70), (1100, 250), (2300, 220), (3300, 250)],
}


def filtre_voyelle(x, voyelle, echelle=1.0):
    for f, largeur in VOYELLES[voyelle]:
        if f * echelle < SR / 2.5:
            x = resonateur(x, f * echelle, largeur * echelle)
    return x


def source_glottale(f0, ouverture=0.6, jitter=0.01, souffle=0.08):
    """Impulsions des cordes vocales (modèle de Rosenberg) + souffle."""
    n = len(f0)
    duree = n / SR
    f = f0 * (1 + jitter * lisse(n, 30, duree))
    phase = np.cumsum(f / SR) % 1.0
    tp, tn = ouverture * 0.65, ouverture * 0.35
    debit = np.where(phase < tp, 0.5 * (1 - np.cos(np.pi * phase / tp)),
                     np.where(phase < tp + tn, np.cos(0.5 * np.pi * (phase - tp) / tn), 0.0))
    onde = np.diff(debit, prepend=0.0) * SR / np.maximum(f, 1)
    onde /= np.abs(onde).max() + 1e-9
    aspiration = passe_haut(alea.standard_normal(n), 500) * (0.3 + debit) * souffle
    return onde + aspiration


def voix(f0, voyelle='a', echelle=1.0, ouverture=0.6, jitter=0.01, souffle=0.08, rugosite=0.0):
    duree = len(f0) / SR
    src = source_glottale(f0, ouverture, jitter, souffle)
    if rugosite:
        src *= 1 + rugosite * lisse(len(f0), 70, duree)
    return normaliser(filtre_voyelle(src, voyelle, echelle))


# ---------- Percussions (synthèse modale) ----------

def reponse_modale(modes, duree=None):
    """Somme de sinusoïdes amorties : [(fréquence, durée d'amortissement, amplitude), ...]."""
    duree = duree or max(d for _, d, _ in modes) * 6
    t = temps(duree)
    return sum(a * np.exp(-t / d) * np.sin(2 * np.pi * f * t) for f, d, a in modes)


def frapper(modes, duree_impact=0.002, force=1.0, clic=0.0, variation=0.01):
    """Un choc sur un objet résonant (porte, horloge, métal...)."""
    modes = [(f * (1 + alea.uniform(-variation, variation)), d, a) for f, d, a in modes]
    m = max(2, n_ech(duree_impact))
    excitation = np.sin(np.pi * np.arange(m) / m)
    x = normaliser(signal.fftconvolve(excitation, reponse_modale(modes)))
    if clic:
        c = passe_bande(bruit(0.02), 1500, 7000) * np.exp(-temps(0.02) / 0.003)
        x[:len(c)] += clic * normaliser(c)
    return x * force


# ---------- Espace ----------

def reponse_salle(rt60, sombre=0.4, predelai=0.012):
    duree = rt60 * 1.1
    t = temps(duree)
    decroissance = 10 ** (-3 * t / rt60)
    canaux = []
    for _ in range(2):
        brut = alea.standard_normal(len(t))
        doux = passe_bas(brut, 1800) * 2.0
        k = np.clip(t / duree, 0, 1) * sombre
        h = (brut * (1 - k) + doux * k) * decroissance
        h = np.concatenate([np.zeros(n_ech(predelai)), h])
        canaux.append(h / np.sqrt(np.sum(h ** 2)))
    return np.array(canaux)


def reverb(x, rt60=1.5, mix=0.3, sombre=0.4, predelai=0.012, boucle=False):
    """Réverbération (stéréo). Avec `boucle`, la queue est repliée au début : boucle sans coupure."""
    st = stereo(x)
    h = reponse_salle(rt60, sombre, predelai)
    n = st.shape[1]
    humide = np.array([signal.fftconvolve(st[c], h[c]) for c in range(2)])
    if boucle:
        plie = humide[:, :n].copy()
        queue = humide[:, n:]
        for i in range(0, queue.shape[1], n):
            morceau = queue[:, i:i + n]
            plie[:, :morceau.shape[1]] += morceau
        humide, sec = plie, st
    else:
        sec = np.pad(st, ((0, 0), (0, humide.shape[1] - n)))
    return sec * (1 - mix) + humide * mix


def echo(x, delai=0.35, retour=0.4, repetitions=4):
    st = stereo(x)
    sortie = np.pad(st, ((0, 0), (0, n_ech(delai) * repetitions)))
    for k in range(1, repetitions + 1):
        i = n_ech(delai) * k
        decale = st * retour ** k
        if k % 2:
            decale = decale[::-1]  # ping-pong gauche/droite
        sortie[:, i:i + st.shape[1]] += decale
    return sortie


class Piste:
    """Table de mixage simple. Avec `boucle`, ce qui dépasse la fin revient au début."""

    def __init__(self, duree=0.0, boucle=False):
        self.x = np.zeros((2, n_ech(duree)))
        self.boucle = boucle

    def ajouter(self, son, debut=0.0, gain=1.0, pan=0.0):
        s = stereo(son, pan) * gain
        i = n_ech(debut)
        if self.boucle:
            n = self.x.shape[1]
            for j in range(0, s.shape[1], n):
                morceau = s[:, j:j + n]
                position = (i + j) % n
                fin = min(n, position + morceau.shape[1])
                self.x[:, position:fin] += morceau[:, :fin - position]
                reste = morceau.shape[1] - (fin - position)
                if reste > 0:
                    self.x[:, :reste] += morceau[:, fin - position:]
            return self
        fin = i + s.shape[1]
        if fin > self.x.shape[1]:
            self.x = np.pad(self.x, ((0, 0), (0, fin - self.x.shape[1])))
        self.x[:, i:fin] += s
        return self


def boucler(x, fondu=3.0):
    """Rend une texture bouclable : la fin est fondue dans le début (x doit dépasser de `fondu`)."""
    st = stereo(x)
    f = n_ech(fondu)
    n = st.shape[1] - f
    sortie = st[:, :n].copy()
    k = np.linspace(0, np.pi / 2, f)
    sortie[:, :f] = st[:, :f] * np.sin(k) + st[:, n:n + f] * np.cos(k)
    return sortie


# ---------- Finition ----------

def couper_silence(x, seuil_db=-55):
    st = stereo(x)
    niveau = np.abs(st).max(axis=0)
    seuil = niveau.max() * 10 ** (seuil_db / 20)
    au_dessus = np.nonzero(niveau > seuil)[0]
    if len(au_dessus) == 0:
        return st
    return st[:, :au_dessus[-1] + n_ech(0.05)]


def fondus(x, entree=0.003, sortie=0.03):
    x = x.copy()
    a, b = n_ech(entree), n_ech(sortie)
    if a:
        x[..., :a] *= np.linspace(0, 1, a)
    if b:
        x[..., -b:] *= np.linspace(1, 0, b)
    return x


def niveau_rms(x, cible_db):
    rms = np.sqrt(np.mean(x ** 2)) + 1e-12
    x = x * 10 ** (cible_db / 20) / rms
    crete = np.abs(x).max()
    if crete > 0.95:
        x = np.tanh(x / 0.95) * 0.95  # limiteur doux
    return x


def exporter(x, chemin, qualite=0.45):
    st = np.clip(stereo(x), -1, 1).T.astype(np.float32)
    with sf.SoundFile(chemin, 'w', SR, 2, format='OGG', subtype='VORBIS', compression_level=1 - qualite) as f:
        for i in range(0, len(st), 16384):  # par morceaux : libsndfile plante sur les gros blocs Vorbis
            f.write(st[i:i + 16384])
    return st.shape[0] / SR
