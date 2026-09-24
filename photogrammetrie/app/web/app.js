import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { DRACOLoader } from "three/addons/loaders/DRACOLoader.js";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import { MeshoptDecoder } from "three/addons/libs/meshopt_decoder.module.js";

const $ = (id) => document.getElementById(id);
const EXTENSIONS = [".jpg", ".jpeg", ".png", ".tif", ".tiff", ".heic", ".heif"];
const SPECIAUX = ["gcp_list.txt", "geo.txt"];
const LIBELLES_STATUT = {
  en_attente: "En attente", en_cours: "En cours", termine: "Terminé", erreur: "Erreur", annule: "Annulé",
};
const DESCRIPTION_FICHIERS = {
  "modele_3d.glb": "Modèle 3D texturé (GLB, s'ouvre partout)",
  "modele_3d.obj": "Modèle 3D texturé (OBJ, Blender, logiciels CAO)",
  "nuage_points.laz": "Nuage de points géoréférencé (CloudCompare, QGIS)",
  "nuage_points.ply": "Nuage de points (CloudCompare, MeshLab)",
  "orthophoto.tif": "Orthophoto géoréférencée (QGIS)",
  "mns.tif": "Modèle numérique de surface (altitudes)",
  "rapport_qualite.pdf": "Rapport qualité OpenDroneMap",
  "analyse_photos.json": "Analyse détaillée des photos",
  "journal.log": "Journal complet du calcul",
  "odm_textured_model_geo.mtl": "Matériaux de l'OBJ (à garder avec le .obj et les .png)",
};

let travaux = [];
let selection = null;
let fichiersChoisis = [];

// ---------------------------------------------------------------- Utilitaires

function taille(octets) {
  if (octets > 1e9) return (octets / 1e9).toFixed(1) + " Go";
  if (octets > 1e6) return (octets / 1e6).toFixed(0) + " Mo";
  return Math.max(1, Math.round(octets / 1e3)) + " ko";
}

function dateCourte(iso) {
  return iso ? new Date(iso).toLocaleString("fr-FR", { dateStyle: "short", timeStyle: "short" }) : "";
}

function duree(debut, fin) {
  if (!debut) return "";
  const s = Math.round(((fin ? new Date(fin) : new Date()) - new Date(debut)) / 1000);
  const h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60);
  return h ? `${h} h ${m} min` : m ? `${m} min ${s % 60} s` : `${s} s`;
}

function el(tag, attrs = {}, ...enfants) {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === "class") e.className = v;
    else if (k.startsWith("on")) e.addEventListener(k.slice(2), v);
    else e.setAttribute(k, v);
  }
  for (const c of enfants) if (c != null) e.append(c);
  return e;
}

function accepte(nom) {
  const n = nom.toLowerCase();
  return SPECIAUX.includes(n) || EXTENSIONS.some((ext) => n.endsWith(ext));
}

// ---------------------------------------------------------------- Dépôt des photos

function ajouterFichiers(liste) {
  const connus = new Set(fichiersChoisis.map((f) => f.name + f.size));
  for (const f of liste) {
    if (accepte(f.name) && !connus.has(f.name + f.size)) fichiersChoisis.push(f);
  }
  const photos = fichiersChoisis.filter((f) => !SPECIAUX.includes(f.name.toLowerCase()));
  const extras = fichiersChoisis.length - photos.length;
  const total = fichiersChoisis.reduce((s, f) => s + f.size, 0);
  $("selection").hidden = fichiersChoisis.length === 0;
  $("selection-texte").textContent =
    `${photos.length} photo(s)${extras ? ` + ${extras} fichier(s) de calage` : ""} · ${taille(total)}` +
    (photos.length > 0 && photos.length < 3 ? " · il en faut au moins 3" : "");
  $("lancer").disabled = photos.length < 3;
}

// Parcourt récursivement un dossier glissé-déposé
async function lireEntree(entree) {
  if (entree.isFile) return new Promise((ok) => entree.file((f) => ok([f]), () => ok([])));
  if (!entree.isDirectory) return [];
  const lecteur = entree.createReader();
  const enfants = [];
  for (;;) {
    const lot = await new Promise((ok) => lecteur.readEntries(ok, () => ok([])));
    if (!lot.length) break;
    enfants.push(...lot);
  }
  return (await Promise.all(enfants.map(lireEntree))).flat();
}

