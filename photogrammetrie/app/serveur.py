"""Interface web locale : dépôt des photos, suivi des calculs, visualisation 3D."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path, PurePath

from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

from .analyse import EXTENSIONS_HEIC, EXTENSIONS_PHOTOS, FICHIER_GCP, FICHIER_GEO
from .moteur import docker_disponible
from .travaux import GestionnaireTravaux, creer_identifiant

WEB = Path(__file__).parent / "web"
TAILLE_BLOC = 1024 * 1024


def creer_app(gestionnaire: GestionnaireTravaux) -> FastAPI:
    app = FastAPI(title="Photogrammétrie")
    config = gestionnaire.config

    def travail_ou_404(id_: str):
        travail = gestionnaire.obtenir(id_)
        if not travail:
            raise HTTPException(404, "Calcul introuvable")
        return travail

    @app.get("/api/etat")
    def etat():
        if config.simulation:
            docker = (True, "Mode simulation : aucun calcul réel.")
        else:
            docker = docker_disponible()
        return {
            "simulation": config.simulation,
            "docker_ok": docker[0],
            "docker_message": docker[1],
            "dossier_entree": str(config.dossier_entree),
            "dossier_resultats": str(config.dossier_resultats),
        }

    @app.get("/api/travaux")
    def lister():
        return [t.to_dict() for t in gestionnaire.lister()]

    @app.get("/api/travaux/{id_}")
    def detail(id_: str):
        return travail_ou_404(id_).to_dict()

    @app.get("/api/travaux/{id_}/journal", response_class=PlainTextResponse)
    def journal(id_: str, lignes: int = 200):
        travail_ou_404(id_)
        chemin = gestionnaire.journal(id_)
        if not chemin.exists():
            return ""
        contenu = chemin.read_text(encoding="utf-8", errors="replace").splitlines()
        return "\n".join(contenu[-lignes:])

    @app.post("/api/travaux")
    async def creer(nom: str = Form(""), fichiers: list[UploadFile] = File(...)):
        nom = nom.strip() or "Projet"
        id_ = creer_identifiant(nom)
        dossier = gestionnaire.dossier_photos(id_)
        dossier.mkdir(parents=True)
        acceptes = 0
        for fichier in fichiers:
            # Nom seul : on ignore tout chemin envoyé par le navigateur (sécurité)
            nom_fichier = PurePath((fichier.filename or "").replace("\\", "/")).name
            ext = Path(nom_fichier).suffix.lower()
            if not nom_fichier or not (
                ext in EXTENSIONS_PHOTOS or ext in EXTENSIONS_HEIC or nom_fichier in (FICHIER_GCP, FICHIER_GEO)
            ):
                continue
            cible = dossier / nom_fichier
            n = 1
            while cible.exists():
                cible = dossier / f"{Path(nom_fichier).stem}_{n}{ext}"
                n += 1
            with open(cible, "wb") as sortie:
                while bloc := await fichier.read(TAILLE_BLOC):
                    sortie.write(bloc)
            acceptes += 1
        if acceptes == 0:
            dossier.rmdir()
            raise HTTPException(400, "Aucune photo reconnue (formats : JPG, PNG, TIFF, HEIC).")
        return gestionnaire.soumettre(id_, nom, source="web").to_dict()

    @app.post("/api/travaux/{id_}/annuler")
    def annuler(id_: str):
        travail_ou_404(id_)
        if not gestionnaire.annuler(id_):
            raise HTTPException(409, "Ce calcul n'est plus en cours.")
        return {"ok": True}

    @app.delete("/api/travaux/{id_}")
    def supprimer(id_: str):
        travail_ou_404(id_)
        if not gestionnaire.supprimer(id_):
            raise HTTPException(409, "Impossible de supprimer un calcul en cours : annulez-le d'abord.")
        return {"ok": True}

    @app.get("/resultats/{id_}.zip")
    def archive(id_: str, taches: BackgroundTasks):
        travail = travail_ou_404(id_)
        temporaire = Path(tempfile.mkdtemp())
        chemin = shutil.make_archive(str(temporaire / id_), "zip", gestionnaire.dossier_resultat(id_))
        taches.add_task(shutil.rmtree, temporaire, ignore_errors=True)
        return FileResponse(chemin, filename=f"{travail.nom}.zip")

    @app.get("/resultats/{id_}/{fichier}")
    def telecharger(id_: str, fichier: str):
        travail_ou_404(id_)
        dossier = gestionnaire.dossier_resultat(id_).resolve()
        chemin = (dossier / fichier).resolve()
        if chemin.parent != dossier or not chemin.is_file():
            raise HTTPException(404, "Fichier introuvable")
        return FileResponse(chemin)

    @app.get("/")
    def accueil():
        return FileResponse(WEB / "index.html")

    app.mount("/static", StaticFiles(directory=WEB), name="static")
    return app
