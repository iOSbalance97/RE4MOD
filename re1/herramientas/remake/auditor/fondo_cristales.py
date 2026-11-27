"""fondo_cristales.py sala.obj salida.obj centro_x,centro_y,centro_z: fondo de noche detrás de cada cristal (los cristales de UC tienen transparencia)"""
import sys, re, numpy as np
from scipy.cluster.hierarchy import fcluster, linkage
sala, out = sys.argv[1], sys.argv[2]; cen = np.array([float(v) for v in sys.argv[3].split(',')])
V = []; F = []; M = []; cur = None
for l in open(sala):
    if l.startswith('v '): V.append([float(x) for x in l.split()[1:4]])
    elif l.startswith('usemtl'): cur = l.split()[1]
    elif l.startswith('f '): F.append([int(x.split('/')[0]) - 1 for x in l.split()[1:4]]); M.append(cur)
V = np.array(V); P = V[np.array(F)]; c = P.mean(1)
g = np.array([bool(re.search(sys.argv[4] if len(sys.argv) > 4 else 'glass', m)) for m in M])
lab = fcluster(linkage(c[g], 'single'), 0.5, 'distance')
Vs = []; Ls = []
for L in sorted(set(lab)):
    Q = P[g][lab == L].reshape(-1, 3); m_ = Q.mean(0)
    u, s, vt = np.linalg.svd(Q - m_); nn = vt[2]
    if (m_ - cen) @ nn < 0: nn = -nn          # hacia fuera de la sala
    e1, e2 = vt[0], vt[1]; a = (Q - m_) @ e1; b = (Q - m_) @ e2; mg = 0.25
    p0 = m_ + nn * 0.3
    k = len(Vs); Vs += [p0 + e1 * x + e2 * y for x, y in ((a.min() - mg, b.min() - mg), (a.max() + mg, b.min() - mg), (a.max() + mg, b.max() + mg), (a.min() - mg, b.max() + mg))]
    Ls.append('usemtl cas_noche')
    for i, j, kk in ((0, 1, 2), (0, 2, 3), (0, 2, 1), (0, 3, 2)): Ls.append(f'f {k+i+1}/{(i%4)+1} {k+j+1}/{(j%4)+1} {k+kk+1}/{(kk%4)+1}')
open(out, 'w').write('\n'.join([f'v {x:.4f} {y:.4f} {z:.4f}' for x, y, z in Vs] + ['vt 0 0', 'vt 1 0', 'vt 1 1', 'vt 0 1'] + Ls) + '\n')
print(len(set(lab)), 'cristales con fondo')
