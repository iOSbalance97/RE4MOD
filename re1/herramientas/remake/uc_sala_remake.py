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
    if n_[1] < 0.7 and n_[1] > -0.7: continue
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
            if any(abs(h - y) < 0.35 for h, _ in hs): continue
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
suma = np.zeros((len(V), 3)); peso = np.zeros(len(V))
for ci, c in enumerate(cams):
    img = np.asarray(Image.eval(c['img'], lambda x: int(255 * (x / 255) ** 0.85)).filter(ImageFilter.GaussianBlur(5)), float) / 255
    Z = zbuffer(c)
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
# ---------------- luz horneada en las texturas (el juego no usa color por vértice en el escenario):
# cada triángulo usa una copia de su textura oscurecida al nivel de luz que le toca (niveles en escala log)
lumv = colv @ np.array([0.3, 0.59, 0.11])
lt = lumv[F[:, :3]].mean(1)
NIV = np.geomspace(0.035, 1.0, int(os.environ.get('NIVELES', 12)))
nivel = np.abs(np.log(np.maximum(lt, 0.01))[:, None] - np.log(NIV)[None]).argmin(1)
tinte_sala = np.median(colv[visto] / np.maximum(lumv[visto, None], 0.02), 0) if visto.any() else np.ones(3)
tinte_sala = 1 + (np.clip(tinte_sala, 0.7, 1.3) - 1) * 0.6
texf = np.array([mats.get(mm) for mm in FM], dtype=object)
areas_t = np.linalg.norm(np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]]), axis=1) / 2
PRES = int(os.environ.get('MAXTEX', 140))
from collections import defaultdict
uso = defaultdict(float)
for tf, nv_, a_ in zip(texf, nivel, areas_t):
    if tf: uso[(tf, int(nv_))] += a_
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
    for (tf, nv_) in vivos:
        stem = os.path.splitext(os.path.basename(tf))[0]; nm = f'{stem}__L{nv_:02d}'
        try: im = Image.open(os.path.join(base, tf)).convert('RGBA')
        except Exception: continue
        lado = 256 if area_tex[tf] / tot > 0.03 else 128
        if max(im.size) > lado: im = im.resize((min(lado, im.size[0]), min(lado, im.size[1])), Image.LANCZOS)
        a_ = np.asarray(im, float); fac = NIV[nv_] * tinte_sala
        a_[..., :3] = np.clip(a_[..., :3] * fac, 0, 255)
        Image.fromarray(a_.astype(np.uint8), 'RGBA').save(f'{out}/{nm}.png')
        fm.write(f'newmtl {nm}\nKd 1 1 1\nmap_Kd {nm}.png\n'); nombre_mat[(tf, nv_)] = nm
with open(f'{out}/sala.obj', 'w') as f:
    f.write('mtllib sala.mtl\n')
    for v in V: f.write(f'v {v[0]:.4f} {v[1]:.4f} {v[2]:.4f}\n')
    for vt in VT: f.write(f'vt {vt[0]:.5f} {vt[1]:.5f}\n')
    orden = np.lexsort((nivel, texf.astype(str)))
    cur = None
    for i in orden:
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
