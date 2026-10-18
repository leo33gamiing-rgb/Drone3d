'use strict';
// Moteur audio de la régie : joue les fichiers importés, et des sons de secours
// générés par l'ordinateur pour que l'app fonctionne avant d'avoir importé de vrais sons.

function bruit(c, secondes) {
  const tampon = c.createBuffer(1, Math.ceil(c.sampleRate * secondes), c.sampleRate);
  const donnees = tampon.getChannelData(0);
  for (let i = 0; i < donnees.length; i++) donnees[i] = Math.random() * 2 - 1;
  return tampon;
}

function saturation(c, force) {
  const courbe = new Float32Array(1024);
  for (let i = 0; i < courbe.length; i++) {
    const x = (i / (courbe.length - 1)) * 2 - 1;
    courbe[i] = ((1 + force) * x) / (1 + force * Math.abs(x));
  }
  const ws = c.createWaveShaper();
  ws.curve = courbe;
  return ws;
}

function coupSourd(c, sortie, t, volume) {
  const o = c.createOscillator();
  const g = c.createGain();
  o.type = 'triangle';
  o.frequency.setValueAtTime(110, t);
  o.frequency.exponentialRampToValueAtTime(32, t + 0.3);
  g.gain.setValueAtTime(0, t);
  g.gain.linearRampToValueAtTime(volume, t + 0.01);
  g.gain.exponentialRampToValueAtTime(0.001, t + 0.35);
  o.connect(g).connect(sortie);
  o.start(t);
  o.stop(t + 0.36);
}

function gemissement(c, sortie) {
  const t = c.currentTime;
  const duree = 4 + Math.random() * 4;
  const f = 280 + Math.random() * 450;
  const o = c.createOscillator();
  const vibrato = c.createOscillator();
  const profondeur = c.createGain();
  const g = c.createGain();
  const espace = c.createStereoPanner();
  o.type = 'triangle';
  o.frequency.setValueAtTime(f, t);
  o.frequency.linearRampToValueAtTime(f * (0.8 + Math.random() * 0.15), t + duree);
  vibrato.frequency.value = 4 + Math.random() * 3;
  profondeur.gain.value = f * 0.012;
  vibrato.connect(profondeur).connect(o.frequency);
  g.gain.setValueAtTime(0, t);
  g.gain.linearRampToValueAtTime(0.06, t + duree * 0.4);
  g.gain.linearRampToValueAtTime(0, t + duree);
  espace.pan.value = Math.random() * 2 - 1;
  o.connect(g).connect(espace).connect(sortie);
  o.start(t);
  vibrato.start(t);
  o.stop(t + duree);
  vibrato.stop(t + duree);
}

