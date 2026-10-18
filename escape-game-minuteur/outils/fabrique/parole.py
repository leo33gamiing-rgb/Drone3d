"""Synthèse vocale hors ligne (espeak-ng, via le paquet Python espeakng-loader)."""
import ctypes
import numpy as np
import espeakng_loader

_lib = None
_taux = 22050


def _init():
    global _lib, _taux
    if _lib:
        return _lib
    _lib = ctypes.cdll.LoadLibrary(espeakng_loader.get_library_path())
    _lib.espeak_Initialize.restype = ctypes.c_int
    _taux = _lib.espeak_Initialize(2, 0, espeakng_loader.get_data_path().encode(), 0)  # synchrone
    return _lib


RAPPEL = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.POINTER(ctypes.c_short), ctypes.c_int, ctypes.c_void_p)


def parler(texte, voix='fr+whisper', vitesse=130, hauteur=40, etendue=30):
    """Renvoie (signal float32 mono, fréquence d'échantillonnage)."""
    lib = _init()
    morceaux = []

    def recevoir(wav, n, _evenements):
        if n > 0:
            morceaux.append(np.ctypeslib.as_array(wav, shape=(n,)).copy())
        return 0

    rappel = RAPPEL(recevoir)
    lib.espeak_SetSynthCallback(rappel)
    lib.espeak_SetVoiceByName(voix.encode())
    lib.espeak_SetParameter(1, vitesse, 0)   # vitesse (mots/min)
    lib.espeak_SetParameter(3, hauteur, 0)   # hauteur 0-100
    lib.espeak_SetParameter(4, etendue, 0)   # étendue 0-100
    octets = texte.encode('utf-8')
    lib.espeak_Synth(octets, len(octets) + 1, 0, 0, 0, 1, None, None)  # 1 = UTF-8
    lib.espeak_Synchronize()
    signal = np.concatenate(morceaux).astype(np.float32) / 32768 if morceaux else np.zeros(1, np.float32)
    return signal, _taux
