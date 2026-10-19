# Escape Game — Minuteur et régie sonore

Une petite application qui tourne en local sur le PC, sans installation :

- **Écran des joueurs** : fond noir, minuteur rouge (8 h au départ par défaut).
- **Régie** (ton poste) : minuteur, pénalités, indices, annonces, micro à voix déformée, bande continue et plus de 150 sons d'horreur.

## La régie en un coup d'œil

Tout tient sur un seul écran ; seules les longues listes défilent dans leur cadre.

| À gauche | Au centre | À droite |
| --- | --- | --- |
| Minuteur, **Pénalité**, indice, annonce, **micro** | **Bibliothèque** en onglets : Screamers, Indice, Rires, Chuchotements, Portes, Bruitages, Récits | **Volumes généraux**, **bande continue**, **sons en cours** |

En haut : **Écran des joueurs** (à glisser sur la télé, double-clic pour le plein écran) et **Réglages et journal** (durée, pénalité, annonces, voix, micro, réinitialisation, historique).

## Installation (Windows, une seule fois)

1. Copie le dossier `escape-game-minuteur` sur le PC (par exemple dans `Documents`).
2. Double-clique sur **`INSTALLER-ICONE.bat`**.
   Si Windows affiche « Windows a protégé votre ordinateur », clique sur *Informations complémentaires* puis *Exécuter quand même*.
3. L'icône **« Escape Game - Minuteur »** apparaît sur le bureau. C'est elle qu'il faut utiliser pour lancer la régie.

**Mettre à jour** : ferme la régie, puis double-clique sur **`METTRE-A-JOUR.bat`**. La dernière version est téléchargée et remplace les fichiers. Tes réglages et tes sons importés sont conservés.

> Si tu déplaces le dossier, relance `INSTALLER-ICONE.bat`. `LANCER.bat` lance aussi la régie, sans passer par l'icône.

## Avant la soirée

1. **Barre de son Bluetooth** : appaire-la dans *Paramètres Windows → Bluetooth et appareils*, puis choisis-la comme sortie dans *Paramètres → Son*.
2. **Veille** : dans *Paramètres → Système → Alimentation*, mets l'écran et la mise en veille sur **Jamais**.
3. **Notifications** : active *Ne pas déranger*.
4. **Voix des annonces** : dans *Réglages et journal → Voix des annonces*, choisis une voix française « Online (Natural) » (Denise, Eloise, Vivienne, Henri…). Ce sont les plus naturelles, mais elles demandent Internet (le partage de connexion d'un téléphone suffit). Teste avec *Annoncer le temps restant maintenant*.

## Le minuteur

- **Démarrer le minuteur** quand tu veux. Le même bouton sert à mettre en pause et à reprendre.
- **−10 / −5 / −1 / +1 / +5 / +10 min** pour corriger le temps.
- **Temps restant : … h … min → Régler** pour le fixer exactement.
- **Ou finir à : 02:00 → Régler** : le minuteur se cale pour tomber à zéro à cette heure-là.
- **Réinitialiser** (dans *Réglages et journal*) : retour à la durée de départ, sans pénalités.
- Au premier démarrage : annonce vocale et lancement de la bande continue (option à décocher).
- **Annonce toutes les 58 min de jeu** : un glas sonne, puis la voix dit le temps restant. Les pauses ne comptent pas.
- À zéro : le minuteur clignote, « LE TEMPS EST ÉCOULÉ » s'affiche, un screamer part. Ajouter du temps relance le minuteur.

## Actions

| Bouton | Effet |
| --- | --- |
| **Pénalité −7 min** | Retire 7 min, joue un screamer (au hasard par défaut) et fait flasher l'écran. |
| Annuler la dernière | Rend les minutes de la dernière pénalité. |
| **Indice disponible** | Joue le son d'indice et affiche « UN INDICE EST DISPONIBLE » pendant 30 s. |
| Annoncer le temps | Fait l'annonce vocale tout de suite. |
| Tout couper (*Sons en cours*) | Arrête net screamers, voix, récits, micro et bande continue. |

## Micro : parler avec une voix déformée

Carte **Micro — voix déformée** : clique sur **Activer le micro** une fois au début de la soirée, puis :

- **maintiens le bouton violet** (ou **la barre Espace**) pour parler, relâche pour couper ;
- ou coche **Rester en direct** : un clic allume, un clic coupe ;
- choisis l'effet : **Démon** (très grave), **Monstre** (grave et grondant), **Possédé** (métallique), **Fantôme** (écho lointain), **Voix d'outre-tombe**, ou voix normale ;
- la jauge montre que le micro t'entend ; la bande continue baisse automatiquement pendant que tu parles ; « Micro en direct » apparaît dans *Sons en cours* ; le choix du micro est dans *Réglages et journal*.

Ta voix sort par la barre de son, avec un petit retard (normal en Bluetooth). Pour éviter le **larsen** (sifflement), prends un casque-micro ou éloigne le micro de la barre de son et baisse le volume de la voix si besoin. Après cette mise à jour, relance une fois **`INSTALLER-ICONE.bat`** : l'icône autorisera alors le micro sans poser la question à chaque lancement.

## Les volumes

- **Chaque son a son propre curseur**, dans la bibliothèque, dans la bande continue et dans *Sons en cours* (les trois restent synchronisés et sont mémorisés).
- **Volumes généraux** (à droite) : **Bande continue**, **Screamers** et **Autres sons** (indices, rires, bruitages, récits). Volume entendu = volume général × volume du son ; ça s'applique aussi aux sons déjà en train de jouer.

## Sons en cours

Le cadre **Sons en cours** (en bas à droite) liste tout ce qui joue : screamers, bruitages, récit, annonce vocale, micro, ambiances et horloges, avec le temps écoulé et un curseur de volume. **■ Arrêter** coupe un son lancé par erreur ; **Tout couper** arrête tout.

## La bande continue

Plusieurs **ambiances** (nappe sombre, vent, cave, chœur fantôme, asile, berceuse, orage, cœur lent, robinet), **horloges** (grande horloge lourde, pendule, montre à gousset, horloge fantôme, mécanisme, tic-tac et cœur) et **énigmes** peuvent tourner **en même temps** : un clic lance ou arrête chacune (■ = en cours), avec son propre volume. Le mélange est mémorisé : **Lancer** le relance d'un clic. Il garde aussi la barre de son éveillée (beaucoup s'éteignent après 15 à 20 min de silence).

