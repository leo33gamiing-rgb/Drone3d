'use strict';
// Régie : minuteur, pénalités, annonces vocales, fond sonore et bibliothèque de sons.

const $ = selecteur => document.querySelector(selecteur);

// Catégories de sons. `defaut` : réglage qui mémorise le son utilisé automatiquement.
// `fond` : sons qui tournent en boucle et peuvent se superposer.
const CATEGORIES = {
  screamer: { titre: 'Screamers', court: 'Screamers', defaut: 'screamer',
    aide: '⚡ jump scare · ★ vrai enregistrement · rond coché = son de la pénalité · curseur = volume du son' },
  indice: { titre: 'Indice disponible', court: 'Indice', defaut: 'sonIndice', aide: 'Rond coché = son du bouton « Indice ».' },
  rire: { titre: 'Rires', court: 'Rires' },
  chuchotement: { titre: 'Chuchotements', court: 'Chuchotements' },
  porte: { titre: 'Portes et coups', court: 'Portes' },
  bruitage: { titre: 'Autres bruitages', court: 'Bruitages' },
  recit: { titre: 'Récits et voix', court: 'Récits', enchaine: true, aide: '« Tout lire » enchaîne les récits dans l\'ordre.' },
  ambiance: { titre: 'Ambiances', court: 'Ambiances', fond: true },
  horloge: { titre: 'Horloges (tic-tac)', court: 'Horloges', fond: true },
  enigme: { titre: 'Énigmes sonores (en boucle)', court: 'Énigmes', fond: true },
};
const ONGLETS = Object.keys(CATEGORIES).filter(cle => !CATEGORIES[cle].fond);

let reglages = charger(CLE_REGLAGES, DEFAUTS);
reglages.fond = [...reglages.fond];
reglages.volumesCouches = { ...reglages.volumesCouches };
if (!reglages.reelsAjoutes) {
  // Les vrais cris sont arrivés : la pénalité les tire désormais au hasard (choix modifiable).
  if (reglages.screamer === 'hasard') reglages.screamer = 'hasard-reels';
  reglages.reelsAjoutes = true;
}
if (!reglages.terrifiantsAjoutes) {
  // Les jump scares composés de vrais sons sont arrivés : ils deviennent le choix par défaut.
  if (['hasard', 'hasard-reels'].includes(reglages.screamer)) reglages.screamer = 'hasard-terrifiants';
  reglages.terrifiantsAjoutes = true;
}
let partie = charger(CLE_PARTIE, partieVide(reglages));
let sons = [];
let derniereAnnonce = null; // numéro de la dernière annonce passée (null = à recaler)
let fenetreEcran = null;
let lecture = 0; // numéro de la lecture enchaînée en cours (changé pour l'interrompre)
let lectureActive = false;
let onglet = 'screamer'; // catégorie affichée dans la bibliothèque
const derniersTirages = {};

const heure = ms => new Date(ms).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
const attendre = ms => new Promise(fin => setTimeout(fin, ms));
const nomDuSon = id => sons.find(s => s.id === id)?.nom ?? 'aucun son';
const existe = id => sons.some(s => s.id === id);
const estImporte = son => son.id.startsWith('f:');
const estReel = son => son.reel || estImporte(son); // vrai enregistrement (fourni ou importé)
const intervalleAnnonce = () => Math.max(1, reglages.minutesAnnonce) * MINUTE;
// Volume propre de chaque son (0 à 1) ; la bande continue démarre un peu plus bas.
const volumeSon = id => reglages.volumesCouches[id] ?? (CATEGORIES[sons.find(s => s.id === id)?.cat]?.fond ? 0.8 : 1);
const groupeDe = id => (sons.find(s => s.id === id)?.cat === 'screamer' ? 'screamers' : 'effets');
const jouerSon = id => Sons.jouer(id, { groupe: groupeDe(id), volume: volumeSon(id) });

function sauver() {
  localStorage.setItem(CLE_REGLAGES, JSON.stringify(reglages));
  localStorage.setItem(CLE_PARTIE, JSON.stringify(partie));
}

function noter(message) {
  partie.journal.unshift({ t: Date.now(), message });
  partie.journal.length = Math.min(partie.journal.length, 200);
  sauver();
  afficherJournal();
}

// Déclenche un effet visuel sur l'écran des joueurs.
function signalerEcran(type, texte) {
  localStorage.setItem(CLE_EFFET, JSON.stringify({ id: Math.random(), type, texte, t: Date.now() }));
}

// Tirages au hasard possibles pour les screamers : tous, les vrais cris, ou les jump scares terrifiants.
const FILTRES_HASARD = { hasard: null, 'hasard-reels': estReel, 'hasard-terrifiants': son => son.terrifiant };

