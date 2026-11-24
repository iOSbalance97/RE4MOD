"""Sala de UC (modelo 3D real) colocada en el sitio de la sala del REmake y con la LUZ del REmake:
cada vértice toma el color de vértice = luz que se ve en los fondos del REmake / color propio de la textura.
uso: uc_sala_remake.py uc_sala.obj alin.json st rNNN salida_dir"""
import sys, os, json, shutil
import numpy as np
from PIL import Image, ImageFilter
from scipy.spatial import cKDTree
sys.path.insert(0, '/home/claude/re1gc/work'); import remake
ucobj, alj, st, r, out = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4], sys.argv[5]
os.makedirs(out, exist_ok=True)
A = json.load(open(alj)); R = np.array(A['R']); s = A['s']; t = np.array(A['t'])
base = os.path.dirname(ucobj)
# ---------------- leer UC
V = []; VT = []; F = []; FM = []; cur = None; mtl = None
for l in open(ucobj):
    if l.startswith('v '): V.append([float(x) for x in l.split()[1:4]])
    elif l.startswith('vt '): VT.append([float(x) for x in l.split()[1:3]])
    elif l.startswith('f '):
        p = [x.split('/') for x in l.split()[1:4]]; F.append([int(a[0]) - 1 for a in p] + [int(a[1]) - 1 for a in p]); FM.append(cur)
    elif l.startswith('usemtl'): cur = l.split()[1]
    elif l.startswith('mtllib'): mtl = l.split()[1]
V = np.array(V) @ R.T * s + t; VT = np.array(VT); F = np.array(F); FM = np.array(FM, dtype=object)
mats = {}; m = None
for l in open(os.path.join(base, mtl)):
    if l.startswith('newmtl'): m = l.split()[1]; mats[m] = None
    elif l.startswith('map_Kd'): mats[m] = l.split(None, 1)[1].strip()
# ---------------- aligerar la geometría de UC (piezas muy densas: tallas, balaustres) para que quepa en la memoria de sala
if float(os.environ.get('DECIMAR', 0)) > 0:
    sys.path.insert(0, '/home/claude/tools'); import decimate
    from re4room import weld
    RAT = float(os.environ['DECIMAR']); nV = []; nT = []; nF = []; nM = []; tot0 = len(F)
    for mm in dict.fromkeys(FM):
        sel = FM == mm
        P_, UV_, tr_ = weld(V, VT, F[sel])
        ar_ = np.linalg.norm(np.cross(P_[tr_[:, 1]] - P_[tr_[:, 0]], P_[tr_[:, 2]] - P_[tr_[:, 0]]), axis=1).sum() / 2
        if len(tr_) > 400 and len(tr_) / max(ar_, 1e-6) > 25:
            try: P_, UV_, tr_ = decimate.decimate(P_, UV_, tr_, RAT)
            except Exception as ex: print('  decimado falló en', mm, ex)
        b0 = sum(len(x) for x in nV)
        nV.append(P_); nT.append(UV_); nF.append(np.concatenate([tr_ + b0, tr_ + b0], 1)); nM += [mm] * len(tr_)
    V = np.concatenate(nV); VT = np.concatenate(nT); F = np.concatenate(nF); FM = np.array(nM, dtype=object)
    print(f'decimado: {tot0} -> {len(F)} triángulos')
# ---------------- huecos: suelo y paredes de la colisión del REmake que UC no tiene (UC solo modela lo que ve su cámara)
def _cargar_col(p):
    Vc = []; Fc = []
    for l in open(p):
        if l.startswith('v '): Vc.append([float(x) for x in l.split()[1:4]])
        elif l.startswith('f '): Fc.append([int(x.split('/')[0]) - 1 for x in l.split()[1:4]])
    return np.array(Vc), np.array(Fc)
Vc, Fc = _cargar_col(f'/home/claude/re1gc/salas/{r}/colision.obj')
Tc = Vc[Fc]; nc = np.cross(Tc[:, 1] - Tc[:, 0], Tc[:, 2] - Tc[:, 0]); ac = np.linalg.norm(nc, axis=1); nc /= ac[:, None] + 1e-12
Tu = V[F[:, :3]]; nu = np.cross(Tu[:, 1] - Tu[:, 0], Tu[:, 2] - Tu[:, 0]); au = np.linalg.norm(nu, axis=1) / 2; nu /= 2 * au[:, None] + 1e-12
UVu = VT[F[:, 3:]]
d1 = UVu[:, 1] - UVu[:, 0]; d2 = UVu[:, 2] - UVu[:, 0]; uva = np.abs(d1[:, 0] * d2[:, 1] - d1[:, 1] * d2[:, 0]) / 2
# metros por repetición de cada material (para dar UV a lo nuevo)
mpr = {}
for mm in set(FM):
    s_ = (FM == mm) & (uva > 1e-9)
    if s_.any(): mpr[mm] = float(np.clip(np.sqrt(au[s_].sum() / uva[s_].sum()), 0.2, 6))
CEL = 0.2
# alturas de suelo de UC por celda
alt = {}
hor = np.abs(nu[:, 1]) > 0.7
for tri, mm in zip(Tu[hor], FM[hor]):
    x0, z0 = tri[:, [0, 2]].min(0); x1, z1 = tri[:, [0, 2]].max(0)
    for i in range(int(np.floor(x0 / CEL)), int(np.floor(x1 / CEL)) + 1):
        for j in range(int(np.floor(z0 / CEL)), int(np.floor(z1 / CEL)) + 1):
            x, z = (i + .5) * CEL, (j + .5) * CEL
            a, b, c = tri; dd = (b[2] - c[2]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[2] - c[2])
            if abs(dd) < 1e-12: continue
            w0 = ((b[2] - c[2]) * (x - c[0]) + (c[0] - b[0]) * (z - c[2])) / dd; w1 = ((c[2] - a[2]) * (x - c[0]) + (a[0] - c[0]) * (z - c[2])) / dd
            if w0 < -0.15 or w1 < -0.15 or 1 - w0 - w1 < -0.15: continue          # algo de margen: no rellenar rendijas de juntas
            alt.setdefault((i, j), []).append((w0 * a[1] + w1 * b[1] + (1 - w0 - w1) * c[1], mm))
