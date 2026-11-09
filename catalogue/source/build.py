# -*- coding: utf-8 -*-
"""Génère catalog.html (A4, 8 pages) : catalogue de location de drones."""
import math, os

HERE = os.path.dirname(os.path.abspath(__file__))
NB = " "   # espace insécable
NN = " "   # espace fine insécable
BRAND = "DRONEINSITE"
TAGLINE = "Aerial Solutions"
EDITION = "Édition novembre 2026"
TOTAL = 8
SAFETY = 0.15   # marge de sécurité appliquée à l'autonomie constructeur
SCALE_MAX = 60  # échelle commune des barres d'autonomie (min)
M4T_200G = 49 / (1420 / 1219) ** 1.5  # estimation : autonomie du 4T avec 200 g

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
        key="m400", page=3, name="Matrice 400", maker="DJI",
        cat="Porteur lourd",
        short="Jusqu’à 6" + NB + "kg de charge",
        pitch=("Le porteur lourd de la flotte : il soulève jusqu’à 6" + NB + "kg et vole jusqu’à "
               + u(safe(59), "min") + ". Il est le seul des trois à supporter la pluie."),
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
            ("Classe UE", "C3 <i>(vol à l’écart des personnes)</i>"),
        ],
        ideal=[
            "Lever, déplacer et déposer des objets jusqu’à 6" + NB + "kg.",
            "Vols longs en extérieur, y compris sous la pluie (IP55).",
            "Maintien en vol stationnaire précis, avec une charge suspendue.",
        ],
    ),
    dict(
        key="m4t", page=4, name="Matrice 4T", maker="DJI",
        cat="Porteur léger",
        short="Jusqu’à 200" + NB + "g de charge",
        pitch=("Compact et rapide à déployer : il emporte de petits objets jusqu’à 200" + NB + "g "
               "et vole jusqu’à " + u(safe(49), "min") + " sans charge."),
        hero="img/hero_m4t.jpg", hero_pos="50% 45%", cut="img/cut_m4t.png",
        kpi=[
            ("charge", "Charge max", "200", "g", "masse max 1,42" + NB + "kg au décollage"),
            ("battery", "Autonomie*", str(safe(49)), "min", "≈" + NN + u(safe(M4T_200G), "min") + " avec 200" + NB + "g"),
            ("range", "Portée radio", "12", "km", "norme CE, sans obstacle"),
            ("sound", "Bruit (LWA)", "85", "dB(A)", "≈" + NN + u(round(spl(85, 10)), "dB(A)") + " à 10" + NB + "m"),
        ],
        bars=[
            ("Sans charge", 49, True),
            ("Charge 200" + NB + "g (max)", M4T_200G, False),
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
            "Transporter de petits objets légers, jusqu’à 200" + NB + "g.",
            "Mise en œuvre rapide : plié, il tient dans un sac à dos.",
            "Bonne tenue au vent (12" + NB + "m/s) et longue autonomie.",
        ],
    ),
    dict(
        key="mini", page=5, name="Mini 4 Pro", maker="DJI",
        cat="Prise de vue",
        short="Vidéo 4K · moins de 250" + NB + "g",
        pitch=("Ultra-léger et discret : le drone de prise de vue, pour filmer et repérer les lieux. "
               "Il n’est pas conçu pour porter des objets."),
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
            ("Caméra", "Vidéo 4K HDR stabilisée · photo 48" + NB + "Mpx"),
            ("Classe UE", "C0 <i>(moins de 250" + NB + "g)</i>"),
        ],
        ideal=[
            "Prise de vue aérienne, photo et vidéo 4K.",
            "Repérage des lieux et préparation des vols.",
            "Le plus léger et le plus discret de la flotte.",
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

# ---------------------------------------------------------------- blocs communs
def header(page):
    return f'''<header class="top">
  <div class="brand"><img class="logo" src="img/logo_droneinsite.png" alt="DRONEINSITE"></div>
  <div class="top-r">Catalogue de location · drones<span class="pg">{page:02d} / {TOTAL:02d}</span></div>
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
    return f'<div class="block ideal"><h3>Usages</h3><ul>{lis}</ul></div>'

def specs(d):
    rows = "".join(f'<tr><th>{k}</th><td>{v}</td></tr>' for k, v in d["specs"])
    return f'<div class="specs"><h3>Caractéristiques</h3><table>{rows}</table></div>'

FOOT = ("<b>*</b> Autonomie conseillée = valeur constructeur DJI réduite de 15" + NB + "% pour garder une marge de sécurité "
        "(vent, froid, retour au point de décollage). Bruit : LWA = puissance acoustique déclarée (registre EASA / déclaration UE) ; "
        "valeurs à 1" + NB + "m et 10" + NB + "m estimées en champ libre. Portée : maximum théorique en norme CE, "
        "sans obstacle ni interférence ; le vol se fait toujours à vue du télépilote.")
SRC = ("Sources : fiches techniques officielles DJI (dji.com, enterprise.dji.com) et registre EASA des drones à marquage de classe, "
       "novembre 2026. Photos : DJI.")

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
<footer class="foot"><p>{FOOT}</p><p class="src">{SRC}</p></footer>
</section>'''

# ---------------------------------------------------------------- page de garde
def cover():
    m400, m4t, mini = DRONES
    cards = ""
    for d, w, left, top, cap_top in (
        (m400, 124, None, 6, 69),
        (m4t, 80, 6, 88, 123),
        (mini, 56, 124, 92, 123),
    ):
        x = (186 - w) / 2 if left is None else left
        cards += f'''<img class="g-img" src="{d["cut"]}" style="left:{x:.1f}mm;top:{top}mm;width:{w}mm" alt="{d["maker"]} {d["name"]}">
<div class="g-cap" style="left:{x:.1f}mm;top:{cap_top}mm;width:{w}mm"><span class="lu-n">{d["name"]}</span><span class="lu-c">{d["short"]}</span></div>'''
    return f'''<section class="page cover">
<header class="top top-cover">
  <div class="brand brand-cover"><img class="logo" src="img/logo_droneinsite.png" alt="DRONEINSITE"><span class="tagline">{TAGLINE}</span></div>
  <div class="top-r">{EDITION}</div>
</header>
<div class="c-title">
  <div class="eyebrow">Catalogue de location</div>
  <h1>Drones DJI</h1>
  <p class="pitch">Matrice 400 · Matrice 4T · Mini 4 Pro</p>
</div>
<div class="lineup">{cards}</div>
<footer class="c-foot">
  <span>Capacité de charge · autonomie · portée · dimensions · niveau sonore</span>
  <span>{TOTAL} pages</span>
</footer>
</section>'''

# ---------------------------------------------------------------- sommaire
def sommaire():
    items = "".join(f'''<li>
  <span class="s-p">{d["page"]:02d}</span>
  <span class="s-img"><img src="{d["cut"]}" alt=""></span>
  <span class="s-t"><b>{d["name"]}</b><em>{d["cat"]} · {d["short"]}</em></span>
</li>''' for d in DRONES)
    items += f'''<li class="s-plain"><span class="s-p">06</span><span class="s-img"></span><span class="s-t"><b>Comparatif de la flotte</b><em>Toutes les caractéristiques côte à côte</em></span></li>
<li class="s-plain"><span class="s-p">07</span><span class="s-img"></span><span class="s-t"><b>Bon à savoir</b><em>Marge de sécurité, bruit, portée, réglementation, lexique</em></span></li>'''
    how = [
        ("charge", "Charge max", "Masse maximale que le drone peut emporter en plus de son propre poids, fixée sous l’appareil."),
        ("battery", "Autonomie", "Durée de vol conseillée : la valeur constructeur réduite de 15" + NB + "% pour garder une marge de sécurité."),
        ("range", "Portée radio", "Distance maximale de liaison avec la télécommande, en norme européenne (CE), sans obstacle."),
        ("sound", "Bruit", "Puissance acoustique déclarée (LWA), et niveau estimé à 1" + NB + "m et 10" + NB + "m."),
    ]
    how_html = "".join(f'<div class="how"><div class="how-i">{icon(ic)}</div><div><b>{t}</b><p>{p}</p></div></div>' for ic, t, p in how)
    return f'''<section class="page toc-page">
{header(2)}
<div class="title">
  <div class="eyebrow">Sommaire</div>
  <h1>Trois drones,<br>trois usages</h1>
</div>
<div class="toc-cols">
  <div>
    <p class="intro">Ce catalogue présente les trois drones DJI disponibles à la location. Chaque fiche tient sur une page
    et reprend les mêmes repères : la charge que le drone peut soulever, son autonomie de vol, sa portée radio,
    ses dimensions et son niveau sonore.</p>
    <p class="intro">Les autonomies indiquées incluent une marge de sécurité de 15{NB}% par rapport aux valeurs du constructeur.
    Les valeurs constructeur restent visibles sur chaque fiche, en plus petit.</p>
    <h3 class="how-h">Comment lire une fiche</h3>
    <div class="hows">{how_html}</div>
  </div>
  <ol class="som">{items}</ol>
</div>
<footer class="foot"><p class="src">{SRC}</p></footer>
</section>'''

# ---------------------------------------------------------------- comparatif
def comparatif():
    head = "".join(f'<th><img src="{d["cut"]}" style="width:{w}mm" alt=""><span>{d["name"]}</span><em>{d["cat"]}</em></th>'
                   for d, w in zip(DRONES, (36, 29, 22)))
    est = safe(M4T_200G)
    groups = [
        ("Charge", [
            ("Charge max", "6" + NB + "kg", "200" + NB + "g", "—"),
            ("Mode de fixation", "Vissée (6" + NB + "kg) ou attache rapide (3" + NB + "kg)", "Port accessoire E-Port", "—"),
            ("Masse max au décollage", "15,8" + NB + "kg", "1,42" + NB + "kg", "—"),
        ]),
        ("Autonomie*", [
            ("Autonomie conseillée", u(safe(59), "min"), u(safe(49), "min"), u(safe(34), "min")),
            ("Autonomie à charge max", u(safe(31), "min") + " <i>(6" + NB + "kg)</i>", "≈" + NN + u(est, "min") + " <i>(estimation)</i>", "—"),
            ("Vol stationnaire", u(safe(53), "min"), u(safe(42), "min"), u(safe(30), "min")),
            ("Recharge d’une batterie", "45" + NB + "min <i>(rapide)</i>", "≈" + NN + "1" + NB + "h", "≈" + NN + "1" + NB + "h"),
        ]),
        ("Portée & bruit", [
            ("Portée radio (CE)", "20" + NB + "km", "12" + NB + "km", "10" + NB + "km"),
            ("Bruit — LWA déclaré", "105" + NB + "dB(A)", "85" + NB + "dB(A)", "81" + NB + "dB(A)"),
            ("Bruit à 10" + NB + "m (estimation)", "≈" + NN + str(round(spl(105, 10))) + NB + "dB(A)", "≈" + NN + str(round(spl(85, 10))) + NB + "dB(A)", "≈" + NN + str(round(spl(81, 10))) + NB + "dB(A)"),
        ]),
        ("Taille & poids", [
            ("Poids (batterie incluse)", "9,74" + NB + "kg", "1,22" + NB + "kg", "< 249" + NB + "g"),
            ("Dimensions déplié", "98 × 76 × 48" + NB + "cm", "31 × 39 × 15" + NB + "cm", "30 × 37 × 10" + NB + "cm"),
            ("Dimensions plié", "49 × 49 × 48" + NB + "cm", "26 × 11 × 14" + NB + "cm", "15 × 9 × 6" + NB + "cm"),
            ("Encombrement en vol", "≈" + NN + "1,7" + NB + "m", "≈" + NN + "71" + NB + "cm", "≈" + NN + "45" + NB + "cm"),
        ]),
        ("Conditions de vol", [
            ("Vitesse max", "90" + NB + "km/h", "75" + NB + "km/h", "58" + NB + "km/h"),
            ("Vent max supporté", "43" + NB + "km/h <i>(12" + NB + "m/s)</i>", "43" + NB + "km/h <i>(12" + NB + "m/s)</i>", "38" + NB + "km/h <i>(10,7" + NB + "m/s)</i>"),
            ("Vol sous la pluie", "Oui (IP55)", "Non", "Non"),
            ("Températures", "−20 à 50" + NB + "°C", "−10 à 40" + NB + "°C", "−10 à 40" + NB + "°C"),
            ("Classe UE", "C3", "C2", "C0"),
        ]),
    ]
    body = ""
    for g, rows in groups:
        body += f'<tr class="grp"><th colspan="4">{g}</th></tr>'
        body += "".join(f'<tr><th>{r[0]}</th><td>{r[1]}</td><td>{r[2]}</td><td>{r[3]}</td></tr>' for r in rows)
    return f'''<section class="page comp">
{header(6)}
<div class="title">
  <div class="eyebrow">Récapitulatif</div>
  <h1>Comparatif de la flotte</h1>
</div>
<table class="ctable"><thead><tr><th class="c0"></th>{head}</tr></thead><tbody>{body}</tbody></table>
<footer class="foot"><p><b>*</b> Valeurs constructeur DJI réduites de 15{NB}% (marge de sécurité). Détails et méthode page 7.</p><p class="src">{SRC} Courbe autonomie / charge du Matrice 400 : DJI.</p></footer>
</section>'''

# ---------------------------------------------------------------- bon à savoir
def savoir():
    notes = [
        ("Marge de sécurité",
         "Toutes les autonomies affichées sont les valeurs DJI (mesurées sans vent, batterie de 100" + NB + "% à 0" + NB + "%) "
         "réduites de 15" + NB + "%. Le vent, le froid et les manœuvres réduisent encore l’autonomie : l’atterrissage se prévoit "
         "avant l’alerte de batterie faible."),
        ("Charge et autonomie",
         "Plus la charge est lourde, plus l’autonomie baisse. Pour le Matrice 400, les valeurs avec 3" + NB + "kg et 6" + NB + "kg "
         "viennent des courbes publiées par DJI. Pour le Matrice 4T, l’autonomie avec 200" + NB + "g est une estimation. "
         "La capacité d’emport diminue aussi avec l’altitude."),
        ("Niveau sonore",
         "Le LWA est la puissance acoustique déclarée pour le marquage de classe européen. Le niveau perçu baisse d’environ 6" + NB + "dB "
         "chaque fois que la distance double. Les niveaux à 1" + NB + "m et 10" + NB + "m sont estimés en champ libre, sans réverbération."),
        ("Portée radio",
         "La portée indiquée est un maximum théorique en norme CE, sans obstacle ni interférence. En ville ou en intérieur, elle est "
         "bien plus faible. La réglementation impose de toute façon de garder le drone à vue."),
        ("Réglementation",
         "Les vols suivent la réglementation européenne (règlement UE 2019/947). Le vol au-dessus d’un rassemblement de personnes "
         "est interdit en catégorie Ouverte. Voler à proximité des personnes demande un télépilote qualifié et, selon le cas, "
         "une autorisation de l’autorité nationale de l’aviation civile (catégorie Spécifique). La classe UE de chaque drone "
         "fixe la distance minimale à respecter."),
        ("Météo",
         "Seul le Matrice 400 peut voler sous la pluie (IP55). Aucun vol par vent supérieur aux valeurs indiquées, ni en dehors "
         "des plages de température de chaque appareil."),
    ]
    nh = "".join(f'<div class="note"><h4>{t}</h4><p>{p}</p></div>' for t, p in notes)
    lex = [
        ("Charge utile", "Masse que le drone peut emporter en plus de son propre poids."),
        ("Masse max au décollage", "Poids total autorisé : drone, batterie et charge compris."),
        ("Vol stationnaire", "Drone immobile en l’air. Il consomme un peu plus qu’en déplacement lent."),
        ("LWA", "Puissance acoustique de la source, en dB(A). Ce n’est pas le niveau entendu à distance."),
        ("dB(A)", "Décibels pondérés selon la sensibilité de l’oreille humaine."),
        ("Classe UE (C0 à C3)", "Marquage européen qui fixe les règles de vol : C0 et C2 autorisent le vol près des personnes "
                                "avec des distances minimales, C3 impose de rester à l’écart."),
        ("IP55", "Indice de protection contre la poussière et les projections d’eau."),
        ("Norme CE / FCC", "Puissance radio autorisée en Europe (CE) ou aux États-Unis (FCC). Les portées sont données en CE."),
    ]
    lx = "".join(f'<tr><th>{k}</th><td>{v}</td></tr>' for k, v in lex)
    return f'''<section class="page savoir">
{header(7)}
<div class="title">
  <div class="eyebrow">Repères</div>
  <h1>Bon à savoir</h1>
</div>
<div class="notes notes-big">{nh}</div>
<h3 class="lex-h">Lexique</h3>
<table class="lex">{lx}</table>
<footer class="foot"><p class="src">{SRC}</p></footer>
</section>'''

# ---------------------------------------------------------------- dos
def back():
    return f'''<section class="page back">
<div class="bk-body">
  <div class="brand brand-big"><img class="logo" src="img/logo_droneinsite.png" alt="DRONEINSITE"><span class="tagline">{TAGLINE}</span></div>
  <p class="bk-t">Catalogue de location · drones DJI</p>
  <p class="bk-e">{EDITION}</p>
</div>
<div class="bk-contact">
  <div class="bk-col">
    <h4>DRONEINSITE SRL</h4>
    <p>4ᵉ Avenue 46, boîte 19<br>4040 Herstal, Belgique</p>
    <p class="bk-muted">TVA BE 1.037.066.689<br>Exploitant drone déclaré et assuré</p>
  </div>
  <div class="bk-col">
    <h4>Contact</h4>
    <p>+32 (0)471 86 18 41<br>contact@droneinsite.com<br>www.droneinsite.com</p>
    <p class="bk-muted">Interventions en Belgique et en France<br>du lundi au samedi</p>
  </div>
  <div class="bk-qr"><img src="img/qr_contact.png" alt=""><span>Enregistrer<br>notre contact</span></div>
  <div class="bk-qr"><img src="img/qr_site.png" alt=""><span>Voir nos<br>réalisations</span></div>
</div>
<footer class="bk-foot">
  <p>Document d’information. Les caractéristiques proviennent des fiches techniques officielles DJI (dji.com, enterprise.dji.com)
  et du registre EASA des drones à marquage de classe, consultés en novembre 2026. Elles sont indicatives et susceptibles d’évoluer.</p>
  <p>Les autonomies conseillées incluent une marge de sécurité de 15{NB}% ; les niveaux sonores à distance et l’autonomie du
  Matrice 4T en charge sont des estimations. Photos : DJI. Matrice et Mini sont des marques de DJI.</p>
</footer>
</section>'''

def build(pages, out):
    css = open(os.path.join(HERE, "style.css"), encoding="utf-8").read()
    doc = f'''<!doctype html><html lang="fr"><head><meta charset="utf-8">
<title>Catalogue de location drones — {BRAND}</title><style>{css}</style></head>
<body>{"".join(pages)}</body></html>'''
    open(os.path.join(HERE, out), "w", encoding="utf-8").write(doc)

if __name__ == "__main__":
    pages = [cover(), sommaire()] + [drone_page(d) for d in DRONES] + [comparatif(), savoir(), back()]
    build(pages, "catalog.html")
    for d in DRONES:
        build([drone_page(d)], f"fiche_{d['key']}.html")
    print("ok")
