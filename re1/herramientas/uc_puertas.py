"""Puertas entre salas de UC ya colocadas en coordenadas de RE4 (misma transformación para todas).
1) se agrupa la geometría con textura de puerta de cada sala (hojas de puerta, ~2 m de alto)
2) el plano de la hoja da la normal; a 1 m por cada lado se mira qué sala tiene suelo pisable allí
3) si a un lado hay una sala y al otro otra distinta, es una puerta entre ellas.
Salida JSON con puntos de llegada (suelo a ~1 m de la puerta dentro de cada sala) y ángulo mirando hacia dentro."""
import json, re, sys
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, '/home/claude/tools')
import objload
from re4room import place
SALAS = sys.argv[1].split(','); COLOCAR = sys.argv[2]; OUT = sys.argv[3]

def floor_pts(r, step=0.15):
    V, F = [], []
    for ln in open(f'/home/claude/uc/re4/{r}/col/colision.obj'):
        if ln.startswith('v '): V.append([float(x) for x in ln.split()[1:4]])
        elif ln.startswith('f '): F.append([int(x.split('/')[0]) - 1 for x in ln.split()[1:4]])
    V = np.array(V); F = np.array(F)
    a, b, c = V[F[:, 0]], V[F[:, 1]], V[F[:, 2]]
    n = np.cross(b - a, c - a); ny = n[:, 1] / np.maximum(np.linalg.norm(n, axis=1), 1e-9)
    pts = []
    for i in np.where(ny > 0.5)[0]:
        A, B, C = a[i], b[i], c[i]
        k = int(max(np.linalg.norm(B - A), np.linalg.norm(C - A), np.linalg.norm(C - B)) / step) + 1
        for u in range(k + 1):
            for v in range(k + 1 - u):
                pts.append(A + (B - A) * u / k + (C - A) * v / k)
    return np.array(pts)

def door_clusters(r):
    V, T, F, M, G, mats = objload.load(f'/home/claude/uc/m/{r}/sala.obj')
    sel = [i for i, m in enumerate(M) if re.search('door', (mats.get(m) or ''), re.I)
           and not re.search('nob|huchi|fuchi|waku|kazari|parts|ue|low_alfa', (mats.get(m) or ''), re.I)]
    if not sel: return []
    Vp = place(V, COLOCAR, 1000.0)
    tri = Vp[F[sel, :3]]; cen = tri.mean(1)
    # componentes por cercanía (0,4 m)
    tr = cKDTree(cen); lab = -np.ones(len(cen), int); k = 0
    for s in range(len(cen)):
        if lab[s] >= 0: continue
        st = [s]; lab[s] = k
        while st:
            q = st.pop()
            for j in tr.query_ball_point(cen[q], 0.4):
                if lab[j] < 0: lab[j] = k; st.append(j)
        k += 1
    out = []
    for c in range(k):
        P = tri[lab == c].reshape(-1, 3)
        lo, hi = P.min(0), P.max(0)
        if hi[1] - lo[1] < 1.6 or hi[1] - lo[1] > 4.5: continue        # no es una hoja de puerta
        w = np.hypot(hi[0] - lo[0], hi[2] - lo[2])
        if w < 0.6 or w > 4: continue
        X = P[:, [0, 2]] - P[:, [0, 2]].mean(0)
        ev, evec = np.linalg.eigh(X.T @ X)
        nrm = evec[:, 0]                                                   # eje fino = normal de la hoja
        out.append(dict(c=np.array([(lo[0] + hi[0]) / 2, lo[1], (lo[2] + hi[2]) / 2]), n=nrm, w=w, src=r))
    return out

fl = {r: floor_pts(r) for r in SALAS}
trees = {r: cKDTree(fl[r]) for r in SALAS}

def who(p):
    best = []
    for r in SALAS:
        d, i = trees[r].query(p)
        if d < 0.45: best.append((len(trees[r].query_ball_point(p, 1.2)), r, i))
    return max(best)[1:] if best else None

puertas = []
allc = []
for r in SALAS:
    for D in door_clusters(r):
        if D['c'][1] < -0.2: continue                                  # restos del reflejo del suelo
        if any(np.linalg.norm(D['c'] - q['c']) < 0.8 for q in allc): continue
        allc.append(D)
for D in allc:
    c, n = D['c'], D['n']; n3 = np.array([n[0], 0, n[1]])
    lado = {1: [], -1: []}
    for R in SALAS:
        P = fl[R]; d = np.hypot(P[:, 0] - c[0], P[:, 2] - c[2])
        m = (d < 2.2) & (np.abs(P[:, 1] - c[1]) < 0.6)
        if m.sum() < 5: continue
        s_ = np.sign((P[m] - c) @ n3)
        for sg in (1, -1):
            k = (s_ == sg)
            if k.sum() >= 5:
                idx = np.where(m)[0][k]
                lado[sg].append((d[idx].min(), k.sum(), R, idx))
    if not lado[1] or not lado[-1]: continue
    a_ = min(lado[1]); b_ = min(lado[-1])
    if a_[2] == b_[2]:
        # la misma sala a ambos lados: probar la segunda mejor de cada lado
        alt = [(x, y) for x in sorted(lado[1]) for y in sorted(lado[-1]) if x[2] != y[2]]
        if not alt: continue
        a_, b_ = alt[0]
    def arrive(t, sg):
        d_, cnt, R, idx = t; P = fl[R][idx]
        dd = np.hypot(P[:, 0] - c[0], P[:, 2] - c[2])
        # a ~1,2 m de la puerta, lo más centrado posible respecto a la hoja
        lat = np.abs((P[:, [0, 2]] - c[[0, 2]]) @ np.array([-n[1], n[0]]))
        j = np.argmin(np.abs(dd - 1.2) + 1.5 * lat)
        ang = float(np.arctan2(n[0] * sg, n[1] * sg))
        return [float(x * 1000) for x in P[j]], ang, float(d_)
    ea, aa, da = arrive(a_, 1); eb, ab, db = arrive(b_, -1)
    puertas.append(dict(a=a_[2], b=b_[2], centro=[float(x * 1000) for x in c], ancho=float(D['w']),
                        llegada_a=ea, ang_a=aa, llegada_b=eb, ang_b=ab, visto_en=D['src']))
    print(f"{a_[2]}<->{b_[2]} en {np.round(c, 2)} hueco {da:.2f}/{db:.2f} m (puerta de {D['src']})")
json.dump(puertas, open(OUT, 'w'), indent=1)
