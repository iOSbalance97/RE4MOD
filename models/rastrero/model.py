"""EL RASTRERO - original fast enemy: a mutated Ganado that drops onto all fours to close in.
Lean and wiry, burlap hood, sickle in the right hand, the left arm burst open by the Plaga into a long
taloned limb, bone spikes along the spine. mm, y up, faces +z, its right = -x. Bind = T-pose."""
import numpy as np, math
from sdf import *
SKIN, PANTS, BOOT, LEATHER, IRON, WOOD, CHAIN, SOLE, CLOTH, HOT, PLAGA, EYE, SACK, BONE = range(14)

# ---- skeleton -----------------------------------------------------------------------------------
def J(s):
    d = dict(hip=V(s*105, 935, 0), knee=V(s*122, 510, 38), ank=V(s*118, 88, -12), sh=V(s*205, 1468, 0))
    up, fo = (300, 270) if s < 0 else (322, 335)                 # the left (mutated) arm is longer
    d.update(el=d['sh'] + V(s*up, 0, 0)); d.update(wr=d['el'] + V(s*fo, 0, 0))
    return d
JR, JL = J(-1), J(1)
HEAD = V(0, 1640, 58)
SPINE = dict(root=V(0, 960, 0), s1=V(0, 975, 0), s2=V(0, 1210, 0), neck=V(0, 1505, 10), head=V(0, 1585, 40),
             clav=1450, seg1=(V(0, 960, 0), V(0, 1080, 5)), seg2=(V(0, 1150, 5), V(0, 1440, 0)),
             seg3=(V(0, 1505, 10), V(0, 1570, 35)), seg4=(V(0, 1600, 45), V(0, 1720, 60)))
LEGS_Y = 900                                                     # finish.py: below -> 'legs' texture
ARM_X = 245                                                      # tex.py: |x| beyond -> arm
# Plaga growths (infection source for the texture): left shoulder, neck, up the arm
GROWTH = [((150, 1500, -20), 46), ((215, 1520, 40), 40), ((105, 1545, -40), 32), ((330, 1475, -30), 40), ((420, 1490, 35), 34),
          ((520, 1470, -25), 36), ((640, 1475, 30), 34), ((760, 1460, -20), 40), ((860, 1470, 25), 36), ((960, 1455, -10), 34),
          ((0, 1300, -150), 30), ((0, 1210, -140), 26)]

# ---- body ---------------------------------------------------------------------------------------
def torso(p):
    d = ell(p, V(0, 1305, 18), V(172, 190, 122))                          # rib cage
    d = smin(d, ell(p, V(0, 1105, 12), V(138, 150, 100)), 55)             # belly, drawn in
    d = smin(d, ell(p, V(0, 1415, -32), V(170, 105, 112)), 45)            # hunched upper back
    for s in (-1, 1):
        d = smin(d, ell(p, V(s*88, 1395, 92), V(92, 62, 42)), 25)         # flat pecs
        d = smin(d, ell(p, V(s*112, 1380, -98), V(78, 92, 46)), 22)       # shoulder blades
        d = smin(d, ell(p, V(s*135, 1250, -30), V(60, 140, 85)), 30)      # lats
        d = smin(d, ell(p, V(s*44, 1140, -95), V(34, 170, 36)), 18)       # erectors
    for i in range(7):                                                    # ribs showing on the flanks
        y = 1170 + i * 34
        for s in (-1, 1): d = smin(d, rcone(p, V(s*60, y + 30, 105), V(s*160, y - 10, 20), 9, 10), 9)
    for i in range(10):                                                   # vertebrae
        d = smin(d, sph(p, V(0, 1040 + i * 44, -112 - 18 * math.sin(i * 0.33)), 15), 8)
    return d
def pelvis(p): return ell(p, V(0, 958, 0), V(158, 112, 112))
def arms(p):
    d = None
    for s, j in ((-1, JR), (1, JL)):
        X = V(s, 0, 0)
        if s < 0:
            a = rcone(p, j['sh'], j['el'], 60, 47)
            a = smin(a, ell(p, j['sh'] + V(s*18, 16, 0), V(92, 74, 78)), 18)                   # deltoid
            a = smin(a, ell(p, j['sh'] + X*160 + V(0, 4, 38), V(95, 44, 40)), 10)              # biceps
            a = smin(a, ell(p, j['sh'] + X*150 + V(0, 10, -40), V(110, 46, 42)), 10)           # triceps
            f = rcone(p, j['el'], j['wr'], 47, 32)
            f = smin(f, ell(p, j['el'] + X*70 + V(0, 22, 14), V(95, 40, 40)), 9)               # brachioradialis
            f = smin(f, ell(p, j['el'] + X*85 + V(0, -20, 0), V(100, 40, 44)), 9)              # flexors
            a = smin(a, f, 14)
            a = smin(a, sph(p, j['el'] + V(0, -4, -46), 30), 8)                                # elbow
            a = smin(a, sph(p, j['wr'] - X*10 + V(0, 18, -26), 17), 6)                         # ulna head
        else:                                                                                 # the Plaga's limb
            a = rcone(p, j['sh'], j['el'], 72, 62)
            a = smin(a, ell(p, j['sh'] + V(s*20, 22, 0), V(110, 92, 95)), 22)
            a = smin(a, ell(p, j['sh'] + X*170 + V(0, 10, 0), V(120, 70, 66)), 14)            # swollen upper arm
            f = rcone(p, j['el'], j['wr'], 66, 50)
            f = smin(f, ell(p, j['el'] + X*120 + V(0, 18, 4), V(150, 62, 58)), 14)             # swollen forearm
            a = smin(a, f, 18)
            a = smin(a, sph(p, j['el'] + V(0, -2, -58), 38), 10)
        d = a if d is None else np.minimum(d, a)
    return d
