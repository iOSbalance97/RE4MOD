"""skeleton (the game's part numbers 0-25, bind = T-pose, identity rotations), skin weights, posing"""
import numpy as np, math
import model
from model import JR, JL, V, BOOT, SOLE
B = {0: (-1, V(0, 1100, 0)), 1: (0, V(0, 1110, 0)), 2: (1, V(0, 1400, 10)), 3: (2, V(0, 1745, 140)), 4: (3, V(0, 1840, 300)),
     17: (0, V(0, 1100, 0))}
for s, j, o in ((-1, JR, 5), (1, JL, 11)):
    B[o] = (2, V(s * 70, 1640, 60)); B[o + 1] = (o, j['sh']); B[o + 2] = (o, j['sh']); B[o + 3] = (o + 2, j['el'])
    B[o + 4] = (o + 3, j['el'] + (j['wr'] - j['el']) * 0.57); B[o + 5] = (o + 4, j['wr'])
for s, j, o in ((-1, JR, 18), (1, JL, 22)):
    B[o] = (17, j['hip']); B[o + 1] = (o, j['knee']); B[o + 2] = (o + 1, j['ank']); B[o + 3] = (o + 2, j['ank'] * V(1, 0, 1) + V(s * 30, 40, 175))
ORDER = sorted(B)                                           # parents come first (numbering guarantees it, except 17 < 18)
SEG = {1: (V(0, 1100, 0), V(0, 1230, 30)), 2: (V(0, 1330, 40), V(0, 1700, 30)), 3: (V(0, 1745, 140), V(0, 1810, 250)), 4: (V(0, 1850, 310), V(0, 1960, 340))}
for s, j, o in ((-1, JR, 5), (1, JL, 11)):
    fd = (j['wr'] - j['el']) / np.linalg.norm(j['wr'] - j['el'])
    SEG[o] = (V(s * 120, 1650, 60), j['sh'] - V(s * 60, 0, 0)); SEG[o + 2] = (j['sh'], j['el']); SEG[o + 3] = (j['el'], B[o + 4][1])
    SEG[o + 4] = (B[o + 4][1], j['wr']); SEG[o + 5] = (j['wr'], j['wr'] + fd * 220)
for s, j, o in ((-1, JR, 18), (1, JL, 22)):
    SEG[o] = (j['hip'], j['knee']); SEG[o + 1] = (j['knee'], j['ank']); SEG[o + 2] = (j['ank'], B[o + 3][1]); SEG[o + 3] = (B[o + 3][1], B[o + 3][1] + V(0, 0, 110))
RAD = {1: 2.2, 2: 2.6, 3: 1.0, 4: 1.0, 5: 1.2, 11: 1.2}       # big bones reach further
def segdist(P, a, b):
    ab = b - a; t = np.clip(((P - a) @ ab) / (ab @ ab), 0, 1); return np.linalg.norm(P - a - t[:, None] * ab, axis=1)
def auto_weights(P, allowed=None):
    ids = [k for k in sorted(SEG) if allowed is None or k in allowed]
    D = np.stack([segdist(P, *SEG[k]) / RAD.get(k, 1.0) for k in ids], 1) + 1.0
    W = D ** -7.0
    o = np.argsort(-W, 1)[:, :2]; w = np.take_along_axis(W, o, 1); w /= w.sum(1, keepdims=True)
    w[w[:, 1] < 0.06] = (1, 0); w /= w.sum(1, keepdims=True)
    return np.array(ids)[o], w.astype(np.float32)
def components(n, f):
    par = np.arange(n)
    def find(x):
        while par[x] != x: par[x] = par[par[x]]; x = par[x]
        return x
    for a, b, c in f:
        ra, rb, rc = find(a), find(b), find(c); par[ra] = rc; par[rb] = rc
    return np.array([find(i) for i in range(n)])
def weights(part):
    name, v, f = part['name'], part['v'], part['f']; n = len(v)
    fixed = {'mask': 4, 'fist': 10, 'weapon': 10, 'claw': 16}
    if name in fixed: return np.tile([fixed[name], 0], (n, 1)), np.tile(np.float32([1, 0]), (n, 1))
    J_, W_ = auto_weights(v)
    if name in ('body', 'legs'):
        bt = np.isin(part['mat'], (BOOT, SOLE)) & (v[:, 1] < 330)
        for s, legs in ((-1, (19, 20, 21)), (1, (23, 24, 25))):
            m = bt & (v[:, 0] * s > 0)
            if m.any(): J_[m], W_[m] = auto_weights(v[m], legs)
    else:                                                    # accessories: rigid, the dominant bone of each piece
        comp = components(n, f)
        for c in np.unique(comp):
            m = comp == c; ids, cnt = np.unique(J_[m, 0], return_counts=True); b = ids[cnt.argmax()]
            if np.linalg.norm(v[m].mean(0) - JR['sh']) < 300: b = 5      # pauldron: on the clavicle
            J_[m] = (b, 0); W_[m] = (1, 0)
    return J_, W_
def rx(a): c, s = math.cos(a), math.sin(a); return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])
def ry(a): c, s = math.cos(a), math.sin(a); return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
def rz(a): c, s = math.cos(a), math.sin(a); return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
def pose_mats(rot, root_off=(0, 0, 0)):
    """rot: part -> local 3x3 (deg helpers above). returns part -> (R world, t) with x' = R x + t"""
    WR = {}; WP = {}; M = {}
    for k in ORDER:
        par, pos = B[k]
        if par < 0: WR[k] = rot.get(k, np.eye(3)); WP[k] = pos + np.array(root_off)
        else: WR[k] = WR[par] @ rot.get(k, np.eye(3)); WP[k] = WP[par] + WR[par] @ (pos - B[par][1])
        M[k] = (WR[k], WP[k] - WR[k] @ pos)
    return M
def skin(v, J_, W_, M, normals=None):
    out = np.zeros_like(v, dtype=np.float64)
    for c in range(2):
        for k in np.unique(J_[:, c]):
            m = (J_[:, c] == k) & (W_[:, c] > 0)
            if not m.any(): continue
            R, t = M[int(k)]
            out[m] += W_[m, c][:, None] * ((v[m] @ R.T + t) if normals is None else (v[m] @ R.T))
    return out
d = math.radians
POSE = {7: rz(d(71)) @ ry(d(-8)), 8: ry(d(22)), 10: ry(d(39)),
        13: rz(d(-58)) @ ry(d(-32)), 14: ry(d(-48)), 16: rx(d(-20)) @ ry(d(-12)),
        3: rx(d(6)), 4: rx(d(8)) @ ry(d(-10)), 2: ry(d(-5)), 18: ry(d(4)), 22: ry(d(-6))}