function auHasard(cat, filtre = null) {
  let liste = sons.filter(s => s.cat === cat);
  if (filtre && liste.some(filtre)) liste = liste.filter(filtre);
  if (!liste.length) return null;
  let choix;
  do {
    choix = liste[Math.floor(Math.random() * liste.length)];
  } while (liste.length > 1 && choix.id === derniersTirages[cat]);
  derniersTirages[cat] = choix.id;
  return choix.id;
}

function screamerPenalite() {
  if (reglages.screamer in FILTRES_HASARD) return auHasard('screamer', FILTRES_HASARD[reglages.screamer]);
  return existe(reglages.screamer) ? reglages.screamer : auHasard('screamer', FILTRES_HASARD['hasard-terrifiants']);
}
const sonIndice = () => (existe(reglages.sonIndice) ? reglages.sonIndice : auHasard('indice'));

// ---------- Fichiers audio importés (gardés dans le navigateur) ----------

const Base = {
  ouverture: null,
  db() {
    this.ouverture ??= new Promise((ok, ko) => {
      const requete = indexedDB.open('escape-game-sons', 1);
      requete.onupgradeneeded = () => requete.result.createObjectStore('sons', { keyPath: 'id' });
      requete.onsuccess = () => ok(requete.result);
      requete.onerror = () => ko(requete.error);
    });
    return this.ouverture;
  },
  async executer(mode, action) {
    const db = await this.db();
    return new Promise((ok, ko) => {
      const transaction = db.transaction('sons', mode);
      const requete = action(transaction.objectStore('sons'));
      transaction.oncomplete = () => ok(requete.result);
      transaction.onerror = transaction.onabort = () => ko(transaction.error);
    });
  },
  tous() {
    return this.executer('readonly', magasin => magasin.getAll());
  },
  ecrire(son) {
    return this.executer('readwrite', magasin => magasin.put(son));
  },
  supprimer(id) {
    return this.executer('readwrite', magasin => magasin.delete(id));
  },
};

// ---------- Minuteur ----------

function boucle() {
  const t = calculer(partie);
  const numero = Math.floor(t.jeu / intervalleAnnonce());
  if (derniereAnnonce === null || numero < derniereAnnonce) derniereAnnonce = numero;
  if (numero > derniereAnnonce) {
    derniereAnnonce = numero;
    if (t.etat === 'jeu' || t.etat === 'critique') annoncer();
  }

  const finie = t.etat === 'fini';
  if (finie !== partie.finie) {
    partie.finie = finie;
    sauver();
    if (finie) finDePartie();
  }
  afficherStatut(t);
  afficherEnCours();
}

// ---------- Sons en cours (pour arrêter un son lancé par erreur) ----------

let signatureEnCours = '';
const arretsEnCours = new Map(); // clé de la ligne -> fonction d'arrêt

function minSec(s) {
  return Number.isFinite(s) ? `${Math.floor(s / 60)}:${deuxChiffres(Math.floor(s % 60))}` : '…';
}

function afficherEnCours() {
  const lignes = [];
  if (window.speechSynthesis?.speaking) {
    lignes.push({ cle: 'voix', nom: 'Annonce vocale', detail: 'voix', arreter: () => speechSynthesis.cancel() });
  }
  if (Micro.enDirect()) {
    lignes.push({ cle: 'micro', nom: 'Micro en direct', detail: Micro.effets[Micro.effet()]?.nom ?? '', arreter: () => parler(false) });
  }
  if (lectureActive) lignes.push({ cle: `lecture${lecture}`, nom: 'Lecture enchaînée', detail: 'récit', arreter: arreterLecture });
  for (const s of Sons.sonsEnCours()) {
    const son = sons.find(x => x.id === s.id);
    lignes.push({
      cle: `son${s.cle}`,
      id: s.id,
      nom: son?.nom ?? 'son',
      detail: `${CATEGORIES[son?.cat]?.court ?? ''} · ${minSec(s.position)} / ${minSec(s.duree)}`,
      arreter: () => Sons.arreterSon(s.cle),
    });
  }
  for (const id of Sons.couchesActives()) {
    const son = sons.find(x => x.id === id);
    lignes.push({ cle: `couche${id}`, id, nom: son?.nom ?? 'son', detail: `${CATEGORIES[son?.cat]?.court ?? ''} · en boucle`,
      arreter: () => basculerCouche(id) });
  }

  arretsEnCours.clear();
  lignes.forEach(l => arretsEnCours.set(l.cle, l.arreter));
  const signature = lignes.map(l => l.cle).join('|');
  const liste = $('#liste-en-cours');
  if (signature !== signatureEnCours) {
    // On ne reconstruit la liste que si elle change : un clic sur « Arrêter » n'est jamais perdu.
    signatureEnCours = signature;
    liste.replaceChildren(...lignes.map(l => element('li', {},
      element('span', { className: 'nom', textContent: l.nom, title: l.nom }),
      element('span', { className: 'detail' }),
      l.id ? curseurVolume(l.id) : element('span'),
      bouton('■ Arrêter', 'Arrêter ce son', () => arretsEnCours.get(l.cle)?.()))));
  }
  [...liste.children].forEach((li, i) => {
    const detail = li.querySelector('.detail');
    if (detail.textContent !== lignes[i].detail) detail.textContent = lignes[i].detail;
  });
  $('#rien-en-cours').hidden = lignes.length > 0;
  $('#b-stop-tout').hidden = lignes.length === 0;
}

