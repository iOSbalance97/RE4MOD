"""Envolvente de seguridad de una sala de UC (sobre uc/m/rNNN/sala.obj: metros, marco de UC).
UC solo modela lo que ve la cámara del recorrido; al andar libre se ven huecos (vacío gris/negro).
1) máscara de planta: suelos visibles (+ suelos de la colisión chit cercanos), cerrada y sin agujeros (rejilla 0,2 m)
2) suelo que falta: celdas con suelo de colisión sin suelo visible a ±0,4 m -> losa con la textura del suelo visible más cercano
3) paredes: en el borde de la máscara, a 0,3 m por fuera, del suelo al techo local, mirando hacia dentro
   (quedan detrás de las paredes reales; solo se ven donde UC no tiene pared)
4) techo: celdas sin nada por encima del suelo -> techo a la altura local
Se añade al final de sala.obj reutilizando materiales de la sala.  uso: uc_envolvente.py rNNN [--solo-informe]"""
import os, re, sys
import numpy as np
from scipy import ndimage
from scipy.spatial import cKDTree
sys.path.insert(0, '/home/claude/tools')
import objload, ucol

CEL = 0.2
r = sys.argv[1]; informe = '--solo-informe' in sys.argv
path = f'/home/claude/uc/m/{r}/sala.obj'
V, T, F, M, G, mats = objload.load(path)
tri = V[F[:, :3]]
n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]); ar = np.linalg.norm(n, axis=1) / 2
n = n / (2 * ar[:, None] + 1e-12)
tex = np.array([(mats.get(m) or '') for m in M])
CV, CN, CA = ucol.load(f'/home/claude/uc/r/{r}/{r}_chit.col'); CV = CV * 0.1
cn = CN / (np.linalg.norm(CN, axis=1, keepdims=True) + 1e-12)
cfl = CV[cn[:, 1] > 0.5]

lo = tri.reshape(-1, 3).min(0) - 1.0; hi = tri.reshape(-1, 3).max(0) + 1.0
nx, nz = int(np.ceil((hi[0] - lo[0]) / CEL)), int(np.ceil((hi[2] - lo[2]) / CEL))

def rast(T3, fn):
    """llama fn(i, ix, iz, y) para las celdas cuyo centro cae dentro del triángulo i (proyección XZ)"""
    for i, t in enumerate(T3):
        x0, z0 = t[:, 0].min(), t[:, 2].min(); x1, z1 = t[:, 0].max(), t[:, 2].max()
        i0, i1 = int((x0 - lo[0]) / CEL), int((x1 - lo[0]) / CEL); j0, j1 = int((z0 - lo[2]) / CEL), int((z1 - lo[2]) / CEL)
        xs = lo[0] + (np.arange(i0, i1 + 1) + .5) * CEL; zs = lo[2] + (np.arange(j0, j1 + 1) + .5) * CEL
        X, Z = np.meshgrid(xs, zs, indexing='ij')
        a, b, c = t
        d = (b[2] - c[2]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[2] - c[2])
        if abs(d) < 1e-9: continue
        w0 = ((b[2] - c[2]) * (X - c[0]) + (c[0] - b[0]) * (Z - c[2])) / d
        w1 = ((c[2] - a[2]) * (X - c[0]) + (a[0] - c[0]) * (Z - c[2])) / d
        w2 = 1 - w0 - w1; m = (w0 >= -1e-4) & (w1 >= -1e-4) & (w2 >= -1e-4)
        if not m.any(): continue
        Y = w0 * a[1] + w1 * b[1] + w2 * c[1]
        ii, jj = np.nonzero(m)
        fn(i, ii + i0, jj + j0, Y[m])

# suelos visibles (|ny|>0.7) y todo lo no vertical (para techos)
vis_fl = [[[] for _ in range(nz)] for _ in range(nx)]
vis_any = np.full((nx, nz), -1e9); vis_low = np.full((nx, nz), 1e9)
fl_idx = np.nonzero((n[:, 1] > 0.7) & (ar > 1e-5))[0]
def f_fl(i, ii, jj, Y):
    for a, b, y in zip(ii, jj, Y): vis_fl[a][b].append((y, fl_idx[i]))
