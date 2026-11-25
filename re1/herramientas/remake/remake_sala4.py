"""Sala del REmake sin modelo en UC, con el estilo del vestíbulo: toda la sala en un atlas (luz continua, sin rombos).
Arquitectura (paredes, techos, suelos grandes): color y luz del fondo del REmake suavizado × detalle de una textura
en alta (RE5/UC) de la paleta de la zona, elegida por píxel (zócalo/parte alta por altura). Muebles y detalles:
la proyección del fondo tal cual, con más densidad. Suelos con ortofoto: ortofoto + un poco de detalle.
uso: remake_sala4.py st rNNN salas/rNNN salida"""
import sys, os, json
import numpy as np, cv2
from PIL import Image
from collections import defaultdict
Image.MAX_IMAGE_PIXELS = None
st, r, src, out = int(sys.argv[1]), sys.argv[2], sys.argv[3], sys.argv[4]
os.makedirs(out, exist_ok=True)
PAG = 1024; NPAG = int(os.environ.get('PAGINAS', 4)); DMAX = float(os.environ.get('DMAX', 220))
# ---------------- leer
V = []; VT = []; F = []; FM = []; cur = None
for l in open(f'{src}/sala.obj'):
    if l.startswith('v '): V.append([float(x) for x in l.split()[1:4]])
    elif l.startswith('vt '): VT.append([float(x) for x in l.split()[1:3]])
    elif l.startswith('f '):
        p = [x.split('/') for x in l.split()[1:]]
        for k in range(1, len(p) - 1):
            q = [p[0], p[k], p[k + 1]]; F.append([int(a[0]) - 1 for a in q] + [int(a[1]) - 1 for a in q]); FM.append(cur)
    elif l.startswith('usemtl'): cur = l.split()[1]
V = np.array(V); VT = np.array(VT); F = np.array(F); FM = np.array(FM, dtype=object)
mats = {}; m = None
for l in open(f'{src}/sala.mtl'):
    if l.startswith('newmtl'): m = l.split()[1]
    elif l.startswith('map_Kd'): mats[m] = l.split(None, 1)[1].strip()
P3 = V[F[:, :3]]; nf = np.cross(P3[:, 1] - P3[:, 0], P3[:, 2] - P3[:, 0]); af = np.linalg.norm(nf, axis=1) / 2; nf /= 2 * af[:, None] + 1e-12
cen = P3.mean(1)
cls = np.where(nf[:, 1] > 0.75, 0, np.where(nf[:, 1] < -0.75, 2, np.where(np.abs(nf[:, 1]) < 0.35, 1, 3)))
ok_t = af > 1e-8
# ---------------- grupos planos (soldando vértices por posición) -> arquitectura
_, pid = np.unique(np.round(V * 500).astype(np.int64), axis=0, return_inverse=True); pid = pid.ravel()
arist = defaultdict(list)
for i, f in enumerate(pid[F[:, :3]]):
    for a_, b_ in ((f[0], f[1]), (f[1], f[2]), (f[2], f[0])): arist[(min(a_, b_), max(a_, b_))].append(i)
padre = list(range(len(F)))
def raiz(i):
    while padre[i] != i: padre[i] = padre[padre[i]]; i = padre[i]
    return i
for ts in arist.values():
    for j in ts[1:]:
        a_, b_ = ts[0], j
        if cls[a_] == cls[b_] and cls[a_] != 3 and np.dot(nf[a_], nf[b_]) > 0.97: padre[raiz(a_)] = raiz(b_)
