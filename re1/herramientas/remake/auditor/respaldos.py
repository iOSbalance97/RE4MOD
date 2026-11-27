"""respaldos.py sala.obj fugas.npz salida_dir prefijo
Para cada grupo de rayos que se escapan, pone detrás de la superficie por la que se cuelan un trozo
del MISMO material, en su mismo plano desplazado unos cm hacia atrás y con su misma proyección de
textura: solo se ve a través de la rendija y continúa lo que hay alrededor. Detrás del cristal de las
ventanas pone un fondo de noche."""
import sys, os, re, json, numpy as np
from scipy.spatial import cKDTree
from scipy.cluster.hierarchy import fcluster, linkage
sala, fz, out, pref = sys.argv[1:5]; os.makedirs(out, exist_ok=True)
V = []; VT = []; F = []; M = []; cur = None
for l in open(sala):
    if l.startswith('v '): V.append([float(x) for x in l.split()[1:4]])
    elif l.startswith('vt '): VT.append([float(x) for x in l.split()[1:3]])
    elif l.startswith('usemtl'): cur = l.split()[1]
    elif l.startswith('f '): q = [x.split('/') for x in l.split()[1:4]]; F.append([int(a[0]) - 1 for a in q] + [int(a[1]) - 1 for a in q]); M.append(re.sub(r'__L\d+$', '', cur))
V = np.array(V); VT = np.array(VT); F = np.array(F); P = V[F[:, :3]]; UV = VT[F[:, 3:]]; M = np.array(M)
n = np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0]); A = np.linalg.norm(n, axis=1) / 2; n /= 2 * A[:, None] + 1e-12
ok = (A > 1e-4) & np.array([not m.startswith(('pag_', 'atlas')) and 'alpha' not in m and 'jutan' not in m for m in M])          # ni atlas ni materiales con transparencia (alfombras)
# muestras de superficie para buscar vecinos
S = []; Si = []
rng = np.random.default_rng(0)
for i in np.nonzero(ok)[0]:
    k = int(min(40, max(1, A[i] / 0.004))); w = rng.dirichlet([1, 1, 1], k); S.append(w @ P[i]); Si += [i] * k
S = np.concatenate(S); Si = np.array(Si); KS = cKDTree(S)
d = np.load(fz); X, O, D = d['X'], d['O'], d['D']
if len(X) < 2: print('sin fugas'); sys.exit()
sub = rng.choice(len(X), min(len(X), 8000), replace=False); X, O, D = X[sub], O[sub], D[sub]
# dónde se cuela de verdad: el último punto del rayo que pasa rozando una superficie antes de salir de la sala
bmin = S.min(0) - 0.5; bmax = S.max(0) + 0.5; X2 = []; keep = []
for k, (o, dd) in enumerate(zip(O, D)):
    inv = 1 / np.where(np.abs(dd) < 1e-9, 1e-9, dd); t1 = float(np.min(np.maximum((bmin - o) * inv, (bmax - o) * inv)))
    ts = np.arange(0.05, min(t1, 40), 0.04); pts = o + dd[None] * ts[:, None]
    dist, _ = KS.query(pts, distance_upper_bound=0.12)
    near = np.nonzero(dist < 0.12)[0]
    if len(near): X2.append(pts[near[-1]]); keep.append(k)