nuevos_v = []; nuevos_t = []; nuevas_f = []; nuevas_m = []
def quad(pts, mm, ejes):
    m_ = mpr.get(mm, 1.5); b0 = len(V) + len(nuevos_v); bt = len(VT) + len(nuevos_t)
    for p in pts:
        nuevos_v.append(p); nuevos_t.append([p[ejes[0]] / m_, p[ejes[1]] / m_])
    nuevas_f.append([b0, b0 + 1, b0 + 2, bt, bt + 1, bt + 2]); nuevas_m.append(mm)
    nuevas_f.append([b0, b0 + 2, b0 + 3, bt, bt + 2, bt + 3]); nuevas_m.append(mm)
# suelo
huecos = {}
for tri, n_ in zip(Tc, nc):
    if n_[1] < 0.97: continue                    # rampas de escalera de la colisión: no (UC tiene los peldaños)
    x0, z0 = tri[:, [0, 2]].min(0); x1, z1 = tri[:, [0, 2]].max(0)
    for i in range(int(np.floor(x0 / CEL)), int(np.floor(x1 / CEL)) + 1):
        for j in range(int(np.floor(z0 / CEL)), int(np.floor(z1 / CEL)) + 1):
            x, z = (i + .5) * CEL, (j + .5) * CEL
            a, b, c = tri; dd = (b[2] - c[2]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[2] - c[2])
            if abs(dd) < 1e-12: continue
            w0 = ((b[2] - c[2]) * (x - c[0]) + (c[0] - b[0]) * (z - c[2])) / dd; w1 = ((c[2] - a[2]) * (x - c[0]) + (a[0] - c[0]) * (z - c[2])) / dd
            if w0 < 0 or w1 < 0 or 1 - w0 - w1 < 0: continue
            y = w0 * a[1] + w1 * b[1] + (1 - w0 - w1) * c[1]
            hs = alt.get((i, j), [])
            if any(-0.8 < h - y < 0.35 for h, _ in hs): continue
            # material: el suelo de UC más cercano a esa altura
            huecos[(i, j, round(y, 2))] = y
if huecos:
    cand = [(k, v) for k, v in alt.items()]
    pts_ = np.array([[(k[0] + .5) * CEL, h, (k[1] + .5) * CEL] for k, lst in cand for h, _ in lst])
    mats_ = [mm for k, lst in cand for h, mm in lst]
    tr_ = cKDTree(pts_ * [1, 3, 1])
    for (i, j, _), y in huecos.items():
        _, q = tr_.query([(i + .5) * CEL, y * 3, (j + .5) * CEL]); mm = mats_[q]
        quad([[i * CEL, y + 0.01, j * CEL], [i * CEL, y + 0.01, (j + 1) * CEL], [(i + 1) * CEL, y + 0.01, (j + 1) * CEL], [(i + 1) * CEL, y + 0.01, j * CEL]], mm, (0, 2))
nsuelo = len(nuevas_f) // 2
# paredes: triángulos de pared de la colisión sin superficie de UC cerca
vert = np.abs(nu[:, 1]) < 0.4
if vert.any():
    S = []; SM = []
    for tri, mm, a_ in zip(Tu[vert], FM[vert], au[vert]):
        n_ = max(1, int(a_ / 0.04)); w = np.random.default_rng(0).dirichlet([1, 1, 1], min(n_, 200))
        S.append(w @ tri); SM += [mm] * len(w)
    S = np.concatenate(S); trw = cKDTree(S)
    for tri, n_, a2 in zip(Tc, nc, ac):
        if abs(n_[1]) > 0.3 or a2 / 2 < 0.05: continue
        w = np.random.default_rng(1).dirichlet([1, 1, 1], max(4, int(a2 / 2 / 0.06)))
        P_ = w @ tri; d_, q_ = trw.query(P_)
        falta = d_ > 0.3
        if falta.mean() < 0.6: continue
        # pared que separa dos zonas con suelo (bloqueo invisible del REmake): no se dibuja
        c_ = tri.mean(0); lados = 0
        for sg in (1, -1):
            q = c_ + sg * 0.6 * np.array([n_[0], 0, n_[2]]) / (np.hypot(n_[0], n_[2]) + 1e-9)
            i_, j_ = int(np.floor(q[0] / CEL)), int(np.floor(q[2] / CEL))
            ys_ = [h for h, _ in alt.get((i_, j_), [])] + [y for (a_, b_, _), y in huecos.items() if (a_, b_) == (i_, j_)]
            if ys_: lados += 1
        if lados == 2: continue          # hay suelo a ambos lados (aunque sea más abajo): barrera invisible, no pared
        mm = SM[int(q_[np.argmin(d_)])]
        ejes = (2, 1) if abs(n_[0]) > abs(n_[2]) else (0, 1)
        b0 = len(V) + len(nuevos_v); bt = len(VT) + len(nuevos_t); m_ = mpr.get(mm, 1.5)
        for p in tri: nuevos_v.append(p); nuevos_t.append([p[ejes[0]] / m_, p[ejes[1]] / m_])
        nuevas_f.append([b0, b0 + 1, b0 + 2, bt, bt + 1, bt + 2]); nuevas_m.append(mm)
print(f'huecos rellenados: {nsuelo} celdas de suelo, {len(nuevas_f) - 2 * nsuelo} triángulos de pared')
if nuevas_f:
    V = np.concatenate([V, np.array(nuevos_v)]); VT = np.concatenate([VT, np.array(nuevos_t)])
    F = np.concatenate([F, np.array(nuevas_f)]); FM = np.concatenate([FM, np.array(nuevas_m, dtype=object)])

# ---------------- piezas que UC no modeló (columnas, tramos de barandilla, bordes de suelo): se toman de la malla
# detallada del REmake donde no hay nada de UC cerca, con la textura de UC más cercana
Vd_, Td_, _ = remake.malla(st, r, 1); Vd_ = np.asarray(Vd_, float) / 1000; Td_ = np.asarray(Td_)[:, :3]
Tu2 = V[F[:, :3]]; au2 = np.linalg.norm(np.cross(Tu2[:, 1] - Tu2[:, 0], Tu2[:, 2] - Tu2[:, 0]), axis=1) / 2
rng = np.random.default_rng(3); S = []; SM = []; SN = []
nu2 = np.cross(Tu2[:, 1] - Tu2[:, 0], Tu2[:, 2] - Tu2[:, 0]); nu2 /= np.linalg.norm(nu2, axis=1, keepdims=True) + 1e-12
for tri, mm, a_, nn in zip(Tu2, FM, au2, nu2):
    k_ = int(min(60, max(1, a_ / 0.01)))
    w = rng.dirichlet([1, 1, 1], k_); S.append(w @ tri); SM += [mm] * k_; SN.append(np.repeat(nn[None], k_, 0))