// Sons ponctuels générés : chacun joue sur `sortie` et renvoie sa durée en secondes.
const GENERATEURS = {
  cri(c, sortie) {
    const t = c.currentTime;
    const duree = 2.4;
    const enveloppe = c.createGain();
    const sat = saturation(c, 30);
    enveloppe.gain.setValueAtTime(0, t);
    enveloppe.gain.linearRampToValueAtTime(0.6, t + 0.02);
    enveloppe.gain.setValueAtTime(0.6, t + duree - 0.6);
    enveloppe.gain.exponentialRampToValueAtTime(0.001, t + duree);
    sat.connect(enveloppe).connect(sortie);
    // Plusieurs « voix » stridentes qui tremblent et montent.
    [620, 655, 930, 1390].forEach((f, i) => {
      const o = c.createOscillator();
      const vibrato = c.createOscillator();
      const profondeur = c.createGain();
      const g = c.createGain();
      o.type = 'sawtooth';
      o.frequency.setValueAtTime(f * 0.5, t);
      o.frequency.exponentialRampToValueAtTime(f, t + 0.12);
      o.frequency.linearRampToValueAtTime(f * 1.3, t + duree);
      vibrato.frequency.value = 7 + i * 2.3;
      profondeur.gain.value = f * 0.05;
      g.gain.value = 0.15;
      vibrato.connect(profondeur).connect(o.frequency);
      o.connect(g).connect(sat);
      o.start(t);
      vibrato.start(t);
      o.stop(t + duree);
      vibrato.stop(t + duree);
    });
    // Souffle rauque.
    const souffle = c.createBufferSource();
    const filtre = c.createBiquadFilter();
    const gs = c.createGain();
    souffle.buffer = bruit(c, duree);
    filtre.type = 'bandpass';
    filtre.Q.value = 1.2;
    filtre.frequency.setValueAtTime(1000, t);
    filtre.frequency.exponentialRampToValueAtTime(3800, t + duree);
    gs.gain.value = 0.6;
    souffle.connect(filtre).connect(gs).connect(sat);
    souffle.start(t);
    coupSourd(c, sortie, t, 0.5);
    return duree;
  },

  carillon(c, sortie) {
    const t = c.currentTime;
    const bus = c.createGain();
    const echo = c.createDelay(1);
    const etouffe = c.createBiquadFilter();
    const retour = c.createGain();
    bus.gain.value = 0.5;
    echo.delayTime.value = 0.37;
    etouffe.type = 'lowpass';
    etouffe.frequency.value = 2200;
    retour.gain.value = 0.45;
    bus.connect(sortie);
    bus.connect(echo);
    echo.connect(etouffe).connect(retour).connect(echo);
    etouffe.connect(sortie);
    // Boîte à musique désaccordée qui ralentit, comme si elle s'épuisait.
    let instant = t;
    [76, 79, 83, 82, 76, 79, 74, 75].forEach((note, i) => {
      const f = 440 * 2 ** ((note - 69) / 12) * (1 + (Math.random() - 0.5) * 0.015);
      [[1, 0.35, 1.4], [2.01, 0.12, 0.6], [3.98, 0.06, 0.3]].forEach(([harmonique, volume, tenue]) => {
        const o = c.createOscillator();
        const g = c.createGain();
        o.frequency.value = f * harmonique;
        g.gain.setValueAtTime(0, instant);
        g.gain.linearRampToValueAtTime(volume, instant + 0.005);
        g.gain.exponentialRampToValueAtTime(0.0001, instant + tenue);
        o.connect(g).connect(bus);
        o.start(instant);
        o.stop(instant + tenue);
      });
      instant += 0.3 + i * 0.045;
    });
    return instant - t + 2;
  },

  glas(c, sortie) {
    const t = c.currentTime;
    // Partiels inharmoniques d'une grosse cloche : [rapport, volume, durée].
    [[0.5, 0.5, 7], [1, 0.45, 5], [1.19, 0.3, 4], [1.5, 0.25, 3.5], [2, 0.2, 3],
      [2.52, 0.15, 2.2], [2.66, 0.12, 2], [3.01, 0.1, 1.6], [4.07, 0.06, 1]].forEach(([rapport, volume, duree]) => {
      const o = c.createOscillator();
      const g = c.createGain();
      o.frequency.value = 98 * rapport;
      g.gain.setValueAtTime(0, t);
      g.gain.linearRampToValueAtTime(volume * 0.45, t + 0.01);
      g.gain.exponentialRampToValueAtTime(0.0001, t + duree);
      o.connect(g).connect(sortie);
      o.start(t);
      o.stop(t + duree);
    });
    return 7;
  },

  coeur(c, sortie) {
    const t = c.currentTime;
    let instant = t;
    for (let i = 0; i < 8; i++) {
      coupSourd(c, sortie, instant, 0.9);
      coupSourd(c, sortie, instant + 0.28, 0.6);
      instant += 1 - i * 0.06; // le cœur s'accélère
    }
    return instant - t + 0.5;
  },
};

// Ambiances générées : chacune démarre sur `sortie` et renvoie une fonction d'arrêt.
const AMBIANCES = {
  nappe(c, sortie) {
    const sources = [];
    const demarrer = source => {
      source.start();
      sources.push(source);
      return source;
    };
    // Grondement grave et dissonant, filtré lentement.
    const grave = c.createBiquadFilter();
    const modulation = c.createGain();
    grave.type = 'lowpass';
    grave.frequency.value = 160;
    grave.Q.value = 6;
    grave.connect(sortie);
    const lfo = demarrer(c.createOscillator());
    lfo.frequency.value = 0.04;
    modulation.gain.value = 80;
    lfo.connect(modulation).connect(grave.frequency);
    [41.2, 43.7, 61.7, 83.1].forEach(f => {
      const o = c.createOscillator();
      const g = c.createGain();
      o.type = 'sawtooth';
      o.frequency.value = f;
      g.gain.value = 0.15;
      o.connect(g).connect(grave);
      demarrer(o);
    });
    // Vent qui siffle.
    const vent = c.createBufferSource();
    const sifflement = c.createBiquadFilter();
    const lfoVent = c.createOscillator();
    const amplitudeVent = c.createGain();
    const gv = c.createGain();
    vent.buffer = bruit(c, 5);
    vent.loop = true;
    sifflement.type = 'bandpass';
    sifflement.Q.value = 9;
    sifflement.frequency.value = 600;
    lfoVent.frequency.value = 0.06;
    amplitudeVent.gain.value = 400;
    lfoVent.connect(amplitudeVent).connect(sifflement.frequency);
    gv.gain.value = 0.35;
    vent.connect(sifflement).connect(gv).connect(sortie);
    demarrer(vent);
    demarrer(lfoVent);
    // Gémissements lointains, au hasard.
    const minuterie = setInterval(() => Math.random() < 0.45 && gemissement(c, sortie), 7000);
    return () => {
      clearInterval(minuterie);
      sources.forEach(source => source.stop());
    };
  },
};