function initialiserDepot() {
  const zone = $("zone-depot");
  zone.addEventListener("dragover", (e) => { e.preventDefault(); zone.classList.add("survol"); });
  zone.addEventListener("dragleave", () => zone.classList.remove("survol"));
  zone.addEventListener("drop", async (e) => {
    e.preventDefault();
    zone.classList.remove("survol");
    const entrees = [...e.dataTransfer.items].map((i) => i.webkitGetAsEntry?.()).filter(Boolean);
    if (entrees.length) {
      const dossier = entrees.find((x) => x.isDirectory);
      if (dossier && !$("nom-projet").value) $("nom-projet").value = dossier.name;
      ajouterFichiers((await Promise.all(entrees.map(lireEntree))).flat());
    } else {
      ajouterFichiers(e.dataTransfer.files);
    }
  });
  $("choisir-photos").onclick = () => $("entree-photos").click();
  $("choisir-dossier").onclick = () => $("entree-dossier").click();
  $("entree-photos").onchange = (e) => { ajouterFichiers(e.target.files); e.target.value = ""; };
  $("entree-dossier").onchange = (e) => {
    const premier = e.target.files[0];
    if (premier && !$("nom-projet").value) $("nom-projet").value = premier.webkitRelativePath.split("/")[0];
    ajouterFichiers(e.target.files);
    e.target.value = "";
  };
  $("vider-selection").onclick = () => { fichiersChoisis = []; ajouterFichiers([]); };
  $("lancer").onclick = envoyer;
}

function envoyer() {
  const donnees = new FormData();
  donnees.append("nom", $("nom-projet").value || "Projet");
  for (const f of fichiersChoisis) donnees.append("fichiers", f, f.name);

  const barre = $("envoi");
  barre.hidden = false;
  $("lancer").disabled = true;
  $("lancer").textContent = "Envoi des photos…";

  const xhr = new XMLHttpRequest();
  xhr.open("POST", "/api/travaux");
  xhr.upload.onprogress = (e) => {
    if (e.lengthComputable) barre.firstElementChild.style.width = `${(100 * e.loaded) / e.total}%`;
  };
  xhr.onload = async () => {
    barre.hidden = true;
    barre.firstElementChild.style.width = "0";
    $("lancer").textContent = "Lancer le calcul";
    if (xhr.status >= 300) {
      alert("Erreur : " + (JSON.parse(xhr.responseText || "{}").detail || xhr.status));
      $("lancer").disabled = false;
      return;
    }
    const travail = JSON.parse(xhr.responseText);
    fichiersChoisis = [];
    ajouterFichiers([]);
    $("nom-projet").value = "";
    await rafraichir();
    selectionner(travail.id);
  };
  xhr.onerror = () => {
    alert("L'envoi a échoué : l'application est-elle toujours lancée ?");
    barre.hidden = true;
    $("lancer").disabled = false;
    $("lancer").textContent = "Lancer le calcul";
  };
  xhr.send(donnees);
}

// ---------------------------------------------------------------- Liste et détail

async function rafraichir() {
  try {
    travaux = await (await fetch("/api/travaux")).json();
  } catch {
    $("etat-moteur").textContent = "Application arrêtée";
    $("etat-moteur").className = "pastille ko";
    return;
  }
  afficherListe();
  if (selection) afficherDetail(travaux.find((t) => t.id === selection));
}

function afficherListe() {
  const liste = $("liste-travaux");
  liste.replaceChildren(
    ...travaux.map((t) => {
      const barre = t.statut === "en_cours"
        ? el("div", { class: "barre" }, el("div", { style: `width:${t.progression}%` }))
        : null;
      return el(
        "li",
        { class: t.id === selection ? "actif" : "", onclick: () => selectionner(t.id) },
        el("span", { class: "nom" }, t.nom),
        el("span", { class: `statut ${t.statut}` }, LIBELLES_STATUT[t.statut] || t.statut),
        el("span", { class: "petit" },
          dateCourte(t.cree) + (t.analyse ? ` · ${t.analyse.nb_photos} photos` : "")),
        barre,
      );
    }),
  );
  $("liste-vide").hidden = travaux.length > 0;
}

function selectionner(id) {
  selection = id;
  afficherListe();
  afficherDetail(travaux.find((t) => t.id === id));
  chargerJournal();
}

function tuile(libelle, valeur, oui = false) {
  return el("div", { class: "tuile" },
    el("span", { class: "petit" }, libelle),
    el("span", { class: "valeur" + (oui ? " oui" : "") }, valeur));
}

