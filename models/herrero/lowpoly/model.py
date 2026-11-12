"""EL HERRERO - original heavy enemy (village blacksmith). mm, y up, faces +z, its right = -x."""
import numpy as np, math
from sdf import *
SKIN, PANTS, BOOT, LEATHER, IRON, WOOD, CHAIN, SOLE, CLOTH, HOT, PLAGA, EYE = range(12)

# ---- skeleton -----------------------------------------------------------------------------------
def J(s):
    d = dict(hip=V(s*215, 1040, -10), knee=V(s*305, 570, 75), ank=V(s*285, 120, -5),
             sh=V(s*465, 1690, 75))
    d.update(sh=V(s*455, 1665, 60)); d.update(el=d['sh'] + V(s*442, 0, 0)); d.update(wr=d['el'] + V(s*400, 0, 0))   # T-pose (bind)
    return d
GROWTH = [((165, 1835, 30), 66), ((235, 1800, -55), 54), ((115, 1880, -45), 46), ((285, 1770, 40), 44), ((95, 1820, 120), 38), ((200, 1870, -10), 34),
          ((330, 1740, -150), 46), ((250, 1640, -250), 40), ((560, 1745, 80), 44), ((640, 1700, -40), 36), ((760, 1760, 70), 30),
          ((1010, 1740, 90), 40), ((1090, 1690, -20), 34), ((1180, 1745, 60), 28), ((300, 1560, 250), 34)]
# the Plaga breaking out of the neck: tendrils (bind pose)
TENDRILS = [[(170, 1850, 20), (225, 1965, -10), (325, 2040, 10), (425, 2020, 60)],
            [(220, 1820, -60), (300, 1890, -160), (365, 1840, -255), (355, 1735, -295), (300, 1690, -300)],
            [(120, 1850, 110), (160, 1955, 190), (245, 1995, 262)]]
def plaga(p):
    d = None
    for path in TENDRILS:
        n = len(path) - 1
        for i in range(n):
            r0 = 40 - 20 * i / n; r1 = 40 - 20 * (i + 1) / n
            seg = rcone(p, V(*path[i]), V(*path[i + 1]), r0, r1)
            d = seg if d is None else smin(d, seg, 9)
    return d
JR, JL = J(-1), J(1)
HEAD = V(0, 1872, 352)
def fore_r(j, s): return (132 if s < 0 else 128), (80 if s < 0 else 78)

# ---- body ---------------------------------------------------------------------------------------
def torso(p):
    d = ell(p, V(0, 1285, 105), V(395, 305, 335))                          # belly
    d = smin(d, ell(p, V(0, 1575, 75), V(435, 275, 295)), 60)              # chest
    d = smin(d, ell(p, V(0, 1730, -75), V(330, 235, 250)), 90)             # hump: a dome, not a slab
    d = smin(d, ell(p, V(0, 1440, -120), V(300, 340, 215)), 70)            # back, tapering to the waist
    for s in (-1, 1):
        d = smin(d, ell(p, V(s*185, 1560, 300), V(195, 140, 95)), 40)      # pecs
        d = smin(d, ell(p, V(s*235, 1545, -175), V(150, 215, 120)), 55)    # lats (wedge towards the waist)
        d = smin(d, ell(p, V(s*190, 1700, -235), V(125, 115, 75)), 35)     # shoulder blades
        d = smin(d, ell(p, V(s*75, 1420, -300), V(60, 250, 55)), 30)       # erectors
        d = smin(d, ell(p, V(s*290, 1250, -40), V(150, 130, 220)), 50)     # love handles
    for i in range(0):
        d = smin(d, sph(p, V(0, 1240 + i * 62, -322 - 22 * math.sin(i * 0.42) + (i > 6) * 14 * (i - 6)), 21), 10)
    return d
