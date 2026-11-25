"""buscar_uc2d.py uc.obj st r salida.json : búsqueda gruesa (giro 8x, espejo, traslación) por correlación de mapas de paredes en planta, luego ICP local"""
import sys, os, json, numpy as np, remake
from scipy.signal import fftconvolve
from scipy.spatial import cKDTree
sys.argv_ = sys.argv; import alinear_uc as AL
uc, st, r, out = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4]
A = AL.muestras_obj(uc)
V, T, _ = remake.malla(st, r, 1); B = AL.muestrear(np.asarray(V, float) / 1000, np.asarray(T)[:, :3], 60000)
RES = 0.25
def mapa(P, lo, shape):
    ij = np.floor((P[:, [0, 2]] - lo) / RES).astype(int); ok = (ij >= 0).all(1) & (ij[:, 0] < shape[0]) & (ij[:, 1] < shape[1])
    M = np.zeros(shape); np.add.at(M, (ij[ok, 0], ij[ok, 1]), 1); return np.minimum(M, 3)
loB = B[:, [0, 2]].min(0) - 1; shB = tuple((np.ptp(B[:, [0, 2]], 0) / RES + 8).astype(int))
MB = mapa(B, loB, shB); MB -= MB.mean()
mejor = None
for esp in (False, True):
    for k in range(8):
        R = AL.rot(k * np.pi / 4, esp); Ar = A @ R.T
        loA = Ar[:, [0, 2]].min(0) - 1; shA = tuple((np.ptp(Ar[:, [0, 2]], 0) / RES + 8).astype(int))
        MA = mapa(Ar, loA, shA)
        C = fftconvolve(MA, MB[::-1, ::-1], mode='valid')
        i, j = np.unravel_index(C.argmax(), C.shape); sc = C[i, j]
        t2 = loB - (loA + np.array([i, j]) * RES)
        if mejor is None or sc > mejor[0]: mejor = (sc, esp, k, t2)
sc, esp, k, t2 = mejor
R = AL.rot(k * np.pi / 4, esp); Ar = A @ R.T
ty = np.median(B[:, 1]) - np.median(Ar[:, 1])
# alturas: probar desplazamientos verticales y quedarse con el mejor
t = np.array([t2[0], 0, t2[1]])
# recortar UC a la zona de la sala +3 m
lo = B.min(0) - 3; hi = B.max(0) + 3
best = None
for dy in np.arange(-6, 6.01, 0.25):
    X = Ar + t + [0, dy, 0]; m = np.all((X >= lo) & (X <= hi), 1)
    if m.sum() < 1000: continue
    d, _ = cKDTree(B).query(X[m][::5]); f = np.mean(d < 0.2)
    if best is None or f > best[0]: best = (f, dy)
t[1] = best[1]
X = Ar + t; m = np.all((X >= lo) & (X <= hi), 1)
AL.R0_esp = AL.rot(k * np.pi / 4, esp)
Rf, s, tf, med, frac = AL.icp(A[m], B, R, 1.0, t)
print('mejor:', dict(giro=k * 45, espejo=esp, mediana=round(med, 3), cerca=round(frac, 3)))
json.dump(dict(R=Rf.tolist(), s=s, t=tf.tolist(), mediana=med, cerca=frac, espejo=esp), open(out, 'w'), indent=1)
