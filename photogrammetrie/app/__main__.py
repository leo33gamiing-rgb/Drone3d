"""Point d'entrée : ``python -m app [options]``.

    python -m app                  interface web + surveillance du dossier a_traiter
    python -m app --sans-web       surveillance du dossier seule
    python -m app traiter DOSSIER  calcule un seul dossier puis s'arrête
"""

from __future__ import annotations

import argparse
import shutil
import socket
import sys
import threading
import webbrowser
from pathlib import Path

from .config import RACINE, charger_config
from .moteur import MoteurODM, MoteurSimulation, docker_disponible
from .surveillance import Surveillance
from .travaux import TERMINE, GestionnaireTravaux, creer_identifiant


def creer_moteur(config):
    if config.simulation:
        return MoteurSimulation(config, modele_exemple=RACINE.parent / "Matrice400-v3.glb")
    return MoteurODM(config)


def adresse_locale() -> str:
    """Adresse IP du PC sur le réseau local (aucun paquet n'est réellement envoyé)."""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        try:
            s.connect(("192.168.0.1", 80))
            return s.getsockname()[0]
        except OSError:
            return "adresse-du-pc"


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):  # accents dans la console Windows
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(prog="python -m app", description="Photos -> modèle 3D (OpenDroneMap)")
    parser.add_argument("commande", nargs="?", choices=["traiter"], help="traiter un seul dossier")
    parser.add_argument("dossier", nargs="?", type=Path, help="dossier de photos (avec 'traiter')")
    parser.add_argument("--sans-web", action="store_true", help="surveillance du dossier sans interface web")
    parser.add_argument("--port", type=int, help="port de l'interface web (8000 par défaut)")
    parser.add_argument("--donnees", type=Path, help="dossier des données (a_traiter, resultats...)")
    parser.add_argument("--reseau", action="store_true",
                        help="accessible depuis les téléphones du même Wi-Fi (envoi direct des photos)")
    parser.add_argument("--simulation", action="store_true", help="mode démonstration sans calcul réel")
    parser.add_argument("--pas-de-navigateur", action="store_true", help="ne pas ouvrir le navigateur")
    args = parser.parse_args(argv)

    config = charger_config()
    if args.port:
        config.port = args.port
    if args.donnees:
        config.dossier_donnees = args.donnees.resolve()
    if args.simulation:
        config.simulation = True
    if args.reseau:
        config.hote = "0.0.0.0"

    if not config.simulation:
        ok, message = docker_disponible()
        print(message)
        if not ok:
            print("Astuce : lancez Docker Desktop, ou essayez l'interface avec --simulation.")
            return 1

    gestionnaire = GestionnaireTravaux(config, creer_moteur(config))
    gestionnaire.demarrer()

    if args.commande == "traiter":
        if not args.dossier or not args.dossier.is_dir():
            parser.error("indiquez un dossier de photos existant")
        id_ = creer_identifiant(args.dossier.name)
        shutil.copytree(args.dossier, gestionnaire.dossier_photos(id_))
        gestionnaire.soumettre(id_, args.dossier.name, source="dossier")
        print(f"Calcul {id_} lancé. Journal : {gestionnaire.journal(id_)}")
        travail = gestionnaire.attendre_fin(id_)
        print(f"Statut : {travail.statut}")
        if travail.statut == TERMINE:
            print(f"Résultats : {gestionnaire.dossier_resultat(id_)}")
            for s in travail.sorties:
                print(f"  - {s}")
            return 0
        print(f"Erreur : {travail.erreur}")
        return 1

    Surveillance(gestionnaire).demarrer()
    print(f"Déposez vos dossiers de photos dans : {config.dossier_entree}")
    print(f"Les résultats arrivent dans        : {config.dossier_resultats}")

    if args.sans_web:
        threading.Event().wait()
        return 0

    import uvicorn

    from .serveur import creer_app

    url = f"http://localhost:{config.port}"
    print(f"Interface web : {url}")
    if config.hote != "127.0.0.1":
        print(f"Depuis un téléphone du même Wi-Fi : http://{adresse_locale()}:{config.port}")
    if not args.pas_de_navigateur:
        threading.Timer(1.5, lambda: webbrowser.open(url)).start()
    uvicorn.run(creer_app(gestionnaire), host=config.hote, port=config.port, log_level="warning")
    return 0


if __name__ == "__main__":
    sys.exit(main())
