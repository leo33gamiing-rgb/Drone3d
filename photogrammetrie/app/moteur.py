"""Lancement d'OpenDroneMap (via Docker) et suivi de sa progression."""

from __future__ import annotations

import re
import shutil
import subprocess
import time
from pathlib import Path
from typing import Callable

from .config import Config

# Étapes d'ODM et progression (%) atteinte au début de chacune
ETAPES = {
    "dataset": (2, "Lecture des photos"),
    "split": (4, "Découpage"),
    "merge": (4, "Fusion"),
    "opensfm": (5, "Alignement des photos (points communs)"),
    "openmvs": (45, "Nuage de points dense"),
    "odm_filterpoints": (65, "Filtrage du nuage de points"),
    "odm_meshing": (70, "Création du maillage 3D"),
    "mvs_texturing": (78, "Application des textures"),
    "odm_georeferencing": (86, "Géoréférencement"),
    "odm_dem": (89, "Modèle numérique de surface"),
    "odm_orthophoto": (92, "Orthophoto"),
    "odm_report": (96, "Rapport qualité"),
    "odm_postprocess": (98, "Finalisation"),
}
_RE_ETAPE = re.compile(r"Running (\w+) stage")
_RE_COULEURS = re.compile(r"\x1b\[[0-9;]*m")

# Fichiers produits par ODM -> nom lisible dans le dossier de résultats
SORTIES = {
    "odm_texturing/odm_textured_model_geo.glb": "modele_3d.glb",
    "odm_texturing/odm_textured_model_geo.obj": "modele_3d.obj",
    # Le .obj référence ce .mtl par son nom d'origine : on le garde tel quel
    "odm_texturing/odm_textured_model_geo.mtl": "odm_textured_model_geo.mtl",
    "odm_georeferencing/odm_georeferenced_model.laz": "nuage_points.laz",
    "odm_filterpoints/point_cloud.ply": "nuage_points.ply",
    "odm_orthophoto/odm_orthophoto.tif": "orthophoto.tif",
    "odm_dem/dsm.tif": "mns.tif",
    "odm_report/report.pdf": "rapport_qualite.pdf",
}
# Les textures de l'OBJ sont copiées à côté (odm_textured_model_geo_material0000_map_Kd.png, ...)
MOTIF_TEXTURES = "odm_texturing/odm_textured_model_geo*.png"


class ErreurMoteur(RuntimeError):
    pass


Journal = Callable[[str], None]
Progression = Callable[[int, str], None]


def docker_disponible() -> tuple[bool, str]:
    if not shutil.which("docker"):
        return False, "Docker n'est pas installé (ou pas dans le PATH)."
    try:
        r = subprocess.run(["docker", "info"], capture_output=True, text=True, timeout=20)
    except (OSError, subprocess.TimeoutExpired) as e:
        return False, f"Docker ne répond pas : {e}"
    if r.returncode != 0:
        return False, "Docker est installé mais pas démarré (lancez Docker Desktop)."
    return True, "Docker prêt."


class MoteurODM:
    """Exécute ``docker run opendronemap/odm`` sur un projet du dossier de travail."""

    def __init__(self, config: Config):
        self.config = config
        self._processus: dict[str, subprocess.Popen] = {}

    def lancer(self, projet: str, options: list[str], journal: Journal, progression: Progression) -> None:
        dossier_travail = self.config.dossier_travail.resolve()
        options = [o.replace("{projet}", f"/datasets/{projet}") for o in options]
        commande = ["docker", "run", "--rm", "--name", f"photogram_{projet}"]
        if self.config.gpu:
            commande += ["--gpus", "all"]
        commande += [
            "-v", f"{dossier_travail}:/datasets",
            self.config.image_odm,
            "--project-path", "/datasets", projet,
            *options,
        ]
        journal("$ " + " ".join(commande))
        proc = subprocess.Popen(
            commande,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )
        self._processus[projet] = proc
        derniere_etape = ""
        try:
            assert proc.stdout is not None
            for ligne in proc.stdout:
                ligne = _RE_COULEURS.sub("", ligne).rstrip()
                journal(ligne)
                m = _RE_ETAPE.search(ligne)
                if m and m.group(1) in ETAPES and m.group(1) != derniere_etape:
                    derniere_etape = m.group(1)
                    pct, libelle = ETAPES[derniere_etape]
                    progression(pct, libelle)
            code = proc.wait()
        finally:
            self._processus.pop(projet, None)
        if code != 0:
            raise ErreurMoteur(f"OpenDroneMap s'est arrêté avec le code {code}.")

    def annuler(self, projet: str) -> None:
        if projet in self._processus:
            subprocess.run(["docker", "kill", f"photogram_{projet}"], capture_output=True)


class MoteurSimulation:
    """Faux moteur pour essayer l'interface sans Docker : n'effectue aucun calcul.

    Il parcourt les étapes rapidement et fournit un modèle GLB d'exemple.
    """

    simulation = True

    def __init__(self, config: Config, modele_exemple: Path | None = None, pause: float = 0.4):
        self.config = config
        self.modele_exemple = modele_exemple
        self.pause = pause
        self._annules: set[str] = set()

    def lancer(self, projet: str, options: list[str], journal: Journal, progression: Progression) -> None:
        journal("[SIMULATION] Aucun calcul réel n'est effectué.")
        journal("Options qui seraient utilisées : " + " ".join(options))
        for etape, (pct, libelle) in ETAPES.items():
            if etape in ("split", "merge"):
                continue
            if projet in self._annules:
                self._annules.discard(projet)
                raise ErreurMoteur("Annulé.")
            journal(f"[INFO]    Running {etape} stage")
            progression(pct, libelle)
            time.sleep(self.pause)
        if self.modele_exemple and self.modele_exemple.exists():
            dest = self.config.dossier_travail / projet / "odm_texturing" / "odm_textured_model_geo.glb"
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(self.modele_exemple, dest)

    def annuler(self, projet: str) -> None:
        self._annules.add(projet)


def recuperer_sorties(dossier_projet: Path, dossier_resultat: Path) -> list[str]:
    """Copie les fichiers utiles d'ODM sous des noms lisibles ; renvoie la liste copiée."""
    dossier_resultat.mkdir(parents=True, exist_ok=True)
    copies = []
    for source, nom in SORTIES.items():
        chemin = dossier_projet / source
        if nom == "nuage_points.ply" and "nuage_points.laz" in copies:
            continue  # même nuage : le .laz géoréférencé suffit
        if chemin.exists():
            shutil.copy(chemin, dossier_resultat / nom)
            copies.append(nom)
    if "modele_3d.obj" in copies:
        for texture in dossier_projet.glob(MOTIF_TEXTURES):
            shutil.copy(texture, dossier_resultat / texture.name)
    return copies
