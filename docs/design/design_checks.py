#!/usr/bin/env python3
"""Palette checks for SecondLook + RefundRadar (stdlib + numpy only).

Computes, for every (text, background) pair:
  * WCAG 2.x contrast ratio (SC 1.4.3 / 1.4.6 / 1.4.11)
  * APCA Lc (APCA-W3 0.0.98G-4g constants; advisory only, not a W3C standard)
and, for every pair of hazard / chart colours:
  * CIEDE2000 colour difference under normal vision and under Machado et al.
    (2009) severity-1.0 protanopia, deuteranopia and tritanopia simulation.

Usage:  python3 design_checks.py            -> prints report, exits 1 on any failure
Edit PAIRS / SETS below when the palette changes; wire into CI next to axe-core.
"""
import itertools, math, sys
import numpy as np

# ---------------------------------------------------------------- colour maths
def hex2rgb(h):
    h = h.lstrip('#'); return np.array([int(h[i:i+2], 16) for i in (0, 2, 4)]) / 255.0

def srgb_to_lin(c):
    c = np.asarray(c, float)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)

def lin_to_srgb(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.0031308, 12.92 * c, 1.055 * c ** (1 / 2.4) - 0.055)

def wcag_lum(h):
    return float(np.dot(srgb_to_lin(hex2rgb(h)), [0.2126, 0.7152, 0.0722]))

def wcag_ratio(a, b):
    la, lb = sorted([wcag_lum(a), wcag_lum(b)], reverse=True)
    return (la + 0.05) / (lb + 0.05)

def apca_lc(txt, bg):
    def y(h):
        r, g, b = hex2rgb(h)
        Y = 0.2126729 * r ** 2.4 + 0.7151522 * g ** 2.4 + 0.0721750 * b ** 2.4
        return Y + (0.022 - Y) ** 1.414 if Y < 0.022 else Y
    yt, yb = y(txt), y(bg)
    if abs(yb - yt) < 0.0005: return 0.0
    if yb > yt:   # dark text on light bg
        s = (yb ** 0.56 - yt ** 0.57) * 1.14
        return 0.0 if s < 0.1 else (s - 0.027) * 100
    s = (yb ** 0.65 - yt ** 0.62) * 1.14      # light text on dark bg
    return 0.0 if s > -0.1 else (s + 0.027) * 100

# Machado, Oliveira & Fernandes 2009, severity 1.0, applied to linear RGB
MACHADO = {
    'protan': np.array([[0.152286, 1.052583, -0.204868],
                        [0.114503, 0.786281, 0.099216],
                        [-0.003882, -0.048116, 1.051998]]),
    'deutan': np.array([[0.367322, 0.860646, -0.227968],
                        [0.280085, 0.672501, 0.047413],
                        [-0.011820, 0.042940, 0.968881]]),
    'tritan': np.array([[1.255528, -0.076749, -0.178779],
                        [-0.078411, 0.930809, 0.147602],
                        [0.004733, 0.691367, 0.303900]]),
}

def simulate(h, kind):
    if kind == 'normal': return hex2rgb(h)
    if kind == 'mono':   # achromatic / greyscale print: keep relative luminance only
        return lin_to_srgb(np.full(3, wcag_lum(h)))
    return lin_to_srgb(MACHADO[kind] @ srgb_to_lin(hex2rgb(h)))

def rgb_to_lab(rgb):
    lin = srgb_to_lin(rgb)
    M = np.array([[0.4124564, 0.3575761, 0.1804375],
                  [0.2126729, 0.7151522, 0.0721750],
                  [0.0193339, 0.1191920, 0.9503041]])
    xyz = M @ lin / np.array([0.95047, 1.0, 1.08883])
    f = np.where(xyz > (6 / 29) ** 3, np.cbrt(xyz), xyz / (3 * (6 / 29) ** 2) + 4 / 29)
    return np.array([116 * f[1] - 16, 500 * (f[0] - f[1]), 200 * (f[1] - f[2])])