def pelvis(p): return ell(p, V(0, 1085, 5), V(335, 205, 250))
def arms(p):
    """T-pose; real arm anatomy instead of tubes: deltoid cap, biceps / triceps split, brachioradialis and
    flexor masses that taper to a narrow wrist, bony elbow and wrist"""
    d = None
    for s, j in ((-1, JR), (1, JL)):
        ra, rb = fore_r(j, s); X = V(s, 0, 0)
        a = rcone(p, j['sh'], j['el'], 128, 104)
        a = smin(a, ell(p, j['sh'] + V(s*35, 28, -5), V(178, 150, 160)), 26)                 # deltoid
        a = smin(a, ell(p, j['sh'] + X*235 + V(0, 8, 78), V(165, 98, 88)), 16)               # biceps
        a = smin(a, ell(p, j['sh'] + X*215 + V(0, 22, -82), V(185, 92, 80)), 16)             # triceps (long head)
        a = smin(a, ell(p, j['sh'] + X*300 + V(0, -55, -60), V(120, 70, 72)), 16)            # triceps (lateral)
        f = rcone(p, j['el'], j['wr'], 100, rb)
        f = smin(f, ell(p, j['el'] + X*95 + V(0, 48, 30), V(165, 80, 84)), 16)               # brachioradialis
        f = smin(f, ell(p, j['el'] + X*120 + V(0, -42, 5), V(170, 84, 92)), 16)              # flexors
        f = smin(f, ell(p, j['el'] + X*150 + V(0, 10, -62), V(150, 66, 62)), 16)             # extensors
        a = smin(a, f, 22)
        a = smin(a, sph(p, j['el'] + V(0, -8, -84), 58), 14)                                 # olecranon
        a = smin(a, sph(p, j['el'] + V(0, -50, 20), 50), 14)                                 # medial epicondyle
        a = smin(a, sph(p, j['wr'] - X*18 + V(0, 34, -52), 30), 10)                          # ulna head
        d = a if d is None else np.minimum(d, a)
    return d
def neck_head(p):
    d = rcone(p, V(0, 1730, 130), V(0, 1830, 300), 165, 130)
    for s in (-1, 1): d = smin(d, rcone(p, V(s*60, 1830, 180), V(s*390, 1745, 60), 120, 150), 60)   # traps
    for s in (-1, 1):
        d = smin(d, rcone(p, V(s*28, 1688, 262), V(s*360, 1742, 130), 21, 26), 14)                      # clavicle
        d = smin(d, rcone(p, V(s*95, 1850, 250), V(s*35, 1700, 270), 26, 22), 14)                       # sternomastoid
    h = ell(p, HEAD, V(118, 138, 138))
    h = smin(h, ell(p, HEAD + V(0, -75, 30), V(102, 85, 105)), 30)                        # jaw
    for s in (-1, 1): h = smin(h, ell(p, HEAD + V(s*118, -5, -15), V(18, 38, 26)), 12)    # ears
    return smin(d, h, 35)
def skin(p):
    d = su(38, torso(p), arms(p), neck_head(p))
    for c, r in GROWTH: d = smin(d, sph(p, V(*c), r), 22)                  # Plaga growths, left neck / shoulder / arm
    return d
def legs(p):
    d = pelvis(p)
    for s, j in ((-1, JR), (1, JL)):
        l = rcone(p, j['hip'], j['knee'], 205, 138)
        l = smin(l, ell(p, (j['hip'] + j['knee'])/2 + V(s*10, 40, 70), V(150, 220, 130)), 40)   # quad
        l = smin(l, sph(p, j['knee'] + V(0, 0, 40), 118), 30)                                    # knee
        l = smin(l, rcone(p, j['knee'], j['ank'] + V(0, 150, 0), 140, 112), 30)
        l = smin(l, ell(p, (j['knee'] + j['ank'])/2 + V(0, 60, -70), V(110, 170, 105)), 35)      # calf
        d = smin(d, l, 60)
    # cloth folds
    d = d + 9.0 * np.sin(p[:, 1] * 0.05 + p[:, 0] * 0.025 + 2.0 * np.sin(p[:, 2] * 0.02)) * np.clip((p[:, 1] - 250) / 200, 0, 1) * np.clip((1000 - p[:, 1]) / 200, 0, 1)
    return d