function ecrire(selecteur, texte) {
  const element = $(selecteur);
  if (element.textContent !== texte) element.textContent = texte;
}

function afficherStatut(t) {
  ecrire('#horloge', new Date(t.maintenant).toLocaleTimeString('fr-FR'));
  ecrire('#statut', {
    attente: `Prêt : ${hms(t.reste)} au compteur. Cliquez sur « Démarrer » quand vous voulez.`,
    jeu: `En cours — fin prévue à ${heure(t.fin)}`,
    critique: `Dernières minutes ! Fin à ${heure(t.fin)}`,
    pause: `En pause — ${hms(t.reste)} restant`,
    fini: 'Temps écoulé',
  }[t.etat]);

  const marche = $('#b-marche');
  ecrire('#b-marche', {
    attente: 'Démarrer le minuteur',
    jeu: 'Mettre en pause',
    critique: 'Mettre en pause',
    pause: 'Reprendre',
    fini: 'Temps écoulé : ajoutez du temps pour continuer',
  }[t.etat]);
  marche.classList.toggle('vert', t.etat === 'attente' || t.etat === 'pause');
  marche.disabled = t.etat === 'fini';

  const n = partie.penalites.length;
  const total = partie.penalites.reduce((somme, p) => somme + p.minutes, 0);
  ecrire('#nb-penalites', n === 0 ? 'Aucune pénalité' : `${n} pénalité${n > 1 ? 's' : ''} (−${total} min)`);

  const avantAnnonce = intervalleAnnonce() - (t.jeu % intervalleAnnonce());
  let prochaine = '';
  if (t.etat !== 'fini' && avantAnnonce >= t.reste) prochaine = "Plus d'annonce automatique avant la fin";
  else if (t.etat === 'jeu' || t.etat === 'critique') prochaine = `Prochaine annonce automatique à ${heure(t.maintenant + avantAnnonce)}`;
  else if (t.etat !== 'fini') prochaine = `Prochaine annonce après ${Math.ceil(avantAnnonce / MINUTE)} min de jeu`;
  ecrire('#prochaine-annonce', prochaine);

  ecrire('#b-fond', Sons.couchesActives().length ? 'Tout couper' : 'Lancer');
  $('#alerte-son').hidden = Sons.actif();
}

function reglerReste(ms) {
  ms = Math.max(0, ms);
  if (partie.enMarche) partie.finPrevue = Date.now() + ms;
  else partie.resteFige = ms;
  sauver();
  boucle();
}

function demarrerOuPause() {
  const t = calculer(partie);
  if (partie.enMarche) {
    Object.assign(partie, { enMarche: false, resteFige: t.reste, jeuAccumule: t.jeu });
    noter('Minuteur en pause');
  } else if (t.reste > 0) {
    const premiereFois = !partie.lance;
    Object.assign(partie, { lance: true, enMarche: true, finPrevue: Date.now() + t.reste, repriseA: Date.now() });
    noter(premiereFois ? 'Minuteur démarré' : 'Minuteur relancé');
    if (premiereFois) {
      if (reglages.fondAuDemarrage && !Sons.couchesActives().length) lancerFond();
      annoncer();
    }
  }
  sauver();
  boucle();
}

function ajuster(minutes) {
  reglerReste(calculer(partie).reste + minutes * MINUTE);
  noter(`Temps ${minutes > 0 ? '+' : '−'}${Math.abs(minutes)} min`);
}

function reglerTempsRestant() {
  const h = Math.max(0, Number($('#i-heures').value) || 0);
  const m = Math.max(0, Number($('#i-minutes').value) || 0);
  reglerReste((h * 60 + m) * MINUTE);
  noter(`Temps restant réglé sur ${h} h ${deuxChiffres(m)}`);
}