rast(tri[fl_idx], f_fl)
nv_idx = np.nonzero((np.abs(n[:, 1]) > 0.25) & (ar > 1e-5))[0]
def f_any(i, ii, jj, Y):
    np.maximum.at(vis_any, (ii, jj), Y); np.minimum.at(vis_low, (ii, jj), Y)
rast(tri[nv_idx], f_any)
col_fl = [[[] for _ in range(nz)] for _ in range(nx)]
def f_col(i, ii, jj, Y):
    for a, b, y in zip(ii, jj, Y): col_fl[a][b].append(y)
rast(cfl, f_col)

mv = np.array([[len(vis_fl[i][j]) > 0 for j in range(nz)] for i in range(nx)])
mc = np.array([[len(col_fl[i][j]) > 0 for j in range(nz)] for i in range(nx)])
cerca = ndimage.binary_dilation(mv, iterations=int(1.5 / CEL))
cerca_c = ndimage.binary_dilation(mc, iterations=int(2.0 / CEL))
mask = ndimage.binary_closing((mv & cerca_c) | (mc & cerca), iterations=3)
mask = ndimage.binary_fill_holes(mask)
mask = ndimage.binary_opening(mask, iterations=1)

# altura de suelo de cada celda (la más baja) y techo local
suelo = np.full((nx, nz), np.nan)
for i in range(nx):
    for j in range(nz):
        hs = [y for y, _ in vis_fl[i][j]] + col_fl[i][j]
        if hs: suelo[i, j] = min(hs)
ok = ~np.isnan(suelo)
if ok.any():
    _, (ii, jj) = ndimage.distance_transform_edt(~ok, return_indices=True); suelo = suelo[ii, jj]
cap = np.where(vis_any > -1e8, vis_any, -1e9)
techo_loc = ndimage.maximum_filter(cap, size=int(2.0 / CEL) * 2 + 1)
techo_loc = np.maximum(techo_loc, suelo + 2.6)

# texturas por defecto
vert = (np.abs(n[:, 1]) < 0.2)
def domina(sel, pat):
    t, a = tex[sel], ar[sel]
    cand = [(a[t == x].sum(), x) for x in set(t) if x and re.search(pat, x, re.I) and not re.search('door|glass|nob|picture|portra|candle|mirror', x, re.I)]
    if not cand: cand = [(a[t == x].sum(), x) for x in set(t) if x and not re.search('door|glass|nob|picture|portra|candle|mirror', x, re.I)]
    return max(cand)[1] if cand else None
t_pared = domina(vert, 'wall|kabe')
t_techo = domina(n[:, 1] < -0.7, 'ceil|tenjo|tenjou') or t_pared
t_suelo = domina(n[:, 1] > 0.7, 'floor|yuka|carpet|lug') or t_pared
mat_de = {}
for m, t in mats.items():
    if t and t not in mat_de: mat_de[t] = m
fl_cent = tri[fl_idx].mean(1); fl_tree = cKDTree(fl_cent[:, [0, 2]]) if len(fl_idx) else None

quads = []   # (material, 4 puntos, normal para uv)
def cx(i): return lo[0] + i * CEL
def cz(j): return lo[2] + j * CEL
# 2) suelo que falta
interior = ndimage.binary_erosion(mask, iterations=3)
falta = np.zeros((nx, nz), bool); yfalta = np.zeros((nx, nz))
for i in range(nx):
    for j in range(nz):
        if not mask[i, j] or not col_fl[i][j]: continue
        vh = np.array([y for y, _ in vis_fl[i][j]])
        for y in col_fl[i][j]:
            if (not len(vh) or not ((vh > y - 0.8) & (vh < y + 2.0)).any()) and vis_any[i, j] > y + 1.5 and interior[i, j]:
                falta[i, j] = True; yfalta[i, j] = y; break
