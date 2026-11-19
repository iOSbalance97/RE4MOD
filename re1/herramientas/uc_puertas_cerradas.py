"""Puertas cerradas en todos los umbrales de las conexiones (sobre uc/m: metros, marco de UC).
1) quita las piezas de hoja (textura *door*, losa vertical) a <1,8 m del umbral que no estén paralelas a la pared
   (puertas abiertas o entreabiertas del recorrido de cámara de UC)
2) mide el hueco con rayos (ancho, alto, plano de la pared); si una hoja cerrada ya lo tapa, no se toca
3) coloca una puerta cerrada de UC ajustada al hueco: de la propia sala (doble si el hueco > 1,3 m, sencilla si no)
uso: uc_puertas_cerradas.py conexiones2.json"""
import glob, json, os, re, shutil, sys
import numpy as np
sys.path.insert(0, '/home/claude/tools')
import objload
from uc_relleno_rays import rays
COL = [19.4, 0, 15.0, -47609, 12, 7084, -1.253]
hx, hy, hz, X0, Y0, Z0, th = COL
c_, s_ = np.cos(th), np.sin(th); R = np.array([[c_, 0, s_], [0, 1, 0], [-s_, 0, c_]])
def a_uc(p): return (np.asarray(p, float) - np.array([X0, Y0, Z0]) / 1000) @ R + np.array([hx, hy, hz])
def dir_uc(u): v = np.array([u[0], 0, u[1]]) @ R; v = v[[0, 2]]; return v / np.linalg.norm(v)

def modelos_puerta(r):
    sen, dob = [], []
    for d in sorted(glob.glob(f'/home/claude/uc/objs/*/_m/*door*')):
        n = os.path.basename(d)
        if not re.match(r'r1\d\d_door(L|R|LR)(_[AB])?$', n): continue
        V = objload.load(f'{d}/{n}.obj')[0]; w = np.ptp(V[:, 0]) * 0.1
        (dob if w > 1.5 else sen).append((n.startswith(r + '_'), d, n))
    sen.sort(key=lambda x: (not x[0], x[2])); dob.sort(key=lambda x: (not x[0], x[2]))
    return sen[0][1:], dob[0][1:]

conx = json.load(open(sys.argv[1]))
lados = {}
for q in conx:
    for R_, sg, y in ((q['a'], 1, q['ya']), (q['b'], -1, q['yb'])):
        if R_ == 'PUEBLO' or y is None: continue
        t = a_uc([q['umbral'][0], y, q['umbral'][2]]); u = dir_uc(q['u']) * sg
        lados.setdefault(R_, []).append((t, u, q['b'] if sg == 1 else q['a']))