S = np.concatenate(S); SN = np.concatenate(SN); trS = cKDTree(S)
DLIM = float(os.environ.get('DFALTA', 0.22))
nv0 = len(V); nvt0 = len(VT); add_v = []; add_t = []; add_f = []; add_m = []
_flw = Tc[nc[:, 1] > 0.7]; _rgw = np.random.default_rng(9)
_wpw = (_rgw.dirichlet([1, 1, 1], (len(_flw), 6))[..., None] * _flw[:, None]).sum(2).reshape(-1, 3) + [0, 1.0, 0]
_trw = cKDTree(_wpw)
def _dwalk(p): return _trw.query(p)[0]
# subdividir la malla del REmake para que el test sea fino
pila = [tuple(t_) for t_ in Td_]; Vd_l = list(Vd_); trisd = []
while pila:
    a, b, c = pila.pop(); L = [np.linalg.norm(Vd_l[a] - Vd_l[b]), np.linalg.norm(Vd_l[b] - Vd_l[c]), np.linalg.norm(Vd_l[c] - Vd_l[a])]
    k = int(np.argmax(L))
    if L[k] <= 0.5: trisd.append((a, b, c)); continue
    x, y = ((a, b), (b, c), (c, a))[k]; Vd_l.append((Vd_l[x] + Vd_l[y]) / 2); m_ = len(Vd_l) - 1
    o = ({a, b, c} - {x, y}).pop()
    pila += [(x, m_, o), (m_, y, o)]
Vd_ = np.array(Vd_l); trisd = np.array(trisd)
for tri_i in trisd:
    tri = Vd_[tri_i]; nn = np.cross(tri[1] - tri[0], tri[2] - tri[0]); ar = np.linalg.norm(nn) / 2
    if ar < 1e-4: continue
    nn /= 2 * ar
    if nn[1] < -0.5: continue                      # techos y caras de abajo: no
    w = np.array([[1/3, 1/3, 1/3], [.7, .15, .15], [.15, .7, .15], [.15, .15, .7], [.45, .45, .1], [.1, .45, .45]])
    d_, q_ = trS.query(w @ tri)
    if (d_ > DLIM).mean() < 0.84: continue
    # que no sea una pared tapando una abertura que UC sí tiene abierta (puertas, arcos): solo si UC tiene algo a <1 m
    if d_.min() > 1.2: continue
    if _dwalk(tri.mean(0)) > 4.0: continue        # solo piezas cerca de donde se camina
    mm = SM[int(q_[np.argmin(d_)])]
    ejes = (0, 2) if abs(nn[1]) > 0.7 else ((2, 1) if abs(nn[0]) > abs(nn[2]) else (0, 1))
    m_ = mpr.get(mm, 1.5)
    b0 = nv0 + len(add_v); bt = nvt0 + len(add_t)
    for p in tri: add_v.append(p); add_t.append([p[ejes[0]] / m_, p[ejes[1]] / m_])
    add_f.append([b0, b0 + 1, b0 + 2, bt, bt + 1, bt + 2]); add_m.append(mm)
print(f'piezas del REmake añadidas donde UC no tiene nada: {len(add_f)} triángulos')
if add_f:
    V = np.concatenate([V, np.array(add_v)]); VT = np.concatenate([VT, np.array(add_t)])
    F = np.concatenate([F, np.array(add_f)]); FM = np.concatenate([FM, np.array(add_m, dtype=object)])

# ---------------- subdividir triángulos grandes (la luz se guarda por vértice)
LMAX = float(os.environ.get('LMAX', 0.9))
Vl = list(V); Tl = list(VT); nuevasF = []; nuevasM = []
cache = {}
def mid(a, b, ta, tb):
    k = (min(a, b), max(a, b), min(ta, tb), max(ta, tb))
    if k not in cache:
        Vl.append((Vl[a] + Vl[b]) / 2); Tl.append((Tl[ta] + Tl[tb]) / 2); cache[k] = (len(Vl) - 1, len(Tl) - 1)
    return cache[k]
pila = [(list(f), mm) for f, mm in zip(F, FM)]
while pila:
    f, mm = pila.pop()
    a, b, c, ta, tb, tc = f
    L = [np.linalg.norm(Vl[a] - Vl[b]), np.linalg.norm(Vl[b] - Vl[c]), np.linalg.norm(Vl[c] - Vl[a])]
    k = int(np.argmax(L))
    if L[k] <= LMAX or len(Vl) > 400000: nuevasF.append(f); nuevasM.append(mm); continue
    if k == 0:   m_, tm = mid(a, b, ta, tb); pila += [([a, m_, c, ta, tm, tc], mm), ([m_, b, c, tm, tb, tc], mm)]
    elif k == 1: m_, tm = mid(b, c, tb, tc); pila += [([a, b, m_, ta, tb, tm], mm), ([a, m_, c, ta, tm, tc], mm)]
    else:        m_, tm = mid(c, a, tc, ta); pila += [([a, b, m_, ta, tb, tm], mm), ([m_, b, c, tm, tb, tc], mm)]
V = np.array(Vl); VT = np.array(Tl); F = np.array(nuevasF); FM = np.array(nuevasM, dtype=object)
print(f'UC: {len(V)} vértices, {len(F)} triángulos tras subdividir')
# normales por vértice
P3 = V[F[:, :3]]; nf = np.cross(P3[:, 1] - P3[:, 0], P3[:, 2] - P3[:, 0])
NV = np.zeros_like(V)
for j in range(3): np.add.at(NV, F[:, j], nf)
NV /= np.linalg.norm(NV, axis=1, keepdims=True) + 1e-12
# ---------------- albedo de textura en cada vértice (textura muy suavizada)
tex_suave = {}
def suave(tn):
    if tn not in tex_suave:
        try: im = Image.open(os.path.join(base, tn)).convert('RGB').resize((16, 16), Image.BOX)
        except Exception: im = Image.new('RGB', (16, 16), (128, 128, 128))
        tex_suave[tn] = np.asarray(im, float) / 255
    return tex_suave[tn]
