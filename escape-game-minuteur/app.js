'use strict';
// Régie : minuteur, pénalités, annonces vocales et bibliothèque de sons.

const $ = selecteur => document.querySelector(selecteur);

// Sons générés par l'ordinateur, disponibles même sans fichier importé.
const SONS_INTEGRES = [
  { id: 'synth:cri', nom: 'Cri strident (généré)', cat: 'screamer' },
  { id: 'synth:carillon', nom: 'Boîte à musique faussée (générée)', cat: 'indice' },
  { id: 'synth:glas', nom: 'Glas funèbre (généré)', cat: 'bruitage' },
  { id: 'synth:coeur', nom: 'Battements de cœur (générés)', cat: 'bruitage' },
  { id: 'synth:nappe', nom: 'Nappe angoissante (générée)', cat: 'ambiance' },
];

// Catégorie de sons -> réglage qui mémorise le son « par défaut » de la catégorie.
const CATEGORIES = { screamer: 'screamer', indice: 'sonIndice', bruitage: null, ambiance: 'ambiance' };

let reglages = charger('egm.reglages', DEFAUTS);
let partie = charger('egm.partie', partieVide());
let sons = [...SONS_INTEGRES];
let derniereAnnonce = null; // numéro de la dernière annonce passée (null = à recaler sur l'heure)
let fenetreEcran = null;

const heure = ms => new Date(ms).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
const attendre = ms => new Promise(fin => setTimeout(fin, ms));
const nomDuSon = id => sons.find(s => s.id === id)?.nom ?? 'son inconnu';
const intervalleAnnonce = () => Math.max(1, reglages.minutesAnnonce) * MINUTE;

function sauver() {
  localStorage.setItem('egm.reglages', JSON.stringify(reglages));
  localStorage.setItem('egm.partie', JSON.stringify(partie));
}

function noter(message) {
  partie.journal.unshift({ t: Date.now(), message });
  partie.journal.length = Math.min(partie.journal.length, 200);
  sauver();
  afficherJournal();
}

// Déclenche un effet visuel sur l'écran des joueurs.
function signalerEcran(type, texte) {
  localStorage.setItem('egm.effet', JSON.stringify({ id: Math.random(), type, texte, t: Date.now() }));
}

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
  const t = calculer(reglages, partie);
  const numero = t.commencee ? Math.floor((t.maintenant - t.debut) / intervalleAnnonce()) : -1;
  if (derniereAnnonce === null || numero < derniereAnnonce) derniereAnnonce = numero;
  if (numero > derniereAnnonce) {
    derniereAnnonce = numero;
    if (t.etat !== 'fini') annoncer();
  }

  const finie = t.etat === 'fini';
  if (finie !== partie.finie) {
    partie.finie = finie;
    sauver();
    if (finie) finDePartie();
  }
  afficherStatut(t, numero);
}

function ecrire(selecteur, texte) {
  const element = $(selecteur);
  if (element.textContent !== texte) element.textContent = texte;
}