X, O, D = np.array(X2), O[keep], D[keep]
lab = fcluster(linkage(X, 'single'), 0.25, 'distance')
quads = []
for L in sorted(set(lab)):
    m = lab == L
    if m.sum() < int(os.environ.get('MIN_RAYOS', 4)): continue
    Xc, Oc, Dc = X[m], O[m], D[m]
    # triángulos visibles cerca de por donde se cuelan los rayos
    cand = {}
    for x, dd in zip(Xc[::max(1, len(Xc) // 60)], Dc[::max(1, len(Xc) // 60)]):
        for j in KS.query_ball_point(x, 0.35):
            i = Si[j]
            if abs(n[i] @ dd) < 0.25: continue
            cand[i] = cand.get(i, 0) + 1
    if not cand: continue
    # plano dominante: agrupar candidatos por normal (sin signo) y distancia, pesar por área
    planos = {}
    for i, c in cand.items():
        nn = n[i] * (1 if n[i] @ Dc.mean(0) < 0 else -1)          # normal hacia quien mira
        key = (tuple(np.round(nn, 1)), round(float(nn @ P[i][0]) / 0.04))
        planos.setdefault(key, []).append(i)
    key, tris = max(planos.items(), key=lambda kv: sum(A[i] for i in kv[1]))
    i0 = max(tris, key=lambda i: A[i]); nn = np.array(key[0], float); nn /= np.linalg.norm(nn)
    nn = n[i0] * (1 if n[i0] @ nn > 0 else -1)
    mat = M[i0]; vidrio = bool(re.search('glass|mado', mat))
    off = 0.3 if vidrio else 0.06
    p0 = P[i0][0] - nn * off          # plano desplazado hacia atrás (lejos de quien mira)
    # cortes de los rayos con ese plano
    den = Dc @ nn; sel = np.abs(den) > 1e-3
    t = ((p0 - Oc[sel]) @ nn) / den[sel]; H = Oc[sel] + Dc[sel] * t[:, None]
    H = H[(t > 0)]
    if len(H) < 2: continue
    e1 = np.cross(nn, [0, 1, 0]) if abs(nn[1]) < 0.9 else np.cross(nn, [1, 0, 0]); e1 /= np.linalg.norm(e1); e2 = np.cross(nn, e1)
    a_ = (H - p0) @ e1; b_ = (H - p0) @ e2; mg = 0.15
    if np.ptp(a_) > 6 or np.ptp(b_) > 6: continue          # demasiado grande: no es una rendija
    Q = [p0 + e1 * a + e2 * b for a, b in ((a_.min() - mg, b_.min() - mg), (a_.max() + mg, b_.min() - mg), (a_.max() + mg, b_.max() + mg), (a_.min() - mg, b_.max() + mg))]
    if vidrio: mt = 'cas_noche'; uvq = [[0, 0], [1, 0], [1, 1], [0, 1]]
    elif re.search('door', mat): mt = 'cas_negro'; uvq = [[0, 0], [1, 0], [1, 1], [0, 1]]          # por la rendija de una puerta se ve oscuro, no más puerta
    else:
        # misma proyección de textura que el triángulo de referencia (afín xyz -> uv en su plano)
        T3 = P[i0]; U3 = UV[i0]; f1 = T3[1] - T3[0]; f2 = T3[2] - T3[0]
        G = np.array([[f1 @ f1, f1 @ f2], [f1 @ f2, f2 @ f2]])
        def uv(q):
            r = q + nn * off - T3[0]; s, tt = np.linalg.solve(G, [r @ f1, r @ f2]); return (U3[0] + s * (U3[1] - U3[0]) + tt * (U3[2] - U3[0])).tolist()
        mt = mat; uvq = [uv(q) for q in Q]
    quads.append((mt, Q, uvq, int(m.sum()), np.round(Xc.mean(0), 2).tolist()))
Vs = []; Ts = []; Ls = []
for mt, Q, uvq, k, c in quads:
    b = len(Vs); Vs += [q.tolist() for q in Q]; Ts += uvq; Ls.append(f'usemtl {mt}')
    for a1, b1, c1 in ((0, 1, 2), (0, 2, 3), (0, 2, 1), (0, 3, 2)): Ls.append(f'f {b+a1+1}/{b+a1+1} {b+b1+1}/{b+b1+1} {b+c1+1}/{b+c1+1}')
open(f'{out}/{pref}.obj', 'w').write('\n'.join([f'v {x:.4f} {y:.4f} {z:.4f}' for x, y, z in Vs] + [f'vt {u:.5f} {v:.5f}' for u, v in Ts] + Ls) + '\n')
json.dump(sorted({q[0] for q in quads}), open(f'{out}/{pref}_mats.json', 'w'))
for mt, Q, uvq, k, c in quads: print(f'{k:5d} rayos  {mt:22s} centro {c}')
print(len(quads), 'respaldos')
