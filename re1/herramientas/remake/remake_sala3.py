"""Paso 3 de una sala del REmake (las que no tienen modelo en UC): la arquitectura (paredes, techos y suelos
grandes) se rehace con texturas en alta de la mansión Spencer de RE5 (o de UC), con la luz del REmake pintada
en ellas; los muebles y detalles siguen con la proyección del fondo, y los suelos con su ortofoto.
uso: remake_sala3.py st rNNN salas/rNNN salida"""
import sys, os, json, shutil
import numpy as np
from PIL import Image, ImageFilter
from scipy.spatial import cKDTree
from collections import defaultdict
st, r, src, out = int(sys.argv[1]), sys.argv[2], sys.argv[3], sys.argv[4]
os.makedirs(out, exist_ok=True)
V = []; VT = []; F = []; FM = []; cur = None
for l in open(f'{src}/sala.obj'):
    if l.startswith('v '): V.append([float(x) for x in l.split()[1:4]])
    elif l.startswith('vt '): VT.append([float(x) for x in l.split()[1:3]])
    elif l.startswith('f '):
        p = [x.split('/') for x in l.split()[1:4]]; F.append([int(a[0]) - 1 for a in p] + [int(a[1]) - 1 for a in p]); FM.append(cur)
    elif l.startswith('usemtl'): cur = l.split()[1]
V = np.array(V); VT = np.array(VT); F = np.array(F); FM = np.array(FM, dtype=object)
mats = {}; m = None
for l in open(f'{src}/sala.mtl'):
    if l.startswith('newmtl'): m = l.split()[1]
    elif l.startswith('map_Kd'): mats[m] = l.split(None, 1)[1].strip()
P = V[F[:, :3]]; n = np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0]); area = np.linalg.norm(n, axis=1) / 2; n /= 2 * area[:, None] + 1e-12
cen = P.mean(1)
cls = np.where(n[:, 1] > 0.75, 0, np.where(n[:, 1] < -0.75, 2, np.where(np.abs(n[:, 1]) < 0.35, 1, 3)))
# ---------------- color visto (luz * color propio) por triángulo, de su textura actual muy suavizada
img_s = {}; img_d = {}
def suave(tn):
    if tn not in img_s:
        im = Image.open(f'{src}/{tn}').convert('RGB')
        img_s[tn] = np.asarray(im.filter(ImageFilter.GaussianBlur(4)), float) / 255
        g = np.asarray(im.convert('L'), float) / 255
        from scipy.ndimage import gaussian_filter, uniform_filter
        hp = g - gaussian_filter(g, 3); img_d[tn] = np.sqrt(uniform_filter(hp * hp, 9))
    return img_s[tn], img_d[tn]
visto = np.full((len(F), 3), np.nan); detalle = np.full(len(F), np.nan)
for i, (f, mm) in enumerate(zip(F, FM)):
    tn = mats.get(mm)
    if not tn or not (mm.startswith('fondo') or mm.startswith('orto')): continue
    a, d = suave(tn); h, w = a.shape[:2]
    uv = VT[f[3:]].mean(0); x = int(np.clip(uv[0] % 1.0001, 0, 0.9999) * w); y = int(np.clip(1 - uv[1], 0, 0.9999) * h)
    visto[i] = a[y, x]; detalle[i] = d[y, x]
ok = ~np.isnan(visto[:, 0])
if ok.any():
    tr = cKDTree(cen[ok]); iv = np.nonzero(ok)[0]
    for i in np.nonzero(~ok)[0]:
        _, jj = tr.query(cen[i], k=min(12, ok.sum())); jj = np.atleast_1d(jj)
        c = [iv[j] for j in jj if np.dot(n[iv[j]], n[i]) > 0.6] or [iv[j] for j in jj]
        visto[i] = visto[c].mean(0); detalle[i] = np.nanmean(detalle[c])
else:
    visto[:] = 0.2; detalle[:] = 0.02
# ---------------- grupos planos grandes = arquitectura
arist = defaultdict(list)
for i, f in enumerate(F[:, :3]):
    for a_, b_ in ((f[0], f[1]), (f[1], f[2]), (f[2], f[0])): arist[(min(a_, b_), max(a_, b_))].append(i)
padre = list(range(len(F)))
def raiz(i):
    while padre[i] != i: padre[i] = padre[padre[i]]; i = padre[i]
    return i