def boots(p):
    d = None; sole = None; st = None; bk = None
    for s, j in ((-1, JR), (1, JL)):
        R = frame(nrm(V(s*0.22, 0, 1)), V(0, 1, 0))                     # toes out
        c = j['ank'] * V(1, 0, 1)
        sh = rcone(p, j['ank'] + V(0, 235, 5), j['ank'] + V(0, -30, 0), 128, 108)
        ft = smin(rbox(p, c + V(s*14, 62, 70), V(175, 62, 100), 45, R), ell(p, c + V(s*36, 70, 195), V(98, 72, 95)), 25)
        b = smin(sh, ft, 30)
        b = b + 4.0 * np.sin(p[:, 1] * 0.09) * np.clip((p[:, 1] - 150) / 60, 0, 1)        # creased shaft
        so = np.maximum(smin(ft, sh, 30) - 9, p[:, 1] - 30)                               # welted sole
        so = np.maximum(so, -p[:, 1])
        b = np.maximum(b, 20 - p[:, 1])
        cuff = rcone(p, j['ank'] + V(0, 240, 5), j['ank'] + V(0, 200, 5), 128, 128) - 15
        b = np.minimum(b, np.maximum(cuff, np.abs(p[:, 1] - (j['ank'][1] + 222)) - 26))
        for yk in ():
            s_ = np.maximum(sh - 9, np.abs(p[:, 1] - yk - 0.15 * (p[:, 0] - c[0]) * s) - 15)
            st = s_ if st is None else np.minimum(st, s_)
            k_ = rbox(p, V(c[0] + s * 118, yk + 18, 20), V(12, 22, 24), 4)
            bk = k_ if bk is None else np.minimum(bk, k_)
        d = b if d is None else np.minimum(d, b); sole = so if sole is None else np.minimum(sole, so)
    return d, sole, np.full(len(p), 1e3, np.float32), np.full(len(p), 1e3, np.float32)
def waist(p): return np.minimum(pelvis(p), ell(p, V(0, 1285, 105), V(395, 305, 335)))
def apron(p, dt=None):
    x, y, z = p[:, 0], p[:, 1], p[:, 2]
    if dt is None: dt = np.minimum(torso(p), pelvis(p))
    up = dt - 24
    wtop = 175 + np.clip((1660 - y) / 300, 0, 1) * 175                   # bib widens downwards
    up = mn(np.maximum(np.maximum(up, np.abs(x) - wtop), np.maximum(y - 1665, 1255 - y)))
    up = np.maximum(up, 60 - z)
    # hanging skirt: elliptic cylinder shell from the belly down to the knees, ragged hem
    rr = np.sqrt((x * 0.86) ** 2 + (z - 60) ** 2)
    hem = 505 + 38 * np.sin(x * 0.021 + 1.3) + 22 * np.sin(x * 0.067)
    fold = 9 * np.sin(x * 0.05) * np.clip((1150 - y) / 400, 0, 1)
    sk = np.abs(rr - 372 - fold) - 8
    sk = np.maximum(sk, np.maximum(y - 1275, hem - y))
    sk = np.maximum(sk, np.maximum(np.abs(x) - 345, 100 - z))
    d = smin(up, sk, 12)
    # straps over the shoulders, down the back
    ds = np.minimum(dt, neck_head(p)) - 22
    for s in ():
        xs = s * (165 + np.clip((y - 1650) / 150, 0, 1) * 40)
        reg = np.abs(x - xs) - 30
        reg = np.maximum(reg, np.where(z > 60, 1625 - y, 1130 - y))
        d = np.minimum(d, np.maximum(ds, reg))
    # big pocket
    pk = np.maximum(rr - (372 + 21), np.maximum(np.abs(x) - 150, np.maximum(np.abs(y - 880) - 95, 100 - z)))
    return d
