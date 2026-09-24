"""Surveillance du dossier ``a_traiter`` : chaque sous-dossier déposé devient un calcul."""

from __future__ import annotations

import shutil
import threading
import time
from pathlib import Path

from .travaux import GestionnaireTravaux, creer_identifiant

DOSSIERS_SYSTEME = {"_en_cours", "_fait", "_erreur"}


def _empreinte(dossier: Path) -> tuple[int, int]:
    fichiers = [f for f in dossier.rglob("*") if f.is_file()]
    return len(fichiers), sum(f.stat().st_size for f in fichiers)


class Surveillance:
    def __init__(self, gestionnaire: GestionnaireTravaux, journal=print):
        self.gestionnaire = gestionnaire
        self.config = gestionnaire.config
        self.journal = journal
        # dossier -> (empreinte, instant depuis lequel elle n'a pas changé)
        self._vus: dict[Path, tuple[tuple[int, int], float]] = {}

    def verifier(self, maintenant: float | None = None) -> list[str]:
        """Un passage de surveillance ; renvoie les identifiants des travaux créés."""
        maintenant = time.monotonic() if maintenant is None else maintenant
        crees = []
        presents = set()
        for dossier in sorted(self.config.dossier_entree.iterdir()):
            if not dossier.is_dir() or dossier.name in DOSSIERS_SYSTEME or dossier.name.startswith("."):
                continue
            presents.add(dossier)
            try:
                empreinte = _empreinte(dossier)
            except OSError:  # fichier en cours de copie ou supprimé entre-temps
                continue
            precedent = self._vus.get(dossier)
            if precedent is None or precedent[0] != empreinte or empreinte[0] == 0:
                self._vus[dossier] = (empreinte, maintenant)
                continue
            if maintenant - precedent[1] < self.config.delai_stabilite:
                continue
            # Plus rien ne bouge : la copie est terminée, on lance le calcul
            id_ = creer_identifiant(dossier.name)
            try:
                shutil.move(str(dossier), str(self.gestionnaire.dossier_photos(id_)))
            except OSError as e:
                self.journal(f"Impossible de prendre en charge {dossier.name} : {e}")
                continue
            self._vus.pop(dossier, None)
            self.gestionnaire.soumettre(id_, dossier.name, source="dossier")
            self.journal(f"Nouveau dossier détecté : {dossier.name} -> calcul {id_}")
            crees.append(id_)
        for disparu in set(self._vus) - presents:
            self._vus.pop(disparu, None)
        return crees

    def demarrer(self) -> threading.Thread:
        def boucle():
            while True:
                try:
                    self.verifier()
                except Exception as e:  # noqa: BLE001 - la surveillance ne doit jamais s'arrêter
                    self.journal(f"Erreur de surveillance : {e}")
                time.sleep(self.config.intervalle_surveillance)

        thread = threading.Thread(target=boucle, name="surveillance", daemon=True)
        thread.start()
        return thread