grupo = np.array([raiz(i) for i in range(len(F))])
garea = defaultdict(float)
for g, a in zip(grupo, af): garea[g] += a
arq = np.array([(c == 1 and garea[g] >= 1.5) or (c == 2 and garea[g] >= 1.0) or (c == 0 and garea[g] >= 2.0) for g, c in zip(grupo, cls)])
orto = np.array([str(mm).startswith('suelo') or str(mm).startswith('orto') for mm in FM])
# ---------------- densidad por tipo: muebles y suelos nítidos, techos menos
fac = np.where(cls == 2, 0.45, np.where(arq & (cls == 1), 0.8, np.where(cls == 0, 1.0, 1.5)))
# cerca de donde se camina, más nítido (salas grandes y exteriores)
from scipy.spatial import cKDTree
try:
    _cv = []; _cf = []
    for l in open(f'{src}/colision.obj'):
        if l.startswith('v '): _cv.append([float(x) for x in l.split()[1:4]])
        elif l.startswith('f '): _cf.append([int(x.split('/')[0]) - 1 for x in l.split()[1:4]])
    _cv = np.array(_cv); _cf = np.array(_cf); _T = _cv[_cf]
    _n = np.cross(_T[:, 1] - _T[:, 0], _T[:, 2] - _T[:, 0]); _n /= np.linalg.norm(_n, axis=1, keepdims=True) + 1e-12
    _fl = _T[np.abs(_n[:, 1]) > 0.7]
    _rg = np.random.default_rng(3); _wp = (_rg.dirichlet([1, 1, 1], (len(_fl), 6))[..., None] * _fl[:, None]).sum(2).reshape(-1, 3) + [0, 1.4, 0]
    _d, _ = cKDTree(_wp).query(cen)
    fac = fac * np.clip(3.0 / (_d + 1.0), 0.25, 1.6)
    fac = 1.5 ** np.round(np.log(fac) / np.log(1.5))       # escalones: triángulos vecinos comparten carta
except Exception as ex: print('  sin colisión para densidad:', ex)
eft = (af * fac ** 2)[ok_t].sum()
D = float(np.clip(np.sqrt(NPAG * PAG * PAG * 0.70 / max(eft, 1)), 20, DMAX))
ax = np.abs(nf).argmax(1); sg = np.sign(nf[np.arange(len(nf)), ax])
carta = list(range(len(F)))
def rz(i):
    while carta[i] != i: carta[i] = carta[carta[i]]; i = carta[i]
    return i
for ts in arist.values():
    for j in ts[1:]:
        if ax[ts[0]] == ax[j] and sg[ts[0]] == sg[j] and fac[ts[0]] == fac[j]: carta[rz(ts[0])] = rz(j)
def empaquetar(D):
    def proy2(i):
        a = ax[i]; return P3[i][:, [k for k in range(3) if k != a]] * D * fac[i]
    cs = defaultdict(list)
    for i in np.nonzero(ok_t)[0]: cs[rz(int(i))].append(int(i))
    rects = []
    for ts in cs.values():
        Q = {i: proy2(i) for i in ts}
        celda = np.floor(np.array([Q[i].mean(0) for i in ts]) / 700).astype(int); sub = defaultdict(list)
        for i, cc in zip(ts, map(tuple, celda)): sub[cc].append(i)
        for tt in sub.values():
            pts = np.concatenate([Q[i] for i in tt]); mn = pts.min(0) - 1.5; mx = pts.max(0) + 1.5
            w, h = int(np.ceil(mx[0] - mn[0])) + 1, int(np.ceil(mx[1] - mn[1])) + 1
            esc = 1.0
            if w > PAG - 2 or h > PAG - 2: esc = min((PAG - 2) / w, (PAG - 2) / h); w, h = int(w * esc), int(h * esc)
            rects.append((h, w, tt, mn, esc))
    rects.sort(key=lambda x: (-x[0], -x[1]))
    from numpy.lib.stride_tricks import sliding_window_view
    sky = [np.zeros(PAG, int)]; pos = []
    for h, w, tt, mn, esc in rects:
        for pg, sk in enumerate(sky):
            mx_ = sliding_window_view(sk, w).max(1); cand = np.nonzero(mx_ + h <= PAG)[0]
            if len(cand):
                xb = int(cand[np.argmin(mx_[cand])]); yb = int(mx_[xb]); sk[xb:xb + w] = yb + h; pos.append((pg, xb, yb)); break
        else:
            sk = np.zeros(PAG, int); sk[:w] = h; sky.append(sk); pos.append((len(sky) - 1, 0, 0))
    return rects, pos, len(sky), proy2
