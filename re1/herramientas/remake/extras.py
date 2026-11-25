"""Piezas hechas a mano para completar salas: balaustres torneados bajo pasamanos que no los tienen y columnas
torneadas. Devuelven vértices, UV y triángulos para añadir a la malla de la sala (metros, coordenadas del REmake)."""
import numpy as np
from scipy.spatial import cKDTree

PERFIL_BALAUSTRE = [(0.00, 0.040), (0.06, 0.045), (0.10, 0.030), (0.16, 0.028), (0.30, 0.055), (0.42, 0.058),
                    (0.55, 0.030), (0.70, 0.026), (0.82, 0.034), (0.90, 0.044), (0.95, 0.040), (1.00, 0.040)]
PERFIL_BALAUSTRE_LIGERO = [(0.00, 0.042), (0.12, 0.030), (0.40, 0.058), (0.75, 0.026), (1.00, 0.040)]
PERFIL_COLUMNA = [(0.00, 1.25), (0.04, 1.25), (0.05, 1.10), (0.09, 1.10), (0.10, 1.00), (0.12, 0.95), (0.85, 0.85),
                  (0.88, 0.95), (0.90, 0.95), (0.92, 1.05), (0.96, 1.20), (1.00, 1.25)]

def torneado(base, alto, perfil, escala_r=1.0, lados=10, uv_vueltas=1.0, uv_alto=1.0):
    """pieza de revolución: base (x,y,z) del eje, alto en m; perfil [(h 0..1, radio m)]"""
    V = []; T = []; F = []
    ang = np.linspace(0, 2 * np.pi, lados + 1)
    for h, rr in perfil:
        for a in ang:
            V.append([base[0] + np.cos(a) * rr * escala_r, base[1] + h * alto, base[2] + np.sin(a) * rr * escala_r])
            T.append([a / (2 * np.pi) * uv_vueltas, h * uv_alto])
    n = lados + 1
    for i in range(len(perfil) - 1):
        for j in range(lados):
            a, b, c, d = i * n + j, i * n + j + 1, (i + 1) * n + j + 1, (i + 1) * n + j
            F.append([a, c, b]); F.append([a, d, c])
    return np.array(V), np.array(T), np.array(F)

def rieles(P, radio=0.35):
    """agrupa centros de triángulos de pasamanos en barandillas separadas"""
    t = cKDTree(P); pares = t.query_pairs(radio, output_type='ndarray')
    import scipy.sparse as sp
    from scipy.sparse.csgraph import connected_components
    n = len(P); A = sp.coo_matrix((np.ones(len(pares)), (pares[:, 0], pares[:, 1])), shape=(n, n)) if len(pares) else sp.coo_matrix((n, n))
    k, lab = connected_components(A, directed=False)
    return [P[lab == i] for i in range(k) if (lab == i).sum() >= 6]

def balaustres(P_riel, alturas_suelo, hay_algo, paso=0.16, grosor_riel=0.09):
    """P_riel: puntos del pasamanos (centros). Recorre el riel por su eje principal y pone un balaustre cada `paso`
    donde no hay nada debajo (hay_algo(x,y0,y1,z) -> bool). alturas_suelo(x,z,ymax) -> altura del suelo o None."""
    c = P_riel.mean(0); X = P_riel - c
    u, s, vt = np.linalg.svd(X, full_matrices=False); eje = vt[0]
    t = X @ eje; t0, t1 = t.min() + 0.12, t.max() - 0.12
    piezas = []; razones = {}
    if t1 - t0 < 0.3: return piezas
    arbol = cKDTree(P_riel)
    for tt in np.arange(t0, t1, paso):
        p = c + eje * tt
        # altura del pasamanos en ese punto: la más baja de los puntos cercanos
        idx = arbol.query_ball_point(p, 0.25)
        if not idx: continue
        ytop = P_riel[idx, 1].min() - grosor_riel / 2
        yb = alturas_suelo(p[0], p[2], ytop - 0.2)
        if yb is None: razones['sin suelo'] = razones.get('sin suelo', 0) + 1; continue
        h = ytop - yb
        if h < 0.35 or h > 1.3: razones['alto'] = razones.get('alto', 0) + 1; continue
        if hay_algo(p[0], yb + 0.15 * h, yb + 0.85 * h, p[2]): razones['ya hay'] = razones.get('ya hay', 0) + 1; continue
        piezas.append(((p[0], yb, p[2]), h))
    if razones: print('    riel', np.round(c, 1), 'descartes', razones, 'puestos', len(piezas))
    return piezas