## L'énigme en morse

Dans *Bande continue → Énigmes*, **« Code morse au violon : A B E F U »** tourne en boucle comme les ambiances (▶ / ■ et son volume) :

- **son court = point**, **son long = trait** : un vrai violon joue sa note la plus grave (sol) en coups d'archet courts ou longs ; le trait dure 3 fois le point (0,3 s contre 0,9 s) ;
- 0,3 s de silence entre les signes, 1,5 s entre les lettres, puis **6 s de pause** avant que le message recommence ;
- un grondement sourd et une nappe sombre tournent en continu, sans aucun rythme pour ne pas brouiller le message.

| Lettre | Morse |
| --- | --- |
| A | · — |
| B | — · · · |
| E | · |
| F | · · — · |
| U | · · — |

Vrais sons libres de droit (CC0) : violon de VSCO 2 Community Edition (Versilian Studios), sources dans `sons/enigmes/CREDITS.txt`. Version de 5 minutes à télécharger : `recits/morse-abefu.mp3`. Pour un autre mot : `python3 outils/fabrique/fabriquer_morse.py <collection CC0> <VSCO-2-CE> MOT`.

## La bibliothèque de sons

Trois sortes de sons, chaque onglet a un bouton **Au hasard** :

- **⚡ 12 jump scares** en tête des screamers, composés comme au cinéma avec de vrais instruments d'orchestre et de vrais cris : piano fracassé, violons de *Psychose*, trémolo qui monte puis cri, coup d'orchestre avec cuivres, timbales et gong, démon, chœur des damnés, orgue maudit, timbales de l'enfer… Instruments de VSCO 2 Community Edition (CC0), crédits dans `sons/reels/jumpscares/CREDITS.txt`.
- **★ Vrais enregistrements**, libres de droit (CC0, domaine public), en tête de liste : 24 screamers (cris de femme et d'homme, hurlements, cris d'agonie, monstres, rugissements, verre brisé, violoncelle…), 5 portes et grincements, 12 bruitages (souffles, couteaux, eau, verre, robinet…) et un robinet en boucle. Sources dans `sons/CREDITS-CC0.txt`.
- **Sons fabriqués par l'ordinateur** (synthèse) : 12 screamers, 5 indices, 8 rires, 10 chuchotements, 8 portes, 12 bruitages, 8 ambiances et 6 horloges.

Par défaut, chaque pénalité joue **un jump scare au hasard**, jamais deux fois le même de suite. Dans la liste des screamers, tu peux aussi choisir « au hasard parmi les vrais cris », « au hasard parmi tous » ou un son précis.

Pour ajouter tes propres sons : **+ Ajouter des sons** (sites gratuits : freesound.org, pixabay.com/sound-effects, lasonotheque.org).

**Récits et voix** : contient le **récit de la policière** (3 min 50), enregistré avec une voix féminine de synthèse neuronale, de vrais cris et souffles, et les bruits d'eau, de robinet et de téléphone. Il est aussi téléchargeable seul : `recits/recit-policiere.mp3`. Tu peux importer tes propres enregistrements ; *Tout lire* les enchaîne dans l'ordre.

## Bon à savoir

- Les réglages, la partie en cours et les sons importés sont enregistrés : fermer et rouvrir l'app ne perd rien.
- Sur Mac ou Linux : ouvre `index.html` dans Chrome, et clique une fois dans la régie pour autoriser le son.
- Les sons fournis se refabriquent avec `outils/fabrique/fabriquer_sons.py` (Python, pour les curieux).