const Sons = (() => {
  let ctx = null;
  let busEffets;
  let busAmbiance;
  let volEffets = 1;
  let volAmbiance = 0.5;
  let attenuations = 0;
  const urls = new Map(); // id du son -> URL du fichier importé
  const enCours = new Set(); // fonctions d'arrêt des sons ponctuels en cours
  let ambiance = null; // { id, audio, arreter }

  function contexte() {
    if (!ctx) {
      ctx = new AudioContext();
      busEffets = ctx.createGain();
      busAmbiance = ctx.createGain();
      busEffets.connect(ctx.destination);
      busAmbiance.connect(ctx.destination);
      appliquerVolumes();
    }
    if (ctx.state === 'suspended') ctx.resume().catch(() => {});
    return ctx;
  }

  function appliquerVolumes() {
    if (!ctx) return;
    const t = ctx.currentTime;
    busEffets.gain.setTargetAtTime(volEffets, t, 0.05);
    // L'ambiance baisse pendant les annonces et les screamers.
    busAmbiance.gain.setTargetAtTime(volAmbiance * (attenuations > 0 ? 0.25 : 1), t, 0.25);
  }

  // Joue un son une fois ; la promesse se résout quand il est fini.
  function jouer(id) {
    return new Promise(fin => {
      const c = contexte();
      const sortie = c.createGain();
      let audio = null;
      const arreter = () => {
        audio?.pause();
        sortie.disconnect();
        enCours.delete(arreter);
        fin();
      };
      sortie.connect(busEffets);
      enCours.add(arreter);
      if (id?.startsWith('synth:') && GENERATEURS[id.slice(6)]) {
        setTimeout(arreter, GENERATEURS[id.slice(6)](c, sortie) * 1000);
      } else if (urls.has(id)) {
        audio = new Audio(urls.get(id));
        c.createMediaElementSource(audio).connect(sortie);
        audio.onended = arreter;
        audio.onerror = arreter;
        audio.play().catch(arreter);
      } else {
        arreter();
      }
    });
  }

  function lancerAmbiance(id, { boucle = true, quandFini } = {}) {
    arreterAmbiance();
    const c = contexte();
    const sortie = c.createGain();
    let arretGenere = null;
    let audio = null;
    if (id?.startsWith('synth:') && AMBIANCES[id.slice(6)]) {
      arretGenere = AMBIANCES[id.slice(6)](c, sortie);
    } else if (urls.has(id)) {
      audio = new Audio(urls.get(id));
      audio.loop = boucle;
      c.createMediaElementSource(audio).connect(sortie);
      audio.onended = () => {
        if (ambiance?.audio !== audio) return;
        ambiance = null;
        quandFini?.();
      };
      audio.play().catch(() => {});
    } else {
      return;
    }
    sortie.connect(busAmbiance);
    sortie.gain.setValueAtTime(0, c.currentTime);
    sortie.gain.linearRampToValueAtTime(1, c.currentTime + 2); // fondu d'entrée
    ambiance = {
      id,
      audio,
      arreter() {
        sortie.gain.cancelScheduledValues(c.currentTime);
        sortie.gain.setTargetAtTime(0, c.currentTime, 0.4); // fondu de sortie
        setTimeout(() => {
          audio?.pause();
          arretGenere?.();
          sortie.disconnect();
        }, 2000);
      },
    };
  }

  function arreterAmbiance() {
    ambiance?.arreter();
    ambiance = null;
  }

  return {
    actif: () => ctx?.state === 'running',
    reveiller: contexte,
    enregistrer(id, fichier) {
      urls.set(id, URL.createObjectURL(fichier));
    },
    oublier(id) {
      if (urls.has(id)) URL.revokeObjectURL(urls.get(id));
      urls.delete(id);
    },
    jouer,
    lancerAmbiance,
    arreterAmbiance,
    ambianceEnCours: () => ambiance?.id ?? null,
    toutCouper() {
      [...enCours].forEach(arreter => arreter());
      arreterAmbiance();
    },
    volumes(effets, amb) {
      volEffets = effets;
      volAmbiance = amb;
      appliquerVolumes();
    },
    attenuer(oui) {
      attenuations = Math.max(0, attenuations + (oui ? 1 : -1));
      appliquerVolumes();
    },
  };
})();