def neck_head(p):
    d = rcone(p, V(0, 1470, 5), V(0, 1580, 40), 58, 48)
    for s in (-1, 1): d = smin(d, rcone(p, V(s*30, 1540, 10), V(s*190, 1478, 0), 46, 52), 34)    # traps
    for s in (-1, 1): d = smin(d, rcone(p, V(s*20, 1462, 112), V(s*185, 1478, 40), 12, 15), 9)   # clavicles
    h = ell(p, HEAD, V(82, 102, 98))
    h = smin(h, ell(p, HEAD + V(0, -58, 34), V(66, 56, 70)), 22)
    return smin(d, h, 26)
def plaga_arm(p):
    """bundles of red fibre twisting round the left arm (shoulder -> wrist) and fleshy growths"""
    j = JL; d = None
    a0, a1 = j['sh'] + V(-40, 0, 0), j['wr']
    L = float(np.linalg.norm(a1 - a0))
    for k in range(5):
        ph = k * 2 * math.pi / 5
        pts = []
        for i in range(13):
            t = i / 12; x = a0 + (a1 - a0) * t
            r = (58 if t < 0.5 else 48) + 10 * math.sin(t * 7 + k * 1.7)
            an = ph + t * (1.6 + 0.5 * k) + 0.4 * math.sin(t * 5 + k)
            pts.append(x + V(0, r * math.cos(an), r * math.sin(an)))
        for i in range(12):
            r0 = (17 - 8 * abs(i - 6) / 6) * (0.8 + 0.35 * math.sin(i * 1.3 + k))
            seg = rcone(p, pts[i], pts[i + 1], r0, r0)
            d = seg if d is None else smin(d, seg, 14)
    for c, r in GROWTH[:10]: d = smin(d, sph(p, V(*c), r * 0.8), 14)
    return d + 1.5 * np.sin(p[:, 0] * 0.35 + p[:, 1] * 0.21) * np.sin(p[:, 2] * 0.3)
def spikes_arm(p):
    j = JL; d = None
    for i, t in enumerate((0.15, 0.32, 0.5, 0.63, 0.76, 0.88)):
        b = j['sh'] + (j['wr'] - j['sh']) * t + V(0, 50, -40)
        tip = b + nrm(V(-0.35 + 0.1 * i, 0.75, -0.55)) * (95 + 25 * (i % 2))
        s = rcone(p, b, tip, 15, 2)
        d = s if d is None else np.minimum(d, s)
    for i, t in enumerate((0.25, 0.55, 0.8)):                              # a second row below
        b = j['sh'] + (j['wr'] - j['sh']) * t + V(0, -45, -50)
        s = rcone(p, b, b + nrm(V(-0.2, -0.45, -0.85)) * 70, 12, 2)
        d = np.minimum(d, s)
    return d
def spine_spikes(p):
    d = None
    for i, (y, ln_) in enumerate(((1170, 70), (1235, 95), (1300, 120), (1365, 115), (1430, 95), (1490, 70))):
        b = V(0, y, -112); tip = b + nrm(V(0.12 * (-1) ** i, 0.45, -1.0)) * ln_
        s = rcone(p, b, tip, 17, 2)
        d = s if d is None else np.minimum(d, s)
    return d
def skin(p):
    d = su(24, torso(p), arms(p), neck_head(p))
    return d
def legs(p):
    d = pelvis(p)
    for s, j in ((-1, JR), (1, JL)):
        l = rcone(p, j['hip'], j['knee'], 102, 70)
        l = smin(l, ell(p, (j['hip'] + j['knee']) / 2 + V(s*8, 30, 40), V(78, 175, 70)), 30)
        l = smin(l, sph(p, j['knee'] + V(0, 0, 26), 64), 20)
        l = smin(l, rcone(p, j['knee'], j['ank'] + V(0, 120, 0), 72, 56), 22)
        l = smin(l, ell(p, (j['knee'] + j['ank']) / 2 + V(0, 70, -38), V(58, 140, 55)), 22)
        d = smin(d, l, 40)
    # baggy trousers: loose cloth over the leg, big folds, gathered over the boots
    y = p[:, 1]
    d = d - 16 - 6 * np.clip((900 - y) / 300, 0, 1)
    d = d + 7.0 * np.sin(y * 0.045 + p[:, 0] * 0.03 + 2.2 * np.sin(p[:, 2] * 0.025)) * np.clip((y - 260) / 150, 0, 1) * np.clip((930 - y) / 120, 0, 1)
    d = d + 4.0 * np.sin(y * 0.12 + 1.7 * np.sin(p[:, 0] * 0.05)) * np.clip((330 - y) / 80, 0, 1) * np.clip((y - 190) / 40, 0, 1)
    # torn over the right knee and the left shin
    for c, r in ((JR['knee'] + V(0, -10, 70), V(55, 60, 60)), (JL['knee'] + V(10, -170, 55), V(48, 70, 60))):
        d = np.maximum(d, -(ell(p, c, r) + 6 * np.sin(p[:, 0] * 0.3 + p[:, 1] * 0.25)))
    return d
