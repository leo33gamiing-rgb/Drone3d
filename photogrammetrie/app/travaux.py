"""File d'attente des calculs : un travail = un dossier de photos -> un modèle 3D.

Les travaux sont traités un par un (la photogrammétrie utilise déjà toute la
machine). Leur état est enregistré dans ``resultats/<id>/travail.json`` pour
survivre à un redémarrage.
"""

from __future__ import annotations

import json
import queue
import re
import shutil
import threading
import time
import traceback
import unicodedata
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path

from PIL import Image

from .analyse import EXTENSIONS_HEIC, FICHIER_GCP, FICHIER_GEO, analyser_dossier, lister_photos
from .config import Config
from .moteur import ErreurMoteur, recuperer_sorties
from .profils import PasAssezDePhotos, choisir_profil

EN_ATTENTE, EN_COURS, TERMINE, ERREUR, ANNULE = "en_attente", "en_cours", "termine", "erreur", "annule"


@dataclass
class Travail:
    id: str
    nom: str
    source: str  # "web" ou "dossier"
    statut: str = EN_ATTENTE
    progression: int = 0
    etape: str = "En attente"
    cree: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    debut: str | None = None
    fin: str | None = None
    analyse: dict | None = None
    profil: dict | None = None
    sorties: list[str] = field(default_factory=list)
    erreur: str | None = None
    simulation: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


def creer_identifiant(nom: str) -> str:
    base = unicodedata.normalize("NFKD", nom).encode("ascii", "ignore").decode()
    base = re.sub(r"[^A-Za-z0-9]+", "_", base).strip("_")[:40] or "projet"
    return f"{base}_{datetime.now():%Y%m%d-%H%M%S}"


