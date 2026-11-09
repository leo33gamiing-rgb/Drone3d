# -*- coding: utf-8 -*-
"""Génère catalog.html (A4) pour le catalogue location drones."""
import math, os, html

HERE = os.path.dirname(os.path.abspath(__file__))
NB = " "   # espace insécable
NN = " "   # espace fine insécable
BRAND = "Insite Rental"
TOTAL = 5
SAFETY = 0.15   # marge de sécurité appliquée à l'autonomie constructeur
SCALE_MAX = 60  # échelle commune des barres d'autonomie (min)

def safe(m):
    return int(math.floor(m * (1 - SAFETY) + 1e-9))

def spl(lwa, r):
    """Pression acoustique estimée en champ libre à r mètres depuis LWA."""
    return lwa - 20 * math.log10(r) - 11

def u(v, unit):
    return f"{v}{NB}{unit}"

# ---------------------------------------------------------------- données
DRONES = [
    dict(
        key="m400", page=2, name="Matrice 400", maker="DJI",
        cat="Porteur lourd",
        pitch=("Le porteur lourd de la flotte : jusqu’à 6" + NB + "kg d’objets, de décors légers "
               "ou d’effets suspendus, et jusqu’à " + u(safe(59), "min") + " de vol."),
        hero="img/hero_m400.jpg", hero_pos="50% 50%", cut="img/cut_m400.png",
        kpi=[
            ("charge", "Charge max", "6", "kg", "3" + NB + "kg en attache rapide"),
            ("battery", "Autonomie*", str(safe(59)), "min", u(safe(31), "min") + " avec 6" + NB + "kg"),
            ("range", "Portée radio", "20", "km", "norme CE, sans obstacle"),
            ("sound", "Bruit (LWA)", "105", "dB(A)", "≈" + NN + u(round(spl(105, 10)), "dB(A)") + " à 10" + NB + "m"),
        ],
        bars=[
            ("Charge < 1" + NB + "kg", 59, True),
            ("Charge 3" + NB + "kg", 44, True),
            ("Charge 6" + NB + "kg (max)", 31, True),
        ],
        lwa=105,
        specs=[
            ("Poids (batterie incluse)", "9,74" + NB + "kg"),
            ("Masse max au décollage", "15,8" + NB + "kg"),
            ("Charge utile", "6" + NB + "kg vissée · 3" + NB + "kg attache rapide"),
            ("Dimensions déplié", "98 × 76 × 48" + NB + "cm <i>(hors hélices)</i>"),
            ("Dimensions plié", "49 × 49 × 48" + NB + "cm"),
            ("Encombrement en vol", "≈" + NN + "1,7" + NB + "m de diagonale <i>(hélices 25″)</i>"),
            ("Valise de transport", "78 × 36 × 53" + NB + "cm"),
            ("Vol stationnaire*", u(safe(53), "min") + " <i>(53" + NB + "min constructeur)</i>"),
            ("Vitesse max", "25" + NB + "m/s <i>(90" + NB + "km/h)</i>"),
            ("Vent max supporté", "12" + NB + "m/s <i>(43" + NB + "km/h)</i>"),
            ("Pluie & poussière", "Oui — IP55"),
            ("Températures", "−20 à 50" + NB + "°C"),
            ("Batterie", "TB100 · 977" + NB + "Wh · recharge 45" + NB + "min"),
            ("Classe UE", "C3 <i>(vol à l’écart du public)</i>"),
        ],
        ideal=[
            "Lever et déplacer des objets jusqu’à 6" + NB + "kg : accessoires, décors légers, banderoles.",
            "Effets suspendus et apparitions aériennes au-dessus de la scène.",
            "Longues prestations en extérieur, même sous la pluie (IP55).",
        ],
    ),
    dict(
        key="m4t", page=3, name="Matrice 4T", maker="DJI",
        cat="Porteur léger",
        pitch=("Compact et rapide à déployer : idéal pour faire voler de petits objets légers "
               "(jusqu’à 200" + NB + "g) avec une grande autonomie."),
        hero="img/hero_m4t.jpg", hero_pos="50% 45%", cut="img/cut_m4t.png",
        kpi=[
            ("charge", "Charge max", "200", "g", "masse max 1,42" + NB + "kg au décollage"),
            ("battery", "Autonomie*", str(safe(49)), "min", "≈" + NN + u(safe(49 / (1420 / 1219) ** 1.5), "min") + " avec 200" + NB + "g"),
            ("range", "Portée radio", "12", "km", "norme CE, sans obstacle"),
            ("sound", "Bruit (LWA)", "85", "dB(A)", "≈" + NN + u(round(spl(85, 10)), "dB(A)") + " à 10" + NB + "m"),
        ],
        bars=[
            ("Sans charge", 49, True),
            ("Charge 200" + NB + "g (max)", 49 / (1420 / 1219) ** 1.5, False),
        ],
        lwa=85,
        specs=[
            ("Poids (batterie incluse)", "1,22" + NB + "kg <i>(1" + NN + "219" + NB + "g)</i>"),
            ("Masse max au décollage", "1,42" + NB + "kg"),
            ("Charge utile", "200" + NB + "g max"),
            ("Dimensions déplié", "31 × 39 × 15" + NB + "cm <i>(hors hélices)</i>"),
            ("Dimensions plié", "26 × 11 × 14" + NB + "cm"),
            ("Encombrement en vol", "≈" + NN + "71" + NB + "cm de diagonale <i>(hélices 10,8″)</i>"),
            ("Vol stationnaire*", u(safe(42), "min") + " <i>(42" + NB + "min constructeur)</i>"),
            ("Vitesse max", "21" + NB + "m/s <i>(75" + NB + "km/h)</i>"),
            ("Montée avec charge", "6" + NB + "m/s max"),
            ("Vent max supporté", "12" + NB + "m/s <i>(43" + NB + "km/h)</i>"),
            ("Pluie & poussière", "Non — pas d’indice IP"),
            ("Températures", "−10 à 40" + NB + "°C"),
            ("Classe UE", "C2 <i>(30" + NB + "m des personnes, 5" + NB + "m en basse vitesse)</i>"),
        ],
        ideal=[
            "Faire voler de petits objets jusqu’à 200" + NB + "g : rubans, petits accessoires, éléments décoratifs.",
            "Interventions rapides : plié, il tient dans un sac à dos.",
            "Bonne tenue au vent (12" + NB + "m/s) et longue autonomie.",
        ],
    ),
    dict(
        key="mini", page=4, name="Mini 4 Pro", maker="DJI",
        cat="Prise de vue",
        pitch=("Ultra-léger et discret : le drone de captation pour filmer vos spectacles "
               "et repérer les lieux. Il n’est pas conçu pour porter des objets."),
        hero="img/hero_mini.jpg", hero_pos="50% 50%", cut="img/cut_mini.png",
        kpi=[
            ("charge", "Charge max", "—", "", "non prévu pour l’emport"),
            ("battery", "Autonomie*", str(safe(34)), "min", u(safe(30), "min") + " en stationnaire"),
            ("range", "Portée radio", "10", "km", "norme CE, sans obstacle"),
            ("sound", "Bruit (LWA)", "81", "dB(A)", "≈" + NN + u(round(spl(81, 10)), "dB(A)") + " à 10" + NB + "m"),
        ],
        bars=[
            ("En déplacement", 34, True),
            ("Vol stationnaire", 30, True),
        ],
        lwa=81,
        specs=[
            ("Poids (batterie incluse)", "< 249" + NB + "g"),
            ("Charge utile", "Aucune <i>(non prévu)</i>"),
            ("Dimensions déplié", "30 × 37 × 10" + NB + "cm <i>(hélices incluses)</i>"),
            ("Dimensions plié", "15 × 9 × 6" + NB + "cm"),
            ("Vol stationnaire*", u(safe(30), "min") + " <i>(30" + NB + "min constructeur)</i>"),
            ("Vitesse max", "16" + NB + "m/s <i>(58" + NB + "km/h)</i>"),
            ("Vent max supporté", "10,7" + NB + "m/s <i>(38" + NB + "km/h)</i>"),
            ("Pluie & poussière", "Non — pas d’indice IP"),
            ("Températures", "−10 à 40" + NB + "°C"),
            ("Caméra", "Vidéo 4K HDR stabilisée"),
            ("Classe UE", "C0 <i>(moins de 250" + NB + "g)</i>"),
        ],
        ideal=[
            "Captation vidéo aérienne de vos spectacles et événements.",
            "Repérage des lieux et préparation des vols des porteurs.",
            "Le plus léger et le plus silencieux de la flotte.",
        ],
    ),
]

