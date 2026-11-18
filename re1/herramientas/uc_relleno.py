"""Tapa los huecos de puerta que llevan a otra sala (en UC se ve la sala de al lado, aquí sería vacío negro).
Por puerta y lado: si el modelo de la sala no tiene hoja de puerta en el umbral, se mide el hueco con rayos
(ancho, alto y plano de la pared) y se coloca la puerta doble r102_doorLR escalada a ese hueco.
Salida: /home/claude/uc/objs/rNNN/relleno.obj (unidades de UC, mundo de UC), que uc_prep.py añade a la sala.
uso: uc_relleno.py conexiones2.json"""
import json, os, re, shutil, sys
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, '/home/claude/tools')
import objload, re4room

COL = "19.4,0,15.0,-47609,12,7084,-1.253"
hx, hy, hz, X, Y, Z, th = [float(v) for v in COL.split(',')]
c_, s_ = np.cos(th), np.sin(th); R = np.array([[c_, 0, s_], [0, 1, 0], [-s_, 0, c_]])
def a_uc(P):   # metros RE4 -> unidades de UC (inversa de place con escala 1000 y luego /0.1)
    return ((np.asarray(P) - np.array([X, Y, Z]) / 1000) @ R + np.array([hx, hy, hz])) * 10.0

PUERTA = '/home/claude/uc/objs/r102/_m/r102_doorLR'
DV, DT, DF, DM, DG, Dmats = objload.load(f'{PUERTA}/r102_doorLR.obj')
dlo, dhi = DV.min(0), DV.max(0)

conx = json.load(open(sys.argv[1]))
cache = {}
def sala(r):
    if r not in cache:
        V, T, F, M, G, mats = objload.load(f'/home/claude/uc/m/{r}/sala.obj')
        P = re4room.place(V, COL, 1000.0)
        tri = P[F[:, :3]]
        tex = np.array([(mats.get(m) or '') for m in M])
        door = np.array([bool(re.search('door', t, re.I)) and not re.search('nob|huchi|fuchi|waku|kazari|parts', t, re.I) for t in tex])
        cache[r] = (tri, door)
    return cache[r]

def rays(tri, O, D, tmax):
    """distancia al primer triángulo por rayo (Möller-Trumbore), tmax si no choca"""
    v0, e1, e2 = tri[:, 0], tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]
    out = np.full(len(O), tmax)
    for k in range(len(O)):
        p = np.cross(D[k], e2); det = (e1 * p).sum(1)
        ok = np.abs(det) > 1e-9; inv = np.where(ok, 1 / np.where(ok, det, 1), 0)
        s = O[k] - v0; u = (s * p).sum(1) * inv
        q = np.cross(s, e1); v = (D[k] * q).sum(1) * inv; t = (e2 * q).sum(1) * inv
        hit = ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 1e-4) & (t < tmax)
        if hit.any(): out[k] = t[hit].min()
    return out

