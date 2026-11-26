"""sala_colision.py rNNN salida : sala modelada desde la colisión del REmake con texturas del castillo de RE4.
Paredes de doble cara, suelos de losas, rampas convertidas en escaleras con peldaños, techo a +3 m (salvo bajo otro tramo)."""
import sys, os, shutil
import numpy as np
from collections import defaultdict
sys.path.insert(0, '/home/claude/tools'); from hmap import floors, heights
r, out = sys.argv[1], sys.argv[2]; os.makedirs(out, exist_ok=True)
CAS = '/home/claude/uc/m/r103'
TEX = dict(pared='cas_ladrillo', suelo='cas_losas', huella='cas_losas', tabica='cas_piedra', techo='cas_piedra_techo')
CUEVA = bool(os.environ.get('CUEVA'))
if CUEVA: TEX = dict(pared='cas_roca_pared', suelo='cas_roca_suelo', huella='cas_roca_peldano', tabica='cas_roca_pared', techo='cas_roca_techo')
def _ruido(p, f=1.6, sem=0):
    # ruido de valor 3D suave (continuo entre paredes vecinas): suma de senos con fases fijas
    x, y, z = p[..., 0] * f, p[..., 1] * f, p[..., 2] * f
    r = (np.sin(1.7 * x + 0.3 + sem) * np.sin(1.3 * z + 1.1) + np.sin(2.9 * y + 0.7 * x + 2.0) * 0.6 + np.sin(3.7 * z - 1.9 * y + 0.4) * 0.45
         + np.sin(5.3 * x + 4.1 * z + 1.3 * y) * 0.3)
    return r / 2.35
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
    h = heights(TF, c[0], c[2]); return True if CUEVA else not np.any((h > c[1] + 0.5) & (h < c[1] + ALTO + 0.2))
def _y_techo(x, z, yf):
    q0 = np.array([x, 0.0, z]); y = 2.75 + 0.35 * _ruido(q0, 1.3, 3.0) + 0.1 * _ruido(q0, 4.0, 5.0)
    h = heights(TF, x, z); h = h[h > yf + 0.5]
    if len(h): y = min(y, h.min() - yf - 0.15)          # nunca atravesar el tramo de encima
    return yf + y
def _techo_cueva(t3, k=4):
    # subdividir y dar relieve (bóveda de roca entre 2.4 y 3.1 m)
    P0, P1, P2 = t3
    for i in range(k):
        for j in range(k - i):
            for tri_ in (((i, j), (i + 1, j), (i, j + 1)), ((i + 1, j), (i + 1, j + 1), (i, j + 1))):
                if any(a_ + b_ > k for a_, b_ in tri_): continue
                q = np.array([P0 + (P1 - P0) * a_ / k + (P2 - P0) * b_ / k for a_, b_ in tri_])
                q[:, 1] = [_y_techo(p_[0], p_[2], p_[1]) for p_ in q]
                tri(TEX['techo'], q, q[:, [0, 2]] / E)
plano = n[:, 1] > 0.97; rampa = (n[:, 1] > 0.45) & ~plano; pared = np.abs(n[:, 1]) < 0.35
# suelos y techo
for t3 in T[plano]:
    tri(TEX['suelo'], t3, t3[:, [0, 2]] / E, dos=False if False else True)
    c = t3.mean(0)
    if techo_libre(c):
        if CUEVA: _techo_cueva(t3)
        else: q = t3.copy(); q[:, 1] += ALTO; tri(TEX['techo'], q, q[:, [0, 2]] / E)
# esquinas: extremos de pared compartidos por paredes con otra orientación (ahí el relieve se anula para no abrir rendijas)
from scipy.spatial import cKDTree as _KD
_EP = []; _EN = []
for t3, nn in zip(T[pared], n[pared]):
    for p_ in t3: _EP.append(p_); _EN.append(np.array([nn[0], nn[2]]) / (np.hypot(nn[0], nn[2]) + 1e-9))
_EP = np.array(_EP); _EN = np.array(_EN); _EK = _KD(_EP[:, [0, 2]])
def _es_esquina(p_):
    ii = [j for j in _EK.query_ball_point([p_[0], p_[2]], 0.12) if -0.5 < _EP[j, 1] - p_[1] < 3.5]
    return any(abs(_EN[a_] @ _EN[b_]) < 0.94 for a_ in ii for b_ in ii)
