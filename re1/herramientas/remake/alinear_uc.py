"""Alinea una sala de UC (modelo 3D real) con la misma sala del REmake (malla detallada, mm).
Busca giro en Y (y espejo si hace falta), escala y traslación por ICP. Escribe la transformación en json.
uso: alinear_uc.py uc_sala.obj st rNNN salida.json"""
import os
import sys, json
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, '/home/claude/re1gc/work'); import remake
def muestras_obj(path, n=60000):
    V = []; F = []
    for l in open(path):
        if l.startswith('# envolvente'): break
        if l.startswith('v '): V.append([float(x) for x in l.split()[1:4]])
        elif l.startswith('f '): F.append([int(t.split('/')[0]) - 1 for t in l.split()[1:4]])
    V = np.array(V); F = np.array(F)
    return muestrear(V, F, n)
def muestrear(V, F, n):
    T = V[F]; a = np.linalg.norm(np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]), axis=1) / 2
    p = a / a.sum(); idx = np.random.default_rng(0).choice(len(F), n, p=p)
    r1 = np.random.default_rng(1).random((n, 2)); s = np.sqrt(r1[:, 0])
    w = np.stack([1 - s, s * (1 - r1[:, 1]), s * r1[:, 1]], 1)
    return (T[idx] * w[:, :, None]).sum(1)
def rot(t, esp):
    c, s = np.cos(t), np.sin(t); R = np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
    return R @ np.diag([-1 if esp else 1, 1, 1])
def icp(A, B, R, s, t, it=40):
    tree = cKDTree(B)
    for k in range(it):
        X = (A @ R.T) * s + t
        d, j = tree.query(X)
        lim = np.percentile(d, 80); m = d < lim
        P = A[m]; Q = B[j[m]]
        # solo giro en Y: resolver en XZ (Procrustes 2D con espejo fijo) + escala + traslación
        Pr = P @ R0_esp.T
        mp, mq = Pr.mean(0), Q.mean(0)
        P2, Q2 = Pr[:, [0, 2]] - mp[[0, 2]], Q[:, [0, 2]] - mq[[0, 2]]
        H = P2.T @ Q2; U, S, Vt = np.linalg.svd(H); Rm = (U @ Vt).T
        if np.linalg.det(Rm) < 0: Vt[-1] *= -1; Rm = (U @ Vt).T
        ang = np.arctan2(Rm[0, 1], Rm[0, 0])
        R = rot(-ang, False) @ R0_esp
        Pr2 = P @ R.T
        s = float(np.sum((Q - mq) * (Pr2 - Pr2.mean(0))) / np.sum((Pr2 - Pr2.mean(0)) ** 2))
        s = float(np.clip(s, 0.7, 1.4)) if not os.environ.get("ESCALA") else float(os.environ["ESCALA"])
        t = mq - s * Pr2.mean(0)
    X = (A @ R.T) * s + t; d, _ = tree.query(X)
    return R, s, t, float(np.median(d)), float(np.mean(d < 0.15))
if __name__ == '__main__':
    ucobj, st, r, out = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4]
    A = muestras_obj(ucobj)
    V, T, _ = remake.malla(st, r, 1); B = muestrear(np.asarray(V, float) / 1000, np.asarray(T)[:, :3], 60000)
    mejor = None
    for esp in (False, True):
        for k in range(8):
            R0_esp = rot(k * np.pi / 4, esp)
            R = R0_esp; s = 1.0
            t = np.median(B, 0) - np.median(A @ R.T, 0)
            R, s, t, med, frac = icp(A, B, R, s, t)
            print(f'espejo {esp} giro {k*45:3d}: escala {s:.3f} mediana {med:.3f} m, cerca {frac*100:.0f} %')
            if mejor is None or frac > mejor[4]: mejor = (R, s, t, med, frac, esp)
    R, s, t, med, frac, esp = mejor
    json.dump(dict(R=R.tolist(), s=s, t=t.tolist(), mediana=med, cerca=frac, espejo=esp), open(out, 'w'), indent=1)
    print('mejor:', dict(escala=round(s, 3), mediana=round(med, 3), cerca=round(frac, 3), espejo=esp))