for _ in range(15):
    rects, pos, npag, proy2 = empaquetar(D)
    if npag <= NPAG: break
    D *= 0.92
print(f'{r}: atlas {npag} páginas, {D:.0f} px/m (muebles {D*1.5:.0f}, techos {D*0.45:.0f})')
uvat = np.zeros((len(F), 3, 2)); pagt = np.full(len(F), -1)
for (h, w, tt, mn, esc), (pg, x0, y0) in zip(rects, pos):
    for i in tt: uvat[i] = (proy2(i) - mn) * esc + [x0, y0]; pagt[i] = pg
# ---------------- rasterizar
pix_i = []; pix_xy = []; pix_w = []
for i in np.nonzero(pagt >= 0)[0]:
    q = uvat[i]; x0, y0 = np.floor(q.min(0) - 1).astype(int); x1, y1 = np.ceil(q.max(0) + 1).astype(int)
    X, Y = np.meshgrid(np.arange(x0, x1 + 1) + .5, np.arange(y0, y1 + 1) + .5)
    d = (q[1, 1] - q[2, 1]) * (q[0, 0] - q[2, 0]) + (q[2, 0] - q[1, 0]) * (q[0, 1] - q[2, 1])
    if abs(d) < 1e-9: continue
    w0 = ((q[1, 1] - q[2, 1]) * (X - q[2, 0]) + (q[2, 0] - q[1, 0]) * (Y - q[2, 1])) / d
    w1 = ((q[2, 1] - q[0, 1]) * (X - q[2, 0]) + (q[0, 0] - q[2, 0]) * (Y - q[2, 1])) / d
    w2 = 1 - w0 - w1; tol = 1.2 / max(np.sqrt(abs(d)), 1)
    mk = (w0 >= -tol) & (w1 >= -tol) & (w2 >= -tol)
    if not mk.any(): continue
    W = np.clip(np.stack([w0[mk], w1[mk], w2[mk]], 1), 0, None); W /= W.sum(1, keepdims=True)
    pix_i.append(np.full(mk.sum(), i)); pix_xy.append(np.stack([X[mk], Y[mk]], 1).astype(int)); pix_w.append(W)
pix_i = np.concatenate(pix_i); pix_xy = np.concatenate(pix_xy); pix_w = np.concatenate(pix_w)
okp = (pix_xy >= 0).all(1) & (pix_xy < PAG).all(1); pix_i, pix_xy, pix_w = pix_i[okp], pix_xy[okp], pix_w[okp]
pix_p = pagt[pix_i]
Wp = (P3[pix_i] * pix_w[:, :, None]).sum(1); UVp = (VT[F[pix_i, 3:]] * pix_w[:, :, None]).sum(1)
print(f'  {len(pix_i)/1e6:.2f} M píxeles')
# ---------------- color de la proyección (nítido y suave) por píxel
def muestrear(a, uv, rep=True):
    h, w = a.shape[:2]
    u = (uv[:, 0] % 1 if rep else np.clip(uv[:, 0], 0, 1)) * w - .5; v = ((1 - uv[:, 1]) % 1 if rep else np.clip(1 - uv[:, 1], 0, 1)) * h - .5
    x0 = np.floor(u).astype(int); y0 = np.floor(v).astype(int); fx = (u - x0)[:, None]; fy = (v - y0)[:, None]
    x0 %= w; y0 %= h; x1 = (x0 + 1) % w; y1 = (y0 + 1) % h
    return a[y0, x0] * (1 - fx) * (1 - fy) + a[y0, x1] * fx * (1 - fy) + a[y1, x0] * (1 - fx) * fy + a[y1, x1] * fx * fy
