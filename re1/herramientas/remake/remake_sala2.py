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
_A = sum(np.linalg.norm(np.cross(np.subtract(V[b], V[a]), np.subtract(V[c], V[a]))) / 2 for a, b, c in T)
LMAX = max(LMAX, float(np.sqrt(_A / (0.43 * float(os.environ.get('MAXTRI', 45000))))))
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
puntos = []; Zs = []
for ci, c in enumerate(cams):
    Z = zbuffer(c); Zs.append(Z)
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
MAXCAM = int(os.environ.get('MAXCAM', 22))
activas = np.ones(len(cams), bool)
while True:
    usos = np.array([area[(elegida == ci) & ok].sum() if activas[ci] else np.inf for ci in range(len(cams))])
    if activas.sum() <= MAXCAM: break
    activas[int(np.argmin(usos))] = False
    S_ = np.where(activas[:, None], S, -1.0); elegida = np.argmax(S_, 0); ok = S_.max(0) > 0
if not activas.all(): print(f'  cámaras usadas {activas.sum()} de {len(cams)} (límite de texturas)')
reserva = np.argmax(S2, 0); ok2 = S2.max(0) > -1
cam_t = np.where(ok, elegida, np.where(ok2, reserva, -1))
print(f'  con cámara buena {ok.mean()*100:.0f} %, de reserva {(~ok & ok2).mean()*100:.0f} %, sin cámara {(cam_t < 0).mean()*100:.0f} %')
# ---------------- calidad: densidad de píxeles por m² y ángulo; lo que no llega se rellena con material
dens = np.zeros(len(T)); colores = np.full((len(T), 3), np.nan)
imgs = [np.asarray(Image.eval(c['img'], lambda x: int(255 * (x / 255) ** 0.8)), float) for c in cams]
for ci, (score, score2, p) in enumerate(puntos):
    q = p[T]; px = np.abs((q[:, 1, 0] - q[:, 0, 0]) * (q[:, 2, 1] - q[:, 0, 1]) - (q[:, 2, 0] - q[:, 0, 0]) * (q[:, 1, 1] - q[:, 0, 1])) / 2
    d = px / (area / 1e6 + 1e-9)
    sel = (elegida == ci) & ok
    dens[sel] = d[sel]
    vis = score > 0
    pc = q.mean(1); x = np.clip(pc[:, 0].astype(int), 0, 511); y = np.clip(pc[:, 1].astype(int), 0, 447)
    c = imgs[ci][y, x]
    nuevo_c = vis & np.isnan(colores[:, 0])
    colores[nuevo_c] = c[nuevo_c]
cosmejor = np.zeros(len(T))
for i in np.nonzero(ok)[0]:
    c = cams[int(elegida[i])]; v = c['ojo'] - cen[i]; cosmejor[i] = abs(np.dot(nrm[i], v / np.linalg.norm(v)))
DMIN = float(os.environ.get('DMIN', 100))             # píxeles por m² (≈16 px/m)
bueno = ok & (dens >= DMIN) & (cosmejor >= 0.15)
print(f'  proyección buena {bueno.mean()*100:.0f} %, con material {(~bueno).mean()*100:.0f} %')
uv_t = {}
for i in np.nonzero(bueno)[0]: uv_t[i] = (int(elegida[i]), puntos[int(elegida[i])][2][T[i]])
cam_t = np.where(bueno, elegida, -1)