def seams(p, lg):
    """raised outer seams, a stitched patch on the left thigh, rolled cuffs"""
    x, y, z = p[:, 0], p[:, 1], p[:, 2]
    d = None
    for s, j in ((-1, JR), (1, JL)):
        ln_ = np.maximum(np.maximum(lg - 2.5, -lg - 2), np.maximum(np.abs(z - 10) - 3.0, np.maximum(s * (j['hip'][0] - x), y - 930)))
        cf = np.maximum(np.abs(rcone(p, j['ank'] + V(0, 185, 0), j['ank'] + V(0, 235, 0), 86, 84)) - 7, np.abs(y - j['ank'][1] - 210) - 26)
        d = mn(*(e for e in (d, ln_, cf) if e is not None))
    pt = np.maximum(np.maximum(lg - 3.5, -lg - 3), rbox(p, JL['hip'] + V(25, -230, 90), V(55, 65, 80), 10))
    return np.minimum(d, pt)
def knees(p):                                                     # skin showing through the tears
    d = None
    for s, j in ((-1, JR), (1, JL)):
        k = smin(sph(p, j['knee'] + V(0, 0, 22), 62), rcone(p, j['knee'], j['ank'] + V(0, 130, 0), 66, 52), 20)
        d = k if d is None else np.minimum(d, k)
    return d
def boots(p):
    d = None; sole = None; st = None
    for s, j in ((-1, JR), (1, JL)):
        R = frame(nrm(V(s*0.15, 0, 1)), V(0, 1, 0))
        c = j['ank'] * V(1, 0, 1)
        sh = rcone(p, j['ank'] + V(0, 160, 5), j['ank'] + V(0, -20, 0), 66, 58)
        ft = smin(rbox(p, c + V(s*4, 40, 55), V(48, 40, 88), 24, R), ell(p, c + V(s*10, 42, 138), V(48, 40, 56)), 14)
        b = smin(sh, ft, 22)
        b = b + 3.0 * np.sin(p[:, 1] * 0.11) * np.clip((p[:, 1] - 110) / 40, 0, 1)
        so = np.maximum(np.maximum(smin(ft, sh, 22) - 7, p[:, 1] - 24), -p[:, 1])
        b = np.maximum(b, 16 - p[:, 1])
        lace = np.maximum(sh - 4, np.maximum(np.abs(p[:, 0] - c[0]) - 16, (j['ank'][2] + 20) - p[:, 2]))
        lace = np.maximum(lace, np.abs(p[:, 1] - 140) - 70)
        d = b if d is None else np.minimum(d, b); sole = so if sole is None else np.minimum(sole, so)
        st = lace if st is None else np.minimum(st, lace)
    return d, sole, st
def shirt(p, tor):
    """grey-brown work shirt: torn open at the left shoulder (the arm burst out), down the spine
    (the spikes), open at the neck; short rolled sleeve on the right"""
    x, y, z = p[:, 0], p[:, 1], p[:, 2]
    rs = rcone(p, JR['sh'] + V(40, 0, 0), JR['sh'] + V(-175, 0, 0), 72, 64)                # right sleeve
    rs = np.maximum(rs, -(x - (JR['sh'][0] - 175)))
    cuff = np.maximum(torus(p, JR['sh'] + V(-168, 0, 0), V(1, 0, 0), 62, 13), 0 * x - 1)
    d = smin(tor - 9, rs, 12)
    d = np.minimum(d, cuff)
    d = d + 2.5 * np.sin(y * 0.09 + 1.5 * np.sin(x * 0.04)) * np.clip((1450 - y) / 100, 0, 1)    # folds
    d = d + 3.0 * np.sin(x * 0.06 + y * 0.015) * np.clip((1180 - y) / 100, 0, 1)
    d = np.maximum(d, np.maximum(y - 1545, 930 - y))
    rag = 14 * np.sin(y * 0.11) + 9 * np.sin(z * 0.2 + y * 0.05)
    d = np.maximum(d, -(sph(p, V(225, 1475, 0), 135) + rag))                          # torn off the left shoulder
    d = np.maximum(d, -(rbox(p, V(0, 1320, -150), V(46 + 0.4 * rag.mean() * 0, 200, 70), 20) + 0.7 * rag))   # down the spine
    vn = np.maximum(np.abs(x) - (25 + np.clip(y - 1330, 0, 300) * 0.55), z - 0)            # open collar
    d = np.maximum(d, -np.maximum(vn, 1300 - y))
    for i in range(4):                                                               # buttons
        d = np.minimum(d, sph(p, V(-26, 1300 - i * 75, 150 - 8 * i), 7))
    col = np.maximum(np.abs(rcone(p, V(0, 1470, 5), V(0, 1545, 25), 78, 66)) - 6, np.maximum(np.abs(y - 1505) - 30, 1300 - y))   # collar
    col = np.maximum(col, -np.maximum(np.abs(x) - 35, -z))
    d = np.minimum(d, col)
    for s_ in (-1, 1):                                                               # shoulder seams
        d = np.minimum(d, np.maximum(np.maximum(tor - 12.5, -(tor - 6)), np.abs(x - s_ * 150) - 2.5 + 0 * y))
    d = np.maximum(d, np.maximum(y - 1545, 930 - y))
    return d