# ---------------------------------------------------------------- icônes
ICONS = {
    "charge": '<path d="M8.5 8a3.5 3.5 0 0 1 7 0"/><path d="M5.5 10.5h13l-1.6 9h-9.8z"/><path d="M12 3v1.5"/>',
    "battery": '<rect x="2.5" y="7" width="16.5" height="10" rx="2.2"/><path d="M21.5 10.5v3"/><path d="M6 10.5v3M9.5 10.5v3M13 10.5v3"/>',
    "range": '<circle cx="12" cy="11" r="1.6"/><path d="M12 12.6V21"/><path d="M8.6 7.6a4.8 4.8 0 0 0 0 6.8M15.4 7.6a4.8 4.8 0 0 1 0 6.8M5.6 4.6a9 9 0 0 0 0 12.8M18.4 4.6a9 9 0 0 1 0 12.8"/>',
    "sound": '<path d="M3.5 9.5h3.8l4.7-4v13l-4.7-4H3.5z"/><path d="M15.5 9a4.2 4.2 0 0 1 0 6M18.3 6.3a8 8 0 0 1 0 11.4"/>',
}
def icon(name, cls="ico"):
    return (f'<svg class="{cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            f'stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{ICONS[name]}</svg>')

# ---------------------------------------------------------------- blocs
def header(page):
    return f'''<header class="top">
  <div class="brand"><span class="mark"></span>{BRAND.upper()}</div>
  <div class="top-r">Catalogue location drones · 2026<span class="pg">{page:02d} / {TOTAL:02d}</span></div>
</header>'''

def kpis(d):
    out = []
    for ic, label, val, unit, sub in d["kpi"]:
        unit_html = f'<span class="unit">{unit}</span>' if unit else ""
        out.append(f'''<div class="kpi">
  <div class="kpi-h">{icon(ic)}<span>{label}</span></div>
  <div class="kpi-v">{val}{unit_html}</div>
  <div class="kpi-s">{sub}</div>
</div>''')
    return '<section class="kpis">' + "".join(out) + "</section>"

def bars(d):
    rows = []
    for label, maker, official in d["bars"]:
        s = safe(maker)
        w_safe = s / SCALE_MAX * 100
        if official:
            w_ghost = (maker - s) / SCALE_MAX * 100
            ghost = f'<span class="b-ghost" style="width:{w_ghost:.2f}%"></span>'
            val = f'<b>{s}{NB}min</b><span class="b-m">DJI : {round(maker)}{NB}min</span>'
        else:
            ghost = ""
            val = f'<b>≈{NN}{s}{NB}min</b><span class="b-m">estimation</span>'
        rows.append(f'''<div class="b-row">
  <div class="b-l">{label}</div>
  <div class="b-track"><span class="b-safe" style="width:{w_safe:.2f}%"></span>{ghost}</div>
  <div class="b-val">{val}</div>
</div>''')
    ticks = "".join(f'<span style="left:{t/SCALE_MAX*100:.2f}%">{t}</span>' for t in (0, 15, 30, 45, 60))
    grid = "".join(f'<i style="left:{t/SCALE_MAX*100:.2f}%"></i>' for t in (15, 30, 45, 60))
    return f'''<div class="block">
  <h3>Autonomie de vol <span class="h3-s">en minutes</span></h3>
  <div class="bars"><div class="b-grid">{grid}</div>{"".join(rows)}
    <div class="b-axis"><div class="b-l"></div><div class="b-ticks">{ticks}</div><div class="b-vs"></div></div>
  </div>
  <div class="legend"><span><i class="lg-safe"></i>Autonomie conseillée (sécurité incluse)</span><span><i class="lg-ghost"></i>Marge de sécurité</span></div>
</div>'''

REFS = [(40, "Bibliothèque"), (60, "Conversation"), (75, "Aspirateur"), (90, "Tondeuse")]
DB_MIN, DB_MAX = 30, 100
def dbx(v):
    return (v - DB_MIN) / (DB_MAX - DB_MIN) * 100

def noise(d):
    lwa = d["lwa"]
    p10, p1 = round(spl(lwa, 10)), round(spl(lwa, 1))
    refs = "".join(f'<span class="n-ref" style="left:{dbx(v):.2f}%"><i></i><b>{v}</b><em>{t}</em></span>' for v, t in REFS)
    return f'''<div class="block">
  <h3>Niveau sonore <span class="h3-s">dB(A) perçus, selon la distance</span></h3>
  <div class="noise">
    <div class="n-labels">
      <span class="n-lab n-lab10" style="left:{dbx(p10):.2f}%">≈{NN}{p10}{NB}dB(A) <em>à 10{NB}m</em></span>
      <span class="n-lab n-lab1" style="left:{dbx(p1):.2f}%">≈{NN}{p1} <em>à 1{NB}m</em></span>
    </div>
    <div class="n-track">
      <span class="n-span" style="left:{dbx(p10):.2f}%;width:{dbx(p1)-dbx(p10):.2f}%"></span>
      <span class="n-dot n-10" style="left:{dbx(p10):.2f}%"></span>
      <span class="n-dot n-1" style="left:{dbx(p1):.2f}%"></span>
    </div>
    <div class="n-refs">{refs}</div>
  </div>
</div>'''

def ideal(d):
    lis = "".join(f"<li>{t}</li>" for t in d["ideal"])
    return f'<div class="block ideal"><h3>Idéal pour</h3><ul>{lis}</ul></div>'

def specs(d):
    rows = "".join(f'<tr><th>{k}</th><td>{v}</td></tr>' for k, v in d["specs"])
    return f'<div class="specs"><h3>Caractéristiques</h3><table>{rows}</table></div>'

FOOT = ("<b>*</b> Autonomie conseillée = valeur constructeur DJI réduite de 15" + NB + "% pour garder une marge de sécurité "
        "(vent, froid, retour au point de décollage). Bruit : LWA = puissance acoustique déclarée (registre EASA / déclaration UE) ; "
        "valeurs à 1" + NB + "m et 10" + NB + "m estimées en champ libre. Portée : maximum théorique en norme CE, "
        "sans obstacle ni interférence — en spectacle, le vol se fait à vue du télépilote.")

def drone_page(d):
    return f'''<section class="page">
{header(d["page"])}
<div class="title">
  <div class="eyebrow">{d["maker"]} · {d["cat"]}</div>
  <h1>{d["name"]}</h1>
  <p class="pitch">{d["pitch"]}</p>
</div>
<figure class="hero"><img src="{d["hero"]}" style="object-position:{d["hero_pos"]}" alt="{d["maker"]} {d["name"]}"></figure>
{kpis(d)}
<div class="cols">
  {specs(d)}
  <div class="side">{bars(d)}{noise(d)}{ideal(d)}</div>
</div>
<footer class="foot"><p>{FOOT}</p><p class="src">Sources : fiches techniques officielles DJI (dji.com, enterprise.dji.com) et registre EASA, novembre 2026. Photos : DJI.</p></footer>
</section>'''

def cover():
    m400, m4t, mini = DRONES
    # photo de groupe : (drone, largeur mm, gauche mm ou None=centré, haut mm, légende)
    cards = ""
    for d, w, left, top, tag, cap_top in (
        (m400, 116, None, 10, "jusqu’à 6" + NB + "kg", 69),
        (m4t, 76, 8, 84, "jusqu’à 200" + NB + "g", 117),
        (mini, 52, 124, 88, "captation vidéo", 117),
    ):
        x = (186 - w) / 2 if left is None else left
        cards += f'''<img class="g-img" src="{d["cut"]}" style="left:{x:.1f}mm;top:{top}mm;width:{w}mm" alt="{d["maker"]} {d["name"]}">
<div class="g-cap" style="left:{x:.1f}mm;top:{cap_top}mm;width:{w}mm"><span class="lu-n">{d["name"]}</span><span class="lu-c">{d["cat"]} · {tag}</span></div>'''
    toc = "".join(f'<li><span class="toc-p">{d["page"]:02d}</span><span class="toc-n">{d["name"]}</span><span class="toc-c">{d["cat"]}</span></li>' for d in DRONES)
    toc += f'<li><span class="toc-p">05</span><span class="toc-n">Comparatif</span><span class="toc-c">& bon à savoir</span></li>'
    return f'''<section class="page cover">
{header(1)}
<div class="c-title">
  <div class="eyebrow">Spectacle · Événementiel · Location</div>
  <h1>Location de drones<br>pour le spectacle</h1>
  <p class="pitch">Trois drones DJI disponibles à la location. Pour chacun : la charge qu’il peut soulever,
  son autonomie (marge de sécurité incluse), sa portée, sa taille et son niveau sonore.</p>
</div>
<div class="lineup">{cards}</div>
<div class="c-bottom">
  <div class="c-facts">
    <div><b>6{NB}kg</b><span>charge max<br>de la flotte</span></div>
    <div><b>{safe(59)}{NB}min</b><span>d’autonomie conseillée<br>(Matrice 400)</span></div>
    <div><b>−15{NB}%</b><span>de marge de sécurité<br>sur chaque batterie</span></div>
  </div>
  <ol class="toc">{toc}</ol>
</div>
</section>'''

def comparatif():
    m400, m4t, mini = DRONES
    head = "".join(f'<th><img src="{d["cut"]}" style="width:{w}mm" alt=""><span>{d["name"]}</span></th>' for d, w in zip(DRONES, (40, 33, 25)))
    est = safe(49 / (1420 / 1219) ** 1.5)
    rows = [
        ("Charge max", "6" + NB + "kg", "200" + NB + "g", "—"),
        ("Autonomie conseillée*", u(safe(59), "min"), u(safe(49), "min"), u(safe(34), "min")),
        ("Autonomie à charge max*", u(safe(31), "min") + " <i>(6" + NB + "kg)</i>", "≈" + NN + u(est, "min") + " <i>(estim.)</i>", "—"),
        ("Vol stationnaire*", u(safe(53), "min"), u(safe(42), "min"), u(safe(30), "min")),
        ("Portée radio (CE)", "20" + NB + "km", "12" + NB + "km", "10" + NB + "km"),
        ("Bruit — LWA", "105" + NB + "dB(A)", "85" + NB + "dB(A)", "81" + NB + "dB(A)"),
        ("Bruit à 10" + NB + "m (estim.)", "≈" + NN + str(round(spl(105, 10))) + NB + "dB(A)", "≈" + NN + str(round(spl(85, 10))) + NB + "dB(A)", "≈" + NN + str(round(spl(81, 10))) + NB + "dB(A)"),
        ("Poids", "9,74" + NB + "kg", "1,22" + NB + "kg", "< 249" + NB + "g"),
        ("Masse max au décollage", "15,8" + NB + "kg", "1,42" + NB + "kg", "—"),
        ("Dimensions déplié", "98 × 76 × 48" + NB + "cm", "31 × 39 × 15" + NB + "cm", "30 × 37 × 10" + NB + "cm"),
        ("Dimensions plié", "49 × 49 × 48" + NB + "cm", "26 × 11 × 14" + NB + "cm", "15 × 9 × 6" + NB + "cm"),
        ("Vitesse max", "90" + NB + "km/h", "75" + NB + "km/h", "58" + NB + "km/h"),
        ("Vent max supporté", "43" + NB + "km/h", "43" + NB + "km/h", "38" + NB + "km/h"),
        ("Vol sous la pluie", "Oui (IP55)", "Non", "Non"),
        ("Classe UE", "C3", "C2", "C0"),
    ]
    body = "".join(f'<tr><th>{r[0]}</th><td>{r[1]}</td><td>{r[2]}</td><td>{r[3]}</td></tr>' for r in rows)
    notes = [
        ("Marge de sécurité",
         "Toutes les autonomies affichées sont les valeurs DJI (mesurées sans vent, batterie de 100" + NB + "% à 0" + NB + "%) "
         "réduites de 15" + NB + "%. Le vent, le froid et les manœuvres réduisent encore l’autonomie : prévoyez l’atterrissage avant l’alerte batterie faible."),
        ("Charge et autonomie",
         "Plus la charge est lourde, plus l’autonomie baisse. Pour le Matrice 400, les valeurs avec 3" + NB + "kg et 6" + NB + "kg viennent des courbes DJI. "
         "Pour le Matrice 4T, l’autonomie avec 200" + NB + "g est une estimation de notre part. La capacité d’emport diminue aussi en altitude."),
        ("Niveau sonore",
         "Le LWA est la puissance acoustique déclarée pour le marquage de classe UE. Le niveau perçu baisse d’environ 6" + NB + "dB "
         "chaque fois que la distance double. Les niveaux à 1" + NB + "m et 10" + NB + "m sont estimés en champ libre."),
        ("Portée",
         "La portée radio est un maximum théorique (norme CE, sans obstacle ni interférence). En ville ou en salle, elle est bien plus faible, "
         "et la réglementation impose de toute façon de garder le drone à vue."),
        ("Réglementation",
         "Le survol d’un public rassemblé est interdit en catégorie Ouverte. Un vol au-dessus ou près du public demande un "
         "télépilote qualifié et une autorisation en catégorie Spécifique (DGAC). Nous vérifions avec vous le cadre de chaque prestation."),
        ("Météo",
         "Seul le Matrice 400 peut voler sous la pluie (IP55). Pas de vol par vent supérieur aux valeurs indiquées, ni hors des plages de température."),
    ]
    nh = "".join(f'<div class="note"><h4>{t}</h4><p>{p}</p></div>' for t, p in notes)
    return f'''<section class="page comp">
{header(5)}
<div class="title">
  <div class="eyebrow">Récapitulatif</div>
  <h1>Comparatif de la flotte</h1>
</div>
<table class="ctable"><thead><tr><th class="c0"></th>{head}</tr></thead><tbody>{body}</tbody></table>
<h2 class="nb">Bon à savoir</h2>
<div class="notes">{nh}</div>
<footer class="foot"><p class="src">Sources : fiches techniques officielles DJI (dji.com, enterprise.dji.com), courbe autonomie/charge du Matrice 400 (DJI), registre EASA des drones à marquage de classe. Données indicatives au 9 novembre 2026, susceptibles d’évoluer. Photos : DJI.</p></footer>
</section>'''

def build(pages, out):
    css = open(os.path.join(HERE, "style.css"), encoding="utf-8").read()
    doc = f'''<!doctype html><html lang="fr"><head><meta charset="utf-8">
<title>Catalogue location drones — {BRAND}</title><style>{css}</style></head>
<body>{"".join(pages)}</body></html>'''
    open(os.path.join(HERE, out), "w", encoding="utf-8").write(doc)

if __name__ == "__main__":
    pages = [cover()] + [drone_page(d) for d in DRONES] + [comparatif()]
    build(pages, "catalog.html")
    for d in DRONES:
        build([drone_page(d)], f"fiche_{d['key']}.html")
    print("ok")