def balaustres_escalera(Tc, nc, P_riel, hay_algo, paso=0.16):
    """balaustres en los bordes de las rampas de escalera de la colisión, hasta el pasamanos que haya encima"""
    from collections import defaultdict
    ramp = np.nonzero((nc[:, 1] > 0.45) & (nc[:, 1] < 0.97))[0]
    if not len(ramp) or not len(P_riel): return []
    key = lambda p: tuple(np.round(p, 3))
    cuenta = defaultdict(list)
    piso = np.nonzero(nc[:, 1] > 0.45)[0]
    for i in piso:
        t = Tc[i]
        for a, b in ((0, 1), (1, 2), (2, 0)):
            cuenta[tuple(sorted((key(t[a]), key(t[b]))))].append(i)
    arbol = cKDTree(P_riel[:, [0, 2]]); out = []
    for (pa, pb), ts in cuenta.items():
        if len(ts) != 1 or ts[0] not in set(ramp): continue
        a, b = np.array(pa), np.array(pb); L = np.linalg.norm((b - a)[[0, 2]])
        if L < 0.3: continue
        cen = Tc[ts[0]].mean(0)
        for s in np.arange(paso / 2, L, paso):
            p = a + (b - a) * (s / L)
            dentro = cen - p; dentro[1] = 0; dentro /= np.linalg.norm(dentro) + 1e-9
            q = p + dentro * 0.07
            idx = arbol.query_ball_point(q[[0, 2]], 0.3)
            ys = [P_riel[j, 1] for j in idx if 0.5 < P_riel[j, 1] - q[1] < 1.4]
            if not ys: continue
            h = min(ys) - 0.05 - q[1]
            if h < 0.4: continue
            if hay_algo(q[0], q[1] + 0.15 * h, q[1] + 0.85 * h, q[2]): continue
            out.append(((q[0], q[1], q[2]), h))
    return out

def viga(a, b, ancho=0.09, alto=0.07):
    """caja alargada de a a b (pasamanos), con UV a lo largo"""
    a = np.asarray(a, float); b = np.asarray(b, float); d = b - a; L = np.linalg.norm(d)
    if L < 1e-6: return np.zeros((0, 3)), np.zeros((0, 2)), np.zeros((0, 3), int)
    u = d / L; lado = np.cross(u, [0, 1, 0]); lado /= np.linalg.norm(lado) + 1e-12; arriba = np.cross(lado, u)
    esq = [(-1, -1), (1, -1), (1, 1), (-1, 1)]
    V = []; T = []; F = []
    for k, (sx, sy) in enumerate(esq):
        for p, t in ((a, 0.0), (b, L)):
            V.append(p + lado * sx * ancho / 2 + arriba * sy * alto / 2); T.append([t, k * 0.25])
    for k in range(4):
        i0, i1 = 2 * k, 2 * ((k + 1) % 4)
        F.append([i0, i0 + 1, i1 + 1]); F.append([i0, i1 + 1, i1])
    F += [[0, 2, 4], [0, 4, 6], [1, 5, 3], [1, 7, 5]]
    return np.array(V), np.array(T), np.array(F)

