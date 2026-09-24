from __future__ import annotations

import sys
from pathlib import Path

import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import Config  # noqa: E402

XMP_DJI = (
    '<x:xmpmeta xmlns:x="adobe:ns:meta/"><rdf:Description '
    'drone-dji:RtkFlag="{flag}" drone-dji:RtkStdLon="0.012" drone-dji:RtkStdLat="0.015" '
    'drone-dji:RtkStdHgt="0.031"/></x:xmpmeta>'
)


def creer_photo(chemin: Path, marque="", modele="", gps=False, rtk_flag=None, taille=(64, 48)):
    """Petite image JPEG avec les métadonnées voulues (EXIF, GPS, XMP DJI)."""
    img = Image.new("RGB", taille, (120, 140, 160))
    exif = Image.Exif()
    if marque:
        exif[0x010F] = marque
    if modele:
        exif[0x0110] = modele
    if gps:
        exif[0x8825] = {1: "N", 2: (48.0, 51.0, 29.0), 3: "E", 4: (2.0, 17.0, 40.0)}
    options = {"exif": exif.tobytes()}
    if rtk_flag is not None:
        # Le lecteur cherche le bloc XMP dans les premiers octets : un commentaire JPEG suffit
        options["comment"] = XMP_DJI.format(flag=rtk_flag).encode()
    chemin.parent.mkdir(parents=True, exist_ok=True)
    img.save(chemin, "JPEG", **options)
    return chemin


@pytest.fixture
def config(tmp_path) -> Config:
    c = Config(dossier_donnees=tmp_path / "donnees", simulation=True, delai_stabilite=10)
    c.creer_dossiers()
    return c