# paredes (de doble cara)
for t3, nn in zip(T[pared], n[pared]):
    h_ = np.array([-nn[2], 0, nn[0]]); h_ /= np.linalg.norm(h_) + 1e-12
    pr = t3 @ h_; A_, B_ = t3[pr.argmin()], t3[pr.argmax()]
    if pr.max() - pr.min() < 0.03: continue
    ya, yb = t3[:, 1].min(), t3[:, 1].min() + ALTO + 0.15          # de su base hasta el techo
    p = [np.array([A_[0], ya, A_[2]]), np.array([B_[0], ya, B_[2]]), np.array([B_[0], yb, B_[2]]), np.array([A_[0], yb, A_[2]])]
    if not CUEVA:
        quad(TEX['pared'], p, [[pr.min() / E, ya / E], [pr.max() / E, ya / E], [pr.max() / E, yb / E], [pr.min() / E, yb / E]]); continue
    nh = np.array([nn[0], 0, nn[2]]); nh /= np.linalg.norm(nh) + 1e-12
    cen_c = t3.mean(0) + nh * 0.3; hs_ = heights(TF, cen_c[0], cen_c[2])
    if not (len(hs_) and np.abs(hs_ - t3[:, 1].min()).min() < 0.6): nh = -nh          # la normal apunta al paso
    nu_ = max(1, int(np.ceil((pr.max() - pr.min()) / 0.35))); nv_ = max(2, int(np.ceil((yb - ya) / 0.35)))
    G = np.zeros((nv_ + 1, nu_ + 1, 3)); UV = np.zeros((nv_ + 1, nu_ + 1, 2))
    LL = pr.max() - pr.min(); eA = _es_esquina(A_); eB = _es_esquina(B_)
    for j in range(nv_ + 1):
        for i in range(nu_ + 1):
            u = i / nu_; v = j / nv_; q = A_ + (B_ - A_) * u
            pu = pr.min() + (pr.max() - pr.min()) * u; ys_ = []
            for e0, e1 in ((t3[0], t3[1]), (t3[1], t3[2]), (t3[2], t3[0])):
                a0, a1 = e0 @ h_, e1 @ h_
                if min(a0, a1) - 1e-6 <= pu <= max(a0, a1) + 1e-6 and abs(a1 - a0) > 1e-6: ys_.append(e0[1] + (e1[1] - e0[1]) * (pu - a0) / (a1 - a0))
            yf = min(ys_) if ys_ else ya                                       # suelo bajo esta columna (rampas)
            ytop = _y_techo(q[0] + nh[0] * 0.05, q[2] + nh[2] * 0.05, yf)      # la misma bóveda que el techo
            q = np.array([q[0], yf + (ytop - yf) * v, q[2]])
            d = 0.12 + 0.16 * _ruido(q) + 0.05 * _ruido(q, 4.0, 1.0)
            d *= min(1.0, 0.35 + v * 1.6) * min(1.0, (1 - v) * 4.0)          # pegado al suelo abajo y al borde de la bóveda arriba
            if eA: d *= min(1.0, u * LL / 0.45)
            if eB: d *= min(1.0, (1 - u) * LL / 0.45)
            G[j, i] = q - nh * max(d, 0.0) + np.array([0, 0.05 * _ruido(q, 3.0, 2.0) * (0 < j < nv_), 0])
            UV[j, i] = [(pr.min() + (pr.max() - pr.min()) * u) / E, q[1] / E]
    for j in range(nv_):
        for i in range(nu_):
            quad(TEX['pared'], [G[j, i], G[j, i + 1], G[j + 1, i + 1], G[j + 1, i]], [UV[j, i], UV[j, i + 1], UV[j + 1, i + 1], UV[j + 1, i]])
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
        for k in lst:
            tri(TEX['suelo'], T[k], T[k][:, [0, 2]] / E)
            if techo_libre(T[k].mean(0)):
                if CUEVA: _techo_cueva(T[k])
                else: q = T[k].copy(); q[:, 1] += ALTO; tri(TEX['techo'], q, q[:, [0, 2]] / E)
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
        if techo_libre(c):
            if CUEVA: _techo_cueva(T[k])
            else: q = T[k].copy(); q[:, 1] += ALTO; tri(TEX['techo'], q, q[:, [0, 2]] / E)
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
