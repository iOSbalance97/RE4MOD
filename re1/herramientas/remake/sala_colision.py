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
def _uv_fix(p, uv):
    # si la proyección de la textura deja el triángulo estirado (p. ej. un tramo vertical del techo con UV en planta), usar la cara dominante
    p = np.array(p, float); uv = np.array(uv, float)
    nn = np.cross(p[1] - p[0], p[2] - p[0]); a3 = np.linalg.norm(nn) / 2
    if a3 < 1e-6: return uv
    t1, t2 = uv[1] - uv[0], uv[2] - uv[0]; auv = abs(t1[0] * t2[1] - t1[1] * t2[0]) / 2
    if auv >= 0.25 * a3 / E ** 2: return uv
    ax = np.argmax(np.abs(nn)); ej = {0: [2, 1], 1: [0, 2], 2: [0, 1]}[ax]
    return p[:, ej] / E
def tri(m, p, uv, dos=True):
    uv = _uv_fix(p, uv)
    geo[m].append((np.array(p, float), np.array(uv, float)))
    if dos: geo[m].append((np.array(p, float)[::-1], np.array(uv, float)[::-1]))
def quad(m, p, uv, dos=True):
    tri(m, [p[0], p[1], p[2]], [uv[0], uv[1], uv[2]], dos); tri(m, [p[0], p[2], p[3]], [uv[0], uv[2], uv[3]], dos)
def techo_libre(c):
    h = heights(TF, c[0], c[2]); return True if CUEVA else not np.any((h > c[1] + 0.5) & (h < c[1] + ALTO + 0.2))
def _y_techo(x, z, yf):
    q0 = np.array([x, 0.0, z]); y = 2.75 + 0.35 * _ruido(q0, 1.3, 3.0) + 0.1 * _ruido(q0, 4.0, 5.0)
    h = heights(TF, x, z); h = h[h > yf + 1.8]          # solo otro tramo de verdad encima (un bloque de 1 m no baja el techo)
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
PAREDES_PLANAS = [[float(v) for v in c_.split(',')] for c_ in os.environ.get('PAREDES_PLANAS', '').split(';') if c_]
CELDAS = []
if CUEVA and os.environ.get('CELDAS'):
    for c_ in os.environ['CELDAS'].split(';'):
        x0_, lado_ = [float(v) for v in c_.split(',')]
        zz_ = [z for z in np.arange(0.3, 4.7, 0.03) if len(heights(TF, x0_, z))]
        cz_, hw_ = (min(zz_) + max(zz_)) / 2, (max(zz_) - min(zz_)) / 2
        y0_ = float(heights(TF, x0_, cz_).min()); CELDAS.append((x0_ - 0.66, x0_ + 0.66, cz_ + lado_ * (hw_ + 0.02), lado_, y0_))
ESQ = []
# paredes (de doble cara). Los triángulos coplanarios que comparten un lado (las dos mitades de un muro sobre una rampa)
# se tratan como un solo muro: el suelo de cada columna es el borde más bajo del conjunto, no la diagonal de cada mitad.
_TP = T[pared]; _NP = n[pared]; _gp = list(range(len(_TP)))
def _raiz(i):
    while _gp[i] != i: _gp[i] = _gp[_gp[i]]; i = _gp[i]
    return i
for i_ in range(len(_TP)):
    for j_ in range(i_ + 1, len(_TP)):
        if _NP[i_] @ _NP[j_] < 0.995 or abs((_TP[j_][0] - _TP[i_][0]) @ _NP[i_]) > 0.03: continue
        dd_ = np.linalg.norm(_TP[i_][:, None] - _TP[j_][None], axis=2)
        _sh = np.nonzero(dd_.min(1) < 0.06)[0]
        if len(_sh) >= 3 or (len(_sh) == 2 and np.hypot(*(_TP[i_][_sh[0]] - _TP[i_][_sh[1]])[[0, 2]]) > 0.1): _gp[_raiz(j_)] = _raiz(i_)     # solo las dos mitades de un muro (lado común no vertical)
_GR = {}
for i_ in range(len(_TP)): _GR.setdefault(_raiz(i_), []).append(i_)
_MUROS = []
for g_, l_ in _GR.items():
    _MUROS.append((np.concatenate([_TP[k] for k in l_]), _NP[g_], [(_TP[k][a_], _TP[k][b_]) for k in l_ for a_, b_ in ((0, 1), (1, 2), (2, 0))]))
