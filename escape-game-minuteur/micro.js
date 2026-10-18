'use strict';
// Micro du maître du jeu : la voix est déformée en direct (plus grave, métallique, écho…)
// et sort sur les haut-parleurs. On ne l'entend que pendant qu'on « parle » (bouton maintenu ou verrouillé).

// Effets de voix. hauteur : demi-tons ; anneau : modulation métallique (Hz, dosage) ;
// distorsion : saturation ; echo : [délai s, retour] ; reverb : dosage ; filtres en Hz ; gain : équilibre des volumes.
const EFFETS_VOIX = {
  demon: { nom: 'Démon (très grave)', hauteur: -7, distorsion: 4, reverb: 0.35, passeBas: 4500 },
  monstre: { nom: 'Monstre (grave et grondant)', hauteur: -11, anneau: [32, 0.45], distorsion: 8, reverb: 0.3, passeBas: 3500, gain: 0.7 },
  possede: { nom: 'Possédé (voix métallique)', hauteur: -4, anneau: [55, 0.7], reverb: 0.3, gain: 4 },
  fantome: { nom: 'Fantôme (écho lointain)', hauteur: -2, echo: [0.32, 0.45], reverb: 0.6, passeHaut: 300, gain: 2 },
  outreTombe: { nom: "Voix d'outre-tombe", hauteur: -5, echo: [0.5, 0.35], reverb: 0.75, passeHaut: 250, passeBas: 3000, gain: 1.8 },
  normale: { nom: 'Voix normale (sans effet)', hauteur: 0, reverb: 0, gain: 2.2 },
};