def belt(p):
    y = p[:, 1]; x = p[:, 0]; z = p[:, 2]
    rr = np.sqrt((x * 0.86) ** 2 + (z - 60) ** 2)
    dw = np.minimum(waist(p) - 16, np.where(z > 100, rr - 388, 1e3))
    tilt = y - (1128 - 0.06 * z)
    b = np.maximum(dw - 19, np.abs(tilt) - 36)
    bk = rbox(p, V(0, 1105, 452), V(52, 46, 14), 8)                     # buckle
    bk = np.maximum(bk, -rbox(p, V(0, 1105, 462), V(30, 26, 14), 4))
    return b, bk
def body(p):
    sk = skin(p); lg = legs(p); bt, so, bst, bbk = boots(p); bl, bk = belt(p)
    ap = apron(p)
    kp = np.maximum(lg - 11, sph(p, JL['knee'] + V(0, 5, 70), 112))                        # knee patch
    rope = torus(p, JR['knee'] + V(4, -105, 12), nrm(V(0.05, 1, 0.12)), 138, 11)           # cord under the knee
    rope = np.minimum(rope, torus(p, JR['knee'] + V(4, -128, 10), nrm(V(-0.04, 1, 0.1)), 134, 11))
    # dirty linen bandage round the right upper arm (two turns), a rag tied on the right forearm
    x = p[:, 0]; ang = np.arctan2(p[:, 2] - JR['sh'][2], p[:, 1] - JR['sh'][1])
    bnd = np.maximum(sk - 7, np.abs(x + 735 - 16 * np.sin(ang) - 5 * np.sin(ang * 5)) - 52)
    bnd = np.minimum(bnd, np.maximum(sk - 10, np.abs(x + 772 + 26 * np.sin(ang + 1.0)) - 30))
    rag = np.maximum(sk - 8, np.abs(x + 1085 + 14 * np.sin(ang * 2 + 0.5)) - 26)
    rag = np.minimum(rag, rcone(p, V(-1085, 1665 + 98, 60 + 30), V(-1040, 1665 + 150, 60 + 75), 15, 7))      # knot ends
    rag = np.minimum(rag, rcone(p, V(-1085, 1665 + 98, 60 + 30), V(-1130, 1665 + 135, 60 - 10), 15, 7))
    return {SKIN: sk, PANTS: lg, BOOT: np.minimum(bt, so), LEATHER: mn(ap, bl), PLAGA: plaga(p)}
BODY_BOX = (V(-1420, -5, -480), V(1420, 2110, 560))

# ---- mask ----------------------------------------------------------------------------------------
MC = HEAD + V(0, -10, 0)
MA = math.radians(27)
def mask(p):
    """welded forge mask: two flat plates meeting at a prow, a slit, breathing slots, riveted bands"""
    q = p - MC; x, y, z = q[:, 0], q[:, 1], q[:, 2]
    ax = np.abs(x)
    wedge = ax * math.sin(MA) + z * math.cos(MA) - 152
    top = y * math.cos(0.42) + z * math.sin(0.42) - 168
    bot = -y * 0.83 + z * 0.56 - 172
    rnd = ell(p, MC, V(176, 222, 214))
    def plate(off): return mn(np.maximum(np.maximum(np.maximum(wedge, top), np.maximum(bot, ax - 136)) - off, np.maximum(-28 - z, rnd - off)))
    pl = plate(0.0)
    return {IRON: pl}
MASK_BOX = (HEAD - V(190, 235, 185), HEAD + V(190, 190, 215))