print('muros:', len(_MUROS), 'de', len(_TP), 'triángulos de pared')
for t3, nn, _EDG in _MUROS:
    h_ = np.array([-nn[2], 0, nn[0]]); h_ /= np.linalg.norm(h_) + 1e-12
    pr = t3 @ h_; A_, B_ = t3[pr.argmin()], t3[pr.argmax()]
    if pr.max() - pr.min() < 0.03: continue
    ya, yb = t3[:, 1].min(), t3[:, 1].min() + ALTO + 0.15          # de su base hasta el techo
    p = [np.array([A_[0], ya, A_[2]]), np.array([B_[0], ya, B_[2]]), np.array([B_[0], yb, B_[2]]), np.array([A_[0], yb, A_[2]])]
    if not CUEVA:
        quad(TEX['pared'], p, [[pr.min() / E, ya / E], [pr.max() / E, ya / E], [pr.max() / E, yb / E], [pr.min() / E, yb / E]]); continue
    _nh0 = np.array([nn[0], 0, nn[2]]) / (np.hypot(nn[0], nn[2]) + 1e-12); _c0 = t3.mean(0); _amb = 0
    for _sg in (1, -1):
        _q = _c0 + _sg * 0.35 * _nh0; _h = heights(TF, _q[0], _q[2]); _amb += int(np.any((_h > ya - 0.6) & (_h < ya + 0.6)))
    if _amb == 2 and t3[:, 1].max() - ya < 1.3:          # escalón o murete en mitad del paso: solo su altura real
        yt_ = t3[:, 1].max(); p = [np.array([A_[0], ya, A_[2]]), np.array([B_[0], ya, B_[2]]), np.array([B_[0], yt_, B_[2]]), np.array([A_[0], yt_, A_[2]])]
        quad(TEX['tabica'], p, [[pr.min() / E, ya / E], [pr.max() / E, ya / E], [pr.max() / E, yt_ / E], [pr.min() / E, yt_ / E]]); continue
    nh = np.array([nn[0], 0, nn[2]]); nh /= np.linalg.norm(nh) + 1e-12
    _lad = []
    for _sg in (1, -1):
        cen_c = t3.mean(0) * [1, 0, 1] + [0, ya, 0] + _sg * nh * 0.3; hs_ = heights(TF, cen_c[0], cen_c[2])
        _lad.append(bool(len(hs_) and np.abs(hs_ - ya).min() < 0.6))
    _plano = None; _hplano = 99; _sinjamba = False
    for _pp in PAREDES_PLANAS:
        c_ = t3.mean(0)
        if _pp[0] <= c_[0] <= _pp[1] and _pp[2] <= c_[1] <= _pp[3] and _pp[4] <= c_[2] <= _pp[5]: _plano = _pp[6]; _hplano = _pp[7] if len(_pp) > 7 else 99; _sinjamba = len(_pp) > 8 and _pp[8] > 0
    if os.environ.get('DEPURA') and t3[:, 0].mean() < -14.2: print('pared final', np.round(t3.mean(0), 2), _lad, _plano)
    if _lad[1] and not _lad[0]: nh = -nh          # nh apunta al paso
    elif _lad[0] == _lad[1]: _plano = 0.0 if _plano is None else _plano          # dudoso: sin relieve (nunca hacia dentro)
    nu_ = max(1, int(np.ceil((pr.max() - pr.min()) / 0.35))); nv_ = max(2, int(np.ceil((yb - ya) / 0.35)))
    G = np.zeros((nv_ + 1, nu_ + 1, 3)); UV = np.zeros((nv_ + 1, nu_ + 1, 2))
    LL = pr.max() - pr.min(); eA = _es_esquina(A_); eB = _es_esquina(B_)
    if _plano is None:
        if eA: ESQ.append((A_.copy(), -nh.copy(), ya))
        if eB: ESQ.append((B_.copy(), -nh.copy(), ya))
    for j in range(nv_ + 1):
        for i in range(nu_ + 1):
            u = i / nu_; v = j / nv_; q = A_ + (B_ - A_) * u
            pu = pr.min() + (pr.max() - pr.min()) * u; ys_ = []
            for e0, e1 in _EDG:
                a0, a1 = e0 @ h_, e1 @ h_
                if min(a0, a1) - 0.08 <= pu <= max(a0, a1) + 0.08 and abs(a1 - a0) > 0.05:          # tolerancia: el borde de abajo puede acabar unos cm antes que el de arriba
                    pc_ = min(max(pu, min(a0, a1)), max(a0, a1)); ys_.append(e0[1] + (e1[1] - e0[1]) * (pc_ - a0) / (a1 - a0))
            yf = min(ys_) if ys_ else ya                                       # suelo bajo esta columna (rampas)
            ytop = _y_techo(q[0] + nh[0] * 0.05, q[2] + nh[2] * 0.05, yf)      # la misma bóveda que el techo
            q = np.array([q[0], yf + (ytop + 0.22 - yf) * v, q[2]])
            if j == 0: q[1] -= 0.12          # el pie del muro baja un poco por debajo del suelo: sin rendija en la junta          # sube un poco por encima de la bóveda: sin rendija entre muro y techo
            d = 0.12 + 0.16 * _ruido(q) + 0.05 * _ruido(q, 4.0, 1.0)
            d *= min(1.0, v * 2.2) * min(1.0, (1 - v) * 4.0)          # pegado al suelo abajo y al borde de la bóveda arriba
            d *= min(1.0, u * LL / (0.45 if eA else 0.3)) * min(1.0, (1 - u) * LL / (0.45 if eB else 0.3))      # en cada junta el relieve vuelve a la línea del muro: no se abren cuñas
            if _plano is not None: d = _plano if (q[1] - yf) < (_hplano if _plano else 99) else 0.0
            for cl in CELDAS:          # la pared de la celda, plana: la reja queda pegada a ella
                if cl[0] - 0.45 <= q[0] <= cl[1] + 0.45 and abs(q[2] - cl[2]) < 0.6: d = d * min(1.0, max(0.0, max(cl[0] - 0.15 - q[0], q[0] - cl[1] - 0.15) / 0.3))
            G[j, i] = q - nh * max(d, 0.0) + np.array([0, 0.05 * _ruido(q, 3.0, 2.0) * (0 < j < nv_) * (_plano is None), 0])
            UV[j, i] = [(pr.min() + (pr.max() - pr.min()) * u) / E, q[1] / E]
    for j in range(nv_):
        for i in range(nu_):
            cq = (G[j, i] + G[j + 1, i + 1]) / 2
            if any(cl[0] <= cq[0] <= cl[1] and abs(cq[2] - cl[2]) < 0.6 and cq[1] < cl[4] + 2.15 for cl in CELDAS): continue     # hueco de la celda
            quad(TEX['pared'], [G[j, i], G[j, i + 1], G[j + 1, i + 1], G[j + 1, i]], [UV[j, i], UV[j, i + 1], UV[j + 1, i + 1], UV[j + 1, i]])
    if _plano and not _sinjamba:          # jambas del rebaje (detrás de una puerta): cierran los lados entre la pared y el fondo
        for P0 in (A_, B_):
            ytj = ya + _hplano + 0.02
            quad(TEX['pared'], [np.array([P0[0], ya - 0.05, P0[2]]), np.array([P0[0] - nh[0] * _plano, ya - 0.05, P0[2] - nh[2] * _plano]),
                                np.array([P0[0] - nh[0] * _plano, ytj, P0[2] - nh[2] * _plano]), np.array([P0[0], ytj, P0[2]])],
                 [[0, ya / E], [_plano / E, ya / E], [_plano / E, ytj / E], [0, ytj / E]])
        q0, q1 = A_ * [1, 0, 1] + [0, ya + _hplano + 0.02, 0], B_ * [1, 0, 1] + [0, ya + _hplano + 0.02, 0]
        quad(TEX['pared'], [q0, q1, q1 - nh * _plano, q0 - nh * _plano], [[0, 0], [LL / E, 0], [LL / E, _plano / E], [0, _plano / E]])     # dintel
    if _plano: continue          # sin respaldo detrás de un rebaje (taparía la boca)
    # respaldo liso por detrás del relieve: tapa las rendijas entre paredes (sin invadir nunca el paso)
    dh_ = (B_ - A_) * np.array([1, 0, 1]); dh_ /= np.linalg.norm(dh_) + 1e-12; ytb = G[:, :, 1].max() + 0.2
    def _libre(p_):
        h_ = heights(TF, p_[0], p_[2]); return not (len(h_) and np.any(np.abs(h_ - ya) < 1.0))
    _dr = next((d_ for d_ in (0.42, 0.36) if all(_libre(A_ + (B_ - A_) * f_ - nh * d_) for f_ in (0.1, 0.25, 0.5, 0.75, 0.9))), None)
    if _dr is None: continue
    ext_a = max([e for e in (0.0, 0.1, 0.2, 0.3) if _libre(A_ - dh_ * e - nh * _dr)] or [0.0]); ext_b = max([e for e in (0.0, 0.1, 0.2, 0.3) if _libre(B_ + dh_ * e - nh * _dr)] or [0.0])
    if any(not (max(A_[0], B_[0]) < cl[0] - 0.2 or min(A_[0], B_[0]) > cl[1] + 0.2) and abs((A_[2] + B_[2]) / 2 - cl[2]) < 0.8 for cl in CELDAS): continue     # no tapar la celda
    Ab = A_ - dh_ * ext_a - nh * _dr; Bb = B_ + dh_ * ext_b - nh * _dr
    quad(TEX['pared'], [np.array([Ab[0], ya - 0.1, Ab[2]]), np.array([Bb[0], ya - 0.1, Bb[2]]), np.array([Bb[0], ytb, Bb[2]]), np.array([Ab[0], ytb, Ab[2]])],
         [[(pr.min() - 0.5) / E, (ya - 0.1) / E], [(pr.max() + 0.5) / E, (ya - 0.1) / E], [(pr.max() + 0.5) / E, ytb / E], [(pr.min() - 0.5) / E, ytb / E]])
