"""Choix automatique des réglages d'OpenDroneMap selon les photos fournies.

Principe : peu de photos donne un modèle rapide et approximatif ; plus il y a de
photos, de GPS, de RTK ou de points de contrôle, plus le calcul est poussé et
plus le résultat est précis.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

from .analyse import FICHIER_GCP, FICHIER_GEO, Analyse

MIN_PHOTOS = 3

# Appareils DJI à obturateur mécanique : pas besoin de correction « rolling shutter »
OBTURATEUR_MECANIQUE = ("FC6310", "FC6540", "M3E", "L1D", "L2", "P1", "ZH20", "FC7303")


@dataclass
class Profil:
    code: str
    libelle: str
    niveau: int  # 1 (esquisse) à 5 (très grand chantier)
    options: list[str]
    precision: str
    fiabilite: int  # indice 0-100 affiché à l'utilisateur
    duree_estimee: str
    avertissements: list[str] = field(default_factory=list)
    conseils: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


class PasAssezDePhotos(ValueError):
    pass


# (code, libellé, niveau, nb min de photos, options de base, minutes par photo)
_VOLUMES = [
    (
        "esquisse", "Esquisse rapide", 1, MIN_PHOTOS,
        [
            "--feature-quality", "ultra", "--min-num-features", "20000",
            "--matcher-type", "bruteforce", "--pc-quality", "high",
            "--mesh-size", "100000", "--mesh-octree-depth", "10",
            "--use-3dmesh", "--skip-orthophoto", "--skip-report",
        ],
        0.8,
    ),
    (
        "standard", "Standard", 2, 10,
        [
            "--feature-quality", "ultra", "--min-num-features", "15000",
            "--matcher-type", "bruteforce", "--pc-quality", "high",
            "--mesh-size", "200000", "--mesh-octree-depth", "11", "--use-3dmesh",
        ],
        0.6,
    ),
    (
        "detaille", "Détaillé", 3, 50,
        [
            "--feature-quality", "high", "--pc-quality", "high",
            "--mesh-size", "400000", "--mesh-octree-depth", "12",
        ],
        0.4,
    ),
    (
        "grand", "Grand chantier", 4, 300,
        [
            "--feature-quality", "high", "--pc-quality", "medium",
            "--mesh-size", "500000", "--mesh-octree-depth", "12",
        ],
        0.25,
    ),
    (
        "tres_grand", "Très grand chantier", 5, 800,
        [
            "--feature-quality", "high", "--pc-quality", "medium",
            "--mesh-size", "600000", "--mesh-octree-depth", "12",
        ],
        0.25,
    ),
]


def _volume(nb: int):
    choix = _VOLUMES[0]
    for v in _VOLUMES:
        if nb >= v[3]:
            choix = v
    return choix


def _fiabilite(analyse: Analyse) -> int:
    """Indice indicatif : nombre de photos (jusqu'à 60 pts) + géoréférencement (jusqu'à 40 pts)."""
    nb = analyse.nb_photos
    points_photos = 60 * min(1.0, max(0, nb - MIN_PHOTOS + 1) / 150) ** 0.5
    if analyse.gcp and analyse.rtk:
        points_geo = 40
    elif analyse.gcp or analyse.rtk:
        points_geo = 35
    elif analyse.georeferencee:
        points_geo = 20
    else:
        points_geo = 0
    return max(5, round(points_photos + points_geo))


def _precision(analyse: Analyse) -> str:
    if analyse.gcp:
        return (
            "Position absolue calée sur vos points de contrôle (souvent 1 à 3 cm si les points "
            "sont bien mesurés et répartis)."
        )
    if analyse.rtk:
        precisions = [p.rtk_precision_m for p in analyse.photos if p.rtk_precision_m]
        detail = f" (écart-type RTK max relevé : {max(precisions) * 100:.1f} cm)" if precisions else ""
        return f"Position absolue de l'ordre de 2 à 5 cm grâce au RTK fixe{detail}."
    if analyse.georeferencee:
        return (
            "Formes et distances relatives correctes ; position absolue décalée de 1 à 5 m "
            "(GPS standard, sans RTK)."
        )
    return (
        "Forme correcte mais échelle et position arbitraires : les photos n'ont pas de GPS. "
        "Les mesures en mètres ne seront pas fiables sans points de contrôle."
    )


def choisir_profil(analyse: Analyse, options_supplementaires: list[str] | None = None) -> Profil:
    nb = analyse.nb_photos
    if nb < MIN_PHOTOS:
        raise PasAssezDePhotos(
            f"Il faut au moins {MIN_PHOTOS} photos lisibles (trouvées : {nb})."
        )

    code, libelle, niveau, _, options, minutes_par_photo = _volume(nb)
    options = list(options) + ["--gltf"]
    avertissements: list[str] = []
    conseils: list[str] = []

    if analyse.georeferencee:
        if niveau >= 2:
            options.append("--dsm")
        if niveau >= 3:
            options.append("--auto-boundary")
    elif "--skip-orthophoto" not in options:
        # Sans GPS, orthophoto et MNS n'ont pas de sens (pas de repère au sol)
        options.append("--skip-orthophoto")

    if analyse.gcp:
        options += ["--gcp", f"{{projet}}/{FICHIER_GCP}"]
    if analyse.geo_txt:
        options += ["--geo", f"{{projet}}/{FICHIER_GEO}"]

    modeles = " ".join(analyse.appareils)
    if analyse.part_dji >= 0.5 and niveau >= 2 and not any(m in modeles for m in OBTURATEUR_MECANIQUE):
        options.append("--rolling-shutter")
        conseils.append(
            "Correction « rolling shutter » activée (caméra DJI sans obturateur mécanique) : "
            "volez lentement pour de meilleurs résultats."
        )

    options += options_supplementaires or []

    # Avertissements et conseils pour progresser
    if niveau == 1:
        avertissements.append(
            "Peu de photos : le modèle sera partiel et approximatif. Les photos doivent se "
            "recouvrir fortement (au moins 70 %) et être prises en tournant autour du sujet, "
            "tous les 15 à 20° environ."
        )
    if analyse.nb_illisibles:
        avertissements.append(f"{analyse.nb_illisibles} fichier(s) illisible(s) ignoré(s).")
    if analyse.source == "mixte":
        avertissements.append(
            "Photos de téléphone et de drone mélangées : cela fonctionne si elles montrent les "
            "mêmes zones avec assez de recouvrement."
        )
    if 0 < analyse.nb_gps < 0.8 * nb and not analyse.geo_txt:
        avertissements.append(
            f"Seulement {analyse.nb_gps}/{nb} photos ont un GPS : le modèle n'est pas mis à l'échelle réelle."
        )
    if niveau == 5:
        avertissements.append(
            "Très gros lot : prévoyez 32 Go de RAM minimum et plusieurs heures de calcul. "
            "En cas de manque de mémoire, découpez la zone en plusieurs dossiers."
        )

    if nb < 50:
        conseils.append("Plus de photos (50+) avec un bon recouvrement = modèle plus complet et plus fin.")
    if not analyse.georeferencee:
        conseils.append("Activez la localisation de l'appareil photo pour obtenir un modèle à l'échelle.")
    elif not analyse.rtk and not analyse.gcp:
        conseils.append(
            "Pour une précision centimétrique : drone avec RTK, ou fichier gcp_list.txt "
            "(points de contrôle) déposé avec les photos."
        )

    minutes = 3 + nb * minutes_par_photo
    duree = f"environ {max(1, round(minutes * 0.5))} à {round(minutes * 2)} min (indicatif, dépend du PC)"

    return Profil(
        code=code,
        libelle=libelle,
        niveau=niveau,
        options=options,
        precision=_precision(analyse),
        fiabilite=_fiabilite(analyse),
        duree_estimee=duree,
        avertissements=avertissements,
        conseils=conseils,
    )
