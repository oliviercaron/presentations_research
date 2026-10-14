# -*- coding: utf-8 -*-
"""
carte_sens_svg.py — schéma de la diapo de la mesure, sur données réelles (fenêtre Pfizer/BioNTech).
Statut : EXPLORATOIRE (illustration).

Gauche : un tweet réel (verbatim) et les six premières des 768 composantes de son vecteur.
Droite : messages réels projetés sur les deux premiers axes de l'ACP des neuf moyennes journalières
(J−4 à J+4), deux autres tweets réels placés à leur position, et en encart la trajectoire des jours
(moyennes journalières, même plan, échelle agrandie).
Entrées : embeddings H3.2 (sentence-camembert-base), carte_sens_pfizer_tweets.json.
Sortie : carte_sens.svg.html (fragment SVG inséré dans les deux .qmd entre les marqueurs carte-sens).
"""
import json, sys, html, textwrap
from pathlib import Path
import numpy as np, pandas as pd
sys.stdout.reconfigure(encoding="utf-8")
ICI = Path(__file__).resolve().parent
EMB = Path("C:/Users/Olivier/Documents/GitHub/article_afm/explore/rq3_derive_serielle_2026-07-21/data/embeddings")
ids = pd.read_parquet(EMB / "child_ids.parquet"); E = np.load(EMB / "child_emb.npy", mmap_mode="r")
ids["j"] = (pd.to_datetime(ids["day"]) - pd.Timestamp("2020-11-09")).dt.days
w = ids[ids["j"].between(-4, 4)].copy()
X = np.asarray(E[w.index.values], dtype=np.float32); w = w.reset_index(drop=True)
C = np.vstack([X[w["j"].values == j].mean(0) for j in range(-4, 5)])
mu = C.mean(0); _, S, Vt = np.linalg.svd(C - mu, full_matrices=False); P = Vt[:2]
XY = (X - mu) @ P.T; CXY = (C - mu) @ P.T
TW = {t["compte"]: t for t in json.load(open(ICI / "carte_sens_pfizer_tweets.json", encoding="utf-8"))}
rng = np.random.default_rng(2026)
q = np.quantile(np.abs(XY), 0.98, axis=0); print("98e centile |x|, |y| :", q)

ENC, MUT, ACC, RISK, GRIS = "#1f2328", "#5b6672", "#2b5a7f", "#c0392b", "#8a96a3"
esc = html.escape
virg = lambda v, d=3: f"{v:+.{d}f}".replace(".", ",").replace("+", "").replace("-", "−")

def carte_tweet(x, y, larg, t, taille=16, cpl=46):
    lignes = textwrap.wrap(t["texte"], cpl)
    h = 34 + 21 * len(lignes) + 26
    s = [f'<rect x="{x}" y="{y}" width="{larg}" height="{h}" rx="9" fill="#fff" stroke="#cfd6dd" stroke-width="1.4"/>',
         f'<text x="{x+14}" y="{y+24}" font-size="{taille}" fill="{ENC}"><tspan font-weight="700">{esc(t["nom"].replace(" 🌍", ""))}</tspan>'
         f'<tspan fill="{MUT}"> @{esc(t["compte"])} · J{t["j"]:+d}</tspan></text>']
    for k, l in enumerate(lignes):
        s.append(f'<text x="{x+14}" y="{y+48+21*k}" font-size="{taille}" fill="{ENC}">{esc(l)}</text>')
    s.append(f'<text x="{x+14}" y="{y+h-12}" font-size="{taille-2}" fill="{MUT}">{t["jaime"]:,} j\'aime · {t["retweets"]:,} retweets'.replace(",", "\u202f") + '</text>')
    return "\n".join(s), h

# ---------- gauche : du texte aux nombres ----------
R = TW["MicheleRivasi"]
g = ['<text x="0" y="30" font-size="25" font-weight="700" fill="#1f2328">1. Chaque message devient une suite de nombres</text>']
c, h = carte_tweet(0, 52, 520, R, cpl=56)
g.append(c)
y0 = 52 + h
g.append(f'<line x1="260" y1="{y0+4}" x2="260" y2="{y0+34}" stroke="{MUT}" stroke-width="2" marker-end="url(#flm)"/>')
g.append(f'<rect x="150" y="{y0+38}" width="220" height="46" rx="8" fill="#fff" stroke="{ENC}" stroke-width="1.6"/>'
         f'<text x="260" y="{y0+68}" text-anchor="middle" font-size="21" font-weight="700" fill="{ENC}">CamemBERT</text>'
         f'<text x="382" y="{y0+58}" font-size="16" fill="{MUT}">modèle de langue</text>'
         f'<text x="382" y="{y0+77}" font-size="16" fill="{MUT}">entraîné sur du français</text>')