# columnas de roca pedidas a mano (x0,x1,z0,z1,y0,y1): p. ej. sobre un bloque, hasta el techo
for _cs in [c_ for c_ in os.environ.get('COLUMNAS', '').split(';') if c_]:
    x0_, x1_, z0_, z1_, y0_, y1_ = [float(v) for v in _cs.split(',')]
    cx_, cz_ = (x0_ + x1_) / 2, (z0_ + z1_) / 2; rx_, rz_ = (x1_ - x0_) / 2 + 0.03, (z1_ - z0_) / 2 + 0.03
    NL_ = 16; NV_ = max(2, int((y1_ - y0_) / 0.35))
    for k_ in range(NL_):
        for j_ in range(NV_):
            pts_ = []
            for (kk, jj) in ((k_, j_), (k_ + 1, j_), (k_ + 1, j_ + 1), (k_, j_ + 1)):
                th_ = 2 * np.pi * kk / NL_; yy_ = y0_ + (y1_ - y0_) * jj / NV_
                # contorno entre círculo y rectángulo (abarca la base cuadrada) con relieve de roca
                cx2, sz2 = np.cos(th_), np.sin(th_); m_ = max(abs(cx2), abs(sz2))
                q0_ = np.array([cx_ + rx_ * cx2 / m_, yy_, cz_ + rz_ * sz2 / m_])          # contorno rectangular: abarca toda la base (también las esquinas)
                rr_ = 1.0 + 0.06 * abs(_ruido(q0_, 2.5, 7.0))
                pts_.append(np.array([cx_ + (q0_[0] - cx_) * rr_, yy_, cz_ + (q0_[2] - cz_) * rr_]))
            u0_, u1_ = k_ / NL_ * 2.4, (k_ + 1) / NL_ * 2.4; v0_, v1_ = (y0_ + (y1_ - y0_) * j_ / NV_) / E, (y0_ + (y1_ - y0_) * (j_ + 1) / NV_) / E
            quad(TEX['pared'], pts_, [[u0_, v0_], [u1_, v0_], [u1_, v1_], [u0_, v1_]])
    print('columna de roca:', _cs)