function afficherDetail(t) {
  $("aucun-detail").hidden = !!t;
  $("detail").hidden = !t;
  if (!t) return;

  $("d-nom").textContent = t.nom;
  const dates = [`Créé le ${dateCourte(t.cree)}`];
  if (t.debut) dates.push(`durée ${duree(t.debut, t.fin)}`);
  dates.push(t.source === "web" ? "envoyé depuis le navigateur" : "déposé dans le dossier");
  $("d-dates").textContent = dates.join(" · ");

  const actif = t.statut === "en_cours" || t.statut === "en_attente";
  $("d-annuler").hidden = !actif;
  $("d-supprimer").hidden = actif;
  $("d-etape").textContent = t.etape;
  $("d-pct").textContent = `${t.progression} %`;
  $("d-barre").style.width = `${t.progression}%`;
  $("d-barre").style.background = t.statut === "erreur" ? "var(--erreur)" : t.statut === "termine" ? "var(--succes)" : "";

  $("d-erreur").hidden = !t.erreur;
  $("d-erreur").textContent = t.erreur || "";

  const a = t.analyse;
  $("d-analyse").hidden = !a;
  if (a) {
    const sources = { drone: "Drone", telephone: "Téléphone", mixte: "Drone + téléphone", inconnu: "Appareil photo" };
    $("d-analyse").replaceChildren(
      tuile("Photos", a.nb_photos),
      tuile("GPS", `${a.nb_gps}/${a.nb_photos}`, a.georeferencee),
      tuile("RTK fixe", a.nb_rtk_fixe ? `${a.nb_rtk_fixe}/${a.nb_photos}` : "Non", a.rtk),
      tuile("Points de contrôle", a.gcp ? "Oui" : "Non", a.gcp),
      tuile("Source", sources[a.source] || a.source),
    );
    const appareils = Object.entries(a.appareils).map(([n, c]) => `${n} (${c})`).join(", ");
    $("d-analyse").append(el("p", { class: "petit", style: "grid-column:1/-1;margin:0" }, `Appareils : ${appareils}`));
  }

  const p = t.profil;
  $("d-profil").hidden = !p;
  if (p) {
    $("p-libelle").textContent = `${p.libelle} (niveau ${p.niveau}/5)`;
    $("p-fiabilite").textContent = `${p.fiabilite}/100`;
    const jauge = $("p-jauge");
    jauge.style.width = `${p.fiabilite}%`;
    jauge.style.background = p.fiabilite >= 70 ? "var(--succes)" : p.fiabilite >= 40 ? "var(--attention)" : "var(--erreur)";
    $("p-precision").textContent = p.precision;
    $("p-duree").textContent = `Durée estimée : ${p.duree_estimee}`;
    remplirListe($("p-avertissements"), p.avertissements);
    remplirListe($("p-conseils"), p.conseils.map((c) => "💡 " + c));
  }

  const fichiers = [...t.sorties];
  if (t.statut === "termine" || t.statut === "erreur") fichiers.push("analyse_photos.json", "journal.log");
  $("d-fichiers").hidden = fichiers.length === 0;
  $("liste-fichiers").replaceChildren(
    ...fichiers.map((f) =>
      el("li", {},
        el("a", { href: `/resultats/${t.id}/${f}`, download: f }, f),
        el("span", { class: "petit" }, DESCRIPTION_FICHIERS[f] || ""))),
  );
  if (t.statut === "termine") {
    $("liste-fichiers").prepend(
      el("li", {},
        el("a", { href: `/resultats/${t.id}.zip`, download: "" }, el("strong", {}, "Tout télécharger (.zip)")),
        el("span", { class: "petit" }, "Tous les fichiers, textures comprises")));
  }

  const glb = t.sorties.includes("modele_3d.glb");
  $("d-visu").hidden = !glb;
  if (glb) visionneuse.charger(`/resultats/${t.id}/modele_3d.glb`, t.id, t.simulation);
}

function remplirListe(ul, elements) {
  ul.hidden = !elements.length;
  ul.replaceChildren(...elements.map((x) => el("li", {}, x)));
}

async function chargerJournal() {
  if (!selection || !$("d-journal").open) return;
  const texte = await (await fetch(`/api/travaux/${selection}/journal?lignes=300`)).text();
  const pre = $("journal-texte");
  const enBas = pre.scrollTop + pre.clientHeight >= pre.scrollHeight - 20;
  pre.textContent = texte || "(vide)";
  if (enBas) pre.scrollTop = pre.scrollHeight;
}

function initialiserDetail() {
  $("d-annuler").onclick = async () => {
    if (!confirm("Annuler ce calcul ?")) return;
    await fetch(`/api/travaux/${selection}/annuler`, { method: "POST" });
    rafraichir();
  };
  $("d-supprimer").onclick = async () => {
    if (!confirm("Supprimer ce calcul et tous ses résultats ?")) return;
    await fetch(`/api/travaux/${selection}`, { method: "DELETE" });
    selection = null;
    rafraichir();
  };
  $("d-journal").addEventListener("toggle", chargerJournal);
}

// ---------------------------------------------------------------- Visionneuse 3D

