'use strict';
// Moteur audio de la régie. Chaque son est un lecteur audio dont on règle le volume :
// sons ponctuels (screamers, rires…) et couches de fond sonore qui tournent en boucle,
// plusieurs à la fois, baissées automatiquement pendant les annonces et les screamers.

const Sons = (() => {
  const urls = new Map(); // id du son -> URL du fichier
  const enCours = new Map(); // numéro -> { id, audio, arreter } : sons ponctuels en cours
  let numero = 0;
  const couches = new Map(); // id -> { audio, volume } : fond sonore en cours
  let volEffets = 1;
  let volFond = 0.7;
  let attenuations = 0;
  let actif = false;

  const borne = v => Math.min(1, Math.max(0, v));
  const volumeCouche = couche => borne(volFond * couche.volume * (attenuations > 0 ? 0.25 : 1));

  function fondu(audio, cible, ms, puis) {
    clearInterval(audio.fondu);
    const depart = audio.volume;
    const debut = performance.now();
    audio.fondu = setInterval(() => {
      const k = Math.min(1, (performance.now() - debut) / ms);
      audio.volume = borne(depart + (cible - depart) * k);
      if (k === 1) {
        clearInterval(audio.fondu);
        puis?.();
      }
    }, 40);
  }

  // Petit fichier silencieux pour vérifier que le navigateur autorise le son.
  function urlSilence() {
    const n = 800;
    const vue = new DataView(new ArrayBuffer(44 + n));
    const texte = (position, mot) => [...mot].forEach((c, i) => vue.setUint8(position + i, c.charCodeAt(0)));
    texte(0, 'RIFF');
    vue.setUint32(4, 36 + n, true);
    texte(8, 'WAVEfmt ');
    vue.setUint32(16, 16, true);
    vue.setUint16(20, 1, true);
    vue.setUint16(22, 1, true);
    vue.setUint32(24, 8000, true);
    vue.setUint32(28, 8000, true);
    vue.setUint16(32, 1, true);
    vue.setUint16(34, 8, true);
    texte(36, 'data');
    vue.setUint32(40, n, true);
    for (let i = 0; i < n; i++) vue.setUint8(44 + i, 128);
    return URL.createObjectURL(new Blob([vue], { type: 'audio/wav' }));
  }
  const silence = urlSilence();

  function reveiller() {
    couches.forEach(c => c.audio.paused && c.audio.play().catch(() => {}));
    if (!actif) new Audio(silence).play().then(() => (actif = true), () => {});
  }

  // Joue un son une fois ; la promesse se résout quand il est fini.
  function jouer(id) {
    return new Promise(fin => {
      if (!urls.has(id)) return fin();
      const audio = new Audio(urls.get(id));
      audio.volume = borne(volEffets);
      const cle = ++numero;
      const arreter = () => {
        audio.pause();
        enCours.delete(cle);
        fin();
      };
      audio.onended = arreter;
      audio.onerror = arreter;
      enCours.set(cle, { id, audio, arreter });
      audio.play().then(() => (actif = true), arreter);
    });
  }

  function demarrerCouche(id, volume = 1) {
    if (couches.has(id) || !urls.has(id)) return;
    const audio = new Audio(urls.get(id));
    audio.loop = true;
    audio.volume = 0;
    const couche = { audio, volume };
    couches.set(id, couche);
    audio.play().then(() => (actif = true), () => {});
    fondu(audio, volumeCouche(couche), 2500);
  }

  function arreterCouche(id) {
    const couche = couches.get(id);
    if (!couche) return;
    couches.delete(id);
    fondu(couche.audio, 0, 1500, () => couche.audio.pause());
  }

  function appliquerFond(ms) {
    couches.forEach(couche => fondu(couche.audio, volumeCouche(couche), ms));
  }

  return {
    actif: () => actif,
    reveiller,
    enregistrer(id, source) {
      urls.set(id, typeof source === 'string' ? source : URL.createObjectURL(source));
    },
    oublier(id) {
      arreterCouche(id);
      if (urls.get(id)?.startsWith('blob:')) URL.revokeObjectURL(urls.get(id));
      urls.delete(id);
    },
    jouer,
    demarrerCouche,
    arreterCouche,
    sonsEnCours: () => [...enCours].map(([cle, { id, audio }]) => ({ cle, id, position: audio.currentTime, duree: audio.duration })),
    arreterSon: cle => enCours.get(cle)?.arreter(),
    coucheActive: id => couches.has(id),
    couchesActives: () => [...couches.keys()],
    volumeDeCouche(id, volume) {
      const couche = couches.get(id);
      if (!couche) return;
      couche.volume = volume;
      clearInterval(couche.audio.fondu);
      couche.audio.volume = volumeCouche(couche);
    },
    arreterFond() {
      [...couches.keys()].forEach(arreterCouche);
    },
    toutCouper() {
      [...enCours.values()].forEach(son => son.arreter());
      [...couches.keys()].forEach(arreterCouche);
    },
    volumes(effets, fond) {
      volEffets = effets;
      volFond = fond;
      appliquerFond(300);
    },
    attenuer(oui) {
      attenuations = Math.max(0, attenuations + (oui ? 1 : -1));
      appliquerFond(700);
    },
  };
})();