# columnas de roca en las esquinas: tapan la rendija que deja el relieve de dos paredes que se juntan
if CUEVA and ESQ:
    usados = np.zeros(len(ESQ), bool); nesq = 0
    for i_, (p_, o_, y_) in enumerate(ESQ):
        if usados[i_]: continue
        grp = [j for j, (q_, _, yq) in enumerate(ESQ) if np.hypot(*(q_ - p_)[[0, 2]]) < 0.15 and abs(yq - y_) < 0.6]
        for j in grp: usados[j] = True
        oo = np.mean([ESQ[j][1] for j in grp], 0)
        if len(grp) < 2 or np.linalg.norm(oo) < 0.2: continue
        oo /= np.linalg.norm(oo); c_ = p_ + oo * 0.2; yb_ = min(ESQ[j][2] for j in grp) - 0.1
        _inv = False
        for k_ in range(12):
            q_ = c_ + 0.27 * np.array([np.cos(k_ * np.pi / 6), 0, np.sin(k_ * np.pi / 6)]); hq = heights(TF, q_[0], q_[2])
            if np.any((hq > yb_ - 0.5) & (hq < yb_ + 2.2)): _inv = True; break
        if _inv: continue          # invadiría el paso (se veía como una pared que sobresale)
        yt_ = _y_techo(p_[0] - oo[0] * 0.1, p_[2] - oo[2] * 0.1, yb_ + 0.1) + 0.15
        L8 = 8; R_ = 0.26
        for k in range(L8):
            a0, a1 = 2 * np.pi * k / L8, 2 * np.pi * (k + 1) / L8
            q = [np.array([c_[0] + R_ * np.cos(a0), yb_, c_[2] + R_ * np.sin(a0)]), np.array([c_[0] + R_ * np.cos(a1), yb_, c_[2] + R_ * np.sin(a1)])]
            q += [q[1] + [0, yt_ - yb_, 0], q[0] + [0, yt_ - yb_, 0]]
            quad(TEX['pared'], q, [[k * 0.2, yb_ / E], [(k + 1) * 0.2, yb_ / E], [(k + 1) * 0.2, yt_ / E], [k * 0.2, yt_ / E]])
        nesq += 1
    print('columnas de esquina:', nesq)
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
        for vv in (v0, v1):          # costados del peldaño hasta el pie del tramo (en la cueva, roca con la UV a lo largo del tramo)
            quad(TEX['pared'] if CUEVA else TEX['tabica'], [pt(ua, vv, y0 - 0.02), pt(ub, vv, y0 - 0.02), pt(ub, vv, yt), pt(ua, vv, yt)],
                 [[ua / E, (y0 - 0.02) / E], [ub / E, (y0 - 0.02) / E], [ub / E, yt / E], [ua / E, yt / E]])
    # techo inclinado sobre el tramo
    for k in lst:
        c = T[k].mean(0)
        if techo_libre(c):
            if CUEVA: _techo_cueva(T[k])
            else: q = T[k].copy(); q[:, 1] += ALTO; tri(TEX['techo'], q, q[:, [0, 2]] / E)
    esc += 1