def straps(p, tor):
    """leather braces: front from the belt over the shoulders, crossed on the back"""
    x, y, z = p[:, 0], p[:, 1], p[:, 2]
    base = tor - 15
    d = None
    for s in (-1, 1):
        fx = s * (78 + np.clip(y - 990, 0, 500) * 0.06)
        fr = np.maximum(np.abs(x - fx) - 20, np.maximum(-z + 10, np.maximum(y - 1500, 975 - y)))
        bx = s * (100 - np.clip(1480 - y, 0, 500) * 0.17)                           # the two cross at the back
        bk = np.maximum(np.abs(x - bx) - 20, np.maximum(z + 10, np.maximum(y - 1500, 975 - y)))
        top = np.maximum(np.abs(x - s * 120) - 22, 1440 - y)
        r = np.minimum(np.minimum(fr, bk), top)
        d = r if d is None else np.minimum(d, r)
    return np.maximum(base, d)
def belt(p):
    y = p[:, 1]
    dw = np.minimum(pelvis(p), ell(p, V(0, 1105, 12), V(138, 150, 100))) - 24
    b = np.maximum(dw - 12, np.abs(y - 975) - 24)
    bk = rbox(p, V(-30, 975, 132), V(32, 28, 9), 4)
    bk = np.maximum(bk, -rbox(p, V(-30, 975, 140), V(19, 15, 9), 3))
    return b, bk
def apron(p, tor):
    """the butcher's apron: heavy leather from the chest to below the knees, a strap round the neck,
    tied at the back; a stitched pocket, rivets, cut and scored all over"""
    x, y, z = p[:, 0], p[:, 1], p[:, 2]
    rr = np.sqrt((x * 0.9) ** 2 + (z + 40) ** 2)
    sl = 0.10 * np.clip(990 - y, 0, 600)
    lo = np.abs(rr - 170 - sl - 7 * np.sin(x * 0.05) * np.clip((900 - y) / 300, 0, 1)) - 5.5
    hem = 455 + 40 * np.sin(x * 0.045 + 0.8) + 22 * np.sin(x * 0.13) + 14 * np.sin(x * 0.31)
    lo = np.maximum(lo, np.maximum(y - 1000, hem - y))
    lo = np.maximum(lo, np.maximum(np.abs(x) - 190 - 0.12 * np.clip(990 - y, 0, 600), 40 - z))
    bib = np.abs(tor - 30) - 5.5                                                # over the shirt and braces
    bw = 92 + np.clip(1390 - y, 0, 400) * 0.13
    top = 1395 - 0.004 * x * x                                                  # rounded top corners
    bib = np.maximum(bib, np.maximum(np.abs(x) - bw, np.maximum(y - top, 990 - y)))
    bib = bib + 2.2 * np.sin(y * 0.05 + 0.6 * np.sin(x * 0.04)) * np.clip((1350 - y) / 100, 0, 1)    # heavy hide sags
    bib = np.maximum(bib, 30 - z)
    d = np.minimum(lo, bib)
    d = d + 1.6 * np.sin(y * 0.07 + 1.3 * np.sin(x * 0.03)) * np.clip((1000 - y) / 80, 0, 1)      # creases where it bends
    for c in (V(70, 640, 200), V(-110, 560, 200), V(10, 760, 190), V(150, 520, 160)):              # holes, cuts
        d = np.maximum(d, -(sph(p * V(1, 0.6, 1), c * V(1, 0.6, 1), 18)))
    for x0, y0, a_ in ((-40, 860, 0.5), (60, 1180, -0.3), (-80, 1250, 0.2), (95, 700, 0.9), (-20, 1080, -0.6)):  # knife scores
        dd = np.abs((x - x0) * math.sin(a_) - (y - y0) * math.cos(a_)) - 1.6
        along = np.abs((x - x0) * math.cos(a_) + (y - y0) * math.sin(a_)) - 45
        d = np.maximum(d, -np.maximum(np.maximum(dd, along), z - 0))
    # pocket on the front with a stitched rim
    pk = np.maximum(np.abs(rr - 170 - sl) - 10.5, np.maximum(np.abs(x - 70) - 62, np.abs(y - 820) - 55))
    pk = np.maximum(pk, 40 - z)
    rim = np.maximum(pk + 1.5, -np.maximum(np.abs(x - 70) - 55, np.abs(y - 820) - 48))
    d = np.minimum(d, pk)
    # neck strap and the ties at the back
    ns = None
    for s_ in (-1, 1):
        a0 = V(s_ * 88, 1365, 0); a0[2] = 140
        r_ = rcone(p, a0, V(s_ * 70, 1520, 40), 13, 13); r_ = np.maximum(r_, np.abs((p - a0) @ V(s_, 0, 0.3)) - 3.5 - 1e3 * 0)
        ns = r_ if ns is None else np.minimum(ns, r_)
    ns = np.minimum(ns, np.maximum(torus(p, V(0, 1520, -10), nrm(V(0, 1, -0.25)), 80, 11), z - 40))
    ties = np.maximum(np.abs(np.minimum(pelvis(p), ell(p, V(0, 1105, 12), V(138, 150, 100))) - 34) - 5, np.maximum(np.abs(y - 990) - 11, z + 20))
    bow = np.minimum(ell(p, V(-38, 992, -150), V(38, 18, 9)), ell(p, V(38, 992, -150), V(38, 18, 9)))
    bow = np.minimum(bow, sph(p, V(0, 990, -150), 14))
    tl = np.minimum(rcone(p, V(-5, 985, -150), V(-30, 860, -148), 7, 6), rcone(p, V(5, 985, -150), V(25, 870, -150), 7, 6))
    rv = None
    for c in (V(-88, 1362, 0), V(88, 1362, 0), V(-125, 1000, 0), V(125, 1000, 0)):
        c = c.copy(); c[2] = 152 if c[1] > 1200 else 150
        r2 = sph(p, c, 7); rv = r2 if rv is None else np.minimum(rv, r2)
    return mn(d, ns, ties, bow, tl), rv, rim