from PIL import ImageFilter
# ---------------- ortofoto de los suelos: vista cenital reconstruida con lo mejor de cada cámara
import cv2
horiz = nrm[:, 1] > 0.75
niveles = {}
for i in np.nonzero(horiz)[0]: niveles.setdefault(int(round(cen[i, 1] / 300)), []).append(int(i))
orto = []           # (tris, png, x0, z0, ancho_m, alto_m)
en_orto = np.zeros(len(T), bool)
imgs_f = [cv2.cvtColor(np.asarray(Image.eval(c['img'], lambda x: int(255 * (x / 255) ** 0.8))), cv2.COLOR_RGB2BGR).astype(np.float32) for c in cams]
for lv, ts in sorted(niveles.items()):
    ts = np.array(ts)
    if area[ts].sum() / 1e6 < float(os.environ.get('ORTO_MIN', 2.0)): continue
    Pq = P[ts]; x0, z0 = Pq[:, :, 0].min(), Pq[:, :, 2].min(); x1, z1 = Pq[:, :, 0].max(), Pq[:, :, 2].max()
    ext = max(x1 - x0, z1 - z0) / 1000
    ppm = float(np.clip(1024 / max(ext, 0.5), 24, 80))
    Wd, Hd = max(8, int((x1 - x0) / 1000 * ppm) + 2), max(8, int((z1 - z0) / 1000 * ppm) + 2)
    # alturas por píxel (rasterizado cenital de los triángulos del nivel)
    Y = np.full((Hd, Wd), np.nan, np.float32)
    for t in T[ts]:
        q = np.stack([(V[t, 0] - x0) / 1000 * ppm, (V[t, 2] - z0) / 1000 * ppm], 1); yy = V[t, 1]
        xa, xb = int(max(0, np.floor(q[:, 0].min()))), int(min(Wd - 1, np.ceil(q[:, 0].max())))
        ya, yb = int(max(0, np.floor(q[:, 1].min()))), int(min(Hd - 1, np.ceil(q[:, 1].max())))
        if xa > xb or ya > yb: continue
        X_, Y_ = np.meshgrid(np.arange(xa, xb + 1) + .5, np.arange(ya, yb + 1) + .5)
        d = (q[1, 1] - q[2, 1]) * (q[0, 0] - q[2, 0]) + (q[2, 0] - q[1, 0]) * (q[0, 1] - q[2, 1])
        if abs(d) < 1e-9: continue
        w0 = ((q[1, 1] - q[2, 1]) * (X_ - q[2, 0]) + (q[2, 0] - q[1, 0]) * (Y_ - q[2, 1])) / d
        w1 = ((q[2, 1] - q[0, 1]) * (X_ - q[2, 0]) + (q[0, 0] - q[2, 0]) * (Y_ - q[2, 1])) / d
        w2 = 1 - w0 - w1; m = (w0 >= -.05) & (w1 >= -.05) & (w2 >= -.05)
        sub = Y[ya:yb + 1, xa:xb + 1]; v = w0 * yy[0] + w1 * yy[1] + w2 * yy[2]
        sub[m & np.isnan(sub)] = v[m & np.isnan(sub)]
    mask = ~np.isnan(Y)
    if mask.sum() < 50: continue
    Yf = np.where(mask, Y, np.nanmean(Y))
    gx, gz = np.meshgrid((np.arange(Wd) + .5) / ppm * 1000 + x0, (np.arange(Hd) + .5) / ppm * 1000 + z0)
    W3 = np.stack([gx, Yf, gz], -1).reshape(-1, 3)
    mejor = np.zeros(Wd * Hd); color = np.zeros((Wd * Hd, 3), np.float32)
    paso = 1000 / ppm
    for ci, c in enumerate(cams):
        p, z = remake.proyectar(c, W3)
        px_, _ = remake.proyectar(c, W3 + [paso, 0, 0]); pz_, _ = remake.proyectar(c, W3 + [0, 0, paso])
        dx = px_ - p; dz = pz_ - p
        mag = np.abs(dx[:, 0] * dz[:, 1] - dx[:, 1] * dz[:, 0])        # píxeles de fondo por píxel de ortofoto
        ok_ = (z > 20) & (p[:, 0] >= 0) & (p[:, 0] < 511) & (p[:, 1] >= 0) & (p[:, 1] < 447)
        xi = np.clip((p[:, 0] * RW / 512).astype(int), 0, RW - 1); yi = np.clip((p[:, 1] * RH / 448).astype(int), 0, RH - 1)
        ok_ &= z <= Zs[ci][yi, xi] * 1.03 + 60
        # de cara: la cámara por encima del suelo
        ok_ &= c['ojo'][1] > W3[:, 1] + 100
        sc = np.where(ok_, np.minimum(mag, 4.0) * (1 + 0.0 * mag), 0)
        upd = sc > mejor
        if upd.any():
            mp = p[upd].astype(np.float32)
            im_ = imgs_f[ci]; xf = np.clip(mp[:, 0] - .5, 0, 510.999); yf = np.clip(mp[:, 1] - .5, 0, 446.999)
            xa_ = xf.astype(int); ya_ = yf.astype(int); fx = (xf - xa_)[:, None]; fy = (yf - ya_)[:, None]
            smp = (im_[ya_, xa_] * (1 - fx) * (1 - fy) + im_[ya_, xa_ + 1] * fx * (1 - fy) + im_[ya_ + 1, xa_] * (1 - fx) * fy + im_[ya_ + 1, xa_ + 1] * fx * fy)
            color[upd] = smp; mejor[upd] = sc[upd]
    vale = (mejor >= float(os.environ.get('ORTO_MAG', 0.08))).reshape(Hd, Wd) & mask
    img = color.reshape(Hd, Wd, 3).clip(0, 255).astype(np.uint8)
    hueco = (~vale).astype(np.uint8) * 255
    if vale.mean() < 0.15: continue
    import periodico
    try: img2, vale2, info_ = periodico.rellenar_recorte(img, vale, mejor.reshape(Hd, Wd))
    except Exception as ex_: print('    relleno periódico falló:', ex_); info_ = None
    if info_ is not None:
        print(f'    patrón repetido: periodo {info_[0]}, {info_[1]}, parecido {info_[2]:.2f}')
        img = img2; hueco = (~vale2).astype(np.uint8) * 255
    img = cv2.inpaint(img, hueco, 6, cv2.INPAINT_TELEA)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    nombre = f'suelo_{len(orto):02d}.png'
    Image.fromarray(img).filter(ImageFilter.UnsharpMask(radius=1.2, percent=50, threshold=2)).save(f'{out}/{nombre}')
    orto.append((ts, nombre, x0, z0, (x1 - x0), (z1 - z0), Wd / ppm * 1000, Hd / ppm * 1000))
    en_orto[ts] = True
    print(f'  ortofoto nivel {lv*0.3:.1f} m: {Wd}x{Hd} px ({ppm:.0f} px/m), visto {vale[mask].mean()*100:.0f} %')

