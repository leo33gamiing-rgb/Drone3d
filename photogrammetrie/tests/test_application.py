import time

from fastapi.testclient import TestClient

from app.moteur import MoteurSimulation
from app.serveur import creer_app
from app.surveillance import Surveillance
from app.travaux import TERMINE, GestionnaireTravaux

from .conftest import creer_photo


def gestionnaire_simule(config, tmp_path):
    modele = tmp_path / "exemple.glb"
    modele.write_bytes(b"glTF-factice")
    g = GestionnaireTravaux(config, MoteurSimulation(config, modele_exemple=modele, pause=0))
    g.demarrer()
    return g


def attendre(client, id_, delai=10):
    fin = time.time() + delai
    while time.time() < fin:
        t = client.get(f"/api/travaux/{id_}").json()
        if t["statut"] not in ("en_attente", "en_cours"):
            return t
        time.sleep(0.1)
    raise AssertionError("délai dépassé")


def test_envoi_web_jusqu_au_modele(config, tmp_path):
    client = TestClient(creer_app(gestionnaire_simule(config, tmp_path)))
    photos = [creer_photo(tmp_path / f"p{i}.jpg", "Apple", "iPhone 15") for i in range(4)]
    fichiers = [("fichiers", (p.name, p.read_bytes(), "image/jpeg")) for p in photos]
    fichiers.append(("fichiers", ("../../evil.jpg", photos[0].read_bytes(), "image/jpeg")))
    fichiers.append(("fichiers", ("virus.exe", b"x", "application/octet-stream")))

    r = client.post("/api/travaux", data={"nom": "Façade église"}, files=fichiers)
    assert r.status_code == 200, r.text
    travail = attendre(client, r.json()["id"])

    assert travail["statut"] == TERMINE, travail
    assert travail["analyse"]["nb_photos"] == 5  # evil.jpg ramené dans le dossier, .exe ignoré
    assert travail["analyse"]["source"] == "telephone"
    assert travail["profil"]["code"] == "esquisse"
    assert "modele_3d.glb" in travail["sorties"]
    assert not (config.dossier_donnees.parent / "evil.jpg").exists()

    glb = client.get(f"/resultats/{travail['id']}/modele_3d.glb")
    assert glb.status_code == 200 and glb.content == b"glTF-factice"
    assert client.get(f"/resultats/{travail['id']}/..%2Ftravail.json").status_code == 404
    assert "Profil choisi" in client.get(f"/api/travaux/{travail['id']}/journal").text
    # Les photos d'origine sont rangées dans _fait
    assert (config.dossier_entree / "_fait" / travail["id"]).is_dir()


def test_trop_peu_de_photos_donne_une_erreur_claire(config, tmp_path):
    client = TestClient(creer_app(gestionnaire_simule(config, tmp_path)))
    p = creer_photo(tmp_path / "seule.jpg")
    r = client.post("/api/travaux", files=[("fichiers", ("seule.jpg", p.read_bytes(), "image/jpeg"))])
    travail = attendre(client, r.json()["id"])
    assert travail["statut"] == "erreur"
    assert "au moins 3 photos" in travail["erreur"]


def test_aucune_photo_refusee(config, tmp_path):
    client = TestClient(creer_app(gestionnaire_simule(config, tmp_path)))
    r = client.post("/api/travaux", files=[("fichiers", ("a.txt", b"x", "text/plain"))])
    assert r.status_code == 400


def test_surveillance_attend_que_le_dossier_soit_stable(config, tmp_path):
    g = gestionnaire_simule(config, tmp_path)
    s = Surveillance(g, journal=lambda *_: None)
    dossier = config.dossier_entree / "Chantier A"
    for i in range(3):
        creer_photo(dossier / f"DJI_{i}.JPG", "DJI", "M4T", gps=True)

    assert s.verifier(maintenant=0) == []  # première vue
    creer_photo(dossier / "DJI_9.JPG", "DJI", "M4T", gps=True)
    assert s.verifier(maintenant=5) == []  # encore en train de changer
    assert s.verifier(maintenant=10) == []  # stable depuis 5 s seulement
    crees = s.verifier(maintenant=16)
    assert len(crees) == 1 and not dossier.exists()

    travail = g.attendre_fin(crees[0], intervalle=0.05)
    assert travail.statut == TERMINE and travail.nom == "Chantier A"
    assert travail.analyse["georeferencee"] is True


def test_reprise_apres_redemarrage(config, tmp_path):
    g = GestionnaireTravaux(config, MoteurSimulation(config, pause=0))  # sans démarrer le traitement
    for i in range(3):
        creer_photo(g.dossier_photos("x_1") / f"{i}.jpg")
    g.soumettre("x_1", "x", "web")

    g2 = gestionnaire_simule(config, tmp_path)
    assert g2.obtenir("x_1").statut == "en_attente"
    assert g2.attendre_fin("x_1", intervalle=0.05).statut == TERMINE


def test_archive_zip_des_resultats(config, tmp_path):
    import io
    import zipfile

    client = TestClient(creer_app(gestionnaire_simule(config, tmp_path)))
    photos = [creer_photo(tmp_path / f"p{i}.jpg") for i in range(3)]
    r = client.post("/api/travaux", files=[("fichiers", (p.name, p.read_bytes(), "image/jpeg")) for p in photos])
    travail = attendre(client, r.json()["id"])
    assert travail["simulation"] is True

    z = client.get(f"/resultats/{travail['id']}.zip")
    assert z.status_code == 200
    noms = zipfile.ZipFile(io.BytesIO(z.content)).namelist()
    assert "modele_3d.glb" in noms and "journal.log" in noms


def test_photos_heic_de_telephone_converties_avec_gps(config, tmp_path):
    from PIL import Image

    client = TestClient(creer_app(gestionnaire_simule(config, tmp_path)))
    fichiers = []
    for i in range(3):
        jpg = creer_photo(tmp_path / f"IMG_{i}.jpg", "Apple", "iPhone 15", gps=True)
        heic = tmp_path / f"IMG_{i}.HEIC"
        with Image.open(jpg) as im:
            im.save(heic, exif=im.getexif().tobytes())
        fichiers.append(("fichiers", (heic.name, heic.read_bytes(), "image/heic")))

    travail = attendre(client, client.post("/api/travaux", files=fichiers).json()["id"])
    assert travail["statut"] == TERMINE, travail
    assert travail["analyse"]["nb_photos"] == 3
    assert travail["analyse"]["nb_gps"] == 3  # EXIF conservé lors de la conversion en JPEG
    assert travail["analyse"]["source"] == "telephone"