function finirA() {
  const [h, m] = $('#i-fin').value.split(':').map(Number);
  if (!Number.isFinite(h)) return;
  const fin = new Date();
  fin.setHours(h, m || 0, 0, 0);
  if (fin <= new Date()) fin.setDate(fin.getDate() + 1); // l'heure est passée : c'est demain (ex. 2 h du matin)
  reglerReste(fin - Date.now());
  noter(`Fin réglée à ${$('#i-fin').value}`);
}

function reinitialiser() {
  if (!confirm(`Remettre le minuteur à ${reglages.dureeDepart.replace(':', ' h ')}, sans pénalités, et vider le journal ?`)) return;
  partie = partieVide(reglages);
  derniereAnnonce = null;
  noter('Partie réinitialisée');
  boucle();
}

// Ex. 7 h 02 -> « 7 heures et 2 minutes ».
function enToutesLettres(ms) {
  const minutes = Math.round(ms / MINUTE);
  if (minutes < 1) return "moins d'une minute";
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  const morceaux = [];
  if (h) morceaux.push(h === 1 ? 'une heure' : `${h} heures`);
  if (m) morceaux.push(m === 1 ? 'une minute' : `${m} minutes`);
  return morceaux.join(' et ');
}

// ---------- Voix ----------

let enonce = null; // gardé en mémoire : sinon Chrome peut oublier de signaler la fin

// Les voix « Natural » (Edge, en ligne) sont bien plus réalistes que les voix Windows classiques.
function meilleureVoix(voix) {
  const score = v => (v.lang.startsWith('fr') ? 4 : 0) + (/natural|online|neural/i.test(v.name) ? 2 : 0)
    + (/denise|eloise|vivienne|julie|hortense|female/i.test(v.name) ? 1 : 0);
  return voix.slice().sort((a, b) => score(b) - score(a))[0] ?? null;
}

function parler(texte) {
  return new Promise(fin => {
    if (!window.speechSynthesis) return fin();
    speechSynthesis.cancel();
    const voix = speechSynthesis.getVoices();
    enonce = new SpeechSynthesisUtterance(texte);
    enonce.lang = 'fr-FR';
    enonce.voice = voix.find(v => v.voiceURI === reglages.voix) || meilleureVoix(voix);
    enonce.pitch = reglages.hauteurVoix;
    enonce.rate = reglages.vitesseVoix;
    enonce.onend = fin;
    enonce.onerror = fin;
    setTimeout(fin, 20000);
    speechSynthesis.speak(enonce);
  });
}

function remplirVoix() {
  if (!window.speechSynthesis) return;
  const voix = speechSynthesis.getVoices();
  const auto = meilleureVoix(voix);
  const select = $('[data-reglage="voix"]');
  select.replaceChildren(
    new Option(`Automatique${auto ? ` (${auto.name})` : ''}`, ''),
    ...voix.filter(v => v.lang.startsWith('fr')).map(v => new Option(`${v.name} (${v.lang})`, v.voiceURI)),
  );
  select.value = reglages.voix;
}

// ---------- Actions de la régie ----------

function penalite() {
  const bouton = $('#b-penalite');
  bouton.disabled = true; // évite une double pénalité sur un double-clic
  setTimeout(() => (bouton.disabled = false), 1500);
  const minutes = reglages.minutesPenalite;
  const screamer = screamerPenalite();
  partie.penalites.push({ t: Date.now(), minutes });
  reglerReste(calculer(partie).reste - minutes * MINUTE);
  noter(`Pénalité : −${minutes} min (${nomDuSon(screamer)})`);
  signalerEcran('penalite', `−${minutes} MIN`);
  Sons.attenuer(true);
  jouerSon(screamer).then(() => Sons.attenuer(false));
}

function annulerPenalite() {
  const derniere = partie.penalites.pop();
  if (!derniere) return;
  reglerReste(calculer(partie).reste + derniere.minutes * MINUTE);
  noter(`Pénalité annulée (+${derniere.minutes} min)`);
}

function indice() {
  jouerSon(sonIndice());
  signalerEcran('indice', reglages.texteIndice);
  noter('Indice disponible');
}

async function annoncer() {
  const texte = reglages.texteAnnonce.replaceAll('{temps}', enToutesLettres(calculer(partie).reste));
  noter(`Annonce : « ${texte} »`);
  Sons.attenuer(true);
  await Promise.race([jouerSon(reglages.sonAvantAnnonce), attendre(4000)]);
  await parler(texte);
  Sons.attenuer(false);
}

async function finDePartie() {
  noter('Temps écoulé !');
  Sons.attenuer(true);
  await Promise.race([jouerSon(screamerPenalite()), attendre(6000)]);
  await parler('Le temps est écoulé.');
  Sons.attenuer(false);
}