function afficherStatut(t, numero) {
  ecrire('#horloge', new Date(t.maintenant).toLocaleTimeString('fr-FR'));
  ecrire('#statut', {
    attente: `En attente — la partie commence à ${heure(t.debut)}`,
    jeu: `Partie en cours — fin à ${heure(t.fin)}`,
    critique: `Dernières minutes ! Fin à ${heure(t.fin)}`,
    fini: 'Temps écoulé',
  }[t.etat]);
  const n = partie.penalites.length;
  ecrire('#nb-penalites', n === 0 ? 'Aucune pénalité' : `${n} pénalité${n > 1 ? 's' : ''} (−${n * reglages.minutesPenalite} min)`);
  const prochaine = t.debut + (numero + 1) * intervalleAnnonce();
  ecrire('#prochaine-annonce', t.etat === 'fini' ? '' : prochaine < t.fin
    ? `Prochaine annonce automatique à ${heure(prochaine)}`
    : "Plus d'annonce automatique avant la fin");
  $('#alerte-son').hidden = Sons.actif();
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

function parler(texte) {
  return new Promise(fin => {
    if (!window.speechSynthesis) return fin();
    speechSynthesis.cancel();
    const voix = speechSynthesis.getVoices();
    enonce = new SpeechSynthesisUtterance(texte);
    enonce.lang = 'fr-FR';
    enonce.voice = voix.find(v => v.voiceURI === reglages.voix) || voix.find(v => v.lang.startsWith('fr')) || null;
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
  const voix = speechSynthesis.getVoices().slice()
    .sort((a, b) => b.lang.startsWith('fr') - a.lang.startsWith('fr') || a.name.localeCompare(b.name));
  const select = $('[data-reglage="voix"]');
  select.replaceChildren(
    new Option('Automatique (première voix française)', ''),
    ...voix.map(v => new Option(`${v.name} (${v.lang})`, v.voiceURI)),
  );
  select.value = reglages.voix;
}

// ---------- Actions de la régie ----------

function penalite() {
  const bouton = $('#b-penalite');
  bouton.disabled = true; // évite une double pénalité sur un double-clic
  setTimeout(() => (bouton.disabled = false), 1500);
  partie.penalites.push(Date.now());
  noter(`Pénalité : −${reglages.minutesPenalite} min (${nomDuSon(reglages.screamer)})`);
  signalerEcran('penalite', `−${reglages.minutesPenalite} MIN`);
  Sons.attenuer(true);
  Sons.jouer(reglages.screamer).then(() => Sons.attenuer(false));
  boucle();
}

function annulerPenalite() {
  if (!partie.penalites.length) return;
  partie.penalites.pop();
  noter('Dernière pénalité annulée');
  boucle();
}

function indice() {
  Sons.jouer(reglages.sonIndice);
  signalerEcran('indice', reglages.texteIndice);
  noter('Indice disponible');
}

async function annoncer() {
  const texte = reglages.texteAnnonce.replaceAll('{temps}', enToutesLettres(calculer(reglages, partie).reste));
  noter(`Annonce : « ${texte} »`);
  Sons.attenuer(true);
  await Promise.race([Sons.jouer(reglages.sonAvantAnnonce), attendre(4000)]);
  await parler(texte);
  Sons.attenuer(false);
}

async function finDePartie() {
  noter('Temps écoulé !');
  Sons.attenuer(true);
  await Promise.race([Sons.jouer(reglages.screamer), attendre(6000)]);
  await parler('Le temps est écoulé.');
  Sons.attenuer(false);
}

function toutCouper() {
  Sons.toutCouper();
  window.speechSynthesis?.cancel();
  afficherAmbiance();
}

function ouvrirEcran() {
  if (fenetreEcran && !fenetreEcran.closed) return fenetreEcran.focus();
  fenetreEcran = window.open('ecran.html', 'ecran-joueurs', 'popup,width=1280,height=720');
}

function versChampDate(d) {
  return `${d.getFullYear()}-${deuxChiffres(d.getMonth() + 1)}-${deuxChiffres(d.getDate())}T${deuxChiffres(d.getHours())}:${deuxChiffres(d.getMinutes())}`;
}

function demarrerMaintenant() {
  if (!confirm(`Démarrer la partie maintenant ? La fin reste fixée à ${heure(new Date(reglages.fin))}.`)) return;
  const maintenant = new Date();
  maintenant.setSeconds(0, 0);
  reglages.debut = versChampDate(maintenant);
  sauver();
  document.querySelectorAll('[data-reglage="debut"]').forEach(afficherValeur);
  noter('Partie démarrée');
  reglagesModifies();
  annoncer();
}

function reinitialiser() {
  if (!confirm('Effacer les pénalités et le journal de la partie ?')) return;
  partie = partieVide();
  sauver();
  noter('Partie réinitialisée');
  boucle();
}

// ---------- Ambiance ----------

function lancerAmbiance(id) {
  const musiques = sons.filter(s => s.cat === 'ambiance' && s.fichier);
  const enchainer = reglages.enchainer && musiques.length > 1 && musiques.some(s => s.id === id);
  Sons.lancerAmbiance(id, {
    boucle: !enchainer,
    quandFini() {
      const suivante = musiques[(musiques.findIndex(s => s.id === id) + 1) % musiques.length];
      lancerAmbiance(suivante.id);
    },
  });
  noter(`Ambiance : ${nomDuSon(id)}`);
  afficherAmbiance();
}

function basculerAmbiance() {
  if (Sons.ambianceEnCours()) Sons.arreterAmbiance();
  else lancerAmbiance(reglages.ambiance);
  afficherAmbiance();
}

function afficherAmbiance() {
  const id = Sons.ambianceEnCours();
  $('#amb-actuelle').textContent = id ? `En cours : ${nomDuSon(id)}` : 'Aucune musique en cours';
  $('#b-ambiance').textContent = id ? "Arrêter l'ambiance" : "Lancer l'ambiance";
}

// ---------- Bibliothèque de sons ----------

function bouton(texte, titre, action) {
  const b = document.createElement('button');
  b.textContent = texte;
  b.title = titre;
  b.onclick = action;
  return b;
}

function ligneSon(son, cle) {
  const li = document.createElement('li');
  const nom = document.createElement('span');
  nom.className = 'nom';
  nom.textContent = son.nom;
  nom.title = son.nom;
  li.append(
    bouton('▶', son.cat === 'ambiance' ? 'Lancer comme ambiance' : 'Jouer', () =>
      son.cat === 'ambiance' ? lancerAmbiance(son.id) : Sons.jouer(son.id)),
    nom,
  );
  if (cle) {
    const choix = document.createElement('input');
    choix.type = 'radio';
    choix.name = `defaut-${son.cat}`;
    choix.title = 'Son utilisé par défaut';
    choix.checked = reglages[cle] === son.id;
    choix.onchange = () => {
      reglages[cle] = son.id;
      sauver();
    };
    li.append(choix);
  }
  if (son.fichier) {
    nom.ondblclick = () => renommer(son);
    li.append(bouton('✕', 'Supprimer', () => supprimerSon(son)));
  }
  return li;
}

function afficherSons() {
  for (const [cat, cle] of Object.entries(CATEGORIES)) {
    $(`.cat[data-cat="${cat}"] ul`).replaceChildren(...sons.filter(s => s.cat === cat).map(s => ligneSon(s, cle)));
  }
  const select = $('[data-reglage="sonAvantAnnonce"]');
  select.replaceChildren(
    new Option('Aucun', ''),
    ...sons.filter(s => s.cat !== 'ambiance').map(s => new Option(s.nom, s.id)),
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
    // Le premier vrai son importé remplace le son généré par défaut.
    const cle = CATEGORIES[cat];
    if (cle && reglages[cle].startsWith('synth:')) reglages[cle] = son.id;
  }
  sauver();
  afficherSons();
}

async function renommer(son) {
  const nom = prompt('Nouveau nom :', son.nom)?.trim();
  if (!nom) return;
  son.nom = nom;
  await Base.ecrire(son);
  afficherSons();
  afficherAmbiance();
}

async function supprimerSon(son) {
  if (!confirm(`Supprimer « ${son.nom} » de la bibliothèque ?`)) return;
  await Base.supprimer(son.id);
  if (Sons.ambianceEnCours() === son.id) Sons.arreterAmbiance();
  Sons.oublier(son.id);
  sons = sons.filter(s => s !== son);
  for (const cle of ['screamer', 'sonIndice', 'ambiance', 'sonAvantAnnonce']) {
    if (reglages[cle] === son.id) reglages[cle] = DEFAUTS[cle];
  }
  sauver();
  afficherSons();
  afficherAmbiance();
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
      let valeur = champ.value;
      if (champ.type === 'checkbox') valeur = champ.checked;
      if (champ.type === 'range' || champ.type === 'number') valeur = Number(champ.value);
      const invalide = (champ.type === 'number' && !(valeur >= Number(champ.min)))
        || (champ.type === 'datetime-local' && !valeur);
      if (invalide) return afficherValeur(champ);
      reglages[champ.dataset.reglage] = valeur;
      sauver();
      reglagesModifies();
    });
  });
}