const visionneuse = {
  url: null,
  scene: null,
  modele: null,

  initialiser() {
    const conteneur = $("v-canvas");
    this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    this.renderer.setPixelRatio(window.devicePixelRatio);
    this.renderer.outputColorSpace = THREE.SRGBColorSpace;
    conteneur.append(this.renderer.domElement);
    this.scene = new THREE.Scene();
    this.scene.add(new THREE.HemisphereLight(0xffffff, 0x444444, 2.2));
    const soleil = new THREE.DirectionalLight(0xffffff, 1.2);
    soleil.position.set(1, 2, 1.5);
    this.scene.add(soleil);
    this.camera = new THREE.PerspectiveCamera(45, 1, 0.01, 1e6);
    this.controles = new OrbitControls(this.camera, this.renderer.domElement);
    this.controles.enableDamping = true;
    // Modèles compressés (Draco pour OpenDroneMap, Meshopt pour d'autres outils)
    const draco = new DRACOLoader().setDecoderPath("/static/vendor/addons/libs/draco/");
    this.chargeur = new GLTFLoader().setDRACOLoader(draco).setMeshoptDecoder(MeshoptDecoder);
    new ResizeObserver(() => this.redimensionner()).observe(conteneur);
    const boucle = () => {
      requestAnimationFrame(boucle);
      this.controles.update();
      this.renderer.render(this.scene, this.camera);
    };
    boucle();
    $("v-axe").onclick = () => this.redresser();
    $("v-recentrer").onclick = () => this.cadrer();
    $("v-plein").onclick = () => conteneur.requestFullscreen?.();
  },

  redimensionner() {
    const c = $("v-canvas");
    if (!c.clientWidth) return;
    this.renderer.setSize(c.clientWidth, c.clientHeight, false);
    this.camera.aspect = c.clientWidth / c.clientHeight;
    this.camera.updateProjectionMatrix();
  },

  charger(url, id, simulation) {
    if (this.url === url) return;
    this.simulation = simulation;
    if (!this.renderer) this.initialiser();
    this.url = url;
    this.id = id;
    if (this.modele) this.scene.remove(this.modele);
    this.modele = null;
    $("v-chargement").hidden = false;
    $("v-chargement").textContent = "Chargement du modèle…";
    this.chargeur.load(
      url,
      (gltf) => {
        if (this.url !== url) return;
        $("v-chargement").hidden = true;
        // Pivot centré : les modèles géoréférencés ont des coordonnées très grandes
        const pivot = new THREE.Group();
        const centre = new THREE.Box3().setFromObject(gltf.scene).getCenter(new THREE.Vector3());
        gltf.scene.position.sub(centre);
        pivot.add(gltf.scene);
        this.modele = pivot;
        // Les modèles d'OpenDroneMap ont l'axe vertical en Z : on les redresse par défaut
        let redresse = this.simulation ? "0" : "1";
        try { redresse = localStorage.getItem("redresse_" + id) ?? redresse; } catch {}
        if (redresse === "1") pivot.rotation.x = -Math.PI / 2;
        this.scene.add(pivot);
        this.redimensionner();
        this.cadrer();
      },
      (e) => {
        if (e.lengthComputable) $("v-chargement").textContent = `Chargement… ${Math.round((100 * e.loaded) / e.total)} %`;
      },
      () => { $("v-chargement").textContent = "Impossible d'afficher le modèle (téléchargez-le ci-dessous)."; },
    );
  },

  redresser() {
    if (!this.modele) return;
    this.modele.rotation.x = this.modele.rotation.x ? 0 : -Math.PI / 2;
    try { localStorage.setItem("redresse_" + this.id, this.modele.rotation.x ? "1" : "0"); } catch {}
    this.cadrer();
  },

  cadrer() {
    if (!this.modele) return;
    const boite = new THREE.Box3().setFromObject(this.modele);
    const centre = boite.getCenter(new THREE.Vector3());
    const rayon = boite.getSize(new THREE.Vector3()).length() / 2 || 1;
    const distance = rayon / Math.sin((this.camera.fov * Math.PI) / 360);
    this.camera.position.copy(centre).add(new THREE.Vector3(0.6, 0.55, 0.6).normalize().multiplyScalar(distance));
    this.camera.near = distance / 1000;
    this.camera.far = distance * 100;
    this.camera.updateProjectionMatrix();
    this.controles.target.copy(centre);
  },
};

// ---------------------------------------------------------------- Démarrage

async function chargerEtat() {
  const etat = await (await fetch("/api/etat")).json();
  const pastille = $("etat-moteur");
  if (etat.simulation) {
    pastille.textContent = "Mode simulation (aucun calcul réel)";
    pastille.className = "pastille demo";
  } else {
    pastille.textContent = etat.docker_ok ? "Moteur prêt" : "Docker non démarré";
    pastille.className = "pastille " + (etat.docker_ok ? "ok" : "ko");
    pastille.title = etat.docker_message;
  }
  $("dossier-entree").textContent = etat.dossier_entree;
}

initialiserDepot();
initialiserDetail();
await chargerEtat();
await rafraichir();
if (travaux.length) selectionner(travaux[0].id);
setInterval(rafraichir, 2000);
setInterval(chargerJournal, 3000);
setInterval(chargerEtat, 30000);