alb = np.full((len(V), 3), np.nan)
for fi, (f, mm) in enumerate(zip(F, FM)):
    tn = mats.get(mm)
    if not tn: continue
    ts = suave(tn)
    for j in range(3):
        if np.isnan(alb[f[j], 0]):
            u, v = VT[f[3 + j]]; alb[f[j]] = ts[int((1 - v) % 1 * 16) % 16, int(u % 1 * 16) % 16]
alb = np.where(np.isnan(alb), 0.5, alb); alb = np.maximum(alb, 0.04)
# ---------------- luz de los fondos del REmake
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
Pm = V * 1000; NVm = NV
suma = np.zeros((len(V), 3)); peso = np.zeros(len(V)); ZB = []
for ci, c in enumerate(cams):
    img = np.asarray(Image.eval(c['img'], lambda x: int(255 * (x / 255) ** 0.85)).filter(ImageFilter.GaussianBlur(5)), float) / 255
    Z = zbuffer(c); ZB.append(Z)
    p, z = remake.proyectar(c, Pm)
    ok = (z > 100) & (p[:, 0] >= 2) & (p[:, 0] < 509) & (p[:, 1] >= 2) & (p[:, 1] < 445)
    xi = np.clip((p[:, 0] * ZW / 512).astype(int), 0, ZW - 1); yi = np.clip((p[:, 1] * ZH / 448).astype(int), 0, ZH - 1)
    zr = Z[yi, xi]
    ok &= (z <= zr * 1.04 + 150) | ~np.isfinite(zr)
    vdir = np.asarray(c['ojo'], float) - Pm; dist = np.linalg.norm(vdir, axis=1); vdir /= dist[:, None] + 1e-9
    cosang = np.abs((vdir * NVm).sum(1))           # la cara puede estar mal orientada en UC: valor absoluto
    ok &= cosang > 0.15
    w = np.where(ok, cosang / (dist / 1000 + 1.0) ** 2, 0)
    col = img[np.clip(p[:, 1].astype(int), 0, 447), np.clip(p[:, 0].astype(int), 0, 511)]
    suma += col * w[:, None]; peso += w
    print(f'  cámara {ci:2d}: {ok.sum()} vértices vistos', flush=True)
visto = peso > 0
bg = np.zeros((len(V), 3)); bg[visto] = suma[visto] / peso[visto, None]
lum = lambda x: x @ [0.3, 0.59, 0.11]
k = np.zeros(len(V)); k[visto] = lum(bg[visto]) / np.maximum(lum(alb[visto]), 0.05)
tinte = np.ones((len(V), 3))
tinte[visto] = (bg[visto] / np.maximum(lum(bg[visto])[:, None], 0.02)) / (alb[visto] / np.maximum(lum(alb[visto])[:, None], 0.02))
tinte = 1 + (np.clip(tinte, 0.5, 1.6) - 1) * 0.4
colv = np.clip(k[:, None] * tinte, 0.02, 1.0)
# lo que no ve ninguna cámara: de los vecinos vistos con normal parecida
if (~visto).any() and visto.any():
    tr = cKDTree(V[visto]); iv = np.nonzero(visto)[0]
    d, j = tr.query(V[~visto], k=16)
    nv = []
    for row, jj, dd in zip(np.nonzero(~visto)[0], j, d):
        cand = [iv[q] for q in jj if np.dot(NV[row], NV[iv[q]]) > 0.5] or [iv[q] for q in jj]
        val = colv[cand].mean(0) * (0.85 if dd[0] > 1.5 else 1.0)
        nv.append(val)
    colv[~visto] = np.array(nv)
# suavizado de la luz (quita el ruido de los fondos y el moteado por triángulos)
_tr = cKDTree(V); _d, _j = _tr.query(V, k=24, distance_upper_bound=1.2)
_lum = colv.copy(); _sv = np.zeros_like(colv)
for _i in range(len(V)):
    jj = _j[_i][np.isfinite(_d[_i])]; dd = _d[_i][np.isfinite(_d[_i])]
    w = np.exp(-(dd / 0.6) ** 2) * np.clip((NV[jj] @ NV[_i]) , 0, 1) ** 2
    _sv[_i] = (colv[jj] * w[:, None]).sum(0) / max(w.sum(), 1e-6)