for ts in arist.values():
    for j in ts[1:]:
        a_, b_ = ts[0], j
        if cls[a_] == cls[b_] and cls[a_] != 3 and np.dot(n[a_], n[b_]) > 0.97: padre[raiz(a_)] = raiz(b_)
grupos = defaultdict(list)
for i in range(len(F)): grupos[raiz(i)].append(i)
arq = np.zeros(len(F), bool)
for g, ts in grupos.items():
    ts = np.array(ts); c = cls[ts[0]]
    if c == 3: continue
    A = area[ts].sum()
    if (c == 1 and A >= 1.5) or (c == 2 and A >= 1.0) or (c == 0 and A >= 2.0): arq[ts] = True
arq &= ~np.array([str(mm).startswith('orto') for mm in FM])           # los suelos con ortofoto se quedan
# ---------------- paletas por zona (texturas de RE5 de la biblioteca)
BIB = json.load(open('/home/claude/re1gc/biblioteca/indice.json'))
def por_nombre(n_):
    for e in BIB:
        if e['origen'].startswith('re5:') and e['origen'][4:].startswith(n_.lower()): return e
    return None
ZONA = {1: 'mansion', 2: 'mansion', 3: 'fuera', 4: 'residencia', 5: 'lab'}[st]
PAL = {
 'mansion': dict(madera=['h_s700_woodpanel'], papel=['h_s700_wallpaper', 'h_s700_wall03', 'h_s700_wall02'], liso=['h_s700_wall_white14', 'h_s700_turo_wall'],
                 techo=['h_s700_tenjyou01'], suelo_madera=['h_s700_floor01'], suelo_piedra=['h_s700_yuka06'], alfombra=['g_s700_din_jutang01']),
 'residencia': dict(madera=['h_s700_woodpanel'], papel=['y_s407_kabef', 'h_s700_wallpaper'], liso=['y_s407_sotokabe', 'h_s700_wall_white14'],
                    techo=['g-s701-ctenjo'], suelo_madera=['y_407_yukaa', 'h_s700_floor01'], suelo_piedra=['g-s701-cyuka'], alfombra=['g_s700_din_jutang01']),
 'fuera': dict(madera=['g-s701-bsotokabe01'], papel=['g-s701-akabeiwa'], liso=['g-s701-akabetsuchi', 'g-s701-csotokabenaka'],
               techo=['g-s701-atenjo'], suelo_madera=['g-s701-bnakayuka01'], suelo_piedra=['g-s701-cyuka', 'y-s705-yukaaa'], alfombra=['g-s701-ayukakoshitsu']),
}
lum = lambda c: np.asarray(c, float) @ [0.3, 0.59, 0.11]
def elegir(tipo):
    pal = PAL.get(ZONA)
    if not pal: return None
    for n_ in pal[tipo]:
        e = por_nombre(n_)
        if e: return e
    return None
def clasifica(ts):
    c = cls[ts[0]]; col = np.average(visto[ts], 0, weights=area[ts]); det = float(np.nanmean(detalle[ts]))
    L = lum(col) + 1e-6; ch = col / L
    if c == 2: return 'techo'
    if c == 0:
        if ch[0] > 1.35 and ch[2] < 0.8: return 'alfombra'
        return 'suelo_madera' if ch[0] > 1.12 else 'suelo_piedra'
    marron = ch[0] > 1.15 and ch[2] < 0.85
    if marron and L < 0.35: return 'madera'
    return 'papel' if det > 0.035 else 'liso'
asign = {}
for g, ts in grupos.items():
    ts = np.array(ts)
    if not arq[ts].all(): continue
    if cls[ts[0]] == 1:
        # paredes: zócalo (hasta 1,1 m sobre el suelo más bajo del grupo) y parte alta por separado
        y0 = P[ts][:, :, 1].min()
        for parte in (cen[ts, 1] < y0 + 1.1, cen[ts, 1] >= y0 + 1.1):
            tt = ts[parte]
            if len(tt):
                tipo = clasifica(tt); e = elegir(tipo)
                for i in tt: asign[int(i)] = e
    else:
        e = elegir(clasifica(ts))
        for i in ts: asign[int(i)] = e