// Joue tous les sons d'une catégorie à la suite (ex. un récit découpé en plusieurs fichiers).
async function lireDansLOrdre(cat) {
  const numero = ++lecture;
  lectureActive = true;
  noter(`Lecture : ${CATEGORIES[cat].titre}`);
  Sons.attenuer(true);
  for (const son of sons.filter(s => s.cat === cat)) {
    if (numero !== lecture) break;
    await jouerSon(son.id);
    await attendre(500);
  }
  if (numero === lecture) lectureActive = false;
  Sons.attenuer(false);
}

function arreterLecture() {
  lecture++;
  lectureActive = false;
  Sons.sonsEnCours().filter(s => CATEGORIES[sons.find(x => x.id === s.id)?.cat]?.enchaine)
    .forEach(s => Sons.arreterSon(s.cle));
}

function toutCouper() {
  parler(false);
  lecture++;
  lectureActive = false;
  Sons.toutCouper();
  window.speechSynthesis?.cancel();
  afficherFond();
}

function ouvrirEcran() {
  if (fenetreEcran && !fenetreEcran.closed) return fenetreEcran.focus();
  fenetreEcran = window.open('ecran.html', 'ecran-joueurs', 'popup,width=1280,height=720');
}

// ---------- Micro (voix déformée en direct) ----------

const microVerrouille = () => $('#i-micro-verrou').checked;

function parler(oui) {
  if (!Micro.pret() || oui === Micro.enDirect()) return;
  Micro.parler(oui);
  Sons.attenuer(oui); // le fond sonore baisse pendant qu'on parle
  const b = $('#b-parler');
  b.classList.toggle('en-direct', oui);
  b.textContent = oui ? '● EN DIRECT' + (microVerrouille() ? ' — cliquer pour couper' : ' — relâcher pour couper')
    : microVerrouille() ? 'Cliquer pour parler' : 'Maintenir pour parler';
}

async function activerMicro() {
  const bouton = $('#b-micro-activer');
  bouton.disabled = true;
  bouton.textContent = 'Activation…';
  try {
    await Micro.activer(reglages.micro);
  } catch (erreur) {
    bouton.disabled = false;
    bouton.textContent = 'Activer le micro';
    const raisons = {
      NotAllowedError: "l'accès au micro a été refusé. Autorisez-le dans la fenêtre du navigateur (icône du micro dans la barre d'adresse).",
      NotFoundError: "aucun micro n'est branché ou reconnu par Windows.",
      OverconstrainedError: "le micro choisi n'est plus disponible.",
    };
    if (erreur?.name === 'OverconstrainedError' && reglages.micro) {
      reglages.micro = '';
      sauver();
      return activerMicro();
    }
    return alert(`Impossible d'activer le micro : ${raisons[erreur?.name] ?? erreur?.message ?? erreur}`);
  }
  bouton.hidden = true;
  $('#micro-commandes').hidden = false;
  noter('Micro activé');
  const micros = await Micro.appareils();
  const choix = $('#s-micro');
  choix.replaceChildren(new Option('Micro par défaut de Windows', ''),
    ...micros.filter(m => m.deviceId && m.deviceId !== 'default').map(m => new Option(m.label || 'Micro', m.deviceId)));
  choix.value = reglages.micro;
  const jauge = $('#micro-niveau');
  const mesurer = () => {
    jauge.style.width = `${Math.round(Micro.niveau() * 100)}%`;
    requestAnimationFrame(mesurer);
  };
  mesurer();
}

function brancherMicro() {
  const effets = $('#s-effet-voix');
  effets.replaceChildren(...Object.entries(Micro.effets).map(([cle, e]) => new Option(e.nom, cle)));
  effets.value = reglages.effetVoix;
  Micro.choisirEffet(reglages.effetVoix);
  Micro.volume(reglages.volumeVoix);
  $('#b-micro-activer').onclick = activerMicro;
  $('#s-micro').onchange = async evenement => {
    reglages.micro = evenement.target.value;
    sauver();
    const etaitEnDirect = Micro.enDirect();
    parler(false);
    await Micro.activer(reglages.micro).catch(erreur => alert(`Micro indisponible : ${erreur?.message ?? erreur}`));
    if (etaitEnDirect) parler(true);
  };
  $('#i-micro-verrou').onchange = () => parler(false);

  // Bouton : maintenu = en direct, relâché = coupé (ou un clic allume / un clic coupe si verrouillé).
  const b = $('#b-parler');
  b.onpointerdown = evenement => {
    b.setPointerCapture(evenement.pointerId);
    parler(microVerrouille() ? !Micro.enDirect() : true);
  };
  b.onpointerup = b.onpointercancel = () => {
    if (!microVerrouille()) parler(false);
  };

  // Barre Espace maintenue = parler (sauf pendant la saisie d'un texte).
  const saisie = cible => cible.closest?.('input, textarea, select');
  document.addEventListener('keydown', evenement => {
    if (evenement.code !== 'Space' || !Micro.pret() || saisie(evenement.target)) return;
    evenement.preventDefault();
    if (!evenement.repeat) parler(microVerrouille() ? !Micro.enDirect() : true);
  });
  document.addEventListener('keyup', evenement => {
    if (evenement.code !== 'Space' || !Micro.pret() || saisie(evenement.target)) return;
    evenement.preventDefault();
    if (!microVerrouille()) parler(false);
  });
}