falta = ndimage.binary_opening(falta, iterations=1)      # nada de celdas sueltas
fl_y = tri[fl_idx].mean(1)[:, 1]
t_forzada = next((a.split('=', 1)[1] for a in sys.argv if a.startswith('--suelo-tex=')), None)
def tex_suelo(x, z, y=None):
    if t_forzada: return t_forzada
    if fl_tree is None: return t_suelo
    ks = fl_tree.query_ball_point([x, z], 4.0)
    ks = [k for k in ks if y is None or abs(fl_y[k] - y) < 0.5]
    if not ks: return t_suelo
    k = min(ks, key=lambda k: (fl_cent[k][0] - x) ** 2 + (fl_cent[k][2] - z) ** 2); t = tex[fl_idx[k]]
    return t if t and not re.search('door|glass|nob|picture|candle', t, re.I) else t_suelo
for i in range(nx):
    j = 0
    while j < nz:
        if not falta[i, j]: j += 1; continue
        y = round(yfalta[i, j] / 0.05) * 0.05; j2 = j
        while j2 + 1 < nz and falta[i, j2 + 1] and abs(round(yfalta[i, j2 + 1] / 0.05) * 0.05 - y) < 1e-6 and j2 - j < 20: j2 += 1
        x0, x1, z0, z1 = cx(i), cx(i + 1), cz(j), cz(j2 + 1)
        quads.append((tex_suelo((x0 + x1) / 2, (z0 + z1) / 2, y), [(x0, y + 0.02, z0), (x0, y + 0.02, z1), (x1, y + 0.02, z1), (x1, y + 0.02, z0)], 'y'))
        j = j2 + 1
# 3) paredes en el borde de la máscara (aristas entre celda dentro y fuera), 0,3 m por fuera
OFF = 0.3
def pared(p0, p1, y0, y1, nrm):
    o = np.array([-nrm[0], 0, -nrm[1]]) * OFF     # nrm apunta hacia dentro; se aparta hacia fuera
    a = np.array([p0[0], y0, p0[1]]) + o; b = np.array([p1[0], y0, p1[1]]) + o
    pts = [a, b, b + [0, y1 - y0, 0], a + [0, y1 - y0, 0]]
    L = np.linalg.norm(b - a); s0 = (p0[0] + p0[1])
    uv = [(s0, y0), (s0 + L, y0), (s0 + L, y1), (s0, y1)]
    # orden: la cara debe mirar hacia dentro (nrm)
    e = np.cross(pts[1] - pts[0], pts[3] - pts[0])
    if e[0] * nrm[0] + e[2] * nrm[1] < 0: pts = pts[::-1]; uv = uv[::-1]
    quads.append((t_pared, [tuple(p) for p in pts], uv))
q = lambda v: round(v / 0.5) * 0.5
for axis in (0, 1):
    for sgn in (1, -1):
        # celdas dentro cuyo vecino en esa dirección está fuera
        sh = np.zeros_like(mask)
        if axis == 0:
            if sgn > 0: sh[:-1] = mask[1:]
            else: sh[1:] = mask[:-1]
        else:
            if sgn > 0: sh[:, :-1] = mask[:, 1:]
            else: sh[:, 1:] = mask[:, :-1]
        borde = mask & ~sh
        if axis == 0:
            for i in range(nx):
                j = 0
                while j < nz:
                    if not borde[i, j]: j += 1; continue
                    y0 = q(suelo[i, j] - 0.25); y1 = q(techo_loc[i, j] + 0.25); j2 = j
                    while j2 + 1 < nz and borde[i, j2 + 1] and q(suelo[i, j2 + 1] - 0.25) == y0 and q(techo_loc[i, j2 + 1] + 0.25) == y1: j2 += 1
                    xe = cx(i + 1) if sgn > 0 else cx(i)
                    pared((xe, cz(j)), (xe, cz(j2 + 1)), y0, y1, (-sgn, 0)); j = j2 + 1
        else:
            for j in range(nz):
                i = 0
                while i < nx:
                    if not borde[i, j]: i += 1; continue
                    y0 = q(suelo[i, j] - 0.25); y1 = q(techo_loc[i, j] + 0.25); i2 = i
                    while i2 + 1 < nx and borde[i2 + 1, j] and q(suelo[i2 + 1, j] - 0.25) == y0 and q(techo_loc[i2 + 1, j] + 0.25) == y1: i2 += 1
                    ze = cz(j + 1) if sgn > 0 else cz(j)
                    pared((cx(i), ze), (cx(i2 + 1), ze), y0, y1, (0, -sgn)); i = i2 + 1