# suelos sueltos (escalones, alfombras, tarimas pequeñas) cerca de un nivel con ortofoto: usan esa ortofoto
if orto:
    ylv = [float(np.median(cen[o_[0], 1])) for o_ in orto]
    extra = [[] for _ in orto]
    for i in np.nonzero(horiz & ~en_orto)[0]:
        k = int(np.argmin([abs(cen[i, 1] - y_) for y_ in ylv]))
        if abs(cen[i, 1] - ylv[k]) < 400: extra[k].append(int(i))
    for k, ex in enumerate(extra):
        if ex:
            o_ = list(orto[k]); o_[0] = np.concatenate([o_[0], np.array(ex, int)]); orto[k] = tuple(o_); en_orto[ex] = True
cam_t[en_orto] = -2
# ---------------- superficies a rellenar: clase (suelo/pared/techo) + componentes casi coplanares
cls = np.where(nrm[:, 1] > 0.75, 0, np.where(nrm[:, 1] < -0.75, 2, 1))
cls[(cls == 0) & ~en_orto] = 1          # horizontales que no son suelo (mostradores, mesas): material de mueble

rel = np.nonzero(~bueno & ~en_orto)[0]
from collections import defaultdict
arist = defaultdict(list)
for i in rel:
    t = T[i]
    for a_, b_ in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])): arist[(min(a_, b_), max(a_, b_))].append(i)
