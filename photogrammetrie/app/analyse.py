"""Analyse d'un lot de photos : appareils, GPS, RTK, points de contrôle.

Ces informations servent à choisir automatiquement les réglages du calcul
(voir ``profils.py``) et à annoncer la précision qu'on peut en attendre.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path

from PIL import ExifTags, Image

try:  # Photos HEIC des iPhone
    from pillow_heif import register_heif_opener

    register_heif_opener()
    HEIC_DISPONIBLE = True
except ImportError:  # pragma: no cover - dépend de l'installation
    HEIC_DISPONIBLE = False

EXTENSIONS_PHOTOS = {".jpg", ".jpeg", ".png", ".tif", ".tiff"}
EXTENSIONS_HEIC = {".heic", ".heif"}
FICHIER_GCP = "gcp_list.txt"
FICHIER_GEO = "geo.txt"

MARQUES_DRONES = {"dji", "parrot", "autel", "autel robotics", "skydio", "yuneec", "sensefly", "wingtra"}
MARQUES_TELEPHONES = {
    "apple", "samsung", "google", "xiaomi", "huawei", "honor", "oneplus", "oppo",
    "vivo", "motorola", "nokia", "realme", "fairphone", "nothing", "asus",
}

# Valeurs de drone-dji:RtkFlag dans les métadonnées XMP des photos DJI
RTK_FIXE = 50
RTK_FLOTTANT = 34

_XMP_RTK = re.compile(rb"drone-dji:RtkFlag(?:=\"|>)\s*([0-9.+-]+)")
_XMP_RTK_STD = re.compile(rb"drone-dji:RtkStd(?:Lon|Lat|Hgt)(?:=\"|>)\s*([0-9.eE+-]+)")


@dataclass
class InfoPhoto:
    nom: str
    marque: str = ""
    modele: str = ""
    largeur: int = 0
    hauteur: int = 0
    gps: bool = False
    rtk: str = "aucun"  # "fixe", "flottant" ou "aucun"
    rtk_precision_m: float | None = None
    type_appareil: str = "inconnu"  # "drone", "telephone" ou "inconnu"
    lisible: bool = True


@dataclass
class Analyse:
    photos: list[InfoPhoto] = field(default_factory=list)
    gcp: bool = False
    geo_txt: bool = False
    fichiers_ignores: list[str] = field(default_factory=list)

    @property
    def nb_photos(self) -> int:
        return sum(1 for p in self.photos if p.lisible)

    @property
    def nb_gps(self) -> int:
        return sum(1 for p in self.photos if p.lisible and p.gps)

    @property
    def nb_rtk_fixe(self) -> int:
        return sum(1 for p in self.photos if p.lisible and p.rtk == "fixe")

    @property
    def nb_illisibles(self) -> int:
        return sum(1 for p in self.photos if not p.lisible)

    @property
    def georeferencee(self) -> bool:
        """Assez de photos géolocalisées (ou un fichier geo.txt) pour un modèle à l'échelle réelle."""
        return self.geo_txt or self.gcp or (self.nb_photos > 0 and self.nb_gps >= 0.8 * self.nb_photos)

    @property
    def rtk(self) -> bool:
        return self.nb_photos > 0 and self.nb_rtk_fixe >= 0.8 * self.nb_photos

    @property
    def appareils(self) -> dict[str, int]:
        compte = Counter(
            (f"{p.marque} {p.modele}".strip() or "Appareil inconnu") for p in self.photos if p.lisible
        )
        return dict(compte.most_common())

    @property
    def source(self) -> str:
        types = {p.type_appareil for p in self.photos if p.lisible} - {"inconnu"}
        if types == {"drone"}:
            return "drone"
        if types == {"telephone"}:
            return "telephone"
        if len(types) > 1:
            return "mixte"
        return "inconnu"

    @property
    def part_dji(self) -> float:
        if not self.nb_photos:
            return 0.0
        return sum(1 for p in self.photos if p.lisible and p.marque.lower() == "dji") / self.nb_photos

    def resume(self) -> dict:
        return {
            "nb_photos": self.nb_photos,
            "nb_gps": self.nb_gps,
            "nb_rtk_fixe": self.nb_rtk_fixe,
            "nb_illisibles": self.nb_illisibles,
            "georeferencee": self.georeferencee,
            "rtk": self.rtk,
            "gcp": self.gcp,
            "geo_txt": self.geo_txt,
            "source": self.source,
            "appareils": self.appareils,
            "fichiers_ignores": self.fichiers_ignores,
        }

    def detail(self) -> list[dict]:
        return [asdict(p) for p in self.photos]


