"""Empareja cada sala de UC con la sala del REmake que representa (alineando por ICP contra las candidatas de tamaño parecido)."""
import sys, os, json, glob, numpy as np
sys.path.insert(0, '/home/claude/re1gc/work'); import remake, alinear_uc as AU
from scipy.spatial import cKDTree
REM = {}
for st in range(1, 6):
    for f in sorted(os.listdir(f'/home/claude/re1gc/files/st{st}')):
        if f.endswith('.dat'):
            r = f[:4]; V, T, _ = remake.malla(st, r, 1); V = np.asarray(V, float) / 1000
            REM[r] = (st, V, np.asarray(T)[:, :3])
def dims(P):
    e = np.percentile(P, 98, 0) - np.percentile(P, 2, 0); xz = sorted([e[0], e[2]]); return np.array([xz[0], xz[1], e[1]])
dR = {r: dims(AU.muestrear(V, T, 8000)) for r, (st, V, T) in REM.items()}
res = {}
for obj in sorted(glob.glob('/home/claude/uc/m/r1*/sala.obj')):
    u = obj.split('/')[-2]
    A = AU.muestras_obj(obj, 30000); du = dims(A)
    cand = sorted(dR, key=lambda r: np.abs(np.log(np.maximum(dR[r], 0.5) / np.maximum(du, 0.5))).sum())[:6]
    mejor = None
    for r in cand:
        st, V, T = REM[r]; B = AU.muestrear(V, T, 30000)
        for esp in (False,):
            for k in range(4):
                AU.R0_esp = AU.rot(k * np.pi / 2, esp)
                t = np.median(B, 0) - np.median(A @ AU.R0_esp.T, 0)
                R, s, t, med, frac = AU.icp(A, B, AU.R0_esp, 1.0, t, it=25)
                # simetría: también lo cerca que queda B de A
                X = (A @ R.T) * s + t; d2, _ = cKDTree(X).query(B); frac2 = float(np.mean(d2 < 0.15))
                sc = min(frac, frac2)
                if mejor is None or sc > mejor[0]: mejor = (sc, r, st, R, s, t, med)
    sc, r, st, R, s, t, med = mejor
    res[u] = dict(remake=r, st=st, puntuacion=sc, R=R.tolist(), s=s, t=t.tolist(), mediana=med)
    print(f'UC {u} -> REmake {r} (st{st})  coincide {sc*100:.0f} %, escala {s:.2f}', flush=True)
json.dump(res, open('/home/claude/re1gc/uc_alin/emparejado.json', 'w'), indent=1)