nit = np.zeros((len(pix_i), 3), np.float32); low = np.zeros_like(nit); det = np.zeros(len(pix_i), np.float32)
mmp = FM[pix_i]
for mm in set(mmp):
    sel = np.nonzero(mmp == mm)[0]; tn = mats.get(mm)
    if not tn: nit[sel] = low[sel] = 0.3; continue
    a = np.asarray(Image.open(f'{src}/{tn}').convert('RGB'), np.float32) / 255
    s_ = max(1.5, a.shape[1] / 512 * 4)
    lp = cv2.GaussianBlur(a, (0, 0), s_)
    g = a @ np.array([0.3, 0.59, 0.11], np.float32); hp = g - cv2.GaussianBlur(g, (0, 0), 3); dd = np.sqrt(np.maximum(cv2.blur(hp * hp, (9, 9)), 0))
    nit[sel] = muestrear(a, UVp[sel]); low[sel] = muestrear(lp, UVp[sel]); det[sel] = muestrear(dd[..., None], UVp[sel])[:, 0]
# ---------------- color visto por las cámaras del REmake (con z-buffer): nítido = la cámara que mejor lo ve; suave = media
import remake
from PIL import ImageFilter
cams = [c for c in remake.camaras(st, r) if c['img'] is not None]
Vr, Tr, _ = remake.malla(st, r, 1); Vr = np.asarray(Vr, float); Tr = np.asarray(Tr)[:, :3]
ZW, ZH = 256, 224
def zbuffer(c):
    p, z = remake.proyectar(c, Vr); p = p * [ZW / 512, ZH / 448]
    Z = np.full((ZH, ZW), np.inf)
    for tri in Tr:
        q = p[tri]; zz = z[tri]
        if (zz < 50).any(): continue
        x0, x1 = int(max(0, q[:, 0].min())), int(min(ZW - 1, q[:, 0].max() + 1)); y0, y1 = int(max(0, q[:, 1].min())), int(min(ZH - 1, q[:, 1].max() + 1))
        if x0 > x1 or y0 > y1: continue
        X, Y = np.meshgrid(np.arange(x0, x1 + 1) + .5, np.arange(y0, y1 + 1) + .5)
        d = (q[1, 1] - q[2, 1]) * (q[0, 0] - q[2, 0]) + (q[2, 0] - q[1, 0]) * (q[0, 1] - q[2, 1])
        if abs(d) < 1e-9: continue
        w0 = ((q[1, 1] - q[2, 1]) * (X - q[2, 0]) + (q[2, 0] - q[1, 0]) * (Y - q[2, 1])) / d
        w1 = ((q[2, 1] - q[0, 1]) * (X - q[2, 0]) + (q[0, 0] - q[2, 0]) * (Y - q[2, 1])) / d
        w2 = 1 - w0 - w1; mk = (w0 >= 0) & (w1 >= 0) & (w2 >= 0)
        zi = w0 * zz[0] + w1 * zz[1] + w2 * zz[2]
        sub = Z[y0:y1 + 1, x0:x1 + 1]; upd = mk & (zi < sub); sub[upd] = zi[upd]
    return Z
Np = nf[pix_i]; Wm = Wp * 1000
cn = np.zeros((len(pix_i), 3), np.float32); bw = np.zeros(len(pix_i), np.float32)
cs_ = np.zeros((len(pix_i), 3), np.float32); sw = np.zeros(len(pix_i), np.float32)
def bil(img, p):
    x = np.clip(p[:, 0] - .5, 0, img.shape[1] - 1.001); y = np.clip(p[:, 1] - .5, 0, img.shape[0] - 1.001)
    x0 = x.astype(int); y0 = y.astype(int); fx = (x - x0)[:, None]; fy = (y - y0)[:, None]
    return img[y0, x0] * (1 - fx) * (1 - fy) + img[y0, x0 + 1] * fx * (1 - fy) + img[y0 + 1, x0] * (1 - fx) * fy + img[y0 + 1, x0 + 1] * fx * fy