def _type_appareil(marque: str, modele: str, xmp_dji: bool) -> str:
    m = marque.lower().strip()
    if xmp_dji or m in MARQUES_DRONES:
        return "drone"
    if m in MARQUES_TELEPHONES or "iphone" in modele.lower() or "pixel" in modele.lower():
        return "telephone"
    return "inconnu"


def _lire_xmp(chemin: Path) -> bytes:
    """Renvoie le bloc XMP (les DJI le placent dans les premiers ko du fichier)."""
    with open(chemin, "rb") as f:
        debut = f.read(512 * 1024)
    i = debut.find(b"<x:xmpmeta")
    if i < 0:
        return b""
    j = debut.find(b"</x:xmpmeta>", i)
    return debut[i : j if j > 0 else len(debut)]


def analyser_photo(chemin: Path) -> InfoPhoto:
    info = InfoPhoto(nom=chemin.name)
    try:
        with Image.open(chemin) as img:
            info.largeur, info.hauteur = img.size
            exif = img.getexif()
            info.marque = str(exif.get(ExifTags.Base.Make, "") or "").strip("\x00 ").strip()
            info.modele = str(exif.get(ExifTags.Base.Model, "") or "").strip("\x00 ").strip()
            gps = exif.get_ifd(ExifTags.IFD.GPSInfo)
            lat = gps.get(ExifTags.GPS.GPSLatitude)
            lon = gps.get(ExifTags.GPS.GPSLongitude)
            info.gps = bool(lat and lon and any(float(v) for v in (*lat, *lon)))
    except Exception:
        info.lisible = False
        return info

    xmp = _lire_xmp(chemin) if chemin.suffix.lower() in {".jpg", ".jpeg"} else b""
    m = _XMP_RTK.search(xmp)
    if m:
        drapeau = int(float(m.group(1)))
        info.rtk = "fixe" if drapeau == RTK_FIXE else "flottant" if drapeau == RTK_FLOTTANT else "aucun"
        ecarts = [float(v) for v in _XMP_RTK_STD.findall(xmp)]
        if ecarts:
            info.rtk_precision_m = round(max(ecarts), 3)
    info.type_appareil = _type_appareil(info.marque, info.modele, b"drone-dji" in xmp)
    return info


def lister_photos(dossier: Path) -> tuple[list[Path], list[str]]:
    """Photos du dossier (sous-dossiers compris) et fichiers ignorés."""
    photos, ignores = [], []
    for f in sorted(dossier.rglob("*")):
        if not f.is_file() or f.name.startswith("."):
            continue
        ext = f.suffix.lower()
        if ext in EXTENSIONS_PHOTOS or (ext in EXTENSIONS_HEIC and HEIC_DISPONIBLE):
            photos.append(f)
        elif f.name not in (FICHIER_GCP, FICHIER_GEO):
            ignores.append(str(f.relative_to(dossier)))
    return photos, ignores


def analyser_dossier(dossier: Path) -> Analyse:
    photos, ignores = lister_photos(dossier)
    return Analyse(
        photos=[analyser_photo(p) for p in photos],
        gcp=(dossier / FICHIER_GCP).exists(),
        geo_txt=(dossier / FICHIER_GEO).exists(),
        fichiers_ignores=ignores,
    )
