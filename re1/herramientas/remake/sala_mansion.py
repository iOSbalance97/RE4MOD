"""sala_mansion.py rNNN salida : sala de la mansión modelada desde la colisión del REmake, con las texturas del comedor de UC
(papel pintado, zócalo de cuarterones de madera, listel, cornisa y techo de casetones) y puertas de madera en cada puerta del REmake.
Paredes lisas de doble cara a la altura real (sin rendijas: siguen la colisión), rampas -> peldaños, techo a +3 m."""
import sys, os, json
import numpy as np
from collections import defaultdict
from PIL import Image
sys.path.insert(0, '/home/claude/tools'); from hmap import floors, heights
r, out = sys.argv[1], sys.argv[2]; os.makedirs(out, exist_ok=True)
CAS = '/home/claude/uc/m/r103'
OSC = float(os.environ.get('OSCURO', 0.8))
TEXF = {'cas_papel_verde': 0.62}
TEX = dict(papel='cas_papel_verde', zocalo='cas_zocalo', listel='cas_listel', techo='cas_techo_cas', suelo='cas_tablas',
           huella='cas_tablas', tabica='cas_listel', puerta='cas_puerta', marco='cas_listel', pomo='cas_pomo')
for t in set(TEX.values()):
    im = np.asarray(Image.open(f'{CAS}/{t}.png').convert('RGB'), np.float32) * OSC * TEXF.get(t, 1.0)
    Image.fromarray(np.clip(im, 0, 255).astype(np.uint8)).save(f'{out}/{t}.png')
col = f'/home/claude/re1gc/salas/{r}/colision.obj'
V = []; Fi = []
for l in open(col):
    if l.startswith('v '): V.append([float(x) for x in l.split()[1:4]])
    elif l.startswith('f '): Fi.append([int(x.split('/')[0]) - 1 for x in l.split()[1:4]])
V = np.array(V); Fi = np.array(Fi); T = V[Fi]
n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]); a = np.linalg.norm(n, axis=1) / 2; n /= 2 * a[:, None] + 1e-12
TF = floors(col); ALTO = float(os.environ.get('ALTO', 3.0))
geo = defaultdict(list)
def tri(m, p, uv, dos=True):
    geo[m].append((np.array(p, float), np.array(uv, float)))
    if dos: geo[m].append((np.array(p, float)[::-1], np.array(uv, float)[::-1]))
def quad(m, p, uv, dos=True):
    tri(m, [p[0], p[1], p[2]], [uv[0], uv[1], uv[2]], dos); tri(m, [p[0], p[2], p[3]], [uv[0], uv[2], uv[3]], dos)
def caja(p0, p1, m, esc=0.5):
    x0, y0, z0 = p0; x1, y1, z1 = p1
    P = [[x0, y0, z0], [x1, y0, z0], [x1, y1, z0], [x0, y1, z0], [x0, y0, z1], [x1, y0, z1], [x1, y1, z1], [x0, y1, z1]]
    for (i, j, k, l), ej in (((0, 1, 2, 3), (0, 1)), ((5, 4, 7, 6), (0, 1)), ((4, 0, 3, 7), (2, 1)), ((1, 5, 6, 2), (2, 1)), ((3, 2, 6, 7), (0, 2)), ((4, 5, 1, 0), (0, 2))):
        q = [np.array(P[i], float), np.array(P[j], float), np.array(P[k], float), np.array(P[l], float)]
        quad(m, q, [[q_[ej[0]] / esc, q_[ej[1]] / esc] for q_ in q], dos=False)
def techo_y(x, z, yf):
    h = heights(TF, x, z); h = h[h > yf + 0.5]
    return yf + (min(ALTO, h.min() - yf - 0.12) if len(h) else ALTO)
plano = n[:, 1] > 0.97; rampa = (n[:, 1] > 0.45) & ~plano; pared = np.abs(n[:, 1]) < 0.35
E = 1.4
# ---------------- suelos y techos
for t3 in T[plano]:
    if t3[:, 1].mean() > float(os.environ.get('SUELO_MAX', 99)): continue
    tri(TEX['suelo'], t3, t3[:, [0, 2]] / E)
    q = t3.copy(); q[:, 1] = [techo_y(p[0], p[2], p[1]) for p in t3]; tri(TEX['techo'], q, q[:, [0, 2]] / 1.0)
