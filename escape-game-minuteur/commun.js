'use strict';
// Code partagé entre la régie (index.html) et l'écran des joueurs (ecran.html).
// Les deux fenêtres se parlent via le stockage local du navigateur.

const MINUTE = 60000;

// Réglages par défaut : tous modifiables depuis la régie.
const DEFAUTS = {
  debut: '2026-10-19T18:00',
  fin: '2026-10-20T02:00',
  minutesPenalite: 7,
  minutesAnnonce: 58,
  texteAnnonce: 'Il vous reste {temps}.',
  texteIndice: 'UN INDICE EST DISPONIBLE',
  voix: '',
  hauteurVoix: 0.5,
  vitesseVoix: 0.85,
  volumeEffets: 1,
  volumeAmbiance: 0.5,
  screamer: 'synth:cri',
  sonIndice: 'synth:carillon',
  sonAvantAnnonce: 'synth:glas',
  ambiance: 'synth:nappe',
  enchainer: true,
};

const partieVide = () => ({ penalites: [], finie: false, journal: [] });

function charger(cle, defaut) {
  try {
    return { ...defaut, ...JSON.parse(localStorage.getItem(cle)) };
  } catch {
    return defaut;
  }
}

// Temps restant = fin de l'évènement − pénalités − heure actuelle (figé avant le début).
function calculer(reglages, partie, maintenant = Date.now()) {
  const debut = new Date(reglages.debut).getTime();
  const fin = new Date(reglages.fin).getTime() - partie.penalites.length * reglages.minutesPenalite * MINUTE;
  const commencee = maintenant >= debut;
  const reste = Math.max(0, fin - Math.max(maintenant, debut));
  const etat = !commencee ? 'attente' : reste <= 0 ? 'fini' : reste <= 10 * MINUTE ? 'critique' : 'jeu';
  return { maintenant, debut, fin, reste, commencee, etat };
}

const deuxChiffres = n => String(n).padStart(2, '0');

function hms(ms) {
  if (!Number.isFinite(ms)) return '--:--:--';
  const s = Math.ceil(ms / 1000);
  return `${deuxChiffres(Math.floor(s / 3600))}:${deuxChiffres(Math.floor((s % 3600) / 60))}:${deuxChiffres(s % 60)}`;
}