for c in cams:
    img = np.asarray(c['img'].convert('RGB'), np.float32) / 255; imgs = cv2.GaussianBlur(img, (0, 0), 3)
    Z = zbuffer(c)
    for a0 in range(0, len(Wm), 500000):
        sl = slice(a0, a0 + 500000)
        p, z = remake.proyectar(c, Wm[sl])
        ok_ = (z > 100) & (p[:, 0] >= 1) & (p[:, 0] < 510) & (p[:, 1] >= 1) & (p[:, 1] < 446)
        xi = np.clip((p[:, 0] * ZW / 512).astype(int), 0, ZW - 1); yi = np.clip((p[:, 1] * ZH / 448).astype(int), 0, ZH - 1)
        zr = Z[yi, xi]; ok_ &= (z <= zr * 1.03 + 120) | ~np.isfinite(zr)
        vd = np.asarray(c['ojo'], float) - Wm[sl]; dist = np.linalg.norm(vd, axis=1); vd /= dist[:, None] + 1e-9
        co = np.abs((vd * Np[sl]).sum(1)); ok_ &= co > 0.15
        if not ok_.any(): continue
        w_ = np.where(ok_, co * co / (dist / 1000 + 1) ** 2, 0).astype(np.float32)
        csl = cn[sl]; bsl = bw[sl]; mejor = w_ > bsl
        csl[mejor] = bil(img, p[mejor]); bsl[mejor] = w_[mejor]; cn[sl] = csl; bw[sl] = bsl
        cs_[sl] += bil(imgs, p) * w_[:, None]; sw[sl] += w_
visto = (bw > 0) & ~orto[pix_i]
print(f'  píxeles vistos por alguna cámara: {visto.mean()*100:.0f} %')
low_c = cs_ / np.maximum(sw, 1e-9)[:, None]
# lo no visto: color suave de la textura v2 ajustado al nivel medio de lo visto en su grupo
nit = np.where(visto[:, None], cn, nit); low = np.where(visto[:, None], low_c, low)
# ---------------- lámparas: zonas muy brillantes de los fondos que no son arquitectura ni suelo, por encima de 0,9 m
lumf = lambda c: np.asarray(c, np.float32) @ np.array([0.3, 0.59, 0.11], np.float32)
try:
    _lu = lumf(cn); _y0 = Wp[cls[pix_i] == 0, 1].min() if (cls[pix_i] == 0).any() else Wp[:, 1].min()
    _cand = (bw > 0) & (cls[pix_i] != 0) & (_lu > np.where(arq[pix_i], 0.93, 0.85)) & (Wp[:, 1] > _y0 + 0.9)
    fuentes = []
    if _cand.sum() > 20:
        _q = np.round(Wp[_cand] / 0.8).astype(int); _k, _inv, _n = np.unique(_q, axis=0, return_inverse=True, return_counts=True)
        for j in np.argsort(-_n)[:5]:
            if _n[j] >= 20: fuentes.append(Wp[_cand][_inv.ravel() == j].mean(0).round(3).tolist())
    json.dump({'fuentes': fuentes, 'llamas': []}, open(f'{out}/luces.json', 'w'))
    print(f'  lámparas detectadas: {len(fuentes)}')
except Exception as ex: print('  lámparas: error', ex)
if os.environ.get('SOLO_LUCES'): sys.exit(0)
# ---------------- paleta de la zona y elección de material por parte de pared
BIB = json.load(open('/home/claude/re1gc/biblioteca/indice.json'))
def por_nombre(n_):
    for e in BIB:
        if e['origen'].startswith('re5:') and e['origen'][4:].startswith(n_.lower()): return e
    for e in BIB:
        if n_.lower() in e['origen'].lower(): return e
    return None
