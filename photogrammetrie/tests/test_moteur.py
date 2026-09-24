import io

import pytest

from app import moteur
from app.config import Config

JOURNAL_ODM = """\x1b[39m[INFO]    Running dataset stage\x1b[0m
[INFO]    Running opensfm stage
[INFO]    running "/code/SuperBuild/install/bin/opensfm/bin/opensfm" detect_features "/datasets/p/opensfm"
[INFO]    running "/code/SuperBuild/install/bin/opensfm/bin/opensfm" match_features "/datasets/p/opensfm"
[INFO]    running "/code/SuperBuild/install/bin/opensfm/bin/opensfm" reconstruct "/datasets/p/opensfm"
[INFO]    Running openmvs stage
[INFO]    running "/code/SuperBuild/install/bin/DensifyPointCloud" "/datasets/p/scene.mvs"
[INFO]    Running odm_meshing stage
[INFO]    Running mvs_texturing stage
[INFO]    running "/code/SuperBuild/install/bin/texrecon" "/datasets/p/x"
[INFO]    Running odm_postprocess stage
"""


class FauxProcessus:
    def __init__(self, commande, code=0, **_):
        self.commande = commande
        self.code = code
        self.stdout = io.StringIO(JOURNAL_ODM)

    def wait(self):
        return self.code


def lancer(monkeypatch, code=0, **config):
    appels = {}

    def popen(commande, **kwargs):
        appels["commande"] = commande
        return FauxProcessus(commande, code)

    monkeypatch.setattr(moteur.subprocess, "Popen", popen)
    lignes, etapes = [], []
    moteur.MoteurODM(Config(**config)).lancer(
        "p_1", ["--gcp", "{projet}/gcp_list.txt"], lignes.append, lambda pct, e: etapes.append(pct)
    )
    return appels["commande"], lignes, etapes


def test_progression_croissante_et_journal_sans_couleurs(monkeypatch):
    commande, lignes, etapes = lancer(monkeypatch)
    assert etapes == sorted(etapes) and etapes[0] == 2 and etapes[-1] == 98
    assert 15 in etapes and 47 in etapes  # sous-étapes détectées
    assert not any("\x1b" in l for l in lignes)
    assert commande[commande.index("--gcp") + 1] == "/datasets/p_1/gcp_list.txt"
    assert "--gpus" not in commande


def test_option_gpu(monkeypatch):
    commande, _, _ = lancer(monkeypatch, gpu=True, image_odm="opendronemap/odm:gpu")
    assert commande[commande.index("--gpus") + 1] == "all" and "opendronemap/odm:gpu" in commande


def test_code_de_sortie_non_nul_leve_une_erreur(monkeypatch):
    with pytest.raises(moteur.ErreurMoteur):
        lancer(monkeypatch, code=1)