const Micro = (() => {
  let ctx = null;
  let flux = null;
  let source = null;
  let analyseur = null;
  let chaine = null; // nœuds de l'effet en cours
  let sortie = null; // volume général du micro (0 quand on ne parle pas)
  let volume = 1;
  let enDirect = false;
  let effet = 'demon';

  // Décaleur de hauteur par lignes à retard (technique « Jungle » de Chris Wilson, sans AudioWorklet).
  function decaleur(demiTons) {
    const entree = ctx.createGain();
    const sortieDecaleur = ctx.createGain();
    const actif = 0.1;
    const fondu = 0.05;
    const taux = ctx.sampleRate;
    const n1 = Math.round(actif * taux);
    const n = n1 + Math.round((actif - 2 * fondu) * taux);
    const rampe = monte => {
      const tampon = ctx.createBuffer(1, n, taux);
      const d = tampon.getChannelData(0);
      for (let i = 0; i < n1; i++) d[i] = monte ? (n1 - i) / n : i / n1;
      return tampon;
    };
    const fenetre = ctx.createBuffer(1, n, taux);
    const f = fenetre.getChannelData(0);
    const nf = Math.round(fondu * taux);
    for (let i = 0; i < n1; i++) f[i] = i < nf ? Math.sqrt(i / nf) : i >= n1 - nf ? Math.sqrt(1 - (i - (n1 - nf)) / nf) : 1;

    const rapport = 2 ** (demiTons / 12);
    const multiplicateur = 2 * (rapport - 1); // -1 = une octave plus bas
    const tampon = rampe(multiplicateur > 0);
    const depart = ctx.currentTime + 0.05;
    const sources = [];
    for (const decalage of [0, actif - fondu]) {
      const modulation = ctx.createBufferSource();
      modulation.buffer = tampon;
      modulation.loop = true;
      const ampleur = ctx.createGain();
      ampleur.gain.value = 0.5 * 0.1 * Math.abs(multiplicateur);
      const retard = ctx.createDelay(1);
      modulation.connect(ampleur).connect(retard.delayTime);
      const volet = ctx.createBufferSource();
      volet.buffer = fenetre;
      volet.loop = true;
      const mixage = ctx.createGain();
      mixage.gain.value = 0;
      volet.connect(mixage.gain);
      entree.connect(retard).connect(mixage).connect(sortieDecaleur);
      modulation.start(depart + decalage);
      volet.start(depart + decalage);
      sources.push(modulation, volet);
    }
    return { entree, sortie: sortieDecaleur, arreter: () => sources.forEach(s => s.stop()) };
  }

  function salle(duree) {
    const tampon = ctx.createBuffer(2, Math.round(duree * ctx.sampleRate), ctx.sampleRate);
    for (let c = 0; c < 2; c++) {
      const d = tampon.getChannelData(c);
      for (let i = 0; i < d.length; i++) d[i] = (Math.random() * 2 - 1) * Math.pow(1 - i / d.length, 3);
    }
    const convolution = ctx.createConvolver();
    convolution.buffer = tampon;
    return convolution;
  }

  function filtre(type, frequence) {
    const f = ctx.createBiquadFilter();
    f.type = type;
    f.frequency.value = frequence;
    return f;
  }

  function construire() {
    chaine?.arreter();
    chaine?.noeuds.forEach(noeud => noeud.disconnect());
    const reglage = EFFETS_VOIX[effet] ?? EFFETS_VOIX.demon;
    const noeuds = [];
    const garder = noeud => (noeuds.push(noeud), noeud);
    let bout = garder(filtre('highpass', reglage.passeHaut ?? 90));
    source.disconnect();
    source.connect(analyseur);
    source.connect(bout);
    const relier = noeud => (bout.connect(noeud), (bout = garder(noeud)));
    let arreter = () => {};
    if (reglage.hauteur) {
      const d = decaleur(reglage.hauteur);
      bout.connect(d.entree);
      bout = garder(d.sortie);
      noeuds.push(d.entree);
      arreter = d.arreter;
    }
    if (reglage.anneau) {
      const [frequence, dosage] = reglage.anneau;
      const metal = ctx.createGain();
      metal.gain.value = 0;
      const oscillateur = ctx.createOscillator();
      oscillateur.frequency.value = frequence;
      oscillateur.connect(metal.gain);
      oscillateur.start();
      const sec = garder(ctx.createGain());
      sec.gain.value = 1 - dosage;
      const mouille = garder(ctx.createGain());
      mouille.gain.value = dosage;
      const somme = garder(ctx.createGain());
      bout.connect(sec).connect(somme);
      bout.connect(metal).connect(mouille).connect(somme);
      noeuds.push(metal);
      bout = somme;
      const precedent = arreter;
      arreter = () => (precedent(), oscillateur.stop());
    }
    if (reglage.distorsion) {
      const saturation = ctx.createWaveShaper();
      const courbe = new Float32Array(1024);
      for (let i = 0; i < courbe.length; i++) {
        const x = (i / (courbe.length - 1)) * 2 - 1;
        courbe[i] = Math.tanh(reglage.distorsion * x) / Math.tanh(reglage.distorsion);
      }
      saturation.curve = courbe;
      relier(saturation);
    }
    if (reglage.passeBas) relier(filtre('lowpass', reglage.passeBas));
    const melange = garder(ctx.createGain());
    melange.gain.value = reglage.gain ?? 1;
    bout.connect(melange);
    if (reglage.echo) {
      const [delai, retour] = reglage.echo;
      const ligne = garder(ctx.createDelay(2));
      ligne.delayTime.value = delai;
      const boucle = garder(ctx.createGain());
      boucle.gain.value = retour;
      bout.connect(ligne).connect(boucle).connect(ligne);
      ligne.connect(melange);
    }
    if (reglage.reverb) {
      const echoSalle = garder(salle(2.5));
      const dosage = garder(ctx.createGain());
      dosage.gain.value = reglage.reverb;
      melange.connect(echoSalle).connect(dosage).connect(sortie);
    }
    melange.connect(sortie);
    chaine = { noeuds, arreter };
  }

  async function activer(appareil = '') {
    ctx ??= new AudioContext({ latencyHint: 'interactive' });
    if (ctx.state === 'suspended') await ctx.resume();
    flux?.getTracks().forEach(piste => piste.stop());
    flux = await navigator.mediaDevices.getUserMedia({
      audio: { deviceId: appareil ? { exact: appareil } : undefined, echoCancellation: true, noiseSuppression: true, autoGainControl: true },
    });
    source?.disconnect();
    source = ctx.createMediaStreamSource(flux);
    analyseur ??= ctx.createAnalyser();
    analyseur.fftSize = 1024;
    if (!sortie) {
      sortie = ctx.createGain();
      sortie.gain.value = 0;
      const limiteur = ctx.createDynamicsCompressor();
      limiteur.threshold.value = -6;
      limiteur.ratio.value = 12;
      sortie.connect(limiteur).connect(ctx.destination);
    }
    construire();
  }

  function parler(oui) {
    if (!sortie) return;
    enDirect = oui;
    sortie.gain.setTargetAtTime(oui ? volume : 0, ctx.currentTime, 0.03);
  }

  return {
    effets: EFFETS_VOIX,
    activer,
    pret: () => Boolean(flux),
    enDirect: () => enDirect,
    effet: () => effet,
    choisirEffet(nom) {
      effet = nom;
      if (source) construire();
    },
    volume(v) {
      volume = v;
      if (enDirect) parler(true);
    },
    parler,
    // Niveau du micro entre 0 et 1, pour la jauge.
    niveau() {
      if (!analyseur) return 0;
      const d = new Float32Array(analyseur.fftSize);
      analyseur.getFloatTimeDomainData(d);
      return Math.min(1, Math.sqrt(d.reduce((s, x) => s + x * x, 0) / d.length) * 4);
    },
    async appareils() {
      const tous = await navigator.mediaDevices.enumerateDevices();
      return tous.filter(a => a.kind === 'audioinput');
    },
  };
})();