colv = _sv
print(f'vértices vistos {visto.mean()*100:.0f} %, luz media {colv.mean():.2f}')
# ---------------- luz por triángulo (misma luz por píxel que el atlas, pero promediada en cada triángulo):
# así se conservan las texturas de UC a su resolución y la luz sale de los fondos del REmake
import cv2
texa = {}
def tex_arr(tn):
    if tn not in texa:
        try: im = Image.open(os.path.join(base, tn)).convert('RGBA')
        except Exception: im = Image.new('RGBA', (8, 8), (128, 128, 128, 255))
        a = np.asarray(im, np.float32) / 255
        k = max(1, min(a.shape[:2]) // 12)
        from scipy.ndimage import uniform_filter as _uf; lp = _uf(a[..., :3], (k * 2 + 1, k * 2 + 1, 1), mode='wrap')
        texa[tn] = (a, lp, float((a[..., 3] < 0.5).mean()))
    return texa[tn]
P3 = V[F[:, :3]]
Wbar = np.array([[1/3, 1/3, 1/3], [.6, .2, .2], [.2, .6, .2], [.2, .2, .6], [.45, .45, .1], [.1, .45, .45], [.45, .1, .45]], np.float32)
NS = len(Wbar)
pix_i = np.repeat(np.arange(len(F)), NS); pix_w = np.tile(Wbar, (len(F), 1))
Wp = (P3[pix_i] * pix_w[:, :, None]).sum(1)
Np = (NV[F[pix_i, :3]] * pix_w[:, :, None]).sum(1); Np /= np.linalg.norm(Np, axis=1, keepdims=True) + 1e-12
UVp = (VT[F[pix_i, 3:]] * pix_w[:, :, None]).sum(1)
Lv = (colv[F[pix_i, :3]] * pix_w[:, :, None]).sum(1)
albl = np.zeros((len(pix_i), 3), np.float32); mmp = FM[pix_i]
for mm in set(mmp):
    sel = np.nonzero(mmp == mm)[0]; tn = mats.get(mm)
    if not tn: albl[sel] = 0.5; continue
    a, lp, _ = tex_arr(tn); h, w = a.shape[:2]
    xs = ((UVp[sel, 0] % 1) * w).astype(int) % w; ys = (((1 - UVp[sel, 1]) % 1) * h).astype(int) % h
    albl[sel] = lp[ys, xs]
# ---------------- luz de los fondos del REmake por píxel
Wm = Wp * 1000; suma = np.zeros((len(pix_i), 3), np.float32); peso = np.zeros(len(pix_i), np.float32)
for ci, c in enumerate(cams):
    img = cv2.GaussianBlur(np.asarray(Image.eval(c['img'], lambda x: int(255 * (x / 255) ** 0.85)), np.float32) / 255, (0, 0), 1.2)
    Z = ZB[ci]
    for a0 in range(0, len(Wm), 600000):
        sl = slice(a0, a0 + 600000)
        p, z = remake.proyectar(c, Wm[sl])
        ok_ = (z > 100) & (p[:, 0] >= 1) & (p[:, 0] < 510) & (p[:, 1] >= 1) & (p[:, 1] < 446)
        xi = np.clip((p[:, 0] * ZW / 512).astype(int), 0, ZW - 1); yi = np.clip((p[:, 1] * ZH / 448).astype(int), 0, ZH - 1)
        zr = Z[yi, xi]; ok_ &= (z <= zr * 1.03 + 120) | ~np.isfinite(zr)
        vd = np.asarray(c['ojo'], float) - Wm[sl]; dist = np.linalg.norm(vd, axis=1); vd /= dist[:, None] + 1e-9
        cs = np.abs((vd * Np[sl]).sum(1)); ok_ &= cs > 0.2
        w_ = np.where(ok_, cs * cs / (dist / 1000 + 1) ** 2, 0).astype(np.float32)
        if not ok_.any(): continue
        col = img[np.clip(p[:, 1].astype(int), 0, 447), np.clip(p[:, 0].astype(int), 0, 511)]
        suma[sl] += col * w_[:, None]; peso[sl] += w_
vis = peso > 1e-4
bgc = np.zeros_like(suma); bgc[vis] = suma[vis] / peso[vis, None]
Lb = bgc / np.maximum(albl, 0.05)
lumf = lambda x: x @ np.array([0.3, 0.59, 0.11], np.float32)
# tinte suave: mitad de la cromaticidad de la luz
Lb = lumf(Lb)[:, None] * (1 + (Lb / np.maximum(lumf(Lb)[:, None], 1e-3) - 1) * 0.5)
alfa = np.clip(peso / (np.percentile(peso[vis], 30) + 1e-6), 0, 1)[:, None] if vis.any() else np.zeros((len(peso), 1))
L = np.where(vis[:, None], alfa * np.clip(Lb, 0.02, 1.6) + (1 - alfa) * Lv, Lv)
Lt = L.reshape(len(F), NS, 3).mean(1)
# suavizado entre triángulos vecinos (sombras unidas): media ponderada por distancia en 0,8 m con normal parecida
_cen = P3.mean(1); _nf = np.cross(P3[:, 1] - P3[:, 0], P3[:, 2] - P3[:, 0]); _nf /= np.linalg.norm(_nf, axis=1, keepdims=True) + 1e-12
_trc = cKDTree(_cen); _d, _j = _trc.query(_cen, k=12, distance_upper_bound=0.8)
_Ls = np.zeros_like(Lt)
for _i in range(len(F)):
    m_ = np.isfinite(_d[_i]); jj = _j[_i][m_]; w_ = np.exp(-(_d[_i][m_] / 0.45) ** 2) * np.clip(_nf[jj] @ _nf[_i], 0, 1) ** 2 + 1e-6
    _Ls[_i] = (Lt[jj] * w_[:, None]).sum(0) / w_.sum()
Lt = _Ls
print(f'  luz por triángulo: vistos {vis.reshape(len(F), NS).mean()*100:.0f} %')
# el horneado por niveles usa esta luz en vez de la de los vértices
colv_tri = Lt
# ---------------- luz horneada continua: cada superficie tiene su propio trozo de textura (atlas) con
# textura de UC × luz del REmake por píxel (las sombras de los objetos salen de los fondos del REmake)
import cv2
PAG = 1024; NPAG = int(os.environ.get('PAGINAS', 4))
texa = {}
def tex_arr(tn):
    if tn not in texa:
        try: im = Image.open(os.path.join(base, tn)).convert('RGBA')
        except Exception: im = Image.new('RGBA', (8, 8), (128, 128, 128, 255))
        a = np.asarray(im, np.float32) / 255
        k = max(1, min(a.shape[:2]) // 12)
        from scipy.ndimage import uniform_filter as _uf; lp = _uf(a[..., :3], (k * 2 + 1, k * 2 + 1, 1), mode='wrap')
        texa[tn] = (a, lp, float((a[..., 3] < 0.5).mean()))
    return texa[tn]
_ca = {mm: bool(mats.get(mm)) and tex_arr(mats[mm])[2] > 0.03 for mm in set(FM)}; con_alfa = np.array([_ca[mm] for mm in FM])
P3 = V[F[:, :3]]; nf = np.cross(P3[:, 1] - P3[:, 0], P3[:, 2] - P3[:, 0]); af = np.linalg.norm(nf, axis=1) / 2; nf /= 2 * af[:, None] + 1e-12
_flz = Tc[nc[:, 1] > 0.7]; _rgz = np.random.default_rng(11)
_wz = (_rgz.dirichlet([1, 1, 1], (len(_flz), 8))[..., None] * _flz[:, None]).sum(2).reshape(-1, 3)
_dz, _ = cKDTree(_wz).query(P3.mean(1))
LEJOS = float(os.environ.get('LEJOS', 2.6))
lejano = _dz > LEJOS
enat = ~con_alfa & (af > 1e-7) & lejano
print(f'  atlas (lejano, sombra continua): {lejano.mean()*100:.0f} % de triángulos; cerca y nítido: {(~lejano).mean()*100:.0f} %')
D = float(np.clip(np.sqrt(NPAG * PAG * PAG * 0.72 / max(af[enat].sum(), 1)), 12, 90))
print(f'atlas: {af[enat].sum():.0f} m² a {D:.0f} px/m en {NPAG} páginas')
ax = np.abs(nf).argmax(1); sg = np.sign(nf[np.arange(len(nf)), ax])
# cartas: triángulos vecinos con la misma cara dominante
from collections import defaultdict
_, pid = np.unique(np.round(V * 500).astype(np.int64), axis=0, return_inverse=True); pid = pid.ravel()
ar_ = defaultdict(list)
for i in np.nonzero(enat)[0]:
    f = pid[F[i, :3]]
    for a_, b_ in ((f[0], f[1]), (f[1], f[2]), (f[2], f[0])): ar_[(min(a_, b_), max(a_, b_))].append(i)
padre = {int(i): int(i) for i in np.nonzero(enat)[0]}
def rz(i):
    while padre[i] != i: padre[i] = padre[padre[i]]; i = padre[i]
    return i
for ts in ar_.values():
    for j in ts[1:]:
        if ax[ts[0]] == ax[j] and sg[ts[0]] == sg[j]: padre[rz(int(ts[0]))] = rz(int(j))
_flr = Tc[nc[:, 1] > 0.7]; _rg = np.random.default_rng(7)
_wp = (_rg.dirichlet([1, 1, 1], (len(_flr), 8))[..., None] * _flr[:, None]).sum(2).reshape(-1, 3) + [0, 1.4, 0]
_d_imp, _ = cKDTree(_wp).query(P3.mean(1))
fac_t = np.clip(2.5 / (_d_imp + 0.8), 0.3, 1.8) * np.where(nf[:, 1] > 0.7, 1.7, np.where(nf[:, 1] < -0.7, 0.4, 1.0))
def empaquetar(D):
    def proy2(i):
        p = P3[i]; a = ax[i]
        q = p[:, [k for k in range(3) if k != a]]
        return q * D
    cartas = defaultdict(list)
    for i in padre: cartas[rz(i)].append(i)
    rects = []          # (alto, ancho, tris, min2d)
    for ts in cartas.values():
        fch = float(np.median(fac_t[ts]))
        Q = {i: proy2(i) * fch for i in ts}
        c2 = np.array([Q[i].mean(0) for i in ts])
        celda = np.floor(c2 / 900).astype(int)
        sub = defaultdict(list)
        for i, cc in zip(ts, map(tuple, celda)): sub[cc].append(i)
        for tt in sub.values():
            pts = np.concatenate([Q[i] for i in tt]); mn = pts.min(0) - 1.5; mx = pts.max(0) + 1.5
            w, h = int(np.ceil(mx[0] - mn[0])) + 1, int(np.ceil(mx[1] - mn[1])) + 1
            if w > PAG or h > PAG:
                # triángulo enorme: escalar esa carta
                esc = min((PAG - 2) / w, (PAG - 2) / h); rects.append((int(h * esc), int(w * esc), tt, mn, (esc, fch))); continue
            rects.append((h, w, tt, mn, (1.0, fch)))
    rects.sort(key=lambda x: (-x[0], -x[1]))
    from numpy.lib.stride_tricks import sliding_window_view
    sky = [np.zeros(PAG, int)]; pos = []
    for h, w, tt, mn, esc in rects:
        hecho = False
        for pg, sk in enumerate(sky):
            if w > PAG: break
            mx_ = sliding_window_view(sk, w).max(1)
            cand = np.nonzero(mx_ + h <= PAG)[0]
            if len(cand):
                xb = int(cand[np.argmin(mx_[cand])]); yb = int(mx_[xb]); sk[xb:xb + w] = yb + h
                pos.append((pg, xb, yb)); hecho = True; break
        if not hecho:
            sk = np.zeros(PAG, int); sk[:w] = h; sky.append(sk); pos.append((len(sky) - 1, 0, 0))
    pag = len(sky) - 1

    return rects, pos, pag, proy2
D0 = D
for _int in range(12):
    rects, pos, pag, proy2 = empaquetar(D)
    if pag + 1 <= NPAG: break
    D *= 0.9
print(f'  densidad final {D:.0f} px/m')
npag = pag + 1
print(f'  {len(rects)} cartas en {npag} páginas')
if npag > NPAG + 1: print('  AVISO: más páginas de las previstas')
uvat = np.zeros((len(F), 3, 2)); pagt = np.full(len(F), -1)
for (h, w, tt, mn, esc), (pg, x0, y0) in zip(rects, pos):
    for i in tt:
        q = (proy2(i) * esc[1] - mn) * esc[0] + [x0, y0]
        uvat[i] = q; pagt[i] = pg
# ---------------- rasterizar: por cada píxel, triángulo y baricéntricas
pix_i = []; pix_xy = []; pix_w = []; pix_p = []
for i in np.nonzero(pagt >= 0)[0]:
    q = uvat[i]; x0, y0 = np.floor(q.min(0) - 1).astype(int); x1, y1 = np.ceil(q.max(0) + 1).astype(int)
    X, Y = np.meshgrid(np.arange(x0, x1 + 1) + .5, np.arange(y0, y1 + 1) + .5)
    d = (q[1, 1] - q[2, 1]) * (q[0, 0] - q[2, 0]) + (q[2, 0] - q[1, 0]) * (q[0, 1] - q[2, 1])
    if abs(d) < 1e-9: continue
    w0 = ((q[1, 1] - q[2, 1]) * (X - q[2, 0]) + (q[2, 0] - q[1, 0]) * (Y - q[2, 1])) / d
    w1 = ((q[2, 1] - q[0, 1]) * (X - q[2, 0]) + (q[0, 0] - q[2, 0]) * (Y - q[2, 1])) / d
    w2 = 1 - w0 - w1
    tol = 1.2 / max(np.sqrt(abs(d)), 1)
    mk = (w0 >= -tol) & (w1 >= -tol) & (w2 >= -tol)
    if not mk.any(): continue
    W = np.clip(np.stack([w0[mk], w1[mk], w2[mk]], 1), 0, None); W /= W.sum(1, keepdims=True)
    pix_i.append(np.full(mk.sum(), i)); pix_xy.append(np.stack([X[mk], Y[mk]], 1).astype(int)); pix_w.append(W); pix_p.append(np.full(mk.sum(), pagt[i]))
pix_i = np.concatenate(pix_i); pix_xy = np.concatenate(pix_xy); pix_w = np.concatenate(pix_w); pix_p = np.concatenate(pix_p)
okp = (pix_xy[:, 0] >= 0) & (pix_xy[:, 0] < PAG) & (pix_xy[:, 1] >= 0) & (pix_xy[:, 1] < PAG)
pix_i, pix_xy, pix_w, pix_p = pix_i[okp], pix_xy[okp], pix_w[okp], pix_p[okp]
print(f'  {len(pix_i)/1e6:.2f} M píxeles')
Wp = (P3[pix_i] * pix_w[:, :, None]).sum(1)                          # posición (m)
Np = (NV[F[pix_i, :3]] * pix_w[:, :, None]).sum(1); Np /= np.linalg.norm(Np, axis=1, keepdims=True) + 1e-12
UVp = (VT[F[pix_i, 3:]] * pix_w[:, :, None]).sum(1)
Lv = (colv[F[pix_i, :3]] * pix_w[:, :, None]).sum(1)                # luz por vértice (suave), para lo no visto
# ---------------- color propio (textura de UC a resolución completa) y su versión suave
alb = np.zeros((len(pix_i), 3), np.float32); albl = np.zeros((len(pix_i), 3), np.float32)
mmp = FM[pix_i]
for mm in set(mmp):
    sel = np.nonzero(mmp == mm)[0]; tn = mats.get(mm)
    if not tn: alb[sel] = 0.5; albl[sel] = 0.5; continue
    a, lp, _ = tex_arr(tn); h, w = a.shape[:2]
    u = (UVp[sel, 0] % 1) * w - .5; v = ((1 - UVp[sel, 1]) % 1) * h - .5
    x0 = np.floor(u).astype(int); y0 = np.floor(v).astype(int); fx = (u - x0)[:, None]; fy = (v - y0)[:, None]
    x0 %= w; y0 %= h; x1 = (x0 + 1) % w; y1 = (y0 + 1) % h
    alb[sel] = (a[y0, x0, :3] * (1 - fx) * (1 - fy) + a[y0, x1, :3] * fx * (1 - fy) + a[y1, x0, :3] * (1 - fx) * fy + a[y1, x1, :3] * fx * fy)
    albl[sel] = lp[y0, x0]
# ---------------- luz de los fondos del REmake por píxel
Wm = Wp * 1000; suma = np.zeros((len(pix_i), 3), np.float32); peso = np.zeros(len(pix_i), np.float32)
for ci, c in enumerate(cams):
    img = cv2.GaussianBlur(np.asarray(Image.eval(c['img'], lambda x: int(255 * (x / 255) ** 0.85)), np.float32) / 255, (0, 0), 1.2)
    Z = ZB[ci]
    for a0 in range(0, len(Wm), 600000):
        sl = slice(a0, a0 + 600000)
        p, z = remake.proyectar(c, Wm[sl])
        ok_ = (z > 100) & (p[:, 0] >= 1) & (p[:, 0] < 510) & (p[:, 1] >= 1) & (p[:, 1] < 446)
        xi = np.clip((p[:, 0] * ZW / 512).astype(int), 0, ZW - 1); yi = np.clip((p[:, 1] * ZH / 448).astype(int), 0, ZH - 1)
        zr = Z[yi, xi]; ok_ &= (z <= zr * 1.03 + 120) | ~np.isfinite(zr)
        vd = np.asarray(c['ojo'], float) - Wm[sl]; dist = np.linalg.norm(vd, axis=1); vd /= dist[:, None] + 1e-9
        cs = np.abs((vd * Np[sl]).sum(1)); ok_ &= cs > 0.2
        w_ = np.where(ok_, cs * cs / (dist / 1000 + 1) ** 2, 0).astype(np.float32)
        if not ok_.any(): continue
        col = img[np.clip(p[:, 1].astype(int), 0, 447), np.clip(p[:, 0].astype(int), 0, 511)]
        suma[sl] += col * w_[:, None]; peso[sl] += w_
vis = peso > 1e-4
bgc = np.zeros_like(suma); bgc[vis] = suma[vis] / peso[vis, None]
Lb = bgc / np.maximum(albl, 0.05)
lumf = lambda x: x @ np.array([0.3, 0.59, 0.11], np.float32)
# tinte suave: mitad de la cromaticidad de la luz
Lb = lumf(Lb)[:, None] * (1 + (Lb / np.maximum(lumf(Lb)[:, None], 1e-3) - 1) * 0.5)
alfa = np.clip(peso / (np.percentile(peso[vis], 30) + 1e-6), 0, 1)[:, None] if vis.any() else np.zeros((len(peso), 1))
L = np.where(vis[:, None], alfa * np.clip(Lb, 0.02, 1.6) + (1 - alfa) * Lv, Lv)
final = np.clip(alb * L, 0, 1)
print(f'  píxeles vistos por alguna cámara: {vis.mean()*100:.0f} %')
paginas = []
for pg in range(npag):
    s_ = pix_p == pg
    im = np.zeros((PAG, PAG, 3), np.float32); cnt = np.zeros((PAG, PAG), np.float32)
    np.add.at(im, (pix_xy[s_, 1], pix_xy[s_, 0]), final[s_]); np.add.at(cnt, (pix_xy[s_, 1], pix_xy[s_, 0]), 1)
    llen = cnt > 0; im[llen] /= cnt[llen, None]
    # suavizado ligero de la luz dentro de cada carta ya va en el fondo; rellenar bordes (2 px) para el filtrado
    m8 = llen.astype(np.uint8)
    for _ in range(3):
        dil = cv2.dilate(im, np.ones((3, 3), np.uint8)); dm = cv2.dilate(m8, np.ones((3, 3), np.uint8))
        nuevo = (dm > 0) & (m8 == 0)
        # media de vecinos llenos
        s3 = cv2.blur(im * m8[..., None], (3, 3)); c3 = cv2.blur(m8.astype(np.float32), (3, 3))
        im[nuevo] = s3[nuevo] / np.maximum(c3[nuevo, None], 1e-6); m8 = np.maximum(m8, nuevo.astype(np.uint8))
    nm = f'atlas_{pg}.png'
    Image.fromarray((im * 255).astype(np.uint8)).save(f'{out}/{nm}'); paginas.append(nm)
# ---------------- luz horneada en las texturas (el juego no usa color por vértice en el escenario):
# cada triángulo usa una copia de su textura oscurecida al nivel de luz que le toca (niveles en escala log)
lumv = colv @ np.array([0.3, 0.59, 0.11])
lt = colv_tri @ np.array([0.3, 0.59, 0.11])
NIV = np.geomspace(0.035, 1.0, int(os.environ.get('NIVELES', 12)))
nivel = np.abs(np.log(np.maximum(lt, 0.01))[:, None] - np.log(NIV)[None]).argmin(1)
tinte_sala = np.median(colv[visto] / np.maximum(lumv[visto, None], 0.02), 0) if visto.any() else np.ones(3)
tinte_sala = 1 + (np.clip(tinte_sala, 0.7, 1.3) - 1) * 0.6
texf = np.array([mats.get(mm) for mm in FM], dtype=object)
areas_t = np.linalg.norm(np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]]), axis=1) / 2
PRES = int(os.environ.get('MAXTEX', 140))
from collections import defaultdict
uso = defaultdict(float)
for _k, (tf, nv_, a_) in enumerate(zip(texf, nivel, areas_t)):
    if tf and pagt[_k] < 0: uso[(tf, int(nv_))] += a_