# ---------------- paredes por bandas: zócalo, listel, papel y cornisa
BANDAS = [(0.0, 0.95, 'zocalo', 0.95), (0.95, 1.03, 'listel', 0.5), (1.03, ALTO - 0.16, 'papel', 0.9), (ALTO - 0.16, ALTO + 0.4, 'listel', 0.5)]
npar = 0
for t3, nn in zip(T[pared], n[pared]):
    h_ = np.array([-nn[2], 0, nn[0]]); h_ /= np.linalg.norm(h_) + 1e-12
    pr = t3 @ h_; A_, B_ = t3[pr.argmin()], t3[pr.argmax()]
    if pr.max() - pr.min() < 0.03: continue
    ya = t3[:, 1].min(); nh = np.array([nn[0], 0, nn[2]]) / (np.hypot(nn[0], nn[2]) + 1e-12)
    amb = 0
    for sg in (1, -1):
        q = t3.mean(0) + sg * 0.35 * nh; hh = heights(TF, q[0], q[2]); amb += int(np.any((hh > ya - 0.6) & (hh < ya + 0.6)))
    if amb == 2 and t3[:, 1].max() - ya < 1.3:          # escalón o murete: solo su altura
        yt_ = t3[:, 1].max()
        quad(TEX['tabica'], [A_ * [1, 0, 1] + [0, ya, 0], B_ * [1, 0, 1] + [0, ya, 0], B_ * [1, 0, 1] + [0, yt_, 0], A_ * [1, 0, 1] + [0, yt_, 0]],
             [[pr.min() / 0.5, ya / 0.5], [pr.max() / 0.5, ya / 0.5], [pr.max() / 0.5, yt_ / 0.5], [pr.min() / 0.5, yt_ / 0.5]]); continue
    # columnas a lo largo de la pared (las rampas tienen el suelo inclinado)
    nu_ = max(1, int(np.ceil((pr.max() - pr.min()) / 0.5)))
    cols = []
    for i in range(nu_ + 1):
        u = i / nu_; pu = pr.min() + (pr.max() - pr.min()) * u; q = A_ + (B_ - A_) * u; ys_ = []
        for e0, e1 in ((t3[0], t3[1]), (t3[1], t3[2]), (t3[2], t3[0])):
            a0, a1 = e0 @ h_, e1 @ h_
            if min(a0, a1) - 1e-6 <= pu <= max(a0, a1) + 1e-6 and abs(a1 - a0) > 1e-6: ys_.append(e0[1] + (e1[1] - e0[1]) * (pu - a0) / (a1 - a0))
        yf = min(ys_) if ys_ else ya
        # lado del paso para el techo
        ytop = max(techo_y(q[0] + nh[0] * 0.2, q[2] + nh[2] * 0.2, yf), techo_y(q[0] - nh[0] * 0.2, q[2] - nh[2] * 0.2, yf))
        cols.append((q, pu, yf, ytop))
    for (q0, p0, y0, t0), (q1, p1, y1, t1) in zip(cols[:-1], cols[1:]):
        for b0, b1, tx, esc in BANDAS:
            ya0, yb0 = y0 + b0, min(y0 + b1, t0); ya1, yb1 = y1 + b0, min(y1 + b1, t1)
            if yb0 <= ya0 + 0.005 and yb1 <= ya1 + 0.005: continue
            yb0 = max(yb0, ya0); yb1 = max(yb1, ya1)
            quad(TEX[tx], [q0 * [1, 0, 1] + [0, ya0, 0], q1 * [1, 0, 1] + [0, ya1, 0], q1 * [1, 0, 1] + [0, yb1, 0], q0 * [1, 0, 1] + [0, yb0, 0]],
                 [[p0 / esc, (ya0 - y0) / esc], [p1 / esc, (ya1 - y1) / esc], [p1 / esc, (yb1 - y1) / esc], [p0 / esc, (yb0 - y0) / esc]])
    npar += 1