def bracer(p):
    """leather guard laced on the right forearm (the hand that holds the meat)"""
    j = JR; a = j['el'] + (j['wr'] - j['el']) * 0.30; b = j['wr'] + (j['el'] - j['wr']) * 0.06
    g = rcone(p, a, b, 50, 41)
    g = np.maximum(np.abs(g) - 4.5, np.abs((p - (a + b) / 2) @ nrm(b - a)) - float(np.linalg.norm(b - a)) / 2)
    st = None
    for t in (0.2, 0.75):
        c = a + (b - a) * t; s_ = np.maximum(np.abs(rcone(p, a, b, 55, 46)) - 3.5, np.abs((p - c) @ nrm(b - a)) - 9)
        st = s_ if st is None else np.minimum(st, s_)
    bk = None
    for t in (0.2, 0.75):
        c = a + (b - a) * t + V(0, 0, 50 - 6 * t); b_ = rbox(p, c, V(13, 11, 5), 2)
        bk = b_ if bk is None else np.minimum(bk, b_)
    return g, st, bk
def body(p):
    sk = skin(p); tor = np.minimum(torso(p), pelvis(p))
    lg = legs(p); bt, so, la = boots(p); bl, bk = belt(p)
    ap, rivets, rim = apron(p, tor); sh = shirt(p, tor); stp = straps(p, tor); bg, bst, bbk = bracer(p)
    pl = plaga_arm(p); sp = smin(spikes_arm(p), spine_spikes(p), 6)
    spb = None                                                         # flesh round the spine spikes' roots
    for y in (1170, 1235, 1300, 1365, 1430, 1490):
        s_ = ell(p, V(0, y, -110), V(34, 30, 26)); spb = s_ if spb is None else smin(spb, s_, 12)
    return {SKIN: mn(sk, knees(p)), CLOTH: sh, PANTS: mn(lg, seams(p, lg)), BOOT: bt, SOLE: so, LEATHER: mn(ap, bl, stp, la, bg, bst, rim),
            IRON: mn(bk, rivets, bbk), PLAGA: mn(pl, spb), BONE: sp}
BODY_BOX = (V(-820, -5, -330), V(1010, 1600, 330))

