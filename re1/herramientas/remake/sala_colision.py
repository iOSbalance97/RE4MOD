"""sala_colision.py rNNN salida : sala modelada desde la colisión del REmake con texturas del castillo de RE4.
Paredes de doble cara, suelos de losas, rampas convertidas en escaleras con peldaños, techo a +3 m (salvo bajo otro tramo)."""
import sys, os, shutil
import numpy as np
from collections import defaultdict
sys.path.insert(0, '/home/claude/tools'); from hmap import floors, heights
r, out = sys.argv[1], sys.argv[2]; os.makedirs(out, exist_ok=True)
CAS = '/home/claude/uc/m/r103'
TEX = dict(pared='cas_ladrillo', suelo='cas_losas', huella='cas_losas', tabica='cas_piedra', techo='cas_piedra_techo')
from PIL import Image
for t in TEX.values():
    im = np.asarray(Image.open(f'{CAS}/{t}.png').convert('RGB'), np.float32) * float(os.environ.get('OSCURO', 0.72))
    Image.fromarray(np.clip(im, 0, 255).astype(np.uint8)).save(f'{out}/{t}.png')
col = f'/home/claude/re1gc/salas/{r}/colision.obj'
V = []; Fi = []
for l in open(col):
    if l.startswith('v '): V.append([float(x) for x in l.split()[1:4]])
    elif l.startswith('f '): Fi.append([int(x.split('/')[0]) - 1 for x in l.split()[1:4]])
V = np.array(V); Fi = np.array(Fi); T = V[Fi]
n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]); a = np.linalg.norm(n, axis=1) / 2; n /= 2 * a[:, None] + 1e-12
TF = floors(col); ALTO = 3.0; E = 1.6
geo = defaultdict(list)                         # material -> [(tri xyz, tri uv)]
def tri(m, p, uv, dos=True):
    geo[m].append((np.array(p, float), np.array(uv, float)))
    if dos: geo[m].append((np.array(p, float)[::-1], np.array(uv, float)[::-1]))
def quad(m, p, uv, dos=True):
    tri(m, [p[0], p[1], p[2]], [uv[0], uv[1], uv[2]], dos); tri(m, [p[0], p[2], p[3]], [uv[0], uv[2], uv[3]], dos)
def techo_libre(c):
    h = heights(TF, c[0], c[2]); return not np.any((h > c[1] + 0.5) & (h < c[1] + ALTO + 0.2))
plano = n[:, 1] > 0.97; rampa = (n[:, 1] > 0.45) & ~plano; pared = np.abs(n[:, 1]) < 0.35
# suelos y techo
for t3 in T[plano]:
    tri(TEX['suelo'], t3, t3[:, [0, 2]] / E, dos=False if False else True)
    c = t3.mean(0)
    if techo_libre(c): q = t3.copy(); q[:, 1] += ALTO; tri(TEX['techo'], q, q[:, [0, 2]] / E)
# paredes (de doble cara)
for t3, nn in zip(T[pared], n[pared]):
    h_ = np.array([-nn[2], 0, nn[0]]); h_ /= np.linalg.norm(h_) + 1e-12
    pr = t3 @ h_; A_, B_ = t3[pr.argmin()], t3[pr.argmax()]
    if pr.max() - pr.min() < 0.03: continue
    ya, yb = t3[:, 1].min(), t3[:, 1].min() + ALTO + 0.15          # de su base hasta el techo
    p = [np.array([A_[0], ya, A_[2]]), np.array([B_[0], ya, B_[2]]), np.array([B_[0], yb, B_[2]]), np.array([A_[0], yb, A_[2]])]
    quad(TEX['pared'], p, [[pr.min() / E, ya / E], [pr.max() / E, ya / E], [pr.max() / E, yb / E], [pr.min() / E, yb / E]])
# rampas -> escaleras: agrupar por normal parecida y contigüidad
idx = np.nonzero(rampa)[0]; grupo = {}
for i in idx:
    for g, lst in grupo.items():
        j = lst[0]
        if np.dot(n[i], n[j]) > 0.97 and np.min(np.linalg.norm(T[i][:, None] - np.concatenate([T[k] for k in lst])[None], axis=2)) < 0.05:
            lst.append(i); break
    else: grupo[i] = [i]
esc = 0
for g, lst in grupo.items():
    P = np.concatenate([T[k] for k in lst]); nn = n[lst[0]]
    up = -np.array([nn[0], 0, nn[2]]); up /= np.linalg.norm(up) + 1e-12; ac = np.array([-up[2], 0, up[0]])
    u = P @ up; v = P @ ac; u0, u1 = u.min(), u.max(); v0, v1 = v.min(), v.max()
    y0 = P[np.argmin(u), 1]; y1 = P[np.argmax(u), 1]
    if y1 - y0 < 0.3 or u1 - u0 < 0.4:
        for k in lst: tri(TEX['suelo'], T[k], T[k][:, [0, 2]] / E)
        continue
    N = max(2, int(round((y1 - y0) / 0.18))); rise = (y1 - y0) / N; run = (u1 - u0) / N
    def pt(uu, vv, yy): return up * uu + ac * vv + np.array([0, yy, 0])
    for s in range(N):
        ua, ub = u0 + s * run, u0 + (s + 1) * run; yt = y0 + (s + 1) * rise; yb = y0 + s * rise
        # huella
        quad(TEX['huella'], [pt(ua, v0, yt), pt(ub, v0, yt), pt(ub, v1, yt), pt(ua, v1, yt)],
             [[ua / E, v0 / E], [ub / E, v0 / E], [ub / E, v1 / E], [ua / E, v1 / E]])
        # tabica (frente del peldaño)
        quad(TEX['tabica'], [pt(ua, v0, yb), pt(ua, v1, yb), pt(ua, v1, yt), pt(ua, v0, yt)],
             [[v0 / E, yb / E], [v1 / E, yb / E], [v1 / E, yt / E], [v0 / E, yt / E]])
        # laterales del peldaño (por si queda un lado al aire)
        for vv in (v0, v1):
            quad(TEX['tabica'], [pt(ua, vv, y0 - 0.02), pt(ub, vv, y0 - 0.02), pt(ub, vv, yt), pt(ua, vv, yt)],
                 [[ua / E, (y0 - 0.02) / E], [ub / E, (y0 - 0.02) / E], [ub / E, yt / E], [ua / E, yt / E]])
    # techo inclinado sobre el tramo
    for k in lst:
        c = T[k].mean(0)
        if techo_libre(c): q = T[k].copy(); q[:, 1] += ALTO; tri(TEX['techo'], q, q[:, [0, 2]] / E)
    esc += 1
with open(f'{out}/sala.mtl', 'w') as fm:
    for m in geo: fm.write(f'newmtl {m}\nKd 1 1 1\nmap_Kd {m}.png\n')
with open(f'{out}/sala.obj', 'w') as fo:
    fo.write('mtllib sala.mtl\n'); nv = 1
    for m, lst in geo.items():
        fo.write(f'usemtl {m}\n')
        for p, uv in lst:
            for q in p: fo.write(f'v {q[0]:.4f} {q[1]:.4f} {q[2]:.4f}\n')
            for q in uv: fo.write(f'vt {q[0]:.4f} {q[1]:.4f}\n')
            fo.write(f'f {nv}/{nv} {nv+1}/{nv+1} {nv+2}/{nv+2}\n'); nv += 3
shutil.copy(col, f'{out}/colision.obj')
print(f'{r}: {sum(len(l) for l in geo.values())} triángulos, {esc} tramos de escalera')