# ---- hands ---------------------------------------------------------------------------------------
HDIR = nrm(V(0, 0, -1))                            # weapon: from the grip to the anvil (bind: straight back)
FD_R = nrm(JR['wr'] - JR['el']); GRIP = JR['wr'] + FD_R * 105
def fist(p):
    d = ell(p, GRIP - FD_R * 22, V(86, 92, 84))
    d = smin(d, rcone(p, JR['wr'] - FD_R * 60, JR['wr'] + FD_R * 30, 84, 88), 30)
    for i in range(4):
        c = GRIP + HDIR * ((i - 1.5) * 41) + FD_R * 6
        f = torus(p, c, HDIR, 50, 22 - 1.5 * abs(i - 1.5))
        f = np.maximum(f, -((p - c) @ FD_R) - 30)                       # open at the wrist side
        d = smin(d, f, 10)
    side = nrm(np.cross(HDIR, FD_R))
    th = rcone(p, GRIP - FD_R * 50 + side * 55 - HDIR * 50, GRIP + FD_R * 5 + side * 72 - HDIR * 5, 30, 25)
    th = smin(th, rcone(p, GRIP + FD_R * 5 + side * 72 - HDIR * 5, GRIP + FD_R * 48 + side * 52 + HDIR * 30, 25, 21), 8)
    d = np.maximum(smin(d, th, 14), -((p - (JR['wr'] - FD_R * 41.3)) @ FD_R))      # B92: closed at the wrist (was cut open by its box)
    return {SKIN: d}
FD_L = nrm(JL['wr'] - JL['el'])
def claw(p):
    n = V(0, -1, 0.12); n = nrm(n - FD_L * (n @ FD_L)); w = np.cross(FD_L, n)
    R = np.stack([w, FD_L, n])
    d = rbox(p, JL['wr'] + FD_L * 95 + n * 4, V(82, 90, 36), 32, R)
    d = smin(d, rcone(p, JL['wr'] - FD_L * 60, JL['wr'] + FD_L * 30, 82, 86), 30)
    def chain(base, lens, angs, r0, r1, wj=0.0):
        nonlocal d
        a = base; ang = 0.0; f = None
        for i, (L, da) in enumerate(zip(lens, angs)):
            ang += math.radians(da)
            dr = FD_L * math.cos(ang) + n * math.sin(ang) + w * wj
            b = a + nrm(dr) * L
            t0, t1 = i / len(lens), (i + 1) / len(lens)
            seg = rcone(p, a, b, r0 + (r1 - r0) * t0, r0 + (r1 - r0) * t1)
            kn = sph(p, a, (r0 + (r1 - r0) * t0) * 1.12)                 # knuckle
            seg = np.minimum(seg, kn)
            f = seg if f is None else np.minimum(f, seg); a = b
        d = smin(d, f, 12)
    for off, sc, cu in ((-60, 0.92, 1.0), (-20, 1.05, 0.85), (20, 1.0, 0.95), (58, 0.82, 1.15)):
        chain(JL['wr'] + FD_L * 172 + w * off + n * 2, (72 * sc, 52 * sc, 40 * sc), (18 * cu, 42 * cu, 40 * cu), 25, 17, off * 0.0022)
    # thumb
    a = JL['wr'] + FD_L * 55 - w * 78 + n * 8
    b = a + nrm(FD_L * 0.55 - w * 0.75 + n * 0.35) * 70; c = b + nrm(FD_L * 0.75 - w * 0.2 + n * 0.65) * 52
    th = smin(rcone(p, a, b, 33, 25), rcone(p, b, c, 25, 19), 8)
    d = smin(d, th, 14)
    d = np.maximum(d, -((p - (JL['wr'] - FD_L * 41.3)) @ FD_L))                   # B92: closed at the wrist
    return {SKIN: d}
def box_of(pts, m):
    pts = np.array(pts); return (pts.min(0) - m).astype(f32), (pts.max(0) + m).astype(f32)
FIST_BOX = box_of([GRIP], 150); CLAW_BOX = box_of([JL['wr'], JL['wr'] + FD_L * 300 + V(0, -90, 0), JL['wr'] + V(0, 0, 230)], 150)   # B92: the thumb went past the box (open)