g.append(f'<line x1="260" y1="{y0+86}" x2="260" y2="{y0+114}" stroke="{MUT}" stroke-width="2" marker-end="url(#flm)"/>')
vals = [virg(v) for v in R["vecteur_6"][:5]] + ["…"]
for k, v in enumerate(vals):
    xx = 4 + 86 * k
    g.append(f'<rect x="{xx}" y="{y0+118}" width="80" height="44" rx="6" fill="#fff" stroke="{ACC}" stroke-width="1.6"/>'
             f'<text x="{xx+40}" y="{y0+147}" text-anchor="middle" font-size="18" font-family="Roboto Mono, monospace" fill="{ENC}">{v}</text>')
g.append(f'<text x="4" y="{y0+188}" font-size="17" fill="{MUT}">768 nombres par message</text>')
g.append(f'<text x="0" y="{y0+228}" font-size="20" fill="{ENC}">Deux messages au sens proche reçoivent des nombres</text>')
g.append(f'<text x="0" y="{y0+254}" font-size="20" fill="{ENC}">proches : ils sont <tspan font-weight="700">voisins dans l\'espace</tspan>.</text>')

# ---------- droite : l'espace sémantique ----------
X0, Y0, LW, LH = 580, 52, 910, 540        # cadre de la carte
cx, cy = X0 + LW * 0.46, Y0 + LH * 0.50   # origine du plan
sc = min(LW * 0.40 / q[0], LH * 0.42 / q[1])
px = lambda a, b: (cx + a * sc, cy - b * sc)
d = ['<text x="580" y="30" font-size="25" font-weight="700" fill="#1f2328">2. Chaque jour devient un point dans l\'espace sémantique latent</text>',
     f'<rect x="{X0}" y="{Y0}" width="{LW}" height="{LH}" rx="10" fill="#fafbfc" stroke="#e1e5ea"/>']
groupes = [((w["j"] < 0).values, GRIS, "avant"), ((w["j"] == 1).values, ACC, "J+1"), ((w["j"] >= 2).values, "#b98a2e", "J+2 à J+4")]
for m, col, _ in groupes:
    k = rng.choice(np.flatnonzero(m), 260, replace=False)
    for a, b in XY[k]:
        x, y = px(a, b)
        if X0 + 6 < x < X0 + LW - 6 and Y0 + 6 < y < Y0 + LH - 6:
            d.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="3.2" fill="{col}" fill-opacity="0.38"/>')
# légende des nuages
for k, (_, col, lab) in enumerate(groupes):
    d.append(f'<circle cx="{X0+22}" cy="{Y0+24+24*k}" r="6" fill="{col}" fill-opacity="0.7"/>'
             f'<text x="{X0+34}" y="{Y0+30+24*k}" font-size="16" fill="{ENC}">messages {"des quatre jours d" + chr(39) + "avant" if lab == "avant" else "de " + lab}</text>')
# tweets réels placés à leur position : vignettes en bas, reliées à leur point
def vignette(sn, bx, bw, cpl):
    t = TW[sn]; x, y = px(t["x"], t["y"])
    lignes = len(textwrap.wrap(t["texte"], cpl)); h = 34 + 21 * lignes + 26
    by = Y0 + LH - h - 10
    c, _ = carte_tweet(bx, by, bw, t, taille=15, cpl=cpl)
    ax_ = min(max(x, bx + 20), bx + bw - 20)
    d.append(f'<line x1="{x:.0f}" y1="{y:.0f}" x2="{ax_:.0f}" y2="{by}" stroke="{MUT}" stroke-width="1.4"/>')
    d.append(c)
    d.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="7" fill="#fff" stroke="{ENC}" stroke-width="2.4"/>')
vignette("Maitre_Eolas", X0 + 12, 318, 42)
vignette("f_philippot", X0 + 342, 270, 36)
x, y = px(TW["MicheleRivasi"]["x"], TW["MicheleRivasi"]["y"])
d.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="7" fill="#fff" stroke="{ACC}" stroke-width="2.6"/>'
         f'<text x="{x+12:.0f}" y="{y-10:.0f}" font-size="16" font-weight="700" fill="{ACC}">@MicheleRivasi</text>')