EXT_MTL = {}
if CUEVA:
    from PIL import Image as _Im
    _im = np.asarray(_Im.open(f'{CAS}/cas_hierro.png').convert('RGB'), np.float32); _im = (_im * 0.35 + _im.mean(2, keepdims=True) * 0.65) * 0.5
    _Im.fromarray(np.clip(_im, 0, 255).astype(np.uint8)).save(f'{out}/cas_hierro.png')
    def _cil(a, b, r, m, lados=6):
        a = np.asarray(a, float); b = np.asarray(b, float); d = b - a; L = np.linalg.norm(d); d /= L
        u = np.cross(d, [0, 1, 0] if abs(d[1]) < 0.9 else [1, 0, 0]); u /= np.linalg.norm(u); w = np.cross(d, u)
        for k in range(lados):
            t0, t1 = 2 * np.pi * k / lados, 2 * np.pi * (k + 1) / lados
            o0 = (u * np.cos(t0) + w * np.sin(t0)) * r; o1 = (u * np.cos(t1) + w * np.sin(t1)) * r
            quad(m, [a + o0, a + o1, b + o1, b + o0], [[k / lados, 0], [(k + 1) / lados, 0], [(k + 1) / lados, L], [k / lados, L]])
    def _centro(x):
        zz = [z for z in np.arange(0.3, 4.7, 0.03) if len(heights(TF, x, z))]
        return ((min(zz) + max(zz)) / 2, (max(zz) - min(zz)) / 2) if zz else (None, None)
    def _suelo(x, z):
        h = heights(TF, x, z); return float(h.min()) if len(h) else None
    nobj = 0
    # rejas (celdas excavadas en la roca) a un lado y otro del túnel
    _Im.fromarray(np.full((8, 8, 3), 6, np.uint8)).save(f'{out}/cas_negro.png')
    _ro = np.asarray(_Im.open(f'{CAS}/{TEX["pared"]}.png').convert('RGB'), np.float32) * 0.22
    _Im.fromarray(np.clip(_ro, 0, 255).astype(np.uint8)).save(f'{out}/cas_roca_celda.png')
    for (xa_, xb_, zw, lado, y0) in CELDAS:
        x0 = (xa_ + xb_) / 2; zf = zw + lado * 1.8; yt_ = y0 + 2.15
        for q_ in ([[xa_, y0, zf], [xb_, y0, zf], [xb_, yt_, zf], [xa_, yt_, zf]], [[xa_, y0, zw], [xa_, y0, zf], [xa_, yt_, zf], [xa_, yt_, zw]],
                   [[xb_, y0, zw], [xb_, y0, zf], [xb_, yt_, zf], [xb_, yt_, zw]], [[xa_, yt_, zw], [xb_, yt_, zw], [xb_, yt_, zf], [xa_, yt_, zf]],
                   [[xa_ - 0.1, y0 - 0.01, zw - lado * 0.12], [xb_ + 0.1, y0 - 0.01, zw - lado * 0.12], [xb_ + 0.1, y0 - 0.01, zf], [xa_ - 0.1, y0 - 0.01, zf]]):
            P4 = [np.array(p_, float) for p_ in q_]; ext_ = [np.ptp([p[c] for p in P4]) for c in (0, 1, 2)]
            quad('cas_roca_celda', P4, [[0, 0], [max(ext_[0], ext_[2]) / E, 0], [max(ext_[0], ext_[2]) / E, max(ext_[1], min(ext_[0], ext_[2])) / E], [0, max(ext_[1], min(ext_[0], ext_[2])) / E]])
        # marco de roca sobre la celda (tapa el canto superior)
        quad(TEX['pared'], [np.array([xa_ - 0.2, yt_, zw]), np.array([xb_ + 0.2, yt_, zw]), np.array([xb_ + 0.2, yt_ + 0.6, zw + lado * 0.15]), np.array([xa_ - 0.2, yt_ + 0.6, zw + lado * 0.15])],
             [[(xa_ - 0.2) / E, yt_ / E], [(xb_ + 0.2) / E, yt_ / E], [(xb_ + 0.2) / E, (yt_ + 0.6) / E], [(xa_ - 0.2) / E, (yt_ + 0.6) / E]])
        for xb in np.arange(x0 - 0.6, x0 + 0.61, 0.13): _cil([xb, y0 - 0.02, zw], [xb, y0 + 2.05, zw], 0.014, 'cas_hierro')
        for yy in (y0 + 0.12, y0 + 1.0, y0 + 1.95): _cil([x0 - 0.66, yy, zw], [x0 + 0.66, yy, zw], 0.022, 'cas_hierro', lados=4)
        for xb in (x0 - 0.66, x0 + 0.66): _cil([xb, y0 - 0.02, zw], [xb, y0 + 2.1, zw], 0.035, 'cas_hierro', lados=6)
        nobj += 1
    # cadenas colgando del techo
    for x0, dz, L in ((-5.4, 0.35, 1.1), (-8.6, -0.4, 0.8), (-9.3, 0.3, 1.3), (-13.4, -0.25, 0.9)):
        c, hw = _centro(x0)
        if c is None: continue
        z0 = c + dz; yf = _suelo(x0, z0) or 0.0; yt = _y_techo(x0, z0, yf) + 0.05
        y = yt; k = 0
        while y > yt - L:
            ang = (k % 2) * np.pi / 2; e = 0.03 * np.array([np.cos(ang), 0, np.sin(ang)])
            pa = np.array([x0, y, z0]); pb = np.array([x0, y - 0.075, z0])
            _cil(pa + e, pb + e, 0.008, 'cas_hierro', lados=4); _cil(pa - e, pb - e, 0.008, 'cas_hierro', lados=4)
            _cil(pa + e, pa - e, 0.008, 'cas_hierro', lados=4); _cil(pb + e, pb - e, 0.008, 'cas_hierro', lados=4)
            y -= 0.06; k += 1
        nobj += 1
    # grilletes en la pared: argolla y cadena corta
    # boca de piedra al final del túnel: arco de dovelas y escalones que bajan a oscuras (la siguiente sala está en otro nivel)
    if os.environ.get('PORTAL'):
        px_, = [float(v) for v in os.environ['PORTAL'].split(',')]
        wz = [t3 for t3, nn in zip(T[pared], n[pared]) if abs(nn[0]) > 0.9 and abs(t3[:, 0].mean() - px_) < 0.25]
        if wz:
            zs_ = np.concatenate([t3[:, 2] for t3 in wz]); za_, zb_ = zs_.min(), zs_.max(); zc_ = (za_ + zb_) / 2; hw_ = (zb_ - za_) / 2
            yf_ = float(heights(TF, px_ + 0.4, zc_).min()); D_ = float(os.environ.get('PORTAL_FONDO', 3.2)); N_ = 12
            from PIL import Image as _Im2
            def _oscura(t_, f_):
                nm_ = f'{t_}_f{int(f_ * 100):02d}'
                if not os.path.exists(f'{out}/{nm_}.png'):
                    a_ = np.asarray(_Im2.open(f'{CAS}/{t_}.png').convert('RGB'), np.float32) * float(os.environ.get('OSCURO', 0.72)) * f_
                    _Im2.fromarray(np.clip(a_, 0, 255).astype(np.uint8)).save(f'{out}/{nm_}.png')
                return nm_
            for k in range(N_):                    # escalones que bajan y se pierden en la oscuridad, con paredes y techo
                f_ = max(0.04, (1 - k / (N_ - 1)) ** 1.6); xa_, xb_ = px_ - k * D_ / N_, px_ - (k + 1) * D_ / N_; yy = yf_ - 0.17 * (k + 1)
                th_, tt_, tp_, tc_ = _oscura(TEX['huella'], f_), _oscura(TEX['tabica'], f_), _oscura(TEX['pared'], f_), _oscura(TEX['techo'], f_)
                quad(th_, [np.array([xa_, yy, za_]), np.array([xb_, yy, za_]), np.array([xb_, yy, zb_]), np.array([xa_, yy, zb_])], [[xa_ / E, za_ / E], [xb_ / E, za_ / E], [xb_ / E, zb_ / E], [xa_ / E, zb_ / E]])
                quad(tt_, [np.array([xa_, yy, za_]), np.array([xa_, yy + 0.17, za_]), np.array([xa_, yy + 0.17, zb_]), np.array([xa_, yy, zb_])], [[za_ / E, yy / E], [za_ / E, (yy + 0.17) / E], [zb_ / E, (yy + 0.17) / E], [zb_ / E, yy / E]])
                yt_ = yy + 2.45
                for zz in (za_, zb_):
                    quad(tp_, [np.array([xa_, yy - 0.2, zz]), np.array([xb_, yy - 0.2, zz]), np.array([xb_, yt_ + 0.2, zz]), np.array([xa_, yt_ + 0.2, zz])], [[xa_ / E, (yy - 0.2) / E], [xb_ / E, (yy - 0.2) / E], [xb_ / E, (yt_ + 0.2) / E], [xa_ / E, (yt_ + 0.2) / E]])
                quad(tc_, [np.array([xa_, yt_ + 0.17, za_]), np.array([xb_, yt_, za_]), np.array([xb_, yt_, zb_]), np.array([xa_, yt_ + 0.17, zb_])], [[xa_ / E, za_ / E], [xb_ / E, za_ / E], [xb_ / E, zb_ / E], [xa_ / E, zb_ / E]])
            quad('cas_negro', [np.array([px_ - D_ + 0.01, yf_ - 2.6, za_]), np.array([px_ - D_ + 0.01, yf_ - 2.6, zb_]), np.array([px_ - D_ + 0.01, yf_ + 0.6, zb_]), np.array([px_ - D_ + 0.01, yf_ + 0.6, za_])], [[0, 0], [1, 0], [1, 1], [0, 1]])
            # arco de dovelas de piedra delante de la boca
            R_ = hw_ + 0.05; yc_ = yf_ + 2.35 - R_; nd_ = 9
            for k in range(12):                    # enjutas: tapan las esquinas del hueco por encima del arco
                a0, a1 = np.pi * k / 12, np.pi * (k + 1) / 12
                p0 = np.array([px_ + 0.01, yc_ + R_ * np.sin(a0), zc_ + R_ * np.cos(a0)]); p1 = np.array([px_ + 0.01, yc_ + R_ * np.sin(a1), zc_ + R_ * np.cos(a1)])
                quad(TEX['pared'], [p0, p1, np.array([p1[0], yf_ + 2.45, p1[2]]), np.array([p0[0], yf_ + 2.45, p0[2]])], [[p0[2] / E, p0[1] / E], [p1[2] / E, p1[1] / E], [p1[2] / E, (yf_ + 2.45) / E], [p0[2] / E, (yf_ + 2.45) / E]])
            for k in range(nd_):
                a0, a1 = np.pi * k / nd_, np.pi * (k + 1) / nd_
                for r0, r1 in ((R_, R_ + 0.28),):
                    pts = [np.array([px_ + 0.02, yc_ + r * np.sin(a), zc_ + r * np.cos(a)]) for r, a in ((r0, a0), (r1, a0), (r1, a1), (r0, a1))]
                    quad(TEX['huella'], pts, [[0, 0], [0.3, 0], [0.3, 0.3], [0, 0.3]])
                    for p0, p1 in ((pts[0], pts[3]), (pts[1], pts[2])):          # canto de la dovela
                        quad(TEX['huella'], [p0, p1, p1 - [0.25, 0, 0], p0 - [0.25, 0, 0]], [[0, 0], [0.3, 0], [0.3, 0.2], [0, 0.2]])
            for zz in (zc_ - R_ - 0.14, zc_ + R_ + 0.14):          # pilastras del arco
                caja_ = [np.array([px_ + 0.03, yf_, zz - 0.14]), np.array([px_ + 0.03, yf_, zz + 0.14]), np.array([px_ + 0.03, yc_, zz + 0.14]), np.array([px_ + 0.03, yc_, zz - 0.14])]
                quad(TEX['huella'], caja_, [[0, 0], [0.3, 0], [0.3, (yc_ - yf_) / E], [0, (yc_ - yf_) / E]])
            print('boca de piedra al final del túnel, ancho %.2f' % (2 * hw_))
    print(f'objetos de la cueva: {nobj}')
