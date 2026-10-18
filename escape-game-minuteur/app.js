'use strict';
// Régie : minuteur, pénalités, annonces vocales, fond sonore et bibliothèque de sons.

const $ = selecteur => document.querySelector(selecteur);

// Catégories de sons. `defaut` : réglage qui mémorise le son utilisé automatiquement.
// `fond` : sons qui tournent en boucle et peuvent se superposer.
const CATEGORIES = {
  screamer: { titre: 'Screamers', aide: 'Le son coché part à chaque pénalité.', defaut: 'screamer' },
  indice: { titre: 'Indice disponible', aide: 'Le son coché part avec le bouton « Indice ».', defaut: 'sonIndice' },
  rire: { titre: 'Rires' },
  chuchotement: { titre: 'Chuchotements' },
  porte: { titre: 'Portes et coups' },
  bruitage: { titre: 'Autres bruitages' },
  recit: { titre: 'Récits et voix', aide: 'Vos enregistrements. « Tout lire » les enchaîne dans l\'ordre.', enchaine: true },
  ambiance: { titre: 'Ambiances', fond: true },
  horloge: { titre: 'Horloges (tic-tac)', fond: true },
};

let reglages = charger(CLE_REGLAGES, DEFAUTS);
reglages.fond = [...reglages.fond];
reglages.volumesCouches = { ...reglages.volumesCouches };
let partie = charger(CLE_PARTIE, partieVide(reglages));
let sons = [];
let derniereAnnonce = null; // numéro de la dernière annonce passée (null = à recaler)
let fenetreEcran = null;
let lecture = 0; // numéro de la lecture enchaînée en cours (changé pour l'interrompre)
const derniersTirages = {};

const heure = ms => new Date(ms).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
const attendre = ms => new Promise(fin => setTimeout(fin, ms));
const nomDuSon = id => sons.find(s => s.id === id)?.nom ?? 'aucun son';
const existe = id => sons.some(s => s.id === id);
const estImporte = son => son.id.startsWith('f:');
const intervalleAnnonce = () => Math.max(1, reglages.minutesAnnonce) * MINUTE;
const volumeCouche = id => reglages.volumesCouches[id] ?? 0.8;

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

function auHasard(cat) {
  const liste = sons.filter(s => s.cat === cat);
  if (!liste.length) return null;
  let choix;
  do {
    choix = liste[Math.floor(Math.random() * liste.length)];
  } while (liste.length > 1 && choix.id === derniersTirages[cat]);
  derniersTirages[cat] = choix.id;
  return choix.id;
}

const screamerPenalite = () => (existe(reglages.screamer) ? reglages.screamer : auHasard('screamer'));
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

  ecrire('#b-fond', Sons.couchesActives().length ? 'Couper le fond sonore' : 'Lancer le fond sonore');
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
  Sons.jouer(screamer).then(() => Sons.attenuer(false));
}

function annulerPenalite() {
  const derniere = partie.penalites.pop();
  if (!derniere) return;
  reglerReste(calculer(partie).reste + derniere.minutes * MINUTE);
  noter(`Pénalité annulée (+${derniere.minutes} min)`);
}

function indice() {
  Sons.jouer(sonIndice());
  signalerEcran('indice', reglages.texteIndice);
  noter('Indice disponible');
}

async function annoncer() {
  const texte = reglages.texteAnnonce.replaceAll('{temps}', enToutesLettres(calculer(partie).reste));
  noter(`Annonce : « ${texte} »`);
  Sons.attenuer(true);
  await Promise.race([Sons.jouer(reglages.sonAvantAnnonce), attendre(4000)]);
  await parler(texte);
  Sons.attenuer(false);
}

async function finDePartie() {
  noter('Temps écoulé !');
  Sons.attenuer(true);
  await Promise.race([Sons.jouer(screamerPenalite()), attendre(6000)]);
  await parler('Le temps est écoulé.');
  Sons.attenuer(false);
}

// Joue tous les sons d'une catégorie à la suite (ex. un récit découpé en plusieurs fichiers).
async function lireDansLOrdre(cat) {
  const numero = ++lecture;
  noter(`Lecture : ${CATEGORIES[cat].titre}`);
  Sons.attenuer(true);
  for (const son of sons.filter(s => s.cat === cat)) {
    if (numero !== lecture) break;
    await Sons.jouer(son.id);
    await attendre(500);
  }
  Sons.attenuer(false);
}

function toutCouper() {
  lecture++;
  Sons.toutCouper();
  window.speechSynthesis?.cancel();
  afficherSons();
}

function ouvrirEcran() {
  if (fenetreEcran && !fenetreEcran.closed) return fenetreEcran.focus();
  fenetreEcran = window.open('ecran.html', 'ecran-joueurs', 'popup,width=1280,height=720');
}