# moyennes des jours sur la carte elle-même (même échelle que les messages), cadre du zoom
mp = [px(a, b) for a, b in CXY]
zx0, zx1 = min(p[0] for p in mp) - 16, max(p[0] for p in mp) + 16
zy0, zy1 = min(p[1] for p in mp) - 16, max(p[1] for p in mp) + 16
d.append(f'<rect x="{zx0:.0f}" y="{zy0:.0f}" width="{zx1-zx0:.0f}" height="{zy1-zy0:.0f}" fill="#fff" fill-opacity="0.75" stroke="{ENC}" stroke-width="1.4" stroke-dasharray="5 4"/>')
d.append('<polyline points="' + " ".join(f"{a:.0f},{b:.0f}" for a, b in mp[4:]) + f'" fill="none" stroke="{ACC}" stroke-width="2.2"/>')
for k, (a, b) in enumerate(mp):
    d.append(f'<circle cx="{a:.0f}" cy="{b:.0f}" r="{7 if k - 4 == 1 else 5.5}" fill="{GRIS if k < 4 else ACC}" stroke="#fff" stroke-width="1.5"/>')
d.append(f'<text x="{zx0:.0f}" y="{zy0-8:.0f}" font-size="15" font-weight="700" fill="{ENC}" stroke="#fff" stroke-width="4" paint-order="stroke">moyennes des jours</text>')
# encart en bas à droite : trajectoire des jours (moyennes journalières, même plan, agrandi)
IX, IY, IW, IH = X0 + LW - 278, Y0 + LH - 262, 266, 252
d.append(f'<rect x="{IX}" y="{IY}" width="{IW}" height="{IH}" rx="8" fill="#fff" stroke="{ENC}" stroke-width="1.2"/>'
         f'<text x="{IX+12}" y="{IY+24}" font-size="16" font-weight="700" fill="{ENC}">Les jours : moyenne</text>'
         f'<text x="{IX+12}" y="{IY+44}" font-size="16" font-weight="700" fill="{ENC}">de leurs messages</text>'
         f'<text x="{IX+12}" y="{IY+63}" font-size="13" fill="{MUT}">zoom sur le cadre pointillé</text>')
d.append(f'<line x1="{zx1:.0f}" y1="{zy1:.0f}" x2="{IX}" y2="{IY}" stroke="{ENC}" stroke-width="1.2" stroke-dasharray="5 4"/>')
lo, hi = CXY.min(0), CXY.max(0); s2 = min((IW - 90) / (hi[0] - lo[0]), (IH - 110) / (hi[1] - lo[1]))
ip = lambda a, b: (IX + 30 + (a - lo[0]) * s2, IY + IH - 26 - (b - lo[1]) * s2)
pts = [ip(a, b) for a, b in CXY]
d.append('<polyline points="' + " ".join(f"{a:.0f},{b:.0f}" for a, b in pts[4:]) + f'" fill="none" stroke="{ACC}" stroke-width="2"/>')
for k, (a, b) in enumerate(pts):
    j = k - 4
    d.append(f'<circle cx="{a:.0f}" cy="{b:.0f}" r="{6 if j == 1 else 4.5}" fill="{GRIS if j < 0 else ACC}"/>')
    if j in (0, 1, 2, 4):
        d.append(f'<text x="{a+9:.0f}" y="{b+5:.0f}" font-size="14" font-family="Roboto Mono, monospace" fill="{ACC}">{"J" + format(j, "+d") if j else "J0"}</text>')
ax_, ay_ = np.mean(pts[:4], axis=0)
d.append(f'<text x="{ax_:.0f}" y="{ay_+22:.0f}" text-anchor="middle" font-size="13" fill="{MUT}">jours d\'avant</text>')
a1, b1 = pts[5]
d.append(f'<text x="{a1+9:.0f}" y="{b1+22:.0f}" font-size="12" font-style="italic" fill="{MUT}">obligation</text>'
         f'<text x="{a1+9:.0f}" y="{b1+36:.0f}" font-size="12" font-style="italic" fill="{MUT}">vaccinale</text>')
d.append(f'<text x="{X0+LW-12}" y="{Y0+24}" text-anchor="end" font-size="14" fill="{MUT}">projection sur 2 axes, l\'espace en a 768</text>')

svg = ('<!-- carte-sens debut : genere par scripts/figures_diapo/carte_sens_svg.py, ne pas editer a la main -->\n'
       '```{=html}\n'
       '<svg viewBox="0 0 1500 600" width="100%" style="max-height:640px" font-family="Barlow, sans-serif" xmlns="http://www.w3.org/2000/svg">\n'
       f'<defs><marker id="flm" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{MUT}"/></marker></defs>\n'
       + "\n".join(g) + "\n" + "\n".join(d) + "\n</svg>\n```\n<!-- carte-sens fin -->")
(ICI / "carte_sens.svg.html").write_text(svg, encoding="utf-8")
print("ok", len(svg))