def barandilla_rampas(Tc, nc, es_pared, paso=0.20, alto=0.95, radio_llano=1.5, alturas=None):
    """barandilla completa (tramos de pasamanos + balaustres + postes) en los bordes libres de las rampas de la colisión.
    es_pared(x, y, z) -> True si hay pared de colisión ahí (borde contra pared: sin barandilla)"""
    from collections import defaultdict
    ramp = set(np.nonzero((nc[:, 1] > 0.45) & (nc[:, 1] < 0.97))[0])
    piso = np.nonzero(nc[:, 1] > 0.45)[0]
    key = lambda p: tuple(np.round(p, 3)); cuenta = defaultdict(list)
    for i in piso:
        t = Tc[i]
        for a, b in ((0, 1), (1, 2), (2, 0)): cuenta[tuple(sorted((key(t[a]), key(t[b]))))].append(i)
    vigas = []; bal = []; postes = []
    rc = cKDTree(np.concatenate([Tc[i] for i in ramp])[:, [0, 2]]) if ramp else None
    for (pa, pb), ts in cuenta.items():
        if len(ts) != 1: continue
        a, b = np.array(pa), np.array(pb)
        if ts[0] not in ramp:
            # descansillo llano junto a una rampa: también lleva barandilla en sus bordes libres
            if rc is None or rc.query(((a + b) / 2)[[0, 2]])[0] > radio_llano: continue
        L = np.linalg.norm((b - a)[[0, 2]])
        if L < 0.3: continue
        cen = Tc[ts[0]].mean(0); m = (a + b) / 2
        dentro = cen - m; dentro[1] = 0; dentro /= np.linalg.norm(dentro) + 1e-9
        if es_pared(*(m - dentro * 0.15 + [0, 0.5, 0])): continue
        if alturas is not None:
            n_peg = 0
            for q in (a, m, b, a * 0.75 + b * 0.25, a * 0.25 + b * 0.75):
                fuera = q - dentro * 0.1; hs = alturas(fuera[0], fuera[2])
                if len(hs) and np.abs(hs - q[1]).min() < 0.15: n_peg += 1
            if n_peg >= 4: continue      # al otro lado hay suelo a su altura (unión rampa-suelo): no es un borde libre
        a2 = a + dentro * 0.06; b2 = b + dentro * 0.06
        vigas.append((a2 + [0, alto, 0], b2 + [0, alto, 0]))
        for s in np.arange(paso / 2, L, paso):
            p = a2 + (b2 - a2) * (s / L); bal.append((tuple(p), alto - 0.035))
        postes += [tuple(a2), tuple(b2)]
    # postes: quitar repetidos
    uniq = []
    for p in postes:
        if not any(np.linalg.norm(np.subtract(p, q)) < 0.1 for q in uniq): uniq.append(p)
    return vigas, bal, uniq

def _rot_eje(V, eje, ang, centro):
    eje = np.asarray(eje, float); eje /= np.linalg.norm(eje)
    K = np.array([[0, -eje[2], eje[1]], [eje[2], 0, -eje[0]], [-eje[1], eje[0], 0]])
    R = np.eye(3) + np.sin(ang) * K + (1 - np.cos(ang)) * K @ K
    return (V - centro) @ R.T + centro

def tubo(a, b, r0, r1, lados=10):
    """cilindro cónico de a a b"""
    a = np.asarray(a, float); b = np.asarray(b, float); L = np.linalg.norm(b - a)
    V, T, F = torneado((0, 0, 0), L, [(0.0, r0 * 0.6), (0.05, r0), (0.95, r1), (1.0, r1 * 0.6)], lados=lados)
    d = (b - a) / L; y = np.array([0, 1.0, 0]); ax = np.cross(y, d)
    if np.linalg.norm(ax) > 1e-6: V = _rot_eje(V, ax, np.arccos(np.clip(d @ y, -1, 1)), np.zeros(3))
    elif d[1] < 0: V = V * [1, -1, 1]
    return V + a, T, F