padre = {int(i): int(i) for i in rel}
def raiz(i):
    while padre[i] != i: padre[i] = padre[padre[i]]; i = padre[i]
    return i
for ts in arist.values():
    for j in ts[1:]:
        a_, b_ = int(ts[0]), int(j)
        if cls[a_] == cls[b_] and np.dot(nrm[a_], nrm[b_]) > 0.9: padre[raiz(a_)] = raiz(b_)
grupos = defaultdict(list)
for i in rel: grupos[raiz(int(i))].append(int(i))
media_clase = {}
for k in (0, 1, 2):
    s_ = bueno & (cls == k) & ~np.isnan(colores[:, 0])
    media_clase[k] = colores[s_].mean(0) if s_.any() else None
todo = colores[~np.isnan(colores[:, 0])]
defecto = todo.mean(0) if len(todo) else np.array([70, 60, 50.])
vistos = np.nonzero(bueno & ~np.isnan(colores[:, 0]))[0]
from scipy.spatial import cKDTree
arbol = cKDTree(cen[vistos]) if len(vistos) else None
BIB = json.load(open('/home/claude/re1gc/biblioteca/indice.json'))
EXTERIOR = ('r116', 'r117', 'r118', 'r119', 'r144', 'r140', 'r142')
BIB = [e for e in BIB if e.get('repite', True) and (e['origen'].startswith('re5:') or e['area'] >= 15) and not any(f'/{x}/' in e['origen'] for x in EXTERIOR)
       and not (e['color'][1] > e['color'][0] * 1.08 and e['color'][1] > e['color'][2] * 1.12)]
def lab(c):
    c = np.asarray(c, float) / 255; L = c @ [0.3, 0.59, 0.11]
    return np.array([L * 2.0, (c[0] - c[1]), (c[1] + c[0]) / 2 - c[2]])
PALETA = {
 'mansion': dict(pared=['h_s700_wall02', 'h_s700_wall03', 'h_s700_wallpaper', 'h_s700_woodpanel', 'h_s700_turo_wall', 'h_s700_wall_white14'],
                 suelo=['h_s700_floor01', 'g_s700_din_jutang01', 'g_s700_din_yuka01', 'h_s700_yuka06', 'g-yukarouka01'],
                 techo=['h_s700_tenjyou01', 'g-s701-ctenjo', 'g-s701-atenjo']),
 'fuera': dict(pared=['g-s701-akabeiwa', 'g-s701-akabedanmen', 'g-s701-bnakakabe01', 'g-s701-bsotokabe01', 'g-s701-bsotokabe02', 'g-s701-csotokabenaka', 'g-s701-csotokabeshita', 'g-s701-akabetsuchi'],
               suelo=['g-s701-bnakayuka01', 'g-s701-ayukakoshitsu', 'g-s701-cyuka', 'y-s705-yukaaa'],
               techo=['g-s701-atenjo', 'g-s701-croukatenjo']),
 'residencia': dict(pared=['y_s407_kabef', 'y_s407_sotokabe', 'h_s700_wallpaper', 'h_s700_woodpanel', 'h_s700_wall03'],
                    suelo=['y_407_yukaa', 'h_s700_floor01', 'g-s701-cyuka'],
                    techo=['g-s701-ctenjo', 'h_s700_tenjyou01'])}
ZONA = {1: 'mansion', 2: 'mansion', 3: 'fuera', 4: 'residencia'}.get(st)
BIB_TODO = json.load(open('/home/claude/re1gc/biblioteca/indice.json'))
def elegir(k, col):
    nombre = ('suelo', 'pared', 'techo')[k]
    if ZONA:
        pal = [e for e in BIB_TODO if e['clase'] == nombre and e['origen'].startswith('re5:') and any(e['origen'][4:].startswith(n.lower()) for n in PALETA[ZONA][nombre])]
        if pal:
            L = lambda c: float(np.dot(c, [0.3, 0.59, 0.11]))
            return min(pal, key=lambda e: abs(L(e['color']) - L(col)) + 3.0 * pal.index(e) / len(pal))
    cand = [e for e in BIB if e['clase'] == nombre]
    return min(cand, key=lambda e: np.linalg.norm(lab(e['color']) - lab(col)) - 0.0004 * min(e['area'], 300) - 0.004 * min(e['detalle'], 12) - (0.25 if e['origen'].startswith('re5:') else 0))
