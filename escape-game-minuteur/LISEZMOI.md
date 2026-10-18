# Escape Game — Minuteur et régie sonore

Une petite application qui tourne en local sur le PC, sans installation :

- **Écran des joueurs** : fond noir, minuteur rouge (8 h au départ par défaut).
- **Régie** (ton poste) : minuteur, pénalités, indices, annonces, fond sonore et 69 sons d'horreur fournis.

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
4. **Voix des annonces** : dans *Réglages → Voix des annonces*, choisis une voix française « Online (Natural) » (Denise, Eloise, Vivienne, Henri…). Ce sont les plus naturelles, mais elles demandent Internet (le partage de connexion d'un téléphone suffit). Teste avec *Annoncer le temps restant maintenant*.

## Le minuteur

- **Démarrer le minuteur** quand tu veux. Le même bouton sert à mettre en pause et à reprendre.
- **−10 / −5 / −1 / +1 / +5 / +10 min** pour corriger le temps.
- **Temps restant : … h … min → Régler** pour le fixer exactement.
- **Ou finir à : 02:00 → Régler** : le minuteur se cale pour tomber à zéro à cette heure-là.
- **Réinitialiser** : retour à la durée de départ, sans pénalités.
- Au premier démarrage : annonce vocale et lancement du fond sonore (option à décocher).
- **Annonce toutes les 58 min de jeu** : un glas sonne, puis la voix dit le temps restant. Les pauses ne comptent pas.
- À zéro : le minuteur clignote, « LE TEMPS EST ÉCOULÉ » s'affiche, un screamer part. Ajouter du temps relance le minuteur.

## Actions

| Bouton | Effet |
| --- | --- |
| **Pénalité −7 min** | Retire 7 min, joue un screamer (au hasard par défaut) et fait flasher l'écran. |
| Annuler la dernière | Rend les minutes de la dernière pénalité. |
| **Indice disponible** | Joue le son d'indice et affiche « UN INDICE EST DISPONIBLE » pendant 30 s. |
| Annoncer le temps restant | Fait l'annonce vocale tout de suite. |
| Couper tous les sons | Arrête net screamers, voix, récits et fond sonore. |

## Le fond sonore

Plusieurs **ambiances** (nappe sombre, vent, cave, chœur fantôme, asile, berceuse, orage, cœur lent) et **horloges** (grande horloge lourde, pendule, montre à gousset, horloge fantôme, mécanisme, tic-tac et cœur) peuvent tourner **en même temps**. Chacune a ▶ / ■ et son propre volume. Le mélange est mémorisé : *Lancer le fond sonore* le relance d'un clic. Il garde aussi la barre de son éveillée (beaucoup s'éteignent après 15 à 20 min de silence).

## La bibliothèque de sons

Screamers (12), indices (5), rires (8), chuchotements (10), portes et coups (8), autres bruitages (12, dont téléphone, robinet, chaise et bruit sous l'eau). Chaque catégorie a un bouton **Au hasard**.

Ces sons sont **fabriqués par l'ordinateur** (synthèse), sans enregistrement. Les horloges, portes, ambiances et bruitages rendent bien. Les rires, cris et chuchotements restent synthétiques : pour du vraiment réaliste, importe de vrais enregistrements avec **+ Ajouter des sons** (sites gratuits : freesound.org, pixabay.com/sound-effects, lasonotheque.org).

**Récits et voix** : importe tes enregistrements (par exemple le récit de la policière, voir `recits/RECIT-POLICIERE.txt`). *Tout lire* les enchaîne dans l'ordre.

## Bon à savoir

- Les réglages, la partie en cours et les sons importés sont enregistrés : fermer et rouvrir l'app ne perd rien.
- Sur Mac ou Linux : ouvre `index.html` dans Chrome, et clique une fois dans la régie pour autoriser le son.
- Les sons fournis se refabriquent avec `outils/fabrique/fabriquer_sons.py` (Python, pour les curieux).