def estatua(base, alto=1.15, giro=0.0):
    """figura clásica de mármol con un cántaro al hombro, de piezas torneadas (base = centro de la peana, arriba)"""
    s = alto / 1.15; piezas = []
    bx, by, bz = base
    def add(p): piezas.append(p)
    # túnica (de los pies a la cintura), algo aplanada
    V, T, F = torneado((0, 0, 0), 0.62 * s, [(0, 0.20), (0.05, 0.21), (0.35, 0.17), (0.7, 0.14), (1.0, 0.12)], lados=16); V[:, 2] *= 0.75; add((V, T, F))
    # torso
    V, T, F = torneado((0, 0.60 * s, 0), 0.34 * s, [(0, 0.12), (0.3, 0.125), (0.6, 0.135), (0.85, 0.14), (1.0, 0.07)], lados=16); V[:, 2] *= 0.7; add((V, T, F))
    # cuello y cabeza
    add(tubo((0, 0.92 * s, 0), (0, 1.0 * s, 0.01), 0.045 * s, 0.04 * s))
    V, T, F = torneado((0, 0.98 * s, 0.01), 0.18 * s, [(0, 0.03), (0.15, 0.065), (0.45, 0.08), (0.75, 0.072), (0.95, 0.04), (1.0, 0.0)], lados=14); add((V, T, F))
    # brazos: el derecho sube a sujetar el cántaro, el izquierdo baja
    add(tubo((0.15 * s, 0.90 * s, 0), (0.22 * s, 1.08 * s, 0.02), 0.042 * s, 0.035 * s))
    add(tubo((0.22 * s, 1.08 * s, 0.02), (0.16 * s, 1.22 * s, 0.0), 0.035 * s, 0.03 * s))
    add(tubo((-0.15 * s, 0.90 * s, 0), (-0.19 * s, 0.68 * s, 0.03), 0.042 * s, 0.036 * s))
    add(tubo((-0.19 * s, 0.68 * s, 0.03), (-0.13 * s, 0.50 * s, 0.08), 0.036 * s, 0.03 * s))
    # cántaro sobre el hombro derecho, inclinado
    V, T, F = torneado((0, 0, 0), 0.30 * s, [(0, 0.04), (0.08, 0.07), (0.35, 0.11), (0.6, 0.10), (0.8, 0.05), (0.9, 0.04), (1.0, 0.06)], lados=14)
    V = _rot_eje(V, (0, 0, 1), -0.9, np.zeros(3)) + [0.16 * s, 1.02 * s, 0.0]; add((V, T, F))
    Vs = []; Ts = []; Fs = []; b0 = 0
    for V, T, F in piezas: Vs.append(V); Ts.append(T); Fs.append(F + b0); b0 += len(V)
    V = np.concatenate(Vs); T = np.concatenate(Ts); F = np.concatenate(Fs)
    V = _rot_eje(V, (0, 1, 0), giro, np.zeros(3)) + [bx, by, bz]
    return V, T, F

def torneado2(base, alto, perfil, lados=16, ondas=0, amp=0.0, esc=(1.0, 1.0)):
    """como torneado, con pliegues (ondas en el radio) y sección elíptica"""
    V = []; T = []; F = []
    ang = np.linspace(0, 2 * np.pi, lados + 1)
    for h, rr in perfil:
        for a in ang:
            r_ = rr * (1 + amp * np.sin(ondas * a) * (1 - h)) if ondas else rr
            V.append([base[0] + np.cos(a) * r_ * esc[0], base[1] + h * alto, base[2] + np.sin(a) * r_ * esc[1]])
            T.append([a / (2 * np.pi), h])
    n = lados + 1
    for i in range(len(perfil) - 1):
        for j in range(lados):
            a, b, c, d = i * n + j, i * n + j + 1, (i + 1) * n + j + 1, (i + 1) * n + j
            F.append([a, c, b]); F.append([a, d, c])
    return np.array(V), np.array(T), np.array(F)

def esfera(c, r, lados=12, esc=(1, 1, 1)):
    pf = [(k / 8, np.sin(np.pi * k / 8) * r) for k in range(9)]
    V, T, F = torneado((0, 0, 0), 2 * r, pf, lados=lados)
    V = V - [0, r, 0]; V = V * esc + c
    return V, T, F

