# Escape Game — Minuteur et régie sonore

Une petite application qui tourne en local sur le PC, sans Internet et sans installation :

- **Écran des joueurs** : fond noir, minuteur rouge qui décompte jusqu'à la fin de l'évènement (par défaut **lundi 19 octobre 2026, 18 h → mardi 20 octobre, 2 h**).
- **Régie** (ton poste) : pénalités, indices, annonces, ambiance et bibliothèque de sons.
- **Pénalité** : retire 7 min, lance le screamer choisi par défaut et fait flasher l'écran en rouge.
- **Annonce vocale toutes les 58 min** : un glas sonne, puis une voix grave dit le temps restant.
- **Indice disponible** : joue le son « indice » et affiche un message sur l'écran des joueurs.
- **Ambiance** : musique en boucle (ou plusieurs musiques enchaînées), baissée automatiquement pendant les annonces et les screamers.

## Installation (Windows, une seule fois)

1. Copie le dossier `escape-game-minuteur` sur le PC (par exemple dans `Documents`).
2. Double-clique sur **`INSTALLER-ICONE.bat`**.
   Si Windows affiche « Windows a protégé votre ordinateur », clique sur *Informations complémentaires* puis *Exécuter quand même*.
3. L'icône **« Escape Game - Minuteur »** apparaît sur le bureau. C'est elle qu'il faut utiliser pour lancer la régie.

> Si tu déplaces le dossier, relance `INSTALLER-ICONE.bat`.
> `LANCER.bat` lance aussi la régie, sans passer par l'icône.

L'icône ouvre la régie dans une fenêtre Edge (ou Chrome) dédiée, réglée pour que le son marche sans clic et que le minuteur ne ralentisse jamais, même fenêtre réduite.

## Avant la soirée

1. **Barre de son Bluetooth** : appaire-la dans *Paramètres Windows → Bluetooth et appareils*, puis choisis-la comme sortie dans *Paramètres → Son*. Tout le son de l'app (screamers, voix, ambiance) passera par elle.
2. **Veille** : dans *Paramètres → Système → Alimentation*, mets l'écran et la mise en veille sur **Jamais**.
3. **Notifications** : active *Ne pas déranger* pour qu'aucun bruit Windows ne sorte dans la barre de son.
4. **Sons** : dans la régie, *Bibliothèque de sons → + Ajouter des sons* pour chaque catégorie. Coche le rond du son à utiliser par défaut (screamer de pénalité, son d'indice, musique d'ambiance).
   Les sons sont gardés dans l'app : pas besoin de les réimporter. Garde quand même les fichiers d'origine.
5. **Horaires** : vérifie *Début* et *Fin* dans *Réglages*.
6. **Test** : clique sur *Annoncer le temps restant maintenant* pour régler la voix (liste *Voix*, curseurs grave/aigu et vitesse).

## Pendant la partie

1. Lance l'icône, puis clique sur **Ouvrir l'écran des joueurs**.
2. Glisse cette fenêtre sur la télé ou le projecteur, puis **double-clique dedans** pour le plein écran.
3. Lance l'ambiance. Elle garde aussi la barre de son éveillée : beaucoup s'éteignent seules après 15 à 20 min de silence.
4. Le minuteur démarre tout seul à l'heure de début, avec une annonce. Pour commencer plus tôt : *Réglages → Démarrer la partie maintenant*.

| Bouton | Effet |
| --- | --- |
| **Pénalité −7 min** | Retire 7 min, joue le screamer coché et fait flasher l'écran. |
| Annuler la dernière | Rend les 7 min (en cas d'erreur). |
| **Indice disponible** | Joue le son d'indice et affiche « UN INDICE EST DISPONIBLE » pendant 30 s. |
| Annoncer le temps restant | Fait l'annonce vocale tout de suite. |
| Couper tous les sons | Arrête net screamers, voix et ambiance. |
| ▶ à côté d'un son | Le joue dans la pièce. Pour une musique d'ambiance : la lance comme ambiance. |

Les 10 dernières minutes, le minuteur bat comme un cœur. À zéro, il clignote, « LE TEMPS EST ÉCOULÉ » s'affiche, le screamer part et la voix l'annonce.

## Bon à savoir

- Les réglages, pénalités et sons sont enregistrés : fermer et rouvrir l'app ne perd rien. *Réinitialiser la partie* efface les pénalités et le journal.
- Les sons « (généré) » sont créés par l'ordinateur, en secours, tant que tu n'as pas importé de vrais sons. Le premier vrai son importé dans une catégorie devient automatiquement son son par défaut.
- Sur Mac ou Linux : ouvre `index.html` dans Chrome, et clique une fois dans la régie pour autoriser le son.
