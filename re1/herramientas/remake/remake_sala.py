"""Sala del REmake de GameCube -> OBJ texturizado con sus propios fondos (proyección desde sus cámaras fijas).
uso: remake_sala.py st rNNN salida [lado_max_mm]
 - geometría: malla detallada del .dat (sección 1), subdividida (conforme) hasta lado_max
 - cada triángulo toma la cámara que mejor lo ve: delante, de cara, dentro de la imagen, sin nada delante
   (prueba de profundidad con la propia malla), y con más píxeles en pantalla
 - UV = proyección del vértice en la imagen de esa cámara (fondo 512x448 -> textura 512x512)
 - triángulos que ninguna cámara ve: se les da la cámara que los ve con menos penalización (o gris oscuro)
 - colisión: malla simple del .dat (sección 0) en colision.obj
Unidades del REmake = mm; el OBJ sale en metros."""
import json, os, sys
import numpy as np
from PIL import Image
sys.path.insert(0, '/home/claude/re1gc/work'); import remake

st, r, out = int(sys.argv[1]), sys.argv[2], sys.argv[3]
LMAX = float(sys.argv[4]) if len(sys.argv) > 4 else 700.0
os.makedirs(out, exist_ok=True)
V, T, _ = remake.malla(st, r, 1)
cams = [c for c in remake.camaras(st, r) if c['img'] is not None]

# ---------------- subdivisión conforme (partir aristas largas)
V = [tuple(v) for v in V]; T = [tuple(t) for t in T]
def subdividir(V, T, L):
    V = list(V); T = list(T)
    for _ in range(12):
        mid = {}
        def m(a, b):
            k = (min(a, b), max(a, b))
            if k not in mid:
                mid[k] = len(V); V.append(tuple((np.array(V[a]) + np.array(V[b])) / 2))
            return mid[k]
        largo = lambda a, b: np.linalg.norm(np.subtract(V[a], V[b])) > L
        marcadas = set()
        for t in T:
            for a, b in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
                if largo(a, b): marcadas.add((min(a, b), max(a, b)))
        if not marcadas: break
        NT = []
        for a, b, c in T:
            e = [(min(a, b), max(a, b)) in marcadas, (min(b, c), max(b, c)) in marcadas, (min(c, a), max(c, a)) in marcadas]
            n = sum(e)
            if n == 0: NT.append((a, b, c))
            elif n == 3:
                ab, bc, ca = m(a, b), m(b, c), m(c, a); NT += [(a, ab, ca), (ab, b, bc), (ca, bc, c), (ab, bc, ca)]
            elif n == 1:
                if e[0]: x = m(a, b); NT += [(a, x, c), (x, b, c)]
                elif e[1]: x = m(b, c); NT += [(a, b, x), (a, x, c)]
                else: x = m(c, a); NT += [(a, b, x), (x, b, c)]
            else:
                # dos aristas: partir las dos (y la tercera queda) -> 3 triángulos
                if not e[0]: ab_ = None; bc, ca = m(b, c), m(c, a); NT += [(a, b, bc), (a, bc, ca), (ca, bc, c)]
                elif not e[1]: ab, ca = m(a, b), m(c, a); NT += [(a, ab, ca), (ab, b, c), (ab, c, ca)]
                else: ab, bc = m(a, b), m(b, c); NT += [(a, ab, c), (ab, b, bc), (ab, bc, c)]
        T = NT
    return np.array(V, float), np.array(T, int)
V, T = subdividir(V, T, LMAX)
P = V[T]; nrm = np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0]); area = np.linalg.norm(nrm, axis=1) / 2
nrm /= (2 * area[:, None] + 1e-9); cen = P.mean(1)
print(f'{r}: {len(V)} vértices, {len(T)} triángulos tras subdividir a {LMAX:.0f} mm; {len(cams)} cámaras')

# ---------------- profundidad por cámara (rasterizado de la propia malla a baja resolución)
RW, RH = 256, 224
def zbuffer(c):
    p, z = remake.proyectar(c, V)
    p = p * [RW / 512, RH / 448]
    Z = np.full((RH, RW), np.inf)
    for t in T:
        if (z[t] < 20).any(): continue
        q = p[t]; zz = z[t]
        x0, x1 = int(max(0, np.floor(q[:, 0].min()))), int(min(RW - 1, np.ceil(q[:, 0].max())))
        y0, y1 = int(max(0, np.floor(q[:, 1].min()))), int(min(RH - 1, np.ceil(q[:, 1].max())))
        if x0 > x1 or y0 > y1: continue
        X, Y = np.meshgrid(np.arange(x0, x1 + 1) + .5, np.arange(y0, y1 + 1) + .5)
        d = (q[1, 1] - q[2, 1]) * (q[0, 0] - q[2, 0]) + (q[2, 0] - q[1, 0]) * (q[0, 1] - q[2, 1])
        if abs(d) < 1e-9: continue
        w0 = ((q[1, 1] - q[2, 1]) * (X - q[2, 0]) + (q[2, 0] - q[1, 0]) * (Y - q[2, 1])) / d
        w1 = ((q[2, 1] - q[0, 1]) * (X - q[2, 0]) + (q[0, 0] - q[2, 0]) * (Y - q[2, 1])) / d
        w2 = 1 - w0 - w1; m = (w0 >= -.01) & (w1 >= -.01) & (w2 >= -.01)
        zi = 1 / (w0 / zz[0] + w1 / zz[1] + w2 / zz[2])
        sub = Z[y0:y1 + 1, x0:x1 + 1]; upd = m & (zi < sub); sub[upd] = zi[upd]
    return Z