def estatua_busto(base, alto=1.1, giro=0.0):
    """busto femenino clásico de cintura para arriba con un cántaro grande al hombro derecho (como la del REmake)"""
    s = alto / 1.1; P = []
    # caderas cubiertas por una tela con pliegues
    P.append(torneado2((0, 0, 0), 0.40 * s, [(0, 0.205), (0.15, 0.21), (0.45, 0.19), (0.75, 0.155), (1.0, 0.125)], lados=24, ondas=9, amp=0.07, esc=(1.0, 0.78)))
    # vuelta de la tela en la cintura
    P.append(torneado2((0, 0.36 * s, 0), 0.06 * s, [(0, 0.13), (0.5, 0.135), (1.0, 0.118)], lados=20, ondas=7, amp=0.05, esc=(1.0, 0.78)))
    # torso desnudo
    P.append(torneado2((0, 0.40 * s, 0), 0.34 * s, [(0, 0.118), (0.25, 0.112), (0.55, 0.128), (0.8, 0.14), (0.92, 0.135), (1.0, 0.07)], lados=20, esc=(1.12, 0.68)))
    # pecho
    for sx in (-1, 1): P.append(esfera((sx * 0.058 * s, 0.62 * s, 0.065 * s), 0.052 * s, esc=(1, 0.9, 0.8)))
    # hombros
    for sx in (-1, 1): P.append(esfera((sx * 0.135 * s, 0.70 * s, 0), 0.055 * s))
    # cuello y cabeza inclinada hacia el cántaro, con moño
    P.append(tubo((0, 0.72 * s, 0), (0.015 * s, 0.81 * s, 0.01 * s), 0.042 * s, 0.038 * s))
    P.append(esfera((0.025 * s, 0.88 * s, 0.015 * s), 0.075 * s, esc=(0.9, 1.1, 1.0)))
    P.append(esfera((0.035 * s, 0.93 * s, -0.045 * s), 0.045 * s))
    P.append(esfera((0.025 * s, 0.845 * s, 0.07 * s), 0.018 * s))        # nariz/barbilla
    # brazo derecho levantado sujetando el cántaro
    P.append(tubo((0.14 * s, 0.70 * s, 0), (0.22 * s, 0.86 * s, -0.02 * s), 0.044 * s, 0.036 * s))
    P.append(esfera((0.22 * s, 0.86 * s, -0.02 * s), 0.037 * s))
    P.append(tubo((0.22 * s, 0.86 * s, -0.02 * s), (0.17 * s, 1.02 * s, -0.05 * s), 0.036 * s, 0.028 * s))
    # brazo izquierdo hacia abajo, la mano en la cadera
    P.append(tubo((-0.14 * s, 0.70 * s, 0), (-0.19 * s, 0.52 * s, 0.01 * s), 0.044 * s, 0.037 * s))
    P.append(esfera((-0.19 * s, 0.52 * s, 0.01 * s), 0.037 * s))
    P.append(tubo((-0.19 * s, 0.52 * s, 0.01 * s), (-0.15 * s, 0.38 * s, 0.07 * s), 0.037 * s, 0.03 * s))
    # cántaro grande y redondo sobre el hombro derecho
    V, T, F = torneado((0, 0, 0), 0.34 * s, [(0, 0.045), (0.06, 0.09), (0.3, 0.15), (0.55, 0.155), (0.78, 0.11), (0.88, 0.05), (0.95, 0.045), (1.0, 0.06)], lados=18)
    V = _rot_eje(V, (0, 0, 1), -1.15, np.zeros(3)) + [0.06 * s, 0.93 * s, -0.08 * s]; P.append((V, T, F))
    Vs = []; Ts = []; Fs = []; b0 = 0
    for V, T, F in P: Vs.append(V); Ts.append(T); Fs.append(F + b0); b0 += len(V)
    V = np.concatenate(Vs); T = np.concatenate(Ts); F = np.concatenate(Fs)
    return _rot_eje(V, (0, 1, 0), giro, np.zeros(3)) + list(base), T, F