class GestionnaireTravaux:
    def __init__(self, config: Config, moteur):
        self.config = config
        self.moteur = moteur
        self._travaux: dict[str, Travail] = {}
        self._file: queue.Queue[str] = queue.Queue()
        self._verrou = threading.Lock()
        self._thread: threading.Thread | None = None
        config.creer_dossiers()
        self._recharger()

    # --- Accès -----------------------------------------------------------------

    def lister(self) -> list[Travail]:
        return sorted(self._travaux.values(), key=lambda t: t.cree, reverse=True)

    def obtenir(self, id_: str) -> Travail | None:
        return self._travaux.get(id_)

    def dossier_photos(self, id_: str) -> Path:
        """Où déposer les photos d'un nouveau travail avant de le soumettre."""
        return self.config.dossier_entree / "_en_cours" / id_

    def dossier_resultat(self, id_: str) -> Path:
        return self.config.dossier_resultats / id_

    def journal(self, id_: str) -> Path:
        return self.dossier_resultat(id_) / "journal.log"

    # --- Cycle de vie -------------------------------------------------------------

    def soumettre(self, id_: str, nom: str, source: str) -> Travail:
        travail = Travail(id=id_, nom=nom, source=source)
        with self._verrou:
            self._travaux[id_] = travail
        self._enregistrer(travail)
        self._file.put(id_)
        return travail

    def annuler(self, id_: str) -> bool:
        travail = self._travaux.get(id_)
        if not travail or travail.statut not in (EN_ATTENTE, EN_COURS):
            return False
        en_attente = travail.statut == EN_ATTENTE
        travail.statut, travail.etape = ANNULE, "Annulé"
        if en_attente:
            self._ranger_entree(self.dossier_photos(id_), "_erreur")
        else:
            self.moteur.annuler(id_)
        self._enregistrer(travail)
        return True

    def supprimer(self, id_: str) -> bool:
        travail = self._travaux.get(id_)
        if not travail or travail.statut == EN_COURS:
            return False
        with self._verrou:
            del self._travaux[id_]
        shutil.rmtree(self.dossier_resultat(id_), ignore_errors=True)
        shutil.rmtree(self.config.dossier_travail / id_, ignore_errors=True)
        return True

    def demarrer(self) -> None:
        if self._thread is None:
            self._thread = threading.Thread(target=self._boucle, name="photogrammetrie", daemon=True)
            self._thread.start()

    def attendre_fin(self, id_: str, intervalle: float = 1.0) -> Travail:
        while self._travaux[id_].statut in (EN_ATTENTE, EN_COURS):
            time.sleep(intervalle)
        return self._travaux[id_]

    # --- Traitement -----------------------------------------------------------------

    def _boucle(self) -> None:
        while True:
            id_ = self._file.get()
            travail = self._travaux.get(id_)
            if travail and travail.statut == EN_ATTENTE:
                self._traiter(travail)

    def _traiter(self, travail: Travail) -> None:
        resultat = self.dossier_resultat(travail.id)
        resultat.mkdir(parents=True, exist_ok=True)
        fichier_journal = open(self.journal(travail.id), "a", encoding="utf-8")

        def ecrire(ligne: str) -> None:
            fichier_journal.write(ligne + "\n")
            fichier_journal.flush()

        def avancer(pct: int, etape: str) -> None:
            travail.progression, travail.etape = pct, etape
            self._enregistrer(travail)

        travail.statut, travail.debut = EN_COURS, datetime.now().isoformat(timespec="seconds")
        travail.simulation = getattr(self.moteur, "simulation", False)
        entree = self.dossier_photos(travail.id)
        try:
            avancer(1, "Préparation des photos")
            projet = self._preparer(travail.id, entree, ecrire)

            avancer(1, "Analyse des photos")
            analyse = analyser_dossier(projet / "images")
            analyse.gcp = (projet / FICHIER_GCP).exists()
            analyse.geo_txt = (projet / FICHIER_GEO).exists()
            travail.analyse = analyse.resume()
            (resultat / "analyse_photos.json").write_text(
                json.dumps(analyse.detail(), indent=2, ensure_ascii=False), encoding="utf-8"
            )
            profil = choisir_profil(analyse, self.config.options_supplementaires)
            travail.profil = profil.to_dict()
            ecrire(f"Profil choisi : {profil.libelle} ({analyse.nb_photos} photos)")
            self._enregistrer(travail)

            self.moteur.lancer(travail.id, profil.options, ecrire, avancer)
            if travail.statut == ANNULE:
                raise ErreurMoteur("Annulé.")

            avancer(99, "Copie des résultats")
            travail.sorties = recuperer_sorties(projet, resultat)
            if not any(s.startswith("modele_3d") for s in travail.sorties):
                raise ErreurMoteur(
                    "Le calcul s'est terminé sans modèle 3D : les photos ne se recouvrent "
                    "probablement pas assez. Voir le journal."
                )
            travail.statut, travail.progression, travail.etape = TERMINE, 100, "Terminé"
            self._ranger_entree(entree, "_fait")
        except Exception as e:  # noqa: BLE001 - toute erreur doit être rapportée à l'utilisateur
            if travail.statut != ANNULE:
                travail.statut, travail.etape = ERREUR, "Erreur"
                travail.erreur = _message_erreur(e, self.journal(travail.id))
                if not isinstance(e, (ErreurMoteur, PasAssezDePhotos)):
                    ecrire(traceback.format_exc())
            self._ranger_entree(entree, "_erreur")
        finally:
            travail.fin = datetime.now().isoformat(timespec="seconds")
            self._enregistrer(travail)
            fichier_journal.close()
            if not self.config.garder_travail:
                shutil.rmtree(self.config.dossier_travail / travail.id, ignore_errors=True)

    def _preparer(self, id_: str, entree: Path, ecrire) -> Path:
        """Copie les photos dans le dossier de travail d'ODM (HEIC converties en JPEG)."""
        projet = self.config.dossier_travail / id_
        images = projet / "images"
        if projet.exists():
            shutil.rmtree(projet, ignore_errors=True)
        images.mkdir(parents=True)
        photos, ignores = lister_photos(entree)
        for f in ignores:
            ecrire(f"Fichier ignoré (format non pris en charge) : {f}")
        noms_utilises: set[str] = set()
        for photo in photos:
            nom = photo.name
            if photo.suffix.lower() in EXTENSIONS_HEIC:
                nom = photo.stem + ".jpg"
            # Deux sous-dossiers peuvent contenir le même nom de fichier (DJI_0001.JPG...)
            if nom.lower() in noms_utilises:
                nom = f"{photo.parent.name}_{nom}"
            noms_utilises.add(nom.lower())
            if photo.suffix.lower() in EXTENSIONS_HEIC:
                with Image.open(photo) as img:
                    exif = img.info.get("exif")
                    img.convert("RGB").save(images / nom, "JPEG", quality=95, **({"exif": exif} if exif else {}))
            else:
                shutil.copy2(photo, images / nom)
        for special in (FICHIER_GCP, FICHIER_GEO):
            if (entree / special).exists():
                shutil.copy(entree / special, projet / special)
        ecrire(f"{len(photos)} photo(s) préparée(s).")
        return projet

    def _ranger_entree(self, entree: Path, destination: str) -> None:
        if entree.exists():
            cible = self.config.dossier_entree / destination / entree.name
            shutil.rmtree(cible, ignore_errors=True)
            shutil.move(str(entree), str(cible))

    # --- Persistance ----------------------------------------------------------------

    def _enregistrer(self, travail: Travail) -> None:
        dossier = self.dossier_resultat(travail.id)
        dossier.mkdir(parents=True, exist_ok=True)
        tmp = dossier / "travail.json.tmp"
        tmp.write_text(json.dumps(travail.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(dossier / "travail.json")

    def _recharger(self) -> None:
        for fichier in sorted(self.config.dossier_resultats.glob("*/travail.json")):
            try:
                travail = Travail(**json.loads(fichier.read_text(encoding="utf-8")))
            except (ValueError, TypeError):
                continue
            if travail.statut == EN_COURS:
                # Interrompu par un arrêt de l'application : on le relance
                travail.statut, travail.progression, travail.etape = EN_ATTENTE, 0, "En attente (reprise)"
            self._travaux[travail.id] = travail
            if travail.statut == EN_ATTENTE:
                if self.dossier_photos(travail.id).exists():
                    self._file.put(travail.id)
                else:
                    travail.statut, travail.erreur = ERREUR, "Photos introuvables après redémarrage."
                self._enregistrer(travail)


def _message_erreur(e: Exception, journal: Path) -> str:
    message = str(e) or e.__class__.__name__
    try:
        contenu = journal.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return message
    indices = {
        "Not enough": "Pas assez de points communs entre les photos (recouvrement insuffisant).",
        "No reconstructions": "Les photos n'ont pas pu être assemblées : recouvrement insuffisant ou photos trop différentes.",
        "MemoryError": "Mémoire insuffisante : réduisez le nombre de photos ou augmentez la RAM allouée à Docker.",
        "Killed": "Calcul interrompu par le système (souvent un manque de mémoire).",
    }
    for cle, explication in indices.items():
        if cle in contenu:
            return f"{message} {explication}"
    return message