mat_t = {}; tintes = {}; copia = []
for g, ts in grupos.items():
    ts = np.array(ts); k = int(cls[ts[0]])
    if area[ts].sum() / 1e6 < float(os.environ.get('AMIN', 1.5)) and arbol is not None:
        copia += list(ts); continue
    cs = colores[ts]; cs = cs[~np.isnan(cs[:, 0])]
    if len(cs) >= max(1, len(ts) // 5): col = cs.mean(0)
    elif arbol is not None:
        _, ks = arbol.query(cen[ts].mean(0), k=min(12, len(vistos)))
        ks = np.atleast_1d(ks); mism = [vistos[j] for j in ks if cls[vistos[j]] == k]
        col = colores[mism].mean(0) if mism else (media_clase[k] if media_clase[k] is not None else defecto)
    else: col = media_clase[k] if media_clase[k] is not None else defecto
    col = np.clip(col, 6, 250)
    _l = float(np.dot(col, [0.3, 0.59, 0.11])); col = _l + (col - _l) * 0.35          # color más neutro
    ref_ = media_clase.get(k) if media_clase.get(k) is not None else defecto
    lmax = float(np.dot(ref_, [0.3, 0.59, 0.11])) * 1.35; lc = float(np.dot(col, [0.3, 0.59, 0.11]))
    if lc > lmax: col = col * lmax / lc                       # que el relleno no brille más que lo que se ve
    e = elegir(k, col)
    clave = (e['id'], tuple(int(x) for x in np.round(col / 12) * 12))
    tintes.setdefault(clave, e)
    for i in ts: mat_t[int(i)] = clave
MAXT = 20
while len(tintes) > MAXT:
    ks_ = list(tintes); mejor = None
    for mismo in (True, False):
        for x in range(len(ks_)):
            for y in range(x + 1, len(ks_)):
                if mismo and ks_[x][0] != ks_[y][0]: continue
                d = np.linalg.norm(np.subtract(ks_[x][1], ks_[y][1]))
                if mejor is None or d < mejor[0]: mejor = (d, ks_[x], ks_[y])
        if mejor: break
    _, ka, kb = mejor
    for i, cl in list(mat_t.items()):
        if cl == kb: mat_t[i] = ka
    del tintes[kb]
for i in copia:
    _, ks = arbol.query(cen[i], k=min(24, len(vistos))); ks = np.atleast_1d(ks)
    j = next((vistos[k] for k in ks if abs(np.dot(nrm[i], nrm[vistos[k]])) > 0.8), vistos[ks[0]])
    uv_t[i] = uv_t[j]; cam_t[i] = uv_t[j][0]
print(f'  {len(copia)} triángulos copian la proyección vecina')
print(f'  {len(grupos)} superficies con material, {len(tintes)} materiales teñidos')

# ---------------- OBJ
from PIL import ImageFilter
usadas = sorted(set(int(c) for c in cam_t if c >= 0))
nombres_t = {cl: f'mat_{n:02d}' for n, cl in enumerate(tintes)}
with open(f'{out}/sala.mtl', 'w') as f:
    for ci in usadas:
        im = Image.eval(cams[ci]['img'], lambda x: int(255 * (x / 255) ** 0.8)).resize((512, 512), Image.LANCZOS)
        im = im.filter(ImageFilter.UnsharpMask(radius=1.4, percent=55, threshold=2))
        im.save(f'{out}/fondo_{ci:02d}.png')
        f.write(f'newmtl fondo_{ci:02d}\nKd 1 1 1\nmap_Kd fondo_{ci:02d}.png\n')
    for k_, o_ in enumerate(orto): f.write(f'newmtl orto_{k_:02d}\nKd 1 1 1\nmap_Kd {o_[1]}\n')
    for cl, e in tintes.items():
        im = Image.open(e['png']).convert('RGB')
        if max(im.size) > 256: im = im.resize((256, 256), Image.LANCZOS)
        a_ = np.asarray(im, float); m_ = a_.reshape(-1, 3).mean(0)
        lum = a_ @ [0.3, 0.59, 0.11]; rel_ = 1 + (lum / max(lum.mean(), 1) - 1) * 0.75
        b_ = rel_[..., None] * np.array(cl[1], float) * 0.85     # tinte: solo el relieve de luminancia, con el color visto
        Image.fromarray(np.clip(b_, 0, 255).astype(np.uint8)).save(f'{out}/{nombres_t[cl]}.png')
        f.write(f'newmtl {nombres_t[cl]}\nKd 1 1 1\nmap_Kd {nombres_t[cl]}.png\n')
def uv_plano(i, mrep):
    p = P[i] / 1000.0; n = np.abs(nrm[i]); ax = int(np.argmax(n))
    if ax == 1: u, v = p[:, 0], p[:, 2]
    elif ax == 0: u, v = p[:, 2], p[:, 1]
    else: u, v = p[:, 0], p[:, 1]
    return np.stack([u / mrep, v / mrep], 1)
with open(f'{out}/sala.obj', 'w') as f:
    f.write('mtllib sala.mtl\n')
    for v in V / 1000.0: f.write(f'v {v[0]:.4f} {v[1]:.4f} {v[2]:.4f}\n')
    vt = 1
    for k_, (ts_, nom_, ox, oz, wm, hm, Wm, Hm) in enumerate(orto):
        f.write(f'usemtl orto_{k_:02d}\n')
        for i in ts_:
            t = T[i]
            for vv in V[t]: f.write(f'vt {(vv[0]-ox)/Wm:.5f} {1-(vv[2]-oz)/Hm:.5f}\n')
            f.write(f'f {t[0]+1}/{vt} {t[1]+1}/{vt+1} {t[2]+1}/{vt+2}\n'); vt += 3
    for ci in usadas:
        sel = np.nonzero(cam_t == ci)[0]
        f.write(f'usemtl fondo_{ci:02d}\n')
        for i in sel:
            t = T[i]
            for u, v in uv_t[i][1]: f.write(f'vt {u/512:.5f} {1 - v/448:.5f}\n')
            f.write(f'f {t[0]+1}/{vt} {t[1]+1}/{vt+1} {t[2]+1}/{vt+2}\n'); vt += 3
    for cl in tintes:
        sel = [i for i, c_ in mat_t.items() if c_ == cl]
        if not sel: continue
        f.write(f'usemtl {nombres_t[cl]}\n')
        mrep = max(0.6, min(3.0, tintes[cl]['m_rep']))
        for i in sel:
            t = T[i]; uv = uv_plano(i, mrep)
            for u, v in uv: f.write(f'vt {u:.5f} {v:.5f}\n')
            f.write(f'f {t[0]+1}/{vt} {t[1]+1}/{vt+1} {t[2]+1}/{vt+2}\n'); vt += 3
# colisión (malla simple)
Vc, Tc, _ = remake.malla(st, r, 0)
with open(f'{out}/colision.obj', 'w') as f:
    for v in Vc / 1000.0: f.write(f'v {v[0]:.4f} {v[1]:.4f} {v[2]:.4f}\n')
    for t in Tc: f.write(f'f {t[0]+1} {t[1]+1} {t[2]+1}\n')
json.dump(dict(camaras=[dict(ojo=c['ojo'].tolist(), obj=c['obj'].tolist(), fov=c['fov']) for c in cams], usadas=usadas), open(f'{out}/meta.json', 'w'))