// ---------- Fond sonore ----------

function lancerFond() {
  const ids = reglages.fond.filter(existe);
  (ids.length ? ids : DEFAUTS.fond).forEach(id => Sons.demarrerCouche(id, volumeSon(id)));
  noter('Bande continue lancée');
  afficherFond();
}

function basculerFond() {
  if (Sons.couchesActives().length) {
    Sons.arreterFond();
    noter('Bande continue coupée');
    afficherFond();
  } else {
    lancerFond();
  }
}

function basculerCouche(id) {
  if (Sons.coucheActive(id)) Sons.arreterCouche(id);
  else Sons.demarrerCouche(id, volumeSon(id));
  const actives = Sons.couchesActives();
  if (actives.length) reglages.fond = actives; // mémorise le mélange pour le relancer d'un clic
  sauver();
  afficherFond();
}

// ---------- Bibliothèque de sons ----------

function element(balise, proprietes = {}, ...enfants) {
  const el = Object.assign(document.createElement(balise), proprietes);
  el.append(...enfants);
  return el;
}

const bouton = (texte, title, onclick) => element('button', { textContent: texte, title, onclick });

function choixParDefaut(cle, valeur) {
  return element('input', {
    type: 'radio',
    name: `defaut-${cle}`,
    title: 'Son utilisé automatiquement',
    checked: reglages[cle] === valeur,
    onchange() {
      reglages[cle] = valeur;
      sauver();
    },
  });
}

// Curseur de volume d'un son ; tous les curseurs du même son restent synchronisés.
function curseurVolume(id) {
  const curseur = element('input', {
    type: 'range', min: 0, max: 1, step: 0.05, value: volumeSon(id), title: 'Volume de ce son',
    oninput() {
      reglages.volumesCouches[id] = Number(curseur.value);
      Sons.reglerVolumeSon(id, Number(curseur.value));
      document.querySelectorAll('input[data-son]').forEach(autre => {
        if (autre !== curseur && autre.dataset.son === id) autre.value = curseur.value;
      });
      sauver();
    },
  });
  curseur.setAttribute('data-son', id);
  return curseur;
}

function boutonAjout(cat, texte = '+ Ajouter des sons') {
  const champ = element('input', { type: 'file', accept: 'audio/*', multiple: true });
  champ.onchange = () => {
    importer(cat, [...champ.files]);
    champ.value = '';
  };
  return element('label', { className: 'ajout', title: 'Ajouter des fichiers audio (MP3, WAV, OGG, M4A)' }, texte, champ);
}

function ligneSon(son) {
  const categorie = CATEGORIES[son.cat] ?? {};
  const li = element('li', { className: son.terrifiant ? 'son terrifiant' : 'son' });
  const jouer = element('button', { className: 'jouer', textContent: son.nom, title: son.nom });
  if (categorie.fond) {
    const active = Sons.coucheActive(son.id);
    li.classList.toggle('active', active);
    jouer.title += active ? ' — cliquer pour arrêter' : ' — cliquer pour lancer en boucle';
    jouer.onclick = () => basculerCouche(son.id);
  } else {
    jouer.onclick = () => jouerSon(son.id);
  }
  li.append(jouer);
  if (categorie.defaut) li.append(choixParDefaut(categorie.defaut, son.id));
  li.append(curseurVolume(son.id));
  if (estImporte(son)) {
    jouer.title += ' — clic droit : renommer';
    jouer.oncontextmenu = evenement => {
      evenement.preventDefault();
      renommer(son);
    };
    li.append(element('button', { className: 'supprimer', textContent: '✕', title: 'Supprimer', onclick: () => supprimerSon(son) }));
  }
  return li;
}

function ligneHasard(valeur, texte) {
  return element('li', { className: 'son hasard' },
    element('button', { className: 'jouer', textContent: texte, title: 'Écouter un exemple',
      onclick: () => jouerSon(auHasard('screamer', FILTRES_HASARD[valeur])) }),
    choixParDefaut('screamer', valeur));
}

