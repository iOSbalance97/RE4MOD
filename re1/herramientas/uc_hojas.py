"""Hojas de puerta (texturas *door*) en las salas preparadas (uc/m: metros, marco de UC) y su giro respecto a los ejes.
Las salas de UC están alineadas con X/Z: una hoja que no lo está es una puerta entreabierta."""
import re, sys, json
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, '/home/claude/tools')
import objload

def hojas(r, base='/home/claude/uc/m'):
    V, T, F, M, G, mats = objload.load(f'{base}/{r}/sala.obj')
    M = np.asarray(M, dtype=object)
    tex = np.array([(mats.get(m) or '') for m in M])
    sel = np.array([bool(re.search('door', t, re.I)) and not re.search('nob|huchi|fuchi|waku|kazari|parts|totte|knob|frame', t, re.I) for t in tex])
    idx = np.where(sel)[0]
    if not len(idx): return V, F, []
    cen = V[F[idx, :3]].mean(1)
    tr = cKDTree(cen); lab = -np.ones(len(idx), int); k = 0
    for s in range(len(idx)):
        if lab[s] >= 0: continue
        st = [s]; lab[s] = k
        while st:
            q = st.pop()
            for j in tr.query_ball_point(cen[q], 0.12):
                if lab[j] < 0: lab[j] = k; st.append(j)
        k += 1
    out = []
    for c in range(k):
        tri = idx[lab == c]
        P = V[np.unique(F[tri, :3])]
        h = P[:, 1].max() - P[:, 1].min()
        X = P[:, [0, 2]] - P[:, [0, 2]].mean(0)
        if len(P) < 6: continue
        ev, evec = np.linalg.eigh(X.T @ X)
        ancho = 2 * np.sqrt(ev[1] / len(P)) * 1.73
        if h < 1.5 or ancho < 0.4: continue
        a = np.degrees(np.arctan2(evec[1, 1], evec[0, 1])) % 180     # dirección de la hoja en planta
        desv = min(a % 90, 90 - a % 90)
        out.append(dict(tris=tri, centro=P.mean(0), alto=h, ancho=ancho, ang=a, desv=desv))
    return V, F, out

if __name__ == '__main__':
    for r in sys.argv[1].split(','):
        V, F, H = hojas(r)
        for h in H:
            if h['desv'] > 6: print(f"{r}: hoja en {np.round(h['centro'], 1)} alto {h['alto']:.1f} ancho {h['ancho']:.1f} girada {h['desv']:.0f}°  ({len(h['tris'])} triángulos)")
