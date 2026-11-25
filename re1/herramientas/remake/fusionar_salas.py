"""fusionar_salas.py base otra modelo_uc.obj : colisión única = base + otra con sus suelos recortados a donde el modelo tiene suelo
(el REmake tapa con suelo invisible los huecos entre plantas). Escribe salas/base/colision_fusion.obj y re4/re_base/col."""
import sys, os, shutil, subprocess, numpy as np
from scipy.spatial import cKDTree
base, otra, modelo = sys.argv[1], sys.argv[2], sys.argv[3]
R1 = '/home/claude/re1gc'
def leer(p):
    V = []; F = []
    for l in open(p):
        if l.startswith('v '): V.append([float(x) for x in l.split()[1:4]])
        elif l.startswith('f '):
            q = [int(x.split('/')[0]) - 1 for x in l.split()[1:]]
            for k in range(1, len(q) - 1): F.append([q[0], q[k], q[k + 1]])
    return np.array(V), np.array(F)
Vb, Fb = leer(f'{R1}/salas/{base}/colision.obj'); Vo, Fo = leer(f'{R1}/salas/{otra}/colision.obj')
Vm, Fm = leer(modelo); Tm = Vm[Fm]
nm = np.cross(Tm[:, 1] - Tm[:, 0], Tm[:, 2] - Tm[:, 0]); am = np.linalg.norm(nm, axis=1); nm /= am[:, None] + 1e-12
# muestras del suelo del modelo (caras hacia arriba)
up = np.nonzero((nm[:, 1] > 0.8) & (am > 1e-6))[0]
rg = np.random.default_rng(0); P = []
for i in up:
    k = max(1, int(am[i] / 2 / 0.01)); w = rg.dirichlet([1, 1, 1], min(k, 400)); P.append(w @ Tm[i])
P = np.concatenate(P); arbol = cKDTree(P[:, [0, 2]])
To = Vo[Fo]; no = np.cross(To[:, 1] - To[:, 0], To[:, 2] - To[:, 0]); no /= np.linalg.norm(no, axis=1, keepdims=True) + 1e-12
suelo = no[:, 1] > 0.7
tri_v = []; tri_f = []
def add(pts):
    b = len(tri_v); tri_v.extend(pts); tri_f.append([b, b + 1, b + 2])
for t in To[~suelo]: add(list(t))
# suelos: rejilla de 0.25 m, se conserva la celda si el modelo tiene suelo a esa altura
G = 0.25; quitadas = puestas = 0; celdas_si = {}; celdas_no = set()
for t in To[suelo]:
    lo = t[:, [0, 2]].min(0); hi = t[:, [0, 2]].max(0); y = t[:, 1].mean()
    for x in np.arange(np.floor(lo[0] / G) * G, hi[0], G):
        for z in np.arange(np.floor(lo[1] / G) * G, hi[1], G):
            c = np.array([x + G / 2, z + G / 2])
            # dentro del triángulo (2D)?
            a, b_, cc = t[:, [0, 2]]
            d = (b_[1] - cc[1]) * (a[0] - cc[0]) + (cc[0] - b_[0]) * (a[1] - cc[1])
            if abs(d) < 1e-12: continue
            w0 = ((b_[1] - cc[1]) * (c[0] - cc[0]) + (cc[0] - b_[0]) * (c[1] - cc[1])) / d
            w1 = ((cc[1] - a[1]) * (c[0] - cc[0]) + (a[0] - cc[0]) * (c[1] - cc[1])) / d
            if min(w0, w1, 1 - w0 - w1) < -1e-6: continue
            idx = arbol.query_ball_point(c, G * 0.75)
            if any(abs(P[j, 1] - y) < 0.25 for j in idx):
                add([[x, y, z], [x, y, z + G], [x + G, y, z + G]]); add([[x, y, z], [x + G, y, z + G], [x + G, y, z]]); puestas += 1
                celdas_si[(int(round(x / G)), int(round(z / G)))] = y
            else: quitadas += 1; celdas_no.add((int(round(x / G)), int(round(z / G))))
# paredes invisibles en el borde del hueco: no se puede andar por el aire
paredes = 0
for (i, j), y in celdas_si.items():
    for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        if (i + di, j + dj) in celdas_no:
            x0, z0 = i * G, j * G
            if di == 1: p, q = (x0 + G, z0), (x0 + G, z0 + G)
            elif di == -1: p, q = (x0, z0), (x0, z0 + G)
            elif dj == 1: p, q = (x0, z0 + G), (x0 + G, z0 + G)
            else: p, q = (x0, z0), (x0 + G, z0)
            a_, b_ = [p[0], y, p[1]], [q[0], y, q[1]]; c_ = [q[0], y + 2.5, q[1]]; d_ = [p[0], y + 2.5, p[1]]
            add([a_, b_, c_]); add([a_, c_, d_]); add([a_, c_, b_]); add([a_, d_, c_]); paredes += 1
print(f'{otra}: celdas de suelo conservadas {puestas}, quitadas (hueco entre plantas) {quitadas}, paredes de borde {paredes}')
out = f'{R1}/salas/{base}/colision_fusion.obj'
with open(out, 'w') as f:
    for v in Vb: f.write(f'v {v[0]:.4f} {v[1]:.4f} {v[2]:.4f}\n')
    for v in tri_v: f.write(f'v {v[0]:.4f} {v[1]:.4f} {v[2]:.4f}\n')
    for t in Fb: f.write(f'f {t[0]+1} {t[1]+1} {t[2]+1}\n')
    for t in tri_f: f.write(f'f {t[0]+len(Vb)+1} {t[1]+len(Vb)+1} {t[2]+len(Vb)+1}\n')
dcol = f'{R1}/re4/re_{base}/col'
if not os.path.exists(dcol + '_orig'): shutil.copytree(dcol, dcol + '_orig')
r = subprocess.run(['python3', '/home/claude/tools/obj2sat.py', out, dcol], capture_output=True, text=True); print(r.stdout[-300:], r.stderr[-300:])
shutil.copy(out, f'{dcol}/colision.obj')