function afficherOnglets() {
  $('#onglets').replaceChildren(...ONGLETS.map(cle => element('button', {
    className: cle === onglet ? 'actif' : '',
    onclick() {
      onglet = cle;
      afficherOnglets();
      afficherPads();
    },
  }, CATEGORIES[cle].court, element('span', { className: 'compte', textContent: sons.filter(s => s.cat === cle).length }))));
}

function afficherPads() {
  const categorie = CATEGORIES[onglet];
  const action = categorie.enchaine
    ? bouton('Tout lire dans l\'ordre', 'Jouer tous les récits à la suite', () => lireDansLOrdre(onglet))
    : bouton('Au hasard', 'Jouer un son de cette catégorie au hasard',
      () => jouerSon(auHasard(onglet, onglet === 'screamer' ? FILTRES_HASARD['hasard-terrifiants'] : null)));
  $('#barre-onglet').replaceChildren(action,
    element('p', { className: 'aide', textContent: categorie.aide ?? '★ vrai enregistrement · cliquez sur un son pour le jouer · curseur = volume du son' }),
    boutonAjout(onglet));
  const lignes = onglet === 'screamer'
    ? [ligneHasard('hasard-terrifiants', 'Pénalité : un jump scare ⚡ au hasard'),
      ligneHasard('hasard-reels', 'Pénalité : un vrai cri ★ au hasard'),
      ligneHasard('hasard', "Pénalité : n'importe quel screamer")]
    : [];
  $('#pads').replaceChildren(...lignes, ...sons.filter(s => s.cat === onglet).map(ligneSon));
}

function afficherFond() {
  $('#fond').replaceChildren(...Object.entries(CATEGORIES).filter(([, c]) => c.fond).flatMap(([cle, c]) => [
    element('h3', {}, c.court, boutonAjout(cle, '+')),
    element('ul', { className: 'pads-fond' }, ...sons.filter(s => s.cat === cle).map(ligneSon)),
  ]));
}

function afficherSons() {
  afficherOnglets();
  afficherPads();
  afficherFond();
  const select = $('[data-reglage="sonAvantAnnonce"]');
  select.replaceChildren(
    new Option('Aucun', ''),
    ...sons.filter(s => !CATEGORIES[s.cat]?.fond).map(s => new Option(`${CATEGORIES[s.cat]?.court ?? ''} : ${s.nom}`, s.id)),
  );
  select.value = reglages.sonAvantAnnonce;
}

async function importer(cat, fichiers) {
  for (const fichier of fichiers) {
    const son = {
      id: `f:${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
      nom: fichier.name.replace(/\.[^.]+$/, ''),
      cat,
      ajoute: Date.now(),
      fichier,
    };
    try {
      await Base.ecrire(son);
    } catch (erreur) {
      alert(`Impossible d'enregistrer « ${son.nom} » : ${erreur?.message ?? erreur}`);
      continue;
    }
    Sons.enregistrer(son.id, fichier);
    sons.push(son);
  }
  afficherSons();
}

async function renommer(son) {
  const nom = prompt('Nouveau nom :', son.nom)?.trim();
  if (!nom) return;
  son.nom = nom;
  await Base.ecrire(son);
  afficherSons();
}

async function supprimerSon(son) {
  if (!confirm(`Supprimer « ${son.nom} » de la bibliothèque ?`)) return;
  await Base.supprimer(son.id);
  Sons.oublier(son.id);
  sons = sons.filter(s => s !== son);
  for (const cle of ['screamer', 'sonIndice', 'sonAvantAnnonce']) {
    if (reglages[cle] === son.id) reglages[cle] = DEFAUTS[cle];
  }
  reglages.fond = reglages.fond.filter(id => id !== son.id);
  sauver();
  afficherSons();
}

// ---------- Réglages ----------

function afficherValeur(champ) {
  const valeur = reglages[champ.dataset.reglage];
  if (champ.type === 'checkbox') champ.checked = valeur;
  else champ.value = valeur;
}

function lierReglages() {
  document.querySelectorAll('[data-reglage]').forEach(champ => {
    afficherValeur(champ);
    champ.addEventListener(champ.type === 'range' ? 'input' : 'change', () => {
      const cle = champ.dataset.reglage;
      let valeur = champ.value;
      if (champ.type === 'checkbox') valeur = champ.checked;
      if (champ.type === 'range' || champ.type === 'number') valeur = Number(champ.value);
      const invalide = (champ.type === 'number' && !(valeur >= Number(champ.min))) || (champ.type === 'time' && !valeur);
      if (invalide) return afficherValeur(champ);
      reglages[cle] = valeur;
      if (cle === 'dureeDepart' && !partie.lance) partie.resteFige = dureeEnMs(valeur);
      sauver();
      reglagesModifies();
    });
  });
}