// ---------- Fond sonore ----------

function lancerFond() {
  const ids = reglages.fond.filter(existe);
  (ids.length ? ids : DEFAUTS.fond).forEach(id => Sons.demarrerCouche(id, volumeCouche(id)));
  noter('Fond sonore lancé');
  afficherSons();
}

function basculerFond() {
  if (Sons.couchesActives().length) {
    Sons.arreterFond();
    noter('Fond sonore coupé');
    afficherSons();
  } else {
    lancerFond();
  }
}

function basculerCouche(id) {
  if (Sons.coucheActive(id)) Sons.arreterCouche(id);
  else Sons.demarrerCouche(id, volumeCouche(id));
  const actives = Sons.couchesActives();
  if (actives.length) reglages.fond = actives; // mémorise le mélange pour le relancer d'un clic
  sauver();
  afficherSons();
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

function ligneSon(son, categorie) {
  const nom = element('span', { className: 'nom', textContent: son.nom, title: son.nom });
  const li = element('li');
  if (categorie.fond) {
    const active = Sons.coucheActive(son.id);
    li.classList.toggle('active', active);
    li.append(
      bouton(active ? '■' : '▶', active ? 'Arrêter' : 'Lancer en boucle', () => basculerCouche(son.id)),
      nom,
      element('input', {
        type: 'range', min: 0, max: 1, step: 0.05, value: volumeCouche(son.id), title: 'Volume de ce son',
        oninput(evenement) {
          reglages.volumesCouches[son.id] = Number(evenement.target.value);
          Sons.volumeDeCouche(son.id, reglages.volumesCouches[son.id]);
          sauver();
        },
      }),
    );
  } else {
    li.append(bouton('▶', 'Jouer', () => Sons.jouer(son.id)), nom);
    if (categorie.defaut) li.append(choixParDefaut(categorie.defaut, son.id));
  }
  if (estImporte(son)) {
    nom.title += ' — double-cliquez pour renommer';
    nom.ondblclick = () => renommer(son);
    li.append(bouton('✕', 'Supprimer', () => supprimerSon(son)));
  }
  return li;
}

function blocCategorie(cle, categorie) {
  const liste = element('ul');
  if (cle === 'screamer') {
    liste.append(element('li', { className: 'hasard' },
      bouton('▶', 'Jouer un screamer au hasard', () => Sons.jouer(auHasard('screamer'))),
      element('span', { className: 'nom', textContent: 'Au hasard (un différent à chaque fois)' }),
      choixParDefaut('screamer', 'hasard')));
  }
  liste.append(...sons.filter(s => s.cat === cle).map(s => ligneSon(s, categorie)));
  const entete = element('div', { className: 'entete' }, element('h3', { textContent: categorie.titre }));
  if (categorie.enchaine) entete.append(bouton('Tout lire', 'Jouer tous les sons dans l\'ordre', () => lireDansLOrdre(cle)));
  else if (!categorie.fond) entete.append(bouton('Au hasard', 'Jouer un son de cette catégorie au hasard', () => Sons.jouer(auHasard(cle))));
  const ajout = element('input', { type: 'file', accept: 'audio/*', multiple: true });
  ajout.onchange = () => {
    importer(cle, [...ajout.files]);
    ajout.value = '';
  };
  return element('div', { className: 'cat' },
    entete,
    ...(categorie.aide ? [element('p', { className: 'aide', textContent: categorie.aide })] : []),
    liste,
    element('label', { className: 'ajout' }, '+ Ajouter des sons', ajout));
}

function afficherSons() {
  const blocs = Object.entries(CATEGORIES).map(([cle, categorie]) => [categorie, blocCategorie(cle, categorie)]);
  $('#bibliotheque').replaceChildren(...blocs.filter(([c]) => !c.fond).map(([, bloc]) => bloc));
  $('#fond').replaceChildren(...blocs.filter(([c]) => c.fond).map(([, bloc]) => bloc));

  const select = $('[data-reglage="sonAvantAnnonce"]');
  select.replaceChildren(
    new Option('Aucun', ''),
    ...sons.filter(s => !CATEGORIES[s.cat]?.fond).map(s => new Option(`${CATEGORIES[s.cat]?.titre ?? ''} : ${s.nom}`, s.id)),
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
  Sons.volumes(reglages.volumeEffets, reglages.volumeFond);
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
  for (const { cat, fichier, nom } of typeof CATALOGUE === 'undefined' ? [] : CATALOGUE) {
    sons.push({ id: `pack:${fichier}`, nom, cat });
    Sons.enregistrer(`pack:${fichier}`, fichier);
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
  $('#b-stop').onclick = toutCouper;
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
