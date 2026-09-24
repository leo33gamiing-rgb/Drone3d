# Photos → Modèle 3D

Application locale et gratuite de photogrammétrie. Vous déposez des photos
(drone, téléphone ou appareil photo) et elle produit un modèle 3D texturé,
un nuage de points et, si les photos ont un GPS, une orthophoto et un modèle
numérique de surface.

Le calcul est fait par [OpenDroneMap](https://opendronemap.org) (ODM), lancé
automatiquement dans Docker. Tout reste sur votre PC.

## Principe : plus de données = plus de précision

L'application analyse les photos et choisit seule les réglages :

| Photos | Réglage choisi | Résultat attendu |
|---|---|---|
| 3 à 9 | Esquisse rapide | Modèle partiel et approximatif, calcul en quelques minutes |
| 10 à 49 | Standard | Objet ou petite zone complète |
| 50 à 299 | Détaillé | Bâtiment, parcelle ; orthophoto et MNS si GPS |
| 300 à 799 | Grand chantier | Grande zone, nuage de points un peu allégé pour tenir en mémoire |
| 800 et plus | Très grand chantier | À réserver aux PC puissants (32 Go et plus) |

Elle regarde aussi ce qui fixe la **précision réelle** :

| Données | Précision de position |
|---|---|
| Pas de GPS (ex. téléphone sans localisation) | Forme correcte, **échelle arbitraire** |
| GPS standard | 1 à 5 m en absolu, bonnes proportions |
| Drone **RTK fixe** (détecté automatiquement sur les photos DJI) | 2 à 5 cm |
| Fichier `gcp_list.txt` (points de contrôle) | 1 à 3 cm selon vos mesures |

Un **indice de fiabilité** (0 à 100) résume tout ça dans l'interface, avec des
conseils pour l'améliorer.

## Installation (Windows)

1. Installez **Docker Desktop** : https://www.docker.com/products/docker-desktop/
   puis lancez-le une fois.
2. Donnez-lui assez de mémoire : créez le fichier `C:\Users\<vous>\.wslconfig`
   avec ce contenu, puis redémarrez Docker Desktop :
   ```
   [wsl2]
   memory=26GB
   ```
   (Sur un PC de 32 Go, 26 Go laisse de la marge à Windows.)
3. Installez **Python 3.10 ou plus** : https://www.python.org/downloads/
   (cochez « Add Python to PATH »).
4. Téléchargez le moteur une fois (environ 5 Go) dans un terminal :
   ```
   docker pull opendronemap/odm
   ```
5. Double-cliquez sur **`lancer.bat`**. La première fois, il installe ce qu'il
   faut, puis ouvre l'interface dans le navigateur (http://localhost:8000).

Sur Linux ou macOS : `./lancer.sh`.

## Utilisation

**Par l'interface web** : glissez vos photos ou un dossier entier dans la zone
de dépôt, donnez un nom, cliquez sur « Lancer le calcul ». La progression, la
précision attendue puis le modèle 3D s'affichent directement.

**Par le dossier** : copiez un dossier de photos dans `donnees/a_traiter/`.
Dès que la copie est terminée (aucun changement pendant 20 s), le calcul
démarre. Les résultats arrivent dans `donnees/resultats/<nom>_<date>/` et les
photos d'origine sont rangées dans `donnees/a_traiter/_fait/`.

**En une commande** : `lancer.bat traiter C:\chemin\vers\photos`.

**Depuis le téléphone** : lancez **`lancer_reseau.bat`** (ou `lancer.bat --reseau`).
La console affiche une adresse du type `http://192.168.1.20:8000` : ouvrez-la
sur le téléphone connecté au même Wi-Fi, puis « Choisir des photos ». Windows
peut demander d'autoriser Python dans le pare-feu (réseau privé uniquement).
Sur iPhone, dans le sélecteur de photos, touchez « Options » et activez
« Position » pour que le GPS soit envoyé avec les photos.

### Fichiers produits

| Fichier | Contenu | S'ouvre avec |
|---|---|---|
| `modele_3d.glb` | Modèle 3D texturé | Navigateur, Blender, Windows 3D Viewer |
| `modele_3d.obj` + textures | Modèle 3D texturé | Blender, logiciels de CAO |
| `nuage_points.laz` / `.ply` | Nuage de points | CloudCompare, QGIS |
| `orthophoto.tif` | Vue du dessus géoréférencée (si GPS) | QGIS |
| `mns.tif` | Altitudes (si GPS) | QGIS |
| `rapport_qualite.pdf` | Rapport d'OpenDroneMap (10 photos et plus) | Lecteur PDF |
| `journal.log` | Détail du calcul | Éditeur de texte |

## Bien prendre les photos

- **Recouvrement** : chaque zone doit apparaître sur au moins 3 photos. Visez
  70 à 80 % de recouvrement entre deux photos voisines.
- **Objet ou bâtiment** : tournez autour en prenant une photo tous les 15 à 20°,
  puis refaites un tour plus haut ou plus bas.
- **Zone au drone** : mission de cartographie dans DJI Pilot 2 (80 % / 70 %), et
  ajoutez des photos obliques (caméra à 45°) pour les façades.
- **Éviter** : flou, surfaces uniformes (murs blancs, eau, vitres), objets qui
  bougent, fortes différences de lumière entre les photos.
- **Téléphone** : activez la localisation de l'appareil photo pour obtenir un
  modèle à l'échelle.
- **Matrice 4T** : sa caméra n'a pas d'obturateur mécanique ; volez lentement.
  La correction « rolling shutter » est activée automatiquement (ODM utilise
  une durée de lecture par défaut si le capteur n'est pas dans sa base).

### Points de contrôle (`gcp_list.txt`)

Pour une précision centimétrique sans RTK, placez des cibles au sol, mesurez-les
au GPS de précision et décrivez-les dans un fichier `gcp_list.txt` déposé avec
les photos ([format ODM](https://docs.opendronemap.org/gcp/)).

## Réglages

Copiez `config.exemple.json` en `config.json` pour modifier :

- `gpu` : `true` avec une carte NVIDIA, et `image_odm` à `"opendronemap/odm:gpu"` ;
- `dossier_donnees` : emplacement des dossiers de photos et des résultats ;
- `options_supplementaires` : options ODM ajoutées à toutes les tâches ;
- `garder_travail` : garder les fichiers intermédiaires (pour déboguer).

`python -m app --simulation` lance l'interface sans calcul réel, pour l'essayer
sans Docker.

## Développement

```
pip install -r requirements-dev.txt
python -m pytest
```

Structure : `app/analyse.py` (lecture EXIF/GPS/RTK), `app/profils.py` (choix des
réglages), `app/moteur.py` (lancement d'ODM), `app/travaux.py` (file de calculs),
`app/surveillance.py` (dossier surveillé), `app/serveur.py` + `app/web/`
(interface).

OpenDroneMap est distribué sous licence AGPL : si vous proposez cette
application en ligne à d'autres personnes, vous devez publier son code source.
