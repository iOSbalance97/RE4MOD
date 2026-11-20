"""Colisión de UC (rNNN_chit.col) -> SAT/EAT de RE4 con la misma colocación que los modelos.
chit = colisión de personajes de UC: suelos, escaleras como rampas y paredes, ya simplificada.
Clasificación por normal: suelo ny>0.97, pendiente 0.5..0.97, pared |ny|<=0.5; techos (ny<-0.5) fuera.
uso: ucol2re4.py rNNN salida --colocar hx,hy,hz,x,y,z,giro"""
import argparse, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ucol, re4room
from re4col import write_sat

ap = argparse.ArgumentParser(); ap.add_argument('sala'); ap.add_argument('out'); ap.add_argument('--colocar', required=True)
ap.add_argument('--tipo', default='chit')
ap.add_argument('--suelo-extra', default='', help='x0,z0,x1,z1,y en mm: plano de suelo de seguridad (baldosas de 10 m)')
ap.add_argument('--bloque', type=float, default=2000.0)
ap.add_argument('--suelo-visible', default='', help='y0,y1 en m: en esa franja los suelos de chit se rehacen con la altura del suelo visible (rejilla 0,4 m)')
a = ap.parse_args()
os.makedirs(a.out, exist_ok=True)
V, N, A = ucol.load(f'/home/claude/uc/r/{a.sala}/{a.sala}_{a.tipo}.col')
P = re4room.place((V * 0.1).reshape(-1, 3), a.colocar, 1000.0) * 1000.0          # mm de RE4
Nr = re4room.place(N, '0,0,0,0,0,0,' + a.colocar.split(',')[-1], 1000.0)        # solo giro
# soldar vértices (1 mm)
key = np.round(P).astype(np.int64)
_, first, inv = np.unique(key, axis=0, return_index=True, return_inverse=True)
SV = P[first]; T = inv.reshape(-1, 3)
ny = Nr[:, 1]
keep = (ny >= 0.5) | (np.abs(ny) <= 0.2)          # paredes casi verticales; lo inclinado intermedio y los techos fuera
# fuera degenerados
ar = np.linalg.norm(np.cross(SV[T[:, 1]] - SV[T[:, 0]], SV[T[:, 2]] - SV[T[:, 0]]), axis=1)
keep &= ar > 1.0
# orientación: que el orden de vértices dé la normal de UC
c = np.cross(SV[T[:, 1]] - SV[T[:, 0]], SV[T[:, 2]] - SV[T[:, 0]])
flip = (c * Nr).sum(1) < 0
T[flip] = T[flip][:, [0, 2, 1]]
T = T[keep]; ny = ny[keep]
K = np.where(ny > 0.97, 0, np.where(ny >= 0.5, 1, 2))
if a.suelo_visible:
    import objload
    y0b, y1b = [float(v) * 1000 for v in a.suelo_visible.split(',')]
    Vv, Tv_, Fv, Mv, Gv, _ = objload.load(f'/home/claude/uc/m/{a.sala}/sala.obj')
    Pv = re4room.place(Vv, a.colocar, 1000.0) * 1000.0; tv = Pv[Fv[:, :3]]
    nv = np.cross(tv[:, 1] - tv[:, 0], tv[:, 2] - tv[:, 0]); nv /= np.linalg.norm(nv, axis=1, keepdims=True) + 1e-12
    vf = tv[(np.abs(nv[:, 1]) > 0.9) & (tv[:, :, 1].mean(1) > y0b - 1000) & (tv[:, :, 1].mean(1) < y1b + 1000)]
    cy = SV[T].mean(1)[:, 1]; band = (K == 0) & (cy > y0b) & (cy < y1b)
    cf = SV[T[band]]
    G = 400.0
    lo_ = cf.reshape(-1, 3).min(0); hi_ = cf.reshape(-1, 3).max(0)
    gx = int(np.ceil((hi_[0] - lo_[0]) / G)); gz = int(np.ceil((hi_[2] - lo_[2]) / G))
    def bary(t, X, Z):
        a_, b_, c_ = t; d = (b_[2] - c_[2]) * (a_[0] - c_[0]) + (c_[0] - b_[0]) * (a_[2] - c_[2])
        if abs(d) < 1e-9: return None, None
        w0 = ((b_[2] - c_[2]) * (X - c_[0]) + (c_[0] - b_[0]) * (Z - c_[2])) / d
        w1 = ((c_[2] - a_[2]) * (X - c_[0]) + (a_[0] - c_[0]) * (Z - c_[2])) / d
        w2 = 1 - w0 - w1; m = (w0 >= -1e-4) & (w1 >= -1e-4) & (w2 >= -1e-4)
        return m, w0 * a_[1] + w1 * b_[1] + w2 * c_[1]
    X, Z = np.meshgrid(lo_[0] + (np.arange(gx) + .5) * G, lo_[2] + (np.arange(gz) + .5) * G, indexing='ij')
    hc = np.full((gx, gz), np.nan)
    for t in cf:
        m, Y = bary(t, X, Z)
        if m is not None: hc[m] = np.where(np.isnan(hc[m]), Y[m], np.maximum(hc[m], Y[m]))
    best = np.full((gx, gz), np.nan); bd = np.full((gx, gz), 1e9)
    for t in vf:
        i0 = max(0, int((t[:, 0].min() - lo_[0]) / G)); i1 = min(gx - 1, int((t[:, 0].max() - lo_[0]) / G))
        j0 = max(0, int((t[:, 2].min() - lo_[2]) / G)); j1 = min(gz - 1, int((t[:, 2].max() - lo_[2]) / G))
        if i0 > i1 or j0 > j1: continue
        m, Y = bary(t, X[i0:i1+1, j0:j1+1], Z[i0:i1+1, j0:j1+1])
        if m is None: continue
        sub_h = hc[i0:i1+1, j0:j1+1]; d = np.abs(Y - sub_h); ok_ = m & ~np.isnan(sub_h) & (d < 800) & (d < bd[i0:i1+1, j0:j1+1])
        best[i0:i1+1, j0:j1+1][ok_] = Y[ok_]; bd[i0:i1+1, j0:j1+1][ok_] = d[ok_]
    h = np.where(np.isnan(best), hc, best); celdas = ~np.isnan(hc)
    # vértices de la rejilla: media de las celdas que tocan
    Hv = np.zeros((gx + 1, gz + 1)); Nc = np.zeros((gx + 1, gz + 1))
    for di in (0, 1):
        for dj in (0, 1):
            Hv[di:gx+di, dj:gz+dj] += np.where(celdas, h, 0); Nc[di:gx+di, dj:gz+dj] += celdas
    Hv = Hv / np.maximum(Nc, 1)
    base = len(SV); vid = -np.ones((gx + 1, gz + 1), int); nvx = []
    tris = []
    for i in range(gx):
        for j in range(gz):
            if not celdas[i, j]: continue
            ids = []
            for di, dj in ((0, 0), (1, 0), (0, 1), (1, 1)):
                if vid[i+di, j+dj] < 0: vid[i+di, j+dj] = base + len(nvx); nvx.append((lo_[0] + (i+di) * G, Hv[i+di, j+dj], lo_[2] + (j+dj) * G))
                ids.append(vid[i+di, j+dj])
            a_, b_, c_, d_ = ids; tris += [(a_, c_, b_), (b_, c_, d_)]
    SV = np.concatenate([SV, np.array(nvx)]); keepb = ~band
    T = np.concatenate([T[keepb], np.array(tris)]); K = np.concatenate([K[keepb], np.zeros(len(tris), int)])
    n_ = np.cross(SV[T[-1, 1]] - SV[T[-1, 0]], SV[T[-1, 2]] - SV[T[-1, 0]]); assert n_[1] > 0
    print(f'suelo visible en {a.suelo_visible} m: {band.sum()} suelos de chit -> {len(tris)} triángulos de rejilla, '
          f'{int((~np.isnan(best)).sum())}/{int(celdas.sum())} celdas con altura visible, desfase medio {np.nanmean(np.where(np.isnan(best), np.nan, best - hc)):.0f} mm')
