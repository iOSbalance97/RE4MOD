"""Piezas hechas a mano para completar salas: balaustres torneados bajo pasamanos que no los tienen y columnas
torneadas. Devuelven vértices, UV y triángulos para añadir a la malla de la sala (metros, coordenadas del REmake)."""
import numpy as np
from scipy.spatial import cKDTree

PERFIL_BALAUSTRE = [(0.00, 0.040), (0.06, 0.045), (0.10, 0.030), (0.16, 0.028), (0.30, 0.055), (0.42, 0.058),
                    (0.55, 0.030), (0.70, 0.026), (0.82, 0.034), (0.90, 0.044), (0.95, 0.040), (1.00, 0.040)]
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