function reglagesModifies() {
  derniereAnnonce = null; // l'intervalle a pu changer : on se recale sans annoncer
  Sons.volumes({ fond: reglages.volumeFond, screamers: reglages.volumeScreamers, effets: reglages.volumeEffets });
  if (Micro.effet() !== reglages.effetVoix) Micro.choisirEffet(reglages.effetVoix);
  Micro.volume(reglages.volumeVoix);
  $('#l-penalite').textContent = `−${reglages.minutesPenalite} min`;
  boucle();
}

function afficherJournal() {
  $('#journal').replaceChildren(...partie.journal.map(({ t, message }) =>
    element('li', {}, element('time', { textContent: new Date(t).toLocaleTimeString('fr-FR') }), message)));
}

// Tic-tac dans un « worker » : il continue à l'heure même si la fenêtre est en arrière-plan.
function lancerHorloge() {
  try {
    const tictac = new Worker(URL.createObjectURL(new Blob(['setInterval(() => postMessage(0), 250)'])));
    tictac.onmessage = boucle;
    tictac.onerror = () => setInterval(boucle, 250);
  } catch {
    setInterval(boucle, 250);
  }
}

async function demarrer() {
  // Récits et vrais enregistrements d'abord, puis les sons fabriqués par synthèse.
  const catalogues = [
    [typeof CATALOGUE_RECITS === 'undefined' ? [] : CATALOGUE_RECITS, { reel: true }],
    [typeof CATALOGUE_JUMPSCARES === 'undefined' ? [] : CATALOGUE_JUMPSCARES, { reel: true, terrifiant: true }],
    [typeof CATALOGUE_REELS === 'undefined' ? [] : CATALOGUE_REELS, { reel: true }],
    [typeof CATALOGUE === 'undefined' ? [] : CATALOGUE, { reel: false }],
    [typeof CATALOGUE_ENIGMES === 'undefined' ? [] : CATALOGUE_ENIGMES, { reel: false }],
  ];
  for (const [catalogue, { reel, terrifiant = false }] of catalogues) {
    for (const { cat, fichier, nom } of catalogue) {
      const libelle = terrifiant ? `⚡ ${nom}` : reel && cat !== 'recit' ? `★ ${nom}` : nom; // ⚡ jump scare, ★ vrai son
      sons.push({ id: `pack:${fichier}`, nom: libelle, cat, reel, terrifiant });
      Sons.enregistrer(`pack:${fichier}`, fichier);
    }
  }
  try {
    const importes = (await Base.tous()).sort((a, b) => a.ajoute - b.ajoute);
    importes.forEach(son => Sons.enregistrer(son.id, son.fichier));
    sons.push(...importes);
  } catch (erreur) {
    noter(`Impossible de relire les sons importés : ${erreur?.message ?? erreur}`);
  }

  const reste = calculer(partie).reste;
  $('#i-heures').value = Math.floor(reste / 3600000);
  $('#i-minutes').value = Math.floor((reste % 3600000) / MINUTE);

  lierReglages();
  afficherSons();
  remplirVoix();
  window.speechSynthesis?.addEventListener('voiceschanged', remplirVoix);
  afficherJournal();
  reglagesModifies();

  $('#b-marche').onclick = demarrerOuPause;
  $('#b-regler').onclick = reglerTempsRestant;
  $('#b-finir').onclick = finirA;
  $('#b-reinitialiser').onclick = reinitialiser;
  $('#b-ecran').onclick = ouvrirEcran;
  $('#b-penalite').onclick = penalite;
  $('#b-annuler').onclick = annulerPenalite;
  $('#b-indice').onclick = indice;
  $('#b-annonce').onclick = annoncer;
  $('#b-stop-tout').onclick = toutCouper;
  $('#b-reglages').onclick = () => $('#tiroir').showModal();
  $('#b-fermer-tiroir').onclick = () => $('#tiroir').close();
  brancherMicro();
  $('#b-fond').onclick = basculerFond;
  document.querySelectorAll('[data-ajuster]').forEach(b => (b.onclick = () => ajuster(Number(b.dataset.ajuster))));

  Sons.reveiller();
  document.addEventListener('pointerdown', Sons.reveiller, true);
  // Empêche l'ordinateur de se mettre en veille tant que la régie est affichée.
  const resterEveille = () => navigator.wakeLock?.request('screen').catch(() => {});
  resterEveille();
  document.addEventListener('visibilitychange', () => document.visibilityState === 'visible' && resterEveille());

  lancerHorloge();
}

demarrer();
