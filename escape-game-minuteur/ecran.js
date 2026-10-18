'use strict';
// Écran des joueurs : relit en continu l'état écrit par la régie et l'affiche.

const apercu = location.search.includes('apercu');
const el = id => document.getElementById(id);

function lireEffet() {
  try {
    return JSON.parse(localStorage.getItem(CLE_EFFET));
  } catch {
    return null;
  }
}

let dernierEffet = lireEffet()?.id; // on ignore les effets déjà passés à l'ouverture

function rejouer(element, classe) {
  element.classList.remove(classe);
  void element.offsetWidth; // relance l'animation CSS
  element.classList.add(classe);
}

function rafraichir() {
  const reglages = charger(CLE_REGLAGES, DEFAUTS);
  const t = calculer(charger(CLE_PARTIE, partieVide(reglages)));
  const texte = hms(t.reste);
  if (el('minuteur').textContent !== texte) el('minuteur').textContent = texte;
  if (document.body.dataset.etat !== t.etat) document.body.dataset.etat = t.etat;

  const effet = lireEffet();
  if (effet && effet.id !== dernierEffet) {
    dernierEffet = effet.id;
    if (effet.type === 'penalite') {
      el('malus').textContent = effet.texte;
      ['flash', 'malus', 'scene'].forEach(id => rejouer(el(id), 'go'));
    }
  }

  // Message sous le minuteur : fin de partie, sinon indice récent (30 s).
  let message = '';
  if (t.etat === 'fini') message = 'LE TEMPS EST ÉCOULÉ';
  else if (effet?.type === 'indice' && t.maintenant - effet.t < 30000) message = effet.texte;
  if (message && el('message').textContent !== message) el('message').textContent = message;
  el('message').classList.toggle('visible', Boolean(message));
}

if (apercu) {
  document.body.classList.add('apercu');
} else {
  document.addEventListener('dblclick', () => {
    if (document.fullscreenElement) document.exitFullscreen();
    else document.documentElement.requestFullscreen().catch(() => {});
  });
  // Empêche l'écran de se mettre en veille pendant la partie.
  const resterEveille = () => navigator.wakeLock?.request('screen').catch(() => {});
  resterEveille();
  document.addEventListener('visibilitychange', () => document.visibilityState === 'visible' && resterEveille());
}

rafraichir();
setInterval(rafraichir, 250);