def de2000(l1, l2):
    L1, a1, b1 = l1; L2, a2, b2 = l2
    C1, C2 = math.hypot(a1, b1), math.hypot(a2, b2); Cb = (C1 + C2) / 2
    G = 0.5 * (1 - math.sqrt(Cb ** 7 / (Cb ** 7 + 25 ** 7)))
    a1p, a2p = (1 + G) * a1, (1 + G) * a2
    C1p, C2p = math.hypot(a1p, b1), math.hypot(a2p, b2)
    h1p = math.degrees(math.atan2(b1, a1p)) % 360; h2p = math.degrees(math.atan2(b2, a2p)) % 360
    dLp, dCp = L2 - L1, C2p - C1p
    dh = 0 if C1p * C2p == 0 else (h2p - h1p if abs(h2p - h1p) <= 180 else h2p - h1p - 360 * math.copysign(1, h2p - h1p))
    dHp = 2 * math.sqrt(C1p * C2p) * math.sin(math.radians(dh / 2))
    Lbp, Cbp = (L1 + L2) / 2, (C1p + C2p) / 2
    if C1p * C2p == 0: hbp = h1p + h2p
    elif abs(h1p - h2p) <= 180: hbp = (h1p + h2p) / 2
    else: hbp = (h1p + h2p + 360) / 2 if h1p + h2p < 360 else (h1p + h2p - 360) / 2
    T = (1 - 0.17 * math.cos(math.radians(hbp - 30)) + 0.24 * math.cos(math.radians(2 * hbp))
         + 0.32 * math.cos(math.radians(3 * hbp + 6)) - 0.20 * math.cos(math.radians(4 * hbp - 63)))
    dth = 30 * math.exp(-(((hbp - 275) / 25) ** 2))
    Rc = 2 * math.sqrt(Cbp ** 7 / (Cbp ** 7 + 25 ** 7))
    Sl = 1 + 0.015 * (Lbp - 50) ** 2 / math.sqrt(20 + (Lbp - 50) ** 2)
    Sc, Sh = 1 + 0.045 * Cbp, 1 + 0.015 * Cbp * T
    Rt = -math.sin(math.radians(2 * dth)) * Rc
    return math.sqrt((dLp / Sl) ** 2 + (dCp / Sc) ** 2 + (dHp / Sh) ** 2 + Rt * (dCp / Sc) * (dHp / Sh))

# ---------------------------------------------------------------- palettes
# (label, text, background, required WCAG ratio, required |APCA Lc|)
# 4.5 = SC 1.4.3 normal text; 3.0 = large/bold text or SC 1.4.11 graphics.
PAIRS = [
    # --- reference: Pantone-derived approximations of ANSI Z535.1 colours
    ('ANSI ref  DANGER  white/red',      '#FFFFFF', '#C8102E', 4.5, 60),
    ('ANSI ref  WARNING black/orange 24b', '#000000', '#FF6900', 4.5, 45),
    ('ANSI ref  WARNING white/orange',   '#FFFFFF', '#FF6900', 4.5, 60),
    ('ANSI ref  CAUTION black/yellow',   '#000000', '#F6D04D', 4.5, 60),
    ('ANSI ref  SAFE    white/green',    '#FFFFFF', '#00843D', 4.5, 60),
    # --- SecondLook proposed bands
    ('SL DANGER        white/#B0001E',   '#FFFFFF', '#B0001E', 4.5, 60),
    ('SL WARNING black/#FF7A00 >=24px b', '#000000', '#FF7A00', 4.5, 45),
    ('SL CAUTION       black/#FFD23F',   '#000000', '#FFD23F', 4.5, 60),
    ('SL NO KNOWN chip #0B5D3B/#E8F5EE', '#0B5D3B', '#E8F5EE', 4.5, 75),
    ('SL NO KNOWN border #2E7D5B/white', '#2E7D5B', '#FFFFFF', 3.0, 45),
    ('SL DANGER band vs white page',     '#B0001E', '#FFFFFF', 3.0, 45),
    ('SL detail text on band: avoid',   '#1A1A1A', '#FF7A00', 4.5, 60),
    ('SL body text     #1A1A1A/#FFFFFF', '#1A1A1A', '#FFFFFF', 7.0, 90),
    ('SL muted text    #595959/#FFFFFF', '#595959', '#FFFFFF', 4.5, 75),
    ('SL band edge  #FFD23F vs white',   '#FFD23F', '#FFFFFF', 1.0, 0),   # informational: yellow needs a dark border
    ('SL yellow border #8A6D00/white',   '#8A6D00', '#FFFFFF', 3.0, 45),
    # --- RefundRadar proposed
    ('RR body          #111827/#FFFFFF', '#111827', '#FFFFFF', 7.0, 90),
    ('RR secondary     #4B5563/#FFFFFF', '#4B5563', '#FFFFFF', 4.5, 75),
    ('RR primary btn   white/#1F4E9C',   '#FFFFFF', '#1F4E9C', 4.5, 75),
    ('RR link          #1F4E9C/#FFFFFF', '#1F4E9C', '#FFFFFF', 4.5, 75),
    ('RR HOLD banner   white/#B42318',   '#FFFFFF', '#B42318', 4.5, 75),
    ('RR HOLD tint     #7A1A12/#FEF3F2', '#7A1A12', '#FEF3F2', 4.5, 75),
    ('RR deadline amb  #1A1A1A/#F5A524', '#1A1A1A', '#F5A524', 4.5, 60),
    ('RR big $ verdict #0B3B2E/#FFFFFF', '#0B3B2E', '#FFFFFF', 7.0, 90),
]