# ---- hood: a burlap sack tied at the neck, eye holes torn in it, a sewn mouth ----------------------
def hood(p):
    x, y, z = p[:, 0], p[:, 1], p[:, 2]
    c = HEAD + V(0, 18, -6)
    h = ell(p, c, V(112, 132, 120))
    h = smin(h, rcone(p, c + V(0, 60, -20), c + V(0, 250, -120), 70, 14), 50)           # the pointed, slumped top
    h = smin(h, ell(p, HEAD + V(0, -55, 30), V(98, 80, 96)), 30)                          # over the jaw
    # loose cloth: big soft folds, sagging
    h = h + 9 * np.sin(y * 0.035 + x * 0.03) * np.sin(z * 0.04 + 1.0) + 3 * np.sin(x * 0.13 + y * 0.07)
    gath = np.clip((HEAD[1] - 40 - y) / 70, 0, 1)                                      # gathered by the rope round the neck
    h = h + 6 * gath * np.sin(np.arctan2(x, z - HEAD[2] + 1e-3) * 11)
    h = h + 4 * np.clip((y - HEAD[1] - 60) / 80, 0, 1) * np.sin(x * 0.05 + z * 0.04 + y * 0.02)
    # drapes over the shoulders like a short cape
    tor = np.minimum(torso(p), neck_head(p))
    cape = np.abs(tor - 22) - 6
    hem = 1385 + 30 * np.sin(x * 0.04 + 1) + 18 * np.sin(x * 0.11) + 12 * np.sin(z * 0.15)
    cape = np.maximum(cape, np.maximum(y - 1560, hem - y))
    cape = np.maximum(cape, np.abs(x) - 250 + 0 * y)
    cape = cape + 3 * np.sin(np.arctan2(x, z + 1e-3) * 9 + y * 0.03)
    d = smin(h, cape, 25)
    # torn eye holes, a dark inside with the eyes glowing deep in it
    eyes = None; glint = None; dark = None
    for s in (-1, 1):
        e = ell(p, HEAD + V(s * 38, 24, 118), V(26, 21, 60)) + 4 * np.sin(x * 0.5 + y * 0.4)
        eyes = e if eyes is None else np.minimum(eyes, e)
        g = sph(p, HEAD + V(s * 35, 20, 82), 5.5); glint = g if glint is None else np.minimum(glint, g)
    d = np.maximum(d, -eyes)
    d = np.maximum(d, -np.maximum(groove, -(h + 3)) ) if False else d
    dark = np.maximum(ell(p, HEAD + V(0, 18, 60), V(85, 50, 45)), -eyes - 1)
    dark = np.maximum(ell(p, HEAD + V(0, 18, 55), V(80, 45, 50)), 0 * x - 1)
    # sewn mouth: a ridge with cross-stitches
    m0 = HEAD + V(0, -40, 0)
    groove = np.maximum(np.abs(y - m0[1] - 0.002 * x * x) - 3.5, np.abs(x) - 55)
    seam = np.maximum(h + 2, -h - 4) + 1e3 * 0                                        # (no raised band)
    seam = np.maximum(seam, 1e3 + 0 * x)
    st = None
    for i in range(7):
        xx = -48 + i * 16
        q = rcone(p, V(xx - 5, m0[1] + 0.002 * xx * xx + 14, 0), V(xx + 5, m0[1] + 0.002 * xx * xx - 14, 0), 3.2, 3.2)
        q = np.maximum(q, -(h + 6)); q = np.maximum(q, h - 3.5)
        st = q if st is None else np.minimum(st, q)
    # centre seam down the front, stitched
    cs = np.maximum(np.maximum(np.abs(x) - 3.5, h - 3.5), np.maximum(-(h + 3), np.maximum(y - (HEAD[1] + 175), (HEAD[1] + 60) - y)))
    rope = torus(p, V(0, 1520, 18), nrm(V(0, 1, 0.12)), 62, 9) + 1.5 * np.sin(np.arctan2(x, z) * 16)
    knot = sph(p, V(30, 1505, 82), 18)
    rope = smin(rope, np.minimum(knot, np.minimum(rcone(p, V(30, 1500, 85), V(42, 1395, 98), 7, 6), rcone(p, V(30, 1500, 85), V(12, 1410, 102), 7, 6))), 6)
    d = np.maximum(d, -np.maximum(groove - 0.0, np.abs(h) - 3.0))                     # the sewn-up mouth sinks in
    # a sewn-on patch over the right temple, with big stitches round it
    pc = HEAD + V(-78, 70, 55)
    pt = np.maximum(np.maximum(h - 3.0, -h - 6), ell(p, pc, V(60, 48, 70)))
    d = np.minimum(d, pt)
    for i in range(10):
        a_ = i * 2 * math.pi / 10; c_ = pc + V(52 * math.cos(a_) * 0.55, 42 * math.sin(a_), 52 * math.cos(a_) * 0.75)
        q_ = np.maximum(sph(p, c_, 4.5), np.abs(h - 2) - 4)
        st = np.minimum(st, q_)
    # frayed threads hanging from the eye holes
    for s_ in (-1, 1):
        for k in range(3):
            t0 = HEAD + V(s_ * (28 + 12 * k), 2 - 4 * k, 112 - 4 * k)
            st = np.minimum(st, rcone(p, t0, t0 + V(s_ * 4, -28 - 10 * k, 4), 1.8, 1.2))
    return {SACK: d, SOLE: dark, EYE: glint, LEATHER: mn(seam, st, cs, rope)}
HOOD_BOX = (V(-290, 1340, -280), V(290, 1920, 300))

# ---- right hand on the sickle's handle ------------------------------------------------------------
FD_R = nrm(JR['wr'] - JR['el']); GRIP = JR['wr'] + FD_R * 78
HDIR = nrm(V(0, 0, 1))                                  # the handle runs forward through the fist (bind)
def fist(p):
    d = ell(p, GRIP - FD_R * 14, V(50, 55, 52))
    d = smin(d, rcone(p, JR['wr'] - FD_R * 40, JR['wr'] + FD_R * 20, 36, 46), 18)
    for i in range(4):
        c = GRIP + HDIR * ((i - 1.5) * 24) + FD_R * 4
        f = torus(p, c, HDIR, 30, 12.5 - 0.8 * abs(i - 1.5))
        f = np.maximum(f, -((p - c) @ FD_R) - 18)
        d = smin(d, f, 6)
    side = nrm(np.cross(HDIR, FD_R))
    th = rcone(p, JR['wr'] + FD_R * 30 + side * 30, GRIP + HDIR * 40 + side * 26, 15, 12)       # thumb over the fingers
    d = smin(d, th, 8)
    for i in range(4):                                                                         # knuckles
        d = smin(d, sph(p, GRIP + HDIR * ((i - 1.5) * 24) + FD_R * 26 - side * 22, 11), 6)
    rag = np.maximum(np.abs(rcone(p, JR['wr'] - FD_R * 45, JR['wr'] + FD_R * 8, 40, 40)) - 4, -1e3 + 0 * d)
    return {SKIN: d, CLOTH: rag}
def box_of(pts, m):
    pts = np.array(pts); return (pts.min(0) - m).astype(f32), (pts.max(0) + m).astype(f32)
FIST_BOX = box_of([GRIP, JR['wr'] - FD_R * 60], 95)