nuevos = {}
for q in conx:
    t0 = np.array(q['umbral']); u0 = np.array(q['u'])
    for R_, sg, y0 in ((q['a'], 1, q['ya']), (q['b'], -1, q['yb'])):
        if R_ == 'PUEBLO' or y0 is None: continue
        tri, door = sala(R_)
        u = u0 * sg; n = np.array([-u[1], u[0]])
        u3 = np.array([u[0], 0, u[1]]); n3 = np.array([n[0], 0, n[1]])
        cen = tri.mean(1)
        near = np.hypot(cen[:, 0] - t0[0], cen[:, 2] - t0[2]) < 5.0
        T = tri[near]
        # ¿ya hay hoja de puerta?
        dc = cen[door]
        hoja = ((np.hypot(dc[:, 0] - t0[0], dc[:, 2] - t0[2]) < 1.0) & (dc[:, 1] > y0 + 0.3) & (dc[:, 1] < y0 + 2.6)).sum()
        if hoja >= 4: print(f'{R_} hacia {q["b"] if sg == 1 else q["a"]}: ya tiene puerta ({hoja} triángulos)'); continue
        base = np.array([t0[0], y0, t0[2]]) - u3 * 1.5
        S = np.arange(-3.0, 3.001, 0.05)
        O = np.array([base + n3 * s + np.array([0, 1.2, 0]) for s in S]); D = np.tile(u3, (len(S), 1))
        d = rays(T, O, D, 3.5)
        abierto = d > 2.1
        if not abierto.any(): print(f'{R_}: sin hueco medible, no se tapa'); continue
        i0 = int(np.argmin(np.abs(S)))
        if not abierto[i0]:
            cand = np.where(abierto & (np.abs(S) < 1.0))[0]
            if not len(cand): print(f'{R_}: hueco lejos del umbral, no se tapa'); continue
            i0 = cand[np.argmin(np.abs(S[cand]))]
        lo = i0; hi = i0
        while lo > 0 and abierto[lo - 1]: lo -= 1
        while hi < len(S) - 1 and abierto[hi + 1]: hi += 1
        ancho = S[hi] - S[lo] + 0.05
        pared = d[(np.arange(len(S)) < lo) | (np.arange(len(S)) > hi)]
        pared = pared[pared < 2.1]
        dw = float(np.median(pared)) if len(pared) else 1.5
        sc = (S[lo] + S[hi]) / 2
        # alto del hueco
        H = np.arange(0.1, 4.5, 0.05)
        O2 = np.array([base + n3 * sc + np.array([0, h, 0]) for h in H]); D2 = np.tile(u3, (len(H), 1))
        d2 = rays(T, O2, D2, 3.5)
        k = 0
        while k < len(H) and d2[k] > 2.1: k += 1
        alto = H[k - 1] + 0.05 if k > 0 else 2.4
        if ancho > 4.5 or ancho < 0.7: print(f'{R_}: hueco raro ({ancho:.2f} m), no se tapa'); continue
        alto = float(np.clip(alto, 2.0, 4.5))
        centro = base + n3 * sc + u3 * (dw + 0.08)       # pegada a la pared por el otro lado del marco
        sx = (ancho + 0.1) / ((dhi[0] - dlo[0]) * 0.1); sy = (alto + 0.05) / ((dhi[1] - dlo[1]) * 0.1)
        L = DV.copy() * 0.1
        L[:, 0] = (L[:, 0] - (dlo[0] + dhi[0]) * 0.05) * sx; L[:, 1] = (L[:, 1] - dlo[1] * 0.1) * sy
        Pm = centro + np.outer(L[:, 0], n3) + np.outer(L[:, 1], [0, 1, 0]) + np.outer(L[:, 2], u3)
        nuevos.setdefault(R_, []).append(a_uc(Pm))
        print(f'{R_} hacia {q["b"] if sg == 1 else q["a"]}: hueco {ancho:.2f} x {alto:.2f} m, pared a {dw - 1.5:+.2f} m del umbral -> puerta')

for R_, lst in nuevos.items():
    out = f'/home/claude/uc/objs/{R_}'; os.makedirs(out, exist_ok=True)
    with open(f'{out}/relleno.obj', 'w') as f:
        f.write('mtllib relleno.mtl\n'); vb = 1; tb = 1
        for P in lst:
            f.writelines(f'v {x:.4f} {y:.4f} {z:.4f}\n' for x, y, z in P)
            f.writelines(f'vt {a:.5f} {b:.5f}\n' for a, b in DT)
            cur = None
            for fc, m in zip(DF, DM):
                if m != cur: f.write(f'usemtl relleno_{m}\n'); cur = m
                f.write('f ' + ' '.join(f'{vb + fc[k]}/{tb + fc[k + 3]}' for k in range(3)) + '\n')
            vb += len(P); tb += len(DT)
    with open(f'{out}/relleno.mtl', 'w') as f:
        for m, t in Dmats.items():
            f.write(f'newmtl relleno_{m}\nKd 1 1 1\n' + (f'map_Kd {t}\n' if t else ''))
            if t and not os.path.exists(f'{out}/{t}'): shutil.copy(f'{PUERTA}/{t}', f'{out}/{t}')
print('salas con puertas añadidas:', {k: len(v) for k, v in nuevos.items()})