# geometría extra con los materiales de la propia sala (respaldos detrás de rendijas): sin copiar ni oscurecer texturas
for _gx in [e for e in os.environ.get('GEO_EXTRA', '').split(';') if e and os.path.exists(e)]:
    _V = []; _T = []; _m = None
    for l in open(_gx):
        if l.startswith('v '): _V.append([float(x) for x in l.split()[1:4]])
        elif l.startswith('vt '): _T.append([float(x) for x in l.split()[1:3]])
        elif l.startswith('usemtl'): _m = l.split()[1]
        elif l.startswith('f '):
            q_ = [x.split('/') for x in l.split()[1:4]]
            tri(_m, [_V[int(a_[0]) - 1] for a_ in q_], [_T[int(a_[1]) - 1] for a_ in q_], dos=False)
    print('geometría extra:', _gx)
for _ex in [e for e in os.environ.get('MODELOS_EXTRA', '').split(';') if e]:
    _d = os.path.dirname(_ex); _mt = {}; _m = None
    for l in open(os.path.join(_d, os.path.basename(_ex)[:-4] + '.mtl')):
        if l.startswith('newmtl'): _m = l.split()[1]
        elif l.startswith('map_Kd'): _mt[_m] = l.split()[1]
    from PIL import Image as _Im
    for _m, _t in _mt.items():
        _im = np.asarray(_Im.open(os.path.join(_d, _t)).convert('RGBA'), np.float32); _im[..., :3] *= float(os.environ.get('OSCURO_EXTRA', 0.6))
        _Im.fromarray(np.clip(_im, 0, 255).astype(np.uint8), 'RGBA').save(f'{out}/{_m}.png')
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
shutil.copy(col, f'{out}/colision.obj')
print(f'{r}: {sum(len(l) for l in geo.values())} triángulos, {esc} tramos de escalera')