function reglagesModifies() {
  derniereAnnonce = null; // les horaires ont pu changer : on se recale sans annoncer
  Sons.volumes(reglages.volumeEffets, reglages.volumeAmbiance);
  $('#l-penalite').textContent = `−${reglages.minutesPenalite} min`;
  boucle();
}

function afficherJournal() {
  $('#journal').replaceChildren(...partie.journal.map(({ t, message }) => {
    const li = document.createElement('li');
    const quand = document.createElement('time');
    quand.textContent = new Date(t).toLocaleTimeString('fr-FR');
    li.append(quand, message);
    return li;
  }));
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
  Sons.reveiller();
  document.addEventListener('pointerdown', Sons.reveiller, true);
  try {
    const importes = (await Base.tous()).sort((a, b) => a.ajoute - b.ajoute);
    importes.forEach(son => Sons.enregistrer(son.id, son.fichier));
    sons.push(...importes);
  } catch (erreur) {
    noter(`Impossible de relire les sons importés : ${erreur?.message ?? erreur}`);
  }

  lierReglages();
  afficherSons();
  remplirVoix();
  window.speechSynthesis?.addEventListener('voiceschanged', remplirVoix);
  afficherJournal();
  afficherAmbiance();
  reglagesModifies();

  $('#b-ecran').onclick = ouvrirEcran;
  $('#b-penalite').onclick = penalite;
  $('#b-annuler').onclick = annulerPenalite;
  $('#b-indice').onclick = indice;
  $('#b-annonce').onclick = annoncer;
  $('#b-stop').onclick = toutCouper;
  $('#b-ambiance').onclick = basculerAmbiance;
  $('#b-demarrer').onclick = demarrerMaintenant;
  $('#b-reinitialiser').onclick = reinitialiser;
  document.querySelectorAll('.cat input[type="file"]').forEach(champ => {
    champ.onchange = () => {
      importer(champ.closest('.cat').dataset.cat, [...champ.files]);
      champ.value = '';
    };
  });

  // Empêche l'ordinateur de se mettre en veille tant que la régie est affichée.
  const resterEveille = () => navigator.wakeLock?.request('screen').catch(() => {});
  resterEveille();
  document.addEventListener('visibilitychange', () => document.visibilityState === 'visible' && resterEveille());

  lancerHorloge();
}

demarrer();