# 4) techo: celdas sin nada por encima de suelo+1,8 m
sin_techo = mask & (vis_any < suelo + 1.8)
sin_techo = ndimage.binary_opening(sin_techo, iterations=1)
if '--sin-techo' in sys.argv: sin_techo[:] = False
for i in range(nx):
    j = 0
    while j < nz:
        if not sin_techo[i, j]: j += 1; continue
        y = q(techo_loc[i, j] + 0.1); j2 = j
        while j2 + 1 < nz and sin_techo[i, j2 + 1] and q(techo_loc[i, j2 + 1] + 0.1) == y: j2 += 1
        x0, x1, z0, z1 = cx(i), cx(i + 1), cz(j), cz(j2 + 1)
        quads.append((t_techo, [(x0, y, z0), (x1, y, z0), (x1, y, z1), (x0, y, z1)], 'y'))   # mirando hacia abajo
        j = j2 + 1

doble = next((a.split('=', 1)[1] for a in sys.argv if a.startswith('--doble=')), None)
dobles = []
if doble:
    y0d, y1d = map(float, doble.split(','))
    cyv = tri[:, :, 1].mean(1)
    sel = np.nonzero((np.abs(n[:, 1]) < 0.7) & (cyv > y0d) & (cyv < y1d) & (ar > 1e-6))[0]
    dobles = sel
print(f'{r}: dobles {len(dobles)} tri, rejilla {nx}x{nz}, planta {mask.sum()*CEL*CEL:.0f} m2, suelo que falta {falta.sum()*CEL*CEL:.1f} m2, '
      f'sin techo {sin_techo.sum()*CEL*CEL:.1f} m2, piezas {len(quads)} ({2*len(quads)} tri); texturas pared={t_pared} techo={t_techo} suelo={t_suelo}')
np.save(f'/tmp/env_mask_{r}.npy', np.stack([mask, falta, sin_techo, mv, mc]))
if informe: sys.exit()
with open(path, 'a') as f:
    f.write('\n# envolvente (uc_envolvente.py)\n')
    if len(dobles):
        cur = None
        for i in dobles:
            if M[i] != cur: f.write(f'usemtl {M[i]}\n'); cur = M[i]
            fv = F[i]
            f.write('f ' + ' '.join(f'{fv[k]+1}/{fv[3+k]+1}' for k in (0, 2, 1)) + '\n')
    nvb = len(V); ntb = len(T)
    for k, (t, P, kind) in enumerate(quads):
        P = np.array(P)
        uv = P[:, [0, 2]] / 2.0 if isinstance(kind, str) else np.array(kind) / 2.0
        for p in P: f.write(f'v {p[0]:.4f} {p[1]:.4f} {p[2]:.4f}\n')
        for u, v in uv: f.write(f'vt {u:.4f} {v:.4f}\n')
        a = nvb + 4 * k + 1; b = ntb + 4 * k + 1
        f.write(f'usemtl {mat_de[t]}\nf {a}/{b} {a+1}/{b+1} {a+2}/{b+2}\nf {a}/{b} {a+2}/{b+2} {a+3}/{b+3}\n')
