import pytest

from app.analyse import Analyse, InfoPhoto, analyser_dossier
from app.profils import PasAssezDePhotos, choisir_profil

from .conftest import creer_photo


def lot(nb, **kwargs):
    defaut = {"marque": "DJI", "modele": "M4T", "gps": True, "type_appareil": "drone"}
    defaut.update(kwargs)
    return Analyse(photos=[InfoPhoto(nom=f"{i}.jpg", **defaut) for i in range(nb)])


def test_lit_gps_rtk_et_type_appareil(tmp_path):
    creer_photo(tmp_path / "drone.jpg", "DJI", "M4T", gps=True, rtk_flag=50)
    creer_photo(tmp_path / "tel.jpg", "Apple", "iPhone 15", gps=False)
    creer_photo(tmp_path / "sous" / "cam.jpg", "Canon", "EOS R6", gps=True)
    (tmp_path / "notes.docx").write_text("x")
    (tmp_path / "gcp_list.txt").write_text("EPSG:4326\n")

    a = analyser_dossier(tmp_path)
    infos = {p.nom: p for p in a.photos}

    assert a.nb_photos == 3
    assert infos["drone.jpg"].gps and infos["drone.jpg"].rtk == "fixe"
    assert infos["drone.jpg"].rtk_precision_m == 0.031
    assert infos["drone.jpg"].type_appareil == "drone"
    assert infos["tel.jpg"].type_appareil == "telephone" and not infos["tel.jpg"].gps
    assert infos["cam.jpg"].type_appareil == "inconnu"
    assert a.source == "mixte"
    assert a.gcp is True
    assert a.fichiers_ignores == ["notes.docx"]


def test_fichier_corrompu_ignore(tmp_path):
    (tmp_path / "casse.jpg").write_bytes(b"pas une image")
    creer_photo(tmp_path / "ok.jpg")
    a = analyser_dossier(tmp_path)
    assert a.nb_photos == 1 and a.nb_illisibles == 1


@pytest.mark.parametrize(
    "nb, code",
    [(3, "esquisse"), (9, "esquisse"), (10, "standard"), (50, "detaille"), (300, "grand"), (800, "tres_grand")],
)
def test_profil_selon_nombre_de_photos(nb, code):
    assert choisir_profil(lot(nb)).code == code


def test_moins_de_trois_photos_refuse():
    with pytest.raises(PasAssezDePhotos):
        choisir_profil(lot(2))


def test_sans_gps_pas_d_orthophoto_ni_mns():
    p = choisir_profil(lot(60, gps=False))
    assert "--skip-orthophoto" in p.options and "--dsm" not in p.options
    assert "arbitraires" in p.precision


def test_gcp_et_geo_passes_a_odm():
    a = lot(20)
    a.gcp = a.geo_txt = True
    opts = choisir_profil(a).options
    assert opts[opts.index("--gcp") + 1] == "{projet}/gcp_list.txt"
    assert opts[opts.index("--geo") + 1] == "{projet}/geo.txt"


def test_fiabilite_augmente_avec_photos_et_rtk():
    peu = choisir_profil(lot(5, gps=False)).fiabilite
    gps = choisir_profil(lot(5)).fiabilite
    beaucoup = choisir_profil(lot(200)).fiabilite
    rtk = choisir_profil(lot(200, rtk="fixe", rtk_precision_m=0.02)).fiabilite
    assert peu < gps < beaucoup < rtk <= 100


def test_rolling_shutter_uniquement_pour_dji_sans_obturateur_mecanique():
    assert "--rolling-shutter" in choisir_profil(lot(20)).options
    assert "--rolling-shutter" not in choisir_profil(lot(20, modele="FC6310")).options
    assert "--rolling-shutter" not in choisir_profil(lot(20, marque="Apple", type_appareil="telephone")).options


def test_toujours_un_modele_glb():
    assert "--gltf" in choisir_profil(lot(3)).options