if a.suelo_extra:
    x0, z0, x1, z1, yy = [float(v) for v in a.suelo_extra.split(',')]
    xs = np.arange(x0, x1 + 1, 10000.0); zs = np.arange(z0, z1 + 1, 10000.0)
    base = len(SV); extra_v = [(x, yy, z) for z in zs for x in xs]; nx = len(xs)
    tris = []
    for j in range(len(zs) - 1):
        for i in range(nx - 1):
            a_, b_, c_, d_ = base + j * nx + i, base + j * nx + i + 1, base + (j + 1) * nx + i, base + (j + 1) * nx + i + 1
            tris += [(a_, c_, b_), (b_, c_, d_)]           # normal hacia arriba
    SV = np.concatenate([SV, np.array(extra_v)]); T = np.concatenate([T, np.array(tris)]); K = np.concatenate([K, np.zeros(len(tris), int)])
    n_ = np.cross(SV[T[-1, 1]] - SV[T[-1, 0]], SV[T[-1, 2]] - SV[T[-1, 0]]); assert n_[1] > 0
    print(f'suelo de seguridad: {len(tris)} triángulos a y={yy:.0f} mm')
sat = write_sat(SV, T, K, np.zeros(len(T), int), block_size=a.bloque)
open(f'{a.out}/sala.sat', 'wb').write(sat); open(f'{a.out}/sala.eat', 'wb').write(sat)
with open(f'{a.out}/colision.obj', 'w') as f:
    f.writelines(f'v {x/1000} {y/1000} {z/1000}\n' for x, y, z in SV)
    for t, k in zip(T, K):
        f.write(f'g {"suelo" if k == 0 else "pendiente" if k == 1 else "pared"}\nf {t[0]+1} {t[1]+1} {t[2]+1}\n')
print(f'{a.sala}: SAT {len(T)} polígonos (suelo {(K==0).sum()}, pendiente {(K==1).sum()}, pared {(K==2).sum()}), {len(sat)//1024} KB, '
      f'giradas {int(flip.sum())}')