# ---- the left hand: long fingers ending in curved talons of bone ---------------------------------
FD_L = nrm(JL['wr'] - JL['el'])
def claw(p):
    w = JL['wr']
    d = ell(p, w + FD_L * 62, V(78, 40, 66))                              # palm, swollen
    d = smin(d, rcone(p, w - FD_L * 40, w + FD_L * 30, 50, 46), 18)
    tal = None
    fing = [(-48, 0.10, 210), (-16, 0.0, 240), (16, -0.04, 230), (46, -0.12, 195)]
    for zo, spread, L in fing:
        b = w + FD_L * 110 + V(0, -4, zo)
        d1 = nrm(FD_L + V(0, -0.15, spread))
        k1 = b + d1 * L * 0.45
        d2 = nrm(d1 + V(0, -0.55, 0))
        k2 = k1 + d2 * L * 0.32
        f = smin(rcone(p, b, k1, 15, 12), rcone(p, k1, k2, 12, 10), 6)
        f = smin(f, sph(p, k1, 13), 5)
        d = smin(d, f, 10)
        # talon: a curved horn from the last knuckle, bending down and back
        pts = [k2]; dd = d2
        for i in range(5):
            dd = nrm(dd + V(0, -0.22, 0) - FD_L * 0.08)
            pts.append(pts[-1] + dd * (L * 0.16))
        for i in range(5):
            r0 = 11 - 9 * i / 5; r1 = 11 - 9 * (i + 1) / 5
            t_ = rcone(p, pts[i], pts[i + 1], r0, max(r1, 1.2))
            tal = t_ if tal is None else np.minimum(tal, t_)
    # thumb with its own talon
    tb = w + FD_L * 45 + V(0, -20, 60); td = nrm(V(0.6, -0.4, 0.7))
    th = rcone(p, tb, tb + td * 75, 16, 12); d = smin(d, th, 10)
    tp = tb + td * 75
    tal = np.minimum(tal, rcone(p, tp, tp + nrm(td + V(0, -0.6, 0)) * 85, 10, 1.5))
    # Plaga fibres over the back of the hand
    pl = None
    for k in range(3):
        a = w - FD_L * 40 + V(0, 38, -30 + 30 * k); b = w + FD_L * 120 + V(0, 28, -45 + 45 * k)
        s_ = rcone(p, a, b, 13, 9); pl = s_ if pl is None else smin(pl, s_, 6)
    return {SKIN: d, BONE: tal, PLAGA: pl}
CLAW_BOX = box_of([JL['wr'] - FD_L * 60, JL['wr'] + FD_L * 420 + V(0, -260, 0), JL['wr'] + V(0, 60, 150), JL['wr'] + V(0, 60, -150)], 40)

# ---- accessories ---------------------------------------------------------------------------------
def acc(p):
    """the butcher's belt: a cleaver on a ring at the right hip, a knife in its sheath at the left, the
    sharpening steel behind it, two meat hooks on a chain at the back"""
    x, y, z = p[:, 0], p[:, 1], p[:, 2]
    clips = None
    for s in (-1, 1):
        c = rbox(p, V(s * 79, 1005, 132), V(19, 15, 6), 3); clips = c if clips is None else np.minimum(clips, c)
    # cleaver: hanging blade down, flat to the thigh
    R1 = frame(nrm(V(0.08, -1, 0.15)), V(0, 0, 1))
    q = (p - V(-258, 950, 40)) @ R1.T
    cb = rbox(q, V(105, 0, 0), V(85, 55, 3.5), 2)
    cb = np.maximum(cb, -(ln(q[:, [0, 1]] - np.array([38, -30], np.float32)) - 11))                       # the hang hole
    cb = np.maximum(cb, -np.maximum(np.abs(q[:, 1] + 55) - 3, np.abs(q[:, 0] - 130) - 8))                 # a notch
    ch = ccyl(q, V(40, 55, 0), V(40, 170, 0), 15, 4)
    ring = torus(p, V(-232, 948, 40), nrm(V(0, 0, 1)), 26, 5)
    rivc = np.minimum(sph(q, V(40, 90, 15), 4.5), sph(q, V(40, 130, 15), 4.5))
    # sheath + knife on the left hip
    R2 = frame(nrm(V(-0.05, -1, 0.12)), V(1, 0, 0))
    q2 = (p - V(262, 900, 20)) @ R2.T
    sheath = rbox(q2, V(115, 0, 0), V(120, 24, 11), 6) + 0.08 * np.clip(q2[:, 0] - 60, 0, 200)
    sheath = np.maximum(sheath, q2[:, 0] - 240)
    kh = ccyl(q2, V(-120, 0, 0), V(-6, 0, 0), 15, 4); bol = ccyl(q2, V(-8, 0, 0), V(6, 0, 0), 19, 2)
    loop = np.maximum(np.abs(rbox(q2, V(0, 0, 0), V(30, 36, 18), 6)) - 3, np.abs(q2[:, 0] - 20) - 14)
    # sharpening steel behind it
    R3 = frame(nrm(V(0.05, -1, -0.1)), V(1, 0, 0))
    q3 = (p - V(240, 930, -95)) @ R3.T
    st = ccyl(q3, V(20, 0, 0), V(300, 0, 0), 7, 1)
    st = st + 0.6 * np.sin(q3[:, 0] * 1.2)
    sh_ = ccyl(q3, V(-95, 0, 0), V(0, 0, 0), 15, 4); gd = ccyl(q3, V(0, 0, 0), V(18, 0, 0), 22, 3)
    eye = torus(q3, V(-110, 0, 0), V(0, 0, 1), 12, 3.5)
    # two meat hooks on a short chain, right back
    hk = None; chn = None
    for i, (hx, hz) in enumerate(((-200, -150), (-140, -190))):
        top = V(hx, 980, hz)
        for k in range(3):
            c = top + V(0, -22 * k - 10, 0)
            l_ = torus(p, c, V(1, 0, 0) if k % 2 else V(0, 0, 1), 9, 3.2)
            chn = l_ if chn is None else np.minimum(chn, l_)
        b0 = top + V(0, -80, 0)
        sh2 = rcone(p, b0, b0 + V(0, -110 - 20 * i, 0), 5.5, 5.5)
        cv = top + V(0, -190 - 20 * i, 0) + V(0, 0, 32)
        qq = p - cv; r_ = np.sqrt(qq[:, 1] ** 2 + qq[:, 2] ** 2)
        arc = np.maximum(np.abs(r_ - 32) - 5.5 + 0 * qq[:, 0], np.abs(qq[:, 0]) - 5.5)
        arc = np.maximum(arc, qq[:, 1] - 8 * 0 - 0)                                                     # lower half
        arc = np.maximum(arc, -(qq[:, 2] + 30) * 0 + (qq[:, 2] > 26) * 1e3)
        tip = rcone(p, cv + V(0, 0, 32), cv + V(0, 30, 34), 5.5, 1.2)
        h_ = mn(sh2, arc, tip)
        hk = h_ if hk is None else np.minimum(hk, h_)
    return {IRON: mn(clips, cb, ring, st, bol, gd, eye, hk, chn), WOOD: mn(ch, kh, sh_), LEATHER: mn(sheath, loop), CHAIN: rivc}