# reparto: cada textura recibe niveles según su superficie (mínimo 1), y sus niveles se eligen por k-medias
area_tex = defaultdict(float)
for (tf, nv_), a_ in uso.items(): area_tex[tf] += a_
tot = sum(area_tex.values()); cupo = {tf: 1 for tf in area_tex}
resto = PRES - len(cupo)
for tf in sorted(area_tex, key=lambda t: -area_tex[t]):
    extra = min(len(NIV) - 1, int(round(resto * area_tex[tf] / tot)))
    cupo[tf] += max(0, extra)
while sum(cupo.values()) > PRES:
    tf = max(cupo, key=lambda t: cupo[t]); cupo[tf] -= 1
mapa = {}; vivos = {}
for tf in area_tex:
    nivs = sorted(n for (t, n) in uso if t == tf); pesos = [uso[(tf, n)] for n in nivs]
    k = min(cupo[tf], len(nivs))
    cent = list(np.quantile(nivs, np.linspace(0, 1, k + 2)[1:-1])) if k > 1 else [float(np.average(nivs, weights=pesos))]
    for _ in range(10):
        grupos_ = [[] for _ in cent]
        for n, w in zip(nivs, pesos): grupos_[int(np.argmin([abs(n - c) for c in cent]))].append((n, w))
        cent = [float(np.average([n for n, _ in g], weights=[w for _, w in g])) if g else c for g, c in zip(grupos_, cent)]
    for n in nivs:
        c = int(round(cent[int(np.argmin([abs(n - c) for c in cent]))]))
        mapa[(tf, n)] = (tf, c); vivos[(tf, c)] = vivos.get((tf, c), 0) + uso[(tf, n)]