asign = {i: e for i, e in asign.items() if e is not None}
print(f'{r}: {len(asign)} de {len(F)} triángulos pasan a material en alta ({sum(area[list(asign)])if asign else 0:.0f} m²)')
# ---------------- luz por triángulo para los nuevos materiales: color visto / color propio del material
def tex_media(e):
    return np.asarray(Image.open(e['png']).convert('RGB').resize((8, 8), Image.BOX), float).reshape(-1, 3).mean(0) / 255
NIV = np.geomspace(0.03, 1.0, 12)
nivel = {}; tinte = {}
for i, e in asign.items():
    k = lum(visto[i]) / max(lum(tex_media(e)), 0.05)
    nivel[i] = int(np.abs(np.log(max(k, 0.01)) - np.log(NIV)).argmin())
# ---------------- salida
for mm, tn in mats.items():
    if os.path.exists(f'{src}/{tn}') and not os.path.exists(f'{out}/{tn}'): shutil.copy(f'{src}/{tn}', f'{out}/{tn}')
variantes = {}
def variante(e, nv):
    k = (e['id'], nv)
    if k not in variantes:
        nm = f'hd_{e["id"]:03d}_L{nv:02d}'
        im = Image.open(e['png']).convert('RGB')
        if max(im.size) > 256: im = im.resize((256, 256), Image.LANCZOS)
        a = np.asarray(im, float) * NIV[nv]
        Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).save(f'{out}/{nm}.png'); variantes[k] = nm
    return variantes[k]
# limitar variantes: como mucho 5 niveles por material (los más usados) y el resto al más cercano
uso = defaultdict(float)
for i, e in asign.items(): uso[(e['id'], nivel[i])] += area[i]
porid = defaultdict(list)
for (eid, nv), a_ in uso.items(): porid[eid].append((a_, nv))
permit = {eid: sorted(nv for _, nv in sorted(l, reverse=True)[:5]) for eid, l in porid.items()}
for i, e in asign.items():
    nv = nivel[i]; pm = permit[e['id']]; nivel[i] = min(pm, key=lambda x: abs(x - nv))
with open(f'{out}/sala.mtl', 'w') as fm:
    for mm, tn in mats.items(): fm.write(f'newmtl {mm}\nKd 1 1 1\nmap_Kd {tn}\n')
    for i, e in asign.items():
        nm = variante(e, nivel[i])
    for (eid, nv), nm in variantes.items(): fm.write(f'newmtl {nm}\nKd 1 1 1\nmap_Kd {nm}.png\n')
def uv_plano(i, mrep):
    p = P[i]; a_ = np.abs(n[i]); ax = int(np.argmax(a_))
    if ax == 1: u, v = p[:, 0], p[:, 2]
    elif ax == 0: u, v = p[:, 2], p[:, 1]
    else: u, v = p[:, 0], p[:, 1]
    return np.stack([u / mrep, v / mrep], 1)
with open(f'{out}/sala.obj', 'w') as f:
    f.write('mtllib sala.mtl\n')
    for v in V: f.write(f'v {v[0]:.4f} {v[1]:.4f} {v[2]:.4f}\n')
    for vt in VT: f.write(f'vt {vt[0]:.5f} {vt[1]:.5f}\n')
    nvt = len(VT) + 1; cur = None
    for i in np.argsort(FM.astype(str), kind='stable'):
        if i in asign: continue
        mm = FM[i]
        if mm != cur: f.write(f'usemtl {mm}\n'); cur = mm
        fa = F[i]; f.write(f'f {fa[0]+1}/{fa[3]+1} {fa[1]+1}/{fa[4]+1} {fa[2]+1}/{fa[5]+1}\n')
    orden = sorted(asign, key=lambda i: (asign[i]['id'], nivel[i]))
    for i in orden:
        e = asign[i]; nm = variantes[(e['id'], nivel[i])]
        if nm != cur: f.write(f'usemtl {nm}\n'); cur = nm
        mrep = max(0.8, min(3.0, e.get('m_rep', 2.0)))
        uv = uv_plano(i, mrep); fa = F[i]
        for u_, v_ in uv: f.write(f'vt {u_:.5f} {v_:.5f}\n')
        f.write(f'f {fa[0]+1}/{nvt} {fa[1]+1}/{nvt+1} {fa[2]+1}/{nvt+2}\n'); nvt += 3
shutil.copy(f'{src}/colision.obj', f'{out}/colision.obj')
if os.path.exists(f'{src}/meta.json'): shutil.copy(f'{src}/meta.json', f'{out}/meta.json')
print('ok', out, len(variantes), 'texturas en alta')