for r, lst in sorted(lados.items()):
    path = f'/home/claude/uc/m/{r}/sala.obj'; dst = os.path.dirname(path)
    V, T, F, M, G, mats = objload.load(path)
    M = list(M)
    tex = [(mats.get(m) or '') for m in M]
    es = np.array([bool(re.search('door', t_, re.I)) and not re.search('nob|huchi|fuchi|waku|kazari|knob', t_, re.I) for t_ in tex])
    # 1) piezas de hoja abiertas cerca de los umbrales
    from scipy.spatial import cKDTree
    idx = np.where(es)[0]; quitar = set()
    if len(idx):
        cen = V[F[idx, :3]].mean(1); trc = cKDTree(cen); lab = -np.ones(len(idx), int); k = 0
        for s0 in range(len(idx)):
            if lab[s0] >= 0: continue
            st = [s0]; lab[s0] = k
            while st:
                qq = st.pop()
                for j in trc.query_ball_point(cen[qq], 0.10):
                    if lab[j] < 0: lab[j] = k; st.append(j)
            k += 1
        for c in range(k):
            tris = idx[lab == c]; P = V[np.unique(F[tris, :3])]
            h = np.ptp(P[:, 1]); Xc = P[:, [0, 2]] - P[:, [0, 2]].mean(0)
            ev, evec = np.linalg.eigh(Xc.T @ Xc); d = evec[:, 1]
            if not (0.8 <= h <= 3.2 and 0.3 <= np.ptp(Xc @ d) <= 1.8 and np.ptp(Xc @ evec[:, 0]) < 0.25): continue
            for t, u, _ in lst:
                if np.linalg.norm(P[:, [0, 2]].mean(0) - t[[0, 2]]) < 1.8 and abs(P[:, 1].min() - t[1]) < 1.0:
                    n = np.array([-u[1], u[0]])
                    if np.degrees(np.arccos(min(1, abs(np.dot(d, n))))) > 12: quitar.update(tris.tolist())
                    break
    F_orig = F.copy()
    keep = np.array([i not in quitar for i in range(len(F))])
    F = F[keep]; M = [m for m, k_ in zip(M, keep) if k_]
    tri = V[F[:, :3]]
    # 2-3) hueco en las paredes de la colisión de UC (colision.obj de la sala, metros RE4 -> marco UC)
    CV, CW = [], []
    for ln in open(f'/home/claude/uc/re4/{r}/col/colision.obj'):
        if ln.startswith('v '): CV.append([float(x) for x in ln.split()[1:4]])
        elif ln.startswith('g '): gname = ln.split()[1]
        elif ln.startswith('f ') and gname == 'pared': CW.append([int(x) - 1 for x in ln.split()[1:4]])
    CV = a_uc(np.array(CV)); CW = np.array(CW)
    piezas = []
    tri = V[F[:, :3]]
    for t, u, otra in lst:
        u3 = np.array([u[0], 0, u[1]]); n = np.array([-u[1], u[0]]); n3 = np.array([n[0], 0, n[1]])
        W = CV[CW] - t                                         # paredes relativas al umbral
        a_ = W[:, :, [0, 2]] @ u; l_ = W[:, :, [0, 2]] @ n; y_ = W[:, :, 1]
        par = (np.ptp(l_, 1) > 0.05) & (np.ptp(a_, 1) < 0.35 * np.ptp(l_, 1) + 0.05)     # paralelas al umbral
        cerca = (np.abs(a_.mean(1)) < 1.2) & (y_.min(1) < 2.0) & (y_.max(1) > 0.3)
        sel = par & cerca
        iv = sorted((float(l_[i].min()), float(l_[i].max()), float(a_[i].mean())) for i in np.where(sel)[0])
        # unir tramos y buscar el hueco junto a 0
        tramos = []
        for lo_, hi_, a0 in iv:
            if tramos and lo_ <= tramos[-1][1] + 0.05: tramos[-1][1] = max(tramos[-1][1], hi_); tramos[-1][2].append(a0)
            else: tramos.append([lo_, hi_, [a0]])
        huecos = [(tramos[i][1], tramos[i + 1][0], tramos[i][2] + tramos[i + 1][2]) for i in range(len(tramos) - 1)]
        huecos = [h for h in huecos if 0.6 <= h[1] - h[0] <= 3.2]
        if huecos:
            h = min(huecos, key=lambda h: abs((h[0] + h[1]) / 2))
            if abs((h[0] + h[1]) / 2) > 1.6: huecos = []
        if huecos:
            ancho = h[1] - h[0]; sc = (h[0] + h[1]) / 2; plano = float(np.median(h[2]))
        else:
            # la colisión cierra el hueco: buscarlo en la geometría visible (rayos que pasan, con pared a ambos lados)
            cen_ = tri.mean(1); T5 = tri[np.hypot(cen_[:, 0] - t[0], cen_[:, 2] - t[2]) < 5.0]
            base = t - u3 * 1.5; S = np.arange(-3.0, 3.001, 0.05)
            res = None
            for hh in (1.0, 1.6):
                d = rays(T5, np.array([base + n3 * s_ + [0, hh, 0] for s_ in S]), np.tile(u3, (len(S), 1)), 4.0)
                far = d > 2.2; i = 0; runs = []
                while i < len(S):
                    if far[i]:
                        j = i
                        while j + 1 < len(S) and far[j + 1]: j += 1
                        if i > 0 and j < len(S) - 1 and 0.6 < d[i - 1] < 2.3 and 0.6 < d[j + 1] < 2.3:
                            runs.append((S[i] - 0.025, S[j] + 0.025, (d[i - 1] + d[j + 1]) / 2 - 1.5))
                        i = j + 1
                    else: i += 1
                runs = [x for x in runs if 0.6 <= x[1] - x[0] <= 3.0 and abs((x[0] + x[1]) / 2) < 1.6]
                if runs:
                    x = min(runs, key=lambda x: abs((x[0] + x[1]) / 2)); res = x; break
            if res:
                ancho = res[1] - res[0]; sc = (res[0] + res[1]) / 2; plano = res[2]
                print(f'{r} -> {otra}: hueco visible de {ancho:.2f} m')
            else:
                ancho, sc, plano = 1.1, 0.0, 0.0
                print(f'{r} -> {otra}: sin hueco claro, puerta de 1,1 m en el umbral')
        # ¿ya hay una hoja cerrada (paralela a la pared) en el umbral?
        cerrada = False; cubiertos = []
        if len(idx):
            for c in range(k):
                tris = idx[lab == c]
                if any(x in quitar for x in tris.tolist()): continue
                P = V[np.unique(F_orig[tris, :3])]
                if np.ptp(P[:, 1]) < 1.6: continue
                rp = P[:, [0, 2]].mean(0) - t[[0, 2]]
                if abs(rp @ u - plano) < 0.35 and abs(P[:, 1].min() - t[1]) < 0.6:
                    Xc = P[:, [0, 2]] - P[:, [0, 2]].mean(0); ev, evec = np.linalg.eigh(Xc.T @ Xc)
                    if abs(evec[:, 1] @ n) > 0.95:
                        lp = (P[:, [0, 2]] - t[[0, 2]]) @ n
                        cubre = max(0, min(lp.max(), sc + ancho / 2) - max(lp.min(), sc - ancho / 2))
                        cubiertos.append(cubre)
            if sum(cubiertos) >= 0.6 * ancho: cerrada = True
        if cerrada: print(f'{r} -> {otra}: ya tiene puerta cerrada'); continue
        alto = 2.35 if ancho <= 1.3 else 2.5
        sen, dob = modelos_puerta(r)
        md, mn = dob if ancho > 1.3 else sen
        DV, DT, DF, DM, DG, Dm = objload.load(f'{md}/{mn}.obj')
        lo_, hi_ = DV.min(0), DV.max(0)
        L = DV * 0.1
        L[:, 0] = (L[:, 0] - (lo_[0] + hi_[0]) * 0.05) * (ancho + 0.06) / (np.ptp(DV[:, 0]) * 0.1)
        L[:, 1] = (L[:, 1] - lo_[1] * 0.1) * alto / (np.ptp(DV[:, 1]) * 0.1)
        L[:, 2] = (L[:, 2] - (lo_[2] + hi_[2]) * 0.05)
        centro = t + n3 * sc + u3 * plano
        Pm = centro + np.outer(L[:, 0], n3) + np.outer(L[:, 1], [0, 1, 0]) + np.outer(L[:, 2], -u3)
        piezas.append((Pm, DT, DF, DM, Dm, md))
        print(f'{r} -> {otra}: puerta {mn} de {ancho:.2f} x {alto:.2f} m (centro {sc:+.2f} m, plano {plano:+.2f} m)')
    # escribir sala con lo quitado y las puertas nuevas
    Vs, Ts, Fs, Ms = [V], [T], [F], list(M); nv, nt = len(V), len(T)
    for k, (Pm, DT, DF, DM, Dm, md) in enumerate(piezas):
        f = DF.copy(); f[:, :3] += nv; f[:, 3:] += nt
        Vs.append(Pm); Ts.append(DT); Fs.append(f); Ms += [f'cerrada_{os.path.basename(md)}_{m}' for m in DM]
        for m, tx in Dm.items():
            mats[f'cerrada_{os.path.basename(md)}_{m}'] = tx
            if tx and not os.path.exists(f'{dst}/{tx}'): shutil.copy(f'{md}/{tx}', f'{dst}/{tx}')
        nv += len(Pm); nt += len(DT)
    V2 = np.concatenate(Vs); T2 = np.concatenate(Ts); F2 = np.concatenate(Fs)
    with open(path, 'w') as f:
        f.write('mtllib sala.mtl\n')
        f.writelines(f'v {x:.4f} {y:.4f} {z:.4f}\n' for x, y, z in V2)
        f.writelines(f'vt {a:.5f} {b:.5f}\n' for a, b in T2)
        cur = None
        for fc, m in zip(F2, Ms):
            if m != cur: f.write(f'usemtl {m}\n'); cur = m
            f.write(f'f {fc[0]+1}/{fc[3]+1} {fc[1]+1}/{fc[4]+1} {fc[2]+1}/{fc[5]+1}\n')
    with open(f'{dst}/sala.mtl', 'w') as f:
        for m in dict.fromkeys(Ms):
            tx = mats.get(m); f.write(f'newmtl {m}\nKd 1 1 1\n' + (f'map_Kd {tx}\n' if tx else ''))
    print(f'{r}: quitadas {len(quitar)} piezas de hoja abiertas, puestas {len(piezas)} puertas')