print(f'texturas horneadas: {len(vivos)} (de {len(uso)} pares textura/nivel)')
for tn in set(x for x in mats.values() if x): pass
nombre_mat = {}
with open(f'{out}/sala.mtl', 'w') as fm:
    for k_, nm in enumerate(paginas): fm.write(f'newmtl pag_{k_}\nKd 1 1 1\nmap_Kd {nm}\n')
    for (tf, nv_) in vivos:
        stem = os.path.splitext(os.path.basename(tf))[0]; nm = f'{stem}__L{nv_:02d}'
        try: im = Image.open(os.path.join(base, tf)).convert('RGBA')
        except Exception: continue
        lado = int(os.environ.get('TEXG', 512)) if area_tex[tf] / tot > 0.02 else int(os.environ.get('TEXP', 256))
        if max(im.size) > lado: im = im.resize((min(lado, im.size[0]), min(lado, im.size[1])), Image.LANCZOS)
        a_ = np.asarray(im, float); fac = NIV[nv_] * tinte_sala
        a_[..., :3] = np.clip(a_[..., :3] * fac, 0, 255)
        Image.fromarray(a_.astype(np.uint8), 'RGBA').save(f'{out}/{nm}.png')
        fm.write(f'newmtl {nm}\nKd 1 1 1\nmap_Kd {nm}.png\n'); nombre_mat[(tf, nv_)] = nm
