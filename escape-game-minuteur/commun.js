'use strict';
// Code partagé entre la régie (index.html) et l'écran des joueurs (ecran.html).
// Les deux fenêtres se parlent via le stockage local du navigateur.

const MINUTE = 60000;
const CLE_REGLAGES = 'egm2.reglages';
const CLE_PARTIE = 'egm2.partie';
const CLE_EFFET = 'egm.effet';

// Réglages par défaut : tous modifiables depuis la régie.
const DEFAUTS = {
  dureeDepart: '08:00',
  minutesPenalite: 7,
  minutesAnnonce: 58,
  texteAnnonce: 'Il vous reste {temps}.',
  texteIndice: 'UN INDICE EST DISPONIBLE',
  voix: '',
  hauteurVoix: 0.8,
  vitesseVoix: 0.9,
  volumeEffets: 1,
  volumeFond: 0.7,
  screamer: 'hasard-reels',
  sonIndice: 'pack:sons/indice/boite-a-musique.ogg',
  sonAvantAnnonce: 'pack:sons/bruitages/glas.ogg',
  fond: ['pack:sons/ambiances/nappe-sombre.ogg', 'pack:sons/horloges/horloge-lourde.ogg'],
  volumesCouches: {},
  fondAuDemarrage: true,
};

const dureeEnMs = texte => {
  const [h, m] = String(texte).split(':').map(Number);
  return ((h || 0) * 60 + (m || 0)) * MINUTE;
};

const partieVide = reglages => ({
  lance: false, // le minuteur a déjà été démarré une fois
  enMarche: false,
  finPrevue: 0, // heure de fin (ms) pendant que le minuteur tourne
  resteFige: dureeEnMs(reglages.dureeDepart), // temps restant (ms) quand il est arrêté
  jeuAccumule: 0, // temps de jeu écoulé avant la dernière reprise
  repriseA: 0,
  penalites: [], // [{ t, minutes }]
  finie: false,
  journal: [],
});

function charger(cle, defaut) {
  try {
    return { ...defaut, ...JSON.parse(localStorage.getItem(cle)) };
  } catch {
    return defaut;
  }
}

function calculer(partie, maintenant = Date.now()) {
  const reste = partie.enMarche ? Math.max(0, partie.finPrevue - maintenant) : Math.max(0, partie.resteFige);
  const jeu = partie.jeuAccumule + (partie.enMarche ? maintenant - partie.repriseA : 0);
  const etat = !partie.lance ? 'attente'
    : reste <= 0 ? 'fini'
      : !partie.enMarche ? 'pause'
        : reste <= 10 * MINUTE ? 'critique' : 'jeu';
  return { maintenant, reste, jeu, etat, fin: maintenant + reste };
}

const deuxChiffres = n => String(n).padStart(2, '0');

function hms(ms) {
  if (!Number.isFinite(ms)) return '--:--:--';
  const s = Math.ceil(ms / 1000);
  return `${deuxChiffres(Math.floor(s / 3600))}:${deuxChiffres(Math.floor((s % 3600) / 60))}:${deuxChiffres(s % 60)}`;
}