ACC_BOX = (V(-330, 480, -300), V(330, 1060, 240))

# ---- weapon: a rusted sickle ---------------------------------------------------------------------
WB = np.stack([HDIR, FD_R, np.cross(HDIR, FD_R)])                   # local x along the handle, y along the forearm: hanging, the blade curves down in front of the leg
def weapon(p):
    q = (p - GRIP) @ WB.T
    x, y, z = q[:, 0], q[:, 1], q[:, 2]
    hd = ccyl(q, V(-150, 0, 0), V(150, 0, 0), 17, 4)
    hd = hd + 1.2 * np.sin(x * 0.4) * np.sin(np.arctan2(z, y) * 3)
    knob = ccyl(q, V(-170, 0, 0), V(-148, 0, 0), 21, 6)
    fer = ccyl(q, V(150, 0, 0), V(185, 0, 0), 20, 3)                                     # iron ferrule
    # blade: a hook of rusted iron in the handle's vertical plane, opening back towards the wielder
    C = V(240, 205, 0); R_ = 205.0
    u = x - C[0]; v = y - C[1]; ang = np.arctan2(v, u)                       # 0 = forward, pi/2 = up
    r = np.sqrt(u * u + v * v)
    a0, a1 = -math.pi / 2 - 0.10, math.pi * 0.92                             # from under the ferrule round to the tip
    t = np.clip((ang - a0) / (a1 - a0), 0, 1)
    wdt = 58 * (1 - t) ** 0.55 + 3
    inner = R_ - wdt                                                        # cutting edge on the inside
    rad = np.maximum(r - R_, inner - r)
    edge = np.clip((r - inner) / np.maximum(wdt, 1), 0, 1)                   # thin towards the edge
    th = 1.0 + 3.6 * edge
    bl = np.maximum(rad, np.abs(z) - th)
    inrange = (ang >= a0) & (ang <= a1)
    bl = np.where(inrange, bl, 1e3)
    tipd = sph(q, C + V(R_ * math.cos(a1), R_ * math.sin(a1), 0) - V(math.cos(a1 + 1.4), math.sin(a1 + 1.4), 0) * 8, 6)
    neck = rcone(q, V(170, 0, 0), C + V(R_ * math.cos(a0), R_ * math.sin(a0), 0) + V(-10, 20, 0), 9, 8)
    bl = np.minimum(np.minimum(bl, tipd), np.maximum(neck, np.abs(z) - 4.5))
    nicks = None
    for an_ in (0.3, 1.1, 1.9):                                              # notches in the edge
        c = C + V((inner_r := R_ - 30) * math.cos(an_), inner_r * math.sin(an_), 0)
        n_ = sph(q, c, 9); nicks = n_ if nicks is None else np.minimum(nicks, n_)
    bl = np.maximum(bl, -nicks)
    wrap = ccyl(q, V(-110, 0, 0), V(-20, 0, 0), 19.5, 3) + 1.5 * np.sin(x * 0.5 + np.arctan2(z, y))
    return {WOOD: hd, IRON: mn(bl, fer), LEATHER: wrap, CHAIN: knob}
def wbox():
    c = [GRIP + WB.T @ V(x, y, z) for x in (-190, 470) for y in (-40, 430) for z in (-30, 30)]
    return box_of(c, 12)
WEAPON_BOX = wbox()
PARTS = [('body', body, BODY_BOX, 3.5, 13000), ('mask', hood, HOOD_BOX, 2.0, 2200), ('fist', fist, FIST_BOX, 2.0, 500),
         ('claw', claw, CLAW_BOX, 2.0, 1500), ('acc', acc, ACC_BOX, 2.0, 2200), ('weapon', weapon, WEAPON_BOX, 2.0, 1200)]
def field(fn, p):
    g = fn(p); mats = list(g.keys()); D = np.stack([g[m] for m in mats])
    return D.min(0), np.array(mats)[D.argmin(0)]