with open(f'{out}/sala.obj', 'w') as f:
    f.write('mtllib sala.mtl\n')
    for v in V: f.write(f'v {v[0]:.4f} {v[1]:.4f} {v[2]:.4f}\n')
    for vt in VT: f.write(f'vt {vt[0]:.5f} {vt[1]:.5f}\n')
    nvt = len(VT) + 1
    for pg in range(npag):
        f.write(f'usemtl pag_{pg}\n')
        for i in np.nonzero(pagt == pg)[0]:
            fa = F[i]
            for q in uvat[i]: f.write(f'vt {q[0]/PAG:.6f} {1-q[1]/PAG:.6f}\n')
            f.write(f'f {fa[0]+1}/{nvt} {fa[1]+1}/{nvt+1} {fa[2]+1}/{nvt+2}\n')
            if os.environ.get('DOBLE'): f.write(f'f {fa[0]+1}/{nvt} {fa[2]+1}/{nvt+2} {fa[1]+1}/{nvt+1}\n')
            nvt += 3
    orden = np.lexsort((nivel, texf.astype(str)))
    cur = None
    for i in orden:
        if pagt[i] >= 0: continue
        tf = texf[i]
        if not tf: continue
        nm = nombre_mat.get(mapa.get((tf, int(nivel[i]))))
        if not nm: continue
        if nm != cur: f.write(f'usemtl {nm}\n'); cur = nm
        fa = F[i]
        f.write(f'f {fa[0]+1}/{fa[3]+1} {fa[1]+1}/{fa[4]+1} {fa[2]+1}/{fa[5]+1}\n')
        if os.environ.get('DOBLE'): f.write(f'f {fa[0]+1}/{fa[3]+1} {fa[2]+1}/{fa[5]+1} {fa[1]+1}/{fa[4]+1}\n')
shutil.copy(f'/home/claude/re1gc/salas/{r}/colision.obj', f'{out}/colision.obj')
json.dump(dict(origen=ucobj, alin=A), open(f'{out}/meta_uc.json', 'w'))
print('ok', out)