ZONA = os.environ.get('ZONA') or {1: 'mansion', 2: 'mansion', 3: 'fuera', 4: 'residencia', 5: 'lab'}.get(st, 'mansion')
PAL = {
 'mansion': dict(madera=['r100/r100_wood_a.png'], papel=['r105/r105_kabegami00.png'], liso=['r102/yg_wall01.png'],
                 techo=['r100/st_103tenjou_a.png'], suelo_madera=['r105/r105_yuka_in02.png'], suelo_piedra=['r115/r115_yuka_ishi.png'], alfombra=['r107/st_107jutan_a.png']),
 'residencia': dict(madera=['h_s700_woodpanel'], papel=['y_s407_kabef', 'h_s700_wallpaper'], liso=['y_s407_sotokabe', 'h_s700_wall_white14'],
                    techo=['g-s701-ctenjo'], suelo_madera=['y_407_yukaa', 'h_s700_floor01'], suelo_piedra=['g-s701-cyuka'], alfombra=['g_s700_din_jutang01']),
 'fuera': dict(madera=['g-s701-bsotokabe01'], papel=['g-s701-akabeiwa'], liso=['g-s701-akabetsuchi', 'g-s701-csotokabenaka'],
               techo=['g-s701-atenjo'], suelo_madera=['g-s701-bnakayuka01'], suelo_piedra=['g-s701-cyuka', 'y-s705-yukaaa'], alfombra=['g-s701-ayukakoshitsu']),
 'lab': dict(madera=['r128/r128_wallironB.png'], papel=['r128/r128_wallconcD.png'], liso=['r128/r128_wallconcD.png'],
             techo=['r128/r128_wallconA.png'], suelo_madera=['r128/r128_wallconcC.png'], suelo_piedra=['r128/r128_wallconcC.png'], alfombra=['r128/r128_wallconcC.png']),
}
def elegir(tipo):
    for n_ in PAL[ZONA][tipo]:
        e = por_nombre(n_)
        if e: return e
lumf = lambda c: np.asarray(c, np.float32) @ np.array([0.3, 0.59, 0.11], np.float32)
def clasifica(c, col, dt):
    L = float(lumf(col)) + 1e-6; ch = col / L
    if c == 2: return 'techo'
    if c == 0:
        if ch[0] > 1.35 and ch[2] < 0.8: return 'alfombra'
        return 'suelo_madera' if ch[0] > 1.05 else 'suelo_piedra'
    if ch[0] > 1.15 and ch[2] < 0.85 and L < 0.35: return 'madera'
    return 'papel' if dt > 0.035 else 'liso'
etiqueta = np.full(len(pix_i), -1); elegidos = []
def asignar(sel, e):
    if e is None: return
    if e['png'] not in [x['png'] for x in elegidos]: elegidos.append(e)
    etiqueta[sel] = [x['png'] for x in elegidos].index(e['png'])
ga = pix_i[arq[pix_i]]; garr = grupo[pix_i]
idx_arq = np.nonzero(arq[pix_i] & ~orto[pix_i])[0]
por_g = defaultdict(list)
for k, g in zip(idx_arq, garr[idx_arq]): por_g[g].append(k)
cortes = 0
for g, ks in por_g.items():
    ks = np.array(ks); c = cls[pix_i[ks[0]]]
    if c == 1:
        y = Wp[ks, 1]; y0 = y.min(); y1 = y.max()
        mejor = None
        if y1 - y0 > 1.6:
            for yc in np.arange(y0 + 0.6, min(y0 + 1.6, y1 - 0.4), 0.05):
                a_ = y < yc; b_ = ~a_
                if a_.sum() < 50 or b_.sum() < 50: continue
                dif = np.abs(low[ks[a_]].mean(0) - low[ks[b_]].mean(0)).sum() / (lumf(low[ks].mean(0)) + 0.05)
                if mejor is None or dif > mejor[0]: mejor = (dif, yc)
        if mejor and mejor[0] > 0.35:
            cortes += 1
            for parte in (y < mejor[1], y >= mejor[1]):
                kk = ks[parte]; asignar(kk, elegir(clasifica(c, low[kk].mean(0), float(np.median(det[kk])))))
            continue
    asignar(ks, elegir(clasifica(c, low[ks].mean(0), float(np.median(det[ks])))))
# suelos de ortofoto: un poco de detalle del material de suelo
idx_orto = np.nonzero(orto[pix_i])[0]
if len(idx_orto):
    asignar(idx_orto, elegir(clasifica(0, low[idx_orto].mean(0), 0.02)))