SETS = {
    'ANSI ref hazard (red/orange/yellow/green)':
        {'DANGER': '#C8102E', 'WARNING': '#FF6900', 'CAUTION': '#F6D04D', 'SAFE': '#00843D'},
    'SecondLook proposed bands':
        {'DANGER': '#B0001E', 'WARNING': '#FF7A00', 'CAUTION': '#FFD23F', 'NO_KNOWN_chip': '#E8F5EE'},
    'RefundRadar 9-category (3 groups x 3 steps)':
        {'Refund-ready': '#1F4E9C', 'Refund-filed': '#5B8BD9', 'Refund-paid': '#A9C4F0',
         'Fix-docs': '#B25E00', 'Fix-classify': '#F5A524', 'Fix-other': '#FBD38D',
         'Not-elig-dutyfree': '#3F3F46', 'Not-elig-expired': '#8E8E96', 'Not-elig-other': '#D4D4D8'},
    'Okabe-Ito 8 + grey (reference)':
        {'orange': '#E69F00', 'skyblue': '#56B4E9', 'bluegreen': '#009E73', 'yellow': '#F0E442',
         'blue': '#0072B2', 'vermillion': '#D55E00', 'redpurple': '#CC79A7', 'black': '#000000',
         'grey': '#999999'},
}
MIN_DE = 10.0   # inference: ~10 dE2000 = clearly distinct for small chart marks / bands

def main():
    fail = 0
    print('== Text / band contrast ==')
    print(f"{'pair':36} {'WCAG':>6} {'need':>5} {'APCA Lc':>8} {'need':>5}  result")
    for label, t, b, need, need_lc in PAIRS:
        r, lc = wcag_ratio(t, b), apca_lc(t, b)
        ok = r >= need and abs(lc) >= need_lc
        fail += (not ok) and need > 1 and 'ANSI ref' not in label and 'avoid' not in label  # reference rows are informational
        print(f"{label:36} {r:6.2f} {need:5.1f} {lc:8.1f} {need_lc:5}  {'PASS' if ok else 'FAIL'}")
    print('\n== Pairwise CIEDE2000 (min over pairs) under CVD simulation, Machado 2009 sev 1.0 ==')
    for name, cols in SETS.items():
        print(f"\n-- {name}")
        for kind in ('normal', 'protan', 'deutan', 'tritan', 'mono'):
            labs = {k: rgb_to_lab(simulate(v, kind)) for k, v in cols.items()}
            pairs = sorted(((de2000(labs[a], labs[b]), a, b) for a, b in itertools.combinations(cols, 2)))
            worst = pairs[0]
            flag = 'OK ' if worst[0] >= MIN_DE else 'LOW'
            print(f"  {kind:7} min dE={worst[0]:5.1f} ({worst[1]} vs {worst[2]}) {flag}  "
                  f"next: {pairs[1][0]:.1f} ({pairs[1][1]} vs {pairs[1][2]})")
            if 'proposed' in name and kind != 'mono' and worst[0] < MIN_DE: fail += 1  # mono is covered by shape/icon/word coding
        Ls = {k: round(rgb_to_lab(simulate(v, 'normal'))[0]) for k, v in cols.items()}
        print('  CIELAB L* (lightness):', Ls)
    print(f"\n{fail} failing checks")
    return 1 if fail else 0

if __name__ == '__main__':
    sys.exit(main())