# ---- accessories ---------------------------------------------------------------------------------
def acc(p):
    iron = None
    for s, j, fd in ((-1, JR, FD_R), (1, JL, FD_L)):
        ra, rb = fore_r(j, s)
        c = ccyl(p, j['wr'] - fd * 95, j['wr'] - fd * 25, rb + 26, 5)
        iron = c if iron is None else np.minimum(iron, c)
    c = JR['sh'] + V(-5, 15, 0); ax = nrm(V(-0.55, 0.8, 0.05)); h = (p - c) @ ax
    # B87: a closed iron shell 14 mm thick (was a solid cap culled inside the body: open, the user saw a hole)
    pl = np.maximum(np.maximum(np.abs(sph(p, c, 222)) - 7, -45 - h), (p[:, 0] - c[0]) - 70)
    return {IRON: np.minimum(iron, pl)}
ACC_BOX = (V(-1400, 640, -330), V(1760, 1990, 620))

# ---- weapon: an anvil chained to a beam -----------------------------------------------------------
WB = np.stack([HDIR, nrm(np.cross(np.cross(HDIR, V(0, 1, 0)), HDIR)), np.cross(HDIR, nrm(np.cross(np.cross(HDIR, V(0, 1, 0)), HDIR)))])
BEAM_L = 1180.0
def weapon(p):
    q = (p - GRIP) @ WB.T                               # local: x along the beam, y up-ish
    x, y, z = q[:, 0], q[:, 1], q[:, 2]
    O = V(0, 0, 0)
    hd = ccyl(q, V(-330, 0, 0), V(170, 0, 0), 31, 6)                                     # grip (B84: long enough for both hands)
    hd = np.minimum(hd, ccyl(q, V(-365, 0, 0), V(-330, 0, 0), 44, 10))                   # pommel
    bm = rbox(q, V(170 + (BEAM_L - 170) / 2, 0, 0), V((BEAM_L - 170) / 2, 58, 58), 10)
    bm = np.maximum(bm, -(sph(q, V(520, 70, 20), 38)))                                   # chips
    bm = np.maximum(bm, -(sph(q, V(820, -30, -78), 42)))
    # the anvil sits on the beam's end, face up
    A = V(BEAM_L - 190, 0, 0); AS = 1.28
    a = (q - A) / AS; a[:, 1] += 58 - 58 / AS
    base = rbox(a, V(0, 78, 0), V(150, 22, 105), 6)
    feet = np.minimum(rbox(a, V(-112, 70, 0), V(46, 30, 118), 6), rbox(a, V(112, 70, 0), V(46, 30, 118), 6))
    wst = rbox(a, V(0, 150, 0), V(88, 62, 62), 14)
    top = rbox(a, V(-20, 232, 0), V(165, 34, 92), 5)
    horn = rcone(a, V(140, 236, 0), V(360, 252, 0), 60, 9)
    horn = np.maximum(horn, a[:, 1] - 266)
    heel = rbox(a, V(-205, 240, 0), V(45, 22, 70), 5)
    hole = rbox(a, V(-150, 250, 30), V(15, 40, 15), 2)
    an = su(10, base, feet, wst)
    an = smin(an, np.minimum(np.minimum(top, horn), heel), 14)
    an = np.maximum(an, -hole) * AS
    a = q - A
    return {WOOD: bm, IRON: np.minimum(an, hd)}
def wbox():
    c = [GRIP + WB.T @ V(x, y, z) for x in (-380, BEAM_L + 330) for y in (-110, 400) for z in (-170, 170)]
    return box_of(c, 12)
WEAPON_BOX = wbox()
PARTS = [('body', body, BODY_BOX, 6.0, 1900), ('mask', mask, MASK_BOX, 2.5, 150), ('fist', fist, FIST_BOX, 3.0, 170),
         ('claw', claw, CLAW_BOX, 2.5, 320), ('acc', acc, ACC_BOX, 3.0, 230), ('weapon', weapon, WEAPON_BOX, 3.0, 380)]
def field(fn, p):
    g = fn(p); mats = list(g.keys()); D = np.stack([g[m] for m in mats])
    return D.min(0), np.array(mats)[D.argmin(0)]