puntos = []
for ci, c in enumerate(cams):
    Z = zbuffer(c)
    p, z = remake.proyectar(c, V)
    pc, zc = remake.proyectar(c, cen)
    q = p[T]                                           # (nt,3,2)
    dentro = (z[T] > 20).all(1) & (q[:, :, 0] >= 1).all(1) & (q[:, :, 0] <= 511).all(1) & (q[:, :, 1] >= 1).all(1) & (q[:, :, 1] <= 447).all(1)
    de_cara = np.einsum('ij,ij->i', nrm, c['ojo'] - cen) > 0
    # visible: la profundidad del centro (y de los 3 vértices) no está tapada en el z-buffer
    def vis(pp, zz):
        x = np.clip((pp[..., 0] * RW / 512).astype(int), 0, RW - 1); y = np.clip((pp[..., 1] * RH / 448).astype(int), 0, RH - 1)
        return zz <= Z[y, x] * 1.03 + 40
    visible = vis(pc, zc) & vis(q, z[T]).all(1)
    px = np.abs((q[:, 1, 0] - q[:, 0, 0]) * (q[:, 2, 1] - q[:, 0, 1]) - (q[:, 2, 0] - q[:, 0, 0]) * (q[:, 1, 1] - q[:, 0, 1])) / 2
    cosang = np.abs(np.einsum('ij,ij->i', nrm, (c['ojo'] - cen) / np.linalg.norm(c['ojo'] - cen, axis=1, keepdims=True)))
    score = np.where(dentro & de_cara & visible, px * (0.3 + cosang), -1.0)
    score2 = np.where(dentro & de_cara, px * 0.01, -2.0)              # reserva: aunque esté tapado
    puntos.append((score, score2, p))
    print(f'  cámara {ci:2d}: ve bien {int((score > 0).sum())} triángulos')
S = np.stack([s for s, _, _ in puntos]); S2 = np.stack([s for _, s, _ in puntos])
elegida = np.argmax(S, 0); ok = S.max(0) > 0
reserva = np.argmax(S2, 0); ok2 = S2.max(0) > -1
cam_t = np.where(ok, elegida, np.where(ok2, reserva, -1))
print(f'  con cámara buena {ok.mean()*100:.0f} %, de reserva {(~ok & ok2).mean()*100:.0f} %, sin cámara {(cam_t < 0).mean()*100:.0f} %')

# ---------------- OBJ
usadas = sorted(set(int(c) for c in cam_t if c >= 0))
with open(f'{out}/sala.mtl', 'w') as f:
    for ci in usadas:
        cams[ci]['img'].resize((512, 512), Image.LANCZOS).save(f'{out}/fondo_{ci:02d}.png')
        f.write(f'newmtl fondo_{ci:02d}\nKd 1 1 1\nmap_Kd fondo_{ci:02d}.png\n')
    Image.new('RGB', (8, 8), (24, 22, 20)).save(f'{out}/oscuro.png'); f.write('newmtl oscuro\nKd 1 1 1\nmap_Kd oscuro.png\n')
with open(f'{out}/sala.obj', 'w') as f:
    f.write('mtllib sala.mtl\n')
    for v in V / 1000.0: f.write(f'v {v[0]:.4f} {v[1]:.4f} {v[2]:.4f}\n')
    vt = 1
    for ci in usadas + [-1]:
        sel = np.nonzero(cam_t == ci)[0]
        if not len(sel): continue
        f.write(f'usemtl {"fondo_%02d" % ci if ci >= 0 else "oscuro"}\n')
        for i in sel:
            t = T[i]
            if ci >= 0:
                q = puntos[ci][2][t]
                for u, v in q: f.write(f'vt {u/512:.5f} {1 - v/448:.5f}\n')
            else:
                for _ in range(3): f.write('vt 0.5 0.5\n')
            f.write(f'f {t[0]+1}/{vt} {t[1]+1}/{vt+1} {t[2]+1}/{vt+2}\n'); vt += 3
# colisión (malla simple)
Vc, Tc, _ = remake.malla(st, r, 0)
with open(f'{out}/colision.obj', 'w') as f:
    for v in Vc / 1000.0: f.write(f'v {v[0]:.4f} {v[1]:.4f} {v[2]:.4f}\n')
    for t in Tc: f.write(f'f {t[0]+1} {t[1]+1} {t[2]+1}\n')
json.dump(dict(camaras=[dict(ojo=c['ojo'].tolist(), obj=c['obj'].tolist(), fov=c['fov']) for c in cams], usadas=usadas), open(f'{out}/meta.json', 'w'))