# ---------------- rampas -> escaleras
idx = np.nonzero(rampa)[0]; grupo = {}
for i in idx:
    for g, lst in grupo.items():
        j = lst[0]
        if np.dot(n[i], n[j]) > 0.97 and np.min(np.linalg.norm(T[i][:, None] - np.concatenate([T[k] for k in lst])[None], axis=2)) < 0.05: lst.append(i); break
    else: grupo[i] = [i]
esc = 0
for g, lst in grupo.items():
    P = np.concatenate([T[k] for k in lst]); nn = n[lst[0]]
    up = -np.array([nn[0], 0, nn[2]]); up /= np.linalg.norm(up) + 1e-12; ac = np.array([-up[2], 0, up[0]])
    u = P @ up; v = P @ ac; u0, u1 = u.min(), u.max(); v0, v1 = v.min(), v.max()
    y0 = P[np.argmin(u), 1]; y1 = P[np.argmax(u), 1]
    for k in lst:
        c = T[k].mean(0); q = T[k].copy(); q[:, 1] = [techo_y(p[0], p[2], p[1]) for p in T[k]]; tri(TEX['techo'], q, q[:, [0, 2]])
    if y1 - y0 < 0.3 or u1 - u0 < 0.4:
        for k in lst: tri(TEX['suelo'], T[k], T[k][:, [0, 2]] / E)
        continue
    N = max(2, int(round((y1 - y0) / 0.18))); rise = (y1 - y0) / N; run = (u1 - u0) / N
    def pt(uu, vv, yy): return up * uu + ac * vv + np.array([0, yy, 0])
    for s in range(N):
        ua, ub = u0 + s * run, u0 + (s + 1) * run; yt = y0 + (s + 1) * rise; yb = y0 + s * rise
        quad(TEX['huella'], [pt(ua, v0, yt), pt(ub, v0, yt), pt(ub, v1, yt), pt(ua, v1, yt)], [[ua / E, v0 / E], [ub / E, v0 / E], [ub / E, v1 / E], [ua / E, v1 / E]])
        quad(TEX['tabica'], [pt(ua, v0, yb), pt(ua, v1, yb), pt(ua, v1, yt), pt(ua, v0, yt)], [[v0 / 0.5, 0], [v1 / 0.5, 0], [v1 / 0.5, 0.4], [v0 / 0.5, 0.4]])
        for vv in (v0, v1):
            quad(TEX['zocalo'], [pt(ua, vv, y0 - 0.02), pt(ub, vv, y0 - 0.02), pt(ub, vv, yt), pt(ua, vv, yt)], [[ua / 0.95, 0], [ub / 0.95, 0], [ub / 0.95, (yt - y0) / 0.95], [ua / 0.95, (yt - y0) / 0.95]])
    esc += 1
