"""Configuration de l'application.

Valeurs par défaut, surchargeables par un fichier ``config.json`` placé à côté
du dossier ``app`` ou par des variables d'environnement (préfixe ``PHOTOGRAM_``).
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, fields
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent


@dataclass
class Config:
    # Dossier qui contient a_traiter/, travail/ et resultats/
    dossier_donnees: Path = RACINE / "donnees"
    # Image Docker d'OpenDroneMap ("opendronemap/odm:gpu" pour une carte NVIDIA)
    image_odm: str = "opendronemap/odm"
    gpu: bool = False
    # Mode démonstration : aucun calcul réel, sert à tester l'interface sans Docker
    simulation: bool = False
    port: int = 8000
    # "0.0.0.0" rend l'interface accessible aux téléphones du même Wi-Fi (option --reseau)
    hote: str = "127.0.0.1"
    # Secondes sans changement avant de considérer qu'un dossier déposé est complet
    delai_stabilite: int = 20
    intervalle_surveillance: int = 5
    # Garder les fichiers intermédiaires d'ODM (utile pour déboguer, prend beaucoup de place)
    garder_travail: bool = False
    # Options ODM ajoutées à celles choisies automatiquement, ex. ["--max-concurrency", "4"]
    options_supplementaires: list[str] = field(default_factory=list)

    @property
    def dossier_entree(self) -> Path:
        return self.dossier_donnees / "a_traiter"

    @property
    def dossier_travail(self) -> Path:
        return self.dossier_donnees / "travail"

    @property
    def dossier_resultats(self) -> Path:
        return self.dossier_donnees / "resultats"

    def creer_dossiers(self) -> None:
        for d in (
            self.dossier_entree,
            self.dossier_entree / "_en_cours",
            self.dossier_entree / "_fait",
            self.dossier_entree / "_erreur",
            self.dossier_travail,
            self.dossier_resultats,
        ):
            d.mkdir(parents=True, exist_ok=True)


def _convertir(valeur: str, type_attendu):
    if type_attendu in (bool, "bool"):
        return valeur.strip().lower() in ("1", "true", "oui", "yes", "on")
    if type_attendu in (int, "int"):
        return int(valeur)
    if type_attendu in (Path, "Path"):
        return Path(valeur)
    if type_attendu in ("list[str]",):
        return valeur.split()
    return valeur


def charger_config(fichier: Path | None = None) -> Config:
    config = Config()
    fichier = fichier or RACINE / "config.json"
    if fichier.exists():
        donnees = json.loads(fichier.read_text(encoding="utf-8"))
        for f in fields(Config):
            if f.name in donnees:
                valeur = donnees[f.name]
                setattr(config, f.name, Path(valeur) if f.name == "dossier_donnees" else valeur)
    for f in fields(Config):
        env = os.environ.get(f"PHOTOGRAM_{f.name.upper()}")
        if env is not None:
            setattr(config, f.name, _convertir(env, f.type))
    dossier = Path(config.dossier_donnees).expanduser()
    config.dossier_donnees = (dossier if dossier.is_absolute() else RACINE / dossier).resolve()
    return config