print(f'  materiales en alta: {[os.path.basename(e["origen"]) for e in elegidos]}  (zócalos detectados: {cortes})')
# ---------------- detalle de las texturas en alta en coordenadas del mundo
final = nit.copy()
for k_, e in enumerate(elegidos):
    sel = np.nonzero(etiqueta == k_)[0]
    if not len(sel): continue
    a = np.asarray(Image.open(e['png']).convert('RGB'), np.float32) / 255
    g = a @ np.array([0.3, 0.59, 0.11], np.float32)
    rep = float(e.get('m_rep') or 2.0); rep = float(np.clip(rep, 0.6, 4.0))
    # solo el detalle fino (vetas, grano, poros < ~10 cm): la forma grande (paneles, emblemas) la pone el REmake
    sig = max(1.5, float(os.environ.get('ESCALA_DET', 0.10)) * a.shape[1] / rep / 2)
    gt = np.tile(g, (3, 3)); gl = cv2.GaussianBlur(gt, (0, 0), sig)[g.shape[0]:2 * g.shape[0], g.shape[1]:2 * g.shape[1]]
    ratio = np.clip(g / np.maximum(gl, 0.03), 0.6, 1.6)
    ti = pix_i[sel]; a_ = ax[ti]
    u = np.where(a_ == 1, Wp[sel, 0], np.where(a_ == 0, Wp[sel, 2], Wp[sel, 0])); v = np.where(a_ == 1, Wp[sel, 2], Wp[sel, 1])
    dr = muestrear(ratio[..., None], np.stack([u / rep, v / rep], 1))[:, 0]
    fuerte = np.where(orto[ti], 0.5, float(os.environ.get('FUERZA', 0.8)))[:, None]
    hd = low[sel] * (1 + (dr[:, None] - 1) * fuerte)
    final[sel] = hd + 0.3 * (nit[sel] - low[sel])
final = np.clip(final * float(os.environ.get('BRILLO', 1.0)), 0, 1)
# ---------------- páginas
paginas = []
for pg in range(npag):
    s_ = pix_p == pg
    im = np.zeros((PAG, PAG, 3), np.float32); cnt = np.zeros((PAG, PAG), np.float32)
    np.add.at(im, (pix_xy[s_, 1], pix_xy[s_, 0]), final[s_]); np.add.at(cnt, (pix_xy[s_, 1], pix_xy[s_, 0]), 1)
    llen = cnt > 0; im[llen] /= cnt[llen, None]; m8 = llen.astype(np.uint8)
    for _ in range(3):
        dm = cv2.dilate(m8, np.ones((3, 3), np.uint8)); nuevo = (dm > 0) & (m8 == 0)
        s3 = cv2.blur(im * m8[..., None], (3, 3)); c3 = cv2.blur(m8.astype(np.float32), (3, 3))
        im[nuevo] = s3[nuevo] / np.maximum(c3[nuevo, None], 1e-6); m8 = np.maximum(m8, nuevo.astype(np.uint8))
    nm = f'atlas_{pg}.png'; Image.fromarray((im * 255).astype(np.uint8)).save(f'{out}/{nm}'); paginas.append(nm)
# ---------------- obj
with open(f'{out}/sala.mtl', 'w') as fm:
    for nm in paginas: fm.write(f'newmtl {nm[:-4]}\nKd 1 1 1\nmap_Kd {nm}\n')
with open(f'{out}/sala.obj', 'w') as fo:
    fo.write('mtllib sala.mtl\n')
    for v in V: fo.write(f'v {v[0]:.4f} {v[1]:.4f} {v[2]:.4f}\n')
    for i in range(len(F)):
        if pagt[i] < 0: continue
        for q in uvat[i]: fo.write(f'vt {q[0]/PAG:.6f} {1-q[1]/PAG:.6f}\n')
    # índices de vt en el orden escrito
    orden = np.nonzero(pagt >= 0)[0]; pos_vt = {int(i): 3 * k + 1 for k, i in enumerate(orden)}
    for pg in range(npag):
        fo.write(f'usemtl atlas_{pg}\n')
        for i in np.nonzero(pagt == pg)[0]:
            b = pos_vt[int(i)]; f = F[i]
            fo.write(f'f {f[0]+1}/{b} {f[1]+1}/{b+1} {f[2]+1}/{b+2}\n')
import shutil
shutil.copy(f'{src}/colision.obj', f'{out}/colision.obj')
print(f'ok {out}')