# ---------------- puertas: hoja de madera con marco en la pared más cercana a cada puerta del REmake
G = json.load(open('/home/claude/re1gc/work/puertas_remake.json')).get(r, [])
Wc = [(t3, nn) for t3, nn in zip(T[pared], n[pared])]
npu = 0
for d in G:
    if d['dst'] == r: continue
    Q = np.array(d['quad'], float).reshape(4, 2) / 1000; c = Q.mean(0)
    best = None
    for t3, nn in Wc:
        if t3[:, 1].max() - t3[:, 1].min() < 1.5: continue
        nh = np.array([nn[0], nn[2]]) / (np.hypot(nn[0], nn[2]) + 1e-12); p0 = t3[0, [0, 2]]
        dist = abs((c - p0) @ nh)
        tg = np.array([-nh[1], nh[0]]); pr_ = (t3[:, [0, 2]] - p0) @ tg; s_ = (c - p0) @ tg
        if not (pr_.min() - 0.3 <= s_ <= pr_.max() + 0.3): continue
        if best is None or dist < best[0]: best = (dist, t3, nh)
    if best is None or best[0] > 1.6: print('  puerta sin pared:', d['dst']); continue
    _, t3, nh = best; p0 = t3[0, [0, 2]]; tg = np.array([-nh[1], nh[0]])
    pc = p0 + tg * ((c - p0) @ tg)                          # centro de la puerta sobre la pared
    lados = [sg for sg in (1.0, -1.0) if len(heights(TF, *(pc + nh * sg * 0.4)))]
    lado = lados[0] if len(lados) == 1 else (np.sign((c - pc) @ nh) or 1.0)          # la puerta mira al lado del paso
    hh = heights(TF, *(pc + nh * lado * 0.4)); hh = hh[hh < float(os.environ.get('SUELO_MAX', 99))]
    yf = float(hh.min()) if len(hh) else float(t3[:, 1].min())
    W_, H_ = 1.0, 2.2; o = np.array([pc[0], yf, pc[1]]); tt = np.array([tg[0], 0, tg[1]]); nn3 = np.array([nh[0], 0, nh[1]]) * lado
    P = lambda a_, b_, c_: o + tt * a_ + np.array([0, b_, 0]) + nn3 * c_
    # hoja (dos caras) un poco hacia el paso, marco y dintel saliendo de la pared
    quad(TEX['puerta'], [P(-W_ / 2, 0, 0.03), P(W_ / 2, 0, 0.03), P(W_ / 2, H_, 0.03), P(-W_ / 2, H_, 0.03)], [[0, 0], [1, 0], [1, 1], [0, 1]], dos=False)
    quad(TEX['puerta'], [P(W_ / 2, 0, 0.03), P(-W_ / 2, 0, 0.03), P(-W_ / 2, H_, 0.03), P(W_ / 2, H_, 0.03)], [[1, 0], [0, 0], [0, 1], [1, 1]], dos=False)
    for a0, a1 in ((-W_ / 2 - 0.12, -W_ / 2), (W_ / 2, W_ / 2 + 0.12)):
        caja(tuple(np.minimum(P(a0, 0, 0.0), P(a1, H_ + 0.1, 0.08))), tuple(np.maximum(P(a0, 0, 0.0), P(a1, H_ + 0.1, 0.08))), TEX['marco'], 0.3)
    caja(tuple(np.minimum(P(-W_ / 2 - 0.2, H_, 0.0), P(W_ / 2 + 0.2, H_ + 0.22, 0.11))), tuple(np.maximum(P(-W_ / 2 - 0.2, H_, 0.0), P(W_ / 2 + 0.2, H_ + 0.22, 0.11))), TEX['marco'], 0.3)
    for zz in (0.06, 0.0):
        caja(tuple(np.minimum(P(W_ / 2 - 0.16, 0.98, zz), P(W_ / 2 - 0.1, 1.06, zz + 0.05))), tuple(np.maximum(P(W_ / 2 - 0.16, 0.98, zz), P(W_ / 2 - 0.1, 1.06, zz + 0.05))), TEX['pomo'], 0.1)
    npu += 1; print('  puerta', d['dst'], 'en', np.round(o, 2), 'normal', np.round(nn3, 2))
for _ex in [e for e in os.environ.get('MODELOS_EXTRA', '').split(';') if e]:
    _d = os.path.dirname(_ex); _mt = {}; _m = None
    for l in open(os.path.join(_d, os.path.basename(_ex)[:-4] + '.mtl')):
        if l.startswith('newmtl'): _m = l.split()[1]
        elif l.startswith('map_Kd'): _mt[_m] = l.split()[1]
    for _m, _t in _mt.items():
        _im = np.asarray(Image.open(os.path.join(_d, _t)).convert('RGBA'), np.float32); _im[..., :3] *= float(os.environ.get('OSCURO_EXTRA', 0.9))
        Image.fromarray(np.clip(_im, 0, 255).astype(np.uint8), 'RGBA').save(f'{out}/{_m}.png')
    _V = []; _T = []; _m = None
    for l in open(_ex):
        if l.startswith('v '): _V.append([float(x) for x in l.split()[1:4]])
        elif l.startswith('vt '): _T.append([float(x) for x in l.split()[1:3]])
        elif l.startswith('usemtl'): _m = l.split()[1]
        elif l.startswith('f '):
            q = [x.split('/') for x in l.split()[1:4]]
            tri(_m, [_V[int(a[0]) - 1] for a in q], [_T[int(a[1]) - 1] for a in q])
    print('modelo añadido:', _ex)
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
import shutil; shutil.copy(col, f'{out}/colision.obj')
print(f'{r}: {sum(len(l) for l in geo.values())} triángulos, {npar} paredes, {esc} tramos de escalera, {npu} puertas')
